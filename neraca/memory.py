"""Shared Sibyl Memory layer — the only communication bus between NERACA's agents.

Every write and read of the bureau's knowledge goes through this module.
Judges: this file is where memory is load-bearing (see README).
"""

import json
import os

from sibyl_memory_client import MemoryClient

RUBRIC_KEY = "scoring-rubric"

# Single source of truth for scoring, stored in the REFERENCE tier on first run
# so ANALIS reads the rubric from memory, not from code.
DEFAULT_RUBRIC = {
    "base_score": 50,
    "completed_bonus": 5,           # provider delivered, client accepted
    "client_completed_bonus": 3,    # client funded and accepted; less risk taken, so trust accrues slower
    "dispute_penalty": 25,          # client rejected delivered work
    "rejection_received_penalty": 5,  # provider whose delivery was rejected
    "failed_penalty": 10,           # provider let the job expire
    "settlement_bonus": 2,          # counterparty paid an x402 invoice to our storefront
    "approve_threshold": 70,
    "guarantee_threshold": 40,
    "premium_rate": 0.5,            # % of budget per point below approve_threshold
    "no_history_premium": 20,       # % premium for unknown counterparties
    "stale_days": 30,
}

JOB_PHASES = ("CREATED", "FUNDED", "DELIVERED", "COMPLETED", "REJECTED", "EXPIRED")


def db_path() -> str:
    return os.environ.get("NERACA_DB", "./data/neraca.db")


def client() -> MemoryClient:
    if os.environ.get("NERACA_MEMORY_DISABLED"):
        raise SystemExit(
            "NERACA: memory layer disabled - no memory, no bureau.\n"
            "The Sibyl Memory layer is load-bearing; there is nothing to fall back to."
        )
    return MemoryClient.local(db_path())


def get_rubric(m: MemoryClient) -> dict:
    ref = m.get_reference(RUBRIC_KEY)
    if ref is None:
        m.set_reference(RUBRIC_KEY, DEFAULT_RUBRIC)
        return dict(DEFAULT_RUBRIC)
    body = ref["body"]
    body = json.loads(body) if isinstance(body, str) else body
    return {**DEFAULT_RUBRIC, **body}  # a rubric written by an older NERACA still has every knob


def _events(m: MemoryClient, kind: str, limit: int, until: str | None) -> list[dict]:
    # ponytail: full scan per call; add a since-cursor if the journal outgrows hackathon scale
    evs = [e for e in m.read_events(limit=limit, until=until)
           if (e.get("extra") or {}).get("kind") == kind]
    return sorted(evs, key=lambda e: e["ts"])


def job_events(m: MemoryClient, limit: int = 10000, until: str | None = None) -> list[dict]:
    """All acp_job events from the COLD journal, oldest first.
    `until` is an ISO timestamp: the journal as it stood at that moment."""
    return _events(m, "acp_job", limit, until)


def verdict_events(m: MemoryClient, limit: int = 10000, until: str | None = None) -> list[dict]:
    """Every decision MAKELAR ever gave, oldest first - what reflection grades."""
    return _events(m, "verdict", limit, until)


def search(m: MemoryClient, query: str, limit: int = 20) -> list[dict]:
    """Cross-tier full-text search (FTS5) over everything the bureau remembers."""
    return list(m.search(query, limit=limit))


def settlement_events(m: MemoryClient, limit: int = 10000, until: str | None = None) -> list[dict]:
    """x402 settlements MAKELAR's own storefront witnessed, oldest first."""
    return _events(m, "x402_settlement", limit, until)


def record_settlement(m: MemoryClient, *, payer: str, payee: str, amount_usd: float,
                      tx: str, resource: str) -> str | None:
    """A paid invoice is an observation too: this agent settles what it owes.
    Idempotent on the settlement transaction."""
    if any(e["extra"].get("tx") == tx for e in settlement_events(m)):
        return None
    return m.write_event(
        acted=[f"observed x402 settlement {tx}"],
        extra={"kind": "x402_settlement", "payer": payer, "payee": payee,
               "amount_usd": amount_usd, "tx": tx, "resource": resource},
    )


def record_job_event(
    m: MemoryClient,
    *,
    job_id: str,
    phase: str,
    client_addr: str,
    provider: str,
    budget: float | None = None,
    tx: str | None = None,
) -> str | None:
    """Append one observation to the COLD journal. Idempotent on (job_id, phase)."""
    if phase not in JOB_PHASES:
        raise ValueError(f"unknown job phase: {phase}")
    key = f"{job_id}:{phase}"
    seen = {f"{x['extra']['job_id']}:{x['extra']['phase']}" for x in job_events(m)}
    if key in seen:
        return None
    return m.write_event(
        acted=[f"observed acp_job {key}"],
        extra={
            "kind": "acp_job",
            "job_id": job_id,
            "phase": phase,
            "client": client_addr,
            "provider": provider,
            "budget": budget,
            "tx": tx,
        },
    )
