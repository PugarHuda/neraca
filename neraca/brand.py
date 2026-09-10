"""NERACA's mark: a balance scale drawn as ledger rules.

Neraca is Indonesian for a balance scale and for the ledger that balances.
The mark is both at once: a beam on a post, and two pans that are ruled
slips of ledger paper. The beam tilts — a verdict is never a tie. Hairlines
only, no radius, ink on paper, the same vocabulary as every page.

Served at /logo.svg and /favicon.svg; inlined in the mastheads.
"""

INK = "#1b1c17"
PAPER = "#e9eedf"
VERMILION = "#b3301c"


def mark(size: int = 28, ink: str = INK, paper: str | None = None) -> str:
    """The scale alone. `paper` fills the pans (favicon); None keeps them open."""
    fill = paper or "none"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}" role="img" aria-label="NERACA">
<g fill="none" stroke="{ink}" stroke-width="3" stroke-linecap="square">
  <path d="M32 12v40M20 54h24"/>
  <path d="M11 22l42-6" />
  <path d="M11 22v9M53 16v9"/>
  <g fill="{fill}"><path d="M3 31h16v3H3zM3 37h16M3 43h12"/><path d="M45 25h16v3H45zM45 31h16M45 37h12"/></g>
</g>
<rect x="29.5" y="16.5" width="5" height="5" fill="{ink}"/>
<circle cx="53" cy="16" r="2.4" fill="{VERMILION}"/>
</svg>"""


def wordmark(height: int = 22) -> str:
    """Mark + NERACA, set in the pages' own letterspaced sans, for mastheads.
    The text carries the name; the mark is decorative here, so assistive tech
    reads NERACA once, not twice."""
    decorative = mark(height).replace('role="img" aria-label="NERACA"', 'aria-hidden="true" focusable="false"', 1)
    return f'<span class="brand">{decorative}<span>NERACA</span></span>'


FAVICON = mark(64, paper=PAPER)
LOGO = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 96" width="360" height="96" role="img" aria-label="NERACA — trust bureau for the agent economy">
<rect width="360" height="96" fill="{PAPER}"/>
<g transform="translate(16 16)">{mark(64).split('>', 1)[1].rsplit('</svg>', 1)[0]}</g>
<text x="96" y="52" font-family="'Source Sans 3', system-ui, sans-serif" font-size="30" font-weight="600" letter-spacing="5" fill="{INK}">NERACA</text>
<text x="96" y="74" font-family="'Source Sans 3', system-ui, sans-serif" font-size="13" letter-spacing="1" fill="#454a3e">TRUST BUREAU FOR THE AGENT ECONOMY</text>
<path d="M96 60h248" stroke="{INK}" stroke-width="1"/>
</svg>"""
