"""The player's live view of the stage (T45): one capture of the display on demand, decoded and read
by pixels, and the battle probe the attack flow waits on.

The watcher's frames come on a timer (~1.4 s apart, T44), which is why E020 could read the
computers' exchanges only as nets. The human's own turns wait for the human, so the player reads
the board itself, right after each of its own clicks: `FrameReader.read` takes one capture through
the session (the launcher's `capture`: Session.observe_screenshot, which keeps the PNG as a bundle
file, then that file decoded), reads it with E020's reader (boardreader, glyphs -- imported, never
edited) and returns a `Reading`: the 46 countries' army counts and owners, the seat whose row is
boxed in the score panel, whether the battle panel is up, whether the card trade-in offer is up
(`offer`, fix #175), and the PNG's sha256, which is how a
record cites the frame.

A country the reader cannot read with confidence comes back with `army` and `owner` None, never
guessed (the reader's own rule). The picker never names such a country (cases.readable), and the
loop treats a reading with more than `UNREAD_LIMIT` unread countries as no reading at all.

`battle_ready` is the spike's own probe (runtime/iwp/spike/cycle.py, `attack_picked`): the gold
quit-attack button in the centre panel, at least 1000 pixels within 20 of (208, 176, 64). The
waits here are bounded polls on captures (no input), never fixed sleeps.
"""
import sys
import time
from collections import namedtuple
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
READER = ROOT / "experiments" / "E020-wine-first-run" / "reader"
if str(READER) not in sys.path:
    sys.path.insert(0, str(READER))
import boardreader  # noqa: E402  (E020's reader, imported read-only)
import glyphs  # noqa: E402

# The spike's constants (runtime/iwp/spike/cycle.py: CENTRE_PANEL and QUIT_ATTACK).
CENTRE_PANEL = (262, 502, 276, 70)
QUIT_ATTACK_COLOUR = (208, 176, 64)
QUIT_ATTACK_TOLERANCE = 20
QUIT_ATTACK_MINIMUM = 1000
POLL_SECONDS = 0.3
UNREAD_LIMIT = 6            # more unread countries than this and the reading is not used (a guess:
                            # a blinking arrow or a panel may hide a few numerals; E020's three
                            # sittings' frames are not measured for it here)
# The Game Options screen (fix #171): the setup screen New Game shows, which a game abandoned with 10 or
# more human countries goes to with no Scoreboard (sitting 20261011T142906Z, game 2 turn 3). The panel
# is one flat periwinkle ground, (148, 165, 247); `options_up` counts the pixels within
# OPTIONS_TOLERANCE of it in two regions. Census over all 27883 frames of the 11 model-driven sittings
# on the user's machine (decoded in place, constraint A; nothing copied): 41 frames show the screen, and
# every one of them counts exactly 177809 (the whole panel) and 4865 (the strip between the title and
# the first row), against at most 1119 and 628 on every other frame (the title, the board with and
# without its menu row, the winner and elimination notices, the Scoreboard). The frames the numbers
# are traced to, by name and sha256: 20261011T142906Z frames/696-1791729608702.png
# (36306d4cb5826970770fa6cddedf5e447fee0fdde123d8c47d8839c2282caeb5, the screen after the abandon) and
# 20261011T115331Z frames/4-1791719620971.png (6d5ba20ed4c4061fab7c404d54e4afd282e2eb168e09e8a25a23135d086e8163,
# right after New Game's first click; the same bytes as 20261008T184505Z frames/5-1791485114278.png).
# Each minimum sits at about half of the measured count, between the two populations.
OPTIONS_GROUND = (148, 165, 247)
OPTIONS_TOLERANCE = 8
OPTIONS_PANEL = (140, 35, 510, 460)       # x, y, w, h: the panel; measured 177809 of 234600, others <= 1119
OPTIONS_PANEL_MINIMUM = 100000
OPTIONS_STRIP = (150, 84, 490, 10)        # the strip under the title; measured 4865 of 4900, others <= 628
OPTIONS_STRIP_MINIMUM = 2500
DEFAULT_TEMPLATES = Path("/mnt/c/Temp/iwp-shots/wine/reader-templates.json")

# The card trade-in offer (fix #175): at a turn's start with a valid match in hand the game shows two buttons
# in the middle panel (the info panel says to click the matching cards, the right panel shows the hand)
# instead of the placement row, and `place-select` can pick nothing until one of them is answered (F014
# Q-BON-07: the human's screen; the second button skips it). The right button, red, declines, and is the
# one `card-decline` clicks; the left, green, trades, and is the other half of the test. Each is a flat
# coloured button: `offer_up` counts the pixels of the button's colour in a box around it.
# Census over all 28570 frames of the 12 model-driven sittings on the user's machine (frames/*.png, decoded in
# place, constraint A; nothing copied) and the 2091 captures of their session folders: the offer is on one
# frame, 20261011T154319Z frames/618-1791734039170.png (sha256
# c34707147e9a488b57a47fc693353e66a11542d92442885e8e6b779c669c912c), and on the loop's own capture of it,
# session/e021-read-00230.png (sha256 410ad3999b1892070ba83a7a3743637c8fe1563512aa167755329c35a3a08394; the
# same bytes as e021-read-00231.png, after.png and unknown-screen.png of that sitting). On both, the red test
# counts 2006 and the green 2071; on every other frame the red counts at most 301 (a setup screen of
# 20261008T184505Z, frames/10-1791485157213.png and its neighbours) and the green at most 23, and no frame
# counts both. One offer screen is all the sittings hold, so each minimum sits at about half of its
# count (1000), between the two populations; the twin frame 618-1791734038206.png (sha256
# 1eed8b23e9acbeb346c6ac401b7b0730bca95e939078f1d56ec62adbeb9b788b) is the income message about a second
# before the offer, and counts 0 and 0.
OFFER_RED_BOX = (418, 510, 98, 45)        # x, y, w, h: around the red decline button (x 421-512, y 512-552 on the frame)
OFFER_GREEN_BOX = (286, 510, 98, 45)      # around the green trade button (x 289-380, y 512-551 on the frame)
OFFER_RED_MINIMUM = 1000
OFFER_GREEN_MINIMUM = 1000
DECLINE_POINT = (466, 532)                # the centre of the red button's extent on the frame; block card-decline

# The placement panel (fix #182): the "How Many?" box in the middle of the bottom bar, with the counter and
# the four grey buttons ALL, +, - and PLACE, which stays up until the pool is exactly zero (F013 Q-REI-03).
# The screen reader's name (`board-menu`) cannot say so: it reads the bottom bar's menu row, which is lit
# while the panel is up (sitting 20261011T184210Z, game 1 turn 1: after PLACE with 3 armies left the name was
# still `board-menu`). E020's own placement-row test separates the two: the buttons' grey (168, 168, 168, per
# channel within 24), at least 1000 pixels of the row (265, 530, 270, 26), the test `place-select`'s
# `click-until?` already uses. `panel_up` is that test as a pixel count on one capture.
# Frames, by name and sha256 (sitting 20261011T184210Z, frames/): 26-1791744164897.png (sha256
# 047911ab1a68c764c4725db087619b41ac18453d76e595c2ee5e5fa70b137570) and 26-1791744167484.png (sha256
# 2085325e95fecf48ba0d1432d295fd500663a3d9309007b3e2b201d040fe4b11: "How Many? 0", "3 Armies To Place." in the
# right panel, the pool still 3): panel up. The census is in the pull request of
# fix #182 and in `PANEL_CENSUS` below.
PANEL_ROW = (265, 530, 270, 26)           # x, y, w, h: the placement row (E020's `place` watch)
PANEL_GREY = (168, 168, 168)
PANEL_TOLERANCE = 24
PANEL_MINIMUM = 1000
# The two CONTINUE notices (the winner's and the Scoreboard's) have a grey button in the same row too, which
# the test above alone would take for the panel; theirs is one wide button over the gap between ALL and +, where
# the panel's own ground is black. So the panel also needs that gap free of the grey.
PANEL_GAP = (328, 533, 24, 16)            # x, y, w, h: the black between ALL and +
PANEL_GAP_MAXIMUM = 40

Reading = namedtuple("Reading", "board sha256 seat battle unread offer panel", defaults=(False, False))


def gold_count(rgb, rect=CENTRE_PANEL, colour=QUIT_ATTACK_COLOUR, tolerance=QUIT_ATTACK_TOLERANCE):
    """How many pixels of `rect` in an (h, w, 3) uint8 capture are within `tolerance` (per channel)
    of `colour`."""
    x, y, w, h = rect
    box = np.asarray(rgb)[y:y + h, x:x + w].astype(np.int32)
    r, g, b = colour
    hit = ((np.abs(box[:, :, 0] - r) <= tolerance)
           & (np.abs(box[:, :, 1] - g) <= tolerance)
           & (np.abs(box[:, :, 2] - b) <= tolerance))
    return int(hit.sum())


def battle_ready(rgb):
    """True when the capture shows the quit-attack button: a battle the game accepted is on."""
    return gold_count(rgb) >= QUIT_ATTACK_MINIMUM


def options_up(rgb):
    """True when the capture shows the Game Options screen (constants above): both regions hold the
    panel's flat ground in the measured amount. A pure pixel check, never a guess from the board."""
    return (gold_count(rgb, OPTIONS_PANEL, OPTIONS_GROUND, OPTIONS_TOLERANCE) >= OPTIONS_PANEL_MINIMUM
            and gold_count(rgb, OPTIONS_STRIP, OPTIONS_GROUND, OPTIONS_TOLERANCE) >= OPTIONS_STRIP_MINIMUM)


def panel_up(rgb):
    """True when the capture shows the placement panel (constants above): the grey buttons' row holds the
    measured amount. False on the turn menu, whose buttons are not that grey. A pure pixel check."""
    return (gold_count(rgb, PANEL_ROW, PANEL_GREY, PANEL_TOLERANCE) >= PANEL_MINIMUM
            and gold_count(rgb, PANEL_GAP, PANEL_GREY, PANEL_TOLERANCE) <= PANEL_GAP_MAXIMUM)


def offer_red(r, g, b):
    return (r > 140) & (g < 60) & (b < 60)


def offer_green(r, g, b):
    return (r < 60) & (g > 140) & (b < 110)


def colour_count(rgb, rect, predicate):
    """How many pixels of `rect` in an (h, w, 3) uint8 capture satisfy `predicate(r, g, b)` on int32 arrays."""
    x, y, w, h = rect
    box = np.asarray(rgb)[y:y + h, x:x + w].astype(np.int32)
    return int(predicate(box[:, :, 0], box[:, :, 1], box[:, :, 2]).sum())


def offer_up(rgb):
    """True when the capture shows the card trade-in offer (constants above): the red decline
    button and the green trade button, both in the measured amount. A pure pixel check."""
    return (colour_count(rgb, OFFER_RED_BOX, offer_red) >= OFFER_RED_MINIMUM
            and colour_count(rgb, OFFER_GREEN_BOX, offer_green) >= OFFER_GREEN_MINIMUM)


def board_of(rgb, templates, anchors=None):
    """({country: {"army", "owner"}}, number of unread countries) of one capture."""
    board = boardreader.read_board(rgb, templates, anchors)
    out, unread = {}, 0
    for country, row in board.items():
        if row["army"] is None or row["owner"] is None:
            unread += 1
            out[country] = {"army": None, "owner": None}
        else:
            out[country] = {"army": row["army"], "owner": row["owner"]}
    return out, unread


def pair_of(board, countries):
    """The (army, owner) of each of `countries` on `board`, for comparing two readings."""
    return tuple(((board.get(c) or {}).get("army"), (board.get(c) or {}).get("owner")) for c in countries)


class FrameReader:
    """Captures the stage on demand and reads it. `capture` is () -> (rgb array, png sha256)."""

    def __init__(self, capture, templates=None, sleep=time.sleep, clock=time.monotonic, anchors=None):
        """`templates` is a path to the machine-local digit templates (DEFAULT_TEMPLATES when None,
        overridden by the launcher from E021_TEMPLATES) or an already loaded `glyphs.Templates`."""
        if isinstance(templates, glyphs.Templates):
            self.templates = templates
        else:
            self.templates = glyphs.Templates.load(templates or DEFAULT_TEMPLATES)
        self.capture = capture
        self.anchors = anchors
        self.sleep, self.clock = sleep, clock
        self.shots = 0

    def read(self):
        """One capture, read: a Reading (board, png sha256, seat, battle panel up, unread count)."""
        rgb, digest = self.capture()
        self.shots += 1
        board, unread = board_of(rgb, self.templates, self.anchors)
        return Reading(board, digest, boardreader.current_seat(rgb), battle_ready(rgb), unread, offer_up(rgb),
                       panel_up(rgb))

    def options_screen(self):
        """One capture: (True when it shows the Game Options screen, the PNG's sha256). The loop asks
        it only when the screen reader answered `unknown` after the abandon's New Game click."""
        rgb, digest = self.capture()
        self.shots += 1
        return options_up(rgb), digest

    def wait_battle(self, seconds):
        """Poll until the battle panel is up or the bound runs out: the last Reading."""
        end = self.clock() + seconds
        while True:
            reading = self.read()
            if reading.battle or self.clock() >= end:
                return reading
            self.sleep(POLL_SECONDS)

    def wait_settled(self, before, countries, seconds):
        """After a click: poll until `countries` show something else than on `before` and then the
        same on two readings in a row, or the bound runs out. ([Reading, ...] in order, never empty):
        every capture taken, so the record can cite each; the last is the one to use."""
        end = self.clock() + seconds
        seen, changed = [], False
        while True:
            reading = self.read()
            seen.append(reading)
            now = pair_of(reading.board, countries)
            if not changed and now != pair_of(before, countries) and None not in sum(now, ()):
                changed = True
            elif changed and len(seen) > 1 and now == pair_of(seen[-2].board, countries):
                return seen
            if self.clock() >= end:
                return seen
            self.sleep(POLL_SECONDS)
