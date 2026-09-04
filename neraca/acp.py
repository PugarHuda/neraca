"""MAKELAR's storefront #2 + PENGAMAT's live eyes: Virtuals ACP (v2).

Seller: NERACA registered as an ACP provider — a funded job gets a
memory-backed risk report as its deliverable, and every job phase we see is
journaled into COLD memory (live PENGAMAT). Buyer: helper to hire NERACA
(used by our KLIEN demo agents).

Env (.env — from app.virtuals.io/acp/new, Signers tab):
  WHITELISTED_WALLET_PRIVATE_KEY, SELLER_AGENT_WALLET_ADDRESS, SELLER_ENTITY_ID,
  BUYER_AGENT_WALLET_ADDRESS, BUYER_ENTITY_ID, ACP_TESTNET=1 for Base Sepolia.

CLI:  python -m neraca.acp seller            (serve + observe, blocks)
      python -m neraca.acp buyer <provider> <counterparty> <budget_usdc>
"""

import json
import os
import sys
import threading

from .memory import client, record_job_event
from . import makelar

_PHASE_MAP = {  # ACP v2 phase -> our journal phase
    "REQUEST": "CREATED", "NEGOTIATION": "CREATED", "TRANSACTION": "FUNDED",
    "EVALUATION": "DELIVERED", "COMPLETED": "COMPLETED",
    "REJECTED": "REJECTED", "EXPIRED": "EXPIRED",
}


def _config():
    from virtuals_acp.configs import configs
    return (configs.BASE_SEPOLIA_CONFIG_V2 if os.environ.get("ACP_TESTNET")
            else configs.BASE_MAINNET_CONFIG_V2)


def _contract_client(role: str):
    from virtuals_acp.contract_clients.contract_client_v2 import ACPContractClientV2
    addr = os.environ.get(f"{role}_AGENT_WALLET_ADDRESS")
    pk = os.environ.get("WHITELISTED_WALLET_PRIVATE_KEY")
    entity = os.environ.get(f"{role}_ENTITY_ID")
    if not (addr and pk and entity):
        raise SystemExit(
            f"ACP credentials missing for {role}: set {role}_AGENT_WALLET_ADDRESS, "
            f"{role}_ENTITY_ID and WHITELISTED_WALLET_PRIVATE_KEY "
            "(register at app.virtuals.io/acp/new)")
    return ACPContractClientV2(addr, pk, int(entity), config=_config())


def _journal(job) -> None:
    """PENGAMAT live: every phase we see lands in the COLD journal."""
    try:
        phase = _PHASE_MAP.get(getattr(job.phase, "name", str(job.phase)), None)
        if phase is None:
            return
        record_job_event(
            client(),
            job_id=str(job.id),
            phase=phase,
            client_addr=job.client_address,
            provider=job.provider_address,
            budget=float(getattr(job, "price", 0) or 0),
        )
    except Exception as e:  # observation must never take the storefront down
        print(f"journal error: {e}", file=sys.stderr)


def seller() -> None:
    from virtuals_acp.client import VirtualsACP
    from virtuals_acp.models import ACPJobPhase

    def on_new_task(job, memo_to_sign=None):
        _journal(job)
        if job.phase == ACPJobPhase.REQUEST:
            # the bureau checks its memory before accepting the client at all
            verdict = makelar.decide(job.client_address, float(getattr(job, "price", 0) or 1))
            if verdict["verdict"] == "DECLINE":
                print(f"job {job.id}: declining client {job.client_address} — remembered: "
                      f"{verdict['reasons']}")
                return
            job.accept(reason="accepted by NERACA bureau")
        elif job.phase == ACPJobPhase.TRANSACTION:
            # funded: the deliverable IS a read of Sibyl Memory
            req = getattr(job, "service_requirement", None) or {}
            target = (req.get("counterparty") if isinstance(req, dict) else None) \
                or job.client_address
            budget = float((req.get("budget") if isinstance(req, dict) else 0) or 10)
            report = makelar.decide(target, budget) | {
                "evidence": makelar.evidence(target)[-5:]}
            job.deliver(json.dumps(report))
            print(f"job {job.id}: delivered risk report on {target}")

    acp = VirtualsACP(_contract_client("SELLER"), on_new_task=on_new_task)
    print(f"NERACA ACP seller live as {acp.wallet_address} — waiting for jobs")
    threading.Event().wait()  # socket callbacks drive everything


def buyer(provider: str, counterparty: str, budget: float) -> None:
    from virtuals_acp.client import VirtualsACP
    from virtuals_acp.fare import FareAmount

    acp = VirtualsACP(_contract_client("BUYER"), skip_socket_connection=True)
    job_id = acp.initiate_job(
        provider_address=provider,
        service_requirement={"counterparty": counterparty, "budget": budget},
        fare_amount=FareAmount(budget, _config().base_fare),
    )
    print(f"initiated ACP job {job_id} with provider {provider}")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "seller"
    if cmd == "seller":
        seller()
    elif cmd == "buyer":
        buyer(sys.argv[2], sys.argv[3], float(sys.argv[4]))
    else:
        raise SystemExit("usage: python -m neraca.acp [seller|buyer <provider> <counterparty> <budget>]")


if __name__ == "__main__":
    main()
