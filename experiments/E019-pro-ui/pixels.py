"""E019 (T24): the recorder's pixels-read helpers — censuses, text rows, hover grids.

Everything here takes raw 8-bit RGB bytes (what the screen reader returns for a stage rectangle)
and returns plain numbers. No OCR pass anywhere: the recorder reads the screen by pixels, and the
catalogue describes what the values show in its own words (the task's Done-when 4).
"""
from collections import Counter


def _quantised(data, quantise):
    """(r, g, b) tuples with every channel folded to a multiple of `quantise`."""
    step = max(1, int(quantise))
    it = iter(data)
    while True:
        try:
            r, g, b = next(it), next(it), next(it)
        except StopIteration:
            return
        yield r // step * step, g // step * step, b // step * step


def census(data, quantise=16, top=8):
    """Distinct quantised colours of a raw RGB8 capture, the total pixel count, and the most
    common colours as ((r, g, b), count). Raw numbers; what they mean is the catalogue's reading."""
    counts = Counter(_quantised(data, quantise))
    total = sum(counts.values())
    return {"distinct": len(counts), "total": total,
            "top": [[list(colour), n] for colour, n in counts.most_common(top)]}


def _luma(r, g, b):
    return (r * 299 + g * 587 + b * 114) // 1000


def greyscale_census(data, quantise=16, top=8):
    """The same census over luminance: how the capture reads without colour (the greyscale half
    of Q-UI-01 and the contrast half of Q-UI-20)."""
    counts = Counter(_luma(r, g, b) // max(1, int(quantise)) * max(1, int(quantise))
                     for r, g, b in _quantised(data, 1))
    total = sum(counts.values())
    return {"distinct": len(counts), "total": total,
            "top": [[g, n] for g, n in counts.most_common(top)]}


def text_rows(data, width, tol=40):
    """Rows that carry ink, grouped into boxes; the boxes' pixel heights.

    The background is the modal quantised colour of the capture; a pixel is ink when it differs
    from it by more than `tol` in any channel. Returns {"background": [r, g, b], "boxes": n,
    "heights": [...]} — the heights of the text the game drew, in pixels.
    """
    quantise = 16
    counts = Counter(_quantised(data, quantise))
    if not counts:
        return {"background": None, "boxes": 0, "heights": []}
    background = counts.most_common(1)[0][0]

    def is_ink(y):
        row = data[y * width * 3:(y + 1) * width * 3]
        for i in range(0, len(row) - 2, 3):
            if any(abs(row[i + c] - background[c]) > tol for c in range(3)):
                return True
        return False

    heights, run = [], 0
    height = len(data) // (width * 3)
    for y in range(height):
        if is_ink(y):
            run += 1
        elif run:
            heights.append(run)
            run = 0
    if run:
        heights.append(run)
    return {"background": list(background), "boxes": len(heights), "heights": heights}


def hover_points(rect, step, ys):
    """The grid points of a hover map inside rect=(x, y, w, h): every `step` px column, one point
    per y row given. The caller filters the points the step language refuses (the Soleau label)."""
    x, _, w, _ = rect
    return [(x + i * step, y) for y in ys for i in range(max(1, w // step)) if x + i * step < x + w]


def changed_fraction(before, after):
    """Share of pixels that differ between two captures of one rect (0.0 to 1.0). The flash
    candidates of Q-UI-06 and Q-UI-07 are changes with a large fraction."""
    if len(before) != len(after) or not before:
        return 1.0
    differ = 0
    total = 0
    for i in range(0, len(before) - 2, 3):
        total += 1
        if before[i:i + 3] != after[i:i + 3]:
            differ += 1
    return differ / total if total else 0.0
