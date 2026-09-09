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
    assert a["score"] == 50            # clients gain nothing, lose nothing when clean
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
