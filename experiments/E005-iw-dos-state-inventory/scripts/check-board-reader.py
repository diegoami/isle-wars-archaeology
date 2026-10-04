#!/usr/bin/env python3
"""Board reader against the scoreboard: the totals runtime/iw-dos/spike/board.py reads from the pixels beside
each number box, against the four figures of the game's own scoreboard panel ("BLUE : 17" ...) read by eye
from the same screenshot. Writes measurements/board-owner-check.tsv (a re-run writes <name>.new).

    check-board-reader.py OUTDIR       needs E005_BUNDLES and E005_EXPLORE (machine-local, never written out)
The eye readings were taken when each screenshot was first looked at (exploration runs x02 to x06, E005-r0011,
E005-r0012); the screenshots themselves stay local and are named by file sha256.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments" / "E005-iw-dos-state-inventory" / "scripts"))
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "spike"))
import board  # noqa: E402
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("analyze", ROOT / "experiments" / "E005-iw-dos-state-inventory" / "scripts" / "analyze.py")
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)

EXPLORE = Path(os.environ["E005_EXPLORE"])
# (where, name, eye reading: blue, red, green, brown)
CASES = [
    ("explore", "x02.a.png", (17, 8, 12, 9)),
    ("explore", "x03.a.png", (17, 12, 7, 10)),
    ("explore", "x04.f17.png", (16, 7, 14, 9)),
    ("explore", "x05.human-turn.png", (17, 9, 12, 8)),
    ("explore", "x06.human-turn.png", (17, 10, 6, 13)),
    ("E005-r0011", "human-turn-2.png", (18, 9, 9, 10)),
    ("E005-r0011", "attack-result.png", (17, 10, 9, 10)),
    ("E005-r0012", "human-turn-2.png", (16, 12, 7, 11)),
]


NOTES = {"attack-result.png": "the conquered country is already Blue on the map while the scoreboard panel still reads 17: "
                              "the panel is redrawn at the end of the move in (after-move-in.png reads 18)"}


def main(outdir):
    rows = ["source\tscreenshot_file_sha256\teye_blue_red_green_brown\treader_blue_red_green_brown\tequal\tnote"]
    for where, name, eye in CASES:
        path = EXPLORE / name if where == "explore" else analyze.asset(where, name)
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        raw = analyze.read_png(path)[2]
        t = board.totals(raw)
        got = (t["blue"], t["red"], t["green"], t["brown"])
        label = f"exploration {name}" if where == "explore" else f"{where} {name}"
        rows.append(f"{label}\t{digest}\t{','.join(map(str, eye))}\t{','.join(map(str, got))}\t{got == eye}\t{NOTES.get(name, '') if where != 'explore' else ''}")
    out = Path(outdir) / "board-owner-check.tsv"
    if out.exists():
        out = Path(outdir) / "board-owner-check.tsv.new"
    out.write_text("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main(sys.argv[1])
