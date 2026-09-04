# NERACA — Design Spec

**Date:** 2026-09-04 · **Event:** Sibyl Labs Hackathon (submission due 2026-09-10 23:59 UTC)

NERACA (Indonesian: "balance scale / ledger") is a trust bureau for the agent
economy. It watches agents transact on Virtuals ACP (on Base), distills what it
sees into evolving reputation profiles inside Sibyl Memory, and sells
risk-priced trust decisions. Its entire value **is** its memory: delete the
Sibyl layer and there is no bureau.

## 1. Problem & impact

ACP's own graduation mechanism (10 successful jobs before production) exists
because agents can't tell who to trust. Humans have credit bureaus; agents
don't. NERACA is that bureau: before hiring an agent, ask NERACA and get a
memory-backed verdict — approve, decline, or counter with adjusted budget and
a guarantee premium.

## 2. Goals / non-goals

**Goals**
- Pass the gate: memory load-bearing by construction, cold-start recall demo.
- Top band of the 40-pt memory criterion: 3 agents coordinating through one
  shared Sibyl Memory; all five tiers used meaningfully; scores that evolve.
- Both partner multipliers doing real product work: x402 payment, CDP wallet
  operation, registered/transacting ACP agent (×1.25).
- Re-runnable by a judge from README in one attempt.

**Non-goals (deliberate, YAGNI)**
- No web UI (CLI demo; easier for judges to re-run).
- No token, no ML scoring (deterministic rubric is auditable).
- No mainnet spend beyond optional free reads (registry / B20 `eth_call`).
- No PMF-bonus chase unless verifiable evidence materializes for free.

## 3. Architecture

Three small Python processes coordinating **only** through one shared Sibyl
Memory database (`MemoryClient.local(...)`, single tenant). No queues, no IPC —
the memory layer *is* the bus, which is the point.

```
PENGAMAT (scout)   -> COLD  write_event()      raw observations: ACP job created/funded/
                                               delivered/rejected, per counterparty
ANALIS  (analyst)  -> WARM  set_entity("agent", <addr>, profile)   evolving profiles
                   -> ARCHIVE archive_entity() agents inactive > N days
                   <- REFERENCE get_reference("scoring-rubric")    deterministic rules
MAKELAR (broker)   <- WARM/COLD reads          decisions
                   -> HOT  set_state()         in-flight negotiation state
```

### 3.1 Memory schema (Sibyl tiers)

| Tier | Key shape | Content |
|---|---|---|
| COLD | event journal | `{kind: "acp_job", phase, client, provider, budget, outcome, tx, ts}` |
| WARM | `("agent", <address>)` | `{name, jobs_ok, jobs_failed, disputes, avg_budget, last_seen, score, score_history[]}` |
| REFERENCE | `"scoring-rubric"` | weights + thresholds the analyst applies (single source of truth) |
| HOT | `"negotiation:<job_id>"` | current offer, counter, guarantee premium |
| ARCHIVE | retired `("agent", ...)` | agents with no activity in the window |

Score is recomputed by ANALIS from COLD events using the REFERENCE rubric —
never stored ad hoc — so the demo can show the same question getting a
*different answer* after one new adverse event lands in the journal.

### 3.2 Components

**PENGAMAT** (`neraca/pengamat.py`)
- Source A (primary): our own two ACP sandbox agents (see §4.2) whose real
  on-chain jobs it observes via `virtuals-acp` events / job listing.
- Source B (garnish, read-only): ERC-8004 identity registry read on Base
  mainnet via public RPC `eth_call` (free, no wallet) to enrich profiles.
- Idempotent: event carries `(job_id, phase)`; re-observing writes nothing new.

**ANALIS** (`neraca/analis.py`)
- Replays unprocessed COLD events → updates WARM entities → appends to
  `score_history`. Archives stale agents. Pure function of (events, rubric):
  same inputs, same scores — this is what survives "a second run and a
  curious judge".

**MAKELAR** (`neraca/makelar.py`)
- `decide(agent_addr, proposed_budget) -> {verdict, counter_budget, premium, reasons[]}`
  reading WARM + COLD; reasons cite the exact remembered events (pitch gold).
- Sells the decision three ways, each a partner trigger doing product work:
  1. **x402 paid endpoint** (Base Sepolia, test USDC): `GET /risk/<addr>`
     behind a 402 paywall.
  2. **ACP provider**: registered sandbox agent offering "risk report";
     serves jobs via the v2 lifecycle (fund → submit → complete).
  3. **Guarantee stake**: for an "approve with guarantee" verdict, MAKELAR's
     CDP wallet sends a small USDC stake on Base Sepolia (skin in the game),
     link printed to sepolia.basescan.org.

### 3.3 Language & SDK decisions

- Python 3.11+ everywhere the memory is touched (`sibyl-memory-client` is
  Python-only). Packages: `sibyl-memory-client`, `cdp-sdk`, `virtuals-acp`,
  `httpx`.
- ACP: try `virtuals-acp` (PyPI, v2-compatible) first; **day-1 probe** decides.
  Fallback: shell out to `@virtuals-protocol/acp-cli` (Node) for
  register/create-job/submit — acceptable because ACP is at the edge, not in
  the memory core.
- x402 seller side in Python is unverified; **day-1 probe**. Fallback: a
  ~30-line `@x402/express` Node shim that proxies to MAKELAR's local HTTP
  port. Buyer side (for the demo's paying client) uses `x402[httpx]`.

## 4. On-chain plan

### 4.1 Base (all Sepolia unless noted)
- CDP server wallets (free API key, faucet ETH + USDC) for MAKELAR and the
  two demo agents. Every tx printed as a Basescan link.
- x402 testnet facilitator (x402.org) settles the paywall in test USDC.
- Optional one-liner: B20 / ERC-8004 registry read on mainnet
  (free `eth_call`) shown live in the demo.

### 4.2 Virtuals ACP
- Register 3 sandbox agents at app.virtuals.io/acp/new (no token needed):
  KLIEN-A (well-behaved client), KLIEN-B (misbehaving client — rejects a
  delivered job to create the dispute event), and NERACA-MAKELAR (provider).
- During the build window these run real sandbox jobs; that history is both
  our seed data and honest commit-history evidence.

## 5. Demo script (2–5 min, maps to gate evidence)

1. Problem: 20s — agents can't tell who to trust.
2. Live: KLIEN-B rejects a delivered job → PENGAMAT writes the event →
   ANALIS drops B's score (show `score_history`).
3. **Fresh-session beat (one continuous take, on-screen timestamp + commit
   hash):** kill everything, open a new terminal, cold-start MAKELAR, ask
   "hire KLIEN-B at $50?" → it recalls the dispute it never saw in this
   process and counters: lower budget + higher guarantee premium, citing the
   remembered event.
4. Paying for that answer: x402 402→paid flow, then the same as an ACP job,
   then the guarantee stake tx — three explorer/terminal proofs.
5. Deletion test on camera: run with `NERACA_MEMORY_DISABLED=1` → MAKELAR
   refuses: "no memory, no bureau" (exit non-zero).

## 6. Error handling & testing

- Memory writes: fail loud, never partial — a scout that can't write exits
  non-zero rather than silently dropping events (a bureau with gaps lies).
- On-chain calls: retry once, then surface the error with the attempted
  payload; never fake a tx hash.
- Tests (small, no frameworks beyond pytest): one test per component —
  `test_analis.py` (events → expected scores, incl. the dispute drop),
  `test_makelar.py` (profiles → expected verdicts/premiums),
  `test_idempotent.py` (re-observed job writes nothing). On-chain paths get
  a `--dry-run` flag so tests never need a network.

## 7. Repo & submission hooks

- Public GitHub repo, MIT. README sections: what it does; **"Where memory is
  load-bearing"** with file/line pointers to every `set_entity`/`write_event`/
  `get_entity`/`read_events` call (judge-findable < 2 min); partner stacks and
  where; "how memory made this possible"; Prior Work declaration (none —
  greenfield 2026-09-04).
- Commit early, commit real: the sandbox-job seed runs double as build-log
  material for the two required public posts (@sibylcap + @base + @virtuals_io).

## 8. Risks & fallbacks

| Risk | Fallback |
|---|---|
| `virtuals-acp` Python SDK broken | acp-cli via subprocess (day-1 probe decides) |
| x402 Python seller missing | 30-line Node express shim |
| ACP sandbox registration needs manual review / delays | demo still complete with x402 + CDP stake (×1.15); ACP added when approved |
| Telkomsel DNS-hijacks docs.cdp.coinbase.com | DoH/VPN; content mirrored at docs.x402.org + GitHub READMEs |
| Sibyl CLI auth issues | `MemoryClient.local()` path needs no cloud auth at all |
