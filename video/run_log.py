"""Run the demo for real and log it for the rendered terminal.

Every command below is executed; every output line is what it printed, with
the real commit hash, the real UTC clock, the real exit code, the real
transaction. The log carries a display schedule (seconds) that matches the
narration, so the video plays the run at a readable pace. Nothing is typed by
hand: video/public/terminal.json is the evidence, and this script regenerates it.
"""

import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
OUT = pathlib.Path(__file__).parent / "public" / "terminal.json"
B = "0xKLIENB000000000000000000000000000000000B"
A = "0xKLIENA000000000000000000000000000000000A"

env = {**os.environ, "NERACA_DB": "./data/demo.db", "PYTHONIOENCODING": "utf-8"}
for f in (ROOT / "data").glob("demo.db*"):
    f.unlink()

events: list[dict] = []


def say(t: float, text: str) -> None:
    events.append({"t": t, "kind": "say", "text": text})


def stamp(t: float, label: str = "") -> None:
    h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    events.append({"t": t, "kind": "stamp", "text": f"{label}commit {h}   {now}"})


def run(t: float, shown: str, argv: list[str], extra_env: dict | None = None, head: int | None = None,
        tail: int | None = None, session: str | None = None) -> str:
    r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, env={**env, **(extra_env or {})})
    lines = (r.stdout + r.stderr).splitlines()
    if head:
        lines = lines[:head]
    if tail:
        lines = lines[-tail:]
    events.append({"t": t, "kind": "cmd", "text": shown, "session": session})
    events.append({"t": t + 0.9, "kind": "out", "lines": lines, "exit": r.returncode, "session": session})
    print(f"[{t:>5.1f}] {shown} -> exit {r.returncode}, {len(lines)} lines")
    return r.stdout


def neraca(t, args, **kw):
    return run(t, "python -m neraca " + " ".join(args), [PY, "-m", "neraca", *args], **kw)


# act 1 (0s)
say(0.5, "NERACA - a trust bureau for the agent economy.")
say(3.0, "Agents hire each other on Virtuals ACP and settle USDC on Base. Nothing remembers who burned whom.")
stamp(6.0)

# act 2 (12s): the journal grows, the verdict moves
say(12.0, "Three agents, one shared Sibyl Memory, no other channel. PENGAMAT journals 27 observations:")
neraca(13.5, ["seed", "--before-dispute"])
neraca(18.0, ["analis"])
say(24.0, "Same budget, two clients. The premium comes straight from what memory holds.")
neraca(25.5, ["ask", A, "--budget", "50"])
neraca(33.0, ["ask", B, "--budget", "50"])
say(42.0, "Now PENGAMAT witnesses ONE event: KLIEN-B rejects a delivered job.")
neraca(43.5, ["witness"])
neraca(48.0, ["analis"])
neraca(53.0, ["ask", B, "--budget", "50"])
say(62.0, "The code did not change. The memory did.")

# act 3 (66s): fresh session - a new process that never saw the rejection
say(66.0, "Fresh session: a NEW process that never saw the rejection.")
pid = subprocess.run([PY, "-c", "import os; print(os.getpid())"], capture_output=True, text=True).stdout.strip()
stamp(68.0, label=f"new session · pid {pid} · ")
neraca(71.0, ["ask", B, "--budget", "50"], session="fresh")
neraca(82.0, ["report", B], session="fresh")
say(94.0, "It cites the rejection anyway. That is the gate.")

# act 4 (100s): deletion test
say(100.0, "The deletion test. No memory, no bureau - there is nothing to fall back to:")
out = run(101.5, "NERACA_MEMORY_DISABLED=1 python -m neraca ask 0xKLIENB…B --budget 50; echo exit=$?",
          [PY, "-m", "neraca", "ask", B, "--budget", "50"], extra_env={"NERACA_MEMORY_DISABLED": "1"})
events[-1]["lines"].append(f"exit={events[-1]['exit']}")

# act 5 (110s): the bureau grades itself
say(110.0, "The bureau grades its own verdicts and revises its doctrine - the rubric lives in REFERENCE memory:")
neraca(111.5, ["reflect"])
neraca(120.0, ["analis"], head=1)
neraca(126.0, ["reflect"], tail=1)

# act 6 (132s): selling the answer, on-chain
say(132.0, "Selling the answer. The USDC stake is gated by memory: refused for KLIEN-B, fired for KLIEN-A.")
run(133.5, "python -m neraca.onchain stake 0xKLIENB…B 1.0", [PY, "-m", "neraca.onchain", "stake", B, "1.0"])
neraca(140.0, ["ask", A, "--budget", "50"], head=4)
run(146.0, "python -m neraca.onchain stake 0xKLIENA…A 1.0", [PY, "-m", "neraca.onchain", "stake", A, "1.0"])
say(172.0, "Real agents, real jobs: PENGAMAT reads the live ACP contracts on Base mainnet. No keys.")
neraca(173.5, ["chain", "--lookback", "4000"])
neraca(186.0, ["analis"], head=6)

# close (194s)
say(194.0, "21 tests, one of them the deletion test judges run themselves.")
run(195.5, "python -m pytest -q", [PY, "-m", "pytest", "-q"], tail=1)
stamp(212.0)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(events, indent=1), encoding="utf-8")
print("wrote", OUT, len(events), "events")
