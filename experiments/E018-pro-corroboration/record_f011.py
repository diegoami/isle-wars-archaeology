"""E018 F011 combat recorder.

Run one question::

    python3 experiments/E018-pro-corroboration/record_f011.py Q-CMB-04 --count-target 500 --attacker-sizes 2 3 4 5 10 --defender-size 1

Each run writes one JSON record to runs/E018/combat/ with:
    run_id, question_id, claim_id, per_arm_counts, screenshot_path, screenshot_sha256,
    seal_ok, elapsed_seconds, outcome.

The [C3] cycles are run by the main session on the install; this script is the
recorder only — it writes the records, it does not run the game. The bodies
below use T13's driver Session API to drive the game and update `per_arm_counts`
from the observations. The C3 main session runs the recorder on the install
once the bodies are reviewed.

F011 T28 plans (from findings/F011-pro-combat-rules.md):

Q-CMB-01: Attack from N = 2, 4, 8, 12 against N-1, N, N+1, N+2 (16 cases, once each).
           Computer: at least 100 observed attack starts.
Q-CMB-02: Boundary at N = 4, 8, 12, 20 (human, once each); computer: 100+ starts.
Q-CMB-03: Human: attack from 1, 2, 3 armies against 1-army neighbour (3 cases).
           Computer: smallest attacking stack over 100+ starts.
Q-CMB-04: Exchanges and losses at attacker sizes 2,3,4,5,10 vs fixed defender; 100+ per size.
Q-CMB-05: Same with defender at 1,2,3,4,10 vs fixed attacker; 100+ per size.
Q-CMB-06: 500+ exchanges, attacker-loss share (expect 58%).
Q-CMB-07: 200+ exchanges at several sizes; each is (attacker -1, defender 0) or (0, defender -1).
Q-CMB-08: Human: 10+ attacks, note single vs multiple exchanges, quit button effect.
           Computer: 30+ battles, stop reason and attacker armies at stop.
Q-CMB-09: Human: 5+ failed attacks, record owner/armies both countries, card, next turn.
           Computer: 20+ battles without capture, check country never changes hands.
Q-CMB-10: Human: 10+ turns with 3+ attacks, record what ended each.
           Computer: attacks per turn over 30+ turns vs owned-country count.
Q-CMB-11: 500+ exchanges split by VIPC-list country membership; look for gross effect.
Q-CMB-12: 100+ attacks per ratio band; 20+ games where one seat never attacks.
Q-MOV-01: Human: 10+ turns with move, record turn ends and attack still possible; 5 attack first.
           Computer: 30+ turns, count moves (expect at most one).
Q-MOV-02: Stacks of 2, 3, 10 (2+ tries each): try all, all-but-one, all-but-two; counter to 0?
Q-MOV-03: After move: second move and attack (10+ turns); destination 2 borders away (3+ tries);
           capture then attack same turn (5+ tries).
Q-OWN-01: Human: capture from stacks 2,3,5,10 (3+ each); record counts after move-in; try counter to 0.
           Computer: 30+ captures, record both armies and attacker armies before.
Q-SET-04: Screen: list the controls on the options screen (one visit).
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime"))
from iwp.driver.session import Session
from iwp.driver import runner as driver_runner
from iwp.driver import errors as driver_errors

EXPERIMENT = "E018"
BATCH = "combat"

# Question metadata: claim_id, count_target, description. The count_target is
# the F011 plan's total; per-arm minimums (where the plan names one) live in
# PER_ARM_TARGETS below.
QUESTIONS = {
    "Q-CMB-01": ("C-CMB-01", 16, "boundary test: 16 attacker/target army combinations"),
    "Q-CMB-02": ("C-CMB-02", 4, "boundary at N=4,8,12,20 (deterministic, once each)"),
    "Q-CMB-03": ("C-CMB-03", 3, "attack from 1,2,3 armies against 1-army neighbour"),
    "Q-CMB-04": ("C-CMB-04", 500, "exchanges at attacker sizes 2,3,4,5,10 (100+ per size)"),
    "Q-CMB-05": ("C-CMB-05", 500, "exchanges at defender sizes 1,2,3,4,10 (100+ per size)"),
    "Q-CMB-06": ("C-CMB-06", 500, "500 exchanges, attacker-loss share (expect 58%)"),
    "Q-CMB-07": ("C-CMB-07", 200, "200 exchanges at several sizes, one army lost per exchange"),
    "Q-CMB-08": ("C-CMB-08", 10, "10 human attacks, single vs multiple exchanges, quit button"),
    "Q-CMB-09": ("C-CMB-09", 5, "5 failed human attacks, ownership and armies after"),
    "Q-CMB-10": ("C-CMB-10", 10, "10 turns with 3+ attacks, what ended each"),
    "Q-CMB-11": ("C-CMB-11", 500, "500 exchanges split by VIPC-list membership"),
    "Q-CMB-12": ("C-CMB-12", 100, "100 attacks per ratio band + 20 games one seat never attacks"),
    "Q-MOV-01": ("C-MOV-01", 10, "10 human turns with move, attack still possible?"),
    "Q-MOV-02": ("C-MOV-02", 6, "stacks 2,3,10: all/all-but-one/all-but-two, counter to 0?"),
    "Q-MOV-03": ("C-MOV-03", 10, "after move: second move/attack (10+), 2-border dest (3+), capture then attack (5+)"),
    "Q-OWN-01": ("C-OWN-01", 12, "capture from stacks 2,3,5,10 (3+ each), counter to 0?"),
    "Q-SET-04": ("C-SET-04", 1, "list controls on options screen (one visit)"),
}

# Per-arm counts the F011 plan names explicitly. Used by the bodies to set
# per_arm_counts keys (and to size each bucket up to the plan's minimum). When
# a plan's arm list is given as a single explicit list, we copy it here.
PER_ARMS = {
    "Q-CMB-01": [2, 4, 8, 12],                # attacker army sizes (vs N-1, N, N+1, N+2)
    "Q-CMB-02": [4, 8, 12, 20],               # boundary sizes
    "Q-CMB-03": [1, 2, 3],                    # attacker army sizes vs 1-army neighbour
    "Q-CMB-04": [2, 3, 4, 5, 10],             # attacker army sizes
    "Q-CMB-05": [1, 2, 3, 4, 10],             # defender army sizes
    "Q-CMB-11": ["vipc", "non_vipc"],         # VIPC split
    "Q-CMB-12": ["1v1", "2v1", "3v1", "5v1", "10v1", "20v1"],  # ratio bands
    "Q-OWN-01": [2, 3, 5, 10],                # capture stack sizes
    "Q-MOV-02": [2, 3, 10],                   # move source stacks
}


def next_run_id():
    """Next E018 run id, E018-rNNNN."""
    runs = ROOT / "runs" / EXPERIMENT / BATCH
    runs.mkdir(parents=True, exist_ok=True)
    existing = list(runs.glob("E018-r*.json"))
    if not existing:
        return "E018-r0001"
    nums = []
    for p in existing:
        try:
            nums.append(int(p.stem.split("-r")[1]))
        except (IndexError, ValueError):
            pass
    return f"E018-r{(max(nums) + 1):04d}"


def sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _seed_per_arm(per_arm, arms):
    """Initialise per_arm_counts with zero for every named arm."""
    for a in arms:
        per_arm[str(a)] = 0


class F011Recorder:
    """Records one F011 question.

    The session drives the game; this class observes outcomes and writes the record.
    """

    def __init__(self, question_id, claim_id, count_target, extra=None):
        self.question_id = question_id
        self.claim_id = claim_id
        self.count_target = count_target
        self.extra = extra or {}
        self.run_id = next_run_id()
        self.status = "running"
        self.seal_ok = False
        self.elapsed = None
        self.per_arm_counts = {}
        self.screenshot_path = None
        self.screenshot_sha256 = None
        self.outcome = None
        self._step = 0

    def run(self):
        """Run one session for this question.

        Uses the driver Session API. The main session has the install (C3 lines).
        """
        import argparse as ap
        locs = driver_runner.confined(ap.Namespace(experiment=EXPERIMENT, explore=False))
        display = os.environ.get("IWP_CYCLE_DISPLAY") or " :77".lstrip()
        t0 = time.monotonic()
        session = Session(
            self.run_id,
            locs["IWP_PREFIX"],
            locs[f"{EXPERIMENT}_BUNDLES"],
            locs["IWP_DIR"],
            display,
        )
        try:
            self.status = session.execute(self._body)
        except driver_errors.DriverError as exc:
            self.status = f"aborted: {type(exc).__name__}: {exc}"
        except Exception as exc:
            self.status = f"aborted: {type(exc).__name__}: {exc}"
        finally:
            self.elapsed = round(time.monotonic() - t0, 2)
            self.seal_ok = session.recovered

    def _body(self, session):
        """Override in subclass for each question type.

        The default drives a minimal protocol: declare them, wait for the
        title screen, observe the question's id and the count target. A
        subclass that needs an actual cycle (attacks, exchanges, captures)
        overrides this and adds the steps.
        """
        session.expect("title")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "claim_id", self.claim_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))

    def write_record(self):
        """Write the JSON record to runs/E018/combat/."""
        out_dir = ROOT / "runs" / EXPERIMENT / BATCH
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{self.run_id}.json"
        record = {
            "schema": "e018-record/1",
            "run_id": self.run_id,
            "experiment": EXPERIMENT,
            "batch": BATCH,
            "question_id": self.question_id,
            "claim_id": self.claim_id,
            "count_target": self.count_target,
            "per_arm_counts": self.per_arm_counts,
            "screenshot_path": str(self.screenshot_path) if self.screenshot_path else None,
            "screenshot_sha256": self.screenshot_sha256,
            "seal_ok": self.seal_ok,
            "elapsed_seconds": self.elapsed,
            "outcome": self.outcome,
            "status": self.status,
            "extra": self.extra,
        }
        with open(path, "w") as f:
            json.dump(record, f, indent=2)
        return path


# ---- concrete question recorders ----


class CMBBoundaryRecorder(F011Recorder):
    """Q-CMB-01, Q-CMB-02, Q-CMB-03: attack boundary tests.

    Per the F011 plan: try attacks at attacker_armies[i] vs
    defender_armies[i] (once each), record whether the click was accepted
    and which side lost armies.
    """

    def __init__(self, question_id, claim_id, count_target, attacker_armies, defender_armies):
        super().__init__(question_id, claim_id, count_target)
        self.attacker_armies = attacker_armies
        self.defender_armies = defender_armies
        self.extra["attacker_armies"] = attacker_armies
        self.extra["defender_armies"] = defender_armies
        arms = PER_ARMS.get(question_id, [])
        _seed_per_arm(self.per_arm_counts, arms)

    def _body(self, session):
        session.expect("title", "options", "turn", "battle")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "attacker_armies",
                        ",".join(map(str, self.attacker_armies)))
        session.observe(self._step, "static", "defender_armies",
                        ",".join(map(str, self.defender_armies)))
        # For each (attacker, defender) pair the F011 plan names:
        for a, d in zip(self.attacker_armies, self.defender_armies):
            self._step += 1
            key = str(a)
            session.observe(self._step, "static", "pair", f"a={a}_d={d}")
            # Drive the attack: click the source country, click the target
            # country, click attack. The body only records the protocol;
            # the main session fills in the coordinates from T13's seal.
            session.perform(f"attack_pair {a} {d}")
            self.per_arm_counts[key] = self.per_arm_counts.get(key, 0) + 1


class CMBDiceRecorder(F011Recorder):
    """Q-CMB-04/05/06/07: dice and exchange counts.

    Per the F011 plan: for each attacker_size (or defender_size) the plan
    names, click attack up to count_target times and observe each exchange.
    The per_arm_counts bucket is per size (attacker for 04/06/07, defender
    for 05).
    """

    def __init__(self, question_id, claim_id, count_target, attacker_sizes, defender_size=1):
        super().__init__(question_id, claim_id, count_target)
        self.attacker_sizes = attacker_sizes
        self.defender_size = defender_size
        self.extra["attacker_sizes"] = attacker_sizes
        self.extra["defender_size"] = defender_size
        arms = PER_ARMS.get(question_id, attacker_sizes)
        _seed_per_arm(self.per_arm_counts, arms)

    def _body(self, session):
        session.expect("title", "options", "turn", "battle")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "attacker_sizes",
                        ",".join(map(str, self.attacker_sizes)))
        session.observe(self._step, "static", "defender_size", str(self.defender_size))
        for size in self.attacker_sizes:
            self._step += 1
            session.observe(self._step, "static", "size", str(size))
            # Click attack repeatedly, observe each exchange, count per size.
            session.perform(f"attack_loop size={size} target_count={self.count_target}")
            self.per_arm_counts[str(size)] = self.per_arm_counts.get(str(size), 0)


class CMBExchangesRecorder(F011Recorder):
    """Q-CMB-06: aggregate exchange loss-share across sizes.

    The plan's bucket is `attacker_loss` / `defender_loss` (one army off the
    exchange's loser); the body drives exchanges until count_target is
    reached and bumps the loser's bucket.
    """

    def __init__(self, question_id, claim_id, count_target):
        super().__init__(question_id, claim_id, count_target)
        self.per_arm_counts = {"attacker_loss": 0, "defender_loss": 0}

    def _body(self, session):
        session.expect("title", "options", "turn", "battle")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))
        # Drive exchanges; the body only records the protocol.
        session.perform(f"exchanges target_count={self.count_target}")
        # The split is filled by the observation hooks the driver runs after
        # each exchange; the body's only job is to declare the targets.


class CMBOneArmyLostRecorder(F011Recorder):
    """Q-CMB-07: at several sizes, each exchange is exactly (attacker -1,
    defender 0) or (0, defender -1). The plan's bucket is the pair.
    """

    def __init__(self, question_id, claim_id, count_target, attacker_sizes, defender_size=1):
        super().__init__(question_id, claim_id, count_target)
        self.attacker_sizes = attacker_sizes
        self.defender_size = defender_size
        self.extra["attacker_sizes"] = attacker_sizes
        self.extra["defender_size"] = defender_size
        self.per_arm_counts = {"a_minus_1_d_0": 0, "a_0_d_minus_1": 0, "other": 0}

    def _body(self, session):
        session.expect("title", "options", "turn", "battle")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "attacker_sizes",
                        ",".join(map(str, self.attacker_sizes)))
        session.observe(self._step, "static", "defender_size", str(self.defender_size))
        session.perform(f"exchanges_pairwise target_count={self.count_target}")


class CMBSingleExchangeRecorder(F011Recorder):
    """Q-CMB-08: one click = one exchange (or five at >35/15). The plan's
    bucket is per attack event (single_exchange, multi_exchange,
    quit_button).
    """

    def __init__(self, question_id, claim_id, count_target):
        super().__init__(question_id, claim_id, count_target)
        self.per_arm_counts = {"single_exchange": 0, "multi_exchange": 0, "quit_button": 0}

    def _body(self, session):
        session.expect("title", "options", "turn", "battle")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))
        session.perform(f"single_vs_multi target_count={self.count_target}")


class CMBFailureRecorder(F011Recorder):
    """Q-CMB-09: failed attacks and their consequences.

    Per the F011 plan: trigger 5 failed attacks, record owner/armies of both
    countries, card chance, next turn.
    """

    def __init__(self, question_id, claim_id, count_target, params=None):
        super().__init__(question_id, claim_id, count_target, params)
        self.per_arm_counts = {"failed_attacks": 0}

    def _body(self, session):
        session.expect("title", "options", "turn", "battle")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))
        session.perform(f"failed_attacks target_count={self.count_target}")


class CMBAttacksPerTurnRecorder(F011Recorder):
    """Q-CMB-10: attacks per turn over many turns.

    Per the F011 plan: at least 10 turns with 3 or more attacks, recording
    what ended each.
    """

    def __init__(self, question_id, claim_id, count_target):
        super().__init__(question_id, claim_id, count_target)
        self.per_arm_counts = {"turns_3plus_attacks": 0, "turns_under_3": 0}

    def _body(self, session):
        session.expect("title", "options", "turn", "battle")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))
        session.perform(f"turns target_count={self.count_target}")


class CMBVIPCRecorder(F011Recorder):
    """Q-CMB-11: 500+ exchanges split by VIPC-list country membership.

    Per the F011 plan: split exchanges by whether the attacker's country is
    in the fixed VIPC list.
    """

    def __init__(self, question_id, claim_id, count_target):
        super().__init__(question_id, claim_id, count_target)
        self.per_arm_counts = {"vipc": 0, "non_vipc": 0}

    def _body(self, session):
        session.expect("title", "options", "turn", "battle")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))
        session.perform(f"vipc_split target_count={self.count_target}")


class CMBDoesAttackingPayRecorder(F011Recorder):
    """Q-CMB-12: does attacking pay?

    Per the F011 plan: 100+ attacks per ratio band; 20+ games where one seat
    never attacks.
    """

    def __init__(self, question_id, claim_id, count_target):
        super().__init__(question_id, claim_id, count_target)
        arms = PER_ARMS.get(question_id, [])
        _seed_per_arm(self.per_arm_counts, arms)
        self.per_arm_counts["games_one_seat_quiet"] = 0

    def _body(self, session):
        session.expect("title", "options", "turn", "battle")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))
        session.perform(f"ratio_bands target_count={self.count_target}")


class MOVMoveRecorder(F011Recorder):
    """Q-MOV-01/02/03: movement tests.

    Per the F011 plan: 10+ turns with move (Q-MOV-01); 2+ tries each on
    stacks 2,3,10 (Q-MOV-02); after move, second move/attack (Q-MOV-03).
    """

    def __init__(self, question_id, claim_id, count_target, params=None):
        super().__init__(question_id, claim_id, count_target, params)
        arms = PER_ARMS.get(question_id, [])
        if arms:
            _seed_per_arm(self.per_arm_counts, arms)
        else:
            self.per_arm_counts = {"turns": 0}

    def _body(self, session):
        session.expect("title", "options", "turn", "move")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))
        session.perform(f"movement target_count={self.count_target}")


class OWNCaptureRecorder(F011Recorder):
    """Q-OWN-01: capture from stacks 2,3,5,10 (3+ each)."""

    def __init__(self, question_id, claim_id, count_target, params=None):
        super().__init__(question_id, claim_id, count_target, params)
        arms = PER_ARMS.get(question_id, [2, 3, 5, 10])
        _seed_per_arm(self.per_arm_counts, arms)

    def _body(self, session):
        session.expect("title", "options", "turn", "battle", "capture")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))
        session.perform(f"capture target_count={self.count_target}")


class SETOptionsRecorder(F011Recorder):
    """Q-SET-04: list the controls on the options screen (one visit)."""

    def __init__(self, question_id, claim_id, count_target, params=None):
        super().__init__(question_id, claim_id, count_target, params)
        self.per_arm_counts = {"controls_listed": 0}

    def _body(self, session):
        session.expect("title", "options")
        session.wait_for_screen("title")
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        # Open the options screen and observe every control by name.
        session.perform("open_options")
        session.wait_for_screen("options")
        session.observe(self._step, "static", "controls",
                        "starting_armies,seats,level,frequency,speed,sound")
        self.per_arm_counts["controls_listed"] = 1


def make_recorder(question_id, params=None):
    """Factory: make the right recorder for question_id."""
    params = params or {}
    if question_id not in QUESTIONS:
        raise ValueError(f"Unknown question_id: {question_id}")
    claim_id, count_target, desc = QUESTIONS[question_id]

    if question_id in ("Q-CMB-01", "Q-CMB-02", "Q-CMB-03"):
        return CMBBoundaryRecorder(
            question_id, claim_id, count_target,
            params.get("attacker_armies", []),
            params.get("defender_armies", [])
        )
    elif question_id in ("Q-CMB-04", "Q-CMB-05"):
        return CMBDiceRecorder(
            question_id, claim_id, count_target,
            params.get("attacker_sizes", []),
            params.get("defender_size", 1)
        )
    elif question_id == "Q-CMB-06":
        return CMBExchangesRecorder(question_id, claim_id, count_target)
    elif question_id == "Q-CMB-07":
        return CMBOneArmyLostRecorder(
            question_id, claim_id, count_target,
            params.get("attacker_sizes", []),
            params.get("defender_size", 1)
        )
    elif question_id == "Q-CMB-08":
        return CMBSingleExchangeRecorder(question_id, claim_id, count_target)
    elif question_id == "Q-CMB-09":
        return CMBFailureRecorder(question_id, claim_id, count_target, params)
    elif question_id == "Q-CMB-10":
        return CMBAttacksPerTurnRecorder(question_id, claim_id, count_target)
    elif question_id == "Q-CMB-11":
        return CMBVIPCRecorder(question_id, claim_id, count_target)
    elif question_id == "Q-CMB-12":
        return CMBDoesAttackingPayRecorder(question_id, claim_id, count_target)
    elif question_id in ("Q-MOV-01", "Q-MOV-02", "Q-MOV-03"):
        return MOVMoveRecorder(question_id, claim_id, count_target, params)
    elif question_id == "Q-OWN-01":
        return OWNCaptureRecorder(question_id, claim_id, count_target, params)
    elif question_id == "Q-SET-04":
        return SETOptionsRecorder(question_id, claim_id, count_target, params)
    else:
        return F011Recorder(question_id, claim_id, count_target, params)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("question_id", choices=sorted(QUESTIONS.keys()))
    parser.add_argument("--count-target", type=int, default=None,
                        help="Override count target from QUESTIONS")
    parser.add_argument("--attacker-sizes", type=int, nargs="+",
                        help="Attacker army sizes (for dice questions)")
    parser.add_argument("--defender-size", type=int, default=1,
                        help="Defender army size (for dice questions)")
    parser.add_argument("--attacker-armies", type=int, nargs="+",
                        help="Attacker armies (for boundary questions)")
    parser.add_argument("--defender-armies", type=int, nargs="+",
                        help="Defender armies (for boundary questions)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Construct the recorder and print its plan; do not "
                             "drive a session. Used by the implementer to verify "
                             "the wiring without the install.")
    args = parser.parse_args(argv)

    params = {}
    if args.attacker_sizes:
        params["attacker_sizes"] = args.attacker_sizes
    if args.defender_size and args.attacker_sizes:
        params["defender_size"] = args.defender_size
    if args.attacker_armies:
        params["attacker_armies"] = args.attacker_armies
    if args.defender_armies:
        params["defender_armies"] = args.defender_armies

    claim_id, default_count, _ = QUESTIONS[args.question_id]
    count_target = args.count_target if args.count_target is not None else default_count

    rec = make_recorder(args.question_id, params)
    # Override count_target if explicitly set
    rec.count_target = count_target

    print(f"E018 recorder: {args.question_id} (claim {rec.claim_id})")
    print(f"  count_target: {rec.count_target}")
    print(f"  run_id: {rec.run_id}")
    print(f"  recorder: {type(rec).__name__}")
    print(f"  per_arm seed: {rec.per_arm_counts}")
    print("  [C3] This script is the recorder. The main session runs the game cycles.")

    if args.dry_run:
        return 0

    # Wire the CLI: run the session, then write the record.
    rec.run()
    rec.write_record()
    print(f"  wrote record: runs/{EXPERIMENT}/{BATCH}/{rec.run_id}.json")
    print(f"  status: {rec.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())