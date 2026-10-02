#!/usr/bin/env python3
"""Fail if a tracked file looks like an original game file, or is too large to be anything but one.

CLAUDE.md rule 18 (U2): original game files and patched builds never enter this repository. A
.gitignore can be bypassed with `git add -f`, so CI checks what is actually tracked. That means a
tracked file is a problem if its extension is an original-file or evidence-media type, if it is
larger than any source file should be, or if its bytes are one of the artifact sets registered by
hash in artifacts/known.json. Exit 0 clean, 1 not.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PATTERN = re.compile(r"\.(exe|com|dll|ovl|hlp|cnt|zip|iso|img|vhd|x32|sav|png|mp4|wav)$", re.IGNORECASE)
MAX_BYTES = 1024 * 1024
root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root, text=True).split("\0")


def known_hashes():
    """Every file hash of every artifact set in artifacts/known.json."""
    known = root / "artifacts" / "known.json"
    if not known.is_file():
        return set()
    hashes = set()
    for entry in json.loads(known.read_text(encoding="utf-8")).get("sets", []):
        for record in entry.get("manifest", {}).get("files", []):
            if isinstance(record.get("sha256"), str):
                hashes.add(record["sha256"])
    return hashes


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


registered = known_hashes()
problems = []
for name in filter(None, tracked):
    path = root / name
    if PATTERN.search(name) or name.startswith("originals/"):
        problems.append(f"{name}: an original-file or evidence-media type; it belongs on the user's machine or in a release")
    elif path.is_file() and path.stat().st_size > MAX_BYTES:
        problems.append(f"{name}: {path.stat().st_size} bytes, over {MAX_BYTES}; nothing here should be that large")
    elif registered and path.is_file() and sha256_file(path) in registered:
        problems.append(f"{name}: sha256 is in artifacts/known.json; the bytes of a registered artifact never enter this repository")
print("\n".join(problems) if problems else f"no original files tracked ({len(tracked) - 1} files checked)")
sys.exit(1 if problems else 0)
