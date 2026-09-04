"""PENGAMAT — the scout. Observes ACP jobs and journals them into COLD memory.

Sources:
- sim_scenario(): deterministic seed scenario used for tests and the demo's
  first act, until the live ACP sandbox agents (day 4) take over.
- ACP live observation lands in acp source (see onchain.py, day 4).
"""

from .memory import client, record_job_event

KLIEN_A = "0xKLIENA000000000000000000000000000000000A"   # well-behaved client
KLIEN_B = "0xKLIENB000000000000000000000000000000000B"   # rejects delivered work
MAKELAR_ADDR = "0xNERACA00000000000000000000000000000000AA"  # our provider


def sim_scenario() -> list[dict]:
    """KLIEN-A completes six jobs; KLIEN-B funds one, then rejects the delivery."""
    jobs = []
    for i in range(1, 7):
        for phase in ("CREATED", "FUNDED", "DELIVERED", "COMPLETED"):
            jobs.append(dict(job_id=f"sim-a{i}", phase=phase,
                             client_addr=KLIEN_A, provider=MAKELAR_ADDR, budget=10.0))
    for phase in ("CREATED", "FUNDED", "DELIVERED", "REJECTED"):
        jobs.append(dict(job_id="sim-b1", phase=phase,
                         client_addr=KLIEN_B, provider=MAKELAR_ADDR, budget=50.0))
    return jobs


def observe(events: list[dict], m=None) -> int:
    """Journal a batch of observations; returns how many were new."""
    m = m or client()
    written = 0
    for ev in events:
        if record_job_event(m, **ev) is not None:
            written += 1
    return written
