"""Narration for the demo: neural voice + word-timed subtitles via edge-tts.

Each segment is pinned to the second it starts in the terminal recording
(video/demo.ps1) or the browser clip. Output: video/audio/<id>.mp3 and
video/audio/<id>.json (word boundaries) which the Remotion composition reads.
"""

import asyncio
import json
import pathlib

import edge_tts

VOICE = "en-US-AndrewNeural"
OUT = pathlib.Path(__file__).parent / "audio"

# (id, start second in the terminal clip, text)
TERMINAL = [
    ("t01", 0.5, "NERACA is a trust bureau for the agent economy. Agents hire each other on Virtuals ACP and settle in USDC on Base, and nothing remembers who burned whom. This bureau does."),
    ("t02", 12.5, "Three agents share nothing but Sibyl Memory. The scout journals twenty-seven observations into the cold tier, and the analyst turns them into reputation profiles."),
    ("t03", 24.5, "Same budget, two clients. KLIEN-A has six clean jobs behind it and pays a one percent premium. KLIEN-B is clean but thin, and pays ten. The price comes straight from what memory holds."),
    ("t04", 42.5, "Now the scout witnesses one event: KLIEN-B rejects a delivered job. The analyst rebuilds, and the same question gets a different answer: decline, citing the rejection. The code did not change. The memory did."),
    ("t05", 66.5, "Fresh session. This is a brand-new process that never saw the rejection. It opens the same Sibyl store, and it cites the rejection anyway. That is the gate."),
    ("t06", 100.5, "The deletion test. Disable the memory layer and the bureau does not degrade. It exits with code one. There is nothing to fall back to."),
    ("t07", 110.5, "The bureau also grades itself. Its first verdict on KLIEN-B was an approval, and the rejection landed afterwards. Reflect scores it as a false approve and tightens the rubric to version two, in reference memory. Run it again and the doctrine holds."),
    ("t08", 132.5, "Selling the answer. The USDC guarantee stake is gated by memory: for KLIEN-B it refuses before touching a key. For KLIEN-A, with an open guarantee, it fires a real transfer on Base Sepolia."),
    ("t09", 172.5, "And the scout has real eyes. It reads the live ACP contracts on Base mainnet over a public RPC, resumes from a cursor kept in hot memory, and real agents get real balances."),
    ("t10", 194.5, "Twenty-one tests, one of them the deletion test judges can run themselves. The code is public, and the bureau is live on Vercel."),
]

BROWSER = [
    ("b01", 0.5, "The storefront. Type an address into the counter ticket and the bureau prints what its memory is worth: aixbt, one remembered event, two cents. A stranger is priced blind at one cent."),
    ("b02", 14.0, "The registry is rendered straight from memory: the daybook of verdicts, an index card per agent with its balance and stamp, and the invoices the storefront saw paid. Every number on the page is a memory read."),
]


async def speak(seg_id: str, text: str) -> None:
    OUT.mkdir(exist_ok=True)
    tts = edge_tts.Communicate(text, VOICE, rate="-4%", boundary="WordBoundary")
    words = []
    with open(OUT / f"{seg_id}.mp3", "wb") as f:
        async for chunk in tts.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({"t": chunk["offset"] / 1e7, "d": chunk["duration"] / 1e7, "w": chunk["text"]})
    (OUT / f"{seg_id}.json").write_text(json.dumps({"text": text, "words": words}), encoding="utf-8")
    print(seg_id, f"{words[-1]['t'] + words[-1]['d']:.1f}s" if words else "no timing")


async def main() -> None:
    for seg_id, _, text in TERMINAL + BROWSER:
        await speak(seg_id, text)
    manifest = {"terminal": [{"id": i, "start": s} for i, s, _ in TERMINAL],
                "browser": [{"id": i, "start": s} for i, s, _ in BROWSER]}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
