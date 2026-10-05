#!/usr/bin/env python3
"""Done-when 2 of T21: every script and handler F013 cites exists in the E008 inventory, and the scripts
E011 lists carry the inventory's ls_sha256.

  python3 experiments/E011-pro-reinforcement-reading/check_cited_scripts.py
      the record checks only (needs no original; this is what CI can run);
  IWA_STATIC=<folder> python3 experiments/E011-pro-reinforcement-reading/check_cited_scripts.py --disk [--run r1] [--out r1]
      also hashes each listed decompiled script IN PLACE in the static folder and compares it with the
      record's ls_sha256 (nothing is copied; the static folder must be outside every checkout), and writes
      measurements/disk-check-<out>.json (default <out> = <run>; an existing file is never overwritten):
      names, hashes and booleans only, never a path or a line of code.

A script is cited in F013 as `Kind N Name` and a handler as `handler()` (the form of tools/check_pro_question_map.py);
a handler must belong to the closest script cited before it on the same line. Exit 0 when every check holds.

Adapted from experiments/E010-pro-turn-victory-reading/check_cited_scripts.py (T30), which checked F012.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FINDING = ROOT / "findings" / "F013-pro-reinforcement-rules.md"
INVENTORY = ROOT / "experiments" / "E008-static-triage" / "measurements" / "iwp-extract-pro-r1.json"
LIST = HERE / "scripts-read.json"
SCRIPT_REF = re.compile(r"^(MovieScript|BehaviorScript|CastScript) (\d+)(?: (\S+))?$")
HANDLER_REF = re.compile(r"^(\S+)\(\)$")
MOVIE_DIR = ("movie-01-out", "movie-01.abs", "casts", "Internal")


def cited(text, scripts, errors):
    """Every (kind, number) cited in the finding, checking names and handlers as it goes."""
    found = set()
    for lineno, line in enumerate(text.splitlines(), 1):
        current = None
        for span in re.findall(r"`([^`]*)`", line):
            s = SCRIPT_REF.match(span)
            h = HANDLER_REF.match(span)
            if s:
                kind, num, name = s.group(1), int(s.group(2)), s.group(3)
                current = scripts.get((kind, num))
                if current is None:
                    errors.append("line %d: no script %s %d" % (lineno, kind, num))
                    continue
                if (name or "") != current["name"]:
                    errors.append("line %d: %s %d is named %r, cited %r" % (lineno, kind, num, current["name"], name))
                found.add((kind, num))
            elif h:
                if current is None or h.group(1) not in current["handlers"]:
                    errors.append("line %d: handler %s is not in the script cited before it" % (lineno, h.group(1)))
    return found


def file_name(s):
    return "%s %d - %s.ls" % (s["kind"], s["number"], s["name"]) if s["name"] else "%s %d.ls" % (s["kind"], s["number"])


def main():
    errors = []
    inv = json.loads(INVENTORY.read_text())
    scripts = {(s["kind"], s["number"]): s for s in inv["movies"][0]["scripts"]}
    found = cited(FINDING.read_text(), scripts, errors)

    listed = json.loads(LIST.read_text())
    entries = listed["scripts"]
    keys = [(e["kind"], e["number"]) for e in entries]
    if len(set(keys)) != len(keys):
        errors.append("a script is listed twice")
    for e in entries:
        s = scripts.get((e["kind"], e["number"]))
        if s is None:
            errors.append("listed %s %d is not in the inventory" % (e["kind"], e["number"]))
            continue
        for field in ("name", "handlers", "ls_sha256"):
            if e.get(field) != s[field]:
                errors.append("listed %s %d: %s differs from the inventory" % (e["kind"], e["number"], field))
    for k in sorted(found - set(keys)):
        errors.append("F013 cites %s %d, which E011 does not list" % k)
    print("F013 cites %d scripts; E011 lists %d; every one is in the inventory with its ls_sha256: %s"
          % (len(found), len(entries), "yes" if not errors else "NO"))

    if "--disk" in sys.argv:
        sys.path.insert(0, str(ROOT / "tools" / "static"))
        import static_common as sc  # noqa: E402
        run = sys.argv[sys.argv.index("--run") + 1] if "--run" in sys.argv else "r1"
        root = sc.static_root()
        folder = root.joinpath("iwp-extract-pro-" + run, *MOVIE_DIR)
        rows, bad = [], 0
        for e in entries:
            s = scripts[(e["kind"], e["number"])]
            path = folder / file_name(s)
            try:
                digest, size = sc.sha256_path(path)
            except Exception as exc:  # a missing or unsafe file is a failure, reported without its path
                digest, size = None, None
                errors.append("%s: not readable in place (%s)" % (file_name(s), type(exc).__name__))
            ok = digest == s["ls_sha256"]
            bad += 0 if ok else 1
            rows.append({"script": "%s %d" % (s["kind"], s["number"]), "file": file_name(s), "bytes": size,
                         "sha256_on_disk": digest, "ls_sha256_in_record": s["ls_sha256"], "match": ok})
        print("on disk, in place: %d of %d match the record's ls_sha256" % (len(rows) - bad, len(rows)))
        if bad:
            errors.append("%d scripts differ from the record on disk" % bad)
        rec = {"what": "each script listed in scripts-read.json, hashed in place in the static folder of run pro-%s, "
                       "against the record's ls_sha256 (nothing copied; no path or code kept)" % run,
               "record": "experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json",
               "matched": len(rows) - bad, "listed": len(rows), "rows": rows}
        text = json.dumps(rec, indent=1) + "\n"
        if sc.leaks(text):
            errors.append("the disk record would hold a machine path; not written")
        else:
            # --out names the output (a re-check of the same run writes a new file); default: the run id
            tag = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else run
            out = HERE / "measurements" / ("disk-check-%s.json" % tag)
            if out.exists():
                print("not overwriting", out.name)
            else:
                out.write_text(text)
                print("wrote", out.name)

    for e in errors:
        print("FAIL", e)
    if errors:
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
