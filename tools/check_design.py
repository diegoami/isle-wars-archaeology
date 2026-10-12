#!/usr/bin/env python3
"""Check each design file's decision table against its in-scope spec claims (T50, T51).

Each design file in `DESIGNS` has its own in-scope `spec/` files. For each, the check reads the
claim tables of those spec files and the design file's decision table (every line that starts with
`| C-`). A design file fails if:
- an in-scope claim has no row, or more than one;
- a row names an id that is not in its own in-scope spec files;
- a decision is not one of keep, change, replace, drop, open;
- a change, replace or drop row has an empty "why";
- an open row's id does not appear in the owner's section: the `## Choices for the owner` section
  while choices are pending, or the `## The owner's decisions (<date>)` section once they are made.
  With no open row left, neither section is required.

With no argument it checks every design file and prints one line per clean file,
`design/<file> ok: N claims, N rows`, or one line per problem; it exits 1 if any file has a
problem. Naming design files (`variety.md` or `design/variety.md`) checks only those.
`--root` points at another tree (the tests use it).
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

SPEC_FILES = ("board", "setup", "seats", "starting-state", "turn-sequence", "reinforcement",
              "movement", "combat", "ownership", "victory", "surrender")
VARIETY_SPEC_FILES = ("cards", "island-bonuses", "production-centres", "hazards")
DESIGNS = {"core-rules.md": SPEC_FILES, "variety.md": VARIETY_SPEC_FILES}
DECISIONS = {"keep", "change", "replace", "drop", "open"}
NEED_WHY = {"change", "replace", "drop"}
CLAIM_ROW = re.compile(r"^\|\s*(C-[A-Z]+-\d+)\s*\|")
CHOICES = "the owner's section ('## Choices for the owner' or '## The owner's decisions')"
OWNER_HEADING = re.compile(r"^## (Choices for the owner|The owner's decisions\b.*)$", re.M)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def spec_claims(root, spec_files=SPEC_FILES):
    """The claim ids of the given spec files, in file order."""
    ids, problems = [], []
    for name in spec_files:
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


def check(root, design="core-rules.md"):
    """Return (problems, claim count, row count) for one design file, named as in DESIGNS."""
    claims, problems = spec_claims(root, DESIGNS[design])
    rel = f"design/{design}"
    path = root / "design" / design
    if not path.is_file():
        return problems + [f"{rel}: missing"], len(claims), 0
    text = path.read_text(encoding="utf-8")
    rows = []
    for n, line in enumerate(text.splitlines(), 1):
        m = CLAIM_ROW.match(line)
        if m:
            rows.append((n, m.group(1), cells(line)))
    known = set(claims)
    counts = Counter(cid for _, cid, _ in rows)
    for cid in claims:
        if counts[cid] == 0:
            problems.append(f"{cid}: no row in {rel}")
        elif counts[cid] > 1:
            problems.append(f"{cid}: {counts[cid]} rows in {rel}")
    section = choices_section(text)
    for n, cid, row in rows:
        where = f"{rel}:{n}"
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
    parser.add_argument("designs", nargs="*", help="design files to check (default: all of them)")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    names = [Path(d).name for d in args.designs] or list(DESIGNS)
    unknown = [n for n in names if n not in DESIGNS]
    if unknown:
        print(f"not a design file: {', '.join(unknown)} (known: {', '.join(DESIGNS)})")
        return 1
    failed = False
    for name in names:
        problems, n_claims, n_rows = check(args.root, name)
        if problems:
            failed = True
            print("\n".join(problems))
        else:
            print(f"design/{name} ok: {n_claims} claims, {n_rows} rows")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
