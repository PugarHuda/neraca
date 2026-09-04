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
    "dispute_penalty": 25,          # client rejected delivered work
    "rejection_received_penalty": 5,  # provider whose delivery was rejected
    "failed_penalty": 10,           # provider let the job expire
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
            "NERACA: memory layer disabled — no memory, no bureau.\n"
            "The Sibyl Memory layer is load-bearing; there is nothing to fall back to."
        )
    return MemoryClient.local(db_path())


def get_rubric(m: MemoryClient) -> dict:
    ref = m.get_reference(RUBRIC_KEY)
    if ref is None:
        m.set_reference(RUBRIC_KEY, DEFAULT_RUBRIC)
        return dict(DEFAULT_RUBRIC)
    body = ref["body"]
    return json.loads(body) if isinstance(body, str) else body


def job_events(m: MemoryClient, limit: int = 10000) -> list[dict]:
    """All acp_job events from the COLD journal, oldest first."""
    # ponytail: full scan per call; add a since-cursor if the journal outgrows hackathon scale
    evs = [e for e in m.read_events(limit=limit) if (e.get("extra") or {}).get("kind") == "acp_job"]
    return sorted(evs, key=lambda e: e["ts"])


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
