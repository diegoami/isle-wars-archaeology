#!/usr/bin/env python3
"""Check design/core-rules.md's decision table against the in-scope spec claims (T50).

It reads the claim tables of the eleven in-scope `spec/` files and the decision table of
`design/core-rules.md` (every line that starts with `| C-`). It fails if:
- an in-scope claim has no row, or more than one;
- a row names an id that is not in the spec;
- a decision is not one of keep, change, replace, drop, open;
- a change, replace or drop row has an empty "why";
- an open row's id does not appear in the owner's section: the `## Choices for the owner` section
  while choices are pending, or the `## The owner's decisions (<date>)` section once they are made.
  With no open row left, neither section is required.

Exit 0 and `design ok: N claims, N rows` when clean; exit 1 and one line per problem otherwise.
`--root` points at another tree (the tests use it).
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

SPEC_FILES = ("board", "setup", "seats", "starting-state", "turn-sequence", "reinforcement",
              "movement", "combat", "ownership", "victory", "surrender")
DECISIONS = {"keep", "change", "replace", "drop", "open"}
NEED_WHY = {"change", "replace", "drop"}
CLAIM_ROW = re.compile(r"^\|\s*(C-[A-Z]+-\d+)\s*\|")
CHOICES = "the owner's section ('## Choices for the owner' or '## The owner's decisions')"
OWNER_HEADING = re.compile(r"^## (Choices for the owner|The owner's decisions\b.*)$", re.M)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def spec_claims(root):
    """The claim ids of the in-scope spec files, in file order."""
    ids, problems = [], []
    for name in SPEC_FILES:
        path = root / "spec" / f"{name}.md"
        if not path.is_file():
            problems.append(f"spec/{name}.md: missing")
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            m = CLAIM_ROW.match(line)
            if m:
                ids.append(m.group(1))
    return ids, problems


def choices_section(text):
    """The text under the owner's heading, up to the next `## ` heading, or None."""
    m = OWNER_HEADING.search(text)
    if not m:
        return None
    rest = text[m.end():]
    end = re.search(r"^## ", rest, re.M)
    return rest[:end.start()] if end else rest


def check(root):
    """Return (problems, claim count, row count)."""
    claims, problems = spec_claims(root)
    design = root / "design" / "core-rules.md"
    if not design.is_file():
        return problems + ["design/core-rules.md: missing"], len(claims), 0
    text = design.read_text(encoding="utf-8")
    rows = []
    for n, line in enumerate(text.splitlines(), 1):
        m = CLAIM_ROW.match(line)
        if m:
            rows.append((n, m.group(1), cells(line)))
    known = set(claims)
    counts = Counter(cid for _, cid, _ in rows)
    for cid in claims:
        if counts[cid] == 0:
            problems.append(f"{cid}: no row in design/core-rules.md")
        elif counts[cid] > 1:
            problems.append(f"{cid}: {counts[cid]} rows in design/core-rules.md")
    section = choices_section(text)
    for n, cid, row in rows:
        where = f"design/core-rules.md:{n}"
        if cid not in known:
            problems.append(f"{where}: {cid} is not an in-scope spec claim")
        if len(row) != 4:
            problems.append(f"{where}: {cid} has {len(row)} cells, not 4")
            continue
        decision, why = row[1], row[3]
        if decision not in DECISIONS:
            problems.append(f"{where}: {cid} decision {decision!r} is not one of {sorted(DECISIONS)}")
        elif decision in NEED_WHY and not why:
            problems.append(f"{where}: {cid} is {decision} with an empty why")
        elif decision == "open" and (section is None or not re.search(rf"\b{re.escape(cid)}\b", section)):
            problems.append(f"{where}: {cid} is open but not in {CHOICES}")
    return problems, len(claims), len(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    problems, n_claims, n_rows = check(args.root)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"design ok: {n_claims} claims, {n_rows} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
