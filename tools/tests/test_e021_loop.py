"""T45: the Session A player (experiments/E021-pro-session-a/e021_loop.py), offline.

A synthetic game (tools/tests/e021_fixtures.py FakeGame) stands behind a fake click-driver and a
fake board reader: no wine, no display, no PNG of the game (rule 18). The game answers the attack
flow as F011's reading says the human's attack goes, so these tests pin what the player sends and
what it records, never what the real game does (that is the main session's sittings, DW2 and DW3).
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "tests"))
import e021_fixtures as fx  # noqa: E402  (puts E020 and E021 on sys.path)
import e020_loop  # noqa: E402
import e021_loop  # noqa: E402

BLUE, RED = fx.BLUE, fx.RED
ALL = fx.all_met()


def only(*cells):
    """Every cell met but `cells`: the loop works on those alone."""
    return ALL - set(cells)


class World:
    def __init__(self, cells, screen="board", met=(), losers=(), per_click=1, unread=0, fail=None,
                 seconds=60, games_max=1):
        self.game = fx.FakeGame(fx.board(cells), screen=screen, losers=losers, per_click=per_click)
        self.driver = fx.FakeDriver(self.game)
        self.reader = fx.FakeReader(self.game, unread=unread, fail=fail)
        self.loop = e021_loop.SessionALoop(self.driver, {"games_max": games_max, "sitting_seconds": seconds},
                                           clock=lambda: 0, sleep=lambda s: None, reader=self.reader,
                                           adjacency=fx.ADJ, points=fx.POINTS, met=met)
        self.loop.deadline = seconds

    def attempts(self):
        return self.driver.events("attack-attempt")

    def met(self, case):
        return [row["cell"] for row in self.driver.events("case-met") if row["case"] == case]


class NewGameTest(unittest.TestCase):
    """Done-when 1: the player never sends New Game except on the title (E020's rule, reused)."""

    def test_the_games_and_their_new_game_rule_are_e020s_own(self):
        for name in ("run", "games", "play_game", "off_board", "continue_after_game_over",
                     "leave_scoreboard", "restore_shipped_skr", "send"):
            self.assertIs(getattr(e021_loop.SessionALoop, name), getattr(e020_loop.BatchLoop, name), name)

    def test_new_game_is_sent_from_the_title_only(self):
        for screen in ("board", "board-menu", "scoreboard", "game-over", "eliminated", "unknown", "title"):
            with self.subTest(screen=screen):
                world = World({3: (BLUE, 2), 4: (RED, 1)}, screen=screen, met=ALL)
                world.loop.play_game = lambda: "synthetic-stop"
                world.loop.run()
                self.assertEqual(world.driver.blocks.count("new-game"), int(screen == "title"))

    def test_a_game_that_ends_on_the_board_is_never_followed_by_new_game(self):
        # a whole game from the title: the turn ends the sitting (unknown screen after PASS), and
        # the next game is not started from the board it left
        world = World({3: (BLUE, 2), 4: (RED, 1)}, screen="title", met=ALL, games_max=3)
        world.game.after_pass = "unknown"
        world.loop.run()
        self.assertEqual(world.driver.blocks.count("new-game"), 1)
        self.assertEqual(world.loop.summary["ended"], "unknown-screen")


class AttackFlowTest(unittest.TestCase):
    def test_an_attack_is_open_target_attacker_exchange_then_leave(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=only(("even", 1)), losers=["d"])
        world.game.reinforcements = 0
        self.assertIsNone(world.loop.turn())
        order = [b for b in world.driver.blocks if b in ("attack-open", "exchange", "leave-battle", "pass")]
        self.assertEqual(order[:3], ["attack-open", "exchange", "leave-battle"])
        self.assertEqual(order[-1], "pass")
        self.assertEqual([c for c in world.driver.country_clicks()],
                         [("attack-target", 4), ("attack-attacker", 3)])

    def test_the_even_cell_is_met_by_the_battle_and_left_by_the_quit_attack_button(self):
        # attacker 4 against 5 (even cell 7, N+1); the synthetic gate refuses it, so use 4 vs 4
        world = World({3: (BLUE, 4), 4: (RED, 4)}, met=only(("even", 6), ("quit", 1)), losers=["d"])
        world.game.reinforcements = 0
        world.loop.turn()
        self.assertEqual(world.met("even"), [6])
        self.assertEqual(world.met("quit"), [1])
        (attempt,) = world.attempts()
        self.assertEqual(attempt["outcome"], "quit")
        self.assertEqual(attempt["clicks"], 1)
        self.assertEqual(attempt["before"], [4, BLUE, 4, RED])
        self.assertEqual(attempt["after"], [4, BLUE, 3, RED])
        (click,) = world.driver.events("exchange-click")
        self.assertEqual(click["lost"], 1)
        self.assertEqual(world.loop.summary["clicks_one_army"], 1)

    def test_a_refused_attacker_of_one_is_the_tiny_observation(self):
        world = World({3: (BLUE, 1), 4: (RED, 1)}, met=only(("tiny", 1)))
        world.game.reinforcements = 0
        world.loop.turn()
        self.assertEqual(world.met("tiny"), [1])
        (attempt,) = world.attempts()
        self.assertEqual(attempt["outcome"], "attacker-refused")
        self.assertFalse(attempt["battle"])
        self.assertIn("attack-cancel", world.driver.blocks)
        self.assertNotIn("exchange", world.driver.blocks)
        self.assertEqual([row["battle"] for row in world.driver.events("case-met")], [0])

    def test_an_underdog_order_is_sent_and_its_refusal_recorded(self):
        world = World({3: (BLUE, 4), 4: (RED, 9)}, met=only(("underdog", 1)))
        world.game.reinforcements = 0
        world.loop.turn()
        self.assertEqual(world.met("underdog"), [1])
        self.assertEqual(world.attempts()[0]["outcome"], "attacker-refused")
        self.assertEqual(world.loop.summary["refusals"], 1)

    def test_a_refused_target_meets_no_cell(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=only(("even", 1)))
        world.game.reinforcements = 0
        world.game.adjacency = {}               # the game takes no target the player names
        world.loop.turn()
        self.assertEqual(world.attempts()[0]["outcome"], "target-refused")
        self.assertEqual(world.driver.events("case-met"), [])
        self.assertEqual(world.driver.country_clicks(), [("attack-target", 4)])

    def test_a_failed_attack_meets_one_lost_cell_and_sends_nothing_more_that_turn(self):
        world = World({3: (BLUE, 3), 4: (RED, 3)}, met=only(("lost", 1), ("lost", 2)), losers=["a", "a"])
        world.game.reinforcements = 0
        self.assertIsNone(world.loop.turn())
        self.assertEqual(world.met("lost"), [1])
        (attempt,) = world.attempts()
        self.assertEqual(attempt["outcome"], "forfeit")
        self.assertEqual(attempt["after"], [1, RED, 3, RED])
        self.assertEqual(attempt["seat_after"], RED)
        self.assertNotIn("pass", world.driver.blocks)
        self.assertNotIn("leave-battle", world.driver.blocks)
        self.assertEqual([c["lost"] for c in world.driver.events("exchange-click")], [1, 1])
        self.assertEqual(world.driver.events("turn-end")[-1]["end"], "forfeit")

    def test_a_capture_is_left_by_done_and_its_exchanges_come_from_the_conserved_total(self):
        world = World({3: (BLUE, 6), 4: (RED, 2)}, met=only(("lost", 1)), losers=["a", "d", "d"])
        world.game.reinforcements = 0
        world.loop.turn()
        (attempt,) = world.attempts()
        self.assertEqual(attempt["outcome"], "capture")
        self.assertEqual(attempt["clicks"], 3)
        self.assertEqual(attempt["lost"], 3)
        self.assertEqual(attempt["after"], [4, BLUE, 1, BLUE])       # 1 moved in after DONE
        clicks = world.driver.events("exchange-click")
        self.assertEqual([c["lost"] for c in clicks], [1, 1, 1])
        self.assertTrue(clicks[-1]["moved_in"])
        self.assertEqual(world.met("lost"), [])
        self.assertIn("pass", world.driver.blocks)

    def test_a_click_that_resolves_two_exchanges_is_logged_as_such(self):
        # DW3's hazard: the player records the number, never works around it
        world = World({3: (BLUE, 8), 4: (RED, 8)}, met=only(("even", 10)), losers=["a", "d"], per_click=2)
        world.game.reinforcements = 0
        world.loop.turn()
        (click,) = world.driver.events("exchange-click")
        self.assertEqual(click["lost"], 2)
        self.assertEqual(world.loop.summary["clicks_several_armies"], 1)
        self.assertEqual(world.loop.summary["clicks_one_army"], 0)

    def test_a_turn_of_three_battles_meets_one_busy_cell_with_what_ended_it(self):
        adjacency = {3: {4, 5, 6}, 4: {3}, 5: {3}, 6: {3}}
        world = World({3: (BLUE, 9), 4: (RED, 1), 5: (RED, 1), 6: (RED, 1)},
                      met=only(("busy", 1), ("busy", 2), ("quit", 1), ("quit", 2)))
        world.game.adjacency = adjacency
        world.loop.adjacency = adjacency
        world.game.reinforcements = 0
        world.loop.turn()
        self.assertEqual(len([a for a in world.attempts() if a["battle"]]), 3)
        self.assertEqual(world.met("busy"), [1])
        end = world.driver.events("turn-end")[-1]
        self.assertEqual((end["battles"], end["end"]), (3, "pass"))

    def test_refusals_never_count_towards_a_busy_turn(self):
        adjacency = {3: {4, 5, 6}, 4: {3}, 5: {3}, 6: {3}}
        world = World({3: (BLUE, 2), 4: (RED, 9), 5: (RED, 9), 6: (RED, 9)},
                      met=only(("busy", 1), ("lost", 1)))
        world.game.adjacency = adjacency
        world.loop.adjacency = adjacency
        world.game.reinforcements = 0
        world.loop.turn()
        self.assertEqual(world.met("busy"), [])

    def test_the_attack_button_not_answering_ends_the_attack_phase_with_a_pass(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=only(("even", 1)))
        world.game.reinforcements = 0
        world.game.attack_button_works = False
        self.assertIsNone(world.loop.turn())
        self.assertEqual(world.attempts()[0]["outcome"], "no-menu")
        self.assertEqual(world.driver.country_clicks(), [])
        self.assertEqual(world.driver.blocks[-1], "pass")

    def test_with_nothing_needed_the_turn_places_and_passes_without_attacking(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=ALL)
        self.assertIsNone(world.loop.turn())
        self.assertNotIn("attack-open", world.driver.blocks)
        self.assertEqual(world.driver.blocks[-2:], ["place-commit", "pass"])

    def test_every_country_clicked_is_a_pair_of_the_board(self):
        # an attacker is always the human's and borders its target, which is another seat's
        adjacency = {1: {2}, 2: {1, 3}, 3: {2, 4}, 4: {3, 5}, 5: {4}}
        world = World({1: (RED, 5), 2: (BLUE, 3), 3: (BLUE, 6), 4: (RED, 2), 5: (RED, 1)},
                      met=only(("lost", 1), ("lost", 2), ("quit", 1)), losers=["d"] * 10)
        world.game.adjacency = adjacency
        world.loop.adjacency = adjacency
        world.loop.turn()
        for attempt in world.attempts():
            a, d = attempt["attacker"], attempt["defender"]
            self.assertIn(d, adjacency[a])
            self.assertEqual(attempt["before"][1], BLUE)
            self.assertNotEqual(attempt["before"][3], BLUE)


class PlacementTest(unittest.TestCase):
    def test_all_reinforcements_go_on_the_frontier_country(self):
        # blue 3 at 2 next to red 4 at 3: even cell 5 is attacker 4 vs 3, two away
        world = World({3: (BLUE, 2), 4: (RED, 3)}, met=only(("even", 5)))
        world.game.reinforcements = 2
        world.loop.turn()
        self.assertEqual(world.driver.events("place-target")[0]["country"], 3)
        self.assertEqual(world.attempts()[0]["before"][0], 4)
        self.assertEqual(world.met("even"), [5])

    def test_a_stack_that_already_shows_its_size_is_not_grown_past_it(self):
        adjacency = {1: {2}, 2: {1}, 3: {4}, 4: {3}}
        world = World({1: (BLUE, 5), 2: (RED, 9), 3: (BLUE, 2), 4: (RED, 1)}, met=only(("even", 1)))
        world.game.adjacency = adjacency
        world.loop.adjacency = adjacency
        world.loop.turn()
        self.assertEqual(world.driver.events("place-target")[0]["country"], 1)
        self.assertEqual(world.attempts()[0]["before"][0], 2)
        self.assertEqual(world.met("even"), [1])

    def test_a_country_that_cannot_be_selected_falls_back_to_e020s_placement(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=ALL)
        original = world.driver.run_step

        def refuse(block, step):
            if block == "place-select" and step.op == "click-until?":
                world.driver.steps.append((block, step.op, tuple(step.args)))
                return {"picked": None}
            return original(block, step)
        world.driver.run_step = refuse
        self.assertIsNone(world.loop.turn())
        self.assertEqual(world.driver.blocks[:4], ["dismiss", "quiet", "place-any", "place-commit"])


class ReadingTest(unittest.TestCase):
    def test_an_unreadable_board_ends_the_sitting_cleanly_with_no_click(self):
        for kwargs in ({"unread": 7}, {"fail": FileNotFoundError("no templates")}):
            with self.subTest(**{k: str(v) for k, v in kwargs.items()}):
                world = World({3: (BLUE, 2), 4: (RED, 1)}, **kwargs)
                self.assertEqual(world.loop.turn(), "board-unreadable")
                self.assertEqual(world.driver.blocks, [])
                self.assertEqual(world.driver.steps, [])
                self.assertTrue(world.loop.summary["ended"].startswith("board-unreadable"))

    def test_a_few_unread_countries_are_tolerated(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=ALL, unread=6)
        self.assertIsNone(world.loop.turn())

    def test_the_click_states(self):
        state = e021_loop.SessionALoop.state
        before = fx.board({3: (BLUE, 5), 4: (RED, 3)})
        cases = {"on": {3: (BLUE, 4), 4: (RED, 3)}, "no-change": {3: (BLUE, 5), 4: (RED, 3)},
                 "capture": {3: (BLUE, 5), 4: (BLUE, 0)}, "forfeit": {3: (RED, 1), 4: (RED, 3)},
                 "pending": {3: (BLUE, 1), 4: (RED, 3)}}
        for want, cells in cases.items():
            self.assertEqual(state(before, fx.board(cells), 3, 4), want)
        unread = fx.board({4: (RED, 3)})
        unread[3] = {"army": None, "owner": None}
        self.assertEqual(state(before, unread, 3, 4), "unread")


class DeadlineTest(unittest.TestCase):
    def test_synthesised_clicks_recheck_the_deadline(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)})
        world.loop.deadline = 0
        with self.assertRaises(e020_loop.TimeUp):
            world.loop.send_step("attack-target", "click 40 40")
        self.assertEqual(world.driver.steps, [])

    def test_a_step_outside_the_click_drivers_list_is_refused(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)})
        with self.assertRaises(ValueError):
            world.loop.send_step("attack-target", "attack-picked 40 40")
        self.assertEqual(world.driver.steps, [])


if __name__ == "__main__":
    unittest.main()
