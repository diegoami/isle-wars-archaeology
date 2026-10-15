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
import json
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

    def test_the_measured_green_card_probe_excludes_terminal_and_human_menu_states(self):
        self.assertTrue(screens.card_award_green(stage_frame("score-panel", "continue-green")))
        self.assertFalse(screens.card_award_green(stage_frame("score-panel", "notice-panel",
                                                              "continue-green")))
        self.assertFalse(screens.card_award_green(stage_frame("score-panel", "menu",
                                                              "continue-green")))
        self.assertFalse(screens.card_award_green(stage_frame("score-panel")))

    def test_the_committed_census_separates_green_prompt_population(self):
        path = Path(__file__).resolve().parents[2] / "experiments" / "E019-pro-ui" / "measurements" \
            / "236-card-phase-census.json"
        census = json.loads(path.read_text(encoding="utf-8"))
        rows = census["frames"]
        positive_hash = census["positive_raw_rgb8_sha256"]
        positive = [row for row in rows if row["raw_rgb8_sha256"] == positive_hash]
        negative = [row for row in rows if row["raw_rgb8_sha256"] != positive_hash]
        self.assertEqual(len(positive), 2)
        self.assertEqual(len({row["raw_rgb8_sha256"] for row in positive}), 1)
        self.assertTrue(all(row["signals"]["score-panel"] for row in positive))
        self.assertTrue(all(row["signals"]["continue-green"] for row in positive))
        self.assertTrue(all(not row["signals"][name] for name in ("notice-panel", "menu")
                            for row in positive))
        self.assertLess(max(row["counts"]["continue-green"] for row in negative),
                        screens.TESTS["continue-green"].minimum)

    def test_the_continue_minimum_sits_between_the_measured_populations(self):
        """Round 6: 2958 grey pixels on the winner notice; at most 1603 on any other frame (a card
        award's CONTINUE). With the panel up, 1603 is not the winner notice and 2958 is."""
        parts = ("score-panel", "notice-panel", "continue")
        self.assertEqual(screens.name_of(stage_frame(*parts, pixels={"continue": 2958})), "game-over")
        self.assertNotEqual(screens.name_of(stage_frame(*parts, pixels={"continue": 1603})), "game-over")
        self.assertTrue(1603 < screens.TESTS["continue"].minimum <= 2958)

    def test_the_continue_buttons_green_phase_is_read_as_game_over(self):
        """#141 round 2: the winner notice's CONTINUE blinks between a grey phase (the `continue`
        test) and a green phase, which the grey test does not match (the green phase counts 385
        light-grey pixels, below 2200), so a green-phase notice read as the board and the loop
        played its placement blocks on it (sitting 20261009T160556Z, E020-r0008). The `continue-green`
        test matches the green phase: with the notice panel and the score panel up, either phase
        names `game-over`, and the winner is read from it either way."""
        parts = ("score-panel", "notice-panel", "continue-green")
        self.assertEqual(screens.name_of(stage_frame(*parts)), "game-over")
        self.assertEqual(screens.winner_of(stage_frame(*parts, seats={"red": 31 * 14})), "red")

    def test_each_continue_phase_trips_only_its_own_test(self):
        """The two phases never blur: a frame of one phase misses the other's test, and both name
        `game-over` over the notice panel and the score panel."""
        for phase, other in (("continue", "continue-green"), ("continue-green", "continue")):
            with self.subTest(phase=phase):
                frame = stage_frame("score-panel", "notice-panel", phase)
                signals = screens.signals(frame)
                self.assertTrue(signals[phase])
                self.assertFalse(signals[other])
                self.assertEqual(screens.name_of(frame), "game-over")

    def test_the_continue_green_minimum_sits_between_the_measured_populations(self):
        """#141 round 2: about 1760 green pixels on the green-phase frame (bins 1209 + 302 + 249,
        the main session's census on PR #146); the grey phase counts 0 here, its green spread at
        most 15 against the more than 24 the predicate asks. The minimum keeps the grey test's own
        margin (2200 of its measured 2958, 74%): 74% of 1760."""
        parts = ("score-panel", "notice-panel", "continue-green")
        self.assertEqual(screens.name_of(stage_frame(*parts, pixels={"continue-green": 1760})), "game-over")
        self.assertTrue(0 < screens.TESTS["continue-green"].minimum <= 1760)
        self.assertFalse(screens.signals(stage_frame("score-panel", "notice-panel", "continue"))["continue-green"])

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
        # a board or a notice over it is never the Scoreboard; the title never demotes it (#141):
        # four measured scoreboard signals are the Scoreboard, whatever the subtitle and menu show
        self.assertEqual(screens.name_of(stage_frame("score-panel", *parts)), "board")
        self.assertEqual(screens.name_of(stage_frame("score-panel", "menu", *parts)), "board-menu")
        self.assertEqual(screens.name_of(stage_frame("subtitle", "menu", *parts)), "scoreboard")
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

    def test_the_scoreboard_is_named_before_the_title(self):
        """#141 (cause 2): the title branch ran first, so a frame carrying the Scoreboard's four
        measured signals and the title's subtitle and menu rows read `title` -- the one name the loop
        acts on blind, by sending New Game. Over all 2267 frames of the three sittings no frame but
        the Scoreboard's reaches even half of any scoreboard minimum (elsewhere at most 368, 1, 130,
        59 against minima 720, 1500, 1500, 1500), so a frame that trips all four is the Scoreboard,
        never the title; a real title never trips them, so no real title changes name."""
        frame = stage_frame("subtitle", "menu", *screens.SCOREBOARD_TESTS)
        self.assertEqual(screens.name_of(frame), "scoreboard")
        self.assertEqual(screens.name_of(stage_frame("subtitle", "menu")), "title")   # no scoreboard signals
        # T38's classifier (check_screens.py's comparator) still names it from the subtitle and menu
        self.assertEqual(screens.name_from(screens.signals(frame), scoreboard=False), "title")

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


class AttackReadyProbeTest(unittest.TestCase):
    """#239: the attack probe is a bounded human-menu plus watched-panel measurement."""

    @staticmethod
    def frame(red_pixels, *parts):
        frame = bytearray(stage_frame("score-panel", "menu", *parts))
        x, y, w, h = screens.ATTACK_READY_PANEL
        left = red_pixels
        for row in range(y, y + h):
            n = min(w, left)
            if n <= 0:
                break
            start = (row * 800 + x) * 3
            frame[start:start + n * 3] = bytes((200, 0, 0)) * n
            left -= n
        return bytes(frame)

    def test_the_measured_red_midpoint_is_a_bound(self):
        at = self.frame(screens.ATTACK_READY_RED_MINIMUM)
        below = self.frame(screens.ATTACK_READY_RED_MINIMUM - 1)
        self.assertTrue(screens.human_attack_ready(at))
        self.assertFalse(screens.human_attack_ready(below))
        self.assertEqual(screens.count(at, screens.ATTACK_READY_PANEL, screens.attack_red),
                         screens.ATTACK_READY_RED_MINIMUM)

    def test_the_probe_requires_the_human_menu_and_excludes_terminal_notice(self):
        self.assertFalse(screens.human_attack_ready(self.frame(screens.ATTACK_READY_RED_MINIMUM, "notice-panel")))
        self.assertFalse(screens.human_attack_ready(
            stage_frame("score-panel", "menu")))
        no_menu = self.frame(screens.ATTACK_READY_RED_MINIMUM)
        # Remove only the existing human-menu signal while preserving the measured red population.
        x, y, w, h = screens.MENU_LABEL
        clean = bytearray(no_menu)
        for row in range(y, y + h):
            start = (row * 800 + x) * 3
            clean[start:start + w * 3] = bytes((128, 128, 128)) * w
        self.assertFalse(screens.human_attack_ready(bytes(clean)))

    def test_the_probe_threshold_is_derived_from_the_committed_census_populations(self):
        path = Path(__file__).resolve().parents[2] / "experiments" / "E019-pro-ui" / "measurements" \
            / "239-attack-phase-census.json"
        census = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(census["rect"], list(screens.ATTACK_READY_PANEL))
        self.assertEqual(census["predicate"], {"r_gt": 150, "g_lt": 60, "b_lt": 60})
        positives = {"7ca1db9ca3019e7a", "865937d28607e468", "36494cf78e3a15cf",
                     "ecd0ce15458e533f", "84b4b1f44ff09610", "2944f60e1ee969ae",
                     "6c6802ee018d457b"}
        rows = census["frames"]
        positive_rows = [row for row in rows if row["file_sha256"].startswith(tuple(positives))]
        negative_board_rows = [row for row in rows
                               if row["screen"] == "board-menu"
                               and not row["file_sha256"].startswith(tuple(positives))]
        self.assertEqual(len(positive_rows), 8)       # one positive file is indexed twice
        self.assertEqual(min(row["centre_red"] for row in positive_rows), 2296)
        self.assertEqual(max(row["centre_red"] for row in negative_board_rows), 1974)
        self.assertEqual(screens.ATTACK_READY_RED_MINIMUM,
                         (2296 + 1974) // 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
