#!/usr/bin/env python3
"""Write ../pairs.json: the pairs of runs the findings' fields are decoded from (read by pair-diffs.py). Never replaces
a pairs file that exists with other bytes."""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "pairs.json"
P = []


def add(pid, field, action, a, b):
    P.append({"id": pid, "field": field, "action": action, "a": a, "b": b})


LEVELS = {"Normal": ("E007-r0002", "E007-r0021"), "Hard": ("E007-r0003", "E007-r0019"),
          "Hardest": ("E007-r0004", "E007-r0020")}
CTRL = ("E007-r0001", "E007-r0023")                      # Easy, 1 starting army, no other action
for i, (level, (r1, r2)) in enumerate(LEVELS.items()):
    add(f"L{i * 2 + 1}", "dft1", f"Set level Easy -> {level}, 1 starting army held", [CTRL[0], 0], [r1, 0])
    add(f"L{i * 2 + 2}", "dft1", f"Set level Easy -> {level}, 1 starting army held (second pair)", [CTRL[1], 0], [r2, 0])
add("A1", "dft2", "Starting armies 1 -> 3 at Easy", [CTRL[0], 0], ["E007-r0005", 0])
add("A2", "dft2", "Starting armies 1 -> 3 at Easy (second pair)", [CTRL[1], 0], ["E007-r0022", 0])
add("A3", "dft2", "Starting armies 1 -> 6 at Easy", [CTRL[0], 0], ["E007-r0006", 0])
add("A4", "dft2", "Starting armies 1 -> 10 at Easy", [CTRL[0], 0], ["E007-r0007", 0])
add("A5", "dft2", "Starting armies 1 -> 6 at Hard", ["E007-r0003", 0], ["E007-r0008", 0])
add("S1", "speed", "Speed Faster once (2 -> 1)", [CTRL[0], 0], ["E007-r0009", 0])
add("S2", "speed", "Speed Faster once (2 -> 1), second pair", [CTRL[1], 0], ["E007-r0017", 0])
add("S3", "speed", "Speed Slower once (2 -> 3)", [CTRL[0], 0], ["E007-r0010", 0])
add("S4", "speed", "Speed Slower once (2 -> 3), second pair", [CTRL[1], 0], ["E007-r0018", 0])
add("M1", "sound", "Sound button clicked once (on -> off)", [CTRL[0], 0], ["E007-r0011", 0])
add("M2", "sound", "Sound button clicked once (on -> off), second pair", [CTRL[1], 0], ["E007-r0016", 0])
for k, (run, n) in enumerate((("E007-r0012", 3), ("E007-r0014", 6))):
    for t in range(n):
        add(f"T{len([p for p in P if p['id'].startswith('T')]) + 1}", "cards",
            f"one turn passes with no attack ({run}, turn {t + 1} -> {t + 2})", [run, t], [run, t + 1])
for run in ("E007-r0025", "E007-r0026", "E007-r0027"):
    add(f"B{run[-1]}", "cards", f"turn 1: Blue attacks, conquers a country and passes ({run}, turn 1 -> 2)", [run, 0], [run, 1])

text = json.dumps(P, indent=1) + "\n"
if OUT.exists() and OUT.read_text() != text:
    sys.exit(f"{OUT.name} exists with other bytes; nothing replaced")
OUT.write_text(text)
print(len(P), "pairs")
