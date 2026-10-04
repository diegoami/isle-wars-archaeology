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
expects were reached, at least one input step of perform() succeeded, `before.png` was taken before the
first input and `after.png` after the last, and the game was alive at the end; then finish() must also
terminate, stop the display and reset the prefix without a fault. Every other way out is
"aborted: <kind>: <reason>" (the first reason; every later fault is an observation too), and the clean-up
stages and the reset run in both cases. `recovered` is True only when every clean-up stage succeeded and
the reset was shown to restore the prefix: a caller may start the next session only then.

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
        self.events = 0                              # a counter that orders the inputs and the screenshots
        self.actions = []                            # (event, op, line) of every input step that succeeded
        self.shot_at = {}                            # screenshot name -> event
        self.later_faults = []                       # every fault after the first, and every clean-up fault
        self.cleaned = {}                            # clean-up stage -> succeeded without a fault
        self.recovered = False                       # set by finish(): every clean-up stage succeeded

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
                self.fail(f"{name} could not be compared with its baseline ({when}): {exc}", SealError)
            if here != there:
                self.fail(f"{name} of the prefix is not the baseline's ({when}); something outside the driver changed "
                          "the prefix (the reset would not bring it back to this state)", SealError)
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
        return subprocess.Popen(["Xvfb", self.display, "-screen", "0", f"{width}x{height}x{depth}", "-nolisten", "tcp"],
                                env=self.display_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def display_is_ours(self, proc):
        """True only when this run's Xvfb is alive, itself holds the display's listening socket, and answers.
        A server of someone else's that answers on the same display is never taken for it."""
        if proc.poll() is not None:
            return False
        path = f"@/tmp/.X11-unix/X{self.display[1:]}"
        if not listening_socket_inodes(path) & socket_inodes_of(proc.pid):
            return False
        return spike.run(["xdpyinfo"], env=self.env).returncode == 0

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

    def checkpoint(self, name):
        """A named point in the body where an injected fault (or a test) may act; see on()."""
        for hook in self.hooks.get(name, ()):
            self.say(f"checkpoint {name}: {getattr(hook, '__name__', 'hook')}")
            hook(self)

    def on(self, name, hook):
        self.hooks.setdefault(name, []).append(hook)

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

    def observe_file(self, rel):
        """One file of the game copy, read in place: size, sha256 and whether it equals the install's."""
        self.step_no += 1
        self.read_game_file(rel)

    def complete(self):
        """The only place a session becomes completed: the body ran, the known screens it expects were
        reached, it acted (an input step of perform() succeeded), `before.png` was taken before its first
        input and `after.png` after its last, and the game was still alive."""
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
        items = [f"{MARK}={self.run_id}".encode(), f"{SIDE}={side}".encode()]
        for pid in self.alive(side):
            kill_marked(pid, items)

    def terminate(self):
        """`wineserver -k` (immediate, F002), then a bounded wait for the game side: no fixed wait, and no
        wait for the display side's daemons. A game side that is still there after the bound is killed, and
        a second bound ends in TerminateError. The exit status of `wineserver -k` is recorded, not relied on
        (it is 1 when no server is left, after a game that died); what is relied on is the game side gone."""
        self.say("wineserver -k")
        killed = spike.run([spike.WINESERVER, "-k"], env=self.env, timeout=WINESERVER_TIMEOUT)
        self.observe(9, "process", "wineserver -k exit status", killed.returncode)
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
            spike.run([spike.WINESERVER, "-k"], env=self.env, timeout=WINESERVER_TIMEOUT)
            self.kill_side("game")
            if self.wait_gone("game", AFTER_KILL_TIMEOUT) is None:
                self.fail(f"{len(self.alive('game'))} process(es) of the game side survived a kill", TerminateError)

    def check_before_terminate(self):
        """Class C, just before terminate: a game that died, or a display process that exited, since the last
        check makes the session aborted (the first reason is kept); the clean-up and the reset still run."""
        dead = self.display_dead()
        game_dead = "game" in self.procs and not self.game_alive()
        if game_dead:
            self._set_aborted(f"the game process exited before terminate (status {self.procs['game'].poll()})", GameDied)
        if dead:
            self._set_aborted(f"{' and '.join(dead)} exited before terminate", DisplayError)
        self.observe(9, "process", "game and display alive just before terminate",
                     "no: " + ", ".join((["game"] if game_dead else []) + dead) if game_dead or dead else "yes")

    def stop_own(self, proc, sig):
        """A signal to one of this run's display processes, through kill_marked (its markers re-checked)."""
        kill_marked(proc.pid, [f"{MARK}={self.run_id}".encode(), f"{SIDE}=display".encode()], sig)

    def stop_x(self):
        """Stop xfwm4 and Xvfb (SIGTERM, then SIGKILL after STOP_TIMEOUT), every wait bounded; then the
        display side's processes, then the check that nothing of this run is left. TerminateError otherwise."""
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
        before. The status is left aborted unless complete() ran and nothing here failed."""
        self.check_before_terminate()
        self.cleanup("terminate", self.terminate if "game" in self.procs else None, TerminateError)
        self.cleanup("stopping the display", self.stop_x, TerminateError)
        if hasattr(self, "snap_before"):
            self.cleanup("snapshot and reset", self.snapshot_and_reset, ResetError)
        self.cleanup("keeping the logs", self.keep_logs, RecordError)
        self.recovered = (all(self.cleaned.values())
                          and (not hasattr(self, "snap_before") or self.cleaned.get("snapshot and reset") is True))
        failed = [stage for stage, ok in self.cleaned.items() if not ok]
        self.observe(12, "process", "clean-up: every stage succeeded and the prefix was reset (the next session may start)",
                     "yes" if self.recovered else "no: " + ", ".join(failed or ["the reset did not run"]))
        for fault in self.later_faults:
            self.observe(12, "process", "a fault logged by abort_later (the status keeps only the first reason)", fault[:300])
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
