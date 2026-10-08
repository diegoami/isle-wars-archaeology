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
  sends no further input and ends the sitting `aborted: not-ready: <reason>`, with no normal summary.
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
        events = [(l.get("event"), l.get("game"), l.get("reason")) for l in self.actions() if "event" in l]
        self.assertEqual(events, [("game-start", 1, None), ("game-end", 1, "turns-max")])


if __name__ == "__main__":
    unittest.main()
