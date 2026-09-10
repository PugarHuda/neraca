"""MAKELAR — the broker. Turns remembered history into a priced trust decision.

decide() is the load-bearing moment: with no profile in memory it cannot price
risk, and with a different journal it gives a different answer.
"""

from .memory import client, get_rubric, job_events

APPROVE = "APPROVE"
APPROVE_WITH_GUARANTEE = "APPROVE_WITH_GUARANTEE"
DECLINE = "DECLINE"
NO_HISTORY = "NO_HISTORY"


def decide(counterparty: str, budget: float, m=None) -> dict:
    m = m or client()
    rubric = get_rubric(m)
    try:
        profile = m.get_entity("agent", counterparty)["body"]
    except Exception:
        # WARM is a cache; COLD is the journal of record. A profile that was
        # never built, or that ANALIS archived for going stale, is not the same
        # as no history - nobody outruns their record by waiting a month.
        from .analis import build_profiles
        profile = build_profiles(job_events(m), rubric).get(counterparty)

    if profile is None:
        decision = {
            "counterparty": counterparty,
            "verdict": NO_HISTORY,
            "counter_budget": round(budget * 0.5, 2),
            "premium_pct": rubric["no_history_premium"],
            "score": None,
            "reasons": ["no remembered history for this counterparty; pricing blind risk"],
        }
    else:
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
        decision.update({"counterparty": counterparty, "score": score, "reasons": reasons})

    # HOT tier: the in-flight negotiation state this decision opens
    m.set_state(f"negotiation:{counterparty}", decision)
    return decision


def evidence(counterparty: str, m=None) -> list[dict]:
    """The raw remembered events behind a decision — cited on demand."""
    m = m or client()
    return [e["extra"] | {"ts": e["ts"]} for e in job_events(m)
            if counterparty in (e["extra"]["client"], e["extra"]["provider"])]
