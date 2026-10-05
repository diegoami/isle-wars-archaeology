#!/usr/bin/env python3
"""Import an executable into Ghidra headless, analyse it as 16-bit real mode, and report counts (T26).

    IWA_STATIC=<folder outside every checkout> IW_DOS_DIR=<the copy> python3 tools/static/ghidra_import.py
        (--original iw-dos | --file <name in the static folder> --sha256 <hex>)
        [--needle TEXT]... [--range SEG:OFF-SEG:OFF]... [--language ID] [--run ID] [--record NAME]

The input is one of:
- `--original KEY`: the original in place (`iw-dos` or `iwp`), which must match its registered sha256
  (`static_common.original`); Ghidra reads it where it is, and it is hashed again afterwards;
- `--file NAME --sha256 HEX`: a file inside the static folder (the unpacked executable of an earlier
  run), which must match the given sha256.

Ghidra's project, its log and the report (`tools/static/ghidra/T26Report.java`) are written into the
new directory `<IWA_STATIC>/ghidra-<run>/`. The report holds counts, addresses and function names.
`--record NAME` writes those, with the tool versions and the exit code, to
`experiments/E008-static-triage/measurements/NAME` as a new file. No disassembly is printed.

`--range START-END` (addresses as Ghidra writes them, `1000:9b33`) has the post-script disassemble
from START, following the flow, and write the instructions from START to END into the file
`listing-<START>.txt` of the run directory, in the static folder, for a person to read there; the
report, and so the record, gets only the range, its instruction count and its count of far calls
(the feasibility probe of T26: the code that writes `ISLEWAR.SAV`, found by `dos_probe.py`).
"""
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import static_common as common  # noqa: E402

LANGUAGE = "x86:LE:16:Real Mode"
SCRIPT_DIR = Path(__file__).resolve().parent / "ghidra"
RANGE = re.compile(r"[0-9a-f]{4}:[0-9a-f]{4}-[0-9a-f]{4}:[0-9a-f]{4}")


def tool_identity(ghidra, java):
    props = {}
    for line in (ghidra / "Ghidra" / "application.properties").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            props[key] = value
    release = {}
    for line in (java / "release").read_text().splitlines():
        key, _, value = line.partition("=")
        release[key] = value.strip('"')
    return {"ghidra": {"version": props.get("application.version"), "path": common.anonymise(ghidra),
                       "revision": props.get("application.revision.ghidra"),
                       "build_date": props.get("application.build.date.short")},
            "java": {"version": release.get("JAVA_RUNTIME_VERSION"), "implementor": release.get("IMPLEMENTOR_VERSION"),
                     "path": common.anonymise(java),
                     "modules_sha256": common.sha256_path(java / "lib" / "modules")[0]}}


def project_location(project):
    """(path Ghidra is given, a temporary folder to remove or None). Ghidra refuses a project path with
    a folder whose name starts with a dot (`.local` is one), so then it gets a link, in a fresh
    temporary folder, to the project folder in the static root; the files are written in the static
    root all the same."""
    if not any(part.startswith(".") for part in Path(project).parts):
        return Path(project), None
    holder = Path(tempfile.mkdtemp(prefix="iwa-ghidra-"))
    os.symlink(project, holder / "project")
    return holder / "project", holder


def parse_report(text):
    result = {"blocks": [], "needles": [], "ranges": []}
    needle = None
    for line in text.splitlines():
        if line.startswith("needle "):
            name, _, hits = line[len("needle "):].rpartition(" hits=")
            needle = {"text": name, "hits": int(hits), "occurrences": []}
            result["needles"].append(needle)
        elif line.startswith("  at ") and needle is not None:
            needle["occurrences"].append({"at": line.split()[1], "offset": line.split("offset=")[1], "references": []})
        elif line.startswith("    ") and needle is not None and needle["occurrences"]:
            needle["occurrences"][-1]["references"].append(line.strip())
        elif line.startswith("range "):
            _, start, end, *counts = line.split()
            item = {"start": start, "end": end}
            item.update({k: int(v) for k, v in (c.split("=") for c in counts)})
            result["ranges"].append(item)
        elif line.startswith("block "):
            _, name, start, size = line.split(" ", 3)
            result["blocks"].append({"name": name, "start": start, "size": int(size)})
        elif "=" in line:
            key, _, value = line.partition("=")
            result[key] = int(value) if value.isdigit() else value
    return result


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--original", choices=sorted(common.ORIGINALS), help="the original, in place")
    source.add_argument("--file", help="a file inside the static folder (a relative name)")
    parser.add_argument("--sha256", help="the sha256 the --file must have")
    parser.add_argument("--needle", action="append", default=[], help="text to search for (addresses are reported)")
    parser.add_argument("--range", action="append", default=[], help="START-END: disassemble and list into the run folder")
    parser.add_argument("--language", default=LANGUAGE)
    parser.add_argument("--run")
    parser.add_argument("--record")
    parser.add_argument("--timeout", type=int, default=1800)
    return parser


def main(argv=None, env=None):
    args = build_parser().parse_args(argv)
    originals = (args.original,) if args.original else ()
    root = common.static_root(env, originals=originals)
    for item in args.range:
        if not RANGE.fullmatch(item):
            common.die(f"--range {item!r} is not START-END with addresses like 1000:9b33")
    if args.original:
        original = common.original(args.original, env)
        target, identity = original.path, {"original": original.set_id, "file": original.rel,
                                           "sha256": original.sha256, "bytes": original.size}
    else:
        target, size = common.derived(root, args.file, args.sha256)
        original, sha = None, args.sha256
        identity = {"derived_file_sha256": sha, "bytes": size}
    ghidra = common.tool_home("IWA_GHIDRA", ["ghidra_12.1.4_PUBLIC"])
    java = common.tool_home("IWA_JAVA_HOME", ["jdk-21.0.12.1+1"])
    headless = ghidra / "support" / "analyzeHeadless"
    if not headless.is_file() or not (java / "bin" / "java").is_file():
        common.die("Ghidra or its Java runtime is not installed (setup/static/README.md): a missing tool is a "
                   "step to finish, never a reason to fall back to runs (U32)")
    run_dir = common.new_run_dir(root, "ghidra", args.run)
    common.safeio.make_directory(run_dir, "project")
    project, holder = project_location(run_dir / "project")
    report = run_dir / "report.txt"
    command = [headless, project, "t26", "-import", target, "-processor", args.language,
               "-cspec", "default", "-scriptPath", SCRIPT_DIR, "-postScript", "T26Report.java", report,
               *args.needle, *[f"range={r}" for r in args.range], "-log", run_dir / "ghidra.log"]
    child_env = dict(os.environ if env is None else env)
    child_env["JAVA_HOME"] = str(java)
    child_env["PATH"] = str(java / "bin") + os.pathsep + child_env.get("PATH", "")
    try:
        code, seconds = common.run(command, run_dir, run_dir, "analyzeHeadless", env=child_env,
                                   timeout=args.timeout)
    finally:
        if holder is not None:
            shutil.rmtree(holder, ignore_errors=True)       # the link only: rmtree never follows it
    if original is not None:
        original.recheck()
    result = {"tools": tool_identity(ghidra, java), "input": identity, "language": args.language,
              "analyzeHeadless_exit": code, "seconds": seconds, "needles": args.needle, "ranges": args.range}
    if code == 0 and report.is_file():
        result["report"] = parse_report(report.read_text(encoding="utf-8"))
    if args.record:
        name = args.record if args.record.endswith(".json") else args.record + ".json"
        print(f"record: {common.write_record(name, result)}")
    print(json.dumps({"run_directory": run_dir.name, "exit": code,
                      "functions": result.get("report", {}).get("functions")}, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
