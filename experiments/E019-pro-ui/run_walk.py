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
DEFAULT_SIZE = "800x600x24"   # the display a walk without `sizes` runs at (E004's)


# --- the recorder's own reads -----------------------------------------------------------------

# The recorder's clock and sleep. Every timed loop goes through these two names, so a test drives the
# loops with a fake clock instead of waiting (tests/test_e019_ui_catalogue.py).
CLOCK = time.monotonic
SLEEP = time.sleep


def poll(condition, timeout, interval=0.1):
    """Seconds until condition() is truthy, or None at the timeout (the spike's poll, on CLOCK/SLEEP)."""
    start = CLOCK()
    while True:
        if condition():
            return round(CLOCK() - start, 2)
        if CLOCK() - start > timeout:
            return None
        SLEEP(interval)


def read_region(session, rect):
    """Raw pixels of a stage rectangle (or, with rect None, of the whole display) for the recorder's
    own reads (a census, text rows, a hover map, a timed watch, the display size). The driver's
    public observe_region records such a read's hash as an observation; the recorder needs the
    values, and reads them through the engine's screen here, as the E004 command reaches the
    engine's env for its faults (runtime/iwp/driver/runner.py). The game is checked alive before
    and after, the same guarantee the guarded methods carry."""
    if not session.game_alive():
        raise sessionlib.GameDied("the game exited before a recorder read")
    data = session._engine.screen.raw(rect)
    if not session.game_alive():
        raise sessionlib.GameDied("the game exited during a recorder read")
    return data


class Ctx:
    """One walk's counters and observations-in-waiting (the counts the record stamps at the end)."""

    def __init__(self, spec, size=None):
        self.spec = spec
        self.size = size or DEFAULT_SIZE
        self.step = 50                     # the recorder's own observations start past the driver's
        self.counts = {}                   # count word -> value
        self.labels = set()                # bottom-bar bands whose hover map reacted
        self.shots = 0                     # the walk's own screenshots (the `shot` steps)
        self.shot_names = []               # their names, in order
        self.attempts = 0                  # the `click-any?` groups (attempts the game may refuse)
        self.reads = {}                    # read kind -> how many were recorded
        self.timings = 0                   # timing observations recorded
        self.candidate_shots = 0           # the flash candidates' own shots

    def obs(self, session, field, value, source="screen"):
        session.observe(self.step, source, field, str(value))
        self.step += 1
        if field.startswith("read: "):
            kind = field[len("read: "):]
            self.reads[kind] = self.reads.get(kind, 0) + 1
        if field.startswith("timing:"):
            self.timings += 1

    def count(self, word, value):
        self.counts[word] = self.counts.get(word, 0) + int(value)


def perform(session, ctx, line):
    """One step-language line; a click or key counts as an input of this walk, a `shot` as one of the
    walk's screenshots, and a `click-any?` group as one attempted (possibly refused) input."""
    session.perform(line)
    words = line.split()
    first = words[0]
    if first in sessionlib.INPUT_OPS:
        ctx.count("inputs", 1)
    if first == "shot":
        ctx.shots += 1
        ctx.shot_names.append(f"{words[1]}.png")
    if first in ("click-any?", "click-any"):
        ctx.attempts += 1


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


def display_size_action(session, ctx):
    """The display's size as measured: the pixel count of one capture of the whole display, beside
    the size the walk asked the driver for (R5, round 2: a Q-UI-19 record names the size it shows,
    and the check compares the two; a launch is never counted as a size)."""
    data = read_region(session, None)
    ctx.obs(session, "display size",
            json.dumps({"requested": ctx.size, "display pixels": len(data) // 3}))


def watch_regions(session, ctx, labels, seconds, interval=WATCH_INTERVAL, flashes=False, countable=None,
                  begun=None, field="timing: watch change", extra=None, stop_at=None, shoot=False):
    """Timestamped reads of one or more regions, **polled together in one timed loop** (R4, round 2:
    one budget shared by sequential per-region loops starved every region but the first). Each tick
    reads every region once; every change of every region is a timing observation (wall clock,
    speed = normal).

    With `flashes`, a change over FLASH_SHARE of a region's pixels is a flash candidate, recorded per
    region. A tick in which any `countable` region had one is one counted candidate tick (two regions
    changing together are one tick, never two); with `shoot` each counted tick gets its own screenshot,
    the evidence the catalogue inspects. A candidate is a large change, nothing more: an ordinary
    redraw or either transition of a flash makes one, and the recorder never names its kind.
    Returns the counted candidate ticks."""
    labels = list(labels)
    countable = set(labels if countable is None else countable)
    extra = dict(extra or {})
    rects = {label: region_rect(label) for label in labels}
    begun = CLOCK() if begun is None else begun
    last = {label: read_region(session, rects[label]) for label in labels}
    changes = {label: 0 for label in labels}
    candidates = {label: 0 for label in labels}
    ticks = counted = 0
    while CLOCK() - begun < seconds:
        if stop_at is not None and counted >= stop_at:
            break
        SLEEP(interval)
        ticks += 1
        now = round(CLOCK() - begun, 2)
        tick_counts = False
        for label in labels:
            data = read_region(session, rects[label])
            if data == last[label]:
                continue
            share = round(pixels.changed_fraction(last[label], data), 3)
            ctx.obs(session, field, json.dumps({**extra, "region": label, "at_s": now, "share": share}))
            changes[label] += 1
            if flashes and share >= FLASH_SHARE:
                candidates[label] += 1
                ctx.obs(session, "flash candidate",
                        json.dumps({**extra, "region": label, "at_s": now, "share": share}))
                if label in countable:
                    tick_counts = True
            last[label] = data
        if tick_counts:
            counted += 1
            if shoot:
                ctx.candidate_shots += 1
                perform(session, ctx, f"shot flash-candidate-{ctx.candidate_shots}")
    result = {**extra, "regions": labels, "seconds": seconds, "interval": interval, "ticks": ticks,
              "changes": changes}
    if flashes:
        result["flash candidates"] = candidates
        result["counted candidate ticks"] = counted
    ctx.obs(session, "read: timed-watch", json.dumps(result))
    return counted


def timed_watch(session, ctx, labels, seconds, interval=WATCH_INTERVAL, flashes=False):
    """The `timed_watch` action: one region or a list of them, polled together (watch_regions)."""
    labels = [labels] if isinstance(labels, str) else list(labels)
    return watch_regions(session, ctx, labels, seconds, interval, flashes=flashes)


def hover_map(session, ctx, label, step, ys):
    """The hover-reactive area of one region, measured by pointer moves only: at each grid point
    the pointer goes to the stage's neutral corner and then to the point, and the recorder records
    whether the region changed (the highlight the game draws under the pointer). No point is
    clicked. Points inside a refused rectangle (the Soleau label) are skipped and counted."""
    x, y, w, h = region_rect(label)
    rect = (x, y, w, h)
    points = [(px, py) for px, py in pixels.hover_points(rect, step, ys)]
    allowed = [(px, py) for px, py in points if stepslib.forbidden(px, py) is None]
    skipped = len(points) - len(allowed)
    reacted = 0
    for px, py in allowed:
        perform(session, ctx, f"move {NEUTRAL[0]} {NEUTRAL[1]}")
        SLEEP(0.25)
        base = read_region(session, rect)
        perform(session, ctx, f"move {px} {py}")
        change = poll(lambda: read_region(session, rect) != base, HOVER_POLL, 0.1)
        if change is not None:
            reacted += 1
            if label == "bottom-bar":
                for name, centre in LABEL_BANDS:
                    if abs(px - centre) <= BAND_HALF:
                        ctx.labels.add(name)
    ctx.obs(session, "read: hit-area",
            json.dumps({"region": label, "points": len(allowed), "reacted": reacted,
                        "skipped in refused areas": skipped, "grid step px": step}))
    ctx.obs(session, f"hit-area: {label}", json.dumps({"points": len(allowed), "reacted": reacted}))


# --- the composites (the multi-turn plans) ----------------------------------------------------

def place_and_attack(session, ctx, exchanges=0, attack_watch="attack-panel", attack_click=None,
                     strict_attack_ready=False):
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
        if strict_attack_ready:
            screen = session.screen_name()
            if screen in {"eliminated", "game-over", "scoreboard"}:
                ctx.obs(session, "attacks stop", json.dumps({"result": f"terminal {screen}"}))
                return False
            if screen != "board-menu" or not session.screen_attack_ready():
                ctx.obs(session, "attacks stop", json.dumps({
                    "result": "unsupported attack phase", "screen": screen,
                }))
                return False
        attack_ok = True
        try:
            perform(session, ctx, f"watch {watch[0]} {watch[1]} {watch[2]} {watch[3]}")
            for _ in range(exchanges):
                begun = CLOCK()
                before = read_region(session, watch)
                if strict_attack_ready:
                    screen = session.screen_name()
                    if screen in {"eliminated", "game-over", "scoreboard"}:
                        ctx.obs(session, "attacks stop", json.dumps({"result": f"terminal {screen}"}))
                        attack_ok = False
                        break
                    if screen != "board-menu" or not session.screen_attack_ready():
                        ctx.obs(session, "attacks stop", json.dumps({
                            "result": "unsupported attack phase", "screen": screen,
                        }))
                        attack_ok = False
                        break
                inputs_before = ctx.counts.get("inputs", 0) if strict_attack_ready else None
                perform(session, ctx, f"click! {attack_click[0]} {attack_click[1]}")
                after = read_region(session, watch)
                panel_changed = before != after
                if strict_attack_ready:
                    input_proved = ctx.counts.get("inputs", 0) == inputs_before + 1
                    ctx.obs(session, "timing: attack exchange",
                            json.dumps({"at_s": round(CLOCK() - begun, 2), "panel changed": panel_changed,
                                        "input proved": input_proved}))
                    if not input_proved or not panel_changed:
                        ctx.obs(session, "attacks stop", json.dumps({
                            "result": "attack input or watched panel change unproved",
                            "input proved": input_proved, "panel changed": panel_changed,
                        }))
                        attack_ok = False
                        break
                else:
                    ctx.obs(session, "timing: attack exchange",
                            json.dumps({"at_s": round(CLOCK() - begun, 2), "panel changed": panel_changed}))
                ctx.count("attacks", 1)
        except StepFailed as exc:
            ctx.obs(session, "turn note", f"the attacks stopped after {ctx.counts.get('attacks', 0)} "
                          f"in this walk: {exc}")
            if strict_attack_ready:
                ctx.obs(session, "attacks stop", json.dumps({
                    "result": "strict attack input refused", "count preserved": ctx.counts.get("attacks", 0),
                }))
                attack_ok = False
    return attack_ok if strict_attack_ready else True


def leave_attack_and_pass(session, ctx):
    """QUIT ATTACK or DONE (whichever the panel shows), then PASS; return its clock origin.

    The origin is taken after the attack panel has closed and immediately before the accepted PASS
    click, so setup time is not included in the computer-turn watch. A refusal is an observation and
    returns None.
    """
    try:
        perform(session, ctx, "watch 262 502 276 70")
        perform(session, ctx, walks.QUIT_ATTACK_CLICKS)
        begun = CLOCK()
        perform(session, ctx, f"click! {walks.PASS_CLICK[0]} {walks.PASS_CLICK[1]}")
    except StepFailed as exc:
        ctx.obs(session, "turn note", f"the turn could not be passed: {exc}")
        return None
    return begun


def wait_human_ready_after_pass(session, ctx, turn):
    """Require a real post-PASS departure, the existing quiet settle, and the human turn menu.

    This is deliberately separate from the Q-UI-15 card-path helper.  Q-UI-16 has no supported
    award probe: terminal, capture/move-in, unknown and any other unsupported state all stop the
    walk rather than receiving a stale placement or PASS input.
    """
    departure = poll(lambda: session.screen_name() != "board-menu", 4, WATCH_INTERVAL)
    if departure is None:
        ctx.obs(session, "attack path stop", f"turn {turn}: no observed post-PASS departure before timeout")
        return False
    ctx.obs(session, "attack path departure", json.dumps({"turn": turn, "after_s": departure}))
    try:
        perform(session, ctx, "watch all")
        perform(session, ctx, "settle 4")
    except StepFailed as exc:
        ctx.obs(session, "attack path stop", f"turn {turn}: settle4 timeout or refusal: {exc}")
        return False

    screen = session.screen_name()
    if screen == "board-menu":
        ctx.obs(session, "attack path probe", json.dumps({"turn": turn, "result": "human-ready board-menu"}))
        return True
    if screen in {"eliminated", "game-over", "scoreboard"}:
        ctx.obs(session, "attack path stop", json.dumps({"turn": turn, "result": f"terminal {screen}"}))
        return False
    ctx.obs(session, "attack path stop", json.dumps({
        "turn": turn, "result": "unsupported post-PASS state", "screen": screen,
    }))
    return False


def composite_title_options_rounds(session, ctx, rounds=3):
    """Q-UI-10: title -> Options -> title, timed, `rounds` times, the inputs counted."""
    ctx.count("walkthroughs", 0)
    for i in range(1, rounds + 1):
        begun = CLOCK()
        perform(session, ctx, f"click {walks.OPTIONS_CLICK[0]} {walks.OPTIONS_CLICK[1]}")
        session.wait_for_screen("options")
        to_options = round(CLOCK() - begun, 2)
        begun = CLOCK()
        for line in walks.BACK_TO_TITLE:
            perform(session, ctx, line)
        session.wait_for_screen("title", stable=False)
        back = round(CLOCK() - begun, 2)
        ctx.obs(session, "timing: round to options", json.dumps({"round": i, "at_s": to_options}))
        ctx.obs(session, "timing: round back to title", json.dumps({"round": i, "at_s": back}))
        ctx.count("walkthroughs", 1)


def composite_computer_turns(session, ctx, passes=7, watch=("message-strip",), seconds=25,
                             interval=WATCH_INTERVAL, shots=True):
    """Q-UI-13 and the long half of Q-UI-14: play and close the human turn, PASS, then watch the
    regions together while the computer players take their turns. Every change of every watched
    region is timestamped from the accepted PASS click, so the pauses show as the gaps. The recorder
    counts its own PASS clicks that the game took; the computer turns are derived from them (three
    computer seats by default, F003), never identified on the screen."""
    taken = 0
    for i in range(1, passes + 1):
        perform(session, ctx, f"click-any? {walks.CONTINUE_CLICK[0]} {walks.CONTINUE_CLICK[1]}")
        if not place_and_attack(session, ctx, exchanges=0):
            break
        begun = leave_attack_and_pass(session, ctx)
        if begun is None:
            break
        taken += 1
        watch_regions(session, ctx, watch, seconds, interval, begun=begun,
                      field="timing: computer turn change", extra={"pass": i})
        if shots:
            perform(session, ctx, f"shot computer-turn-{i}")
    ctx.count("passes", taken)
    ctx.count("computer turns derived from passes", taken * 3)
    ctx.obs(session, "computer turns note",
            "the computer turns are not identified on the screen: the count is the walk's PASS "
            "clicks the game took, times three computer seats at the default seats (F003's options "
            "table)", "static")


def composite_attack_exchanges(session, ctx, turns=8, exchanges=3, need=20, watch="attack-panel",
                               strict=False):
    """Q-UI-16: up to `turns` aggressive turns; in each, up to `exchanges` clicks on ATTACK, each
    timed around the watched panel, until `need` attacks are recorded."""
    total = 0
    for t in range(1, turns + 1):
        if total >= need:
            break
        if strict:
            screen = session.screen_name()
            if screen in {"eliminated", "game-over", "scoreboard"}:
                ctx.obs(session, "attack path stop", json.dumps({"turn": t, "result": f"terminal {screen}"}))
                break
            if screen != "board-menu":
                ctx.obs(session, "attack path stop", json.dumps({
                    "turn": t, "result": "unsupported pre-placement state", "screen": screen,
                }))
                break
        before = ctx.counts.get("attacks", 0)
        place_ok = place_and_attack(session, ctx, exchanges=exchanges, attack_watch=watch,
                                    strict_attack_ready=strict)
        if strict and not place_ok:
            break
        total = ctx.counts.get("attacks", 0)
        if total == before:
            ctx.obs(session, "turn note", f"turn {t} gave no exchange")
        if strict and total == before:
            break
        if strict and not session.screen_attack_ready():
            ctx.obs(session, "attacks stop", json.dumps({"result": "combat ended before PASS", "turn": t}))
            break
        if leave_attack_and_pass(session, ctx) is None:
            break
        if strict and total < need and not wait_human_ready_after_pass(session, ctx, t):
            break
    ctx.count("attacks", 0)     # ensure the count exists even when every turn was refused
    ctx.obs(session, "attacks note", "an attack counted here is a click on the ATTACK button that "
            "changed the watched panel (click! refuses one that did not); one click is one exchange "
            "by F011's reading", "static")


def composite_event_watch(session, ctx, turns=30, need=5, watch=("message-strip", "board-area"),
                          word="flash candidates", count_regions=None):
    """Q-UI-06 and Q-UI-07: play turns and watch the regions together (watch_regions) for large
    changes. Each counted candidate tick is timestamped and shot; whether it was a flood, a
    rebellion, a centre move or an ordinary redraw is not decidable by pixels, so the count is of
    candidates only (`word`), and the walk table declares it a proxy of the row's target.
    `count_regions` names the regions a tick may be counted from (Q-UI-07 counts only the board
    area, where the centre flash is drawn; Q-UI-06 counts either)."""
    countable = tuple(count_regions) if count_regions else tuple(watch)
    candidates = 0
    for _ in range(1, turns + 1):
        if candidates >= need:
            break
        place_and_attack(session, ctx)
        leave_attack_and_pass(session, ctx)
        candidates += watch_regions(session, ctx, watch, 15, WATCH_INTERVAL, flashes=True,
                                    countable=countable, stop_at=need - candidates, shoot=True)
    ctx.count(word, candidates)
    ctx.obs(session, f"{word} note",
            "a candidate is a poll tick in which a counted region changed over a large share of its "
            "pixels; an ordinary redraw or either transition of a flash makes one; which event, if "
            "any, it was is not decided here; each one's shot and timestamp are the evidence",
             "static")


def wait_card_path(session, ctx, turn):
    """Wait for a post-PASS human turn or the measured green card-path probe.

    The existing settle-4 machinery is the only wait here: it establishes quiet pixels, then the
    measured screen probes decide whether an input is safe. A quiet board, a grey card prompt, an
    unknown state, a terminal state, or a failed settle is unsupported and stops the composite;
    none permits a game input. A candidate shot is deliberately named and recorded as unidentified
    evidence for the catalogue to read later.
    """
    # A board-menu reading immediately after PASS may be stale.  Require one observed departure
    # before the settle-4 result can be interpreted as human readiness or an award prompt.
    departure = poll(lambda: session.screen_name() != "board-menu", 4, WATCH_INTERVAL)
    if departure is None:
        ctx.obs(session, "card path stop", f"turn {turn}: no observed post-PASS departure before timeout")
        return None
    ctx.obs(session, "card path departure", json.dumps({"turn": turn, "after_s": departure}))

    try:
        perform(session, ctx, "watch all")
        perform(session, ctx, "settle 4")
    except StepFailed as exc:
        ctx.obs(session, "card path stop", f"turn {turn}: settle4 timeout or refusal: {exc}")
        return None

    screen = session.screen_name()
    if screen == "board-menu":
        ctx.obs(session, "card path probe", json.dumps({"turn": turn, "result": "human-ready board-menu"}))
        return "human"
    if screen in {"eliminated", "game-over", "scoreboard"}:
        ctx.obs(session, "card path stop", json.dumps({"turn": turn, "result": f"terminal {screen}"}))
        return None
    if screen == "board" and session.screen_card_award():
        ctx.obs(session, "card path probe", json.dumps({
            "turn": turn,
            "result": "measured green prompt population",
            "reading": "none: candidate screenshot remains unidentified",
        }))
        return "candidate"

    ctx.obs(session, "card path stop", json.dumps({
        "turn": turn,
        "result": "unsupported post-PASS state",
        "screen": screen,
        "reading": "no award or human phase identified",
    }))
    return None


def composite_card_turns(session, ctx, turns=10):
    """Q-UI-15: up to `turns` aggressive turns with conservative post-PASS phase handling.

    Placement refusal ends the composite. After an accepted PASS, the recorder waits for quiet and
    then accepts only the existing measured human-menu or green prompt probe. The prompt candidate
    is shot before the measured CONTINUE click; the screenshot's meaning remains for F020 to read.
    The walk stops after the first captured candidate: its target is one screenshot, and the next
    turn could begin while the computers are still acting after CONTINUE.
    """
    candidates = 0
    for t in range(1, turns + 1):
        if not place_and_attack(session, ctx, exchanges=1):
            break
        if leave_attack_and_pass(session, ctx) is None:
            break
        phase = wait_card_path(session, ctx, t)
        if phase is None:
            break
        if phase == "candidate":
            candidates += 1
            perform(session, ctx, f"shot card-path-candidate-{t}")
            try:
                perform(session, ctx, f"click! {walks.CONTINUE_CLICK[0]} {walks.CONTINUE_CLICK[1]}")
            except StepFailed as exc:
                ctx.obs(session, "card path stop", f"turn {t}: measured CONTINUE was refused: {exc}")
                break
            ctx.obs(session, "cards note",
                    "walk stops after the first captured candidate and its measured CONTINUE",
                    "static")
            break
    ctx.count("card-path candidate screenshots", candidates)
    ctx.obs(session, "cards note",
            "the turn menu's CARD button has no measured point (F003), so the hand screen is not "
            "walked; candidate screenshots are taken only after the bounded green prompt probe and "
            "remain unidentified for the catalogue", "static")


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


def shot_hashes(session, names):
    """{screenshot name: sha256 of its raw pixels}, from the driver's own observation of each shot."""
    want = {f"{name} raw RGB8 pixels sha256": name for name in names}
    return {want[o["field"]]: o["value"] for o in session.obs if o.get("field") in want}


def measured_count(session, ctx):
    """The value of the spec's declared count target, from the walk's own counters: `shots`,
    `distinct shots` (distinct raw-pixel hashes among the walk's own shots), `attempts` and `labels`
    are the recorder's live counters; every other target is the counter a composite filled
    (`ctx.counts[measure]`). None when it cannot be produced."""
    declared = ctx.spec.get("count") or {}
    measure = declared.get("measure")
    if measure == "shots":
        return ctx.shots
    if measure == "distinct shots":
        return len(set(shot_hashes(session, ctx.shot_names).values()))
    if measure == "attempts":
        return ctx.attempts
    if measure == "labels":
        return len(ctx.labels)
    if measure:
        return ctx.counts.get(measure)
    return None


def stamp_walk_summaries(session, ctx):
    """The counts, the raw reads and the walk's observation, after the walk's actions.

    Everything stamped here is a measurement or a statement of what was measured (the class of
    round 1's R3/R4 and round 2's R3, R5 and R7): the declared count target is emitted under the
    word the recorder actually counts (`measured` when the row's word needs an identification the
    pixels cannot make, with a `count note` naming the substitution); the absence tour names the
    screenshots it took and nothing more; and the per-question `observation` is the summary of the
    walk's own measurements, with the reading left to the catalogue (F020)."""
    emitted = {word: value for word, value in ctx.counts.items() if word != "inputs"}
    declared = ctx.spec.get("count")
    if declared:
        field = declared.get("measured", declared["word"])
        value = measured_count(session, ctx)
        if value is not None:
            emitted[field] = value
        if field != declared["word"]:
            ctx.obs(session, f"count note: {declared['word']}",
                    f"the walk measures {field!r}, not {declared['word']!r}: the pixels cannot identify "
                    f"one; this is a proxy, never an identification", "static")
    for word, value in sorted(emitted.items()):
        ctx.obs(session, f"count: {word}", value)
    if ctx.spec.get("reads", {}).get("absence-tour"):
        ctx.obs(session, "read: absence-tour",
                json.dumps({"screenshots": list(ctx.shot_names), "count": ctx.shots}))
    if ctx.spec.get("reads", {}).get("ear-toggle"):
        ctx.obs(session, "read: ear-toggle",
                json.dumps({"clicked": list(walks.EAR_CLICK), "clicks": 2,
                            "screenshots": [n for n in ctx.shot_names if n.startswith("sound-")],
                            "audio": "off (the driver's engine runs with audio off; no sound is captured)"}))
    ctx.obs(session, "observation", json.dumps({
        "question": ctx.spec["qid"],
        "display size requested": ctx.size,
        "screenshots": list(ctx.shot_names),
        "counts": dict(sorted(emitted.items())),
        "reads": dict(sorted(ctx.reads.items())),
        "timing observations": ctx.timings,
        "reading": "none by the recorder: the catalogue (F020) reads the screenshots and values named here",
    }))


def walk_body(spec, ctx):
    """The session body of one walk: the known screens, the display size, before.png, the walk,
    after.png. The counts and notes are stamped after the walk's own shots, so their numbers include
    every screenshot."""
    def body(session):
        session.expect(*walks.expects_of(spec))
        session.known_screen()
        display_size_action(session, ctx)
        session.observe_screenshot("before.png")
        run_actions(session, spec, ctx)
        session.observe_screenshot("after.png")
        stamp_walk_summaries(session, ctx)
    return body


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


def write_records(session, spec, bundles, commit, machine, state_sha, binary_sha, argv, fingerprint, set_id, root=ROOT):
    """Store the bundle and write the manifest and the record, once each, under the batch's
    folders. RecordError says what was not written; a record is never overwritten and never names
    an output the store does not hold (the E004 writer's rule)."""
    batch = spec["batch"]
    root = Path(root)
    paths = {key: Path(rel) for key, rel in records.record_paths(batch, session.run_id).items()}
    taken = [str(rel) for rel in paths.values() if os.path.lexists(root / rel)]
    if taken:
        raise RecordError(f"no record written: {', '.join(taken)} already exist(s)")
    try:
        for rel in paths.values():
            os.close(safeio.open_directory(root / rel.parent, create_below=root))
    except (safeio.Refused, OSError) as exc:
        raise RecordError(f"no record written: {exc}") from None
    engine = session._engine
    engine._error = RecordError
    engine.outputs = spike.store_outputs(engine, bundles, lambda name, digest: f"{digest[:16]}-{name}", "same")
    manifest = records.build_manifest(session.run_id, engine.outputs, set_id)
    record = records.build_record(session.run_id, spec, argv, commit, machine, state_sha, binary_sha, fingerprint,
                                  engine.obs, engine.outputs, engine.started, engine.ended,
                                  engine.status, session.elapsed, set_id, root=root)
    try:
        safeio.write_file(root / paths["manifest"].parent, paths["manifest"].name,
                          data=(json.dumps(manifest, indent=2) + "\n").encode(), exist="new",
                          create_below=root)
        safeio.write_file(root / paths["run"].parent, paths["run"].name,
                          data=(json.dumps(record, indent=2) + "\n").encode(), exist="new",
                          create_below=root)
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


def run_walk(qid, size, locs, display, commit, machine, argv, fingerprint, root=ROOT, session_factory=Session):
    """One walk: one session, one record. (status, recovered)

    `root` is where the records go and `session_factory` makes the session (the driver's Session);
    the end-to-end test passes a temporary root and a fake session, so that the records it checks are
    the ones this function writes."""
    spec = dict(walks.WALKS[qid])
    spec["qid"] = qid
    run_id = next_run_id(root)
    set_id = records.artifact_set_for(spec)
    # T48 (#149, constraint C): the binary that ran, hashed from the install bound read-only for this
    # command, before the walk starts anything. It is start_state.sha256, and the wine gate verifies
    # it against F019's row. A binary that cannot be hashed means no launch and no record.
    try:
        binary_sha = records.binary_sha256(locs["IWP_DIR"])
    except OSError as exc:
        sys.exit(f"the walk was not started: the install's {records.BINARY} could not be hashed ({exc})")
    size = size or DEFAULT_SIZE
    session = session_factory(run_id, locs["IWP_PREFIX"], locs[f"{EXPERIMENT}_BUNDLES"], locs["IWP_DIR"],
                              display, records.arm_of_question(qid), size)
    ctx = Ctx(spec, size)
    session.observe(0, "static", "walk question", qid)
    session.observe(0, "static", "walk batch", spec["batch"])
    session.observe(0, "static", "speed setting",
                    "normal (the unlocked default; every timing is a wall-clock reading at it)")
    session.execute(walk_body(spec, ctx))
    # no snapshot (the session stopped before the seal): the prefix listing's hash is zeros, which
    # start_state.restore names, as the field itself did before T48 (#149). start_state.sha256 is
    # the binary's hash now — measured above, whatever the session did — and the catalogue's seal
    # check reads it: a walk that sealed and one that did not both name a measured binary.
    snap = getattr(session, "snap_before", None)
    state_sha = spike.start_state_sha(snap[1]) if snap else "0" * 64
    try:
        write_records(session, spec, locs[f"{EXPERIMENT}_BUNDLES"], commit, machine, state_sha, binary_sha,
                      argv, fingerprint, set_id, root=root)
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
