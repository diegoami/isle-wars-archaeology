#!/usr/bin/env python3
"""Fail if a tracked file is something derived from an original (T26 Done-when 4, rule 18).

    python3 tools/static/check_derived_hashes.py [--root DIR]

Every output derived from an original (the unpacked executable, the carved movie, a decompiled
script, a Ghidra database) stays in the machine-local static folder, and is recorded here only by
sha256 and size, in `experiments/E008-static-triage/measurements/`. Each run's record, and the
inventories of `inventory_derived.py`, list every file of the run directory under `derived_files`
(the tool's own files too: a Ghidra database, a listing, a dumped chunk). This script collects every
sha256 written in those records, the inventoried ones with their path in the run, then hashes
every tracked file of the checkout and fails when one has a listed hash: it would be that output
itself, whatever its name. It also fails on a tracked file whose name is one of the derived kinds
(a Director movie, a Ghidra project file), whatever its bytes.

`tools/check_no_originals.py` does the same for the registered originals; this one covers the
outputs whose hashes `artifacts/known.json` cannot hold. Exit 0 clean, 1 not, 2 for a usage error.
"""
import argparse
import hashlib
import json
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


def inventoried(doc):
    """Every {path, sha256} entry of a `derived_files` list anywhere in a parsed record."""
    if isinstance(doc, dict):
        for key, value in doc.items():
            if key == "derived_files" and isinstance(value, list):
                yield from (item for item in value if isinstance(item, dict) and isinstance(item.get("sha256"), str))
            else:
                yield from inventoried(value)
    elif isinstance(doc, list):
        for value in doc:
            yield from inventoried(value)


def listed_hashes(root, tracked):
    """({sha256: where it is listed}, the number of inventoried files), from every tracked file
    under measurements/: each `derived_files` entry of a JSON record, then any other sha256."""
    found, count = {}, 0
    for name in tracked:
        if not name.startswith(MEASUREMENTS + "/"):
            continue
        path = Path(root) / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if name.endswith(".json"):
            try:
                doc = json.loads(text)
            except ValueError:
                doc = None
            for item in inventoried(doc):
                count += 1
                found.setdefault(item["sha256"], "%s (the run's file %s)" % (name, item.get("path")))
        for value in HEX.findall(text):
            found.setdefault(value, name)
    return found, count


def problems(root):
    root = Path(root)
    tracked = tracked_files(root)
    listed, count = listed_hashes(root, tracked)
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
    return tracked, listed, count, found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".", help="the checkout to check (default: the working directory)")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not (root / ".git").exists():
        print(f"{root}: not a git checkout")
        return 2
    tracked, listed, count, found = problems(root)
    if found:
        print("\n".join(found))
        return 1
    print(f"checked {len(tracked)} tracked files against {len(listed)} hashes listed in {MEASUREMENTS} "
          f"({count} inventoried derived files among them): none is derived from an original")
    return 0


if __name__ == "__main__":
    sys.exit(main())
