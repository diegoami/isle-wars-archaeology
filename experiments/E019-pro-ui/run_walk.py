#!/usr/bin/env python3
"""E019 (T24): the per-question UI walk of Isle Wars Pro, one run/1 record per question.

    python3 experiments/E019-pro-ui/run_walk.py --question Q-UI-06
    python3 experiments/E019-pro-ui/run_walk.py --batch title-options

[C3]: the main session runs this on the install machine (the walks read the user's own install
through T13's driver); the implementer turns the records into the catalogue. The command mirrors
the E004 runner's envelope (runtime/iwp/driver/runner.py): the seal, the display and the reset are
the driver Session's own; the outer process runs the walks in private user, mount and PID
namespaces, marks its processes with a token of its own, and never signals another command's.

One walk = one launch of the game = one run/1 record under runs/E019/<batch>/, with its evidence
manifest under evidence/E019/<batch>/ (the screenshots are release assets named by hash; no PNG is
committed). The next walk starts only when the last one was recovered (the reset shown to restore
the prefix); anything else stops the command, as in E004.

Machine-local values come from the environment and are never written to a record:
IWP_PREFIX, IWP_DIR, E019_BUNDLES (confined by setup/iwp/locations.py), IWP_MACHINE.

The recorder's own screen reads are pixels-read only (censuses, text rows, hover maps, timed
watches): there is no OCR pass anywhere, and no line of decompiled Lingo is read or written.
"""
import argparse
import contextlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _sub in ("setup/iwp", "runtime/iwp/spike", "runtime/iwp"):
    sys.path.insert(0, str(ROOT / _sub))
sys.path.insert(0, str(HERE))

import cycle as spike  # noqa: E402
import safeio  # noqa: E402
import steps as stepslib  # noqa: E402
from driver import session as sessionlib  # noqa: E402
from driver.errors import RecordError, StepFailed  # noqa: E402
from driver.session import Session  # noqa: E402

import pixels  # noqa: E402
import records  # noqa: E402
import walks  # noqa: E402

EXPERIMENT = records.EXPERIMENT
LAUNCHER = Path(__file__).resolve()
WALK_BOUND = 1200        # s, one walk at most: E002's whole tour took 137 to 170 s; the long
                         # watches stay far below this; the bound only ends a hang
REAP_BOUND = 10          # s, for a killed command to be reaped
WATCH_INTERVAL = 0.25    # s, the timed watches' default poll
HOVER_POLL = 0.6         # s, how long a hover map waits for a label to react
FLASH_SHARE = 0.25       # a change over this share of the watched pixels is a flash candidate
# The title screen's bottom-bar labels, for Q-UI-18's count: the measured click points and the
# band (+/- 40 px) each name. The Soleau label between Options and Scores is refused (steps.py).
LABEL_BANDS = (("new-game", 100), ("help", 215), ("options", 320), ("scores", 620), ("quit", 712))
BAND_HALF = 40
NEUTRAL = (2, 2)         # a point on any screen that highlights nothing (the stage's corner)


# --- the recorder's own reads -----------------------------------------------------------------

def read_region(session, rect):
    """Raw pixels of a stage rectangle for the recorder's own reads (a census, text rows, a hover
    map, a timed watch). The driver's public observe_region records such a read's hash as an
    observation; the recorder needs the values, and reads them through the engine's screen here,
    as the E004 command reaches the engine's env for its faults (runtime/iwp/driver/runner.py).
    The game is checked alive before and after, the same guarantee the guarded methods carry."""
    if not session.game_alive():
        raise sessionlib.GameDied("the game exited before a recorder read")
    data = session._engine.screen.raw(rect)
    if not session.game_alive():
        raise sessionlib.GameDied("the game exited during a recorder read")
    return data


class Ctx:
    """One walk's counters and observations-in-waiting (the counts the record stamps at the end)."""

    def __init__(self, spec):
        self.spec = spec
        self.step = 50                     # the recorder's own observations start past the driver's
        self.counts = {}                   # count word -> value
        self.labels = set()                # bottom-bar bands whose hover map reacted
        self.shots = 0

    def obs(self, session, field, value, source="screen"):
        session.observe(self.step, source, field, str(value))
        self.step += 1

    def count(self, word, value):
        self.counts[word] = self.counts.get(word, 0) + int(value)


def perform(session, ctx, line):
    """One step-language line; a click or key counts as an input of this walk."""
    session.perform(line)
    first = line.split()[0]
    if first in sessionlib.INPUT_OPS:
        ctx.count("inputs", 1)


def region_rect(label):
    return walks.REGIONS[label]["rect"]


# --- the recorder's read actions --------------------------------------------------------------

def census_action(session, ctx, label, quantise):
    rect = region_rect(label)
    data = read_region(session, rect)
    result = pixels.census(data, quantise)
    ctx.obs(session, "read: colour-census",
            json.dumps({"region": label, "rect": list(rect), "quantise": quantise, **result}))


def greyscale_action(session, ctx, label, quantise):
    rect = region_rect(label)
    data = read_region(session, rect)
    result = pixels.greyscale_census(data, quantise)
    ctx.obs(session, "read: greyscale-census",
            json.dumps({"region": label, "rect": list(rect), "quantise": quantise, **result}))


def text_rows_action(session, ctx, label):
    x, y, w, h = region_rect(label)
    data = read_region(session, (x, y, w, h))
    result = pixels.text_rows(data, w)
    ctx.obs(session, "read: text-rows",
            json.dumps({"region": label, "rect": [x, y, w, h], **result}))


def timed_watch(session, ctx, label, seconds, interval=WATCH_INTERVAL, flashes=False):
    """Timestamped reads of one region: every change is a timing observation (wall clock, speed =
    normal). With `flashes`, a change over FLASH_SHARE of the pixels is a flash candidate (the
    pixels-read stand-in for the event flash of Q-UI-06 and Q-UI-07)."""
    rect = region_rect(label)
    begun = time.monotonic()
    last = read_region(session, rect)
    changes = flash_candidates = 0
    while time.monotonic() - begun < seconds:
        time.sleep(interval)
        data = read_region(session, rect)
        if data == last:
            continue
        now = round(time.monotonic() - begun, 2)
        share = pixels.changed_fraction(last, data)
        ctx.obs(session, "timing: watch change",
                json.dumps({"region": label, "at_s": now, "share": round(share, 3)}))
        if flashes and share >= FLASH_SHARE:
            flash_candidates += 1
            ctx.obs(session, "flash candidate",
                    json.dumps({"region": label, "at_s": now, "share": round(share, 3)}))
        changes += 1
        last = data
    result = {"region": label, "seconds": seconds, "changes": changes}
    if flashes:
        result["flash candidates"] = flash_candidates
    ctx.obs(session, "read: timed-watch", json.dumps(result))
    return flash_candidates


def hover_map(session, ctx, label, step, ys):
    """The hover-reactive area of one region, measured by pointer moves only: at each grid point
    the pointer goes to the stage's neutral corner and then to the point, and the recorder records
    whether the band reacted (the highlight the game draws under the pointer). No point is
    clicked. Points inside a refused rectangle (the Soleau label) are skipped and counted."""
    x, y, w, h = region_rect(label)
    rect = (x, y, w, h)
    points = [(px, py) for px, py in pixels.hover_points(rect, step, ys)]
    allowed = [(px, py) for px, py in points if stepslib.forbidden(px, py) is None]
    skipped = len(points) - len(allowed)
    reacted = 0
    for px, py in allowed:
        perform(session, ctx, f"move {NEUTRAL[0]} {NEUTRAL[1]}")
        time.sleep(0.25)
        base = read_region(session, rect)
        perform(session, ctx, f"move {px} {py}")
        change = spike.poll(lambda: read_region(session, rect) != base, HOVER_POLL, 0.1)
        if change is not None:
            reacted += 1
            if label == "bottom-bar":
                for name, centre in LABEL_BANDS:
                    if abs(px - centre) <= BAND_HALF:
                        ctx.labels.add(name)
    ctx.obs(session, "read: hit-area",
            json.dumps({"region": label, "points": len(allowed), "reacted": reacted,
                        "skipped in refused areas": skipped, "grid step px": step}))
    ctx.obs(session, f"hit-area: {label}", f"{reacted} of {len(allowed)} points reacted")


# --- the composites (the multi-turn plans) ----------------------------------------------------

def place_and_attack(session, ctx, exchanges=0, attack_watch="attack-panel", attack_click=None):
    """The tour's turn up to the attack panel: place every army on the first Blue country that
    reacts, then open the attack panel. Returns whether the attack panel was reached. A refusal
    anywhere (the game ignored a country, no pair was accepted) is an observation, never a crash:
    the walk goes on and the record reports it."""
    try:
        perform(session, ctx, walks.PLACE_WATCH)
        perform(session, ctx, walks.PLACE_CLICK)
        perform(session, ctx, "watch 262 502 276 70")
        perform(session, ctx, f"click! {walks.ALL_CLICK[0]} {walks.ALL_CLICK[1]}")
        perform(session, ctx, f"click! {walks.PLACE_DONE_CLICK[0]} {walks.PLACE_DONE_CLICK[1]}")
        perform(session, ctx, "settle")
        perform(session, ctx, f"attack-picked {walks.PLACE_COUNTRIES}")
    except StepFailed as exc:
        ctx.obs(session, "turn note", f"the turn stopped early: {exc}")
        return False
    if exchanges:
        watch = walks.REGIONS[attack_watch]["rect"]
        attack_click = attack_click or walks.ATTACK_PANEL_CLICK
        try:
            perform(session, ctx, f"watch {watch[0]} {watch[1]} {watch[2]} {watch[3]}")
            done = 0
            for _ in range(exchanges):
                begun = time.monotonic()
                before = read_region(session, watch)
                perform(session, ctx, f"click! {attack_click[0]} {attack_click[1]}")
                after = read_region(session, watch)
                ctx.obs(session, "timing: attack exchange",
                        json.dumps({"at_s": round(time.monotonic() - begun, 2),
                                    "panel changed": before != after}))
                ctx.count("attacks", 1)
                done += 1
            return done
        except StepFailed as exc:
            ctx.obs(session, "turn note", f"the attacks stopped after {ctx.counts.get('attacks', 0)} "
                          f"in this turn: {exc}")
    return True


def leave_attack_and_pass(session, ctx):
    """QUIT ATTACK or DONE (whichever the panel shows), then PASS; a refusal is an observation."""
    try:
        perform(session, ctx, "watch 262 502 276 70")
        perform(session, ctx, walks.QUIT_ATTACK_CLICKS)
        perform(session, ctx, f"click! {walks.PASS_CLICK[0]} {walks.PASS_CLICK[1]}")
    except StepFailed as exc:
        ctx.obs(session, "turn note", f"the turn could not be passed: {exc}")
        return False
    return True


def composite_title_options_rounds(session, ctx, rounds=3):
    """Q-UI-10: title -> Options -> title, timed, `rounds` times, the inputs counted."""
    ctx.count("walkthroughs", 0)
    for i in range(1, rounds + 1):
        begun = time.monotonic()
        perform(session, ctx, f"click {walks.OPTIONS_CLICK[0]} {walks.OPTIONS_CLICK[1]}")
        session.wait_for_screen("options")
        to_options = round(time.monotonic() - begun, 2)
        begun = time.monotonic()
        for line in walks.BACK_TO_TITLE:
            perform(session, ctx, line)
        session.wait_for_screen("title", stable=False)
        back = round(time.monotonic() - begun, 2)
        ctx.obs(session, "timing: round to options", json.dumps({"round": i, "at_s": to_options}))
        ctx.obs(session, "timing: round back to title", json.dumps({"round": i, "at_s": back}))
        ctx.count("walkthroughs", 1)


def composite_computer_turns(session, ctx, passes=7, watch=("message-strip",), seconds=25,
                             interval=WATCH_INTERVAL, shots=True):
    """Q-UI-13 and the long halves of Q-UI-14: PASS, then watch the regions while the computer
    players take their turns; every change of every watched region is timestamped, so the pauses
    show as the gaps."""
    for i in range(1, passes + 1):
        perform(session, ctx, f"click-any? {walks.CONTINUE_CLICK[0]} {walks.CONTINUE_CLICK[1]}")
        begun = time.monotonic()
        perform(session, ctx, f"click! {walks.PASS_CLICK[0]} {walks.PASS_CLICK[1]}")
        for label in watch:
            rect = region_rect(label)
            last = read_region(session, rect)
            while time.monotonic() - begun < seconds:
                time.sleep(interval)
                data = read_region(session, rect)
                if data != last:
                    ctx.obs(session, "timing: computer turn change",
                            json.dumps({"pass": i, "region": label,
                                        "at_s": round(time.monotonic() - begun, 2),
                                        "share": round(pixels.changed_fraction(last, data), 3)}))
                    last = data
        if shots:
            perform(session, ctx, f"shot computer-turn-{i}")
    ctx.count("computer turns", passes * 3)
    ctx.obs(session, "computer turns note",
            "three computer turns between two human turns at the default seats (F003's options "
            "table); the count is passes x 3", "static")


def composite_attack_exchanges(session, ctx, turns=8, exchanges=3, need=20, watch="attack-panel"):
    """Q-UI-16: up to `turns` aggressive turns; in each, up to `exchanges` clicks on ATTACK, each
    timed around the watched panel, until `need` attacks are recorded."""
    total = 0
    for t in range(1, turns + 1):
        if total >= need:
            break
        before = ctx.counts.get("attacks", 0)
        place_and_attack(session, ctx, exchanges=exchanges, attack_watch=watch)
        total = ctx.counts.get("attacks", 0)
        if total == before:
            ctx.obs(session, "turn note", f"turn {t} gave no exchange")
        if not leave_attack_and_pass(session, ctx):
            break
    ctx.count("attacks", 0)     # ensure the count exists even when every turn was refused
    ctx.obs(session, "attacks note", "one attack is one click on the ATTACK button (F011); the "
            "timed observations carry each exchange", "static")


def composite_event_watch(session, ctx, turns=30, need=5, watch=("message-strip", "board-area")):
    """Q-UI-06 and Q-UI-07: play turns and watch for the event flash — a change taking in a large
    share of a watched region for one short interval. Candidates are counted and timestamped; the
    strip's changes are recorded beside them. Whether a candidate is a flood, a rebellion or a
    centre move is not decidable by pixels; the record says so."""
    word = "events" if ctx.spec["qid"] == "Q-UI-06" else "centre moves"
    candidates = 0
    for t in range(1, turns + 1):
        if candidates >= need:
            break
        place_and_attack(session, ctx)
        leave_attack_and_pass(session, ctx)
        for label in watch:
            candidates += timed_watch(session, ctx, label, 15, WATCH_INTERVAL, flashes=True)
            if candidates >= need:
                break
    ctx.count(word, candidates)
    ctx.obs(session, f"{word} note",
            "a candidate is a change over a large share of the watched pixels; which event it "
            "was is not decidable by pixels, and the shots and timestamps are the evidence",
            "static")


def composite_card_turns(session, ctx, turns=10):
    """Q-UI-15: up to `turns` aggressive turns; after each PASS the recorder clicks CONTINUE and
    records whether the strip changed (the award notice) — a shot when it did."""
    awards = 0
    strip = region_rect("message-strip")
    for t in range(1, turns + 1):
        place_and_attack(session, ctx, exchanges=1)
        if not leave_attack_and_pass(session, ctx):
            break
        perform(session, ctx, f"watch {strip[0]} {strip[1]} {strip[2]} {strip[3]}")
        before = read_region(session, strip)
        perform(session, ctx, f"click {walks.CONTINUE_CLICK[0]} {walks.CONTINUE_CLICK[1]}")
        if read_region(session, strip) != before:
            awards += 1
            perform(session, ctx, f"shot card-award-{t}")
    ctx.count("screenshots", awards)
    ctx.obs(session, "cards note",
            "a card follows a capture; the award notice is what this walk can reach (the turn "
            "menu's CARD button has no measured point, F003)", "static")


COMPOSITES = {
    "title_options_rounds": composite_title_options_rounds,
    "computer_turns": composite_computer_turns,
    "attack_exchanges": composite_attack_exchanges,
    "event_watch": composite_event_watch,
    "card_turns": composite_card_turns,
}


# --- the walk itself --------------------------------------------------------------------------

def run_actions(session, spec, ctx):
    for item in spec["actions"]:
        kind = item[0]
        if kind == "step":
            perform(session, ctx, item[1])
        elif kind == "wait":
            session.wait_for_screen(item[1])
        elif kind == "census":
            census_action(session, ctx, item[1], item[2])
        elif kind == "greyscale":
            greyscale_action(session, ctx, item[1], item[2])
        elif kind == "text_rows":
            text_rows_action(session, ctx, item[1])
        elif kind == "timed_watch":
            timed_watch(session, ctx, item[1], item[2], item[3])
        elif kind == "hover_map":
            hover_map(session, ctx, item[1], item[2], item[3])
        elif kind == "composite":
            COMPOSITES[item[1]](session, ctx, **item[2])
        else:
            raise ValueError(f"unknown walk action {kind!r}")


def stamp_walk_summaries(session, ctx):
    """The counts and the absence/ear notes, after the walk's actions."""
    for word, value in sorted(ctx.counts.items()):
        if word != "inputs":
            ctx.obs(session, f"count: {word}", value)
    if ctx.spec.get("reads", {}).get("absence-tour"):
        ctx.obs(session, "read: absence-tour",
                f"no list-of-events control seen on the {ctx.shots} screens this walk shot; "
                "'absence confirmed on the screens visited' is the observation, never a proof")
    if ctx.spec.get("reads", {}).get("ear-toggle"):
        ctx.obs(session, "read: ear-toggle",
                "the ear switch was clicked and clicked back; the shots before and after are the "
                "record of its reaction. Audio is off in this runtime: the driver's display "
                "namespace has no sound device, so no sound is captured here")
    if ctx.spec.get("hit_areas"):
        ctx.obs(session, "count: labels", len(ctx.labels))


def walk_body(spec, ctx):
    """The session body of one walk: the known screens, before.png, the walk, after.png."""
    def body(session):
        session.expect(*walks.expects_of(spec))
        session.known_screen()
        session.observe_screenshot("before.png")
        run_actions(session, spec, ctx)
        stamp_walk_summaries(session, ctx)
        session.observe_screenshot("after.png")
    return body


def count_shots(session):
    """The walk's screenshots so far, by name (the absence note uses it)."""
    return len({name for name, _, _ in session._engine.outputs if name.endswith(".png")})


# --- records ----------------------------------------------------------------------------------

def next_run_id(root=ROOT):
    """The next run id of E019, over every batch folder (records are never overwritten)."""
    folder = Path(root) / "runs" / EXPERIMENT
    numbers = []
    if folder.is_dir():
        for pattern in (f"{EXPERIMENT}-r*.json", f"*/{EXPERIMENT}-r*.json"):
            for p in folder.glob(pattern):
                if m := re.match(rf"{EXPERIMENT}-r(\d+)\.json$", p.name):
                    numbers.append(int(m.group(1)))
    return f"{EXPERIMENT}-r{max(numbers, default=0) + 1:04d}"


def write_records(session, spec, bundles, commit, machine, state_sha, argv, fingerprint, set_id):
    """Store the bundle and write the manifest and the record, once each, under the batch's
    folders. RecordError says what was not written; a record is never overwritten and never names
    an output the store does not hold (the E004 writer's rule)."""
    batch = spec["batch"]
    paths = {key: Path(rel) for key, rel in records.record_paths(batch, session.run_id).items()}
    taken = [str(rel) for rel in paths.values() if os.path.lexists(ROOT / rel)]
    if taken:
        raise RecordError(f"no record written: {', '.join(taken)} already exist(s)")
    try:
        for rel in paths.values():
            os.close(safeio.open_directory(ROOT / rel.parent, create_below=ROOT))
    except (safeio.Refused, OSError) as exc:
        raise RecordError(f"no record written: {exc}") from None
    engine = session._engine
    engine._error = RecordError
    engine.outputs = spike.store_outputs(engine, bundles, lambda name, digest: f"{digest[:16]}-{name}", "same")
    manifest = records.build_manifest(session.run_id, engine.outputs, set_id)
    record = records.build_record(session.run_id, spec, argv, commit, machine, state_sha, fingerprint,
                                  engine.obs, engine.outputs, engine.started, engine.ended,
                                  engine.status, session.elapsed, set_id)
    try:
        safeio.write_file(ROOT / paths["manifest"].parent, paths["manifest"].name,
                          data=(json.dumps(manifest, indent=2) + "\n").encode(), exist="new",
                          create_below=ROOT)
        safeio.write_file(ROOT / paths["run"].parent, paths["run"].name,
                          data=(json.dumps(record, indent=2) + "\n").encode(), exist="new",
                          create_below=ROOT)
    except (safeio.Refused, OSError) as exc:
        raise RecordError(f"no record written: {exc}") from None


# --- the command ------------------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--question", action="append", default=[],
                       help="a catalogue question id (Q-UI-04), repeatable, in the table's order")
    group.add_argument("--batch", help="every question of one batch, in the table's order")
    return ap.parse_args(argv)


def questions_of(args):
    if args.batch:
        batches = dict(walks.BATCHES)
        if args.batch not in batches:
            sys.exit(f"unknown batch {args.batch!r}; the batches are {sorted(batches)}; nothing was started")
        return batches[args.batch]
    for qid in args.question:
        if qid not in walks.WALKS:
            sys.exit(f"unknown question {qid!r}; nothing was started")
    return list(args.question)


def run_walk(qid, size, locs, display, commit, machine, argv, fingerprint):
    """One walk: one session, one record. (status, recovered)"""
    spec = dict(walks.WALKS[qid])
    spec["qid"] = qid
    run_id = next_run_id()
    set_id = spike.SUCCESSOR2_ID if spec.get("may_write_saved_files") else spike.SET_ID
    session = Session(run_id, locs["IWP_PREFIX"], locs[f"{EXPERIMENT}_BUNDLES"], locs["IWP_DIR"],
                      display, records.arm_of_question(qid), size or "800x600x24")
    ctx = Ctx(spec)
    session.observe(0, "static", "walk question", qid)
    session.observe(0, "static", "walk batch", spec["batch"])
    session.observe(0, "static", "speed setting",
                    "normal (the unlocked default; every timing is a wall-clock reading at it)")
    session.execute(walk_body(spec, ctx))
    ctx.shots = count_shots(session)
    state_sha = spike.start_state_sha(session.snap_before[1]) if hasattr(session, "snap_before") else "0" * 64
    try:
        write_records(session, spec, locs[f"{EXPERIMENT}_BUNDLES"], commit, machine, state_sha,
                      argv, fingerprint, set_id)
    except RecordError as exc:
        print(str(exc), file=sys.stderr)
        return session.status, False
    print(json.dumps({"question": qid, "size": size, "run_id": run_id, "status": session.status,
                      "seconds": session.elapsed, "recovered": session.recovered}), flush=True)
    return session.status, session.recovered


def inner(args, argv):
    """Runs as PID 1 of the private namespaces."""
    questions = questions_of(args)
    locs = spike.confined_locations(argparse.Namespace(explore=False, experiment=EXPERIMENT))
    machine = os.environ.get("IWP_MACHINE", "local")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", machine):
        sys.exit("IWP_MACHINE is not a machine id (lowercase letters, digits, dashes); nothing was started")
    display = os.environ.get("IWP_CYCLE_DISPLAY") or sessionlib.free_display()
    commit = os.environ["IWP_CYCLE_COMMIT"]
    spike.must(["mount", "-t", "tmpfs", "-o", "mode=1777", "tmpfs", "/tmp"], require_output=False)
    sessionlib.bind_install_readonly(locs["IWP_DIR"])
    fingerprint = spike.versions()
    for qid in questions:
        sizes = walks.WALKS[qid].get("sizes") or [None]
        for size in sizes:
            _, recovered = run_walk(qid, size, locs, display, commit, machine, argv, fingerprint)
            if not recovered:
                print(f"the {qid} walk was not recovered; stopping, so that no wrong state is carried on",
                      file=sys.stderr)
                return 1
    return 0


def outer(args, argv):
    questions = questions_of(args)
    walks_planned = sum(len(walks.WALKS[qid].get("sizes") or [None]) for qid in questions)
    locs = spike.confined_locations(argparse.Namespace(explore=False, experiment=EXPERIMENT))
    prefix = locs["IWP_PREFIX"]
    strays = spike.marked_processes() + spike.prefix_processes(prefix)
    if strays:
        sys.exit(f"stale processes of an earlier run or of setup are alive: {sorted(set(strays))}; "
                 "stop them first (nothing was started)")
    problems = spike.prefixlib.prefix_problems(prefix, locs["IWP_DIR"])
    if problems:
        sys.exit("the prefix is not safe to launch from; nothing was started: " + "; ".join(problems)[:400])
    try:
        commit = spike.must(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT).stdout.decode().strip()
        dirty = spike.must(["git", "status", "--porcelain", "--", "runtime", "setup", "tools", "formats",
                            "experiments/E019-pro-ui"], cwd=ROOT, require_output=False).stdout
    except spike.CommandFailed as exc:
        sys.exit(f"git could not say which commit runs: {exc}; nothing was started")
    if dirty:
        sys.exit("runtime/, setup/, tools/, formats/ or experiments/E019-pro-ui/ has uncommitted "
                 "changes; commit before a recorded walk")
    token = secrets.token_hex(16)
    env = dict(os.environ, IWP_CYCLE_COMMIT=commit, IWP_CYCLE_INNER="1",
               IWP_CYCLE_DISPLAY=sessionlib.free_display(),
               **{sessionlib.INVOCATION: token})
    cmd = ["unshare", "-r", "-m", "-p", "-f", "--kill-child", "--mount-proc", sys.executable,
           str(LAUNCHER)] + argv
    code = launch_inner(cmd, env, walks_planned * WALK_BOUND)
    left = reap_invocation(token)
    if left:
        print(f"processes of this command survived its namespace and were killed: {sorted(left)}",
              file=sys.stderr)
        return 1
    return code


def launch_inner(cmd, env, bound):
    """Run the namespaced command for at most `bound` s; at the bound it is killed (its namespace
    with it, --kill-child) through kill_marked, with this command's token."""
    items = [f"{sessionlib.INVOCATION}={env[sessionlib.INVOCATION]}".encode()]
    proc = spike.spawn(cmd, env=env)
    try:
        return proc.wait(bound)
    except subprocess.TimeoutExpired:
        sessionlib.kill_marked(proc.pid, items)
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(REAP_BOUND)
        print(f"the command ran past its bound of {bound} s and was killed; the walk it was in has no "
              "record, and the prefix may be off its baseline (setup/iwp/iwp-runtime.sh)", file=sys.stderr)
        return 1


def reap_invocation(token):
    """SIGKILL what is left of this command: the processes whose environment holds this command's
    token, exactly. Another command's processes are never signalled. The pids found."""
    found = sessionlib.invocation_processes(token)
    want = [f"{sessionlib.INVOCATION}={token}".encode()]
    for pid in found:
        sessionlib.kill_marked(pid, want)
    return found


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    args = parse_args(argv)
    if os.environ.get("IWP_CYCLE_INNER") == "1":
        return inner(args, argv)
    return outer(args, argv)


if __name__ == "__main__":
    sys.exit(main())
