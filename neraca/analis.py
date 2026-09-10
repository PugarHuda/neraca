"""ANALIS — distills the COLD journal into evolving WARM reputation profiles.

Pure function of (events, rubric): rebuilding from scratch every run makes it
deterministic and idempotent by construction — the same journal always yields
the same profiles and the same score_history.
"""

import time
from datetime import datetime, timedelta, timezone

from .memory import client, get_rubric, job_events


def _blank(rubric: dict) -> dict:
    return {
        "jobs_ok": 0,
        "disputes_initiated": 0,
        "rejections_received": 0,
        "jobs_expired": 0,
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


def build_profiles(events: list[dict], rubric: dict) -> dict[str, dict]:
    profiles: dict[str, dict] = {}
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
    profiles = build_profiles(job_events(m), rubric)
    cutoff = datetime.now(timezone.utc) - timedelta(days=rubric["stale_days"])
    for addr, p in profiles.items():
        last = datetime.fromisoformat(p["last_seen"].replace("Z", "+00:00"))
        if last < cutoff:
            m.set_entity("agent", addr, p)
            m.archive_entity("agent", addr, reason=f"inactive since {p['last_seen']}")
        else:
            m.set_entity("agent", addr, p)
    return profiles


def refresh(m, seen: int) -> tuple[int, dict | None]:
    """One watch tick: rebuild profiles only if the journal actually grew."""
    n = len(job_events(m))
    return (n, None) if n == seen else (n, run(m))


def watch(m=None, interval: float = 2.0) -> None:
    """ANALIS as its own long-lived process.

    It is handed nothing and told nothing: no queue, no socket, no callback.
    It watches the COLD journal and reacts when another process writes to it.
    That is the whole coordination mechanism — memory is the bus.
    """
    # ponytail: polls; swap for a memory change-feed if Sibyl grows one
    m = m or client()
    seen = -1
    print(f"ANALIS watching the journal every {interval}s - Ctrl-C to stop", flush=True)
    while True:
        seen, profiles = refresh(m, seen)
        if profiles is not None:
            stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
            print(f"[{stamp}] journal grew to {seen} events - profiles rebuilt", flush=True)
            for addr, prof in sorted(profiles.items(), key=lambda kv: kv[1]["score"]):
                print(f"   {prof['score']:>3}  {addr}", flush=True)
        time.sleep(interval)
