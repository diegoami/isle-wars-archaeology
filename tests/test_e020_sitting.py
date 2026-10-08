"""T38 round 2: the E020 sitting's body on the real Session (runtime/iwp/driver/session.py), with the
game and the display replaced by the E004 test world (tests/test_iwp_driver.py DriverWorld): a
`sleep` process for the game, the spike's run_step replaced by a stand-in that answers as the
spike's notes do. No wine, no Xvfb, no xdotool.

What it pins, each a round-1 finding:
- R2: a sitting whose loop ran is `completed` by Session's own completion guard (round 1 bypassed
  Session.perform, so Engine.complete() raised "the cycle performed no input step");
- R1: every step reaches the session's run_step (so the session's display, environment and stage
  origin), and the watcher gets the session's environment and game window, whatever the caller's
  DISPLAY is;
- R10: a `click!` the screen did not answer aborts the sitting through the session (step-failed),
  with the step's line logged as failed first (R12);
- round 3, R1: a board that never goes quiet, or a `settle` that never settles inside a block,
  sends no further input and ends the sitting `aborted: not-ready: <reason>`, with no normal summary;
- round 4: the screen is read through Session.screen_name (pixels of the session's own capture, here
  synthetic frames painted by e020_fixtures.screen_frame): the elimination notice is answered with
  KEEP PLAYING once and nothing more is sent; an unknown screen ends the sitting cleanly, with a
  last screenshot whose sha256 is logged, and no click.
"""
import json
import os
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_iwp_driver as base  # noqa: E402  (DriverWorld: the E004 test world)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "tests"))
import e020_fixtures  # noqa: E402,F401  (puts experiments/E020-wine-first-run on sys.path)
import e020_loop  # noqa: E402
import e020_sitting  # noqa: E402
from driver import session as sessionlib  # noqa: E402

launcher = sys.modules.get("t38_launcher")
if launcher is None:
    import importlib.util
    _spec = importlib.util.spec_from_file_location("t38_launcher", ROOT / "experiments" / "E020-wine-first-run" / "launcher.py")
    launcher = importlib.util.module_from_spec(_spec)
    sys.modules["t38_launcher"] = launcher
    _spec.loader.exec_module(launcher)

BLOCKS = (ROOT / "experiments" / "E020-wine-first-run" / "play.steps").read_text()
BATCH = {"games_max": "1", "turns_max": "2", "sitting_seconds": "1000"}


class FakeWatcher:
    made = []

    def __init__(self, window, env, frames, index, log, step_source):
        self.window, self.env = window, env
        FakeWatcher.made.append(self)

    def start(self):
        thread = threading.Thread(target=lambda: None)
        thread.start()
        return thread, threading.Event()


class E020SessionTest(base.DriverWorld):
    def setUp(self):
        super().setUp()
        self.sent = []                       # (op, args, DISPLAY of the engine's environment)
        self.unchanged = set()               # click! points the screen does not answer
        self.unsettled = set()               # settle argument tuples whose area never settles
        self.unsettled_after = None          # a click! point after which a bare `settle` never settles
        world_start = self.start_game

        def start_game(engine):
            world_start(engine)
            engine.window = "0x2a"
        patcher = mock.patch.object(sessionlib.Engine, "start_game", start_game)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(sessionlib.Engine, "run_step", lambda engine, step: self.run_step(engine, step))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.screen = "title"                # what the synthetic capture shows (round 4)
        self.eliminated_after_passes = None  # the notice comes up after this many PASS clicks
        self.playout_reads = 2               # board readings in the play-out before the screen is unknown
        self.playout_end = "unknown"         # what the play-out ends on (round 6: the winner notice)
        self.after_continue = "title"        # what the winner notice's CONTINUE shows (round 6)
        self.reads = []
        patcher = mock.patch.object(base.spike.Screen, "raw", lambda screen, crop=None: self.raw(crop))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(e020_loop, "PLAYOUT_POLL", 0)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.paths = e020_sitting.sitting_paths(self.tmp / "wine", e020_fixtures.SID)
        for key in ("frames", "dumps", "session"):
            self.paths[key].mkdir(parents=True)
        FakeWatcher.made = []

    def run_step(self, engine, step):
        """What the spike's run_step notes for each op, so the loop reads a quiet board, a country
        picked on the placement, and a screen that changed after each click."""
        self.sent.append((step.op, step.args, engine.env["DISPLAY"]))
        op = step.op
        if op == "settle":
            engine.note("screen", f"settle: watched area unchanged for {step.args[0] if step.args else 0} s (s)",
                        "not within the time allowed" if self.never_settles(step) else 4.2)
        elif op == "click-until?":
            engine.note("screen", "click-until: candidate that worked", "55,193 (number 1 of 44)")
        elif op == "click-any?":
            engine.note("screen", "click-any?: candidate that worked", "none of the 1")
        elif op in ("click", "click!"):
            if op == "click!" and step.args in self.unchanged:
                engine.fail(f"step on line {step.line}: the screen did not change after the click at "
                            f"{step.args[0]},{step.args[1]}")
            engine.note("screen", f"click at {step.args[0]},{step.args[1]}: screen changed after the click (s)", 0.02)
            self.screen_after_click(tuple(step.args))

    def screen_after_click(self, point):
        """The synthetic game's screen: Play Game shows the board with its menu; the notice comes up
        after the PASS clicks named; KEEP PLAYING shows the board (the computers play on)."""
        if point == (565, 532):
            self.screen = "board-menu"
        elif point == (417, 530) and self.eliminated_after_passes is not None:
            passes = [a for o, a, _ in self.sent if o == "click!" and tuple(a) == (417, 530)]
            if len(passes) >= self.eliminated_after_passes:
                self.screen = "eliminated"
        elif point == (665, 531):
            self.screen = "board"
        elif point == (401, 534):
            self.screen = self.after_continue

    def raw(self, crop):
        """The session's capture: the whole stage (Session.screen_name and screen_winner read it) or a
        crop of it. The winner notice shows red as the winner (sitting 20261008T195537Z)."""
        if crop == (0, 0, 800, 600):
            self.reads.append(self.screen)
            if self.screen == "board" and self.reads.count("board") > self.playout_reads:
                self.screen = self.reads[-1] = self.playout_end
        return e020_fixtures.screen_frame(self.screen, winner="red" if self.screen == "game-over" else None)

    def never_settles(self, step):
        if tuple(step.args) in self.unsettled:
            return True
        clicked = [tuple(a) for o, a, _ in self.sent if o == "click!"]
        return not step.args and self.unsettled_after is not None and clicked[-1:] == [self.unsettled_after]

    def sitting(self):
        made = self.session()
        summary = {}
        with mock.patch.dict(os.environ, {"DISPLAY": ":wrong"}):
            made.execute(launcher.make_body(self.paths, BATCH, BLOCKS, summary, watcher_factory=FakeWatcher))
        self.addCleanup(lambda: made._engine.procs.get("game") and made._engine.procs["game"].poll() is None
                        and made._engine.procs["game"].kill())
        return made, summary

    def actions(self):
        return [json.loads(line) for line in self.paths["actions"].read_text().splitlines()]

    def test_a_sitting_that_ran_its_loop_is_completed_by_sessions_own_guard(self):
        """R2: the inputs are Session's actions, between before.png and after.png."""
        made, summary = self.sitting()
        self.assertEqual(made.status, "completed", made.status)
        self.assertEqual(summary, {"games": 1, "turns": 2, "placements": 2, "ended": "games-max"})
        self.assertGreater(len(made._engine.actions), 0)
        self.assertEqual({o for o, _, _ in self.sent} - {"watch", "settle", "click", "click!", "click-until?",
                                                         "click-any?"}, set())
        self.assertNotIn("attack-picked", [o for o, _, _ in self.sent])

    def test_every_step_and_the_watcher_are_on_the_sessions_display(self):
        """R1: the session's display (":99" in this world), never the caller's ":wrong"."""
        self.sitting()
        self.assertEqual({d for _, _, d in self.sent}, {":99"})
        self.assertEqual([(w.window, w.env["DISPLAY"]) for w in FakeWatcher.made], [("0x2a", ":99")])

    def test_a_click_the_screen_did_not_answer_aborts_through_the_session(self):
        """R10 and R12: `click!` keeps its meaning on the launch path, and its line is logged failed."""
        self.unchanged.add((565, 532))                 # Play Game does nothing
        made, _ = self.sitting()
        self.assertTrue(made.status.startswith("aborted: step-failed: "), made.status)
        last = self.actions()[-1]
        self.assertEqual((last["op"], last["args"], last["status"], last["error"]),
                         ("click!", [565, 532], "failed", "step-failed"))

    def test_a_board_that_never_goes_quiet_sends_no_placement_or_commit(self):
        """Round 3, R1: the `quiet` blocks spent, nothing more is sent, and the session records why."""
        self.unsettled.add((4,))
        made, summary = self.sitting()
        self.assertTrue(made.status.startswith("aborted: not-ready: the board was not quiet after 6 quiet blocks"),
                        made.status)
        ops = [o for o, _, _ in self.sent]
        self.assertNotIn("click-until?", ops)                       # no placement
        self.assertNotIn((307, 543), [tuple(a) for o, a, _ in self.sent if o == "click!"])   # no ALL (commit)
        self.assertEqual(ops.count("settle"), 1 + 6)                # new-game's own, then the quiet blocks
        self.assertEqual(ops[-1], "settle")                         # nothing after the last wait
        self.assertTrue(summary["ended"].startswith("aborted: not-ready: "), summary)

    def test_a_wait_inside_the_commit_that_never_settles_stops_before_pass(self):
        """Round 3, R1: the commit block's own `settle` (no argument) is not ignored either: PASS is
        never clicked when the screen did not settle after PLACE."""
        self.unsettled_after = (497, 543)                           # PLACE
        made, summary = self.sitting()
        self.assertTrue(made.status.startswith("aborted: not-ready: "), made.status)
        clicked = [tuple(a) for o, a, _ in self.sent if o == "click!"]
        self.assertIn((497, 543), clicked)                          # the commit was reached
        self.assertNotIn((417, 530), clicked)                       # PASS never clicked
        self.assertEqual((self.actions()[-1]["op"], self.actions()[-1]["error"]), ("settle", "not-ready"))
        self.assertNotEqual(summary.get("ended"), "games-max")

    def test_the_actions_log_names_the_game_and_its_end(self):
        self.sitting()
        events = [(l.get("event"), l.get("game"), l.get("reason")) for l in self.actions()
                  if l.get("event") in ("game-start", "game-end")]
        self.assertEqual(events, [("game-start", 1, None), ("game-end", 1, "turns-max")])
        self.assertEqual([l["screen"] for l in self.actions() if l.get("event") == "screen"],
                         ["title", "board-menu", "board-menu"])

    def test_the_elimination_notice_is_answered_with_keep_playing_once_then_no_input(self):
        """Round 4: turn 2 starts on the notice (sitting 20261008T184505Z's turn 16). One click on
        KEEP PLAYING, then only screen readings; the game's end (an unknown screen) ends the sitting
        with a last screenshot and no click. New Game (100,585) is never sent off the title."""
        self.eliminated_after_passes = 1
        made, summary = self.sitting()
        self.assertEqual(made.status, "completed", made.status)
        clicks = [tuple(a) for o, a, _ in self.sent if o in ("click", "click!", "click-until?", "click-any?")]
        self.assertEqual(clicks[-1], (665, 531))                    # nothing sent after KEEP PLAYING
        self.assertEqual(clicks.count((665, 531)), 1)
        self.assertEqual(clicks.count((100, 585)), 1)               # game 1's New Game, on the title only
        self.assertEqual(self.reads[-3:], ["board", "board", "unknown"])
        self.assertEqual((summary["ended"], summary["screen"], summary["eliminated"], summary["turns"]),
                         ("unknown-screen", "unknown", True, 1))
        lines = self.actions()
        keep = [l for l in lines if l.get("block") == "eliminated-keep-playing"]
        self.assertEqual([(l["op"], l["args"], l["status"], l["turn"]) for l in keep],
                         [("watch", [], "ok", 2), ("click!", [665, 531], "ok", 2)])
        ended = [l for l in lines if l.get("event") == "ended"]
        shot = {name: path for name, path, _ in made.outputs}[e020_loop.FINAL_FRAME]
        self.assertEqual([(l["ended"], l["sha256"]) for l in ended],
                         [("unknown-screen", e020_fixtures.sha(Path(shot).read_bytes()))])
        self.assertEqual(summary["final_frame"], ended[0]["sha256"])

    def test_the_winner_notice_ends_the_game_names_the_winner_and_continue_is_clicked_once(self):
        """Round 6 (sitting 20261008T195537Z): the play-out ends on the winner notice, read through
        Session.screen_name and the winner through Session.screen_winner (pixels of the session's own
        capture). The game-end line says game-over and red; CONTINUE (401,534) once; the screen after it
        is read, and the sitting completes at games_max."""
        self.eliminated_after_passes = 1
        self.playout_end = "game-over"
        made, summary = self.sitting()
        self.assertEqual(made.status, "completed", made.status)
        clicks = [tuple(a) for o, a, _ in self.sent if o in ("click", "click!", "click-until?", "click-any?")]
        self.assertEqual(clicks[-2:], [(665, 531), (401, 534)])         # KEEP PLAYING, then CONTINUE, nothing after
        self.assertEqual(self.reads[-2:], ["game-over", "title"])
        lines = self.actions()
        ends = [l for l in lines if l.get("event") == "game-end"]
        self.assertEqual([(l["reason"], l["ended"], l["winner"]) for l in ends],
                         [("played-out: game-over", "game-over", "red")])
        cont = [l for l in lines if l.get("block") == "game-over-continue"]
        self.assertEqual([(l["op"], l["args"], l["status"]) for l in cont],
                         [("watch", [], "ok"), ("click!", [401, 534], "ok")])
        self.assertLess(lines.index(ends[0]), lines.index(cont[0]))      # the end is logged before the click
        self.assertEqual(summary["ended"], "games-max")
        self.assertNotIn(e020_loop.FINAL_FRAME, [name for name, _, _ in made.outputs])

    def test_an_unknown_screen_after_continue_ends_the_sitting_cleanly(self):
        self.eliminated_after_passes = 1
        self.playout_end = "game-over"
        self.after_continue = "unknown"
        made, summary = self.sitting()
        self.assertEqual(made.status, "completed", made.status)
        self.assertEqual([tuple(a) for o, a, _ in self.sent if o.startswith("click")][-1], (401, 534))
        self.assertEqual((summary["ended"], summary["screen"]), ("unknown-screen", "unknown"))
        self.assertIn(e020_loop.FINAL_FRAME, [name for name, _, _ in made.outputs])

    def test_an_unknown_screen_ends_the_sitting_cleanly_without_a_click(self):
        """Round 4: Play Game led to a screen the loop does not know: a last screenshot, no click."""
        made = None
        with mock.patch.object(self, "screen_after_click", lambda point: None):   # the title stays up
            made, summary = self.sitting()
        self.assertEqual(made.status, "completed", made.status)
        self.assertEqual((summary["ended"], summary["screen"], summary["turns"]), ("unknown-screen", "title", 0))
        self.assertEqual([tuple(a) for o, a, _ in self.sent if o.startswith("click")][-1], (565, 532))
        self.assertNotIn("click-until?", [o for o, _, _ in self.sent])
        self.assertIn(e020_loop.FINAL_FRAME, [name for name, _, _ in made.outputs])


if __name__ == "__main__":
    unittest.main()
