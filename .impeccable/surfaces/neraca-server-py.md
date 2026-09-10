---
version: 1
slug: "neraca-server-py"
primary_target: "neraca/server.py"
related_targets: []
---

# Surface brief: NERACA status page + storefront (`GET /`)

Scope: the bureau's status page, server-rendered from memory, and the storefront hints on it. Visitor mode: Operate — a judge or an operator reads the state of the bureau in seconds: what it remembers, who it rates, what it decided, what it was paid.

Audience / job: judges re-running the project and opening the public deployment; agent operators checking a counterparty before dealing. Task: scan the registry, read the latest verdicts, confirm the numbers are real memory. Proof/content: every figure is a read of Sibyl Memory (journal counts, WARM profiles, verdict log, settlements, directory names). Constraints: single Python-rendered template in `neraca/server.py`, no JS framework, works without JavaScript, addresses selectable, no fabricated claims.

## Direction contract

THESIS: A bureau's registry of index cards, stamped — not a dashboard of metric tiles. It refuses the hero-metric template and the card-inside-card admin grid; the ledger's ruled lines and the stamp carry the meaning.

OWN-WORLD: eye-ease ledger-green paper as the ground (the owner's words, 2026-09-10: "Hijau eye-ease" — the accountant's ledger stock, chosen over bone/cream), iron-black ink, hairlines drawn at one device pixel and no radius anywhere; one rubric vermilion reserved for DECLINE, a bottle-green for APPROVE, ochre for APPROVE_WITH_GUARANTEE, graphite for NO_HISTORY — a fixed status vocabulary, never decoration. Figures in a typewriter face with tabular numerals (Courier Prime); labels and prose in a workhorse sans (Source Sans 3) set in small caps for apparatus. Components: the index card (ruled 4-line entry list, balance figure at right, a rotated ink stamp), the daybook board (fixed columns, live rows, DECLINE rows dim to vermilion), the receipts slip, the tariff note in the margin.

STORY: the visitor understands that this bureau remembers, sees who it trusts and who it declines, believes the numbers because every one is a memory read, and — if an operator — copies an address into `/quote` or `/risk`.

FIRST VIEWPORT: a bureau masthead strip (name, ledger date line) over one ruled tabulation line of the journal totals in tabular type; beneath it the registry opens immediately — the first row of index cards, worst score first, each with its stamp; the daybook board's header is visible at the fold. No primary action beyond reading; the tariff note sits in the right margin at desktop width, inline on phones.

FORM: the bureau registry card — candidate 4 of my ordered ledger-world list (1 double-entry ledger, 2 credit report, 3 bank passbook, 4 registry docket cards, 5 clearing-house statement, 6 notary protocol, 7 quotes chalkboard); seed key b32e0f57. Raises taken from the hand: "ruling engine" — every rule at 1px, states as printed marks, no radius (from rw-centre-rail-reference-setting, declined); "fixed-column board with row states" — the daybook as a board whose columns never move (from signals-instruments-split-flap-concourse, competitive); "one fixed color language for status only" (from notation-diagram-systems-orienteering-map, declined); "total commitment to one material" — paper and ink, no chrome, no shadows (from the two surreal challengers, declined).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

Unresolved: whether the page ever gains controls (none today).
