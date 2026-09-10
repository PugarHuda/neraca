# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Operators of AI agents that hire or get hired by other agents on Virtuals ACP
and settle in USDC on Base — and the agents themselves, calling the bureau
over x402 or MCP before they commit a budget. Secondary, for this build's
lifetime: hackathon judges re-running the project from the README and opening
the public status page to check that memory is doing the work.
[inferred from the repository and the hackathon brief; not interviewed]

## Product Purpose

NERACA is a trust bureau for the agent economy. Three agents — PENGAMAT the
scout, ANALIS the analyst, MAKELAR the broker — share nothing but Sibyl
Memory. The bureau watches real agents transact, remembers every outcome,
sells memory-priced trust decisions (APPROVE, APPROVE_WITH_GUARANTEE with a
counter-budget and premium, DECLINE, NO_HISTORY), stakes real USDC behind its
guarantees, grades its own past verdicts, and publishes what it learned as
ERC-8004 reputation. Success: a counterparty's verdict changes because the
journal grew, and a stranger to the bureau is priced blind and cheap.

## Positioning

The bureau only trusts what it saw. Marketplace claims (an agent's own
success rate) ride beside NERACA's remembered score, never inside it. Nobody
outruns their record by going quiet: an archived profile rebuilds from the
journal. The doctrine that scores agents is itself remembered, versioned
state that the bureau revises when its verdicts turn out wrong.

## Operating Context

- CLI first: `python -m neraca <cmd>`; three terminals coordinating through one
  Sibyl store is the core demonstration.
- The web surface: `GET /` is the landing (`neraca/landing.py`), a counter
  ticket with one real GET form that returns the memory-set quote;
  `GET /registry` is the status page (`neraca/server.py`) rendered from memory;
  `GET /quote/<addr>` (free price); `GET /risk/<addr>?budget=` (x402 paywall,
  402 until paid). Deployed publicly on Vercel
  (neraca-psi.vercel.app) as a read-mostly window into a memory snapshot.
- Real data: live Virtuals ACP contracts on Base mainnet (JobManager,
  MemoManager), the public ACP directory, Base Sepolia settlements.
- Evaluated by judges under time pressure, often on a laptop; on camera in a
  2–5 minute demo video.

## Capabilities and Constraints

- Server-rendered HTML from FastAPI, no JavaScript; each page is a single
  Python-rendered template (`neraca/landing.py`, `neraca/server.py`), readable
  to judges. Mark and wordmark live in `neraca/brand.py` (SVG).
- Every number on the page is a read of memory: journal counts, profiles with
  score/jobs/disputes/invoices, latest verdicts, settlements witnessed.
- Terminology: PENGAMAT / ANALIS / MAKELAR; tiers HOT / WARM / COLD /
  REFERENCE / ARCHIVE; verdicts APPROVE / APPROVE_WITH_GUARANTEE / DECLINE /
  NO_HISTORY; "the bureau does not rate strangers".
- Addresses are long hex; names exist only for agents in the ACP directory.
- The landing carries exactly one control, the quote form; the registry has none.

## Brand Commitments

- Mark: a balance scale drawn as ledger rules, beam tilted, one vermilion
  point at the raised end (`neraca/brand.py`; `/logo.svg`, `/favicon.svg`).
- Name: NERACA (Indonesian: a balance scale; a ledger). Voice: plain,
  declarative, slightly dry ("no memory, no bureau").
- Visual direction pinned by the owner on 2026-09-10: **ledger / credit
  bureau** — the language of the book of accounts and the trust registry.

## Evidence on Hand

- 21 passing tests; six confirmed Base Sepolia transactions cited in README.
- Real journal snapshot (`api/snapshot.db`): 151 mainnet job observations,
  176 directory entries, 16 profiles.
- No customer testimonials, no pricing beyond the x402 policy ($0.01 blind +
  $0.01 per remembered event, cap $0.25). Do not fabricate either.

## Product Principles

- Memory is the only source of truth on the page; nothing decorative claims more than the journal holds.
- Read in seconds: a judge must find the load-bearing numbers without scrolling.
- Verdicts are typographic events; the rest is quiet.
- Names beside addresses, claims beside scores — adjacent, never merged.

## Accessibility & Inclusion

Text-first, no color-only meaning; long addresses must remain selectable and
copyable; works without JavaScript.
