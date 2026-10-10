"""Synthetic T45 fixtures: boards, adjacency, a fake click-driver, a fake live reader and shaped
records. No wine, no display, no original bytes, no PNG of the game (rule 18): every board here is
a dict of country readings, and every frame stand-in is bytes the test itself made.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _sub in ("tools", "runtime/iwp", "runtime/iwp/spike", "setup/iwp",
             "experiments/E020-wine-first-run", "experiments/E021-pro-session-a"):
    if str(ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(ROOT / _sub))

import cases  # noqa: E402

COUNTRIES = 46
# A small synthetic island for the tests: 1-2-3 blue, 4-5 red, 3 next to 4 (the frontier).
ADJ = {1: {2, 3}, 2: {1, 3}, 3: {1, 2, 4}, 4: {3, 5}, 5: {4}}
BLUE = "blue"
RED = "red"


def board(cells=None, owner="red", army=1):
    """A 46-country board of `owner`/`army`, with `cells` ({country: (owner, army)}) over it."""
    out = {c: {"army": army, "owner": owner} for c in range(1, COUNTRIES + 1)}
    for country, (own, count) in (cells or {}).items():
        out[country] = {"army": count, "owner": own}
    return out


def frontier_board():
    """Blue 3 with 2 armies next to red 4 with 1: the even cell 1 (attacker 2 vs defender 1)."""
    return board({1: (BLUE, 1), 2: (BLUE, 1), 3: (BLUE, 2), 4: (RED, 1), 5: (RED, 3)})


def all_met():
    """The whole table met: a sitting that needs nothing."""
    return {(case, cell) for case in cases.CASES for cell in cases.cells(case)}


class FakeDriver:
    """What the loop needs of the click-driver (runtime/iwp/driver/clicks.py): run blocks and
    steps, note lines, read the screen. `screen_after_click` moves the synthetic game on the way
    the E020 tests' world does (a Play Game shows the board, a PASS starts the computers' turns,
    the notices' CONTINUE buttons show what the test scripts)."""

    def __init__(self, screen="title"):
        self.screen = screen
        self.after_pass = None            # the screen after a PASS click (None: unchanged)
        self.after_continue = "title"
        self.after_scoreboard = "title"
        self.blocks, self.steps, self.notes = [], [], []
        self.context = {}
        self.quiet = True
        self.picked = 1                   # what the `click-until?` searches report

    # --- the click-driver's interface

    def run_block(self, name):
        self.blocks.append(name)
        if name == "quiet":
            return {"quiet": self.quiet}
        if name == "new-game":
            self.screen_after_click((565, 532))     # Play Game ends the block
        if name == "pass" and self.after_pass is not None:
            self.screen = self.after_pass
        return {}

    def run_step(self, block, step):
        self.steps.append((block, step.op, tuple(step.args)))
        if step.op in ("click-until?", "click-until"):
            return {"picked": self.picked}
        if step.op in ("click", "click!"):
            self.screen_after_click(tuple(step.args))
        return {}

    def note(self, **fields):
        self.notes.append(dict(self.context, **fields))

    def read_screen(self):
        return self.screen

    def read_winner(self):
        return None

    def final_frame(self, name):
        return "f" * 64

    # --- the synthetic game behind the clicks

    def screen_after_click(self, point):
        if point == (565, 532):                       # Play Game
            self.screen = "board"
        elif point == (417, 530) and self.after_pass is not None:
            self.screen = self.after_pass
        elif point == (401, 534):
            self.screen = self.after_continue
        elif point == (401, 526):
            self.screen = self.after_scoreboard

    # --- the log the tests read

    def events(self, name):
        return [note for note in self.notes if note.get("event") == name]

    def clicks(self, x, y):
        return [s for s in self.steps if s[1] in ("click", "click!") and s[2] == (x, y)]


class FakeReader:
    """The live view the loop reads (boardview.FrameReader's interface): a scripted sequence of
    boards for `read`, one battle-ready answer, and one board per `wait_change`."""

    def __init__(self, boards, ready=True, changes=()):
        self.boards = list(boards)
        self.ready = ready
        self.changes = list(changes)
        self.reads = 0

    def read(self):
        self.reads += 1
        board = self.boards[min(self.reads - 1, len(self.boards) - 1)]
        return board, f"{self.reads:064d}", object()

    def wait_ready(self, seconds):
        return self.ready, "e" * 64

    def wait_change(self, board, countries, seconds):
        if self.changes:
            return self.changes.pop(0), "a" * 64
        return board, "a" * 64


def attack_line(case, cell, **values):
    """One attack-attempt note line, as the loop writes it."""
    line = {"event": "attack-attempt", "aim:case": case, "aim:cell": cell,
            "country:attacker": "3", "country:defender": "4",
            "counter:attacker-before": "2", "counter:defender-before": "1",
            "counter:attacker-after": "2", "counter:defender-after": "1",
            "counter:clicks": "1", "outcome": "exchange"}
    line.update(values)
    return line


def met_line(case, cell, **values):
    """One case-met note line, as the loop writes it."""
    line = {"event": "case-met", "case": case, "cell": cell}
    line.update(values)
    return line


def record(run_id, groups, experiment="E021", batch="session-a"):
    """A run/1-shaped record whose observations are `groups` ([(step, {field: value}, [refs])])."""
    observations = [{"step": 0, "source": "process", "field": "sitting:epoch", "value": "1790000000"}]
    outputs = []
    step_of = {}
    for step, fields, refs in groups:
        for field, value in fields.items():
            observations.append({"step": step, "source": "screen", "field": field, "value": str(value)})
        for ref in refs:
            observations.append({"step": step, "source": "screen", "ref": f"sha256:{ref}"})
            if ref not in step_of:
                outputs.append({"name": f"{len(outputs)}.png", "sha256": ref, "store": "release:E021"})
                step_of[ref] = step
    return {"schema": "run/1", "run_id": run_id, "experiment": experiment, "arm": batch, "rep": 1,
            "code_commit": "abcdef123456", "machine": "local",
            "artifact": {"set": "iwp-2.0-996e86c5", "variant": "unregistered"},
            "runtime": {"driver": f"experiments/E021-pro-session-a/launcher.py@abcdef123456",
                        "platform": "wine-on-user-machine-iwp-2.0", "fingerprint": {"wine": "wine-10.0"}},
            "interventions": [{"level": "I1", "what": "screenshots of the display"}],
            "start_state": {"id": "S-iwp-prefix-sync", "sha256": "c" * 64,
                            "restore": "fresh prefix sync from the F019 install, no save"},
            "seed": None,
            "actions": {"script": "experiments/E021-pro-session-a/session-a.steps", "sha256": "b" * 64,
                        "args": ["--batch", batch]},
            "observations": observations, "outputs": outputs,
            "started": "2026-10-10T12:00:00Z", "ended": "2026-10-10T13:00:00Z", "status": "completed"}


def write_record(root, doc):
    """The record at runs/E021/<batch>/<run_id>.json under `root`."""
    path = Path(root) / "runs" / doc["experiment"] / doc["arm"] / f"{doc['run_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path
