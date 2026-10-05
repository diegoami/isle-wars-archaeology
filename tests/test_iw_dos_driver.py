"""Tests of the DOS Isle Wars driver (T15): runtime/iw-dos/driver/.

They use T11's synthetic world (test_iw_dos_seal.World: a copy, a run directory and a known.json in a temporary
directory outside every checkout) and a fake game: Xvfb and DOSBox-X are FakeProc objects started through the real
procs.start, and the commands the driver runs (xdpyinfo, xdotool, ImageMagick's import, mount) are answered by
`fake_run` in place of subprocess.run, so the real procs.must, with its exit-status check, runs. Signals go through
a fake kill_marked that applies them to the FakeProc, except in ProcessIdentityTest, which uses real processes.

tests/mutants_iw_dos_driver.py removes each guarantee of T15's Done-when 3 in turn and shows these tests failing.
Every test runs under an alarm (WATCHDOG_S), so a wait that lost its bound fails instead of hanging.
"""
import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "runtime" / "iw-dos"))
import test_iw_dos_seal as seal  # noqa: E402

from driver import errors, procs, repeat, session as sessionlib  # noqa: E402

spike = sessionlib.spike
safeio = spike.safeio
REAL_RUN, REAL_POPEN = subprocess.run, subprocess.Popen
PROCS_KILL_MARKED = procs.kill_marked
WATCHDOG_S = 30
OX, OY = 80, 100
W, H = spike.GAME_SIZE


class Hang(BaseException):
    """The watchdog's alarm: a wait ran past every bound the test allows."""


def frame(state):
    """The game window's pixels in a state: the option box's colours, the Select level dialog's, or neither."""
    data = bytearray(W * H * 3)

    def paint(rect, colour):
        x, y, w, h = rect
        for row in range(y, y + h):
            for col in range(x, x + w):
                data[(row * W + col) * 3:(row * W + col) * 3 + 3] = bytes(colour)
    if state == "menu":
        paint(spike.SET_LEVEL_TEXT, spike.RED)
        paint(spike.CHOOSE_TEXT, spike.CYAN)
    elif state == "dialog":
        paint(spike.DIALOG_TITLE, spike.ORANGE)
    return bytes(data)


FRAMES = {state: frame(state) for state in ("menu", "dialog", "black")}


class FakeProc:
    next_pid = 4_000_000

    def __init__(self, cmd, env):
        FakeProc.next_pid += 1
        self.pid, self.cmd, self.env = FakeProc.next_pid, cmd, env
        self.returncode = None
        self.ignore_term = False

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        if self.returncode is None:
            raise subprocess.TimeoutExpired(self.cmd, timeout)
        return self.returncode

    def carries(self, items):
        entries = [f"{k}={v}".encode() for k, v in self.env.items()]
        return self.returncode is None and all(i in entries for i in items)


FAKE_COMMANDS = ("xdpyinfo", "xdotool", "import", "mount")


class FakeCommand:
    """A helper command (procs.must) answered by DriverWorld.fake_run."""
    next_pid = 5_000_000

    def __init__(self, done):
        FakeCommand.next_pid += 1
        self.pid, self.done, self.returncode = FakeCommand.next_pid, done, None

    def communicate(self, timeout=None):
        self.returncode = self.done.returncode
        return self.done.stdout, self.done.stderr


class DriverWorld(seal.World):
    """A session over the synthetic world, with the fake game."""

    def setUp(self):
        super().setUp()
        self.game_dir = self.sync()
        self.work = self.tmp / "work"
        self.work.mkdir()
        os.environ["E006_BUNDLES"] = str(self.bundles)
        self.state = "menu"          # what the fake game shows
        self.pointer = 0
        self.fail_commands = {}      # ("xdotool", "click") -> exit status
        self.on_command = {}         # ("xdotool", "click") -> callable run before the answer
        self.started = []            # FakeProcs
        self.signals = []            # (pid, signal) applied
        self.netns = "net:[inner]"
        self.writable = False
        self.dosbox_running = []
        self.display_held = True
        self.between_seals = None
        self.commands = []
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        for target, name, value in ((subprocess, "run", self.fake_run), (subprocess, "Popen", self.fake_popen),
                                    (procs, "kill_marked", self.fake_kill), (procs, "marked_pids", self.fake_marked),
                                    (procs, "program_pids", lambda name: list(self.dosbox_running)),
                                    (procs, "listening_socket_inodes", lambda path: {7} if self.held() else set()),
                                    (procs, "socket_inodes_of", lambda pid: {7} if self.held() else set()),
                                    (spike, "netns_of", lambda pid: self.netns),
                                    (spike, "interfaces_of", lambda pid: ["lo"]),
                                    (spike, "install_writable", lambda path: self.writable),
                                    (time, "sleep", lambda s: None)):
            stack.enter_context(mock.patch.object(target, name, value))
        stack.enter_context(redirect_stdout(io.StringIO()))
        original = sessionlib._Core._start_display

        def start_display(session):
            original(session)
            if self.between_seals:
                self.between_seals(session)
        stack.enter_context(mock.patch.object(sessionlib._Core, "_start_display", start_display))
        signal.signal(signal.SIGALRM, self._alarm)
        signal.alarm(WATCHDOG_S)
        self.addCleanup(signal.alarm, 0)
        self.baseline = spike.snapshot_tree(self.game_dir)

    @staticmethod
    def _alarm(*_):
        raise Hang("the watchdog's alarm: a wait did not end within its bound")

    # ---- the fake game and display

    def held(self):
        xvfb = [p for p in self.started if p.cmd[0] == "Xvfb"]
        return bool(xvfb) and xvfb[-1].returncode is None and self.display_held

    def game(self):
        found = [p for p in self.started if p.cmd[0] == "dosbox-x"]
        return found[-1] if found else None

    def fake_popen(self, cmd, *args, **kw):
        if cmd and cmd[0] in ("Xvfb", "dosbox-x"):
            proc = FakeProc(cmd, kw.get("env") or {})
            self.started.append(proc)
            return proc
        if cmd and cmd[0] in FAKE_COMMANDS:
            return FakeCommand(self.fake_run(cmd))
        return REAL_POPEN(cmd, *args, **kw)

    def fake_run(self, cmd, *args, **kw):
        key = tuple(cmd[:2])
        if cmd[0] not in FAKE_COMMANDS:
            return REAL_RUN(cmd, *args, **kw)
        self.commands.append(list(cmd))
        if key in self.on_command:
            self.on_command[key]()
        code = self.fail_commands.get(key, self.fail_commands.get((cmd[0],), 0))
        out = b""
        game = self.game()
        if code == 0:
            if key == ("xdotool", "search"):
                if game is None or game.returncode is not None:
                    return subprocess.CompletedProcess(cmd, 1, b"", b"")
                out = b"4242\n"
            elif key == ("xdotool", "getwindowgeometry"):
                out = f"Window 4242\n  Position: {OX},{OY} (screen: 0)\n  Geometry: {W}x{H}\n".encode()
            elif key == ("xdotool", "mousemove"):
                self.pointer += 1
            elif key == ("xdotool", "click") and self.state == "menu":
                self.state = "dialog"
            elif cmd[0] == "import":
                out = self.capture(cmd)
        return subprocess.CompletedProcess(cmd, code, out, b"failed" if code else b"")

    def capture(self, cmd):
        geometry = cmd[cmd.index("-crop") + 1]
        size, x, y = geometry.split("+")
        w, h = map(int, size.split("x"))
        x, y = int(x) - OX, int(y) - OY
        pixels = bytearray(FRAMES[self.state])
        if self.pointer % 2:
            pixels[-3:] = b"\xff\xff\xff"
        data = b"".join(bytes(pixels[((y + r) * W + x) * 3:((y + r) * W + x + w) * 3]) for r in range(h))
        return data[:-3] if getattr(self, "short_capture", False) else data

    def fake_kill(self, pid, items, sig=signal.SIGKILL):
        if not items:
            raise ValueError("kill_marked needs the markers the process must carry")
        for proc in self.started:
            if proc.pid == pid and proc.carries(items):
                self.signals.append((proc.cmd[0], sig))
                if sig == signal.SIGTERM and not proc.ignore_term:
                    proc.returncode = 0
                elif sig == signal.SIGKILL:
                    proc.returncode = -9
                return True
        return False

    def fake_marked(self, items):
        return [p.pid for p in self.started if p.carries(items)]

    # ---- sessions

    def make(self, run_id="E006-r9001", display=":61", workdir=None):
        if workdir is None:
            self.made_count = getattr(self, "made_count", 0) + 1
            workdir = self.tmp / f"work{self.made_count}"
            workdir.mkdir()
        made = sessionlib.Session(run_id, self.run_dir, self.install, workdir, display, self.baseline,
                                  "tok123", "net:[outer]")
        return made

    def started_session(self):
        made = self.make()
        made.start()
        return made

    def kill_game(self, code=-9):
        self.game().returncode = code


class StructureTest(DriverWorld):
    """The guard and the helpers are in one place each, and every path goes through them."""

    def test_the_session_s_whole_callable_surface_is_the_guarded_api(self):
        """Every public callable reachable on Session, its MRO included (dir, not vars), is a PUBLIC method with
        its guard; the spike is not among its bases (PR #74 R2, R3)."""
        self.assertEqual(sessionlib.Session.__mro__, (sessionlib.Session, object))
        made = self.make()
        for target in (sessionlib.Session, made):
            public = {n for n in dir(target) if not n.startswith("_") and callable(getattr(target, n))}
            self.assertEqual(public, set(sessionlib.PUBLIC), target)
        for name, modes in sessionlib.PUBLIC.items():
            self.assertEqual(getattr(getattr(sessionlib.Session, name), "guard", None), modes, name)

    def test_every_public_callable_of_the_adapter_is_used_or_blocked(self):
        """The adapter's whole public surface, its MRO included: each name in exactly one of CORE_USED and BLOCKED."""
        core = sessionlib._Core
        public = {n for n in dir(core) if not n.startswith("_") and callable(getattr(core, n))}
        used, blocked = set(sessionlib.CORE_USED), set(sessionlib.BLOCKED)
        self.assertEqual(used & blocked, set())
        self.assertEqual(public, used | blocked)

    def test_every_blocked_spike_method_refuses_and_sends_nothing(self):
        made = self.started_session()
        core = made._core
        sent, signals = len(self.commands), len(self.signals)
        for name in sessionlib.BLOCKED:
            with self.subTest(name), self.assertRaises(errors.DriverError):
                getattr(core, name)("s")
        self.assertEqual((len(self.commands), len(self.signals)), (sent, signals))
        self.assertIsNone(self.game().returncode)
        made.finish()

    def test_no_spike_method_the_adapter_uses_runs_a_command_waits_or_signals_by_itself(self):
        """Each CORE_USED method that the adapter inherits unchanged from the spike sends its commands only through
        self.sh and waits only through self.wait_until: no call of the spike's run(), poll() or popen(), and no
        send_signal, kill or terminate (PR #74 R3)."""
        import ast
        import inspect
        for name in sessionlib.CORE_USED:
            owner = next(k for k in sessionlib._Core.__mro__ if name in vars(k))
            if owner is not spike.Cycle:
                continue
            tree = ast.parse(inspect.cleandoc("\n" + inspect.getsource(getattr(spike.Cycle, name))))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    bad = ((isinstance(func, ast.Name) and func.id in ("run", "poll", "popen", "run_namespace"))
                           or (isinstance(func, ast.Attribute) and func.attr in ("send_signal", "kill", "terminate")))
                    self.assertFalse(bad, f"the spike's {name} calls {ast.unparse(func)} by itself")

    def test_no_driver_module_runs_a_command_or_sends_a_signal_but_procs(self):
        import ast
        for path in sorted((ROOT / "runtime/iw-dos/driver").glob("*.py")):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    name = node.attr
                    owner = node.value.id if isinstance(node.value, ast.Name) else ""
                    bad = ((owner == "subprocess" and name in ("run", "call", "check_call", "check_output", "Popen"))
                           or (owner == "os" and name in ("kill", "killpg", "system", "popen"))
                           or name in ("send_signal", "terminate") or (owner == "signal" and name == "pidfd_send_signal"))
                    allowed = path.name == "procs.py" or (path.name == "repeat.py" and name == "Popen")
                    self.assertFalse(bad and not allowed, f"{path.name}:{node.lineno} uses {owner}.{name}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "kill" \
                        and not (isinstance(node.func.value, ast.Name) and node.func.value.id == "procs"):
                    self.fail(f"{path.name}:{node.lineno} calls .kill()")

    def test_the_spike_s_unchecked_run_is_never_used_on_the_driver_s_path(self):
        with mock.patch.object(spike, "run", side_effect=AssertionError("the spike's unchecked run() was used")):
            made = self.make()
            made.execute(repeat.set_level_cycle)
        self.assertEqual(made.status, "completed")


class GuardTest(DriverWorld):
    """The liveness guard of every public method and step (Done-when 3, first item)."""

    CALLS = {
        "wait_for_screen": lambda s: s.wait_for_screen("option-box"),
        "perform": lambda s: s.perform("click 60 32"),
        "observe_screenshot": lambda s: s.observe_screenshot("before.png"),
        "observe_region": lambda s: s.observe_region("box", (0, 0, 4, 4)),
        "observe_file": lambda s: s.observe_file("ISLEWAR.SCR"),
        "complete": lambda s: s.complete(),
    }

    def test_a_good_cycle_completes(self):
        made = self.make()
        made.execute(repeat.set_level_cycle)
        self.assertEqual((made.status, made.recovered), ("completed", True))
        self.assertEqual(made._core.inputs_sent, 1)

    def test_every_public_method_raises_game_died_when_the_game_is_gone_before_it(self):
        for name, call in self.CALLS.items():
            with self.subTest(name):
                made = self.started_session()
                self.kill_game()
                commands = len(self.commands)
                with self.assertRaises(errors.GameDied):
                    call(made)
                self.assertEqual(self.commands[commands:], [], f"{name} sent a command to a dead game")
                made.finish()

    def test_every_public_method_raises_display_died_when_the_display_is_gone(self):
        for name, call in self.CALLS.items():
            with self.subTest(name):
                self.display_held = True
                made = self.started_session()
                self.display_held = False
                with self.assertRaises(errors.DisplayDied):
                    call(made)
                made.finish()

    def test_a_game_that_dies_during_a_public_method_is_found_after_it(self):
        def die_during(name, call):
            made = self.started_session()
            made.wait_for_screen("option-box") if name != "wait_for_screen" else None
            if name == "complete":
                made.observe_screenshot("before.png")
                made.perform("click 60 32")
                made.observe_screenshot("after.png")
            # the game dies inside the method, after its last capture or command
            original = spike.Cycle.observe

            def observe(self_, *a):
                original(self_, *a)
                if self.game().returncode is None:
                    self.kill_game()
            with mock.patch.object(spike.Cycle, "observe", observe):
                with self.assertRaises(errors.GameDied):
                    call(made)
            made.finish()
        for name, call in self.CALLS.items():
            if name == "complete":
                continue          # it captures and sends nothing; its after-check is the same code as the others'
            with self.subTest(name):
                self.state = "menu"
                die_during(name, call)

    def test_start_runs_once(self):
        made = self.started_session()
        with self.assertRaises(errors.SealError):
            made.start()
        made.finish()

    def test_finish_leaves_no_process_of_the_run_alive_or_says_so(self):
        made = self.make()
        with mock.patch.object(sessionlib._Core, "_stop_display", lambda self_: None):
            made.execute(repeat.set_level_cycle)
        self.assertTrue(made.status.startswith("aborted: terminate: "), made.status)
        self.assertIn("alive after finish", made.status)
        self.assertFalse(made.recovered)

    def test_a_step_is_checked_before_it_runs(self):
        made = self.started_session()
        made.wait_for_screen("option-box")
        self.on_command[("xdotool", "click")] = self.kill_game
        with self.assertRaises(errors.GameDied):
            made.perform("click 60 32\nclick 100 32")
        clicks = [c for c in self.commands if c[:2] == ["xdotool", "click"]]
        self.assertEqual(len(clicks), 1, "the second step was sent to a dead game")
        done = [o for o in made.observations if o["field"] == "step done, seconds after launch"]
        self.assertEqual(done, [], "a step the game died in was recorded as done")
        made.finish()

    def test_a_process_of_another_invocation_is_never_signalled_even_with_the_same_run_id(self):
        made = self.make()
        other = FakeProc(["dosbox-x"], {procs.INVOCATION: "another-command", procs.MARK: made.run_id,
                                        procs.SIDE: "game"})
        self.started.insert(0, other)
        made.execute(repeat.set_level_cycle)
        self.assertEqual(made.status, "completed")
        self.assertIsNone(other.returncode, "another command's process was signalled")

    def test_a_game_that_dies_between_two_steps_is_sent_nothing_more(self):
        made = self.started_session()
        made.wait_for_screen("option-box")
        original = spike.Cycle.observe

        def observe(self_, step, source, field, value):
            original(self_, step, source, field, value)
            if field == "step done, seconds after launch":
                self.kill_game()
        with mock.patch.object(spike.Cycle, "observe", observe):
            sent = len(self.commands)
            with self.assertRaises(errors.GameDied):
                made.perform("wait-stable\nfiles")
        self.assertEqual([c for c in self.commands[sent:] if c[0] == "xdotool"], [],
                         "a command of step 2 was sent to a dead game")
        self.assertEqual([o for o in made.observations if o["field"].startswith("run copy at step 2")], [],
                         "step 2 ran on a dead game")
        made.finish()

    def test_a_public_method_does_not_run_at_all_on_a_dead_game(self):
        """The guard's before-check, beyond the dispatch's: observe_file sends no command, and must not run."""
        made = self.started_session()
        self.kill_game()
        with self.assertRaises(errors.GameDied):
            made.observe_file("ISLEWAR.EXE")
        self.assertEqual([o for o in made.observations if o["field"].startswith("run copy file")], [])
        made.finish()

    def test_a_wait_checks_the_game_on_every_poll(self):
        made = self.started_session()
        self.state = "black"
        polls = []

        def condition():
            polls.append(1)
            if len(polls) == 3:
                self.kill_game()
            return False
        with self.assertRaises(errors.GameDied):
            made._core.wait_until(condition, 25)
        self.assertEqual(len(polls), 3)
        made.finish()

    def test_a_failure_while_the_game_died_is_reported_as_its_death(self):
        made = self.started_session()
        self.state = "black"
        with mock.patch.object(sessionlib._Core, "wait_until", lambda self_, c, t, i=0.1: self.kill_game()):
            with self.assertRaises(errors.GameDied):
                made.wait_for_screen("option-box")
        made.finish()


class InputGateTest(DriverWorld):
    """An input reaches the game only through a step of perform(), with the notice guard on (PR #74 R1)."""

    def ready(self):
        made = self.started_session()
        made.wait_for_screen("option-box")
        return made, made._core

    def test_an_input_outside_a_step_is_refused_and_not_counted(self):
        made, core = self.ready()
        for cmd in (["xdotool", "mousemove", "140", "132"], ["xdotool", "click", "1"], ["xdotool", "key", "Return"]):
            with self.subTest(cmd):
                sent = len(self.commands)
                with self.assertRaises(errors.StepFailed):
                    core.sh(cmd)
                self.assertEqual(self.commands[sent:], [])
        with self.assertRaises(errors.StepFailed):
            core.step_key(101, "Return")
        self.assertEqual(core.inputs_sent, 0)
        made.finish()

    def test_a_click_or_a_key_is_refused_at_the_dispatch_while_the_notices_are_up(self):
        made, core = self.ready()
        core.in_step, core.pointer_at = True, (60, 32)
        with mock.patch.object(core.screen, "notice_up", return_value=True):
            for cmd in (["xdotool", "click", "1"], ["xdotool", "key", "Return"]):
                with self.subTest(cmd), self.assertRaises(errors.StepFailed):
                    core.sh(cmd)
            core.sh(["xdotool", "key", "c"])
        self.assertEqual([c for c in self.commands if c[:2] == ["xdotool", "click"]], [])
        made.finish()

    def test_a_click_on_a_forbidden_point_or_off_the_window_is_refused_at_the_dispatch(self):
        made, core = self.ready()
        core.in_step = True
        for point in ((300, 300), (420, 295), (700, 10), None):
            with self.subTest(point), self.assertRaises(errors.StepFailed):
                core.pointer_at = point
                core.sh(["xdotool", "click", "1"])
        self.assertEqual([c for c in self.commands if c[:2] == ["xdotool", "click"]], [])
        made.finish()

    def test_a_key_outside_the_grammar_and_any_other_xdotool_command_are_refused(self):
        made, core = self.ready()
        core.in_step = True
        for cmd in (["xdotool", "key", "u"], ["xdotool", "key", "r"], ["xdotool", "keydown", "F12"],
                    ["xdotool", "windowkill", "4242"], ["xdotool", "type", "x"]):
            with self.subTest(cmd), self.assertRaises(errors.StepFailed):
                core.sh(cmd)
        self.assertEqual([c for c in self.commands if c[0] == "xdotool" and c[1] not in ("search", "getwindowgeometry")],
                         [])
        made.finish()

    def test_a_command_to_a_dead_game_is_refused_at_the_dispatch(self):
        made, core = self.ready()
        self.kill_game()
        sent = len(self.commands)
        with self.assertRaises(errors.GameDied):
            core.sh(["import", "-window", "root", "-crop", "4x4+80+100", "+repage", "-depth", "8", "rgb:-"])
        self.assertEqual(self.commands[sent:], [])
        made.finish()


class CommandTest(DriverWorld):
    """The subprocess helper's exit-status check (Done-when 3, second item)."""

    def test_must_raises_on_a_non_zero_exit_and_returns_on_zero(self):
        with self.assertRaises(errors.CommandFailed):
            procs.must(["sh", "-c", "exit 3"])
        with self.assertRaises(errors.CommandFailed):
            procs.must(["sh", "-c", "echo found; exit 1"], miss_ok=True)
        self.assertIsNone(procs.must(["sh", "-c", "exit 1"], miss_ok=True))
        self.assertEqual(procs.must(["sh", "-c", "echo ok"]).stdout, b"ok\n")

    def test_every_command_of_the_cycle_that_fails_aborts_the_repeat(self):
        for key in (("xdotool", "click"), ("xdotool", "mousemove"), ("xdotool", "getwindowgeometry"),
                    ("import",), ("xdpyinfo",)):
            with self.subTest(key):
                self.state, self.fail_commands = "menu", {key: 1}
                for name in os.listdir(self.work):
                    safeio.remove(self.work, name)
                made = self.make()
                made.execute(repeat.set_level_cycle)
                self.assertTrue(made.status.startswith("aborted: command-failed: "), made.status)
                self.assertTrue(made.recovered)

    def test_a_capture_of_the_wrong_size_aborts_the_repeat(self):
        self.short_capture = True
        made = self.make()
        made.execute(repeat.set_level_cycle)
        self.assertTrue(made.status.startswith("aborted: command-failed: a capture of"), made.status)

    def test_a_failed_click_is_not_an_input(self):
        self.fail_commands = {("xdotool", "click"): 1}
        made = self.make()
        made.execute(repeat.set_level_cycle)
        self.assertEqual(made._core.inputs_sent, 0)


class SealSymmetryTest(DriverWorld):
    """Every check of the first seal runs again immediately before the launch (Done-when 3, fourth item)."""

    def damage(self, check):
        def run_copy(_):
            os.link(self.game_dir / "ISLEWAR.EXE", self.tmp / "second-name")

        def baseline(_):
            path = self.game_dir / "ISLEWAR.DAT"
            os.utime(path, ns=(path.stat().st_atime_ns, path.stat().st_mtime_ns + 10 ** 9))

        def configuration(session):
            text = (session.workdir / "dosbox.conf").read_text().replace("@echo off\n", "@echo off\nmount d /\n")
            safeio.write_file(session.workdir, "dosbox.conf", data=text.encode(), exist="replace")
        return {"install-read-only": lambda _: setattr(self, "writable", True),
                "network-namespace": lambda _: setattr(self, "netns", "net:[outer]"),
                "run-copy": run_copy, "baseline": baseline, "configuration": configuration,
                "no-dosbox-x": lambda _: self.dosbox_running.append(99)}[check]

    def test_each_check_is_made_again_immediately_before_the_launch(self):
        for check in sessionlib.SEAL_CHECKS:
            with self.subTest(check):
                self.writable, self.netns, self.dosbox_running[:] = False, "net:[inner]", []
                (self.game_dir / "ISLEWAR.DAT").unlink()
                self.sync()
                for name in os.listdir(self.work):
                    safeio.remove(self.work, name)
                with contextlib.suppress(FileNotFoundError):
                    (self.tmp / "second-name").unlink()
                self.between_seals = self.damage(check)
                made = self.make()
                with self.assertRaises(errors.SealError) as caught:
                    made.start()
                self.assertTrue(str(caught.exception).startswith(f"{check} (immediately before launch)"),
                                str(caught.exception))
                self.assertIsNone(self.game(), "DOSBox-X was started")
                made.finish()

    def test_the_six_checks_are_the_ones_named(self):
        self.assertEqual(set(sessionlib.SEAL_CHECKS), {"install-read-only", "network-namespace", "run-copy",
                                                       "baseline", "configuration", "no-dosbox-x"})

    def test_each_check_also_refuses_at_the_start(self):
        for check in sessionlib.SEAL_CHECKS:
            with self.subTest(check):
                self.writable, self.netns, self.dosbox_running[:] = False, "net:[inner]", []
                (self.game_dir / "ISLEWAR.DAT").unlink()
                self.sync()
                for name in os.listdir(self.work):
                    safeio.remove(self.work, name)
                with contextlib.suppress(FileNotFoundError):
                    (self.tmp / "second-name").unlink()
                made = self.make()
                made._core.write_conf()
                self.damage(check)(made._core)
                with self.assertRaises(errors.SealError) as caught:
                    made._core._seal("at the start", 0)
                self.assertTrue(str(caught.exception).startswith(f"{check} (at the start)"), str(caught.exception))

    def test_a_display_not_held_by_this_run_s_xvfb_is_refused_before_the_launch(self):
        self.between_seals = lambda _: setattr(self, "display_held", False)
        made = self.make()
        with self.assertRaises(errors.SealError):
            made.start()
        self.assertIsNone(self.game())
        made.finish()

    def test_a_display_already_held_is_refused_before_xvfb_starts(self):
        made = self.make()
        with mock.patch.object(procs, "listening_socket_inodes", lambda path: {9}), \
                self.assertRaises(errors.DisplayError):
            made.start()
        self.assertEqual(self.started, [])


class CompletedTest(DriverWorld):
    """`completed` needs a successful input, the before-state and the reset (Done-when 3, fifth item)."""

    def test_a_body_without_an_input_is_never_completed(self):
        def body(session):
            session.wait_for_screen("option-box")
            session.observe_screenshot("before.png")
            session.observe_screenshot("after.png")
        made = self.make()
        made.execute(body)
        self.assertTrue(made.status.startswith("aborted: step-failed: "), made.status)
        self.assertIn("an input whose command succeeded", made.status)

    def test_a_before_shot_after_an_input_or_without_a_known_screen_is_not_the_before_state(self):
        def late(session):
            session.wait_for_screen("option-box")
            session.perform("click 60 32")
            session.observe_screenshot("before.png")
            session.observe_screenshot("after.png")

        def unseen(session):
            session.observe_screenshot("before.png")
            session.perform("click 60 32")
            session.observe_screenshot("after.png")
        for body in (late, unseen):
            with self.subTest(body.__name__):
                self.state = "menu"
                for name in os.listdir(self.work):
                    safeio.remove(self.work, name)
                made = self.make()
                made.execute(body)
                self.assertIn("before.png at a known screen before any input", made.status)

    def test_a_before_shot_captured_before_the_screen_was_reached_is_not_the_before_state(self):
        """PR #74 R5: a black capture, then the option box, an input and after.png."""
        def body(session):
            self.state = "black"
            session.observe_screenshot("before.png")
            self.state = "menu"
            session.wait_for_screen("option-box")
            session.perform("click 60 32")
            session.wait_for_screen("select-level")
            session.observe_screenshot("after.png")
        made = self.make()
        made.execute(body)
        self.assertNotEqual(made.status, "completed")
        self.assertIn("before.png at a known screen before any input", made.status)

    def test_a_before_shot_that_does_not_show_the_screen_reached_is_not_the_before_state(self):
        def body(session):
            session.wait_for_screen("option-box")
            self.state = "black"              # the screen changed after it was reached, with no input
            session.observe_screenshot("before.png")
            self.state = "menu"
            session.perform("click 60 32")
            session.wait_for_screen("select-level")
            session.observe_screenshot("after.png")
        made = self.make()
        made.execute(body)
        self.assertIn("before.png showing option-box", made.status)

    def test_an_after_shot_needs_a_screen_reached_after_the_last_input_and_showing_it(self):
        def no_wait(session):
            session.wait_for_screen("option-box")
            session.observe_screenshot("before.png")
            session.perform("click 60 32")
            session.observe_screenshot("after.png")

        def not_shown(session):
            session.wait_for_screen("option-box")
            session.observe_screenshot("before.png")
            session.perform("click 60 32")
            session.wait_for_screen("select-level")
            self.state = "black"
            session.observe_screenshot("after.png")
        for body, words in ((no_wait, "after.png at a known screen after the last input"),
                            (not_shown, "after.png showing select-level")):
            with self.subTest(body.__name__):
                self.state = "menu"
                made = self.make()
                made.execute(body)
                self.assertIn(words, made.status)

    def test_the_game_killed_at_the_entry_to_terminate_is_not_completed(self):
        made = self.make()
        original = sessionlib._Core._terminate

        def killed_first(self_):
            self.kill_game()
            original(self_)
        with mock.patch.object(sessionlib._Core, "_terminate", killed_first):
            made.execute(repeat.set_level_cycle)
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)

    def test_a_game_that_ends_otherwise_than_by_sigterm_is_not_completed(self):
        made = self.make()
        original = self.fake_kill

        def kill(pid, items, sig=signal.SIGKILL):
            sent = original(pid, items, sig)
            if sig == signal.SIGTERM and self.game().returncode == 0:
                self.game().returncode = 1        # as if its X client had been closed meanwhile
            return sent
        with mock.patch.object(procs, "kill_marked", kill):
            made.execute(repeat.set_level_cycle)
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)


class ResetTest(DriverWorld):
    """The reset runs after an aborted repeat too, and the next one starts from the baseline (third-last item)."""

    def test_an_aborted_repeat_is_reset_and_the_next_one_completes(self):
        def body(session):
            session.wait_for_screen("option-box")
            (self.game_dir / "ISLEWAR.SCR").write_bytes(b"written by the game")
            session.observe_screenshot("before.png")
            self.kill_game()
            session.perform("click 60 32")
        made = self.make()
        made.execute(body)
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)
        self.assertTrue(made.recovered)
        self.assertEqual(spike.snapshot_tree(self.game_dir), self.baseline)
        self.state = "menu"
        (self.tmp / "w2").mkdir()
        again = self.make(run_id="E006-r9002", display=":62", workdir=self.tmp / "w2")
        again.execute(repeat.set_level_cycle)
        self.assertEqual(again.status, "completed")

    def test_a_reset_that_never_showed_the_baseline_is_not_recovery(self):
        made = self.make()
        with mock.patch.object(sessionlib._Core, "_snapshot_and_reset", lambda self_: None):
            made.execute(repeat.set_level_cycle)
        self.assertNotEqual(made.status, "completed")
        self.assertFalse(made.recovered)

    def test_a_reset_that_cannot_restore_the_baseline_is_not_recovered(self):
        made = self.make()
        with mock.patch.object(spike.rundir, "sync", lambda env: None):
            def body(session):
                repeat.set_level_cycle(session)
                (self.game_dir / "ISLEWAR.SCR").write_bytes(b"x")
            made.execute(body)
        self.assertTrue(made.status.startswith("aborted: reset: "), made.status)
        self.assertFalse(made.recovered)


class BoundTest(DriverWorld):
    """Every wait has a bound (Done-when 3, last item); the watchdog fails a test whose wait has lost it."""

    def test_wait_until_returns_none_at_its_bound(self):
        made = self.started_session()
        t0 = time.monotonic()
        self.assertIsNone(made._core.wait_until(lambda: False, 0.3, 0.01))
        self.assertLess(time.monotonic() - t0, 5)
        made.finish()

    def test_a_screen_that_never_comes_is_screen_not_reached(self):
        made = self.started_session()
        self.state = "black"
        with mock.patch.dict(sessionlib.SCREENS, {"option-box": (sessionlib.SCREENS["option-box"][0], 0.3)}):
            with self.assertRaises(errors.ScreenNotReached):
                made.wait_for_screen("option-box")
        made.finish()

    def test_an_xvfb_that_never_holds_its_display_is_a_display_error(self):
        self.display_held = False
        made = self.make()
        with mock.patch.object(sessionlib, "XVFB_S", 0.3), self.assertRaises(errors.DisplayError):
            made.start()
        self.assertIsNone(self.game())
        made.finish()

    def test_a_window_that_never_shows_is_a_launch_error(self):
        made = self.make()
        original = self.fake_run

        def no_window(cmd, *a, **kw):
            if cmd[:2] == ["xdotool", "search"]:
                return subprocess.CompletedProcess(cmd, 1, b"", b"")
            return original(cmd, *a, **kw)
        with mock.patch.object(self, "fake_run", no_window), mock.patch.object(sessionlib, "WINDOW_S", 0.3), \
                self.assertRaises(errors.LaunchError):
            made.start()
        made.finish()

    def test_a_command_past_its_bound_is_stopped(self):
        t0 = time.monotonic()
        with self.assertRaises(errors.CommandFailed):
            procs.must(["sleep", "20"], timeout=0.3)
        self.assertLess(time.monotonic() - t0, 10)

    def test_a_command_past_its_bound_is_killed_through_kill_marked_with_its_own_marker(self):
        """PR #74 R4: never subprocess's own kill, never a signal by pid."""
        sent = []

        def spy(pid, items, sig=signal.SIGKILL):
            sent.append((pid, items, sig))
            return PROCS_KILL_MARKED(pid, items, sig)
        forbidden = AssertionError("a signal outside kill_marked")
        with mock.patch.object(procs, "kill_marked", spy), \
                mock.patch.object(REAL_POPEN, "kill", side_effect=forbidden), \
                mock.patch.object(REAL_POPEN, "terminate", side_effect=forbidden), \
                mock.patch.object(REAL_POPEN, "send_signal", side_effect=forbidden), \
                mock.patch.object(os, "kill", side_effect=forbidden), self.assertRaises(errors.CommandFailed):
            procs.must(["sleep", "20"], timeout=0.3)
        self.assertEqual(len(sent), 1)
        pid, items, sig = sent[0]
        self.assertEqual(sig, signal.SIGKILL)
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0].startswith(procs.COMMAND.encode() + b"="))
        self.assertFalse(os.path.exists(f"/proc/{pid}"), "the command was not reaped")

    def test_every_helper_command_carries_a_marker_of_its_own(self):
        first = procs.must(["sh", "-c", f"echo ${procs.COMMAND}"]).stdout.strip()
        second = procs.must(["sh", "-c", f"echo ${procs.COMMAND}"]).stdout.strip()
        self.assertEqual(len(first), 16)
        self.assertNotEqual(first, second)

    def test_a_game_that_ignores_sigterm_is_killed_and_reported(self):
        made = self.make()
        with mock.patch.object(sessionlib, "TERM_S", 0.3):
            def body(session):
                repeat.set_level_cycle(session)
                self.game().ignore_term = True
            made.execute(body)
        self.assertTrue(made.status.startswith("aborted: terminate: "), made.status)
        self.assertEqual(self.game().returncode, -9)

    def test_an_xvfb_that_ignores_sigterm_is_killed(self):
        made = self.make()
        with mock.patch.object(sessionlib, "STOP_S", 0.3):
            def body(session):
                repeat.set_level_cycle(session)
                session._core.procs["xvfb"].ignore_term = True
            made.execute(body)
        self.assertEqual(made._core.procs["xvfb"].returncode, -9)
        self.assertEqual(made.status, "completed")

    def test_the_command_is_killed_at_its_bound(self):
        env = dict(os.environ, **{procs.INVOCATION: "bound-test"})
        t0 = time.monotonic()
        with redirect_stderr(io.StringIO()), mock.patch.object(repeat, "REAP_BOUND", 2):
            code = repeat.launch_inner(["sleep", "20"], env, 0.3)
        self.assertEqual(code, 1)
        self.assertLess(time.monotonic() - t0, 10)


def sleeper(env_extra):
    return REAL_POPEN(["sleep", "30"], env=dict(os.environ, **env_extra))


class ProcessIdentityTest(unittest.TestCase):
    """Signals reach only this invocation's processes, re-checked through a pidfd (Done-when 3, third item).
    Real processes, real /proc."""

    def setUp(self):
        self.procs = []
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for proc in self.procs:
            if proc.poll() is None:
                proc.kill()
            proc.wait()

    def spawn(self, **env):
        proc = sleeper(env)
        self.procs.append(proc)
        deadline = time.monotonic() + 5
        while not procs.environ_has(proc.pid, [procs.item(k, v) for k, v in env.items()]):
            if time.monotonic() > deadline:
                self.fail("the child's environment never showed its markers")
            time.sleep(0.01)
        return proc

    def test_a_process_without_the_markers_is_never_signalled(self):
        other = self.spawn(**{procs.INVOCATION: "someone-else", procs.MARK: "E006-r0001"})
        self.assertFalse(procs.kill_marked(other.pid, [procs.item(procs.INVOCATION, "mine")]))
        time.sleep(0.1)
        self.assertIsNone(other.poll())
        mine = self.spawn(**{procs.INVOCATION: "mine"})
        self.assertTrue(procs.kill_marked(mine.pid, [procs.item(procs.INVOCATION, "mine")]))
        self.assertEqual(mine.wait(5), -signal.SIGKILL)

    def test_the_markers_are_checked_through_a_pidfd_opened_first_and_the_signal_goes_through_it(self):
        order = []
        real_open = os.pidfd_open
        proc = self.spawn(**{procs.INVOCATION: "mine"})
        with mock.patch.object(os, "pidfd_open", lambda pid: order.append("pidfd_open") or real_open(pid)), \
                mock.patch.object(procs, "environ_has", lambda pid, items: order.append("check") or True), \
                mock.patch.object(signal, "pidfd_send_signal", lambda fd, sig: order.append("pidfd_send_signal")), \
                mock.patch.object(os, "kill", side_effect=AssertionError("os.kill: a pid, not a pidfd")):
            self.assertTrue(procs.kill_marked(proc.pid, [b"x"]))
        self.assertEqual(order, ["pidfd_open", "check", "pidfd_send_signal"])

    def test_the_reap_after_a_command_signals_only_its_own_token(self):
        mine = self.spawn(**{procs.INVOCATION: "tok-mine"})
        other = self.spawn(**{procs.INVOCATION: "tok-other"})
        found = repeat.reap_invocation("tok-mine")
        self.assertEqual(found, [mine.pid])
        self.assertEqual(mine.wait(5), -signal.SIGKILL)
        time.sleep(0.1)
        self.assertIsNone(other.poll(), "another command's process was signalled")

    def test_every_child_of_a_session_carries_the_invocation_and_run_markers(self):
        with self.assertRaises(ValueError):
            procs.start(["true"], {procs.MARK: "E006-r0001", procs.SIDE: "game"})
        with self.assertRaises(ValueError):
            procs.start(["true"], {procs.INVOCATION: "t", procs.SIDE: "game"})


class RepeatTest(DriverWorld):
    """The command's loop, on the fake game: records, the fault edge (Scope: Recovery), the stop on a bad repeat."""

    def run_inner(self, argv):
        repo = self.tmp / "repo"
        (repo / "runs").mkdir(parents=True, exist_ok=True)
        self.inner_runs = getattr(self, "inner_runs", 0) + 1
        work = self.tmp / f"private-tmp-{self.inner_runs}"
        work.mkdir()
        env = {procs.INVOCATION: "tok-inner", "IW_DOS_DRIVER_COMMIT": "abcdef123456", "IW_DOS_OUTER_NETNS": "net:[outer]"}
        with mock.patch.object(repeat, "ROOT", repo), mock.patch.object(repeat, "WORK_BASE", work), \
                mock.patch.object(repeat, "versions", return_value={}), mock.patch.dict(os.environ, env), \
                redirect_stderr(io.StringIO()):
            code = repeat.inner(repeat.parser().parse_args(argv), argv)
        records = [json.loads(p.read_text()) for p in sorted((repo / "runs" / "E006").glob("*.json"))]
        return code, records

    def test_three_repeats_complete_with_one_record_each_and_one_start_state(self):
        original = sessionlib.Session.start

        def start(self_):
            self.state = "menu"
            original(self_)
        with mock.patch.object(sessionlib.Session, "start", start):
            code, records = self.run_inner(["--repeats", "3"])
        self.assertEqual(code, 0)
        self.assertEqual([r["status"] for r in records], ["completed"] * 3)
        self.assertEqual(len({r["start_state"]["sha256"] for r in records}), 1)
        self.assertEqual([r["run_id"] for r in records], ["E006-r0001", "E006-r0002", "E006-r0003"])

    def test_a_killed_game_aborts_its_repeat_and_the_next_starts_from_the_baseline_and_completes(self):
        for fault in repeat.FAULTS:
            with self.subTest(fault):
                original = sessionlib.Session.start

                def start(self_):
                    self.state = "menu"
                    original(self_)
                if fault == "close":
                    self.on_command[("xdotool", "windowkill")] = lambda: self.kill_game(1)
                with mock.patch.object(sessionlib.Session, "start", start), \
                        mock.patch.object(sessionlib._Core, "_snapshot_and_reset",
                                          self.writing_reset(sessionlib._Core._snapshot_and_reset)):
                    code, records = self.run_inner(["--repeats", "3", "--fault", fault, "--fault-repeat", "2"])
                records = records[-3:]
                self.assertEqual(code, 0)
                self.assertEqual(records[0]["status"], "completed")
                self.assertTrue(records[1]["status"].startswith("aborted: game-died: "), records[1]["status"])
                self.assertEqual(records[2]["status"], "completed")
                self.assertEqual(len({r["start_state"]["sha256"] for r in records}), 1)
                reset = [o["value"] for o in records[1]["observations"] if o["field"] == "run copy after reset equals the baseline"]
                self.assertEqual(reset, ["yes"])

    def writing_reset(self, original):
        """The game writes ISLEWAR.SCR, as at every launch (F005), just before the reset."""
        def reset(self_):
            (self.game_dir / "ISLEWAR.SCR").write_bytes(b"scores")
            original(self_)
        return reset

    def test_a_repeat_that_does_not_complete_stops_the_command(self):
        self.fail_commands = {("xdotool", "click"): 1}
        code, records = self.run_inner(["--repeats", "3"])
        self.assertEqual(code, 1)
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["status"].startswith("aborted: command-failed: "))


if __name__ == "__main__":
    unittest.main()
