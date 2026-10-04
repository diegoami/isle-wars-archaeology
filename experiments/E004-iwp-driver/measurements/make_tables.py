#!/usr/bin/env python3
"""Make cycle-table.md and stage-times.md from runs/E004/*.json (rule 20: nothing here is typed by hand).

    python3 experiments/E004-iwp-driver/measurements/make_tables.py

Every number is read from a record's observations or outputs.
"""
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECORDS = sorted((ROOT / "runs" / "E004").glob("E004-r*.json"))

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


def main():
    rows = [(path.stem, *load(path)) for path in RECORDS]
    out = ["# E004 cycle table", "", "Made by `make_tables.py` from `runs/E004/*.json`. One row per record.", "",
           "| run | arm | rep | status | session s | before pixels sha256 (first 16) | before.png file sha256 (first 16) | start_state sha256 (first 16) |",
           "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for name, record, obs in rows:
        before = next((o["sha256"] for o in record["outputs"] if o["name"] == "before.png"), "none")
        pixels = obs.get("before.png raw RGB8 pixels sha256", "none")
        out.append(f"| {name} | {record['arm']} | {record['rep']} | {record['status'][:70]} | "
                   f"{obs.get('session seconds, from the first seal to the end of the reset', 'n/a')} | "
                   f"{pixels[:16]} | {before[:16]} | {record['start_state']['sha256'][:16]} |")
    out.append("")
    completed = [(n, r, o) for n, r, o in rows if r["status"] == "completed"]
    out += ["## What is identical", ""]
    for label, getter in (("before pixels sha256", lambda r, o: o.get("before.png raw RGB8 pixels sha256")),
                          ("before.png file sha256", lambda r, o: next((x["sha256"] for x in r["outputs"] if x["name"] == "before.png"), None)),
                          ("after.png file sha256", lambda r, o: next((x["sha256"] for x in r["outputs"] if x["name"] == "after.png"), None)),
                          ("start_state sha256", lambda r, o: r["start_state"]["sha256"])):
        for arm in sorted({r["arm"] for _, r, _ in rows}):
            values = [getter(r, o) for _, r, o in rows if r["arm"] == arm and r["status"] == "completed"]
            out.append(f"- {label}, arm `{arm}`: {len(values)} completed record(s), {len(set(values))} distinct value(s)")
        values = [getter(r, o) for _, r, o in completed]
        out.append(f"- {label}, all completed records: {len(values)} records, {len(set(values))} distinct value(s)"
                   + (f": `{next(iter(set(values)))}`" if len(set(values)) == 1 else ""))
    out.append("")
    out += ["## The seal, in every record that reached it", "",
            "| observation | value | records with it | records |", "| --- | --- | --- | --- |"]
    for field, want in (("install read-only inside the run", "yes"),
                        ("prefix seal before anything starts: problems found", "0"),
                        ("registry files equal their baseline before the launch", "yes"),
                        ("prefix seal immediately before launch: problems found", "0"),
                        ("game in its own network namespace", "yes"),
                        ("network interfaces the game sees", "lo"),
                        ("processes of this run still alive after terminate", "0"),
                        ("prefix after reset equals prefix before launch", "yes")):
        have = [o for _, _, o in rows if field in o]
        out.append(f"| {field} | {want} | {sum(1 for o in have if o[field] == want)} | {len(have)} of {len(rows)} |")
    out.append("")
    (HERE / "cycle-table.md").write_text("\n".join(out) + "\n")

    out = ["# E004 stage times", "", "Seconds, median (range, n) over the completed records of each arm group; "
           "read from the observations of `runs/E004/*.json`. The `control` arm is the 10-repeat command; "
           "`fault arms` are the completed repeats of `kill-mid-cycle` and `sigkill-mid-cycle`.", "",
           "| stage | control | fault arms (completed repeats) |", "| --- | --- | --- |"]
    groups = {"control": [o for _, r, o in completed if r["arm"] == "control"],
              "fault": [o for _, r, o in completed if r["arm"] != "control"]}
    for label, field in STAGES:
        out.append(f"| {label} | {fmt([number(o.get(field)) for o in groups['control']])} | "
                   f"{fmt([number(o.get(field)) for o in groups['fault']])} |")
    out.append("")
    aborted = [(n, r, o) for n, r, o in rows if r["status"].startswith("aborted")]
    out += ["## Aborted repeats", ""]
    for name, record, obs in aborted:
        out.append(f"- {name} (arm `{record['arm']}`): `{record['status']}`; prefix after reset equals prefix before launch: "
                   f"{obs.get('prefix after reset equals prefix before launch')}; session {obs.get('session seconds, from the first seal to the end of the reset')} s")
    if not aborted:
        out.append("- none")
    out.append("")
    (HERE / "stage-times.md").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
