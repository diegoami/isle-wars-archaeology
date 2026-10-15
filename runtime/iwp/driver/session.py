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
status is "completed" only from finish(), and only when complete() had run first — after the body, and
only when the known screens the body expects were reached, at least one input step of perform()
succeeded, `before.png` was taken before the first input and `after.png` after the last, and the game
was alive at the end — and finish() itself then terminated, stopped the display and reset the prefix
without a fault (T13 round 6, R3: complete() alone publishes only `body_complete`, never the status).
Every other way out is
"aborted: <kind>: <reason>" (the first reason; every later fault is an observation too), and the clean-up
stages and the reset run in both cases. `recovered` is True only when every clean-up stage succeeded and
the reset was shown to restore the prefix: a caller may start the next session only then. A session that
ended before its snapshot of the prefix (a refused seal, no display) performed no reset and is never
recovered (T13 round 4, R2).

Session is a facade (T13 round 4): it holds the machinery, an Engine built on the spike's Cycle, privately,
and its public interface is only its own methods, each through the one liveness guard (`guarded`) or with a
stated reason (`unguarded`), and read-only views of the state. Every view is an immutable copy of the
engine's state, made at each read (T13 round 5, R1 to R3): the live objects let a caller retarget
WINEPREFIX after the seal, mark a screen reached by hand, or delete the liveness guard's process entry, so
no view hands out the engine's own dict, set or list, and expect() is the one way to name the screens a
body will reach. No method of the spike's Cycle (its
complete_script(), run_step(), ...) is an attribute of a Session, so complete() is its only completion route
and perform() its only way to send the game a step; the Engine also refuses the spike's own routes
(Engine.SPIKE_ONLY). tests/test_iwp_driver.py GuardSweepTest checks this over the effective interface,
ViewImmutabilityTest checks that the views cannot mutate the engine, and
CommandHelperSweepTest checks every command on the driver's path, the reused spike and setup files included,
with every state probe (spike.probe) allowed only at its named sites (T13 round 5, R4).

What the driver keeps from T08 on every launch: the install bound read-only (checked at the start of
every session), the prefix sealed before anything starts and again immediately before the game starts,
the game in a network namespace of its own, and every file written through setup/iwp/safeio.py.

What it changes against the spike (measured in F006):
* a process is told apart by the marker `IWP_CYCLE_RUN=<run id>`, by `IWP_CYCLE_INVOCATION=<token>` of the
  command that started it (runner.py; the outer process signals only its own token's processes), and by a side, `IWP_CYCLE_SIDE=game` for
  the game and `display` for Xvfb, the window manager and the daemons the window manager starts. Terminate
  waits, with a bound, for the game side only: the spike's 30 s poll counted the display side's daemons
  (dbus-daemon, at-spi, xfconfd seen in one diagnosis), which the driver saw end only after the display
  stopped (#40; F006 says what this does and does not establish);
* the children get no DBUS_SESSION_BUS_ADDRESS (#40: with a stale one, E002's xfwm4 did not register; the cause
  is a hypothesis, F006) and no TMPDIR, so that Wine uses the private /tmp of the namespace (F006 keeps the
  TMPDIR failures seen while building the driver as unreplicated observations);
* every helper command and every wait has a bound (spike.run, RUN_TIMEOUT; the reaps in stop_x);
* round 2 of the review (PR #54): every signal goes through kill_marked (the markers re-checked through a
  pidfd); every helper whose result is used is checked (spike.must), so a failed input is a failed step; the
  game side and the display side are checked alive at every stage boundary, just before terminate too; the
  check immediately before launch repeats every check of the first that can change; and the display is
  this run's own Xvfb's (start_x, display_is_ours), never another server that happens to answer.
"""
import argparse
import contextlib
import functools
import os
import types
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
from . import screens  # noqa: E402
from .errors import (DriverError, DisplayError, GameDied, LaunchError, ResetError, RecordError,  # noqa: E402
                     ScreenNotReached, SealError, StepFailed, TerminateError)

EXPERIMENT = "E004"
MARK = spike.MARK                      # IWP_CYCLE_RUN
SIDE = "IWP_CYCLE_SIDE"
SIDES = ("game", "display")
INVOCATION = "IWP_CYCLE_INVOCATION"    # one token per command (runner.outer); never shared by two commands
INPUT_OPS = frozenset({"click", "click!", "clicks", "click-any", "click-until", "click-any?", "click-until?",
                       "key", "attack-picked"})    # the steps that send the game a click or a key ("move" does not)
SCREENS = {"title": "title_up", "options": "options_up", "notice": "notice_up"}
TITLE_TIMEOUT = 45                     # s, the title screen after launch (F002: 6.6 to 6.7 s)
WAIT_GONE_TIMEOUT = 10                 # s, the game side after `wineserver -k` (F002: 2.1 s; the bound is slack)
DISPLAY_GONE_TIMEOUT = 5               # s, the display side after Xvfb and xfwm4 were stopped
AFTER_KILL_TIMEOUT = 5                 # s, after a second `wineserver -k` and SIGKILL, before TerminateError
STOP_TIMEOUT = 10                      # s, for Xvfb or xfwm4 to end after SIGTERM, before SIGKILL
WINESERVER_TIMEOUT = 15                # s, `wineserver -k` itself (it returns at once, F002)
FIRST_DISPLAY, LAST_DISPLAY = 77, 120
XVFB_READY_TIMEOUT = 20                # s, for this run's Xvfb to hold its display (F006: 0.06 to 0.12 s)
DISPLAY_ATTEMPTS = 3                   # displays tried when the one picked was taken meanwhile, before DisplayError


def now():
    return spike.now()


def guarded(where):
    """The one liveness guard of the driver (class C, T13 round 3). Marks a public method of Session:
    the game side and the display side must be alive before and after it. The before-check runs at
    entry, the after-check only when the method returned without raising, so a first failure keeps its
    reason; a death raises the driver's own GameDied or DisplayError (never an unlabelled one), and the
    waits inside the method carry their own bounds (spike.poll), so an expiry is a bound, never a fixed
    wait. Every public method of Session carries this guard or `unguarded(reason)`, and
    tests/test_iwp_driver.py GuardSweepTest checks that over Session's effective interface (T13 round 4)."""
    def decorate(fn):
        @functools.wraps(fn)
        def wrapped(self, *args, **kwargs):
            engine = self._engine
            if "game" in engine.procs:               # nothing to guard before the game is started
                engine.require_alive(where)
            result = fn(self, *args, **kwargs)
            if "game" in engine.procs:
                engine.require_alive(f"{where} (after)")
            return result
        wrapped.guarded = where
        return wrapped
    return decorate


def unguarded(reason):
    """Marks a public method of Session that does not go through the guard, and says why: it starts or
    ends the game itself and checks liveness where it does (start, finish), it only composes guarded
    methods (execute), or it neither sends the game anything nor reads its screen (the rest)."""
    def decorate(fn):
        fn.unguarded = reason
        return fn
    return decorate


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


def environ_has(pid, items):
    """True when every one of `items` (b"NAME=value") is a whole entry of the environment of pid."""
    try:
        env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
    except OSError:
        return False
    return all(item in env for item in items)


def invocation_processes(token):
    """pids of the processes whose environment holds exactly IWP_CYCLE_INVOCATION=<token>, read from /proc:
    the processes of one command and of nothing else (another E004 command has another token)."""
    if not token:
        raise ValueError("invocation_processes needs a token; it never looks at every marked process")
    want = [f"{INVOCATION}={token}".encode()]
    return [int(e.name) for e in Path("/proc").iterdir()
            if e.name.isdigit() and int(e.name) != os.getpid() and environ_has(e.name, want)]


def kill_marked(pid, items, sig=signal.SIGKILL):
    """Send sig (SIGKILL) to pid only if it still carries every one of `items`: the check is made again
    through a pidfd, so a pid reused by another process between the listing and the signal is never
    signalled. True when sent. Every signal the driver sends to a process goes through here."""
    if not items:
        raise ValueError("kill_marked needs the markers the process must carry")
    try:
        fd = os.pidfd_open(pid)
    except OSError:
        return False
    try:
        if not environ_has(pid, items):
            return False
        signal.pidfd_send_signal(fd, sig)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def free_display(first=FIRST_DISPLAY, last=LAST_DISPLAY, exclude=()):
    """The first display number in [first, last] that no X server of this machine listens on, and not one of
    `exclude` (":n" names). Only a hint: another server can take it before this run's Xvfb does, which
    Session.start_x finds out (display_is_ours) and answers with another display.

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
    taken.update(int(name[1:]) for name in exclude)
    for number in range(first, last + 1):
        if number not in taken and not Path(f"/tmp/.X{number}-lock").exists():
            return f":{number}"
    raise DisplayError(f"no free X display between :{first} and :{last}")


def listening_socket_inodes(path):
    """Inodes of the listening unix sockets bound to `path` ("@..." for an abstract one), from /proc/net/unix."""
    found = set()
    for line in Path("/proc/net/unix").read_text(errors="replace").splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 8 and fields[7] == path and int(fields[3], 16) & 0x10000:   # __SO_ACCEPTCON: listening
            found.add(int(fields[6]))
    return found


def socket_inodes_of(pid):
    """Inodes of the sockets that process pid holds open, from /proc/<pid>/fd."""
    found = set()
    try:
        entries = list(Path(f"/proc/{pid}/fd").iterdir())
    except OSError:
        return found
    for entry in entries:
        try:
            match = re.fullmatch(r"socket:\[(\d+)\]", os.readlink(entry))
        except OSError:
            continue
        if match:
            found.add(int(match.group(1)))
    return found


def bind_install_readonly(install):
    """Bind the install read-only in this mount namespace, once per command; SealError unless it then is
    read-only here. Every session checks it again (Session.require_install_readonly)."""
    install = str(install)
    try:
        spike.must(["mount", "--bind", install, install], require_output=False)
        spike.must(["mount", "-o", "remount,bind,ro", install], require_output=False)
    except spike.CommandFailed as exc:
        raise SealError(f"the install could not be made read-only inside the run: {exc}") from None
    if spike.install_writable(install):
        raise SealError("the install could not be made read-only inside the run")


# --- the session -----------------------------------------------------------------------------

class Engine(spike.Cycle):
    """The machinery of one session, private to the driver: the spike's Cycle with the driver's stages.

    A caller never holds an Engine: it holds a Session, which keeps its Engine in `_engine` and exposes only
    the driver's own methods, each through the liveness guard or a stated exception (T13 round 4, R1 and R3:
    when Session inherited Cycle, the spike's complete_script() and run_step() were public methods of a
    session, one a completion route past complete(), the other a game input past the guard). The spike's
    own routes that the driver does not take are refused here too (SPIKE_ONLY), so that even an Engine
    reached on purpose has no completion route but complete()."""

    SPIKE_ONLY = ("complete_script", "run_script", "load_script", "session", "input", "hover_click",
                  "protect_install", "execute")

    def __init__(self, run_id, prefix, bundles, install, display, arm="control", size="800x600x24",
                 experiment=None):
        args = argparse.Namespace(size=size, audio="off", wm="xfwm4", click="hover", terminate="kill", script=None,
                                  session=False, input="options", arm=arm, experiment=experiment or EXPERIMENT,
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
        self.t0 = None
        self.elapsed = None
        self.events = 0                              # a counter that orders the inputs and the screenshots
        self.actions = []                            # (event, op, line) of every input step that succeeded
        self.shot_at = {}                            # screenshot name -> event
        self.later_faults = []                       # every fault after the first, and every clean-up fault
        self.cleaned = {}                            # clean-up stage -> succeeded without a fault
        self.recovered = False                # set by finish(): every clean-up stage succeeded
        self.body_complete = False            # set by complete(): the body's cycle was a good one (round 6, R3)

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
        """A fault found after the stages (terminate, reset, storing). The first reason is the one in the
        status; every one is logged and kept in later_faults, which `recovered` and the record read."""
        self.later_faults.append(f"{self._error.kind}: {reason}")
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
            reason = f"{type(exc).__name__}: {exc} (in the {name} stage)"
            self._set_aborted(reason, error)
            self.say(f"ABORT {error.kind}: {reason}")
            raise error(reason) from exc
        finally:
            self._error = previous

    def require_game(self, where):
        """GameDied unless the game process is still running."""
        if not self.game_alive():
            self.fail(f"the game process exited before {where} (status {self.procs['game'].poll()})", GameDied)

    def display_dead(self):
        """Names of this run's display processes (Xvfb, xfwm4) that were started and have exited."""
        return [name for name in ("xvfb", "wm") if name in self.procs and self.procs[name].poll() is not None]

    def require_display(self, where):
        """DisplayError unless every display process this run started is still running."""
        dead = self.display_dead()
        if dead:
            self.fail(f"{' and '.join(dead)} exited before {where}", DisplayError)

    def require_alive(self, where):
        """The game side and the display side are both alive (class C: checked at every stage boundary)."""
        self.require_display(where)
        self.require_game(where)

    # ---- the seal

    def require_install_readonly(self, when="before anything starts", step=0):
        """SealError unless the install is read-only for this process: the bind was made once for the namespace."""
        if spike.install_writable(str(self.install)):
            self.fail(f"the install is writable inside this run ({when})", SealError)
        self.observe(step, "process", f"install read-only inside the run ({when})", "yes")

    def require_baseline(self, when="before anything starts", step=0):
        """SealError unless every registry file the prefix has matches its baseline, byte for byte: the reset
        puts the baseline back, so a prefix that is off it can never come back to its state before the launch.

        The baseline is never partly matched (T13 round 3, R1): a registry file the prefix has with no
        plain baseline file, or with a baseline that is a link, refuses the launch, rather than being
        skipped as if it were equal."""
        baseline = Path(str(self.prefix) + ".baseline")
        checked = 0
        incomplete = []
        for name in spike.REG_FILES:
            kept = baseline / name
            if not (self.prefix / name).is_file():     # not present in the prefix: nothing to compare or reset
                continue
            if not kept.is_file() or kept.is_symlink():
                incomplete.append(name)
                continue
            checked += 1
            try:
                with safeio.open_source(self.prefix / name) as fh:
                    here = fh.read()
                with safeio.open_source(kept) as fh:
                    there = fh.read()
            except (safeio.Refused, OSError) as exc:
                self.fail(f"{name} could not be compared with its baseline ({when}): {exc}", SealError)
            if here != there:
                self.fail(f"{name} of the prefix is not the baseline's ({when}); something outside the driver changed "
                          "the prefix (the reset would not bring it back to this state)", SealError)
        if incomplete:
            self.fail(f"the prefix has no baseline for its registry file(s) ({when}): "
                      + ", ".join(incomplete), SealError)
        if not checked:
            self.fail(f"the prefix has no baseline to be reset to ({when})", SealError)
        self.observe(step, "file", f"registry files equal their baseline ({when})", "yes")

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
            self.require_install_readonly("before anything starts", 0)
            self.seal("before anything starts", 0)
            self.require_baseline("before anything starts", 0)
        with self.stage("display", DisplayError):
            self.start_x()
            self.start_wm()
            self.require_display("the snapshot")
        with self.stage("snapshot", SealError):
            begun = time.monotonic()
            self.take_snapshots("before")
            self.observe(3, "process", "snapshot of the prefix before the launch took (s)", round(time.monotonic() - begun, 2))
        self.launch()

    def launch(self):
        """Every check of the first seal that can change meanwhile, again, immediately before the game starts
        (the install read-only, the prefix safe to launch from, the registry files equal to the baseline;
        class D); the display alive; then the game, alive at the end of the launch."""
        with self.stage("seal", SealError):
            self.require_install_readonly("immediately before launch", 1)
            self.seal("immediately before launch", 1)
            self.require_baseline("immediately before launch", 1)
        with self.stage("launch", LaunchError):
            self.require_display("the launch")
            self.start_game()
            self.require_alive("the end of the launch")

    # ---- the display, this run's own (class E)

    def set_display(self, display):
        self.display = display
        self.env["DISPLAY"] = display
        self.display_env["DISPLAY"] = display

    def spawn_xvfb(self):
        width, height, depth = self.size
        return spike.spawn(["Xvfb", self.display, "-screen", "0", f"{width}x{height}x{depth}", "-nolisten", "tcp"],
                           env=self.display_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def display_is_ours(self, proc):
        """True only when this run's Xvfb is alive, itself holds the display's listening socket, and answers.
        A server of someone else's that answers on the same display is never taken for it."""
        if proc.poll() is not None:
            return False
        path = f"@/tmp/.X11-unix/X{self.display[1:]}"
        if not listening_socket_inodes(path) & socket_inodes_of(proc.pid):
            return False
        return spike.probe(["xdpyinfo"], env=self.env)[0]

    def start_x(self):
        """Xvfb on a free display, ready only when display_is_ours: the display number picked is only a hint,
        and when another server takes it first this run's Xvfb exits (it cannot bind), so another display is
        tried, DISPLAY_ATTEMPTS in all; DisplayError otherwise. Never attached to a server it did not start."""
        Path("/tmp/.X11-unix").mkdir(mode=0o1777, exist_ok=True)
        tried = []
        for attempt in range(1, DISPLAY_ATTEMPTS + 1):
            if attempt > 1:
                self.set_display(free_display(exclude=tried))
            tried.append(self.display)
            proc = self.procs["xvfb"] = self.spawn_xvfb()
            waited = spike.poll(lambda: proc.poll() is not None or self.display_is_ours(proc), XVFB_READY_TIMEOUT, 0.05)
            if waited is not None and self.display_is_ours(proc):
                break
            if proc.poll() is None:
                self.fail(f"Xvfb on {self.display} did not hold its display within {XVFB_READY_TIMEOUT} s", DisplayError)
            self.say(f"Xvfb on {self.display} exited (status {proc.returncode}): the display was taken; another one")
            self.observe(0, "process", "display taken before this run's Xvfb held it; Xvfb exit status", proc.returncode)
        else:
            self.fail(f"no display of this run's own after {DISPLAY_ATTEMPTS} attempts ({', '.join(tried)})", DisplayError)
        info = spike.must(["xdpyinfo"], env=self.env).stdout.decode()
        dims = re.search(r"dimensions:\s+(\d+x\d+)", info).group(1)
        planes = re.search(r"depth of root window:\s+(\d+)", info).group(1)
        self.observe(0, "process", "xvfb ready (s)", waited)
        self.observe(0, "process", "root window", f"{dims}x{planes}")
        self.observe(0, "process", "X display held by this run's Xvfb (attempt)", attempt)
        self.say(f"Xvfb ready after {waited} s on attempt {attempt}, root {dims}x{planes}")

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
                self.require_alive(f"the {name} screen appeared")
                return seen()
            waited = spike.poll(up, timeout, 0.25)
            if waited is None:
                with contextlib.suppress(Exception):
                    self.shot(f"{name}-screen-timeout.png", 2)
                self.fail(f"the {name} screen was not seen within {timeout} s")
            if stable:
                def stable_and_alive():          # R3: the stability poll also checks the game is alive,
                    result = self.screen.stable()    # after the capture, so a death during it is caught
                    self.require_alive(f"the {name} screen was not stable")
                    return result
                if spike.poll(stable_and_alive, 30, 0.1) is None:
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
                self.require_alive(f"step on line {step.line}")
                self.step_no += 1
                self.say(f"step {step.line}: {step.op} {' '.join(map(str, step.args))}")
                try:
                    self.run_step(step)
                except (stepslib.StepError, spike.CommandFailed) as exc:
                    self.fail(f"step on line {step.line}: {exc}")
                if step.op in INPUT_OPS:             # run_step returned: every command of the step exited 0
                    self.events += 1
                    self.actions.append((self.events, step.op, step.line))
            self.require_alive("the steps ended")
            self.observe(self.step_no, "process", "input steps that succeeded so far", len(self.actions))

    # ---- observations

    def shot(self, name, step):
        self.require_alive(f"the screenshot {name}")
        taken = super().shot(name, step)
        self.events += 1
        self.shot_at[name] = self.events
        return taken

    def observe_screenshot(self, name, step=None):
        """A screenshot of the whole display, kept as a bundle file; (sha256 of the raw pixels, sha256 of the PNG)."""
        if step is None:
            self.step_no += 1
            step = self.step_no
        return self.shot(name, step)

    def observe_region(self, rect, label):
        """sha256 of the raw pixels of x, y, w, h (the 800x600 stage's coordinates), as an observation."""
        self.require_alive(f"reading the region {label}")
        digest = spike.sha256_bytes(self.screen.raw(rect))
        self.step_no += 1
        self.observe(self.step_no, "screen", f"region {label} {','.join(map(str, rect))} raw RGB8 sha256", digest)
        return digest

    def screen_name(self):
        """The screen the game shows, by pixel counts on measured regions (screens.name_of; T38 round 4):
        eliminated, game-over (round 6), board-menu, board, title or unknown. Reads the stage; sends nothing."""
        self.require_alive("reading the screen")
        return screens.name_of(self.screen.raw((0, 0) + spike.STAGE))

    def screen_card_award(self):
        """The bounded measured green card-prompt probe, or False for grey/unknown/terminal states."""
        self.require_alive("reading the card prompt")
        return screens.card_award_green(self.screen.raw((0, 0) + spike.STAGE))

    def screen_winner(self):
        """The winning seat's colour word on the winner notice, by pixels on the score panel
        (screens.winner_of; T38 round 6), or None. Reads the stage; sends nothing."""
        self.require_alive("reading the winner")
        return screens.winner_of(self.screen.raw((0, 0) + spike.STAGE))

    def observe_file(self, rel):
        """One file of the game copy, read in place: size, sha256 and whether it equals the install's."""
        self.step_no += 1
        self.read_game_file(rel)

    def complete(self):
        """The only route by which a body's cycle may be completed (T13 round 6, R3): the body ran, the
        known screens it expects were reached, it acted (an input step of perform() succeeded),
        `before.png` was taken before its first input and `after.png` after its last, and the game was
        still alive. What it publishes is provisional (`body_complete` True, the status still
        "running"): the status becomes "completed" only in finish(), when termination and the reset have
        succeeded too, so the public status never claims completion of a session that was not reset."""
        have = {name for name, _, _ in self.outputs}
        missing = [name for name in ("before.png", "after.png") if name not in have]
        if missing:
            self.fail("the cycle ended without " + " and ".join(missing), StepFailed)
        absent = sorted(self.expected - self.reached)
        if absent:
            self.fail("the cycle never reached its known screen: " + ", ".join(absent), ScreenNotReached)
        if not self.actions:
            self.fail("the cycle performed no input step (perform() never sent a click or a key that succeeded)",
                      StepFailed)
        if not self.shot_at.get("before.png", 0) < self.actions[0][0]:
            self.fail("before.png was not taken before the first input", StepFailed)
        if not self.shot_at.get("after.png", 0) > self.actions[-1][0]:
            self.fail("after.png was not taken after the last input", StepFailed)
        self.require_alive("the cycle ended")
        self.body_complete = True

    # ---- terminate

    def alive(self, side=None):
        return run_processes(self.run_id, side)

    def wait_gone(self, side, timeout):
        """Seconds until no process of this run on `side` is alive, or None at the bound. Only this run's
        processes (its marker, whole) are looked at, and the wait always ends."""
        return spike.poll(lambda: not self.alive(side), timeout, 0.05)

    def kill_side(self, side):
        items = [f"{MARK}={self.run_id}".encode(), f"{SIDE}={side}".encode()]
        for pid in self.alive(side):
            kill_marked(pid, items)

    def terminate(self):
        """`wineserver -k` (immediate, F002), then a bounded wait for the game side: no fixed wait, and no
        wait for the display side's daemons. A game side that is still there after the bound is killed, and
        a second bound ends in TerminateError. The exit status of `wineserver -k` is recorded, not relied on
        (it is 1 when no server is left, after a game that died); what is relied on is the game side gone.

        R2 (T13 round 3): the liveness check at the point of termination is inside this method, not in a
        separate check before it. A game that died on its own since the last check aborts the session here,
        and the clean-up and the reset still run.

        A dead game process is not a dead game side: after a SIGKILL of the game, the run's wineserver,
        services, winedevice, explorer and the rest are still alive (E004-r0108: 7 survived). So the full
        termination below runs whether the game process is alive or not; only the status differs."""
        if not self.game_alive():
            self._set_aborted(f"the game process exited before terminate (status {self.procs['game'].poll()})", GameDied)
            self.say("the game had already exited before terminate; the rest of its side is still terminated")
        self.say("wineserver -k")
        # The exit status of `wineserver -k` is a state, not an error: it is 1 when no server is left.
        # What terminate relies on is the game side gone (the bounded wait below), never this exit code.
        ok, _, _ = spike.probe([spike.WINESERVER, "-k"], env=self.env, timeout=WINESERVER_TIMEOUT)
        self.observe(9, "process", "wineserver -k exit status",
                     "0" if ok else "non-zero (no server left; the game side is what is relied on)")
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
            spike.probe([spike.WINESERVER, "-k"], env=self.env, timeout=WINESERVER_TIMEOUT)
            self.kill_side("game")
            if self.wait_gone("game", AFTER_KILL_TIMEOUT) is None:
                self.fail(f"{len(self.alive('game'))} process(es) of the game side survived a kill", TerminateError)

    def stop_own(self, proc, sig):
        """A signal to one of this run's display processes, through kill_marked (its markers re-checked)."""
        kill_marked(proc.pid, [f"{MARK}={self.run_id}".encode(), f"{SIDE}=display".encode()], sig)

    def stop_x(self):
        """Stop xfwm4 and Xvfb (SIGTERM, then SIGKILL after STOP_TIMEOUT), every wait bounded; then the
        display side's processes, then the check that nothing of this run is left. TerminateError otherwise.

        The display-side liveness check is inside this method, at the point of stopping, symmetric with
        terminate(): a display process that already exited aborts the session, and the stop still runs."""
        dead = self.display_dead()
        if dead:
            self._set_aborted(f"{' and '.join(dead)} exited before terminate", DisplayError)
        unreaped = []
        for name in ("wm", "xvfb"):
            proc = self.procs.get(name)
            if proc and proc.poll() is None:
                self.stop_own(proc, signal.SIGTERM)
                try:
                    proc.wait(STOP_TIMEOUT)
                except subprocess.TimeoutExpired:
                    self.stop_own(proc, signal.SIGKILL)
                    try:
                        proc.wait(AFTER_KILL_TIMEOUT)
                    except subprocess.TimeoutExpired:
                        unreaped.append(name)
        if unreaped:
            self.fail(f"{' and '.join(unreaped)} not reaped within {AFTER_KILL_TIMEOUT} s of SIGKILL", TerminateError)
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
        begun = time.monotonic()
        faults = len(self.later_faults)
        try:
            action()
        except BaseException as exc:
            self.abort_later(f"{stage} failed: {type(exc).__name__}: {exc}")
        finally:
            self._error = previous
            self.cleaned[stage] = len(self.later_faults) == faults
            self.observe(11, "process", f"clean-up stage '{stage}' took (s)", round(time.monotonic() - begun, 2))

    def snapshot_and_reset(self):
        """The spike's snapshot, diff and reset, and ResetError unless the reset restored the prefix."""
        self.take_snapshots("after")
        self.report_changes()
        if self.reset() is not True:
            raise ResetError("the prefix after the reset is not the prefix before the launch")

    def finish(self):
        """Terminate, stop the display, snapshot and reset, keep the logs; every stage runs, whatever failed
        before. This is the only place the status "completed" is published (T13 round 6, R3), and only when
        complete() ran (its checks passed, `body_complete`) and every clean-up stage succeeded with the
        reset shown to restore the prefix (`recovered`); the status is left aborted otherwise. The liveness
        at the terminate and stop boundaries is checked inside terminate() and stop_x() themselves."""
        self.cleanup("terminate", self.terminate if "game" in self.procs else None, TerminateError)
        self.cleanup("stopping the display", self.stop_x, TerminateError)
        snapshot = hasattr(self, "snap_before")
        if snapshot:
            self.cleanup("snapshot and reset", self.snapshot_and_reset, ResetError)
        self.cleanup("keeping the logs", self.keep_logs, RecordError)
        # R2 (T13 round 4): recovered means the reset ran and was shown to restore the prefix. A session that
        # ended before its snapshot (a seal that refused the prefix, a display that never came up) had nothing
        # to reset to, so no reset or restoration was performed and it is never recovered, whatever else went
        # well: the prefix it refused may be off its baseline, and it is never reset to manufacture a success.
        # The next session may start only once a seal has proven the prefix on its baseline (start()).
        self.recovered = snapshot and all(self.cleaned.values()) and self.cleaned.get("snapshot and reset") is True
        self.observe(12, "process", "reset and restoration of the prefix performed",
                     "yes" if snapshot else "no: the session ended before its snapshot, so there was nothing to "
                     "reset to; the prefix is not proven on its baseline")
        failed = [stage for stage, ok in self.cleaned.items() if not ok]
        self.observe(12, "process", "clean-up: every stage succeeded and the prefix was reset (the next session may start)",
                     "yes" if self.recovered else "no: " + ", ".join(
                         failed or ["no reset was performed (no snapshot of the prefix was taken)"]))
        for fault in self.later_faults:
            self.observe(12, "process", "a fault logged by abort_later (the status keeps only the first reason)", fault[:300])
        if self.status == "running":
            if self.body_complete and self.recovered:
                self.status = "completed"          # published here only: the reset was shown to restore the prefix
            else:
                self._error = DriverError
                self.status = f"aborted: {DriverError.kind}: the cycle stopped before its end"
        self.elapsed = round(time.monotonic() - self.t0, 2) if self.t0 is not None else None
        self.observe(12, "process", "session seconds, from the first seal to the end of the reset", self.elapsed)


def _spike_only(name):
    def refused(self, *args, **kwargs):
        raise DriverError(f"{name}() is the spike's own route, which the driver never takes (T13 round 4)")
    refused.__name__ = refused.__qualname__ = name
    return refused


for _name in Engine.SPIKE_ONLY:
    setattr(Engine, _name, _spike_only(_name))


# --- the session: the driver's only public interface ------------------------------------------

class _FrozenArgs:
    """The spike's arguments as the caller sees them: a namespace whose fields cannot be written."""
    __slots__ = ("_fields",)

    def __init__(self, fields):
        object.__setattr__(self, "_fields", dict(fields))

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, "_fields")[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, item, value):
        raise AttributeError("the session's arguments are read-only")

    def __delattr__(self, item):
        raise AttributeError("the session's arguments are read-only")

    def __repr__(self):
        return f"read-only args {object.__getattribute__(self, '_fields')!r}"


class _ProcView:
    """One process of the run as the caller sees it: a name, a pid, the exit status at this read and a
    dead/alive query, never the engine's Popen (T13 round 6, R2: through the live handle a caller set
    `p.poll = lambda: None` on a dead child and game-facing steps stayed alive). Every attribute is
    read-only, `alive` is asked of /proc at each access (so it keeps answering after the process died),
    and there is no method on it that touches the process."""
    __slots__ = ("name", "pid", "_returncode")

    def __init__(self, name, proc):
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "pid", proc.pid)
        object.__setattr__(self, "_returncode", proc.poll())

    @property
    def returncode(self):
        """The exit status as it was at this read (None while the process ran); it is a copy, not a handle."""
        return self._returncode

    @property
    def alive(self):
        """Whether /proc still shows this pid running (not a zombie); asked anew at each access."""
        return spike.Cycle.is_alive(self.pid)

    def __setattr__(self, item, value):
        raise AttributeError("the session's process view is read-only")

    def __delattr__(self, item):
        raise AttributeError("the session's process view is read-only")

    def __repr__(self):
        return f"<process {self.name} pid {self.pid}, {'alive' if self.alive else 'dead'}>"


def _frozen(value):
    """An immutable copy of one piece of engine state, made fresh at every read: the caller's view is
    never the live object (T13 round 5, R1 to R3:     the live dict let a caller retarget WINEPREFIX after
    the seal, the live set let it mark screens reached by hand, the live process registry let it delete
    the liveness guard's entry, and the live snapshot dictionaries inside a tuple let one be substituted
    for the reset's target, T13 round 6, R1). Maps become read-only mappings, sets frozensets, lists
    and tuples tuples of frozen descendants (a tuple is frozen through: its items were the live snapshot
    dictionaries), a namespace a read-only namespace; the copies of one read snapshot the state at that
    moment."""
    if isinstance(value, dict):
        return types.MappingProxyType({k: _frozen(v) for k, v in value.items()})
    if isinstance(value, set):
        return frozenset(_frozen(v) for v in value)
    if isinstance(value, (list, tuple)):
        return tuple(_frozen(v) for v in value)
    if isinstance(value, argparse.Namespace):
        return _FrozenArgs(vars(value))
    return value


def _view(name, doc):
    """A read-only view of one attribute of the session's engine: an immutable copy, never the live object."""
    return property(lambda self: _frozen(getattr(self._engine, name)), doc=doc)


class Session:
    """One launch of the game, from a sealed prefix to a reset one. See the module text.

    Composition, not inheritance (T13 round 4, R1 and R3): a Session holds its Engine privately and its
    public interface is only what is defined here. Every public method goes through the liveness guard
    (`guarded`) or names why not (`unguarded`); no method of the spike's Cycle is an attribute of a Session,
    so complete() is the only completion route and perform() the only way to send the game a step. The
    state a caller or a record reads (status, observations, outputs, processes, ...) is read-only here:
    every view is an immutable copy, never the engine's live object (T13 round 5, R1 to R3, and round 6:
    the process views carry pid, exit status and a dead/alive query instead of the engine's Popen handles,
    and the snapshot view freezes the dictionaries inside its tuples), so no caller can retarget the
    launched environment, mark a screen reached, edit what complete() requires, delete the liveness
    guard's process, quiet its dead-game check or substitute the reset's target; expect() is the one way
    to name the screens a body will reach."""

    def __init__(self, run_id, prefix, bundles, install, display, arm="control", size="800x600x24",
                 experiment=None):
        object.__setattr__(self, "_engine", Engine(run_id, prefix, bundles, install, display, arm, size,
                                                   experiment=experiment))
        object.__setattr__(self, "_hooks", {})

    def __setattr__(self, name, value):
        raise AttributeError(f"a Session's attributes are read-only (here {name!r}); its state is its engine's")

    run_id = _view("run_id", "the run id, E004-rNNNN")
    args = _view("args", "the spike's arguments the engine runs with (arm, experiment, size, ...)")
    status = _view("status", "running, completed (published by finish() only, when complete() ran and the reset "
                             "restored the prefix) or aborted: <kind>: <reason>")
    recovered = _view("recovered", "True only when finish() ran every clean-up stage and the reset restored the prefix")
    body_complete = _view("body_complete", "True after complete() passed its checks: the provisional completion, "
                                           "which finish() turns into the status completed only when the reset "
                                           "restored the prefix (T13 round 6, R3)")
    elapsed = _view("elapsed", "seconds from the first seal to the end of the reset")
    obs = _view("obs", "the run/1 observations")
    outputs = _view("outputs", "(name, path, class) of the bundle files")
    started = _view("started", "the start time of execute()")
    ended = _view("ended", "the end time of execute()")
    procs = property(lambda self: types.MappingProxyType({name: _ProcView(name, proc)
                                                          for name, proc in self._engine.procs.items()}),
                     doc="the run's own processes by name (xvfb, wm, game), as read-only views: name, pid, "
                         "returncode and a dead/alive query, never the engine's process handles "
                         "(T13 round 6, R2)")
    env = _view("env", "the game side's environment (marked with the run and the side), as it was at this read")
    display_env = _view("display_env", "the display side's environment, as it was at this read")
    expected = _view("expected", "the known screens complete() requires the body to have reached (set through expect())")
    reached = _view("reached", "the known screens reached so far (established by wait_for_screen only)")
    step_no = _view("step_no", "the run/1 step of the last observation")
    snap_before = _view("snap_before", "the snapshot of the prefix before the launch (absent until it is taken)")
    window = _view("window", "the game window's id on this session's display, as start_game found it (absent "
                             "before the launch); the E020 watcher captures it (T38 round 2, R1)")

    # ---- the lifecycle

    @unguarded("starts the game: the seal before anything starts and again immediately before the launch, "
               "and the game and the display alive at the end of the launch (Engine.launch)")
    def start(self):
        """The seal, the display, the snapshot, the seal again, the launch."""
        self._engine.start()

    @unguarded("ends the game: the liveness at the point of terminating and of stopping the display is checked "
               "inside Engine.terminate and Engine.stop_x, and the clean-up runs whatever died")
    def finish(self):
        """Terminate, stop the display, snapshot and reset, keep the logs; sets `recovered` and publishes the
        status completed only when complete() ran and the reset restored the prefix (T13 round 6, R3)."""
        self._engine.finish()

    @unguarded("composes start(), the body (which calls guarded methods), complete() (guarded) and finish()")
    def execute(self, body):
        """start, body(session), complete, finish, with one status. Returns the status."""
        engine = self._engine
        started = now()
        try:
            self.start()
            body(self)
            self.complete()
        except DriverError as exc:
            # fail() recorded why. An error the body raised itself, without fail() (the E020 loop's
            # NotReady, T38 round 3, R1), is recorded with its own kind and reason; a first reason stays.
            engine._set_aborted(str(exc), type(exc))
        except BaseException as exc:               # a crash or an interruption: cleaned up, recorded, never completed
            engine.abort_later(f"{type(exc).__name__}: {exc}")
        self.finish()
        engine.started, engine.ended = started, now()
        return engine.status

    # ---- what touches the game: every one guarded

    @guarded("wait for a screen")
    def wait_for_screen(self, name, timeout=None, stable=True):
        """Wait, by pixels, until the named screen is up (and stable); see Engine.wait_for_screen."""
        return self._engine.wait_for_screen(name, timeout, stable)

    @guarded("the known screen")
    def known_screen(self):
        """The title screen, waited for by its pixels."""
        return self._engine.known_screen()

    @guarded("a step")
    def perform(self, text):
        """Steps in the E002 step language; StepFailed when one is refused or fails."""
        return self._engine.perform(text)

    @guarded("a screenshot observation")
    def observe_screenshot(self, name, step=None):
        """A screenshot of the whole display, kept as a bundle file."""
        return self._engine.observe_screenshot(name, step)

    @guarded("a region observation")
    def observe_region(self, rect, label):
        """sha256 of the raw pixels of x, y, w, h, as an observation."""
        return self._engine.observe_region(rect, label)

    @guarded("a screen reading")
    def screen_name(self):
        """The screen the game shows (screens.name_of): eliminated, game-over, board-menu, board, title or
        unknown."""
        return self._engine.screen_name()

    @guarded("a card-prompt reading")
    def screen_card_award(self):
        """True only for the bounded measured green card-prompt population; sends nothing."""
        return self._engine.screen_card_award()

    @guarded("a winner reading")
    def screen_winner(self):
        """The winning seat's colour word on the winner notice, or None (screens.winner_of; round 6)."""
        return self._engine.screen_winner()

    @guarded("a file observation")
    def observe_file(self, rel):
        """One file of the game copy, read in place."""
        return self._engine.observe_file(rel)

    @guarded("the cycle's end")
    def complete(self):
        """The only completion route of a session (Engine.complete says what it requires); it publishes the
        provisional body_complete, and finish() alone publishes the status completed (T13 round 6, R3)."""
        return self._engine.complete()

    # ---- what does not touch the game

    @unguarded("names the known screens the body will wait for; touches nothing itself. The set it fills is "
               "private engine state (T13 round 5, R2): a view of it is read-only, so no caller can narrow "
               "what complete() requires")
    def expect(self, *names):
        """Add the named known screens to those complete() requires the body to have reached."""
        for name in names:
            if name not in SCREENS:
                raise ValueError(f"{name!r} is not a known screen; the driver knows {sorted(SCREENS)}")
        self._engine.expected.update(names)

    @unguarded("a named point of the body: runs the hooks registered with on() and touches nothing itself; "
               "a hook that kills the game (an injected fault) is found by the next guarded method")
    def checkpoint(self, name):
        """A named point in the body where an injected fault (or a test) may act; see on()."""
        for hook in self._hooks.get(name, ()):
            self._engine.say(f"checkpoint {name}: {getattr(hook, '__name__', 'hook')}")
            hook(self)

    @unguarded("registers a hook; touches nothing")
    def on(self, name, hook):
        self._hooks.setdefault(name, []).append(hook)

    @unguarded("appends an observation to the record; touches nothing")
    def observe(self, step, source, field, value):
        self._engine.observe(step, source, field, value)

    @unguarded("reads whether the game process is alive; must answer after it died (the fault checks)")
    def game_alive(self):
        return self._engine.game_alive()

    @unguarded("reads /proc for the game's pid; must answer after it died (the fault checks)")
    def find_game_pid(self):
        return self._engine.find_game_pid()
