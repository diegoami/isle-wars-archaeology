#!/usr/bin/env python3
"""What varies across E006 records FIRST..LAST: measurements/varies-E006-rFIRST-rLAST-<UTC time>.md, never over a file.

Usage: E006_BUNDLES=<dir> python3 experiments/E006-iw-dos-driver/scripts/varies.py FIRST LAST
For each observation (by step, field and order) and each output, the number of distinct values over the records;
then, for the outputs that differ, the number of distinct texts once the repeat's own work directory (/tmp/wN), its
display (:N) and times and clocks are replaced by placeholders, read from the bundles (E006_BUNDLES, by sha256).
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "E006-iw-dos-driver" / "measurements"
NORMAL = [(re.compile(r"/tmp/w\d+"), "/tmp/wN"), (re.compile(r"Xvfb :\d+ "), "Xvfb :N "),
          (re.compile(r"^\d\d:\d\d:\d\d ", re.M), "HH:MM:SS "), (re.compile(r"\d+\.\d+ s\b"), "T s"),
          (re.compile(r"(seconds after launch|after) \d+(\.\d+)?"), r"\1 T")]


def main(first, last):
    records = [json.loads((ROOT / "runs/E006" / f"E006-r{n:04d}.json").read_text()) for n in range(first, last + 1)]
    values = defaultdict(set)
    for r in records:
        seen = defaultdict(int)
        for o in r["observations"]:
            key = (o["step"], o["field"])
            values[key + (seen[key],)].add(o["value"])
            seen[key] += 1
    outputs = defaultdict(set)
    for r in records:
        for o in r["outputs"]:
            outputs[o["name"]].add(o["sha256"])
    lines = [f"# What varies, E006-r{first:04d} to E006-r{last:04d}", "",
             f"Made by `scripts/varies.py {first} {last}`. {len(records)} records, "
             f"{len(values)} observations each (by step, field and order).", "",
             "## Observations with more than one value", "", "| step | field | distinct values |", "| --- | --- | --- |"]
    lines += [f"| {s} | {f} | {len(v)} |" for (s, f, _), v in sorted(values.items()) if len(v) > 1]
    lines += ["", "## Outputs", "", "| output | distinct sha256 | distinct once normalised |", "| --- | --- | --- |"]
    bundles = Path(os.environ["E006_BUNDLES"])
    for name, digests in sorted(outputs.items()):
        normal = "same file" if len(digests) == 1 else ""
        if len(digests) > 1 and name.endswith((".log", ".txt")):
            texts = set()
            for d in digests:
                text = (bundles / f"{d[:16]}-{name}").read_text(errors="replace")
                for pattern, repl in NORMAL:
                    text = pattern.sub(repl, text)
                texts.add(text)
            normal = str(len(texts))
        lines.append(f"| {name} | {len(digests)} | {normal} |")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = OUT / f"varies-E006-r{first:04d}-r{last:04d}-{stamp}.md"
    with open(target, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(int(sys.argv[1]), int(sys.argv[2]))
