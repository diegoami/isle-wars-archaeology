#!/usr/bin/env python3
"""The pairs of runs F009 decodes the save's lines from: for each pair, the one action that differs, and which decoded
fields of the two saves differ (F009 "Observations").

    pair-diffs.py PAIRS.json BATCH_DIR     BATCH_DIR must not exist: it is created, and each table is created in it

PAIRS.json is a list of {"id", "field", "action", "a": [run, save index], "b": [run, save index]}: the save index is
the position of the save among the run's distinct game-written saves taken at a Save click (0 for the first `s<NN>`
file), and `a` is the run without the action. Needs E005_BUNDLES and E007_BUNDLES. Writes pair-diffs.tsv: per pair,
the value of the stated field in both saves, and every other field that differs (the board's fields differ between two
games that started from different boards; the table says so rather than hiding them). Never overwrites (rule 20).
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "save"))
import savefmt  # noqa: E402


def saves_of(run):
    experiment = run.split("-")[0]
    bundles = Path(os.environ[f"{experiment}_BUNDLES"])
    manifest = json.loads((ROOT / "evidence" / experiment / f"{run}.manifest.json").read_text())
    out, seen = [], set()
    for entry in sorted((e for e in manifest["files"] if e["name"].startswith("s") and e["name"].endswith("-ISLEWAR.SAV")),
                        key=lambda e: int(e["name"][1:3])):
        if entry["sha256"] not in seen:
            seen.add(entry["sha256"])
            out.append((entry["name"], entry["sha256"], savefmt.decode((bundles / entry["asset"]).read_bytes())))
    return out


def field(position, name):
    if name == "dft1":
        return position["dft"][0]
    if name == "dft2":
        return position["dft"][1]
    if name == "speed":
        return position["settings"][0]
    if name == "sound":
        return position["settings"][1]
    return position[name]


def differing(a, b):
    out = []
    if a["centres"] != b["centres"]:
        out.append(f"centres {a['centres']} -> {b['centres']}")
    for name, i in (("dft1", 0), ("dft2", 1)):
        if a["dft"][i] != b["dft"][i]:
            out.append(f"{name} {a['dft'][i]} -> {b['dft'][i]}")
    for name, i in (("speed", 0), ("sound", 1)):
        if a["settings"][i] != b["settings"][i]:
            out.append(f"{name} {a['settings'][i]} -> {b['settings'][i]}")
    own = [n + 1 for n in range(savefmt.COUNTRIES) if a["owners"][n] != b["owners"][n]]
    arm = [n + 1 for n in range(savefmt.COUNTRIES) if a["armies"][n] != b["armies"][n]]
    if own:
        out.append(f"owners differ in {len(own)} countries")
    if arm:
        out.append(f"armies differ in {len(arm)} countries")
    for colour in savefmt.COLOURS:
        if a["cards"][colour] != b["cards"][colour]:
            out.append(f"cards {colour} {''.join(map(str, a['cards'][colour])) or '-'} -> {''.join(map(str, b['cards'][colour])) or '-'}")
    return out


def main(pairs_file, batch):
    pairs = json.loads(Path(pairs_file).read_text())
    batch = Path(batch)
    batch.mkdir(parents=True)
    rows = []
    for pair in pairs:
        (run_a, i_a), (run_b, i_b) = pair["a"], pair["b"]
        name_a, sha_a, pos_a = saves_of(run_a)[i_a]
        name_b, sha_b, pos_b = saves_of(run_b)[i_b]
        rows.append((pair["id"], pair["field"], pair["action"], f"{run_a} {name_a} ({sha_a[:16]})",
                     f"{run_b} {name_b} ({sha_b[:16]})", field(pos_a, pair["field"].split()[0]) if " " not in pair["field"] else "",
                     field(pos_b, pair["field"].split()[0]) if " " not in pair["field"] else "", "; ".join(differing(pos_a, pos_b))))
    with open(batch / "pair-diffs.tsv", "xb") as fh:
        fh.write(("pair\tfield\tstated action\tsave a (without the action)\tsave b\tfield in a\tfield in b\tall decoded fields that differ\n"
                  + "".join("\t".join(map(str, r)) + "\n" for r in rows)).encode())
    print(f"{len(rows)} pairs")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
