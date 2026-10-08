"""Exchange events from two readings of the board (T40). Pure functions, no pixels.

An event is a pair of consecutive frames of one computer's turn in which exactly two adjacent
countries change, and nothing else is ambiguous. What it records: the attacker's and the defender's
counters before and after, their country numbers, and the owners before. The attacker is the
country of the seat whose turn it is (the boxed row of the score panel, in both frames).

What is NOT an event (each counted, never guessed, in the summary):
  - a country of either frame is unread (it could be a third change);
  - no change, one change, or more than two changes (a placement, a redraw, several battles);
  - two changes in countries that do not border each other;
  - the seat is unread or differs between the two frames, or is the human's (blue);
  - the two countries have one owner, or neither belongs to the seat in turn, or both do;
  - an owner changes (a capture), or a counter rises (a placement or a move).

One limit is built into the sampling and stated in the finding, not hidden here: the watcher takes
a frame about every 1.4 s, while the computer's passes follow each other faster, so two changed
counters between two frames are the net of two or more exchanges, never one.
"""
import json
from pathlib import Path

ADJACENCY_FILE = (Path(__file__).resolve().parents[2] / "E015-pro-board-reading" / "measurements"
                  / "board-tabulation-r1e.json")

# The human is seat 1, blue (F019 Q-SET-02; the driver plays blue). On the first frames of a computer's
# turn the score panel's box can still sit on blue (91 of 598 frames of the third sitting's computer
# windows): the changes of such a pair belong to the computers, and which one is not known.
HUMAN_SEAT = "blue"

REASONS = ("exchange", "unread", "no-change", "one-change", "many-changes", "not-adjacent", "seat-unknown",
           "human-seat", "same-owner", "no-attacker", "ownership-change", "counter-rise")


def load_adjacency(path=ADJACENCY_FILE):
    """{country: set of bordering countries}, symmetric, from the committed static tabulation."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    table = {int(k): set(map(int, v)) for k, v in doc["adjacency"].items()}
    for a, bs in list(table.items()):
        for b in bs:
            table.setdefault(b, set()).add(a)
    return table


def complete(board):
    """True when every country of the board has an army and an owner."""
    return len(board) == 46 and all(r["army"] is not None and r["owner"] is not None for r in board.values())


def classify(before, after, seat_before, seat_after, adjacency):
    """(reason, values): the reason is one of REASONS; `values` is the event's field dict when the
    reason is 'exchange', else None."""
    if not complete(before) or not complete(after):
        return "unread", None
    changed = [c for c in sorted(before) if (before[c]["army"], before[c]["owner"]) != (after[c]["army"], after[c]["owner"])]
    if not changed:
        return "no-change", None
    if len(changed) == 1:
        return "one-change", None
    if len(changed) > 2:
        return "many-changes", None
    a, b = changed
    if b not in adjacency.get(a, ()):
        return "not-adjacent", None
    if seat_before is None or seat_before != seat_after:
        return "seat-unknown", None
    if seat_before == HUMAN_SEAT:
        return "human-seat", None
    if before[a]["owner"] == before[b]["owner"]:
        return "same-owner", None
    mine = [c for c in (a, b) if before[c]["owner"] == seat_before]
    if len(mine) != 1:
        return "no-attacker", None
    attacker = mine[0]
    defender = b if attacker == a else a
    if any(before[c]["owner"] != after[c]["owner"] for c in (a, b)):
        return "ownership-change", None
    if any(after[c]["army"] > before[c]["army"] for c in (a, b)):
        return "counter-rise", None
    return "exchange", {
        "counter:attacker-before": str(before[attacker]["army"]), "counter:attacker-after": str(after[attacker]["army"]),
        "counter:defender-before": str(before[defender]["army"]), "counter:defender-after": str(after[defender]["army"]),
        "country:attacker": str(attacker), "country:defender": str(defender),
        "owner:attacker": before[attacker]["owner"], "owner:defender": before[defender]["owner"],
    }
