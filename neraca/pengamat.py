"""PENGAMAT — the scout. Observes ACP jobs and journals them into COLD memory.

Sources, in order of how real they are:
- observe_chain(): the live Virtuals ACP JobManager on Base mainnet, read
  straight from contract logs over a public RPC. No registration, no API key.
  Where it left off lives in HOT memory, so every run resumes, never rescans.
- acp.py: jobs NERACA itself is party to, seen through the ACP socket.
- sim_scenario(): the deterministic scenario the tests and the demo's first
  act use, so the verdict flip is reproducible on any machine.
"""

import os

from .memory import client, record_job_event

KLIEN_A = "0xKLIENA000000000000000000000000000000000A"   # well-behaved client
KLIEN_B = "0xKLIENB000000000000000000000000000000000B"   # rejects delivered work
MAKELAR_ADDR = "0xNERACA00000000000000000000000000000000AA"  # our provider

# Virtuals ACP v2 on Base mainnet. The JobManager module is resolved from the
# main contract at runtime, the way the official SDK does it.
ACP_MAINNET = "0xa6C9BA866992cfD7fd6460ba912bfa405adA9df0"
BASE_MAINNET_RPC = os.environ.get("NERACA_BASE_RPC", "https://mainnet.base.org")
CHAIN_CURSOR = "pengamat:chain-cursor"          # HOT: last block scanned
LOG_CHUNK = 2000                                 # public RPC's eth_getLogs ceiling

# on-chain ACPJobPhase -> the journal's vocabulary
ONCHAIN_PHASE = {0: "CREATED", 1: "CREATED", 2: "FUNDED", 3: "DELIVERED",
                 4: "COMPLETED", 5: "REJECTED", 6: "EXPIRED"}


def sim_scenario(with_dispute: bool = True) -> list[dict]:
    """KLIEN-A completes six jobs; KLIEN-B funds one, then rejects the delivery.

    with_dispute=False stops one event short of B's rejection, so the demo can
    land that single event live and show the same question change its answer.
    """
    jobs = []
    for i in range(1, 7):
        for phase in ("CREATED", "FUNDED", "DELIVERED", "COMPLETED"):
            jobs.append(dict(job_id=f"sim-a{i}", phase=phase,
                             client_addr=KLIEN_A, provider=MAKELAR_ADDR, budget=10.0))
    phases = ("CREATED", "FUNDED", "DELIVERED")
    if with_dispute:
        phases += ("REJECTED",)
    for phase in phases:
        jobs.append(dict(job_id="sim-b1", phase=phase,
                         client_addr=KLIEN_B, provider=MAKELAR_ADDR, budget=50.0))
    return jobs


def dispute_event() -> dict:
    """The single adverse observation the demo lands live."""
    return dict(job_id="sim-b1", phase="REJECTED",
                client_addr=KLIEN_B, provider=MAKELAR_ADDR, budget=50.0)


def observe(events: list[dict], m=None) -> int:
    """Journal a batch of observations; returns how many were new."""
    m = m or client()
    written = 0
    for ev in events:
        if record_job_event(m, **ev) is not None:
            written += 1
    return written


def chain_logs_to_events(created: list, phases: list, lookup,
                         new_memos: list = (), signed: list = (), memo_job=None) -> list[dict]:
    """Turn raw JobManager + MemoManager logs into journal observations.

    Most of an ACP job's life happens in memos, not phase updates: a memo is
    posted proposing `nextPhase`, and the counterparty signs it approved or
    not. An approved signature moves the job; a refusal is a rejection.

    `lookup(job_id)` resolves (client, provider, budget) for a job whose
    creation we never saw — first from memory, then the contract.
    `memo_job(memo_id)` resolves the job behind a memo posted before the scan.
    Pure over its inputs so it can be tested without a chain.
    """
    parties: dict[int, tuple[str, str, float | None]] = {}
    events: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def emit(job_id: int, phase: str, tx) -> None:
        if phase is None or phase == "CREATED" or (job_id, phase) in seen:
            return
        who = parties.get(job_id) or lookup(job_id)
        if who is None:
            return
        cl, pr, budget = who
        seen.add((job_id, phase))
        events.append(dict(job_id=f"acp-{job_id}", phase=phase, client_addr=cl,
                           provider=pr, budget=budget, tx=_hex(tx)))

    for log in created:
        a = log["args"]
        parties[a["jobId"]] = (a["client"], a["provider"], None)
        events.append(dict(job_id=f"acp-{a['jobId']}", phase="CREATED",
                           client_addr=a["client"], provider=a["provider"],
                           tx=_hex(log["transactionHash"])))
    for log in phases:
        a = log["args"]
        emit(a["jobId"], ONCHAIN_PHASE.get(a["newPhase"]), log["transactionHash"])

    memos = {m["args"]["memoId"]: (m["args"]["jobId"], m["args"]["nextPhase"]) for m in new_memos}
    for log in signed:
        a = log["args"]
        job_and_phase = memos.get(a["memoId"]) or (memo_job(a["memoId"]) if memo_job else None)
        if job_and_phase is None:
            continue
        job_id, next_phase = job_and_phase
        phase = ONCHAIN_PHASE.get(next_phase) if a["approved"] else "REJECTED"
        emit(job_id, phase, log["transactionHash"])
    return events


ACP_DIRECTORY_API = "https://acpx.virtuals.io/api/agents/v4/search"
DIRECTORY_KEYWORDS = ("agent", "trading", "research", "data", "alpha", "risk",
                      "market", "token", "defi", "ai", "analysis", "content")


def refresh_directory(m=None, keywords=DIRECTORY_KEYWORDS, fetch=None) -> dict:
    """Pull the public ACP marketplace directory into REFERENCE.

    Names and the marketplace's own success metrics, keyed by wallet, so a
    verdict on a real address can say who that is. What the marketplace
    claims is stored beside - never mixed into - what NERACA remembers.
    `fetch(keyword)` is injectable so the mapping is testable offline.
    """
    from datetime import datetime, timezone

    from .memory import get_directory, set_directory

    if fetch is None:
        import httpx

        def fetch(keyword: str) -> list[dict]:
            r = httpx.get(ACP_DIRECTORY_API, params={"search": keyword, "top_k": 50}, timeout=40)
            r.raise_for_status()
            return r.json().get("data", [])

    m = m or client()
    directory = get_directory(m)
    before = len(directory)
    skipped = []
    for kw in keywords:
        try:
            agents = fetch(kw)
        except Exception as e:  # one slow keyword must not cost the whole refresh
            skipped.append(f"{kw}: {type(e).__name__}")
            continue
        for a in agents:
            metrics = a.get("metrics") or {}
            directory[a["walletAddress"].lower()] = {
                "name": a.get("name"),
                "success_rate": metrics.get("successRate"),
                "jobs": metrics.get("successfulJobCount"),
                "buyers": metrics.get("uniqueBuyerCount"),
                "refreshed": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            }
    set_directory(m, directory)
    return {"entries": len(directory), "new": len(directory) - before, "skipped": skipped}


def _hex(h) -> str:
    h = h.hex() if hasattr(h, "hex") else str(h)
    return h if h.startswith("0x") else "0x" + h


def observe_chain(m=None, lookback: int = 20000, w3=None) -> dict:
    """Read real ACP jobs off Base mainnet and journal them. Resumable.

    The cursor is HOT state: a second PENGAMAT, or the same one tomorrow,
    picks up at the block this one stopped at. Nothing else is shared.
    """
    from web3 import Web3
    from virtuals_acp.abis.abi_v2 import ACP_V2_ABI
    from virtuals_acp.abis.job_manager import JOB_MANAGER_ABI

    from .memory import job_events

    from virtuals_acp.abis.memo_manager import MEMO_MANAGER_ABI

    m = m or client()
    w3 = w3 or Web3(Web3.HTTPProvider(BASE_MAINNET_RPC))
    acp = w3.eth.contract(address=ACP_MAINNET, abi=ACP_V2_ABI)
    jm = w3.eth.contract(address=acp.functions.jobManager().call(), abi=JOB_MANAGER_ABI)
    mm = w3.eth.contract(address=acp.functions.memoManager().call(), abi=MEMO_MANAGER_ABI)

    head = w3.eth.block_number
    cursor = ((m.get_state(CHAIN_CURSOR) or {}).get("body") or {}).get("block")
    start = cursor + 1 if cursor else head - lookback

    def lookup(job_id: int):
        # memory first: we may have journaled the creation in an earlier run
        for e in job_events(m):
            x = e["extra"]
            if x["job_id"] == f"acp-{job_id}" and x["phase"] == "CREATED":
                return x["client"], x["provider"], x.get("budget")
        try:  # then the contract itself
            j = jm.functions.jobs(job_id).call()
            return j[2], j[3], (j[6] / 1_000_000 if j[6] else None)
        except Exception:
            return None

    def memo_job(memo_id: int):
        # a memo posted before the window: the contract knows its job but not
        # the phase it proposed, so only a refusal (phase-agnostic) survives
        try:
            return mm.functions.memos(memo_id).call()[1], None
        except Exception:
            return None

    created, phases, new_memos, signed = [], [], [], []
    for s in range(start, head + 1, LOG_CHUNK):
        e = min(s + LOG_CHUNK - 1, head)
        created += jm.events.JobCreated().get_logs(from_block=s, to_block=e)
        phases += jm.events.JobPhaseUpdated().get_logs(from_block=s, to_block=e)
        new_memos += mm.events.NewMemo().get_logs(from_block=s, to_block=e)
        signed += mm.events.MemoSigned().get_logs(from_block=s, to_block=e)

    events = chain_logs_to_events(created, phases, lookup, new_memos, signed, memo_job)
    written = observe(events, m)
    m.set_state(CHAIN_CURSOR, {"block": head, "job_manager": jm.address, "memo_manager": mm.address})
    return {"from_block": start, "to_block": head, "job_created": len(created),
            "phase_updates": len(phases), "memos": len(new_memos), "memos_signed": len(signed),
            "journaled": written, "job_manager": jm.address, "memo_manager": mm.address}
