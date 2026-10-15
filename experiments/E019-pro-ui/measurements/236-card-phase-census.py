#!/usr/bin/env python3
"""Reproduce the #236 screen-test census from supplied local bundle directories.

The bundle directories are arguments so this provenance script contains no machine-local path.
It reads PNGs only, converts them to the measured 800x600 RGB8 stage, and emits counts from the
unchanged driver predicates. It performs no OCR and defines no thresholds.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime" / "iwp"))
from driver import screens  # noqa: E402


def census(bundle_dirs):
    rows = []
    for bundle_dir in bundle_dirs:
        folder = Path(bundle_dir)
        for path in sorted(folder.glob("*.png")):
            raw = subprocess.run(
                ["convert", str(path), "-depth", "8", "rgb:-"],
                check=True, capture_output=True,
            ).stdout
            if len(raw) != 800 * 600 * 3:
                continue
            counts = {name: screens.count(raw, test.rect, test.predicate)
                      for name, test in screens.TESTS.items()}
            rows.append({
                "bundle": folder.name,
                "asset": path.name,
                "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "raw_rgb8_sha256": hashlib.sha256(raw).hexdigest(),
                "counts": counts,
                "signals": screens.signals(raw),
            })
    return rows


def main(argv):
    if not argv:
        raise SystemExit("usage: 236-card-phase-census.py BUNDLE_DIR [BUNDLE_DIR ...]")
    rows = census(argv)
    print(json.dumps({
        "method": "Main-session ImageMagick RGB8 census using unchanged measured screen tests; "
                  "800x600 stage. No OCR, no new thresholds. Positive visual reading is r0030 "
                  "settled-before-continue and identical after; one unique positive only. Other "
                  "population frames include title/options/board/placement/attack/computers; "
                  "absence here is bounded, not universal.",
        "positive_raw_rgb8_sha256": "16a84dc21a66a6cbb12f52302133bd3963bf5819b66d9b0c5903b55432ee6776",
        "frames": rows,
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
