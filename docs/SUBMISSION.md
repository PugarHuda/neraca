# Submission pack — NERACA

Repo: https://github.com/PugarHuda/neraca (MIT) · Deadline: 2026-09-10 23:59 UTC

## 1 · Memory implementation note (paste into the form)

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
> REFERENCE tier, the stake fires on @base, jobs come from @virtuals_io ACP.
>
> [video link]

## 3 · Checklist

- [x] Public repo, MIT, real commit history
- [x] README points to where memory is written/read (top section)
- [x] Deletion test in the suite (5/5 passing)
- [x] Free Base leg verified live (`onchain b20` → AAPLc)
- [x] x402 paywall returns a valid v2 402 with `payment-required` header
- [ ] CDP keys → `onchain wallet`, faucet, `onchain stake` (Basescan link)
- [ ] `NERACA_BUYER_KEY` funded → paid x402 leg
- [ ] ACP agents registered → `neraca.acp seller` (second stack, ×1.25)
- [ ] Demo video 2–5 min, recall beat as ONE unedited take with commit hash + clock
- [ ] 2 public posts
- [ ] Submitted via the private build-page link from registration
