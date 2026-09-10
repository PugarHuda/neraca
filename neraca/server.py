"""MAKELAR's storefront #1: x402-paywalled risk reports on Base Sepolia.

GET /risk/{counterparty}?budget=50 → 402 until paid (test USDC via the
x402.org facilitator), then the memory-backed decision. Memory runs the whole
storefront, not just the answer:

- the price is set by memory: a counterparty NERACA has never seen is priced
  blind and cheap, and every remembered event about them adds a cent;
- every settlement is journaled as an observation — an agent that pays its
  invoices has told the bureau something about itself;
- the paid answer is literally a read of Sibyl Memory. No memory, nothing to
  sell.

GET / is a plain status page rendered straight from memory.

Run: uvicorn neraca.server:app --port 8402
"""

import base64
import html
import json
import os

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from x402.extensions.bazaar import declare_discovery_extension
from x402.http import HTTPFacilitatorClient
from x402.http.middleware.fastapi import payment_middleware
from x402.http.types import HTTPRequestContext
from x402.mechanisms.evm.exact import register_exact_evm_server
from x402.server import x402ResourceServer

from . import makelar
from .memory import (client, job_events, norm, record_settlement, settlement_events,
                     verdict_events)

PAY_TO = os.environ.get("NERACA_PAY_TO", "0x0000000000000000000000000000000000000000")
NETWORK = "eip155:84532"  # Base Sepolia
BLIND_PRICE = 0.01        # USD: nothing remembered, priced blind
PER_EVENT = 0.01          # USD per remembered event about the counterparty
PRICE_CAP = 0.25

app = FastAPI(title="NERACA risk bureau")


def quote(counterparty: str, m=None) -> float:
    """What an answer costs is set by how much memory stands behind it."""
    m = m or client()
    counterparty = norm(counterparty)
    n = sum(1 for e in job_events(m) if counterparty in (e["extra"]["client"], e["extra"]["provider"]))
    return round(min(BLIND_PRICE + PER_EVENT * n, PRICE_CAP), 2)


def _counterparty(path: str) -> str:
    return norm(path.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1])


def price_by_memory(ctx: HTTPRequestContext) -> str:
    return f"${quote(_counterparty(ctx.path)):.2f}"


# x402 Bazaar: the facilitator indexes endpoints that declare themselves, so
# any x402 client can discover the bureau without being told about it.
_discovery = declare_discovery_extension(
    input={"budget": "50"},
    input_schema={"properties": {"budget": {"type": "string", "description": "USDC you intend to put at risk"}},
                  "required": []},
    path_params_schema={"properties": {"counterparty": {"type": "string", "description": "EVM address of the agent you are about to deal with"}},
                        "required": ["counterparty"]},
)

routes = {
    "GET /risk/*": {
        "accepts": {
            "scheme": "exact",
            "payTo": PAY_TO,
            "price": price_by_memory,
            "network": NETWORK,
        },
        "description": "Memory-backed counterparty risk decision, priced by memory",
        "extensions": _discovery,
    }
}

server = register_exact_evm_server(x402ResourceServer(HTTPFacilitatorClient()))
_middleware = payment_middleware(routes, server)


@app.middleware("http")
async def x402_paywall(request: Request, call_next):
    response = await _middleware(request, call_next)
    raw = response.headers.get("payment-response")
    if raw:  # settled: PENGAMAT's storefront eyes journal who paid
        try:
            receipt = json.loads(base64.b64decode(raw))
            if receipt.get("success") and receipt.get("transaction"):
                record_settlement(client(), payer=receipt["payer"], payee=PAY_TO,
                                  amount_usd=quote(_counterparty(request.url.path)),
                                  tx=receipt["transaction"], resource=request.url.path)
        except Exception as e:  # a bad receipt must not cost the buyer their answer
            print(f"settlement journal error: {e}")
    return response


@app.api_route("/risk/{counterparty}", methods=["GET", "HEAD"])  # the SDK paywall probes with HEAD
def risk(counterparty: str, budget: float = 10.0):
    m = client()
    return makelar.decide(counterparty, budget, m) | {
        "evidence": makelar.evidence(counterparty, m)[-5:],
    }


@app.get("/quote/{counterparty}")
def quote_endpoint(counterparty: str):
    """Free: what the answer would cost, and why."""
    m = client()
    counterparty = norm(counterparty)
    n = sum(1 for e in job_events(m) if counterparty in (e["extra"]["client"], e["extra"]["provider"]))
    return {"counterparty": counterparty, "remembered_events": n, "price_usd": quote(counterparty, m),
            "policy": f"${BLIND_PRICE:.2f} blind + ${PER_EVENT:.2f} per remembered event, cap ${PRICE_CAP:.2f}"}


@app.get("/health")
def health():
    return {"ok": True, "pay_to": PAY_TO, "network": NETWORK}


@app.get("/favicon.ico", status_code=204)
def favicon():
    return Response(status_code=204)  # keeps the browser console clean on the status page


@app.get("/", response_class=HTMLResponse)
def home():
    """Status page, rendered straight from memory. No JS, nothing cached."""
    m = client()
    jobs, settles, verdicts = job_events(m), settlement_events(m), verdict_events(m)
    agents = sorted(m.list_entities("agent", limit=200), key=lambda a: a["body"]["score"])
    e = html.escape

    def row(cells):
        return "<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in cells) + "</tr>"

    agent_rows = "".join(row((a["body"]["score"], a["name"], a["body"]["jobs_ok"],
                              a["body"]["disputes_initiated"], a["body"]["invoices_paid"]))
                         for a in agents)
    verdict_rows = "".join(row((v["ts"][:19], v["extra"]["verdict"], v["extra"]["counterparty"],
                                v["extra"]["score"], v["extra"]["counter_budget"]))
                           for v in reversed(verdicts[-10:]))
    settle_rows = "".join(row((s["ts"][:19], s["extra"]["payer"], f"${s['extra']['amount_usd']}",
                               s["extra"]["tx"][:18] + "…")) for s in reversed(settles[-10:]))
    note = os.environ.get("NERACA_DEPLOYMENT_NOTE")
    banner = f'<p id="deployment-note"><i>{e(note)}</i></p>' if note else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>NERACA</title>
<style>body{{font:14px/1.4 system-ui,sans-serif;margin:2rem;max-width:72rem}}
table{{border-collapse:collapse;margin:.5rem 0 1.5rem}}td,th{{border:1px solid #ccc;padding:.25rem .6rem;text-align:left}}
code{{background:#eee;padding:0 .3rem}}</style></head><body>
<h1>NERACA — trust bureau</h1>{banner}
<p id="summary">Journal: <b id="jobs">{len(jobs)}</b> job observations,
<b id="settlements">{len(settles)}</b> settlements, <b id="verdicts">{len(verdicts)}</b> verdicts.
Profiles: <b id="agents">{len(agents)}</b>. Pay to <code>{e(PAY_TO)}</code> on {e(NETWORK)}.</p>
<p>Price policy: ${BLIND_PRICE:.2f} blind + ${PER_EVENT:.2f} per remembered event, cap ${PRICE_CAP:.2f}.
Try <code>GET /quote/&lt;address&gt;</code>, then <code>GET /risk/&lt;address&gt;?budget=50</code> (402 until paid).</p>
<h2>Reputation profiles (WARM)</h2>
<table id="profiles"><tr><th>score</th><th>agent</th><th>jobs ok</th><th>disputes</th><th>invoices paid</th></tr>{agent_rows}</table>
<h2>Latest verdicts (COLD)</h2>
<table id="verdict-log"><tr><th>when</th><th>verdict</th><th>counterparty</th><th>score</th><th>counter</th></tr>{verdict_rows}</table>
<h2>Settlements witnessed (COLD)</h2>
<table id="settlement-log"><tr><th>when</th><th>payer</th><th>paid</th><th>tx</th></tr>{settle_rows}</table>
</body></html>"""


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
    print(f"buyer {account.address} walking the 402 at {url}")
    client_ = register_exact_evm_client(x402Client(), EthAccountSigner(account))
    async with x402HttpxClient(client_) as http:
        r = await http.get(url)
        if r.status_code == 402:
            raise SystemExit(f"payment not settled - is {account.address} funded with "
                             f"Base Sepolia test USDC? server said: {r.text[:200]}")
        r.raise_for_status()
        raw = r.headers.get("x-payment-response") or r.headers.get("payment-response")
        receipt = json.loads(base64.b64decode(raw)) if raw else None
        if receipt and receipt.get("transaction"):
            receipt["explorer"] = "https://sepolia.basescan.org/tx/" + receipt["transaction"]
        print(json.dumps({"paid": True, "receipt": receipt, "answer": r.json()}, indent=2))


if __name__ == "__main__":
    import asyncio
    import sys
    asyncio.run(pay(sys.argv[1] if len(sys.argv) > 1
                    else "http://127.0.0.1:8402/risk/0xKLIENB000000000000000000000000000000000B?budget=50"))
