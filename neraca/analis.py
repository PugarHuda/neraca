"""ANALIS — distills the COLD journal into evolving WARM reputation profiles.

Pure function of (events, rubric): rebuilding from scratch every run makes it
deterministic and idempotent by construction — the same journal always yields
the same profiles and the same score_history.
"""

import time
from datetime import datetime, timedelta, timezone

from .memory import client, get_rubric, job_events, settlement_events


def _blank(rubric: dict) -> dict:
    return {
        "jobs_ok": 0,
        "disputes_initiated": 0,
        "rejections_received": 0,
        "jobs_expired": 0,
        "invoices_paid": 0,
        "budgets": [],
        "last_seen": None,
        "score": rubric["base_score"],
        "score_history": [],
    }


def _bump(profiles: dict, rubric: dict, addr: str, ts: str, delta: int, why: str, counter: str) -> None:
    p = profiles.setdefault(addr, _blank(rubric))
    p[counter] += 1
    p["score"] = max(0, min(100, p["score"] + delta))
    p["score_history"].append({"ts": ts, "score": p["score"], "why": why})


def build_profiles(events: list[dict], rubric: dict, settlements: list[dict] = ()) -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    for e in settlements:
        x = e["extra"]
        p = profiles.setdefault(x["payer"], _blank(rubric))
        p["last_seen"] = e["ts"]
        _bump(profiles, rubric, x["payer"], e["ts"], rubric["settlement_bonus"],
              f"settled ${x['amount_usd']} for {x['resource']}", "invoices_paid")
    for e in events:
        x = e["extra"]
        ts, cl, pr, job = e["ts"], x["client"], x["provider"], x["job_id"]
        for addr in (cl, pr):
            p = profiles.setdefault(addr, _blank(rubric))
            p["last_seen"] = ts
            if x.get("budget"):
                p["budgets"].append(x["budget"])
        if x["phase"] == "COMPLETED":
            _bump(profiles, rubric, pr, ts, rubric["completed_bonus"],
                  f"job {job} completed", "jobs_ok")
            _bump(profiles, rubric, cl, ts, rubric["client_completed_bonus"],
                  f"funded and accepted job {job}", "jobs_ok")
        elif x["phase"] == "REJECTED":
            _bump(profiles, rubric, cl, ts, -rubric["dispute_penalty"],
                  f"rejected delivered job {job}", "disputes_initiated")
            _bump(profiles, rubric, pr, ts, -rubric["rejection_received_penalty"],
                  f"delivery on job {job} was rejected", "rejections_received")
        elif x["phase"] == "EXPIRED":
            _bump(profiles, rubric, pr, ts, -rubric["failed_penalty"],
                  f"let job {job} expire", "jobs_expired")
    return profiles


def run(m=None) -> dict[str, dict]:
    """Rebuild all WARM profiles from the journal; archive stale agents."""
    m = m or client()
    rubric = get_rubric(m)
    profiles = build_profiles(job_events(m), rubric, settlement_events(m))
    cutoff = datetime.now(timezone.utc) - timedelta(days=rubric["stale_days"])
    for addr, p in profiles.items():
        last = datetime.fromisoformat(p["last_seen"].replace("Z", "+00:00"))
        if last < cutoff:
            m.set_entity("agent", addr, p)
            m.archive_entity("agent", addr, reason=f"inactive since {p['last_seen']}")
        else:
            m.set_entity("agent", addr, p)
    return profiles


def refresh(m, seen) -> tuple[tuple, dict | None]:
    """One watch tick: rebuild only if memory actually moved - a new event in
    the journal, or a new version of the doctrine. `reflect` in one process
    revises the rubric; the watcher in another rescored everyone under it."""
    mark = (len(job_events(m)) + len(settlement_events(m)), get_rubric(m).get("version", 1))
    return (mark, None) if mark == seen else (mark, run(m))


def watch(m=None, interval: float = 2.0) -> None:
    """ANALIS as its own long-lived process.

    It is handed nothing and told nothing: no queue, no socket, no callback.
    It watches the COLD journal and reacts when another process writes to it.
    That is the whole coordination mechanism — memory is the bus.
    """
    # ponytail: polls; swap for a memory change-feed if Sibyl grows one
    m = m or client()
    seen = None
    print(f"ANALIS watching the journal every {interval}s - Ctrl-C to stop", flush=True)
    try:
        while True:
            seen, profiles = refresh(m, seen)
            if profiles:  # empty journal: nothing to announce yet
                stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
                events, version = seen
                print(f"[{stamp}] memory moved: {events} events, rubric v{version} - profiles rebuilt", flush=True)
                for addr, prof in sorted(profiles.items(), key=lambda kv: kv[1]["score"]):
                    print(f"   {prof['score']:>3}  {addr}", flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nANALIS stopped - the journal it read is still on disk", flush=True)


ADVERSE = ("REJECTED", "EXPIRED")
REFLECTED_KEY = "analis:reflected"   # HOT: verdict ids already graded


def grade_verdicts(verdicts: list[dict], jobs: list[dict]) -> dict:
    """Grade past verdicts against what the journal saw afterwards.

    A verdict is graded on the first thing that happened to that counterparty
    after it was given: an APPROVE followed by a rejection or an expiry was a
    false approve; a DECLINE followed by a clean completion was a false
    decline. Pure over its inputs.
    """
    first: dict[str, dict] = {}
    for v in verdicts:  # the earliest call on a counterparty is the prediction that mattered
        first.setdefault(v["extra"]["counterparty"], v)
    graded = false_approve = false_decline = 0
    cases = []
    for cp, v in first.items():
        after = [e["extra"]["phase"] for e in jobs
                 if e["ts"] > v["ts"] and cp in (e["extra"]["client"], e["extra"]["provider"])]
        if not after:
            continue
        graded += 1
        adverse, good = any(p in ADVERSE for p in after), "COMPLETED" in after
        verdict = v["extra"]["verdict"]
        outcome = "held"
        if verdict in ("APPROVE", "APPROVE_WITH_GUARANTEE") and adverse:
            false_approve += 1
            outcome = "false_approve"
        elif verdict == "DECLINE" and good and not adverse:
            false_decline += 1
            outcome = "false_decline"
        cases.append({"counterparty": cp, "verdict": verdict, "then": after, "outcome": outcome})
    return {"graded": graded, "false_approve": false_approve,
            "false_decline": false_decline, "cases": cases}


def reflect(m=None, tolerance: float = 0.25) -> dict:
    """The bureau grades its own past verdicts and edits its doctrine.

    Too many approvals that went bad: disputes cost more and approval gets
    harder. Too many declines that would have been fine: the guarantee band
    opens lower. The rubric lives in REFERENCE, so the change is remembered
    state with a version and a history - the next ANALIS run applies it.
    Deterministic, no LLM, and it only moves when the evidence clears the bar.
    """
    from .memory import RUBRIC_KEY, verdict_events

    m = m or client()
    rubric = get_rubric(m)
    # HOT: which verdicts have already been graded, so the same evidence never
    # tightens the doctrine twice
    already = set(((m.get_state(REFLECTED_KEY) or {}).get("body") or {}).get("ids", []))
    fresh = [v for v in verdict_events(m) if v["id"] not in already]
    report = grade_verdicts(fresh, job_events(m))
    graded_ids = [v["id"] for v in fresh
                  if any(c["counterparty"] == v["extra"]["counterparty"] for c in report["cases"])]
    if graded_ids:
        m.set_state(REFLECTED_KEY, {"ids": sorted(already | set(graded_ids))})
    changes: dict[str, list] = {}
    if report["graded"]:
        if report["false_approve"] / report["graded"] > tolerance:
            for key, step, cap in (("dispute_penalty", 5, 50), ("approve_threshold", 5, 90)):
                new = min(cap, rubric[key] + step)
                if new != rubric[key]:
                    changes[key] = [rubric[key], new]
                    rubric[key] = new
        if report["false_decline"] / report["graded"] > tolerance:
            new = max(20, rubric["guarantee_threshold"] - 5)
            if new != rubric["guarantee_threshold"]:
                changes["guarantee_threshold"] = [rubric["guarantee_threshold"], new]
                rubric["guarantee_threshold"] = new
    if changes:
        rubric["version"] = rubric.get("version", 1) + 1
        rubric.setdefault("history", []).append({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "version": rubric["version"], "changes": changes,
            "graded": report["graded"], "false_approve": report["false_approve"],
            "false_decline": report["false_decline"],
        })
        m.set_reference(RUBRIC_KEY, rubric)
    return report | {"changes": changes, "rubric_version": rubric.get("version", 1)}
