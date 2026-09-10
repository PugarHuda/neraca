"""NERACA as an MCP server: any agent that speaks MCP can ask the bureau.

Claude Code, Cursor, an OpenClaw/Hermes agent, another Python agent - they
add one stdio server and get `ask`, `quote`, `report`, `search` as tools.
Every tool is a read of Sibyl Memory; nothing here computes trust from
scratch. No memory, no bureau - the MCP server fails the same way the CLI does.

Run:   python -m neraca.mcp_server            (stdio; NERACA_DB picks the store)
Claude Code:  claude mcp add neraca -- python -m neraca.mcp_server
"""

from mcp.server.mcpserver import MCPServer

from . import makelar
from .memory import client, job_events
from .memory import search as memory_search

server = MCPServer("neraca", instructions=(
    "NERACA is a trust bureau for the agent economy. Before paying or hiring an agent, "
    "call `ask` with its address and your budget in USDC: you get APPROVE, "
    "APPROVE_WITH_GUARANTEE (with a counter-budget and premium), DECLINE, or NO_HISTORY, "
    "each backed by remembered evidence. `report` lists that evidence; `quote` says what the "
    "paid x402 answer would cost; `search` is full-text over everything the bureau remembers."))


@server.tool()
def ask(counterparty: str, budget: float = 50.0) -> dict:
    """Should I deal with this counterparty for this budget (USDC)? A memory-priced verdict
    with reasons; opens a negotiation in HOT memory and journals the verdict."""
    return makelar.decide(counterparty, budget, client())


@server.tool()
def quote(counterparty: str) -> dict:
    """What the paid x402 risk report on this counterparty would cost, and why:
    $0.01 blind plus $0.01 per remembered event, capped at $0.25."""
    from .server import BLIND_PRICE, PER_EVENT, PRICE_CAP
    from .memory import norm
    cp = norm(counterparty)
    n = sum(1 for e in job_events(client()) if cp in (e["extra"]["client"], e["extra"]["provider"]))
    return {"counterparty": cp, "remembered_events": n,
            "price_usd": round(min(BLIND_PRICE + PER_EVENT * n, PRICE_CAP), 2)}


@server.tool()
def report(counterparty: str, as_of: str | None = None) -> list[dict]:
    """Every remembered event behind a verdict on this counterparty, oldest first.
    `as_of` (ISO timestamp) returns the evidence as it stood at that moment."""
    return makelar.evidence(counterparty, client(), as_of=as_of)


@server.tool()
def search(query: str, limit: int = 20) -> list[dict]:
    """Full-text search across every memory tier: journal, profiles, doctrine, open negotiations."""
    return memory_search(client(), query, limit=limit)


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
