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

    def test_the_scoreboard_needs_its_button_and_its_three_percentage_boxes_and_no_board(self):
        """T41 (sitting 20261008T204817Z, steps 367 and 368): the Scoreboard is its CONTINUE button's top
        rows and the black percentage box of each level, with no board behind it."""
        parts = screens.SCOREBOARD_TESTS
        self.assertEqual(screens.name_of(stage_frame(*parts)), "scoreboard")
        for missing in parts:
            with self.subTest(missing=missing):
                self.assertEqual(screens.name_of(stage_frame(*[p for p in parts if p != missing])), "unknown")
        # a board, a title or a notice over it is never the Scoreboard
        self.assertEqual(screens.name_of(stage_frame("score-panel", *parts)), "board")
        self.assertEqual(screens.name_of(stage_frame("score-panel", "menu", *parts)), "board-menu")
        self.assertEqual(screens.name_of(stage_frame("subtitle", "menu", *parts)), "title")
        self.assertEqual(screens.name_of(stage_frame("score-panel", "notice-panel", "continue", *parts)), "game-over")

    def test_the_scoreboards_button_sits_above_the_winner_notices(self):
        """The winner notice's CONTINUE (y 522-546) never fills the Scoreboard button's top rows
        (y 514-521): its frames count at most 368 there; the Scoreboard's 1079."""
        x, y, w, h = screens.SCOREBOARD_BUTTON_TOP
        wx, wy, ww, wh = screens.CONTINUE_BOX
        self.assertLess(y + h - 1, wy)
        self.assertEqual(screens.name_of(stage_frame("score-panel", "notice-panel", "continue")), "game-over")
        self.assertEqual(screens.name_of(stage_frame("continue")), "unknown")
        self.assertLess(screens.SCOREBOARD_CONTINUE_CLICK[1], screens.CONTINUE_CLICK[1])   # higher than 401,534

    def test_each_scoreboard_minimum_sits_between_the_measured_populations(self):
        """Over all 2267 frames of the three sittings: the Scoreboard's 1079 (button top) and 1969 (each
        box); everywhere else at most 368, 1, 130 and 59."""
        measured = {"scoreboard-button": (368, 1079), "scoreboard-easy": (1, 1969),
                    "scoreboard-normal": (130, 1969), "scoreboard-hard": (59, 1969)}
        for name, (elsewhere, on) in measured.items():
            with self.subTest(test=name):
                self.assertTrue(elsewhere < screens.TESTS[name].minimum <= on)
        # one pixel below a minimum, the Scoreboard is not read; at it, it is
        at = {n: screens.TESTS[n].minimum for n in screens.SCOREBOARD_TESTS}
        self.assertEqual(screens.name_of(stage_frame(*screens.SCOREBOARD_TESTS, pixels=at)), "scoreboard")
        for name in screens.SCOREBOARD_TESTS:
            with self.subTest(below=name):
                self.assertEqual(screens.name_of(stage_frame(*screens.SCOREBOARD_TESTS,
                                                             pixels=dict(at, **{name: at[name] - 1}))), "unknown")

    def test_without_the_scoreboard_the_classifier_is_t38s(self):
        """`name_from(scoreboard=False)` is round 6's classifier: check_screens.py compares the two."""
        for name in screens.NAMES:
            frame = screen_frame(name)
            expected = "unknown" if name == "scoreboard" else name
            self.assertEqual(screens.name_from(screens.signals(frame), scoreboard=False), expected)

    def test_a_capture_that_is_not_the_stage_is_refused(self):
        with self.assertRaises(ValueError):
            screens.name_of(b"\0" * 30)

    def test_the_keep_playing_point_is_inside_its_box(self):
        x, y, w, h = screens.KEEP_PLAYING_BOX
        cx, cy = screens.KEEP_PLAYING_CLICK
        self.assertTrue(x <= cx < x + w and y <= cy < y + h)


if __name__ == "__main__":
    unittest.main(verbosity=2)
