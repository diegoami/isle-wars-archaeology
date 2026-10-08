#!/usr/bin/env python3
"""Tabulate the committed E020 net observations (T40): what the three sittings' nets show.

    python3 experiments/E020-wine-first-run/reader/tabulate.py [--out measurements/nets-tabulation-r2.json]

Reads the net observations the committed records hold (tools/check_counts.py's `net:seq` groups of
`cmb-accumulation`, R1) and prints and, with --out, writes: the number of nets per sitting, the
distribution of the armies each side lost between the two frames, the attacker's share of all
armies lost in them, the nets by attacker size and by defender size, and the VIPC split. A net is
what changed between two frames about 1.4 s apart (exchange_events.py): one or more exchanges, never
known to be one. This is a descriptive measurement only; no claim rule reads it, and it says nothing
about a single exchange. The exchanges the records hold (none, from these sittings) are counted
beside it, never mixed in.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_counts  # noqa: E402


def tabulate(scenarios=check_counts.SCENARIOS, records_root=check_counts.RECORDS):
    batch = check_counts.load_batches(scenarios)["cmb-accumulation"]
    exchanges, nets, problems = check_counts.batch_observations("cmb-accumulation", batch, records_root)
    events = nets
    vipc = {int(v) for v in batch["vipc_countries"].split()}
    lost = Counter()
    by_attacker, by_defender, per_sitting = Counter(), Counter(), Counter()
    attacker_lost = defender_lost = inside = 0
    for (sitting, game, _seq), v in sorted(events.items()):
        a0, a1 = int(v["counter:attacker-before"]), int(v["counter:attacker-after"])
        d0, d1 = int(v["counter:defender-before"]), int(v["counter:defender-after"])
        lost[(a0 - a1, d0 - d1)] += 1
        attacker_lost += a0 - a1
        defender_lost += d0 - d1
        by_attacker[a0] += 1
        by_defender[d0] += 1
        per_sitting[f"{sitting}:game{game}"] += 1
        inside += int(v["country:attacker"]) in vipc
    total = attacker_lost + defender_lost
    return {
        "what": "what the committed E020 cmb-accumulation net observations show (numbers only; descriptive, "
                "never exchanges)",
        "problems": problems,
        "exchanges": len(exchanges),
        "net_observations": len(events),
        "nets_by_sitting_and_game": dict(sorted(per_sitting.items())),
        "armies_lost_per_net": {f"attacker {a}, defender {d}": n for (a, d), n in sorted(lost.items())},
        "nets_with_exactly_one_army_lost_in_all": sum(n for (a, d), n in lost.items() if a + d == 1),
        "armies_lost_attacker": attacker_lost, "armies_lost_defender": defender_lost,
        "attacker_share_of_armies_lost": round(attacker_lost / total, 4) if total else None,
        "nets_by_attacker_before": {str(k): n for k, n in sorted(by_attacker.items())},
        "nets_by_defender_before": {str(k): n for k, n in sorted(by_defender.items())},
        "attacker_in_vipc_list": inside, "attacker_outside_vipc_list": len(events) - inside,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    table = tabulate()
    text = json.dumps(table, indent=1) + "\n"
    print(text, end="")
    if args.out:
        with open(args.out, "x", encoding="utf-8") as handle:
            handle.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
