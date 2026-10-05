#!/usr/bin/env python3
"""The I0 corroboration of each crafted save (F009): what the game showed after Load saved game, and what it wrote
when asked to Save again.

    check-crafted.py BATCH_DIR      BATCH_DIR must not exist: it is created, and the table is created in it

For each E007 run whose arm is `load-<variant>` (a crafted save placed by the cycle's put-save step and loaded):
  - the game's second Save (`save-resave.png`, kept as the last `s<NN>-ISLEWAR.SAV` of the run) against the crafted
    save placed (its sha256 is in the record's observation `crafted save placed ...`): equal bytes, or the fields that
    differ;
  - the board after the load (`loaded-human-turn.png`) against the same capture of the control run `load-base`, whose
    crafted save is byte for byte a natural save: the countries whose pixels differ (each differing pixel is given to
    the country whose number box is nearest), and whether anything else differs (the scoreboard panel, x 0..180 and
    y 10..80; the prompt boxes below the board, y 296 and below);
  - the owners read from the pixels (board.py) against the crafted owners, the stars against the crafted list
    (check-stars.py), and the scoreboard's four `C>` figures against the crafted card counts, read through the map
    from pattern to count that the natural saves of E005 and E007 give (check-cards.py; no crafted run is in it).
Needs E005_BUNDLES and E007_BUNDLES. Never overwrites (CLAUDE.md rule 20).
"""
import json
import math
import os
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "save"))
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "spike"))
import board  # noqa: E402
import savefmt  # noqa: E402

stars = SourceFileLoader("check_stars", str(HERE / "check-stars.py")).load_module()
cards = SourceFileLoader("check_cards", str(HERE / "check-cards.py")).load_module()
SCOREBOARD = (0, 10, 180, 80)        # x0, y0, x1, y1
PROMPTS_Y = 296


NEAR = 40                            # pixels from a changed country's number box that count as its own


def diff_regions(a, b, changed):
    """The differing pixels of two captures, sorted: near a country the save changed (within NEAR pixels of its number
    box: the fill, the digit, the star), in the scoreboard panel, in the prompt boxes below the board, and elsewhere
    on the map (given as the bounding box of each 20x20 cell that holds some: the game's pointer arrow, drawn in
    only one of two captures, and its text, are of this kind). Returns (near, score, prompt, [elsewhere boxes])."""
    near, score, prompt, cells = 0, 0, 0, {}
    for y in range(board.HEIGHT):
        for x in range(board.WIDTH):
            i = (y * board.WIDTH + x) * 3
            if a[i:i + 3] == b[i:i + 3]:
                continue
            if SCOREBOARD[0] <= x < SCOREBOARD[2] and SCOREBOARD[1] <= y < SCOREBOARD[3]:
                score += 1
            elif y >= PROMPTS_Y:
                prompt += 1
            elif any(math.dist(board.BOXES[n], (x, y)) <= NEAR for n in changed):
                near += 1
            else:
                box = cells.setdefault((x // 20, y // 20), [x, y, x, y])
                box[0], box[1], box[2], box[3] = min(box[0], x), min(box[1], y), max(box[2], x), max(box[3], y)
    return near, score, prompt, [tuple(v) for _, v in sorted(cells.items())]


def main(batch):
    batch = Path(batch)
    batch.mkdir(parents=True)
    bundles = Path(os.environ["E007_BUNDLES"])
    learned = {}
    for _, _, _, pat, count in cards.natural_cells():
        learned[pat] = count
    runs = []
    for record in stars.records("E007"):
        if record["arm"].startswith("load-") and record["status"] == "completed":
            manifest = json.loads((ROOT / "evidence" / "E007" / f"{record['run_id']}.manifest.json").read_text())
            asset = {e["name"]: bundles / e["asset"] for e in manifest["files"]}
            placed = [o["value"].split()[1] for o in record["observations"] if o["field"].startswith("crafted save placed")]
            resaves = sorted(n for n in asset if n.startswith("s") and n.endswith("-ISLEWAR.SAV"))
            runs.append((record, asset, placed[0] if placed else None, resaves))
    base = {r["arm"]: (a) for r, a, _, _ in runs}.get("load-base")
    rows = []
    for record, asset, placed_sha, resaves in runs:
        arm = record["arm"]
        position = json.loads((ROOT / "experiments" / "E007-iw-dos-save-format" / "crafted" /
                               f"{arm[len('load-'):]}.position.json").read_text())
        crafted = savefmt.encode(position)
        written = savefmt.decode(asset[resaves[-1]].read_bytes()) if len(resaves) > 1 else None
        loaded = stars.read_png(asset["loaded-human-turn.png"])[2]
        owners = board.owners(loaded)
        read = [owners[n] for n in range(1, 47)]
        same_owners = sum(1 for a, b in zip(read, position["owners"]) if a == b)
        seen = stars.stars(loaded)
        figures = [learned.get(cards.pattern(loaded, row), "?") for row in range(4)]
        wanted = [len(position["cards"][c]) for c in savefmt.COUNT_ORDER]
        resave = ("no second save" if written is None else
                  "equal to the crafted save" if asset[resaves[-1]].read_bytes() == crafted else
                  "differs in: " + ", ".join(k for k in position if written[k] != position[k]))
        if base and arm != "load-base":
            control = json.loads((ROOT / "experiments" / "E007-iw-dos-save-format" / "crafted" / "base.position.json").read_text())
            changed = ({n for n in range(1, 47) if position["owners"][n - 1] != control["owners"][n - 1]
                        or position["armies"][n - 1] != control["armies"][n - 1]}
                       | set(position["centres"]) ^ set(control["centres"]))
            near, score, prompt, elsewhere = diff_regions(stars.read_png(base["loaded-human-turn.png"])[2], loaded, changed)
            differ = (f"save changes countries {sorted(changed)}; px near them {near}; scoreboard px {score}; "
                      f"prompt px {prompt}; elsewhere on the map (boxes x0,y0,x1,y1) {elsewhere}")
        else:
            differ = "the control" if arm == "load-base" else "no control run"
        rows.append((record["run_id"], arm, placed_sha[:16] if placed_sha else "-", resave, f"{same_owners} of 46",
                     ",".join(map(str, seen)), ",".join(map(str, sorted(position["centres"]))),
                     ",".join(map(str, figures)) + (" = the crafted counts" if figures == wanted else f" (crafted {wanted})"), differ))
    with open(batch / "crafted.tsv", "xb") as fh:
        fh.write(("run\tarm\tcrafted save sha256 (16)\tthe game's second Save against it\towners read from the screen equal "
                  "the crafted\tstars on the screen\tcrafted centres\tC> figures on the screen (Blue Red Green Brown)\tpixels that differ from the control's loaded board\n"
                  + "".join("\t".join(r) + "\n" for r in rows)).encode())
    print(f"{len(rows)} crafted runs")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
