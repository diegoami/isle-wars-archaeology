#!/usr/bin/env python3
"""The evidence for board.py's numeric constants (PR #58 R10), measured on the `human-turn.png` screenshot of every
completed E005 record that has one (bundles, E005_BUNDLES):

  - the number boxes: the black rectangles derive_boxes finds, their widths and heights, and the distance from each
    BOXES centre to the nearest one found (BOXES, and why SAMPLES lies outside the box);
  - SAMPLES: for each offset, on how many countries it lands on an army colour, and on how many on the box itself;
  - BORDER: for every pair of countries whose fills come within 10 pixels of each other in a row or a column, the
    smallest such gap, as a histogram over all screenshots (what BORDER = 3 takes in and what it leaves out).

    board-constants.py OUTDIR      OUTDIR exists (analyze.py's batch directory); board-constants.tsv is created there
                                   exclusively (never overwritten)
"""
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "spike"))
import board  # noqa: E402

spec = importlib.util.spec_from_file_location("analyze", ROOT / "experiments" / "E005-iw-dos-state-inventory" / "scripts" / "analyze.py")
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)


def gaps(raw, limit=10):
    """{(a, b): smallest gap in pixels} between the fills of countries a < b, in a row or a column, up to limit."""
    label = board.regions(raw)
    found = {}
    W, H = board.WIDTH, board.HEIGHT
    for y in range(H):
        for x in range(W):
            a = label[y * W + x]
            if not a:
                continue
            for d in range(1, limit + 1):
                for nx, ny in ((x + d, y), (x, y + d)):
                    if nx < W and ny < H:
                        b = label[ny * W + nx]
                        if b and b != a:
                            key = (min(a, b), max(a, b))
                            found[key] = min(found.get(key, d), d)
    return found


def main(outdir):
    shots = []
    for path in sorted((ROOT / "runs" / "E005").glob("E005-r*.json")):
        record = json.loads(path.read_text())
        if record["status"] == "completed":
            shot = analyze.asset(record["run_id"], "human-turn.png")
            if shot and shot.exists():
                shots.append((record["run_id"], shot))
    sizes, centre_off, sample_hits, sample_box, gap_hist = Counter(), Counter(), Counter(), Counter(), Counter()
    for run_id, shot in shots:
        raw = analyze.read_png(shot)[2]
        found = board.derive_boxes(raw)
        for x, y, w, h in found:
            sizes[(w, h)] += 1
        for n, (cx, cy) in board.BOXES.items():
            off = min(abs(cx - (x + w // 2)) + abs(cy - (y + h // 2)) for x, y, w, h in found) if found else None
            centre_off[off] += 1
            box = next(((x, y, w, h) for x, y, w, h in found if x <= cx < x + w and y <= cy < y + h), None)
            for dx, dy in board.SAMPLES:
                px, py = cx + dx, cy + dy
                if board.BY_COLOUR.get(board.pixel(raw, px, py)):
                    sample_hits[(dx, dy)] += 1
                if box and box[0] <= px < box[0] + box[2] and box[1] <= py < box[1] + box[3]:
                    sample_box[(dx, dy)] += 1
        for _, d in gaps(raw).items():
            gap_hist[d] += 1
    countries = 46 * len(shots)
    rows = ["what\tvalue\tcount\tnote",
            f"screenshots\t{len(shots)}\t{len(shots)}\t" + " ".join(run for run, _ in shots)]
    rows += [f"number box found (w x h)\t{w}x{h}\t{n}\tderive_boxes" for (w, h), n in sorted(sizes.items())]
    rows += [f"BOXES centre to the nearest box found (pixels, |dx|+|dy|)\t{off}\t{n}\tof {countries}" for off, n in sorted(centre_off.items(), key=lambda kv: (kv[0] is None, kv[0] or 0))]
    rows += [f"SAMPLES offset {dx},{dy} on an army colour\t{sample_hits[(dx, dy)]}\t{countries}\tcountries x screenshots" for dx, dy in board.SAMPLES]
    rows += [f"SAMPLES offset {dx},{dy} inside the number box\t{sample_box[(dx, dy)]}\t{countries}\t" for dx, dy in board.SAMPLES]
    rows += [f"smallest gap between two fills (pixels)\t{d}\t{n}\tpairs over all screenshots; BORDER = {board.BORDER} takes in gaps 1 to {board.BORDER}" for d, n in sorted(gap_hist.items())]
    analyze.write(outdir, "board-constants.tsv", "\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main(sys.argv[1])
