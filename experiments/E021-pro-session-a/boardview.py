"""The player's live view of the stage (T45): one capture of the display on demand, decoded and read
by pixels, and the battle probe the attack flow waits on.

The watcher's frames come on a timer (~1.4 s apart, T44), which is why E020 could read the
computers' exchanges only as nets. The human's own turns wait for the human, so the player reads
the board itself, right after each of its own clicks: `FrameReader.read` takes one capture through
the session (the launcher's `capture`: Session.observe_screenshot, which keeps the PNG as a bundle
file, then that file decoded), reads it with E020's reader (boardreader, glyphs -- imported, never
edited) and returns a `Reading`: the 46 countries' army counts and owners, the seat whose row is
boxed in the score panel, whether the battle panel is up, and the PNG's sha256, which is how a
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

Reading = namedtuple("Reading", "board sha256 seat battle unread")


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
        return Reading(board, digest, boardreader.current_seat(rgb), battle_ready(rgb), unread)

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
