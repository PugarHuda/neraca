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

    seen, profiles = analis.refresh(m, -1)
    assert profiles is not None and seen == 27
    before = profiles[pengamat.KLIEN_B]["score"]

    assert analis.refresh(m, seen) == (27, None)      # journal quiet, no rebuild

    pengamat.observe([pengamat.dispute_event()], m)   # "another process" writes
    seen, profiles = analis.refresh(m, seen)
    assert seen == 28 and profiles[pengamat.KLIEN_B]["score"] < before


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
