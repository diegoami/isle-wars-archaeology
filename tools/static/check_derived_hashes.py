#!/usr/bin/env python3
"""Fail if a tracked file is something derived from an original (T26 Done-when 4, rule 18).

    python3 tools/static/check_derived_hashes.py [--root DIR]

Every output derived from an original (the unpacked executable, the carved movie, a decompiled
script, a Ghidra database) stays in the machine-local static folder, and is recorded here only by
sha256 and size, in `experiments/E008-static-triage/measurements/`. This script collects every
sha256 written in those records, then hashes every tracked file of the checkout and fails when one
has a listed hash: it would be that output itself. It also fails on a tracked file whose name is
one of the derived kinds (a Director movie, a Ghidra project file), whatever its bytes.

`tools/check_no_originals.py` does the same for the registered originals; this one covers the
outputs whose hashes `artifacts/known.json` cannot hold. Exit 0 clean, 1 not, 2 for a usage error.
"""
import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

HEX = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{64}(?![0-9a-fA-F])")
DERIVED_NAME = re.compile(r"\.(dxr|dir|dcr|cct|cst|cxt|lasm|gpr|rep|unpacked)$|\.ls$|^movie-[0-9]+", re.IGNORECASE)
MEASUREMENTS = "experiments/E008-static-triage/measurements"


def tracked_files(root):
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout
    return [name for name in out.decode("utf-8", "surrogateescape").split("\0") if name]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def listed_hashes(root, tracked):
    """{sha256: the measurement file that lists it}, from every tracked file under measurements/."""
    found = {}
    for name in tracked:
        if name.startswith(MEASUREMENTS + "/"):
            path = Path(root) / name
            if path.is_file():
                for value in HEX.findall(path.read_text(encoding="utf-8", errors="replace")):
                    found.setdefault(value, name)
    return found


def problems(root):
    root = Path(root)
    tracked = tracked_files(root)
    listed = listed_hashes(root, tracked)
    found = []
    for name in tracked:
        path = root / name
        if not path.is_file():
            continue
        if DERIVED_NAME.search(Path(name).name):
            found.append(f"{name}: a name of something derived from an original (a movie, a decompiled script, "
                         "a Ghidra file); these stay in the static folder")
        elif path.stat().st_size and sha256_file(path) in listed:
            found.append(f"{name}: its sha256 is listed in {listed[sha256_file(path)]} as an output derived "
                         "from an original; it must stay in the static folder")
    return tracked, listed, found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".", help="the checkout to check (default: the working directory)")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not (root / ".git").exists():
        print(f"{root}: not a git checkout")
        return 2
    tracked, listed, found = problems(root)
    if found:
        print("\n".join(found))
        return 1
    print(f"checked {len(tracked)} tracked files against {len(listed)} hashes listed in {MEASUREMENTS}: "
          "none is derived from an original")
    return 0


if __name__ == "__main__":
    sys.exit(main())
