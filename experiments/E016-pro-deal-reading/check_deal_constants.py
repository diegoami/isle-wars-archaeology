#!/usr/bin/env python3
"""Done-when 2 of T33, the bytecode half: every constant and draw F018's reading names is present in the
.lasm bytecode listings of the three handlers that hold the deal's numbers, with no extra draw the reading
does not account for. Like E015's tabulate_board.py, it reads the listings IN PLACE in the static folder
(nothing copied) and keeps only counts, offsets and booleans (never a line of code).

  IWA_STATIC=<folder> python3 experiments/E016-pro-deal-reading/check_deal_constants.py [--run r1] [--out r1]

Writes measurements/deal-constants-<out>.json (default <out> = <run>; an existing file is never overwritten).
Exit 0 when every check holds.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MOVIE_DIR = ("movie-01-out", "movie-01.abs", "casts", "Internal")

OFFSET = re.compile(r"^\s*\[\s*(\d+)\]")
PUSH_LINE = re.compile(r"^\s*\[\s*(\d+)\] pushint8 (-?\d+)")
RANDOM_LINE = re.compile(r"^\s*\[\s*(\d+)\] extcall \d+ .*<random\((.*)\)>")
SUB_LINE = re.compile(r"^\s*\[\s*(\d+)\] sub\b")
ADD_LINE = re.compile(r"^\s*\[\s*(\d+)\] add\b")
PAIR_WINDOW = 25   # bytes between a 15-comparison and its own redraw draw
WRAP_WINDOW = 15   # bytes between the subtraction and the wrap push of 4
PLUS_WINDOW = 12   # bytes between random(10) and the add fed by the push of 8

# The expectations, one predicate per claim F018 makes about the handler's numbers. `pushes` maps a pushed
# integer to its count; `r` holds {"args": {rendered random argument: count}, "cap_paired", "minimum_order",
# "plus8", "subs", "wrap4"}.
EXPECT = {
    ("MovieScript", 5): [
        ("the seat draw, its 8 cap redraws, the all-human fill and the dead TURN draw: exactly 11 draws of 4",
         lambda pushes, r: r["args"].get("4", 0) == 11),
        ("the shuffle: exactly 1 draw of the remaining list's size",
         lambda pushes, r: r["args"].get("count(TEM)", 0) == 1),
        ("the starting armies: exactly 1 draw of the starting-armies option",
         lambda pushes, r: r["args"].get("STARTINGARMY", 0) == 1),
        ("no other draw anywhere in the handler: the reading names all 13",
         lambda pushes, r: sum(r["args"].values()) == 13),
        ("the soft cap: exactly 8 comparisons against 15 (two passes over four seats)",
         lambda pushes, r: pushes.get(15, 0) == 8),
        ("each 15-comparison is followed within %d bytes by its own redraw draw" % PAIR_WINDOW,
         lambda pushes, r: r["cap_paired"] == 8),
        ("the dealt minimums 5, 9, 14 and 16 are pushed exactly once each",
         lambda pushes, r: all(pushes.get(v, 0) == 1 for v in (5, 9, 14, 16))),
        ("the all-human minimum 11 is pushed exactly once",
         lambda pushes, r: pushes.get(11, 0) == 1),
        ("the minimum pushes appear in the order 5, 9, 14, 16, then 11 (levels 1 to 4, then the all-human branch)",
         lambda pushes, r: r["minimum_order"] == [5, 9, 14, 16, 11]),
        ("the board total 46 is pushed exactly 4 times (skip value, loop bound, all-human fill, army loop)",
         lambda pushes, r: pushes.get(46, 0) == 4),
    ],
    ("MovieScript", 399): [
        ("the length of the animated selection: exactly 1 draw of 10",
         lambda pushes, r: r["args"].get("10", 0) == 1),
        ("the seat draw with its two anti-repeat redraws: exactly 3 draws of 4",
         lambda pushes, r: r["args"].get("4", 0) == 3),
        ("no other draw in the handler: the reading names all 4",
         lambda pushes, r: sum(r["args"].values()) == 4),
        ("the length draw is 10 + 8 (9 to 18 iterations)",
         lambda pushes, r: r["plus8"] is True),
        ("exactly 1 subtraction (the final decrement of the drawn seat)",
         lambda pushes, r: r["subs"] == 1),
        ("the wrap to 4 is pushed within %d bytes after that subtraction" % WRAP_WINDOW,
         lambda pushes, r: r["wrap4"] is True),
    ],
    ("MovieScript", 51): [
        ("the shuffle of the whole board: exactly 1 draw of the remaining list's size",
         lambda pushes, r: r["args"].get("count(TEM)", 0) == 1),
        ("no other draw in the handler",
         lambda pushes, r: sum(r["args"].values()) == 1),
        ("the board total 46 and the three centre slots 12, 24 and 37 are pushed once each",
         lambda pushes, r: all(pushes.get(v, 0) == 1 for v in (46, 12, 24, 37))),
    ],
}

LISTING = {("MovieScript", 5): "MovieScript 5 - Putinboard.lasm",
           ("MovieScript", 399): "MovieScript 399 - WHOGOESFIRST.lasm",
           ("MovieScript", 51): "MovieScript 51 - putinproductioncenters.lasm"}


def parse_listing(text):
    """{pushes, randoms [(offset, argument)], plus8, subs, wrap4, cap_paired, minimum_order}."""
    pushes = Counter()
    randoms = []                 # (offset, rendered argument)
    push_offsets = {}            # value -> [offsets]
    add_offsets = []
    sub_offsets = []
    minimum_order = []
    for line in text.splitlines():
        m = PUSH_LINE.match(line)
        if m:
            off, val = int(m.group(1)), int(m.group(2))
            pushes[val] += 1
            push_offsets.setdefault(val, []).append(off)
            if val in (5, 9, 14, 16, 11) and val not in minimum_order:
                minimum_order.append(val)
            continue
        m = RANDOM_LINE.match(line)
        if m:
            randoms.append((int(m.group(1)), m.group(2).strip()))
            continue
        m = SUB_LINE.match(line)
        if m:
            sub_offsets.append(int(m.group(1)))
            continue
        m = ADD_LINE.match(line)
        if m:
            add_offsets.append(int(m.group(1)))
    # the + 8 after random(10): an add within PLUS_WINDOW bytes of a draw of 10, fed by a push of 8
    plus8 = any(o10 < a <= o10 + PLUS_WINDOW for o10, arg in randoms if arg == "10" for a in add_offsets) \
        and pushes.get(8, 0) >= 1
    # cap pairing: every push of 15 has a random draw within PAIR_WINDOW bytes after it
    cap_paired = sum(1 for off in push_offsets.get(15, [])
                     if any(off < o <= off + PAIR_WINDOW for o, _ in randoms))
    # the wrap: a push of 4 shortly after the single subtraction
    wrap4 = len(sub_offsets) == 1 and any(
        sub_offsets[0] < off <= sub_offsets[0] + WRAP_WINDOW for off in push_offsets.get(4, []))
    return {"pushes": pushes, "randoms": randoms, "plus8": plus8, "subs": len(sub_offsets),
            "wrap4": wrap4, "cap_paired": cap_paired, "minimum_order": minimum_order}


def args_of(parsed):
    counts = Counter(arg for _, arg in parsed["randoms"])
    return dict(counts)


def main():
    errors = []
    sys.path.insert(0, str(ROOT / "tools" / "static"))
    import static_common as sc  # noqa: E402
    run = sys.argv[sys.argv.index("--run") + 1] if "--run" in sys.argv else "r1"
    root = sc.static_root()
    folder = root.joinpath("iwp-extract-pro-" + run, *MOVIE_DIR)

    result = {"what": "the deal's constants and draws, read back from the bytecode listings of the three "
                      "handlers that hold them, against the numbers F018 states (nothing copied; counts, "
                      "offsets and booleans only, never a line of code)",
              "record": "experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json",
              "run": "pro-" + run, "scripts": {}, "checks": {}}
    for key, checks in EXPECT.items():
        label = "%s %d" % key
        path = folder / LISTING[key]
        try:
            parsed = parse_listing(path.read_text(errors="replace"))
            digest, _ = sc.sha256_path(path)
        except Exception as exc:
            errors.append("%s: listing not readable in place (%s)" % (label, type(exc).__name__))
            continue
        r = {"args": args_of(parsed), "cap_paired": parsed["cap_paired"],
             "minimum_order": parsed["minimum_order"], "plus8": parsed["plus8"],
             "subs": parsed["subs"], "wrap4": parsed["wrap4"]}
        result["scripts"][label] = {
            "listing": LISTING[key], "listing_sha256": digest,
            "random_args": r["args"], "random_total": len(parsed["randoms"]),
            "push_15": parsed["pushes"].get(15, 0), "push_46": parsed["pushes"].get(46, 0),
            "minimum_order_first_seen": parsed["minimum_order"],
            "cap_compares_paired": parsed["cap_paired"],
            "subs": parsed["subs"], "random10_plus8": parsed["plus8"], "wrap_after_sub": parsed["wrap4"]}
        for desc, predicate in checks:
            ok = False
            try:
                ok = bool(predicate(parsed["pushes"], r))
            except Exception as exc:
                errors.append("%s: check %r raised %s" % (label, desc, type(exc).__name__))
            result["checks"]["%s: %s" % (label, desc)] = ok
            if not ok:
                errors.append("%s: %s" % (label, desc))

    # the share arithmetic the finding states, checked here so it cannot drift from the constants
    shares = {}
    for level, a in ((1, 5), (2, 9), (3, 14), (4, 16)):
        shares["level %d" % level] = {"human_countries": a, "computer_countries": 46 - a}
        if a + (46 - a) != 46:
            errors.append("level %d: the shares do not sum to 46" % level)
    result["arithmetic"] = shares

    passed = sum(1 for v in result["checks"].values() if v)
    result["checks_passed"] = passed
    result["checks_total"] = len(result["checks"])
    result["all_checks_pass"] = not errors
    text = json.dumps(result, indent=1) + "\n"
    if sc.leaks(text):
        errors.append("the record would hold a machine path; not written")
    else:
        tag = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else run
        out = HERE / "measurements" / ("deal-constants-%s.json" % tag)
        if out.exists():
            print("not overwriting", out.name)
        else:
            out.write_text(text)
            print("wrote", out.name)

    print("deal constants: %d of %d checks hold" % (passed, len(result["checks"])))
    for e in errors:
        print("FAIL", e)
    if errors:
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
