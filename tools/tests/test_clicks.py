"""Tests for runtime/iwp/driver/clicks.py (T38).

The click-driver executes a step list in the E002 step language through xdotool with F006's
exit-status discipline, appending one line per action to `actions.jsonl`. These tests use a fake
runner: no display, no xdotool. They pin the contract the task names — a failed helper is a failed
step, `click!` aborts when the screen did not change (when a change check is wired), and the
actions log records step, coordinates and exit status.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime" / "iwp"))
from driver.clicks import ClickDriver  # noqa: E402
from driver.errors import StepFailed  # noqa: E402


class FakeRunner:
    """Records every command; exits non-zero for a command whose op is in `fails`."""

    def __init__(self, fails=()):
        self.calls = []
        self.fails = set(fails)

    def __call__(self, cmd):
        self.calls.append(list(cmd))
        return 1 if cmd[1] in self.fails else 0


class ClickDriverTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.actions = Path(self._tmp.name) / "actions.jsonl"
        self.slept = []

    def driver(self, runner=None, changed=None):
        return ClickDriver(run=runner or FakeRunner(), actions_path=self.actions,
                           sleep=self.slept.append, changed=changed)

    def lines(self):
        return [json.loads(line) for line in self.actions.read_text().splitlines()]

    def test_click_bang_sends_xdotool_and_logs_the_action(self):
        runner = FakeRunner()
        self.driver(runner).execute("click! 10 20")
        self.assertEqual(runner.calls, [["xdotool", "mousemove", "10", "20"],
                                        ["xdotool", "click", "1"]])
        self.assertEqual(self.lines(), [{"step": 1, "op": "click!", "coordinates": {"x": 10, "y": 20},
                                         "exit_status": 0}])

    def test_a_failed_helper_is_a_failed_step(self):
        with self.assertRaises(StepFailed):
            self.driver(FakeRunner(fails=("mousemove",))).execute("click! 10 20")

    def test_click_bang_aborts_when_the_screen_did_not_change(self):
        with self.assertRaises(StepFailed):
            self.driver(changed=lambda: False).execute("click! 10 20")

    def test_click_bang_passes_when_the_screen_changed(self):
        self.driver(changed=lambda: True).execute("click! 10 20")
        self.assertEqual(self.lines()[0]["exit_status"], 0)

    def test_settle_waits_and_logs(self):
        self.driver().execute("settle 5")
        self.assertEqual(self.slept, [5])
        self.assertEqual(self.lines()[0]["op"], "settle")
        self.assertIsNone(self.lines()[0]["coordinates"])

    def test_key_uses_the_allow_list_and_a_step_outside_it_is_refused(self):
        runner = FakeRunner()
        self.driver(runner).execute("key Return")
        self.assertEqual(runner.calls, [["xdotool", "key", "Return"]])
        with self.assertRaises(StepFailed):
            self.driver().execute("key dollarsign")

    def test_an_unsupported_step_is_refused(self):
        with self.assertRaises(StepFailed):
            self.driver().execute("attack-picked 10 20")

    def test_move_sends_only_mousemove(self):
        runner = FakeRunner()
        self.driver(runner).execute("move 5 6")
        self.assertEqual(runner.calls, [["xdotool", "mousemove", "5", "6"]])

    def test_a_forbidden_click_is_refused_before_anything_is_sent(self):
        runner = FakeRunner()
        with self.assertRaises(StepFailed):
            self.driver(runner).execute("click! 450 580")   # the publisher's label area
        self.assertEqual(runner.calls, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
