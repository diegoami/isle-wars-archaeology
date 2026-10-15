"""Which screen the game shows, by pixel colour counts on measured regions (T38 round 4; never OCR).

`name_of(frame)` takes one 800x600 stage capture as raw 8-bit RGB bytes (the spike's
`Screen.raw((0, 0, 800, 600))`) and answers one of:

* `eliminated`: the elimination notice, a modal panel over the board with two buttons in the bottom
  bar (the left one gives up, the right one lets the computers play on);
* `game-over`: the winner notice (T38 round 6), the same dark panel over the board with one
  CONTINUE button in the middle of the bottom bar -- it blinks between a light grey and a green
  phase (fix #141, round 2, measured on sitting 20261009T160556Z), and either phase names it --
  and neither of the elimination notice's buttons;
* `scoreboard` (T41): the Scoreboard the game shows after it credits a loss, with its one grey CONTINUE
  button in the bottom bar, higher than the winner notice's, and no board behind it;
* `board-menu`: the board with the menu row lit (the human's turn: New Game is on the screen);
* `board`: the board without the menu row (the computers' turns, or a prompt over the board);
* `title`: the title screen;
* `unknown`: anything else.

`card_award_green(frame)` and `human_attack_ready(frame)` are narrower phase probes, not new screen
names. `card_award_green` is validated only against the #236 census population: the supplied
positive card-prompt frame has the measured green
CONTINUE signal, a score panel, no notice or terminal buttons, and no menu row; the 134 other census
frames have at most 37 green CONTINUE pixels against the existing 1300 minimum. The grey award phase
was not measured and therefore never matches this probe.

`human_attack_ready` is validated only against the bounded #239 census population described below.

Every region and threshold of round 4 was measured from the frames of sitting 20261008T184505Z
(batch 1, the first model-driven sitting; the frames stay on the user's machine, constraint A),
decoded to RGB and counted over all 693 indexed frames. The source frames, by step: the notice in
164 (its last frames), 166, 168, 170, 172 and 176 (176-1791486093693.png, sha256 ad5970b6...); the
board in every frame from step 8 on; the title in 0; the options screen in 5 and the first frame of
8. The numbers measured are beside each threshold; each threshold sits between the two populations.
The coordinates are in walkthroughs/coordinates.md, with the same source.

Round 6 added `game-over` and the winner's seat (`winner_of`), measured from the frames of sitting
20261008T195537Z (batch 2): the winner notice in its 36 frames of steps 177 to 186
(182-1791490010546.png, sha256 14ae2f71...), and every other frame of both sittings (1143) as the
population it must not match. The round 6 numbers are over all 1179 frames of the two sittings; over
them every round 4 name is unchanged.

T41 added `scoreboard`, measured from the frames of sitting 20261008T204817Z (batch 3): the Scoreboard
in its 7 frames, steps 367 and 368 (368-1791494104472.png, sha256 in walkthroughs/coordinates.md),
which the game showed after New Game was sent from the board of a live game with the human holding
fewer than 10 countries (F003). The numbers measured over all 2267 frames of the three sittings are
beside each threshold; over them every earlier name is unchanged, which
experiments/E020-wine-first-run/check_screens.py re-checks from the frames.
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
# Notice frames: 26798 of 90200; every other frame: at most 10204. Winner notice: 27935.
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
# The winner notice's CONTINUE button, in the middle of the bottom bar: x 327-475, y 522-546,
# centre 401,534 (round 6). It blinks between two phases (fix #141, round 2): light grey, 2958 of
# 3725 pixels on the round 6 frames and at most 1603 on every other frame of both sittings (the
# CONTINUE of a card award, a smaller button near 402,531, which shows with no notice panel: its
# frames count at most 3901 navy on NOTICE_PANEL); and green, which the grey test does not match,
# so a green-phase notice read as the board and the loop played its placement blocks on it (the
# r0008 abort). Either phase names the notice, below.
CONTINUE_BOX = (327, 522, 149, 25)
CONTINUE_CLICK = (401, 534)

# The centre panel used by the bounded attack-ready probe.  The panel is the existing E002/F003
# phase-panel rectangle; only its measured red population is new here.  The positive population's
# lowest red count is 2296 and the other human board-menu population's highest is 1974 (E019
# measurement 239).  2135 is the deliberately conservative midpoint, not a universal classifier.
ATTACK_READY_PANEL = (262, 502, 276, 70)
ATTACK_READY_RED_MINIMUM = 2135


# The Scoreboard's CONTINUE button (T41), light grey like the winner notice's, but higher: x 327-474,
# y 514-538, centre 401,526 (E002's "Continue (after loss)" is 400,526). Its top rows only, which the
# winner notice's button (y 522-546) and a card award's CONTINUE (near y 531) never fill:
# Scoreboard frames: 1079 of 1192 pixels; every other frame: at most 368.
SCOREBOARD_BUTTON_TOP = (327, 514, 149, 8)
SCOREBOARD_CONTINUE_CLICK = (401, 526)
# The Scoreboard's three percentage boxes, black grounds under cyan text, one per level (Easy, Normal,
# Hard): x 538-621, y 230-257, 302-329 and 376-403 (the tests take x 537-621, 85 wide, 28 high).
# Scoreboard frames: 1969 of 2380 pixels in each; every other frame: at most 1 (Easy), 130 (Normal), 59 (Hard).
SCOREBOARD_PERCENT_EASY = (537, 230, 85, 28)
SCOREBOARD_PERCENT_NORMAL = (537, 302, 85, 28)
SCOREBOARD_PERCENT_HARD = (537, 376, 85, 28)


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


def light_grey(r, g, b):
    return r > 140 and g > 140 and b > 140 and max(r, g, b) - min(r, g, b) < 20


def continue_green(r, g, b):
    """The CONTINUE button's green phase (fix #141, round 2): the button blinks between this green
    and the light grey `light_grey` matches, and the grey test saw only the grey phase, so a
    green-phase winner notice read as the board and the loop played placement blocks on it (sitting
    20261009T160556Z, E020-r0008: aborted at the ALL click of turn 21 on the notice). The census is
    the main session's over CONTINUE_BOX in 16-level bins (PR #146): green (144,208,128) 1209 px,
    (160,208,160) 302, (112,192,112) 249 -- about 1760 px, against 2200 for the grey test on the
    grey phase -- and the grey phase (176,176,176) 1409, (160,160,160) 427, (240,240,240) 387,
    (192,192,192) 351 counts 0 here, its green spread at most 15 against the more than 24 asked
    below. The bounds hold every measured bin: red and blue inside 111..175, green inside 192..223."""
    return 100 < r < 190 and 180 < g < 240 and 100 < b < 190 and g - r > 24 and g - b > 24


def attack_red(r, g, b):
    """The measured candidate predicate for the human attack-ready panel."""
    return r > 150 and g < 60 and b < 60


TESTS = {
    "keep-playing": Test(KEEP_PLAYING_BOX, red, 2900),
    "accept-loss": Test(ACCEPT_LOSS_BOX, olive, 2500),
    "notice-panel": Test(NOTICE_PANEL, navy, 18000),
    "score-panel": Test(SCORE_PANEL, black, 6000),
    "menu": Test(MENU_LABEL, menu_cyan, 200),
    "subtitle": Test(SUBTITLE, title_cyan, 1500),
    "continue": Test(CONTINUE_BOX, light_grey, 2200),
    # The green phase of the same button. Minimum 1300: the measured green phase is about 1760, and
    # the minimum keeps the grey test's own margin (2200 of its measured 2958, 74%): 74% of 1760.
    # The grey phase counts 0 here; no other frame of the three sittings was censused for green in
    # this box, so the name still needs the notice panel and the score panel and neither elimination
    # button (name_from below), which no board, card award or title shows together.
    "continue-green": Test(CONTINUE_BOX, continue_green, 1300),
    "scoreboard-button": Test(SCOREBOARD_BUTTON_TOP, light_grey, 720),
    "scoreboard-easy": Test(SCOREBOARD_PERCENT_EASY, black, 1500),
    "scoreboard-normal": Test(SCOREBOARD_PERCENT_NORMAL, black, 1500),
    "scoreboard-hard": Test(SCOREBOARD_PERCENT_HARD, black, 1500),
}
SCOREBOARD_TESTS = ("scoreboard-button", "scoreboard-easy", "scoreboard-normal", "scoreboard-hard")
NAMES = ("eliminated", "game-over", "scoreboard", "board-menu", "board", "title", "unknown")


# The score panel's seat rows (round 6): the number after each seat's name, in the seat's own colour,
# x 107-137 (after the colon, before "Cards"). Its colours, as measured: blue 49,156,255, yellow
# 255,255,0, red 255,49,49, green 0,206,49. A two-digit number fills about twice the pixels of a
# one-digit one; the counts are beside SEAT_MINIMUM.
def seat_blue(r, g, b):
    return r < 100 and 120 < g < 200 and b > 220


def seat_yellow(r, g, b):
    return r > 220 and g > 220 and b < 60


def seat_red(r, g, b):
    return r > 220 and g < 90 and b < 90


def seat_green(r, g, b):
    return r < 60 and g > 170 and b < 90


SEAT_NUMBERS = {
    "blue": ((107, 24, 31, 14), seat_blue),
    "yellow": ((107, 45, 31, 14), seat_yellow),
    "red": ((107, 66, 31, 14), seat_red),
    "green": ((107, 86, 31, 14), seat_green),
}
# Winner frames: the winner's 46 fills 130 pixels (red), every other seat's 0 58 to 67. Over all 1179
# frames a seat's number counted 42 to 74 when its row showed one digit (as seen on the frames) and
# up to 130; the minimum sits between the winner's 46 and the others' 0, and winner_of is only asked
# on the winner notice, where every other seat holds 0.
SEAT_MINIMUM = 100


def check_stage(frame):
    if len(frame) != STAGE[0] * STAGE[1] * 3:
        raise ValueError(f"a frame is {STAGE[0]}x{STAGE[1]} RGB, {STAGE[0] * STAGE[1] * 3} bytes, not {len(frame)}")


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
    check_stage(frame)
    return {name: count(frame, t.rect, t.predicate) >= t.minimum for name, t in TESTS.items()}


def card_award_green(frame):
    """True for the measured green card-prompt population, conservatively only.

    This is not a universal award classifier: the positive/negative separation is bounded to
    `experiments/E019-pro-ui/measurements/236-card-phase-census.json`. The score panel and the
    absence of both terminal notice buttons retain the existing terminal-state exclusions; the
    absent menu row prevents a stale human-turn reading from being treated as the prompt. A grey
    award frame is unsupported and returns False.
    """
    s = signals(frame)
    return (s["score-panel"] and s["continue-green"] and not s["notice-panel"]
            and not s["keep-playing"] and not s["accept-loss"] and not s["menu"])


def human_attack_ready(frame):
    """True only for the bounded, measured human attack-ready population.

    This deliberately combines the existing human board-menu/score reading with the measured
    centre-panel red population.  It is not a general phase classifier: a notice or any other
    unsupported state is refused, and an ordinary board-menu frame is not enough.
    """
    s = signals(frame)
    human_menu = s["score-panel"] and s["menu"]
    terminal = (s["notice-panel"] or s["keep-playing"] or s["accept-loss"] or s["continue"]
                or s["continue-green"] or all(s[name] for name in SCOREBOARD_TESTS))
    return (human_menu and not terminal
            and count(frame, ATTACK_READY_PANEL, attack_red) >= ATTACK_READY_RED_MINIMUM)


# Short name for callers that already scope the probe to a human turn.
attack_ready = human_attack_ready


def name_from(s, scoreboard=True):
    """The name of the screen the `signals` show. `scoreboard=False` is T38's classifier (round 6),
    without the Scoreboard: check_screens.py compares the two over every frame."""
    board = s["score-panel"]
    if board and s["keep-playing"] and s["accept-loss"] and s["notice-panel"]:
        return "eliminated"
    if board and s["notice-panel"] and (s["continue"] or s["continue-green"]) \
            and not s["keep-playing"] and not s["accept-loss"]:
        # Either phase of the blinking CONTINUE (fix #141, round 2): the grey test alone left the
        # green phase unnamed, and the loop then played placement blocks on the winner notice.
        return "game-over"
    if board:
        return "board-menu" if s["menu"] else "board"
    if scoreboard and all(s[name] for name in SCOREBOARD_TESTS):
        # #141: named before the title. Over all 2267 frames of the three sittings no frame but the
        # Scoreboard's reaches even half of any of the four minima (elsewhere at most 368, 1, 130,
        # 59), so a frame that trips all four is the Scoreboard whatever else it shows; a real title
        # never trips them, so no real title changes name. While the title branch ran first, a frame
        # with the four signals and the title's subtitle and menu read "title", the one name the
        # loop acts on blind: New Game was sent on a screen that was not the title.
        return "scoreboard"                                # T41: no board behind it
    if s["subtitle"] and s["menu"]:
        return "title"
    return "unknown"


def name_of(frame):
    """The screen's name (one of NAMES) from one stage capture."""
    return name_from(signals(frame))


def winner_of(frame):
    """The winning seat's colour word, read from the score panel by pixels (never OCR): the one seat
    whose number fills SEAT_MINIMUM pixels or more of its colour, a two-digit number (at the game's
    end the winner holds all 46 countries, every other seat 0). None unless the frame is the winner
    notice (`game-over`; elsewhere one seat with two digits is only a leader) and exactly one seat
    does."""
    if name_of(frame) != "game-over":
        return None
    seats = [seat for seat, (rect, colour) in SEAT_NUMBERS.items() if count(frame, rect, colour) >= SEAT_MINIMUM]
    return seats[0] if len(seats) == 1 else None
