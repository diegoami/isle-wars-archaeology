"""Read the board of one 800x600 frame by pixels (T40): for each of the 46 countries, the army
number and the owner's colour word, or why it is unread. No OCR, no text: the number is the
numeral blobs of the country's anchor matched against bitmap templates (glyphs.py), the owner is
the land colour around the numeral, and a country the reader cannot read with confidence is
recorded as unread with a reason, never guessed.

The 46 anchors (`anchors.json`) are the centres of the numerals as measured over the frames of
the three sittings (measure.py anchors); each is within a few pixels of the E002 tour's click points
(walkthroughs/coordinates.md), which list 44 countries (#120: countries 11 and 15 have no point
there); the anchors of those two were measured from the same frames like the rest.
"""
import json
from pathlib import Path

import numpy as np

import glyphs

HERE = Path(__file__).resolve().parent
ANCHORS_FILE = HERE / "anchors.json"
COUNTRIES = 46
HALF_WIDTH, HALF_HEIGHT = 28, 10      # the window around an anchor in which numerals are looked for
CENTRE_TOLERANCE = (6, 3)             # how far a number's centre may lie from its anchor, (x, y)
MAX_GAP = 8                           # pixels between two glyphs of one number
MAX_DIGITS = 3
STRAY_HEIGHT = 8                      # a blob this high that is not a digit makes the country unread
OWNER_HALF = (5, 4)                   # margin around the numerals in which the land colour is voted
OWNER_MIN_VOTES = 40
OWNER_MIN_SHARE = 0.7
COLOURS = ("blue", "green", "red", "yellow")


def load_anchors(path=ANCHORS_FILE):
    """{country: (x, y)} from anchors.json."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return {int(k): (v["x"], v["y"]) for k, v in doc["anchors"].items()}


def land_family(rgb):
    """The colour family of each pixel of an (h, w, 3) uint8 array: 0 none (sea, shadow, grey,
    glyph), 1 blue, 2 green, 3 red, 4 yellow. The land is drawn in four seat colours, each with
    shades (measured from frames, e.g. red CC3333 993300 CC6666 800000, yellow 999933 CCCC66 666600,
    green 339966 006633 66CC99 009933, blue 333399 6666CC 003366 336699); the sea is a brighter
    blue-cyan whose green exceeds its red."""
    r, g, b = (rgb[:, :, i].astype(np.int32) for i in range(3))
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    live = (mx >= 0x30) & (mx - mn >= 0x20)
    sea = (b >= 0xC0) & (g > r + 0x10)
    out = np.zeros(r.shape, dtype=np.uint8)
    out[live & ~sea & (b > r + 0x30) & (b >= g)] = 1
    out[live & ~sea & (g > r + 0x20) & (g > b + 0x08)] = 2
    out[live & (r > g + 0x28) & (r > b + 0x28)] = 3
    out[live & (r > b + 0x30) & (g > b + 0x30) & (abs(r - g) <= 0x40)] = 4
    return out


def owner_of(rgb, x0, y0, x1, y1):
    """(colour word, why): the family holding at least OWNER_MIN_SHARE of the land-coloured pixels
    of the box, when it holds OWNER_MIN_VOTES of them; else (None, reason)."""
    box = rgb[max(y0, 0):y1, max(x0, 0):x1]
    glyph, _ = glyphs.mask_of(box)
    family = land_family(box)
    family[glyph] = 0
    votes = np.bincount(family.reshape(-1), minlength=5)[1:]
    total = int(votes.sum())
    if total < OWNER_MIN_VOTES:
        return None, "owner-no-land"
    top = int(votes.argmax())
    if votes[top] < OWNER_MIN_SHARE * total:
        return None, "owner-mixed"
    return COLOURS[top], None


def read_country(rgb, anchor, templates):
    """{'army': int|None, 'owner': str|None, 'mark': 'white'|'cyan'|None, 'why': str|None} for the
    country whose numeral is centred on `anchor` (x, y)."""
    cx, cy = anchor
    x0, x1 = int(round(cx)) - HALF_WIDTH, int(round(cx)) + HALF_WIDTH + 1
    y0, y1 = int(round(cy)) - HALF_HEIGHT, int(round(cy)) + HALF_HEIGHT + 1
    if x0 < 0 or y0 < 0 or x1 > rgb.shape[1] or y1 > rgb.shape[0]:
        return {"army": None, "owner": None, "mark": None, "why": "window-outside-frame"}
    window = rgb[y0:y1, x0:x1]
    mask, kind = glyphs.mask_of(window)
    found = []
    for bx, by, bitmap in glyphs.blobs(mask):
        height, width = bitmap.shape
        touches = bx == 0 or by == 0 or bx + width == window.shape[1] or by + height == window.shape[0]
        if height < STRAY_HEIGHT or touches:
            continue      # a speck, or a piece of a neighbour (a label's ring) cut by the window
        if not (glyphs.HEIGHT_RANGE[0] <= height <= glyphs.HEIGHT_RANGE[1]):
            return {"army": None, "owner": None, "mark": None, "why": "stray-blob"}
        digit = templates.match(bitmap)
        if digit is None:
            return {"army": None, "owner": None, "mark": None, "why": "unmatched-glyph"}
        colours = {int(k) for k in kind[by:by + height, bx:bx + width][bitmap > 0]}
        found.append((bx, by, width, digit, colours))
    unread = {"army": None, "owner": None, "mark": None}
    if not found:
        return {**unread, "why": "no-glyph"}
    found.sort()
    if len(found) > MAX_DIGITS:
        return {**unread, "why": "too-many-glyphs"}
    ys = {f[1] for f in found}
    if max(ys) - min(ys) > 1:
        return {**unread, "why": "glyphs-not-in-a-row"}
    for left, right in zip(found, found[1:]):
        if right[0] - (left[0] + left[2]) > MAX_GAP or right[0] < left[0] + left[2] - 1:
            return {**unread, "why": "glyphs-not-adjacent"}
    colours = set().union(*(f[4] for f in found))
    if len(colours) != 1:
        return {**unread, "why": "mixed-glyph-colours"}
    digits = "".join(f[3] for f in found)
    if digits[0] == "0" and len(digits) > 1:
        return {**unread, "why": "leading-zero"}
    left, right = found[0][0], found[-1][0] + found[-1][2]
    centre = (x0 + (left + right) / 2.0, y0 + found[0][1] + 9.0)
    if abs(centre[0] - cx) > CENTRE_TOLERANCE[0] or abs(centre[1] - cy) > CENTRE_TOLERANCE[1]:
        return {**unread, "why": "off-anchor"}
    mark = "cyan" if colours == {2} else "white"
    ox0, ox1 = x0 + left - OWNER_HALF[0], x0 + right + OWNER_HALF[0]
    oy0 = y0 + found[0][1] - OWNER_HALF[1]
    oy1 = y0 + found[0][1] + 18 + OWNER_HALF[1]
    owner, why = owner_of(rgb, ox0, oy0, ox1, oy1)
    return {"army": int(digits), "owner": owner, "mark": mark, "why": why}


def read_board(rgb, templates, anchors=None):
    """{country: reading} for the 46 countries of one (600, 800, 3) frame."""
    anchors = load_anchors() if anchors is None else anchors
    return {c: read_country(rgb, anchors[c], templates) for c in sorted(anchors)}


# The score panel's four seat rows; the row of the player whose turn it is has a light blue box
# whose left edge is on column 19 (measured: 10 or more pixels of that colour down the row's band
# on the current seat, none on the others, over all frames of the three sittings).
SEAT_BANDS = {"blue": (24, 38), "yellow": (45, 59), "red": (66, 80), "green": (87, 101)}
SEAT_COLUMN = 19
SEAT_MINIMUM = 10


def current_seat(rgb):
    """The colour word of the seat whose row is boxed in the score panel, or None when no row, or
    more than one, is."""
    seats = []
    for colour, (top, bottom) in SEAT_BANDS.items():
        column = rgb[top:bottom, SEAT_COLUMN].astype(np.int32)
        if int(((column[:, 2] > 200) & (column[:, 0] < 200)).sum()) >= SEAT_MINIMUM:
            seats.append(colour)
    return seats[0] if len(seats) == 1 else None
