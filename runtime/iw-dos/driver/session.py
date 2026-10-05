"""One session of the DOS Isle Wars driver (T15, W5b): the seal, a display, DOSBox-X, named screens, steps in
T14's step language, observations, termination and reset, every failure a named error (errors.py).

    session = Session(run_id, run_dir, install, workdir, display, baseline, token, outer_netns)
    session.start()                          # the seal, this run's own Xvfb, snapshot, the seal again, launch
    session.wait_for_screen("option-box")    # by pixels, with a bound; ScreenNotReached, GameDied, DisplayDied
    session.observe_screenshot("before.png") # a screenshot by hash; observe_region(), observe_file() likewise
    session.perform("click 60 32")           # steps of navsteps.py (T14), each guarded
    session.complete()                       # what `completed` needs, checked
    session.finish()                         # terminate, stop the display, reset, keep the logs; never raises

or `session.execute(body)`: start, body(session), complete, finish, with one status. It is "completed" only when
the body ran, complete() found the known before-state reached and shot before any input, at least one input
whose command exited 0, `after.png` taken after the last input, and finish() then terminated DOSBox-X by its own
SIGTERM (exit status 0, F005), stopped its Xvfb, and reset the run copy to its baseline, every stage without a
fault. Any other way out is "aborted: <kind>: <reason>" (the first reason), and finish() runs in every case.
`recovered` is True only when every stage of finish() succeeded and the run copy equals the baseline again: the
next session may start only then.

Built by construction from T13's lessons (PR #54, its three reviews) and T15's round 1 (PR #74):
- `Session` holds the spike through a private adapter (`_Core`, a subclass of the spike's Cycle) and inherits
  nothing from it: its whole public surface is PUBLIC, each method wrapped by one guard (`_guarded`) that checks
  DOSBox-X and the display before and after it. In the adapter, every public name of the spike is either one the
  driver uses (CORE_USED) or replaced by a method that refuses (BLOCKED: the spike's own launch, terminate,
  hotkey, savestate and the rest), so no inherited path runs a command or sends a signal of its own;
- perform() checks DOSBox-X and the display before and after every step; every wait of the session (wait_until,
  which the spike's step verbs call) checks them on each poll, and has a bound;
- one helper runs every command (procs.must, through the adapter's sh(), which the spike's step verbs and screen
  call): a non-zero exit is a CommandFailed, never a silent "no". sh() sends an input (a pointer move, a click, a
  key) only while a step of perform() runs and DOSBox-X is alive, never a click on a forbidden control or while
  the shareware notices are up, and never a key outside navsteps.KEYS (R1);
- every signal goes through procs.kill_marked: the run's markers re-checked through a pidfd;
- the check immediately before the launch runs every check of the first (SEAL_CHECKS, both from seal()), and
  then that the display is held by this run's own Xvfb.
"""
import functools
import io
import os
import re
import signal
import subprocess
import time
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path

from driver import errors, procs
from driver.errors import (CommandFailed, DisplayDied, DisplayError, DriverError, GameDied, LaunchError,
                           ResetError, ScreenNotReached, SealError, StepFailed, TerminateError)

spike = errors.spike
rundir, dosconf, safeio, navsteps = spike.rundir, spike.dosconf, spike.safeio, spike.stepscript

GAME_SIZE = spike.GAME_SIZE
ROOT_SCREEN = spike.ROOT_SCREEN
# Named screens. F005: the option box at 16.92 to 17.07 s after the
# launch (fixed 3000), the Select level dialog after the click within 20 s (the spike's bound, kept).
# Each screen is its pixel tests (rectangle, colour, more than this many pixels: the spike's menu_up and dialog_up)
# and its bound in s; the same tests are applied to a capture's own pixels to check what it shows (R5).
SCREENS = {"option-box": (((spike.SET_LEVEL_TEXT, spike.RED, 150), (spike.CHOOSE_TEXT, spike.CYAN, 250)), 120),
           "select-level": (((spike.DIALOG_TITLE, spike.ORANGE, 800),), 20)}
STABLE_S = 30            # s, a named screen still after it appeared (the spike's bound)
WINDOW_S = 30            # s, DOSBox-X's 640x350 window after the launch (the spike's bound; F005: under 1 s)
XVFB_S = 20              # s, this run's Xvfb holding its display (the spike's bound for xdpyinfo)
TERM_S = 15              # s, DOSBox-X gone after SIGTERM (the spike's bound; F005: 0.05 s)
STOP_S = 10              # s, Xvfb gone after SIGTERM, and any process after SIGKILL
INPUT_COMMANDS = (("xdotool", "click"), ("xdotool", "key"))   # the commands that give the game an input
# Verbs of navsteps.py this driver refuses: `wait-exit` waits for DOSBox-X to end, which the session's guard
# reports as GameDied; `savestate` is I2, beyond this driver's I1 (a later task may add them).
REFUSED_VERBS = ("wait-exit", "savestate")
# Every check of the seal, run at the start and again immediately before the launch (seal()).
SEAL_CHECKS = ("install-read-only", "network-namespace", "run-copy", "baseline", "configuration", "no-dosbox-x")
# The public methods and their guard: the state DOSBox-X and the display must be in before and after the method.
# "live": both alive, the display held by this run's Xvfb; "none": nothing started yet; "any": not checked;
# "gone": no process of this run alive.
PUBLIC = {
    "on": ("none", "none"),
    "execute": ("none", "any"),
    "start": ("none", "live"),
    "expect": ("live", "live"),
    "checkpoint": ("live", "any"),
    "wait_for_screen": ("live", "live"),
    "perform": ("live", "live"),
    "observe_screenshot": ("live", "live"),
    "observe_region": ("live", "live"),
    "observe_file": ("live", "live"),
    "complete": ("live", "live"),
    "finish": ("any", "gone"),
    "store_outputs": ("gone", "gone"),
}
# The adapter's public names: those the driver uses (CORE_USED) and the spike's that it must never run (BLOCKED,
# each replaced by a method that raises). A structural test requires every public callable of _Core, its MRO
# included, to be in exactly one of them.
CORE_USED = ("say", "observe", "fail", "abort_later", "command", "write_conf", "window_geometry", "verify_isolation",
             "since_launch", "shot", "record_written", "take_snapshot", "report_changes", "sanitise", "keep_logs", "sh",
             "wait_until", "items", "require", "game_alive", "start", "wait_for_screen", "perform",
             "observe_screenshot", "observe_region", "observe_file", "complete", "finish",
             "step_click", "step_rclick", "step_click_change", "step_rclick_change", "step_click_until",
             "step_wait_stable", "step_wait_change", "step_until", "step_choose_attack", "step_click_mine",
             "step_rclick_mine", "step_click_target", "step_rclick_target", "step_shot", "step_files", "step_key")
BLOCKED = ("protect_install", "check_launch", "check_seal_only", "start_x", "launch", "known_screen", "hotkey", "input",
           "load_script", "navigate", "step_wait_exit", "step_savestate", "save_state", "probe_at_known_screen",
           "probe_after_input", "terminate", "stop_x", "reset", "snapshot_and_reset", "cleanup", "execute")
MOVES, CLICKS, KEYS = ("xdotool", "mousemove"), ("xdotool", "click"), ("xdotool", "key")


def _guarded(name, before, after, method):
    @functools.wraps(method)
    def wrapper(self, *args, **kw):
        core = self._core
        core.require(before, f"before {name}")
        try:
            result = method(self, *args, **kw)
        except DriverError as exc:
            # a failure while DOSBox-X or the display died is that death, whatever the wait that saw it says
            if not isinstance(exc, (GameDied, DisplayDied)) and before == "live" and core._dead():
                raise core._dead() from exc
            raise
        core.require(after, f"after {name}")
        return result
    wrapper.guard = (before, after)
    return wrapper


def shows(screen, data, rect=None):
    """True when the pixels `data` (the game window, or `rect` of it) pass every pixel test of the named screen."""
    rx, ry, rw, _ = rect or (0, 0) + GAME_SIZE
    for (x, y, w, h), colour, least in SCREENS[screen][0]:
        found = 0
        for row in range(y - ry, y - ry + h):
            line = data[(row * rw + x - rx) * 3:(row * rw + x - rx + w) * 3]
            found += sum(1 for i in range(0, len(line) - 2, 3) if tuple(line[i:i + 3]) == colour)
        if found <= least:
            return False
    return True


class CheckedScreen(spike.Screen):
    """The spike's screen, its capture sent through the adapter's sh() and its size checked."""

    def __init__(self, session):
        super().__init__(session.env)
        self.session = session

    def sh(self, cmd):
        return self.session.sh(cmd)

    def raw(self, crop=None):
        data = super().raw(crop)
        w, h = (crop[2], crop[3]) if crop else GAME_SIZE
        if len(data) != w * h * 3:
            raise CommandFailed(f"a capture of {w}x{h} gave {len(data)} bytes, not {w * h * 3}")
        return data


class _Core(spike.Cycle):
    """The private adapter: the spike's Cycle with the driver's checked hooks; only Session uses it."""

    def __init__(self, run_id, run_dir, install, workdir, display, baseline, token, outer_netns, arm="control"):
        args = Namespace(arm=arm, cycles="fixed-3000", clock="fixed", probe="none", terminate="term", steps=None,
                         experiment="E006", explore=False)
        super().__init__(args, run_id, run_dir, install, workdir, outer_netns)
        if not token or not display:
            raise ValueError("a session needs its command's token and a display")
        self.env.pop(spike.MARK, None)               # the spike's marker is for its own runs (T16 runs one beside)
        self.env.update({"DISPLAY": display, procs.INVOCATION: token, procs.MARK: run_id})
        self.display, self.token, self.baseline = display, token, baseline
        self.screen = CheckedScreen(self)
        self._kind = SealError
        self.inputs_sent = 0
        self.reached, self.shot_states, self.frames = {}, {}, {}
        self.current_screen = None       # the named screen reached and not left by an input since
        self.in_step = False             # inputs are sent only while a step of perform() runs
        self.live_commands = False       # after the launch, every command needs DOSBox-X and the display alive
        self.pointer_at = None           # the game-window point of the last pointer move
        self.expected = set()
        self.body_ok = self.reset_ok = self.recovered = False
        self.step_no = 0
        self.started = self.ended = None
        self.elapsed = None

    # ---- markers and sides

    def items(self, side=None):
        found = [procs.item(procs.INVOCATION, self.token), procs.item(procs.MARK, self.run_id)]
        return found + ([procs.item(procs.SIDE, side)] if side else [])

    def _side_env(self, side):
        return dict(self.env, **{procs.SIDE: side})

    def _socket_name(self):
        return f"@/tmp/.X11-unix/X{self.display.lstrip(':')}"

    def _display_is_ours(self):
        """This run's Xvfb is alive and holds every listening socket of its display (none is another server's)."""
        xvfb = self.procs.get("xvfb")
        if xvfb is None or xvfb.poll() is not None:
            return False
        listening = procs.listening_socket_inodes(self._socket_name())
        return bool(listening) and listening <= procs.socket_inodes_of(xvfb.pid)

    # ---- the guard

    def _dead(self):
        """GameDied or DisplayDied when DOSBox-X or the display is gone (or never started), else None."""
        game = self.procs.get("game")
        if game is None:
            return GameDied("DOSBox-X was not started")
        code = game.poll()
        if code is not None:
            return GameDied(f"DOSBox-X was gone (exit status {code})")
        if not self._display_is_ours():
            return DisplayDied(f"the display {self.display} was not held by this run's Xvfb")
        return None

    def require(self, state, when):
        if state == "live":
            problem = self._dead()
            if problem:
                raise type(problem)(f"{problem} {when}")
        elif state == "none":
            if self.procs:
                raise SealError(f"a session starts once; it has started {', '.join(sorted(self.procs))} ({when})")
        elif state == "gone":
            left = procs.marked_pids(self.items())
            if left:
                raise TerminateError(f"{len(left)} process(es) of this run alive {when}")
        elif state != "any":
            raise ValueError(f"unknown guard state {state!r}")

    # ---- the hooks the spike's code calls

    def sh(self, cmd):
        """Every command of the session: procs.must, so a non-zero exit is a CommandFailed. After the launch every
        command needs DOSBox-X and the display alive. An input goes through _gate_input first; a click or a key that
        exited 0 counts as an input sent, and leaves the named screen it was sent on."""
        key = tuple(cmd[:2])
        if self.live_commands:
            self.require("live", f"before {' '.join(cmd[:2])}")
        if cmd[:1] == ["xdotool"] and key not in (MOVES, CLICKS, KEYS):
            raise StepFailed(f"xdotool {cmd[1] if len(cmd) > 1 else ''} is not a command the steps send")
        if key in (MOVES, CLICKS, KEYS):
            self._gate_input(cmd)
        done = procs.must(cmd, env=self.env)
        if key == MOVES:
            self.pointer_at = (int(cmd[2]) - self.screen.ox, int(cmd[3]) - self.screen.oy)
        if key in INPUT_COMMANDS:
            self.inputs_sent += 1
            self.current_screen = None
        return done

    def _gate_input(self, cmd):
        """Refuse an input outside a step of perform(), to a dead DOSBox-X, a click off the window, on a forbidden
        control (navsteps.FORBIDDEN) or while the shareware notices are up, and a key outside navsteps.KEYS, or
        other than c and e while the notices are up (T14's notice guard, again at the dispatch itself)."""
        if not self.in_step:
            raise StepFailed(f"an input ({' '.join(cmd[:2])}) is sent only by a step of perform()")
        self.require("live", f"before {' '.join(cmd[:2])}")
        key = tuple(cmd[:2])
        if key == MOVES:
            if len(cmd) != 4:
                raise StepFailed("a pointer move takes x and y only")
            return
        if key == CLICKS:
            if len(cmd) != 3 or cmd[2] not in ("1", "3"):
                raise StepFailed(f"a click takes button 1 or 3 only: {cmd[2:]}")
            point = self.pointer_at
            if point is None or not (0 <= point[0] < GAME_SIZE[0] and 0 <= point[1] < GAME_SIZE[1]):
                raise StepFailed(f"a click with the pointer off the game window ({point}) is never sent")
            if navsteps.forbidden(*point):
                raise StepFailed(f"a click at {point[0]},{point[1]} is on the shareware notices' buttons; never sent")
            if self.screen.notice_up():
                raise StepFailed("the shareware notices are on the screen; no click is sent there")
            return
        if len(cmd) != 3 or cmd[2] not in navsteps.KEYS:
            raise StepFailed(f"the key {cmd[2:]} is not one of navsteps.KEYS; never sent")
        if cmd[2] not in spike.NOTICE_KEYS and self.screen.notice_up():
            raise StepFailed(f"the shareware notices are on the screen; only {', '.join(spike.NOTICE_KEYS)} is pressed there")

    def wait_until(self, condition, timeout, interval=0.1):
        """Seconds until condition() is true, or None after `timeout` s; DOSBox-X and the display are checked on
        every poll, so a wait never outlasts them (GameDied, DisplayDied)."""
        start = time.monotonic()
        while True:
            self.require("live", "during a wait")
            if condition():
                return round(time.monotonic() - start, 2)
            if time.monotonic() - start > timeout:
                return None
            time.sleep(interval)

    def fail(self, reason):
        raise self._kind(reason)

    def abort_later(self, reason):
        self._note(DriverError(reason))

    def window_geometry(self):
        """(window id, (x, y)) of DOSBox-X's window once it is the game's size, else None. A search that finds no
        window exits 1 with no output (procs.must miss_ok); any other failure is a CommandFailed."""
        found = procs.must(["xdotool", "search", "--class", "dosbox"], env=self.env, miss_ok=True)
        for wid in (found.stdout.split() if found else []):
            text = procs.must(["xdotool", "getwindowgeometry", wid], env=self.env).stdout.decode()
            pos = re.search(r"Position: (-?\d+),(-?\d+)", text)
            size = re.search(r"Geometry: (\d+)x(\d+)", text)
            if pos and size and (int(size.group(1)), int(size.group(2))) == GAME_SIZE:
                return wid.decode(), (int(pos.group(1)), int(pos.group(2)))
        return None

    def shot(self, name, step):
        """The spike's shot, keeping the captured pixels too (for complete(): what a capture shows)."""
        t0 = time.monotonic()
        pixels, png, data = self.screen.capture(self.workdir, name)
        self.outputs.append((name, self.workdir / name, "screenshot"))
        self.observe(step, "screen", f"{name} raw RGB8 pixels sha256", pixels)
        self.observe(step, "screen", f"{name} capture and PNG (s)", round(time.monotonic() - t0, 3))
        self.say(f"{name}: pixels {pixels[:16]}, file {png[:16]}")
        self.shots[name], self.frames[name] = pixels, data
        return pixels

    # ---- status

    def _note(self, exc):
        """The first failure sets the status; every one is said and observed."""
        kind = getattr(exc, "kind", "driver-bug")
        reason = str(exc) if isinstance(exc, DriverError) else f"{type(exc).__name__}: {exc}"
        if self.status == "running":
            self.status = f"aborted: {kind}: {reason}"
        self.observe(self.step_no + 100, "process", "fault", f"{kind}: {reason}"[:300])
        self.say(f"ABORT {kind}: {reason}")

    # ---- the seal

    def _seal(self, when, step):
        """Every check of SEAL_CHECKS, in order; SealError naming the first that fails."""
        for name in SEAL_CHECKS:
            problem = getattr(self, "_seal_" + name.replace("-", "_"))()
            self.observe(step, "file", f"seal {when}: {name}", "ok" if not problem else problem[:300])
            if problem:
                raise SealError(f"{name} ({when}): {problem}"[:400])
        self.say(f"seal {when}: ok")

    def _seal_install_read_only(self):
        return "IW_DOS_DIR is writable here" if spike.install_writable(self.install) else None

    def _seal_network_namespace(self):
        try:
            mine, seen = spike.netns_of("self"), spike.interfaces_of("self")
        except OSError as exc:
            return f"the network namespace could not be read: {type(exc).__name__}"
        if not self.outer_netns or mine == self.outer_netns:
            return "this process shares the outer process's network namespace, or it is unknown"
        if seen != ["lo"]:
            return f"network interfaces besides lo: {seen}"
        return None

    def _seal_run_copy(self):
        problems = rundir.run_problems(self.run_dir, self.install)
        return "; ".join(problems) if problems else None

    def _seal_baseline(self):
        now_ = spike.snapshot_tree(self.game)
        if now_ == self.baseline:
            return None
        added, removed, changed = spike.diff_tree(self.baseline, now_)
        return f"the run copy is off its baseline: {len(added)} added, {len(removed)} removed, {len(changed)} changed"

    def _seal_configuration(self):
        try:
            with safeio.open_source(self.workdir / "dosbox.conf") as fh:
                text = fh.read().decode("utf-8")
        except (OSError, safeio.Refused, UnicodeDecodeError) as exc:
            return f"the configuration cannot be read: {exc}"
        problems = dosconf.problems(text, self.game, self.workdir, self.command())
        return "; ".join(problems) if problems else None

    def _seal_no_dosbox_x(self):
        running = procs.program_pids("dosbox-x")
        return f"DOSBox-X is already running: {running}" if running else None

    # ---- the stages Session's API calls (Session guards each)

    def start(self):
        """The seal, this run's Xvfb, the snapshot, the seal again with the display check, the launch."""
        self.t_start = time.monotonic()
        self._kind = SealError
        self.write_conf()
        self._seal("at the start", 0)
        self._kind = DisplayError
        self._start_display()
        self.take_snapshot("before")
        self._kind = SealError
        self._seal("immediately before launch", 1)
        if not self._display_is_ours():
            raise SealError("the display is not held by this run's Xvfb (immediately before launch)")
        self.observe(1, "process", "seal immediately before launch: display held by this run's Xvfb", "ok")
        self._kind = LaunchError
        self._launch()

    def wait_for_screen(self, name):
        """Wait, by its pixels and within its bound, for a named screen (SCREENS), then until it is still."""
        if name not in SCREENS:
            raise StepFailed(f"no screen is called {name!r}")
        self._kind = ScreenNotReached
        bound = SCREENS[name][1]
        waited = self.wait_until(lambda: self._screen_up(name), bound, 0.25)
        if waited is None:
            self.shot(f"{name}-timeout.png", 2)
            raise ScreenNotReached(f"{name} did not appear within {bound} s")
        if self.wait_until(self.screen.stable, STABLE_S, 0.1) is None:
            raise ScreenNotReached(f"{name} was not still within {STABLE_S} s")
        self.reached.setdefault(name, self.inputs_sent)
        self.current_screen = name
        self.observe(2, "screen", f"{name} reached and stable, seconds after launch", self.since_launch())
        self.say(f"{name} reached {self.since_launch()} s after launch")

    def _screen_up(self, name):
        rects = [rect for rect, _, _ in SCREENS[name][0]]
        x0, y0 = min(r[0] for r in rects), min(r[1] for r in rects)
        x1, y1 = max(r[0] + r[2] for r in rects), max(r[1] + r[3] for r in rects)
        box = (x0, y0, x1 - x0, y1 - y0)
        return shows(name, self.screen.raw(box), box)

    def perform(self, text):
        """Run steps of T14's step language (navsteps.py), each checked before and after (DOSBox-X, the display);
        a line the grammar refuses, or a REFUSED_VERBS verb, is refused before any step runs."""
        self._kind = StepFailed
        try:
            steps = navsteps.parse(text)
        except navsteps.Refused as exc:
            raise StepFailed(f"the steps are refused: {exc}") from None
        refused = [verb for verb, _ in steps if verb in REFUSED_VERBS]
        if refused or not steps:
            raise StepFailed(f"the steps are refused: {', '.join(refused) or 'no step'}")
        for verb, args in steps:
            self.step_no += 1
            n = self.step_no
            self.require("live", f"before step {n}")
            self.say(f"step {n}: {verb} {' '.join(map(str, args))}".rstrip())
            self.in_step = True
            try:
                getattr(self, "step_" + verb.replace("-", "_"))(100 + n, *args)
            finally:
                self.in_step = False
            self.require("live", f"after step {n}")
            self.observe(100 + n, "process", "step done, seconds after launch", self.since_launch())

    def observe_screenshot(self, name):
        """A screenshot of the game window, kept as an output and observed by its pixels' sha256."""
        self._kind = StepFailed
        pixels = self.shot(name, 3 if not self.inputs_sent else 6)
        screen = self.current_screen
        self.shot_states[name] = (self.inputs_sent, screen, screen is not None and shows(screen, self.frames[name]))
        self.observe(3 if not self.inputs_sent else 6, "screen", f"{name} shows the screen reached",
                     screen if self.shot_states[name][2] else "no")
        return pixels

    def observe_region(self, label, rect):
        """The sha256 of the raw pixels of a rectangle (x, y, w, h) of the game window, observed."""
        self._kind = StepFailed
        digest = spike.sha256_bytes(self.screen.raw(tuple(rect)))
        self.observe(self.step_no + 100, "screen", f"region {label} {tuple(rect)} raw RGB8 pixels sha256", digest)
        return digest

    def observe_file(self, name):
        """Size and sha256 of a file of the run copy (one the game wrote), observed; its bytes are not kept."""
        self._kind = StepFailed
        safeio.safe_name(name, "file name")
        path = self.game / name
        if not os.path.lexists(path):
            value = "absent"
        else:
            with safeio.open_source(path) as fh:
                data = fh.read()
            value = f"{len(data)} {spike.sha256_bytes(data)}"
        self.observe(self.step_no + 100, "file", f"run copy file {name}: bytes, sha256", value)
        return value

    def complete(self):
        """What `completed` needs from the body; StepFailed naming what is missing. finish() decides the status."""
        before = self.shot_states.get("before.png", (None, None, False))
        after = self.shot_states.get("after.png", (None, None, False))
        missing = []
        if before[0] != 0 or before[1] is None:
            missing.append("before.png at a known screen before any input")
        elif not before[2]:
            missing.append(f"before.png showing {before[1]}")
        if self.inputs_sent < 1:
            missing.append("an input whose command succeeded")
        if after[0] is None or after[0] != self.inputs_sent or after[0] < 1 or after[1] is None:
            missing.append("after.png at a known screen after the last input")
        elif not after[2]:
            missing.append(f"after.png showing {after[1]}")
        missing += [f"the screen {name}" for name in sorted(self.expected - set(self.reached))]
        if missing:
            raise StepFailed("the session did not show " + "; ".join(missing))
        self.body_ok = True

    def finish(self):
        """Terminate DOSBox-X, stop the display, snapshot, reset and keep the logs: every stage runs, whatever
        happened before; a fault in one is noted and the others still run. Then the status."""
        self.live_commands = False
        stages = (("terminate", self._terminate), ("stopping the display", self._stop_display),
                  ("snapshot and reset", self._snapshot_and_reset), ("keeping the logs", self.keep_logs))
        clean = True
        for label, action in stages:
            try:
                action()
            except BaseException as exc:      # noqa: BLE001  (every stage runs; the fault is noted)
                clean = False
                if not isinstance(exc, DriverError):
                    exc = DriverError(f"{label} failed: {type(exc).__name__}: {exc}")
                self._note(exc)
        self.recovered = clean and self.reset_ok
        if self.status == "running":
            if self.body_ok and self.recovered:
                self.status = "completed"
            else:
                self.status = "aborted: driver-bug: finish() came before complete()"
        self.elapsed = round(time.monotonic() - getattr(self, "t_start", time.monotonic()), 2)
        self.observe(12, "process", "repeat seconds, start to end of finish", self.elapsed)

    # ---- the stages behind them

    def _start_display(self):
        if procs.listening_socket_inodes(self._socket_name()):
            raise DisplayError(f"the display {self.display} is already held by another server")
        Path("/tmp/.X11-unix").mkdir(mode=0o1777, exist_ok=True)
        self.procs["xvfb"] = procs.start(["Xvfb", self.display, "-screen", "0", ROOT_SCREEN, "-nolisten", "tcp"],
                                         self._side_env("display"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        waited = spike.poll(lambda: self._display_is_ours() or self.procs["xvfb"].poll() is not None, XVFB_S, 0.05)
        if waited is None or not self._display_is_ours():
            raise DisplayError(f"this run's Xvfb did not hold {self.display} within {XVFB_S} s")
        procs.must(["xdpyinfo"], env=self.env)
        self.observe(0, "process", "xvfb ready, display held by this run's Xvfb (s)", waited)
        self.say(f"Xvfb {self.display} ready after {waited} s")

    def _launch(self):
        cmd = self.command()
        self.t_launch = time.monotonic()
        with safeio.create_stream(self.workdir, "dosbox.raw.log") as log:
            self.procs["game"] = procs.start(cmd, self._side_env("game"), cwd=self.workdir, stdout=log, stderr=log)
        self.say("launched: " + " ".join(cmd))
        self.verify_isolation()
        waited = self.wait_until(lambda: self.window_geometry() is not None, WINDOW_S)
        if waited is None:
            raise LaunchError(f"no {GAME_SIZE[0]}x{GAME_SIZE[1]} DOSBox-X window within {WINDOW_S} s")
        self.window, pos = self.window_geometry()
        self.screen.ox, self.screen.oy = pos
        self.observe(1, "process", "DOSBox-X window at 640x350, seconds after launch", self.since_launch())
        self.observe(1, "process", "DOSBox-X window position", f"{pos[0]},{pos[1]}")
        self.live_commands = True

    def _terminate(self):
        """SIGTERM through kill_marked, a bounded wait, and exit status 0 required (F005: SIGTERM with quit
        warning=false gives 0; SIGKILL gives -9 and a closed X client 1). DOSBox-X found gone at this point, or
        ended with another status, is a GameDied when the body had completed: something else ended it."""
        game = self.procs.get("game")
        if game is None:
            return
        code = game.poll()
        if code is not None:
            self.observe(9, "process", "DOSBox-X already gone at terminate, exit status", code)
            if self.body_ok:
                raise GameDied(f"DOSBox-X was gone before terminate (exit status {code})")
            return
        sent = procs.kill_marked(game.pid, self.items("game"), signal.SIGTERM)
        waited = spike.poll(lambda: game.poll() is not None, TERM_S, 0.05)
        if waited is None:
            procs.kill_marked(game.pid, self.items("game"), signal.SIGKILL)
            try:
                game.wait(STOP_S)
            except subprocess.TimeoutExpired:
                pass
            raise TerminateError(f"DOSBox-X did not stop within {TERM_S} s of SIGTERM")
        code = game.returncode
        self.observe(9, "process", "DOSBox-X exit after SIGTERM (s); exit status", f"{waited}; {code}")
        self.say(f"DOSBox-X exit status {code}, {waited} s after SIGTERM")
        if not sent:
            raise GameDied(f"DOSBox-X no longer carried this run's markers at SIGTERM (exit status {code})")
        if code != 0:
            raise GameDied(f"DOSBox-X ended with exit status {code}, not 0 as after this driver's SIGTERM")

    def _stop_display(self):
        xvfb = self.procs.get("xvfb")
        if xvfb is None:
            return
        held = self._display_is_ours()
        if xvfb.poll() is None:
            procs.kill_marked(xvfb.pid, self.items("display"), signal.SIGTERM)
            if spike.poll(lambda: xvfb.poll() is not None, STOP_S, 0.05) is None:
                procs.kill_marked(xvfb.pid, self.items("display"), signal.SIGKILL)
                try:
                    xvfb.wait(STOP_S)
                except subprocess.TimeoutExpired:
                    raise TerminateError(f"Xvfb did not stop within {STOP_S} s of SIGKILL") from None
        left = procs.marked_pids(self.items())
        for pid in left:
            procs.kill_marked(pid, self.items(), signal.SIGKILL)
        self.observe(10, "process", "processes of this run still alive after terminate", len(left))
        if left:
            raise TerminateError(f"{len(left)} process(es) of this run survived terminate")
        if not held and self.body_ok:
            raise DisplayDied(f"the display {self.display} was not held by this run's Xvfb at its stop")

    def _snapshot_and_reset(self):
        """Put the run copy back to the registered set (rundir.sync), then require it equal to the baseline."""
        if hasattr(self, "snap_before"):
            self.take_snapshot("after")
            self.report_changes()
        env = {"IW_DOS_DIR": str(self.install), "IW_DOS_RUN": str(self.run_dir)}
        try:
            with redirect_stdout(io.StringIO()) as out:
                rundir.sync(env)
        except SystemExit as exc:
            raise ResetError(f"the run copy could not be synchronised: {exc}") from None
        self.say("reset: " + out.getvalue().strip())
        restored = spike.snapshot_tree(self.game)
        ok = restored == self.baseline
        self.observe(11, "file", "run copy after reset equals the baseline", "yes" if ok else "no")
        if not ok:
            raise ResetError("the reset did not restore the run copy to its baseline")
        self.reset_ok = True


def _refuse(name):
    def refused(self, *args, **kw):
        raise DriverError(f"the spike's {name}() is not on the driver's path (session.BLOCKED)")
    refused.blocked = True
    return refused


for _name in BLOCKED:
    setattr(_Core, _name, _refuse(_name))


class Session:
    """The driver's API: PUBLIC and nothing else callable, each method guarded. The spike is held, not inherited."""

    def __init__(self, run_id, run_dir, install, workdir, display, baseline, token, outer_netns, arm="control",
                 notes=()):
        self._core = _Core(run_id, run_dir, install, workdir, display, baseline, token, outer_netns, arm)
        self._hooks = {}
        for field, value in notes:
            self._core.observe(0, "static", field, value)

    # ---- read-only state, for the record
    run_id = property(lambda self: self._core.run_id)
    arm = property(lambda self: self._core.args.arm)
    status = property(lambda self: self._core.status)
    recovered = property(lambda self: self._core.recovered)
    elapsed = property(lambda self: self._core.elapsed)
    started = property(lambda self: self._core.started)
    ended = property(lambda self: self._core.ended)
    observations = property(lambda self: list(self._core.obs))
    outputs = property(lambda self: list(self._core.outputs))
    start_state_sha256 = property(lambda self: spike.listing_hash(self._core.baseline))

    # ---- the API (each wrapped by _guarded from PUBLIC, below the class)

    def on(self, checkpoint, action):
        """Before start: run `action(adapter)` at `checkpoint` (a fault of the command; the session does not know)."""
        self._hooks[checkpoint] = action

    def checkpoint(self, name):
        action = self._hooks.get(name)
        if action is not None:
            self._core.observe(self._core.step_no + 100, "process", "fault injected at", name)
            action(self._core)

    def start(self):
        self._core.start()

    def expect(self, *names):
        """The named screens the body must reach for `completed`."""
        unknown = [n for n in names if n not in SCREENS]
        if unknown:
            raise StepFailed(f"no screen is called {unknown}")
        self._core.expected.update(names)

    def wait_for_screen(self, name):
        self._core.wait_for_screen(name)

    def perform(self, text):
        self._core.perform(text)

    def observe_screenshot(self, name):
        return self._core.observe_screenshot(name)

    def observe_region(self, label, rect):
        return self._core.observe_region(label, rect)

    def observe_file(self, name):
        return self._core.observe_file(name)

    def complete(self):
        self._core.complete()

    def finish(self):
        self._core.finish()

    def store_outputs(self, bundles):
        """Copy the outputs into the bundle store (spike.store_outputs); an output not stored aborts the repeat."""
        core = self._core
        core.outputs = spike.store_outputs(core, bundles, lambda name, digest: f"{digest[:16]}-{name}", "same")

    def execute(self, body):
        """start, body(session), complete and finish, with one status; finish runs whatever happened."""
        core = self._core
        core.started = spike.now()
        try:
            self.start()
            body(self)
            self.complete()
        except BaseException as exc:          # noqa: BLE001  (the status says why; finish() still runs)
            core._note(exc)
        try:
            self.finish()
        except BaseException as exc:          # noqa: BLE001  (finish's guard: a process of the run alive after it)
            core.recovered = False
            if core.status == "completed":
                core.status = "running"
            core._note(exc)
        core.ended = spike.now()


for _name, (_before, _after) in PUBLIC.items():
    setattr(Session, _name, _guarded(_name, _before, _after, getattr(Session, _name)))
