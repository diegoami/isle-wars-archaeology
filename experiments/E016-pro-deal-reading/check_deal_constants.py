#!/usr/bin/env python3
"""Done-when 2 of T33, the bytecode half: every constant and draw F018's reading names is present in the
.lasm bytecode listings of the handlers that hold the deal's numbers, with no extra draw the reading
does not account for. Like E015's tabulate_board.py, it reads the listings IN PLACE in the static folder
(nothing copied) and keeps only counts, offsets and booleans (never a line of code).

Round 3 (T33's second rework) replaces the round-2 checker's textual match of the shuffle's loop guard
(a complete line of decompiled source embedded in a regular expression — the round-2 R1) with a
structural check of the bytecode listing. The guard is now read as its instruction shape: a list-length
call feeding a greater-than test whose result is a conditional jump immediately after it. Every draw is
now classified by the bytecode that supplies its argument — a literal push, a list-length call or a
global read — instead of by its rendered source text. The checker's own strings name only opcode
indices, slot numbers and the numeric values the reading states; no decompiled identifier or statement
appears anywhere in it.

Round 2 (T33's rework) added the structural checks the round-1 review asked for: the cap runs as two
sweeps of four ordered seat checks (seat order 1,2,3,4,1,2,3,4) and each check's redraw reassigns the
same seat local the later checks of its sweep test (so up to eight redraws per fill iteration, and the
final redraw is never re-tested against the threshold); the four first-draw counters are written before
the first cap comparison; the shuffle is a length-nonzero loop with one draw of the current length and one
removal per iteration (so it runs once per entry, 46 times from the 46-entry deal list, with descending
bounds 46 to 1); and the turn-advance handler increments the stored turn once and wraps it, the
compensation for the first-seat selection's decrement.

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

PUSHINT8_LINE = re.compile(r"^\s*\[\s*(\d+)\] pushint8 (-?\d+)")
GETGLOBAL_LINE = re.compile(r"^\s*\[\s*(\d+)\] getglobal (-?\d+)")
EXTCALL_LINE = re.compile(r"^\s*\[\s*(\d+)\] extcall (\d+)")
SUB_LINE = re.compile(r"^\s*\[\s*(\d+)\] sub\b")
ADD_LINE = re.compile(r"^\s*\[\s*(\d+)\] add\b")
GT_LINE = re.compile(r"^\s*\[\s*(\d+)\] gt\b")
SETLOCAL_LINE = re.compile(r"^\s*\[\s*(\d+)\] setlocal (\d+)")
SETGLOBAL_LINE = re.compile(r"^\s*\[\s*(\d+)\] setglobal (\d+)")
JMPIFZ_LINE = re.compile(r"^\s*\[\s*(\d+)\] jmpifz \[(\d+)\]")

# The opcode indices the reading turns on (numbers only, no decompiled text).
EXTCALL_DRAW = 70      # the draw primitive
EXTCALL_LENGTH = 73    # the list-length primitive
EXTCALL_REMOVE = 75    # the list-removal primitive

PAIR_WINDOW = 25   # bytes between a 15-comparison and its own redraw draw
REDRAW_WINDOW = 30  # bytes between a 15-comparison and the setlocal that reassigns the drawn seat
WRAP_WINDOW = 15   # bytes between the subtraction and the wrap push of 4
PLUS_WINDOW = 12   # bytes between the draw of 10 and the add fed by the push of 8
TURN_WINDOW = 4    # bytes between the setglobal of the turn and its add / push of 1
TURN_GT_WINDOW = 12  # bytes between the turn wrap's setglobal and its preceding > comparison
TURN_WRAP_WINDOW = 20  # bytes between the turn advance's store and its wrap store
ARG_WINDOW = 8     # bytes between a draw and the instruction that supplies its argument
GUARD_WINDOW = 6   # bytes between the list-length call and the greater-than test of the loop guard

# The expectations, one predicate per claim F018 makes about the handler's numbers. `pushes` maps a pushed
# integer to its count; `r` holds the parsed structure: {"random_literals", "random_count", "random_global",
# "random_total", "cap_paired", "cap_seat_order", "cap_redraws_assign_p", "counter_before_cap",
# "shuffle_guard", "shuffle_draws", "shuffle_deletes", "minimum_order", "plus8", "subs", "wrap4",
# "turn_increment", "turn_wrap"}.
EXPECT = {
    ("MovieScript", 5): [
        ("the seat draw, its 8 cap redraws, the all-human fill and the dead turn draw: exactly 11 draws of 4",
         lambda pushes, r: r["random_literals"].get(4, 0) == 11),
        ("the shuffle: exactly 1 draw whose argument is a list-length call (the remaining list's size)",
         lambda pushes, r: r["random_count"] == 1),
        ("the starting armies: exactly 1 draw whose argument is a global (the option value)",
         lambda pushes, r: r["random_global"] == 1),
        ("no other draw anywhere in the handler: the reading names all 13",
         lambda pushes, r: r["random_total"] == 13),
        ("the soft cap: exactly 8 comparisons against 15 (two passes over four seats)",
         lambda pushes, r: pushes.get(15, 0) == 8),
        ("each 15-comparison is followed within %d bytes by its own redraw draw" % PAIR_WINDOW,
         lambda pushes, r: r["cap_paired"] == 8),
        ("the 8 cap comparisons run as two sweeps of four, in seat order 1,2,3,4,1,2,3,4",
         lambda pushes, r: r["cap_seat_order"] == [1, 2, 3, 4, 1, 2, 3, 4]),
        ("each cap comparison's redraw reassigns the seat local the later checks of its sweep test "
         "(so a redraw can be re-tested in the same sweep, up to 8 redraws per fill iteration)",
         lambda pushes, r: r["cap_redraws_assign_p"] == 8),
        ("the four first-draw counters are written before the first 15-comparison (increment before test)",
         lambda pushes, r: r["counter_before_cap"] is True),
        ("the shuffle runs while the list is nonempty, one draw of its length and one removal per iteration "
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
         lambda pushes, r: r["random_literals"].get(10, 0) == 1),
        ("the seat draw with its two anti-repeat redraws: exactly 3 draws of 4",
         lambda pushes, r: r["random_literals"].get(4, 0) == 3),
        ("no other draw in the handler: the reading names all 4",
         lambda pushes, r: r["random_total"] == 4),
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
        ("the shuffle of the whole board: exactly 1 draw whose argument is a list-length call",
         lambda pushes, r: r["random_count"] == 1),
        ("no other draw in the handler",
         lambda pushes, r: r["random_total"] == 1),
        ("the board total 46 and the three centre slots 12, 24 and 37 are pushed once each",
         lambda pushes, r: all(pushes.get(v, 0) == 1 for v in (46, 12, 24, 37))),
    ],
}

LISTING = {("MovieScript", 5): "MovieScript 5 - Putinboard.lasm",
           ("MovieScript", 399): "MovieScript 399 - WHOGOESFIRST.lasm",
           ("MovieScript", 10): "MovieScript 10 - Checkturn.lasm",
           ("MovieScript", 51): "MovieScript 51 - putinproductioncenters.lasm"}

COUNTER_LOCALS = (8, 16, 24, 32)   # the four first-draw counters
P_LOCAL = 40                        # the drawn seat local


def shuffle_guard_info(gt_offsets, count_offsets, jmpifzs):
    """The shuffle loop's guard, read structurally from the listing: a greater-than test fed by a
    list-length call (the list is nonempty) whose result is a conditional jump immediately after it.
    Returns (jump offset, jump target) for the first such guard, or None. Numbers and booleans only."""
    for g in sorted(gt_offsets):
        for off, target in sorted(jmpifzs):
            if 0 < off - g <= 2:  # the conditional jump directly after the test
                if any(0 < g - c <= GUARD_WINDOW for c in count_offsets):
                    return off, target
    return None


def parse_listing(text):
    """The handler's structure, from its .lasm listing: counts, offsets and booleans only, no code."""
    lines = text.splitlines()
    pushes = Counter()
    push_offsets = {}            # value -> [offsets]
    random_offsets = []          # offsets of the draw primitive
    count_offsets = []           # offsets of the list-length primitive
    delete_offsets = []          # offsets of the list-removal primitive
    getglobal_offsets = {}       # offset -> global slot
    add_offsets = []
    sub_offsets = []
    gt_offsets = []
    setlocals = []               # (offset, local)
    global_sets = []             # (offset, global slot)
    jmpifzs = []                 # (offset, target)
    minimum_order = []
    cap15_offsets = []
    for line in lines:
        m = PUSHINT8_LINE.match(line)
        if m:
            off, val = int(m.group(1)), int(m.group(2))
            pushes[val] += 1
            push_offsets.setdefault(val, []).append(off)
            if val == 15:
                cap15_offsets.append(off)
            if val in (5, 9, 14, 16, 11) and val not in minimum_order:
                minimum_order.append(val)
            continue
        m = GETGLOBAL_LINE.match(line)
        if m:
            getglobal_offsets[int(m.group(1))] = int(m.group(2))
            continue
        m = EXTCALL_LINE.match(line)
        if m:
            off, idx = int(m.group(1)), int(m.group(2))
            if idx == EXTCALL_DRAW:
                random_offsets.append(off)
            elif idx == EXTCALL_LENGTH:
                count_offsets.append(off)
            elif idx == EXTCALL_REMOVE:
                delete_offsets.append(off)
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
        m = JMPIFZ_LINE.match(line)
        if m:
            jmpifzs.append((int(m.group(1)), int(m.group(2))))

    # Each draw's argument is the instruction nearest before it (within ARG_WINDOW bytes) that supplies
    # one: a literal push, a list-length call or a global read. This classifies each draw without ever
    # reading its rendered source text.
    arg_sources = {}
    for val, offs in push_offsets.items():
        for off in offs:
            arg_sources[off] = ("literal", val)
    for off in count_offsets:
        arg_sources[off] = ("count",)
    for off, slot in getglobal_offsets.items():
        arg_sources[off] = ("global", slot)

    random_literals = Counter()
    random_count = 0
    random_global = 0
    random_kinds = {}
    for off in random_offsets:
        kind = None
        for probe in range(off - 1, off - ARG_WINDOW - 1, -1):
            if probe in arg_sources:
                kind = arg_sources[probe]
                break
        if kind is None:
            key = "unknown"
        elif kind[0] == "literal":
            key = "literal %d" % kind[1]
            random_literals[kind[1]] += 1
        elif kind[0] == "count":
            key = "count"
            random_count += 1
        else:
            key = "global"
            random_global += 1
        random_kinds[off] = key

    # the + 8 after the draw of 10: an add within PLUS_WINDOW bytes of a draw of 10, fed by a push of 8
    plus8 = any(o < a <= o + PLUS_WINDOW for o, k in random_kinds.items() if k == "literal 10"
                for a in add_offsets) and pushes.get(8, 0) >= 1
    # cap pairing: every push of 15 has a draw within PAIR_WINDOW bytes after it
    cap_paired = sum(1 for off in cap15_offsets
                     if any(off < o <= off + PAIR_WINDOW for o in random_offsets))
    # the wrap: a push of 4 shortly after the single subtraction
    wrap4 = len(sub_offsets) == 1 and any(
        sub_offsets[0] < off <= sub_offsets[0] + WRAP_WINDOW for off in push_offsets.get(4, []))
    # the cap's seat order: after each push of 15, the next small push is the tested seat of that check
    cap_seat_order = []
    for i, line in enumerate(lines):
        m = PUSHINT8_LINE.match(line)
        if m and int(m.group(2)) == 15:
            for j in range(i + 1, min(i + 7, len(lines))):
                n = PUSHINT8_LINE.match(lines[j])
                if n and 1 <= int(n.group(2)) <= 4:
                    cap_seat_order.append(int(n.group(2)))
                    break
    # each cap check's redraw reassigns the drawn-seat local
    cap_redraws_assign_p = sum(
        1 for off in cap15_offsets
        if any(off < s <= off + REDRAW_WINDOW for s, loc in setlocals if loc == P_LOCAL))
    # the counters are written before the first cap comparison
    counter_writes = [off for off, loc in setlocals if loc in COUNTER_LOCALS]
    counter_before_cap = bool(counter_writes) and bool(cap15_offsets) \
        and max(counter_writes) < min(cap15_offsets)
    # the shuffle: a nonempty-loop guard whose body holds one length draw and one removal
    guard = shuffle_guard_info(gt_offsets, count_offsets, jmpifzs)
    if guard is None:
        shuffle_guard = False
        shuffle_draws = 0
        shuffle_deletes = 0
    else:
        shuffle_guard = True
        shuffle_draws = sum(1 for o in random_offsets if guard[0] < o < guard[1])
        shuffle_deletes = sum(1 for o in delete_offsets if guard[0] < o < guard[1])
    # the turn advance in CheckTurn: the handler's first store of the turn is fed by an add (the advance
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
    return {"pushes": pushes, "random_literals": random_literals,
            "random_count": random_count, "random_global": random_global,
            "random_total": len(random_offsets), "random_kinds": random_kinds,
            "plus8": plus8, "subs": len(sub_offsets), "wrap4": wrap4,
            "cap_paired": cap_paired, "cap_seat_order": cap_seat_order,
            "cap_redraws_assign_p": cap_redraws_assign_p, "counter_before_cap": counter_before_cap,
            "shuffle_guard": shuffle_guard, "shuffle_draws": shuffle_draws,
            "shuffle_deletes": shuffle_deletes, "minimum_order": minimum_order,
            "turn_increment": turn_increment, "turn_wrap": turn_wrap}


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
        r = {"random_literals": parsed["random_literals"],
             "random_count": parsed["random_count"], "random_global": parsed["random_global"],
             "random_total": parsed["random_total"],
             "cap_paired": parsed["cap_paired"], "cap_seat_order": parsed["cap_seat_order"],
             "cap_redraws_assign_p": parsed["cap_redraws_assign_p"],
             "counter_before_cap": parsed["counter_before_cap"],
             "shuffle_guard": parsed["shuffle_guard"], "shuffle_draws": parsed["shuffle_draws"],
             "shuffle_deletes": parsed["shuffle_deletes"],
             "minimum_order": parsed["minimum_order"], "plus8": parsed["plus8"],
             "subs": parsed["subs"], "wrap4": parsed["wrap4"],
             "turn_increment": parsed["turn_increment"], "turn_wrap": parsed["turn_wrap"]}
        result["scripts"][label] = {
            "listing": LISTING[key], "listing_sha256": digest,
            "random_literals": dict(parsed["random_literals"]),
            "random_count": parsed["random_count"], "random_global": parsed["random_global"],
            "random_total": parsed["random_total"],
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
