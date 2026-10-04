"""Reading the DOS Isle Wars board from a screenshot (T14): who owns each country, and which
countries touch. Pure functions over `raw`, the 640x350 8-bit RGB pixels of the game window.

This is observation only (directly-observable state read from the pixels, F007); it is how an
exploration script finds a Blue country that borders an enemy on a board that is random in every run.
It claims nothing about the rules: "touch" means two countries' fills are at most BORDER pixels apart
on the screen, and the sea routes (the white lines between islands) are not looked at.

Provenance of the constants (CLAUDE.md rule 17):
- BOXES: the centre of each country's number box in the 640x350 window, found as the black rectangles
  of 8 or 9 pixels in height in a screenshot of a human turn (exploration x06, `human-turn.png`, file
  sha256 in `experiments/E005-iw-dos-state-inventory/measurements/`), and labelled by cropping each box
  to a montage and reading the number. All 46 labels were checked by eye; `derive_boxes` below finds
  the rectangles again.
- COLOURS: the fill colour of the number box's neighbourhood in the same screenshot for each owner, and
  the totals of the scoreboard ("BLUE : 17" and so on) agree with the count of boxes of each colour
  (measurements `board-owner-check.tsv`). The names are the scoreboard's: BLUE, RED, GREEN, BROWN (the
  Brown army is drawn grey).
"""

WIDTH, HEIGHT = 640, 350
BOXES = {
    1: (36, 108), 2: (47, 148), 3: (48, 182), 4: (112, 220), 5: (87, 249), 6: (133, 251), 7: (159, 223),
    8: (189, 256), 9: (183, 158), 10: (143, 160), 11: (144, 114), 12: (107, 137), 13: (105, 95),
    14: (215, 97), 15: (225, 64), 16: (269, 30), 17: (269, 56), 18: (247, 88), 19: (303, 72), 20: (318, 50),
    21: (350, 94), 22: (374, 72), 23: (398, 121), 24: (266, 149), 25: (260, 175), 26: (318, 169),
    27: (259, 240), 28: (336, 225), 29: (307, 258), 30: (373, 241), 31: (364, 202), 32: (421, 220),
    33: (419, 191), 34: (516, 252), 35: (555, 247), 36: (598, 233), 37: (524, 168), 38: (529, 125),
    39: (594, 150), 40: (586, 98), 41: (543, 90), 42: (591, 63), 43: (548, 51), 44: (473, 51),
    45: (427, 44), 46: (454, 76),
}
COLOURS = {"blue": (85, 85, 255), "red": (170, 0, 0), "green": (0, 170, 0), "brown": (85, 85, 85)}
BY_COLOUR = {v: k for k, v in COLOURS.items()}
# Where a country's fill is sampled: beside its number box (the box itself is black and white).
SAMPLES = [(-10, 0), (10, 0), (-10, 4), (10, 4), (-10, -4), (10, -4), (0, 7), (0, -7)]
BORDER = 3          # two fills this close, across a black border line, touch


def pixel(raw, x, y):
    i = (y * WIDTH + x) * 3
    return tuple(raw[i:i + 3])


def owner(raw, n):
    """The army colour at country n ('blue', 'red', 'green', 'brown'), by a vote of the pixels beside
    its number box; None when no sampled pixel is an army colour."""
    cx, cy = BOXES[n]
    votes = {}
    for dx, dy in SAMPLES:
        x, y = cx + dx, cy + dy
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            name = BY_COLOUR.get(pixel(raw, x, y))
            if name:
                votes[name] = votes.get(name, 0) + 1
    return max(sorted(votes), key=votes.get) if votes else None


def owners(raw):
    return {n: owner(raw, n) for n in BOXES}


def totals(raw):
    found = {name: 0 for name in COLOURS}
    for name in owners(raw).values():
        if name:
            found[name] += 1
    return found


def regions(raw):
    """label[y*WIDTH+x] = the country whose fill the pixel is in (0 for none): the 4-connected pixels of
    one army colour around the country's sample points."""
    label = [0] * (WIDTH * HEIGHT)
    for n, (cx, cy) in BOXES.items():
        name = owner(raw, n)
        if not name:
            continue
        colour = COLOURS[name]
        stack = []
        for dx, dy in SAMPLES:
            x, y = cx + dx, cy + dy
            if 0 <= x < WIDTH and 0 <= y < HEIGHT and pixel(raw, x, y) == colour and not label[y * WIDTH + x]:
                stack.append((x, y))
        while stack:
            x, y = stack.pop()
            if label[y * WIDTH + x] or not (0 <= x < WIDTH and 0 <= y < HEIGHT) or pixel(raw, x, y) != colour:
                continue
            label[y * WIDTH + x] = n
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return label


def neighbours(raw):
    """{n: sorted countries that touch n}: fills of two countries at most BORDER pixels apart in a row
    or a column."""
    label = regions(raw)
    touch = {n: set() for n in BOXES}
    for y in range(HEIGHT):
        row = y * WIDTH
        for x in range(WIDTH):
            a = label[row + x]
            if not a:
                continue
            for d in range(1, BORDER + 1):
                if x + d < WIDTH:
                    b = label[row + x + d]
                    if b and b != a:
                        touch[a].add(b)
                        touch[b].add(a)
                if y + d < HEIGHT:
                    b = label[row + d * WIDTH + x]
                    if b and b != a:
                        touch[a].add(b)
                        touch[b].add(a)
    return {n: sorted(v) for n, v in touch.items()}


def derive_boxes(raw):
    """[(x, y, w, h)] of the black rectangles 8 or 9 pixels tall in the map area (y 20..279): the
    number boxes (and nothing else on a board screenshot with no dialog open)."""
    seen = bytearray(WIDTH * HEIGHT)
    found = []
    for y in range(20, 280):
        for x in range(8, 632):
            if seen[y * WIDTH + x] or pixel(raw, x, y) != (0, 0, 0):
                continue
            stack, xs, ys = [(x, y)], [], []
            seen[y * WIDTH + x] = 1
            while stack:
                cx, cy = stack.pop()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and not seen[ny * WIDTH + nx] and pixel(raw, nx, ny) == (0, 0, 0):
                        seen[ny * WIDTH + nx] = 1
                        stack.append((nx, ny))
            w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            if h in (8, 9) and 8 <= w <= 16 and len(xs) > 40:
                found.append((min(xs), min(ys), w, h))
    return sorted(found, key=lambda b: (b[1], b[0]))
