#!/usr/bin/env python3
"""E006: the repeated cycle of the DOS Isle Wars driver, one command, one `run/1` record per repeat (T15, W5b).

    python3 runtime/iw-dos/driver/repeat.py [--arm control] [--repeats 10]
                                            [--fault sigkill|close --fault-at after-before|after-input --fault-repeat N]

A repeat is a session (session.py): the seal, this run's own Xvfb, DOSBox-X launched from the baseline, the
option box (by its pixels), `before.png`, one input (a click on Set level, in T14's step language), the Select
level dialog, `after.png`, terminate, reset. Every repeat is recorded under runs/E006/ and evidence/E006/,
completed or aborted, and the next starts from the baseline whatever happened to the last: each session's seal
requires the run copy equal to the baseline taken at the start of the command.

With --fault, repeat N (default 2) has DOSBox-X ended at the checkpoint --fault-at by something the session does
not do itself: SIGKILL of its process (`sigkill`, through kill_marked) or its X client closed (`close`,
`xdotool windowkill`). That repeat must be recorded `aborted: game-died: ...` with its finish recovered, and the
others completed; any other outcome stops the command with exit 1. Without --fault every repeat must complete,
and the first that does not stops the command, so that a wrong state is never carried on.

The outer process gives the command a token, IW_DOS_DRIVER_INVOCATION, which every process of the command
inherits; afterwards it signals only processes that carry that token. The command runs for at most
--repeats x REPEAT_BOUND s. Everything but the outer checks runs in private user, mount, PID and network
namespaces (`unshare -rmpfn`): a private /tmp, IW_DOS_DIR bound read-only once for the command (checked by every
session's seal), and no network but a loopback (N0).

Machine-local values come from the environment and are never written to a record: IW_DOS_DIR, IW_DOS_RUN and
E006_BUNDLES (confined by setup/iw-dos/rundir.py), and IW_DOS_MACHINE, the machine id (default: local).
"""
import argparse
import hashlib
import json
import os
import re
import secrets
import signal
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from driver import repeat as _self      # run main() in the package's module, not in a second copy
    sys.exit(_self.main())

from driver import procs, session as sessionlib     # noqa: E402
from driver.errors import CommandFailed, FaultNotInjected, RecordError     # noqa: E402

spike = sessionlib.spike
rundir, safeio, locations = spike.rundir, spike.safeio, spike.locations
ROOT = spike.ROOT                  # where the records go (a test points it elsewhere)
SOURCES = Path(__file__).resolve().parents[3]   # the checkout whose sources run
WORK_BASE = Path("/tmp")          # the private /tmp of the namespace, where each repeat has its work directory
EXPERIMENT = "E006"
LAUNCHER = Path(__file__).resolve()
SET_LEVEL_STEP = "click {} {}".format(*spike.SET_LEVEL_CLICK)
FAULTS = ("sigkill", "close")
FAULT_POINTS = ("after-before", "after-input")
FIRST_DISPLAY = 60          # repeat n uses :60+n, inside the command's own network namespace and /tmp
REPEAT_BOUND = 400          # s, one repeat at most: above the sum of the session's bounds on the cycle's path
                            # (the option box 120, still 30, the window 30, the dialog 20 and 30, the click 5+5,
                            # Xvfb 20, terminate 15+10, Xvfb's stop 10+10); F005: a cycle took 17 to 18 s
REAP_BOUND = 10             # s, for the killed command to be reaped
GONE_BOUND = 10             # s, DOSBox-X gone after an injected fault (F005: 0.05 s)
RESTORE = ("fresh private user, mount, PID and network namespaces for the command; IW_DOS_DIR bound read-only once "
           "for the command and checked by every repeat's seal; a fresh Xvfb and a fresh DOSBox-X process per repeat, "
           "from a generated configuration mounting only the run copy; the run copy checked (register_artifact.py "
           "check --strict, links, second names, mounts, aliases) and required equal to the baseline taken at the "
           "start of the command, at the start of the repeat and again immediately before the launch; reset to it "
           "after every repeat, completed or aborted; start_state.sha256 lists every entry of the run copy with its "
           "size, sha256 and modification time")


# --- the cycle and the faults ----------------------------------------------------------------

def set_level_cycle(session):
    """The cycle of E006: the option box, `before`, one input (Set level), the Select level dialog, `after`."""
    session.expected.update({"option-box", "select-level"})
    session.wait_for_screen("option-box")
    session.observe_screenshot("before.png")
    session.checkpoint("after-before")
    session.perform(SET_LEVEL_STEP)
    session.checkpoint("after-input")
    session.wait_for_screen("select-level")
    session.observe_screenshot("after.png")


def wait_gone(session, how):
    if spike.poll(lambda: session.procs["game"].poll() is not None, GONE_BOUND, 0.05) is None:
        raise FaultNotInjected(f"DOSBox-X survived the injected {how} for {GONE_BOUND} s")
    session.observe(session.step_no + 100, "process", f"fault: DOSBox-X gone after {how}, exit status",
                    session.procs["game"].returncode)


def sigkill_game(session):
    """SIGKILL of DOSBox-X from outside the session, through kill_marked (its markers re-checked)."""
    session.observe(session.step_no + 100, "process", "fault injected", "SIGKILL of DOSBox-X")
    if not procs.kill_marked(session.procs["game"].pid, session.items("game"), signal.SIGKILL):
        raise FaultNotInjected("DOSBox-X no longer carried this run's markers; nothing was signalled")
    wait_gone(session, "SIGKILL")


def close_game(session):
    """DOSBox-X's X client closed (XKillClient, `xdotool windowkill`), as a window manager's kill would."""
    session.observe(session.step_no + 100, "process", "fault injected", "xdotool windowkill of DOSBox-X's window")
    try:
        procs.must(["xdotool", "windowkill", session.window], env=session.env)
    except CommandFailed as exc:
        raise FaultNotInjected(f"the X client was not closed: {exc}") from None
    wait_gone(session, "windowkill")


FAULT_ACTIONS = {"sigkill": sigkill_game, "close": close_game}


# --- records ---------------------------------------------------------------------------------

def driver_sources_sha256():
    """One hash over the driver's sources and the spike files it reuses: names and sha256."""
    here = Path(__file__).resolve().parent
    files = sorted(here.glob("*.py")) + [SOURCES / "runtime/iw-dos/spike" / n for n in
                                         ("cycle.py", "navsteps.py", "dosconf.py", "board.py")]
    text = "\n".join(f"{p.relative_to(SOURCES).as_posix()} {spike.sha256_file(p)}" for p in files)
    return hashlib.sha256(text.encode()).hexdigest()


def next_run_id():
    folder = ROOT / "runs" / EXPERIMENT
    numbers = [int(m.group(1)) for p in folder.glob(f"{EXPERIMENT}-r*.json")
               if (m := re.match(rf"{EXPERIMENT}-r(\d+)\.json$", p.name))]
    return f"{EXPERIMENT}-r{(max(numbers) if numbers else 0) + 1:04d}"


def rep_of(arm):
    folder = ROOT / "runs" / EXPERIMENT
    return 1 + sum(1 for p in folder.glob("*.json") if json.loads(p.read_text()).get("arm") == arm)


def versions():
    """The tools' versions, each "unknown" unless its probe exited 0 and printed the version (T13 R6)."""
    def first(cmd, pattern):
        try:
            done = procs.must(cmd)
        except CommandFailed:
            return "unknown"
        match = re.search(pattern, (done.stdout + done.stderr).decode(errors="replace"))
        return match.group(1) if match else "unknown"
    return {
        "dosbox-x": first(["dosbox-x", "-version"], r"DOSBox-X version (\S+ \S+)"),
        "dosbox-x-package": first(["dpkg-query", "-W", "-f=${Version}", "dosbox-x"], r"(.+)"),
        "xvfb": first(["dpkg-query", "-W", "-f=${Version}", "xvfb"], r"(.+)"),
        "xdotool": first(["xdotool", "--version"], r"(\d+\.\d+\.\d+)"),
        "imagemagick": first(["import", "-version"], r"ImageMagick (\S+)"),
        "python": ".".join(map(str, sys.version_info[:3])),
        "kernel": os.uname().release,
    }


def build_record(session, commit, machine, rep, argv, fingerprint):
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
            "driver": f"runtime/iw-dos/driver/repeat.py@{commit}",
            "platform": "linux-wsl2/dosbox-x-xvfb",
            "fingerprint": fingerprint,
        },
        "interventions": [dict(spike.SCREENSHOTS)],
        "start_state": {"id": "S-run-copy-option-box", "sha256": spike.listing_hash(session.baseline),
                        "restore": RESTORE},
        "seed": None,
        "actions": {"script": "runtime/iw-dos/driver/repeat.py", "sha256": spike.sha256_file(LAUNCHER), "args": argv},
        "observations": session.obs,
        "outputs": [{"name": n, "sha256": spike.sha256_file(p), "store": f"release:{EXPERIMENT}"}
                    for n, p, _ in session.outputs],
        "started": session.started,
        "ended": session.ended,
        "status": session.status,
    }


def build_manifest(session):
    files = []
    for name, path, klass in session.outputs:
        digest = spike.sha256_file(path)
        files.append({"name": name, "bytes": path.stat().st_size, "sha256": digest,
                      "asset": f"{digest[:16]}-{name}", "class": klass})
    return {"schema": "evidence-manifest/1", "run_id": session.run_id, "experiment": EXPERIMENT,
            "store": f"release:{EXPERIMENT}", "artifact": {"set": spike.SET_ID, "variant": None}, "files": files}


def write_records(session, bundles, commit, machine, argv, fingerprint):
    """Store the bundles, then write the manifest and the record, once each; RecordError says what was not
    written. A record is never overwritten and never names an output the store does not hold."""
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
    session.outputs = spike.store_outputs(session, bundles, lambda name, digest: f"{digest[:16]}-{name}", "same")
    manifest = build_manifest(session)
    record = build_record(session, commit, machine, rep_of(session.args.arm), argv, fingerprint)
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
    ap.add_argument("--fault", choices=FAULTS, default=None)
    ap.add_argument("--fault-at", choices=FAULT_POINTS, default="after-before")
    ap.add_argument("--fault-repeat", type=int, default=2)
    return ap


def check_args(args):
    if not 1 <= args.repeats <= 30:
        sys.exit("--repeats is between 1 and 30; nothing was started")
    if args.fault and not 1 <= args.fault_repeat <= args.repeats:
        sys.exit("--fault-repeat is between 1 and --repeats; nothing was started")


def as_expected(session, faulted):
    """Completed, or for the faulted repeat aborted because DOSBox-X died; in both cases recovered."""
    if faulted:
        return session.status.startswith("aborted: game-died: ") and session.recovered
    return session.status == "completed" and session.recovered


def run_repeat(index, args, locs, baseline, token, commit, machine, argv, fingerprint):
    """One repeat: a session and its record. (status, seconds, as expected?)"""
    run_id = next_run_id()
    workdir = WORK_BASE / f"w{index}"
    os.close(safeio.open_directory(workdir, create_below=WORK_BASE))
    session = sessionlib.Session(run_id, locs["IW_DOS_RUN"], locs["IW_DOS_DIR"], workdir,
                                 f":{FIRST_DISPLAY + index}", baseline, token, os.environ.get("IW_DOS_OUTER_NETNS"),
                                 args.arm)
    session.argv = argv
    faulted = bool(args.fault) and index == args.fault_repeat
    if faulted:
        session.on(args.fault_at, FAULT_ACTIONS[args.fault])
    session.observe(0, "static", "driver sources sha256 (runtime/iw-dos/driver/*.py, spike cycle.py, navsteps.py, "
                    "dosconf.py, board.py)", driver_sources_sha256())
    session.observe(0, "static", "repeat of the command", f"{index} of {args.repeats}")
    session.observe(0, "static", "fault injected in this repeat", f"{args.fault} at {args.fault_at}" if faulted else "none")
    session.execute(set_level_cycle)
    try:
        write_records(session, locs[f"{EXPERIMENT}_BUNDLES"], commit, machine, argv, fingerprint)
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
    locs = rundir.run_locations(need_bundles=True, experiment=EXPERIMENT)
    machine = os.environ.get("IW_DOS_MACHINE", "local")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", machine):
        sys.exit("IW_DOS_MACHINE is not a machine id (lowercase letters, digits, dashes); nothing was started")
    token, commit = os.environ[procs.INVOCATION], os.environ["IW_DOS_DRIVER_COMMIT"]
    install = str(locs["IW_DOS_DIR"])
    try:
        procs.must(["mount", "-t", "tmpfs", "-o", "mode=1777", "tmpfs", "/tmp"])
        procs.must(["mount", "--bind", install, install])
        procs.must(["mount", "-o", "remount,bind,ro", install])
    except CommandFailed as exc:
        sys.exit(f"the namespace could not be prepared: {exc}; nothing was launched")
    if spike.install_writable(install):
        sys.exit("IW_DOS_DIR is still writable inside the namespace; nothing was launched")
    problems = rundir.run_problems(locs["IW_DOS_RUN"], locs["IW_DOS_DIR"])
    if problems:
        sys.exit("the run copy is not safe to launch from; nothing was launched: " + "; ".join(problems)[:400])
    baseline = spike.snapshot_tree(locs["IW_DOS_RUN"] / rundir.GAME_DIR)
    fingerprint = versions()
    for index in range(1, args.repeats + 1):
        _, _, good = run_repeat(index, args, locs, baseline, token, commit, machine, argv, fingerprint)
        if not good:
            print(f"repeat {index} did not end as expected; stopping, so that no wrong state is carried on",
                  file=sys.stderr)
            return 1
    return 0


def outer(args, argv):
    check_args(args)
    locs = rundir.run_locations(need_bundles=True, experiment=EXPERIMENT)
    strays = procs.pids_carrying(procs.INVOCATION)
    if strays:
        sys.exit(f"processes of an earlier driver command are alive: {strays}; stop them first (nothing was started)")
    problems = rundir.run_problems(locs["IW_DOS_RUN"], locs["IW_DOS_DIR"])
    if problems:
        sys.exit("the run copy is not safe to launch from; nothing was started: " + "; ".join(problems)[:400])
    try:
        commit = procs.must(["git", "rev-parse", "--short=12", "HEAD"], cwd=SOURCES).stdout.decode().strip()
        dirty = procs.must(["git", "status", "--porcelain", "--", "runtime", "setup", "tools", "formats"],
                           cwd=SOURCES).stdout
    except CommandFailed as exc:
        sys.exit(f"git could not say which commit runs: {exc}; nothing was started")
    if dirty:
        sys.exit("runtime/, setup/, tools/ or formats/ has uncommitted changes; commit before a recorded run")
    token = secrets.token_hex(16)
    env = dict(os.environ, IW_DOS_DRIVER_COMMIT=commit, IW_DOS_DRIVER_INNER="1",
               IW_DOS_OUTER_NETNS=spike.netns_of("self"), **{procs.INVOCATION: token})
    cmd = ["unshare", "-r", "-m", "-p", "-n", "-f", "--kill-child", "--mount-proc", sys.executable, str(LAUNCHER)] + argv
    code = launch_inner(cmd, env, args.repeats * REPEAT_BOUND)
    left = reap_invocation(token)
    if left:
        print(f"processes of this command survived its namespace and were killed: {left}", file=sys.stderr)
        return 1
    return code


def launch_inner(cmd, env, bound):
    """Run the namespaced command for at most `bound` s; at the bound it is killed through kill_marked (its
    namespace with it, --kill-child) and the exit is 1."""
    items = [procs.item(procs.INVOCATION, env[procs.INVOCATION])]
    proc = subprocess.Popen(cmd, env=env)
    try:
        return proc.wait(bound)
    except subprocess.TimeoutExpired:
        procs.kill_marked(proc.pid, items, signal.SIGKILL)
        try:
            proc.wait(REAP_BOUND)
        except subprocess.TimeoutExpired:
            pass
        print(f"the command ran past its bound of {bound} s and was killed; the repeat it was in has no record, and "
              "the run copy may be off its baseline (setup/iw-dos/iw-dos-runtime.sh)", file=sys.stderr)
        return 1


def reap_invocation(token):
    """SIGKILL what is left of this command: processes whose environment holds this command's token, exactly."""
    want = [procs.item(procs.INVOCATION, token)]
    found = procs.marked_pids(want)
    for pid in found:
        procs.kill_marked(pid, want, signal.SIGKILL)
    return found


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    args = parser().parse_args(argv)
    if os.environ.get("IW_DOS_DRIVER_INNER") == "1":
        return inner(args, argv)
    return outer(args, argv)
