#!/usr/bin/env python3
"""The save's card-count line against the scoreboard's `C>` figures on the screen taken at the Save (F009).

    check-cards.py BATCH_DIR      BATCH_DIR must not exist: it is created, and each table is created in it

For every game-written save of E005 and E007 that has a screenshot of the human turn taken before the Save click (the
last `human-turn*` capture before the `files` step that kept it: the capture taken at the Save shows `GAME SAVED` over
the scoreboard), the four `C>` figures are cut out of the screenshot
(one cell per colour row: Blue, Red, Green, Brown, top to bottom) as bit patterns of the digit's pixels, and each
pattern is compared with the count the save gives that colour (the save's line `a , b , c , d` as Blue, Red, Green,
Brown).

There is no digit reader and no template of the game's font in this repository: a pattern is a bit string, and the table
asks one question of the whole set: is the map from pattern to the save's count a function (every cell with the same
pattern has the same count, whatever its colour row), and is it one to one (two counts never share a pattern)? A save
whose card line were in another colour order, or whose figures were other cards than the scoreboard's, would give cells
that disagree. The values 0, 1 and 2 are also read by eye in E005-r0037's `human-turn-2.png` (Blue 1, Red 0, Green 2, Brown 0;
the save taken there reads `1 , 0 , 2 , 0`), which anchors the patterns to the numbers they look like.

Cell geometry (designed from E005-r0037's `human-turn-2.png`, where the figures are at x 158..165): x 157..166,
rows y 21, 34, 47 and 60, nine pixels tall; a pixel is 1 when it is not black. Never overwrites (CLAUDE.md rule 20): a new
batch directory, each file created exclusively. Needs E005_BUNDLES and E007_BUNDLES in the environment.
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "save"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import savefmt  # noqa: E402
from importlib.machinery import SourceFileLoader  # noqa: E402

stars = SourceFileLoader("check_stars", str(Path(__file__).resolve().parent / "check-stars.py")).load_module()
CELL_X, CELL_W, CELL_H = 157, 10, 9
ROWS = (21, 34, 47, 60)
WIDTH = 640


def pattern(raw, row):
    bits = []
    for y in range(ROWS[row], ROWS[row] + CELL_H):
        for x in range(CELL_X, CELL_X + CELL_W):
            i = (y * WIDTH + x) * 3
            bits.append("0" if raw[i:i + 3] == b"\0\0\0" else "1")
    return "".join(bits)


def main(batch):
    batch = Path(batch)
    batch.mkdir(parents=True)
    cells = []           # (run, save, colour, pattern, count)
    for experiment in stars.EXPERIMENTS:
        bundles = Path(os.environ[f"{experiment}_BUNDLES"])
        for record in stars.records(experiment):
            manifest = json.loads((ROOT / "evidence" / experiment / f"{record['run_id']}.manifest.json").read_text())
            asset = {e["name"]: bundles / e["asset"] for e in manifest["files"]}
            shots = {o["step"]: o["field"].split(" ")[0] for o in record["observations"]
                     if o["field"].endswith("raw RGB8 pixels sha256") and "human-turn" in o["field"].split(" ")[0]}
            for name, path in sorted(asset.items()):
                if not (name.startswith("s") and name.endswith("-ISLEWAR.SAV")):
                    continue
                before = [s for s in shots if s < 100 + int(name[1:3])]
                if not before or shots[max(before)] not in asset:
                    continue
                shot = shots[max(before)]
                _, _, raw = stars.read_png(asset[shot])
                position = savefmt.decode(path.read_bytes())
                for row, colour in enumerate(savefmt.COUNT_ORDER):
                    cells.append((record["run_id"], f"{name} / {shot}", colour, pattern(raw, row),
                                  len(position["cards"][colour])))
    by_pattern, by_count = defaultdict(set), defaultdict(set)
    for _, _, _, pat, count in cells:
        by_pattern[pat].add(count)
        by_count[count].add(pat)
    names = {pat: f"p{i}" for i, pat in enumerate(sorted(by_pattern, key=lambda p: (min(by_pattern[p]), p)))}
    with open(batch / "card-cells.tsv", "xb") as fh:
        fh.write(("run\tsave / screenshot\tcolour row\tpattern\tcount in the save\n"
                  + "".join(f"{r}\t{s}\t{c}\t{names[p]}\t{n}\n" for r, s, c, p, n in cells)).encode())
    with open(batch / "card-patterns.tsv", "xb") as fh:
        fh.write(("pattern\tcounts in the saves for the cells with this pattern\tcells\tbits (9 rows of 10)\n"
                  + "".join(f"{names[p]}\t{','.join(map(str, sorted(by_pattern[p])))}\t"
                           f"{sum(1 for c in cells if c[3] == p)}\t{p}\n" for p in sorted(by_pattern, key=names.get))).encode())
    functional = all(len(v) == 1 for v in by_pattern.values())
    injective = all(len(v) == 1 for v in by_count.values())
    print(f"{len(cells)} cells of {len(cells) // 4} saves; {len(by_pattern)} patterns; "
          f"a pattern has one count: {functional}; a count has one pattern: {injective}")
    return 0 if functional and injective else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
