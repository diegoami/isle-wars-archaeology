#!/usr/bin/env python3
"""Done-when 2 of T41: the screen classifier over every frame of the model-driven sittings.

    python3 experiments/E020-wine-first-run/check_screens.py FRAMES1 FRAMES2 FRAMES3

Each argument is one sitting's `frames/` directory on the user's machine (rule 18, constraint A:
read in place, decoded with ImageMagick to raw RGB in memory, never copied). They are the first,
second and third sittings, in that order. It prints, for each sitting, how many frames each screen
name (runtime/iwp/driver/screens.py `name_of`) has, and for the Scoreboard's four tests the counts
on the Scoreboard's frames and the largest count on any other frame (the populations each minimum
sits between). It exits 0 only when:

* every frame of step 368 of the third sitting reads `scoreboard` (the task's contract), and the
  third sitting's Scoreboard frames are exactly those of steps 367 and 368, the screen the game
  showed after the credited loss (actions.jsonl of that sitting: New Game, the loss credited, then
  Play Game's click that the screen did not answer);
* no frame of the three sittings changes name from T38's classifier (`screens.name_from` with
  `scoreboard=False`) except the Scoreboard's frames, which T38's classifier called `unknown`; and
* the first two sittings' counts equal those walkthroughs/coordinates.md prints for T38 round 6, so no
  frame of them reads `scoreboard`.

No frame, no pixel and no decoded byte is written anywhere; the printout holds counts only.
"""
import collections
import os
import re
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "iwp"))
from driver import screens  # noqa: E402

STEP = re.compile(r"^(\d+)-\d+\.png$")
SCOREBOARD_STEPS = (367, 368)           # the third sitting's Scoreboard: the steps whose frames show it
CONTRACT_STEP = 368
# walkthroughs/coordinates.md, "The winner notice (T38 round 6)": names over the first two sittings.
T38_COUNTS = (
    {"board": 332, "board-menu": 201, "eliminated": 156, "unknown": 3, "title": 1},
    {"board": 315, "board-menu": 128, "game-over": 36, "eliminated": 3, "unknown": 3, "title": 1},
)


def decode(path):
    """One frame as raw 8-bit RGB bytes (ImageMagick `convert`, as the spike's Screen.raw does)."""
    return subprocess.run(["convert", str(path), "-depth", "8", "rgb:-"], capture_output=True, check=True).stdout


def read(path):
    """(file name, T38's name, T41's name, {scoreboard test: count}) for one frame."""
    frame = decode(path)
    screens.check_stage(frame)
    counts = {name: screens.count(frame, screens.TESTS[name].rect, screens.TESTS[name].predicate)
              for name in screens.SCOREBOARD_TESTS}
    signals = screens.signals(frame)
    return path.name, screens.name_from(signals, scoreboard=False), screens.name_from(signals), counts


def frames_of(directory):
    directory = Path(directory)
    if not directory.is_dir():
        sys.exit(f"{directory} is not a directory of frames")
    paths = sorted(p for p in directory.iterdir() if STEP.match(p.name))
    if not paths:
        sys.exit(f"{directory} holds no frame named <step>-<ms>.png")
    return paths


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 3:
        print(__doc__)
        return 2
    sittings = [frames_of(a) for a in argv]
    with Pool(max(1, min(8, os.cpu_count() or 1))) as pool:
        results = [pool.map(read, paths, chunksize=16) for paths in sittings]
    problems, scoreboard_counts, other_counts = [], collections.defaultdict(list), collections.defaultdict(list)
    for number, (directory, rows) in enumerate(zip(argv, results), start=1):
        names = collections.Counter(new for _, _, new, _ in rows)
        print(f"sitting {number} ({Path(directory).parent.name}): {len(rows)} frames")
        print("  " + ", ".join(f"{name} {names[name]}" for name in screens.NAMES if names[name]))
        for file, old, new, counts in rows:
            (scoreboard_counts if new == "scoreboard" else other_counts)[number].append(counts)
            if new != old and not (new == "scoreboard" and old == "unknown"):
                problems.append(f"sitting {number}: {file} read {old} before T41 and {new} now")
        if number <= 2:
            if dict(names) != T38_COUNTS[number - 1]:
                problems.append(f"sitting {number}: the names are {dict(names)}, T38 round 6 recorded "
                                f"{T38_COUNTS[number - 1]}")
    third = results[2]
    contract = [(file, new) for file, _, new, _ in third if STEP.match(file).group(1) == str(CONTRACT_STEP)]
    print(f"step {CONTRACT_STEP} of sitting 3: {len(contract)} frames, "
          f"{sum(1 for _, new in contract if new == 'scoreboard')} read scoreboard")
    if not contract:
        problems.append(f"sitting 3 has no frame of step {CONTRACT_STEP}")
    problems += [f"sitting 3: {file} (step {CONTRACT_STEP}) reads {new}, not scoreboard"
                 for file, new in contract if new != "scoreboard"]
    seen = sorted({int(STEP.match(file).group(1)) for file, _, new, _ in third if new == "scoreboard"})
    print(f"scoreboard frames of sitting 3 are of steps {seen}")
    if tuple(seen) != SCOREBOARD_STEPS:
        problems.append(f"sitting 3: the scoreboard is read on steps {seen}, not {list(SCOREBOARD_STEPS)}")
    for sitting in (1, 2):
        if scoreboard_counts[sitting]:
            problems.append(f"sitting {sitting}: {len(scoreboard_counts[sitting])} frames read scoreboard")
    for name in screens.SCOREBOARD_TESTS:
        on = [c[name] for cs in scoreboard_counts.values() for c in cs] or [0]
        off = [c[name] for cs in other_counts.values() for c in cs] or [0]
        minimum = screens.TESTS[name].minimum
        print(f"  {name}: minimum {minimum}; scoreboard frames {min(on)} to {max(on)}; "
              f"every other frame at most {max(off)}")
        if not max(off) < minimum <= min(on):
            problems.append(f"{name}: the minimum {minimum} does not sit between {max(off)} and {min(on)}")
    print("\n".join(problems) if problems else "ok: the Scoreboard is read, and no other frame changes name")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
