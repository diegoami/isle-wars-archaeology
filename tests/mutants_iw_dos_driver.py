#!/usr/bin/env python3
"""Remove each guarantee of the DOS driver in turn and show that its tests then fail (T15 Done-when 3,
CLAUDE.md rule 9). Usage: python3 tests/mutants_iw_dos_driver.py

The same machinery as tests/mutants_iw_dos.py (T11's and T14's mutants, which still run there): each mutant
replaces one exact piece of source (it must occur exactly once), runs the named tests, and restores the file
whatever happens. A mutant is killed when the tests fail. Exit 0 only when every mutant is killed and the unmutated
tests pass; exit 2 when a target test skips. It edits tracked files while it runs: run it in a clean worktree,
never alongside a recorded run. A mutant that removes a bound is killed by the tests' watchdog (WATCHDOG_S).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutants_iw_dos as base  # noqa: E402

T = "tests.test_iw_dos_driver."
S, P, R = "runtime/iw-dos/driver/session.py", "runtime/iw-dos/driver/procs.py", "runtime/iw-dos/driver/repeat.py"
SEAL = '("install-read-only", "network-namespace", "run-copy", "baseline", "configuration", "no-dosbox-x")'


def public_entry(name, modes):
    return (f"the guard of {name} is gone", S, f'    "{name}": {modes},\n', "",
            [T + "StructureTest.test_every_public_method_is_guarded_or_listed_as_internal",
             T + {"start": "GuardTest.test_start_runs_once",
                  "finish": "GuardTest.test_finish_leaves_no_process_of_the_run_alive_or_says_so"}.get(
                 name, "GuardTest.test_every_public_method_raises_game_died_when_the_game_is_gone_before_it")])


def seal_check(name):
    names = ("install-read-only", "network-namespace", "run-copy", "baseline", "configuration", "no-dosbox-x")
    fewer = "(" + ", ".join(f'"{n}"' for n in names if n != name) + ")"
    return (f"the seal no longer checks {name}", S, f"SEAL_CHECKS = {SEAL}", f"SEAL_CHECKS = {fewer}",
            [T + "SealSymmetryTest.test_each_check_is_made_again_immediately_before_the_launch",
             T + "SealSymmetryTest.test_the_six_checks_are_the_ones_named"])


MUTANTS = [
    # ---- the liveness guard on every public method and step
    *[public_entry(n, m) for n, m in (("start", '("none", "live")'), ("wait_for_screen", '("live", "live")'),
                                      ("perform", '("live", "live")'), ("observe_screenshot", '("live", "live")'),
                                      ("observe_region", '("live", "live")'), ("observe_file", '("live", "live")'),
                                      ("complete", '("live", "live")'), ("finish", '("any", "gone")'))],
    ("the guard does not check before a method", S, '        self.require(before, f"before {name}")\n', "",
     [T + "GuardTest.test_every_public_method_raises_game_died_when_the_game_is_gone_before_it"]),
    ("the guard does not check after a method", S, '        self.require(after, f"after {name}")\n', "",
     [T + "GuardTest.test_a_game_that_dies_during_a_public_method_is_found_after_it"]),
    ("a step is not checked before it runs", S, '            self.require("live", f"before step {n}")\n', "",
     [T + "GuardTest.test_a_game_that_dies_between_two_steps_is_sent_nothing_more"]),
    ("a step is not checked after it ran", S, '            self.require("live", f"after step {n}")\n', "",
     [T + "GuardTest.test_a_step_is_checked_before_it_runs"]),
    ("a wait does not check the game on each poll", S, '            self.require("live", "during a wait")\n', "",
     [T + "GuardTest.test_a_wait_checks_the_game_on_every_poll"]),
    # ---- the exit-status check of the one command helper
    ("the helper ignores a non-zero exit", P, "    if done.returncode != 0:\n", "    if False:\n",
     [T + "CommandTest.test_must_raises_on_a_non_zero_exit_and_returns_on_zero",
      T + "CommandTest.test_every_command_of_the_cycle_that_fails_aborts_the_repeat"]),
    ("a search that printed something and exited 1 is taken for no window", P,
     "if miss_ok and done.returncode == 1 and not done.stdout.strip() and not done.stderr.strip():",
     "if miss_ok and done.returncode == 1:",
     [T + "CommandTest.test_must_raises_on_a_non_zero_exit_and_returns_on_zero"]),
    ("the session's commands bypass the helper", S, "        done = procs.must(cmd, env=self.env)\n",
     "        done = spike.run(cmd, env=self.env)\n",
     [T + "CommandTest.test_every_command_of_the_cycle_that_fails_aborts_the_repeat",
      T + "StructureTest.test_the_spike_s_unchecked_run_is_never_used_on_the_driver_s_path"]),
    ("a capture of the wrong size is taken", S, "        if len(data) != w * h * 3:\n", "        if False:\n",
     [T + "CommandTest.test_a_capture_of_the_wrong_size_aborts_the_repeat"]),
    # ---- the pidfd re-check before a signal, and the per-invocation marker
    ("kill_marked does not check the markers", P, "        if not environ_has(pid, items):\n            return False\n", "",
     [T + "ProcessIdentityTest.test_a_process_without_the_markers_is_never_signalled",
      T + "ProcessIdentityTest.test_the_markers_are_checked_through_a_pidfd_opened_first_and_the_signal_goes_through_it"]),
    ("the signal goes by pid, not through the pidfd", P, "        signal.pidfd_send_signal(fd, sig)\n",
     "        os.kill(pid, sig)\n",
     [T + "ProcessIdentityTest.test_the_markers_are_checked_through_a_pidfd_opened_first_and_the_signal_goes_through_it"]),
    ("the reap takes every driver command's processes", R, "    found = procs.marked_pids(want)\n",
     "    found = procs.pids_carrying(procs.INVOCATION)\n",
     [T + "ProcessIdentityTest.test_the_reap_after_a_command_signals_only_its_own_token"]),
    ("a session's markers leave out the invocation token", S,
     "        found = [procs.item(procs.INVOCATION, self.token), procs.item(procs.MARK, self.run_id)]",
     "        found = [procs.item(procs.MARK, self.run_id)]",
     [T + "GuardTest.test_a_process_of_another_invocation_is_never_signalled_even_with_the_same_run_id"]),
    ("a child may start without its markers", P,
     "    if not all(env.get(name) for name in (INVOCATION, MARK, SIDE)):", "    if False:",
     [T + "ProcessIdentityTest.test_every_child_of_a_session_carries_the_invocation_and_run_markers"]),
    # ---- every check of the second seal
    *[seal_check(n) for n in ("install-read-only", "network-namespace", "run-copy", "baseline", "configuration",
                              "no-dosbox-x")],
    ("the seal is not made again before the launch", S, '        self._seal("immediately before launch", 1)\n', "",
     [T + "SealSymmetryTest.test_each_check_is_made_again_immediately_before_the_launch"]),
    ("the display is not checked before the launch", S,
     "        if not self._display_is_ours():\n            raise SealError(",
     "        if False:\n            raise SealError(",
     [T + "SealSymmetryTest.test_a_display_not_held_by_this_run_s_xvfb_is_refused_before_the_launch"]),
    # ---- `completed` requires a successful input (and the rest of what it means)
    ("completed without an input", S, "        if self.inputs_sent < 1:\n", "        if False:\n",
     [T + "CompletedTest.test_a_body_without_an_input_is_never_completed"]),
    ("a failed input command counts as an input", S,
     "        done = procs.must(cmd, env=self.env)\n        if tuple(cmd[:2]) in INPUT_COMMANDS:\n            self.inputs_sent += 1\n",
     "        if tuple(cmd[:2]) in INPUT_COMMANDS:\n            self.inputs_sent += 1\n        done = procs.must(cmd, env=self.env)\n",
     [T + "CommandTest.test_a_failed_click_is_not_an_input"]),
    ("completed without the before-state", S, "        if not at_known or before != 0:\n", "        if False:\n",
     [T + "CompletedTest.test_a_before_shot_after_an_input_or_without_a_known_screen_is_not_the_before_state"]),
    ("a game gone at terminate is taken for terminated", S,
     "            if self.body_ok:\n                raise GameDied(f\"DOSBox-X was gone before terminate",
     "            if False:\n                raise GameDied(f\"DOSBox-X was gone before terminate",
     [T + "CompletedTest.test_the_game_killed_at_the_entry_to_terminate_is_not_completed"]),
    ("any exit status is taken for the driver's SIGTERM", S, "        if code != 0:\n            raise GameDied(",
     "        if False:\n            raise GameDied(",
     [T + "CompletedTest.test_a_game_that_ends_otherwise_than_by_sigterm_is_not_completed"]),
    ("completed without recovery", S, "            if self.body_ok and self.recovered:", "            if self.body_ok:",
     [T + "ResetTest.test_a_reset_that_never_showed_the_baseline_is_not_recovery"]),
    # ---- the reset after an aborted repeat
    ("an aborted repeat is not reset", S, '("snapshot and reset", self._snapshot_and_reset)',
     '("snapshot and reset", self._snapshot_and_reset if self.body_ok else (lambda: None))',
     [T + "ResetTest.test_an_aborted_repeat_is_reset_and_the_next_one_completes",
      T + "RepeatTest.test_a_killed_game_aborts_its_repeat_and_the_next_starts_from_the_baseline_and_completes"]),
    ("the reset is not compared with the baseline", S, "        ok = restored == self.baseline\n", "        ok = True\n",
     [T + "ResetTest.test_a_reset_that_cannot_restore_the_baseline_is_not_recovered"]),
    # ---- a bound on every wait
    ("a wait has no bound", S, "            if time.monotonic() - start > timeout:\n                return None",
     "            if False:\n                return None",
     [T + "BoundTest.test_wait_until_returns_none_at_its_bound"]),
    ("a named screen has no bound", S, "self.wait_until(getattr(self.screen, predicate), bound, 0.25)",
     "self.wait_until(getattr(self.screen, predicate), bound * 10 ** 6, 0.25)",
     [T + "BoundTest.test_a_screen_that_never_comes_is_screen_not_reached"]),
    ("a command has no bound", P, "capture_output=True, timeout=timeout)", "capture_output=True, timeout=None)",
     [T + "BoundTest.test_a_command_past_its_bound_is_stopped"]),
    ("Xvfb's start has no bound", S, "or self.procs[\"xvfb\"].poll() is not None, XVFB_S, 0.05)",
     "or self.procs[\"xvfb\"].poll() is not None, XVFB_S * 10 ** 6, 0.05)",
     [T + "BoundTest.test_an_xvfb_that_never_holds_its_display_is_a_display_error"]),
    ("the window has no bound", S, "self.wait_until(lambda: self.window_geometry() is not None, WINDOW_S)",
     "self.wait_until(lambda: self.window_geometry() is not None, WINDOW_S * 10 ** 6)",
     [T + "BoundTest.test_a_window_that_never_shows_is_a_launch_error"]),
    ("terminate has no bound", S, "spike.poll(lambda: game.poll() is not None, TERM_S, 0.05)",
     "spike.poll(lambda: game.poll() is not None, TERM_S * 10 ** 6, 0.05)",
     [T + "BoundTest.test_a_game_that_ignores_sigterm_is_killed_and_reported"]),
    ("Xvfb's stop has no bound", S, "spike.poll(lambda: xvfb.poll() is not None, STOP_S, 0.05)",
     "spike.poll(lambda: xvfb.poll() is not None, STOP_S * 10 ** 6, 0.05)",
     [T + "BoundTest.test_an_xvfb_that_ignores_sigterm_is_killed"]),
    ("the command has no bound", R, "        return proc.wait(bound)\n", "        return proc.wait()\n",
     [T + "BoundTest.test_the_command_is_killed_at_its_bound"]),
]


if __name__ == "__main__":
    base.MUTANTS = MUTANTS
    sys.exit(base.main())
