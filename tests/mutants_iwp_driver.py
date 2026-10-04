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


def main():
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
