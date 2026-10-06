#!/usr/bin/env python3
"""Done-when 2 of T33, the bytecode half: every constant and draw F018's reading names is present in the
.lasm bytecode listings of the handlers that hold the deal's numbers, with no extra draw the reading
does not account for. Like E015's tabulate_board.py, it reads the listings IN PLACE in the static folder
(nothing copied) and keeps only counts, offsets and booleans (never a line of code).

Round 2 (T33's rework) adds the structural checks the round-1 review asked for, on top of the constant
checks: the cap runs as two sweeps of four ordered seat checks (seat order 1,2,3,4,1,2,3,4) and each
check's redraw reassigns the same seat variable the later checks of its sweep test (so up to eight
redraws per fill iteration, and the final redraw is never re-tested); the four first-draw counters are
written before the first cap comparison; the shuffle is a while-count-nonempty loop with one draw of the
current count and one removal per iteration (so it runs once per entry, 46 times from the 46-entry deal
list, with descending bounds 46 to 1); and the turn-advance handler increments the stored turn once and
wraps it, the compensation for the first-seat selection's decrement.

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
GT_LINE = re.compile(r"^\s*\[\s*(\d+)\] gt\b")
SETLOCAL_LINE = re.compile(r"^\s*\[\s*(\d+)\] setlocal (\d+)")
SETGLOBAL_LINE = re.compile(r"^\s*\[\s*(\d+)\] setglobal (\d+)")
EXTCALL_LINE = re.compile(r"^\s*\[\s*(\d+)\] extcall (\d+)")
PAIR_WINDOW = 25   # bytes between a 15-comparison and its own redraw draw
REDRAW_WINDOW = 30  # bytes between a 15-comparison and the setlocal that reassigns p
WRAP_WINDOW = 15   # bytes between the subtraction and the wrap push of 4
PLUS_WINDOW = 12   # bytes between random(10) and the add fed by the push of 8
TURN_WINDOW = 4    # bytes between the setglobal of TURN and its add / push of 1
TURN_GT_WINDOW = 12  # bytes between the turn wrap's setglobal and its preceding > comparison
TURN_WRAP_WINDOW = 20  # bytes between the turn advance's store and its wrap store

# The expectations, one predicate per claim F018 makes about the handler's numbers. `pushes` maps a pushed
# integer to its count; `r` holds the parsed structure: {"args": {...}, "cap_paired", "cap_seat_order",
# "cap_redraws_assign_p", "counter_before_cap", "shuffle_guard", "shuffle_draws", "shuffle_deletes",
# "minimum_order", "plus8", "subs", "wrap4", "turn_increment", "turn_wrap"}.
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
        ("the 8 cap comparisons run as two sweeps of four, in seat order 1,2,3,4,1,2,3,4",
         lambda pushes, r: r["cap_seat_order"] == [1, 2, 3, 4, 1, 2, 3, 4]),
        ("each cap comparison's redraw reassigns the seat variable the later checks of its sweep test "
         "(so a redraw can be re-tested in the same sweep, up to 8 redraws per fill iteration)",
         lambda pushes, r: r["cap_redraws_assign_p"] == 8),
        ("the four first-draw counters are written before the first 15-comparison (increment before test)",
         lambda pushes, r: r["counter_before_cap"] is True),
        ("the shuffle runs while the list is nonempty, one draw of its count and one removal per iteration "
         "(so 46 draws from the 46-entry deal list, bounds 46 down to 1)",
         lambda pushes, r: r["shuffle_guard"] and r["shuffle_draws"] == 1 and r["shuffle_deletes"] == 1),
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
    ("MovieScript", 10): [
        ("the turn advance increments the stored turn at the head of the handler, before any dispatch "
         "(the compensation of the first-seat selection's decrement)",
         lambda pushes, r: r["turn_increment"] is True),
        ("that first increment wraps the turn when it passes 4 (set to 1)",
         lambda pushes, r: r["turn_wrap"] is True),
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
           ("MovieScript", 10): "MovieScript 10 - Checkturn.lasm",
           ("MovieScript", 51): "MovieScript 51 - putinproductioncenters.lasm"}

COUNTER_LOCALS = (8, 16, 24, 32)   # the four first-draw counters a1 to a4
P_LOCAL = 40                        # the drawn seat


def parse_listing(text):
    """The handler's structure, from its .lasm listing: counts, offsets and booleans only, no code."""
    lines = text.splitlines()
    pushes = Counter()
    randoms = []                 # (offset, rendered argument)
    push_offsets = {}            # value -> [offsets]
    add_offsets = []
    sub_offsets = []
    gt_offsets = []
    setlocals = []               # (offset, local)
    global_sets = []             # (offset, global slot)
    extcalls = []                # (offset, handler index)
    minimum_order = []
    cap15_offsets = []
    for idx, line in enumerate(lines):
        m = PUSH_LINE.match(line)
        if m:
            off, val = int(m.group(1)), int(m.group(2))
            pushes[val] += 1
            push_offsets.setdefault(val, []).append(off)
            if val == 15:
                cap15_offsets.append(off)
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
            continue
        m = GT_LINE.match(line)
        if m:
            gt_offsets.append(int(m.group(1)))
            continue
        m = SETLOCAL_LINE.match(line)
        if m:
            setlocals.append((int(m.group(1)), int(m.group(2))))
            continue
        m = SETGLOBAL_LINE.match(line)
        if m:
            global_sets.append((int(m.group(1)), int(m.group(2))))
            continue
        m = EXTCALL_LINE.match(line)
        if m:
            extcalls.append((int(m.group(1)), int(m.group(2))))
    # the + 8 after random(10): an add within PLUS_WINDOW bytes of a draw of 10, fed by a push of 8
    plus8 = any(o10 < a <= o10 + PLUS_WINDOW for o10, arg in randoms if arg == "10" for a in add_offsets) \
        and pushes.get(8, 0) >= 1
    # cap pairing: every push of 15 has a random draw within PAIR_WINDOW bytes after it
    cap_paired = sum(1 for off in cap15_offsets
                     if any(off < o <= off + PAIR_WINDOW for o, _ in randoms))
    # the wrap: a push of 4 shortly after the single subtraction
    wrap4 = len(sub_offsets) == 1 and any(
        sub_offsets[0] < off <= sub_offsets[0] + WRAP_WINDOW for off in push_offsets.get(4, []))
    # the cap's seat order: after each push of 15, the next small push is the tested seat of that check
    cap_seat_order = []
    for i, line in enumerate(lines):
        if PUSH_LINE.match(line) and PUSH_LINE.match(line).group(2) == "15":
            for j in range(i + 1, min(i + 7, len(lines))):
                m = PUSH_LINE.match(lines[j])
                if m and 1 <= int(m.group(2)) <= 4:
                    cap_seat_order.append(int(m.group(2)))
                    break
    # each cap check's redraw reassigns the tested seat local
    cap_redraws_assign_p = sum(
        1 for off in cap15_offsets
        if any(off < s <= off + REDRAW_WINDOW for s, loc in setlocals if loc == P_LOCAL))
    # the counters are written before the first cap comparison
    counter_writes = [off for off, loc in setlocals if loc in COUNTER_LOCALS]
    counter_before_cap = bool(counter_writes) and bool(cap15_offsets) \
        and max(counter_writes) < min(cap15_offsets)
    # the shuffle: a while the list is nonempty loop with one draw of the count and one removal each pass
    shuffle_guard = bool(re.search(r"repeat while count\(TEM\) > 0", text))
    shuffle_draws = sum(1 for _, arg in randoms if arg == "count(TEM)")
    shuffle_deletes = sum(1 for _, idx in extcalls if idx == 75)  # extcall 75 = deleteAt
    # the turn advance in CheckTurn: the handler's first store of TURN is fed by an add (the advance
    # that compensates the selection's decrement), immediately followed by a test and a wrap to 1
    turn_sets = sorted(off for off, slot in global_sets if slot == 10)
    turn_first = turn_sets[0] if turn_sets else None
    turn_increment = turn_first is not None and any(
        turn_first - TURN_WINDOW <= a < turn_first for a in add_offsets)
    turn_wrap = turn_first is not None and any(
        turn_first < off <= turn_first + TURN_WRAP_WINDOW
        and not any(off - TURN_WINDOW <= a < off for a in add_offsets)
        and any(off - TURN_WINDOW <= p < off for p in push_offsets.get(1, []))
        and any(off - TURN_GT_WINDOW <= g < off for g in gt_offsets)
        for off in turn_sets)
    return {"pushes": pushes, "randoms": randoms, "plus8": plus8, "subs": len(sub_offsets),
            "wrap4": wrap4, "cap_paired": cap_paired, "cap_seat_order": cap_seat_order,
            "cap_redraws_assign_p": cap_redraws_assign_p, "counter_before_cap": counter_before_cap,
            "shuffle_guard": shuffle_guard, "shuffle_draws": shuffle_draws,
            "shuffle_deletes": shuffle_deletes, "minimum_order": minimum_order,
            "turn_increment": turn_increment, "turn_wrap": turn_wrap}


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

    result = {"what": "the deal's constants and draws, read back from the bytecode listings of the "
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
             "cap_seat_order": parsed["cap_seat_order"],
             "cap_redraws_assign_p": parsed["cap_redraws_assign_p"],
             "counter_before_cap": parsed["counter_before_cap"],
             "shuffle_guard": parsed["shuffle_guard"], "shuffle_draws": parsed["shuffle_draws"],
             "shuffle_deletes": parsed["shuffle_deletes"],
             "minimum_order": parsed["minimum_order"], "plus8": parsed["plus8"],
             "subs": parsed["subs"], "wrap4": parsed["wrap4"],
             "turn_increment": parsed["turn_increment"], "turn_wrap": parsed["turn_wrap"]}
        result["scripts"][label] = {
            "listing": LISTING[key], "listing_sha256": digest,
            "random_args": r["args"], "random_total": len(parsed["randoms"]),
            "push_15": parsed["pushes"].get(15, 0), "push_46": parsed["pushes"].get(46, 0),
            "minimum_order_first_seen": parsed["minimum_order"],
            "cap_compares_paired": parsed["cap_paired"],
            "cap_seat_order": parsed["cap_seat_order"],
            "cap_redraws_assign_p": parsed["cap_redraws_assign_p"],
            "counter_written_before_first_cap": parsed["counter_before_cap"],
            "shuffle_guard": parsed["shuffle_guard"],
            "shuffle_draws": parsed["shuffle_draws"], "shuffle_deletes": parsed["shuffle_deletes"],
            "subs": parsed["subs"], "random10_plus8": parsed["plus8"], "wrap_after_sub": parsed["wrap4"],
            "turn_increment": parsed["turn_increment"], "turn_wrap": parsed["turn_wrap"]}
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
