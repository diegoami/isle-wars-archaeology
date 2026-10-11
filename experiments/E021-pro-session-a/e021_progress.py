"""T45's progress number (the task file, "The progress number", L58): how many of the 40 Session A
cells the E021 records have met, per row and in total.

    python3 experiments/E021-pro-session-a/e021_progress.py           # write the next file
    python3 experiments/E021-pro-session-a/e021_progress.py --dry-run # print, write nothing

It reads every committed record under `runs/E021/` (every batch), collects the (case, cell) pairs
their observations name -- one pair per observation group that carries `case:kind` and
`cell:ordinal`, each group counted once however often the record repeats it -- and writes
`measurements/progress-r<nn>.json`, one more than every progress file already there. A measured
output is never overwritten (rule 20): each count is a new `r<nn>`, and the file names the records
it counted. A resumed batch starts from the latest file (the loop reads it with `load_latest`
before a sitting, so a sitting only works the cells still needed).

A group that names a case outside the table, or a cell outside that case's row, is a problem and
stops the count: the file is never written from a record the counter cannot read.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import cases  # noqa: E402

SCHEMA = "e021-progress/1"
RUNS = ROOT / "runs" / "E021"
MEASUREMENTS = HERE / "measurements"
PROGRESS = re.compile(r"^progress-r(\d+)\.json$")


class ProgressRefused(SystemExit):
    """No progress file was written."""


def record_paths(root=RUNS):
    """The committed E021 records, every batch, in run-id order."""
    if not Path(root).is_dir():
        return []
    return sorted(p for p in Path(root).rglob("*.json") if p.is_file())


def load_json(path):
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProgressRefused(f"{path} is not readable JSON: {exc}") from None
    if not isinstance(doc, dict):
        raise ProgressRefused(f"{path} is not a JSON object")
    return doc


def groups(doc):
    """[(step, {field: value})] of one record's observations, in step order."""
    observations = doc.get("observations")
    if not isinstance(observations, list):
        raise ProgressRefused("the record has no observations array")
    by_step = {}
    for number, row in enumerate(observations, start=1):
        if not isinstance(row, dict):
            raise ProgressRefused(f"observation {number} is not an object")
        step = row.get("step")
        if not isinstance(step, int) or isinstance(step, bool) or step < 0:
            raise ProgressRefused(f"observation {number} has no step number")
        field = row.get("field")
        value = row.get("value")
        if field is None and value is None and row.get("ref") is not None:
            continue                                    # a frame reference, not a reading
        if not isinstance(field, str) or not isinstance(value, str):
            raise ProgressRefused(f"observation {number} is neither a reading nor a frame reference")
        by_step.setdefault(step, {})[field] = value
    return sorted(by_step.items())


def cells_of_record(doc, where="the record"):
    """The (case, cell) pairs one record's observations name, once each. ProgressRefused on an
    observation group that carries one of the two fields but not both, or names a cell outside the
    table: the counter never guesses what a group meant."""
    found = set()
    for step, fields in groups(doc):
        named = {key: fields[key] for key in ("case:kind", "cell:ordinal") if key in fields}
        if not named:
            continue
        if len(named) != 2:
            raise ProgressRefused(f"{where}, step {step}: a group names case:kind or cell:ordinal "
                                  "but not both")
        case, cell = named["case:kind"], named["cell:ordinal"]
        if case not in cases.TOTALS:
            raise ProgressRefused(f"{where}, step {step}: {case!r} is not a Session A case "
                                  f"({', '.join(cases.CASES)})")
        if not re.fullmatch(r"[1-9][0-9]{0,2}", cell) or int(cell) > cases.TOTALS[case]:
            raise ProgressRefused(f"{where}, step {step}: cell {cell!r} is not a cell of case {case!r}")
        found.add((case, int(cell)))
    return found


def collect(paths):
    """(cells by case, run ids) over every record: each (case, cell) once, however many records
    name it."""
    met = {case: set() for case in cases.CASES}
    run_ids = []
    for path in paths:
        doc = load_json(path)
        if doc.get("schema") != "run/1" or doc.get("experiment") != "E021":
            raise ProgressRefused(f"{path} is not an E021 run/1 record")
        run_id = doc.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise ProgressRefused(f"{path} carries no run id")
        run_ids.append(run_id)
        for case, cell in cells_of_record(doc, where=path.name):
            met[case].add(cell)
    return met, run_ids


def count(paths):
    """The progress of every record in `paths`: rows per case with their met and unmet cells (a cell
    no deal offered yet stays listed as unmet: the outcome is narrowed for it, the owner's
    2026-10-07 rule for stacks above 12), and the sums."""
    met, run_ids = collect(paths)
    rows = {case: {"met": len(met[case]), "total": cases.TOTALS[case], "cells": sorted(met[case]),
                   "unmet": [c for c in cases.cells(case) if c not in met[case]]}
            for case in cases.CASES}
    return {"schema": SCHEMA, "records": run_ids, "rows": rows,
            "met": sum(row["met"] for row in rows.values()), "total": cases.TOTAL}


def needed_from(doc):
    """The (case, cell) pairs a progress document leaves unmet ({} of an absent or unreadable
    document: a first sitting starts from the whole table)."""
    if not isinstance(doc, dict):
        return {(case, cell) for case in cases.CASES for cell in cases.cells(case)}
    met = set()
    for case, row in (doc.get("rows") or {}).items():
        if case in cases.TOTALS and isinstance(row, dict):
            for cell in row.get("cells") or ():
                if isinstance(cell, int) and 1 <= cell <= cases.TOTALS[case]:
                    met.add((case, cell))
    return {(case, cell) for case in cases.CASES for cell in cases.cells(case) if (case, cell) not in met}


def latest_number(directory=MEASUREMENTS):
    """The number of the newest `progress-r<nn>.json` in `directory`, 0 when there is none."""
    numbers = []
    directory = Path(directory)
    if directory.is_dir():
        for path in directory.iterdir():
            match = PROGRESS.match(path.name)
            if match:
                numbers.append(int(match.group(1)))
    return max(numbers, default=0)


def load_latest(directory=MEASUREMENTS):
    """The newest progress document, or None when there is none (a first sitting)."""
    number = latest_number(directory)
    if not number:
        return None
    return load_json(Path(directory) / f"progress-r{number:02d}.json")


def write_next(doc, directory=MEASUREMENTS):
    """The next progress file, new beside the others (never written over; rule 20). The path."""
    directory = Path(directory)
    number = latest_number(directory) + 1
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"progress-r{number:02d}.json"
    if path.exists():
        raise ProgressRefused(f"{path} exists; a measured output is never overwritten")
    payload = (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode()
    with open(path, "xb") as handle:
        handle.write(payload)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="print the count, write nothing")
    parser.add_argument("--runs", default=str(RUNS), help="the records' directory (tests only)")
    parser.add_argument("--measurements", default=str(MEASUREMENTS), help="the progress files' directory")
    args = parser.parse_args(argv)
    doc = count(record_paths(args.runs))
    if args.dry_run:
        print(json.dumps(doc, indent=1, sort_keys=True))
        return 0
    path = write_next(doc, args.measurements)
    print(json.dumps({"progress": path.name, "met": doc["met"], "total": doc["total"],
                      "rows": {case: f"{row['met']}/{row['total']}" for case, row in doc["rows"].items()}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
