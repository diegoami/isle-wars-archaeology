#!/usr/bin/env python3
"""The crafted-save writer (T16): write ISLEWAR.SAV from a decoded position into a run copy, and nowhere else.

A crafted save is an I3 intervention (vocabulary/interventions.md). What this module guarantees:
- it writes only the name ISLEWAR.SAV (savefmt.FILE_NAME), never another name, a path or a link;
- it writes only into a run copy: `<run_dir>/game` of a run directory outside every checkout, which is not IW_DOS_DIR
  under any name (run_copy_problems) and holds the registered set intact. IW_DOS_DIR itself, a directory that
  overlaps it and any other directory are refused, so a crafted save is never written where the install is;
- it writes only a position that savefmt.encode accepts, whose bytes decode back to that position (the round-trip
  check), and it creates the file new (an existing ISLEWAR.SAV is never replaced).

The cycle calls `place` after its launch checks, while the game is at the option box (cycle.py `put-save`); the reset
at the end of the run removes the file again. Command line (positions are JSON, see savefmt.py):

    writer.py decode FILE                       print the position in a save the game wrote
    writer.py roundtrip FILE [FILE ...]         exit 0 when every save encodes back to its own bytes
    writer.py craft BASE.SAV EDIT [EDIT ...]    print the position of BASE with the edits applied (JSON)
        EDIT: owner:N=colour   armies:N=V   cards:colour=D,D,..   centres=N,N,..   dft=A,B   settings=A,B
    writer.py write POSITION.json --run-dir DIR --install DIR     place the save in DIR/game
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "setup" / "iwp"))
sys.path.insert(0, str(ROOT / "setup" / "iw-dos"))
sys.path.insert(0, str(HERE))
import rundir  # noqa: E402
import safeio  # noqa: E402
import savefmt  # noqa: E402


GAME_WRITES = ("ISLEWAR.SCR", "ISLEWAR.DFT")     # the files the game itself adds to the run copy before a Load (F007)


def run_copy_problems(run_dir, install):
    """What is wrong with <run_dir>/game as a place to put a crafted save; [] when nothing is. Not the seal's
    `check --strict` (rundir.run_problems): the game is running and has added its own ISLEWAR.SCR by now, which
    strict refuses. This checks what matters for one write: the run copy is a real directory that is not IW_DOS_DIR
    under any name (mounts, device and inode identities: rundir.alias_problems), and it holds every registered file
    intact, with nothing else but the files the game writes itself."""
    run_dir, install = Path(run_dir), Path(install)
    game = run_dir / rundir.GAME_DIR
    if run_dir.is_symlink() or not run_dir.is_dir():
        return ["the run directory is not a real directory"]
    if game.is_symlink() or not game.is_dir():
        return ["the run copy is not a real directory"]
    problems = list(rundir.alias_problems(run_dir, install))
    canonical = rundir.locations.real(game)
    if rundir.locations.inside(canonical, install) or rundir.locations.inside(install, canonical):
        problems.append("the run copy overlaps IW_DOS_DIR")
    if problems:
        return problems
    registered = {f["path"]: f["sha256"] for f in rundir.manifest()["files"]}
    for rel, digest in sorted(registered.items()):
        if safeio.sha256_plain(game, rel) != digest:
            problems.append(f"{rel} is not the registered file")
    problems += [f"{name} is not part of the registered set" for name in sorted(os.listdir(game))
                 if name not in registered and name not in GAME_WRITES]
    return problems


def place(run_dir, install, position, name=savefmt.FILE_NAME):
    """Write the save of `position` into <run_dir>/game as `name`; returns (bytes, sha256 hex). Refused (savefmt.Refused)
    for any name but ISLEWAR.SAV, for a run directory that is not a run copy of this install, and for a position
    that cannot be encoded."""
    if name != savefmt.FILE_NAME:
        raise savefmt.Refused(f"only {savefmt.FILE_NAME} is written, not {name!r}")
    try:
        where = rundir.run_locations({"IW_DOS_DIR": str(install), "IW_DOS_RUN": str(run_dir)})
    except SystemExit as exc:
        raise savefmt.Refused(f"not a run directory outside every checkout and IW_DOS_DIR: {exc}") from None
    run_dir, install = where["IW_DOS_RUN"], where["IW_DOS_DIR"]
    problems = run_copy_problems(run_dir, install)
    if problems:
        raise savefmt.Refused("not a run copy to write into: " + "; ".join(problems)[:300])
    data = savefmt.encode(position)
    try:
        safeio.write_file(run_dir / rundir.GAME_DIR, name, data=data, exist="new", mode=0o644)
    except safeio.Refused as exc:
        raise savefmt.Refused(f"the save was not written: {exc}") from None
    return data, hashlib.sha256(data).hexdigest()


def edit(position, edits):
    """The position with each `owner:N=colour`, `armies:N=V`, `cards:colour=D,D`, `centres=N,N`, `dft=A,B`,
    `settings=A,B` applied (a copy). A bad edit is a ValueError; whether the result can be encoded is encode's to say."""
    out = json.loads(json.dumps(position))
    for item in edits:
        key, sep, value = item.partition("=")
        if not sep:
            raise ValueError(f"not an edit: {item!r}")
        what, _, arg = key.partition(":")
        if what == "owner":
            out["owners"][int(arg) - 1] = value
        elif what == "armies":
            out["armies"][int(arg) - 1] = int(value)
        elif what == "cards":
            out["cards"][arg] = [int(ch) for ch in value.split(",") if ch]
        elif what in ("centres", "dft", "settings"):
            out[what] = [int(v) for v in value.split(",") if v]
        else:
            raise ValueError(f"not an edit: {item!r}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("decode").add_argument("file")
    sub.add_parser("roundtrip").add_argument("files", nargs="+")
    craft = sub.add_parser("craft")
    craft.add_argument("base")
    craft.add_argument("edits", nargs="+")
    write = sub.add_parser("write")
    write.add_argument("position")
    write.add_argument("--run-dir", required=True)
    write.add_argument("--install", required=True)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "decode":
            print(json.dumps(savefmt.decode(Path(args.file).read_bytes()), indent=1))
        elif args.cmd == "roundtrip":
            bad = [f for f in args.files if not savefmt.roundtrip(Path(f).read_bytes())]
            for f in bad:
                print(f"does not round-trip: {f}", file=sys.stderr)
            return 1 if bad else 0
        elif args.cmd == "craft":
            position = edit(savefmt.decode(Path(args.base).read_bytes()), args.edits)
            savefmt.check(position)
            print(json.dumps(position, indent=1))
        else:
            data, digest = place(args.run_dir, args.install, json.loads(Path(args.position).read_text()))
            print(f"wrote {savefmt.FILE_NAME}: {len(data)} bytes, sha256 {digest}")
    except (savefmt.SaveError, savefmt.Refused, ValueError, OSError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
