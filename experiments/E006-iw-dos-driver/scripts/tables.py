#!/usr/bin/env python3
"""A table of the E006 records FIRST..LAST: measurements/tables/E006-rFIRST-rLAST.md, never over a file.

Usage: python3 experiments/E006-iw-dos-driver/scripts/tables.py FIRST LAST     (run numbers, e.g. 1 10)
Per repeat: arm, status, the before/after pixel sha256, start_state.sha256, the times, DOSBox-X's exit; then, per
arm, the median and range of the repeat time over its completed repeats, and which values vary.
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "E006-iw-dos-driver" / "measurements" / "tables"
FIELDS = {
    "before": "before.png raw RGB8 pixels sha256",
    "after": "after.png raw RGB8 pixels sha256",
    "option box s": "option-box reached and stable, seconds after launch",
    "dialog s": "select-level reached and stable, seconds after launch",
    "exit": "DOSBox-X exit after SIGTERM (s); exit status",
    "gone": "DOSBox-X already gone at terminate, exit status",
    "reset": "run copy after reset equals the baseline",
    "repeat s": "repeat seconds, start to end of finish",
}


def value(record, field):
    found = [o["value"] for o in record["observations"] if o["field"] == field]
    return found[-1] if found else ""


def main(first, last):
    records = []
    for n in range(first, last + 1):
        path = ROOT / "runs" / "E006" / f"E006-r{n:04d}.json"
        records.append(json.loads(path.read_text(encoding="utf-8")))
    lines = [f"# E006-r{first:04d} to E006-r{last:04d}", "",
             f"Made by `scripts/tables.py {first} {last}` from `runs/E006/`. Hashes are the first 16 hex digits.", "",
             "| run | arm | status | start_state | " + " | ".join(FIELDS) + " |",
             "| --- " * (4 + len(FIELDS)) + "|"]
    for r in records:
        cells = [r["run_id"], r["arm"], r["status"][:70], r["start_state"]["sha256"][:16]]
        cells += [value(r, f)[:16] if k in ("before", "after") else value(r, f) for k, f in FIELDS.items()]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "| arm | completed | median repeat s | range s | before hashes | after hashes | start states |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for arm in sorted({r["arm"] for r in records}):
        done = [r for r in records if r["arm"] == arm and r["status"] == "completed"]
        times = [float(value(r, FIELDS["repeat s"])) for r in done]
        lines.append(f"| {arm} | {len(done)} of {sum(1 for r in records if r['arm'] == arm)} | "
                     f"{statistics.median(times) if times else ''} | {min(times) if times else ''} to "
                     f"{max(times) if times else ''} | {len({value(r, FIELDS['before']) for r in done})} | "
                     f"{len({value(r, FIELDS['after']) for r in done})} | "
                     f"{len({r['start_state']['sha256'] for r in done})} |")
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"E006-r{first:04d}-r{last:04d}.md"
    with open(target, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(int(sys.argv[1]), int(sys.argv[2]))
