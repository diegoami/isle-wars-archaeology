#!/usr/bin/env python3
"""Tables for F007, from the run records (tracked) and the evidence bundles (local, E005_BUNDLES).

    analyze.py BATCH_DIR        BATCH_DIR must not exist: it is created, and every table is created in it

Writes into BATCH_DIR (a new directory under measurements/, one per batch):
  files-by-arm.tsv       per run: the arm, the files the game wrote at the end (size, sha256, bytes in hex when <= 64)
  files-timeline.tsv     per run with step times (r0027 on): the `files` step at which each game-written file first
                         appears or changes, in seconds after the launch, and the last click before it
  save-owner-check.tsv   per save: each owner code against the army colour read from the screenshot taken at the save
  save-codes.tsv         the contingency table of owner code against pixel colour over every save
  save-fields.tsv        per save: the header lines, the card lines and the line count
  turn-diff.tsv          the two saves of each `turn` run, field by field; the chosen countries are marked, nothing else
  load-check.tsv         the saves of the `save-load` runs against the board after Load saved game
  timings.tsv            per run: the option box and the window in seconds after the launch; the first human turn
                         from the first start click (r0027 on) and the poll of the human-turn panel alone (every run);
                         cycle seconds; the seconds one board reading takes; the capture times (r0027 on)
  waits.tsv              per run: every required wait of the steps (wait-stable, wait-change, until, the change and
                         stability waits of a click), its count, its longest value and its time-outs
Never overwrites (CLAUDE.md rule 20, PR #58 R3): the batch directory is new and each file is created exclusively; a
re-run writes a new batch. Machine-local paths come from the environment (E005_BUNDLES) and are never written out.
"""
import json
import os
import re
import sys
import time
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "spike"))
import board  # noqa: E402
import navsteps  # noqa: E402

CODES = {"9": "blue", "2": "green", "4": "red", "8": "brown"}      # read off the first save, then checked on all
# The human-turn panel: the grey (170, 170, 170) of the panel at the top right, more than 800 pixels in this rectangle
# (exploration x05, x06; the `until` of every arm's script after the start click). Matched by the script's own step.
HUMAN_TURN = ((390, 10, 230, 20), (170, 170, 170), 800)


def bundles():
    return Path(os.environ["E005_BUNDLES"])


def records():
    for path in sorted((ROOT / "runs" / "E005").glob("E005-r*.json")):
        yield json.loads(path.read_text())


def asset(run_id, name):
    manifest = json.loads((ROOT / "evidence" / "E005" / f"{run_id}.manifest.json").read_text())
    for entry in manifest["files"]:
        if entry["name"] == name:
            return bundles() / entry["asset"]
    return None


def read_png(path):
    """(width, height, rgb bytes) of a PNG written by cycle.py's png_bytes: 8-bit RGB, filter 0 on every row."""
    data = Path(path).read_bytes()
    pos, idat, width, height = 8, b"", 0, 0
    while pos < len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height = int.from_bytes(body[:4], "big"), int.from_bytes(body[4:8], "big")
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    rows = zlib.decompress(idat)
    stride = width * 3
    out = bytearray()
    for y in range(height):
        assert rows[y * (stride + 1)] == 0, "a filtered row: not one of cycle.py's PNGs"
        out += rows[y * (stride + 1) + 1:(y + 1) * (stride + 1)]
    return width, height, bytes(out)


def parse_save(data):
    lines = [line.strip() for line in data.decode("ascii").split("\r\n")]
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def layout(lines):
    """The save's lines by position: N, then N lines (production-centre country numbers), two lines (the level and
    the starting armies), two lines (constants in every save), 46 owner codes, 46 army counts, the card-counts line,
    and the last line (its meaning unknown, F007 D15)."""
    n = int(lines[0])
    assert len(lines) == 99 + n, f"{len(lines)} lines for N={n}"
    return {"n": n, "centres": lines[1:1 + n], "level": lines[1 + n], "armies_set": lines[2 + n],
            "const": lines[3 + n:5 + n], "owners": lines[5 + n:51 + n], "armies": lines[51 + n:97 + n],
            "card_counts": lines[97 + n], "last_line": lines[98 + n]}


def script_steps(record):
    """{step number: (verb, args)} of the record's script (the steps file named in its arguments)."""
    args = record["actions"]["args"]
    path = ROOT / args[args.index("--steps") + 1]
    return {100 + n: step for n, step in enumerate(navsteps.parse(path.read_text()), 1)}


def saves_of(record):
    """[(shot name, SAV bytes)]: for each shot named save-*, the SAV copy of the first `files` step after it."""
    steps = script_steps(record)
    found = []
    for step, (verb, args) in sorted(steps.items()):
        if verb == "shot" and args[0].startswith("save-"):
            later = [s for s, (v, _) in sorted(steps.items()) if s > step and v == "files"]
            if later:
                path = asset(record["run_id"], f"s{later[0] - 100:02d}-ISLEWAR.SAV")
                if path:
                    found.append((args[0][:-4], later[0] - 100, path.read_bytes()))
    return found


def new_batch(path):
    """Create the batch directory; FileExistsError when it exists (an earlier batch is never written into)."""
    os.mkdir(path)
    return Path(path)


def write(outdir, name, text):
    """Create outdir/name; FileExistsError when it exists: a table is never overwritten."""
    with open(Path(outdir) / name, "x", encoding="utf-8") as fh:
        fh.write(text)


def turn_rows(run_id, a, b, mine, target):
    """The fields of two saves of one run that differ, and the header fields with whether they changed. The countries
    choose-attack named are marked as such; no row derives a number from a rule of the game (PR #58 R9)."""
    rows = [f"{run_id}\tchosen mine, target\t{mine}\t{target}\tchoose-attack, read from the screen at turn 1"]
    for n in range(1, 47):
        for label in ("owners", "armies"):
            if a[label][n - 1] != b[label][n - 1]:
                note = {target: "the target of the attack at turn 1", mine: "the attacking country"}.get(n, "")
                rows.append(f"{run_id}\t{'owner' if label == 'owners' else 'armies'}[{n}]\t{a[label][n - 1]}\t{b[label][n - 1]}\t{note}")
    for label in ("centres", "level", "armies_set", "const", "n"):
        rows.append(f"{run_id}\t{label}\t{a[label]}\t{b[label]}\t{'unchanged' if a[label] == b[label] else 'CHANGED'}")
    rows.append(f"{run_id}\tcard counts line\t{a['card_counts']}\t{b['card_counts']}\t")
    rows.append(f"{run_id}\tlast line\t{a['last_line']}\t{b['last_line']}\t")
    return rows


def first_turn(steps, obs):
    """The first human turn of a run: from the first click of the step before the human-turn `until` (the start click)
    to the end of that `until`, in seconds, from the records' times after the launch (records from r0027 on; empty
    before); and the `until` poll alone (every record: it starts only after the start click's change and stability
    waits, so it is not the time from the click, PR #58 R11)."""
    until = next((s for s, (verb, args) in sorted(steps.items()) if verb == "until" and args[:3] == HUMAN_TURN), None)
    out = {"start_click_to_human_turn_s": "", "human_turn_panel_poll_s": ""}
    if until is None:
        return out
    click = max((s for s, (verb, _) in steps.items() if s < until and "click" in verb), default=None)
    at = {}
    for o in obs:
        at.setdefault((o["step"], o["field"]), o["value"])
    poll = next((o["value"] for o in obs if o["step"] == until and o["field"].startswith("more than 800 pixels of (170, 170, 170)")), "")
    out["human_turn_panel_poll_s"] = poll
    sent = next((o["value"] for o in obs if o["step"] == click and re.fullmatch(r"(left|right) click at \d+,\d+: seconds after launch", o["field"])), None)
    done = at.get((until, "step done, seconds after launch"))
    if sent is not None and done is not None:
        out["start_click_to_human_turn_s"] = f"{float(done) - float(sent):.2f}"
    return out


REQUIRED = (("wait-stable or the settling after a click", re.compile(r"screen stable after \(s\)")),
            ("a click's screen change", re.compile(r"screen changed after click \d+ at \d+,\d+ \(s\)")),
            ("wait-change", re.compile(r"screen changed after \(s\)")),
            ("until", re.compile(r"more than \d+ pixels of .* after \(s\)")),
            ("click-until", re.compile(r"more than \d+ pixels of .* after (click \d+ at|\d+ clicks at) .*")),
            ("still before a click (r0027 on)", re.compile(r"screen still before the click at \d+,\d+ \(s\)")),
            ("wait-exit", re.compile(r"DOSBox-X ended by itself after \(s\)")))


def wait_rows(record):
    rows = []
    for name, pattern in REQUIRED:
        values = [o["value"] for o in record["observations"] if o["step"] > 100 and pattern.fullmatch(o["field"])]
        if not values:
            continue
        numbers = [float(v) for v in values if re.fullmatch(r"[0-9.]+", v)]
        rows.append("\t".join([record["run_id"], record["status"].split(":")[0], name, str(len(values)),
                               f"{max(numbers):.2f}" if numbers else "", str(len(values) - len(numbers))]))
    return rows


def timeline_rows(record, steps):
    """[rows]: each game-written file at the first `files` step it appears at or changes, with that step's end time."""
    times = {o["step"]: o["value"] for o in record["observations"] if o["field"] == "step done, seconds after launch"}
    if not times:
        return []
    clicks = {}
    for o in record["observations"]:
        m = re.fullmatch(r"(left|right) click at (\d+,\d+): seconds after launch", o["field"])
        if m:
            clicks[o["step"]] = (m.group(2), o["value"])
    last, rows = {}, []
    for step, (verb, _) in sorted(steps.items()):
        if verb != "files":
            continue
        for o in record["observations"]:
            m = re.fullmatch(rf"run copy at step {step - 100}: (added|changed) (\S+): bytes, sha256", o["field"])
            if o["step"] == step and m and last.get(m.group(2)) != o["value"]:
                before = max((s for s in clicks if s < step), default=None)
                what = "first seen" if m.group(2) not in last else "bytes changed"
                last[m.group(2)] = o["value"]
                rows.append("\t".join([record["run_id"], record["arm"], m.group(2), what, f"s{step - 100:02d}", times.get(step, ""),
                                       f"step {before - 100} at {clicks[before][0]}, {clicks[before][1]} s" if before else "",
                                       o["value"].split()[0]]))
    return rows


def main(outdir):
    out = new_batch(outdir)
    recs = list(records())
    # 1. the files the game wrote
    rows = ["run\tarm\tstatus\tfile\tbytes\tsha256\thex"]
    for r in recs:
        files = {}
        for o in r["observations"]:
            m = re.fullmatch(r"run copy at the end of the run: (added|changed) (\S+): (bytes, sha256|hex)", o["field"])
            if m:
                files.setdefault(m.group(2), {})[m.group(3)] = o["value"]
        for name, v in sorted(files.items()):
            size, digest = v["bytes, sha256"].split()
            rows.append("\t".join([r["run_id"], r["arm"], r["status"].split(":")[0], name, size, digest, v.get("hex", "")]))
    write(out, "files-by-arm.tsv", "\n".join(rows) + "\n")
    timeline = ["run\tarm\tfile\twhat\tfiles_step\tseconds_after_launch\tlast_click_before_it\tbytes"]
    for r in recs:
        timeline += timeline_rows(r, script_steps(r))
    write(out, "files-timeline.tsv", "\n".join(timeline) + "\n")
    # 2. saves against the screen
    contingency, check = Counter(), ["run\tsave\tstep\tshot\tmatching_of_46\tmismatches"]
    fields = ["run\tsave\tlines\tN\tproduction_centres\tlevel\tstarting_armies\tconstants\tcard_counts\tlast_line\tdft_level_armies"]
    boards = {}
    for r in recs:
        if r["status"] != "completed":
            continue
        dft = [bytes.fromhex(o["value"]).decode().split() for o in r["observations"]
               if o["field"].endswith("ISLEWAR.DFT: hex") and "the end" in o["field"]]
        dft = [v for v in dft[0] if v != ","] if dft else []
        for name, step, data in saves_of(r):
            lines = parse_save(data)
            f = layout(lines)
            _, _, raw = read_png(asset(r["run_id"], f"{name}.png"))
            owners = board.owners(raw)
            codes = f["owners"]
            boards[(r["run_id"], name)] = (f, owners)
            miss = []
            for n in range(1, 47):
                contingency[(codes[n - 1], owners[n])] += 1
                if CODES.get(codes[n - 1]) != owners[n]:
                    miss.append(f"{n}:{codes[n - 1]}!={owners[n]}")
            check.append(f"{r['run_id']}\t{name}\ts{step:02d}\t{name}.png\t{46 - len(miss)}\t{' '.join(miss)}")
            fields.append("\t".join([r["run_id"], name, str(len(lines)), str(f["n"]), ",".join(f["centres"]), f["level"],
                                     f["armies_set"], ",".join(f["const"]), f["card_counts"], f["last_line"],
                                     ",".join(dft[:2])]))
    write(out, "save-owner-check.tsv", "\n".join(check) + "\n")
    write(out, "save-codes.tsv", "code\tpixel_colour\tcountries\n" + "\n".join(
        f"{c}\t{p}\t{n}" for (c, p), n in sorted(contingency.items())) + "\n")
    write(out, "save-fields.tsv", "\n".join(fields) + "\n")
    # 3. the two saves of a turn run
    diff = ["run\tfield\tsave_turn1\tsave_turn2\tnote"]
    for r in recs:
        if r["arm"] != "turn" or r["status"] != "completed":
            continue
        a, b = boards[(r["run_id"], "save-turn1")][0], boards[(r["run_id"], "save-turn2")][0]
        chosen = [o["value"] for o in r["observations"] if o["field"].startswith("chosen")][0].split()
        diff += turn_rows(r["run_id"], a, b, int(chosen[0]), int(chosen[1]))
    write(out, "turn-diff.tsv", "\n".join(diff) + "\n")
    # 4. Load saved game
    load = ["run\tsave_turn1_owners_equal_loaded_board\tcountries_equal_of_46\tsave_totals\tloaded_totals"]
    for r in recs:
        if r["arm"] != "save-load" or r["status"] != "completed":
            continue
        _, _, raw = read_png(asset(r["run_id"], "loaded-human-turn.png"))
        loaded = board.owners(raw)
        f, _ = boards[(r["run_id"], "save-turn1")]
        same = sum(1 for n in range(1, 47) if CODES.get(f["owners"][n - 1]) == loaded[n])
        load.append(f"{r['run_id']}\t{same == 46}\t{same}\t{board.totals(read_png(asset(r['run_id'], 'save-turn1.png'))[2])}\t{board.totals(raw)}")
    write(out, "load-check.tsv", "\n".join(load) + "\n")
    # 5. timings and waits
    times = ["run\tarm\tstatus\toption_box_after_launch_s\twindow_after_launch_s\twindow_poll_after_isolation_check_s"
             "\tstart_click_to_human_turn_s\thuman_turn_panel_poll_s\tcycle_s\tcaptures\tcapture_min_s\tcapture_max_s"
             "\tread_owners_s\tread_neighbours_s"]
    waits = ["run\tstatus\twait\tcount\tlongest_s\ttimed_out"]
    for r in recs:
        obs = {o["field"]: o["value"] for o in r["observations"]}
        turn = first_turn(script_steps(r), r["observations"])
        captures = [float(o["value"]) for o in r["observations"] if o["field"].endswith(" capture and PNG (s)")]
        reading = ["", ""]
        shot = asset(r["run_id"], "human-turn.png") if r["status"] == "completed" else None
        if shot and shot.exists():
            raw = read_png(shot)[2]
            t0 = time.perf_counter()
            board.owners(raw)
            t1 = time.perf_counter()
            board.neighbours(raw)
            t2 = time.perf_counter()
            reading = [f"{t1 - t0:.4f}", f"{t2 - t1:.3f}"]
        times.append("\t".join([
            r["run_id"], r["arm"], r["status"].split(":")[0], obs.get("option box reached and stable, seconds after launch", ""),
            obs.get("DOSBox-X window at 640x350, seconds after launch", ""),
            obs.get("DOSBox-X window at 640x350: poll seconds after the isolation check",
                    obs.get("DOSBox-X window at 640x350 after launch (s)", "")),
            turn["start_click_to_human_turn_s"], turn["human_turn_panel_poll_s"],
            obs.get("cycle seconds, start to end of clean-up", ""), str(len(captures)),
            f"{min(captures):.3f}" if captures else "", f"{max(captures):.3f}" if captures else ""] + reading))
        waits += wait_rows(r)
    write(out, "timings.tsv", "\n".join(times) + "\n")
    write(out, "waits.tsv", "\n".join(waits) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
