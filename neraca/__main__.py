"""NERACA CLI — python -m neraca <command>"""

import argparse
import json

from . import analis, makelar, pengamat
from .memory import client, get_rubric, job_events, search


def main() -> None:
    ap = argparse.ArgumentParser(prog="neraca", description="Trust bureau for the agent economy")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("seed", help="journal the simulated scenario (KLIEN-A good, KLIEN-B disputes)")
    p.add_argument("--before-dispute", action="store_true",
                   help="stop one event short of KLIEN-B's rejection, to land it live")
    sub.add_parser("witness", help="PENGAMAT witnesses KLIEN-B's rejection, live")
    p = sub.add_parser("chain", help="PENGAMAT reads real ACP jobs off Base mainnet (resumable)")
    p.add_argument("--lookback", type=int, default=20000, help="blocks to scan on first run")
    sub.add_parser("analis", help="rebuild reputation profiles from the journal")
    sub.add_parser("watch", help="ANALIS as a live process: reacts when another process writes")
    sub.add_parser("reflect", help="ANALIS grades past verdicts and tunes the rubric in REFERENCE")
    sub.add_parser("rubric", help="the doctrine as memory holds it, with its version history")
    p = sub.add_parser("ask", help="should I deal with this counterparty?")
    p.add_argument("counterparty")
    p.add_argument("--budget", type=float, required=True)
    p.add_argument("--as-of", help="ISO timestamp: answer from the journal as it stood then")
    p = sub.add_parser("report", help="full remembered evidence for a counterparty")
    p.add_argument("counterparty")
    p.add_argument("--as-of", help="ISO timestamp: the evidence as it stood then")
    p = sub.add_parser("search", help="full-text search across every memory tier")
    p.add_argument("query")
    sub.add_parser("events", help="dump the COLD journal")
    args = ap.parse_args()

    m = client()  # exits here if NERACA_MEMORY_DISABLED — no memory, no bureau
    get_rubric(m)  # seed REFERENCE rubric on first touch

    if args.cmd == "seed":
        n = pengamat.observe(pengamat.sim_scenario(not args.before_dispute), m)
        print(f"journaled {n} new observations")
    elif args.cmd == "witness":
        n = pengamat.observe([pengamat.dispute_event()], m)
        print(f"PENGAMAT journaled {n} new observation "
              f"(REJECTED sim-b1) - rerun `analis` to see the score move")
    elif args.cmd == "chain":
        r = pengamat.observe_chain(m, lookback=args.lookback)
        print(f"PENGAMAT read Base mainnet blocks {r['from_block']}..{r['to_block']}: "
              f"{r['job_created']} jobs created, {r['phase_updates']} phase updates, "
              f"{r['memos_signed']} memos signed -> {r['journaled']} new observations "
              f"(cursor saved in HOT memory)")
    elif args.cmd == "watch":
        analis.watch(m)
    elif args.cmd == "analis":
        profiles = analis.run(m)
        for addr, p in sorted(profiles.items(), key=lambda kv: kv[1]["score"]):
            print(f"{p['score']:>3}  {addr}  ok={p['jobs_ok']} disputes={p['disputes_initiated']} "
                  f"rejected_on={p['rejections_received']} expired={p['jobs_expired']} "
                  f"paid={p['invoices_paid']}")
    elif args.cmd == "reflect":
        r = analis.reflect(m)
        print(f"graded {r['graded']} verdict(s): {r['false_approve']} false approve, "
              f"{r['false_decline']} false decline")
        for c in r["cases"]:
            print(f"   {c['outcome']:<14} {c['verdict']:<22} {c['counterparty']}  then {c['then']}")
        if r["changes"]:
            print(f"doctrine revised -> rubric v{r['rubric_version']}: "
                  + ", ".join(f"{k} {a}->{b}" for k, (a, b) in r["changes"].items()))
            print("rerun `analis`: every profile is rescored under the new rubric")
        else:
            print("doctrine holds - nothing to revise")
    elif args.cmd == "rubric":
        print(json.dumps(get_rubric(m), indent=2))
    elif args.cmd == "ask":
        d = makelar.decide(args.counterparty, args.budget, m, as_of=args.as_of)
        print(json.dumps(d, indent=2))
    elif args.cmd == "report":
        for e in makelar.evidence(args.counterparty, m, as_of=args.as_of):
            print(json.dumps(e))
    elif args.cmd == "search":
        for row in search(m, args.query):
            print(json.dumps(row, default=str))
    elif args.cmd == "events":
        for e in job_events(m):
            print(json.dumps(e["extra"] | {"ts": e["ts"]}))


if __name__ == "__main__":
    main()
