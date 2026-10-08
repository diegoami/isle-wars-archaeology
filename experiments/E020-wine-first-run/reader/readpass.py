#!/usr/bin/env python3
"""The reading pass over one sitting (T40): frames to per-frame readings and exchange events.

    readpass.py --sitting /mnt/c/Temp/iwp-shots/wine/<id> [--measurements DIR] [--no-events-file]

Reads `frames-index.jsonl`, `actions.jsonl` and every frame under the sitting directory, in place
(a frame is never copied), and writes:

  <measurements>/frame-readings-<id>.jsonl   one line per indexed frame: its sha256, name, step,
                                             game, whether it lies in a computer's turn, the seat
                                             in turn, and per country the army number and the owner's
                                             colour word, or null with the reason (numbers and colour
                                             words only: constraint D)
  <measurements>/readings-summary-<id>.json  the counts: frames, countries read and unread by reason,
                                             pairs by classification
  <sitting>/readings.jsonl                   the events, one per line, in the form
                                             e020_export.py reads (game, seq, frames, values)

Nothing already written is overwritten: an existing output makes the pass stop.
"""
import argparse
import json
import multiprocessing
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boardreader  # noqa: E402
import exchange_events  # noqa: E402
import glyphs  # noqa: E402
import pngdecode  # noqa: E402

DEFAULT_TEMPLATES = Path("/mnt/c/Temp/iwp-shots/wine/reader-templates.json")
PASS_CLICK = [417, 530]          # the PASS button (walkthroughs/coordinates.md)


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def computer_windows(actions):
    """[(first step, last step)] of the computers' turns, from the click-driver's log: from the
    PASS click of the `commit` block to the step before the next `place` block starts, and from the
    KEEP PLAYING click of `eliminated-keep-playing` (the computers play the game out) to the end of
    the game, or of the log. Steps are the `seq` of actions.jsonl, which is also the prefix of each
    frame's name."""
    windows, start = [], None
    for row in actions:
        op, block = row.get("op"), row.get("block")
        if start is None:
            if block == "commit" and op == "click!" and row.get("args") == PASS_CLICK and row.get("status") == "ok":
                start = row["seq"]
            elif block == "eliminated-keep-playing" and op == "click!" and row.get("status") == "ok":
                start = row["seq"]
        else:
            if block == "place" and op == "watch" or row.get("event") in ("game-start", "game-end"):
                windows.append((start, row["seq"] - 1))
                start = None
    if start is not None:
        windows.append((start, 10 ** 9))
    return windows


def game_of_steps(actions):
    """A function step -> game ordinal: the game of the last logged line at or before the step."""
    seqs = sorted((row["seq"], row.get("game")) for row in actions if "seq" in row and "game" in row)

    def game_of(step):
        game = None
        for seq, g in seqs:
            if seq > step:
                break
            game = g
        return game
    return game_of


def step_of(name):
    return int(name.split("-", 1)[0])


def _read_job(job):
    path, template_path = job
    templates = _read_job.cache.get(template_path)
    if templates is None:
        templates = _read_job.cache[template_path] = glyphs.Templates.load(template_path)
    rgb = pngdecode.decode_file(path)
    return boardreader.read_board(rgb, templates), boardreader.current_seat(rgb)


_read_job.cache = {}


def read_frames(sitting, rows, template_path, processes):
    jobs = [(str(Path(sitting) / "frames" / row["name"]), str(template_path)) for row in rows]
    with multiprocessing.Pool(processes) as pool:
        return pool.map(_read_job, jobs, chunksize=8)


def frame_line(row, reading, seat, game, in_turn):
    board_ = reading
    return {"frame": row["sha256"], "name": row["name"], "step": step_of(row["name"]), "game": game,
            "computer_turn": in_turn, "seat": seat,
            "armies": [board_[c]["army"] for c in sorted(board_)],
            "owners": [board_[c]["owner"] for c in sorted(board_)],
            "marks": [board_[c]["mark"] for c in sorted(board_)],
            "unread": {str(c): board_[c]["why"] for c in sorted(board_) if board_[c]["army"] is None or board_[c]["owner"] is None}}


def run(sitting, measurements, templates=DEFAULT_TEMPLATES, write_events=True, processes=16):
    sitting = Path(sitting)
    sid = sitting.name
    outputs = {"frames": Path(measurements) / f"frame-readings-{sid}.jsonl",
               "summary": Path(measurements) / f"readings-summary-{sid}.json",
               "events": sitting / "readings.jsonl"}
    for key, path in outputs.items():
        if (key != "events" or write_events) and path.exists():
            raise SystemExit(f"{path} exists; a measured output is never overwritten")
    rows = jsonl(sitting / "frames-index.jsonl")
    actions = jsonl(sitting / "actions.jsonl")
    windows = computer_windows(actions)
    game_of = game_of_steps(actions)
    results = read_frames(sitting, rows, templates, processes)
    adjacency = exchange_events.load_adjacency()

    def window_of(step):
        for i, (lo, hi) in enumerate(windows):
            if lo <= step <= hi:
                return i
        return None

    lines, summary_unread, pairs, found, seq_by_game = [], Counter(), Counter(), [], Counter()
    for row, (reading, seat) in zip(rows, results):
        step = step_of(row["name"])
        lines.append(frame_line(row, reading, seat, game_of(step), window_of(step) is not None))
        for c, r in reading.items():
            if r["army"] is None:
                summary_unread["army:" + r["why"]] += 1
            elif r["owner"] is None:
                summary_unread["owner:" + r["why"]] += 1
    for i in range(len(rows) - 1):
        s0, s1 = step_of(rows[i]["name"]), step_of(rows[i + 1]["name"])
        w0, w1 = window_of(s0), window_of(s1)
        if w0 is None or w0 != w1 or game_of(s0) != game_of(s1):
            pairs["outside-a-computer-turn"] += 1
            continue
        reason, values = exchange_events.classify(results[i][0], results[i + 1][0], results[i][1], results[i + 1][1], adjacency)
        pairs[reason] += 1
        if reason == "exchange":
            game = game_of(s0)
            seq_by_game[game] += 1
            found.append({"game": game, "seq": seq_by_game[game], "frames": [rows[i]["sha256"], rows[i + 1]["sha256"]],
                          "values": values})
    countries_read = sum(1 for line in lines for a, o in zip(line["armies"], line["owners"]) if a is not None and o is not None)
    summary = {
        "what": "the reading pass over one sitting's frames (numbers, colour words and counts only)",
        "sitting": sid, "frames": len(rows), "frames_in_computer_turns": sum(1 for line in lines if line["computer_turn"]),
        "country_readings": len(rows) * 46, "country_readings_read": countries_read,
        "country_readings_unread": len(rows) * 46 - countries_read, "unread_by_reason": dict(sorted(summary_unread.items())),
        "pairs": dict(sorted(pairs.items())), "events": len(found),
        "computer_windows": len(windows), "templates": str(Path(templates).name),
    }
    Path(measurements).mkdir(parents=True, exist_ok=True)
    with open(outputs["frames"], "x", encoding="utf-8") as handle:
        for line in lines:
            handle.write(json.dumps(line, separators=(",", ":")) + "\n")
    with open(outputs["summary"], "x", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, indent=1) + "\n")
    if write_events:
        with open(outputs["events"], "x", encoding="utf-8") as handle:
            for event in found:
                handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sitting", required=True)
    parser.add_argument("--measurements", default=str(HERE.parent / "measurements"))
    parser.add_argument("--templates", default=str(DEFAULT_TEMPLATES))
    parser.add_argument("--no-events-file", action="store_true", help="do not write <sitting>/readings.jsonl")
    parser.add_argument("--processes", type=int, default=16)
    args = parser.parse_args(argv)
    summary = run(args.sitting, args.measurements, args.templates, not args.no_events_file, args.processes)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
