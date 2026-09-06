"""MAKELAR's storefront #1: x402-paywalled risk reports on Base Sepolia.

GET /risk/{counterparty}?budget=50 → 402 until paid (test USDC via the
x402.org facilitator), then the memory-backed decision. The paid answer is
literally a read of Sibyl Memory — no memory, nothing to sell.

Run: uvicorn neraca.server:app --port 8402
"""

import json
import os

from fastapi import FastAPI
from x402.http import HTTPFacilitatorClient
from x402.http.middleware.fastapi import payment_middleware
from x402.mechanisms.evm.exact import register_exact_evm_server
from x402.server import x402ResourceServer

from . import makelar
from .memory import client

PAY_TO = os.environ.get("NERACA_PAY_TO", "0x0000000000000000000000000000000000000000")
PRICE = os.environ.get("NERACA_RISK_PRICE", "$0.05")
NETWORK = "eip155:84532"  # Base Sepolia

app = FastAPI(title="NERACA risk bureau")

routes = {
    "GET /risk/*": {
        "accepts": {
            "scheme": "exact",
            "payTo": PAY_TO,
            "price": PRICE,
            "network": NETWORK,
        },
        "description": "Memory-backed counterparty risk decision",
    }
}

server = register_exact_evm_server(x402ResourceServer(HTTPFacilitatorClient()))
_middleware = payment_middleware(routes, server)


@app.middleware("http")
async def x402_paywall(request, call_next):
    return await _middleware(request, call_next)


@app.get("/risk/{counterparty}")
def risk(counterparty: str, budget: float = 10.0):
    m = client()
    return makelar.decide(counterparty, budget, m) | {
        "evidence": makelar.evidence(counterparty, m)[-5:],
    }


@app.get("/health")
def health():
    return {"ok": True, "pay_to": PAY_TO, "network": NETWORK}


async def pay(url: str) -> None:
    """Buyer side of the demo: walk the 402 and print the paid answer.

    Needs NERACA_BUYER_KEY (a Base Sepolia key holding test USDC). Print the
    address first with no key set, then faucet it from the CDP wallet run.
    """
    from eth_account import Account
    from x402.client import x402Client
    from x402.http.clients.httpx import x402HttpxClient
    from x402.mechanisms.evm import EthAccountSigner
    from x402.mechanisms.evm.exact import register_exact_evm_client

    key = os.environ.get("NERACA_BUYER_KEY")
    if not key:
        raise SystemExit("set NERACA_BUYER_KEY to a Base Sepolia key with test USDC "
                         "(`python -m neraca.onchain wallet` faucets one)")
    account = Account.from_key(key)
    print(f"buyer {account.address} paying {PRICE} for {url}")
    client = register_exact_evm_client(x402Client(), EthAccountSigner(account))
    async with x402HttpxClient(client) as http:
        r = await http.get(url)
        if r.status_code == 402:
            raise SystemExit(f"payment not settled — is {account.address} funded with "
                             f"Base Sepolia test USDC? server said: {r.text[:200]}")
        r.raise_for_status()
        receipt = r.headers.get("x-payment-response") or r.headers.get("payment-response")
        print(json.dumps({"paid": True, "payment_response": receipt,
                          "answer": r.json()}, indent=2))


if __name__ == "__main__":
    import asyncio
    import sys
    asyncio.run(pay(sys.argv[1] if len(sys.argv) > 1
                    else "http://127.0.0.1:8402/risk/0xKLIENB000000000000000000000000000000000B?budget=50"))
