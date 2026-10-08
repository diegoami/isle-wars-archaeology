"""Which screen the game shows, by pixel colour counts on measured regions (T38 round 4; never OCR).

`name_of(frame)` takes one 800x600 stage capture as raw 8-bit RGB bytes (the spike's
`Screen.raw((0, 0, 800, 600))`) and answers one of:

* `eliminated`: the elimination notice, a modal panel over the board with two buttons in the bottom
  bar (the left one gives up, the right one lets the computers play on);
* `board-menu`: the board with the menu row lit (the human's turn: New Game is on the screen);
* `board`: the board without the menu row (the computers' turns, or a prompt over the board);
* `title`: the title screen;
* `unknown`: anything else, including the game-over screen, which no sitting has measured yet.

Every region and threshold was measured from the frames of sitting 20261008T184505Z (batch 1, the
first model-driven sitting; the frames stay on the user's machine, constraint A), decoded to RGB and
counted over all 693 indexed frames. The source frames, by step: the notice in 164 (its last
frames), 166, 168, 170, 172 and 176 (176-1791486093693.png, sha256 ad5970b6...); the board in every
frame from step 8 on; the title in 0; the options screen in 5 and the first frame of 8. The
numbers measured are beside each threshold; each threshold sits between the two populations.
The coordinates are in walkthroughs/coordinates.md, with the same source.
"""
from collections import namedtuple

STAGE = (800, 600)

Test = namedtuple("Test", "rect predicate minimum")

# The right button of the notice's bottom bar, red ground: x 572-759, y 512-550, centre 665,531.
# Notice frames: 3897 of 7332 pixels; every other frame: at most 1878.
KEEP_PLAYING_BOX = (572, 512, 188, 39)
KEEP_PLAYING_CLICK = (665, 531)
# The left button, yellow-olive ground: x 37-224, y 513-550, centre 130,531.
# Notice frames: 4036 of 7144; every other frame: at most 966.
ACCEPT_LOSS_BOX = (37, 513, 188, 38)
# The dark navy panel of the notice over the middle of the board.
# Notice frames: 26798 of 90200; every other frame: at most 10204.
NOTICE_PANEL = (180, 165, 410, 220)
# The score panel's black ground, top left of the board.
# Board frames (notice frames included): at least 11545 of 16575; title and options screens: 0.
SCORE_PANEL = (20, 20, 195, 85)
# The first label of the menu row (cyan text on the bottom bar), lit on the title and on the
# human's turn. Shown: 382 of 2000; hidden: 0.
MENU_LABEL = (50, 576, 100, 20)
# The title's cyan subtitle (the spike's SUBTITLE). Title: 3220 of 11000; board frames: at most 413,
# so this test alone (the spike's `title_up` counts more than 300) does not tell the title from the board.
SUBTITLE = (180, 335, 440, 25)


def red(r, g, b):
    return r > 150 and g < 60 and 30 < b < 130


def olive(r, g, b):
    return r > 120 and g > 110 and b < 70 and abs(r - g) < 60


def navy(r, g, b):
    return r < 40 and g < 40 and b < 150


def black(r, g, b):
    return r < 30 and g < 30 and b < 50


def menu_cyan(r, g, b):
    return 110 < r < 170 and g > 210 and b > 220


def title_cyan(r, g, b):
    return r < 80 and g > 150 and b > 200


TESTS = {
    "keep-playing": Test(KEEP_PLAYING_BOX, red, 2900),
    "accept-loss": Test(ACCEPT_LOSS_BOX, olive, 2500),
    "notice-panel": Test(NOTICE_PANEL, navy, 18000),
    "score-panel": Test(SCORE_PANEL, black, 6000),
    "menu": Test(MENU_LABEL, menu_cyan, 200),
    "subtitle": Test(SUBTITLE, title_cyan, 1500),
}
NAMES = ("eliminated", "board-menu", "board", "title", "unknown")


def count(frame, rect, predicate, width=STAGE[0]):
    """Pixels of `rect` (x, y, w, h) in the RGB `frame` for which `predicate(r, g, b)` holds."""
    x, y, w, h = rect
    total = 0
    for row in range(y, y + h):
        start = (row * width + x) * 3
        line = frame[start:start + w * 3]
        total += sum(1 for i in range(0, len(line) - 2, 3) if predicate(line[i], line[i + 1], line[i + 2]))
    return total


def signals(frame):
    """{test name: True when its count reaches its minimum}."""
    if len(frame) != STAGE[0] * STAGE[1] * 3:
        raise ValueError(f"a frame is {STAGE[0]}x{STAGE[1]} RGB, {STAGE[0] * STAGE[1] * 3} bytes, not {len(frame)}")
    return {name: count(frame, t.rect, t.predicate) >= t.minimum for name, t in TESTS.items()}


def name_of(frame):
    """The screen's name (one of NAMES) from one stage capture."""
    s = signals(frame)
    board = s["score-panel"]
    if board and s["keep-playing"] and s["accept-loss"] and s["notice-panel"]:
        return "eliminated"
    if board:
        return "board-menu" if s["menu"] else "board"
    if s["subtitle"] and s["menu"]:
        return "title"
    return "unknown"
