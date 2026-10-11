#!/usr/bin/env python3
"""E021's Session A launcher (T45, rule 18 carve-out): one sitting, or one sitting to its records.

    python3 experiments/E021-pro-session-a/launcher.py --batch session-a --help
                                    print the batch's targets; never starts wine
    python3 experiments/E021-pro-session-a/launcher.py --batch session-a
                                    one sitting (the user's machine; the main session's [C3] lines)
    python3 experiments/E021-pro-session-a/launcher.py --records --sitting DIR --batch session-a
                                    one sitting directory to its run record and manifest (e021_export)

It is E020's launcher (experiments/E020-wine-first-run/launcher.py) with this experiment's loop,
reusing its machinery rather than copying it where it can (E020 is imported, never edited): the
outer process refuses stale processes, an unsafe prefix and uncommitted driver code (E021's folder
included), and runs the inner command bounded, in private user, mount and PID namespaces
(runner.launch_inner, runner.reap_invocation). The inner process mounts a private /tmp, binds the
install read-only, measures the binary against the F019 row (e020_sitting.binary_identity), reads
the shipped scoreboard file's sha256 from artifacts/known.json and gives the loop its restore (fix
#152), and creates the sitting directory below the one sitting root (e020_sitting.SITTING_ROOT,
shared with E020; `sitting.json` names experiment E021, so the two exports never take each other's
sittings). One Session then runs the body: the title, `before.png`, E020's watcher, the Session A
loop (e021_loop.py) sending every step through Session.perform by the click-driver, `after.png`.

E021 adds two things to E020's sitting:
* the live board reader (boardview.FrameReader) over the session's own screenshots: each read is
  `Session.observe_screenshot` (a bundle file, kept in the sitting's `session/`), decoded, cropped
  to the stage at the origin the session recorded, and read by E020's reader with the machine-local
  digit templates (`E021_TEMPLATES`, default boardview.DEFAULT_TEMPLATES). A missing or unreadable
  templates file refuses the sitting before anything starts;
* the cells already met: the latest `measurements/progress-r<nn>.json` (e021_progress), so a
  resumed batch starts where the last stopped.

Machine-local values come from the environment and never reach a record: IWP_PREFIX, IWP_DIR,
E021_BUNDLES, IWP_MACHINE, E021_TEMPLATES.
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
E020 = ROOT / "experiments" / "E020-wine-first-run"
for _path in (ROOT / "tools", ROOT / "runtime/iwp", ROOT / "setup/iwp", E020, E020 / "reader", HERE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import importlib.util  # noqa: E402

import check_counts  # noqa: E402
import e020_sitting as sitting  # noqa: E402


def _e020_launcher():
    """E020's launcher, imported read-only by its path: both experiments name their launcher
    `launcher.py`, so a plain import would find this file."""
    spec = importlib.util.spec_from_file_location("e020_launcher", E020 / "launcher.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e020_launcher = sys.modules.get("e020_launcher") or _e020_launcher()
sys.modules.setdefault("e020_launcher", e020_launcher)

EXPERIMENT = "E021"
FOLDER = "E021-pro-session-a"
SCENARIOS = HERE / "scenarios.txt"
LAUNCHER = Path(__file__).resolve()
USAGE = ("usage: launcher.py --batch <name> [--help] | --records --sitting <dir> --batch <name>")
INNER, COMMIT, DISPLAY = "IWP_E021_INNER", "IWP_E021_COMMIT", "IWP_E021_DISPLAY"
TEMPLATES_ENV = "E021_TEMPLATES"
ORIGIN_FIELD = "stage origin assumed from a centered 800x600 stage"     # the spike's observation
STAGE = (800, 600)


def batches():
    return check_counts.load_batches(SCENARIOS)


def batch_help(name, batch):
    """The batch's targets, printed by `--batch NAME --help`; never starts wine."""
    return "\n".join([
        f"batch {name} (platform {sitting.PLATFORM})",
        f"  questions: {batch.get('questions', '')}",
        f"  source: {batch.get('source', '')}",
        f"  target: {batch.get('target', '')}",
        f"  loop: at most {batch.get('games_max')} games, each played to its end, {batch.get('sitting_seconds')} s; "
        f"blocks experiments/{FOLDER}/{batch.get('blocks', '')}",
        f"  note: {batch.get('note', '')}",
        f"  records land in runs/{EXPERIMENT}/{name}/; manifests in evidence/{EXPERIMENT}/; "
        f"progress in experiments/{FOLDER}/measurements/",
    ])


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    try:
        args = e020_launcher.parser().parse_args(argv)
    except SystemExit:
        print(f"refused arguments {argv!r}; nothing was started", file=sys.stderr)
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
        return records_main(args)
    if args.sitting:
        print("--sitting belongs to --records; nothing was started", file=sys.stderr)
        return 2
    if os.environ.get(INNER) == "1":
        return inner(args.batch, known[args.batch], argv)
    return outer(args.batch, known[args.batch], argv)


def records_main(args):
    import e021_export
    if not args.sitting:
        print("--records needs --sitting <dir>", file=sys.stderr)
        return 2
    try:
        written = e021_export.export(Path(args.sitting), args.batch)
    except SystemExit as exc:
        print(f"no record written: {exc}", file=sys.stderr)
        return 1
    print("wrote " + " and ".join(written))
    return 0


# --- what E021 adds to a sitting ------------------------------------------------------------------

def templates_path(env=None):
    env = os.environ if env is None else env
    import boardview
    return Path(env.get(TEMPLATES_ENV) or boardview.DEFAULT_TEMPLATES)


def load_templates(path):
    """The digit templates, loaded; SittingRefused (nothing started) when they cannot be."""
    import glyphs
    try:
        return glyphs.Templates.load(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise sitting.SittingRefused(f"the reader's digit templates could not be loaded ({type(exc).__name__}); "
                                     f"set {TEMPLATES_ENV}; nothing was started") from None


def met_so_far():
    """The cells the committed records have met (the latest progress file), as (case, cell) pairs."""
    import cases
    import e021_progress
    needed = e021_progress.needed_from(e021_progress.load_latest())
    return {(case, cell) for case in cases.CASES for cell in cases.cells(case)} - set(needed)


def stage_origin(observations):
    """(ox, oy) from the session's own observation of where the stage is, or None."""
    for row in observations:
        if row.get("field") == ORIGIN_FIELD:
            match = re.fullmatch(r"(\d+),(\d+)", str(row.get("value", "")))
            if match:
                return int(match.group(1)), int(match.group(2))
    return None


def session_capture(active):
    """() -> (stage rgb, png sha256): one screenshot through the session, kept as a bundle file
    (`e021-read-NNNNN.png`), decoded and cropped to the stage. A capture the stage does not fit is a
    RuntimeError, which the loop answers with a clean end (`board-unreadable`)."""
    import pngdecode
    taken = [0]

    def capture():
        taken[0] += 1
        name = f"e021-read-{taken[0]:05d}.png"
        _pixels, png = active.observe_screenshot(name)
        path = next(Path(p) for n, p, _ in active.outputs if n == name)
        rgb = pngdecode.decode_file(path)
        origin = stage_origin(active.obs) or (0, 0)
        ox, oy = origin
        stage = rgb[oy:oy + STAGE[1], ox:ox + STAGE[0]]
        if stage.shape[:2] != (STAGE[1], STAGE[0]):
            raise RuntimeError(f"the capture {rgb.shape[1]}x{rgb.shape[0]} does not hold the stage at {origin}")
        return stage, png
    return capture


def make_body(paths, batch, blocks_text, summary, templates, met, restore=None, shipped_skr=None,
              watcher_factory=None, loop_factory=None, reader_factory=None):
    """The session's body, as E020's (the title, before.png, the watcher, the loop, after.png), with the
    Session A loop and its live reader. The factories are for the tests."""
    from driver.clicks import ClickDriver, parse_blocks
    from driver.watcher import Watcher
    import boardview
    import e021_loop

    blocks = parse_blocks(blocks_text)
    watcher_factory = watcher_factory or Watcher
    loop_factory = loop_factory or e021_loop.SessionALoop
    reader_factory = reader_factory or (lambda active: boardview.FrameReader(session_capture(active), templates))

    def body(active):
        active.expect("title")
        active.known_screen()
        clicks = ClickDriver(active.perform, lambda: active.obs, paths["actions"], blocks,
                             screen=active.screen_name, winner=active.screen_winner,
                             shot=lambda name: active.observe_screenshot(name)[1])
        watcher = watcher_factory(active.window, dict(active.env), paths["frames"], paths["index"],
                                  paths["log"], lambda: clicks.seq)
        thread, stop = watcher.start()
        try:
            active.observe_screenshot("before.png")
            loop = loop_factory(clicks, batch, restore=restore, shipped_skr=shipped_skr,
                                reader=reader_factory(active), met=met)
            try:
                loop.run()
            finally:
                summary.update(loop.summary)
            active.observe_screenshot("after.png")
        finally:
            stop.set()
            thread.join(timeout=30)
    return body


# --- the sitting (E020's discipline) --------------------------------------------------------------

def confined():
    _, sessionlib = e020_launcher.driver()
    return sessionlib.spike.confined_locations(argparse.Namespace(explore=False, experiment=EXPERIMENT))


def outer(name, batch, argv):
    """Refuse stale processes, an unsafe prefix, uncommitted code and missing templates; then the
    namespaced inner command, bounded, and the reaping of whatever of it is left."""
    runner, sessionlib = e020_launcher.driver()
    spike = sessionlib.spike
    locs = confined()
    load_templates(templates_path())
    strays = spike.marked_processes() + spike.prefix_processes(locs["IWP_PREFIX"])
    if strays:
        sys.exit(f"stale processes of an earlier run or of setup are alive: {sorted(set(strays))}; nothing was started")
    problems = spike.prefixlib.prefix_problems(locs["IWP_PREFIX"], locs["IWP_DIR"])
    if problems:
        sys.exit("the prefix is not safe to launch from; nothing was started: " + "; ".join(problems)[:400])
    try:
        commit = spike.must(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT).stdout.decode().strip()
        dirty = spike.must(["git", "status", "--porcelain", "--", "runtime", "setup", "tools", "formats",
                            "experiments/E020-wine-first-run", f"experiments/{FOLDER}"], cwd=ROOT,
                           require_output=False).stdout
    except spike.CommandFailed as exc:
        sys.exit(f"git could not say which commit runs: {exc}; nothing was started")
    if dirty:
        sys.exit("the driver's code has uncommitted changes; commit before a sitting (nothing was started)")
    token = secrets.token_hex(16)
    env = dict(os.environ, **{INNER: "1", COMMIT: commit, DISPLAY: sessionlib.free_display(),
                              sessionlib.INVOCATION: token})
    cmd = ["unshare", "-r", "-m", "-p", "-f", "--kill-child", "--mount-proc", sys.executable, str(LAUNCHER)] + argv
    code = runner.launch_inner(cmd, env, int(float(batch["sitting_seconds"])) + e020_launcher.BOUND_MARGIN)
    left = runner.reap_invocation(token)
    if left:
        print(f"processes of this command survived its namespace and were killed: {sorted(left)}", file=sys.stderr)
        return 1
    return code


def inner(name, batch, argv):
    """PID 1 of the private namespaces: /tmp, the install read-only, the binary measured, the
    templates and the cells met, the sitting directory, then the session."""
    _, sessionlib = e020_launcher.driver()
    spike = sessionlib.spike
    locs = confined()
    machine = os.environ.get("IWP_MACHINE", "local")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", machine):
        sys.exit("IWP_MACHINE is not a machine id (lowercase letters, digits, dashes); nothing was started")
    templates = load_templates(templates_path())
    met = met_so_far()
    spike.must(["mount", "-t", "tmpfs", "-o", "mode=1777", "tmpfs", "/tmp"], require_output=False)
    sessionlib.bind_install_readonly(locs["IWP_DIR"])
    binary = sitting.binary_identity(locs["IWP_DIR"], locs["IWP_PREFIX"], e020_launcher.f019_row())
    shipped_skr = sitting.shipped_skr_sha256()

    def restore():
        return sitting.restore_skr(locs["IWP_DIR"], locs["IWP_PREFIX"], shipped_skr)

    others = [(k, Path(v)) for k, v in locs.items()]
    root = sitting.confine_root(sitting.SITTING_ROOT, others=others)
    sid = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    paths = sitting.create_sitting(root, sid)
    blocks_path = HERE / batch["blocks"]
    doc = {"schema": sitting.SITTING_SCHEMA, "experiment": EXPERIMENT, "sitting_id": sid, "batch": name,
           "argv": list(argv), "platform": sitting.PLATFORM, "set": sitting.SET_ID, "variant": sitting.VARIANT,
           "binary": binary, "driver_commit": os.environ[COMMIT], "blocks_sha256": sitting.sha256_of(blocks_path),
           "machine": machine, "versions": spike.versions(), "session_run_id": f"{EXPERIMENT}-sitting-{sid}",
           "cells_met_before": len(met)}
    session = sessionlib.Session(doc["session_run_id"], locs["IWP_PREFIX"], locs[f"{EXPERIMENT}_BUNDLES"],
                                 locs["IWP_DIR"], os.environ.get(DISPLAY) or sessionlib.free_display(), arm=name)
    summary = {}
    try:
        session.execute(make_body(paths, batch, blocks_path.read_text(encoding="utf-8"), summary, templates, met,
                                  restore=restore, shipped_skr=shipped_skr))
    finally:
        e020_launcher.keep_session_outputs(session, paths)
        doc.update(status=session.status, recovered=session.recovered, started=session.started or spike.now(),
                   ended=session.ended or spike.now(), loop=summary)
        sitting.write_sitting_json(paths, doc)
    print(json.dumps({"sitting": sid, "batch": name, "status": session.status, "recovered": session.recovered,
                      "loop": summary}), flush=True)
    return 0 if session.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
