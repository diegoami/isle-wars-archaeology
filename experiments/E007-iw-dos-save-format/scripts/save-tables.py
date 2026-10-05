#!/usr/bin/env python3
"""Tables for F009, from the run records (tracked) and the evidence bundles (local), over the natural saves of E005 and
E007 (the saves the game wrote). Nothing here reads the install.

    save-tables.py BATCH_DIR      BATCH_DIR must not exist: it is created, and each table is created in it

Needs E005_BUNDLES and E007_BUNDLES in the environment. Writes into BATCH_DIR:
  saves.tsv        one row per game-written save in a bundle (every `s<NN>-ISLEWAR.SAV` and `end-ISLEWAR.SAV` of a
                   run, once per distinct sha256 within the run): run, arm, step file, sha256, bytes, the decoded
                   fields (centres, dft, settings, per-colour owner counts, armies' sum, the card counts and hands)
  dft.tsv          every game-written ISLEWAR.DFT of a run (step file, sha256, text)
  roundtrip.tsv    for every distinct natural save of E005 and E007: sha256, bytes, whether encode(decode(bytes)) is
                   the same bytes, and the first difference otherwise (the writer's round-trip, F009)
Never overwrites (CLAUDE.md rule 20): a new batch directory, each file created exclusively.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "save"))
import savefmt  # noqa: E402

EXPERIMENTS = ("E005", "E007")


def bundle(experiment):
    return Path(os.environ[f"{experiment}_BUNDLES"])


def records(experiment):
    for path in sorted((ROOT / "runs" / experiment).glob(f"{experiment}-r*.json")):
        yield json.loads(path.read_text())


def game_files(record, suffix):
    """[(name, asset path)] of the record's kept files that are game-written copies ending in `suffix`."""
    manifest = json.loads((ROOT / "evidence" / record["experiment"] / f"{record['run_id']}.manifest.json").read_text())
    return [(e["name"], bundle(record["experiment"]) / e["asset"]) for e in manifest["files"] if e["name"].endswith(suffix)]


def put(directory, name, rows, header):
    text = "\t".join(header) + "\n" + "".join("\t".join(map(str, r)) + "\n" for r in rows)
    with open(Path(directory) / name, "xb") as fh:
        fh.write(text.encode())


def main(batch):
    batch = Path(batch)
    batch.mkdir(parents=True)
    saves, dfts, trips, seen = [], [], [], set()
    for experiment in EXPERIMENTS:
        for record in records(experiment):
            kept = set()
            for name, path in game_files(record, "ISLEWAR.SAV"):
                data = path.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                if digest in kept:
                    continue
                kept.add(digest)
                try:
                    p = savefmt.decode(data)
                except savefmt.SaveError as exc:
                    saves.append((record["run_id"], record["arm"], name, digest[:16], len(data), f"NOT DECODED: {exc}"))
                    continue
                owners = {c: p["owners"].count(c) for c in savefmt.COLOURS}
                saves.append((record["run_id"], record["arm"], name, digest[:16], len(data), len(p["centres"]),
                              ",".join(map(str, p["centres"])), ",".join(map(str, p["dft"])),
                              ",".join(map(str, p["settings"])),
                              ",".join(f"{c}={owners[c]}" for c in savefmt.COLOURS), sum(p["armies"]),
                              ",".join(str(len(p["cards"][c])) for c in savefmt.COUNT_ORDER),
                              ",".join("".join(map(str, p["cards"][c])) for c in savefmt.HAND_ORDER)))
                if digest not in seen:
                    seen.add(digest)
                    try:
                        same = savefmt.encode(p) == data
                        detail = "" if same else "the bytes differ"
                    except savefmt.Refused as exc:
                        same, detail = False, f"encode refused: {exc}"
                    trips.append((digest, len(data), "yes" if same else "NO", detail))
            kept = set()
            for name, path in game_files(record, "ISLEWAR.DFT"):
                data = path.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                if digest not in kept:
                    kept.add(digest)
                    dfts.append((record["run_id"], record["arm"], name, digest[:16], len(data),
                                 data.decode("latin-1").replace("\r\n", "|")))
    put(batch, "saves.tsv", saves, ["run", "arm", "file", "sha256_16", "bytes", "centres_n", "centres", "dft",
                                    "settings", "owners", "armies_sum", "card_counts_blue_red_green_brown",
                                    "hands_blue_green_red_brown"])
    put(batch, "dft.tsv", dfts, ["run", "arm", "file", "sha256_16", "bytes", "text (CRLF shown as |)"])
    put(batch, "roundtrip.tsv", trips, ["sha256", "bytes", "encode(decode(bytes)) equals the bytes", "detail"])
    bad = [t for t in trips if t[2] != "yes"]
    print(f"{len(saves)} save files, {len(trips)} distinct, {len(bad)} that do not round-trip")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
