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
    "install_path": "C:\\Program Files (x86)\\Solsoft\\Isle Wars Pro Game\\",
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
        formats/examples/ are run/1 documents with a platform naming no wine, and they pass.
        T49 (#154, the main session, rule 5): only formats/examples/ keeps that; the document moved
        there from formats/example.json, which the allowlist now refuses."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            (repo / "formats" / "examples" / "valid").mkdir(parents=True)
            record = dict(wine_record(sha256="a" * 64, platform="python-3.12/ubuntu-24.04"), schema="run/1")
            (repo / "formats" / "examples" / "valid" / "example.json").write_text(json.dumps(record), encoding="utf-8")
            subprocess.run(["git", "add", "formats/examples/valid/example.json"], cwd=repo, check=True)
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


class LegacyWineRoundThreeTest(unittest.TestCase):
    """T48 round 2, Sol's R1 (PR #151): discovery still depended on a `.json` name. Pushed before
    the narrow third round (L64, the owner's choice of 2026-10-09). A tracked run/1 document with a
    Wine platform, an unknown binary hash and no listing must be refused, whatever its name."""

    def test_tracked_wine_run_document_without_json_extension_is_refused(self):
        for rel in ("wine-record.txt", "wine-record", "runs/E002/E002-r0002.JSON", "docs/E002-r0003.Json"):
            with self.subTest(rel=rel), tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(tmp)
                write_f019(repo)
                list_records(repo)
                record = dict(wine_record(sha256="a" * 64, platform=LEGACY), schema="run/1")
                path = repo / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(record), encoding="utf-8")
                subprocess.run(["git", "add", rel], cwd=repo, check=True)
                result = run_tool(repo)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(rel, result.stdout)


class LegacyWineRoundThreeEncodingTest(unittest.TestCase):
    """T48 round 3, a neighbouring class: a run/1 Wine document whose bytes are JSON but not plain
    UTF-8 (a UTF-8 byte-order mark, UTF-16, UTF-32) was skipped as undecodable, inside `runs/` and
    out. JSON readers accept those encodings, so the gate reads them too."""

    def test_a_wine_run_document_in_another_json_encoding_is_refused(self):
        cases = (("runs/E002/E002-r0002.json", "utf-16"), ("docs/wine-record.json", "utf-8-sig"),
                 ("wine-record.txt", "utf-32"))
        for rel, encoding in cases:
            with self.subTest(rel=rel, encoding=encoding), tempfile.TemporaryDirectory() as tmp:
                repo = make_repo(tmp)
                write_f019(repo)
                list_records(repo)
                record = dict(wine_record(sha256="a" * 64, platform=LEGACY), schema="run/1")
                path = repo / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(json.dumps(record).encode(encoding))
                subprocess.run(["git", "add", rel], cwd=repo, check=True)
                result = run_tool(repo)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(rel, result.stdout)


class LegacyWineJsonShapeTest(unittest.TestCase):
    """T48 round 3, Sol's R1 and R2 (PR #151): JSON shapes that hid a record from content discovery.
    Pushed before the structural round the owner chose on 2026-10-09 (L64): every run/1 object in a
    tracked JSON value is gated, wherever it sits, and a candidate with a duplicate key is refused
    rather than read as its last value. Each case is a Wine record with an unknown binary hash and
    no listing, so each must be refused."""

    BODY = ('"runtime": {"platform": "linux-wsl2/wine-xvfb-xfwm4"}, '
            '"artifact": {"set": "iwp-2.0-996e86c5", "variant": "unregistered"}, '
            '"start_state": {"sha256": "' + "a" * 64 + '"}')

    def check_refused(self, rel, text):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            subprocess.run(["git", "add", rel], cwd=repo, check=True)
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(rel, result.stdout)

    def test_a_duplicate_schema_key_cannot_hide_a_wine_record(self):
        for order in (('"schema": "run/1", ', '"schema": "other", '),
                      ('"schema": "other", ', '"schema": "run/1", ')):
            with self.subTest(order=order):
                self.check_refused("duplicate.txt", "{" + order[0] + order[1] + self.BODY + "}")

    def test_a_duplicate_platform_key_cannot_hide_a_wine_record(self):
        text = ('{"schema": "run/1", "runtime": {"platform": "linux-wsl2/wine-xvfb-xfwm4", '
                '"platform": "windows-native-bandicam"}, '
                '"artifact": {"set": "iwp-2.0-996e86c5", "variant": "unregistered"}, '
                '"start_state": {"sha256": "' + "a" * 64 + '"}}')
        for rel in ("runs/E002/E002-r0002.json", "elsewhere.json"):
            with self.subTest(rel=rel):
                self.check_refused(rel, text)

    def test_an_array_wrapped_wine_record_is_refused(self):
        self.check_refused("array.txt", '[{"schema": "run/1", ' + self.BODY + '}]')

    def test_a_wine_record_nested_in_another_object_is_refused(self):
        self.check_refused("nested.json", '{"data": [{"schema": "run/1", ' + self.BODY + '}]}')



class LegacyWineStructuralRoundTest(unittest.TestCase):
    """T48 structural round (the owner's choice, 2026-10-09): neighbouring JSON shapes the round
    closes with the same mechanism. Each refused case fails on d4a41a6's gate: the duplicate wrapper
    key drops the record before discovery, and the gate there neither walked below the top level nor
    survived a `RecursionError`."""

    BODY = LegacyWineJsonShapeTest.BODY

    def run_on(self, rel, text):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            subprocess.run(["git", "add", rel], cwd=repo, check=True)
            return run_tool(repo)

    def check_refused(self, rel, text):
        result = self.run_on(rel, text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(rel, result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_a_duplicate_wrapper_key_cannot_drop_a_nested_wine_record(self):
        self.check_refused("wrapper.json",
                           '{"data": {"schema": "run/1", ' + self.BODY + '}, "data": {}}')

    def test_a_wine_record_below_the_walk_bound_is_refused(self):
        depth = cno.MAX_JSON_DEPTH + 36
        self.check_refused("deep.json", "[" * depth + '{"schema": "run/1", ' + self.BODY + "}" + "]" * depth)

    def test_a_document_nested_100000_levels_is_refused_without_crashing(self):
        depth = 100_000
        self.check_refused("very-deep.json",
                           "[" * depth + '{"schema": "run/1", ' + self.BODY + "}" + "]" * depth)

    def test_a_nested_non_wine_run_record_still_passes(self):
        """T49 (#154, the main session, rule 5): a nested run/1 object is outside the allowlist, Wine
        or not, so this one is now refused (the name is kept so the diff removes no line of T48's)."""
        body = self.BODY.replace("linux-wsl2/wine-xvfb-xfwm4", "windows-native-bandicam")
        self.check_refused("nested-ok.json", '{"data": [{"schema": "run/1", ' + body + '}]}')

class LegacyWineParserLimitTest(unittest.TestCase):
    """T48 structural round, Sol's R1 and R2 (PR #151), pushed before the micro-round the owner chose
    on 2026-10-09 (L64). R1: a valid JSON document the default parser gives up on (an integer past
    Python's digit limit) was skipped as "not JSON", hiding the Wine record in it. R2: a nested run/1
    object whose fields are not the shapes the gate reads crashed the check with a traceback."""

    BODY = ('"runtime": {"platform": "linux-wsl2/wine-xvfb-xfwm4"}, '
            '"artifact": {"set": "iwp-2.0-996e86c5", "variant": "unregistered"}, '
            '"start_state": {"sha256": "' + "a" * 64 + '"}')

    def run_on(self, rel, text):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            subprocess.run(["git", "add", rel], cwd=repo, check=True)
            return run_tool(repo)

    def test_a_huge_integer_cannot_hide_a_wine_record(self):
        for big in ("9" * 5000, "-" + "1" * 5000, "1" + "0" * 5000 + "e1"):
            with self.subTest(digits=len(big)):
                result = self.run_on("large-number.txt",
                                     '{"n": ' + big + ', "data": {"schema": "run/1", ' + self.BODY + '}}')
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("large-number.txt", result.stdout)

    def test_odd_field_shapes_in_a_nested_record_never_crash_the_check(self):
        """No shape crashes the check. Malformed shapes without `wine` are the run validator's
        business (formats/examples/invalid/ holds such documents on purpose), so only no traceback."""
        for shape in ('"runtime": NaN', '"runtime": [1]', '"runtime": null', '"runtime": 5',
                      '"artifact": "x", "start_state": 5'):
            with self.subTest(shape=shape):
                result = self.run_on("nested.json", '{"data": {"schema": "run/1", ' + shape + '}}')
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_a_wine_bearing_malformed_nested_record_is_refused(self):
        """A run/1 object that names Wine in a shape the gate cannot read is refused (fail closed), with
        its path, and without a traceback."""
        for shape in ('"runtime": "wine"', '"runtime": ["linux-wsl2/wine-xvfb-xfwm4"]',
                      '"runtime": {"platform": "wine"}, "artifact": "x", "start_state": 5',
                      '"runtime": {"platform": "wine"}, "artifact": [], "start_state": {"sha256": 7}'):
            with self.subTest(shape=shape):
                result = self.run_on("nested.json", '{"data": {"schema": "run/1", ' + shape + '}}')
                self.assertNotIn("Traceback", result.stdout + result.stderr)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("nested.json", result.stdout)

class RunObjectAllowlistTest(unittest.TestCase):
    """T49 (#154, the owner's decision of 2026-10-09): a run/1 object is allowed only at the top
    level of a lowercase-.json file under runs/ (what tests/test_runs.py validates) or of a file under
    formats/examples/. Pushed before dispatch (L64). Sol's micro-round R1-R3 on PR #151 are here too."""

    PLAIN = ('"runtime": {"platform": "windows-native-bandicam"}, '
             '"artifact": {"set": "iwp-2.0-996e86c5", "variant": "unregistered"}, '
             '"start_state": {"sha256": "' + "a" * 64 + '"}')

    def run_on(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            for rel, text in files.items():
                path = repo / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                subprocess.run(["git", "add", rel], cwd=repo, check=True)
            return run_tool(repo)

    def refused(self, rel, text):
        result = self.run_on({rel: text})
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(rel, result.stdout)

    def test_a_non_wine_run_object_outside_the_two_places_is_refused(self):
        doc = '{"schema": "run/1", ' + self.PLAIN + '}'
        for rel in ("docs/example.json", "formats/example.json", "formats/examples-x/a.json",
                    "runs.json", "runsx/E002/a.json", "docs/runs/E002/a.json",
                    "runs/E002/E002-r0002.JSON", "runs/E002/E002-r0002.txt", "runs/E002/E002-r0002"):
            with self.subTest(rel=rel):
                self.refused(rel, doc)

    def test_a_run_object_nested_inside_an_allowed_file_is_refused(self):
        inner = '{"schema": "run/1", ' + self.PLAIN + '}'
        for rel, text in (("runs/E002/E002-r0002.json", '{"schema": "run/1", ' + self.PLAIN + ', "extra": ' + inner + '}'),
                          ("runs/E002/E002-r0003.json", '[' + inner + ']'),
                          ("formats/examples/valid/a.json", '{"wrap": ' + inner + '}')):
            with self.subTest(rel=rel):
                self.refused(rel, text)

    def test_a_run_document_under_formats_examples_passes(self):
        result = self.run_on({"formats/examples/invalid/bad.json": '{"schema": "run/1", "runtime": null}',
                              "formats/examples/valid/ok.json": '{"schema": "run/1", ' + self.PLAIN + '}'})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sols_micro_round_cases_are_refused_without_a_traceback(self):
        """PR #151, Sol's micro-round R1-R3, nested and at a path no record may live."""
        cases = {
            "r1-null-runtime.json": '{"data": {"schema": "run/1", "runtime": null, "note": "wine"}}',
            "r1-null-platform.json": '{"data": {"schema": "run/1", "runtime": {"platform": null}, "note": "wine"}}',
            "r2-escaped-nul.json": '{"data": {"schema": "run/1", "runtime": ["wi\\u0000ne"]}}',
            "r3-surrogate.json": '{"data": {"schema": "run/1", "runtime": ["\\ud800wine"]}}',
            "docs/r3-top.json": '{"schema": "run/1", "runtime": {"platform": "\\ud800wine"}}',
        }
        for rel, text in cases.items():
            with self.subTest(rel=rel):
                self.refused(rel, text)

    def test_a_lone_surrogate_in_an_allowed_record_never_crashes_the_check(self):
        result = self.run_on({"runs/E002/E002-r0002.json":
                              '{"schema": "run/1", "runtime": {"platform": "linux-wsl2/\\ud800wine"}}'})
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


class RecordSizeLimitTest(unittest.TestCase):
    """#158 (the owner's decision, 2026-10-10): run records (runs/**/*.json) and evidence manifests
    (evidence/**/*.manifest.json) may be up to 8 MB; every other tracked file keeps the 1 MB limit.
    Pushed before dispatch (L64). A multi-game E020 sitting's record was 1.33 MB and its manifest
    1.47 MB (E020-r0009)."""

    MB = 1024 * 1024
    WINE_BODY = ('"runtime": {"platform": "linux-wsl2/wine-xvfb-xfwm4"}, '
                 '"artifact": {"set": "iwp-2.0-996e86c5", "variant": "unregistered"}, '
                 '"start_state": {"sha256": "' + "a" * 64 + '"}')

    def padded(self, size, head='{"schema": "run/1", "runtime": {"platform": "windows-native-bandicam"}, '):
        """A JSON object of exactly `size` bytes."""
        tail = '"pad": "'
        filler = size - len(head) - len(tail) - 2
        return head + tail + "x" * filler + '"}'

    def run_on(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            for rel, text in files.items():
                path = repo / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                subprocess.run(["git", "add", rel], cwd=repo, check=True)
            return run_tool(repo)

    def test_a_record_or_manifest_between_1_and_8_mb_passes(self):
        for rel, size in (("runs/E002/E002-r0002.json", 1 * self.MB + 1),
                          ("runs/E002/E002-r0003.json", 8 * self.MB),
                          ("evidence/E002/E002-r0002.manifest.json", 2 * self.MB)):
            with self.subTest(rel=rel, size=size):
                head = '{"schema": "evidence-manifest/1", ' if rel.startswith("evidence/") else None
                text = self.padded(size, head) if head else self.padded(size)
                self.assertEqual(len(text.encode()), size)
                result = self.run_on({rel: text})
                self.assertEqual(result.returncode, 0, result.stdout[-600:] + result.stderr[-600:])

    def test_a_record_or_manifest_over_8_mb_is_refused(self):
        for rel in ("runs/E002/E002-r0002.json", "evidence/E002/E002-r0002.manifest.json"):
            with self.subTest(rel=rel):
                head = '{"schema": "evidence-manifest/1", ' if rel.startswith("evidence/") else None
                text = self.padded(8 * self.MB + 1, head) if head else self.padded(8 * self.MB + 1)
                result = self.run_on({rel: text})
                self.assertEqual(result.returncode, 1, result.stdout[-600:])
                self.assertIn(rel, result.stdout)

    def test_every_other_path_keeps_the_1_mb_limit(self):
        for rel in ("docs/big.json", "runs/E002/E002-r0002.txt", "runs/E002/E002-r0002.JSON",
                    "evidence/E002/E002-r0002.json", "evidence/E002/E002-r0002.manifest.json.bak",
                    "runsx/E002/a.json", "evidence-x/E002/a.manifest.json", "findings/big.md"):
            with self.subTest(rel=rel):
                result = self.run_on({rel: '{"pad": "' + "x" * (1 * self.MB) + '"}'})
                self.assertEqual(result.returncode, 1, result.stdout[-600:])
                self.assertIn(rel, result.stdout)

    def test_a_large_manifest_cannot_hide_a_wine_record(self):
        """Over 1 MB the gate skipped scanning anything outside runs/*.json, trusting the size check to
        refuse it. A manifest of 1-8 MB now passes the size check, so it must still be scanned."""
        inner = '{"schema": "run/1", ' + self.WINE_BODY + '}'
        text = '{"schema": "evidence-manifest/1", "hidden": ' + inner + ', "pad": "' + "x" * (2 * self.MB) + '"}'
        result = self.run_on({"evidence/E002/E002-r0002.manifest.json": text})
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 1, result.stdout[-600:])
        self.assertIn("evidence/E002/E002-r0002.manifest.json", result.stdout)

    def test_a_large_record_is_still_gated(self):
        text = '{"schema": "run/1", ' + self.WINE_BODY + ', "pad": "' + "x" * (2 * self.MB) + '"}'
        result = self.run_on({"runs/E002/E002-r0002.json": text})
        self.assertEqual(result.returncode, 1, result.stdout[-600:])
        self.assertIn("runs/E002/E002-r0002.json", result.stdout)


class RecordSizePathExactnessTest(unittest.TestCase):
    """#158 (the owner's decision, 2026-10-10): exactly `runs/**/*.json` and
    `evidence/**/*.manifest.json` reach 8 MB; every looser spelling keeps 1 MB; and a file that
    passes the size check is still scanned by the wine gate. Added on top of the main session's
    `RecordSizeLimitTest` (L64), which this class never edits."""

    MB = 1024 * 1024

    def padded(self, size, head='{"schema": "run/1", "runtime": {"platform": "windows-native-bandicam"}, '):
        """A JSON object of exactly `size` bytes."""
        tail = '"pad": "'
        filler = size - len(head) - len(tail) - 2
        return head + tail + "x" * filler + '"}'

    def run_on(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write_f019(repo)
            list_records(repo)
            for rel, text in files.items():
                path = repo / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                subprocess.run(["git", "add", rel], cwd=repo, check=True)
            return run_tool(repo)

    def test_docs_runs_keeps_the_1_mb_limit(self):
        """`docs/runs/` is not `runs/` as the first path component, so the refusal names 1 MB."""
        result = self.run_on({"docs/runs/a.json": self.padded(self.MB + 1)})
        self.assertEqual(result.returncode, 1, result.stdout[-600:])
        self.assertIn(f"over {1 * self.MB}", result.stdout)

    def test_a_manifest_at_the_evidence_root_may_be_8_mb(self):
        """`evidence/a.manifest.json` is a manifest however shallow it sits."""
        text = self.padded(8 * self.MB, '{"schema": "evidence-manifest/1", ')
        self.assertEqual(len(text.encode()), 8 * self.MB)
        result = self.run_on({"evidence/a.manifest.json": text})
        self.assertEqual(result.returncode, 0, result.stdout[-600:] + result.stderr[-600:])

    def test_an_oversize_record_names_the_record_limit(self):
        """A tracked record past 8 MB is refused, and the message names 8 MB, not 1 MB."""
        result = self.run_on({"runs/E002/E002-r0002.json": self.padded(8 * self.MB + 1)})
        self.assertEqual(result.returncode, 1, result.stdout[-600:])
        self.assertIn(f"over {8 * self.MB}", result.stdout)

    def test_a_large_manifest_hiding_a_nested_wine_record_is_refused_by_the_gate(self):
        """The size check passes this 2 MB manifest, so only a scan of it can refuse it: the
        refusal must carry the wine gate's code, not a size line."""
        inner = ('{"schema": "run/1", '
                 '"runtime": {"platform": "linux-wsl2/wine-xvfb-xfwm4"}, '
                 '"artifact": {"set": "iwp-2.0-996e86c5", "variant": "unregistered"}, '
                 '"start_state": {"sha256": "' + "a" * 64 + '"}}')
        text = ('{"schema": "evidence-manifest/1", "hidden": ' + inner +
                ', "pad": "' + "x" * (2 * self.MB) + '"}')
        result = self.run_on({"evidence/E002/E002-r0002.manifest.json": text})
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertEqual(result.returncode, 1, result.stdout[-600:])
        self.assertIn("[E036]", result.stdout)
        self.assertIn("evidence/E002/E002-r0002.manifest.json", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
