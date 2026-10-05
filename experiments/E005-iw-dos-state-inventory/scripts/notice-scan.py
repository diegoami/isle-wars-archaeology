#!/usr/bin/env python3
"""The evidence for cycle.py's notice detector and navsteps.py's FORBIDDEN band (PR #58 R1): for every 640x350
capture in the E005 bundles and exploration outputs, the number of (255, 85, 85) pixels in NOTICE_FRAME, whether the
detector fires, and the extent of that colour in the two button frames' rows (y 291 and 315) where it fires.

    notice-scan.py OUTDIR      OUTDIR exists; notice-scan.tsv is created there exclusively (never overwritten).
                               Needs E005_BUNDLES and E005_EXPLORE (machine-local, never written out).
"""
import hashlib
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "spike"))
spec = importlib.util.spec_from_file_location("analyze", ROOT / "experiments" / "E005-iw-dos-state-inventory" / "scripts" / "analyze.py")
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)
# cycle.py's constants, read from its source so that this scan measures exactly what the cycle uses
cycle_spec = importlib.util.spec_from_file_location("iw_dos_cycle_scan", ROOT / "runtime" / "iw-dos" / "spike" / "cycle.py")
cycle = importlib.util.module_from_spec(cycle_spec)
cycle_spec.loader.exec_module(cycle)


def count(raw, rect, colour):
    x, y, w, h = rect
    return sum(1 for yy in range(y, y + h) for xx in range(x, x + w)
               if tuple(raw[(yy * 640 + xx) * 3:(yy * 640 + xx) * 3 + 3]) == colour)


def runs_of(raw, y, colour):
    out, start = [], None
    for x in range(640):
        hit = tuple(raw[(y * 640 + x) * 3:(y * 640 + x) * 3 + 3]) == colour
        if hit and start is None:
            start = x
        if not hit and start is not None:
            out.append(f"{start}..{x - 1}")
            start = None
    return " ".join(out)


def main(outdir):
    rows = ["source\tname\tfile_sha256\tframe_pixels\tdetector_fires\tframe_row_291\tframe_row_315"]
    for source, folder in (("bundle", os.environ["E005_BUNDLES"]), ("explore", os.environ["E005_EXPLORE"])):
        for path in sorted(Path(folder).glob("*.png")):
            try:
                width, height, raw = analyze.read_png(path)
            except Exception:              # a PNG that is not one of cycle.py's (DOSBox-X's own capture): skipped
                continue
            if (width, height) != (640, 350):
                continue
            n = count(raw, cycle.NOTICE_FRAME, cycle.NOTICE_COLOUR)
            fires = n > cycle.NOTICE_MIN
            rows.append("\t".join([source, path.name, hashlib.sha256(path.read_bytes()).hexdigest(), str(n), str(fires),
                                   runs_of(raw, 291, cycle.NOTICE_COLOUR) if fires else "",
                                   runs_of(raw, 315, cycle.NOTICE_COLOUR) if fires else ""]))
    analyze.write(outdir, "notice-scan.tsv", "\n".join(rows) + "\n")
    fired = [r for r in rows[1:] if r.split("\t")[4] == "True"]
    print(f"{len(rows) - 1} captures, the detector fires on {len(fired)}")


if __name__ == "__main__":
    main(sys.argv[1])
