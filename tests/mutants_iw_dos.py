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
     [T14 + "WrittenFilesTest.test_a_changed_file_is_labelled_changed_and_a_large_one_has_no_hex"]),
    ("a game-written file with any name is copied", "runtime/iw-dos/spike/cycle.py",
     "if len(entry) != 3 or not WRITTEN_NAME.fullmatch(p):", "if len(entry) != 3:",
     [T14 + "WrittenFilesTest.test_a_file_name_that_is_not_a_plain_dos_name_is_not_copied"]),
    ("an older savestate satisfies the wait", "runtime/iw-dos/spike/cycle.py",
     "        if path.is_file():\n            safeio.remove(", "        if False:\n            safeio.remove(",
     [T14 + "SavestateStepTest.test_an_older_savestate_is_removed_so_it_cannot_satisfy_the_wait"]),
    ("a savestate step is recorded as I0", "runtime/iw-dos/spike/cycle.py",
     "    if used_savestate:", "    if False:",
     [T14 + "SavestateStepTest.test_a_run_with_a_savestate_step_is_recorded_as_i2_and_one_without_as_i0"]),
    ("a script the grammar refuses is not stopped", "runtime/iw-dos/spike/cycle.py",
     "except (OSError, UnicodeDecodeError, stepscript.Refused) as exc:", "except (OSError, UnicodeDecodeError) as exc:",
     [T14 + "LoadScriptTest"]),
    ("the keys of the order and registration screens are allowed", "runtime/iw-dos/spike/navsteps.py",
     'KEYS = ("Return", "space", "Escape", "c", "e")', 'KEYS = ("Return", "space", "Escape", "c", "e", "u", "r")',
     [T14 + "ParseTest"]),
    ("the steps do not finish a run", "runtime/iw-dos/spike/cycle.py",
     "(100 + n, *args)\n        self.after_screen_ok = True", "(100 + n, *args)",
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
