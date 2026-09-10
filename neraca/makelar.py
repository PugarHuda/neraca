"""MAKELAR — the broker. Turns remembered history into a priced trust decision.

decide() is the load-bearing moment: with no profile in memory it cannot price
risk, and with a different journal it gives a different answer. Every verdict
it gives is journaled, so ANALIS can later grade it against what happened.
"""

from .memory import client, get_rubric, job_events, settlement_events

APPROVE = "APPROVE"
APPROVE_WITH_GUARANTEE = "APPROVE_WITH_GUARANTEE"
DECLINE = "DECLINE"
NO_HISTORY = "NO_HISTORY"


def _price(profile: dict | None, counterparty: str, budget: float, rubric: dict) -> dict:
    if profile is None:
        return {
            "counterparty": counterparty,
            "verdict": NO_HISTORY,
            "counter_budget": round(budget * 0.5, 2),
            "premium_pct": rubric["no_history_premium"],
            "score": None,
            "reasons": ["no remembered history for this counterparty; pricing blind risk"],
        }
    score = profile["score"]
    reasons = [h["why"] for h in profile["score_history"][-3:]] or ["clean but thin history"]
    if score >= rubric["approve_threshold"]:
        decision = {"verdict": APPROVE, "counter_budget": budget, "premium_pct": 0}
    elif score >= rubric["guarantee_threshold"]:
        premium = round((rubric["approve_threshold"] - score) * rubric["premium_rate"], 1)
        decision = {
            "verdict": APPROVE_WITH_GUARANTEE,
            "counter_budget": round(budget * score / 100, 2),
            "premium_pct": premium,
        }
    else:
        decision = {"verdict": DECLINE, "counter_budget": 0, "premium_pct": None}
    return decision | {"counterparty": counterparty, "score": score, "reasons": reasons}


def _known_as(counterparty: str, m) -> dict:
    """REFERENCE: who the marketplace says this address is. Its claims ride
    beside NERACA's remembered score, never inside it."""
    from .memory import get_directory
    entry = get_directory(m).get(counterparty.lower())
    if not entry:
        return {}
    return {"known_as": entry.get("name"),
            "marketplace_claims": {k: entry.get(k) for k in ("success_rate", "jobs", "buyers")}}


def decide(counterparty: str, budget: float, m=None, as_of: str | None = None) -> dict:
    """Price the risk of dealing with `counterparty` for `budget` USDC.

    as_of: an ISO timestamp. Answer from the journal as it stood then - a
    replay that opens no negotiation and journals no verdict.
    """
    m = m or client()
    rubric = get_rubric(m)

    if as_of is not None:
        from .analis import build_profiles
        profile = build_profiles(job_events(m, until=as_of), rubric,
                                 settlement_events(m, until=as_of)).get(counterparty)
        return _price(profile, counterparty, budget, rubric) | {"as_of": as_of}

    try:
        profile = m.get_entity("agent", counterparty)["body"]
    except Exception:
        # WARM is a cache; COLD is the journal of record. A profile that was
        # never built, or that ANALIS archived for going stale, is not the same
        # as no history - nobody outruns their record by waiting a month.
        from .analis import build_profiles
        profile = build_profiles(job_events(m), rubric, settlement_events(m)).get(counterparty)

    decision = _price(profile, counterparty, budget, rubric) | _known_as(counterparty, m)
    # HOT tier: the in-flight negotiation state this decision opens
    m.set_state(f"negotiation:{counterparty}", decision)
    # COLD tier: the verdict itself is an event, so the bureau can be graded on it
    m.write_event(acted=[f"verdict {decision['verdict']} on {counterparty}"],
                  extra={"kind": "verdict", "counterparty": counterparty,
                         "verdict": decision["verdict"], "score": decision["score"],
                         "budget": budget, "counter_budget": decision["counter_budget"],
                         "premium_pct": decision["premium_pct"],
                         "rubric_version": rubric.get("version", 1)})
    return decision


def evidence(counterparty: str, m=None, as_of: str | None = None) -> list[dict]:
    """The raw remembered events behind a decision — cited on demand."""
    m = m or client()
    jobs = [e["extra"] | {"ts": e["ts"]} for e in job_events(m, until=as_of)
            if counterparty in (e["extra"]["client"], e["extra"]["provider"])]
    paid = [e["extra"] | {"ts": e["ts"]} for e in settlement_events(m, until=as_of)
            if counterparty == e["extra"]["payer"]]
    return sorted(jobs + paid, key=lambda x: x["ts"])
