#!/usr/bin/env python3
"""Check (no longer correct) the classes of the E005 evidence manifests.

Round 0 (F007 "Manifests"; the correction is commit 2ef562a): the cycle wrote `"class": "file"` for the game-written files
it kept, a class evidence-manifest/1 does not allow, and this script then rewrote the 26 manifests of r0001 to r0026
once, giving those entries `save` or `measurement` and changing nothing else (git history keeps both versions). A
script that rewrites a manifest is a script that can overwrite a measured output, so since round 1 (PR #58 R3) it
only reports: it lists every manifest entry whose class is `file` and exits 1 if there is one, writing nothing.

    fix-manifest-classes.py [ROOT]      ROOT: the checkout (default: this one)
"""
import json
import sys
from pathlib import Path


def main(root):
    bad = []
    for path in sorted((Path(root) / "evidence" / "E005").glob("E005-r*.manifest.json")):
        for entry in json.loads(path.read_text())["files"]:
            if entry["class"] == "file":
                bad.append(f"{path.name}: {entry['name']}")
    print("\n".join(bad) if bad else "no manifest entry has the class `file`")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]))
