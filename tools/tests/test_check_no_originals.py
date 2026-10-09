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
        """Done-when 2: a non-wine record passes even with a hash no F019 row names. The check reads
        only records whose platform names `wine`; the existing checks do the rest. T48 (#149)
        adapted the platform: `linux-wsl2/wine-xvfb-xfwm4` *names* wine and is now the legacy
        branch's business, so the platform here carries no `wine` at all."""
        record = wine_record(sha256="f" * 64, platform="windows-native-bandicam")
        self.assertEqual(cno.check_wine_gate(record, TABLE), ("", ""))

    def test_the_platform_prefix_is_case_sensitive(self):
        """The chosen contract: the carve-out's prefix is matched case-sensitively, so
        `Wine-On-User-Machine` is not the carve-out platform; a case-insensitive comparison here
        would be the mutation this test kills. T48 (#149) adapted what follows from that: not the
        carve-out platform used to mean *not this gate's business*, and a record carrying this
        spelling with an unlisted hash passed. Any platform that names `wine` in any case now
        reaches the legacy branch, so such a record is refused unless tools/legacy_wine_records.txt
        lists its path with the file's sha256 — refused here, with the reason named."""
        record = wine_record(sha256="f" * 64, platform="Wine-On-User-Machine")
        problem, warning = cno.check_wine_gate(record, TABLE)
        self.assertNotEqual(problem, "")
        self.assertTrue(problem.startswith(GATE_CODE), problem)
        self.assertIn("Wine-On-User-Machine", problem)
        self.assertEqual(warning, "")

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
        # T48: `linux-wsl2/wine-xvfb-xfwm4` was this test's non-wine platform until the legacy
        # Wine records were found to slip past constraint F (#149); a platform without `wine` now.
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64, platform="windows-native-bandicam"))
            result = run_tool(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_cli_refuses_an_unrecognised_suffix_wine_record(self):
        """Sol's R1 at the CLI level: the whole check refuses an unrecognised suffix even when
        the hash, set and variant match the F019 row, and names the platform and its suffix."""
        platform = WINE + "-iwp-2.0-evil-suffix"
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(platform=platform))
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(GATE_CODE, result.stdout)
            self.assertIn(platform, result.stdout)

    def test_the_cli_passes_a_recognised_suffix_wine_record(self):
        """The other half of the CLI contract: the task file's legitimate suffixed platform
        passes end to end when its hash, set and variant match the F019 row."""
        platform = WINE + "-iwp-2.0"
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(platform=platform))
            result = run_tool(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_wine_gate_skips_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64))
            result = run_tool(repo, "--no-wine-gate")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


# T48 (#149): the legacy Wine platform. Two emitters wrote `linux-wsl2/wine-xvfb-xfwm4` instead of
# the carve-out's token, so constraint F never saw their 274 records, and their
# `start_state.sha256` is a prefix listing's hash, not the binary's. Records are immutable (rule
# 20): they are listed by repo-relative path and file sha256 in tools/legacy_wine_records.txt, and
# any other record whose platform contains `wine` (any case) and is not a recognised carve-out
# platform is refused. These tests were pushed before dispatch (L64): one per bypass class; they
# fail until the gate lands.
LEGACY = "linux-wsl2/wine-xvfb-xfwm4"
LEGACY_LIST = Path("tools") / "legacy_wine_records.txt"
RECORD = "runs/E002/E002-r0001.json"


def list_records(repo, *paths, spelled=None):
    """Write the legacy list naming each path with its file's current sha256 (or `spelled`)."""
    lines = []
    for rel in paths:
        digest = cno.sha256_file(repo / rel)
        lines.append(f"{digest}  {spelled or rel}")
    (repo / LEGACY_LIST).parent.mkdir(parents=True, exist_ok=True)
    (repo / LEGACY_LIST).write_text("\n".join(lines) + "\n", encoding="utf-8")


class LegacyWinePlatformTest(unittest.TestCase):
    """T48: a `wine` platform that is not the carve-out's passes only as a listed legacy record."""

    def refused(self, result, path=RECORD):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(path, result.stdout)

    def test_an_unlisted_legacy_record_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64, platform=LEGACY))
            list_records(repo)
            self.refused(run_tool(repo))

    def test_a_listed_legacy_record_with_its_listed_bytes_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64, platform=LEGACY))
            list_records(repo, RECORD)
            result = run_tool(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_a_listed_legacy_record_whose_bytes_changed_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            path = place_record(repo, wine_record(sha256="a" * 64, platform=LEGACY))
            list_records(repo, RECORD)
            record = json.loads(path.read_text(encoding="utf-8"))
            record["start_state"]["sha256"] = "b" * 64
            path.write_text(json.dumps(record), encoding="utf-8")
            self.refused(run_tool(repo))

    def test_a_copy_of_a_listed_record_at_a_new_path_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            path = place_record(repo, wine_record(sha256="a" * 64, platform=LEGACY))
            list_records(repo, RECORD)
            copy_rel = "runs/E002/E002-r0002.json"
            (repo / copy_rel).write_bytes(path.read_bytes())
            subprocess.run(["git", "add", copy_rel], cwd=repo, check=True)
            self.refused(run_tool(repo), copy_rel)

    def test_a_listed_path_spelled_another_way_does_not_list_the_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64, platform=LEGACY))
            for spelled in ("./" + RECORD, "runs/E002/../E002/E002-r0001.json", RECORD.upper()):
                with self.subTest(spelled=spelled):
                    list_records(repo, RECORD, spelled=spelled)
                    self.refused(run_tool(repo))

    def test_wine_in_any_case_or_place_is_refused_when_unlisted(self):
        for platform in ("Linux-WSL2/WINE-xvfb-xfwm4", "LINUX-WSL2/WINE", "wine", "x-Wine-y",
                         "Wine-On-User-Machine", "wine-on-user-machine-iwp-2.0-evil-suffix"):
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(tmp)
                write_f019(repo)
                place_record(repo, wine_record(sha256="a" * 64, platform=platform))
                list_records(repo)
                self.refused(run_tool(repo))

    def test_the_list_never_admits_a_carve_out_record_off_the_f019_table(self):
        """The list is for legacy platforms only: a record with the carve-out's token and an
        unknown binary hash stays refused even when it is listed."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64, platform=WINE + "-iwp-2.0"))
            list_records(repo, RECORD)
            self.refused(run_tool(repo))

    def test_a_platform_without_wine_is_not_this_gates_business(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64, platform="windows-native-bandicam"))
            list_records(repo)
            result = run_tool(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_repositorys_list_holds_the_274_legacy_records_unchanged(self):
        """Done-when 2: the list on this branch names exactly the legacy records main held when T48
        was written (afb5353's census), each with its file's sha256."""
        lines = (ROOT / LEGACY_LIST).read_text(encoding="utf-8").splitlines()
        entries = [line.split("  ", 1) for line in lines if line.strip()]
        self.assertEqual(len(entries), 274)
        self.assertEqual(len({rel for _, rel in entries}), 274)
        for digest, rel in entries:
            with self.subTest(rel=rel):
                self.assertTrue(rel.startswith("runs/") and rel.endswith(".json"), rel)
                self.assertEqual(cno.sha256_file(ROOT / rel), digest)


class LegacyWineReviewBypassTest(unittest.TestCase):
    """T48 round 1, Sol's R1 and R2 (PR #151): three more bypass classes, each its own test, pushed
    before round 2 (L64). Each places a complete legacy-Wine record with an unknown binary hash and
    no listing, and expects the check to refuse it."""

    def test_unicode_wine_platform_cannot_bypass_the_gate(self):
        """R1: `.lower()` and a substring test miss Unicode spellings of `wine`: fullwidth letters,
        the dotted capital I, a Cyrillic look-alike. A platform the gate cannot classify in plain
        ASCII is refused, never passed as "no wine"."""
        for platform in ("linux/\uff37\uff29\uff2e\uff25-x",      # fullwidth WINE
                         "linux/W\u0130NE-x",                        # dotted capital I
                         "linux-wsl2/w\u0456ne-xvfb",                # Cyrillic i
                         "w\u0456ne-on-user-machine-iwp-2.0",        # the carve-out token, one look-alike
                         "linux-wsl2/wi\u200bne-xvfb"):              # a zero-width space inside
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(tmp)
                write_f019(repo)
                place_record(repo, wine_record(sha256="a" * 64, platform=platform))
                list_records(repo)
                result = run_tool(repo)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(RECORD, result.stdout)

    def test_wine_record_outside_runs_is_refused(self):
        """R2a: run records live under runs/ only. A tracked run/1 document anywhere else is refused,
        so a record cannot leave the gate's walk by moving."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            record = dict(wine_record(sha256="a" * 64, platform=LEGACY), schema="run/1")
            (repo / "wine-record.json").write_text(json.dumps(record), encoding="utf-8")
            subprocess.run(["git", "add", "wine-record.json"], cwd=repo, check=True)
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("wine-record.json", result.stdout)

    def test_symlinked_run_directory_cannot_hide_a_wine_record(self):
        """R2b: a symlinked directory under runs/ (pointing outside the repository) must not hide
        the records behind it: the check refuses the link, or follows it and gates the record."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            outside = Path(tmp) / "elsewhere" / "E003"
            outside.mkdir(parents=True)
            (outside / "E003-r0001.json").write_text(
                json.dumps(wine_record(sha256="a" * 64, platform=LEGACY)), encoding="utf-8")
            (repo / "runs" / "E003").symlink_to(outside, target_is_directory=True)
            subprocess.run(["git", "add", "runs/E003"], cwd=repo, check=True)
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("runs/E003", result.stdout)


class LegacyWineRoundTwoTest(unittest.TestCase):
    """T48 round 2's own edges, beside the main session's three (L64): what the R1 and R2 fixes also
    refuse, and what they must still let through."""

    def test_an_ascii_control_character_in_the_platform_is_refused(self):
        """R1's rule is printable ASCII, not merely ASCII: `wi\\x00ne` would also hide `wine` from a
        substring test."""
        record = wine_record(sha256="a" * 64, platform="linux-wsl2/wi\x00ne-xvfb")
        problem, _ = cno.check_wine_gate(record, TABLE, legacy_ok=True)
        self.assertIn(GATE_CODE, problem)
        self.assertIn("plain printable ASCII", problem)

    def test_a_non_wine_run_document_outside_runs_still_passes(self):
        """R2 gates run/1 documents outside runs/, it does not refuse them: the format examples under
        formats/examples/ are run/1 documents with a platform naming no wine, and they pass."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            (repo / "formats").mkdir()
            record = dict(wine_record(sha256="a" * 64, platform="python-3.12/ubuntu-24.04"), schema="run/1")
            (repo / "formats" / "example.json").write_text(json.dumps(record), encoding="utf-8")
            subprocess.run(["git", "add", "formats/example.json"], cwd=repo, check=True)
            result = run_tool(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_a_tracked_json_symlink_outside_runs_is_refused(self):
        """A tracked `*.json` symlink outside runs/ could point at a run record outside the
        repository; the gate refuses it by name instead of following it."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            outside = Path(tmp) / "elsewhere.json"
            outside.write_text(json.dumps(dict(wine_record(sha256="a" * 64, platform=LEGACY),
                                               schema="run/1")), encoding="utf-8")
            (repo / "linked.json").symlink_to(outside)
            subprocess.run(["git", "add", "linked.json"], cwd=repo, check=True)
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("linked.json", result.stdout)

    def test_a_symlinked_record_file_under_runs_is_refused_even_when_its_target_is_listed(self):
        """A symlinked record under runs/ is refused as a link, whatever it points at: here at a
        listed record with its listed bytes, which would pass if the link were followed."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            place_record(repo, wine_record(sha256="a" * 64, platform=LEGACY))
            (repo / "runs" / "E002" / "E002-r0002.json").symlink_to("E002-r0001.json")
            subprocess.run(["git", "add", "runs/E002/E002-r0002.json"], cwd=repo, check=True)
            list_records(repo, RECORD, "runs/E002/E002-r0002.json")
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("runs/E002/E002-r0002.json", result.stdout)
            self.assertIn("symlink", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
