#!/usr/bin/env python3
"""Which orders of the four colours the last line of a save can have, given the card-count line (F009).

    hand-order.py BATCH_DIR      BATCH_DIR must not exist: it is created, and hand-order.tsv is created in it

The card-count line `a , b , c , d` is Blue, Red, Green, Brown (the scoreboard's rows: check-cards.py). The last line
has four comma-separated fields of card digits. For each of the 24 orders of the four colours over the last line's
fields, this counts the natural saves (E005 and E007) in which every field's length equals the card count of the colour
the order puts there, and lists the digits seen. Needs E005_BUNDLES and E007_BUNDLES. Never overwrites (rule 20).
"""
import itertools
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS = ("E005", "E007")
COLOURS = ("blue", "red", "green", "brown")


def natural_saves():
    for experiment in EXPERIMENTS:
        bundles = Path(os.environ[f"{experiment}_BUNDLES"])
        for path in sorted((ROOT / "runs" / experiment).glob(f"{experiment}-r*.json")):
            record = json.loads(path.read_text())
            if record["arm"].startswith("load-"):
                continue
            manifest = json.loads((ROOT / "evidence" / experiment / f"{record['run_id']}.manifest.json").read_text())
            seen = set()
            for entry in manifest["files"]:
                if entry["name"].endswith("-ISLEWAR.SAV") or entry["name"] == "end-ISLEWAR.SAV":
                    if entry["name"].endswith("ISLEWAR.SAV") and entry["sha256"] not in seen:
                        seen.add(entry["sha256"])
                        yield entry["sha256"], (bundles / entry["asset"]).read_bytes()


def main(batch):
    batch = Path(batch)
    batch.mkdir(parents=True)
    saves = {}
    for sha, data in natural_saves():
        saves[sha] = data
    rows, digits = [], Counter()
    parsed = []
    for data in saves.values():
        lines = data.split(b"\r\n")
        counts = [int(x) for x in re.findall(rb"\d+", lines[-3])]
        hands = lines[-2].decode().split(",")
        parsed.append((counts, hands))
        for h in hands:
            digits.update(h)
    for order in itertools.permutations(range(4)):
        fits = sum(1 for counts, hands in parsed
                   if all(len(hands[i]) == counts[COLOURS.index(c)] for i, c in zip(range(4), (COLOURS[j] for j in order))))
        rows.append((" ".join(COLOURS[j] for j in order), fits, len(parsed)))
    rows.sort(key=lambda r: -r[1])
    with open(batch / "hand-order.tsv", "xb") as fh:
        fh.write(("order of the colours over the last line's four fields\tsaves where every field's length equals that "
                  "colour's count\tnatural saves\n" + "".join(f"{a}\t{b}\t{c}\n" for a, b, c in rows)).encode())
    with open(batch / "card-digits-seen.tsv", "xb") as fh:
        fh.write(("digit\tcards in the natural saves' last lines (summed over saves, so a card is counted once per save)\n"
                  + "".join(f"{d}\t{n}\n" for d, n in sorted(digits.items()))).encode())
    print(f"{len(parsed)} natural saves; best order {rows[0][0]!r} fits {rows[0][1]}; next best fits {rows[1][1]}; digits {sorted(digits)}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
