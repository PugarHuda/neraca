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


@app.get("/favicon.svg")
def favicon_svg():
    from .brand import FAVICON
    return Response(FAVICON, media_type="image/svg+xml")


@app.get("/logo.svg")
def logo_svg():
    from .brand import LOGO
    return Response(LOGO, media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse)
def front(addr: str | None = None):
    """The front door: a counter ticket that prints what memory is worth."""
    from . import landing
    return landing.render(addr)


@app.get("/registry", response_class=HTMLResponse)
def home():
    """The bureau's registry, rendered straight from memory. No JS, nothing cached."""
    from datetime import datetime, timezone

    from .brand import wordmark
    from .memory import get_directory, get_rubric
    m = client()
    rubric = get_rubric(m)
    jobs, settles, verdicts = job_events(m), settlement_events(m), verdict_events(m)
    directory = get_directory(m)
    agents = sorted(m.list_entities("agent", limit=200), key=lambda a: a["body"]["score"])
    e = html.escape

    def verdict_for(score: int) -> str:
        if score >= rubric["approve_threshold"]:
            return "APPROVE"
        if score >= rubric["guarantee_threshold"]:
            return "APPROVE_WITH_GUARANTEE"
        return "DECLINE"

    def tone(verdict: str) -> str:
        return {"APPROVE": "ok", "APPROVE_WITH_GUARANTEE": "hold", "DECLINE": "no"}.get(verdict, "none")

    def card(a) -> str:
        b, addr = a["body"], a["name"]
        v = verdict_for(b["score"])
        who = (directory.get(addr.lower()) or {}).get("name")
        last = (b.get("last_seen") or "")[:10]
        why = b["score_history"][-1]["why"] if b["score_history"] else "clean but thin history"
        sim = '<span class="sim">simulated</span>' if "sim-" in why or addr.startswith("0xKLIEN") or addr.startswith("0xNERACA") else ""
        name = e(who) if who else f'<span class="short">{e(addr[:6])}&hellip;{e(addr[-4:])}</span>'
        return (
            '<article class="card">'
            f'<header><h3>{name}</h3><code class="addr">{e(addr)}</code></header>'
            '<dl>'
            f'<div><dt>jobs completed</dt><dd>{b["jobs_ok"]}</dd></div>'
            f'<div><dt>disputes raised</dt><dd>{b["disputes_initiated"]}</dd></div>'
            f'<div><dt>invoices paid</dt><dd>{b["invoices_paid"]}</dd></div>'
            f'<div><dt>last entry</dt><dd>{e(last) or "&mdash;"}</dd></div>'
            '</dl>'
            f'<p class="why">{e(why)}{sim}</p>'
            f'<div class="balance"><span>balance</span><strong>{b["score"]}</strong></div>'
            f'<span class="stamp {tone(v)}">{e(v.replace("_", " "))}</span>'
            '</article>'
        )

    cards = "".join(card(a) for a in agents) or (
        '<p class="empty">The registry is empty. Journal something first: '
        '<code>python -m neraca seed</code>, then <code>python -m neraca analis</code>.</p>')

    def vrow(v) -> str:
        x = v["extra"]
        who = (directory.get((x["counterparty"] or "").lower()) or {}).get("name")
        named = f"<i>{e(who)}</i>" if who else ""
        if (x["counterparty"] or "").startswith(("0xKLIEN", "0xNERACA")):
            named += '<span class="sim">simulated</span>'
        score = "&mdash;" if x["score"] is None else x["score"]
        cp = x["counterparty"] or ""
        short = cp if len(cp) <= 18 else f"{cp[:8]}&hellip;{cp[-6:]}"
        return (f'<tr class="{tone(x["verdict"])}"><td>{e(v["ts"][:16].replace("T", " "))}</td>'
                f'<td class="v">{e(x["verdict"].replace("_", " "))}</td>'
                f'<td><code class="addr" title="{e(cp)}">{short}</code>{named}</td>'
                f'<td class="n">{score}</td><td class="n">{x["counter_budget"]}</td></tr>')

    def srow(s_) -> str:
        x = s_["extra"]
        return (f'<tr><td>{e(s_["ts"][:16].replace("T", " "))}</td><td><code class="addr">{e(x["payer"])}</code></td>'
                f'<td class="n">${x["amount_usd"]:.2f}</td>'
                f'<td><a href="https://sepolia.basescan.org/tx/{e(x["tx"])}"><code>{e(x["tx"][:10])}&hellip;</code></a></td></tr>')

    verdict_rows = "".join(vrow(v) for v in reversed(verdicts[-12:])) or (
        '<tr><td colspan="5" class="empty">No verdicts yet &mdash; '
        '<code>python -m neraca ask &lt;addr&gt; --budget 50</code>.</td></tr>')
    settle_rows = "".join(srow(s_) for s_ in reversed(settles[-8:])) or (
        '<tr><td colspan="4" class="empty">No invoices settled yet &mdash; '
        'the storefront journals each one it sees paid.</td></tr>')
    note = os.environ.get("NERACA_DEPLOYMENT_NOTE")
    slip = f'<aside class="slip" id="deployment-note">{e(note)}</aside>' if note else ""
    today = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    return PAGE.format(
        today=today, jobs=len(jobs), settles=len(settles), verdicts=len(verdicts), agents=len(agents),
        version=rubric.get("version", 1), cards=cards, verdict_rows=verdict_rows, settle_rows=settle_rows,
        slip=slip, blind=f"{BLIND_PRICE:.2f}", per=f"{PER_EVENT:.2f}", cap=f"{PRICE_CAP:.2f}", pay_to=e(PAY_TO),
        brand=wordmark(30),
    )


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>NERACA &mdash; registry</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
:root{{--bone:#e9eedf;--ink:#1b1c17;--ink-2:#454a3e;--rule:#b3bda6;--ok:#2b5a37;--hold:#735616;--no:#b3301c;--none:#5f6457}}
*{{box-sizing:border-box}}html{{background:var(--bone);color:var(--ink)}}
body{{margin:0;font:16px/1.45 "Source Sans 3",system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
::selection{{background:var(--ink);color:var(--bone)}}
a{{color:inherit;text-decoration-thickness:1px;text-underline-offset:.18em}}
a:focus-visible{{outline:1px solid var(--ink);outline-offset:2px}}
code,dd,.balance strong,td.n,.totals b,.mast time{{font-family:"Courier Prime",ui-monospace,monospace;font-variant-numeric:tabular-nums}}
.addr{{font-size:.8125rem;word-break:break-all;user-select:all}}
.page{{max-width:76rem;margin:0 auto;padding:1.5rem 1.25rem 4rem}}
.mast{{display:flex;justify-content:space-between;align-items:baseline;gap:1rem;flex-wrap:wrap;border-bottom:1px solid var(--ink);padding-bottom:.5rem}}
.mast h1{{margin:0;font-size:1.4375rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase}}
.mast h1 small{{font-weight:400;font-size:.9375rem;letter-spacing:.02em;text-transform:none;color:var(--ink-2);margin-left:.75rem}}
.brand{{display:inline-flex;align-items:center;gap:.6rem}}.brand svg{{display:block}}
.mast time{{font-size:.875rem;color:var(--ink-2)}}
.mast nav{{font-size:.9375rem;color:var(--ink-2)}}
.totals{{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--rule);margin:0 0 2rem}}
.totals div{{padding:.5rem .75rem;display:flex;justify-content:space-between;gap:.75rem;border-right:1px solid var(--rule)}}
.totals div:first-child{{padding-left:0}}.totals div:last-child{{border-right:0}}
.totals span{{font-variant:all-small-caps;letter-spacing:.06em;color:var(--ink-2)}}
.totals b{{font-weight:700}}
h2{{font-size:.875rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;margin:2.5rem 0 .75rem;padding-bottom:.35rem;border-bottom:1px solid var(--ink);display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap}}
h2 span{{font-weight:400;letter-spacing:.02em;text-transform:none;color:var(--ink-2);text-align:right}}
main>h2:first-child{{margin-top:0}}
.registry{{display:grid;grid-template-columns:repeat(auto-fill,minmax(19rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}}
.card{{background:var(--bone);padding:1rem 1rem 1.1rem;display:grid;grid-template-columns:minmax(0,1fr) 8.5rem;grid-template-areas:"head head" "list balance" "why stamp";column-gap:1rem;row-gap:.5rem}}
.card header{{grid-area:head;margin-bottom:.6rem}}
.card h3{{margin:0;font-size:1.125rem;font-weight:600}}
.card h3 .short{{font-family:"Courier Prime",ui-monospace,monospace;font-weight:700;letter-spacing:0}}
.card dl{{grid-area:list;margin:0}}
.card dl div{{display:flex;justify-content:space-between;align-items:baseline;line-height:1.35rem;padding:.12rem 0 .18rem;border-bottom:1px solid var(--rule)}}
.card dt{{font-variant:all-small-caps;letter-spacing:.05em;color:var(--ink-2)}}
.card dd{{margin:0}}
.card .why{{grid-area:why;margin:.1rem 0 0;font-size:.875rem;font-style:italic;color:var(--ink-2);align-self:end}}
.balance{{grid-area:balance;display:flex;flex-direction:column;align-items:flex-end;border-left:1px solid var(--rule);padding-left:1rem;min-width:5.5rem}}
.balance span{{font-variant:all-small-caps;letter-spacing:.06em;color:var(--ink-2)}}
.balance strong{{font-size:2.25rem;line-height:1;font-weight:700}}
.stamp{{grid-area:stamp;justify-self:end;align-self:end;margin:.35rem .25rem 0 0;transform:rotate(-6deg);white-space:normal;text-align:center;max-width:100%;line-height:1.3;font-weight:600;font-size:.6875rem;letter-spacing:.14em;text-transform:uppercase;padding:.25rem .5rem;border:1px solid currentColor;box-shadow:inset 0 0 0 2px var(--bone),inset 0 0 0 3px currentColor;mix-blend-mode:multiply}}
.ok{{color:var(--ok)}}.hold{{color:var(--hold)}}.no{{color:var(--no)}}.none{{color:var(--none)}}
table{{width:100%;border-collapse:collapse;font-size:.9375rem}}
.board{{overflow-x:auto}}
table{{border:1px solid var(--rule)}}
th{{text-align:left;font-variant:all-small-caps;letter-spacing:.06em;font-weight:600;color:var(--ink-2);padding:.45rem .75rem;border-bottom:1px solid var(--ink);white-space:nowrap}}
th.n{{text-align:right}}
td{{padding:.5rem .75rem;border-bottom:1px solid var(--rule);vertical-align:top}}
td:first-child{{white-space:nowrap}}td .addr{{word-break:normal;white-space:nowrap;font-size:.8125rem}}
tr:last-child td{{border-bottom:0}}
td.n{{text-align:right;white-space:nowrap}}td.v{{font-weight:600;letter-spacing:.04em;white-space:nowrap}}
tr.no td{{color:var(--no)}}tr.no td.v{{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.2em}}
tr.ok td.v{{color:var(--ok)}}tr.hold td.v{{color:var(--hold)}}tr.none td{{color:var(--none)}}
td i{{display:block;font-style:normal;font-weight:600;font-size:.875rem}}
.empty{{color:var(--ink-2);font-style:italic}}
.margin{{display:grid;grid-template-columns:minmax(0,1fr) 17rem;gap:2.5rem;align-items:start}}
.margin>main,.margin>aside{{min-width:0}}
.margin>aside{{padding-top:1.6rem}}
.slip,.tariff{{font-size:.875rem;color:var(--ink-2);border-top:1px solid var(--ink);padding-top:.5rem;margin-bottom:1.5rem}}
.sim{{font-variant:all-small-caps;letter-spacing:.06em;color:var(--none);margin-left:.4rem}}
.tariff dl{{margin:.5rem 0 0}}.tariff dt{{font-variant:all-small-caps;letter-spacing:.05em}}.tariff dd{{margin:0 0 .5rem;font-family:inherit}}
td.empty{{white-space:normal}}
@media (max-width:52rem){{.margin{{grid-template-columns:1fr}}.card{{grid-template-columns:minmax(0,1fr) 7.5rem}}.card .addr{{font-size:.72rem}}.totals{{grid-template-columns:1fr 1fr}}.totals div:nth-child(2){{border-right:0}}.totals div:nth-child(3){{padding-left:0}}}}
</style></head><body><div class="page">
<header class="mast"><h1>{brand}<small>registry</small></h1><nav><a href="/">Counter</a> &middot; <time datetime="{today}">{today}</time></nav></header>
<div class="totals" id="summary">
<div><span>journal entries</span><b id="jobs">{jobs}</b></div>
<div><span>invoices settled</span><b id="settlements">{settles}</b></div>
<div><span>verdicts given</span><b id="verdicts">{verdicts}</b></div>
<div><span>agents on file</span><b id="agents">{agents}</b></div>
</div>
<div class="margin">
<main>
<h2>Daybook <span>latest verdicts, newest first</span></h2>
<div class="board"><table id="verdict-log"><thead><tr><th>entered</th><th>verdict</th><th>counterparty</th><th class="n">balance</th><th class="n">counter USDC</th></tr></thead><tbody>{verdict_rows}</tbody></table></div>
<h2>Registry <span>worst balance first &middot; stamped under rubric v{version}</span></h2>
<section class="registry" id="profiles">{cards}</section>
<h2>Receipts <span>invoices the storefront saw paid</span></h2>
<div class="board"><table id="settlement-log"><thead><tr><th>settled</th><th>payer</th><th class="n">paid</th><th>transaction</th></tr></thead><tbody>{settle_rows}</tbody></table></div>
</main>
<aside>
{slip}
<div class="tariff"><b>Tariff.</b> A risk report costs what the memory behind it is worth.
<dl><dt>blind</dt><dd>${blind} &mdash; nothing remembered</dd><dt>per remembered event</dt><dd>+${per}, cap ${cap}</dd><dt>ask</dt><dd><code>GET /quote/&lt;address&gt;</code> free &middot; <code>GET /risk/&lt;address&gt;?budget=50</code> 402 until paid, USDC on Base Sepolia to <code class="addr">{pay_to}</code></dd></dl>
</div>
</aside>
</div>
</div></body></html>"""


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
