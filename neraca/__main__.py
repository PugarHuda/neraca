"""NERACA CLI — python -m neraca <command>"""

import argparse
import json

from . import analis, makelar, pengamat
from .memory import client, get_rubric, job_events


def main() -> None:
    ap = argparse.ArgumentParser(prog="neraca", description="Trust bureau for the agent economy")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("seed", help="journal the simulated scenario (KLIEN-A good, KLIEN-B disputes)")
    p.add_argument("--before-dispute", action="store_true",
                   help="stop one event short of KLIEN-B's rejection, to land it live")
    sub.add_parser("witness", help="PENGAMAT witnesses KLIEN-B's rejection, live")
    sub.add_parser("analis", help="rebuild reputation profiles from the journal")
    p = sub.add_parser("ask", help="should I deal with this counterparty?")
    p.add_argument("counterparty")
    p.add_argument("--budget", type=float, required=True)
    p = sub.add_parser("report", help="full remembered evidence for a counterparty")
    p.add_argument("counterparty")
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
    elif args.cmd == "analis":
        profiles = analis.run(m)
        for addr, p in sorted(profiles.items(), key=lambda kv: kv[1]["score"]):
            print(f"{p['score']:>3}  {addr}  ok={p['jobs_ok']} disputes={p['disputes_initiated']} "
                  f"rejected_on={p['rejections_received']} expired={p['jobs_expired']}")
    elif args.cmd == "ask":
        d = makelar.decide(args.counterparty, args.budget, m)
        print(json.dumps(d, indent=2))
    elif args.cmd == "report":
        for e in makelar.evidence(args.counterparty, m):
            print(json.dumps(e))
    elif args.cmd == "events":
        for e in job_events(m):
            print(json.dumps(e["extra"] | {"ts": e["ts"]}))


if __name__ == "__main__":
    main()
