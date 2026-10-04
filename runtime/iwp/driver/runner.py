"""E004: the 10-repeat cycle of the Isle Wars Pro driver, one command, one `run/1` record per repeat.

    python3 runtime/iwp/driver/run_cycle.py [--arm control] [--repeats 10]
                                            [--fault kill-game|sigkill-game --fault-at after-title|after-input
                                             --fault-repeat N]

A repeat is: the seal, a display, the game launched from the baseline, the title screen (waited for by its
pixels), the `before` screenshot, one input (Options), the Options screen, the `after` screenshot, terminate,
reset. It is built on `session.Session` and is recorded under runs/E004/ and evidence/E004/ whether it
completed or aborted. The next repeat starts from the baseline whatever happened to the last one.

With --fault, repeat N (default 2) has the game killed at the checkpoint named by --fault-at, by something
the driver does not know about: `wineserver -k` (kill-game) or SIGKILL of the game process (sigkill-game).
That repeat must be recorded `aborted: game-died`, its clean-up (terminate, the display, the reset) must
have succeeded, and the next one must complete; any other outcome stops the command with exit 1. Without
--fault, every repeat must complete, and the first that does not stops the command, so that a wrong state is
never carried into the next repeat.

The outer process gives the command a token of its own, IWP_CYCLE_INVOCATION, which every process of the
command inherits; after the command it signals only processes that carry that token, never another E004
command's. The command itself runs for at most `--repeats` x REPEAT_BOUND s.

Machine-local values come from the environment, as for the spike, and are never written to a record:
    IWP_PREFIX, IWP_DIR, E004_BUNDLES (outside every checkout, confined by setup/iwp/locations.py), and
    IWP_MACHINE, the machine id written to records (default: local).
Everything but the records happens in a private user, mount and PID namespace (`unshare -rmpf`): the
install is bound read-only once for the command, /tmp is private, nothing outlives the command, and the
game itself is always in a network namespace of its own (N0).
"""
import argparse
import contextlib
import hashlib
import json
import os
import re
import secrets
import signal
import subprocess
import sys
from pathlib import Path

from . import session as sessionlib
from .errors import RecordError
from .session import Session, spike, safeio, locations

ROOT = sessionlib.ROOT
EXPERIMENT = sessionlib.EXPERIMENT
LAUNCHER = Path(__file__).resolve().with_name("run_cycle.py")
OPTIONS_STEP = "click! {} {}".format(*spike.OPTIONS_CLICK)
FAULTS = ("kill-game", "sigkill-game")
FAULT_POINTS = ("after-title", "after-input")
REPEAT_BOUND = 300     # s, one repeat at most: the sum of the session's bounds is below it (session.py), and a
                       # repeat took 14 to 17 s in E004; the bound only ends a hang
REAP_BOUND = 10        # s, for the killed command to be reaped
RESTORE = ("fresh private user, mount and PID namespaces, the install bound read-only once for the command and "
           "checked at the start of every repeat; the prefix sealed (drive mapping, links, second names, mounts, "
           "the registered game copy) and its registry files equal to their baseline before anything starts, and "
           "the prefix sealed again immediately before each launch; start_state.sha256 lists every entry of the "
           "prefix with the size and sha256 of each file and the target of each link, the registry files "
           "included; the prefix is reset to that state after every repeat, completed or aborted")


# --- the repeat's body and the faults --------------------------------------------------------

def options_cycle(session):
    """The cycle of E004: the title screen, `before`, one input (Options), the Options screen, `after`."""
    session.expected.update({"title", "options"})
    session.known_screen()
    session.checkpoint("after-title")
    session.observe_screenshot("before.png", 3)
    session.perform(OPTIONS_STEP)
    session.checkpoint("after-input")
    session.wait_for_screen("options")
    session.observe_screenshot("after.png", 6)


def kill_game(session):
    """What an outsider does: `wineserver -k` of this run's prefix, from a process of its own."""
    session.observe(session.step_no + 1, "process", "fault injected", "wineserver -k")
    spike.run([spike.WINESERVER, "-k"], env=session.env, timeout=sessionlib.WINESERVER_TIMEOUT)
    spike.poll(lambda: not session.game_alive(), 10, 0.05)


def sigkill_game(session):
    """What an outsider does: SIGKILL of the game process."""
    pid = session.find_game_pid() or session.procs["game"].pid
    session.observe(session.step_no + 1, "process", "fault injected", "SIGKILL of the game process")
    os.kill(pid, signal.SIGKILL)
    spike.poll(lambda: not session.game_alive(), 10, 0.05)


FAULT_ACTIONS = {"kill-game": kill_game, "sigkill-game": sigkill_game}


# --- records ---------------------------------------------------------------------------------

def driver_sources_sha256():
    """One hash over the sources of the driver and of the spike it reuses: the files' names and sha256."""
    files = sorted(Path(__file__).resolve().parent.glob("*.py")) + [Path(spike.__file__).resolve(),
                                                                    Path(spike.stepslib.__file__).resolve()]
    text = "\n".join(f"{p.relative_to(ROOT).as_posix()} {spike.sha256_file(p)}" for p in files)
    return hashlib.sha256(text.encode()).hexdigest()


def next_run_id():
    return spike.next_run_id(EXPERIMENT)


def rep_of(arm):
    folder = ROOT / "runs" / EXPERIMENT
    return 1 + sum(1 for p in folder.glob("*.json") if json.loads(p.read_text()).get("arm") == arm)


def build_record(session, commit, machine, rep, state_sha, argv, fingerprint):
    return {
        "schema": "run/1",
        "run_id": session.run_id,
        "experiment": EXPERIMENT,
        "arm": session.args.arm,
        "rep": rep,
        "code_commit": commit,
        "machine": machine,
        "artifact": {"set": spike.SET_ID, "variant": None},
        "runtime": {
            "driver": f"runtime/iwp/driver/run_cycle.py@{commit}",
            "platform": "linux-wsl2/wine-xvfb-xfwm4",
            "fingerprint": fingerprint,
        },
        "interventions": [{"level": "I1", "what": "screenshots of the display and read-only reads of /proc and of "
                                                  "the game copy; no memory read, no modified file"}],
        "start_state": {"id": "S-cold-prefix-title", "sha256": state_sha, "restore": RESTORE},
        "seed": None,
        "actions": {"script": "runtime/iwp/driver/run_cycle.py", "sha256": spike.sha256_file(LAUNCHER), "args": argv},
        "observations": session.obs,
        "outputs": [{"name": n, "sha256": spike.sha256_file(p), "store": f"release:{EXPERIMENT}"}
                    for n, p, _ in session.outputs],
        "started": session.started,
        "ended": session.ended,
        "status": session.status,
    }


def write_records(session, bundles, commit, machine, state_sha, argv, fingerprint):
    """Store the bundles and write the manifest and the record, once each. RecordError says what was not
    written; a record is never overwritten and never names an output the store does not hold."""
    names = {"runs": f"{session.run_id}.json", "evidence": f"{session.run_id}.manifest.json"}
    taken = [f"{folder}/{EXPERIMENT}/{name}" for folder, name in names.items()
             if os.path.lexists(ROOT / folder / EXPERIMENT / name)]
    if taken:
        raise RecordError(f"no record written: {', '.join(taken)} already exist(s); records are never overwritten")
    try:
        for folder in names:
            os.close(safeio.open_directory(ROOT / folder / EXPERIMENT, create_below=ROOT))
    except (safeio.Refused, OSError) as exc:
        raise RecordError(f"no record written: {exc}") from None
    session._error = RecordError
    session.outputs = spike.store_outputs(session, bundles, lambda name, digest: f"{digest[:16]}-{name}", "same")
    manifest = spike.build_manifest(session)
    record = build_record(session, commit, machine, rep_of(session.args.arm), state_sha, argv, fingerprint)
    try:
        safeio.write_file(ROOT / "evidence" / EXPERIMENT, names["evidence"],
                          data=(json.dumps(manifest, indent=2) + "\n").encode(), exist="new", create_below=ROOT)
        safeio.write_file(ROOT / "runs" / EXPERIMENT, names["runs"],
                          data=(json.dumps(record, indent=2) + "\n").encode(), exist="new", create_below=ROOT)
    except (safeio.Refused, OSError) as exc:
        raise RecordError(f"no record written: {exc}") from None


# --- the command -----------------------------------------------------------------------------

def arm_name(value):
    try:
        return safeio.identifier(value, "arm")
    except safeio.Refused as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--arm", type=arm_name, default="control")
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--fault", choices=FAULTS, default=None,
                    help="kill the game at --fault-at in repeat --fault-repeat: that repeat must abort, the next complete")
    ap.add_argument("--fault-at", choices=FAULT_POINTS, default="after-title")
    ap.add_argument("--fault-repeat", type=int, default=2)
    return ap


def confined(args):
    return spike.confined_locations(argparse.Namespace(explore=False, experiment=EXPERIMENT))


def check_args(args):
    if not 1 <= args.repeats <= 50:
        sys.exit("--repeats is between 1 and 50; nothing was started")
    if args.fault and not 1 <= args.fault_repeat <= args.repeats:
        sys.exit("--fault-repeat is between 1 and --repeats; nothing was started")


def as_expected(session, faulted):
    """A repeat ended as the command requires: completed, or, for the faulted repeat, aborted because the game
    died; and in both cases its clean-up succeeded (session.recovered), so the next repeat starts from the
    baseline. A faulted repeat whose terminate or reset failed is not as expected, whatever its status says."""
    if faulted:
        return session.status.startswith("aborted: game-died: ") and session.recovered
    return session.status == "completed" and session.recovered


def run_repeat(index, args, locs, display, commit, machine, argv, fingerprint):
    """One repeat: a session, its record. (status, seconds, as expected?)"""
    run_id = next_run_id()
    session = Session(run_id, locs["IWP_PREFIX"], locs[f"{EXPERIMENT}_BUNDLES"], locs["IWP_DIR"], display, args.arm)
    faulted = bool(args.fault) and index == args.fault_repeat
    if faulted:
        session.on(args.fault_at, FAULT_ACTIONS[args.fault])
    session.observe(0, "static", "driver sources sha256 (runtime/iwp/driver/*.py, spike cycle.py and steps.py)",
                    driver_sources_sha256())
    session.observe(0, "static", "fault injected in this repeat", f"{args.fault} at {args.fault_at}" if faulted else "none")
    session.execute(options_cycle)
    state_sha = spike.start_state_sha(session.snap_before[1]) if hasattr(session, "snap_before") else "0" * 64
    try:
        write_records(session, locs[f"{EXPERIMENT}_BUNDLES"], commit, machine, state_sha, argv, fingerprint)
    except RecordError as exc:
        print(str(exc), file=sys.stderr)
        return session.status, session.elapsed, False
    good = as_expected(session, faulted)
    print(json.dumps({"repeat": index, "run_id": run_id, "status": session.status, "seconds": session.elapsed,
                      "recovered": session.recovered, "as_expected": good}), flush=True)
    return session.status, session.elapsed, good


def inner(args, argv):
    """Runs as PID 1 of the private namespaces."""
    check_args(args)
    locs = confined(args)
    machine = os.environ.get("IWP_MACHINE", "local")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", machine):
        sys.exit("IWP_MACHINE is not a machine id (lowercase letters, digits, dashes); nothing was started")
    display = os.environ.get("IWP_CYCLE_DISPLAY") or sessionlib.free_display()
    commit = os.environ["IWP_CYCLE_COMMIT"]
    spike.run(["mount", "-t", "tmpfs", "-o", "mode=1777", "tmpfs", "/tmp"], check=True)
    sessionlib.bind_install_readonly(locs["IWP_DIR"])
    fingerprint = spike.versions()
    for index in range(1, args.repeats + 1):
        _, _, good = run_repeat(index, args, locs, display, commit, machine, argv, fingerprint)
        if not good:
            print(f"repeat {index} did not end as expected; stopping, so that no wrong state is carried on",
                  file=sys.stderr)
            return 1
    return 0


def outer(args, argv):
    check_args(args)
    locs = confined(args)
    prefix = locs["IWP_PREFIX"]
    strays = spike.marked_processes() + spike.prefix_processes(prefix)
    if strays:
        sys.exit(f"stale processes of an earlier run or of setup are alive: {sorted(set(strays))}; "
                 "stop them first (nothing was started)")
    problems = spike.prefixlib.prefix_problems(prefix, locs["IWP_DIR"])
    if problems:
        sys.exit("the prefix is not safe to launch from; nothing was started: " + "; ".join(problems)[:400])
    commit = spike.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT).stdout.decode().strip()
    dirty = spike.run(["git", "status", "--porcelain", "--", "runtime", "setup", "tools", "formats"], cwd=ROOT).stdout
    if dirty:
        sys.exit("runtime/, setup/, tools/ or formats/ has uncommitted changes; commit before a recorded run")
    token = secrets.token_hex(16)
    env = dict(os.environ, IWP_CYCLE_COMMIT=commit, IWP_CYCLE_INNER="1", IWP_CYCLE_DISPLAY=sessionlib.free_display(),
               **{sessionlib.INVOCATION: token})
    cmd = ["unshare", "-r", "-m", "-p", "-f", "--kill-child", "--mount-proc", sys.executable, str(LAUNCHER)] + argv
    code = launch_inner(cmd, env, args.repeats * REPEAT_BOUND)
    left = reap_invocation(token)
    if left:
        print(f"processes of this command survived its namespace and were killed: {sorted(left)}", file=sys.stderr)
        return 1
    return code


def launch_inner(cmd, env, bound):
    """Run the namespaced command for at most `bound` s. At the bound it is killed (its namespace with it,
    --kill-child) and the exit is 1; every wait here is bounded."""
    proc = subprocess.Popen(cmd, env=env)
    try:
        return proc.wait(bound)
    except subprocess.TimeoutExpired:
        proc.kill()
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(REAP_BOUND)
        print(f"the command ran past its bound of {bound} s and was killed; the repeat it was in has no record, "
              "and the prefix may be off its baseline (setup/iwp/iwp-runtime.sh)", file=sys.stderr)
        return 1


def reap_invocation(token):
    """SIGKILL what is left of this command: the processes whose environment holds this command's token,
    exactly. Another E004 command's processes carry another token and are never signalled. The pids found."""
    found = sessionlib.invocation_processes(token)
    want = [f"{sessionlib.INVOCATION}={token}".encode()]
    for pid in found:
        sessionlib.kill_marked(pid, want)
    return found


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    args = parser().parse_args(argv)
    if os.environ.get("IWP_CYCLE_INNER") == "1":
        return inner(args, argv)
    return outer(args, argv)
