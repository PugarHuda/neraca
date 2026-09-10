---
name: NERACA
description: A trust bureau for the agent economy, drawn as a ledger office on eye-ease green paper
colors:
  ledger-green: "#e9eedf"
  iron-ink: "#1b1c17"
  faded-ink: "#454a3e"
  hairline: "#b3bda6"
  approve-green: "#2b5a37"
  guarantee-ochre: "#735616"
  decline-vermilion: "#b3301c"
  no-history-graphite: "#5f6457"
  canary: "#efd45a"
  canary-edge: "#e3c43a"
  canary-ink: "#5c4a0c"
  canary-field: "#fff8cf"
typography:
  display:
    fontFamily: "Courier Prime, ui-monospace, monospace"
    fontSize: "4.5rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.02em"
    fontFeature: "tnum"
  figure:
    fontFamily: "Courier Prime, ui-monospace, monospace"
    fontSize: "2.25rem"
    fontWeight: 700
    lineHeight: 1
    fontFeature: "tnum"
  headline:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 400
    lineHeight: 1.3
  masthead:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "1.4375rem"
    fontWeight: 600
    letterSpacing: "0.14em"
  title:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
  section:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    letterSpacing: "0.12em"
  body:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    letterSpacing: "0.05em"
    fontFeature: "all-small-caps"
  stamp:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.14em"
  mono:
    fontFamily: "Courier Prime, ui-monospace, monospace"
    fontSize: "0.9375rem"
    fontWeight: 400
    fontFeature: "tnum"
  address:
    fontFamily: "Courier Prime, ui-monospace, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    fontFeature: "tnum"
rounded:
  none: "0"
spacing:
  hair: "1px"
  xs: "0.25rem"
  sm: "0.5rem"
  cell: "0.5rem 0.75rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2.5rem"
  section: "3rem"
  page-bottom: "4rem"
components:
  button-ticket:
    backgroundColor: "{colors.iron-ink}"
    textColor: "{colors.canary}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0.7rem"
    width: "100%"
  input-ticket:
    backgroundColor: "{colors.canary-field}"
    textColor: "{colors.iron-ink}"
    typography: "{typography.mono}"
    rounded: "{rounded.none}"
    padding: "0.5rem 0.6rem"
    width: "100%"
  index-card:
    backgroundColor: "{colors.ledger-green}"
    textColor: "{colors.iron-ink}"
    rounded: "{rounded.none}"
    padding: "1rem 1rem 1.1rem"
  counter-form:
    backgroundColor: "{colors.ledger-green}"
    textColor: "{colors.iron-ink}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  ticket:
    backgroundColor: "{colors.canary}"
    textColor: "{colors.iron-ink}"
    rounded: "{rounded.none}"
    padding: "1.25rem 1.25rem 1.5rem"
  stamp:
    typography: "{typography.stamp}"
    rounded: "{rounded.none}"
    padding: "0.25rem 0.5rem"
  section-head:
    textColor: "{colors.iron-ink}"
    typography: "{typography.section}"
    padding: "0 0 0.35rem"
  table-cell:
    textColor: "{colors.iron-ink}"
    typography: "{typography.mono}"
    padding: "{spacing.cell}"
---

# Design System: NERACA

## Overview

**Creative North Star: "The Ledger Office"**

NERACA is a credit bureau for agents, and its pages are the bureau's own paper: eye-ease ledger-green stock (the owner's word is *hijau eye-ease*, the accountant's ledger green), iron ink, and rules drawn at one device pixel. Nothing is a dashboard. The registry is a drawer of index cards with a balance and a stamp; the landing is a counter ticket printed on canary carbon-copy stock; the numbers are typed in a typewriter face because they are read from memory as the page renders. There is no chrome: no radius, no drop shadow, no gradient, no icon. Everything that carries meaning is either a rule, a figure, a small-cap label, or a stamp.

Density is that of a well-kept book. Sections open with a ruled heading; tables and card grids are separated by hairlines, not gutters; every figure is right-aligned and tabular. Color is spent on exactly one thing: the verdict. Four fixed status inks (bottle green, ochre, vermilion, graphite) mark APPROVE, APPROVE_WITH_GUARANTEE, DECLINE and NO_HISTORY and nothing else. The one departure from the green paper is the landing's canary ticket, a second real ledger-office material committed for that surface alone.

The world rejects the SaaS hero, metric tiles, card-inside-card admin grids, and any illusion of depth. The page is the receipt.

**Key Characteristics:**
- Ledger-green paper (#e9eedf) with iron ink; a single hairline color for every rule
- Hairlines at 1px, no radius, no drop shadows; depth is stated by rules and ink weight only
- Source Sans 3 for apparatus and prose, Courier Prime with tabular numerals for every figure and address
- Small-caps labels (`font-variant: all-small-caps`) for column heads, keys and captions
- Four fixed status inks used only for verdict state, never for decoration
- The rotated ink stamp as the system's signature mark of state

## Colors

An accountant's palette: one green paper, one ink in two strengths, one hairline, four status inks, and the canary of a carbon-copy ticket.

### Primary
- **Iron Ink** (`iron-ink`): every letter, every heavy rule (masthead, section heads, table heads), the filled ticket button, and text selection background. It is the only "brand" color; the mark is drawn in it.
- **Ledger Green** (`ledger-green`): the page and every container on it. Cards, counters and table cells sit *on* the paper, they do not add a lighter or darker tint. It also fills the stamp's inner ring so the double rule reads as one printed impression.

### Secondary
- **Canary** (`canary`), **Canary Edge** (`canary-edge`), **Canary Ink** (`canary-ink`), **Canary Field** (`canary-field`): the carbon-copy ticket on the landing. Canary is the stock, Canary Edge its cut edge and perforation ring, Canary Ink the fine print and placeholder on that stock, Canary Field the paler fill of the address field. The ticket button prints iron ink with canary type. These four never leave the ticket.

### Neutral
- **Faded Ink** (`faded-ink`): secondary apparatus, labels, captions, the italic "why" line under a card, the date in the masthead, footers.
- **Hairline** (`hairline`): every light rule: table row rules, entry rules inside a card, the 1px "gutter" between cards and counters, container borders.

### Status (fixed vocabulary)
- **Approve Green** (`approve-green`): APPROVE, in the stamp and the verdict column.
- **Guarantee Ochre** (`guarantee-ochre`): APPROVE_WITH_GUARANTEE, and the landing's "quoted" stamp.
- **Decline Vermilion** (`decline-vermilion`): DECLINE. A DECLINE row in the daybook dims entirely to vermilion and the verdict is underlined. It is also the single red point on the mark's beam.
- **No-History Graphite** (`no-history-graphite`): NO_HISTORY, the "blind" stamp, and the "simulated" annotation.

### Named Rules
**The Status-Only Rule.** The four status inks appear only on a stamp, a verdict cell, or a status annotation. No heading, button, link, or decoration borrows them. The mark's one vermilion point is the sole exception and it is the mark, not a surface.

**The One Paper Rule.** There is one ground color. Containers do not tint; they are drawn on the paper with hairlines. A second material (the canary ticket) must be a real ledger-office stock and must be committed for a surface, not sprinkled.

## Typography

**Display / Figure Font:** Courier Prime (with ui-monospace, monospace)
**Body / Apparatus Font:** Source Sans 3 (with system-ui, sans-serif)
**Label:** Source Sans 3 in `all-small-caps`

**Character:** A workhorse sans for everything a clerk would write and a typewriter face with tabular numerals for everything a clerk would type: figures, balances, addresses, transaction hashes, commands. Uppercase letterspaced sans is reserved for the masthead, ruled section heads and stamps.

### Hierarchy
- **Display** (700, 4.5rem, 1, -0.02em, Courier Prime): the ticket's NOW SERVING number. One per page.
- **Figure** (700, 2.25rem, 1, Courier Prime): the balance on an index card. The quote price on the ticket is the same voice at 1.5rem.
- **Headline** (400, 1.75rem, 1.3; 1.5rem under 60rem): the landing thesis, three short lines with one italic phrase.
- **Masthead** (600, 1.4375rem, uppercase, 0.14em): the NERACA wordmark beside the mark; a plain 0.9375rem qualifier ("registry") in faded ink follows it.
- **Title** (600, 1.125rem): a card's counterparty name, with its short address in bold Courier Prime.
- **Section** (600, 0.875rem, uppercase, 0.12em; counters use 0.8125rem): every ruled section head, with an optional plain caption in faded ink at the right of the same line.
- **Body** (400, 1rem/1.45 on the registry; 17px/1.5 on the landing): prose and card entries. The lede is capped at 62ch.
- **Label** (400, all-small-caps, 0.04–0.06em, faded ink): table heads, `dt` keys, totals captions, the ticket's serving line and field label.
- **Mono** (400, 0.9375rem, Courier Prime, tabular-nums): table figures, the address field, commands; addresses drop to 0.8125rem and are `user-select: all`.
- **Stamp** (600, 0.6875rem, uppercase, 0.14em): the rotated stamp text.

### Named Rules
**The Typed Figure Rule.** Any number that came from memory or the chain is set in Courier Prime with tabular numerals and right-aligned. Prose never carries a figure the mono face could.

**The Small-Caps Apparatus Rule.** Keys, column heads and captions are `all-small-caps` with 0.04–0.06em tracking in faded ink; they are never bold, never colored, never uppercase-with-tracking (that treatment belongs to section heads and stamps).

## Layout

One page column at `max-width: 76rem`, padded `1.5rem 1.25rem 4rem`, centered. The masthead is a flex row on a 1px iron rule with the wordmark left and navigation (or date line) right.

The registry is a two-column margin layout: `minmax(0,1fr)` main beside a fixed 17rem aside with a 2.5rem gap, collapsing to one column at 52rem. The landing's first viewport is `minmax(0,24rem)` ticket beside `minmax(0,1fr)` thesis with a 3rem gap, stretched to `min-height: calc(100vh - 7.5rem)` above 60rem so the ticket runs the full fold; it collapses to one column at 60rem.

Grids of like items (index cards, counters) use the hairline as the gutter: `gap: 1px` over a hairline background inside a hairline border, so cards touch along rules instead of floating. Index cards fill `repeat(auto-fill, minmax(19rem, 1fr))`; counters are three equal columns. The totals strip and the on-file figures strip are four cells separated by right hairlines, two-up on phones with the middle rule dropped.

Rhythm: section heads sit 2.5rem (registry) or 3rem (landing) above and 0.75rem below; table cells pad `0.5rem 0.75rem`; card interior is 1rem with 0.5rem row gap; entry rules inside a card pad `0.12rem 0 0.18rem` at 1.35rem line height. Tables that may overflow sit in an `overflow-x: auto` board.

## Elevation & Depth

None. The system is flat paper: no drop shadows, no tonal layering, no translucency. Depth is conveyed by ink weight alone. A heavy rule (1px iron ink) closes the masthead, opens each section and separates a table's head from its body; a light rule (1px hairline) separates everything else. Containers are outlined, not lifted.

The one `box-shadow` in the build is not elevation: the stamp draws its double border with two inset rings (`inset 0 0 0 2px <paper>, inset 0 0 0 3px currentColor`) and `mix-blend-mode: multiply` so the ink sits into the paper like a real impression.

### Named Rules
**The Ruling Rule.** All separation is drawn with 1px rules in exactly two weights: iron ink for structural rules and hairline for everything else. No 2px rules, no borders in status colors except the stamp's own.

## Shapes

Square everywhere: `border-radius: 0` on every box, button, input, card and stamp. Containers are hairline-outlined rectangles; the stamp is a rectangle rotated -6° (registry cards) or -8° (ticket). The ticket's perforated edge is the only curve in the world: 15px paper-colored circles with a canary-edge ring, punched through the ticket's dashed tear line. That is the material's own device, not a radius vocabulary; nothing else may round.

The mark follows the same grammar: a beam, post and two ruled pans in 2.5px square-capped strokes, a square pivot, and one vermilion circle at the raised end of the tilted beam.

## Components

### Buttons
- **Shape:** square (0), 1px iron border.
- **Ticket submit (the only button):** iron ink fill with canary type, `0.7rem` padding, full width, 600 / 0.9375rem uppercase 0.08em Source Sans 3.
- **Hover / Active / Focus:** hover deepens to black; active `translateY(1px)`; focus-visible a 2px iron outline offset 2px. No transition, no shadow.
- **Links:** inherit color, 1px underline offset 0.18em; the same outline on focus.

### Inputs / Fields
- **Style:** 1px iron border on canary-field fill, Courier Prime 0.9375rem, `0.5rem 0.6rem` padding, full width, placeholder in canary ink.
- **Focus:** 2px iron outline, offset 2px. No glow, no border-color shift.

### Cards / Containers (Index Card)
- **Corner Style:** square.
- **Background:** the paper itself; the card grid's hairline background shows through the 1px gaps as the rules between cards.
- **Border:** none on the card; the grid carries a hairline border.
- **Internal Padding:** `1rem 1rem 1.1rem`, grid areas `head / list + balance / why + stamp`, balance column 8.5rem (7.5rem on phones).
- **Anatomy:** title (name + bold mono short address); a ruled `dl` of four entries (small-caps key left, mono value right, hairline under each); the balance at right behind a left hairline, small-caps caption over a 2.25rem bold mono figure; an italic faded "why" line; the stamp bottom-right.

### Stamp (signature)
Rotated ink stamp: 0.6875rem 600 uppercase 0.14em, `0.25rem 0.5rem` padding, `1px solid currentColor` plus two inset rings (paper, then ink), `mix-blend-mode: multiply`, in the status ink of its verdict. Rotated -6° at a card's bottom-right; -8° at the top-right of a stamped ticket answer (where the inner ring is canary). The stamp is the only element that ever carries a status color as a border.

### Daybook Board / Receipts (tables)
Fixed-column tables at 0.9375rem inside a hairline border: small-caps heads on a 1px iron rule, rows on hairlines, last row open, `.n` cells right-aligned in mono, first column `nowrap`. Row state: DECLINE rows dim to vermilion with the verdict underlined; APPROVE and GUARANTEE color only the verdict cell; NO_HISTORY rows dim to graphite. Columns never move.

### Totals / On-File Figures strip
Four cells under a hairline, right hairlines between, small-caps caption left and bold mono figure right; two-up under the breakpoint.

### Counters (ruled forms)
Three sections in a hairline grid: a numbered head (`01` in mono, faded) at 0.8125rem uppercase 0.12em, one sentence, and a mono `pre` under a hairline with the command.

### Tariff / Margin Note
An aside at 0.875rem faded ink opening with a 1px iron rule: a bold run-in word ("Tariff.") then a `dl` of small-caps keys.

### Counter Ticket (landing signature)
A GET form on canary stock with a canary-edge border: uppercase ruled head, small-caps NOW SERVING, the 4.5rem number, one labeled mono field and the submit, then fine print in canary ink above a dashed iron tear line. After submit the same ticket reprints with the answer under a second dashed line, perforation holes at the tear, the price at 1.5rem mono, and a "quoted" (ochre) or "blind" (graphite) stamp.

### Navigation
Plain links in the masthead at 0.9375rem, separated by a middle dot or 1.25rem of space; no active state beyond the page's own qualifier in the masthead. Footer repeats the two links in faded ink under a 1px iron rule.

## Do's and Don'ts

### Do:
- **Do** draw every separation as a 1px rule: iron ink for masthead, section heads and table heads; hairline for rows, entries and grid gutters.
- **Do** set every figure, address, hash and command in Courier Prime with `font-variant-numeric: tabular-nums`, right-aligned in tables.
- **Do** use `gap: 1px` over a hairline background for grids of like containers so cards touch along rules.
- **Do** mark state with the rotated stamp or a colored verdict cell, in the four fixed status inks only.
- **Do** make addresses `user-select: all` at 0.8125rem so an operator can copy one in a click.
- **Do** keep the ticket's canary materials on the ticket.

### Don't:
- **Don't** round any corner; the ticket's punched perforation is the only curve and it is a hole, not a radius.
- **Don't** add drop shadows, tints, gradients or translucency; containers are outlined on the one paper.
- **Don't** spend a status ink on a heading, link, button or accent.
- **Don't** replace the mark or the stamp with an icon set; the world has no glyph icons.
- **Don't** introduce a metric-tile hero, a feature-card grid, or a card inside a card.
- **Don't** bold or color a small-caps label; tracking and faded ink are its whole voice.
