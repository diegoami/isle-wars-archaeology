#!/usr/bin/env python3
"""Remove each guarantee of the Isle Wars Pro driver in turn and show that its tests then fail (T13
Done-when 3, CLAUDE.md rule 9). Usage: TMPDIR=<short dir outside every checkout> python3 tests/mutants_iwp_driver.py

Each mutant replaces exact pieces of source (each must occur exactly once), runs the named tests, and
restores the files whatever happens. A mutant is killed when the tests fail. The script exits 0 only
when every mutant is killed and the unmutated tests pass; it exits 2 when a target test skips (a skip
shows nothing). It edits tracked files while it runs: run it in a clean worktree, never alongside a
recorded cycle run.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = "tests.test_iwp_driver."
S = "runtime/iwp/driver/session.py"
R = "runtime/iwp/driver/runner.py"
C = "runtime/iwp/spike/cycle.py"
# (what, [(file, old, new), ...], [test ids that must fail])
MUTANTS = [
    ("the wait for a screen does not raise at its timeout", [(
        S, '                self.fail(f"the {name} screen was not seen within {timeout} s")', "                pass")],
     [T + "ScreenTest"]),
    ("complete() does not require the known screens to have been reached", [(
        S, "        absent = sorted(self.expected - self.reached)", "        absent = []")],
     [T + "CompleteTest", T + "ScreenTest.test_a_screen_that_never_comes_up_raises_and_the_cycle_is_aborted_not_completed"]),
    ("a cycle that never reached its known screen records completed (neither guard)", [
        (S, '                self.fail(f"the {name} screen was not seen within {timeout} s")', "                pass"),
        (S, "        absent = sorted(self.expected - self.reached)", "        absent = []")],
     [T + "ScreenTest.test_a_screen_that_never_comes_up_raises_and_the_cycle_is_aborted_not_completed",
      T + "CompleteTest.test_a_body_that_never_waits_for_the_screen_is_not_completed"]),
    ("a game that is gone is not noticed (a kill mid-cycle is not recorded aborted)", [(
        S, "        if not self.game_alive():\n            self.fail(f\"the game process exited before",
        "        if False:\n            self.fail(f\"the game process exited before")],
     [T + "KillTest"]),
    ("the reset is skipped after an aborted repeat", [(
        S, '        if hasattr(self, "snap_before"):', '        if hasattr(self, "snap_before") and self.status == "running":')],
     [T + "KillTest.test_the_reset_runs_after_an_aborted_repeat",
      T + "KillTest.test_the_next_repeat_after_an_aborted_one_starts_from_the_baseline_and_completes"]),
    ("the second prefix check, immediately before the launch, is skipped", [(
        S, '            self.seal("immediately before launch", 1)', "            pass")],
     [T + "SealTest.test_a_prefix_made_unsafe_after_the_first_seal_is_refused_immediately_before_launch"]),
    ("the first prefix check is skipped", [(
        S, '            self.seal("before anything starts", 0)', "            pass")],
     [T + "SealTest.test_an_unsafe_prefix_starts_nothing"]),
    ("the wait for the run's processes is unbounded", [(
        S, "        return spike.poll(lambda: not self.alive(side), timeout, 0.05)",
        "        return spike.poll(lambda: not self.alive(side), 10 ** 9, 0.05)")],
     [T + "WaitTest.test_a_game_side_process_that_stays_ends_the_wait_at_its_bound_with_none"]),
    ("the wait looks at another session's processes", [(
        S, "        if all(item in env for item in want) and spike.Cycle.is_alive(int(entry.name)):",
        "        if any(item.startswith(b\"IWP_CYCLE_RUN=\") for item in env) and spike.Cycle.is_alive(int(entry.name)):")],
     [T + "WaitTest.test_the_wait_is_over_at_once_when_only_another_sessions_process_is_alive",
      T + "WaitTest.test_run_processes_never_matches_a_longer_run_id_or_the_marker_of_nobody"]),
    ("the wait for the game side also waits for the display side's daemons (#40)", [(
        S, "        return spike.poll(lambda: not self.alive(side), timeout, 0.05)",
        "        return spike.poll(lambda: not self.alive(None), timeout, 0.05)")],
     [T + "WaitTest.test_the_display_side_does_not_hold_the_game_wait"]),
    ("a stale DBUS_SESSION_BUS_ADDRESS is passed to the children (#40)", [(
        S, '        self.env.pop("DBUS_SESSION_BUS_ADDRESS", None)', "        pass")],
     [T + "EnvironmentTest.test_the_children_get_no_dbus_address_and_no_tmpdir_and_a_side"]),
    ("a prefix that is off its baseline is launched from", [(
        S, "            if here != there:", "            if False:")],
     [T + "SealTest.test_a_prefix_that_is_off_its_baseline_starts_nothing"]),
    # the round-0 review of PR #54
    ("R1: the outer clean-up signals every marked process, not this command's (round 0's selection)", [
        (R, "    found = sessionlib.invocation_processes(token)", "    found = spike.marked_processes()"),
        (R, "        sessionlib.kill_marked(pid, want)", "        os.kill(pid, signal.SIGKILL)")],
     [T + "InvocationTest.test_the_clean_up_kills_this_commands_processes_and_never_another_e004_commands",
      T + "InvocationTest.test_outer_never_signals_another_e004_command"]),
    ("R1: a pid is signalled without checking again that it still carries the marker", [(
        S, "        if not environ_has(pid, items):\n            return False\n        signal.pidfd_send_signal",
        "        signal.pidfd_send_signal")],
     [T + "InvocationTest.test_a_pid_that_no_longer_carries_the_marker_is_not_signalled"]),
    ("R2: a faulted repeat is as expected whatever its clean-up did", [(
        R, '        return session.status.startswith("aborted: game-died: ") and session.recovered',
        '        return session.status.startswith("aborted: game-died: ")')],
     [T + "RecoveryTest.test_a_failed_reset_after_an_injected_kill_is_not_as_expected_and_keeps_the_first_reason",
      T + "RecoveryTest.test_a_reset_that_raises_after_an_injected_kill_is_not_recovered",
      T + "RecoveryTest.test_a_terminate_that_fails_after_an_injected_kill_is_not_recovered"]),
    ("R2: a reset that did not restore the prefix is accepted", [(
        S, "        if self.reset() is not True:", "        if self.reset() is not True and False:")],
     [T + "RecoveryTest.test_a_failed_reset_after_an_injected_kill_is_not_as_expected_and_keeps_the_first_reason",
      T + "RecoveryTest.test_a_completed_cycle_whose_reset_failed_is_aborted_and_not_as_expected"]),
    ("R2: a clean-up stage that faulted counts as succeeded", [(
        S, "            self.cleaned[stage] = len(self.later_faults) == faults", "            self.cleaned[stage] = True")],
     [T + "RecoveryTest.test_a_reset_that_raises_after_an_injected_kill_is_not_recovered",
      T + "RecoveryTest.test_a_terminate_that_fails_after_an_injected_kill_is_not_recovered"]),
    ("R3: a helper command is waited for without a bound", [(
        C, "        out, err = proc.communicate(timeout=timeout)", "        out, err = proc.communicate()")],
     [T + "BoundTest.test_a_helper_command_that_does_not_end_is_killed_at_its_bound",
      T + "BoundTest.test_a_helper_whose_pipes_are_held_open_by_its_own_child_ends_at_its_bound"]),
    ("R3: a killed helper is reaped without a bound", [(
        C, "            proc.wait(REAP_TIMEOUT)", "            proc.wait()")],
     [T + "BoundTest.test_a_killed_helper_that_is_not_reaped_is_a_named_error_not_a_hang"]),
    ("R3: Xvfb or xfwm4 is reaped without a bound after SIGKILL", [(
        S, "                        proc.wait(AFTER_KILL_TIMEOUT)", "                        proc.wait()")],
     [T + "BoundTest.test_stop_x_never_waits_without_a_bound_for_a_process_that_will_not_be_reaped"]),
    ("R3: `wineserver -k` in terminate has no bound", [(
        S, '        spike.run([spike.WINESERVER, "-k"], env=self.env, timeout=WINESERVER_TIMEOUT)\n        spike.poll(',
        '        spike.run([spike.WINESERVER, "-k"], env=self.env, timeout=None)\n        spike.poll(')],
     [T + "BoundTest.test_a_wineserver_that_never_returns_ends_terminate_with_a_named_error"]),
    ("R3: the namespaced command is waited for without a bound", [(
        R, "        return proc.wait(bound)", "        return proc.wait()")],
     [T + "BoundTest.test_the_command_is_killed_at_its_bound"]),
    ("R4: complete() does not require an input (and its order with the screenshots)", [(
        S, """        if not self.actions:
            self.fail("the cycle performed no input step (perform() never sent a click or a key that succeeded)",
                      StepFailed)
        if not self.shot_at.get("before.png", 0) < self.actions[0][0]:
            self.fail("before.png was not taken before the first input", StepFailed)
        if not self.shot_at.get("after.png", 0) > self.actions[-1][0]:
            self.fail("after.png was not taken after the last input", StepFailed)
""", "")],
     [T + "ActionTest.test_a_body_that_waits_for_the_title_and_takes_two_screenshots_but_never_acts_is_not_completed",
      T + "ActionTest.test_complete_refuses_a_session_with_its_screens_and_screenshots_and_a_live_game_but_no_input"]),
    ("R4: after.png may be taken before the input", [(
        S, '        if not self.shot_at.get("after.png", 0) > self.actions[-1][0]:', "        if False:")],
     [T + "ActionTest.test_an_after_screenshot_taken_before_the_input_is_not_an_after_observation"]),
    ("R4: before.png may be taken after the input", [(
        S, '        if not self.shot_at.get("before.png", 0) < self.actions[0][0]:', "        if False:")],
     [T + "ActionTest.test_a_before_screenshot_taken_after_the_input_is_not_a_before_observation"]),
    ("R4: a step that sends no input counts as the action", [(
        S, "                if step.op in INPUT_OPS:", "                if True:")],
     [T + "ActionTest.test_a_step_that_sends_no_input_does_not_count_as_the_action"]),
]


def tests_pass(ids):
    """True when the tests pass. A skipped target test proves nothing either way, so any skip
    stops the script loudly instead of reading as a pass or a kill."""
    done = subprocess.run([sys.executable, "-m", "unittest", "-v"] + ids, cwd=ROOT, capture_output=True, text=True)
    skipped = [line for line in done.stderr.splitlines() if " ... skipped" in line]
    if skipped:
        print("STOPPED: target tests skipped, so no mutant can be shown killed:")
        print("\n".join("  " + line[:300] for line in skipped[:5]))
        print("Run with TMPDIR set to a directory outside every checkout.")
        sys.exit(2)
    return done.returncode == 0


def marked_elsewhere():
    """pids of processes that carry an Isle Wars Pro run marker. The R1 mutant signals every one of them, so
    the script refuses to run while any exists (another session's run, or a recorded cycle)."""
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                env = (entry / "environ").read_bytes().split(b"\0")
            except OSError:
                continue
            if any(item.startswith(b"IWP_CYCLE_RUN=") for item in env):
                found.append(int(entry.name))
    return found


def main():
    if marked_elsewhere():
        print(f"STOPPED: processes with an IWP_CYCLE_RUN marker are alive {marked_elsewhere()}; the R1 mutant "
              "would signal them. Run the mutants when no Isle Wars Pro run is alive.")
        return 2
    ids = sorted({i for *_, group in MUTANTS for i in group})
    if not tests_pass(ids):
        print("the unmutated tests fail; nothing to show")
        return 1
    survived = 0
    for what, edits, group in MUTANTS:
        originals = {rel: (ROOT / rel).read_text() for rel, _, _ in edits}
        bad = [rel for rel, old, _ in edits if originals[rel].count(old) != 1]
        if bad:
            print(f"BAD MUTANT (an edit does not match exactly once in {bad}): {what}")
            survived += 1
            continue
        try:
            mutated = dict(originals)
            for rel, old, new in edits:
                mutated[rel] = mutated[rel].replace(old, new)
            for rel, text in mutated.items():
                (ROOT / rel).write_text(text)
            killed = not tests_pass(group)
        finally:
            for rel, text in originals.items():
                (ROOT / rel).write_text(text)
        print(f"{'killed  ' if killed else 'SURVIVED'} {what} ({len(group)} test id(s))")
        survived += not killed
    print(f"{len(MUTANTS) - survived} of {len(MUTANTS)} mutants killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
