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
And those of the round-0 review (PR #54):
- R1, the outer clean-up signals only this command's processes, never another E004 command's: InvocationTest;
- R2, an aborted repeat whose terminate or reset failed is not recovered, and the command does not go on: RecoveryTest;
- R3, no helper command, reap or command without a bound: BoundTest;
- R4, completed needs a successful input between the two screenshots: ActionTest.
And those of the round-1 review, with the class sweep the owner asked for:
- R1 and class A, no signal to a pid that is not this run's, re-checked through a pidfd: FaultIdentityTest;
- R2 and class B, an input whose command failed is a failed step, a failed capture is an error: CommandTest, MustTest;
- R3 and class C, the game and the display alive at every boundary, just before terminate too: LivenessTest;
- R4 and class D, the check immediately before launch repeats the first's: SealSymmetryTest;
- R5 and class E, the display is the run's own Xvfb's, or another one is tried, or DisplayError: DisplayOwnershipTest.
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
REAL_RUN = spike.run                                # the bounded helper, before any test replaces it
ORIGINAL_START_X = sessionlib.Session.start_x        # the real one, before DriverWorld replaces it
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
        stack.enter_context(mock.patch.object(sessionlib.Session, "run_step", self.stage("run_step")))
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
        self.assertEqual(self.calls[:4], ["start_x", "start_wm", "start_game", "run_step"])
        self.assertTrue(made.recovered)


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
            self.assertTrue(any(o["field"].startswith("install read-only inside the run") for o in doc["observations"]))
            manifest = validate_records.load_file(self.repo / "evidence" / "E004" / f"{made.run_id}.manifest.json")
            self.assertEqual(validate_records.validate_document(manifest), [])
        statuses = sorted(validate_records.load_file(p)["status"][:9] for p in (self.repo / "runs" / "E004").iterdir())
        self.assertEqual(statuses, ["aborted: ", "completed"])

    def test_a_record_is_never_overwritten(self):
        made = self.execute()
        self.store(made)
        with self.assertRaises(errors.RecordError):
            self.store(made)


class ActionTest(DriverWorld):
    """R4 of the round-0 review: completed needs the body to have acted, between its two screenshots."""

    def test_a_body_that_waits_for_the_title_and_takes_two_screenshots_but_never_acts_is_not_completed(self):
        def idle(session):
            session.known_screen()
            session.observe_screenshot("before.png", 3)
            session.observe_screenshot("after.png", 6)
        made = self.execute(idle)
        self.assertTrue(made.status.startswith("aborted: step-failed: the cycle performed no input step"), made.status)
        self.assertNotIn("run_step", self.calls)

    def test_complete_refuses_a_session_with_its_screens_and_screenshots_and_a_live_game_but_no_input(self):
        made = self.session()
        made.start()
        self.addCleanup(made.finish)
        made.wait_for_screen("title", timeout=2)
        made.shot("before.png", 3)
        made.shot("after.png", 6)
        with self.assertRaises(errors.StepFailed):
            made.complete()
        self.assertTrue(made.status.startswith("aborted: step-failed: "), made.status)

    def test_a_step_that_sends_no_input_does_not_count_as_the_action(self):
        def looks_only(session):
            session.known_screen()
            session.observe_screenshot("before.png", 3)
            session.perform("title\nmove 320 585")
            session.observe_screenshot("after.png", 6)
        made = self.execute(looks_only)
        self.assertTrue(made.status.startswith("aborted: step-failed: the cycle performed no input step"), made.status)

    def test_an_after_screenshot_taken_before_the_input_is_not_an_after_observation(self):
        def early(session):
            session.known_screen()
            session.observe_screenshot("before.png", 3)
            session.observe_screenshot("after.png", 6)
            session.perform(runner.OPTIONS_STEP)
        made = self.execute(early)
        self.assertTrue(made.status.startswith("aborted: step-failed: after.png was not taken after the last input"),
                        made.status)

    def test_a_before_screenshot_taken_after_the_input_is_not_a_before_observation(self):
        def late(session):
            session.known_screen()
            session.perform(runner.OPTIONS_STEP)
            session.observe_screenshot("before.png", 3)
            session.observe_screenshot("after.png", 6)
        made = self.execute(late)
        self.assertTrue(made.status.startswith("aborted: step-failed: before.png was not taken before the first input"),
                        made.status)

    def test_a_failed_step_is_not_an_action(self):
        def refused(session):
            session.known_screen()
            session.observe_screenshot("before.png", 3)
            session.perform(runner.OPTIONS_STEP)
            session.observe_screenshot("after.png", 6)

        def fails(session, step):
            raise spike.stepslib.StepError("refused")
        with mock.patch.object(sessionlib.Session, "run_step", fails):
            made = self.execute(refused)
        self.assertTrue(made.status.startswith("aborted: step-failed: step on line 1: refused"), made.status)
        self.assertEqual(made.actions, [])


class RecoveryTest(DriverWorld):
    """R2 of the round-0 review: an aborted repeat counts as recovered only when its clean-up succeeded."""

    def faulted_args(self):
        return runner.parser().parse_args(["--fault", "kill-game", "--fault-at", "after-title", "--fault-repeat", "1"])

    def run_repeat(self, args):
        locs = {"IWP_PREFIX": self.prefix, "E004_BUNDLES": self.bundles, "IWP_DIR": self.install}
        with mock.patch.object(runner, "next_run_id", lambda: self.run_id), \
                mock.patch.object(runner, "write_records", lambda *a, **k: None):
            return runner.run_repeat(1, args, locs, ":99", "abcdef123456", "local", [], {})

    def test_a_clean_injected_kill_is_recovered_and_as_expected(self):
        status, _, good = self.run_repeat(self.faulted_args())
        self.assertTrue(status.startswith("aborted: game-died: "), status)
        self.assertTrue(good)

    def test_a_failed_reset_after_an_injected_kill_is_not_as_expected_and_keeps_the_first_reason(self):
        with mock.patch.object(spike.Cycle, "reset", return_value=False):
            status, _, good = self.run_repeat(self.faulted_args())
        self.assertTrue(status.startswith("aborted: game-died: "), "the first reason is kept: " + status)
        self.assertFalse(good, "a repeat whose reset failed is never as expected")

    def test_a_reset_that_raises_after_an_injected_kill_is_not_recovered(self):
        with mock.patch.object(spike.Cycle, "reset", side_effect=errors.ResetError("reset failed")):
            made = self.execute(hooks={"after-title": runner.kill_game})
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)
        self.assertFalse(made.recovered)
        self.assertFalse(runner.as_expected(made, True))
        self.assertTrue(any(o["field"].startswith("clean-up: every stage succeeded") and o["value"].startswith("no: ")
                            for o in made.obs), "the record says the clean-up failed")

    def test_a_terminate_that_fails_after_an_injected_kill_is_not_recovered(self):
        self.straggler(self.run_id, "game")
        with mock.patch.object(sessionlib.Session, "kill_side", lambda s, side: None):
            made = self.execute(hooks={"after-title": runner.kill_game})
        self.assertTrue(made.status.startswith("aborted: game-died: "), made.status)
        self.assertFalse(made.recovered)
        self.assertFalse(runner.as_expected(made, True))

    def test_a_completed_cycle_whose_reset_failed_is_aborted_and_not_as_expected(self):
        with mock.patch.object(spike.Cycle, "reset", return_value=False):
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: reset: "), made.status)
        self.assertFalse(runner.as_expected(made, False))


class BoundTest(DriverWorld):
    """R3 of the round-0 review: no wait and no helper command without a bound."""

    def within(self, seconds, function):
        done = []

        def target():
            try:
                done.append(function())
            except BaseException as exc:              # the outcome, whatever it is
                done.append(exc)
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(seconds)
        return done[0] if done else "UNBOUNDED"

    def test_a_helper_command_that_does_not_end_is_killed_at_its_bound(self):
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            REAL_RUN(["sleep", "20"], timeout=0.3)
        self.assertLess(time.monotonic() - started, 5)

    def test_a_helper_whose_pipes_are_held_open_by_its_own_child_ends_at_its_bound(self):
        outcome = self.within(5, lambda: REAL_RUN(["sh", "-c", "sleep 3 & exec sleep 20"], timeout=0.3))
        self.assertIsInstance(outcome, subprocess.TimeoutExpired, outcome)

    def test_a_killed_helper_that_is_not_reaped_is_a_named_error_not_a_hang(self):
        class Unkillable:
            stdout = stderr = None
            waits = []

            def __init__(self, *a, **k):
                pass

            def communicate(self, timeout=None):
                raise subprocess.TimeoutExpired("x", timeout)

            def kill(self):
                pass

            def wait(self, timeout=None):
                Unkillable.waits.append(timeout)
                if timeout is None:
                    raise AssertionError("an unbounded wait")
                raise subprocess.TimeoutExpired("x", timeout)
        with mock.patch.object(spike.subprocess, "Popen", Unkillable):
            outcome = self.within(5, lambda: REAL_RUN(["anything"], timeout=0.1))
        self.assertIsInstance(outcome, spike.Unreaped, outcome)
        self.assertEqual(Unkillable.waits, [spike.REAP_TIMEOUT])

    def test_the_helper_keeps_subprocess_run_results(self):
        done = REAL_RUN(["sh", "-c", "echo out; echo err >&2; exit 3"])
        self.assertEqual((done.returncode, done.stdout, done.stderr), (3, b"out\n", b"err\n"))
        with self.assertRaises(subprocess.CalledProcessError):
            REAL_RUN(["false"], check=True)

    def test_stop_x_never_waits_without_a_bound_for_a_process_that_will_not_be_reaped(self):
        class Stuck:
            pid = -1                                    # no such process: kill_marked sends nothing

            def __init__(self):
                self.waits = []

            def poll(self):
                return None

            def terminate(self):
                pass

            def kill(self):
                pass

            def wait(self, timeout=None):
                self.waits.append(timeout)
                if timeout is None:
                    raise AssertionError("an unbounded wait")
                raise subprocess.TimeoutExpired("stuck", timeout)
        made = self.session()
        made.procs = {"wm": Stuck(), "xvfb": Stuck()}
        with mock.patch.object(sessionlib, "STOP_TIMEOUT", 0.1), mock.patch.object(sessionlib, "AFTER_KILL_TIMEOUT", 0.1):
            outcome = self.within(5, made.stop_x)
        self.assertIsInstance(outcome, errors.TerminateError, outcome)
        for proc in made.procs.values():
            self.assertEqual(len(proc.waits), 2)
            self.assertNotIn(None, proc.waits)

    def test_a_wineserver_that_never_returns_ends_terminate_with_a_named_error(self):
        self.fake_wineserver.write_text(f"#!/bin/sh\nkill -9 $(cat {self.pidfile}) 2>/dev/null\nexec sleep 20\n")
        with mock.patch.object(sessionlib, "WINESERVER_TIMEOUT", 0.5):
            started = time.monotonic()
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: terminate: terminate failed: TimeoutExpired"), made.status)
        self.assertLess(time.monotonic() - started, 15)
        self.assertFalse(made.recovered)

    def test_the_command_is_killed_at_its_bound(self):
        started = time.monotonic()
        with mock.patch.object(runner, "REAP_BOUND", 1), mock.patch("sys.stderr"):
            code = self.within(5, lambda: runner.launch_inner(["sleep", "8"], dict(os.environ, **{sessionlib.INVOCATION: "d" * 32}), 0.5))
        self.assertEqual(code, 1)
        self.assertLess(time.monotonic() - started, 5)


class InvocationTest(DriverWorld):
    """R1 of the round-0 review: the outer clean-up signals this command's processes only."""

    def marked(self, run_id, token):
        env = dict(os.environ, **{sessionlib.MARK: run_id, sessionlib.SIDE: "game", sessionlib.INVOCATION: token})
        child = subprocess.Popen(["sleep", "60"], env=env)
        self.children.append(child)
        return child

    def gone(self, child):
        try:
            child.wait(5)
            return True
        except subprocess.TimeoutExpired:
            return False

    def test_the_clean_up_kills_this_commands_processes_and_never_another_e004_commands(self):
        mine = self.marked("E004-r0901", "a" * 32)
        theirs = self.marked("E004-r0902", "b" * 32)
        found = runner.reap_invocation("a" * 32)
        self.assertEqual(found, [mine.pid])
        self.assertTrue(self.gone(mine))
        self.assertIsNone(theirs.poll(), "another E004 command's process survives")

    def test_outer_never_signals_another_e004_command(self):
        theirs = self.marked("E004-r0902", "b" * 32)
        left = []

        def inner(cmd, env, bound):                       # a process of this command outlives its namespace
            left.append(self.marked("E004-r0903", env[sessionlib.INVOCATION]))
            return 0
        locs = {"IWP_PREFIX": self.prefix, "IWP_DIR": self.install, "E004_BUNDLES": self.bundles}
        with mock.patch.object(runner, "confined", return_value=locs), \
                mock.patch.object(spike, "marked_processes", return_value=[]), \
                mock.patch.object(spike, "prefix_processes", return_value=[]), \
                mock.patch.object(spike.prefixlib, "prefix_problems", return_value=[]), \
                mock.patch.object(runner, "launch_inner", inner), mock.patch("sys.stderr"):
            code = runner.outer(runner.parser().parse_args([]), [])
        self.assertEqual(code, 1, "a survivor of this command is reported")
        self.assertTrue(self.gone(left[0]), "this command's survivor is killed")
        self.assertIsNone(theirs.poll(), "another E004 command's process survives the clean-up")

    def test_the_token_reaches_every_child_of_a_session(self):
        with mock.patch.dict(os.environ, {sessionlib.INVOCATION: "c" * 32}):
            made = self.session()
        self.assertEqual((made.env[sessionlib.INVOCATION], made.display_env[sessionlib.INVOCATION]), ("c" * 32,) * 2)

    def test_a_pid_that_no_longer_carries_the_marker_is_not_signalled(self):
        other = subprocess.Popen(["sleep", "60"])
        self.children.append(other)
        self.assertFalse(sessionlib.kill_marked(other.pid, [f"{sessionlib.INVOCATION}={'a' * 32}".encode()]))
        self.assertIsNone(other.poll())
        with self.assertRaises(ValueError):
            sessionlib.invocation_processes("")


class FaultIdentityTest(DriverWorld):
    """Round 1, R1 and class A: no signal to a pid that is not this run's own, re-checked through a pidfd."""

    def test_the_sigkill_fault_never_signals_a_pid_that_is_not_this_runs_game(self):
        other = self.straggler("E004-r0998", "game")          # another run's game, at the pid the listing gave
        made = self.session()
        made.start()
        self.addCleanup(made.finish)
        with mock.patch.object(sessionlib.Session, "find_game_pid", lambda s: other.pid):
            with self.assertRaises(runner.FaultNotInjected):
                runner.sigkill_game(made)
        self.assertIsNone(other.poll(), "another run's process is never signalled")
        self.assertTrue(made.game_alive())

    def test_the_sigkill_fault_kills_this_runs_game(self):
        made = self.session()
        made.start()
        self.addCleanup(made.finish)
        runner.sigkill_game(made)
        self.assertFalse(made.game_alive())

    def test_stop_x_signals_only_a_display_process_that_carries_this_runs_marker(self):
        bare = subprocess.Popen(["sleep", "60"])                 # no marker: not this run's, whatever procs says
        self.children.append(bare)
        made = self.session()
        made.procs = {"xvfb": bare}
        with mock.patch.object(sessionlib, "STOP_TIMEOUT", 0.2), mock.patch.object(sessionlib, "AFTER_KILL_TIMEOUT", 0.2):
            with self.assertRaises(errors.TerminateError):
                made.stop_x()
        self.assertIsNone(bare.poll())

    def test_kill_marked_needs_markers(self):
        with self.assertRaises(ValueError):
            sessionlib.kill_marked(os.getpid(), [])


class CommandTest(DriverWorld):
    """Round 1, R2 and class B: an input step whose command fails is a failed step, never an action."""

    def failing(self, *words):
        def fake(cmd, **kw):
            if cmd and cmd[0] == "xdotool" and cmd[1] in words:
                return mock.MagicMock(returncode=1, stdout=b"", stderr=b"Can't open display")
            return self.fake_run(cmd, **kw)
        return mock.patch.object(spike, "run", side_effect=fake)

    def cycle_with(self, steps):
        def body(session):
            session.known_screen()
            session.observe_screenshot("before.png", 3)
            session.perform(steps)
            session.observe_screenshot("after.png", 6)
        with mock.patch.object(sessionlib.Session, "run_step", spike.Cycle.run_step):
            return self.execute(body)

    def assert_failed_step(self, made):
        self.assertTrue(made.status.startswith("aborted: step-failed: step on line 1: xdotool"), made.status)
        self.assertEqual(made.actions, [])

    def test_a_key_whose_xdotool_fails_is_not_an_action(self):
        with self.failing("key"):
            self.assert_failed_step(self.cycle_with("key Escape"))

    def test_a_click_whose_xdotool_click_fails_is_not_an_action(self):
        with self.failing("click"):
            self.assert_failed_step(self.cycle_with("click 320 585"))

    def test_a_click_whose_pointer_move_fails_is_not_an_action(self):
        with self.failing("mousemove"):
            self.assert_failed_step(self.cycle_with("click 320 585"))

    def test_clicks_whose_xdotool_fails_are_not_an_action(self):
        with self.failing("click"):
            made = self.cycle_with("clicks 2 320 585")
        self.assert_failed_step(made)

    def test_a_move_whose_xdotool_fails_is_a_failed_step(self):
        with self.failing("mousemove"):
            made = self.cycle_with("move 320 585\nkey Escape")
        self.assertTrue(made.status.startswith("aborted: step-failed: step on line 1: xdotool"), made.status)

    def test_window_titles_are_not_read_from_a_failed_command(self):
        def fake(cmd, **kw):
            if cmd[0] == "xprop":
                return mock.MagicMock(returncode=0, stdout=b"_NET_CLIENT_LIST(WINDOW): window id # 0x200001", stderr=b"")
            if cmd[0] == "xdotool":
                return mock.MagicMock(returncode=1, stdout=b"", stderr=b"BadWindow")
            return self.fake_run(cmd, **kw)
        with mock.patch.object(spike, "run", side_effect=fake):
            with self.assertRaises(spike.CommandFailed):
                self.session().window_titles()


class MustTest(unittest.TestCase):
    """Class B: the checked helper, and a capture that failed is never pixels."""

    def test_must_raises_on_a_non_zero_exit_and_returns_otherwise(self):
        with self.assertRaises(spike.CommandFailed):
            spike.must(["sh", "-c", "echo nope >&2; exit 3"])
        self.assertEqual(spike.must(["sh", "-c", "echo yes"]).stdout, b"yes\n")

    def test_a_capture_whose_import_fails_is_an_error_not_empty_pixels(self):
        failed = mock.MagicMock(returncode=1, stdout=b"", stderr=b"unable to open X server")
        with mock.patch.object(spike, "run", return_value=failed):
            with self.assertRaises(spike.CommandFailed):
                spike.Screen(800, 600, {}).raw()


class LivenessTest(DriverWorld):
    """Round 1, R3 and class C: both sides alive at every stage boundary, just before terminate included."""

    def display(self, session):
        """In place of Session.start_x: a display process of this run (a `sleep` with its display markers)."""
        self.calls.append("start_x")
        session.procs["xvfb"] = subprocess.Popen(["sleep", "60"], env=session.display_env)

    def test_a_game_that_dies_after_complete_and_before_terminate_is_not_completed(self):
        real_complete = sessionlib.Session.complete

        def complete_then_die(session):
            real_complete(session)
            session.procs["game"].kill()
            session.procs["game"].wait()
        before = tree(self.prefix)
        with mock.patch.object(sessionlib.Session, "complete", complete_then_die):
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: game-died: the game process exited before terminate"), made.status)
        self.assertTrue(made.recovered, "the clean-up and the reset still ran")
        self.assertEqual(tree(self.prefix), before)

    def test_a_display_that_dies_after_complete_and_before_terminate_is_not_completed(self):
        real_complete = sessionlib.Session.complete

        def complete_then_display_dies(session):
            real_complete(session)
            session.procs["xvfb"].kill()
            session.procs["xvfb"].wait()
        with mock.patch.object(sessionlib.Session, "start_x", lambda s: self.display(s)), \
                mock.patch.object(sessionlib.Session, "complete", complete_then_display_dies):
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: display: xvfb exited before terminate"), made.status)

    def test_a_display_that_dies_mid_cycle_stops_the_cycle_before_its_next_screenshot(self):
        def display_dies(session):
            session.procs["xvfb"].kill()
            session.procs["xvfb"].wait()
        with mock.patch.object(sessionlib.Session, "start_x", lambda s: self.display(s)):
            made = self.execute(hooks={"after-title": display_dies})
        self.assertTrue(made.status.startswith("aborted: display: xvfb exited before the screenshot before.png"), made.status)
        self.assertNotIn("before.png", {n for n, _, _ in made.outputs})


class SealSymmetryTest(DriverWorld):
    """Round 1, R4 and class D: the check immediately before launch repeats every check of the first that can change."""

    def test_a_registry_file_changed_after_the_first_seal_is_refused_immediately_before_launch(self):
        def spoil(session):
            self.calls.append("start_wm")
            (self.prefix / "system.reg").write_text("changed after the first seal")
        with mock.patch.object(sessionlib.Session, "start_wm", spoil):
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: seal: system.reg of the prefix is not the baseline's "
                                               "(immediately before launch)"), made.status)
        self.assertNotIn("start_game", self.calls)

    def test_an_install_made_writable_after_the_first_seal_is_refused_immediately_before_launch(self):
        answers = iter([False])
        with mock.patch.object(spike, "install_writable", side_effect=lambda path: next(answers, True)):
            made = self.execute()
        self.assertTrue(made.status.startswith("aborted: seal: the install is writable inside this run "
                                               "(immediately before launch)"), made.status)
        self.assertNotIn("start_game", self.calls)


LISTENER = ("import socket, sys, time\n"
            "s = socket.socket(socket.AF_UNIX)\n"
            "s.bind('\\0/tmp/.X11-unix/X' + sys.argv[1])\n"
            "s.listen()\n"
            "time.sleep(60)\n")
XDPYINFO = b"dimensions:    800x600 pixels\ndepth of root window:    24 planes\n"


class DisplayOwnershipTest(DriverWorld):
    """Round 1, R5 and class E: the display is this run's own Xvfb's, never merely one that answers."""

    def setUp(self):
        super().setUp()
        self.made = self.session()
        self.made.set_display(sessionlib.free_display())

    def listener(self, display, env=None):
        """A process that holds the display's listening socket, as an X server does."""
        child = subprocess.Popen([sys.executable, "-c", LISTENER, display[1:]], env=env)
        self.children.append(child)
        path = f"@/tmp/.X11-unix/X{display[1:]}"
        spike.poll(lambda: sessionlib.listening_socket_inodes(path) & sessionlib.socket_inodes_of(child.pid), 5, 0.02)
        return child

    def fake_run(self, cmd, **kw):
        if cmd and cmd[0] == "xdpyinfo":                 # the answer of whatever server is on the display
            return mock.MagicMock(returncode=0, stdout=XDPYINFO, stderr=b"")
        return super().fake_run(cmd, **kw)

    def test_a_display_held_by_another_server_is_not_ours_even_when_it_answers(self):
        self.listener(self.made.display)
        ours = subprocess.Popen(["sleep", "60"])
        self.children.append(ours)
        self.assertFalse(self.made.display_is_ours(ours))

    def test_a_display_held_by_this_runs_xvfb_is_ours(self):
        ours = self.listener(self.made.display)
        self.assertTrue(self.made.display_is_ours(ours))

    def test_start_x_tries_another_display_when_its_xvfb_cannot_hold_the_picked_one(self):
        taken = self.made.display
        self.listener(taken)                                  # someone else's server took it first
        spawned = []

        def spawn():
            if not spawned:                                   # a real Xvfb that cannot bind exits 1
                spawned.append(subprocess.Popen(["sh", "-c", "exit 1"]))
            else:
                spawned.append(self.listener(self.made.display))
            return spawned[-1]
        with mock.patch.object(self.made, "spawn_xvfb", spawn):
            ORIGINAL_START_X(self.made)
        self.assertNotEqual(self.made.display, taken)
        self.assertEqual((self.made.env["DISPLAY"], self.made.display_env["DISPLAY"]), (self.made.display,) * 2)
        self.assertIs(self.made.procs["xvfb"], spawned[-1])

    def test_start_x_fails_closed_when_no_display_of_its_own_is_had(self):
        with mock.patch.object(self.made, "spawn_xvfb", lambda: subprocess.Popen(["sh", "-c", "exit 1"])), \
                mock.patch.object(sessionlib, "DISPLAY_ATTEMPTS", 2):
            with self.assertRaises(errors.DisplayError):
                ORIGINAL_START_X(self.made)

    def test_an_xvfb_that_is_alive_but_does_not_hold_the_display_is_never_ready(self):
        self.listener(self.made.display)
        idle = subprocess.Popen(["sleep", "60"])
        self.children.append(idle)
        with mock.patch.object(self.made, "spawn_xvfb", lambda: idle), mock.patch.object(sessionlib, "XVFB_READY_TIMEOUT", 0.5):
            with self.assertRaises(errors.DisplayError):
                ORIGINAL_START_X(self.made)


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
