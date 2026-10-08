#!/usr/bin/env python3
"""The validation sample's selection and its labelling aid (T40).

  sample.py select  --out sample-selection.json   seeded random frames per sitting, seeded random
                                                  countries per frame (the selection never looks at
                                                  what the reader says)
  sample.py notices --out sample-selection-notices.json
                                                  a second stratum: frames under a notice (found by
                                                  the screens module's pixel tests), so that hidden
                                                  numerals are in the sample
  sample.py anchors --out sample-selection-anchors.json --exclude sample-selection.json sample-selection-notices.json
                                                  a third stratum (R3): the measured-only anchors
                                                  (11, 15) on new seeded random frames
  sample.py montage --selection FILE --dir DIR   one zoomed crop per selected reading, captioned
                                                  with its number, in sheets of 24, for labelling
                                                  by eye (ImageMagick; the sheets stay on the
                                                  machine: they hold the game's pixels)

The labels (measurements/labels.json) are written by looking at the sheets; they hold frame
sha256, country number, army count and owner colour word, nothing else.
"""
import argparse
import json
import multiprocessing
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boardreader  # noqa: E402
import pngdecode  # noqa: E402

ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "driver"))
import screens  # noqa: E402

SITTING_ROOT = Path("/mnt/c/Temp/iwp-shots/wine")
SEED = 20261009
FRAMES_PER_SITTING = 12
COUNTRIES_PER_FRAME = 9


def index_of(root):
    out = {}
    for sitting in sorted(p for p in Path(root).iterdir() if p.is_dir() and (p / "frames-index.jsonl").is_file()):
        rows = [json.loads(line) for line in (sitting / "frames-index.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        out[sitting.name] = rows
    return out


def select(args):
    rng = random.Random(SEED)
    chosen = []
    for sitting, rows in index_of(args.root).items():
        by_sha = {}
        for row in rows:
            by_sha.setdefault(row["sha256"], row)
        for row in rng.sample(sorted(by_sha.values(), key=lambda r: r["name"]), FRAMES_PER_SITTING):
            countries = sorted(rng.sample(range(1, 47), COUNTRIES_PER_FRAME))
            chosen.append({"sitting": sitting, "frame": row["sha256"], "name": row["name"], "countries": countries})
    doc = {"what": "the validation sample's selection: seeded random frames of each sitting, seeded random countries of each frame",
           "seed": SEED, "frames_per_sitting": FRAMES_PER_SITTING, "countries_per_frame": COUNTRIES_PER_FRAME,
           "selection": chosen}
    Path(args.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"{len(chosen)} frames, {sum(len(c['countries']) for c in chosen)} readings -> {args.out}")
    return 0


def screen_of(job):
    path, = job
    return screens.name_of(pngdecode.decode_file(path).tobytes())


def select_notices(args):
    """A second stratum: frames on which a notice covers the board (the screens module's
    `eliminated` and `game-over`, found by pixels and independent of the reader), so that the
    numerals the notice hides are in the sample. Seeded like the first."""
    rng = random.Random(SEED + 1)
    found = {}
    for sitting, rows in index_of(args.root).items():
        by_sha = {}
        for row in rows:
            by_sha.setdefault(row["sha256"], row)
        rows = sorted(by_sha.values(), key=lambda r: r["name"])
        with multiprocessing.Pool(16) as pool:
            names = pool.map(screen_of, [(str(Path(args.root) / sitting / "frames" / r["name"]),) for r in rows])
        for row, name in zip(rows, names):
            if name in ("eliminated", "game-over"):
                found.setdefault((sitting, name), []).append(row)
    chosen = []
    for (sitting, name), rows in sorted(found.items()):
        for row in rng.sample(rows, min(args.per_kind, len(rows))):
            chosen.append({"sitting": sitting, "frame": row["sha256"], "name": row["name"], "screen": name,
                           "countries": sorted(rng.sample(range(1, 47), args.countries))})
    doc = {"what": "the notice stratum of the validation sample: frames on which a notice covers the board",
           "seed": SEED + 1, "countries_per_frame": args.countries, "selection": chosen}
    Path(args.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"{len(chosen)} frames ({', '.join(f'{s[-7:]} {n}: {len(r)} distinct' for (s, n), r in sorted(found.items()))}), "
          f"{sum(len(c['countries']) for c in chosen)} readings -> {args.out}")
    return 0


def select_anchors(args):
    """A third stratum (T40 round 2, R3): the countries whose anchor was measured from the frames
    alone (anchors.json `measured_only`, 11 and 15), on seeded random frames of each sitting that the
    sample does not hold yet, so that each has at least 5 labelled readings from 3 frames. Seeded,
    and blind to the reader like the first two."""
    rng = random.Random(SEED + 2)
    taken = set()
    for path in args.exclude:
        taken |= {(item["sitting"], item["frame"]) for item in json.loads(Path(path).read_text(encoding="utf-8"))["selection"]}
    countries = boardreader.measured_only_anchors()
    chosen = []
    for sitting, rows in index_of(args.root).items():
        by_sha = {}
        for row in rows:
            by_sha.setdefault(row["sha256"], row)
        free = [r for r in sorted(by_sha.values(), key=lambda r: r["name"]) if (sitting, r["sha256"]) not in taken]
        for row in rng.sample(free, args.per_sitting):
            chosen.append({"sitting": sitting, "frame": row["sha256"], "name": row["name"], "countries": countries})
    doc = {"what": "the measured-anchor stratum of the validation sample: seeded random frames of each sitting, "
                   "not already in the sample, each labelled for every measured-only country",
           "seed": SEED + 2, "frames_per_sitting": args.per_sitting, "countries": countries, "selection": chosen}
    Path(args.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"{len(chosen)} frames, {sum(len(c['countries']) for c in chosen)} readings -> {args.out}")
    return 0


def montage(args):
    doc = json.loads(Path(args.selection).read_text(encoding="utf-8"))
    anchors = boardreader.load_anchors()
    Path(args.dir).mkdir(parents=True, exist_ok=True)
    crops, number = [], 0
    for item in doc["selection"]:
        frame = Path(args.root) / item["sitting"] / "frames" / item["name"]
        for country in item["countries"]:
            number += 1
            cx, cy = anchors[country]
            x0, y0 = max(int(cx) - 40, 0), max(int(cy) - 22, 0)
            out = Path(args.dir) / f"c{number:04d}.png"
            subprocess.run(["convert", str(frame), "-crop", "80x44+%d+%d" % (x0, y0), "+repage", "-filter", "point", "-resize", "300%",
                            "-background", "white", "-fill", "black", "-gravity", "North", "-splice", "0x26", "-pointsize", "20",
                            "-annotate", "+0+2", f"#{number}", str(out)], check=True)
            crops.append(out)
    for sheet in range(0, len(crops), 24):
        subprocess.run(["montage"] + [str(c) for c in crops[sheet:sheet + 24]] + ["-tile", "4x6", "-geometry", "+3+3",
                        "-background", "gray70", str(Path(args.dir) / f"sheet{sheet // 24 + 1:02d}.png")], check=True)
    print(f"{len(crops)} crops, {(len(crops) + 23) // 24} sheets in {args.dir}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("select")
    p.add_argument("--root", default=str(SITTING_ROOT))
    p.add_argument("--out", required=True)
    p.set_defaults(fn=select)
    p = sub.add_parser("notices")
    p.add_argument("--root", default=str(SITTING_ROOT))
    p.add_argument("--out", required=True)
    p.add_argument("--per-kind", type=int, default=2, help="frames per sitting and notice screen")
    p.add_argument("--countries", type=int, default=12)
    p.set_defaults(fn=select_notices)
    p = sub.add_parser("anchors")
    p.add_argument("--root", default=str(SITTING_ROOT))
    p.add_argument("--out", required=True)
    p.add_argument("--exclude", nargs="+", required=True, help="the selections already in the sample")
    p.add_argument("--per-sitting", type=int, default=2)
    p.set_defaults(fn=select_anchors)
    p = sub.add_parser("montage")
    p.add_argument("--root", default=str(SITTING_ROOT))
    p.add_argument("--selection", required=True)
    p.add_argument("--dir", required=True)
    p.set_defaults(fn=montage)
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
