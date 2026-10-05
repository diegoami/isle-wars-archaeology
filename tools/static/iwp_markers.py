#!/usr/bin/env python3
"""Count ProjectorRays' error markers in the scripts of an earlier extraction run (T26 round 1, R5).

    IWA_STATIC=<folder outside every checkout> python3 tools/static/iwp_markers.py
        --dir iwp-extract-<run> --against <record of that run> [--record NAME]

ProjectorRays (0.2.0, commit 8a3d3b4) marks what it could not decompile in its output text, and
nowhere else: the word `ERROR` stands for an expression it could not build (its `ErrorNode`), for a
name missing from the name table (`Lingo::getName`) and for a variable of an unknown kind, and a
comment `-- ERROR: ...` for control flow it could not identify (`src/director/lingo.cpp` and
`src/director/handler.cpp` of that commit). In the bytecode listings (`.lasm`) an opcode it does not
know is named `unk` and two upper-case hex digits (`Lingo::getOpcodeName`).

This script counts those markers, as whole words, in the `.ls` and `.lasm` files that
`iwp_extract.py` wrote into `<IWA_STATIC>/<dir>/movie-NN-out/`. It counts only the files the run's
record lists (the record's `scripts`), each found by its own identity (kind, number and name, as in
its file name) and checked against its own sha256, and stops when one of them is missing or changed,
or when the numbers of files read differ from the record's, so the count is of the scripts the
record describes (round 2, R2: a check by hash alone let a changed script pass when another script
still had its former hash). It prints counts only, and `--record NAME`
writes them as a new measurement; never a line of the scripts. It reads no original.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import static_common as common  # noqa: E402
import iwp_extract  # noqa: E402

ERROR_WORD = re.compile(r"\bERROR\b")
UNKNOWN_OPCODE = re.compile(r"\bunk[0-9A-F]{2}\b")
TOOL_SOURCE = "ProjectorRays 0.2.0, commit 8a3d3b4211575170276fc6be350b6b52e96d4750"


def identity(kind, number, name):
    """A script's identity: its kind, number and name, as `iwp_extract.py` read them from its file name."""
    return kind, int(number), name or ""


def checked_text(path, sha256):
    """The text of a regular file (its own name not followed) when its bytes have the sha256 given;
    None when it is missing, a link or other bytes. The bytes hashed are the bytes counted."""
    try:
        with common.safeio.open_source(path) as fh:
            data = fh.read()
    except (common.safeio.Refused, OSError):
        return None
    if hashlib.sha256(data).hexdigest() != sha256:
        return None
    return data.decode("utf-8", errors="replace")


def count_markers(out_dir, scripts):
    """Marker counts over the scripts of one movie's output folder; SystemExit unless every script the
    record lists is there, under its own identity, with its own recorded sha256 (round 2, R2).

    Scripts are checked one by one, never as a set of hashes: two scripts may have the same text, and
    one of them changed or missing must not pass because the other still has the hash. A `.ls` file
    is found by its identity (one file per identity in the folder), and its `.lasm` is the file beside
    it, as `iwp_extract.py` read it. The numbers of scripts and listings read must be the record's."""
    found = {}                      # identity -> the .ls file of that identity in the output folder
    for path in sorted(Path(out_dir).rglob("*")):
        match = iwp_extract.SCRIPT_NAME.match(path.name)
        if not match or match.group(4) != "ls":
            continue
        key = identity(match.group(1), match.group(2), match.group(3))
        if key in found:
            common.die(f"two script files in {Path(out_dir).name} are {key[0]} {key[1]}; nothing was counted")
        found[key] = path
    counts = {"ls_files": 0, "lasm_files": 0, "error_words_in_ls": 0, "ls_files_with_an_error_word": 0,
              "unknown_opcodes_in_lasm": 0, "lasm_files_with_an_unknown_opcode": 0}
    bad, listed = [], set()
    for script in scripts:
        key = identity(script["kind"], script["number"], script.get("name"))
        if key in listed:
            common.die(f"the record lists {key[0]} {key[1]} twice; nothing was counted")
        listed.add(key)
        ls_path = found.get(key)
        ls_text = checked_text(ls_path, script["ls_sha256"]) if ls_path else None
        lasm_path = ls_path.with_suffix(".lasm") if ls_path else None
        want_lasm = script.get("lasm_sha256")
        if want_lasm is None:
            lasm_text = ""
            lasm_ok = lasm_path is not None and not os.path.lexists(lasm_path)
        else:
            lasm_text = checked_text(lasm_path, want_lasm) if lasm_path else None
            lasm_ok = lasm_text is not None
        if ls_text is None or not lasm_ok:
            bad.append(key)
            continue
        words = len(ERROR_WORD.findall(ls_text))
        counts["ls_files"] += 1
        counts["error_words_in_ls"] += words
        counts["ls_files_with_an_error_word"] += bool(words)
        if want_lasm is not None:
            unknown = len(UNKNOWN_OPCODE.findall(lasm_text))
            counts["lasm_files"] += 1
            counts["unknown_opcodes_in_lasm"] += unknown
            counts["lasm_files_with_an_unknown_opcode"] += bool(unknown)
    if bad:
        common.die(f"{len(bad)} script(s) the record lists are not in {Path(out_dir).name} under their own name "
                   f"with their recorded sha256 (the first: {bad[0][0]} {bad[0][1]}); nothing was counted")
    return counts


def main(argv=None, env=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dir", required=True, help="the extraction run's folder in the static folder")
    parser.add_argument("--against", required=True, help="that run's record, a file name in the measurements folder")
    parser.add_argument("--record")
    args = parser.parse_args(argv)
    root = common.static_root(env)
    try:
        common.safeio.safe_name(args.dir, "run directory")
        common.safeio.safe_name(args.against, "record name")
    except common.safeio.Refused as exc:
        common.die(str(exc))
    run_dir = root / args.dir
    if run_dir.is_symlink() or not run_dir.is_dir():
        common.die(f"{args.dir} is not a directory of the static folder")
    source = common.ROOT / common.MEASUREMENTS / args.against
    try:
        record = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        common.die(f"{args.against} cannot be read as a record: {exc}")
    result = {"run_directory": args.dir, "against": args.against, "tool_source": TOOL_SOURCE,
              "markers": {"ls": "the word ERROR", "lasm": "unk and two upper-case hex digits"}, "movies": []}
    if not record.get("movies"):
        common.die(f"{args.against} lists no movie; nothing was counted")
    for movie in record["movies"]:
        out_dir = run_dir / f"movie-{movie['movie']:02d}-out"
        counts = count_markers(out_dir, movie.get("scripts", []))
        # every script the record counted was read: its `scripts` list is not short of its `script_count`
        if counts["ls_files"] != movie.get("script_count"):
            common.die(f"movie {movie['movie']}: {counts['ls_files']} scripts were counted, the record's "
                       f"script_count is {movie.get('script_count')}; nothing was counted")
        result["movies"].append(dict(counts, movie=movie["movie"], scripts_in_record=len(movie.get("scripts", []))))
    if args.record:
        name = args.record if args.record.endswith(".json") else args.record + ".json"
        print(f"record: {common.write_record(name, result)}")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
