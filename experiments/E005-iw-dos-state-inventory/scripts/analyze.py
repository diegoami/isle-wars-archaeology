#!/usr/bin/env python3
"""Tables for F007, from the run records (tracked) and the evidence bundles (local, E005_BUNDLES).

    analyze.py OUTDIR

Writes into OUTDIR (measurements/analysis/):
  files-by-arm.tsv       per run: the arm, the files the game wrote at the end (size, sha256, bytes in hex when <= 64)
  save-owner-check.tsv   per save: each owner code against the army colour read from the screenshot taken at the save
  save-codes.tsv         the contingency table of owner code against pixel colour over every save
  save-fields.tsv        per save: the header lines, the card lines and the line count
  turn-diff.tsv          the two saves of each `turn` run, field by field, with the action that explains the change
  load-check.tsv         the saves of the `save-load` runs against the board after Load saved game
  timings.tsv            per run: seconds to the option box, to the first human turn after the start click, cycle seconds,
                         and the seconds one board reading (owners, then neighbours) takes on a screenshot of the run
Never overwrites: an existing file is left as it is and the new one is written as <name>.new.
Machine-local paths come from the environment (E005_BUNDLES) and are never written to the outputs.
"""
import json
import os
import re
import sys
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "spike"))
import board  # noqa: E402
import navsteps  # noqa: E402

CODES = {"9": "blue", "2": "green", "4": "red", "8": "brown"}      # read off the first save, then checked on all
BUNDLES = Path(os.environ["E005_BUNDLES"])


def records():
    for path in sorted((ROOT / "runs" / "E005").glob("E005-r*.json")):
        yield json.loads(path.read_text())


def asset(run_id, name):
    manifest = json.loads((ROOT / "evidence" / "E005" / f"{run_id}.manifest.json").read_text())
    for entry in manifest["files"]:
        if entry["name"] == name:
            return BUNDLES / entry["asset"]
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
    lines = [l.strip() for l in data.decode("ascii").split("\r\n")]
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def layout(lines):
    """The save's fields by their lines: N, then N production-centre country numbers, the level, the starting
    armies, two constants, 46 owner codes, 46 army counts, the card counts line, the card types line."""
    n = int(lines[0])
    assert len(lines) == 99 + n, f"{len(lines)} lines for N={n}"
    return {"n": n, "centres": lines[1:1 + n], "level": lines[1 + n], "armies_set": lines[2 + n],
            "const": lines[3 + n:5 + n], "owners": lines[5 + n:51 + n], "armies": lines[51 + n:97 + n],
            "card_counts": lines[97 + n], "card_types": lines[98 + n]}


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


def write(outdir, name, text):
    target = Path(outdir) / name
    if target.exists():
        target = Path(outdir) / (name + ".new")
    target.write_text(text)


def main(outdir):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    recs = [r for r in records()]
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
    write(outdir, "files-by-arm.tsv", "\n".join(rows) + "\n")
    # 2. saves against the screen
    contingency, check, fields = Counter(), ["run\tsave\tstep\tshot\tmatching_of_46\tmismatches"], \
        ["run\tsave\tlines\tN\tproduction_centres\tlevel\tstarting_armies\tconstants\tcard_counts\tcard_types\tdft_level_armies"]
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
            shot = asset(r["run_id"], f"{name}.png")
            _, _, raw = read_png(shot)
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
                                     f["armies_set"], ",".join(f["const"]), f["card_counts"], f["card_types"],
                                     ",".join(dft[:2])]))
    write(outdir, "save-owner-check.tsv", "\n".join(check) + "\n")
    write(outdir, "save-codes.tsv", "code\tpixel_colour\tcountries\n" + "\n".join(
        f"{c}\t{p}\t{n}" for (c, p), n in sorted(contingency.items())) + "\n")
    write(outdir, "save-fields.tsv", "\n".join(fields) + "\n")
    # 3. the two saves of a turn run
    diff = ["run\tfield\tsave_turn1\tsave_turn2\tnote"]
    for r in recs:
        if r["arm"] != "turn" or r["status"] != "completed":
            continue
        a, b = boards[(r["run_id"], "save-turn1")][0], boards[(r["run_id"], "save-turn2")][0]
        chosen = [o["value"] for o in r["observations"] if o["field"].startswith("chosen")][0].split()
        mine, target = int(chosen[0]), int(chosen[1])
        shot1 = read_png(asset(r["run_id"], "save-turn1.png"))[2]
        placed = max(2, board.totals(shot1)["blue"] // 3)
        diff.append(f"{r['run_id']}\tchosen mine, target\t{mine}\t{target}\tchoose-attack, read from the screen at turn 1; "
                    f"armies placed = Blue countries // 3 (min 2) = {placed} (the game's own rule, ISLEWAR.DOC)")
        for n in range(1, 47):
            for label in ("owners", "armies"):
                if a[label][n - 1] != b[label][n - 1]:
                    note = ""
                    if n == target and label == "owners":
                        note = "the country attacked and conquered at turn 1"
                    if n == target and label == "armies":
                        note = ("the armies moved in: ALL moves all but one of the attacker's armies; the attack-result message reads "
                                "'5 AGAINST 0' in both runs (read by eye), so 4 moved in")
                    if n == mine and label == "armies":
                        note = "the country that attacked"
                    diff.append(f"{r['run_id']}\t{'owner' if label == 'owners' else 'armies'}[{n}]\t{a[label][n - 1]}\t{b[label][n - 1]}\t{note}")
        for label in ("centres", "level", "armies_set", "const", "n"):
            diff.append(f"{r['run_id']}\t{label}\t{a[label]}\t{b[label]}\t{'unchanged' if a[label] == b[label] else 'CHANGED'}")
        diff.append(f"{r['run_id']}\tcard counts line\t{a['card_counts']}\t{b['card_counts']}\tthe C> column of the scoreboard (read by eye, see F007)")
        diff.append(f"{r['run_id']}\tcard types line\t{a['card_types']}\t{b['card_types']}\t")
    write(outdir, "turn-diff.tsv", "\n".join(diff) + "\n")
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
    write(outdir, "load-check.tsv", "\n".join(load) + "\n")
    # 5. timings
    import time
    times = ["run\tarm\tstatus\toption_box_s\tfirst_human_turn_s\tcycle_s\tread_owners_s\tread_owners_and_neighbours_s"]
    for r in recs:
        obs = {o["field"]: o["value"] for o in r["observations"]}
        box = obs.get("option box reached and stable, seconds after launch", "")
        turn = next((o["value"] for o in r["observations"] if o["field"].startswith("more than 800 pixels of (170, 170, 170)")), "")
        cycle = obs.get("cycle seconds, start to end of clean-up", "")
        reading = ["", ""]
        shot = asset(r["run_id"], "human-turn.png") if r["status"] == "completed" else None
        if shot and shot.exists():
            raw = read_png(shot)[2]
            t0 = time.perf_counter()
            board.owners(raw)
            t1 = time.perf_counter()
            board.neighbours(raw)
            t2 = time.perf_counter()
            reading = [f"{t1 - t0:.3f}", f"{t2 - t1:.3f}"]
        times.append("\t".join([r["run_id"], r["arm"], r["status"].split(":")[0], box, turn, cycle] + reading))
    write(outdir, "timings.tsv", "\n".join(times) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
