#!/usr/bin/env python3
"""The checks behind the iw-dos tokens of capabilities.json: exit 0 = verified, 1 = unavailable.

Usage: token_check.py <dosbox-x|artifact|run>

    dosbox-x   DOSBox-X 2024.03.01 is on PATH and says so (`dosbox-x -version`)
    artifact   the registered set iw-dos-3.1-30121376 matches in IW_DOS_DIR (`check --strict`)
    run        the run copy in IW_DOS_RUN is safe to launch from (rundir.run_problems)

These exist because the generic preflight (H3, game-archaeologist 07 §2) does not yet. Nothing here
prints an environment value or a local path.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rundir  # noqa: E402

DOSBOX = "dosbox-x"
VERSION = "DOSBox-X version 2024.03.01 "


def dosbox_x():
    if shutil.which(DOSBOX) is None:
        return "dosbox-x is not on PATH (apt: dosbox-x)"
    try:
        result = subprocess.run([DOSBOX, "-version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"dosbox-x -version did not run: {type(exc).__name__}"
    # `dosbox-x -version` prints its version and exits 1 (2024.03.01 on this machine), so the
    # status is not the verdict; the version line is.
    first = (result.stdout + result.stderr).strip().splitlines()[:1]
    if not first or not first[0].startswith(VERSION):
        return f"dosbox-x reports {first[0] if first else ''!r}, not 2024.03.01"
    return None


def artifact():
    try:
        locs = rundir.run_locations(need_run=False)
    except SystemExit as exc:
        return str(exc)
    ok, _ = rundir.strict_check(locs["IW_DOS_DIR"])
    return None if ok else f"{rundir.SET_ID} does not match in IW_DOS_DIR (check --strict)"


def run_copy():
    try:
        locs = rundir.run_locations()
    except SystemExit as exc:
        return str(exc)
    problems = rundir.run_problems(locs["IW_DOS_RUN"], locs["IW_DOS_DIR"])
    return "; ".join(problems)[:300] if problems else None


CHECKS = {"dosbox-x": dosbox_x, "artifact": artifact, "run": run_copy}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CHECKS:
        sys.exit(__doc__)
    problem = CHECKS[sys.argv[1]]()
    if problem:
        print(f"unavailable: {problem}")
        sys.exit(1)
    print("verified")
