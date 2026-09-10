# Submission pack — NERACA

Repo: https://github.com/PugarHuda/neraca (MIT) · Deadline: 2026-09-10 23:59 UTC

## 0 · Build-page fields (team: Ampun Bang) — paste verbatim

**Public repo URL**

    https://github.com/PugarHuda/neraca

**What breaks when memory is deleted?**

> Delete the memory and NERACA does not degrade, it exits: run anything with
> `NERACA_MEMORY_DISABLED=1` and it returns exit 1 with "no memory, no bureau".
> The three agents share no queue, no RPC and no file — Sibyl Memory is the only
> bus between them — so with it gone there is no journal to price risk from, no
> reputation profile to read, and nothing left to sell.

**Memory walkthrough**

> Persist: every agent-to-agent job phase PENGAMAT observes as a COLD event
> (`write_event`) — simulated, or read live off the Virtuals ACP contracts on
> Base mainnet; every x402 invoice the storefront saw paid; every verdict
> MAKELAR gives. ANALIS distils those into WARM reputation profiles with full
> `score_history` (`set_entity`). The scoring doctrine lives in REFERENCE,
> versioned. HOT state holds open negotiations, the chain-scan cursor, the
> ERC-8004 identity and which verdicts were already graded.
>
> Recall (fresh session): a brand-new process runs
> `python -m neraca ask 0xKLIENB...B --budget 50`, opens the same Sibyl store,
> and cites a rejection by job id from a session already closed. Three agents
> also run concurrently: `python -m neraca watch` leaves ANALIS live with
> nothing handed to it, and when PENGAMAT writes one event from a separate
> process it rebuilds every profile on its own — memory is the entire bus.
>
> Changes the agent's decision by: one REJECTED observation moves KLIEN-B from
> 50 to 25 and flips APPROVE_WITH_GUARANTEE (counter 25 USDC, 10% premium) to
> DECLINE; `reflect` then grades that verdict as a false approve and tightens
> the rubric in REFERENCE to v2, so the next analysis scores B at 20. The x402
> price is set by how much memory stands behind the answer; the USDC
> guarantee stake refuses to fire without an open APPROVE_WITH_GUARANTEE in
> HOT; the ERC-8004 feedback refuses to rate an agent with no remembered
> profile. The code never changed. The memory did.

**Memory primitives** — tick all seven, each is a command a judge can run:
`recall` (`ask` in a fresh process), `entities` (`set_entity`/`get_entity`
profiles), `semantic search` (`python -m neraca search <q>`, FTS5 across
tiers), `temporal / time-travel` (`ask --as-of <iso>`, `read_events(until=)`),
`summarization` (ANALIS distils the journal into profiles), `reflection`
(`python -m neraca reflect` grades past verdicts), `consolidation` (the rubric
revised and versioned in REFERENCE; stale agents archived).

## 1 · Memory implementation note (longer version, if a field wants prose)

NERACA is a trust bureau for the agent economy. Three agents — PENGAMAT
(scout), ANALIS (analyst), MAKELAR (broker) — run as separate processes and
share **no channel except Sibyl Memory**: no queue, no RPC, no shared file.
The memory layer is the bus, the database, and the product.

- **COLD** `write_event` / `read_events` — `neraca/memory.py:record_job_event`,
  `job_events`. Every observed ACP job phase is journaled. This is the only
  input ANALIS ever sees.
- **WARM** `set_entity` / `get_entity` — `neraca/analis.py:run` writes evolving
  reputation profiles with full `score_history`; `neraca/makelar.py:decide`
  reads them. That read is the load-bearing moment: no profile, no priced
  decision.
- **REFERENCE** `get_reference` / `set_reference` — the scoring rubric lives in
  memory, not in code (`neraca/memory.py:get_rubric`), so judgment itself is
  remembered state.
- **HOT** `set_state` / `get_state` — the open negotiation a decision creates.
  The on-chain guarantee stake (`neraca/onchain.py`) refuses to fire without
  one, so real USDC is priced by memory rather than typed by hand.
- **ARCHIVE** `archive_entity` — agents that go stale.

**Deletion test:** `NERACA_MEMORY_DISABLED=1 python -m neraca ask <addr>` exits
1 with "no memory, no bureau". There is no fallback path, and
`tests/test_neraca.py::test_memory_is_load_bearing` asserts it.

**Coordination, not just recall:** three OS processes share no channel but the
Sibyl store. Run `python -m neraca watch` in one terminal and
`python -m neraca witness` in another: ANALIS reacts to a write it was never
told about, and a third process asking `ask` then gets a different verdict.
`tests/test_neraca.py::test_analis_watch_reacts_to_another_process` pins it.

**Dynamic storage, not recall:** the same question gets a different answer as
the journal grows. One live `REJECTED` observation moves KLIEN-B from 50 to 25
and flips APPROVE_WITH_GUARANTEE to DECLINE — the code never changes, the
memory does.

## 2 · Public posts (2 required, tag @sibylcap + partners)

Verify handles before posting: Sibyl `@sibylcap`, Base `@base`, Virtuals
`@virtuals_io`.

**Post 1 — what it is**

> Agents hire each other now. Nothing remembers who burned whom.
>
> Built NERACA for the @sibylcap hackathon: a trust bureau where three agents
> share no channel but memory. It watches agent-to-agent jobs, remembers every
> outcome, and sells priced trust decisions — approve, decline, or counter with
> a guarantee it stakes real USDC behind on @base.
>
> Delete the memory calls and the bureau doesn't degrade, it exits.
>
> github.com/PugarHuda/neraca

**Post 2 — the proof**

> The demo beat I care about: ask NERACA the same question twice.
>
> Before: KLIEN-B scores 50 → APPROVE_WITH_GUARANTEE, counter 25 USDC.
> One observed rejection lands in the journal.
> After: 25 → DECLINE, citing "rejected delivered job sim-b1".
>
> The code did not change. The memory did. Rubric lives in @sibylcap's
> REFERENCE tier; the guarantee stake and the x402 payment both settled on
> @base Sepolia, both gated by memory before a key was ever touched; jobs
> come from @virtuals_io ACP.
>
> stake: https://sepolia.basescan.org/tx/0x8dbebb9d014f63bdc283900b2df3910b8c8d48ece75b9dfe07c8fafd698be678
> [video link]

## 3 · Checklist

- [x] Public repo, MIT, real commit history
- [x] README points to where memory is written/read (top section)
- [x] Deletion test in the suite (20/20 passing)
- [x] Free Base leg verified live (`onchain b20` → AAPLc)
- [x] x402 paywall returns a valid v2 402 with `payment-required` header
- [x] Guarantee stake executed on Base Sepolia: https://sepolia.basescan.org/tx/0x8dbebb9d014f63bdc283900b2df3910b8c8d48ece75b9dfe07c8fafd698be678
- [x] x402 402→paid leg settled on Base Sepolia: https://sepolia.basescan.org/tx/0x8758b13c150d2e29d90e97bfad9d153d9f72643a1696bb9f2b3c6b4aefd33513
- [x] Memory-priced x402 settlement, journaled as an observation: https://sepolia.basescan.org/tx/0xb2c5915ac7c22f2236c97fec70f3e8d4945f2d6cbfa6ffdc9dbfb1a271878a07
- [x] ERC-8004: NERACA registered as agent #9215: https://sepolia.basescan.org/tx/0x616df8a005aef6f4606eca64cb96bf974ce7cd04d861898b2358dcdad9a5d473
- [x] ERC-8004: memory-backed feedback published on agent #9216: https://sepolia.basescan.org/tx/0x7c920e2d96ebbc31993b9ee6437b8dc3915c7dda9ca6cfe15d1d8fe609a1615c
- [x] Live ACP jobs read off Base mainnet contracts, no registration (`python -m neraca chain`)
- [x] Public deployment: https://neraca-psi.vercel.app (landing with a live quote form, /registry, /quote, 402 on /risk) — designed with Impeccable, reviewed and documented
- [x] NERACA as an MCP server (`python -m neraca.mcp_server`), x402 Bazaar discovery declared
- [ ] ACP agents registered → `neraca.acp seller` (provider side; the observer side needs nothing)
- [ ] Demo video 2–5 min, recall beat as ONE unedited take with commit hash + clock
- [ ] 2 public posts
- [ ] Submitted via the private build-page link from registration
