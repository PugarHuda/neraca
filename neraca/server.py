"""MAKELAR's storefront #1: x402-paywalled risk reports on Base Sepolia.

GET /risk/{counterparty}?budget=50 → 402 until paid (test USDC via the
x402.org facilitator), then the memory-backed decision. The paid answer is
literally a read of Sibyl Memory — no memory, nothing to sell.

Run: uvicorn neraca.server:app --port 8402
"""

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
