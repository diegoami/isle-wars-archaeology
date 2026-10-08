#!/usr/bin/env python3
"""Measure the reader's constants from the sitting frames, on the user's machine (T40).

  measure.py census    scan every frame of every sitting for numeral-coloured blobs 17 to 19 pixels
                       high; write the census (hash, size, pixel count, occurrences, example frame:
                       committed) and the unique bitmaps (machine-local, never committed: rule 18)
  measure.py templates build the machine-local template file from the bitmaps and the labels
                       (measurements/digit-labels.json: bitmap hash -> digit, committed)
  measure.py anchors   cluster the centres of the numbers over every frame into the 46 country
                       anchors; with --labels (cluster rank by x -> country, committed) write
                       reader/anchors.json

Frames are read in place under the sitting root and never copied. Every output of this tool that is
committed holds numbers and hashes only.
"""
import argparse
import json
import multiprocessing
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glyphs  # noqa: E402
import pngdecode  # noqa: E402

SITTING_ROOT = Path("/mnt/c/Temp/iwp-shots/wine")
LOCAL_BITMAPS = SITTING_ROOT / "reader-bitmaps.json"
LOCAL_TEMPLATES = SITTING_ROOT / "reader-templates.json"
BOARD_ROWS = 495                     # the board is the top 495 rows of the stage (coordinates.md)
MIN_FRAMES_FOR_ANCHOR = 100
MAX_GAP = 8                          # pixels between two glyphs of one number (board.MAX_GAP)


def sittings(root):
    return sorted(p for p in Path(root).iterdir() if p.is_dir() and (p / "frames-index.jsonl").is_file())


def frames_of(sitting):
    out = []
    for line in (Path(sitting) / "frames-index.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out.append((row["name"], row["sha256"]))
    return out


def scan_frame(job):
    sitting, name = job
    rgb = pngdecode.decode_file(Path(sitting) / "frames" / name)
    mask, kind = glyphs.mask_of(rgb[:BOARD_ROWS])
    found = []
    for x, y, bitmap in glyphs.blobs(mask):
        if glyphs.HEIGHT_RANGE[0] <= bitmap.shape[0] <= glyphs.HEIGHT_RANGE[1]:
            colours = sorted({int(k) for k in kind[y:y + bitmap.shape[0], x:x + bitmap.shape[1]][bitmap > 0]})
            found.append((x, y, bitmap, colours))
    return job, found


def census(args):
    root = Path(args.root)
    jobs = [(str(s), name) for s in sittings(root) for name, _ in frames_of(s)]
    counts, example, bitmaps, colours = Counter(), {}, {}, {}
    sha = {(str(s), name): digest for s in sittings(root) for name, digest in frames_of(s)}
    with multiprocessing.Pool(args.processes) as pool:
        for (sitting, name), found in pool.imap(scan_frame, jobs, chunksize=8):
            for x, y, bitmap, kinds in found:
                h = glyphs.bitmap_sha256(bitmap)
                counts[h] += 1
                bitmaps.setdefault(h, bitmap)
                colours.setdefault(h, set()).update(kinds)
                example.setdefault(h, (Path(sitting).name, sha[(sitting, name)], x, y))
    rows = []
    for h, n in counts.most_common():
        bitmap = bitmaps[h]
        rows.append({"sha256": h, "width": int(bitmap.shape[1]), "height": int(bitmap.shape[0]),
                     "pixels": int(bitmap.sum()), "occurrences": n,
                     "colours": [["", "white", "cyan"][k] for k in sorted(colours[h])],
                     "example": {"sitting": example[h][0], "frame": example[h][1], "x": example[h][2], "y": example[h][3]}})
    doc = {"what": "census of numeral-coloured blobs 17 to 19 pixels high over every frame of the sittings",
           "frames": len(jobs), "sittings": [s.name for s in sittings(root)], "blobs": rows}
    Path(args.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    local = {h: ["".join("#" if v else "." for v in r) for r in bitmaps[h]] for h in counts}
    Path(args.bitmaps).write_text(json.dumps(local) + "\n", encoding="utf-8")
    print(f"{len(jobs)} frames, {len(rows)} unique bitmaps; census {args.out}; bitmaps {args.bitmaps} (machine-local)")
    return 0


def templates(args):
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))["labels"]
    local = json.loads(Path(args.bitmaps).read_text(encoding="utf-8"))
    entries, missing = [], []
    for h, digit in sorted(labels.items(), key=lambda kv: kv[1]):
        if h not in local:
            missing.append(h)
            continue
        entries.append((digit, np.array([[1 if c == "#" else 0 for c in row] for row in local[h]], dtype=np.uint8)))
    if missing:
        print(f"{len(missing)} labelled bitmaps are not in {args.bitmaps}: {missing}")
        return 1
    glyphs.Templates.dump(entries, args.out)
    print(f"{len(entries)} templates for digits {''.join(sorted({d for d, _ in entries}))} written to {args.out} (machine-local)")
    return 0


def numbers_in(job, templates):
    """[(centre x, centre y, digits)] of the numbers of one frame, from its glyph blobs."""
    sitting, name = job
    rgb = pngdecode.decode_file(Path(sitting) / "frames" / name)
    mask, _ = glyphs.mask_of(rgb[:BOARD_ROWS])
    digits = []
    for x, y, bitmap in glyphs.blobs(mask):
        if glyphs.HEIGHT_RANGE[0] <= bitmap.shape[0] <= glyphs.HEIGHT_RANGE[1]:
            d = templates.match(bitmap)
            if d is not None:
                digits.append((y, x, bitmap.shape[1], d))
    digits.sort()
    out, used = [], [False] * len(digits)
    for i, first in enumerate(digits):
        if used[i]:
            continue
        group, used[i] = [first], True
        for j in range(i + 1, len(digits)):
            nxt = digits[j]
            if not used[j] and abs(nxt[0] - first[0]) <= 1 and 0 <= nxt[1] - (group[-1][1] + group[-1][2]) <= MAX_GAP:
                group.append(nxt)
                used[j] = True
        left, right = group[0][1], group[-1][1] + group[-1][2]
        out.append(((left + right) / 2.0, first[0] + 9.0, "".join(g[3] for g in group)))
    return out


def _numbers_job(args):
    job, template_path = args
    return numbers_in(job, glyphs.Templates.load(template_path))


def anchors(args):
    root = Path(args.root)
    jobs = [(str(s), name) for s in sittings(root) for name, _ in frames_of(s)]
    clusters = []
    with multiprocessing.Pool(args.processes) as pool:
        for found in pool.imap(_numbers_job, [(j, args.templates) for j in jobs], chunksize=8):
            for x, y, _ in found:
                for c in clusters:
                    if abs(c["x"] - x) <= 6 and abs(c["y"] - y) <= 6:
                        c["points"].append((x, y))
                        break
                else:
                    clusters.append({"x": x, "y": y, "points": [(x, y)]})
    keep = []
    for c in clusters:
        if len(c["points"]) >= MIN_FRAMES_FOR_ANCHOR:
            pts = np.array(c["points"])
            keep.append({"x": float(np.median(pts[:, 0])), "y": float(np.median(pts[:, 1])), "frames": len(pts),
                         "x_range": [float(pts[:, 0].min()), float(pts[:, 0].max())],
                         "y_range": [float(pts[:, 1].min()), float(pts[:, 1].max())]})
    keep.sort(key=lambda c: (c["x"], c["y"]))
    print(f"{len(jobs)} frames, {len(clusters)} clusters, {len(keep)} with at least {MIN_FRAMES_FOR_ANCHOR} frames")
    if not args.labels:
        for rank, c in enumerate(keep):
            print(rank, c)
        return 0
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))["countries_by_rank"]
    if sorted(map(int, labels.values())) != list(range(1, 47)) or len(keep) != 46:
        print(f"the labels name {len(labels)} clusters, {len(keep)} found; they must map 46 clusters onto countries 1 to 46")
        return 1
    table = {}
    for rank, c in enumerate(keep):
        table[str(labels[str(rank)])] = {**c}
    doc = {"what": "centres of the army numbers of the 46 countries, measured over every frame of the sittings",
           "frames": len(jobs), "anchors": dict(sorted(table.items(), key=lambda kv: int(kv[0])))}
    Path(args.out).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("census")
    p.add_argument("--root", default=str(SITTING_ROOT))
    p.add_argument("--out", required=True)
    p.add_argument("--bitmaps", default=str(LOCAL_BITMAPS))
    p.add_argument("--processes", type=int, default=16)
    p.set_defaults(fn=census)
    p = sub.add_parser("templates")
    p.add_argument("--labels", required=True)
    p.add_argument("--bitmaps", default=str(LOCAL_BITMAPS))
    p.add_argument("--out", default=str(LOCAL_TEMPLATES))
    p.set_defaults(fn=templates)
    p = sub.add_parser("anchors")
    p.add_argument("--root", default=str(SITTING_ROOT))
    p.add_argument("--templates", default=str(LOCAL_TEMPLATES))
    p.add_argument("--labels")
    p.add_argument("--out", default=str(HERE / "anchors.json"))
    p.add_argument("--processes", type=int, default=16)
    p.set_defaults(fn=anchors)
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
