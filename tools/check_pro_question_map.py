#!/usr/bin/env python3
"""Check questions/pro-static.md against questions/malpaco.md and the E008 script inventory.

Done-when 1 and 2 of T17:
  1. one row for every question of malpaco.md whose scope includes Pro, in the same order, with the
     four fields; the DOS-only ids are listed as dropped;
  2. every cited script number and handler name exists in iwp-extract-pro-r1.json.

A script is cited as `Kind N Name` (Name omitted when the script has none) and a handler as
`handler()`; a handler must belong to the closest script cited before it in the same cell.
Prints the counts for the summary with --counts. Exit 0 when every check holds.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "questions" / "malpaco.md"
MAP = ROOT / "questions" / "pro-static.md"
INVENTORY = ROOT / "experiments" / "E008-static-triage" / "measurements" / "iwp-extract-pro-r1.json"

SCRIPT_REF = re.compile(r"^(MovieScript|BehaviorScript|CastScript) (\d+)(?: (\S+))?$")
HANDLER_REF = re.compile(r"^(\S+)\(\)$")
TASKS = {"T18", "T20", "T21", "T22", "T23", "T24", "T27"}
CORR = ("play", "static-only", "screen")
CONF = ("high", "medium", "low")


def malpaco_rows():
    """(id, scope-is-DOS-only) for every Q- row of malpaco.md, in file order."""
    out = []
    for line in QUESTIONS.read_text().splitlines():
        m = re.match(r"\| (Q-[A-Z]+-\d+) \|", line)
        if m:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            out.append((m.group(1), cells[4].startswith("DOS"), cells[-1]))
    return out


def map_rows(text):
    rows = []
    for line in text.splitlines():
        m = re.match(r"\| (Q-[A-Z]+-\d+) \|", line)
        if m:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
    return rows


def main():
    errors = []
    text = MAP.read_text()
    inv = json.loads(INVENTORY.read_text())
    scripts = {(s["kind"], s["number"]): s for s in inv["movies"][0]["scripts"]}

    expected = [(i, p) for i, dos, p in malpaco_rows() if not dos]
    dos_only = [i for i, dos, _ in malpaco_rows() if dos]
    rows = map_rows(text)

    got = [r[0] for r in rows]
    if got != [i for i, _ in expected]:
        want = [i for i, _ in expected]
        errors.append("ids differ: missing %s, extra %s, order ok=%s" % (
            [i for i in want if i not in got], [i for i in got if i not in want],
            [i for i in got if i in want] == [i for i in want if i in got]))

    m = re.search(r"^## Dropped.*?\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    dropped = re.findall(r"Q-[A-Z]+-\d+", m.group(1)) if m else []
    if dropped != dos_only:
        errors.append("dropped list %s != DOS-only ids %s" % (dropped, dos_only))

    tasks, corr, nosource = Counter(), Counter(), []
    prio = dict(expected)
    for cells in rows:
        qid = cells[0]
        if len(cells) != 5:
            errors.append("%s: %d cells, want 5" % (qid, len(cells)))
            continue
        _, sources, task, cor, conf = cells
        if not all((sources, task, cor, conf)):
            errors.append("%s: an empty field" % qid)
            continue
        t = re.match(r"(T\d\d|none)\b", task)
        if not t or (t.group(1) != "none" and t.group(1) not in TASKS):
            errors.append("%s: task %r" % (qid, task))
        elif t.group(1) == "none" and ":" not in task:
            errors.append("%s: task none without a reason" % qid)
        tasks[t.group(1) if t else "?"] += 1
        c = cor.split(":")[0]
        if c not in CORR or ":" not in cor:
            errors.append("%s: corroboration %r" % (qid, cor))
        corr[c] += 1
        if conf.split(":")[0] not in CONF or ":" not in conf:
            errors.append("%s: confidence %r" % (qid, conf))
        if sources.startswith("none found"):
            nosource.append(qid)
            if "searched" not in sources and ":" not in sources:
                errors.append("%s: none found without what was searched" % qid)
            continue
        current = None
        for span in re.findall(r"`([^`]*)`", sources):
            s = SCRIPT_REF.match(span)
            h = HANDLER_REF.match(span)
            if s:
                kind, num, name = s.group(1), int(s.group(2)), s.group(3)
                current = scripts.get((kind, num))
                if current is None:
                    errors.append("%s: no script %s %d" % (qid, kind, num))
                elif (name or "") != current["name"]:
                    errors.append("%s: %s %d is named %r, cited %r" % (qid, kind, num, current["name"], name))
            elif h:
                if current is None or h.group(1) not in current["handlers"]:
                    errors.append("%s: handler %s is not in the script cited before it" % (qid, h.group(1)))
            else:
                errors.append("%s: unrecognised code span %r" % (qid, span))
        if current is None:
            errors.append("%s: sources cite no script" % qid)

    if "--counts" in sys.argv:
        print("rows", len(rows), "dropped", dropped)
        print("tasks", dict(sorted(tasks.items())))
        print("corroboration", dict(sorted(corr.items())))
        print("no source (any priority)", nosource)
        print("no source, P1", [q for q in nosource if prio.get(q) == "P1"])
    for e in errors:
        print("FAIL", e)
    if errors:
        return 1
    print("ok: %d rows match malpaco.md, %d dropped, every cited script and handler exists" % (len(rows), len(dropped)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
