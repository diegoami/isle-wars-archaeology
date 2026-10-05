#!/usr/bin/env python3
"""The production-centre list of a save against the stars on the screen (F009 row for the list).

    check-stars.py BATCH_DIR      BATCH_DIR must not exist: it is created, and each table is created in it

For every game-written save (E005 and E007) it takes the screenshot taken at the Save (the last `save-*` capture before
the `files` step that kept the save), finds the stars drawn on the board by matching the star glyph, and compares the
countries that have one with the save's list of centres. Needs E005_BUNDLES and E007_BUNDLES in the environment.

The glyph (the "(*) below the City number" of ISLEWAR.DOC:269-270): eight pixels wide and five tall, black on the
country's fill:

    .XX..XX.     (rows are 1 or 0 below; X = black (0, 0, 0))
    ..XXXX..
    XXXXXXXX
    ..XXXX..
    .XX..XX.

taken from the star of country 44 in E005-r0037's `human-turn-2.png` (the pixels at x 481..488, y 69..73) and
checked against country 4's star in the same capture. A star is looked for in a window around the country's number
box (x from -20 to +30, y from +12 to +42 of the box centre, board.py BOXES; a first window of -16..+24 by +12..+32,
designed from two stars, missed the star of country 19 (E007-r0022, 33 pixels below its box), so it was widened): the template's black pixels must all
be black and its four hollow pixels (row 0, columns 0, 3, 4, 7 are not part of the glyph and must not be black;
likewise row 4) must not be. The window and the glyph are designed from two stars, not measured on the game; the
table says how many saves it matched on, and the comparison is the evidence.
Never overwrites (CLAUDE.md rule 20): a new batch directory, each file created exclusively.
"""
import json
import os
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "save"))
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos" / "spike"))
import board  # noqa: E402
import savefmt  # noqa: E402

GLYPH = ("01100110",
         "00111100",
         "11111111",
         "00111100",
         "01100110")
WINDOW = (-20, 30, 12, 42)          # x from, x to, y from, y to, relative to the number box's centre
EXPERIMENTS = ("E005", "E007")


def read_png(path):
    """(width, height, rgb bytes) of a PNG written by cycle.py's png_bytes: 8-bit RGB, filter 0 on every row."""
    data = Path(path).read_bytes()
    pos, idat, width, height = 8, b"", 0, 0
    while pos < len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height = int.from_bytes(body[:4], "big"), int.from_bytes(body[4:8], "big")
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    rows = zlib.decompress(idat)
    stride = width * 3
    out = bytearray()
    for y in range(height):
        assert rows[y * (stride + 1)] == 0, "a filtered row: not one of cycle.py's PNGs"
        out += rows[y * (stride + 1) + 1:(y + 1) * (stride + 1)]
    return width, height, bytes(out)


def black(raw, x, y):
    i = (y * board.WIDTH + x) * 3
    return raw[i:i + 3] == b"\0\0\0"


def has_star(raw, n):
    cx, cy = board.BOXES[n]
    for y in range(cy + WINDOW[2], cy + WINDOW[3]):
        for x in range(cx + WINDOW[0], cx + WINDOW[1]):
            if x < 0 or y < 0 or x + 8 > board.WIDTH or y + 5 > board.HEIGHT:
                continue
            if all(black(raw, x + c, y + r) == (GLYPH[r][c] == "1") for r in range(5) for c in range(8)):
                return True
    return False


def stars(raw):
    return sorted(n for n in board.BOXES if has_star(raw, n))


def records(experiment):
    for path in sorted((ROOT / "runs" / experiment).glob(f"{experiment}-r*.json")):
        yield json.loads(path.read_text())


def main(batch):
    batch = Path(batch)
    batch.mkdir(parents=True)
    rows, bad = [], 0
    for experiment in EXPERIMENTS:
        bundles = Path(os.environ[f"{experiment}_BUNDLES"])
        for record in records(experiment):
            manifest = json.loads((ROOT / "evidence" / experiment / f"{record['run_id']}.manifest.json").read_text())
            asset = {e["name"]: bundles / e["asset"] for e in manifest["files"]}
            shots = {}
            for o in record["observations"]:
                if o["field"].endswith("raw RGB8 pixels sha256") and o["field"].startswith(("save-", "loaded-human-turn")):
                    shots[o["step"]] = o["field"].split(" ")[0]
            for name, path in sorted(asset.items()):
                if not (name.startswith("s") and name.endswith("-ISLEWAR.SAV")):
                    continue
                step = 100 + int(name[1:3])
                before = [s for s in shots if s < step]
                if not before:
                    continue
                shot = shots[max(before)]
                if shot not in asset or not shot.startswith("save-"):
                    continue
                position = savefmt.decode(path.read_bytes())
                _, _, raw = read_png(asset[shot])
                seen = stars(raw)
                same = seen == sorted(position["centres"])
                bad += not same
                rows.append((record["run_id"], record["arm"], name, shot, ",".join(map(str, sorted(position["centres"]))),
                             ",".join(map(str, seen)), "yes" if same else "NO"))
    with open(batch / "stars.tsv", "xb") as fh:
        fh.write(("run\tarm\tsave\tscreenshot\tcentres_in_save\tstars_on_screen\tequal\n"
                  + "".join("\t".join(r) + "\n" for r in rows)).encode())
    print(f"{len(rows)} saves compared with their screen, {bad} differ")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
