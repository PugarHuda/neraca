# NERACA — the trust bureau for the agent economy

*Neraca* (Indonesian): a balance scale; a ledger.

Agents are starting to hire each other (Virtuals ACP settles agent-to-agent
jobs in USDC on Base), but nothing remembers who burned whom. NERACA is a
bureau of three agents whose **only** shared substrate is Sibyl Memory: it
watches agents transact, remembers every outcome, and sells memory-priced
trust decisions — approve, decline, or counter with an adjusted budget and a
guarantee premium it stakes real USDC behind.

## Where memory is load-bearing (judges: start here)

The three agents communicate **only** through Sibyl Memory — there is no
queue, no RPC, no shared file. The memory layer is the bus, the database, and
the product:

| Call | Where | What it carries |
|---|---|---|
| `write_event` (COLD) | [`neraca/memory.py`](neraca/memory.py) `record_job_event` | every observed ACP job phase — the journal of record |
| `read_events` (COLD) | [`neraca/memory.py`](neraca/memory.py) `job_events` | the only input ANALIS ever sees |
| `set_entity` / `archive_entity` (WARM/ARCHIVE) | [`neraca/analis.py`](neraca/analis.py) `run` | evolving reputation profiles with full `score_history` |
| `get_reference` / `set_reference` (REFERENCE) | [`neraca/memory.py`](neraca/memory.py) `get_rubric` | the scoring rubric ANALIS applies — memory, not code |
| `get_entity` (WARM) | [`neraca/makelar.py`](neraca/makelar.py) `decide` | **the load-bearing read**: no profile, no priced decision |
| `set_state` / `get_state` (HOT) | [`neraca/makelar.py`](neraca/makelar.py), [`neraca/onchain.py`](neraca/onchain.py) | open negotiations; the stake refuses to fire without one |

**The deletion test:** run anything with `NERACA_MEMORY_DISABLED=1` and the
bureau exits immediately — *no memory, no bureau*. There is no fallback path.
`tests/test_neraca.py::test_memory_is_load_bearing` asserts it.

## How memory made this possible

A trust bureau *is* institutional memory. Recall alone wouldn't be enough:
NERACA's answer to the same question changes as the journal grows (one new
dispute event moves a verdict from APPROVE to DECLINE), its rubric lives in
the REFERENCE tier so judgment itself is remembered state, and three
processes coordinate through the same database with no other channel. Sibyl's
five tiers map one-to-one onto what a bureau needs: a journal (COLD), case
files (WARM), doctrine (REFERENCE), open negotiations (HOT), and a morgue
(ARCHIVE).

## Partner stacks

- **Base** — [`neraca/onchain.py`](neraca/onchain.py): CDP server wallets on
  Base Sepolia; the guarantee stake is a real USDC `transfer()` (wallet
  operation + contract interaction, Basescan link printed), plus a live B20
  read of Coinbase Tokenized Stocks on Base mainnet.
  [`neraca/server.py`](neraca/server.py): the risk endpoint is x402-paywalled
  (test USDC, x402.org facilitator).
- **Virtuals Protocol** — [`neraca/acp.py`](neraca/acp.py): NERACA is a
  registered ACP (v2) provider; a funded job's deliverable is a memory-backed
  risk report, and every job phase it witnesses is journaled live.

## Run it

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows
# .venv/bin/pip on Linux/macOS

# the core loop (no keys, no network needed):
python -m neraca seed      # PENGAMAT journals the demo scenario (COLD)
python -m neraca analis    # ANALIS rebuilds reputation profiles (WARM)
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
#  -> DECLINE, reasons: ["rejected delivered job sim-b1"]  <- recalled, not computed

python -m neraca report <addr>   # the remembered evidence behind any verdict
pytest                            # 4 tests, incl. the deletion test

# the storefronts (see .env.example for credentials):
uvicorn neraca.server:app --port 8402      # x402 paywall: GET /risk/<addr>
python -m neraca.server                    # the buyer: walks the 402 and pays (NERACA_BUYER_KEY)
python -m neraca.onchain b20               # live B20 read, Base mainnet, free
python -m neraca.onchain wallet            # CDP wallets + Base Sepolia faucet
python -m neraca.onchain stake <addr> 1.0  # stake a guarantee (memory-gated)
python -m neraca.acp seller                # serve ACP jobs + observe live
```

Fresh-session recall: run `seed` + `analis`, close the terminal, open a new
one, and `ask` — the verdict cites events this process never saw.

## Prior work declaration

Greenfield, started 2026-09-04 for the Sibyl Labs Hackathon. No prior
codebase; dependencies are the public SDKs in `requirements.txt`.

## License

MIT — see [LICENSE](LICENSE).
