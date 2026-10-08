"""Tests for runtime/iwp/driver/screens.py (T38 round 4): the screen named by pixel counts.

Synthetic captures only (e020_fixtures.stage_frame paints the measured regions in plain colours);
the measured frames stay on the user's machine (rule 18, constraint A). The thresholds were checked
against all 693 frames of sitting 20261008T184505Z when they were set (walkthroughs/coordinates.md
"Screen tests"); these tests pin the decision the loop relies on:

- the elimination notice is named only with all three of its tests and the board;
- the board with its menu row lit is the only board New Game is sent on, and the title is not
  confused with the board (the title subtitle's colour also shows on the board);
- each minimum is a real bound: one pixel below it, the test is false.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e020_fixtures import screen_frame, stage_frame  # noqa: E402

from driver import screens  # noqa: E402


class ScreenNameTest(unittest.TestCase):
    def test_each_synthetic_screen_is_named(self):
        for name in screens.NAMES:
            with self.subTest(name=name):
                self.assertEqual(screens.name_of(screen_frame(name)), name)

    def test_the_notice_needs_all_three_of_its_tests_and_the_board(self):
        notice = ("keep-playing", "accept-loss", "notice-panel")
        for missing in notice + ("score-panel",):
            with self.subTest(missing=missing):
                parts = [p for p in ("score-panel",) + notice if p != missing]
                self.assertNotEqual(screens.name_of(stage_frame(*parts)), "eliminated")

    def test_the_notice_wins_over_the_board_and_its_menu(self):
        frame = stage_frame("score-panel", "menu", "keep-playing", "accept-loss", "notice-panel")
        self.assertEqual(screens.name_of(frame), "eliminated")

    def test_the_title_is_not_read_on_the_board(self):
        """The subtitle's cyan counts up to 413 on board frames; the board is never the title."""
        self.assertEqual(screens.name_of(stage_frame("score-panel", "menu", "subtitle")), "board-menu")
        self.assertEqual(screens.name_of(stage_frame("subtitle")), "unknown")      # no menu row: not the title

    def test_each_minimum_is_a_bound(self):
        for name, test in screens.TESTS.items():
            with self.subTest(test=name):
                at = screens.count(stage_frame(name, pixels={name: test.minimum}), test.rect, test.predicate)
                below = screens.count(stage_frame(name, pixels={name: test.minimum - 1}), test.rect, test.predicate)
                self.assertEqual((at, below), (test.minimum, test.minimum - 1))
                self.assertTrue(screens.signals(stage_frame(name, pixels={name: test.minimum}))[name])
                self.assertFalse(screens.signals(stage_frame(name, pixels={name: test.minimum - 1}))[name])

    def test_the_winner_notice_needs_the_board_its_panel_and_continue(self):
        """Round 6: `game-over` is the notice panel and the CONTINUE box over the board; without the
        panel the box is a card award's CONTINUE (at most 1603 grey, 3901 navy on the frames)."""
        self.assertEqual(screens.name_of(stage_frame("score-panel", "notice-panel", "continue")), "game-over")
        for missing in ("score-panel", "notice-panel", "continue"):
            with self.subTest(missing=missing):
                parts = [p for p in ("score-panel", "notice-panel", "continue") if p != missing]
                self.assertNotEqual(screens.name_of(stage_frame(*parts)), "game-over")
        self.assertEqual(screens.name_of(stage_frame("score-panel", "menu", "continue")), "board-menu")

    def test_the_continue_minimum_sits_between_the_measured_populations(self):
        """Round 6: 2958 grey pixels on the winner notice; at most 1603 on any other frame (a card
        award's CONTINUE). With the panel up, 1603 is not the winner notice and 2958 is."""
        parts = ("score-panel", "notice-panel", "continue")
        self.assertEqual(screens.name_of(stage_frame(*parts, pixels={"continue": 2958})), "game-over")
        self.assertNotEqual(screens.name_of(stage_frame(*parts, pixels={"continue": 1603})), "game-over")
        self.assertTrue(1603 < screens.TESTS["continue"].minimum <= 2958)

    def test_the_winner_notice_is_never_read_with_an_elimination_button(self):
        for button in ("keep-playing", "accept-loss"):
            with self.subTest(button=button):
                frame = stage_frame("score-panel", "notice-panel", "continue", button)
                self.assertNotEqual(screens.name_of(frame), "game-over")
        frame = stage_frame("score-panel", "notice-panel", "continue", "keep-playing", "accept-loss")
        self.assertEqual(screens.name_of(frame), "eliminated")

    def test_the_winner_is_the_one_seat_with_two_digits_on_the_winner_notice(self):
        for seat in screens.SEAT_NUMBERS:
            with self.subTest(seat=seat):
                self.assertEqual(screens.winner_of(screen_frame("game-over", winner=seat)), seat)
        self.assertIsNone(screens.winner_of(screen_frame("game-over")))              # every seat blank
        self.assertIsNone(screens.winner_of(screen_frame("board", winner="red")))     # a leader, not a winner
        self.assertIsNone(screens.winner_of(screen_frame("eliminated", winner="red")))
        two = stage_frame(*("score-panel", "notice-panel", "continue"), seats={"red": 434, "blue": 434})
        self.assertIsNone(screens.winner_of(two))                                      # never a guess between two

    def test_the_seat_minimum_is_a_bound(self):
        at = stage_frame("score-panel", "notice-panel", "continue", seats={"green": screens.SEAT_MINIMUM})
        below = stage_frame("score-panel", "notice-panel", "continue", seats={"green": screens.SEAT_MINIMUM - 1})
        self.assertEqual((screens.winner_of(at), screens.winner_of(below)), ("green", None))

    def test_a_capture_that_is_not_the_stage_is_refused(self):
        with self.assertRaises(ValueError):
            screens.name_of(b"\0" * 30)

    def test_the_keep_playing_point_is_inside_its_box(self):
        x, y, w, h = screens.KEEP_PLAYING_BOX
        cx, cy = screens.KEEP_PLAYING_CLICK
        self.assertTrue(x <= cx < x + w and y <= cy < y + h)


if __name__ == "__main__":
    unittest.main(verbosity=2)
