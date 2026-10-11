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
YELLOW = "yellow"
GREEN = "green"
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
        # `games` is no longer on this list: fix #171 overrides it, for the Game Options case only
        # (OptionsAfterAbandonTest holds every other path to E020's behaviour)
        for name in ("run", "play_game", "off_board", "continue_after_game_over",
                     "leave_scoreboard", "restore_shipped_skr", "send"):
            self.assertIs(getattr(e021_loop.SessionALoop, name), getattr(e020_loop.BatchLoop, name), name)

    def test_new_game_is_sent_from_the_title_or_by_the_no_fit_abandon_only(self):
        # Done-when 1 as amended 2026-10-11: the setup block runs only on the title, and the one
        # New Game sent from a board is the no-fit abandon's, on the board-menu, after its line
        source = (fx.ROOT / "experiments" / "E021-pro-session-a" / "e021_loop.py").read_text()
        self.assertEqual(source.count('self.send("abandon-game")'), 1)
        self.assertNotIn('self.send("new-game")', source)          # the one send is `self.send(block)`
        # fix #171: the games() override sends `new-game` only for a game that starts from the title
        # (the screen it read is not the Game Options screen); the Game Options screen gets options-play
        self.assertEqual(source.count('"new-game"'), 1)
        self.assertEqual(source.count('block = "options-play" if screen == OPTIONS else "new-game"'), 1)
        self.assertEqual(source.count("self.send(block)"), 1)

    def test_options_play_sends_no_new_game(self):
        # fix #171: block options-play holds only the clicks of new-game after its first one (the same
        # points, none new), and never new-game's own first click, 100,585, which is New Game
        from driver.clicks import parse_blocks
        blocks = parse_blocks((fx.ROOT / "experiments" / "E021-pro-session-a" / "session-a.steps").read_text())

        def points(name):
            return [tuple(step.args) for step in blocks[name] if step.op in ("click", "click!")]
        self.assertEqual(points("options-play"), points("new-game")[1:])
        self.assertEqual(points("options-play"), [(533, 311), (565, 532)])
        self.assertNotIn((100, 585), points("options-play"))
        source = (fx.ROOT / "experiments" / "E021-pro-session-a" / "e021_loop.py").read_text()
        self.assertEqual(source.count('"abandon-game"'), 1)         # the abandon is still the one New Game from a board

    def test_card_decline_sends_no_new_game(self):
        # fix #175: block card-decline is one plain click on the trade offer's decline button, never New
        # Game's point (100,585), and the loop sends no other New Game for it
        from driver.clicks import parse_blocks
        import boardview
        blocks = parse_blocks((fx.ROOT / "experiments" / "E021-pro-session-a" / "session-a.steps").read_text())
        ops = [(step.op, tuple(step.args)) for step in blocks["card-decline"]]
        self.assertEqual(ops, [("watch", (262, 502, 276, 70)), ("click", boardview.DECLINE_POINT)])
        self.assertNotEqual(boardview.DECLINE_POINT, (100, 585))
        source = (fx.ROOT / "experiments" / "E021-pro-session-a" / "e021_loop.py").read_text()
        self.assertEqual(source.count('self.send("abandon-game")'), 1)
        self.assertEqual(source.count('"new-game"'), 1)
        self.assertEqual(source.count('self.send("card-decline")'), 1)

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


class NoFitAbandonTest(unittest.TestCase):
    """Done-when 1 (amended 2026-10-11): NO_FIT_TURNS turns in a row of one game with no needed cell
    on the board and no attack opened abandon the game; fewer, or a fit in between, do not."""

    def world(self, met=ALL, games_max=2, restore=True):
        world = World({3: (BLUE, 20), 4: (GREEN, 30)}, screen="title", met=met, games_max=games_max)
        world.game.board_screen = "board-menu"
        world.game.reinforcements = 0
        if restore:
            world.loop.restore, world.loop.shipped_skr = (lambda: "s" * 64), "s" * 64
        return world

    def test_three_no_fit_turns_abandon_the_game_and_the_next_starts_from_the_title(self):
        world = self.world()
        world.loop.run()
        abandoned = world.driver.events("game-abandoned")
        self.assertEqual([(a["game"], a["turn"], a["reason"], a["turns"]) for a in abandoned],
                         [(1, 3, "no-fit", 3), (2, 3, "no-fit", 3)])
        self.assertEqual(world.game.games, 2)
        self.assertEqual(world.driver.blocks.count("abandon-game"), 2)
        self.assertEqual(world.game.passes, 4)                     # turns 1 and 2 of each game
        events = [n["event"] for n in world.driver.notes if n.get("event") in
                  ("game-abandoned", "loss-credited", "skr-restored", "game-start", "game-end")]
        self.assertEqual(events, ["game-start", "game-abandoned", "game-end", "loss-credited",
                                  "skr-restored", "game-start", "game-abandoned", "game-end",
                                  "loss-credited"])
        self.assertEqual(world.loop.summary["ended"], "games-max")
        self.assertEqual(world.loop.summary["abandoned"], 2)

    def test_two_no_fit_turns_and_then_a_fit_do_not_abandon(self):
        world = self.world(met=only(("even", 1)), games_max=1, restore=False)
        world.game.screen = "board-menu"
        world.loop.deadline = 60
        world.loop.driver.context = {"game": 1, "turn": 0}

        def fit_after_two(game):
            if game.passes == 2:               # the computers leave blue a 2 next to a red 1
                game.board[5] = {"army": 2, "owner": BLUE}
                game.board[6] = {"army": 1, "owner": RED}
        world.game.on_pass = fit_after_two
        world.game.adjacency = world.loop.adjacency = {**fx.ADJ, 5: {6}, 6: {5}}
        world.loop.points = {**fx.POINTS}
        for turn in (1, 2, 3, 4, 5):
            world.loop.driver.context = {"game": 1, "turn": turn}
            world.loop.turn()
        self.assertEqual(world.driver.events("game-abandoned"), [])
        self.assertNotIn("abandon-game", world.driver.blocks)
        self.assertEqual([a["attacker"] for a in world.attempts()], [5])     # turn 3 attacked

    def test_the_count_is_per_game(self):
        world = self.world(games_max=1)
        world.loop.no_fit = (0, 2)              # two no-fit turns of an earlier game
        world.loop.driver.context = {"game": 1, "turn": 1}
        self.assertFalse(world.loop.abandon_due())

    def test_on_a_board_without_its_menu_row_the_turn_passes_instead(self):
        world = self.world(games_max=1)
        world.loop.deadline = 60
        world.game.screen = "board"
        world.loop.no_fit = (1, 2)
        world.loop.driver.context = {"game": 1, "turn": 3}
        self.assertIsNone(world.loop.turn())
        self.assertNotIn("abandon-game", world.driver.blocks)
        self.assertEqual(world.driver.events("game-abandoned"), [])
        self.assertEqual(world.game.passes, 1)

    def test_a_screen_other_than_the_scoreboard_after_the_click_ends_the_sitting_cleanly(self):
        # F003: with 10 or more human countries the Scoreboard may not show
        world = self.world(games_max=2)
        world.game.after_abandon = "unknown"
        world.loop.run()
        self.assertEqual(world.game.games, 1)
        self.assertEqual(world.loop.summary["ended"], "unknown-screen")


class OptionsAfterAbandonTest(unittest.TestCase):
    """Fix #171: an abandon whose New Game goes straight to the Game Options screen (no Scoreboard, no
    loss: sitting 20261011T142906Z, game 2 turn 3) carries on instead of ending the sitting."""

    def world(self, games_max=2, restore=True):
        world = World({3: (BLUE, 20), 4: (GREEN, 30)}, screen="title", met=ALL, games_max=games_max)
        world.game.board_screen = "board-menu"
        world.game.reinforcements = 0
        world.game.after_abandon = "game-options"
        if restore:
            world.loop.restore, world.loop.shipped_skr = (lambda: "s" * 64), "s" * 64
        return world

    def test_game_options_after_an_abandon_ends_the_game_and_starts_the_next_through_options_play(self):
        world = self.world()
        world.loop.run()
        events = [(n["event"], n.get("reason")) for n in world.driver.notes if n.get("event") in
                  ("game-abandoned", "loss-credited", "skr-restored", "game-start", "game-end")]
        self.assertEqual(events, [("game-start", None), ("game-abandoned", "no-fit"),
                                  ("game-end", "abandoned-no-scoreboard"), ("skr-restored", None),
                                  ("game-start", None), ("game-abandoned", "no-fit"),
                                  ("game-end", "abandoned-no-scoreboard")])
        blocks = world.driver.blocks
        self.assertEqual(blocks.count("new-game"), 1)                  # game 1, from the title only
        self.assertEqual(blocks.count("options-play"), 1)              # game 2, from the options screen
        self.assertEqual(blocks.count("abandon-game"), 2)
        self.assertNotIn("scoreboard-continue", blocks)
        start = blocks.index("options-play")
        self.assertEqual(blocks[start - 1], "abandon-game")
        self.assertEqual(blocks[start + 1], "quiet")                   # then as after new-game
        self.assertEqual(world.game.games, 2)                          # the second game started and played
        self.assertEqual(world.game.passes, 4)                         # turns 1 and 2 of each game
        self.assertEqual(world.loop.summary["ended"], "games-max")
        self.assertEqual(world.loop.summary["abandoned"], 2)
        self.assertNotIn("loss_credited", world.loop.summary)

    def test_every_game_after_a_credited_loss_has_its_own_restore_line_first(self):
        # the exporter's check (e020_export.games_after_loss): a game after a credited loss is proved
        # only by a restore line that names that game; game 1 credits a loss, games 2 and 3 are started
        # (the second from the options screen), and each is preceded by its own restore line
        world = self.world(games_max=3)
        screens = iter(["scoreboard", "game-options", "game-options"])
        original = world.game.block

        def block(name):
            out = original(name)
            if name == "abandon-game" and out.get("changed"):
                world.game.screen = next(screens)
            return out
        world.game.block = block
        world.loop.run()
        lines = [(n["event"], n.get("game")) for n in world.driver.notes if n.get("event") in
                 ("loss-credited", "skr-restored", "game-start")]
        self.assertEqual(lines, [("game-start", 1), ("loss-credited", 1), ("skr-restored", 2),
                                 ("game-start", 2), ("skr-restored", 3), ("game-start", 3)])

    def test_a_failed_restore_ends_the_sitting_before_options_play(self):
        world = self.world()
        world.loop.restore = lambda: "x" * 64
        world.loop.run()
        self.assertNotIn("options-play", world.driver.blocks)
        self.assertTrue(world.loop.summary["ended"].startswith("skr-restore-failed"))
        self.assertEqual(world.driver.events("skr-restored"), [])

    def test_an_unknown_screen_that_is_not_the_options_screen_still_ends_the_sitting(self):
        world = self.world()
        world.game.after_abandon = "unknown"
        world.loop.run()
        self.assertNotIn("options-play", world.driver.blocks)
        self.assertEqual(world.game.games, 1)
        self.assertEqual(world.loop.summary["ended"], "unknown-screen")

    def test_a_capture_that_cannot_be_read_ends_the_sitting_cleanly(self):
        world = self.world()

        def broken():
            raise RuntimeError("no capture")
        world.reader.options_screen = broken
        world.loop.run()
        self.assertNotIn("options-play", world.driver.blocks)
        self.assertEqual(world.loop.summary["ended"], "unknown-screen")
        self.assertEqual(world.driver.events("options-unread")[0]["reason"], "RuntimeError: no capture")

    def test_the_scoreboard_path_is_unchanged(self):
        world = self.world()
        world.game.after_abandon = "scoreboard"
        world.loop.run()
        self.assertEqual(world.driver.blocks.count("scoreboard-continue"), 2)
        self.assertEqual(len(world.driver.events("loss-credited")), 2)
        self.assertNotIn("options-play", world.driver.blocks)
        self.assertEqual([n["reason"] for n in world.driver.events("game-end")], ["scoreboard", "scoreboard"])


class GrowingStackTest(unittest.TestCase):
    """Fix #171: a turn whose placement grew a stack towards a needed attacker size is not a no-fit
    turn, as long as its gap keeps shrinking; a stack that stops growing counts again."""

    def world(self, reinforcements):
        # blue 3 holds 1 army next to red 4 with 8: the even cell 10 (attacker 8 vs 8) is the only
        # one needed, and the stack must grow by 7 first (the gap)
        world = World({3: (BLUE, 1), 4: (RED, 8)}, screen="board-menu", met=only(("even", 10)))
        world.game.reinforcements = reinforcements
        world.loop.deadline = 600
        return world

    def turn(self, world, number):
        world.loop.driver.context = {"game": 1, "turn": number}
        return world.loop.turn()

    def test_turns_with_a_shrinking_gap_do_not_abandon(self):
        world = self.world(2)
        for number in (1, 2, 3, 4):
            self.assertIsNone(self.turn(world, number))
        self.assertEqual([t["gap"] for t in world.driver.events("place-target")], [7, 5, 3, 1])
        self.assertEqual([t["growing"] for t in world.driver.events("turn-end")], [1, 1, 1, 1])
        self.assertEqual(world.driver.events("game-abandoned"), [])
        self.assertNotIn("abandon-game", world.driver.blocks)
        self.assertEqual(world.game.passes, 4)

    def test_a_gap_that_stops_shrinking_counts_and_abandons_after_no_fit_turns(self):
        world = self.world(2)
        for number in (1, 2, 3):                                     # gaps 7, 5, 3: growing
            self.assertIsNone(self.turn(world, number))
        world.game.reinforcements = 0                                # the stack stops growing
        self.assertIsNone(self.turn(world, 4))                       # gap 1: it did shrink since turn 3
        for number in (5, 6):
            self.assertIsNone(self.turn(world, number))              # gap 1 again: the 1st and 2nd no-fit turn
            self.assertNotIn("abandon-game", world.driver.blocks)
        self.turn(world, 7)
        self.assertEqual(e021_loop.NO_FIT_TURNS, 3)
        abandoned = world.driver.events("game-abandoned")
        self.assertEqual([(a["turn"], a["turns"]) for a in abandoned], [(7, 3)])
        self.assertEqual(world.driver.blocks.count("abandon-game"), 1)
        self.assertEqual([t["growing"] for t in world.driver.events("turn-end")], [1, 1, 1, 1, 0, 0, 0])

    def test_a_stack_that_never_grows_is_abandoned_on_the_fourth_turn(self):
        world = self.world(0)
        for number in (1, 2, 3):
            self.assertIsNone(self.turn(world, number))
        self.assertNotIn("abandon-game", world.driver.blocks)
        self.turn(world, 4)                                          # the 1st turn grew nothing new, but
        self.assertEqual(world.driver.events("game-abandoned")[0]["turn"], 4)   # is the country's first

    def test_the_gap_is_remembered_per_country_so_taking_turns_does_not_hide_a_stalled_stack(self):
        loop = self.world(0).loop
        loop.driver.context = {"game": 1, "turn": 1}
        self.assertTrue(loop.growing(3, 7))                          # new country
        self.assertTrue(loop.growing(5, 7))                          # another new country
        self.assertFalse(loop.growing(3, 7))                         # no smaller than its own best
        self.assertTrue(loop.growing(3, 6))
        self.assertFalse(loop.growing(3, 6))
        self.assertFalse(loop.growing(3, 0))                         # a stack at its size is not growing
        loop.driver.context = {"game": 2, "turn": 1}
        self.assertTrue(loop.growing(3, 7))                          # the list starts again each game


class AttackFlowTest(unittest.TestCase):
    def test_an_attack_is_open_target_attacker_exchange_then_leave(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=only(("even", 1)), losers=["d"])
        world.game.reinforcements = 0
        self.assertIsNone(world.loop.turn())
        order = [b for b in world.driver.blocks
                 if b in ("attack-open", "exchange", "quit-attack", "move-in-done", "pass")]
        self.assertEqual(order[:3], ["attack-open", "exchange", "move-in-done"])     # 2 vs 1 captured
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
        self.assertEqual(world.attempts()[0]["outcome"], "target-not-taken")
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
        self.assertNotIn("quit-attack", world.driver.blocks)
        self.assertNotIn("move-in-done", world.driver.blocks)
        # the reading that shows the hand-over already boxes the next seat: that click's count is
        # unknown (round 1's R2), the one before it is not
        self.assertEqual([c["lost"] for c in world.driver.events("exchange-click")], [1, None])
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

    def test_a_click_read_while_another_seat_is_boxed_has_no_count(self):
        # a reading whose score panel boxes another seat cannot be shown to hold the human's
        # battle alone: the click's count is unknown, wherever in the battle it comes
        world = World({3: (BLUE, 6), 4: (RED, 5)}, met=only(("lost", 1)), losers=["d", "d"])
        world.game.reinforcements = 0
        original = world.reader.read
        reads = []

        def read(seat=None):
            reads.append(1)
            reading = original(seat=seat)
            return reading._replace(seat=YELLOW) if world.game.phase == "battle" else reading
        world.reader.read = read
        world.reader.wait_settled = lambda before, countries, seconds: [read()]
        world.game.losers = ["d"] * 5
        world.loop.turn()
        clicks = world.driver.events("exchange-click")
        self.assertGreater(len(clicks), 1)
        self.assertTrue(all(c["lost"] is None for c in clicks[:-1]))
        self.assertTrue(all(not c["isolated"] for c in clicks[:-1]))
        self.assertEqual(world.loop.summary["clicks_one_army"], 1)     # the capture, read after DONE

    def test_a_quit_press_after_a_reading_without_the_battle_meets_no_quit_cell(self):
        world = World({3: (BLUE, 4), 4: (RED, 4)}, met=only(("even", 6), ("quit", 1)), losers=["d"])
        world.game.reinforcements = 0
        original = world.reader.wait_settled
        world.reader.wait_settled = lambda before, countries, seconds: [
            r._replace(battle=False) for r in original(before, countries, seconds)]
        world.loop.turn()
        self.assertEqual(world.met("even"), [6])
        self.assertEqual(world.attempts()[0]["outcome"], "quit")
        self.assertEqual(world.met("quit"), [])

    def test_a_quit_press_that_does_not_land_meets_no_cell_and_ends_the_sitting_cleanly(self):
        # round 2, point 1: sitting 20261011T070437Z read a press from a colour under the pointer;
        # the press is now confirmed by a reading (no battle panel, the counts unchanged)
        world = World({3: (BLUE, 4), 4: (RED, 4)}, met=only(("even", 6), ("quit", 1)), losers=["d"])
        world.game.reinforcements = 0
        world.game.quit_works = False
        self.assertEqual(world.loop.turn(), "battle-stuck")
        (attempt,) = world.attempts()
        self.assertEqual(attempt["outcome"], "quit-unconfirmed")
        self.assertEqual(world.met("quit"), [])
        self.assertEqual(world.loop.summary["quits"], 0)
        self.assertEqual([n["confirmed"] for n in world.driver.events("quit-attack")], [0])

    def test_a_confirmed_quit_meets_the_quit_cell_only_after_an_exchange_the_board_showed(self):
        world = World({3: (BLUE, 7), 4: (RED, 3)}, met=only(("quit", 1)))
        world.game.reinforcements = 0
        world.game.exchange_noop = True
        world.loop.turn()
        (attempt,) = world.attempts()
        self.assertEqual((attempt["outcome"], attempt["clicks"], attempt["fought"]), ("quit", 1, False))
        self.assertEqual(world.game.quits, 1)
        self.assertEqual(world.met("quit"), [])
        world = World({3: (BLUE, 7), 4: (RED, 3)}, met=only(("quit", 1)), losers=["a"])
        world.game.reinforcements = 0
        world.loop.turn()
        (attempt,) = world.attempts()
        self.assertEqual((attempt["outcome"], attempt["fought"]), ("quit", True))
        self.assertEqual(world.met("quit"), [1])

    def test_battles_with_no_exchange_the_board_showed_never_make_a_busy_turn(self):
        # round 2, point 2: three battles opened, clicked and left, the counts never moving
        adjacency = {3: {4, 5, 6}, 4: {3}, 5: {3}, 6: {3}}
        world = World({3: (BLUE, 9), 4: (RED, 1), 5: (RED, 1), 6: (RED, 1)},
                      met=only(("quit", 1), ("quit", 2), ("busy", 1)))
        world.game.adjacency = adjacency
        world.loop.adjacency = adjacency
        world.game.reinforcements = 0
        world.game.exchange_noop = True
        world.loop.turn()
        self.assertEqual([a["battle"] for a in world.attempts()], [True] * 3)
        end = world.driver.events("turn-end")[-1]
        self.assertEqual((end["battles"], end["fights"]), (3, 0))
        self.assertEqual(world.met("busy"), [])

    def test_a_case_whose_action_keeps_failing_is_dropped_for_the_sitting(self):
        # round 2, point 3: the game takes none of the targets; after DROP_AFTER failures in a row
        # the quit row is not aimed at again, and the log says so
        adjacency = {3: set(range(4, 11)), **{c: {3} for c in range(4, 11)}}
        world = World({3: (BLUE, 9), **{c: (RED, 1) for c in range(4, 11)}}, met=only(("quit", 1)))
        world.game.adjacency = {}
        world.loop.adjacency = adjacency
        world.game.reinforcements = 0
        world.loop.turn()
        self.assertEqual([a["outcome"] for a in world.attempts()], ["target-not-taken"] * e021_loop.DROP_AFTER)
        (dropped,) = world.driver.events("case-dropped")
        self.assertEqual((dropped["case"], dropped["failures"]), ("quit", e021_loop.DROP_AFTER))
        self.assertEqual(world.loop.summary["dropped"], ["quit"])
        world.loop.turn()                                  # the next turn aims at nothing
        self.assertEqual(len(world.attempts()), e021_loop.DROP_AFTER)

    def test_a_success_resets_the_failure_count(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)})
        for outcome in ("target-not-taken",) * (e021_loop.DROP_AFTER - 1):
            world.loop.track("quit", len(world.loop.met), outcome)
        world.loop.track("quit", len(world.loop.met), "capture")
        for outcome in ("target-not-taken",) * (e021_loop.DROP_AFTER - 1):
            world.loop.track("quit", len(world.loop.met), outcome)
        self.assertEqual(world.loop.dropped, set())
        world.loop.track("quit", len(world.loop.met), "unresolved")
        self.assertEqual(world.loop.dropped, {"quit"})

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
        # three orders the game refuses in one turn (attacker 4 against 5, 6 and 9: even cells 7
        # and 8, underdog cell 1), with the busy row still needed: no busy cell is met
        adjacency = {3: {4, 5, 6}, 4: {3}, 5: {3}, 6: {3}}
        world = World({3: (BLUE, 4), 4: (RED, 5), 5: (RED, 6), 6: (RED, 9)},
                      met=only(("even", 7), ("even", 8), ("underdog", 1), ("busy", 1)))
        world.game.adjacency = adjacency
        world.loop.adjacency = adjacency
        world.game.reinforcements = 0
        world.loop.turn()
        self.assertEqual([a["outcome"] for a in world.attempts()], ["attacker-refused"] * 3)
        self.assertEqual(world.game.refused, 3)
        self.assertEqual(world.driver.events("turn-end")[-1]["battles"], 0)
        self.assertEqual(world.met("busy"), [])
        self.assertEqual(sorted(world.met("even")), [7, 8])

    def test_an_unanswered_attacker_click_is_unresolved_and_meets_no_cell(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=only(("even", 1)))
        world.game.reinforcements = 0
        world.game.attacker_unanswered = True
        world.loop.turn()
        (attempt,) = world.attempts()
        self.assertEqual(attempt["outcome"], "unresolved")
        self.assertFalse(attempt["answered"])
        self.assertEqual(world.game.refused, 0)
        self.assertEqual(world.driver.events("case-met"), [])
        self.assertEqual(world.loop.summary["refusals"], 0)
        self.assertIn("attack-cancel", world.driver.blocks)

    def test_a_battle_the_probe_missed_meets_no_cell_and_ends_the_sitting_cleanly(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=only(("even", 1)))
        world.reader.battle_blind = 1
        world.game.reinforcements = 0
        self.assertEqual(world.loop.turn(), "battle-stuck")
        self.assertEqual(world.attempts()[0]["outcome"], "unresolved")
        self.assertEqual(world.driver.events("case-met"), [])
        self.assertEqual(world.loop.summary["ended"], "battle-stuck")
        self.assertNotIn("pass", world.driver.blocks)
        self.assertNotIn("exchange", world.driver.blocks)

    def failure_world(self, seat_lag=False, seat_after=RED):
        """Round 1's R2: 3 vs 3, the attacker loses one army on each of two clicks; after the
        second the country is handed over and the next seat takes an army off the former defender
        before the next reading."""
        def computer(game):
            game.board[4]["army"] -= 1
        world = World({3: (BLUE, 3), 4: (RED, 3)}, met=only(("lost", 1)), losers=["a", "a"])
        world.game.reinforcements = 0
        world.game.computer_move = computer
        world.game.seat_lag = seat_lag
        world.reader.seat_after_failure = seat_after
        world.loop.turn()
        return world

    def test_a_failures_count_is_unknown_once_the_next_seat_may_have_played(self):
        world = self.failure_world()
        clicks = world.driver.events("exchange-click")
        self.assertEqual([c["lost"] for c in clicks], [1, None])
        self.assertEqual([c["isolated"] for c in clicks], [True, False])
        self.assertEqual(world.loop.summary["clicks_several_armies"], 0)
        self.assertEqual(world.loop.summary["clicks_one_army"], 1)
        self.assertEqual(world.loop.summary["clicks_unisolated"], 1)
        (attempt,) = world.attempts()
        self.assertIsNone(attempt["lost"])
        self.assertEqual(attempt["unknown"], 1)
        self.assertEqual(world.met("lost"), [1])

    def test_a_failure_read_while_the_human_seat_is_still_boxed_is_counted_from_that_reading(self):
        world = self.failure_world(seat_lag=True)
        clicks = world.driver.events("exchange-click")
        self.assertEqual([c["lost"] for c in clicks], [1, 1])
        self.assertEqual(world.loop.summary["clicks_several_armies"], 0)
        (attempt,) = world.attempts()
        self.assertEqual(attempt["lost"], 2)
        self.assertEqual(attempt["after"], [1, RED, 3, RED])
        self.assertEqual(attempt["seat_after"], RED)

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
        self.assertGreater(len(world.attempts()), 0)
        for attempt in world.attempts():
            a, d = attempt["attacker"], attempt["defender"]
            self.assertIn(d, adjacency[a])
            self.assertEqual(attempt["before"][1], BLUE)
            self.assertNotEqual(attempt["before"][3], BLUE)


class CardOfferTest(unittest.TestCase):
    """Fix #175: a turn that starts with the card trade-in offer (sitting 20261011T154319Z, game 1 turn
    10) declines it and plays on; an offer a decline does not clear ends the sitting cleanly."""

    def world(self, **kwargs):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, **kwargs)
        world.game.offer = True
        return world

    def events(self, world, name):
        return [n for n in world.driver.notes if n.get("event") == name]

    def test_a_turn_that_starts_with_the_offer_declines_it_then_places_then_plays_on(self):
        world = self.world(met=only(("even", 1)))
        world.game.reinforcements = 0
        self.assertIsNone(world.loop.turn())
        blocks = world.driver.blocks
        self.assertEqual(blocks[0], "card-decline")                       # before any placement click
        self.assertEqual(world.driver.steps[0][0], "place-select")
        self.assertEqual(blocks.count("card-decline"), 1)
        self.assertLess(blocks.index("card-decline"), blocks.index("place-commit"))
        self.assertLess(blocks.index("place-commit"), blocks.index("attack-open"))   # the turn played on
        self.assertEqual(blocks[-1], "pass")
        self.assertEqual(world.game.declines, 1)
        self.assertFalse(world.game.offer)
        names = [n["event"] for n in world.driver.notes]
        self.assertLess(names.index("card-offer"), names.index("place-target"))      # logged, then placed
        (line,) = self.events(world, "card-offer")
        self.assertEqual((line["declined"], len(line["sha256"])), (1, 64))
        self.assertNotIn("forced", line)
        self.assertEqual(len(world.attempts()), 1)                          # the attack phase ran
        self.assertEqual(world.loop.summary["placements"], 1)
        self.assertIsNone(world.loop.summary["ended"])

    def test_a_sitting_with_the_offer_on_its_first_turn_goes_on_to_play_the_game(self):
        # from the title: the turn after the decline places and passes, the game ends on the screen after it
        world = self.world(screen="title", met=ALL)
        world.game.after_pass = "unknown"
        world.loop.run()
        blocks = world.driver.blocks
        self.assertEqual(blocks.count("new-game"), 1)                   # card-decline is never New Game
        self.assertEqual(blocks.count("card-decline"), 1)
        self.assertLess(blocks.index("new-game"), blocks.index("card-decline"))
        self.assertLess(blocks.index("card-decline"), blocks.index("place-commit"))
        self.assertEqual(blocks[blocks.index("place-commit") + 1], "pass")
        self.assertEqual(world.loop.summary["ended"], "unknown-screen")     # the screen after the pass
        self.assertEqual(world.loop.summary["turns"], 1)

    def test_a_decline_that_leaves_the_offer_up_ends_the_sitting_with_no_further_click(self):
        world = self.world(met=ALL)
        world.game.decline_works = False
        self.assertEqual(world.loop.turn(), "card-trade-forced")
        self.assertEqual(world.driver.blocks, ["card-decline"])            # the one click, and nothing after it
        self.assertEqual(world.driver.steps, [])
        self.assertEqual(world.game.declines, 1)
        self.assertEqual(world.loop.summary["ended"], "card-trade-forced")
        self.assertEqual(world.loop.summary["final_frame"], "f" * 64)
        declined, forced = self.events(world, "card-offer")
        self.assertEqual((declined["declined"], forced["forced"]), (1, 1))
        self.assertNotIn("declined", forced)
        self.assertEqual([n["ended"] for n in self.events(world, "ended")], ["card-trade-forced"])
        self.assertEqual(world.loop.summary["placements"], 0)

    def test_the_forced_ending_is_the_sittings_clean_end(self):
        world = self.world(screen="title", met=ALL, games_max=3)
        world.game.decline_works = False
        world.loop.run()
        self.assertEqual(world.loop.summary["ended"], "card-trade-forced")
        self.assertEqual(world.driver.blocks.count("new-game"), 1)         # no game after it
        self.assertEqual(world.driver.blocks.count("card-decline"), 1)
        self.assertNotIn("pass", world.driver.blocks)

    def test_the_offer_is_polled_a_bounded_number_of_times_after_the_click(self):
        world = self.world(met=ALL)
        world.game.decline_works = False
        world.loop.turn()
        # one reading before the click and OFFER_POLLS after it, then the end
        self.assertEqual(world.reader.reads, 1 + e021_loop.OFFER_POLLS)

    def test_a_decline_the_game_answers_a_moment_later_is_not_forced(self):
        # the offer is still on the first two readings after the click, then gone: the poll waits for it
        world = self.world(met=ALL)
        world.game.decline_lag = 2
        self.assertIsNone(world.loop.turn())
        self.assertEqual(world.driver.blocks.count("card-decline"), 1)           # clicked once, never again
        self.assertEqual(world.driver.blocks[-2:], ["place-commit", "pass"])
        self.assertEqual(self.events(world, "card-offer")[-1].get("forced"), None)
        self.assertIsNone(world.loop.summary["ended"])

    def test_an_offer_that_comes_up_during_the_first_placement_click_is_declined_too(self):
        # the income message comes first and the offer about a second later: the first click finds no row
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=ALL)
        world.game.offer_late = True
        self.assertIsNone(world.loop.turn())
        blocks = world.driver.blocks
        self.assertEqual(blocks[:2], ["card-decline", "place-commit"])      # no dismiss, no place-any in between
        self.assertEqual(blocks[-1], "pass")
        self.assertEqual(len(self.events(world, "card-offer")), 1)
        self.assertEqual(len([s for s in world.driver.steps if s[0] == "place-select" and s[1] == "click-until?"]), 2)

    def test_a_turn_without_the_offer_sends_no_card_decline(self):
        world = World({3: (BLUE, 2), 4: (RED, 1)}, met=ALL)
        self.assertIsNone(world.loop.turn())
        self.assertNotIn("card-decline", world.driver.blocks)
        self.assertEqual(self.events(world, "card-offer"), [])

    def test_an_unreadable_capture_after_the_decline_ends_the_sitting_cleanly(self):
        world = self.world(met=ALL)
        original = world.reader.read
        reads = []

        def read():
            reads.append(1)
            if len(reads) > 1:
                raise ValueError("undecodable")
            return original()
        world.reader.read = read
        self.assertEqual(world.loop.turn(), "board-unreadable")
        self.assertEqual(world.driver.blocks, ["card-decline"])
        self.assertTrue(world.loop.summary["ended"].startswith("board-unreadable"))


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
        self.assertEqual(world.driver.blocks[-2:], ["place-commit", "pass"])

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
