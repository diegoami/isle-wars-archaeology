#!/usr/bin/env python3
"""T12 Done-when 3: remove each guarantee that depends on the pinned tools in turn, and show that
its tests then fail (CLAUDE.md rule 9). Usage, from the repository root, with TMPDIR set to a short
directory outside every checkout: python3 experiments/T12-tool-migration/measurements/mutants.py

Each mutant replaces one exact piece of source (it must occur exactly once), runs the named tests,
and restores the file whatever happens. A mutant is killed when the tests fail. The script exits 0
only when every mutant is killed and the unmutated tests pass; it exits 2 when a target test skips
(a skip shows nothing). It edits tracked files while it runs: run it in a clean worktree.
Same shape as tests/mutants_iw_dos.py.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEAL = "tests.test_register_artifact.SealCallersTest."
FORMATS = "tests.test_formats."
RUNS = "tests.test_runs.RunRecordsTest."
MUTANTS = [
    ("prefix.py's game-copy check accepts a changed byte", "setup/iwp/prefix.py",
     "[d for d in differences if d not in unobservable]", '[d for d in differences if "sha256" not in d]',
     [SEAL + "test_the_prefix_game_copy_check_refuses_each_damage"]),
    ("prefix.py's game-copy check accepts an unlisted file", "setup/iwp/prefix.py",
     "tool.compare(observed, wanted, strict=True)", "tool.compare(observed, wanted, strict=False)",
     [SEAL + "test_the_prefix_game_copy_check_refuses_each_damage"]),
    ("prefix.py's game-copy check drops what the tool's tree walk reports (a name it refuses)", "setup/iwp/prefix.py",
     "return problems + unobservable + [d", "return problems + [d",
     [SEAL + "test_the_prefix_game_copy_check_reports_what_the_tool_cannot_observe"]),
    ("rundir.py's check drops --strict", "setup/iw-dos/rundir.py",
     'str(game), SET_ID, "--strict"]', "str(game), SET_ID]",
     [SEAL + "test_the_dos_run_copy_check_runs_strict",
      SEAL + "test_the_dos_run_copy_check_passes_and_refuses_each_damage",
      "tests.test_iw_dos_seal.RunCopyTest.test_a_copy_that_fails_check_strict_is_refused"]),
    ("a record with a duplicate key validates (the repository's reader is json.loads again)", "tests/test_runs.py",
     "doc = validate_records.load_file(path)", 'doc = json.loads(Path(path).read_text(encoding="utf-8"))',
     [RUNS + "test_a_record_with_a_duplicate_key_fails"]),
    ("a record with a duplicate key validates (the pinned validator keeps the last value)", "tools/validate_records.py",
     "object_pairs_hook=_unique_keys", "object_pairs_hook=dict",
     [FORMATS + "ValidatorStrictnessTest", RUNS + "test_a_record_with_a_duplicate_key_fails"]),
    ("one vendored byte of the validator changes", "tools/validate_records.py",
     "never an exception", "never an exceptio",
     [FORMATS + "PinnedBytesTest.test_archaeology_pins_each_vendored_hash"]),
]


def tests_pass(ids):
    done = subprocess.run([sys.executable, "-m", "unittest", "-v"] + ids, cwd=ROOT, capture_output=True, text=True)
    skipped = [line for line in done.stderr.splitlines() if " ... skipped" in line]
    if skipped:
        print("STOPPED: target tests skipped, so no mutant can be shown killed:")
        print("\n".join("  " + line[:300] for line in skipped[:5]))
        sys.exit(2)
    return done.returncode == 0


def main():
    ids = sorted({i for *_, group in MUTANTS for i in group})
    if not tests_pass(ids):
        print("the unmutated tests fail; nothing to show")
        return 1
    print(f"unmutated: {len(ids)} test id(s) pass")
    survived = 0
    for what, rel, old, new, group in MUTANTS:
        path = ROOT / rel
        original = path.read_text(encoding="utf-8")
        if original.count(old) != 1:
            print(f"BAD MUTANT ({original.count(old)} matches): {what}")
            survived += 1
            continue
        try:
            path.write_text(original.replace(old, new), encoding="utf-8")
            killed = not tests_pass(group)
        finally:
            path.write_text(original, encoding="utf-8")
        print(f"{'killed  ' if killed else 'SURVIVED'} {what} ({rel}; {len(group)} test id(s))")
        survived += not killed
    print(f"{len(MUTANTS) - survived} of {len(MUTANTS)} mutants killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
