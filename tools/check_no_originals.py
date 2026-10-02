#!/usr/bin/env python3
"""Fail if a tracked file looks like an original game file, or is too large to be anything but one.

CLAUDE.md rule 18 (U2): original game files and patched builds never enter this repository. A
.gitignore can be bypassed with `git add -f`, so CI checks what is actually tracked. Exit 0 clean, 1 not.
"""
import re
import subprocess
import sys
from pathlib import Path

PATTERN = re.compile(r"\.(exe|com|dll|ovl|hlp|cnt|zip|iso|img|vhd|sav|png|mp4|wav)$", re.IGNORECASE)
MAX_BYTES = 1024 * 1024
root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root, text=True).split("\0")
problems = []
for name in filter(None, tracked):
    path = root / name
    if PATTERN.search(name) or name.startswith("originals/"):
        problems.append(f"{name}: an original-file or evidence-media type; it belongs on the user's machine or in a release")
    elif path.is_file() and path.stat().st_size > MAX_BYTES:
        problems.append(f"{name}: {path.stat().st_size} bytes, over {MAX_BYTES}; nothing here should be that large")
print("\n".join(problems) if problems else f"no original files tracked ({len(tracked) - 1} files checked)")
sys.exit(1 if problems else 0)
