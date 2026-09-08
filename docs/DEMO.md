# NERACA — recording runbook (2–5 min)

Two terminals, both in the repo root with the venv active. Terminal **A** is
the bureau; terminal **B** is the fresh session and the storefront client.

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

## 2 · The journal grows, the verdict moves (60s, terminal A)

```bash
python -m neraca seed --before-dispute   # 27 observations: A's clean history, B's job still open
python -m neraca analis                  # KLIEN-B sits at 50
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
#   -> APPROVE_WITH_GUARANTEE, counter 25.0, premium 10%

python -m neraca witness                 # PENGAMAT sees B reject the delivery. ONE event.
python -m neraca analis                  # 50 -> 25
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
#   -> DECLINE, reasons: ["rejected delivered job sim-b1"]
```

Say it plainly: *the code did not change, the memory did.*

## 3 · Fresh-session recall — ONE CONTINUOUS TAKE (45s)

Close terminal A entirely. Open terminal B, on camera, and show the clock and
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

## 5 · Selling the answer — on-chain proofs (60s)

```bash
# free, no keys, live Base mainnet read:
python -m neraca.onchain b20              # Apple Inc. / AAPLc / totalSupply

# x402 storefront (terminal A), then the buyer (terminal B):
uvicorn neraca.server:app --port 8402
curl -i http://127.0.0.1:8402/risk/0xKLIENB000000000000000000000000000000000B?budget=50   # 402
# make the price legible on camera - x402 v2 carries it in a base64 header:
curl -sD- -o/dev/null 'http://127.0.0.1:8402/risk/0xKLIENB000000000000000000000000000000000B?budget=50' \n  | grep -i '^payment-required' | cut -d' ' -f2 | base64 -d | python -m json.tool
python -m neraca.server                   # walks the 402, pays, prints the answer + receipt

# guarantee stake — memory-gated, refuses without an open APPROVE_WITH_GUARANTEE:
python -m neraca ask 0xKLIENA000000000000000000000000000000000A --budget 50   # APPROVE_WITH_GUARANTEE
python -m neraca.onchain stake 0xKLIENA000000000000000000000000000000000A 1.0 # Basescan link
```

Show the Basescan link resolving in a browser. Try the stake against KLIEN-B
first if there is time — it refuses, because the stake is priced by memory,
not typed by hand.

## 6 · Close (15s)

Three agents, one shared memory, no other channel. `pytest` — 5 tests, one of
which is the deletion test judges will run themselves.

## Credential checklist (do this before recording)

| Needs | Where | Unlocks |
|---|---|---|
| `CDP_API_KEY_ID` / `_SECRET` / `CDP_WALLET_SECRET` | portal.cdp.coinbase.com | `onchain wallet`, `onchain stake`, faucet for the x402 buyer |
| `NERACA_PAY_TO` | output of `python -m neraca.onchain wallet` | the x402 paywall's payee |
| `NERACA_BUYER_KEY` | any Base Sepolia key, faucet it with the CDP creds | the paying client in step 5 |
| ACP entity IDs + whitelisted key | app.virtuals.io/acp/new | `python -m neraca.acp seller` (second partner multiplier) |

Steps 1–4 and the B20 read need **no credentials at all** — record those first
so a failed key never costs you the gate evidence.
