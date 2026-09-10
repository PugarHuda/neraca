# NERACA — recording runbook (2–5 min)

Three panes, all in the repo root with the venv active. **A** is ANALIS
running live, **B** is PENGAMAT, **C** is MAKELAR and later the fresh session.
Two panes also works — run B's and C's commands in the same one.

Before rolling: `rm -f data/demo.db`, `export NERACA_DB=./data/demo.db`
(PowerShell: `$env:NERACA_DB="./data/demo.db"`), and put the commit hash plus a
live clock on screen — the gate requires the recall beat to be **one
continuous unedited segment** carrying a timestamp or commit hash.

```bash
git rev-parse --short HEAD && date -u   # leave this visible
```

## 1 · Problem (20s, talking over a still)

Agents hire each other on Virtuals ACP and settle in USDC on Base. Nothing
remembers who burned whom. NERACA is that bureau.

## 2 · Three processes, one memory, no other channel (75s)

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

## 3 · Fresh-session recall — ONE CONTINUOUS TAKE (45s)

Close every pane, ANALIS included. Open one new pane, on camera, and show the clock and
commit hash again before the first command.

```bash
export NERACA_DB=./data/demo.db
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
python -m neraca report 0xKLIENB000000000000000000000000000000000B
```

This process never saw the rejection. It cites it anyway — that is the gate.

## 4 · Deletion test (15s, same take if possible)

```bash
NERACA_MEMORY_DISABLED=1 python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
echo $?      # 1
```

"No memory, no bureau." There is no fallback path to fall back to.

## 5 · Selling the answer — on-chain proofs (75s)

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
curl -i "http://127.0.0.1:8402/risk/0xKLIENB000000000000000000000000000000000B?budget=50"   # 402
python -m neraca.server                   # walks the 402, pays $0.05, prints the answer + Basescan link
```

Open each Basescan link in the browser, on camera. Rehearsal proofs, both
confirmed on Base Sepolia:

- stake: https://sepolia.basescan.org/tx/0x8dbebb9d014f63bdc283900b2df3910b8c8d48ece75b9dfe07c8fafd698be678
- x402 settlement: https://sepolia.basescan.org/tx/0x8758b13c150d2e29d90e97bfad9d153d9f72643a1696bb9f2b3c6b4aefd33513

The stake is priced by memory, not typed by hand; the paid answer is
literally a read of Sibyl Memory. No memory, nothing to sell.

## 6 · Close (15s)

Three agents, one shared memory, no other channel. `pytest` — 10 tests, one of
which is the deletion test judges will run themselves.

## Credential checklist (do this before recording)

| Needs | Where | Unlocks |
|---|---|---|
| `NERACA_STAKE_KEY` + `NERACA_VAULT` | `python -m neraca.onchain wallet` mints them; faucet at alchemy.com/faucets/base-sepolia and faucet.circle.com | `onchain stake` — a real USDC transfer, no account anywhere |
| *or* `CDP_API_KEY_ID` / `_SECRET` / `CDP_WALLET_SECRET` | portal.cdp.coinbase.com | the same stake through CDP server wallets, with a built-in faucet |
| `NERACA_PAY_TO` | output of `python -m neraca.onchain wallet` | the x402 paywall's payee |
| `NERACA_BUYER_KEY` | any Base Sepolia key, faucet it with the CDP creds | the paying client in step 5 |
| ACP entity IDs + whitelisted key | app.virtuals.io/acp/new | `python -m neraca.acp seller` (second partner multiplier) |

Steps 1–4, the B20 read, the 402, and the stake refusal need **no credentials at all** — record those first
so a failed key never costs you the gate evidence.
