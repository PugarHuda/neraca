import os

import pytest


@pytest.fixture()
def m(tmp_path, monkeypatch):
    monkeypatch.setenv("NERACA_DB", str(tmp_path / "test.db"))
    from neraca.memory import client
    return client()


def seeded(m):
    from neraca import pengamat
    pengamat.observe(pengamat.sim_scenario(), m)
    return m


def test_observe_is_idempotent(m):
    from neraca import pengamat
    from neraca.memory import job_events
    first = pengamat.observe(pengamat.sim_scenario(), m)
    second = pengamat.observe(pengamat.sim_scenario(), m)
    assert first == 28 and second == 0
    assert len(job_events(m)) == 28


def test_analis_scores_dispute_drop(m):
    from neraca import analis, pengamat
    profiles = analis.run(seeded(m))
    a, b = profiles[pengamat.KLIEN_A], profiles[pengamat.KLIEN_B]
    assert a["score"] == 68            # 50 + 6 funded-and-accepted jobs x 3
    assert b["score"] == 25            # 50 - 25 dispute penalty
    assert b["disputes_initiated"] == 1
    assert profiles[pengamat.MAKELAR_ADDR]["score"] == 50 + 6 * 5 - 5  # 6 completed, 1 rejection received
    # deterministic: second run identical
    assert analis.run(m) == profiles


def test_makelar_verdicts(m):
    from neraca import analis, makelar, pengamat
    analis.run(seeded(m))
    good = makelar.decide(pengamat.MAKELAR_ADDR, 50, m)
    risky = makelar.decide(pengamat.KLIEN_A, 50, m)
    bad = makelar.decide(pengamat.KLIEN_B, 50, m)
    unknown = makelar.decide("0xdeadbeef", 50, m)
    assert good["verdict"] == makelar.APPROVE and good["counter_budget"] == 50
    assert risky["verdict"] == makelar.APPROVE_WITH_GUARANTEE
    assert bad["verdict"] == makelar.DECLINE and bad["counter_budget"] == 0
    assert "rejected delivered job sim-b1" in bad["reasons"]
    assert unknown["verdict"] == makelar.NO_HISTORY
    # HOT tier holds the opened negotiation
    assert m.get_state(f"negotiation:{pengamat.KLIEN_B}")["body"]["verdict"] == makelar.DECLINE


def test_memory_is_load_bearing(tmp_path, monkeypatch):
    """The deletion test the judges apply: no memory, no bureau."""
    monkeypatch.setenv("NERACA_MEMORY_DISABLED", "1")
    from neraca.memory import client
    with pytest.raises(SystemExit):
        client()


def test_verdict_changes_when_the_dispute_lands(m):
    """The demo's core claim: same question, different answer, because memory grew."""
    from neraca import analis, makelar, pengamat
    pengamat.observe(pengamat.sim_scenario(with_dispute=False), m)
    analis.run(m)
    before = makelar.decide(pengamat.KLIEN_B, 50, m)
    assert before["verdict"] == makelar.APPROVE_WITH_GUARANTEE

    assert pengamat.observe([pengamat.dispute_event()], m) == 1
    analis.run(m)
    after = makelar.decide(pengamat.KLIEN_B, 50, m)
    assert after["verdict"] == makelar.DECLINE
    assert after["score"] < before["score"]
    assert "rejected delivered job sim-b1" in after["reasons"]


def test_stake_refuses_without_an_approved_negotiation(m, monkeypatch):
    """Real USDC is priced by memory: no open guarantee in HOT, no stake.

    Runs with no CDP credentials on purpose — the memory gate must fire first,
    so anyone can reproduce the refusal without keys.
    """
    import asyncio

    from neraca import analis, makelar, onchain, pengamat
    for k in ("CDP_API_KEY_ID", "CDP_API_KEY_SECRET", "CDP_WALLET_SECRET"):
        monkeypatch.delenv(k, raising=False)
    analis.run(seeded(m))
    assert makelar.decide(pengamat.KLIEN_B, 50, m)["verdict"] == makelar.DECLINE

    with pytest.raises(SystemExit, match="priced by memory"):
        asyncio.run(onchain.stake_guarantee(pengamat.KLIEN_B, 1.0))


def test_analis_watch_reacts_to_another_process(m):
    """Coordination without a channel: ANALIS rebuilds only when the journal grows.

    This is one watch tick. PENGAMAT writing from another process is
    indistinguishable from the write below — memory is the only bus.
    """
    from neraca import analis, pengamat
    pengamat.observe(pengamat.sim_scenario(with_dispute=False), m)

    seen, profiles = analis.refresh(m, None)
    assert profiles is not None and seen == (27, 1)
    before = profiles[pengamat.KLIEN_B]["score"]

    assert analis.refresh(m, seen) == ((27, 1), None)   # memory quiet, no rebuild

    pengamat.observe([pengamat.dispute_event()], m)     # "another process" writes
    seen, profiles = analis.refresh(m, seen)
    assert seen == (28, 1) and profiles[pengamat.KLIEN_B]["score"] < before

    from neraca import makelar
    makelar.decide(pengamat.KLIEN_B, 50, m)             # a verdict to grade...
    analis.reflect(m)                                    # ...graded: nothing after it yet, doctrine holds
    assert analis.refresh(m, seen) == ((28, 1), None)
    pengamat.observe(pengamat.sim_scenario(), m)         # (no-op: all seen)
    # now a verdict that turns out wrong, in "another process": doctrine moves, watcher rescores
    m.set_reference("scoring-rubric", {**analis.get_rubric(m), "dispute_penalty": 30, "version": 2})
    seen, profiles = analis.refresh(m, seen)
    assert seen == (28, 2) and profiles[pengamat.KLIEN_B]["score"] == 20


def test_acp_phases_land_in_the_journal(m):
    """The Virtuals leg, provable without a registration: an ACP job phase
    becomes a COLD event PENGAMAT can score. Judges cannot hire our agent, so
    the mapping is asserted here instead."""
    import types

    from neraca import acp
    from neraca.memory import job_events

    for acp_phase, ours in (("REQUEST", "CREATED"), ("TRANSACTION", "FUNDED"),
                            ("EVALUATION", "DELIVERED"), ("COMPLETED", "COMPLETED"),
                            ("REJECTED", "REJECTED")):
        acp._journal(types.SimpleNamespace(
            id=f"acp-{acp_phase}", phase=types.SimpleNamespace(name=acp_phase),
            client_address="0xCLIENT", provider_address="0xPROVIDER", price=1.5))
        assert any(e["extra"]["job_id"] == f"acp-{acp_phase}"
                   and e["extra"]["phase"] == ours for e in job_events(m))

    # an unknown phase is ignored, never journaled as something it is not
    before = len(job_events(m))
    acp._journal(types.SimpleNamespace(
        id="acp-weird", phase=types.SimpleNamespace(name="SOMETHING_NEW"),
        client_address="0xCLIENT", provider_address="0xPROVIDER", price=1.0))
    assert len(job_events(m)) == before


def test_risk_endpoint_is_paywalled(m):
    """The Base/x402 leg: /risk is 402 until paid, with real v2 requirements."""
    import base64
    import json

    from fastapi.testclient import TestClient

    from neraca.server import app
    r = TestClient(app).get("/risk/0xanyone?budget=50")
    assert r.status_code == 402
    quote = json.loads(base64.b64decode(r.headers["payment-required"]))
    assert quote["x402Version"] == 2
    assert quote["accepts"][0]["network"] == "eip155:84532"   # Base Sepolia


def test_archived_agents_do_not_outrun_their_record(m):
    """Waiting out the staleness window must not launder a bad history.

    ANALIS archives agents that go quiet, and the SDK has no read-back for an
    archived entity. The journal is the record of last resort.
    """
    from neraca import analis, makelar, pengamat
    analis.run(seeded(m))
    assert makelar.decide(pengamat.KLIEN_B, 50, m)["verdict"] == makelar.DECLINE

    m.archive_entity("agent", pengamat.KLIEN_B, reason="gone quiet")
    with pytest.raises(Exception):
        m.get_entity("agent", pengamat.KLIEN_B)      # WARM really is gone

    after = makelar.decide(pengamat.KLIEN_B, 50, m)  # rebuilt from COLD
    assert after["verdict"] == makelar.DECLINE
    assert "rejected delivered job sim-b1" in after["reasons"]
    assert makelar.decide("0xneverseen", 50, m)["verdict"] == makelar.NO_HISTORY


def test_chain_logs_become_journal_events(m):
    """PENGAMAT's real eyes: raw JobManager logs -> scorable observations.

    A phase change on a job whose creation predates the scan window is
    resolved through `lookup` (memory first, then the contract); an unmapped
    phase is dropped, never guessed.
    """
    from neraca import pengamat

    def log(args, tx):
        return {"args": args, "transactionHash": bytes.fromhex(tx)}

    created = [log({"jobId": 7, "client": "0xC1", "provider": "0xP1"}, "aa" * 32)]
    phases = [
        log({"jobId": 7, "oldPhase": 0, "newPhase": 5}, "bb" * 32),    # REJECTED, seen creation
        log({"jobId": 9, "oldPhase": 2, "newPhase": 4}, "cc" * 32),    # COMPLETED, unseen creation
        log({"jobId": 11, "oldPhase": 0, "newPhase": 1}, "dd" * 32),   # NEGOTIATION -> CREATED, skipped
        log({"jobId": 13, "oldPhase": 0, "newPhase": 99}, "ee" * 32),  # unknown, dropped
    ]
    lookup = {7: ("0xC1", "0xP1", None), 9: ("0xC9", "0xP9", 12.5)}.get
    events = pengamat.chain_logs_to_events(created, phases, lookup, budgets={7: 3.25})
    assert events[0]["budget"] == 3.25 and events[1]["budget"] == 3.25   # BudgetSet rides on the job

    assert [(e["job_id"], e["phase"]) for e in events] == [
        ("acp-7", "CREATED"), ("acp-7", "REJECTED"), ("acp-9", "COMPLETED")]
    assert events[1]["client_addr"] == "0xC1" and events[1]["tx"] == "0x" + "bb" * 32
    assert events[2]["provider"] == "0xP9" and events[2]["budget"] == 12.5

    assert pengamat.observe(events, m) == 3
    assert pengamat.observe(events, m) == 0        # idempotent on (job, phase)

    # most of a job's life is memos: an approved signature moves the job, a
    # refusal is a rejection, and a memo from before the window resolves its
    # job through the contract (phase unknown, so only a refusal survives)
    new_memos = [log({"memoId": 501, "jobId": 7, "sender": "0xP1", "memoType": 0, "nextPhase": 4}, "11" * 32)]
    signed = [
        log({"memoId": 501, "approver": "0xC1", "approved": True, "reason": "ok"}, "22" * 32),   # -> COMPLETED
        log({"memoId": 777, "approver": "0xC9", "approved": False, "reason": "no"}, "33" * 32),  # old memo, refused
        log({"memoId": 778, "approver": "0xC9", "approved": True, "reason": "ok"}, "44" * 32),   # old memo, phase unknown
    ]
    memo_job = {777: (9, None), 778: (9, None)}.get
    events = pengamat.chain_logs_to_events([], [], lookup, new_memos, signed, memo_job)
    assert [(e["job_id"], e["phase"]) for e in events] == [("acp-7", "COMPLETED"), ("acp-9", "REJECTED")]
    assert events[0]["client_addr"] == "0xC1" and events[0]["provider"] == "0xP1"


def test_settlement_is_an_observation(m):
    """An agent that pays its x402 invoices has told the bureau something."""
    from neraca import analis
    from neraca.memory import record_settlement
    assert record_settlement(m, payer="0xPAYER", payee="0xUS", amount_usd=0.05,
                             tx="0xabc", resource="/risk/0xX") is not None
    assert record_settlement(m, payer="0xPAYER", payee="0xUS", amount_usd=0.05,
                             tx="0xabc", resource="/risk/0xX") is None       # idempotent on tx
    p = analis.run(m)["0xPAYER"]
    assert p["invoices_paid"] == 1 and p["score"] == 52


def test_verdicts_are_journaled_and_graded(m):
    """MAKELAR journals what it said; ANALIS grades it against what happened
    next and revises the rubric in REFERENCE - remembered doctrine, versioned."""
    from neraca import analis, makelar, pengamat
    from neraca.memory import get_rubric, verdict_events

    pengamat.observe(pengamat.sim_scenario(with_dispute=False), m)
    analis.run(m)
    assert makelar.decide(pengamat.KLIEN_B, 50, m)["verdict"] == makelar.APPROVE_WITH_GUARANTEE
    assert [v["extra"]["verdict"] for v in verdict_events(m)] == [makelar.APPROVE_WITH_GUARANTEE]

    assert analis.reflect(m)["graded"] == 0                # nothing happened yet: no grade
    pengamat.observe([pengamat.dispute_event()], m)        # then B rejects the delivery

    r = analis.reflect(m)
    assert r["graded"] == 1 and r["false_approve"] == 1
    assert r["changes"] == {"dispute_penalty": [25, 30], "approve_threshold": [70, 75]}
    rubric = get_rubric(m)
    assert rubric["version"] == 2 and rubric["history"][-1]["changes"] == r["changes"]

    analis.run(m)                                          # the new doctrine applies
    assert makelar.decide(pengamat.KLIEN_B, 50, m)["score"] == 20   # 50 - 30
    assert analis.reflect(m)["changes"] == {}              # same evidence, no double count


def test_ask_as_of_replays_the_journal(m):
    """Time travel: the verdict as it stood before the dispute landed."""
    import time
    from datetime import datetime, timezone
    from neraca import analis, makelar, pengamat

    pengamat.observe(pengamat.sim_scenario(with_dispute=False), m)
    time.sleep(0.01)
    cut = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    time.sleep(0.01)
    pengamat.observe([pengamat.dispute_event()], m)
    analis.run(m)

    now = makelar.decide(pengamat.KLIEN_B, 50, m)
    then = makelar.decide(pengamat.KLIEN_B, 50, m, as_of=cut)
    assert now["verdict"] == makelar.DECLINE
    assert then["verdict"] == makelar.APPROVE_WITH_GUARANTEE and then["as_of"] == cut
    assert len(makelar.evidence(pengamat.KLIEN_B, m, as_of=cut)) == 3   # the rejection is after the cut
    # a replay opens no negotiation and journals no verdict
    assert m.get_state(f"negotiation:{pengamat.KLIEN_B}")["body"]["verdict"] == makelar.DECLINE


def test_search_spans_tiers(m):
    from neraca import analis, pengamat
    from neraca.memory import search
    analis.run(seeded(m))
    hits = search(m, "sim-b1")
    assert hits and any("sim-b1" in json_dumps(h) for h in hits)


def json_dumps(x):
    import json
    return json.dumps(x, default=str)


def test_storefront_is_priced_by_memory(m):
    """The quote grows with what the bureau remembers; the status page renders memory."""
    from fastapi.testclient import TestClient
    from neraca import analis, pengamat
    from neraca.server import app, quote

    c = TestClient(app)
    assert quote("0xnobody", m) == 0.01                    # blind: cheapest
    analis.run(seeded(m))
    assert quote(pengamat.KLIEN_B, m) == 0.05              # 4 remembered events
    assert quote(pengamat.MAKELAR_ADDR, m) == 0.25         # capped
    assert c.get(f"/quote/{pengamat.KLIEN_B}").json()["price_usd"] == 0.05
    assert c.get(f"/risk/{pengamat.KLIEN_B}?budget=50").status_code == 402

    page = c.get("/")
    assert page.status_code == 200 and "text/html" in page.headers["content-type"]
    assert pengamat.KLIEN_B in page.text and 'id="profiles"' in page.text


def test_directory_names_real_addresses_without_mixing_claims(m):
    """The marketplace's own numbers ride beside NERACA's score, never inside it."""
    from neraca import analis, makelar, pengamat

    def fetch(keyword):
        return [{"walletAddress": "0xABCDEF", "name": "aixbt",
                 "metrics": {"successRate": 91.5, "successfulJobCount": 32806, "uniqueBuyerCount": 900}}]

    assert pengamat.refresh_directory(m, keywords=("x",), fetch=fetch) == {"entries": 1, "new": 1, "skipped": []}
    assert pengamat.refresh_directory(m, keywords=("x",), fetch=fetch)["new"] == 0   # idempotent

    pengamat.observe([dict(job_id="j1", phase="CREATED", client_addr="0xClient", provider="0xabcdef")], m)
    analis.run(m)
    d = makelar.decide("0xabcdef", 50, m)
    assert d["known_as"] == "aixbt" and d["marketplace_claims"]["jobs"] == 32806
    assert d["score"] == 50            # 32,806 marketplace jobs bought it nothing: NERACA saw one CREATED
    assert "known_as" not in makelar.decide("0xClient", 50, m)


def test_stake_refuses_when_memory_moved_since_the_negotiation(m, monkeypatch):
    """An open negotiation is necessary, not sufficient. The dispute lands,
    nobody re-asks, HOT still says APPROVE_WITH_GUARANTEE - the stake must not fire."""
    import asyncio
    from neraca import analis, makelar, onchain, pengamat
    for k in ("NERACA_STAKE_KEY", "CDP_API_KEY_ID", "CDP_API_KEY_SECRET", "CDP_WALLET_SECRET"):
        monkeypatch.delenv(k, raising=False)
    pengamat.observe(pengamat.sim_scenario(with_dispute=False), m)
    analis.run(m)
    assert makelar.decide(pengamat.KLIEN_B, 50, m)["verdict"] == makelar.APPROVE_WITH_GUARANTEE
    pengamat.observe([pengamat.dispute_event()], m)
    analis.run(m)
    assert m.get_state(f"negotiation:{pengamat.KLIEN_B}")["body"]["verdict"] == makelar.APPROVE_WITH_GUARANTEE
    with pytest.raises(SystemExit, match="memory moved"):
        asyncio.run(onchain.stake_guarantee(pengamat.KLIEN_B, 1.0))


def test_addresses_have_one_spelling(m):
    """`ask 0xabc...` and `ask 0xABC...` are the same counterparty, not two strangers."""
    from neraca import analis, makelar, pengamat
    from neraca.server import quote
    real = "0x5FaCEbD66D78A69b400dC702049374B95745FBc5"
    pengamat.observe([dict(job_id="r1", phase="CREATED", client_addr="0xC1", provider=real.lower())], m)
    analis.run(m)
    assert makelar.decide(real.lower(), 50, m)["score"] == 50
    assert makelar.decide(real.upper().replace("0X", "0x"), 50, m)["counterparty"] == real
    assert len(makelar.evidence(real.lower(), m)) == 1
    assert quote(real.lower(), m) == quote(real, m) == 0.02
    assert makelar.decide(pengamat.KLIEN_B.lower(), 50, m)["verdict"] == makelar.NO_HISTORY  # labels are literal


def test_mcp_server_answers_from_memory(m):
    """Another agent asks the bureau over MCP; the answer is the same memory read."""
    import asyncio
    import json
    import os
    import sys

    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from neraca import analis, pengamat

    analis.run(seeded(m))
    params = StdioServerParameters(command=sys.executable, args=["-m", "neraca.mcp_server"],
                                   env={**os.environ, "NERACA_DB": os.environ["NERACA_DB"]})

    async def go():
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as s:
                await s.initialize()
                tools = {t.name for t in (await s.list_tools()).tools}
                res = await s.call_tool("ask", {"counterparty": pengamat.KLIEN_B, "budget": 50})
                return tools, res

    tools, res = asyncio.run(go())
    assert {"ask", "quote", "report", "search"} <= tools
    body = res.structured_content or json.loads(res.content[0].text)
    body = body.get("result", body)
    assert body["verdict"] == "DECLINE" and "rejected delivered job sim-b1" in body["reasons"]
