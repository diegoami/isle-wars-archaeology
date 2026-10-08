"""The click-driver of a model-driven sitting (T38, rule 18 carve-out).

It executes step blocks in the E002 step language (runtime/iwp/spike/steps.py) and appends one line
per attempted step to `actions.jsonl`. It sends nothing itself: every step goes through the
session's own `perform` (runtime/iwp/driver/session.py), one step at a time, so that each one runs
exactly as the E002/E004 machinery runs it (T38 round 2, R1, R2, R10):

* on the session's own private display, with the session's environment, and at stage coordinates
  translated to the game window's stage origin (the spike's `click_at`);
* with F006's exit-status discipline: every xdotool command is the spike's checked helper, and a
  failed command is a failed step;
* with the step language's meaning: `click!` aborts when the screen did not change, `watch` narrows
  what `settle` and the change checks look at, and `settle` is a bounded poll on the screen, never a
  fixed sleep; `click-until` reads the screen after each candidate;
* inside Session's accounting: each input step that succeeded is one of Session's actions, so
  `Session.complete()` sees the inputs and the screenshots around them.

The steps a sitting may send are an allow-list (`ALLOWED`): pointer and key inputs and the waits.
`attack-picked` is refused by name (the human never attacks: the driver never clicks inside a
battle), and so are the steps that write bundle files or read the game copy.

A wait is never ignored (T38 round 3, R1): a `settle` whose watched area did not settle within its
bound is a failed step of its own kind, `NotReady` (`not-ready`), in every block, so no input of the
block after it is sent. The loop may retry a `quiet` block that raised it, within its bound; past
that bound it ends the sitting with it (e020_loop.py), and the session records it as the sitting's
status (Session.execute).

Each line of `actions.jsonl` is written whether the step succeeded or not (R12): `status` is `ok` or
`failed`, a failed step carries the driver error's kind, and the line is on disk before the failure
propagates. A line carries structural values only (constraint D): the block, the step's line in
it, its op and numeric arguments, the context the caller names (game, turn), the wall time in
milliseconds, the duration, and for an `ok` step what the screen showed (`outcome`).
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_SPIKE = str(ROOT / "runtime" / "iwp" / "spike")
if _SPIKE not in sys.path:
    sys.path.insert(0, _SPIKE)
import steps as stepslib  # noqa: E402  (the E002 step language, reused)

from .errors import StepFailed  # noqa: E402

ALLOWED = frozenset({"move", "click", "click!", "clicks", "click-any", "click-any?", "click-until",
                     "click-until?", "key", "settle", "watch"})
BLOCK = re.compile(r"^#\s*---\s*block\s+([a-z][a-z0-9-]*)\s*$")
PICKED = re.compile(r"^(\d+),(\d+) \(number (\d+) of (\d+)\)$")


class NotReady(StepFailed):
    """A wait did not establish the state the next input needs (a `settle` that did not settle, or the
    loop's `quiet` blocks spent): nothing more is sent (T38 round 3, R1)."""
    kind = "not-ready"


def parse_blocks(text):
    """{block name: [Step, ...]} from a block file; StepFailed on a bad block or a refused step.
    Line numbers are the file's, so an action names the line it came from."""
    blocks, name, lines = {}, None, {}
    for number, line in enumerate(text.splitlines(), start=1):
        match = BLOCK.match(line.strip())
        if match:
            name = match.group(1)
            if name in lines:
                raise StepFailed(f"line {number}: the block {name!r} is defined twice")
            lines[name] = []
            continue
        if name is None:
            if line.split("#", 1)[0].strip():
                raise StepFailed(f"line {number}: a step outside every block")
            continue
        lines[name].append((number, line))
    for name, numbered in lines.items():
        steps = []
        for number, line in numbered:
            try:
                step = stepslib.parse_line(line, number)
            except stepslib.StepError as exc:
                raise StepFailed(f"line {number}: {exc}") from None
            if step is None:
                continue
            if step.op not in ALLOWED:
                raise StepFailed(f"line {number}: {step.op} is not a click-driver step; the driver sends "
                                 f"only {', '.join(sorted(ALLOWED))}")
            steps.append(step)
        if not steps:
            raise StepFailed(f"the block {name!r} has no step")
        blocks[name] = steps
    return blocks


def step_text(step):
    """The one-line E002 text of a parsed step, for Session.perform (`watch all` parses to no
    arguments and is written back as `watch all`)."""
    if step.op == "watch" and not step.args:
        return "watch all"
    return " ".join([step.op] + [str(a) for a in step.args])


def outcome_of(step, new):
    """What the screen showed for a step, from the observations the session added for it."""
    op = step.op.rstrip("?")
    fields = {o.get("field"): o.get("value") for o in new}
    if op in ("click-until", "click-any"):
        value = fields.get(f"{op}: candidate that worked")
        match = PICKED.match(value or "")
        return {"picked": int(match.group(3)) if match else None}
    if op == "settle":
        value = next((v for f, v in fields.items() if str(f).startswith("settle:")), None)
        return {"quiet": value is not None and value != "not within the time allowed"}
    if op in ("click", "click!"):
        value = next((v for f, v in fields.items() if str(f).endswith("screen changed after the click (s)")), None)
        return {"changed": value is not None and not str(value).startswith("no change")}
    return {}


class ClickDriver:
    """Sends step blocks through `perform` (Session.perform) and logs one line per attempted step.

    `observations()` returns the session's observations so far (Session.obs); the driver reads the
    ones each step added to say what the screen showed. `context` (a dict of small integers or
    words: game, turn) is copied into every line."""

    def __init__(self, perform, observations, actions_path, blocks, clock=time.time):
        self.perform = perform
        self.observations = observations
        self.actions_path = Path(actions_path)
        self.blocks = blocks
        self.clock = clock
        self.context = {}
        self.seq = 0

    def run_block(self, name):
        """Run one block; the outcome of its last step that has one ({} when none). StepFailed (or the
        session's own error) on the first step that fails, after its line is written."""
        if name not in self.blocks:
            raise StepFailed(f"no block {name!r} in the block file")
        last = {}
        for step in self.blocks[name]:
            result = self.run_step(name, step)
            if result:
                last = result
        return last

    def run_step(self, block, step):
        if step.op not in ALLOWED:
            raise StepFailed(f"{step.op} is not a click-driver step")
        self.seq += 1
        line = {"seq": self.seq, "block": block, "line": step.line, "op": step.op,
                "args": [a for a in step.args if isinstance(a, int)], **self.context}
        before = len(self.observations())
        started = self.clock()
        line["t_ms"] = int(started * 1000)
        try:
            self.perform(step_text(step))
        except BaseException as exc:
            line.update(status="failed", error=getattr(exc, "kind", type(exc).__name__),
                        ms=int((self.clock() - started) * 1000))
            self.log(line)
            raise
        outcome = outcome_of(step, list(self.observations())[before:])
        if step.op == "settle" and not outcome.get("quiet"):
            line.update(status="failed", error=NotReady.kind, ms=int((self.clock() - started) * 1000),
                        outcome=outcome)
            self.log(line)
            raise NotReady(f"block {block}, line {step.line}: the watched area did not settle within its time")
        line.update(status="ok", ms=int((self.clock() - started) * 1000), outcome=outcome)
        self.log(line)
        return outcome

    def note(self, **fields):
        """A line of the loop's own (a game started or ended, and why), in the same file."""
        self.seq += 1
        self.log({"seq": self.seq, **self.context, **fields, "t_ms": int(self.clock() * 1000)})

    def log(self, line):
        """Append one line; never through a link (the sitting directory is the launcher's own)."""
        fd = os.open(self.actions_path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, sort_keys=True) + "\n")
