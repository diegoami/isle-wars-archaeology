#!/usr/bin/env python3
"""Check the static-analysis tools of T26 against `setup/static/tools.json`.

    python3 setup/static/check_tools.py [--root TOOLS_FOLDER] [--only NAME]...

The tools folder is `--root`, else `$IWA_TOOLS`, else `$HOME/tools`. For each tool the file lists,
the script finds its folder, hashes each listed file and compares it with the recorded sha256. It
prints one line per tool and `ready` only when every checked tool matches; it exits 1 otherwise,
naming what is missing or different. A missing tool is a step to finish, never a reason to fall
back to runs (U32). Nothing is installed or changed, and no original is read.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(tools, root, only=()):
    """[(tool name, ok, text)] for each tool of the manifest (or the named ones)."""
    results = []
    for tool in tools["tools"]:
        if only and tool["name"] not in only:
            continue
        folder = Path(root) / tool["dir"]
        if not folder.is_dir():
            results.append((tool["name"], False, f"{tool['name']} {tool['version']}: folder {tool['dir']} is missing"))
            continue
        bad = []
        for rel, expected in sorted(tool["files"].items()):
            path = folder / rel
            if not path.is_file():
                bad.append(f"{rel} is missing")
            elif sha256_file(path) != expected:
                bad.append(f"{rel} has another sha256 than the recorded one")
        if bad:
            results.append((tool["name"], False, f"{tool['name']} {tool['version']}: " + "; ".join(bad)))
        else:
            results.append((tool["name"], True, f"{tool['name']} {tool['version']}: {len(tool['files'])} files match"))
    for name in only:
        if name not in {tool["name"] for tool in tools["tools"]}:
            results.append((name, False, f"{name}: not in tools.json"))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", help="the tools folder (default: $IWA_TOOLS, else $HOME/tools)")
    parser.add_argument("--only", action="append", default=[], help="check only this tool")
    parser.add_argument("--manifest", default=str(HERE / "tools.json"))
    args = parser.parse_args(argv)
    root = args.root or os.environ.get("IWA_TOOLS") or str(Path.home() / "tools")
    tools = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    results = check(tools, root, args.only)
    for _, _, text in results:
        print(text)
    ok = bool(results) and all(ok for _, ok, _ in results)
    print("ready" if ok else "not ready")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
