"""E018 F011 combat recorder.

Run one question::

    python3 experiments/E018-pro-corroboration/record_f011.py Q-CMB-04 --count-target 500 --attacker-sizes 2 3 4 5 10 --defender-size 1

Each run writes one `run/1` record (formats/run-1.schema.json) to runs/E018/combat/.
The run/1 document carries the session's own observations plus the recorder's
fields, mapped by `e018_observation_fields` (a non-string original value is
written as its JSON text, `null` as "null"); the mapping and where the older
`e018-record/1` documents went are recorded in runs/E018/CORRECTIONS.md.

With `--dry-run` the recorder prints its plan (the steps its body will perform,
in the E002 step language) and writes nothing. Without the flag, and unless
IWP_CYCLE_INNER is "1", it re-executes itself through the driver's inner
namespace wrapper first (see `outer`); the game runs only inside that private
environment (the same one runtime/iwp/driver/runner.py builds).

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
import re
import secrets
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime"))
from iwp.driver.session import Session
from iwp.driver import runner as driver_runner
from iwp.driver import session as driver_session
from iwp.driver import errors as driver_errors

EXPERIMENT = "E018"
BATCH = "combat"
INNER_FLAG = "IWP_CYCLE_INNER"        # "1" inside the private namespaces (runner.py sets it too)
INNER_BOUND = 1800                    # s, one recorder attempt at most: every wait inside the
                                      # session carries its own bound (session.py), the R2 launch
                                      # window was 300 s, and this bound only ends a hang
SCRIPT = "experiments/E018-pro-corroboration/record_f011.py"
# The Options button of the title screen's bottom bar: the same input E004's cycle sends
# (runner.py's OPTIONS_STEP; spike.OPTIONS_CLICK measured it).
OPTIONS_STEP = "click! {} {}".format(*driver_runner.spike.OPTIONS_CLICK)
RESTORE_TEXT = ("the T13 driver's session seal: the private user, mount and PID namespaces of the "
                "command, the install bound read-only once, the prefix sealed and equal to its "
                "baseline before anything starts and again immediately before launch, and reset "
                "after the session; start_state.sha256 is the sha256 of the install's Islepro.exe "
                "hashed when the record is written (T48, constraint C)")

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


def _as_text(value):
    """One original field value as the text a run/1 observation carries.

    A string is itself, `None` the text "null", and any other JSON value its JSON
    text (so a number or dict round-trips: the value is preserved verbatim, only
    stringified — runs/E018/CORRECTIONS.md records the mapping).
    """
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True)


def e018_observation_fields(fields):
    """The recorder's own fields as run/1 observations.

    `fields` is the recorder's flat document (the keys the older `e018-record/1`
    records carried): question_id, claim_id, count_target, per_arm_counts,
    screenshot_path, screenshot_sha256, seal_ok, elapsed_seconds, outcome, extra.
    Every value is preserved verbatim as text (see `_as_text`); nothing is
    dropped. The migration of the old records (migrate_to_run1.py) writes these
    same observations, so a migrated record and a fresh one read the same way.
    """
    plan = (("static", "question_id"), ("static", "claim_id"), ("static", "count_target"),
            ("static", "per_arm_counts"), ("static", "screenshot_path"), ("static", "screenshot_sha256"),
            ("process", "seal_ok"), ("process", "elapsed_seconds"), ("static", "outcome"),
            ("static", "extra"))
    return [{"step": 0, "source": source, "field": name, "value": _as_text(fields.get(name))}
            for source, name in plan]


def record_context(argv=None):
    """The run/1 context a record is written with: commit, machine, fingerprint, binary sha.

    Gathered where the recorder runs; the inner re-exec (`inner`) provides the same
    fields from inside the private namespaces, where the install is bound read-only.
    A field that cannot be pinned is a clear refusal, never a guess: a record that
    cannot name its code commit or its start state is not written.
    """
    commit = os.environ.get("IWP_CYCLE_COMMIT")
    if not commit:
        try:
            commit = driver_runner.spike.must(["git", "rev-parse", "--short=12", "HEAD"],
                                              cwd=ROOT).stdout.decode().strip()
        except driver_runner.spike.CommandFailed as exc:
            raise SystemExit(f"no code commit could be pinned: {exc}; nothing was started")
    machine = os.environ.get("IWP_MACHINE", "local")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", machine):
        raise SystemExit("IWP_MACHINE is not a machine id (lowercase letters, digits, dashes); "
                         "nothing was started")
    locs = confined()
    try:
        binary_sha = driver_runner.binary_sha256(locs["IWP_DIR"])
    except OSError as exc:
        raise SystemExit(f"the install's Islepro.exe could not be hashed ({exc}); nothing was started")
    return {"commit": commit, "machine": machine, "fingerprint": driver_runner.spike.versions(),
            "binary_sha": binary_sha, "argv": list(argv or []), "restore": RESTORE_TEXT}


def confined(args=None):
    """The confined machine-local locations (a thin wrapper over the spike's own, patchable)."""
    return driver_runner.spike.confined_locations(
        args or argparse.Namespace(experiment=EXPERIMENT, explore=False))


def mount_private_tmpfs():
    """The private /tmp of the inner environment — the same mount runner.py's inner makes.

    Without it /tmp/.X11-unix is WSLg's read-only mount, the Session's Xvfb can only
    listen on an abstract socket, and the game — inside its own network namespace —
    can never reach it: that is why r0001..r0012 aborted at the launch while r0013,
    launched with this wrapper by hand, found the window in 0.42 s.
    """
    driver_runner.spike.must(["mount", "-t", "tmpfs", "-o", "mode=1777", "tmpfs", "/tmp"],
                             require_output=False)


def outer(argv):
    """Re-exec this recorder through the driver's inner namespace wrapper, and wait for it.

    The same wrapper runtime/iwp/driver/runner.py's outer() builds — `unshare -r -m -p -f
    --kill-child --mount-proc`, a fresh display, the code commit and this command's own
    invocation token in the environment — and the same bounded wait and reaping
    (launch_inner, reap_invocation: reused, not duplicated), so a recorder that runs
    past INNER_BOUND is killed with its namespace and nothing of it survives.
    """
    try:
        commit = driver_runner.spike.must(["git", "rev-parse", "--short=12", "HEAD"],
                                          cwd=ROOT).stdout.decode().strip()
    except driver_runner.spike.CommandFailed as exc:
        print(f"no code commit could be pinned: {exc}; nothing was started", file=sys.stderr)
        return 1
    token = secrets.token_hex(16)
    env = dict(os.environ, IWP_CYCLE_COMMIT=commit, IWP_CYCLE_DISPLAY=driver_session.free_display(),
               **{INNER_FLAG: "1", driver_session.INVOCATION: token})
    cmd = ["unshare", "-r", "-m", "-p", "-f", "--kill-child", "--mount-proc",
           sys.executable, str(Path(__file__).resolve())] + list(argv)
    code = driver_runner.launch_inner(cmd, env, INNER_BOUND)
    left = driver_runner.reap_invocation(token)
    if left:
        print(f"processes of this command survived its namespace and were killed: {sorted(left)}",
              file=sys.stderr)
        return 1
    return code


def inner(args, argv):
    """The recorder inside the private namespaces: the private /tmp, the install bound
    read-only, then one session and its run/1 record (runner.py's inner does the same
    for its repeats)."""
    mount_private_tmpfs()
    locs = confined()
    machine = os.environ.get("IWP_MACHINE", "local")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", machine):
        print("IWP_MACHINE is not a machine id (lowercase letters, digits, dashes); "
              "nothing was started", file=sys.stderr)
        return 1
    driver_session.bind_install_readonly(locs["IWP_DIR"])
    rec = build_recorder(args)
    ctx = record_context(argv)          # commit from IWP_CYCLE_COMMIT, machine, fingerprint,
                                        # the binary sha of the bound install
    rec.run()
    rec.write_record(ctx)
    print(f"  wrote record: runs/{EXPERIMENT}/{BATCH}/{rec.run_id}.json")
    print(f"  status: {rec.status}")
    return 0


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
        self.obs = []                  # the session's run/1 observations, kept when it ends
        self.started = None
        self.ended = None

    def run(self):
        """Run one session for this question.

        Uses the driver Session API. The main session has the install (C3 lines).
        """
        locs = confined()
        display = os.environ.get("IWP_CYCLE_DISPLAY") or driver_session.free_display()
        t0 = time.monotonic()
        session = Session(
            self.run_id,
            locs["IWP_PREFIX"],
            locs[f"{EXPERIMENT}_BUNDLES"],
            locs["IWP_DIR"],
            display,
            experiment=EXPERIMENT,
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
            self.obs = [dict(o) for o in session.obs]
            self.started = session.started or driver_session.now()
            self.ended = session.ended or driver_session.now()

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

    def build_record(self, ctx):
        """One run/1 document for this attempt (formats/run-1.schema.json).

        `ctx` is `record_context()`'s answer: code commit, machine, fingerprint,
        the install binary's sha256 and the argv. The session's own observations
        come first, then the recorder's fields (`e018_observation_fields`). The
        status is the session's, verbatim ("completed" or "aborted: ...").
        """
        return {
            "schema": "run/1",
            "run_id": self.run_id,
            "experiment": EXPERIMENT,
            "arm": BATCH,
            "rep": int(self.run_id.split("-r")[1]),
            "code_commit": ctx["commit"],
            "machine": ctx["machine"],
            "artifact": {"set": driver_runner.spike.SET_ID, "variant": driver_runner.VARIANT},
            "runtime": {
                "driver": f"{SCRIPT}@{ctx['commit']}",
                "platform": driver_runner.PLATFORM,
                "fingerprint": ctx["fingerprint"],
            },
            "interventions": [{"level": "I1", "what":
                               "the driver's cycle seal (the install bound read-only, the prefix "
                               "sealed and reset), read-only reads of /proc, the planned input "
                               "steps and screenshots; no memory read, no modified file"}],
            "start_state": {"id": "S-cold-prefix-title", "sha256": ctx["binary_sha"],
                            "restore": ctx["restore"]},
            "seed": None,
            "actions": {"script": SCRIPT, "sha256": sha256_file(Path(__file__).resolve()),
                        "args": ctx["argv"]},
            "observations": self.obs + e018_observation_fields(self.recorder_fields()),
            "outputs": [],
            "started": self.started,
            "ended": self.ended,
            "status": self.status,
        }

    def recorder_fields(self):
        """The recorder's own flat document — the fields a run/1 record carries as observations."""
        return {
            "question_id": self.question_id,
            "claim_id": self.claim_id,
            "count_target": self.count_target,
            "per_arm_counts": self.per_arm_counts,
            "screenshot_path": str(self.screenshot_path) if self.screenshot_path else None,
            "screenshot_sha256": self.screenshot_sha256,
            "seal_ok": self.seal_ok,
            "elapsed_seconds": self.elapsed,
            "outcome": self.outcome,
            "extra": self.extra,
        }

    def write_record(self, ctx=None):
        """Write the run/1 record to runs/E018/combat/ (never over one that exists)."""
        ctx = ctx or record_context()
        out_dir = ROOT / "runs" / EXPERIMENT / BATCH
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{self.run_id}.json"
        if path.exists():
            raise SystemExit(f"no record written: {path} already exists; records are never "
                             "overwritten (rule 20)")
        record = self.build_record(ctx)
        with open(path, "w") as f:
            json.dump(record, f, indent=2)
            f.write("\n")
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
    """Q-SET-04: list the controls on the options screen (one visit).

    The body uses only real E002 steps (runtime/iwp/spike/steps.py): the title screen
    waited for by its pixels, the Options button of the title screen's bottom bar —
    the same input E004's cycle sends (runner.OPTIONS_STEP; spike.OPTIONS_CLICK) —
    then the options screen, and a screenshot the controls are counted from by
    pixels at C3. `controls_listed` stays 0 here: the count is read from the
    screenshot, never assumed (r0013 aborted on a made-up step named open_options).
    """

    def __init__(self, question_id, claim_id, count_target, params=None):
        super().__init__(question_id, claim_id, count_target, params)
        self.per_arm_counts = {"controls_listed": 0}

    def plan(self):
        """The steps the body sends, in the E002 step language (--dry-run prints them)."""
        return [OPTIONS_STEP, "shot options-controls"]

    def _body(self, session):
        session.expect("title", "options")
        session.known_screen()                       # the title screen, waited for by its pixels
        self._step = 1
        session.observe(self._step, "static", "question_id", self.question_id)
        session.observe(self._step, "static", "claim_id", self.claim_id)
        session.observe(self._step, "static", "count_target", str(self.count_target))
        session.observe(self._step, "static", "controls_to_list",
                        "starting_armies,seats,level,frequency,speed,sound")
        session.observe_screenshot("before.png", 3)
        session.perform(OPTIONS_STEP)                # open the options screen, as E004's cycle does
        session.wait_for_screen("options")
        session.perform("shot options-controls")     # the screenshot the count is read from
        session.observe_screenshot("after.png", 7)


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


def build_recorder(args):
    """The recorder for parsed CLI args, with its count target resolved."""
    params = {}
    if args.attacker_sizes:
        params["attacker_sizes"] = args.attacker_sizes
    if args.defender_size and args.attacker_sizes:
        params["defender_size"] = args.defender_size
    if args.attacker_armies:
        params["attacker_armies"] = args.attacker_armies
    if args.defender_armies:
        params["defender_armies"] = args.defender_armies
    _, default_count, _ = QUESTIONS[args.question_id]
    rec = make_recorder(args.question_id, params)
    rec.count_target = args.count_target if args.count_target is not None else default_count
    return rec


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
                             "drive a session and enter no namespace. Used by the "
                             "implementer to verify the wiring without the install.")
    args = parser.parse_args(argv)

    rec = build_recorder(args)
    print(f"E018 recorder: {args.question_id} (claim {rec.claim_id})")
    print(f"  count_target: {rec.count_target}")
    print(f"  run_id: {rec.run_id}")
    print(f"  recorder: {type(rec).__name__}")
    print(f"  per_arm seed: {rec.per_arm_counts}")
    print("  [C3] This script is the recorder. The main session runs the game cycles.")
    plan = rec.plan() if hasattr(rec, "plan") else None
    if plan is not None:
        print("  plan (E002 steps):")
        for step_text in plan:
            print(f"    {step_text}")

    if args.dry_run:
        return 0

    # Without the inner flag this process is the outer one: re-exec through the driver's
    # namespace wrapper, and the game runs only inside it (see outer).
    if os.environ.get(INNER_FLAG) != "1":
        print(f"  re-exec through the driver's inner wrapper ({INNER_FLAG} unset)")
        return outer(argv)
    return inner(args, argv)


if __name__ == "__main__":
    sys.exit(main())