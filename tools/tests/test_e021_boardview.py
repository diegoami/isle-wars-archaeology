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


def offer_screen():
    """The card trade-in offer as the detector sees it: a board (score panel) with the two buttons of the
    middle panel in their grounds, red on the right and green on the left. Painted to about the pixel
    count the real frame shows (2006 red, 2071 green: the buttons' text and shading take the rest)."""
    # (the painted rectangles are 92x22 = 2024 pixels each)
    rgb = board_screen()
    paint(rgb, (421, 514, 92, 22), (176, 16, 16))
    paint(rgb, (289, 514, 92, 22), (0, 176, 32))
    return rgb


def menu_board():
    """The board with the turn menu lit: its cyan label, and the green CARD button (8, 206, 66)."""
    rgb = board_screen()
    paint(rgb, screens.MENU_LABEL, (140, 230, 230))
    return paint(rgb, (446, 518, 46, 28), (8, 206, 66))


def placement_row_board():
    """The board with a patch of the placement row's grey (168, 168, 168) lit in its area."""
    rgb = board_screen()
    return paint(rgb, (265, 530, 50, 26), (168, 168, 168))


def notice_screen():
    """The elimination notice: its navy panel, its red and olive buttons (screens.py's regions)."""
    rgb = board_screen()
    paint(rgb, screens.NOTICE_PANEL, (10, 10, 100))
    paint(rgb, screens.KEEP_PLAYING_BOX, (190, 30, 60))
    return paint(rgb, screens.ACCEPT_LOSS_BOX, (200, 190, 40))


def winner_screens():
    """The winner notice in both phases of its CONTINUE button (grey, and the green phase of fix #141)."""
    out = []
    for colour in ((176, 176, 176), (144, 208, 128)):
        rgb = board_screen()
        paint(rgb, screens.NOTICE_PANEL, (10, 10, 100))
        out.append(paint(rgb, screens.CONTINUE_BOX, colour))
    return out


def card_award_screen():
    """A card award's CONTINUE: the smaller grey button near 402,531 on the board."""
    return paint(board_screen(), (370, 520, 64, 24), (176, 176, 176))


class OfferScreenTest(unittest.TestCase):
    """Fix #175: the detector of the card trade-in offer (boardview.offer_up), on painted arrays. The
    constants are traced to the real frames by name and sha256 in boardview.py."""

    def census(self):
        return (("board", board_screen()), ("board with the turn menu", menu_board()),
                ("board with the placement row", placement_row_board()), ("elimination notice", notice_screen()),
                ("winner notice, grey", winner_screens()[0]), ("winner notice, green", winner_screens()[1]),
                ("card award", card_award_screen()), ("title", title_screen()),
                ("scoreboard", scoreboard_screen()), ("game options", options_screen()), ("blank", blank()))

    def test_the_offer_is_taken_for_the_offer(self):
        self.assertTrue(boardview.offer_up(offer_screen()))

    def test_the_fixtures_are_the_screens_they_stand_for(self):
        # the negatives mean something only if the screen reader names them as the screens they stand for
        self.assertEqual(screens.name_of(board_screen().tobytes()), "board")
        self.assertEqual(screens.name_of(menu_board().tobytes()), "board-menu")
        self.assertEqual(screens.name_of(placement_row_board().tobytes()), "board")
        self.assertEqual(screens.name_of(notice_screen().tobytes()), "eliminated")
        self.assertEqual([screens.name_of(rgb.tobytes()) for rgb in winner_screens()], ["game-over", "game-over"])
        self.assertEqual(screens.name_of(title_screen().tobytes()), "title")
        self.assertEqual(screens.name_of(scoreboard_screen().tobytes()), "scoreboard")
        # and the screen reader sees the offer as the board it sits on: the loop's old blind spot (fix #175)
        self.assertEqual(screens.name_of(offer_screen().tobytes()), "board")

    def test_no_other_screen_is_taken_for_the_offer(self):
        for name, rgb in self.census():
            with self.subTest(screen=name):
                self.assertFalse(boardview.offer_up(rgb))

    def test_one_button_alone_is_not_the_offer(self):
        red_only = board_screen()
        paint(red_only, (421, 514, 92, 22), (176, 16, 16))
        green_only = board_screen()
        paint(green_only, (289, 514, 92, 22), (0, 176, 32))
        wrong_colours = board_screen()                      # a green button on the right, a red one on the left
        paint(wrong_colours, (421, 514, 92, 22), (0, 176, 32))
        paint(wrong_colours, (289, 514, 92, 22), (176, 16, 16))
        for name, rgb in (("red only", red_only), ("green only", green_only), ("swapped", wrong_colours)):
            with self.subTest(screen=name):
                self.assertFalse(boardview.offer_up(rgb))

    def test_the_minimums_sit_between_the_measured_populations(self):
        # 2006 red and 2071 green on the offer frames; at most 301 red and 23 green on every other frame
        self.assertTrue(301 < boardview.OFFER_RED_MINIMUM < 2006)
        self.assertTrue(23 < boardview.OFFER_GREEN_MINIMUM < 2071)

    def test_the_decline_point_is_inside_the_red_button_and_outside_the_green_one(self):
        x, y = boardview.DECLINE_POINT
        rx, ry, rw, rh = boardview.OFFER_RED_BOX
        gx, gy, gw, gh = boardview.OFFER_GREEN_BOX
        self.assertTrue(rx <= x < rx + rw and ry <= y < ry + rh)
        self.assertFalse(gx <= x < gx + gw)

    def test_the_frame_reader_says_whether_the_offer_is_up_from_the_one_capture(self):
        for rgb, expect in ((offer_screen(), True), (board_screen(), False)):
            reader = boardview.FrameReader(lambda rgb=rgb: (rgb, "d" * 64), TEMPLATES)
            reading = reader.read()
            self.assertEqual((reading.offer, reading.sha256), (expect, "d" * 64))
            self.assertEqual(reader.shots, 1)

    def test_a_reading_built_without_the_flag_has_no_offer(self):
        self.assertFalse(boardview.Reading({}, "s" * 64, "blue", False, 0).offer)


def panel_screen():
    """The placement panel as the detector sees it: a board with the four grey buttons (173, 165, 165 on the
    real frame) in the row. Painted to about the pixel count the real frames show (2100 to 2399)."""
    rgb = board_screen()
    for x in (267, 355, 404, 460):
        paint(rgb, (x, 531, 36, 22), (173, 165, 165))
    return rgb


def turn_menu_screen():
    """The turn menu in the same row: the menu board with its cyan label and the green CARD button (a row
    of other colours, none of them the buttons' grey)."""
    rgb = menu_board()
    paint(rgb, (300, 531, 60, 22), (8, 206, 66))
    paint(rgb, (400, 531, 60, 22), (200, 176, 64))
    return rgb


class PanelScreenTest(unittest.TestCase):
    """Fix #182: the placement panel's test is E020's own placement-row test, as a pixel count."""

    def test_the_constants_are_e020s_place_select_test(self):
        # the loop's PLACE_SELECT and PLACE_WATCH are the click-until? test of E020's block `place`
        import e021_loop
        self.assertEqual(e021_loop.PLACE_SELECT.split(" {x}")[0],
                         "click-until? %d %d %d %d %d" % (*boardview.PANEL_GREY, boardview.PANEL_TOLERANCE,
                                                           boardview.PANEL_MINIMUM))
        self.assertEqual(e021_loop.PLACE_WATCH, "watch %d %d %d %d" % boardview.PANEL_ROW)

    def test_the_panel_is_up_on_the_buttons_grey_and_down_on_the_turn_menu(self):
        self.assertTrue(boardview.panel_up(panel_screen()))
        self.assertFalse(boardview.panel_up(turn_menu_screen()))
        self.assertFalse(boardview.panel_up(board_screen()))
        self.assertFalse(boardview.panel_up(offer_screen()))
        self.assertFalse(boardview.panel_up(blank()))

    def test_a_continue_notice_in_the_same_row_is_not_the_panel(self):
        # the winner notice's and the Scoreboard's one wide grey CONTINUE button (x 328-477) is grey in the
        # row too, 1458 pixels on the real winner frame, over the panel's black gap
        rgb = board_screen()
        paint(rgb, (328, 523, 150, 25), (168, 168, 168))
        self.assertGreaterEqual(boardview.gold_count(rgb, boardview.PANEL_ROW, boardview.PANEL_GREY,
                                                     boardview.PANEL_TOLERANCE), boardview.PANEL_MINIMUM)
        self.assertFalse(boardview.panel_up(rgb))

    def test_the_minimum_separates_the_two(self):
        rgb = blank()
        x, y, w, _h = boardview.PANEL_ROW
        flat = rgb[y:y + 10, x:x + w].reshape(-1, 3)
        flat[:boardview.PANEL_MINIMUM] = boardview.PANEL_GREY
        rgb[y:y + 10, x:x + w] = flat.reshape(10, w, 3)
        self.assertTrue(boardview.panel_up(rgb))
        flat[boardview.PANEL_MINIMUM - 1] = (0, 0, 0)
        rgb[y:y + 10, x:x + w] = flat.reshape(10, w, 3)
        self.assertFalse(boardview.panel_up(rgb))

    def test_the_frame_reader_says_whether_the_panel_is_up_from_the_one_capture(self):
        for rgb, expect in ((panel_screen(), True), (turn_menu_screen(), False)):
            reader = boardview.FrameReader(lambda rgb=rgb: (rgb, "d" * 64), TEMPLATES)
            self.assertEqual(reader.read().panel, expect)
            self.assertEqual(reader.shots, 1)

    def test_a_reading_built_without_the_flag_has_no_panel(self):
        self.assertFalse(boardview.Reading({}, "s" * 64, "blue", False, 0).panel)


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
