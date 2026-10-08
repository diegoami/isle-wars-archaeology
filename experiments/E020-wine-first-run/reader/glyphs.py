"""Digit glyphs by pixels (T40): connected blobs of the numeral colours, matched against bitmap
templates. There is no OCR engine and no text pass: a blob is a set of pixels, a template is a set
of pixels, and a blob that is not within `MAX_DISTANCE` pixels of exactly one template, clearly
closer than any other, is no digit.

What the frames show (measured over all 2,267 frames of the three sittings, see
experiments/E020-wine-first-run/measurements/digit-labels.json): a country's army number is drawn in
one flat colour (white, or cyan on the few countries the game marks) with a black shadow; every
glyph is 18 pixels high and 11 to 15 wide, and the same digit is always the same bitmap, to the
pixel, except for one-pixel variants (3 blobs in 71,000) and one clipped "1".

The templates themselves are bitmaps of the original's numerals: they are measured on the user's
machine by `build_templates.py` and stay there (rule 18); the repository holds only their hashes and
labels. Tests use a synthetic font.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

# The two colours a numeral is drawn in (measured; both exact RGB values, never anti-aliased).
GLYPH_COLOURS = {"white": (0xFF, 0xFB, 0xF0), "cyan": (0x33, 0xFF, 0xFF)}
HEIGHT = 18                  # every numeral glyph is 18 pixels high (measured)
HEIGHT_RANGE = (17, 19)      # a blob this high may be a glyph; anything else is ignored
MAX_DISTANCE = 3             # differing pixels allowed between a blob and its template
MARGIN = 6                   # the next template must be at least this many pixels further away


def mask_of(window):
    """Boolean mask of the (h, w, 3) uint8 window's glyph-coloured pixels, and the colour word of
    each (0 none, 1 white, 2 cyan) as an int array."""
    kind = np.zeros(window.shape[:2], dtype=np.uint8)
    for i, colour in enumerate(GLYPH_COLOURS.values(), start=1):
        kind[(window == colour).all(axis=2)] = i
    return kind > 0, kind


def blobs(mask):
    """Connected blobs (8-neighbourhood) of a boolean mask: [(x0, y0, bitmap)], bitmap a uint8
    (h, w) array of the blob's own pixels. Order: top to bottom, then left to right."""
    height, width = mask.shape
    todo = set(zip(*(a.tolist() for a in np.nonzero(mask)[::-1])))   # {(x, y)}
    out = []
    while todo:
        start = min(todo, key=lambda p: (p[1], p[0]))
        todo.discard(start)
        stack, comp = [start], [start]
        while stack:
            x, y = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    n = (x + dx, y + dy)
                    if n in todo:
                        todo.discard(n)
                        stack.append(n)
                        comp.append(n)
        xs = [p[0] for p in comp]
        ys = [p[1] for p in comp]
        x0, y0 = min(xs), min(ys)
        bitmap = np.zeros((max(ys) - y0 + 1, max(xs) - x0 + 1), dtype=np.uint8)
        for x, y in comp:
            bitmap[y - y0, x - x0] = 1
        out.append((x0, y0, bitmap))
    return sorted(out, key=lambda b: (b[1], b[0]))


def bitmap_sha256(bitmap):
    """The hash the repository records instead of a bitmap: sha256 of `WxH:` and the pixel bytes."""
    h, w = bitmap.shape
    return hashlib.sha256(f"{w}x{h}:".encode() + bitmap.astype(np.uint8).tobytes()).hexdigest()


class Templates:
    """The digit templates: {digit: [bitmap, ...]} (a digit may have more than one bitmap)."""

    def __init__(self, bitmaps):
        self.bitmaps = [(digit, np.asarray(b, dtype=np.uint8)) for digit, group in bitmaps.items() for b in group]
        if not self.bitmaps:
            raise ValueError("no digit templates")

    @classmethod
    def load(cls, path):
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        grouped = {}
        for entry in doc["templates"]:
            rows = entry["rows"]
            bitmap = np.array([[1 if c == "#" else 0 for c in row] for row in rows], dtype=np.uint8)
            grouped.setdefault(entry["digit"], []).append(bitmap)
        return cls(grouped)

    @staticmethod
    def dump(entries, path):
        """Write [(digit, bitmap)] as the machine-local template file."""
        doc = {"what": "digit bitmaps of the original's numerals, measured on this machine; never committed",
               "templates": [{"digit": d, "rows": ["".join("#" if v else "." for v in row) for row in b]}
                             for d, b in entries]}
        Path(path).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")

    def match(self, bitmap):
        """The digit whose template is within MAX_DISTANCE pixels of `bitmap` and at least MARGIN
        pixels closer than every template of another digit; None when there is none."""
        best = {}
        for digit, template in self.bitmaps:
            if template.shape != bitmap.shape:
                continue
            distance = int((template != bitmap).sum())
            if distance < best.get(digit, 10 ** 9):
                best[digit] = distance
        if not best:
            return None
        ranked = sorted(best.items(), key=lambda kv: kv[1])
        digit, distance = ranked[0]
        if distance > MAX_DISTANCE:
            return None
        if len(ranked) > 1 and ranked[1][1] - distance < MARGIN:
            return None
        return digit
