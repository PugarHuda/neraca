# NERACA — recording runbook (2–5 min)

Three panes, all in the repo root with the venv active. **A** is ANALIS
running live, **B** is PENGAMAT, **C** is MAKELAR and later the fresh session.
Two panes also works — run B's and C's commands in the same one.

Before rolling: `rm -f data/demo.db*` (the `*` matters - a stale SQLite WAL
file can resurrect the old journal), `export NERACA_DB=./data/demo.db`
(PowerShell: `Remove-Item data\demo.db* -Force; $env:NERACA_DB="./data/demo.db"`),
and put the commit hash plus a live clock on screen — the gate requires the
recall beat to be **one continuous unedited segment** carrying a timestamp or
commit hash.

```bash
git rev-parse --short HEAD && date -u   # leave this visible
```

Core path (acts 1–5, 7) is ~4 minutes. Acts 6 and 8 are the strongest
extras; add them if the take is running short.

## 1 · Problem (15s, talking over a still)

Agents hire each other on Virtuals ACP and settle in USDC on Base. Nothing
remembers who burned whom. NERACA is that bureau.

## 2 · Three processes, one memory, no other channel (60s)

Seed the journal in **C**, then leave ANALIS running in **A** for the rest of
the demo. Nothing is ever handed to it: no queue, no socket, no callback.

```bash
# C:
python -m neraca seed --before-dispute   # 27 observations: A's six clean jobs, B's still open

# A - leave this running, on screen, for the whole take:
python -m neraca watch
#   [12:11:04] journal grew to 27 events - profiles rebuilt
#        50  0xKLIENB...   68  0xKLIENA...   80  0xNERACA...

# C - WAIT for pane A to print its first "profiles rebuilt" line before this.
#     Ask too early and there is no profile yet: the honest answer is NO_HISTORY.
# Price both clients. Same budget, different premium, straight from memory:
python -m neraca ask 0xKLIENA000000000000000000000000000000000A --budget 50
#   -> APPROVE_WITH_GUARANTEE, counter 34.0, premium 1%    (68: six jobs funded and accepted)
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
#   -> APPROVE_WITH_GUARANTEE, counter 25.0, premium 10%   (50: clean but thin)

# B - PENGAMAT witnesses B reject the delivery. ONE event, one process:
python -m neraca witness
```

Now stop talking and point at **pane A**. Within two seconds, a process nobody
touched reprints KLIEN-B at 25. Then, in **C**:

```bash
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
#   -> DECLINE, reasons: ["rejected delivered job sim-b1"]
```

Three OS processes. No queue, no RPC, no shared file. One wrote, one noticed,
one changed its answer. Say it plainly: *the code did not change, the memory
did* — and *that* is the only wire between them.

## 3 · Fresh-session recall — ONE CONTINUOUS TAKE (40s)

Close every pane, ANALIS included. Open one new pane, on camera, and show the
clock and commit hash again before the first command.

```bash
export NERACA_DB=./data/demo.db
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
python -m neraca report 0xKLIENB000000000000000000000000000000000B
```

This process never saw the rejection. It cites it anyway — that is the gate.

## 4 · Deletion test (10s, same take if possible)

```bash
NERACA_MEMORY_DISABLED=1 python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
echo $?      # 1
```

"No memory, no bureau." There is no fallback path to fall back to.

## 5 · The bureau grades itself (30s)

Its first call on KLIEN-B was APPROVE_WITH_GUARANTEE. Then B rejected a
delivery. That verdict is in the journal too, so it can be graded.

```bash
python -m neraca reflect
#   graded 1 verdict(s): 1 false approve, 0 false decline
#   doctrine revised -> rubric v2: dispute_penalty 25->30, approve_threshold 70->75
python -m neraca analis                  # KLIEN-B rescored under the new doctrine: 20
python -m neraca rubric                  # version 2, with history - doctrine is remembered state
python -m neraca reflect                 # same evidence again: "doctrine holds" (HOT remembers what was graded)
```

Optional, ten seconds: time travel.

```bash
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50 --as-of <clock from act 2, before witness>
#   -> APPROVE_WITH_GUARANTEE, "as_of": ...   the answer as it stood then; no negotiation opened, no verdict journaled
```

## 6 · Real agents, real jobs, no keys (30s, extra)

```bash
python -m neraca chain
#   PENGAMAT read Base mainnet blocks N..M: 35 jobs created, ... -> 35 new observations (cursor saved in HOT memory)
python -m neraca chain                   # again: a handful of blocks - it resumed from memory
python -m neraca analis | head           # real Base addresses, real scores
```

These are the live Virtuals ACP contracts on Base mainnet, read over a public
RPC. A real rejection (job `acp-1003558525`) is already in the journal on the
committed run; if one appears in your window, `ask` that client.

## 7 · Selling the answer — on-chain proofs (60s)

```bash
# free, no keys, live Base mainnet read:
python -m neraca.onchain b20              # Apple Inc. / AAPLc / totalSupply

# the guarantee stake, refused first, then fired for real:
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50   # DECLINE
python -m neraca.onchain stake 0xKLIENB000000000000000000000000000000000B 1.0 # REFUSED - memory gate, no key touched
python -m neraca ask 0xKLIENA000000000000000000000000000000000A --budget 50   # APPROVE_WITH_GUARANTEE
python -m neraca.onchain stake 0xKLIENA000000000000000000000000000000000A 1.0 # real USDC transfer(), Basescan link

# x402 storefront (pane A), then the buyer (pane C):
uvicorn neraca.server:app --port 8402
curl localhost:8402/quote/0xKLIENB000000000000000000000000000000000B        # $0.05: 4 remembered events
curl localhost:8402/quote/0xnobody                                            # $0.01: priced blind
python -m neraca.server                   # walks the 402, pays the memory-set price, prints the Basescan link
python -m neraca analis | grep 0x6505     # the payer now has a profile: it settled an invoice
```

Open `http://localhost:8402/` in the browser: the status page is rendered
straight from memory — profiles, the verdict log, the settlement it just
witnessed. Then open a Basescan link. Rehearsal proofs, all confirmed:

- stake: https://sepolia.basescan.org/tx/0x8dbebb9d014f63bdc283900b2df3910b8c8d48ece75b9dfe07c8fafd698be678
- x402 settlement, memory-priced: https://sepolia.basescan.org/tx/0xb2c5915ac7c22f2236c97fec70f3e8d4945f2d6cbfa6ffdc9dbfb1a271878a07

The stake is priced by memory, not typed by hand; the paid answer is
literally a read of Sibyl Memory. No memory, nothing to sell.

## 8 · The verdict leaves the bureau: ERC-8004 (40s, extra)

NERACA is agent **#9215** in the ERC-8004 Identity Registry on Base Sepolia;
the demo counterparty (the x402 buyer's wallet) is **#9216**, a different
owner.

```bash
python -m neraca.onchain identity         # already_registered: true - agentId remembered in HOT
python -m neraca.onchain feedback 9215    # REFUSED: NERACA remembers nothing about that owner - it does not rate strangers
python -m neraca.onchain feedback 9216    # giveFeedback(52, APPROVE_WITH_GUARANTEE, rubric-v1) -> Basescan link; getSummary reads it back
```

Rehearsal proof: https://sepolia.basescan.org/tx/0x7c920e2d96ebbc31993b9ee6437b8dc3915c7dda9ca6cfe15d1d8fe609a1615c

## 9 · Close (10s)

Three agents, one shared memory, no other channel. `pytest` — 16 tests, one of
which is the deletion test judges will run themselves.

## Credential checklist (do this before recording)

| Needs | Where | Unlocks |
|---|---|---|
| `NERACA_STAKE_KEY` + `NERACA_VAULT` | `python -m neraca.onchain wallet` mints them; faucet at alchemy.com/faucets/base-sepolia and faucet.circle.com | `onchain stake`, `onchain identity`, `onchain feedback` — real transactions, no account anywhere |
| *or* `CDP_API_KEY_ID` / `_SECRET` / `CDP_WALLET_SECRET` | portal.cdp.coinbase.com | the same stake through CDP server wallets, with a built-in faucet |
| `NERACA_PAY_TO` | the staking wallet's address | the x402 paywall's payee |
| `NERACA_BUYER_KEY` | printed by `onchain wallet` (the vault's key) | the paying client in act 7; owner of ERC-8004 agent #9216 |
| ACP entity IDs + whitelisted key | app.virtuals.io/acp/new | `python -m neraca.acp seller` (provider side only; act 6 needs nothing) |

Acts 1–6, the B20 read, the 402, the stake refusal and the feedback refusal
need **no credentials at all** — record those first so a failed key never
costs you the gate evidence.
