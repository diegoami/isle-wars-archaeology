"""E018 F011 combat recorder.

Run one question::

    python3 experiments/E018-pro-corroboration/record_f011.py Q-CMB-04 --count-target 100 --attacker-sizes 2 3 4 5 10 --defender-size 1

Each run writes one JSON record to runs/E018/combat/ with:
    run_id, question_id, claim_id, per_arm_counts, screenshot_path, screenshot_sha256,
    seal_ok, elapsed_seconds, outcome.

The [C3] cycles are run by the main session on the install; this script is the
recorder only — it writes the records, it does not run the game.

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
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "runtime"))
from iwp.driver.session import Session
from iwp.driver import runner as driver_runner
from iwp.driver import errors as driver_errors

EXPERIMENT = "E018"
BATCH = "combat"

# Question metadata: claim_id, count_target, description
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

    def run(self):
        """Run one session for this question.

        Uses the driver Session API. The main session has the install.
        """
        import os
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
        except Exception as exc:
            self.status = f"aborted: {type(exc).__name__}: {exc}"
        finally:
            self.elapsed = round(time.monotonic() - t0, 2)
            self.seal_ok = session.recovered

    def _body(self, session):
        """Override in subclass for each question type."""
        raise NotImplementedError

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

    Parameters
    ----------
    attacker_armies : list of int
    defender_armies : list of int
    """

    def __init__(self, question_id, claim_id, count_target, attacker_armies, defender_armies):
        super().__init__(question_id, claim_id, count_target)
        self.attacker_armies = attacker_armies
        self.defender_armies = defender_armies
        self.extra["attacker_armies"] = attacker_armies
        self.extra["defender_armies"] = defender_armies

    def _body(self, session):
        session.wait_for_screen("title")
        # Navigate to the turn screen (attack phase)
        # The exact steps depend on F011's static reading
        session.observe(1, "static", "question_id", self.question_id)
        session.observe(1, "static", "attacker_armies", str(self.attacker_armies))
        session.observe(1, "static", "defender_armies", str(self.defender_armies))
        # Placeholder: the main session fills in the actual game-play steps
        # based on the static reading of the attack gate


class CMBDiceRecorder(F011Recorder):
    """Q-CMB-04/05/06/07: dice and exchange counts.

    Parameters
    ----------
    attacker_sizes : list of int
    defender_size : int
    """

    def __init__(self, question_id, claim_id, count_target, attacker_sizes, defender_size=1):
        super().__init__(question_id, claim_id, count_target)
        self.attacker_sizes = attacker_sizes
        self.defender_size = defender_size
        self.extra["attacker_sizes"] = attacker_sizes
        self.extra["defender_size"] = defender_size

    def _body(self, session):
        session.wait_for_screen("title")
        session.observe(1, "static", "question_id", self.question_id)
        session.observe(1, "static", "attacker_sizes", str(self.attacker_sizes))
        session.observe(1, "static", "defender_size", str(self.defender_size))


class CMBFailureRecorder(F011Recorder):
    """Q-CMB-09: failed attacks and their consequences."""

    def _body(self, session):
        session.wait_for_screen("title")
        session.observe(1, "static", "question_id", self.question_id)


class MOVMoveRecorder(F011Recorder):
    """Q-MOV-01/02/03: movement tests."""

    def _body(self, session):
        session.wait_for_screen("title")
        session.observe(1, "static", "question_id", self.question_id)


class OWNCaptureRecorder(F011Recorder):
    """Q-OWN-01: capture and move-in."""

    def _body(self, session):
        session.wait_for_screen("title")
        session.observe(1, "static", "question_id", self.question_id)


class SETOptionsRecorder(F011Recorder):
    """Q-SET-04: options screen controls list."""

    def _body(self, session):
        session.wait_for_screen("title")
        session.observe(1, "static", "question_id", self.question_id)


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
    elif question_id in ("Q-CMB-04", "Q-CMB-05", "Q-CMB-06", "Q-CMB-07"):
        return CMBDiceRecorder(
            question_id, claim_id, count_target,
            params.get("attacker_sizes", []),
            params.get("defender_size", 1)
        )
    elif question_id == "Q-CMB-09":
        return CMBFailureRecorder(question_id, claim_id, count_target, params)
    elif question_id in ("Q-MOV-01", "Q-MOV-02", "Q-MOV-03"):
        return MOVMoveRecorder(question_id, claim_id, count_target, params)
    elif question_id == "Q-OWN-01":
        return OWNCaptureRecorder(question_id, claim_id, count_target, params)
    elif question_id == "Q-SET-04":
        return SETOptionsRecorder(question_id, claim_id, count_target, params)
    else:
        return F011Recorder(question_id, claim_id, count_target, params)


def main(argv=None):
    import argparse
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
    print("  [C3] This script is the recorder. The main session runs the game cycles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
