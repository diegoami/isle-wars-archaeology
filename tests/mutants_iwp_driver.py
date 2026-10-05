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
        S, '        if snapshot:\n            self.cleanup("snapshot and reset"',
        '        if snapshot and self.status == "running":\n            self.cleanup("snapshot and reset"')],
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
        (R, "        sessionlib.kill_marked(pid, want)", "        os.kill(pid, 9)")],
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
        S, '        ok, _, _ = spike.probe([spike.WINESERVER, "-k"], env=self.env, timeout=WINESERVER_TIMEOUT)',
        '        ok, _, _ = spike.probe([spike.WINESERVER, "-k"], env=self.env, timeout=None)')],
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
    # the round-1 review of PR #54, and the class sweep (A to E)
    ("R1/A: the SIGKILL fault signals a bare pid", [(
        R, "    if not sessionlib.kill_marked(pid, game_items(session)):",
        "    os.kill(pid, 9)\n    if False:")],
     [T + "FaultIdentityTest.test_the_sigkill_fault_never_signals_a_pid_that_is_not_this_runs_game"]),
    ("A: stop_x signals Xvfb or xfwm4 without its marker re-checked", [(
        S, "        kill_marked(proc.pid, [f\"{MARK}={self.run_id}\".encode(), f\"{SIDE}=display\".encode()], sig)",
        "        proc.send_signal(sig)")],
     [T + "FaultIdentityTest.test_stop_x_signals_only_a_display_process_that_carries_this_runs_marker"]),
    ("R2/B: a key whose xdotool failed counts as sent", [(
        C, '            must(["xdotool", "key", args[0]], env=self.env, require_output=False)',
        '            run(["xdotool", "key", args[0]], env=self.env, require_output=False)')],
     [T + "CommandTest.test_a_key_whose_xdotool_fails_is_not_an_action"]),
    ("B: a click whose xdotool click failed counts as sent", [(
        C, '        must(["xdotool", "click", "1"], env=self.env, require_output=False)',
        '        run(["xdotool", "click", "1"], env=self.env, require_output=False)')],
     [T + "CommandTest.test_a_click_whose_xdotool_click_fails_is_not_an_action"]),
    ("B: a click whose pointer moves failed counts as sent", [
        (C, """        before = self.screen.raw(rect)
        must(["xdotool", "mousemove",""", """        before = self.screen.raw(rect)
        run(["xdotool", "mousemove","""),
        (C, """            must(["xdotool", "mousemove", str(x + 1 + self.screen.ox)""",
         """            run(["xdotool", "mousemove", str(x + 1 + self.screen.ox)"""),
        (C, """            must(["xdotool", "mousemove", str(x + self.screen.ox), str(y + self.screen.oy)], env=self.env,
                 require_output=False)   # back""",
         """            run(["xdotool", "mousemove", str(x + self.screen.ox), str(y + self.screen.oy)], env=self.env,
                 require_output=False)   # back""")],
     [T + "CommandTest.test_a_click_whose_pointer_move_fails_is_not_an_action"]),
    ("B: clicks whose xdotool failed count as sent", [(
        C, '            must(["xdotool", "click", "--repeat",', '            run(["xdotool", "click", "--repeat",')],
     [T + "CommandTest.test_clicks_whose_xdotool_fails_are_not_an_action"]),
    ("B: a move whose xdotool failed passes", [(
        C, """        elif op == "move":
            must(["xdotool", "mousemove",""", """        elif op == "move":
            run(["xdotool", "mousemove",""")],
     [T + "CommandTest.test_a_move_whose_xdotool_fails_is_a_failed_step"]),
    ("B: window titles are read from a failed command", [(
        C, '            names.append(must(["xdotool", "getwindowname",', '            names.append(run(["xdotool", "getwindowname",')],
     [T + "CommandTest.test_window_titles_are_not_read_from_a_failed_command"]),
    ("B: a capture whose import failed is empty pixels", [(
        C, "        return must(cmd, env=self.env).stdout", "        return run(cmd, env=self.env).stdout")],
     [T + "MustTest.test_a_capture_whose_import_fails_is_an_error_not_empty_pixels"]),
    ("B: must() does not check the exit status", [(
        C, "    done = run(cmd, **kw)\n    if done.returncode != 0:", "    done = run(cmd, **kw)\n    if False:")],
     [T + "MustTest", T + "CommandTest.test_a_key_whose_xdotool_fails_is_not_an_action"]),
    ("R3/C: a game that died before terminate is not noticed", [(
        S, '        if not self.game_alive():\n            self._set_aborted(f"the game process exited before terminate',
        '        if False:\n            self._set_aborted(f"the game process exited before terminate')],
     [T + "LivenessTest.test_a_game_that_dies_after_complete_and_before_terminate_is_not_completed"]),
    ("C: a display that died before terminate is not noticed", [(
        S, "        dead = self.display_dead()\n        if dead:\n            self._set_aborted(f\"{' and '.join(dead)} exited before terminate\", DisplayError)",
        "        dead = self.display_dead()\n        if dead:\n            pass")],
     [T + "LivenessTest.test_a_display_that_dies_after_complete_and_before_terminate_is_not_completed"]),
    ("C: the display side is not checked at the stage boundaries", [(
        S, "        self.require_display(where)\n        self.require_game(where)", "        self.require_game(where)")],
     [T + "LivenessTest.test_a_display_that_dies_mid_cycle_stops_the_cycle_before_its_next_screenshot"]),
    ("R4/D: the baseline is not compared again immediately before launch", [(
        S, '            self.require_baseline("immediately before launch", 1)', "            pass")],
     [T + "SealSymmetryTest.test_a_registry_file_changed_after_the_first_seal_is_refused_immediately_before_launch"]),
    ("D: the install is not checked again immediately before launch", [(
        S, '            self.require_install_readonly("immediately before launch", 1)', "            pass")],
     [T + "SealSymmetryTest.test_an_install_made_writable_after_the_first_seal_is_refused_immediately_before_launch"]),
    ("R5/E: a display that answers is taken for this run's, whoever holds it", [(
        S, "        if not listening_socket_inodes(path) & socket_inodes_of(proc.pid):", "        if False:")],
     [T + "DisplayOwnershipTest.test_a_display_held_by_another_server_is_not_ours_even_when_it_answers",
      T + "DisplayOwnershipTest.test_an_xvfb_that_is_alive_but_does_not_hold_the_display_is_never_ready"]),
    ("E: a taken display is tried again instead of another one", [(
        S, "                self.set_display(free_display(exclude=tried))", "                pass")],
     [T + "DisplayOwnershipTest.test_start_x_tries_another_display_when_its_xvfb_cannot_hold_the_picked_one"]),
    ("E: no display of its own is not an error (fails open)", [(
        S, """            self.fail(f"no display of this run's own after {DISPLAY_ATTEMPTS} attempts ({', '.join(tried)})", DisplayError)""",
        "            pass")],
     [T + "DisplayOwnershipTest.test_start_x_fails_closed_when_no_display_of_its_own_is_had"]),
    # the round-3 (structural) review of PR #54
    ("R1: an incomplete baseline (a registry file the prefix has, missing or a link in the baseline) is accepted", [(
        S, "            if not kept.is_file() or kept.is_symlink():\n                incomplete.append(name)\n                continue",
        "            if not kept.is_file() or kept.is_symlink():\n                continue")],
     [T + "BaselineCompletenessTest"]),
    ("R2: a game killed at the entry to terminate is treated as a clean termination", [(
        S, '        if not self.game_alive():\n            self._set_aborted(f"the game process exited before terminate',
        '        if False:\n            self._set_aborted(f"the game process exited before terminate')],
     [T + "TerminateBoundaryTest"]),
    # the round-3 live re-take (E004-r0108): a SIGKILLed game left its side's Wine processes alive
    ("R2: a game already dead at terminate skips the termination of the rest of its side", [(
        S, '            self.say("the game had already exited before terminate; the rest of its side is still terminated")\n',
        '            self.say("the game had already exited before terminate; the rest of its side is still terminated")\n'
        '            return\n')],
     [T + "TerminateBoundaryTest.test_a_sigkilled_game_still_has_the_rest_of_its_side_terminated_and_the_display_stopped"]),
    ("R3: the stability poll does not check the game is alive", [(
        S, '                    self.require_alive(f"the {name} screen was not stable")',
        '                    pass')],
     [T + "StabilityLivenessTest"]),
    ("R4: file observation has no liveness guard", [(
        S, '    @guarded("a file observation")\n    def observe_file(self, rel):',
        '    def observe_file(self, rel):')],
     [T + "FileObservationLivenessTest"]),
    ("R5: xprop exit status is ignored, a partial answer registers the window manager", [(
        C, "    return ok and b\"window id\" in out", "    return b\"window id\" in out")],
     [T + "WMReadinessTest.test_a_nonzero_xprop_is_not_registered_even_with_window_id_on_stdout"]),
    ("R6: a failed version probe is parsed, not recorded unknown", [(
        C, "        if not ok:\n            return \"unknown\"          # R6:", "        if not ok:\n            pass")],
     [T + "VersionsTest.test_a_failed_probe_is_unknown_not_parsed"]),
    ("the sweep: one game-facing method loses its guard", [(
        S, '    @guarded("a file observation")\n    def observe_file(self, rel):',
        '    def observe_file(self, rel):')],
     [T + "GuardSweepTest.test_every_public_method_of_the_effective_interface_is_guarded_or_a_stated_exception"]),
    ("the sweep: one raw subprocess call is made outside the checked helper", [(
        S, '        return spike.spawn(["Xvfb", self.display, "-screen", "0", f"{width}x{height}x{depth}", "-nolisten", "tcp"],',
        '        return subprocess.Popen(["Xvfb", self.display, "-screen", "0", f"{width}x{height}x{depth}", "-nolisten", "tcp"],')],
     [T + "CommandHelperSweepTest"]),
    # the round-3 review of PR #54 by Sol (round 4: composition, sweeps over the effective interface)
    ("R1: Session delegates to its engine, so the spike's complete_script() and run_step() are reachable", [(
        S, "    def __setattr__(self, name, value):",
        "    def __getattr__(self, name):\n        return getattr(self._engine, name)\n\n    def __setattr__(self, name, value):")],
     [T + "CompletionRouteTest.test_complete_script_is_no_route_to_completed",
      T + "GuardSweepTest.test_session_is_not_a_cycle_and_does_not_delegate",
      T + "GuardSweepTest.test_no_method_of_the_spike_is_reachable_on_a_session"]),
    ("R1: the engine no longer refuses the spike's complete_script()", [(
        S, '    SPIKE_ONLY = ("complete_script", "run_script",', '    SPIKE_ONLY = ("run_script",')],
     [T + "GuardSweepTest.test_the_engine_refuses_the_spikes_own_routes",
      T + "CompletionRouteTest.test_complete_script_is_no_route_to_completed"]),
    ("R3: Session inherits the spike's Cycle again (round 3's structure)", [(
        S, "class Session:\n", "class Session(spike.Cycle):\n")],
     [T + "GuardSweepTest.test_session_is_not_a_cycle_and_does_not_delegate",
      T + "GuardSweepTest.test_no_method_of_the_spike_is_reachable_on_a_session",
      T + "DeadGameStepTest"]),
    ("R3: an unguarded public run_step() on Session (Sol's route, on the facade)", [(
        S, "    # ---- what does not touch the game\n",
        "    def run_step(self, step):\n        return self._engine.run_step(step)\n\n    # ---- what does not touch the game\n")],
     [T + "GuardSweepTest.test_every_public_method_of_the_effective_interface_is_guarded_or_a_stated_exception",
      T + "GuardSweepTest.test_no_method_of_the_spike_is_reachable_on_a_session",
      T + "DeadGameStepTest"]),
    ("R3: perform() is marked unguarded instead of guarded", [(
        S, '    @guarded("a step")\n    def perform(self, text):', '    @unguarded("none")\n    def perform(self, text):')],
     [T + "GuardSweepTest.test_every_public_method_of_the_effective_interface_is_guarded_or_a_stated_exception"]),
    ("R2: a session refused before its snapshot is recovered (round 3's rule)", [(
        S, '        self.recovered = snapshot and all(self.cleaned.values()) and self.cleaned.get("snapshot and reset") is True',
        '        self.recovered = all(self.cleaned.values()) and (not snapshot or self.cleaned.get("snapshot and reset") is True)')],
     [T + "RefusedSessionRecoveryTest"]),
    ("R4: Cycle.run_step's key as a bounded raw subprocess.run (Sol's mutant)", [(
        C, '            must(["xdotool", "key", args[0]], env=self.env, require_output=False)',
        '            subprocess.run(["xdotool", "key", args[0]], env=self.env, timeout=RUN_TIMEOUT)')],
     [T + "CommandHelperSweepTest.test_no_raw_or_unchecked_command_on_the_drivers_path"]),
    ("R4: Cycle.run_step's key as an unchecked run()", [(
        C, '            must(["xdotool", "key", args[0]], env=self.env, require_output=False)',
        '            run(["xdotool", "key", args[0]], env=self.env)')],
     [T + "CommandHelperSweepTest.test_no_raw_or_unchecked_command_on_the_drivers_path"]),
    ("R4: a raw subprocess call in the setup module the driver runs (prefix.py, on the path)", [(
        "setup/iwp/prefix.py", "def prefix_problems(prefix, install=None):\n",
        "def prefix_problems(prefix, install=None):\n    subprocess.run([\"true\"])\n")],
     [T + "CommandHelperSweepTest.test_no_raw_or_unchecked_command_on_the_drivers_path"]),
    ("R4: an excluded spike method comes back on the path (the engine stops refusing hover_click)", [(
        S, '    SPIKE_ONLY = ("complete_script", "run_script", "load_script", "session", "input", "hover_click",',
        '    SPIKE_ONLY = ("complete_script", "run_script", "load_script", "session", "input",')],
     [T + "CommandHelperSweepTest.test_the_off_path_exclusions_are_off_the_path"]),
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
