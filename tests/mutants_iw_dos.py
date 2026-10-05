#!/usr/bin/env python3
"""Remove each guarantee of the iw-dos seal in turn and show that its tests then fail (T11
Done-when 3, CLAUDE.md rule 9). Usage: python3 tests/mutants_iw_dos.py

Each mutant replaces one exact piece of source (it must occur exactly once), runs the named tests,
and restores the file whatever happens. A mutant is killed when the tests fail. The script exits 0
only when every mutant is killed and the unmutated tests pass; it exits 2, naming them, when any target test skips (a skip shows
nothing). It edits tracked files while it runs:
run it in a clean worktree, never alongside a recorded cycle run.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = "tests.test_iw_dos_seal."
T14 = "tests.test_iw_dos_steps."      # T14's additions (--steps, --experiment, the board reader)
MUTANTS = [
    ("a run directory inside a checkout is accepted", "setup/iw-dos/rundir.py",
     "found[name] = locations.confine(name, env[name], seen)", "found[name] = locations.real(env[name])",
     [T + "RunLocationsTest"]),
    ("the configuration's mount check is gone", "runtime/iw-dos/spike/dosconf.py",
     "    if mounts != [want]:", "    if False:",
     [T + "ConfTest", T + "LaunchGateTest.test_a_configuration_that_mounts_anything_else_aborts_before_launch"]),
    ("the launch does not check the configuration", "runtime/iw-dos/spike/cycle.py",
     "problems = dosconf.problems(text, self.game, self.workdir, self.command())", "problems = []",
     [T + "LaunchGateTest.test_a_configuration_that_mounts_anything_else_aborts_before_launch"]),
    ("the run copy check skips check --strict", "setup/iw-dos/rundir.py",
     "ok, text = strict_check(game, root)", 'ok, text = True, ""',
     [T + "RunCopyTest.test_a_copy_that_fails_check_strict_is_refused",
      T + "LaunchGateTest.test_a_run_copy_that_fails_check_strict_aborts_before_launch"]),
    ("the launch does not check the run copy", "runtime/iw-dos/spike/cycle.py",
     'command line."""\n        problems = rundir.run_problems(self.run_dir, self.install)',
     'command line."""\n        problems = []',
     [T + "LaunchGateTest.test_a_run_copy_that_fails_check_strict_aborts_before_launch"]),
    ("a capture failure is not recorded as aborted", "runtime/iw-dos/spike/cycle.py",
     '        except BaseException as exc:\n            self.abort_later(f"{type(exc).__name__}: {exc}")\n'
     '        self.cleanup("terminate"',
     '        except BaseException as exc:\n            pass\n        self.cleanup("terminate"',
     [T + "InnerTest.test_a_capture_failure_records_aborted_and_exits_1"]),
    ("a second name of a run copy file is not looked for", "setup/iw-dos/rundir.py",
     "            elif info.st_nlink != 1:", "            elif False:",
     [T + "RunCopyTest.test_a_hard_link_to_the_copy_is_found_and_sync_gives_the_run_copy_a_file_of_its_own"]),
    ("IW_DOS_DIR left writable is not refused", "runtime/iw-dos/spike/cycle.py",
     "if bind.returncode != 0 or remount.returncode != 0 or install_writable(install):", "if False:",
     [T + "LaunchGateTest.test_a_copy_that_stays_writable_aborts_before_anything"]),
    ("DOSBox-X in the outer network namespace is not refused", "runtime/iw-dos/spike/cycle.py",
     "if not self.outer_netns or theirs == self.outer_netns:", "if False:",
     [T + "LaunchGateTest.test_dosbox_x_in_the_outer_network_namespace_aborts"]),
    ("sync does not refuse a run directory that is IW_DOS_DIR through a bind mount (PR #37 R1)",
     "setup/iw-dos/rundir.py",
     "def refuse_aliases(run_dir, install):\n    problems = alias_problems(run_dir, install)",
     "def refuse_aliases(run_dir, install):\n    problems = []",
     [T + "MountAliasTest.test_a_run_copy_that_is_a_bind_mount_of_the_copy_is_refused_and_the_copy_keeps_its_files",
      T + "MountAliasTest.test_a_run_directory_that_is_a_bind_mount_of_the_copy_is_refused_and_nothing_is_created",
      T + "MountAliasTest.test_a_run_directory_below_an_alias_of_the_copy_is_refused"]),
    ("a cycle without its screenshots is completed", "runtime/iw-dos/spike/cycle.py",
     "        if missing:\n            self.fail(\"the cycle ended without", "        if False:\n            self.fail(\"the cycle ended without",
     [T + "InnerTest.test_a_cycle_without_its_screenshots_is_never_completed"]),
    # ---- T14: the step scripts, the files the game writes, the board reader, --experiment
    ("a script run is completed without the shots its script names", "runtime/iw-dos/spike/cycle.py",
     "stepscript.shot_names(self.script) if self.script", "[] if self.script",
     [T14 + "CompleteTest.test_a_script_run_needs_every_shot_the_script_names"]),
    ("an until that never comes does not abort", "runtime/iw-dos/spike/cycle.py",
     "        if seen is None:\n            self.shot(f\"until-failed", "        if False:\n            self.shot(f\"until-failed",
     [T14 + "NavigateTest.test_an_until_that_never_comes_aborts_and_the_run_is_not_completed"]),
    ("click-change does not click again", "runtime/iw-dos/spike/cycle.py",
     "for attempt in (1, 2, 3):", "for attempt in (1,):",
     [T14 + "MoreNavigateTest.test_click_change_clicks_again_when_the_game_ignored_the_click",
      T14 + "MoreNavigateTest.test_click_change_gives_up_after_three_clicks_and_aborts"]),
    ("a repeated click does not step the pointer off first", "runtime/iw-dos/spike/cycle.py",
     "                self.pointer = None\n            self.step_click(step, x, y, button)",
     "                pass\n            self.step_click(step, x, y, button)",
     [T14 + "MoreNavigateTest.test_click_change_clicks_again_when_the_game_ignored_the_click"]),
    ("a game-written file is kept under a class the manifest schema refuses", "runtime/iw-dos/spike/cycle.py",
     '"save" if p.upper().endswith(".SAV") else "measurement"', '"file"',
     [T14 + "WrittenFilesTest.test_the_manifest_of_a_run_that_kept_game_files_is_valid"]),
    ("click-until stops after one click", "runtime/iw-dos/spike/cycle.py",
     "for attempt in range(1, tries + 1):", "for attempt in range(1, 2):",
     [T14 + "MoreNavigateTest.test_click_until_clicks_one_roll_at_a_time_until_the_screen_shows_the_move_panel"]),
    ("click-until does not abort when the screen never comes", "runtime/iw-dos/spike/cycle.py",
     "        self.fail(f\"step {step - 100}: the expected screen did not appear after {tries} clicks",
     "        self.say(f\"step {step - 100}: the expected screen did not appear after {tries} clicks",
     [T14 + "MoreNavigateTest.test_click_until_gives_up_after_its_clicks_and_aborts"]),
    ("a click always moves the pointer first", "runtime/iw-dos/spike/cycle.py",
     "if self.pointer != (x, y):", "if True:",
     [T14 + "MoreNavigateTest.test_a_second_click_at_the_same_place_does_not_move_the_pointer_again"]),
    ("a game-written file of any size is put in an observation as hex", "runtime/iw-dos/spike/cycle.py",
     "if len(data) <= HEX_LIMIT:", "if True:",
     [T14 + "WrittenFilesTest.test_a_large_state_file_has_no_hex_and_a_small_one_has"]),
    ("a game-written file with any name is copied", "runtime/iw-dos/spike/cycle.py",
     "if len(entry) != 3 or not WRITTEN_NAME.fullmatch(p):", "if len(entry) != 3:",
     [T14 + "WrittenFilesTest.test_a_file_name_that_is_not_a_plain_dos_name_is_not_copied"]),
    ("an older savestate satisfies the wait", "runtime/iw-dos/spike/cycle.py",
     "        if path.is_file():\n            safeio.remove(", "        if False:\n            safeio.remove(",
     [T14 + "SavestateStepTest.test_an_older_savestate_is_removed_so_it_cannot_satisfy_the_wait"]),
    ("a savestate step is not recorded as I2", "runtime/iw-dos/spike/cycle.py",
     "    if used_savestate:", "    if False:",
     [T14 + "SavestateStepTest.test_a_run_with_a_savestate_step_is_recorded_as_i2_and_every_run_as_i1_for_its_screenshots"]),
    ("a script the grammar refuses is not stopped", "runtime/iw-dos/spike/cycle.py",
     "except (OSError, UnicodeDecodeError, stepscript.Refused) as exc:", "except (OSError, UnicodeDecodeError) as exc:",
     [T14 + "LoadScriptTest"]),
    ("the keys of the order and registration screens are allowed", "runtime/iw-dos/spike/navsteps.py",
     'KEYS = ("Return", "space", "Escape", "c", "e")', 'KEYS = ("Return", "space", "Escape", "c", "e", "u", "r")',
     [T14 + "ParseTest"]),
    ("the steps do not finish a run", "runtime/iw-dos/spike/cycle.py",
     "self.since_launch())\n        self.after_screen_ok = True", "self.since_launch())",
     [T14 + "NavigateTest.test_a_click_moves_the_pointer_inside_the_window_and_then_presses"]),
    ("the target may be of the attacker's own army", "runtime/iw-dos/spike/cycle.py",
     'if owners[m] and owners[m] != "blue"', "if owners[m]",
     [T14 + "ChooseAttackTest.test_a_country_of_the_same_army_is_never_the_target"]),
    ("touching countries are any within 30 pixels", "runtime/iw-dos/spike/board.py",
     "BORDER = 3 ", "BORDER = 30 ",
     [T14 + "BoardTest.test_a_gap_wider_than_the_border_is_not_touching"]),
    ("E005 bundles are looked for in E003_BUNDLES", "setup/iw-dos/rundir.py",
     'add(f"{experiment}_BUNDLES", need_bundles)', 'add("E003_BUNDLES", need_bundles)',
     [T14 + "ExperimentTest.test_the_bundles_of_e005_come_from_e005_bundles_and_are_confined"]),
    ("a run of E005 writes its record as E003", "runtime/iw-dos/spike/cycle.py",
     "    EXPERIMENT = args.experiment\n    locs = rundir.run_locations(need_bundles=True, explore=args.explore, experiment=EXPERIMENT)\n    run_dir",
     "    locs = rundir.run_locations(need_bundles=True, explore=args.explore, experiment=args.experiment)\n    run_dir",
     [T14 + "InnerE005Test"]),
    # ---- PR #58 round 1: one mutant per fix (R1-R4, R7, R8, R11), each killed by the test that visits it
    ("R1: the grammar takes a click on the notices' buttons", "runtime/iw-dos/spike/navsteps.py",
     "        if verb in CLICK_VERBS and forbidden(args[0], args[1]):", "        if False:",
     [T14 + "ForbiddenControlTest.test_every_click_verb_is_refused_on_both_buttons_and_on_the_band_s_corners",
      T14 + "ForbiddenControlTest.test_no_verb_of_the_grammar_takes_a_forbidden_point_except_the_polls_that_never_click"]),
    ("R1: click-until is not a click verb", "runtime/iw-dos/spike/navsteps.py",
     'CLICK_VERBS = ("click", "rclick", "click-change", "rclick-change", "click-until")',
     'CLICK_VERBS = ("click", "rclick", "click-change", "rclick-change")',
     [T14 + "ForbiddenControlTest.test_no_verb_of_the_grammar_takes_a_forbidden_point_except_the_polls_that_never_click"]),
    ("R1: the forbidden band leaves out the Upgrade button", "runtime/iw-dos/spike/navsteps.py",
     "FORBIDDEN = ((283, 287, 290, 33),)", "FORBIDDEN = ((283, 287, 150, 33),)",
     [T14 + "ForbiddenControlTest.test_every_click_verb_is_refused_on_both_buttons_and_on_the_band_s_corners"]),
    ("R1: the click itself does not refuse a forbidden point", "runtime/iw-dos/spike/cycle.py",
     "        if stepscript.forbidden(x, y):", "        if False:",
     [T14 + "ForbiddenControlTest.test_the_click_itself_refuses_a_forbidden_point_before_the_pointer_moves",
      T14 + "ForbiddenControlTest.test_click_mine_on_a_forbidden_point_is_refused_at_the_click"]),
    ("R1: a click is sent while the notices are up", "runtime/iw-dos/spike/cycle.py",
     "        if self.screen.notice_up():\n            self.shot(f\"notice-refused", "        if False:\n            self.shot(f\"notice-refused",
     [T14 + "ForbiddenControlTest.test_while_the_notices_are_up_no_click_is_sent"]),
    ("R1: any key is pressed while the notices are up", "runtime/iw-dos/spike/cycle.py",
     "        if key not in NOTICE_KEYS and self.screen.notice_up():", "        if False:",
     [T14 + "ForbiddenControlTest.test_while_the_notices_are_up_only_c_and_e_are_pressed"]),
    ("R1: one button frame is taken for the notices", "runtime/iw-dos/spike/cycle.py",
     "NOTICE_FRAME, NOTICE_COLOUR, NOTICE_MIN = (287, 291, 282, 25), (255, 85, 85), 400",
     "NOTICE_FRAME, NOTICE_COLOUR, NOTICE_MIN = (287, 291, 282, 25), (255, 85, 85), 200",
     [T14 + "ForbiddenControlTest.test_the_notice_detector_needs_both_button_frames"]),
    ("R2: a changed file of the set is kept", "runtime/iw-dos/spike/cycle.py",
     'if how == "changed" or p.upper() not in GAME_WRITTEN or p.upper() in set_names:',
     'if p.upper() not in GAME_WRITTEN or p.upper() in set_names:',
     [T14 + "WrittenFilesTest.test_a_file_the_run_copy_had_at_the_launch_is_never_kept_even_under_a_state_name"]),
    ("R2: any added file is kept", "runtime/iw-dos/spike/cycle.py",
     'if how == "changed" or p.upper() not in GAME_WRITTEN or p.upper() in set_names:',
     'if how == "changed" or p.upper() in set_names:',
     [T14 + "WrittenFilesTest.test_an_added_file_that_is_not_a_state_file_is_recorded_by_hash_only"]),
    ("R2: a name of the set is kept", "runtime/iw-dos/spike/cycle.py",
     'if how == "changed" or p.upper() not in GAME_WRITTEN or p.upper() in set_names:',
     'if how == "changed" or p.upper() not in GAME_WRITTEN:',
     [T14 + "WrittenFilesTest.test_a_state_name_that_is_a_name_of_the_set_is_never_kept"]),
    ("R2: the bytes of a set file under a state name are kept", "runtime/iw-dos/spike/cycle.py",
     "            if digest in set_hashes:", "            if False:",
     [T14 + "WrittenFilesTest.test_a_state_file_holding_the_bytes_of_a_set_file_is_never_kept"]),
    ("R3: --explore replaces an earlier run's outputs", "runtime/iw-dos/spike/cycle.py",
     'cycle.outputs = store_outputs(cycle, out, lambda name, _: f"{key}.{name}", "new")',
     'cycle.outputs = store_outputs(cycle, out, lambda name, _: f"{args.arm}.{name}", "replace")',
     [T14 + "ExploreNamesTest"]),
    ("R3: the analysis overwrites a table", "experiments/E005-iw-dos-state-inventory/scripts/analyze.py",
     'with open(Path(outdir) / name, "x", encoding="utf-8") as fh:', 'with open(Path(outdir) / name, "w", encoding="utf-8") as fh:',
     [T14 + "AnalysisWritesTest"]),
    ("R3: keep-explore replaces a kept file", "experiments/E005-iw-dos-state-inventory/scripts/keep-explore.py",
     'with open(target, "xb") as fh:', 'with open(target, "wb") as fh:',
     [T14 + "KeepExploreTest.test_a_kept_file_with_other_bytes_is_never_replaced_and_nothing_is_deleted"]),
    ("R3: done-when.sh writes over an output", "experiments/E005-iw-dos-state-inventory/scripts/done-when.sh",
     "  ( set -C; {", "  ( {",
     [T14 + "DoneWhenOutputsTest"]),
    ("R4: a probe runs around a step script", "runtime/iw-dos/spike/cycle.py",
     '    if args.steps and args.probe != "none":', "    if False:",
     [T14 + "ProbeRefusalTest.test_a_probe_with_steps_is_refused_before_anything_starts",
      T14 + "ProbeRefusalTest.test_inner_refuses_it_too"]),
    ("R4: the cycle restores after a script", "runtime/iw-dos/spike/cycle.py",
     '        if self.script:\n            self.fail("--probe savestate', '        if False:\n            self.fail("--probe savestate',
     [T14 + "ProbeRefusalTest.test_the_cycle_itself_never_restores_after_a_script"]),
    ("R4: a restoring probe is described as never restored", "runtime/iw-dos/spike/cycle.py",
     '    if args.probe == "savestate":\n        found.append(', '    if False:\n        found.append(',
     [T14 + "SavestateStepTest.test_every_operation_of_the_run_is_listed"]),
    ("R7: wait-stable times out and the run goes on", "runtime/iw-dos/spike/cycle.py",
     '            self.shot(f"not-stable-{step}.png", step)\n            self.fail(',
     '            self.shot(f"not-stable-{step}.png", step)\n            self.say(',
     [T14 + "RequiredWaitTest.test_wait_stable_that_times_out_aborts",
      T14 + "RequiredWaitTest.test_a_click_change_whose_screen_never_settles_aborts"]),
    ("R7: wait-change times out and the run goes on", "runtime/iw-dos/spike/cycle.py",
     '            self.shot(f"no-change-{step}.png", step)\n            self.fail(f"step {step - 100}: the screen did not change',
     '            self.shot(f"no-change-{step}.png", step)\n            self.say(f"step {step - 100}: the screen did not change',
     [T14 + "RequiredWaitTest.test_wait_change_that_times_out_aborts"]),
    ("R7: wait-exit times out and the run goes on", "runtime/iw-dos/spike/cycle.py",
     '            self.fail(f"step {step - 100}: DOSBox-X had not ended', '            self.say(f"step {step - 100}: DOSBox-X had not ended',
     [T14 + "RequiredWaitTest.test_wait_exit_that_times_out_aborts"]),
    ("R7: a click is sent on a screen that is never still", "runtime/iw-dos/spike/cycle.py",
     '                self.fail(f"step {step - 100}: the screen was not still', '                self.say(f"step {step - 100}: the screen was not still',
     [T14 + "RequiredWaitTest.test_a_click_on_a_screen_that_is_never_still_is_not_sent"]),
    ("R8: screenshots are not declared", "runtime/iw-dos/spike/cycle.py",
     "    found = [dict(SCREENSHOTS)]", '    found = [{"level": "I0", "what": "none"}]',
     [T14 + "SavestateStepTest.test_a_run_with_a_savestate_step_is_recorded_as_i2_and_every_run_as_i1_for_its_screenshots"]),
    ("R11: the click time is not recorded", "runtime/iw-dos/spike/cycle.py",
     '        self.observe(step, "process", f"{side} click at {x},{y}: seconds after launch", self.since_launch())\n', "",
     [T14 + "TimestampTest.test_clicks_and_step_ends_are_timed_from_the_launch"]),
    ("R11: the window time is the poll's", "runtime/iw-dos/spike/cycle.py",
     'seconds after launch", self.since_launch())\n        self.observe(1, "process", "DOSBox-X window position"',
     'seconds after launch", waited)\n        self.observe(1, "process", "DOSBox-X window position"',
     [T14 + "TimestampTest.test_the_window_is_timed_from_the_launch_too"]),
    ("R11: the first turn is timed from the end of the start click's waits", "experiments/E005-iw-dos-state-inventory/scripts/analyze.py",
     'out["start_click_to_human_turn_s"] = f"{float(done) - float(sent):.2f}"',
     'out["start_click_to_human_turn_s"] = poll',
     [T14 + "TurnDiffTest.test_the_first_human_turn_is_timed_from_the_first_start_click"]),
    ("R9: the turn table derives the armies placed from a rule", "experiments/E005-iw-dos-state-inventory/scripts/analyze.py",
     '\\tchoose-attack, read from the screen at turn 1"]',
     '\\tchoose-attack, read from the screen at turn 1; armies placed = Blue countries // 3 (min 2), the game\'s own rule"]',
     [T14 + "TurnDiffTest.test_the_turn_rows_carry_no_rule_formula"]),
]


def tests_pass(ids):
    """True when the tests pass. A skipped target test proves nothing either way, so any skip
    stops the script loudly instead of reading as a pass or a kill."""
    done = subprocess.run([sys.executable, "-m", "unittest", "-v"] + ids, cwd=ROOT, capture_output=True, text=True)
    skipped = [line for line in done.stderr.splitlines() if " ... skipped" in line]
    if skipped:
        print("STOPPED: target tests skipped, so no mutant can be shown killed:")
        print("\n".join("  " + line[:300] for line in skipped[:5]))
        print("Run with TMPDIR set to a directory outside every checkout (and unshare available).")
        sys.exit(2)
    return done.returncode == 0


def main():
    ids = sorted({i for *_, group in MUTANTS for i in group})
    if not tests_pass(ids):
        print("the unmutated tests fail; nothing to show")
        return 1
    survived = 0
    for what, rel, old, new, group in MUTANTS:
        path = ROOT / rel
        original = path.read_text()
        if original.count(old) != 1:
            print(f"BAD MUTANT ({original.count(old)} matches): {what}")
            survived += 1
            continue
        try:
            path.write_text(original.replace(old, new))
            killed = not tests_pass(group)
        finally:
            path.write_text(original)
        print(f"{'killed  ' if killed else 'SURVIVED'} {what} ({rel}; {len(group)} test id(s))")
        survived += not killed
    print(f"{len(MUTANTS) - survived} of {len(MUTANTS)} mutants killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
