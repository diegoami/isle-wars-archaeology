"""One session of the Isle Wars Pro driver (W5a): the seal, a display, the game, known screens, steps,
observations, termination and reset, with every failure a named error (errors.py).

A session is one launch of the game. It is built on the W3a/W4a spike (runtime/iwp/spike/cycle.py), whose
code does the seal, the screens, the step language and the reset; this module adds what a driver needs on top:

    session = Session(run_id, prefix, bundles, install, display=free_display())
    session.start()                       # install read-only?, prefix sealed, display, snapshot, sealed again, launch
    session.wait_for_screen("title")      # by pixels, never a fixed wait; raises ScreenNotReached or GameDied
    session.perform("click! 320 585")     # steps in the E002 step language (steps.py)
    session.observe_screenshot("a.png")   # a screenshot by hash; observe_region(), observe_file() likewise
    session.finish()                      # terminate, stop the display, snapshot, reset, keep the logs

or `session.execute(body)`, which is start, `body(session)`, complete and finish with one status. The
status is "completed" only from complete(), after the body, and only when the known screens the body
expects were reached, both screenshots exist and the game was alive at the end; every other way out is
"aborted: <kind>: <reason>", and the clean-up stages and the reset run in both cases.

What the driver keeps from T08 on every launch: the install bound read-only (checked at the start of
every session), the prefix sealed before anything starts and again immediately before the game starts,
the game in a network namespace of its own, and every file written through setup/iwp/safeio.py.

What it changes against the spike (measured in F006):
* a process is told apart by the marker `IWP_CYCLE_RUN=<run id>` and by a side, `IWP_CYCLE_SIDE=game` for
  the game and `display` for Xvfb, the window manager and the daemons the window manager starts. Terminate
  waits, with a bound, for the game side only: the spike waited 30 s for the display side's D-Bus daemons
  (dbus-daemon, at-spi, xfconfd), which only end when the display does (#40);
* the children get no DBUS_SESSION_BUS_ADDRESS (a stale one kept xfwm4 from registering, #40) and no TMPDIR, so
  that Wine uses the private /tmp of the namespace. Observed, not explained (F006): with TMPDIR naming a folder that
  is not in the private /tmp Wine stops at once ("unable to create wineserver tmpdir"), and with TMPDIR=/tmp
  itself it aborted ("free(): invalid pointer"); with TMPDIR unset every launch worked.
"""
import argparse
import contextlib
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for _sub in ("setup/iwp", "runtime/iwp/spike"):
    sys.path.insert(0, str(ROOT / _sub))
import cycle as spike  # noqa: E402  (the W3a/W4a spike, reused, not copied)
import locations  # noqa: E402,F401
import safeio  # noqa: E402
import steps as stepslib  # noqa: E402

from . import errors  # noqa: E402
from .errors import (DriverError, DisplayError, GameDied, LaunchError, ResetError, RecordError,  # noqa: E402
                     ScreenNotReached, SealError, StepFailed, TerminateError)

EXPERIMENT = "E004"
MARK = spike.MARK                      # IWP_CYCLE_RUN
SIDE = "IWP_CYCLE_SIDE"
SIDES = ("game", "display")
SCREENS = {"title": "title_up", "options": "options_up", "notice": "notice_up"}
TITLE_TIMEOUT = 45                     # s, the title screen after launch (F002: 6.6 to 6.7 s)
WAIT_GONE_TIMEOUT = 10                 # s, the game side after `wineserver -k` (F002: 2.1 s; the bound is slack)
DISPLAY_GONE_TIMEOUT = 5               # s, the display side after Xvfb and xfwm4 were stopped
AFTER_KILL_TIMEOUT = 5                 # s, after a second `wineserver -k` and SIGKILL, before TerminateError
FIRST_DISPLAY, LAST_DISPLAY = 77, 120


def now():
    return spike.now()


# --- processes of a run ----------------------------------------------------------------------

def run_processes(run_id, side=None):
    """pids of the processes of this run, read from /proc: their environment holds exactly
    IWP_CYCLE_RUN=<run_id> (and, with a side, IWP_CYCLE_SIDE=<side>). Never another run's, never this process.

    Another session's processes are never found: a run id is required, and the marker is compared whole."""
    if not run_id:
        raise ValueError("run_processes needs a run id; it never looks at every marked process")
    want = [f"{MARK}={run_id}".encode()]
    if side is not None:
        if side not in SIDES:
            raise ValueError(f"side {side!r} is not one of {SIDES}")
        want.append(f"{SIDE}={side}".encode())
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            env = (entry / "environ").read_bytes().split(b"\0")
        except OSError:
            continue
        if all(item in env for item in want) and spike.Cycle.is_alive(int(entry.name)):
            found.append(int(entry.name))
    return found


def marked_run_ids(value_prefix):
    """{pid: run id} of the processes whose IWP_CYCLE_RUN starts with value_prefix (this experiment's runs),
    read from /proc. Used by the outer process to find what survived a whole command."""
    found = {}
    needle = f"{MARK}=".encode()
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            env = (entry / "environ").read_bytes().split(b"\0")
        except OSError:
            continue
        for item in env:
            if item.startswith(needle) and item[len(needle):].decode(errors="replace").startswith(value_prefix):
                found[int(entry.name)] = item[len(needle):].decode(errors="replace")
    return found


def free_display(first=FIRST_DISPLAY, last=LAST_DISPLAY):
    """The first display number in [first, last] that no X server of this machine listens on.

    Another project's Xvfb on :99, :453 and so on holds an abstract socket in the host's network namespace,
    which this run shares (only the game has a namespace of its own), so a number in use there would clash."""
    taken = set()
    for line in Path("/proc/net/unix").read_text(errors="replace").splitlines()[1:]:
        match = re.search(r"@?/tmp/\.X11-unix/X(\d+)\s*$", line)
        if match:
            taken.add(int(match.group(1)))
    for directory in (Path("/tmp/.X11-unix"),):
        if directory.is_dir():
            taken.update(int(m.group(1)) for p in directory.iterdir() if (m := re.fullmatch(r"X(\d+)", p.name)))
    for number in range(first, last + 1):
        if number not in taken and not Path(f"/tmp/.X{number}-lock").exists():
            return f":{number}"
    raise DisplayError(f"no free X display between :{first} and :{last}")


def bind_install_readonly(install):
    """Bind the install read-only in this mount namespace, once per command; SealError unless it then is
    read-only here. Every session checks it again (Session.require_install_readonly)."""
    install = str(install)
    bind = spike.run(["mount", "--bind", install, install])
    remount = spike.run(["mount", "-o", "remount,bind,ro", install])
    if bind.returncode != 0 or remount.returncode != 0 or spike.install_writable(install):
        raise SealError("the install could not be made read-only inside the run")


# --- the session -----------------------------------------------------------------------------

class Session(spike.Cycle):
    """One launch of the game, from a sealed prefix to a reset one. See the module text."""

    def __init__(self, run_id, prefix, bundles, install, display, arm="control", size="800x600x24"):
        args = argparse.Namespace(size=size, audio="off", wm="xfwm4", click="hover", terminate="kill", script=None,
                                  session=False, input="options", arm=arm, experiment=EXPERIMENT,
                                  may_write_saved_files=False, explore=False)
        super().__init__(args, run_id, prefix, bundles, install)
        self.env["DISPLAY"] = display
        self.env.pop("TMPDIR", None)                 # the default, the namespace's private /tmp (see the module text)
        self.dbus_before = os.environ.get("DBUS_SESSION_BUS_ADDRESS")
        self.env.pop("DBUS_SESSION_BUS_ADDRESS", None)
        self.env[SIDE] = "game"
        self.display = display
        self.display_env = dict(self.env, **{SIDE: "display"})
        self._error = DriverError                    # what fail() raises: the error of the stage that runs
        self.expected = {"title"}                    # the screens complete() requires the body to have reached
        self.reached = set()
        self.hooks = {}
        self.t0 = None
        self.elapsed = None

    # ---- named failures

    def _set_aborted(self, reason, error):
        if not self.status.startswith("aborted: "):
            self.status = f"aborted: {error.kind}: {reason}"

    def fail(self, reason, error=None):
        """Abort this session with a named error. The first reason is the one recorded."""
        error = error or self._error
        self._set_aborted(reason, error)
        self.say(f"ABORT {error.kind}: {reason}")
        raise error(reason)

    def abort_later(self, reason):
        """A fault found after the stages (terminate, reset, storing). The first reason is the one recorded;
        every one is logged."""
        self._set_aborted(reason, self._error)
        self.say(f"ABORT {self._error.kind}: {reason}")

    @contextlib.contextmanager
    def stage(self, name, error):
        """Run a stage: every failure inside it is `error`, an unexpected exception included (it is the
        stage's failure, with its type in the reason), so no stage fails without a name."""
        previous, self._error = self._error, error
        try:
            yield
        except DriverError:
            raise
        except Exception as exc:
            reason = f"{name}: {type(exc).__name__}: {exc}"
            self._set_aborted(reason, error)
            self.say(f"ABORT {error.kind}: {reason}")
            raise error(reason) from exc
        finally:
            self._error = previous

    def require_game(self, where):
        """GameDied unless the game process is still running."""
        if not self.game_alive():
            self.fail(f"the game process exited before {where} (status {self.procs['game'].poll()})", GameDied)

    # ---- the seal

    def require_install_readonly(self):
        """SealError unless the install is read-only for this process: the bind was made once for the namespace."""
        if spike.install_writable(str(self.install)):
            self.fail("the install is writable inside this run", SealError)
        self.observe(0, "process", "install read-only inside the run", "yes")

    def require_baseline(self):
        """SealError unless the registry files of the prefix are the baseline's, byte for byte: the reset puts
        the baseline back, so a prefix that is off it can never come back to its state before the launch."""
        baseline = Path(str(self.prefix) + ".baseline")
        checked = 0
        for name in spike.REG_FILES:
            kept = baseline / name
            if not kept.is_file() or kept.is_symlink():
                continue
            checked += 1
            try:
                with safeio.open_source(self.prefix / name) as fh:
                    here = fh.read()
                with safeio.open_source(kept) as fh:
                    there = fh.read()
            except (safeio.Refused, OSError) as exc:
                self.fail(f"{name} could not be compared with its baseline: {exc}", SealError)
            if here != there:
                self.fail(f"{name} of the prefix is not the baseline's; something outside the driver changed the "
                          "prefix (the reset would not bring it back to this state)", SealError)
        if not checked:
            self.fail("the prefix has no baseline to be reset to", SealError)
        self.observe(0, "file", "registry files equal their baseline before the launch", "yes")

    # ---- the environment

    def note_environment(self):
        stale = None
        if self.dbus_before:
            match = re.match(r"unix:path=([^,;]+)", self.dbus_before)
            stale = bool(match) and not os.path.exists(match.group(1))
            self.say("DBUS_SESSION_BUS_ADDRESS is set in the environment" +
                     (" and names a bus that does not exist (stale)" if stale else "") +
                     "; unset for this run, the window manager starts a bus of its own")
        self.observe(0, "process", "DBUS_SESSION_BUS_ADDRESS in the driver's environment",
                     "not set" if not self.dbus_before else ("set, stale: unset for the run" if stale else "set: unset for the run"))

    # ---- the stages of a session

    def start(self):
        """Everything before the game's first screen: the seal, the display, the snapshot, the seal again, the launch."""
        self.t0 = time.monotonic()
        with self.stage("seal", SealError):
            self.note_environment()
            self.require_install_readonly()
            self.seal("before anything starts", 0)
            self.require_baseline()
        with self.stage("display", DisplayError):
            self.start_x()
            self.start_wm()
        with self.stage("snapshot", SealError):
            self.take_snapshots("before")
        self.launch()

    def launch(self):
        """The prefix sealed once more, immediately before the game starts; then the game."""
        with self.stage("seal", SealError):
            self.seal("immediately before launch", 1)
        with self.stage("launch", LaunchError):
            self.start_game()

    def wait_for_screen(self, name, timeout=None, stable=True):
        """Wait, by pixels, until the named screen ("title", "options", "notice") is up and, with `stable`,
        unchanged between two captures. Seconds waited. ScreenNotReached at the timeout, with a screenshot of
        what was there; GameDied when the game exits meanwhile. Never a fixed wait."""
        if name not in SCREENS:
            raise ValueError(f"{name!r} is not a known screen; the driver knows {sorted(SCREENS)}")
        timeout = TITLE_TIMEOUT if timeout is None else timeout
        seen = getattr(self.screen, SCREENS[name])
        with self.stage(f"wait for the {name} screen", ScreenNotReached):
            def up():
                self.require_game(f"the {name} screen appeared")
                return seen()
            waited = spike.poll(up, timeout, 0.25)
            if waited is None:
                with contextlib.suppress(Exception):
                    self.shot(f"{name}-screen-timeout.png", 2)
                self.fail(f"the {name} screen was not seen within {timeout} s")
            if stable and spike.poll(self.screen.stable, 30, 0.1) is None:
                self.fail(f"the {name} screen never became stable")
            self.reached.add(name)
            self.observe(2, "screen", f"{name} screen reached, seconds waited", waited)
            return waited

    def known_screen(self):
        """The title screen: waited for by its pixels; the seconds since launch are an observation."""
        self.wait_for_screen("title")
        since = round(time.monotonic() - self.t_launch, 2)
        self.observe(2, "screen", "title screen reached and stable, seconds after launch", since)
        self.say(f"title screen reached {since} s after launch")

    def perform(self, text):
        """Run steps in the E002 step language (runtime/iwp/spike/steps.py). A step the language refuses, or
        that fails, is StepFailed; the game must be alive before each step and after the last."""
        with self.stage("step", StepFailed):
            try:
                steps = stepslib.parse(text)
            except stepslib.StepError as exc:
                self.fail(f"the steps are not usable: {exc}")
            for step in steps:
                self.require_game(f"step on line {step.line}")
                self.step_no += 1
                self.say(f"step {step.line}: {step.op} {' '.join(map(str, step.args))}")
                try:
                    self.run_step(step)
                except stepslib.StepError as exc:
                    self.fail(f"step on line {step.line}: {exc}")
            self.require_game("the steps ended")

    def checkpoint(self, name):
        """A named point in the body where an injected fault (or a test) may act; see on()."""
        for hook in self.hooks.get(name, ()):
            self.say(f"checkpoint {name}: {getattr(hook, '__name__', 'hook')}")
            hook(self)

    def on(self, name, hook):
        self.hooks.setdefault(name, []).append(hook)

    # ---- observations

    def shot(self, name, step):
        self.require_game(f"the screenshot {name}")
        return super().shot(name, step)

    def observe_screenshot(self, name, step=None):
        """A screenshot of the whole display, kept as a bundle file; (sha256 of the raw pixels, sha256 of the PNG)."""
        if step is None:
            self.step_no += 1
            step = self.step_no
        return self.shot(name, step)

    def observe_region(self, rect, label):
        """sha256 of the raw pixels of x, y, w, h (the 800x600 stage's coordinates), as an observation."""
        self.require_game(f"reading the region {label}")
        digest = spike.sha256_bytes(self.screen.raw(rect))
        self.step_no += 1
        self.observe(self.step_no, "screen", f"region {label} {','.join(map(str, rect))} raw RGB8 sha256", digest)
        return digest

    def observe_file(self, rel):
        """One file of the game copy, read in place: size, sha256 and whether it equals the install's."""
        self.step_no += 1
        self.read_game_file(rel)

    def complete(self):
        """The only place a session becomes completed: the body ran, the known screens it expects were
        reached, both screenshots exist, and the game was still alive."""
        have = {name for name, _, _ in self.outputs}
        missing = [name for name in ("before.png", "after.png") if name not in have]
        if missing:
            self.fail("the cycle ended without " + " and ".join(missing), StepFailed)
        absent = sorted(self.expected - self.reached)
        if absent:
            self.fail("the cycle never reached its known screen: " + ", ".join(absent), ScreenNotReached)
        self.require_game("the cycle ended")
        if self.status == "running":
            self.status = "completed"

    # ---- terminate

    def alive(self, side=None):
        return run_processes(self.run_id, side)

    def wait_gone(self, side, timeout):
        """Seconds until no process of this run on `side` is alive, or None at the bound. Only this run's
        processes (its marker, whole) are looked at, and the wait always ends."""
        return spike.poll(lambda: not self.alive(side), timeout, 0.05)

    def kill_side(self, side):
        for pid in self.alive(side):
            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGKILL)

    def terminate(self):
        """`wineserver -k` (immediate, F002), then a bounded wait for the game side: no fixed wait, and no
        wait for the display side's daemons. A game side that is still there after the bound is killed, and
        a second bound ends in TerminateError."""
        self.say("wineserver -k")
        spike.run([spike.WINESERVER, "-k"], env=self.env)
        spike.poll(lambda: not self.game_alive(), 20, 0.05)
        code = self.procs["game"].poll()
        self.observe(9, "process", "game process exit status", code)
        self.say(f"game exit status {code}")
        waited = self.wait_gone("game", WAIT_GONE_TIMEOUT)
        self.observe(9, "process", "game side gone after terminate (s)",
                     f"still running after {WAIT_GONE_TIMEOUT} s" if waited is None else waited)
        self.say(f"game side gone after terminate: {waited}")
        if waited is None:
            self.say("wineserver -k again, then SIGKILL of the game side")
            spike.run([spike.WINESERVER, "-k"], env=self.env)
            self.kill_side("game")
            if self.wait_gone("game", AFTER_KILL_TIMEOUT) is None:
                self.fail(f"{len(self.alive('game'))} process(es) of the game side survived a kill", TerminateError)

    def stop_x(self):
        for name in ("wm", "xvfb"):
            proc = self.procs.get(name)
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        waited = self.wait_gone("display", DISPLAY_GONE_TIMEOUT)
        if waited is None:
            self.say("the display side did not end by itself; SIGKILL")
            self.kill_side("display")
            waited = self.wait_gone("display", AFTER_KILL_TIMEOUT)
        self.observe(10, "process", "display side gone after the display was stopped (s)",
                     "still running" if waited is None else waited)
        left = self.alive()
        self.observe(10, "process", "processes of this run still alive after terminate", len(left))
        self.say(f"processes still alive after terminate: {len(left)}")
        if left:
            self.fail(f"{len(left)} process(es) survived terminate", TerminateError)

    # ---- the whole session

    def cleanup(self, stage, action, error=DriverError):
        """One clean-up stage; a failure of it aborts the session (named by `error`) and does not stop the next."""
        if action is None:
            return
        previous, self._error = self._error, error
        try:
            action()
        except BaseException as exc:
            self.abort_later(f"{stage} failed: {type(exc).__name__}: {exc}")
        finally:
            self._error = previous

    def finish(self):
        """Terminate, stop the display, snapshot and reset, keep the logs; every stage runs, whatever failed
        before. The status is left aborted unless complete() ran and nothing here failed."""
        self.cleanup("terminate", self.terminate if "game" in self.procs else None, TerminateError)
        self.cleanup("stopping the display", self.stop_x, TerminateError)
        if hasattr(self, "snap_before"):
            self.cleanup("snapshot and reset", self.snapshot_and_reset, ResetError)
        self.cleanup("keeping the logs", self.keep_logs, RecordError)
        if self.status == "running":
            self._error = DriverError
            self.status = f"aborted: {DriverError.kind}: the cycle stopped before its end"
        self.elapsed = round(time.monotonic() - self.t0, 2) if self.t0 is not None else None
        self.observe(12, "process", "session seconds, from the first seal to the end of the reset", self.elapsed)

    def execute(self, body):
        """start, body(session), complete, finish. Returns the status."""
        started = now()
        try:
            self.start()
            body(self)
            self.complete()
        except DriverError:
            pass                                   # fail() recorded why
        except BaseException as exc:               # a crash or an interruption: cleaned up, recorded, never completed
            self.abort_later(f"{type(exc).__name__}: {exc}")
        self.finish()
        self.started, self.ended = started, now()
        return self.status
