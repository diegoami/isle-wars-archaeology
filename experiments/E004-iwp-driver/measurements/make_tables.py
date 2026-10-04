#!/usr/bin/env python3
"""Make the cycle table and the stage times of one batch of runs/E004/ records (rule 20: nothing here is
typed by hand, and no measured output is ever overwritten).

    python3 experiments/E004-iwp-driver/measurements/make_tables.py FIRST LAST

FIRST and LAST are run numbers (17 29, or E004-r0017 E004-r0029). It writes
tables/E004-r<FIRST>-r<LAST>-cycle-table.md and tables/E004-r<FIRST>-r<LAST>-stage-times.md, and refuses
(nothing written) when either exists already: a batch's tables are made once. The first tables,
cycle-table.md and stage-times.md (r0001 to r0016), were made by an earlier version of this script at
38e5872 and stay as they are.

Every number is read from a record's observations or outputs.
"""
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

STAGES = [
    ("Xvfb ready", "xvfb ready (s)"),
    ("xfwm4 registered", "xfwm4 registered (s)"),
    ("snapshot of the prefix before the launch", "snapshot of the prefix before the launch took (s)"),
    ("game window after launch", "Islepro window after launch (s)"),
    ("title screen reached and stable, after launch", "title screen reached and stable, seconds after launch"),
    ("terminate (`wineserver -k` and the bounded wait)", "clean-up stage 'terminate' took (s)"),
    ("game side gone after terminate", "game side gone after terminate (s)"),
    ("display side gone after Xvfb and xfwm4 stopped", "display side gone after the display was stopped (s)"),
    ("stopping the display", "clean-up stage 'stopping the display' took (s)"),
    ("snapshot, diff and reset", "clean-up stage 'snapshot and reset' took (s)"),
    ("the whole session, first seal to end of reset", "session seconds, from the first seal to the end of the reset"),
]
SEAL = (("install read-only inside the run", "yes"),
        ("prefix seal before anything starts: problems found", "0"),
        ("registry files equal their baseline before the launch", "yes"),
        ("prefix seal immediately before launch: problems found", "0"),
        ("game in its own network namespace", "yes"),
        ("network interfaces the game sees", "lo"),
        ("processes of this run still alive after terminate", "0"),
        ("prefix after reset equals prefix before launch", "yes"))
LISTED = ("input steps that succeeded so far",
          "clean-up: every stage succeeded and the prefix was reset (the next session may start)")


def load(path):
    record = json.loads(path.read_text())
    obs = {}
    for o in record["observations"]:
        obs.setdefault(o["field"], o["value"])
    return record, obs


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(values):
    values = [v for v in values if v is not None]
    if not values:
        return "n/a"
    return f"{statistics.median(values):.2f} ({min(values):.2f} to {max(values):.2f}, n={len(values)})"


def run_number(text):
    match = re.fullmatch(r"(?:E004-r)?0*(\d+)", text)
    if not match:
        raise SystemExit(f"{text!r} is not a run number (17, or E004-r0017)")
    return int(match.group(1))


def output_sha(record, name):
    return next((o["sha256"] for o in record["outputs"] if o["name"] == name), None)


def cycle_table(batch, first, last, rows):
    completed = [(n, r, o) for n, r, o in rows if r["status"] == "completed"]
    out = [f"# E004 cycle table, {batch}", "",
           f"Made by `make_tables.py {first} {last}` from `runs/E004/`. One row per record.", "",
           "| run | arm | rep | status | session s | before pixels sha256 (first 16) | before.png file sha256 (first 16) | start_state sha256 (first 16) |",
           "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for name, record, obs in rows:
        pixels = obs.get("before.png raw RGB8 pixels sha256", "none")
        out.append(f"| {name} | {record['arm']} | {record['rep']} | {record['status'][:70]} | "
                   f"{obs.get('session seconds, from the first seal to the end of the reset', 'n/a')} | "
                   f"{pixels[:16]} | {(output_sha(record, 'before.png') or 'none')[:16]} | "
                   f"{record['start_state']['sha256'][:16]} |")
    out += ["", "## What is identical", ""]
    for label, getter in (("before pixels sha256", lambda r, o: o.get("before.png raw RGB8 pixels sha256")),
                          ("before.png file sha256", lambda r, o: output_sha(r, "before.png")),
                          ("after.png file sha256", lambda r, o: output_sha(r, "after.png")),
                          ("start_state sha256", lambda r, o: r["start_state"]["sha256"])):
        for arm in sorted({r["arm"] for _, r, _ in rows}):
            values = [getter(r, o) for _, r, o in completed if r["arm"] == arm]
            out.append(f"- {label}, arm `{arm}`: {len(values)} completed record(s), {len(set(values))} distinct value(s)")
        values = [getter(r, o) for _, r, o in completed]
        out.append(f"- {label}, all completed records: {len(values)} records, {len(set(values))} distinct value(s)"
                   + (f": `{next(iter(set(values)))}`" if len(set(values)) == 1 else ""))
    out += ["", "## The seal and the clean-up, in every record that reached them", "",
            "| observation | value wanted | records with it | records |", "| --- | --- | --- | --- |"]
    for field, want in SEAL:
        have = [o for _, _, o in rows if field in o]
        out.append(f"| {field} | {want} | {sum(1 for o in have if o[field] == want)} | {len(have)} of {len(rows)} |")
    out += ["", "| observation | values seen | records |", "| --- | --- | --- |"]
    for field in LISTED:
        have = [o for _, _, o in rows if field in o]
        out.append(f"| {field} | {', '.join(sorted({o[field] for o in have})) or 'n/a'} | {len(have)} of {len(rows)} |")
    return "\n".join(out) + "\n"


def stage_times(batch, rows):
    completed = [(n, r, o) for n, r, o in rows if r["status"] == "completed"]
    arms = sorted({r["arm"] for _, r, _ in completed})
    out = [f"# E004 stage times, {batch}", "",
           f"Seconds, median (range, n) over the completed records of each arm of {batch}, read from their observations.", "",
           "| stage | " + " | ".join(f"`{a}`" for a in arms) + " |", "| --- |" + " --- |" * len(arms)]
    for label, field in STAGES:
        out.append(f"| {label} | " + " | ".join(
            fmt([number(o.get(field)) for _, r, o in completed if r["arm"] == arm]) for arm in arms) + " |")
    out += ["", "## Aborted repeats", ""]
    aborted = [(n, r, o) for n, r, o in rows if r["status"].startswith("aborted")]
    for name, record, obs in aborted:
        out.append(f"- {name} (arm `{record['arm']}`): `{record['status']}`; prefix after reset equals prefix before "
                   f"launch: {obs.get('prefix after reset equals prefix before launch')}; session "
                   f"{obs.get('session seconds, from the first seal to the end of the reset')} s")
    if not aborted:
        out.append("- none")
    return "\n".join(out) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        raise SystemExit(__doc__)
    first, last = (run_number(a) for a in argv)
    batch = f"E004-r{first:04d}-r{last:04d}"
    records = [ROOT / "runs" / "E004" / f"E004-r{n:04d}.json" for n in range(first, last + 1)]
    missing = [p.name for p in records if not p.is_file()]
    if first > last or missing:
        raise SystemExit(f"no batch {batch}: missing {missing}")
    folder = HERE / "tables"
    targets = [folder / f"{batch}-cycle-table.md", folder / f"{batch}-stage-times.md"]
    taken = [p.name for p in targets if p.exists()]
    if taken:
        raise SystemExit(f"{', '.join(taken)} exist(s); a batch's tables are made once and never overwritten")
    rows = [(path.stem, *load(path)) for path in records]
    texts = (cycle_table(batch, first, last, rows), stage_times(batch, rows))
    folder.mkdir(exist_ok=True)
    for path, text in zip(targets, texts):
        with open(path, "x") as fh:          # a new file, never one that exists (rule 20)
            fh.write(text)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
