"""The click-driver of a model-driven sitting (T38, rule 18 carve-out).

It executes a step list in the E002 step language (runtime/iwp/spike/steps.py) through xdotool,
with F006's exit-status discipline: every helper command's exit status is checked, and a failed
input is a failed step. Each action appends one line to `actions.jsonl` (step, coordinates, exit
status), so the sitting directory alone says which inputs were sent and what came back.

`click! x y` additionally aborts when a `changed` callback (the watcher's screen-change check,
when the launcher wires one) says the screen did not move: the E002 meaning of the trailing `!`.
Without a callback the exit status of xdotool is the whole check, which is what a fake-based test
exercises.

The command runner and the sleep are injected so this module is testable with no display; the
default runner is bounded, as every helper command in F006 is.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_SPIKE = str(ROOT / "runtime" / "iwp" / "spike")
if _SPIKE not in sys.path:
    sys.path.insert(0, _SPIKE)
import cycle as spike  # noqa: E402  (the driver's checked command helpers, reused)
import steps as stepslib  # noqa: E402  (the E002 step language, reused)

from .errors import StepFailed  # noqa: E402

RUN_TIMEOUT = 30       # s, one xdotool command (F006: every helper command has a bound)
DEFAULT_SETTLE = 2.0   # s, a bare `settle` (the spike polls the screen; here it is a bounded wait)
SUPPORTED = ("move", "click", "click!", "clicks", "key", "settle", "watch")


def _default_run(cmd):
    """Run one xdotool command through the spike's checked helper, bounded; return 0 or raise."""
    try:
        spike.must(cmd, require_output=False, timeout=RUN_TIMEOUT)
    except (spike.CommandFailed, spike.Unreaped, subprocess.TimeoutExpired, OSError) as exc:
        raise StepFailed(f"{' '.join(map(str, cmd[:2]))} failed: {exc}") from None
    return 0


class ClickDriver:
    """Executes E002 step lines; `run(cmd)` returns an exit status, `sleep(s)` waits."""

    def __init__(self, run=None, actions_path=None, sleep=time.sleep, changed=None, xdotool="xdotool",
                 on_action=None):
        self.run = run or _default_run
        self.actions_path = Path(actions_path) if actions_path else None
        self.sleep = sleep
        self.changed = changed
        self.xdotool = xdotool
        self.on_action = on_action
        self.step = 0

    def execute(self, text=None, steps=None):
        """Run a step list (text or parsed steps), one action per line; StepFailed on the first."""
        if steps is None:
            try:
                steps = stepslib.parse(text)
            except stepslib.StepError as exc:
                raise StepFailed(f"the steps are not usable: {exc}") from None
        for step in steps:
            self.perform(step)
            if self.on_action is not None:
                self.on_action(step)
        return steps

    def perform(self, step):
        if step.op not in SUPPORTED:
            raise StepFailed(f"step on line {step.line}: {step.op} is not a click-driver step; "
                             f"the driver knows {', '.join(SUPPORTED)}")
        self.step = step.line
        if step.op == "watch":
            return                              # screen regions matter to the spike's settle, not here
        if step.op == "settle":
            seconds = step.args[0] if step.args else DEFAULT_SETTLE
            self.sleep(seconds)
            self._log(step, None, 0)
            return
        if step.op == "key":
            status = self._checked([self.xdotool, "key", step.args[0]], step)
            self._log(step, None, status)
            return
        if step.op == "clicks":
            count, x, y = step.args[0], step.args[1], step.args[2]
            status = self._checked([self.xdotool, "mousemove", str(x), str(y)], step)
            for _ in range(count):
                status = self._checked([self.xdotool, "click", "1"], step)
            self._log(step, {"x": x, "y": y}, status)
            return
        # move, click and click! all name one point
        x, y = step.args
        coordinates = {"x": x, "y": y}
        if step.op != "move":
            self._checked([self.xdotool, "mousemove", str(x), str(y)], step)
            status = self._checked([self.xdotool, "click", "1"], step)
        else:
            status = self._checked([self.xdotool, "mousemove", str(x), str(y)], step)
        self._log(step, coordinates, status)
        if step.op == "click!" and self.changed is not None and not self.changed():
            raise StepFailed(f"step on line {step.line}: the screen did not change after the click")

    def _checked(self, cmd, step):
        """Run a command the step relies on; StepFailed unless it exits 0 (F006, class B)."""
        status = self.run(cmd)
        if status != 0:
            raise StepFailed(f"step on line {step.line}: {' '.join(map(str, cmd[:2]))} exited {status}")
        return status

    def _log(self, step, coordinates, status):
        if self.actions_path is None:
            return
        self.actions_path.parent.mkdir(parents=True, exist_ok=True)
        line = {"step": step.line, "op": step.op, "coordinates": coordinates, "exit_status": status}
        with self.actions_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, sort_keys=True) + "\n")
