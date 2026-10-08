"""Mutation tests for T36's constraint-F gate in tools/check_no_originals.py.

The gate is the load-bearing piece of the rule 18 carve-out (CLAUDE.md, 2026-10-08): a run
record whose `runtime.platform` starts with `wine-on-user-machine` is allowed only when its
`start_state.sha256` is the F019-known `Islepro.exe` hash for the `artifact.set` and
`artifact.variant` the record names. Without the gate, a model could write a run record that
merely claims the platform and CI would accept it.

These tests are `unittest.TestCase`, so the brief's `python3 -m pytest
tools/tests/test_check_no_originals.py` and `python3 -m unittest discover -s tools/tests` both
run them. `tests/test_check_no_originals.py` loads this module so CI's `unittest discover -s
tests` runs them too.

The case contract these tests pin: the platform prefix is matched case-sensitively
(`wine-on-user-machine`, never `Wine-On-User-Machine`), the same contract
`experiments/E017-pro-setup-reading/check_known_good_hashes.py` pins on the row side.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "check_no_originals.py"
sys.path.insert(0, str(ROOT / "tools"))
import check_no_originals as cno  # noqa: E402  (the tool under test, beside this file)

WINE = "wine-on-user-machine"
SET_ID = "iwp-2.0-996e86c5"
VARIANT = "unregistered"
KNOWN_HASH = "c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e"
PLACEHOLDER = "0" * 64
GATE_CODE = "[E036]"

# The T35 row, as findings/F019-pro-setup-rules.md holds it.
TABLE = [{
    "set": SET_ID,
    "variant": VARIANT,
    "file": "Islepro.exe",
    "sha256": KNOWN_HASH,
    "install_path": "/mnt/c/Users/<owner>/Downloads/Isle-Wars-Pro_Win_EN_v20-Shareware/",
    "signed_on": "2026-10-08",
}]


def wine_record(sha256=KNOWN_HASH, set_id=SET_ID, variant=VARIANT, platform=WINE):
    """A run-record shape with just the fields constraint F reads (run/1's paths)."""
    return {
        "runtime": {"platform": platform},
        "artifact": {"set": set_id, "variant": variant},
        "start_state": {"sha256": sha256},
    }


def run_tool(repo, *args):
    return subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=repo, capture_output=True, text=True
    )


def make_repo(tmp):
    repo = Path(tmp) / "repo"
    (repo / "runs" / "E002").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def write_f019(repo, table=TABLE):
    """Write a Known-good binary hashes section, as T35's finding holds it."""
    lines = [
        "## Known-good binary hashes",
        "",
        "| Set | Variant | File | sha256 | Install path | Signed on |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in table:
        lines.append(
            f"| `{row['set']}` | `{row['variant']}` | `{row['file']}` | `{row['sha256']}` "
            f"| `{row['install_path']}` | `{row['signed_on']}` |"
        )
    path = repo / "findings" / "F019-pro-setup-rules.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def place_record(repo, record):
    path = repo / "runs" / "E002" / "E002-r0001.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    subprocess.run(["git", "add", "runs/E002/E002-r0001.json"], cwd=repo, check=True)
    return path


class WineGateUnitTest(unittest.TestCase):
    """The gate function itself, mutation by mutation."""

    def test_a_matching_wine_record_passes(self):
        """Done-when 3: the T35 row's set, variant and hash pass the gate."""
        self.assertEqual(cno.check_wine_gate(wine_record(), TABLE), ("", ""))

    def test_removing_the_wine_platform_leaves_the_record_passing(self):
        """Done-when 2: a non-wine record passes even with a hash no F019 row names. The
        check reads only `wine-on-user-machine` records; the existing checks do the rest."""
        record = wine_record(sha256="f" * 64, platform="linux-wsl2/wine-xvfb-xfwm4")
        self.assertEqual(cno.check_wine_gate(record, TABLE), ("", ""))

    def test_the_platform_prefix_is_case_sensitive(self):
        """The chosen contract: `Wine-On-User-Machine` is NOT the carve-out platform, so a
        record carrying that spelling (and an unlisted hash) is not this gate's business. A
        case-insensitive comparison here would be the mutation this test kills."""
        record = wine_record(sha256="f" * 64, platform="Wine-On-User-Machine")
        self.assertEqual(cno.check_wine_gate(record, TABLE), ("", ""))

    def test_an_unrecognised_platform_suffix_is_refused(self):
        """Sol's R1: a platform that *starts with* `wine-on-user-machine` but carries a suffix
        the task file does not name is refused even when its hash, set and variant match the
        F019 row, and the refusal names the unexpected suffix. This fails under R1's mutation
        (`startswith` -> `==` in the gate), because the mutation returns early and passes the
        record instead of reaching the suffix check — that failure is the proof the test
        catches the bypass. The legitimate suffix is matched exactly, so
        `wine-on-user-machine-iwp-2.0-evil-suffix` is refused too, not accepted by prefix."""
        self.assertIn("-iwp-2.0", cno.RECOGNISED_WINE_SUFFIXES)  # Done-when 5: named constant
        for platform in (
            WINE + "-evil-suffix",
            WINE + "-iwp-2.0-evil-suffix",
            WINE + "-iwp-2.0x",
        ):
            with self.subTest(platform=platform):
                problem, warning = cno.check_wine_gate(wine_record(platform=platform), TABLE)
                self.assertNotEqual(problem, "")
                self.assertTrue(problem.startswith(GATE_CODE), problem)
                self.assertIn(platform, problem)
                self.assertIn(platform[len(WINE):], problem)  # names the unexpected suffix
                self.assertEqual(warning, "")

    def test_a_recognised_platform_suffix_is_accepted(self):
        """Constraint C names `wine-on-user-machine-iwp-2.0` as a legitimate more specific
        token, so a record on it, with the F019 row's hash, set and variant, passes. It must
        pass under R1's `==` mutation too: the mutation returns `("", "")` before the hash
        check, which is exactly the pass this contract case expects."""
        platform = WINE + "-iwp-2.0"
        self.assertEqual(cno.check_wine_gate(wine_record(platform=platform), TABLE), ("", ""))

    def test_an_empty_f019_table_refuses_every_wine_record(self):
        """Done-when 2: with no rows, every wine-on-user-machine record is refused. This is
        the fail-closed direction while T35 has not landed."""
        problem, warning = cno.check_wine_gate(wine_record(), [])
        self.assertNotEqual(problem, "")
        self.assertIn(KNOWN_HASH, problem)  # names the row it got
        self.assertIn("empty or missing", problem)  # and why no row was expected

    def test_an_unlisted_wine_hash_is_refused_with_the_code(self):
        problem, warning = cno.check_wine_gate(wine_record(sha256="a" * 64), TABLE)
        self.assertTrue(problem.startswith(GATE_CODE), problem)
        self.assertIn("a" * 64, problem)
        self.assertEqual(warning, "")

    def test_a_hash_match_with_a_foreign_set_or_variant_names_both_rows(self):
        """The T35 row is set+variant-keyed: a matching hash under a wrong set or variant is
        a misconfigured run, and the refusal names the row it expected and the row it got."""
        problem, _ = cno.check_wine_gate(wine_record(set_id="iw-dos-3.1-30121376"), TABLE)
        self.assertIn(KNOWN_HASH, problem)
        self.assertIn("iw-dos-3.1-30121376", problem)
        self.assertIn(SET_ID, problem)
        problem, _ = cno.check_wine_gate(wine_record(variant="registered"), TABLE)
        self.assertIn("registered", problem)
        self.assertIn(VARIANT, problem)

    def test_the_all_zero_placeholder_is_refused_by_name(self):
        """Done-when 4: T28's `0000…0000` ("no save file") must not pass as a known-good
        binary hash, and the refusal must name the placeholder."""
        problem, _ = cno.check_wine_gate(wine_record(sha256=PLACEHOLDER), TABLE)
        self.assertNotEqual(problem, "")
        self.assertIn("placeholder", problem)
        self.assertIn(PLACEHOLDER, problem)

    def test_the_gate_does_not_mutate_the_record(self):
        """Rule 20: the check inspects the record, never writes to it."""
        record = wine_record(sha256="a" * 64)
        before = copy.deepcopy(record)
        cno.check_wine_gate(record, TABLE)
        self.assertEqual(record, before)

    def test_a_missing_field_is_refused_not_crashed(self):
        """A wine record with no artifact or start_state cannot match a row: fail closed."""
        problem, _ = cno.check_wine_gate({"runtime": {"platform": WINE}}, TABLE)
        self.assertNotEqual(problem, "")


class WineGateCliTest(unittest.TestCase):
    """The CLI runs the gate by default, and `--no-wine-gate` skips only it."""

    def test_the_cli_refuses_an_unlisted_wine_record_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64))
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("runs/E002/E002-r0001.json", result.stdout)
            self.assertIn(GATE_CODE, result.stdout)

    def test_the_cli_passes_a_matching_wine_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record())
            result = run_tool(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_cli_passes_a_non_wine_record_with_an_unlisted_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64, platform="linux-wsl2/wine-xvfb-xfwm4"))
            result = run_tool(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_wine_gate_skips_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64))
            result = run_tool(repo, "--no-wine-gate")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
