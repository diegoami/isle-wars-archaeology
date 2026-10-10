"""The player's live view of the stage (T45): one synchronous capture of the display, decoded and
read by pixels, and the battle probe the attack flow waits on.

The watcher's frames come on a timer (~1.4 s apart, T44), which is why the computer-vs-computer
exchanges of E020 could only be read as nets. The human's own turns wait for the human, so the
player reads the board itself, right after each of its own clicks: `FrameReader.read` captures the
stage through the session (Session.observe_screenshot, which keeps the PNG as a bundle file),
decodes it with E020's reader (pngdecode, glyphs, boardreader -- imported, never edited) and
returns the 46 countries' army counts and owners with the PNG's sha256. A country the reader
cannot read with confidence comes back unread with its reason, never guessed; when any country of
the board is unread the caller treats the whole read as unusable (`board_of` returns None) rather
than plan an attack on a country it cannot see.

`battle_ready` is the spike's own probe (runtime/iwp/spike/cycle.py): the gold QUIT ATTACK button
of the centre panel, at least 1000 pixels within tolerance 20 of (208, 176, 64). The waits are
bounded polls on it and on the board (`wait_ready`, `wait_change`), never fixed sleeps.
"""
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
READER = ROOT / "experiments" / "E020-wine-first-run" / "reader"
if str(READER) not in sys.path:
    sys.path.insert(0, str(READER))
import boardreader  # noqa: E402,E501  (E020's reader, imported read-only)
import glyphs  # noqa: E402

# The battle probe, from the spike's constants (runtime/iwp/spike/cycle.py: CENTRE_PANEL and
# QUIT_ATTACK): the gold quit-attack button in the centre panel of the bottom bar.
CENTRE_PANEL = (262, 502, 276, 70)
QUIT_ATTACK_COLOUR = (208, 176, 64)
QUIT_ATTACK_TOLERANCE = 20
QUIT_ATTACK_MINIMUM = 1000
POLL_SECONDS = 0.3
DEFAULT_TEMPLATES = Path("/mnt/c/Temp/iwp-shots/wine/reader-templates.json")
STAGE = (800, 600)


def gold_count(rgb, rect=CENTRE_PANEL, colour=QUIT_ATTACK_COLOUR, tolerance=QUIT_ATTACK_TOLERANCE):
    """How many pixels of `rect` in an (h, w, 3) uint8 stage capture are within `tolerance`
    (per channel) of `colour`."""
    x, y, w, h = rect
    box = rgb[y:y + h, x:x + w].astype(np.int32)
    r, g, b = colour
    hit = ((np.abs(box[:, :, 0] - r) <= tolerance)
           & (np.abs(box[:, :, 1] - g) <= tolerance)
           & (np.abs(box[:, :, 2] - b) <= tolerance))
    return int(hit.sum()))


def battle_ready(rgb):
    """True when the capture shows the quit-attack button: a battle the game accepted is on."""
    return gold_count(rgb) >= QUIT_ATTACK_MINIMUM


def board_of(rgb, templates, anchors=None):
    """{country: reading} of the capture, or None when any of the 46 countries is unread: the
    player never plans on a board it cannot fully see (the reader's reasons stay in the log)."""
    board = boardreader.read_board(rgb, templates, anchors)
    if any(row["army"] is None or row["owner"] is None for row in board.values()):
        return None
    return {country: {"army": row["army"], "owner": row["owner"]} for country, row in board.items()}


class ReaderError(RuntimeError):
    """The player could not read the stage (no templates file, an undecodable capture): the loop
    ends the sitting cleanly with this reason rather than click on a board it cannot see."""


class FrameReader:
    """Captures the stage on demand and reads it. `capture` is () -> (rgb array, png sha256); the
    launcher builds it from the session (observe_screenshot, then the PNG file it wrote)."""

    def __init__(self, capture, templates=None, sleep=time.sleep, clock=time.monotonic):
        """`templates` is a path to the machine-local digit templates (the launcher's default is
        DEFAULT_TEMPLATES, overridable with E021_TEMPLATES), or an already loaded
        `glyphs.Templates`; None loads the default path."""
        if isinstance(templates, glyphs.Templates):
            self.templates = templates
        else:
            self.templates = glyphs.Templates.load(templates or DEFAULT_TEMPLATES)
        self.capture = capture
        self.sleep, self.clock = sleep, clock
        self.shots = 0

    def shot(self):
        """One capture: (rgb, png sha256); counted, so the log can say how many were taken."""
        rgb, digest = self.capture()
        self.shots += 1
        return rgb, digest

    def read(self):
        """(board or None, png sha256, frame rgb): None board when any country is unread."""
        rgb, digest = self.shot()
        return board_of(rgb, self.templates), digest, rgb

    def ready(self):
        """(whether a battle is on, png sha256, frame rgb)."""
        rgb, digest = self.shot()
        return battle_ready(rgb), digest, rgb

    def wait_ready(self, seconds=3.0):
        """Poll `ready` until a battle is on or the bound runs out; (True, sha) | (False, last sha)."""
        end = self.clock() + seconds
        digest = None
        while True:
            ok, digest, _ = self.ready()
            if ok or self.clock() >= end:
                return ok, digest
            self.sleep(POLL_SECONDS)

    def wait_change(self, board, countries, seconds=3.0):
        """Poll `read` until one of `countries` shows a different (army, owner) than `board`, or
        the bound runs out; (board or None, last png sha256). One capture is always taken, so the
        caller has a frame after the click whatever the game did."""
        end = self.clock() + seconds
        latest = board
        digest = None
        while True:
            latest, digest, _ = self.read()
            if latest is not None and any(
                    (latest.get(c) or {}).get("army"), (latest.get(c) or {}).get("owner")) != \
                    ((board.get(c) or {}).get("army"), (board.get(c) or {}).get("owner"))
                    for c in countries):
                return latest, digest
            if self.clock() >= end:
                return latest, digest
            self.sleep(POLL_SECONDS)
