"""The bureau's front door: a counter ticket that prints what memory is worth.

GET /            the ticket, blank
GET /?addr=0x…   the same ticket, stamped with the memory-set quote for that
                 address — one real HTML form, no JavaScript, the page is
                 the receipt.

Every figure here is a read of Sibyl Memory; the on-chain receipts are the
transactions cited in the README.
"""

import html

from .brand import wordmark
from .memory import client, get_directory, job_events, norm, verdict_events

REPO = "https://github.com/PugarHuda/neraca"
BS = "https://sepolia.basescan.org/tx/"
RECEIPTS = (
    ("guarantee stake, USDC transfer(), memory-gated", "0x8dbebb9d014f63bdc283900b2df3910b8c8d48ece75b9dfe07c8fafd698be678", "1.00 USDC"),
    ("x402 settlement at a memory-set price, journaled", "0xb2c5915ac7c22f2236c97fec70f3e8d4945f2d6cbfa6ffdc9dbfb1a271878a07", "0.05 USDC"),
    ("x402 settlement against the public endpoint (aixbt)", "0x8f0beeb23cd67fec44f744358ad24023e7f49fcfd80a5e04db4bea6bfcc1a591", "0.02 USDC"),
    ("ERC-8004 identity: NERACA registered as agent #9215", "0x616df8a005aef6f4606eca64cb96bf974ce7cd04d861898b2358dcdad9a5d473", "register"),
    ("ERC-8004 feedback: verdict published on agent #9216", "0x7c920e2d96ebbc31993b9ee6437b8dc3915c7dda9ca6cfe15d1d8fe609a1615c", "score 52"),
)


def render(addr: str | None = None) -> str:
    from .server import BLIND_PRICE, PAY_TO, PER_EVENT, PRICE_CAP, quote

    e = html.escape
    m = client()
    jobs, verdicts = job_events(m), verdict_events(m)
    directory = get_directory(m)
    profiles = m.list_entities("agent", limit=500)
    serving = len(verdicts) + 1

    stamped = ""
    if addr:
        cp = norm(addr.strip())
        n = sum(1 for x in jobs if cp in (x["extra"]["client"], x["extra"]["provider"]))
        price = quote(cp, m)
        who = (directory.get(cp.lower()) or {}).get("name")
        known = f"<b>{e(who)}</b> &mdash; " if who else ""
        line = (f"{known}<b>{n}</b> remembered event{'s' if n != 1 else ''}. "
                if n else "<b>A stranger.</b> Nothing remembered; priced blind. ")
        stamped = (
            '<div class="answer">'
            f'<code class="addr">{e(cp)}</code>'
            f'<p>{line}The verdict costs <b class="price">${price:.2f}</b>.</p>'
            f'<p class="how">Buy it: <code>GET /risk/{e(cp)}?budget=50</code> &mdash; 402 until paid, USDC on Base Sepolia.</p>'
            f'<span class="stamp">{"quoted" if n else "blind"}</span>'
            '</div>')

    receipts = "".join(
        f'<tr><td>{e(what)}</td><td class="n">{e(amt)}</td>'
        f'<td><a href="{BS}{tx}"><code>{tx[:10]}&hellip;</code></a></td></tr>'
        for what, tx, amt in RECEIPTS)

    return PAGE.format(
        serving=serving, stamped=stamped, addr=e(addr or ""),
        jobs=len(jobs), verdicts=len(verdicts), agents=len(profiles), named=len(directory),
        blind=f"{BLIND_PRICE:.2f}", per=f"{PER_EVENT:.2f}", cap=f"{PRICE_CAP:.2f}",
        pay_to=e(PAY_TO), receipts=receipts, repo=REPO, brand=wordmark(30),
    )


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>NERACA</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="description" content="NERACA is a trust bureau for the agent economy: it remembers how agents behave on Base and sells memory-priced verdicts over x402, MCP and ERC-8004.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
:root{{--bone:#e9eedf;--ink:#1b1c17;--ink-2:#454a3e;--rule:#b3bda6;--canary:#efd45a;--canary-2:#e3c43a;--canary-ink:#5c4a0c;--ok:#2b5a37;--hold:#735616;--no:#b3301c;--none:#5f6457}}
*{{box-sizing:border-box}}html{{background:var(--bone);color:var(--ink)}}
body{{margin:0;font:17px/1.5 "Source Sans 3",system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
::selection{{background:var(--ink);color:var(--bone)}}
a{{color:inherit;text-decoration-thickness:1px;text-underline-offset:.18em}}
a:focus-visible,input:focus-visible,button:focus-visible{{outline:2px solid var(--ink);outline-offset:2px}}
code,.num,.ticket .no,td.n{{font-family:"Courier Prime",ui-monospace,monospace;font-variant-numeric:tabular-nums}}
.addr{{font-size:.8125rem;word-break:break-all;user-select:all}}
.page{{max-width:76rem;margin:0 auto;padding:1.5rem 1.25rem 4rem}}
.mast{{display:flex;justify-content:space-between;align-items:baseline;gap:1rem;flex-wrap:wrap;border-bottom:1px solid var(--ink);padding-bottom:.5rem;margin-bottom:2rem}}
.mast h1{{margin:0;font-size:1.4375rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase}}
.brand{{display:inline-flex;align-items:center;gap:.6rem}}.brand svg{{display:block}}
.mast nav a{{margin-left:1.25rem;font-size:.9375rem}}
.front{{display:grid;grid-template-columns:minmax(0,22rem) minmax(0,1fr);gap:3rem;align-items:start}}
.ticket{{background:var(--canary);color:var(--ink);padding:1.25rem 1.25rem 1.5rem;border:1px solid var(--canary-2);display:flex;flex-direction:column}}
.answer,.fine{{position:relative}}
.answer::before,.answer::after,.fine::before,.fine::after{{content:"";position:absolute;top:-8px;width:15px;height:15px;border-radius:50%;background:var(--bone);border:1px solid var(--canary-2)}}
.answer::before,.fine::before{{left:calc(-1.25rem - 8px)}}.answer::after,.fine::after{{right:calc(-1.25rem - 8px)}}
.ticket .answer + .fine{{border-top-style:solid}}.answer + .fine::before,.answer + .fine::after{{display:none}}
.ticket .head{{font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;font-weight:600;display:flex;justify-content:space-between;border-bottom:1px solid var(--ink);padding-bottom:.4rem}}
.ticket .serving{{margin:1rem 0 .25rem;font-variant:all-small-caps;letter-spacing:.04em;color:var(--canary-ink)}}
.ticket .no{{font-size:4.5rem;line-height:1;font-weight:700;margin:0 0 1rem;letter-spacing:-.02em}}
.ticket label{{display:block;font-variant:all-small-caps;letter-spacing:.04em;margin-bottom:.35rem}}
.ticket input{{width:100%;font:.9375rem/1.3 "Courier Prime",ui-monospace,monospace;padding:.5rem .6rem;border:1px solid var(--ink);background:#fff8cf;color:var(--ink)}}
.ticket input::placeholder{{color:var(--canary-ink)}}
.ticket button{{margin-top:.6rem;width:100%;font:600 .9375rem/1 "Source Sans 3",system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;padding:.7rem;border:1px solid var(--ink);background:var(--ink);color:var(--canary);cursor:pointer}}
.ticket button:hover{{background:#000}}.ticket button:active{{transform:translateY(1px)}}
.ticket .fine{{margin:1rem 0 0;padding-top:.6rem;font-size:.8125rem;color:var(--canary-ink);border-top:1px dashed var(--ink)}}
.answer{{position:relative;margin-top:1.1rem;border-top:1px dashed var(--ink);padding-top:.8rem}}
.answer .addr{{display:block;padding-right:6.5rem}}.answer p{{margin:.4rem 0 0}}.answer .how{{font-size:.875rem;color:var(--canary-ink)}}.answer .how code{{word-break:break-all}}
.price{{font-family:"Courier Prime",monospace;font-size:1.5rem}}
.stamp{{position:absolute;right:.25rem;top:.7rem;transform:rotate(-8deg);font-weight:600;font-size:.6875rem;letter-spacing:.14em;text-transform:uppercase;padding:.25rem .5rem;border:1px solid currentColor;box-shadow:inset 0 0 0 2px var(--canary),inset 0 0 0 3px currentColor;mix-blend-mode:multiply}}
.hold{{color:var(--hold)}}.none{{color:var(--none)}}
.thesis{{font-size:1.75rem;line-height:1.3;margin:0 0 1.5rem}}
.thesis em{{font-style:italic}}
.lede{{max-width:62ch;margin:0 0 2rem;color:var(--ink-2)}}
.counters{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}}
.counter{{background:var(--bone);padding:1rem}}
.counter h2{{margin:0 0 .5rem;font-size:.8125rem;letter-spacing:.12em;text-transform:uppercase;font-weight:600;display:flex;gap:.75rem;align-items:baseline}}
.counter h2 code{{font-size:.75rem;color:var(--ink-2)}}
.counter p{{margin:0 0 .5rem;font-size:.9375rem}}
.counter pre{{margin:0;font:.8125rem/1.45 "Courier Prime",ui-monospace,monospace;white-space:pre-wrap;word-break:break-word;border-top:1px solid var(--rule);padding-top:.5rem}}
h3{{font-size:.875rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;margin:3rem 0 .75rem;padding-bottom:.35rem;border-bottom:1px solid var(--ink);display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap}}
h3 span{{font-weight:400;letter-spacing:.02em;text-transform:none;color:var(--ink-2)}}
table{{width:100%;border-collapse:collapse;font-size:.9375rem;border:1px solid var(--rule)}}
th{{text-align:left;font-variant:all-small-caps;letter-spacing:.04em;font-weight:600;color:var(--ink-2);padding:.45rem .75rem;border-bottom:1px solid var(--ink)}}
th.n,td.n{{text-align:right;white-space:nowrap}}
th:first-child{{width:100%}}td:last-child{{white-space:nowrap}}
td{{padding:.5rem .75rem;border-bottom:1px solid var(--rule);vertical-align:top}}tr:last-child td{{border-bottom:0}}
.board{{overflow-x:auto}}
.figures{{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--rule);margin-top:.75rem}}
.figures div{{padding:.5rem .75rem;display:flex;justify-content:space-between;gap:.75rem;border-right:1px solid var(--rule)}}
.figures div:first-child{{padding-left:0}}.figures div:last-child{{border-right:0}}
.figures span{{font-variant:all-small-caps;letter-spacing:.04em;color:var(--ink-2)}}.figures b{{font-family:"Courier Prime",monospace;font-weight:700}}
footer{{margin-top:3rem;padding-top:.75rem;border-top:1px solid var(--ink);font-size:.875rem;color:var(--ink-2);display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap}}
@media (min-width:60.01rem){{.front{{align-items:stretch;min-height:calc(100vh - 7.5rem);grid-template-columns:minmax(0,24rem) minmax(0,1fr)}}.ticket .fine{{margin-top:auto}}.thesis span{{display:block}}}}
@media (max-width:60rem){{table{{min-width:34rem}}.front{{grid-template-columns:1fr}}.counters{{grid-template-columns:1fr}}.figures{{grid-template-columns:1fr 1fr}}.figures div:nth-child(2){{border-right:0}}.figures div:nth-child(3){{padding-left:0}}.thesis{{font-size:1.5rem}}}}
</style></head><body><div class="page">
<header class="mast"><h1>{brand}</h1><nav><a href="/registry">Registry</a><a href="{repo}">Source</a></nav></header>

<div class="front">
<form class="ticket" method="get" action="/">
  <div class="head"><span>Trust bureau</span><span>quote ticket</span></div>
  <p class="serving">now serving</p>
  <p class="no">{serving:04d}</p>
  <label for="addr">Who are you about to deal with?</label>
  <input id="addr" name="addr" value="{addr}" placeholder="0x… agent address on Base" autocomplete="off" spellcheck="false" required>
  <button type="submit">Ask the tariff</button>
  {stamped}
  <p class="fine">A verdict costs what the memory behind it is worth: ${blind} for a stranger, +${per} per remembered event, cap ${cap}. Paid in USDC on Base Sepolia to <code class="addr">{pay_to}</code>.</p>
</form>

<div>
<p class="thesis"><span>Agents hire each other now.</span> <span>Nothing remembers who burned whom.</span> <span><em>This bureau does.</em></span></p>
<p class="lede">Three agents share nothing but memory. One watches real jobs on Base. One turns what it saw into a balance for every address. One sells the verdict &mdash; and stakes USDC behind the ones it guarantees. Ask about a stranger and you pay a cent; ask about someone the bureau knows and you pay for what it knows.</p>
<div class="counters">
  <section class="counter"><h2><code>01</code> x402</h2><p>Pay per answer. A 402 quotes the memory-set price; settle in USDC and the verdict comes back with its evidence.</p><pre>GET /quote/&lt;addr&gt;
GET /risk/&lt;addr&gt;?budget=50</pre></section>
  <section class="counter"><h2><code>02</code> MCP</h2><p>Give your own agent the bureau as tools: ask, quote, report, search.</p><pre>claude mcp add neraca -- \\
  python -m neraca.mcp_server</pre></section>
  <section class="counter"><h2><code>03</code> ERC-8004</h2><p>Verdicts leave the bureau as portable reputation: NERACA is agent #9215 on the Base Sepolia registries and publishes feedback on the agents it remembers.</p><pre>python -m neraca.onchain \\
  feedback &lt;agentId&gt;</pre></section>
</div>
</div>
</div>

<h3>Receipts <span>every one a transaction you can open</span></h3>
<div class="board"><table><thead><tr><th>what</th><th class="n">amount</th><th>transaction</th></tr></thead><tbody>{receipts}</tbody></table></div>

<h3>On file today <span>read from memory as this page rendered</span></h3>
<div class="figures">
<div><span>journal entries</span><b>{jobs}</b></div>
<div><span>verdicts given</span><b>{verdicts}</b></div>
<div><span>agents on file</span><b>{agents}</b></div>
<div><span>names known</span><b>{named}</b></div>
</div>

<footer><span>Delete the memory and the bureau does not degrade. It exits.</span><span><a href="/registry">Open the registry</a> &middot; <a href="{repo}">Read the code</a></span></footer>
</div></body></html>"""
