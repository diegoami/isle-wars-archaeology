"""E019 (T24): the UI-walk recorder, its records, and the catalogue check.

Tests here need no game, no display and no Wine. The walk table and the pixel helpers are tested
directly. The recorder is tested end to end: every walk of walks.py is driven through
run_walk.run_walk() with a fake session (FakeSession below: a fake screen and a fake clock, no
game), the records and manifests are the ones run_walk writes, with nothing added by hand, and
check_ui_catalogue's checks are run on them. The checker's refusals are tested by mutating that
recorder-written tree, never a hand-made record (round 2, R2).
"""
import contextlib
import hashlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "experiments" / "E019-pro-ui"))

import walks  # noqa: E402
import pixels  # noqa: E402
import records as e019_records  # noqa: E402
import check_ui_catalogue  # noqa: E402
import run_walk  # noqa: E402
import test_runs  # noqa: E402  (the amended record-layout rule, and the pinned run/1 validator)
import check_no_originals as cno  # noqa: E402  (T48: the recorder's platform is pinned to the gate's)

QUESTIONS = ROOT / "questions" / "pro-static.md"
INVENTORY = ROOT / "experiments" / "E008-static-triage" / "measurements" / "iwp-extract-pro-r1.json"

# The five per-screen batches of T24, in the order the task file fixes them.
BRIEF_BATCHES = [
    ("title-options", ["Q-UI-04", "Q-UI-10", "Q-UI-19", "Q-UI-22"]),
    ("board-pieces", ["Q-UI-01", "Q-UI-02", "Q-UI-03", "Q-UI-05", "Q-UI-20", "Q-PLY-04"]),
    ("play", ["Q-UI-08", "Q-UI-12", "Q-UI-13", "Q-UI-15", "Q-UI-16"]),
    ("events-end", ["Q-UI-06", "Q-UI-07", "Q-UI-11", "Q-UI-14", "Q-UI-21"]),
    ("inputs-sounds", ["Q-UI-09", "Q-UI-17", "Q-UI-18"]),
]
FRAME_TIMED = {"Q-UI-06", "Q-UI-13", "Q-UI-16"}
HIT_AREAS = {"Q-UI-18"}
STATIC_ONLY = {"Q-UI-14", "Q-UI-21"}
# the rows whose target needs an identification the pixels cannot make: proxied, F020 narrowed
PROXIED = {"Q-UI-06", "Q-UI-07", "Q-UI-13"}
# the F020 statuses whose sections the citation rule reads (#140); write_f020 cites exactly the
# sections the rule applies to. The tuple lives here, not in the check, so these tests run
# against main's check too (Done-when 2: every one of them fails there).
CITED_STATUSES = ("observed", "narrowed")


def catalogue_ids():
    rows = walks.question_rows(QUESTIONS)
    return [qid for qid in rows if qid.startswith("Q-UI-")] + ["Q-PLY-04"]


def walk_order():
    """(qid, size) of every walk, in the batches' order: one per question, one per size for Q-UI-19."""
    return [(qid, size) for qids in walks.BATCHES.values() for qid in qids
            for size in (walks.WALKS[qid].get("sizes") or [None])]


# --- the fake session: a screen and a clock, no game --------------------------------------------

class FakeClock:
    def __init__(self):
        self.now = 0.0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += max(0.0, float(seconds))


class FakeScreen:
    """Region reads that change when an input or a pointer move is sent, and every two fake seconds
    (so the timed watches see changes); a whole-display read is the size the session was made at."""

    def __init__(self, fake):
        self.fake = fake

    def state(self):
        return (self.fake.events, int(self.fake.clock.now // 2))

    def raw(self, rect):
        if rect is None:
            w, h = (int(v) for v in self.fake.size.split("x")[:2])
            return bytes(w * h * 3)
        return hashlib.sha256(repr((self.state(), tuple(rect))).encode()).digest()[:12]   # 4 pixels


class FakeEngine:
    def __init__(self, fake):
        self.screen = FakeScreen(fake)
        self.obs = []
        self.outputs = []
        self.started = self.ended = None
        self.status = "running"
        self._error = None
        self.faults = []

    def abort_later(self, reason):
        self.faults.append(reason)
        self.status = f"aborted: fake: {reason}"


class FakeSession:
    """The driver Session's surface that run_walk uses, over a fake screen and clock. It makes no
    observation the recorder does not ask for, except the ones the driver itself makes (the title
    time and each screenshot's pixel hash); `drop` removes recorder observations (field, match) and
    `drop_outputs` screenshots, to show the check refuses a record without them."""

    def __init__(self, run_id, prefix, bundles, install, display, arm, size, *, clock, workdir,
                 drop=(), drop_outputs=(), snapshot=True):
        self.run_id, self.size, self.clock = run_id, size, clock
        self.workdir = Path(workdir) / run_id
        self.workdir.mkdir(parents=True)
        self.events = 0
        self.synthetic_phase = "menu"
        self.strict_attack_phase = arm == "q-ui-16"
        self.drop, self.drop_outputs = list(drop), set(drop_outputs)
        self._engine = FakeEngine(self)
        self.snap_before = ("fake", {"drive_c": ("dir",)}) if snapshot else None
        self.recovered = False
        self.elapsed = None

    @property
    def status(self):
        return self._engine.status

    @property
    def obs(self):
        return list(self._engine.obs)

    def execute(self, body):
        self._engine.started = "2026-10-08T00:00:00Z"
        try:
            body(self)
            self._engine.status = "completed"
        except Exception as exc:          # what the driver records as an aborted session
            self._engine.status = f"aborted: fake: {type(exc).__name__}: {exc}"
        self.recovered = True
        self.elapsed = round(self.clock.now, 2)
        self._engine.ended = "2026-10-08T00:01:00Z"
        return self._engine.status

    def expect(self, *names):
        pass

    def known_screen(self):
        self.observe(2, "screen", "title screen reached and stable, seconds after launch", 6.6)

    def wait_for_screen(self, name, timeout=None, stable=True):
        return 0.0

    def screen_name(self):
        if not self.strict_attack_phase:
            return "board"
        return {"menu": "board-menu", "attack": "board-menu", "computer": "board"}[self.synthetic_phase]

    def screen_attack_ready(self):
        return self.strict_attack_phase and self.synthetic_phase == "attack"

    def screen_card_award(self):
        return True

    def game_alive(self):
        return True

    def perform(self, text):
        words = text.split()
        if words[0] == "shot":
            self._shot(f"{words[1]}.png")
        elif words[0] in run_walk.sessionlib.INPUT_OPS or words[0] == "move":
            self.events += 1
        if not self.strict_attack_phase:
            return
        if words[0] == "attack-picked":
            self.synthetic_phase = "attack"
        elif words[0] == "click-until" and self.synthetic_phase == "attack":
            self.synthetic_phase = "menu"
        elif words[0] == "click!" and len(words) >= 3:
            point = tuple(int(value) for value in words[-2:])
            if point == walks.PASS_CLICK:
                self.synthetic_phase = "computer"
        elif words[0] == "settle" and self.synthetic_phase == "computer":
            self.synthetic_phase = "menu"

    def observe_screenshot(self, name, step=None):
        self._shot(name)

    def _shot(self, name):
        pixels_sha = hashlib.sha256(repr(self.screen_state()).encode()).hexdigest()
        self._engine.obs.append({"step": 1, "source": "screen", "field": f"{name} raw RGB8 pixels sha256",
                                 "value": pixels_sha})
        if name in self.drop_outputs:
            return
        path = self.workdir / name
        path.write_bytes(f"{self.run_id} {name} {pixels_sha}".encode())
        self._engine.outputs.append((name, path, "screenshot"))

    def screen_state(self):
        return self._engine.screen.state()

    def observe(self, step, source, field, value):
        for dropped, match in self.drop:
            if (field == dropped) if match == "exact" else field.startswith(dropped):
                return
        self._engine.obs.append({"step": step, "source": source, "field": field, "value": str(value)})


class StatefulTurnSession(FakeSession):
    """A synthetic turn state machine for the computer-turn composite.

    It refuses PASS unless the placement and attack panels have been closed to the turn menu. Its
    screen also changes on each fake-clock tick, so the timing observations expose an origin taken
    before setup rather than immediately before the accepted PASS.
    """

    def __init__(self, *args, refuse_placement=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase = "placement"
        self.refuse_placement = refuse_placement
        self.pass_attempt_phases = []
        self.accepted_pass_times = []
        self._engine.screen.raw = self._stateful_raw

    def _stateful_raw(self, rect):
        key = (self.phase, int(self.clock.now * 4), tuple(rect) if rect is not None else None)
        return hashlib.sha256(repr(key).encode()).digest()[:12]

    def perform(self, text):
        super().perform(text)
        words = text.split()
        is_pass = words[0] == "click!" and tuple(int(value) for value in words[-2:]) == walks.PASS_CLICK
        if (words[0] in run_walk.sessionlib.INPUT_OPS or words[0] == "move") and not is_pass:
            self.clock.now += 0.5

        if words[0] == "click-any?":
            # CONTINUE is allowed to be refused on a normal placement screen.
            if self.phase == "award":
                self.phase = "placement"
            return
        if words[0] == "click-until":
            if self.phase == "placement":
                if self.refuse_placement:
                    raise run_walk.StepFailed("synthetic placement transition refused")
                self.phase = "placement-selected"
            elif self.phase == "attack":
                self.phase = "menu"
            return
        if words[0] == "click!":
            point = tuple(int(value) for value in words[-2:])
            if point == walks.ALL_CLICK and self.phase == "placement-selected":
                self.phase = "placement-all"
            elif point == walks.PLACE_DONE_CLICK and self.phase == "placement-all":
                self.phase = "attack"
            elif point == walks.PASS_CLICK:
                self.pass_attempt_phases.append(self.phase)
                if self.phase != "menu":
                    raise run_walk.StepFailed(f"synthetic PASS refused during {self.phase}")
                self.accepted_pass_times.append(self.clock.now)
                self.phase = "award"


class StatefulCardPhaseSession(StatefulTurnSession):
    """Synthetic Q-UI-15 phases used to pin the unsafe old ordering.

    The phase names are test fixtures, not detector names. ``computer`` is deliberately quiet until
    the existing settle-4 machinery exposes ``award``; the fixture's detector hook stands in for
    the measured screen signal and never changes the game state.
    """

    def __init__(self, *args, refusal_after_menu=False, award_after_settle=True,
                 settle_timeout=False, terminal_state=None, after_continue_phase=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase = "placement"
        self.refusal_after_menu = refusal_after_menu
        self.award_after_settle = award_after_settle
        self.settle_timeout = settle_timeout
        self.terminal_state = terminal_state
        self.after_continue_phase = after_continue_phase
        self.actions = []
        self.shots = []
        self.continue_phases = []
        self.departure_observed = False

    def perform(self, text):
        words = text.split()
        self.actions.append((self.phase, text))
        if words[0] == "shot":
            self.shots.append((self.phase, words[1]))
        FakeSession.perform(self, text)
        is_pass = words[0] == "click!" and tuple(int(value) for value in words[-2:]) == walks.PASS_CLICK
        if words[0] == "settle":
            if self.settle_timeout and self.phase == "computer":
                raise run_walk.StepFailed("synthetic settle4 timeout")
            if self.phase == "computer":
                self.phase = self.terminal_state or ("award" if self.award_after_settle else "menu")
        elif words[0] == "click-until" and self.phase == "placement":
            if self.refusal_after_menu:
                self.phase = "menu"
                raise run_walk.StepFailed("synthetic placement refusal")
            self.phase = "placement-selected"
        elif words[0] == "click!" and tuple(int(value) for value in words[-2:]) == walks.ALL_CLICK:
            self.phase = "placement-all"
        elif words[0] == "click!" and tuple(int(value) for value in words[-2:]) == walks.PLACE_DONE_CLICK:
            self.phase = "attack"
        elif words[0] == "click-until" and self.phase == "attack":
            self.phase = "menu"
        elif is_pass:
            self.pass_attempt_phases.append(self.phase)
            if self.phase != "menu":
                raise run_walk.StepFailed(f"synthetic PASS during {self.phase}")
            self.accepted_pass_times.append(self.clock.now)
            self.phase = "computer"
        elif words[0] in ("click", "click!") and tuple(int(value) for value in words[-2:]) == walks.CONTINUE_CLICK:
            self.continue_phases.append(self.phase)
            if self.phase != "award":
                # The old composite is intentionally allowed to make this unsafe input so the
                # regression can prove its removal.  The repaired path must never reach it.
                self.phase = "placement"
                return
            self.phase = self.after_continue_phase or "placement"

    def screen_name(self):
        """Expose only the states a future gate is allowed to query in this regression."""
        if self.phase != "menu":
            self.departure_observed = True
        return {"menu": "board-menu", "award": "board", "computer": "board",
                "game-over": "game-over", "eliminated": "eliminated"}.get(self.phase, "unknown")

    def screen_card_award(self):
        return self.phase == "award"


def card_ctx():
    return run_walk.Ctx(dict(walks.WALKS["Q-UI-15"], qid="Q-UI-15"))


class QUi15PhaseRegressionTest(unittest.TestCase):
    """#236: card-path actions are gated by an observed phase, not by pixel change or time."""

    def session(self, name, **options):
        clock = FakeClock()
        session = StatefulCardPhaseSession(
            "E019-r0001", None, None, None, ":99", "q-ui-15", "800x600x24",
            clock=clock, workdir=tempfile.mkdtemp(prefix=name + "-"), **options,
        )
        return clock, session

    def test_q_ui_15_stops_after_placement_refusal_without_pass_or_continue(self):
        clock, session = self.session("e019-q15-refused", refusal_after_menu=True)
        try:
            with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
                run_walk.composite_card_turns(session, card_ctx(), turns=1)
        finally:
            shutil.rmtree(session.workdir.parent, ignore_errors=True)

        self.assertEqual(session.pass_attempt_phases, [])
        self.assertEqual(session.continue_phases, [])
        self.assertFalse(any(" 417 530" in text or " 402 531" in text for _, text in session.actions))

    def test_q_ui_15_captures_before_continue_and_never_inputs_during_computer_phase(self):
        clock, session = self.session("e019-q15-order")
        try:
            with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
                run_walk.composite_card_turns(session, card_ctx(), turns=1)
        finally:
            shutil.rmtree(session.workdir.parent, ignore_errors=True)

        self.assertEqual(session.pass_attempt_phases, ["menu"])
        self.assertTrue(session.departure_observed)
        self.assertEqual(session.continue_phases, ["award"])
        continue_index = next(i for i, (_, text) in enumerate(session.actions) if text == "click! 402 531")
        shot_indices = [i for i, (_, text) in enumerate(session.actions) if text.startswith("shot ")]
        self.assertTrue(shot_indices)
        self.assertLess(shot_indices[-1], continue_index)
        self.assertFalse(any(phase == "computer" and text.startswith(("click", "click!", "click-any"))
                             for phase, text in session.actions))

    def test_q_ui_15_stops_after_first_candidate_before_computer_phase_can_restart(self):
        clock, session = self.session("e019-q15-one-candidate", after_continue_phase="computer")
        try:
            with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
                run_walk.composite_card_turns(session, card_ctx(), turns=2)
        finally:
            shutil.rmtree(session.workdir.parent, ignore_errors=True)

        continue_index = next(i for i, (_, text) in enumerate(session.actions) if text == "click! 402 531")
        self.assertEqual(session.pass_attempt_phases, ["menu"])
        self.assertEqual(session.continue_phases, ["award"])
        self.assertEqual(sum(text == walks.PLACE_WATCH for _, text in session.actions), 1)
        self.assertEqual(session.actions[continue_index + 1:], [])
        self.assertTrue(any(o["field"] == "cards note" and "first captured candidate" in o["value"]
                            and o["source"] == "static" for o in session._engine.obs))

    def test_q_ui_15_no_award_stops_at_observed_human_readiness_without_continue(self):
        clock, session = self.session("e019-q15-no-award", award_after_settle=False)
        try:
            with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
                run_walk.composite_card_turns(session, card_ctx(), turns=1)
        finally:
            shutil.rmtree(session.workdir.parent, ignore_errors=True)

        self.assertEqual(session.continue_phases, [])
        self.assertFalse(session.shots)
        self.assertEqual(session.screen_name(), "board-menu")

    def test_q_ui_15_stops_on_settle_timeout_without_input(self):
        clock, session = self.session("e019-q15-timeout", settle_timeout=True)
        try:
            with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
                run_walk.composite_card_turns(session, card_ctx(), turns=1)
        finally:
            shutil.rmtree(session.workdir.parent, ignore_errors=True)

        self.assertEqual(session.continue_phases, [])
        self.assertTrue(any(o["field"] == "card path stop" and "timeout" in o["value"]
                            for o in session._engine.obs))

    def test_q_ui_15_stops_on_terminal_state_without_input(self):
        clock, session = self.session("e019-q15-terminal", terminal_state="game-over")
        try:
            with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
                run_walk.composite_card_turns(session, card_ctx(), turns=1)
        finally:
            shutil.rmtree(session.workdir.parent, ignore_errors=True)

        self.assertEqual(session.continue_phases, [])
        self.assertEqual(session.screen_name(), "game-over")


class StatefulAttackPhaseSession(FakeSession):
    """Synthetic state machine for the repaired Q-UI-16 composite.

    It exposes the same narrow public reads as the real session: screen name, attack-ready probe,
    and region pixels.  No original frame or install is involved.  The panel and outside epochs are
    separate so a generic screen change cannot accidentally count as an attack.
    """

    ATTACK_RECT = tuple(walks.REGIONS["attack-panel"]["rect"])

    def __init__(self, *args, placement_refused=False, attack_ready=True, panel_changes=True,
                 fail_attack_input=False, terminal_before_attack=None, capture_after=None,
                 fail_attack_after=None, panel_changes_after=None, departure=True, settle_timeout=False,
                 initial_phase=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase = initial_phase or "placement"
        self.placement_refused = placement_refused
        self.attack_ready_signal = attack_ready
        self.panel_changes = panel_changes
        self.fail_attack_input = fail_attack_input
        self.fail_attack_after = fail_attack_after
        self.panel_changes_after = panel_changes_after
        self.terminal_before_attack = terminal_before_attack
        self.capture_after = capture_after
        self.departure = departure
        self.settle_timeout = settle_timeout
        self.panel_epoch = 0
        self.outside_epoch = 0
        self.placements = 0
        self.attack_calls = 0
        self.pass_attempt_phases = []
        self.actions = []
        self._engine.screen.raw = self._stateful_raw

    def _stateful_raw(self, rect):
        rect = tuple(rect) if rect is not None else None
        epoch = self.panel_epoch if rect == self.ATTACK_RECT else self.outside_epoch
        key = (self.phase, epoch, rect, int(self.clock.now * 4))
        return hashlib.sha256(repr(key).encode()).digest()[:12]

    def perform(self, text):
        words = text.split()
        self.actions.append((self.phase, text))
        if words[0] == "settle":
            if self.settle_timeout and self.phase == "computer":
                raise run_walk.StepFailed("synthetic settle4 timeout")
            if self.phase == "computer":
                self.phase = "menu" if self.departure else "computer"
            return

        FakeSession.perform(self, text)
        point = tuple(int(value) for value in words[-2:]) if len(words) >= 3 else None
        if words[0] == "click-until":
            if self.phase in {"placement", "menu"}:
                if self.placement_refused:
                    self.phase = "menu"
                    raise run_walk.StepFailed("synthetic placement refusal")
                self.placements += 1
                self.phase = "placement-selected"
            elif self.phase == "attack-ready":
                self.phase = "menu"
            return
        if words[0] == "attack-picked":
            self.phase = self.terminal_before_attack or "attack-ready"
            return
        if words[0] != "click!":
            return
        if point == walks.ALL_CLICK and self.phase == "placement-selected":
            self.phase = "placement-all"
        elif point == walks.PLACE_DONE_CLICK and self.phase == "placement-all":
            self.phase = "attack-opening"
        elif point == walks.ATTACK_PANEL_CLICK:
            if self.phase != "attack-ready":
                raise run_walk.StepFailed("synthetic attack input outside attack-ready")
            if self.fail_attack_input or (self.fail_attack_after is not None
                                          and self.attack_calls + 1 >= self.fail_attack_after):
                raise run_walk.StepFailed("synthetic refused attack input")
            self.attack_calls += 1
            if self.capture_after is not None and self.attack_calls >= self.capture_after:
                self.phase = "capture"
            elif self.panel_changes and (self.panel_changes_after is None
                                         or self.attack_calls <= self.panel_changes_after):
                self.panel_epoch += 1
            else:
                self.outside_epoch += 1
        elif point == walks.PASS_CLICK:
            self.pass_attempt_phases.append(self.phase)
            if self.phase != "menu":
                raise run_walk.StepFailed(f"synthetic PASS during {self.phase}")
            self.phase = "computer" if self.departure else "menu"

    def screen_name(self):
        if self.phase in {"menu", "placement", "placement-selected", "placement-all", "attack-ready"}:
            return "board-menu"
        if self.phase in {"computer", "capture", "attack-opening", "placement", "placement-selected",
                          "placement-all"}:
            return "board"
        if self.phase in {"game-over", "eliminated", "scoreboard"}:
            return self.phase
        return "unknown"

    def screen_attack_ready(self):
        return self.phase == "attack-ready" and self.attack_ready_signal


def attack_ctx():
    return run_walk.Ctx(dict(walks.WALKS["Q-UI-16"], qid="Q-UI-16"))


class QUi16AttackPhaseRegressionTest(unittest.TestCase):
    """#239: Q-UI-16 cannot turn refused, stale, or unrelated screen changes into attacks."""

    def session(self, name, **options):
        clock = FakeClock()
        session = StatefulAttackPhaseSession(
            "E019-r0001", None, None, None, ":99", "q-ui-16", "800x600x24",
            clock=clock, workdir=tempfile.mkdtemp(prefix=name + "-"), **options,
        )
        return clock, session

    @staticmethod
    def drive(clock, session, ctx, **kwargs):
        with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
            run_walk.composite_attack_exchanges(session, ctx, **kwargs)

    def tear(self, session):
        shutil.rmtree(session.workdir.parent, ignore_errors=True)

    def test_placement_refusal_never_leads_to_attack_or_pass(self):
        clock, session = self.session("e019-q16-placement-refused", placement_refused=True)
        try:
            ctx = attack_ctx()
            self.drive(clock, session, ctx, turns=2, exchanges=1, need=2, strict=True)
        finally:
            self.tear(session)
        self.assertEqual((session.placements, session.attack_calls, session.pass_attempt_phases), (0, 0, []))
        self.assertNotIn(walks.PASS_CLICK, [tuple(int(v) for v in text.split()[-2:])
                                             for _, text in session.actions if text.startswith("click!")])

    def test_repeated_cycles_require_departure_quiet_settle_and_human_ready_before_placement(self):
        clock, session = self.session("e019-q16-cycles")
        try:
            ctx = attack_ctx()
            self.drive(clock, session, ctx, turns=3, exchanges=1, need=3, strict=True)
        finally:
            self.tear(session)
        self.assertEqual((session.placements, session.attack_calls, ctx.counts["attacks"]), (3, 3, 3))
        self.assertEqual(session.pass_attempt_phases, ["menu", "menu", "menu"])
        placement_indexes = [i for i, (_, text) in enumerate(session.actions) if text == walks.PLACE_WATCH]
        settle_indexes = [i for i, (_, text) in enumerate(session.actions) if text == "settle 4"]
        self.assertEqual(len(placement_indexes), len(settle_indexes) + 1)
        self.assertTrue(all(any(settle < place for settle in settle_indexes[:i])
                            for i, place in enumerate(placement_indexes[1:], start=1)))

    def test_terminal_and_capture_states_get_no_stale_attack_or_pass_input(self):
        for label, options, expected_attacks in (
                ("terminal", {"terminal_before_attack": "game-over"}, 0),
                ("capture", {"capture_after": 1}, 1)):
            with self.subTest(label=label):
                clock, session = self.session("e019-q16-" + label, **options)
                try:
                    ctx = attack_ctx()
                    self.drive(clock, session, ctx, turns=2, exchanges=2, need=2, strict=True)
                finally:
                    self.tear(session)
                self.assertEqual((session.attack_calls, ctx.counts.get("attacks", 0)),
                                 (expected_attacks, expected_attacks))
                self.assertEqual(session.pass_attempt_phases, [])

    def test_computer_or_terminal_before_placement_gets_no_input(self):
        for phase in ("computer", "unknown", "game-over"):
            with self.subTest(phase=phase):
                clock, session = self.session("e019-q16-before-" + phase, initial_phase=phase)
                try:
                    ctx = attack_ctx()
                    self.drive(clock, session, ctx, turns=1, exchanges=1, need=1, strict=True)
                finally:
                    self.tear(session)
                self.assertEqual((session.placements, session.attack_calls, session.pass_attempt_phases), (0, 0, []))

    def test_generic_change_outside_watched_panel_does_not_count(self):
        clock, session = self.session("e019-q16-outside-change", panel_changes=False)
        try:
            ctx = attack_ctx()
            self.drive(clock, session, ctx, turns=1, exchanges=1, need=1, strict=True)
        finally:
            self.tear(session)
        self.assertEqual((session.attack_calls, ctx.counts.get("attacks", 0)), (1, 0))
        self.assertEqual(session.pass_attempt_phases, [])
        self.assertTrue(any('"panel changed": false' in value for field, value in
                            ((o["field"], o["value"]) for o in session._engine.obs)
                            if field == "timing: attack exchange"))

    def test_non_strict_legacy_path_keeps_counting_after_a_generic_change(self):
        """Q-UI-16's strict arm is isolated; other composites retain their old counter semantics."""
        clock, session = self.session("e019-legacy-generic-change", panel_changes=False)
        try:
            ctx = attack_ctx()
            self.drive(clock, session, ctx, turns=1, exchanges=1, need=1, strict=False)
        finally:
            self.tear(session)
        self.assertEqual((session.attack_calls, ctx.counts.get("attacks", 0)), (1, 1))

    def test_attack_click_is_gated_by_the_human_attack_ready_probe(self):
        clock, session = self.session("e019-q16-not-ready", attack_ready=False)
        try:
            ctx = attack_ctx()
            self.drive(clock, session, ctx, turns=1, exchanges=1, need=1, strict=True)
        finally:
            self.tear(session)
        self.assertEqual((session.attack_calls, ctx.counts.get("attacks", 0), session.pass_attempt_phases), (0, 0, []))

    def test_an_unproved_attack_input_cannot_create_a_count(self):
        clock, session = self.session("e019-q16-input-refused", fail_attack_input=True)
        try:
            ctx = attack_ctx()
            self.drive(clock, session, ctx, turns=1, exchanges=1, need=1, strict=True)
        finally:
            self.tear(session)
        self.assertEqual((session.attack_calls, ctx.counts.get("attacks", 0), session.pass_attempt_phases), (0, 0, []))

    def test_later_attack_refusal_preserves_prior_count_and_stops_before_pass(self):
        clock, session = self.session("e019-q16-late-refusal", fail_attack_after=2)
        try:
            ctx = attack_ctx()
            self.drive(clock, session, ctx, turns=1, exchanges=3, need=3, strict=True)
        finally:
            self.tear(session)
        self.assertEqual((session.attack_calls, ctx.counts.get("attacks", 0)), (1, 1))
        self.assertEqual(session.pass_attempt_phases, [])
        self.assertTrue(any(o["field"] == "attacks stop" and "strict attack input refused" in o["value"]
                            for o in session._engine.obs))

    def test_later_unproved_panel_change_preserves_prior_count_and_stops_before_pass(self):
        clock, session = self.session("e019-q16-late-panel", panel_changes_after=1)
        try:
            ctx = attack_ctx()
            self.drive(clock, session, ctx, turns=1, exchanges=3, need=3, strict=True)
        finally:
            self.tear(session)
        self.assertEqual((session.attack_calls, ctx.counts.get("attacks", 0)), (2, 1))
        self.assertEqual(session.pass_attempt_phases, [])
        self.assertTrue(any(o["field"] == "attacks stop" and "panel changed" in o["value"]
                            for o in session._engine.obs))


FAKE_BINARY = b"Isle Wars Pro, the bytes of a fake install's Islepro.exe (T48)"


def fake_locs(root):
    """The three confined locations of a fake walk: the prefix, the install and the bundles, with a
    fake `Islepro.exe` in the fake install. `run_walk.run_walk` hashes it at the walk's start
    (`records.binary_sha256`) and records it as `start_state.sha256` (T48, #149), so a fake walk
    needs one; two different byte strings give two different hashes, which the record tests use."""
    root = Path(root).resolve()
    locs = {"IWP_PREFIX": root / "prefix", "IWP_DIR": root / "install", "E019_BUNDLES": root / "bundles"}
    for path in locs.values():
        path.mkdir(exist_ok=True)
    (locs["IWP_DIR"] / e019_records.BINARY).write_bytes(FAKE_BINARY)
    return locs


def drive(root, qids=None, **fake_options):
    """Run the recorder (run_walk.run_walk) for the walks named (every walk by default) into `root`,
    with a fake session; returns [(qid, size, status, recovered)]."""
    locs = fake_locs(root)
    root = Path(root).resolve()
    clock = FakeClock()

    def factory(*args):
        return FakeSession(*args, clock=clock, workdir=root / "work", **fake_options)

    results = []
    with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep), \
            contextlib.redirect_stdout(io.StringIO()):
        for qid, size in walk_order():
            if qids is not None and qid not in qids:
                continue
            status, recovered = run_walk.run_walk(qid, size, locs, ":99", "0123456789ab", "local", ["--test"],
                                                  {"wine": "fake"}, root=root, session_factory=factory)
            results.append((qid, size, status, recovered))
    return results


def write_f020(root, status_of=None):
    """A minimal F020 (the catalogue is T39's; this is the shape check_ui_catalogue reads): one
    section per question, the proxied ones narrowed, the none-found ones static-only. Every
    section the citation rule reads (observed or narrowed, #140) cites its question's first
    record by full path with that file's sha256, and one of that record's outputs by hash, so
    the catalogue the check passes on carries the evidence T39's DW2 asks for."""
    lines = ["# F020 UI observations catalogue (structure)", "", "## Observations", ""]
    for qid in catalogue_ids():
        if status_of and qid in status_of:
            status = status_of[qid]
        elif qid in PROXIED:
            status = "narrowed"
        elif qid in STATIC_ONLY:
            status = "static-only"
        else:
            status = "observed"
        lines += [f"#### {qid} question text",
                  f"- **Observation**: {status}: described from the records."]
        if status in CITED_STATUSES:
            found = records_of(root, qid)
            if found:
                record_path, record = found[0]
                rel = record_path.relative_to(Path(root)).as_posix()
                sha = hashlib.sha256(record_path.read_bytes()).hexdigest()
                line = f"- **Run**: `{rel}` (sha256 `{sha[:16]}\u2026`)"
                shots = [o for o in record.get("outputs") or [] if o.get("sha256")]
                if shots:
                    line += (f" **Screenshot**: `{shots[0]['name']}` "
                             f"(sha256 `{shots[0]['sha256'][:16]}\u2026`)")
                lines.append(line)
        lines.append("")
    path = Path(root) / "findings" / "F020-pro-ui-observations.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def records_of(root, qid):
    """[(path, record)] of one question's records under root, in run-id order."""
    found = []
    for path in sorted((Path(root) / "runs" / "E019").glob("*/E019-r*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["arm"] == e019_records.arm_of_question(qid):
            found.append((path, record))
    return found


def check(root, f020=False):
    return check_ui_catalogue.run_checks(Path(root), questions_path=QUESTIONS, inventory_path=INVENTORY,
                                         f020=f020)


_BASE = {}


def recorded_tree():
    """The tree every walk's recorder run wrote (built once per test run, copied by each test)."""
    if "dir" not in _BASE:
        tmp = tempfile.mkdtemp(prefix="e019-e2e-")
        _BASE["dir"] = tmp
        _BASE["results"] = drive(tmp)
    return Path(_BASE["dir"])


def tearDownModule():
    if "dir" in _BASE:
        shutil.rmtree(_BASE["dir"], ignore_errors=True)


class Copy:
    """A private copy of the recorder-written tree, to mutate."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="e019-copy-")
        for part in ("runs", "evidence"):
            shutil.copytree(recorded_tree() / part, Path(self.tmp) / part)
        return Path(self.tmp)

    def __exit__(self, *exc):
        shutil.rmtree(self.tmp, ignore_errors=True)


def rewrite(path, change):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    change(record)
    Path(path).write_text(json.dumps(record), encoding="utf-8")


# --- the walk table ------------------------------------------------------------------------------

class WalkTableTest(unittest.TestCase):
    def test_every_catalogue_question_has_a_walk_spec_in_the_batches_of_the_task(self):
        ids = catalogue_ids()
        self.assertEqual(len(ids), 23)
        self.assertEqual(list(walks.BATCHES), [name for name, _ in BRIEF_BATCHES])
        for name, qids in walks.BATCHES.items():
            want = dict(BRIEF_BATCHES)[name]
            self.assertEqual(qids, want, name)
        self.assertEqual(set(walks.WALKS), set(ids))

    def test_every_spec_belongs_to_the_batch_that_names_it(self):
        for qid, spec in walks.WALKS.items():
            self.assertIn(qid, walks.BATCHES[spec["batch"]], qid)

    def test_targets_come_from_the_question_rows(self):
        import re
        rows = walks.question_rows(QUESTIONS)
        for qid, spec in walks.WALKS.items():
            cell = rows[qid]["corroboration"]
            m = re.search(r"at least (\d+) ([a-z ]+)", cell)
            if m:
                # the row's own "at least N <word>" is the target, in the row's words
                self.assertEqual(spec["count"]["word"], m.group(2).strip(), qid)
                self.assertEqual(spec["count"]["at_least"], int(m.group(1)), qid)
            self.assertEqual(spec.get("timing") == "frame-timed", qid in FRAME_TIMED, qid)
            self.assertEqual(bool(spec.get("hit_areas")), qid in HIT_AREAS, qid)

    def test_the_proxied_targets_are_exactly_the_rows_that_need_an_identification(self):
        proxied = {qid for qid, spec in walks.WALKS.items() if check_ui_catalogue.is_proxy(spec)}
        self.assertEqual(proxied, PROXIED)

    def test_the_two_none_found_rows_are_the_static_only_walks(self):
        for qid in STATIC_ONLY:
            spec = walks.WALKS[qid]
            self.assertTrue(spec.get("absence") or spec.get("states"), qid)

    def test_q_ui_21_names_the_four_reference_states(self):
        self.assertEqual(walks.WALKS["Q-UI-21"]["states"], ["setup", "mid-game", "battle", "end"])

    def test_every_step_line_parses_in_the_e002_step_language(self):
        sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "spike"))
        import steps as stepslib
        for qid, spec in walks.WALKS.items():
            for line in walks.step_lines(spec):
                try:
                    stepslib.parse_line(line)
                except stepslib.StepError as exc:
                    self.fail(f"{qid}: step {line!r} refused: {exc}")

    def test_every_region_is_inside_the_stage_and_says_where_it_came_from(self):
        for label, region in walks.REGIONS.items():
            x, y, w, h = region["rect"]
            self.assertTrue(0 <= x and 0 <= y and x + w <= 800 and y + h <= 600, label)
            self.assertTrue(region.get("source"), label)

    def test_every_spec_region_is_defined(self):
        for qid, spec in walks.WALKS.items():
            for label in spec.get("regions", []):
                self.assertIn(label, walks.REGIONS, f"{qid}: region {label}")
            for item in spec["actions"]:
                if item[0] == "timed_watch":
                    for label in ([item[1]] if isinstance(item[1], str) else item[1]):
                        self.assertIn(label, walks.REGIONS, f"{qid}: watched region {label}")


class PixelsTest(unittest.TestCase):
    def rgb(self, w, h, fn):
        return bytes(v for y in range(h) for x in range(w) for v in fn(x, y))

    def test_census_counts_distinct_quantised_colours(self):
        data = self.rgb(4, 1, lambda x, y: (10, 10, 250) if x < 2 else (250, 10, 10))
        result = pixels.census(data, quantise=16)
        self.assertEqual(result["distinct"], 2)
        self.assertEqual(result["total"], 4)
        self.assertEqual({tuple(c) for c, _ in result["top"]}, {(0, 0, 240), (240, 0, 0)})

    def test_greyscale_census_collapses_to_luminance(self):
        data = self.rgb(2, 1, lambda x, y: (10, 10, 10) if x == 0 else (250, 250, 250))
        result = pixels.greyscale_census(data, quantise=16)
        self.assertEqual(result["distinct"], 2)
        self.assertEqual(sorted(g for g, _ in result["top"]), [0, 240])

    def test_text_rows_finds_the_height_of_ink_bands(self):
        def px(x, y):
            if 2 <= y <= 4 and 1 <= x <= 8:
                return (30, 30, 30)
            if y == 6 and 1 <= x <= 8:
                return (30, 30, 30)
            return (200, 200, 200)
        result = pixels.text_rows(self.rgb(10, 8, px), 10, tol=40)
        self.assertEqual(result["boxes"], 2)
        self.assertEqual(result["heights"], [3, 1])

    def test_hover_points_steps_a_grid_inside_the_rectangle(self):
        points = pixels.hover_points((470, 515, 40, 20), step=10, ys=(525, 535))
        self.assertEqual(points, [(470, 525), (480, 525), (490, 525), (500, 525),
                                  (470, 535), (480, 535), (490, 535), (500, 535)])


class RecordLayoutTest(unittest.TestCase):
    def test_a_batch_folder_record_sits_at_its_batch_and_is_valid(self):
        path = ROOT / "runs" / "E019" / "title-options" / "E019-r9999.json"
        self.assertEqual(test_runs.record_experiment(path), "E019")

    def test_a_record_still_must_sit_under_its_own_experiment(self):
        doc_text = (ROOT / "runs" / "E004" / "E004-r0062.json").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "runs" / "E019" / "title-options"
            folder.mkdir(parents=True)
            path = folder / "E002-r0001.json"
            path.write_text(doc_text, encoding="utf-8")
            errors = test_runs.run_record_errors(path, None)
        self.assertTrue(any("experiment" in e and "E004" in e for e in errors), errors)

    def test_deeper_nesting_is_refused(self):
        self.assertIsNone(test_runs.record_experiment(ROOT / "runs" / "E019" / "a" / "b" / "E019-r0001.json"))

    def test_paths_of_a_record_and_its_manifest(self):
        self.assertEqual(e019_records.record_paths("play", "E019-r0007"),
                         {"run": "runs/E019/play/E019-r0007.json",
                          "manifest": "evidence/E019/play/E019-r0007.manifest.json"})

    def test_arm_and_question_round_trip(self):
        self.assertEqual(e019_records.arm_of_question("Q-UI-04"), "q-ui-04")
        self.assertEqual(e019_records.question_of_arm("q-ply-04"), "Q-PLY-04")

    def test_the_recorder_and_the_driver_agree_on_the_artifact_sets(self):
        sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "spike"))
        import cycle as spike  # noqa: E402
        self.assertEqual(e019_records.ARTIFACT_SET, spike.SET_ID)
        self.assertEqual(e019_records.ARTIFACT_SET_SAVED_FILES, spike.SUCCESSOR2_ID)


# --- DW2: the recorder end to end -----------------------------------------------------------------

class RecorderEndToEndTest(unittest.TestCase):
    """Every walk of walks.py through run_walk.run_walk with a fake session; the check runs on the
    records the recorder wrote, with nothing added by hand."""

    def test_every_walk_is_recorded_completed_and_recovered(self):
        recorded_tree()
        self.assertEqual([(q, s) for q, s, _, _ in _BASE["results"]], walk_order())
        for qid, size, status, recovered in _BASE["results"]:
            self.assertEqual((status, recovered), ("completed", True), f"{qid} {size}")

    def test_the_recorders_own_records_pass_every_record_check(self):
        self.assertEqual(check(recorded_tree()), [])

    def test_the_recorders_own_records_with_a_catalogue_pass_the_whole_check(self):
        with Copy() as tmp:
            write_f020(tmp)
            self.assertEqual(check(tmp, f020=True), [])

    def test_the_recorders_records_and_manifests_are_valid_run_1_and_evidence_manifest_1(self):
        root = recorded_tree()
        known = {e019_records.ARTIFACT_SET, e019_records.ARTIFACT_SET_SAVED_FILES}
        for path in sorted((root / "runs" / "E019").glob("*/E019-r*.json")):
            self.assertEqual(test_runs.run_record_errors(path, known), [], path.name)
        for path in sorted((root / "evidence" / "E019").glob("*/*.manifest.json")):
            errors, _ = test_runs.schema_errors(path, test_runs.MANIFEST_SCHEMA)
            self.assertEqual(errors, [], path.name)

    def test_removing_any_required_field_the_recorder_writes_fails_the_check(self):
        """For every walk and every observation field the check requires of it, a recorder run that
        does not write that field gives a record the check refuses, naming the question."""
        for qid in catalogue_ids():
            spec = walks.WALKS[qid]
            # the task's own list (the run id, screenshots and seal are tested apart), so that a
            # field dropped from the checker's list is still tested here
            task_fields = [("walk question", "exact"), ("speed setting", "exact"), ("display size", "exact"),
                           ("observation", "exact")]
            if spec.get("count"):
                task_fields.append((f"count: {spec['count'].get('measured', spec['count']['word'])}", "exact"))
            if qid in PROXIED:
                task_fields.append((f"count note: {spec['count']['word']}", "exact"))
            if qid in FRAME_TIMED:
                task_fields.append(("timing:", "prefix"))
            if qid in HIT_AREAS:
                task_fields.append(("hit-area:", "prefix"))
            task_fields += [(f"read: {kind}", "exact") for kind in spec.get("reads", {})]
            fields = list(dict.fromkeys(task_fields + check_ui_catalogue.required_fields(spec)))
            for field, match in fields:
                with self.subTest(qid=qid, field=field), tempfile.TemporaryDirectory() as tmp:
                    drive_one(tmp, qid, walk_order_first(qid), drop=[(field, match)])
                    errors = [e for e in check(tmp) if f"({qid})" in e]
                    self.assertTrue(any(field.rstrip(":") in e for e in errors), (field, errors))

    def test_removing_a_required_output_fails_the_check(self):
        for qid in catalogue_ids():
            for name in check_ui_catalogue.required_outputs(walks.WALKS[qid]):
                with self.subTest(qid=qid, output=name), tempfile.TemporaryDirectory() as tmp:
                    drive_one(tmp, qid, walk_order_first(qid), drop_outputs={name})
                    errors = [e for e in check(tmp) if f"({qid})" in e]
                    self.assertTrue(any(name in e for e in errors), errors)

    def test_a_record_without_the_seal_fails_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            drive_one(tmp, "Q-UI-01", None, snapshot=False)
            errors = check(tmp)
            self.assertTrue(any("(Q-UI-01)" in e and "start_state" in e for e in errors), errors)

    def test_a_record_without_the_prefix_seal_is_refused_by_the_seal_not_the_binary(self):
        """T48 round 2 (Sol's R3, PR #151): the test above, as it was before T48, unchanged. Since T48
        `start_state.sha256` holds the binary's hash, which a walk measures whatever the session did,
        so the refusal must come from the prefix seal `start_state.restore` names now. This pins the
        cause: the record as the walk wrote it (no field rewritten) has a measured binary hash, and
        the error names the missing prefix seal."""
        with tempfile.TemporaryDirectory() as tmp:
            drive_one(tmp, "Q-UI-01", None, snapshot=False)
            (_path, record), = records_of(Path(tmp), "Q-UI-01")
            self.assertEqual(record["start_state"]["sha256"], hashlib.sha256(FAKE_BINARY).hexdigest(),
                             "T48: the binary's hash, whatever the session did")
            self.assertEqual(e019_records.prefix_seal(record["start_state"]["restore"]), "0" * 64)
            errors = [e for e in check(tmp) if "(Q-UI-01)" in e]
            self.assertTrue(any("no prefix seal" in e for e in errors), errors)

    def test_a_sealed_record_carries_its_prefix_seal_and_passes_the_seal_check(self):
        """The other side of the seal check: a walk that took its snapshot names a measured prefix
        listing in `start_state.restore`, and the check raises no seal error for it."""
        with tempfile.TemporaryDirectory() as tmp:
            drive_one(tmp, "Q-UI-01", None)
            (_path, record), = records_of(Path(tmp), "Q-UI-01")
            prefix = e019_records.prefix_seal(record["start_state"]["restore"])
            self.assertRegex(prefix or "", r"\A[0-9a-f]{64}\Z")
            self.assertNotEqual(prefix, "0" * 64)
            errors = [e for e in check(tmp) if "(Q-UI-01)" in e and "seal" in e]
            self.assertEqual(errors, [])

    def test_a_record_whose_binary_hash_measures_nothing_fails_the_check(self):
        """T48 (#149): the binary's hash in `start_state.sha256` is checked on its own too. A sealed
        walk whose binary hash is the all-zero placeholder is refused, by the start_state check."""
        with tempfile.TemporaryDirectory() as tmp:
            drive_one(tmp, "Q-UI-01", None)
            (path, _record), = records_of(Path(tmp), "Q-UI-01")
            rewrite(path, lambda r: r["start_state"].update(sha256="0" * 64))
            errors = check(tmp)
            self.assertTrue(any("(Q-UI-01)" in e and "no start_state sha256" in e for e in errors), errors)

    def test_the_real_tree_fails_while_the_walks_have_not_run(self):
        """While T39's batches are still being walked, the repository's own check fails, naming
        every question with no completed record yet."""
        errors = check_ui_catalogue.run_checks(ROOT, questions_path=QUESTIONS, inventory_path=INVENTORY)
        walked = set()
        records = [json.loads(path.read_text()) for path in (ROOT / "runs" / "E019").glob("*/*.json")]
        for record in records:
            if record.get("status") == "completed":
                walked |= {o["value"] for o in record["observations"] if o["field"] == "walk question"}
        pending = [qid for qid in catalogue_ids() if qid not in walked]
        if not pending:
            self.skipTest("every walk has a completed record")
        for qid in pending:
            aborted = any(
                record.get("status", "").startswith("aborted")
                and any(o["field"] == "walk question" and o["value"] == qid
                        for o in record.get("observations", []))
                for record in records
            )
            expected = "aborted" if aborted else "has not run"
            self.assertTrue(any(qid in e and expected in e for e in errors), (qid, errors))


def walk_order_first(qid):
    """The first size a question's walk runs at (None: the default size)."""
    return (walks.WALKS[qid].get("sizes") or [None])[0]


def drive_one(root, qid, size, **fake_options):
    """One walk, at one size, through run_walk into root."""
    locs = fake_locs(root)
    root = Path(root).resolve()
    clock = FakeClock()

    def factory(*args):
        return FakeSession(*args, clock=clock, workdir=root / "work", **fake_options)

    with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep), \
            contextlib.redirect_stdout(io.StringIO()):
        return run_walk.run_walk(qid, size, locs, ":99", "0123456789ab", "local", ["--test"], {"wine": "fake"},
                                 root=root, session_factory=factory)


# --- DW3: one regression per round-2 finding -------------------------------------------------------

class RoundTwoRegressionTest(unittest.TestCase):

    # R2: the recorder writes the per-question observation itself
    def test_r2_the_recorder_writes_the_per_question_observation(self):
        for qid in catalogue_ids():
            with self.subTest(qid=qid):
                (path, record), *_ = records_of(recorded_tree(), qid)
                values = [o["value"] for o in record["observations"] if o["field"] == "observation"]
                self.assertEqual(len(values), 1)
                summary = json.loads(values[0])
                self.assertEqual(summary["question"], qid)
                names = {o["name"] for o in record["outputs"]}
                self.assertTrue(set(summary["screenshots"]) <= names)

    # R3: Q-UI-06's flash candidates are never counted as events
    def test_r3_q_ui_06_never_emits_an_events_count(self):
        (path, record), = records_of(recorded_tree(), "Q-UI-06")
        fields = [o["field"] for o in record["observations"]]
        self.assertNotIn("count: events", fields)
        self.assertIn("count: flash candidates", fields)
        self.assertIn("count note: events", fields)

    def test_r3_the_check_refuses_an_events_count_and_an_observed_q_ui_06(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-06")[0]

            def rename(record):
                for o in record["observations"]:
                    if o["field"] == "count: flash candidates":
                        o["field"] = "count: events"
            rewrite(path, rename)
            write_f020(tmp, status_of={"Q-UI-06": "observed"})
            errors = check(tmp, f020=True)
            self.assertTrue(any("(Q-UI-06)" in e and "count: flash candidates" in e for e in errors), errors)
            self.assertTrue(any(e.startswith("Q-UI-06: F020 is observed") for e in errors), errors)

    def test_r3_one_tick_with_two_regions_changing_is_one_candidate(self):
        """Two countable regions changing in the same poll are one candidate, not two (a flash drawn
        over both is not two events)."""
        clock = FakeClock()
        session = FakeSession("E019-r0001", None, None, None, ":99", "q-ui-06", "800x600x24",
                              clock=clock, workdir=tempfile.mkdtemp(prefix="e019-r3-"))
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-06"], qid="Q-UI-06"))
        with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
            counted = run_walk.watch_regions(session, ctx, ["message-strip", "board-area"], 4.0, 1.0,
                                             flashes=True)
        shutil.rmtree(session.workdir.parent, ignore_errors=True)
        per_region = [json.loads(o["value"])["region"] for o in session.obs if o["field"] == "flash candidate"]
        self.assertEqual(per_region.count("message-strip"), per_region.count("board-area"))
        self.assertEqual(counted, per_region.count("board-area"))     # one per tick, not one per region
        self.assertGreater(counted, 0)

    # R4: the regions are polled together in one timed loop
    def test_r4_every_watched_region_is_polled_on_every_tick(self):
        clock = FakeClock()
        session = FakeSession("E019-r0001", None, None, None, ":99", "q-ui-13", "800x600x24",
                              clock=clock, workdir=tempfile.mkdtemp(prefix="e019-r4-"))
        reads = []
        raw = session._engine.screen.raw

        def counting(rect):
            reads.append(rect)
            return raw(rect)
        session._engine.screen.raw = counting
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-13"], qid="Q-UI-13"))
        labels = ["message-strip", "phase-panel", "board-area"]
        with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
            run_walk.watch_regions(session, ctx, labels, 25, 0.25, field="timing: computer turn change")
        shutil.rmtree(session.workdir.parent, ignore_errors=True)
        rects = [walks.REGIONS[label]["rect"] for label in labels]
        counts = [reads.count(rect) for rect in rects]
        self.assertEqual(counts[0], counts[1])
        self.assertEqual(counts[1], counts[2])
        self.assertGreater(counts[0], 90)                 # 25 s at 0.25 s: every region, every tick
        changed = {json.loads(o["value"])["region"] for o in session.obs
                   if o["field"] == "timing: computer turn change"}
        self.assertEqual(changed, set(labels))

    def test_r4_q_ui_13s_record_times_every_watched_region(self):
        (path, record), = records_of(recorded_tree(), "Q-UI-13")
        regions = {json.loads(o["value"])["region"] for o in record["observations"]
                   if o["field"] == "timing: computer turn change"}
        self.assertEqual(regions, {"message-strip", "phase-panel", "board-area"})

    def test_q_ui_13_reaches_the_turn_menu_before_pass_and_starts_watch_at_pass(self):
        clock = FakeClock()
        session = StatefulTurnSession("E019-r0001", None, None, None, ":99", "q-ui-13", "800x600x24",
                                      clock=clock, workdir=tempfile.mkdtemp(prefix="e019-q-ui-13-"))
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-13"], qid="Q-UI-13"))
        try:
            with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
                run_walk.composite_computer_turns(session, ctx, passes=1,
                                                  watch=["message-strip"], seconds=0.5, interval=0.25,
                                                  shots=False)
        finally:
            shutil.rmtree(session.workdir.parent, ignore_errors=True)

        self.assertEqual(session.pass_attempt_phases, ["menu"])
        self.assertEqual(len(session.accepted_pass_times), 1)
        self.assertEqual(ctx.counts["passes"], 1)
        timings = [json.loads(o["value"])["at_s"] for o in session.obs
                    if o["field"] == "timing: computer turn change"]
        self.assertTrue(timings)
        self.assertEqual(timings[0], 0.25)

    def test_q_ui_13_refused_placement_stops_without_counting_a_pass(self):
        clock = FakeClock()
        session = StatefulTurnSession("E019-r0001", None, None, None, ":99", "q-ui-13", "800x600x24",
                                      clock=clock, workdir=tempfile.mkdtemp(prefix="e019-q-ui-13-refused-"),
                                      refuse_placement=True)
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-13"], qid="Q-UI-13"))
        try:
            with mock.patch.object(run_walk, "CLOCK", clock.clock), mock.patch.object(run_walk, "SLEEP", clock.sleep):
                run_walk.composite_computer_turns(session, ctx, passes=1,
                                                  watch=["message-strip"], seconds=0.5, interval=0.25,
                                                  shots=False)
        finally:
            shutil.rmtree(session.workdir.parent, ignore_errors=True)

        self.assertEqual(session.pass_attempt_phases, [])
        self.assertEqual(session.accepted_pass_times, [])
        self.assertEqual(ctx.counts.get("passes", 0), 0)

    # R5: the display sizes are measured, and distinct sizes are required
    def test_r5_q_ui_19s_records_carry_each_measured_display_size(self):
        shown = set()
        for _, record in records_of(recorded_tree(), "Q-UI-19"):
            size = json.loads(next(o["value"] for o in record["observations"] if o["field"] == "display size"))
            w, h = (int(v) for v in size["requested"].split("x")[:2])
            self.assertEqual(size["display pixels"], w * h)
            shown.add(size["requested"])
        self.assertEqual(shown, set(walks.WALKS["Q-UI-19"]["sizes"]))

    def test_r5_four_records_at_one_size_do_not_cover_four_sizes(self):
        with Copy() as tmp:
            for path, _ in records_of(tmp, "Q-UI-19"):
                def one_size(record):
                    for o in record["observations"]:
                        if o["field"] == "display size":
                            o["value"] = json.dumps({"requested": "800x600x24", "display pixels": 480000})
                rewrite(path, one_size)
            errors = check(tmp)
            self.assertTrue(any(e.startswith("Q-UI-19: no completed record shows the display size 1024x768x24")
                                for e in errors), errors)

    def test_r5_a_size_not_measured_as_asked_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-19")[0]

            def wrong(record):
                for o in record["observations"]:
                    if o["field"] == "display size":
                        o["value"] = json.dumps({"requested": "640x480x24", "display pixels": 480000})
            rewrite(path, wrong)
            errors = check(tmp)
            self.assertTrue(any("(Q-UI-19)" in e and "measured 480000" in e for e in errors), errors)

    def test_r5_a_count_is_met_by_one_record_never_by_adding_records(self):
        with Copy() as tmp:
            path, record = records_of(tmp, "Q-UI-16")[0]
            half = dict(record)

            def low(r):
                for o in r["observations"]:
                    if o["field"] == "count: attacks":
                        o["value"] = "10"
            rewrite(path, low)
            # a second, otherwise identical record with 10 more: 10 + 10 must not make 20
            second = path.with_name("E019-r9999.json")
            half = json.loads(path.read_text(encoding="utf-8"))
            half["run_id"] = "E019-r9999"
            second.write_text(json.dumps(half), encoding="utf-8")
            manifest = Path(tmp) / "evidence" / "E019" / "play"
            shutil.copy(manifest / f"{path.stem}.manifest.json", manifest / "E019-r9999.manifest.json")
            errors = check(tmp)
            self.assertTrue(any(e.startswith("Q-UI-16: count attacks reached 10") for e in errors), errors)

    # R6: citations are checked on every record, aborted ones included
    def test_r6_an_aborted_record_citing_a_script_outside_the_inventory_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-05")[0]

            def abort_and_cite(record):
                record["status"] = "aborted: game-died: test"
                record["observations"].append({"step": 5, "source": "static", "field": "static sources cited",
                                               "value": "BehaviorScript 999 / nope()"})
            rewrite(path, abort_and_cite)
            errors = check(tmp)
            self.assertTrue(any("(Q-UI-05)" in e and "BehaviorScript 999" in e for e in errors), errors)
            self.assertTrue(any(e.startswith("Q-UI-05: no completed record") for e in errors), errors)

    def test_r6_an_aborted_record_of_the_wrong_set_or_without_a_manifest_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-05")[0]
            rewrite(path, lambda r: r.update(status="aborted: game-died: test",
                                             artifact={"set": "iw-dos-3.1-30121376", "variant": None}))
            (Path(tmp) / "evidence" / "E019" / "board-pieces" / f"{path.stem}.manifest.json").unlink()
            errors = [e for e in check(tmp) if "(Q-UI-05)" in e]
            self.assertTrue(any("artifact set" in e for e in errors), errors)
            self.assertTrue(any("manifest" in e for e in errors), errors)

    # R7: the recorder writes no absence statement
    def test_r7_the_absence_tour_read_is_the_screenshots_and_nothing_more(self):
        (path, record), = records_of(recorded_tree(), "Q-UI-14")
        values = [o["value"] for o in record["observations"] if o["field"] == "read: absence-tour"]
        self.assertEqual(len(values), 1)
        tour = json.loads(values[0])
        self.assertEqual(set(tour), {"screenshots", "count"})
        self.assertEqual(tour["count"], len(tour["screenshots"]))
        self.assertGreaterEqual(tour["count"], 9)

    def test_r7_no_recorder_value_asserts_an_absence_or_an_identification(self):
        """The class: across every walk's record, no value the recorder wrote states that something
        was seen, confirmed or identified."""
        words = ("confirmed", " seen", "no list-of-events", "award notice", "centre moves =", "events =")
        for path in sorted((recorded_tree() / "runs" / "E019").glob("*/E019-r*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            for o in record["observations"]:
                for word in words:
                    self.assertNotIn(word, o["value"], f"{path.name} {o['field']}")


# --- the checker's other refusals (round 1's classes), on the recorder's own tree -----------------

class CheckCatalogueTest(unittest.TestCase):

    def test_a_missing_question_fails_by_id(self):
        with Copy() as tmp:
            for path, _ in records_of(tmp, "Q-UI-06"):
                path.unlink()
            self.assertTrue(any(e.startswith("Q-UI-06: no completed record") for e in check(tmp)))

    def test_an_aborted_record_does_not_count_as_coverage(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-13")[0]
            rewrite(path, lambda r: r.update(status="aborted: game-died: test"))
            errors = check(tmp)
            self.assertTrue(any(e.startswith("Q-UI-13: no completed record") and "aborted" in e for e in errors))

    def test_a_count_below_the_target_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-04")[0]

            def low(record):
                for o in record["observations"]:
                    if o["field"] == "count: distinct screenshots":
                        o["value"] = "2"
            rewrite(path, low)
            self.assertTrue(any(e.startswith("Q-UI-04: count distinct screenshots reached 2") for e in check(tmp)))

    def test_a_count_that_is_not_a_number_or_is_given_twice_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-16")[0]
            rewrite(path, lambda r: r["observations"].append(
                {"step": 999, "source": "screen", "field": "count: attacks", "value": "5"}))
            self.assertTrue(any("(Q-UI-16)" in e and "one wanted" in e for e in check(tmp)))

    def test_an_observation_that_is_not_the_recorders_summary_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-10")[0]

            def hand_written(record):
                for o in record["observations"]:
                    if o["field"] == "observation":
                        o["value"] = "the walk looked fine"
            rewrite(path, hand_written)
            self.assertTrue(any("(Q-UI-10)" in e and "summary" in e for e in check(tmp)))

    def test_an_observation_naming_a_screenshot_the_record_lacks_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-01")[0]

            def extra(record):
                for o in record["observations"]:
                    if o["field"] == "observation":
                        summary = json.loads(o["value"])
                        summary["screenshots"].append("invented.png")
                        o["value"] = json.dumps(summary)
            rewrite(path, extra)
            self.assertTrue(any("(Q-UI-01)" in e and "invented.png" in e for e in check(tmp)))

    def test_a_record_without_its_manifest_fails(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-04")[0]
            (Path(tmp) / "evidence" / "E019" / "title-options" / f"{path.stem}.manifest.json").unlink()
            self.assertTrue(any("(Q-UI-04)" in e and "manifest" in e for e in check(tmp)))

    def test_an_output_missing_from_its_manifest_fails(self):
        with Copy() as tmp:
            path, record = records_of(tmp, "Q-UI-04")[0]
            manifest = Path(tmp) / "evidence" / "E019" / "title-options" / f"{path.stem}.manifest.json"
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["files"] = [f for f in doc["files"] if f["name"] != "before.png"]
            manifest.write_text(json.dumps(doc), encoding="utf-8")
            self.assertTrue(any("(Q-UI-04)" in e and "before.png" in e and "manifest" in e for e in check(tmp)))

    def test_a_pending_f020_section_fails(self):
        with Copy() as tmp:
            write_f020(tmp, status_of={"Q-UI-04": "pending the walk"})
            self.assertTrue(any(e.startswith("Q-UI-04: F020") for e in check(tmp, f020=True)))

    def test_an_observed_proxied_section_is_refused(self):
        for qid in sorted(PROXIED):
            with self.subTest(qid=qid), Copy() as tmp:
                write_f020(tmp, status_of={qid: "observed"})
                self.assertTrue(any(e.startswith(f"{qid}: F020 is observed") for e in check(tmp, f020=True)))

    def test_a_record_of_the_wrong_artifact_set_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-08")[0]
            rewrite(path, lambda r: r["artifact"].update(set="iw-dos-3.1-30121376"))
            self.assertTrue(any("artifact set" in e and "iw-dos" in e for e in check(tmp)))

    def test_the_successor_set_is_the_one_the_loss_walks_must_use(self):
        with Copy() as tmp:
            path, record = records_of(tmp, "Q-UI-04")[0]
            self.assertEqual(record["artifact"]["set"], e019_records.ARTIFACT_SET_SAVED_FILES)
            rewrite(path, lambda r: r["artifact"].update(set=e019_records.ARTIFACT_SET))
            self.assertTrue(any("(Q-UI-04)" in e and "artifact set" in e for e in check(tmp)))

    def test_a_record_with_the_wrong_variant_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-08")[0]
            rewrite(path, lambda r: r["artifact"].update(variant="registered"))
            self.assertTrue(any("variant" in e for e in check(tmp)))

    def test_a_manifest_of_the_wrong_artifact_set_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-08")[0]
            manifest = Path(tmp) / "evidence" / "E019" / "play" / f"{path.stem}.manifest.json"
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["artifact"]["set"] = "iw-dos-3.1-30121376"
            manifest.write_text(json.dumps(doc), encoding="utf-8")
            self.assertTrue(any("artifact set" in e and "iw-dos" in e for e in check(tmp)))

    def test_a_record_in_the_wrong_batch_folder_is_refused(self):
        with Copy() as tmp:
            path, _ = records_of(tmp, "Q-UI-08")[0]
            other = Path(tmp) / "runs" / "E019" / "events-end"
            shutil.move(str(path), str(other / path.name))
            self.assertTrue(any("sits in events-end" in e for e in check(tmp)))


# --- #140: F020's cited records, record sha256s and screenshot hashes ------------------------------

def section(path, qid):
    """One question's section of a written F020."""
    return _find_section(Path(path).read_text(encoding="utf-8"), qid).group(0)


def edit_section(path, qid, change):
    """Rewrite one question's section of a written F020 with `change` (the mutations of #140's
    tests); returns what change returned."""
    text = Path(path).read_text(encoding="utf-8")
    match = _find_section(text, qid)
    result = change(match.group(0))
    Path(path).write_text(text[:match.start()] + result + text[match.end():], encoding="utf-8")
    return result


def _find_section(text, qid):
    """The `#### <qid> ...` match of one question's section of a written F020, bounded as the
    check bounds it (#140 round 2): the next heading of level 2-4, or the end of the file."""
    match = re.search(r"^#### " + re.escape(qid) + r" .*?(?=^#{2,4} |\Z)", text, re.S | re.M)
    assert match, f"F020 has no section for {qid}"
    return match


class F020CitationRuleTest(unittest.TestCase):
    """#140: an observed or narrowed F020 section has to cite records that exist under the root
    being checked, with sha256 prefixes that are theirs, and hashes that belong to them. Each
    test writes the catalogue the recorder's own tree needs (write_f020) and mutates one section
    of it, as the issue's mutations do; (e) and (f) pin the citations the rule must not touch,
    and carry a second section with the one error only this rule can produce, because a rule that
    only adds errors has no test that fails on main's check without one."""

    def test_a_wrong_record_sha_prefix_fails_with_error_2(self):
        with Copy() as tmp:
            path = write_f020(tmp)
            record_path = records_of(tmp, "Q-UI-04")[0][0]
            good = hashlib.sha256(record_path.read_bytes()).hexdigest()[:16]
            self.assertIn(f"`{good}\u2026`", section(path, "Q-UI-04"))
            edit_section(path, "Q-UI-04",
                         lambda body: body.replace(f"`{good}\u2026`", f"`{'0' * 16}\u2026`"))
            errors = check(tmp, f020=True)
            self.assertEqual(len(errors), 1, errors)              # error 2, and nothing else
            self.assertIn(f"cites runs/E019/title-options/{record_path.stem}.json with sha256 "
                          f"{'0' * 16}\u2026, which is not a prefix of the file's sha256", errors[0])

    def test_a_screenshot_hash_of_no_cited_record_fails_with_error_4(self):
        with Copy() as tmp:
            path = write_f020(tmp)

            def replace_shot_sha(body):
                text, n = re.subn(r"(\*\*Screenshot\*\*: `[^`]+` \(sha256 `)[0-9a-f]{8,64}(\u2026`)",
                                  lambda m: m.group(1) + "f" * 16 + m.group(2), body, count=1)
                self.assertEqual(n, 1, body)
                return text
            edit_section(path, "Q-UI-04", replace_shot_sha)
            errors = check(tmp, f020=True)
            self.assertEqual(len(errors), 1, errors)              # error 4, and nothing else
            self.assertIn(f"cites the hash {'f' * 16}\u2026, which is neither a record sha", errors[0])

    def test_a_cited_record_path_that_does_not_exist_fails_with_error_1(self):
        with Copy() as tmp:
            path = write_f020(tmp)
            record_path = records_of(tmp, "Q-UI-04")[0][0]
            fake = record_path.with_name("E019-r9999.json").relative_to(Path(tmp)).as_posix()
            self.assertFalse((Path(tmp) / fake).exists())
            edit_section(path, "Q-UI-04",
                         lambda body: body.replace("**Run**:", f"**Run**: `{fake}` and", 1))
            errors = check(tmp, f020=True)
            self.assertEqual(len(errors), 1, errors)              # error 1, and nothing else
            self.assertIn(f"cites {fake}, which does not exist", errors[0])

    def test_an_observed_section_citing_a_record_without_any_sha_fails_with_error_3(self):
        with Copy() as tmp:
            path = write_f020(tmp)
            record_path = records_of(tmp, "Q-UI-04")[0][0]
            good = hashlib.sha256(record_path.read_bytes()).hexdigest()[:16]

            def drop_record_sha(body):
                text, n = re.subn(r" \(sha256 `[0-9a-f]{8,64}\u2026`\)", "", body, count=1)
                self.assertEqual(n, 1, body)
                return text
            edit_section(path, "Q-UI-04", drop_record_sha)
            self.assertNotIn(good, section(path, "Q-UI-04"))   # the record's sha is no longer cited
            errors = check(tmp, f020=True)
            self.assertEqual(len(errors), 1, errors)              # error 3, and nothing else
            self.assertIn("cites no record with its sha256 (T39's DW2 requires the record's sha)",
                          errors[0])

    def test_a_bare_name_citation_and_a_driver_id_are_not_citations(self):
        """(e) Q-UI-19 cites its two aborted attempts by bare file name and every run's driver
        beside its sha: neither is a record citation (a bare name is not a path under the root)
        nor a hash citation (the driver id has no ellipsis), so neither draws an error. The rule
        only adds errors, so the second section — those same two citations and no record path —
        is the control that makes this fail on main's check: the whole check's output is that
        one error 3, with no error 1 or 4 among it, and none of it on Q-UI-04."""
        with Copy() as tmp:
            path = write_f020(tmp)
            for bare in ("E019-r0005.json", "E019-r0009.json"):
                self.assertFalse((Path(tmp) / bare).exists())
            citations = ("Aborted attempts: `E019-r0005.json`, `E019-r0009.json`; "
                         "driver `e257bb1b395a`.")
            edit_section(path, "Q-UI-04",
                         lambda body: body.replace("described from the records.",
                                                   "described from the records. " + citations, 1))
            edit_section(path, "Q-UI-10",
                         lambda body: re.sub(r"^- \*\*Run\*\*:.*$", citations, body,
                                             count=1, flags=re.M))
            errors = check(tmp, f020=True)
            self.assertEqual([e for e in errors if e.startswith("Q-UI-04:")], [], errors)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("Q-UI-10: F020 cites no record with its sha256", errors[0])

    def test_a_pending_section_with_no_citations_is_not_checked(self):
        """(f) The rule reads observed and narrowed sections only: a pending section with no
        citations draws no citation error of its own (the pre-existing status rule still refuses
        it, which test_a_pending_f020_section_fails pins). The second section is the same
        citation-less shape on an observed question — error 3, the control that makes this fail
        on main's check."""
        with Copy() as tmp:
            path = write_f020(tmp, status_of={"Q-UI-08": "pending the walk",
                                              "Q-UI-12": "observed"})
            edit_section(path, "Q-UI-12",
                         lambda body: re.sub(r"^- \*\*Run\*\*:.*\n", "", body, count=1, flags=re.M))
            errors = check(tmp, f020=True)
            cited = [e for e in errors if ": F020 cites" in e]
            self.assertEqual([e for e in cited if e.startswith("Q-UI-08:")], [], errors)
            self.assertEqual(len(cited), 1, errors)               # the control, on Q-UI-12
            self.assertIn("Q-UI-12: F020 cites no record with its sha256", cited[0])
            self.assertTrue(any(e.startswith("Q-UI-08: F020's Observation line has no status")
                                for e in errors), errors)         # the pre-existing status rule


# --- #140 rework rounds 2 and 3: the blocking findings, and the section bound -----------------------

class F020CitationRuleRoundTwoTest(unittest.TestCase):
    """#140's rework round 2 (Sol's R1 and R2): a hash citation is checked against the sha256
    computed from a cited record's file, never against the cited sha text (R1), and every
    backticked token holding a record name is one of the two forms the rule allows (R2), and the
    section stops at the next heading of level 2-4 instead of running to the end of the file.
    Round 3's R1 (the finding of round 2's review) is r1c and r1d: a record cited without a sha
    lends its outputs to error 4's pool, never its own digest, and the digest is exempted only for
    a record cited with a sha that passed error 2.

    Each test writes the catalogue the recorder's tree needs (write_f020) and keeps a valid record
    citation in the section beside the mutation — a path that exists and, unless the sha is what
    it mutates, its real sha256 and a real screenshot hash — so errors 1 and 3 stay out and cannot
    mask the gap (Sol's R2 note). A test that expects an error fails on main's check, which has no
    citation rule at all; where a test expects none — r1d and the section bound — a second section
    carries the one error only this rule produces, so it fails there too, as tests (e) and (f)
    already do."""

    def test_r1a_a_cited_record_prefix_with_an_invented_suffix_fails(self):
        """R1: the cited record prefix extended by an invented suffix is not a prefix of the
        record file's sha256, so it is no record's sha and no output's."""
        with Copy() as tmp:
            path = write_f020(tmp)
            record_path = records_of(tmp, "Q-UI-04")[0][0]
            digest = hashlib.sha256(record_path.read_bytes()).hexdigest()
            fabricated = digest[:16] + "deadbeef"
            edit_section(path, "Q-UI-04", lambda body: body.rstrip("\n")
                         + f"\n- **Screenshot**: `invented.png` (sha256 `{fabricated}\u2026`)\n")
            errors = check(tmp, f020=True)
            self.assertEqual(len(errors), 1, errors)          # error 4, and nothing else
            self.assertIn(f"cites the hash {fabricated}\u2026, which is neither a record sha",
                          errors[0])

    def test_r1b_a_shorter_hash_prefixing_the_cited_sha_but_not_the_file_fails(self):
        """R1: a hash shorter than the cited sha text, prefixing that text but not the file's
        digest. Round 1 exempts it with `sha.startswith(h)`; the digest rule refuses it. The
        section's record path keeps its own citation, so error 2 is the one companion line it
        draws: a sha cited beside a record path that is no prefix of that file's sha256 is error 2
        whatever else the text is, and a shorter hash prefixing such a text cannot be a prefix of
        the file either. The screenshot citation stays valid, so no error 1 and no error 3.

        The Run line is rewritten into the shape F020 really uses — `(sha256 `hex…`, driver
        `…`, display …)` — so the sha field is read out of the repository's own text and not only
        out of write_f020's shorter one; were it not read, the section would cite no record sha and
        error 3 would appear instead of error 2."""
        with Copy() as tmp:
            path = write_f020(tmp)
            record_path = records_of(tmp, "Q-UI-04")[0][0]
            digest = hashlib.sha256(record_path.read_bytes()).hexdigest()
            wrong, short = "5" * 16, "5" * 8
            self.assertFalse(digest.startswith(wrong))
            real_shape = (f"(sha256 `{wrong}\u2026`, driver `e257bb1b395a`, "
                          "display 800x600x24, 42.56 s)")
            edit_section(path, "Q-UI-04",
                         lambda body: body.replace(f"(sha256 `{digest[:16]}\u2026`)", real_shape, 1))
            self.assertIn(real_shape, section(path, "Q-UI-04"))
            edit_section(path, "Q-UI-04", lambda body: body.rstrip("\n")
                         + f"\n- **Screenshot**: `shorter.png` (sha256 `{short}\u2026`)\n")
            errors = check(tmp, f020=True)
            self.assertEqual(len(errors), 2, errors)
            self.assertTrue(any("which is not a prefix of the file's sha256" in e for e in errors),
                            errors)                            # error 2, the cited sha text
            hashes = [e for e in errors if "cites the hash" in e]
            self.assertEqual(len(hashes), 1, errors)           # error 4, the shorter hash alone
            self.assertIn(f"cites the hash {short}\u2026", hashes[0])

    def test_r1c_a_genuine_longer_prefix_of_a_record_cited_without_its_sha_fails_with_error_4(self):
        """R1, round 3 (the finding of round 2's review): a hash that really is a longer prefix of
        a record file's sha256, where the record is cited by full path *without* its sha (as
        Q-UI-19 cites records). Nothing in the section vouches for that digest — the record's sha
        was never cited — so it must not pass as a screenshot hash: error 4 draws the line. Round 2
        exempts it (every cited file's digest was in the pool), so this test fails on c519370 with
        no error at all; main's check has no citation rule at all, so it fails there with no error
        either. The same hash on the same record passes when the record cites its sha — r1d below."""
        with Copy() as tmp:
            path = write_f020(tmp)
            cited_path = records_of(tmp, "Q-UI-04")[0][0]
            other = [p for p in sorted((Path(tmp) / "runs" / "E019").glob("*/E019-r*.json"))
                     if p != cited_path][0]
            longer = hashlib.sha256(other.read_bytes()).hexdigest()[:32]
            self.assertFalse(hashlib.sha256(cited_path.read_bytes()).hexdigest().startswith(longer))
            edit_section(path, "Q-UI-04", lambda body: body.rstrip("\n")
                         + f"\n- **Also**: `{other.relative_to(Path(tmp)).as_posix()}`"
                         + f"\n- **Screenshot**: `second.png` (sha256 `{longer}\u2026`)\n")
            errors = check(tmp, f020=True)
            self.assertEqual(len(errors), 1, errors)          # error 4, and nothing else
            self.assertTrue(errors[0].startswith("Q-UI-04:"), errors)
            self.assertIn(f"cites the hash {longer}\u2026, which is neither a record sha", errors[0])

    def test_r1d_a_genuine_longer_prefix_of_a_record_cited_with_its_sha_passes(self):
        """R1, round 3: the same hash on the same record passes when the record is cited with its
        (valid) sha — error 4 exempts a record's digest only when the record was cited with a sha
        that is that file's own (error 2 passed), which is the vouching r1c says is missing above.
        Removing the lending entirely fails this test (error 4 would then draw a line for a hash
        the signed citation vouches for). The control section carries a hash no record backs: the
        error only this rule produces, which makes the test fail on main's check."""
        with Copy() as tmp:
            path = write_f020(tmp)
            cited_path = records_of(tmp, "Q-UI-04")[0][0]
            other = [p for p in sorted((Path(tmp) / "runs" / "E019").glob("*/E019-r*.json"))
                     if p != cited_path][0]
            digest = hashlib.sha256(other.read_bytes()).hexdigest()
            longer = digest[:32]
            self.assertFalse(hashlib.sha256(cited_path.read_bytes()).hexdigest().startswith(longer))
            edit_section(path, "Q-UI-04",
                         lambda body: body.rstrip("\n")
                         + f"\n- **Also**: `{other.relative_to(Path(tmp)).as_posix()}` "
                           f"(sha256 `{digest[:16]}\u2026`)"
                         + f"\n- **Screenshot**: `second.png` (sha256 `{longer}\u2026`)\n")
            edit_section(path, "Q-UI-10", lambda body: body.rstrip("\n")
                         + f"\n- **Screenshot**: `invented.png` (sha256 `{'f' * 16}\u2026`)\n")
            errors = check(tmp, f020=True)
            self.assertEqual([e for e in errors if e.startswith("Q-UI-04:")], [], errors)
            self.assertEqual(len(errors), 1, errors)          # the control, on Q-UI-10
            self.assertTrue(errors[0].startswith("Q-UI-10:"), errors)

    def test_r2a_a_record_path_with_a_traversal_component_fails_with_error_5(self):
        """R2: `../` is neither the strict full path nor the bare name."""
        self._assert_error_5("runs/E019/../E019-r9999.json")

    def test_r2b_a_record_path_outside_runs_e019_fails_with_error_5(self):
        """R2: a full path outside runs/E019 is not a record citation of this rule."""
        self._assert_error_5("runs/E004/E019-r9999.json")

    def test_r2c_a_record_path_with_a_two_segment_batch_fails_with_error_5(self):
        """R2: the batch is exactly one path segment, so a deeper path is refused."""
        self._assert_error_5("runs/E019/title-options/extra/E019-r9999.json")

    def _assert_error_5(self, bad):
        with Copy() as tmp:
            path = write_f020(tmp)
            edit_section(path, "Q-UI-04",
                         lambda body: body.rstrip("\n") + f"\n- **Also**: `{bad}`\n")
            errors = check(tmp, f020=True)
            self.assertEqual(len(errors), 1, errors)          # error 5, and nothing else
            self.assertIn("cites a record path outside runs/E019/<batch>/ or malformed",
                          errors[0])
            self.assertIn(bad, errors[0])

    def test_a_section_ends_at_the_next_heading_of_level_two_to_four(self):
        """The section bound: a section ran to the next `#### ` heading or the end of the file,
        so the last one (Q-PLY-04 in a written catalogue, Q-UI-18 in F020) also took in the `##`
        sections after it. The hash under `## Evidence` belongs to no question section now; the
        control on Q-UI-10 is the error only this rule produces, which makes the test fail on
        main's check, while the Q-PLY-04 assertion makes it fail on round 1's."""
        with Copy() as tmp:
            path = write_f020(tmp)
            with Path(path).open("a", encoding="utf-8") as fh:
                fh.write(f"\n## Evidence\n- a hash no record backs: `{'f' * 16}\u2026`\n")
            edit_section(path, "Q-UI-10", lambda body: body.rstrip("\n")
                         + f"\n- **Screenshot**: `invented.png` (sha256 `{'f' * 16}\u2026`)\n")
            errors = check(tmp, f020=True)
            self.assertEqual([e for e in errors if e.startswith("Q-PLY-04:")], [], errors)
            self.assertEqual(len(errors), 1, errors)          # the control, on Q-UI-10
            self.assertTrue(errors[0].startswith("Q-UI-10:"), errors)


class RecorderUnitTest(unittest.TestCase):
    def test_manifest_maps_engine_frame_class_to_recording_without_changing_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            frame = Path(tmp) / "frame.png"
            log = Path(tmp) / "walk.log"
            frame.write_bytes(b"frame bytes")
            log.write_bytes(b"walk log bytes")
            outputs = [("frame.png", frame, "screenshot"), ("walk.log", log, "measurement")]

            manifest = e019_records.build_manifest("E019-r9902", outputs, e019_records.ARTIFACT_SET)
            expected = [{"name": name, "bytes": path.stat().st_size,
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "asset": f"{hashlib.sha256(path.read_bytes()).hexdigest()[:16]}-{name}",
                         "class": expected_class}
                       for (name, path, _), expected_class in zip(outputs, ("recording", "measurement"))]
        self.assertEqual(manifest["files"], expected)

    def test_a_shot_step_increments_the_live_screenshot_count(self):
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-14"], qid="Q-UI-14"))
        session = mock.Mock()
        run_walk.perform(session, ctx, "shot something")
        self.assertEqual((ctx.shots, ctx.shot_names), (1, ["something.png"]))

    def test_a_click_any_group_increments_the_attempt_count(self):
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-09"], qid="Q-UI-09"))
        run_walk.perform(mock.Mock(), ctx, "click-any? 400 300 100 100 700 200")
        self.assertEqual(ctx.attempts, 1)

    def test_distinct_shots_counts_distinct_pixels_not_shots(self):
        ctx = run_walk.Ctx(dict(walks.WALKS["Q-UI-04"], qid="Q-UI-04"))
        ctx.shot_names = ["a.png", "b.png", "c.png"]
        session = mock.Mock()
        session.obs = [{"field": "a.png raw RGB8 pixels sha256", "value": "1" * 64},
                       {"field": "b.png raw RGB8 pixels sha256", "value": "1" * 64},
                       {"field": "c.png raw RGB8 pixels sha256", "value": "2" * 64}]
        self.assertEqual(run_walk.measured_count(session, ctx), 2)


# --- T48 (#149): the carve-out platform, the binary's hash and the schema -------------------------

class WineRecordTest(unittest.TestCase):
    """T48 (#149): what a walk's record says about the Wine run (Done-when 3).

    Three things, each with the mutation it kills: the carve-out's platform (a legacy token would
    sail past constraint F unverified), `start_state.sha256` equal to the *fake install's* fake
    binary hashed (a constant, the prefix listing or the run copy would not match), and the whole
    document accepted by the pinned run/1 schema. Two different byte strings are fed in turn, so
    neither the record nor the hasher can be a constant. The recorder-driven half — run_walk passing
    that hash into this builder — is pinned by the start-state test above, which reads the record
    a fake walk wrote.
    """

    def build(self, install, blob, prefix_sha="0" * 64):
        """(binary_sha, record) of one fake install whose `Islepro.exe` is `blob`."""
        install = Path(install)
        install.mkdir(parents=True, exist_ok=True)
        (install / e019_records.BINARY).write_bytes(blob)
        binary_sha = e019_records.binary_sha256(install)
        spec = {"qid": "Q-UI-01", "batch": "title-options"}
        record = e019_records.build_record(
            "E019-r9901", spec, ["--test"], "0123456789ab", "local", prefix_sha, binary_sha,
            {"wine": "wine-9.0"},
            [{"step": 0, "source": "static", "field": "walk question", "value": "Q-UI-01"}],
            [], "2026-10-08T00:00:00Z", "2026-10-08T00:01:00Z", "completed", 60.0,
            e019_records.ARTIFACT_SET, root=install.parent)
        return binary_sha, record

    def test_the_record_names_the_carve_out_platform_the_binarys_hash_and_validates(self):
        hashes = []
        for blob in (b"fake binary A", b"fake binary B"):
            with self.subTest(blob=blob), tempfile.TemporaryDirectory() as tmp:
                binary_sha, record = self.build(Path(tmp) / "install", blob)
                hashes.append(record["start_state"]["sha256"])
                self.assertEqual(record["runtime"]["platform"], "wine-on-user-machine-iwp-2.0")
                self.assertEqual(record["artifact"]["variant"], "unregistered")
                self.assertEqual(record["start_state"]["sha256"], hashlib.sha256(blob).hexdigest())
                self.assertEqual(record["start_state"]["sha256"], binary_sha)
                self.assertEqual(test_runs.validate_records.validate_document(record), [])
        self.assertNotEqual(hashes[0], hashes[1], "the hash is measured, never a constant")

    def test_the_platform_is_one_the_wine_gate_recognises(self):
        """The recorder and the gate may not drift apart (#149): a token the gate does not recognise
        would make every record this recorder writes a refusal, and a token it no longer recognises
        would let them through unchecked."""
        self.assertTrue(cno.recognised_wine_platform(e019_records.PLATFORM), e019_records.PLATFORM)
        self.assertEqual(e019_records.PLATFORM, "wine-on-user-machine-iwp-2.0")

    def test_the_prefix_listings_hash_is_named_in_restore_not_dropped(self):
        """T48 moved what `start_state.sha256` held until now (the prefix listing's hash) where the
        schema allows it: named in `start_state.restore`. Rule 20: nothing measured is dropped."""
        prefix_sha = "c" * 64
        with tempfile.TemporaryDirectory() as tmp:
            _, record = self.build(Path(tmp) / "install", FAKE_BINARY, prefix_sha=prefix_sha)
        self.assertIn(prefix_sha, record["start_state"]["restore"])
        self.assertNotEqual(record["start_state"]["sha256"], prefix_sha)
        self.assertEqual(test_runs.validate_records.validate_document(record), [])


if __name__ == "__main__":
    unittest.main()
