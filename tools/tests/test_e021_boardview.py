"""T45: the player's live view (experiments/E021-pro-session-a/boardview.py), on synthetic captures
only (arrays the test paints, never a frame of the game, rule 18)."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "tests"))
import e021_fixtures as fx  # noqa: E402,F401  (sys.path)
import boardview  # noqa: E402
import glyphs  # noqa: E402
from driver import screens  # noqa: E402

TEMPLATES = glyphs.Templates({"1": [np.ones((9, 3), dtype=np.uint8)]})


def blank():
    return np.zeros((600, 800, 3), dtype=np.uint8)


def with_quit_button(pixels=boardview.QUIT_ATTACK_MINIMUM):
    rgb = blank()
    x, y, w, _h = boardview.CENTRE_PANEL
    flat = rgb[y:y + 10, x:x + w].reshape(-1, 3)
    flat[:pixels] = boardview.QUIT_ATTACK_COLOUR
    rgb[y:y + 10, x:x + w] = flat.reshape(10, w, 3)
    return rgb


class BattleProbeTest(unittest.TestCase):
    def test_the_quit_attack_gold_is_the_battle_and_its_minimum_is_the_spikes(self):
        self.assertTrue(boardview.battle_ready(with_quit_button()))
        self.assertFalse(boardview.battle_ready(with_quit_button(boardview.QUIT_ATTACK_MINIMUM - 1)))
        self.assertFalse(boardview.battle_ready(blank()))


def paint(rgb, rect, colour):
    x, y, w, h = rect
    rgb[y:y + h, x:x + w] = colour
    return rgb


def grey():
    return np.full((600, 800, 3), 90, dtype=np.uint8)


def options_screen():
    """The Game Options screen as the detector sees it: the panel and the strip under its title in
    the panel's flat ground (a painted stand-in, never a frame of the game)."""
    rgb = grey()
    paint(rgb, boardview.OPTIONS_PANEL, boardview.OPTIONS_GROUND)
    return rgb


def board_screen():
    rgb = blank()
    return paint(rgb, screens.SCORE_PANEL, (0, 0, 0))


def title_screen():
    rgb = grey()
    paint(rgb, screens.SUBTITLE, (0, 200, 255))
    return paint(rgb, screens.MENU_LABEL, (140, 230, 230))


def scoreboard_screen():
    rgb = grey()
    paint(rgb, screens.SCOREBOARD_BUTTON_TOP, (200, 200, 200))
    for rect in (screens.SCOREBOARD_PERCENT_EASY, screens.SCOREBOARD_PERCENT_NORMAL,
                 screens.SCOREBOARD_PERCENT_HARD):
        paint(rgb, rect, (0, 0, 0))
    return rgb


class OptionsScreenTest(unittest.TestCase):
    """Fix #171: the detector of the Game Options screen (boardview.options_up), on painted arrays.
    The constants are traced to the real frames by name and sha256 in boardview.py."""

    def test_the_screen_is_taken_for_the_options_screen(self):
        self.assertTrue(boardview.options_up(options_screen()))

    def test_the_fixtures_are_the_screens_they_stand_for(self):
        # the negatives below mean something only if the screen reader itself names them as such
        self.assertEqual(screens.name_of(board_screen().tobytes()), "board")
        self.assertEqual(screens.name_of(title_screen().tobytes()), "title")
        self.assertEqual(screens.name_of(scoreboard_screen().tobytes()), "scoreboard")
        self.assertEqual(screens.name_of(options_screen().tobytes()), "unknown")    # the screen reader has no name for it

    def test_the_board_the_title_and_the_scoreboard_are_not_taken_for_it(self):
        for name, rgb in (("board", board_screen()), ("title", title_screen()),
                          ("scoreboard", scoreboard_screen()), ("blank", blank())):
            with self.subTest(screen=name):
                self.assertFalse(boardview.options_up(rgb))

    def test_a_board_with_the_ground_colour_in_one_region_only_is_not_taken_for_it(self):
        panel_only = options_screen()
        paint(panel_only, boardview.OPTIONS_STRIP, (0, 0, 0))
        strip_only = paint(blank(), boardview.OPTIONS_STRIP, boardview.OPTIONS_GROUND)
        for name, rgb in (("panel without its strip", panel_only), ("strip only", strip_only)):
            with self.subTest(screen=name):
                self.assertFalse(boardview.options_up(rgb))

    def test_the_minimums_sit_between_the_measured_populations(self):
        # 177809 and 4865 pixels on the 41 options frames; at most 1119 and 628 on every other frame
        self.assertTrue(1119 < boardview.OPTIONS_PANEL_MINIMUM < 177809)
        self.assertTrue(628 < boardview.OPTIONS_STRIP_MINIMUM < 4865)

    def test_the_frame_reader_asks_for_one_capture_and_returns_its_digest(self):
        for rgb, expect in ((options_screen(), True), (board_screen(), False)):
            reader = boardview.FrameReader(lambda rgb=rgb: (rgb, "d" * 64), TEMPLATES)
            self.assertEqual(reader.options_screen(), (expect, "d" * 64))
            self.assertEqual(reader.shots, 1)


class ReaderTest(unittest.TestCase):
    def test_a_capture_the_reader_cannot_read_is_unread_never_guessed(self):
        reader = boardview.FrameReader(lambda: (blank(), "a" * 64), TEMPLATES)
        reading = reader.read()
        self.assertEqual(reading.unread, 46)
        self.assertTrue(all(row == {"army": None, "owner": None} for row in reading.board.values()))
        self.assertEqual(reading.sha256, "a" * 64)
        self.assertFalse(reading.battle)

    def scripted(self, boards):
        """A FrameReader whose reads return `boards` in turn (the last repeats)."""
        reader = boardview.FrameReader(lambda: (blank(), "s" * 64), TEMPLATES, sleep=lambda s: None,
                                       clock=iter(range(0, 1000)).__next__)
        queue = list(boards)

        def read():
            board = queue.pop(0) if len(queue) > 1 else queue[0]
            return boardview.Reading(board, "s" * 64, "blue", True, 0)
        reader.read = read
        return reader

    def test_wait_settled_returns_once_the_counts_changed_and_held(self):
        before = fx.board({3: (fx.BLUE, 5), 4: (fx.RED, 3)})
        moving = fx.board({3: (fx.BLUE, 4), 4: (fx.RED, 3)})
        settled = fx.board({3: (fx.BLUE, 4), 4: (fx.RED, 2)})
        reader = self.scripted([before, moving, settled, settled, fx.board({3: (fx.BLUE, 1)})])
        seen = reader.wait_settled(before, (3, 4), seconds=100)
        self.assertEqual(seen[-1].board, settled)
        self.assertEqual(len(seen), 4)

    def test_wait_settled_gives_up_at_its_bound_with_every_capture(self):
        before = fx.board({3: (fx.BLUE, 5), 4: (fx.RED, 3)})
        reader = self.scripted([before])
        seen = reader.wait_settled(before, (3, 4), seconds=3)
        self.assertEqual(seen[-1].board, before)
        self.assertGreaterEqual(len(seen), 3)


if __name__ == "__main__":
    unittest.main()
