#!/usr/bin/env python3
"""Is a model-driven sitting stuck? One check of a sitting folder, for tools/harness/watch.sh --frames.

    python3 tools/harness/sitting_stall.py <sitting dir> [--still-min 5] [--idle-play-min 5] [--now-ms MS]

Reads only the sitting's own logs, never a frame's pixels: `frames-index.jsonl` (one line per
capture, with its sha256 and epoch_ms) and `actions.jsonl` (the driver's lines, with t_ms). Prints
one line per stall found, nothing when the sitting moves:

- `screen still`: the newest captures all have the same sha256 and the run of identical
  captures began --still-min minutes ago or more. The game or the driver is waiting on something.
- `no captures`: the newest capture is --still-min minutes old or more (the watcher stopped).
- `no play`: the driver kept acting but no fight, case, game start or game end was logged for
  --idle-play-min minutes. Sitting 20261011T091212Z passed seven turns in a row that way.

Each line names the frame, so the main session can look at it (CLAUDE.md rule 18, carve-out A).
--now-ms replaces the clock, so a recorded sitting can be checked at a past moment (tests, replays).
Exit 0 with no output when nothing is stuck, 1 with lines when something is, 2 on a bad folder.
"""
import argparse
import json
import pathlib
import sys
import time

# lines of actions.jsonl that show the game moving on, not just the driver clicking
PLAY_EVENTS = {"case-met", "game-start", "game-end", "game-abandoned"}


def lines(path):
    """The JSON lines of a file the driver is still writing; a half-written last line is skipped."""
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                try:
                    out.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return out


def played(row):
    """True for a line that shows the game moving on: a case met, a game started or ended, or an
    attack that fought (an exchange the board showed)."""
    if row.get("event") in PLAY_EVENTS:
        return True
    return row.get("event") == "attack-attempt" and bool(row.get("fought"))


def check(sitting, now_ms, still_min=5.0, idle_play_min=5.0):
    """The stall lines for `sitting` at `now_ms` (empty when it moves)."""
    found = []
    # only what was logged by now_ms, so a replay at a past moment sees what a live check saw
    frames = [r for r in lines(sitting / "frames-index.jsonl")
              if "sha256" in r and "epoch_ms" in r and r["epoch_ms"] <= now_ms]
    if frames:
        newest = frames[-1]
        if now_ms - newest["epoch_ms"] >= still_min * 60000:
            minutes = (now_ms - newest["epoch_ms"]) / 60000
            found.append(f"no captures for {minutes:.1f} min; newest frame {newest['name']}")
        else:
            start = newest["epoch_ms"]
            for row in reversed(frames):
                if row["sha256"] != newest["sha256"]:
                    break
                start = row["epoch_ms"]
            if now_ms - start >= still_min * 60000:
                minutes = (now_ms - start) / 60000
                found.append(f"screen still for {minutes:.1f} min; frame {newest['name']} "
                             f"(sha256 {newest['sha256'][:12]}…)")
    actions = [r for r in lines(sitting / "actions.jsonl") if "t_ms" in r and r["t_ms"] <= now_ms]
    if actions:
        last_play = max((r["t_ms"] for r in actions if played(r)), default=actions[0]["t_ms"])
        if now_ms - last_play >= idle_play_min * 60000 and now_ms - actions[-1]["t_ms"] < still_min * 60000:
            minutes = (now_ms - last_play) / 60000
            where = f"game {actions[-1].get('game')}, turn {actions[-1].get('turn')}"
            frame = f"; newest frame {frames[-1]['name']}" if frames else ""
            found.append(f"no play for {minutes:.1f} min ({where}): the driver acts, the game does not move{frame}")
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("sitting", help="the sitting folder (holds frames-index.jsonl and actions.jsonl)")
    parser.add_argument("--still-min", type=float, default=5.0)
    parser.add_argument("--idle-play-min", type=float, default=5.0)
    parser.add_argument("--now-ms", type=int, default=None, help="check at this moment instead of now")
    a = parser.parse_args(argv)
    sitting = pathlib.Path(a.sitting)
    if not sitting.is_dir():
        print(f"sitting_stall: not a folder: {sitting}", file=sys.stderr)
        return 2
    now_ms = a.now_ms if a.now_ms is not None else int(time.time() * 1000)
    found = check(sitting, now_ms, a.still_min, a.idle_play_min)
    for line in found:
        print(line)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
