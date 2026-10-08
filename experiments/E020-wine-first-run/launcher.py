#!/usr/bin/env python3
"""E020's sitting launcher and batch dispatcher (T38, rule 18 carve-out).

The one command T37's brief sketched, reached through `tools/wine-driver.sh` (the path Done-when 2
names). It resolves a batch from `scenarios.txt` and refuses, by name and before wine starts, any
batch that is not one "Why a run is made" names (constraint B).

    wine-driver.sh --batch NAME --help        print NAME's targets; never starts wine (Done-when 2)
    wine-driver.sh --batch NAME               one sitting of NAME (the user's machine, after the
                                              owner's go-ahead)
    wine-driver.sh --records --sitting DIR --batch NAME
                                              one sitting directory to its run record and manifest

A sitting runs as the E004 command does (runtime/iwp/driver/runner.py), reusing its machinery
rather than reinventing it (T38 round 2, R1, R2, R10): the outer process refuses stale processes,
an unsafe prefix and uncommitted driver code, and gives the command its own invocation token; the
inner process runs as PID 1 of private user, mount and PID namespaces, with a private /tmp and the
install bound read-only. There, before the launch, the binary's identity is measured (e020_sitting:
the install's and the run copy's Islepro.exe equal the F019 row) and the sitting directory is
created in its one confined root (constraint A, R4). Then one Session (session.py: the seal, its
own Xvfb, the game in its own network namespace) executes the body: the title screen, `before.png`,
the watcher on the session's own display and game window, the batch loop (e020_loop.py) sending
every step through Session.perform by the click-driver, `after.png`. Session.complete() and
finish() decide the status; `sitting.json` keeps it, with the session's times, whatever happened.

Machine-local values come from the environment, as for E004, and never reach a record:
IWP_PREFIX, IWP_DIR, E020_BUNDLES (confined by setup/iwp/locations.py), and IWP_MACHINE.
"""
import argparse
import json
import os
import re
import secrets
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _sub in ("tools", "runtime/iwp", "setup/iwp", str(HERE.relative_to(ROOT))):
    if str(ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(ROOT / _sub))

import check_counts  # noqa: E402
import check_no_originals  # noqa: E402
import e020_sitting as sitting  # noqa: E402

EXPERIMENT = sitting.EXPERIMENT
PLATFORM = sitting.PLATFORM
SCENARIOS = HERE / "scenarios.txt"
LAUNCHER = Path(__file__).resolve()
USAGE = "usage: wine-driver.sh --batch <name> [--help] | --records --sitting <dir> --batch <name>"
INNER, COMMIT, DISPLAY = "IWP_E020_INNER", "IWP_E020_COMMIT", "IWP_E020_DISPLAY"
BOUND_MARGIN = 900          # s, past `sitting_seconds`: the seal, the launch, the last turn, finish and reset


def batches():
    return check_counts.load_batches(SCENARIOS)


def batch_help(name, batch):
    """The batch's targets, printed by `--batch NAME --help`; never starts wine."""
    return "\n".join([
        f"batch {name} (platform {PLATFORM})",
        f"  questions: {batch.get('questions', '')}",
        f"  source: {batch.get('source', '')}",
        f"  target: {batch.get('target', '')}",
        f"  counted: one {batch.get('event', '')} = game:ordinal event:seq {batch.get('event_fields', '')}, "
        f"citing two frames",
        f"  floors: at least {batch.get('events_min')} {batch.get('event')} events across at least "
        f"{batch.get('games_min')} game(s); claims {batch.get('claims', '')} checked per arm",
        f"  loop: at most {batch.get('games_max')} games of {batch.get('turns_max')} turns, "
        f"{batch.get('sitting_seconds')} s; blocks experiments/{EXPERIMENT}-wine-first-run/{batch.get('blocks', '')}",
        f"  note: {batch.get('note', '')}",
        f"  records land in runs/{EXPERIMENT}/{name}/; manifests in evidence/{EXPERIMENT}/",
    ])


def parser():
    ap = argparse.ArgumentParser(prog="wine-driver.sh", add_help=False, usage=USAGE, allow_abbrev=False)
    ap.add_argument("--batch")
    ap.add_argument("--help", "-h", action="store_true")
    ap.add_argument("--records", action="store_true")
    ap.add_argument("--sitting")
    return ap


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    try:
        args = parser().parse_args(argv)
    except SystemExit:
        print(f"refused arguments {argv!r} (no other option exists: the sitting root is fixed, "
              "constraint A); nothing was started", file=sys.stderr)
        return 2
    known = batches()
    if args.batch is None:
        print(USAGE, file=sys.stderr if not args.help else sys.stdout)
        print("batches: " + ", ".join(sorted(known)))
        return 0 if args.help else 2
    if args.batch not in known:
        print(f"unknown batch {args.batch!r}: the batch list names {sorted(known)}; nothing was started",
              file=sys.stderr)
        return 2
    if args.help:
        print(batch_help(args.batch, known[args.batch]))
        return 0
    if args.records:
        return records_main(args, known[args.batch])
    if args.sitting:
        print("--sitting belongs to --records; nothing was started", file=sys.stderr)
        return 2
    if os.environ.get(INNER) == "1":
        return inner(args.batch, known[args.batch], argv)
    return outer(args.batch, known[args.batch], argv)


def records_main(args, batch):
    import e020_export
    if not args.sitting:
        print("--records needs --sitting <dir>", file=sys.stderr)
        return 2
    try:
        written = e020_export.export(Path(args.sitting), args.batch, batch)
    except SystemExit as exc:
        print(f"no record written: {exc}", file=sys.stderr)
        return 1
    print("wrote " + " and ".join(written))
    return 0


# --- the sitting -------------------------------------------------------------------------------

def driver():
    from driver import runner, session as sessionlib
    return runner, sessionlib


def confined():
    _, sessionlib = driver()
    return sessionlib.spike.confined_locations(argparse.Namespace(explore=False, experiment=EXPERIMENT))


def outer(name, batch, argv):
    """Refuse stale processes, an unsafe prefix and uncommitted code; then the namespaced inner
    command, bounded, and the reaping of whatever of it is left (runner.outer's discipline)."""
    runner, sessionlib = driver()
    spike = sessionlib.spike
    locs = confined()
    strays = spike.marked_processes() + spike.prefix_processes(locs["IWP_PREFIX"])
    if strays:
        sys.exit(f"stale processes of an earlier run or of setup are alive: {sorted(set(strays))}; nothing was started")
    problems = spike.prefixlib.prefix_problems(locs["IWP_PREFIX"], locs["IWP_DIR"])
    if problems:
        sys.exit("the prefix is not safe to launch from; nothing was started: " + "; ".join(problems)[:400])
    try:
        commit = spike.must(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT).stdout.decode().strip()
        dirty = spike.must(["git", "status", "--porcelain", "--", "runtime", "setup", "tools", "formats",
                            f"experiments/{EXPERIMENT}-wine-first-run"], cwd=ROOT, require_output=False).stdout
    except spike.CommandFailed as exc:
        sys.exit(f"git could not say which commit runs: {exc}; nothing was started")
    if dirty:
        sys.exit("the driver's code has uncommitted changes; commit before a sitting (nothing was started)")
    token = secrets.token_hex(16)
    env = dict(os.environ, **{INNER: "1", COMMIT: commit, DISPLAY: sessionlib.free_display(),
                              sessionlib.INVOCATION: token})
    cmd = ["unshare", "-r", "-m", "-p", "-f", "--kill-child", "--mount-proc", sys.executable, str(LAUNCHER)] + argv
    code = runner.launch_inner(cmd, env, int(float(batch["sitting_seconds"])) + BOUND_MARGIN)
    left = runner.reap_invocation(token)
    if left:
        print(f"processes of this command survived its namespace and were killed: {sorted(left)}", file=sys.stderr)
        return 1
    return code


def inner(name, batch, argv):
    """PID 1 of the private namespaces: /tmp, the install read-only, the binary measured, the sitting
    directory, then the session."""
    _, sessionlib = driver()
    spike = sessionlib.spike
    locs = confined()
    machine = os.environ.get("IWP_MACHINE", "local")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", machine):
        sys.exit("IWP_MACHINE is not a machine id (lowercase letters, digits, dashes); nothing was started")
    spike.must(["mount", "-t", "tmpfs", "-o", "mode=1777", "tmpfs", "/tmp"], require_output=False)
    sessionlib.bind_install_readonly(locs["IWP_DIR"])
    row = f019_row()
    binary = sitting.binary_identity(locs["IWP_DIR"], locs["IWP_PREFIX"], row)
    others = [(k, Path(v)) for k, v in locs.items()]
    root = sitting.confine_root(sitting.SITTING_ROOT, others=others)
    sid = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    paths = sitting.create_sitting(root, sid)
    blocks_path = HERE / batch["blocks"]
    doc = {"schema": sitting.SITTING_SCHEMA, "sitting_id": sid, "batch": name, "argv": list(argv),
           "platform": PLATFORM, "set": sitting.SET_ID, "variant": sitting.VARIANT, "binary": binary,
           "driver_commit": os.environ[COMMIT], "blocks_sha256": sitting.sha256_of(blocks_path),
           "machine": machine, "versions": spike.versions(), "session_run_id": f"{EXPERIMENT}-sitting-{sid}"}
    session = sessionlib.Session(doc["session_run_id"], locs["IWP_PREFIX"], locs[f"{EXPERIMENT}_BUNDLES"],
                                 locs["IWP_DIR"], os.environ.get(DISPLAY) or sessionlib.free_display(), arm=name)
    summary = {}
    try:
        session.execute(make_body(paths, batch, blocks_path.read_text(encoding="utf-8"), summary))
    finally:
        keep_session_outputs(session, paths)
        doc.update(status=session.status, recovered=session.recovered, started=session.started or spike.now(),
                   ended=session.ended or spike.now(), loop=summary)
        sitting.write_sitting_json(paths, doc)
    print(json.dumps({"sitting": sid, "batch": name, "status": session.status, "recovered": session.recovered,
                      "loop": summary}), flush=True)
    return 0 if session.status == "completed" else 1


def f019_row():
    """The F019 known-good row this dispatch runs under (rule 17: read, never re-typed)."""
    for row in check_no_originals.load_f019_table(ROOT):
        if row.get("set") == sitting.SET_ID and row.get("variant") == sitting.VARIANT:
            return row
    raise sitting.SittingRefused(f"the F019 known-good row for {sitting.SET_ID}/{sitting.VARIANT} is missing; "
                                 "nothing was started")


def make_body(paths, batch, blocks_text, summary, watcher_factory=None, loop_factory=None):
    """The session's body: the title, before.png, the watcher on the session's display and window,
    the loop through Session.perform, after.png. The factories are for the tests."""
    from driver.clicks import ClickDriver, parse_blocks
    from driver.watcher import Watcher
    import e020_loop

    blocks = parse_blocks(blocks_text)
    watcher_factory = watcher_factory or Watcher
    loop_factory = loop_factory or e020_loop.BatchLoop

    def body(active):
        active.expect("title")
        active.known_screen()
        clicks = ClickDriver(active.perform, lambda: active.obs, paths["actions"], blocks,
                             screen=active.screen_name,                         # pixels, never OCR (round 4)
                             winner=active.screen_winner,                       # colour words by pixels (round 6)
                             shot=lambda name: active.observe_screenshot(name)[1])   # the PNG file's sha256
        watcher = watcher_factory(active.window, dict(active.env), paths["frames"], paths["index"],
                                  paths["log"], lambda: clicks.seq)
        thread, stop = watcher.start()
        try:
            active.observe_screenshot("before.png")
            loop = loop_factory(clicks, batch)
            try:
                loop.run()
            finally:
                summary.update(loop.summary)     # an aborted loop's summary says why (round 3, R1)
            active.observe_screenshot("after.png")
        finally:
            stop.set()
            thread.join(timeout=30)
    return body


def keep_session_outputs(session, paths):
    """The session's own screenshots and logs, copied into the sitting directory (never written over)."""
    _, sessionlib = driver()
    for name, path, _ in session.outputs:
        try:
            sessionlib.safeio.write_file(paths["session"], name, source=Path(path), exist="new")
        except (sessionlib.safeio.Refused, OSError) as exc:
            print(f"{name} was not kept in the sitting directory: {type(exc).__name__}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
