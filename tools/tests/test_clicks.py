"""Tests for runtime/iwp/driver/clicks.py (T38, round 2).

The click-driver sends step blocks through the session's own `perform`, one step at a time, and
logs every attempted step to `actions.jsonl`. These tests use a fake session (a `perform` that
records the step text and adds the observations the spike's run_step would): no display, no
xdotool. They pin R1/R2/R10 (nothing is sent but through perform, so the session's display,
accounting and step semantics apply), R12 (a failed step's line is on disk before the failure
propagates), the allow-list (no attack, no bundle writes) and the block file's parsing.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime" / "iwp"))
from driver import clicks  # noqa: E402
from driver.clicks import ClickDriver, outcome_of, parse_blocks  # noqa: E402
from driver.errors import StepFailed  # noqa: E402

BLOCKS = """\
# --- block go
watch 0 0 800 495
click! 100 585
settle 4
# --- block pick
click-until? 168 168 168 24 1000 55 193 49 261
# --- block wait-then-click
settle 4
click! 100 585
"""
SETTLED = {"settle": [{"field": "settle: watched area unchanged for 4 s (s)", "value": 4.2}]}
UNSETTLED = {"settle": [{"field": "settle: watched area unchanged for 4 s (s)", "value": "not within the time allowed"}]}


class FakeSession:
    """perform() records the text; `notes` maps an op to the observations it adds; `fail_on` raises."""

    def __init__(self, notes=None, fail_on=None):
        self.sent, self.obs = [], []
        self.notes = SETTLED if notes is None else notes
        self.fail_on = fail_on

    def perform(self, text):
        self.sent.append(text)
        op = text.split()[0]
        if op == self.fail_on:
            error = StepFailed(f"step on line 1: {op} failed")
            raise error
        self.obs.extend(self.notes.get(op, []))


class ClickDriverTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.actions = Path(self._tmp.name) / "actions.jsonl"

    def driver(self, session):
        return ClickDriver(session.perform, lambda: tuple(session.obs), self.actions, parse_blocks(BLOCKS),
                           clock=lambda: 1.0)

    def lines(self):
        return [json.loads(line) for line in self.actions.read_text().splitlines()]

    def test_every_step_goes_through_the_sessions_perform_one_at_a_time(self):
        session = FakeSession()
        self.driver(session).run_block("go")
        self.assertEqual(session.sent, ["watch 0 0 800 495", "click! 100 585", "settle 4"])

    def test_the_driver_never_runs_a_command_itself(self):
        """R1/R2: no xdotool of its own; with every command helper refusing, a block still runs
        because perform is the only route."""
        session = FakeSession()
        with mock.patch("subprocess.run", side_effect=AssertionError("a command was run")), \
                mock.patch("subprocess.Popen", side_effect=AssertionError("a command was run")):
            self.driver(session).run_block("go")
        self.assertFalse(hasattr(clicks, "_default_run"))

    def test_a_failed_step_is_logged_before_the_failure_propagates(self):
        """R12: the line of the step that failed is on disk, with its status and error kind."""
        session = FakeSession(fail_on="click!")
        with self.assertRaises(StepFailed):
            self.driver(session).run_block("go")
        lines = self.lines()
        self.assertEqual([(l["op"], l["status"]) for l in lines], [("watch", "ok"), ("click!", "failed")])
        self.assertEqual(lines[-1]["error"], "step-failed")
        self.assertEqual(lines[-1]["args"], [100, 585])

    def test_an_interruption_is_logged_too(self):
        session = FakeSession()
        session.perform = mock.Mock(side_effect=KeyboardInterrupt)
        with self.assertRaises(KeyboardInterrupt):
            ClickDriver(session.perform, lambda: (), self.actions, parse_blocks(BLOCKS)).run_block("go")
        self.assertEqual(self.lines()[0]["status"], "failed")
        self.assertEqual(self.lines()[0]["error"], "KeyboardInterrupt")

    def test_the_outcome_of_a_candidate_search_names_the_country_picked(self):
        session = FakeSession(notes={"click-until?": [
            {"field": "click-until: candidate that worked", "value": "49,261 (number 2 of 2)"}]})
        self.assertEqual(self.driver(session).run_block("pick"), {"picked": 2})
        self.assertEqual(self.lines()[-1]["outcome"], {"picked": 2})

    def test_a_search_that_found_nothing_picks_nothing(self):
        session = FakeSession(notes={"click-until?": [
            {"field": "click-until?: candidate that worked", "value": "none of the 2"}]})
        self.assertEqual(self.driver(session).run_block("pick"), {"picked": None})

    def test_settle_outcome_reads_whether_the_board_was_quiet(self):
        self.assertEqual(outcome_of(parse_blocks("# --- block a\nsettle 4\n")["a"][0],
                                    [{"field": "settle: watched area unchanged for 4 s (s)", "value": "5.1"}]),
                         {"quiet": True})
        self.assertEqual(outcome_of(parse_blocks("# --- block a\nsettle 4\n")["a"][0],
                                    [{"field": "settle: watched area unchanged for 4 s (s)",
                                      "value": "not within the time allowed"}]),
                         {"quiet": False})

    def test_a_wait_that_did_not_settle_stops_the_block_before_its_next_input(self):
        """Round 3, R1: a `settle` whose area never settled is NotReady (logged failed, `not-ready`),
        and the click after it is never sent."""
        session = FakeSession(notes=UNSETTLED)
        with self.assertRaises(clicks.NotReady) as raised:
            self.driver(session).run_block("wait-then-click")
        self.assertEqual(raised.exception.kind, "not-ready")
        self.assertEqual(session.sent, ["settle 4"])
        self.assertEqual([(l["op"], l["status"], l.get("error")) for l in self.lines()],
                         [("settle", "failed", "not-ready")])
        session = FakeSession()
        self.driver(session).run_block("wait-then-click")
        self.assertEqual(session.sent, ["settle 4", "click! 100 585"])

    def test_context_is_copied_into_every_line(self):
        driver = self.driver(FakeSession())
        driver.context = {"game": 2, "turn": 5}
        driver.run_block("go")
        driver.note(event="game-end", reason="turns-max")
        self.assertTrue(all(l["game"] == 2 and l["turn"] == 5 for l in self.lines()))
        self.assertEqual(self.lines()[-1]["event"], "game-end")

    def test_attack_and_bundle_steps_are_refused_by_the_block_parser(self):
        for line in ("attack-picked 55 193", "shot board", "file xtras/Islepro.skr", "changes"):
            with self.subTest(step=line):
                with self.assertRaises(StepFailed):
                    parse_blocks(f"# --- block a\n{line}\n")

    def test_a_step_outside_a_block_and_a_twice_defined_block_are_refused(self):
        with self.assertRaises(StepFailed):
            parse_blocks("click 1 1\n# --- block a\nsettle\n")
        with self.assertRaises(StepFailed):
            parse_blocks("# --- block a\nsettle\n# --- block a\nsettle\n")

    def test_a_forbidden_click_is_refused_before_anything_is_sent(self):
        with self.assertRaises(StepFailed):
            parse_blocks("# --- block a\nclick 420 580\n")

    def test_the_actions_log_is_never_written_through_a_link(self):
        target = Path(self._tmp.name) / "elsewhere.jsonl"
        target.write_text("")
        self.actions.symlink_to(target)
        with self.assertRaises(OSError):
            self.driver(FakeSession()).run_block("go")
        self.assertEqual(target.read_text(), "")

    def test_every_step_is_sent_as_text_that_parses_back_to_itself(self):
        """Session.perform re-parses the text: `watch all` must stay `watch all`."""
        blocks = parse_blocks((ROOT / "experiments" / "E020-wine-first-run" / "play.steps").read_text())
        for steps in blocks.values():
            for step in steps:
                again = clicks.stepslib.parse_line(clicks.step_text(step))
                self.assertEqual((again.op, again.args), (step.op, step.args))

    def test_the_e020_block_file_parses_and_holds_the_blocks_the_loop_needs(self):
        blocks = parse_blocks((ROOT / "experiments" / "E020-wine-first-run" / "play.steps").read_text())
        self.assertEqual(set(blocks), {"new-game", "quiet", "place", "commit", "dismiss", "eliminated-keep-playing",
                                       "game-over-continue", "scoreboard-continue"})

    def test_keep_playing_is_one_click_that_must_change_the_screen_at_the_measured_point(self):
        """T38 round 4: the notice's KEEP PLAYING, at the centre measured from sitting 20261008T184505Z."""
        from driver import screens
        blocks = parse_blocks((ROOT / "experiments" / "E020-wine-first-run" / "play.steps").read_text())
        steps = [(s.op, s.args) for s in blocks["eliminated-keep-playing"]]
        self.assertEqual(steps, [("watch", ()), ("click!", screens.KEEP_PLAYING_CLICK)])

    def test_continue_is_one_click_that_must_change_the_screen_at_the_measured_point(self):
        """T38 round 6: the winner notice's CONTINUE, at the centre measured from sitting 20261008T195537Z
        (x 327-475, y 522-546), inside the box the screen test counts."""
        from driver import screens
        blocks = parse_blocks((ROOT / "experiments" / "E020-wine-first-run" / "play.steps").read_text())
        steps = [(s.op, s.args) for s in blocks["game-over-continue"]]
        self.assertEqual(steps, [("watch", ()), ("click!", (401, 534))])
        self.assertEqual(screens.CONTINUE_CLICK, (401, 534))
        x, y, w, h = screens.CONTINUE_BOX
        self.assertEqual((x, y, x + w - 1, y + h - 1), (327, 522, 475, 546))

    def test_a_winner_reading_sends_nothing_and_needs_its_reader(self):
        session = FakeSession()
        driver = ClickDriver(session.perform, lambda: session.obs, self.actions, parse_blocks(BLOCKS),
                             winner=lambda: "red")
        self.assertEqual(driver.read_winner(), "red")
        self.assertEqual(session.sent, [])
        with self.assertRaises(StepFailed):
            ClickDriver(session.perform, lambda: session.obs, self.actions, parse_blocks(BLOCKS)).read_winner()

    def test_a_screen_reading_is_logged_and_sends_nothing(self):
        session = FakeSession()
        driver = ClickDriver(session.perform, lambda: session.obs, self.actions, parse_blocks(BLOCKS),
                             screen=lambda: "eliminated", shot=lambda name: "e" * 64)
        driver.context = {"game": 1, "turn": 16}
        self.assertEqual(driver.read_screen(), "eliminated")
        self.assertEqual(driver.final_frame("unknown-screen.png"), "e" * 64)
        self.assertEqual(session.sent, [])
        line = json.loads(self.actions.read_text().splitlines()[-1])
        self.assertEqual((line["event"], line["screen"], line["turn"]), ("screen", "eliminated", 16))

    def test_without_a_screen_reader_the_driver_refuses_to_guess(self):
        session = FakeSession()
        driver = ClickDriver(session.perform, lambda: session.obs, self.actions, parse_blocks(BLOCKS))
        with self.assertRaises(StepFailed):
            driver.read_screen()
        with self.assertRaises(StepFailed):
            driver.final_frame("unknown-screen.png")


if __name__ == "__main__":
    unittest.main(verbosity=2)
