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
record lists (the record's `scripts`, by sha256), and stops when one of them is missing or changed,
so the count is of the scripts the record describes. It prints counts only, and `--record NAME`
writes them as a new measurement; never a line of the scripts. It reads no original.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import static_common as common  # noqa: E402
import iwp_extract  # noqa: E402

ERROR_WORD = re.compile(r"\bERROR\b")
UNKNOWN_OPCODE = re.compile(r"\bunk[0-9A-F]{2}\b")
TOOL_SOURCE = "ProjectorRays 0.2.0, commit 8a3d3b4211575170276fc6be350b6b52e96d4750"


def count_markers(out_dir, scripts):
    """Marker counts over the scripts of one movie's output folder; SystemExit when a script the
    record lists is not there with its recorded sha256."""
    wanted = set()                  # (sha256, "ls" or "lasm"): an empty script has the sha256 of an empty listing
    for script in scripts:
        wanted.add((script["ls_sha256"], "ls"))
        if script.get("lasm_sha256"):
            wanted.add((script["lasm_sha256"], "lasm"))
    seen = set()
    counts = {"ls_files": 0, "lasm_files": 0, "error_words_in_ls": 0, "ls_files_with_an_error_word": 0,
              "unknown_opcodes_in_lasm": 0, "lasm_files_with_an_unknown_opcode": 0}
    for path in sorted(Path(out_dir).rglob("*")):
        match = iwp_extract.SCRIPT_NAME.match(path.name) if path.is_file() and not path.is_symlink() else None
        if not match:
            continue
        sha, _ = common.sha256_path(path)
        if (sha, match.group(4)) not in wanted:
            continue
        seen.add((sha, match.group(4)))
        text = path.read_text(encoding="utf-8", errors="replace")
        if match.group(4) == "ls":
            found = len(ERROR_WORD.findall(text))
            counts["ls_files"] += 1
            counts["error_words_in_ls"] += found
            counts["ls_files_with_an_error_word"] += bool(found)
        else:
            found = len(UNKNOWN_OPCODE.findall(text))
            counts["lasm_files"] += 1
            counts["unknown_opcodes_in_lasm"] += found
            counts["lasm_files_with_an_unknown_opcode"] += bool(found)
    missing = set(wanted) - seen
    if missing:
        common.die(f"{len(missing)} script file(s) the record lists are not in {Path(out_dir).name} with their "
                   "recorded sha256; nothing was counted")
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
    for movie in record.get("movies", []):
        out_dir = run_dir / f"movie-{movie['movie']:02d}-out"
        counts = count_markers(out_dir, movie.get("scripts", []))
        result["movies"].append(dict(counts, movie=movie["movie"], scripts_in_record=len(movie.get("scripts", []))))
    if args.record:
        name = args.record if args.record.endswith(".json") else args.record + ".json"
        print(f"record: {common.write_record(name, result)}")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
