#!/usr/bin/env python3
"""Remove each guarantee of the iw-dos seal in turn and show that its tests then fail (T11
Done-when 3, CLAUDE.md rule 9). Usage: python3 tests/mutants_iw_dos.py

Each mutant replaces one exact piece of source (it must occur exactly once), runs the named tests,
and restores the file whatever happens. A mutant is killed when the tests fail. The script exits 0
only when every mutant is killed and the unmutated tests pass. It edits tracked files while it runs:
run it in a clean worktree, never alongside a recorded cycle run.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = "tests.test_iw_dos_seal."
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
    ("a cycle without its screenshots is completed", "runtime/iw-dos/spike/cycle.py",
     "        if missing:\n            self.fail(\"the cycle ended without", "        if False:\n            self.fail(\"the cycle ended without",
     [T + "InnerTest.test_a_cycle_without_its_screenshots_is_never_completed"]),
]


def tests_pass(ids):
    done = subprocess.run([sys.executable, "-m", "unittest", "-q"] + ids, cwd=ROOT, capture_output=True, text=True)
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
