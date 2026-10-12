#!/usr/bin/env python3
"""Check each design file's decision table against its in-scope spec claims (T50, T51, T53, T52).

Each design file in `DESIGNS` has its own in-scope `spec/` files. For each, the check reads the
claim tables of those spec files and the design file's decision table (every line that starts with
`| C-` or `| Q-`, after at most three spaces, as Markdown allows). A design file in `QUESTIONS` is also checked against the question ids of one
`questions/` file (`design/ui.md`: the `Q-UI-*` rows of `questions/malpaco.md`); its ids count as
claims. A design file fails if:
- an in-scope claim or question has no row, or more than one;
- a row names an id that is not in its own in-scope spec files or questions;
- a decision is not one of keep, change, replace, drop, open;
- a change, replace or drop row has an empty "why";
- an open row's id does not appear in the owner's section: the `## Choices for the owner` section
  while choices are pending, or the `## The owner's decisions (<date>)` section once they are made.
  With no open row left, neither section is required;
- a row does not have exactly four cells;
- a line whose first table cell looks like an id (C- or Q-, any case) is not a well-formed row: indented
  more than three spaces, without a leading pipe, or with an id that is not `C-`/`Q-`, capitals, `-`,
  digits (for example `Q-UI-23a`). Such a line is rejected, never skipped;
- a line opens a code fence (``` or ~~~, after any indentation), holds an HTML comment (`<!--`), or
  starts with an HTML tag (`<` then a letter, `/` or `!`, after any indentation): the check fails
  closed on inactive Markdown and raw HTML rather than parsing around them;
- a table-shaped line is disguised: inside a blockquote (`> | …`), under a list bullet
  (`- | …` or `* ` / `+ ` / numbered list `1. `), holding an HTML entity (`&#45;` etc.), or using a
  look-alike Unicode hyphen (`U+2010` HYPHEN, `U+2011` NON-BREAKING HYPHEN, etc.) where an ASCII `-`
  would make an id. Markdown would render any of those as a row that a strict reader would have
  skipped (or a different id than the author intended), so the check fails closed. Fix #202.

With no argument it checks every design file and prints one line per clean file,
`design/<file> ok: N claims, N rows`, or one line per problem; it exits 1 if any file has a
problem. It also applies the fence and comment ban to the design files without a decision table
(`BAN_ONLY`), printing only their problems. Naming design files (`variety.md` or `design/variety.md`) checks only those.
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
COMPUTER_SPEC_FILES = ("computer-opponent",)
UI_SPEC_FILES = ("user-interface",)
DESIGNS = {"core-rules.md": SPEC_FILES, "variety.md": VARIETY_SPEC_FILES, "computer.md": COMPUTER_SPEC_FILES,
           "ui.md": UI_SPEC_FILES}
# Design files that also answer questions: (the questions file, the id prefix of its in-scope rows).
QUESTIONS = {"ui.md": ("questions/malpaco.md", "Q-UI")}
# Design files with no decision table: only the fence and comment ban applies, and a clean one prints
# nothing (T51's variants catalogue).
BAN_ONLY = ("variants.md",)
DECISIONS = {"keep", "change", "replace", "drop", "open"}
NEED_WHY = {"change", "replace", "drop"}
# Markdown lets a table row start with up to 3 spaces; the check reads rows there too (T52 round 1).
CLAIM_ROW = re.compile(r"^ {0,3}\|\s*(C-[A-Z]+-\d+)\s*\|")
# A decision row names a spec claim or a question; a question row in a file without questions is unknown.
ID = re.compile(r"(?:C|Q)-[A-Z]+-\d+")
# A first cell that looks like an id (C- or Q-, any case, anywhere in the cell) makes a line a candidate
# row; a candidate that is not a well-formed row fails rather than being skipped.
LOOKS_LIKE_ID = re.compile(r"(?<![A-Za-z0-9])[CcQq]-[A-Za-z0-9]")
MAX_INDENT = 3
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


def question_ids(root, design):
    """The in-scope question ids of a design file, in file order, and any problem reading them."""
    if design not in QUESTIONS:
        return [], []
    rel, prefix = QUESTIONS[design]
    path = root / rel
    if not path.is_file():
        return [], [f"{rel}: missing"]
    row = re.compile(rf"^ {{0,3}}\|\s*({re.escape(prefix)}-\d+)\s*\|")
    return [m.group(1) for line in path.read_text(encoding="utf-8").splitlines() if (m := row.match(line))], []


FENCE = re.compile(r"^\s*(```|~~~)")
COMMENT = "<!--"
# A line whose first non-space character starts an HTML tag: an HTML block can hide or swallow rows.
HTML_TAG = re.compile(r"^\s*<[A-Za-z/!]")
# A line that is a table row inside a blockquote or list prefix. Markdown would render
# `> | C-BRD-09 | …` as a row whose first cell the checker sees as `>` — the `>` would slip past
# any reader and the row would not be counted. The disguise is deliberate, so the check fails
# closed (fix #202).
LIST_PREFIX = re.compile(r"^\s*(>|[*+\-]|\d+\.)\s+")
# An HTML entity inside a table line: `| Q&#45;UI&#45;99 | …` looks like `Q-UI-99` to a strict
# reader, but a permissive renderer decodes the entities. Fail closed.
HTML_ENTITY = re.compile(r"&#?\w+;")
# Look-alike Unicode hyphens/dashes that an ASCII `-` mirror shows up where an id needs a hyphen.
# U+2010 HYPHEN, U+2011 NON-BREAKING HYPHEN, U+2012 FIGURE DASH, U+2013 EN DASH, U+2014 EM DASH,
# U+2015 HORIZONTAL BAR. The look-alike id `Q‐UI‐99` is what fix #202 closes.
LOOKALIKE_HYPHEN = re.compile(r"[‐‑‒–—―]")
# An id may LOOK like a C-/Q- id even with look-alike hyphens; a permissive renderer would still
# skip it because the regex `ID` (ASCII only) won't match. The check fails closed on the line
# itself, before parsing it as a row. The character class is exactly the look-alike range
# `U+2010..U+2015` — ASCII `-` is excluded, so a normal id like `C-BRD-02` does not match.
LOOKS_LIKE_ID_ANY_DASH = re.compile(r"(?<![A-Za-z0-9])[CcQq][‐-―][A-Za-z0-9]")


def inactive_markdown(text, rel):
    """One problem per line that opens a code fence, holds an HTML comment, or starts with an HTML tag.
    A design file may hold none of them: either could hide decision rows from a reader while the check counts them, so the check
    fails closed instead of parsing around them. Code goes in indented blocks (four spaces)."""
    problems = []
    for n, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            problems.append(f"{rel}:{n}: a code fence; design files may not hold fenced blocks "
                            "(indent code by four spaces instead)")
        if COMMENT in line:
            problems.append(f"{rel}:{n}: an HTML comment; design files may not hold HTML comments")
        elif HTML_TAG.match(line):
            problems.append(f"{rel}:{n}: a raw HTML tag; design files may not hold raw HTML "
                            "(write &lt; or say it in words)")
    return problems


def disguised_lines(text, rel):
    """One problem per disguised table line (fix #202).

    A table line is "disguised" when a strict reader would not have rendered it as a row but a
    permissive reader would (a blockquote, a list bullet), or when the line disguises its id
    with HTML entities or look-alike Unicode hyphens. Each closes a documented bypass
    (`#202 R1`, `R4`); the check fails closed rather than parsing around them.

    The scan is line-wise: only lines that contain `|` (a table line) are examined; unrelated
    prose with `&` or non-ASCII hyphens is not affected.
    """
    problems = []
    for n, line in enumerate(text.splitlines(), 1):
        if "|" not in line:
            continue
        where = f"{rel}:{n}"
        if LIST_PREFIX.match(line):
            problems.append(
                f"{where}: a table line inside a blockquote or list prefix; "
                f"Markdown skips the prefix but the row is rendered — write the row plainly"
            )
            continue
        if HTML_ENTITY.search(line):
            problems.append(
                f"{where}: a table line holds an HTML entity (`&#nnn;` or `&name;`); "
                f"write the hyphen as '-' instead of &#45;"
            )
            continue
        # Look-alike hyphen next to a C-/Q- prefix: a deliberate disguise for an id such as
        # `Q‐UI‐99`. A permissive renderer skips the row (the ASCII `ID` regex
        # misses) but a human reader sees `Q-UI-99` and may believe it's a valid id. Fail
        # closed on the row's line before counting it.
        if LOOKALIKE_HYPHEN.search(line) and LOOKS_LIKE_ID_ANY_DASH.search(line):
            problems.append(
                f"{where}: a table line uses a look-alike Unicode hyphen "
                f"(U+2010..U+2015) next to a C-/Q- id; the row's id is not valid"
            )
    return problems


def decision_rows(text, rel):
    """The decision rows of a design file as (line number, id, cells), and one problem per candidate row
    that is not a well-formed one. A candidate is a line with a pipe whose first cell looks like an id
    (`LOOKS_LIKE_ID`). It is a row when it starts with a pipe after at most `MAX_INDENT` spaces (what
    Markdown allows) and its first cell is exactly an id (`ID`); otherwise it fails closed: Markdown may
    render it as a table row that a stricter reader would have skipped."""
    rows, problems = [], []
    for n, line in enumerate(text.splitlines(), 1):
        body = line.lstrip(" \t")
        if "|" not in body:
            continue
        lead = line[:len(line) - len(body)].expandtabs(4)
        piped = body.startswith("|")
        first = cells(body)[0] if piped else body.split("|", 1)[0].strip()
        if not LOOKS_LIKE_ID.search(first):
            continue
        where = f"{rel}:{n}"
        if len(lead) > MAX_INDENT:
            problems.append(f"{where}: a row naming {first!r} is indented {len(lead)} spaces; a decision row "
                            f"starts at most {MAX_INDENT} spaces in")
        elif not piped:
            problems.append(f"{where}: a row naming {first!r} has no leading pipe; a decision row starts with '|'")
        elif not ID.fullmatch(first):
            problems.append(f"{where}: {first!r} is not a well-formed claim or question id")
        else:
            rows.append((n, first, cells(body)))
    return rows, problems


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
    questions, q_problems = question_ids(root, design)
    claims, problems = claims + questions, problems + q_problems
    unknown = "is not an in-scope spec claim" + (" or question" if design in QUESTIONS else "")
    rel = f"design/{design}"
    path = root / "design" / design
    if not path.is_file():
        return problems + [f"{rel}: missing"], len(claims), 0
    text = path.read_text(encoding="utf-8")
    problems += inactive_markdown(text, rel)
    problems += disguised_lines(text, rel)
    rows, row_problems = decision_rows(text, rel)
    problems += row_problems
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
            problems.append(f"{where}: {cid} {unknown}")
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
    if not args.designs:
        for name in BAN_ONLY:
            path = args.root / "design" / name
            problems = inactive_markdown(path.read_text(encoding="utf-8"), f"design/{name}") if path.is_file() else []
            if problems:
                failed = True
                print("\n".join(problems))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
