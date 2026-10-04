"""The Isle Wars Pro driver (T13, runtime/iwp/driver/), without the game: a fake game process, a scripted
screen, a fake `wineserver`, on the synthetic fixtures of iwp_fixtures.py.

The fake game is a real child process (`sleep`) that carries the run's marker, so the driver's wait on the
run's own processes, its kill detection and its reset are the real code. Only what needs a display or Wine
is replaced: Xvfb, xfwm4, the launch itself, the screen predicates, `xdotool` and `import`.

The guarantees of T13's Done-when 3, each with the tests that fail when it is removed
(tests/mutants_iwp_driver.py removes each in turn and shows them failing):
- a cycle that never reached its known screen is never completed: ScreenTest, CompleteTest;
- a kill mid-cycle is recorded aborted: KillTest;
- the reset after an aborted repeat is not skipped: KillTest.test_the_reset_runs_after_an_aborted_repeat;
- the second prefix check, immediately before the launch, runs: SealTest;
- the wait for the run's processes is bounded and looks at this run's game side only: WaitTest.
"""
import contextlib
import os
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from iwp_fixtures import InnerHarness, World, prefix, tree, validate_records  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "iwp"))
from driver import errors, runner, session as sessionlib  # noqa: E402

spike = sessionlib.spike
SAMPLE = b"\x10" * (800 * 600 * 3)


class DriverWorld(World):
    """A synthetic prefix with a baseline, and a Session whose game is a `sleep` process."""

    counter = 0

    def setUp(self):
        super().setUp()
        self.game = self.game_copy()
        self.baseline = Path(str(self.prefix) + ".baseline")
        self.baseline.mkdir()
        (self.baseline / "system.reg").write_text("reg")
        DriverWorld.counter += 1
        self.run_id = f"E004-r{9000 + DriverWorld.counter}"
        self.calls, self.children = [], []
        self.pidfile = self.tmp / "game.pid"
        self.fake_wineserver = self.tmp / "wineserver"
        self.fake_wineserver.write_text(f"#!/bin/sh\nkill -9 $(cat {self.pidfile}) 2>/dev/null\nexit 0\n")
        self.fake_wineserver.chmod(0o755)
        self.screens = {"title": True, "options": True}
        self.real_run = spike.run
        self.addCleanup(self.reap)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        for target, value in {"WINESERVER": str(self.fake_wineserver)}.items():
            stack.enter_context(mock.patch.object(spike, target, value))
        stack.enter_context(mock.patch.object(spike, "install_writable", return_value=False))
        stack.enter_context(mock.patch.object(spike, "run", side_effect=self.fake_run))
        stack.enter_context(mock.patch.object(spike.Screen, "raw", return_value=SAMPLE))
        stack.enter_context(mock.patch.object(spike.Screen, "title_up", lambda s: self.screens["title"]))
        stack.enter_context(mock.patch.object(spike.Screen, "options_up", lambda s: self.screens["options"]))
        stack.enter_context(mock.patch.object(sessionlib.Session, "start_x", self.stage("start_x")))
        stack.enter_context(mock.patch.object(sessionlib.Session, "start_wm", self.stage("start_wm")))
        stack.enter_context(mock.patch.object(sessionlib.Session, "start_game", lambda s: self.start_game(s)))
        stack.enter_context(mock.patch.object(sessionlib.Session, "perform", self.stage("perform")))
        stack.enter_context(mock.patch.object(sessionlib, "TITLE_TIMEOUT", 1.0))
        stack.enter_context(mock.patch.object(sessionlib, "WAIT_GONE_TIMEOUT", 0.6))
        stack.enter_context(mock.patch.object(sessionlib, "AFTER_KILL_TIMEOUT", 0.6))
        stack.enter_context(mock.patch.object(sessionlib, "DISPLAY_GONE_TIMEOUT", 0.6))
        stack.enter_context(mock.patch("sys.stdout"))

    def fake_run(self, cmd, **kw):
        if cmd and cmd[0] == spike.WINESERVER:       # the fake wineserver really runs
            return self.real_run(cmd, **kw)
        return mock.MagicMock(returncode=0, stdout=b"", stderr=b"")

    def stage(self, name):
        def stage(session, *args, **kw):
            self.calls.append(name)
        return stage

    def start_game(self, session):
        """In place of Session.start_game: a game that writes into the prefix and a process that carries the marker."""
        self.calls.append("start_game")
        session.t_launch = time.monotonic()
        self.write(self.prefix / "drive_c" / "Temp" / "x.dll", b"written by the game")
        session.procs["game"] = subprocess.Popen(["sleep", "60"], env=session.env)
        self.pidfile.write_text(str(session.procs["game"].pid))

    def straggler(self, run_id, side):
        """A process that carries a marker, as the game side or the display side of a run would."""
        env = dict(os.environ, **{sessionlib.MARK: run_id, sessionlib.SIDE: side})
        child = subprocess.Popen(["sleep", "60"], env=env)
        self.children.append(child)
        return child

    def reap(self):
        for child in self.children:
            child.kill()
            child.wait()

    def session(self):
        return sessionlib.Session(self.run_id, self.prefix, self.bundles, self.install, ":99", "control")

    def execute(self, body=runner.options_cycle, hooks=None):
        made = self.session()
        for name, hook in (hooks or {}).items():
            made.on(name, hook)
        made.execute(body)
        self.addCleanup(lambda: made.procs.get("game") and made.procs["game"].poll() is None and made.procs["game"].kill())
        return made


class CompletedTest(DriverWorld):
    def test_a_good_cycle_completes_with_its_screens_and_nothing_left(self):
        before = tree(self.prefix)
        made = self.execute()
        self.assertEqual(made.status, "completed", made.status)
        self.assertEqual({"title", "options"}, made.reached)
        self.assertEqual({"before.png", "after.png"}, {n for n, _, c in made.outputs if c == "screenshot"})
        self.assertEqual(made.alive(), [])
        self.assertEqual(tree(self.prefix), before, "reset put the prefix back")
        self.assertEqual(self.calls[:4], ["start_x", "start_wm", "start_game", "perform"])


class ScreenTest(DriverWorld):
    def test_a_screen_that_never_comes_up_raises_and_the_cycle_is_aborted_not_completed(self):
        self.screens["title"] = False
        made = self.execute()
        self.assertTrue(made.status.startswith("aborted: screen-not-reached: "), made.status)
        self.assertNotIn("before.png", {n for n, _, _ in made.outputs})

    def test_wait_for_screen_raises_a_named_error_at_the_timeout(self):
        self.screens["title"] = False
        made = self.session()
        made.start()
        self.addCleanup(made.finish)
        started = time.monotonic()
        with self.assertRaises(errors.ScreenNotReached):
            made.wait_for_screen("title", timeout=0.5)
        self.assertLess(time.monotonic() - started, 5)
        self.assertNotIn("title", made.reached)

    def test_the_wait_is_over_when_the_screen_is_there_and_it_is_remembered(self):
        made = self.session()
        made.start()
        self.addCleanup(made.finish)
        made.wait_for_screen("title", timeout=2)
        self.assertEqual(made.reached, {"title"})

    def test_an_unknown_screen_name_is_refused(self):
        with self.assertRaises(ValueError):
            self.session().wait_for_screen("board")


class CompleteTest(DriverWorld):
    def test_complete_refuses_a_cycle_whose_known_screen_was_not_reached_even_with_both_screenshots(self):
        made = self.session()
        made.start()
        self.addCleanup(made.finish)
        made.shot("before.png", 3)
        made.shot("after.png", 6)
        made.expected = {"title", "options"}
        made.reached = {"options"}
        with self.assertRaises(errors.ScreenNotReached):
            made.complete()
        self.assertTrue(made.status.startswith("aborted: screen-not-reached: "), made.status)

    def test_complete_refuses_a_cycle_without_its_screenshots(self):
        made = self.session()
        made.start()
        self.addCleanup(made.finish)
        made.reached = {"title"}
        with self.assertRaises(errors.StepFailed):
            made.complete()
        self.assertTrue(made.status.startswith("aborted: step-failed: "), made.status)

    def test_a_body_that_never_waits_for_the_screen_is_not_completed(self):
        def lazy(session):
            session.expected.update({"title", "options"})
            session.observe_screenshot("before.png", 3)
            session.observe_screenshot("after.png", 6)
        made = self.execute(lazy)
        self.assertTrue(made.status.startswith("aborted: screen-not-reached: "), made.status)


class KillTest(DriverWorld):
    def test_a_kill_mid_cycle_by_wineserver_is_recorded_aborted(self):
        made = self.execute(hooks={"after-title": runner.kill_game})
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)
        self.assertNotIn("after.png", {n for n, _, _ in made.outputs})

    def test_a_sigkill_of_the_game_mid_cycle_is_recorded_aborted(self):
        made = self.execute(hooks={"after-input": runner.sigkill_game})
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)

    def test_a_game_that_is_gone_before_its_first_screen_is_game_died_at_once_not_a_timeout(self):
        self.screens["title"] = False

        def dies(session):
            self.start_game(session)
            session.procs["game"].kill()
            session.procs["game"].wait()
        started = time.monotonic()
        with mock.patch.object(sessionlib, "TITLE_TIMEOUT", 30), mock.patch.object(sessionlib.Session, "start_game", dies):
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)
        self.assertLess(time.monotonic() - started, 10)

    def test_the_reset_runs_after_an_aborted_repeat(self):
        before = tree(self.prefix)
        made = self.execute(hooks={"after-title": runner.kill_game})
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)
        self.assertEqual(tree(self.prefix), before, "what the game wrote is gone after the aborted repeat")
        self.assertFalse((self.prefix / "drive_c" / "Temp").exists())
        self.assertEqual(made.alive(), [])

    def test_the_next_repeat_after_an_aborted_one_starts_from_the_baseline_and_completes(self):
        first = self.execute(hooks={"after-title": runner.kill_game})
        self.assertTrue(first.status.startswith("aborted: "))
        self.run_id = self.run_id + "b"
        self.pidfile.unlink()
        second = self.execute()
        self.assertEqual(second.status, "completed", second.status)
        self.assertEqual(spike.start_state_sha(first.snap_before[1]), spike.start_state_sha(second.snap_before[1]))

    def test_a_game_that_is_gone_at_the_end_is_not_completed(self):
        def kill_late(session):
            runner.options_cycle(session)
            runner.sigkill_game(session)
        made = self.execute(kill_late)
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)


class SealTest(DriverWorld):
    def spoil(self, session):
        os.symlink("/", self.prefix / "dosdevices" / "z:")

    def test_a_prefix_made_unsafe_after_the_first_seal_is_refused_immediately_before_launch(self):
        with mock.patch.object(sessionlib.Session, "start_wm", lambda s: self.spoil(s)):
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: seal: the prefix is not safe to launch from (immediately before launch)"),
                        made.status)
        self.assertNotIn("start_game", self.calls)

    def test_an_unsafe_prefix_starts_nothing(self):
        self.spoil(None)
        made = self.execute()
        self.assertTrue(made.status.startswith("aborted: seal: the prefix is not safe to launch from (before anything starts)"),
                        made.status)
        self.assertEqual([c for c in self.calls if c in ("start_x", "start_wm", "start_game")], [])

    def test_an_install_that_is_writable_starts_nothing(self):
        with mock.patch.object(spike, "install_writable", return_value=True):
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: seal: the install is writable"), made.status)
        self.assertEqual(self.calls, [])

    def test_a_prefix_that_is_off_its_baseline_starts_nothing(self):
        (self.prefix / "system.reg").write_text("changed by something outside the driver")
        made = self.execute()
        self.assertTrue(made.status.startswith("aborted: seal: system.reg of the prefix is not the baseline's"), made.status)
        self.assertEqual(self.calls, [])

    def test_a_prefix_without_a_baseline_starts_nothing(self):
        (self.baseline / "system.reg").unlink()
        made = self.execute()
        self.assertTrue(made.status.startswith("aborted: seal: the prefix has no baseline"), made.status)


class WaitTest(DriverWorld):
    """The wait for the run's processes: bounded, and about this run's game side only."""

    def within(self, seconds, function):
        done = []
        thread = threading.Thread(target=lambda: done.append(function()), daemon=True)
        thread.start()
        thread.join(seconds)
        return done[0] if done else "UNBOUNDED"

    def test_a_game_side_process_that_stays_ends_the_wait_at_its_bound_with_none(self):
        self.straggler(self.run_id, "game")
        made = self.session()
        self.assertIsNone(self.within(5, lambda: made.wait_gone("game", 0.5)))

    def test_the_wait_is_over_at_once_when_only_another_sessions_process_is_alive(self):
        self.straggler("E004-r0999", "game")                   # another run's game side
        made = self.session()
        waited = self.within(5, lambda: made.wait_gone("game", 3))
        self.assertIsInstance(waited, float, "the wait ended because this run has nothing alive")
        self.assertLess(waited, 1)
        self.assertEqual(made.alive(), [])

    def test_the_display_side_does_not_hold_the_game_wait(self):
        self.straggler(self.run_id, "display")                 # what xfwm4 leaves: dbus-daemon, at-spi, xfconfd
        made = self.session()
        waited = self.within(5, lambda: made.wait_gone("game", 3))
        self.assertIsInstance(waited, float)
        self.assertLess(waited, 1)
        self.assertEqual(len(made.alive()), 1, "it is still this run's, and the final check counts it")

    def test_run_processes_never_matches_a_longer_run_id_or_the_marker_of_nobody(self):
        self.straggler(self.run_id + "0", "game")
        self.assertEqual(sessionlib.run_processes(self.run_id), [])
        with self.assertRaises(ValueError):
            sessionlib.run_processes(None)
        with self.assertRaises(ValueError):
            sessionlib.run_processes("")

    def test_terminate_kills_a_game_side_survivor_after_the_bound_and_the_session_is_still_completed(self):
        self.straggler(self.run_id, "game")
        made = self.execute()
        self.assertEqual(made.status, "completed", made.status)
        self.assertEqual(made.alive(), [])

    def test_a_survivor_that_cannot_be_killed_is_a_named_terminate_error(self):
        self.straggler(self.run_id, "game")
        with mock.patch.object(sessionlib.Session, "kill_side", lambda s, side: None):
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: terminate: "), made.status)

    def test_a_display_side_survivor_is_killed_and_counted(self):
        self.straggler(self.run_id, "display")
        made = self.execute()
        self.assertEqual(made.status, "completed", made.status)
        self.assertEqual(made.alive(), [])


class EnvironmentTest(DriverWorld):
    def test_the_children_get_no_dbus_address_and_no_tmpdir_and_a_side(self):
        with mock.patch.dict(os.environ, {"DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/bus", "TMPDIR": "/nonexistent"}):
            made = self.session()
        self.assertNotIn("DBUS_SESSION_BUS_ADDRESS", made.env)
        self.assertNotIn("DBUS_SESSION_BUS_ADDRESS", made.display_env)
        self.assertNotIn("TMPDIR", made.env)
        self.assertEqual((made.env[sessionlib.SIDE], made.display_env[sessionlib.SIDE]), ("game", "display"))
        self.assertEqual((made.env[sessionlib.MARK], made.display_env[sessionlib.MARK]), (self.run_id, self.run_id))
        self.assertEqual(made.env["DISPLAY"], ":99")

    def test_a_stale_bus_is_said_so_in_the_log_and_the_record(self):
        with mock.patch.dict(os.environ, {"DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/bus"}):
            made = self.session()
        made.note_environment()
        self.assertTrue(any("stale" in line and "unset for this run" in line for line in made.log), made.log)
        values = [o["value"] for o in made.obs if o["field"].startswith("DBUS_SESSION_BUS_ADDRESS")]
        self.assertEqual(values, ["set, stale: unset for the run"])
        self.assertNotIn("/nonexistent", repr(made.obs), "the bus's path is the machine's, not evidence")


class DisplayTest(unittest.TestCase):
    def test_a_display_with_a_listening_x_server_is_skipped(self):
        first = sessionlib.free_display()
        number = first[1:]
        sock = socket.socket(socket.AF_UNIX)
        self.addCleanup(sock.close)
        sock.bind(f"\0/tmp/.X11-unix/X{number}")
        self.assertNotEqual(sessionlib.free_display(), first)


class RecordTest(DriverWorld):
    def setUp(self):
        super().setUp()
        self.repo = self.tmp / "repo"
        (self.repo / "runs" / "E004").mkdir(parents=True)
        (self.repo / "evidence" / "E004").mkdir(parents=True)
        self.bundles.mkdir()
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(runner, "ROOT", self.repo))
        stack.enter_context(mock.patch.object(spike, "ROOT", self.repo))

    def store(self, made):
        runner.write_records(made, self.bundles, "abcdef123456", "local", "0" * 64, ["--arm", "control"], {"wine": "x"})

    def test_a_completed_and_an_aborted_repeat_are_both_recorded_and_valid_run_1(self):
        for hooks in ({}, {"after-title": runner.kill_game}):
            self.run_id = f"E004-r{9100 + len(list((self.repo / 'runs' / 'E004').iterdir()))}"
            if self.pidfile.exists():
                self.pidfile.unlink()
            made = self.execute(hooks=hooks)
            self.store(made)
            path = self.repo / "runs" / "E004" / f"{made.run_id}.json"
            doc = validate_records.load_file(path)
            self.assertEqual(validate_records.validate_document(doc), [])
            self.assertEqual(doc["status"], made.status)
            self.assertEqual(doc["experiment"], "E004")
            self.assertEqual(doc["artifact"]["set"], "iwp-2.0-996e86c5")
            self.assertTrue(any(o["field"] == "install read-only inside the run" for o in doc["observations"]))
            manifest = validate_records.load_file(self.repo / "evidence" / "E004" / f"{made.run_id}.manifest.json")
            self.assertEqual(validate_records.validate_document(manifest), [])
        statuses = sorted(validate_records.load_file(p)["status"][:9] for p in (self.repo / "runs" / "E004").iterdir())
        self.assertEqual(statuses, ["aborted: ", "completed"])

    def test_a_record_is_never_overwritten(self):
        made = self.execute()
        self.store(made)
        with self.assertRaises(errors.RecordError):
            self.store(made)


class RunnerTest(unittest.TestCase):
    def test_the_options_step_is_the_spikes_options_click(self):
        self.assertEqual(runner.OPTIONS_STEP, "click! 320 585")

    def test_arguments_are_checked_before_anything_starts(self):
        for argv in (["--repeats", "0"], ["--repeats", "51"], ["--fault", "kill-game", "--fault-repeat", "11"]):
            with self.assertRaises(SystemExit):
                runner.check_args(runner.parser().parse_args(argv))
        runner.check_args(runner.parser().parse_args(["--fault", "sigkill-game", "--fault-repeat", "2"]))


if __name__ == "__main__":
    unittest.main()
