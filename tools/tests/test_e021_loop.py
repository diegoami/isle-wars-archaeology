"""Offline Session A player tests: synthetic reads and a fake click-driver only."""
import unittest

import e021_fixtures as fx
import e021_loop
import e020_loop


class LoopTest(unittest.TestCase):
    def loop(self, screen="board", met=()):
        driver = fx.FakeDriver(screen)
        board = fx.frontier_board()
        loop = e021_loop.SessionALoop(driver, {"games_max": 1, "sitting_seconds": 60},
                                     clock=lambda: 0, reader=fx.FakeReader([board]),
                                     adjacency=fx.ADJ, points={3: (100, 100), 4: (200, 100)},
                                     met=met)
        loop.deadline = 60
        return loop, driver, board

    def test_new_game_only_on_title(self):
        for screen in ("board", "board-menu", "scoreboard", "unknown", "title"):
            with self.subTest(screen=screen):
                loop, driver, _ = self.loop(screen)
                loop.play_game = lambda: "synthetic-stop"
                loop.run()
                self.assertEqual(driver.blocks.count("new-game"), int(screen == "title"))

    def test_synthetic_clicks_recheck_deadline(self):
        loop, driver, _ = self.loop()
        loop.deadline = 0
        with self.assertRaises(e020_loop.TimeUp):
            loop.send_step("attack-exchange", "click 337 531")
        self.assertEqual(driver.steps, [])

    def test_placement_uses_inherited_send_interface(self):
        loop, driver, board = self.loop()
        self.assertTrue(loop.place_for(board))
        self.assertIn("place-commit", driver.blocks)

    def test_refusals_do_not_credit_busy_turns(self):
        loop, driver, board = self.loop()
        loop.attack_once = lambda b, *args: ("refused", b)
        loop.attack_phase(board)
        self.assertEqual(driver.events("case-met"), [])

    def test_failed_attack_credits_only_one_lost_cell(self):
        loop, driver, board = self.loop()
        after = fx.frontier_board()
        after[3]["army"] = 1
        loop.reader.changes = [after]
        loop.exchange(board, "lost", 1, 3, 4, (board[3], board[4]), "e" * 64)
        lost = [row for row in driver.events("case-met") if row["case"] == "lost"]
        self.assertEqual(len(lost), 1)

    def test_quit_attempt_credits_only_one_quit_cell(self):
        loop, driver, board = self.loop()
        loop.attack_once(board, "quit", 1, 3, 4)
        quit_rows = [row for row in driver.events("case-met") if row["case"] == "quit"]
        self.assertEqual(len(quit_rows), 1)

    def test_size_probe_refusal_is_an_observation(self):
        loop, driver, board = self.loop()
        loop.reader.ready = False
        loop.attack_once(board, "tiny", 1, 3, 4)
        self.assertIn(("tiny", 1), loop.met)

    def test_failed_attack_ends_turn_not_game(self):
        loop, driver, board = self.loop()
        loop.attack_phase = lambda b: "forfeit"
        self.assertIsNone(loop.after_placement())
        self.assertNotIn("pass", driver.blocks)
