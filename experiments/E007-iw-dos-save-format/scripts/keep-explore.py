#!/usr/bin/env python3
"""Copy the text outputs of --explore runs (run log, observations, changes log, DOSBox-X log and configuration)
into measurements/explore/, and list every capture and kept game-written file by sha256 (the images and the files
themselves stay on this machine, in E007_EXPLORE: never committed).

    keep-explore.py KEY [KEY ...]     KEY: the prefix of one run's outputs, `<arm>.<start>.<x-id>` (cycle.py
                                      explore_key); the prefix is `<arm>.<start>.<x-id>`

Never replaces and never deletes (CLAUDE.md rule 20, PR #58 R3): a destination that exists with the same bytes is
left as it is; one with other bytes stops the script with nothing written for that file. Each file is created
exclusively. Machine-local paths come from the environment (E007_EXPLORE) and are never written out.
"""
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEXT = ("run.log", "observations.json", "changes.log", "dosbox.conf.txt", "dosbox.log")
DESTINATION = ROOT / "experiments" / "E007-iw-dos-save-format" / "measurements" / "explore"


def put(dst, name, data):
    """Create dst/name with data; the same bytes already there are kept; other bytes are a SystemExit."""
    target = Path(dst) / name
    try:
        with open(target, "xb") as fh:
            fh.write(data)
    except FileExistsError:
        if target.read_bytes() != data:
            raise SystemExit(f"{name} is already kept with other bytes; nothing replaced") from None


def keep(src, dst, key):
    src, dst = Path(src), Path(dst)
    for suffix in TEXT:
        path = src / f"{key}.{suffix}"
        if path.is_file():
            put(dst, path.name, path.read_bytes())
    rows = []
    for path in sorted(src.glob(f"{key}.*")):
        rest = path.name[len(key) + 1:]
        if path.is_file() and (rest.endswith(".png") or "ISLEWAR." in rest):
            data = path.read_bytes()
            rows.append(f"{hashlib.sha256(data).hexdigest()}\t{len(data)}\t{rest}\n")
    put(dst, f"{key}.captures.sha256.tsv", "".join(rows).encode())


def main(keys):
    src = Path(os.environ["E007_EXPLORE"])
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for key in keys:
        keep(src, DESTINATION, key)


if __name__ == "__main__":
    main(sys.argv[1:])
