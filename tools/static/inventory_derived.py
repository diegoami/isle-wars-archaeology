#!/usr/bin/env python3
"""Record the sha256 and size of every file in run directories of the static folder (T26, rule 18).

    IWA_STATIC=<folder outside every checkout> python3 tools/static/inventory_derived.py
        (--dir NAME... | --all) --prefix PREFIX

The static scripts list their run directory's files in their own record (`derived_files`). This one
does the same for run directories made before they did, or by hand: for each directory named (or
each one in the static folder, `--all`), it writes the new measurement
`experiments/E008-static-triage/measurements/<PREFIX>-<directory>.json` with `derived_files`, the
file names relative to the run directory, each with its sha256 and size. It reads no original and
copies nothing; `check_derived_hashes.py` then knows each listed file by its bytes. An existing
record is never rewritten: a second inventory takes a new prefix.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import static_common as common  # noqa: E402


def main(argv=None, env=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--dir", action="append", help="a run directory's name in the static folder")
    which.add_argument("--all", action="store_true", help="every directory of the static folder")
    parser.add_argument("--prefix", required=True, help="the records' name prefix, e.g. inventory-r3")
    args = parser.parse_args(argv)
    root = common.static_root(env)
    try:
        common.safeio.identifier(args.prefix, "prefix")
        for name in args.dir or ():
            common.safeio.safe_name(name, "run directory")
    except common.safeio.Refused as exc:
        common.die(str(exc))
    names = sorted(p.name for p in root.iterdir() if p.is_dir() and not p.is_symlink()) if args.all else args.dir
    summary = []
    for name in names:
        run_dir = root / name
        if run_dir.is_symlink() or not run_dir.is_dir():
            common.die(f"{name} is not a directory of the static folder")
        files = common.inventory(run_dir)
        record = {"run_directory": name, "file_count": len(files),
                  "bytes": sum(item.get("bytes", 0) for item in files), "derived_files": files}
        written = common.write_record(f"{args.prefix}-{name}.json", record)
        summary.append({"record": str(written), "files": len(files)})
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
