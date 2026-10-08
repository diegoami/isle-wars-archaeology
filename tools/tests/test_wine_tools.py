"""Tests for T38's wine tools: validate_wine_manifests, the E020 launcher and check_records.

They use synthetic documents only. They pin: constraint C (every manifest file is `recording`),
the dispatcher's `--batch NAME --help` contract (Done-when 2, never starts wine), the record and
manifest shape (Done-when 3/4/6), and the sitting-directory layout (constraint A).
"""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_no_originals  # noqa: E402
import validate_records  # noqa: E402
import validate_wine_manifests  # noqa: E402
import check_counts  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


launcher = load("t38_launcher", "experiments/E020-wine-first-run/launcher.py")
check_records = load("t38_check_records", "experiments/E020-wine-first-run/check_records.py")

STAMP = "2026-10-08T12:00:00Z"
HEX64 = "a" * 64


def sample_record(**overrides):
    record = launcher.build_record(
        "E020-r0001", "cmb-accumulation", "abcdef123456", "local",
        {"wine": "wine-9.0", "xvfb": "2:21.1", "xfwm4": "4.18"}, HEX64, STAMP, STAMP, "completed",
        [{"step": 0, "source": "screen", "field": "counter:attacker-before", "value": "3"}],
        ["--batch", "cmb-accumulation"])
    record.update(overrides)
    return record


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.frame = Path(self._tmp.name) / "3-1700.png"
        self.frame.write_bytes(b"synthetic frame")

    def test_a_built_manifest_is_valid_and_all_recording(self):
        manifest = launcher.build_manifest("E020-r0001", [self.frame])
        self.assertEqual(validate_records.validate_document(manifest), [])
        self.assertEqual(validate_wine_manifests.errors_for(manifest), [])
        self.assertEqual(manifest["files"][0]["class"], "recording")
        self.assertEqual(manifest["files"][0]["asset"][:16], manifest["files"][0]["sha256"][:16])

    def test_a_screenshot_class_is_refused(self):
        manifest = launcher.build_manifest("E020-r0001", [self.frame])
        manifest["files"][0]["class"] = "screenshot"
        errors = validate_wine_manifests.errors_for(manifest)
        self.assertTrue(any("screenshot" in e for e in errors), errors)

    def test_an_invalid_manifest_is_refused_by_the_schema(self):
        errors = validate_wine_manifests.errors_for({"schema": "evidence-manifest/1"})
        self.assertTrue(errors)


class LauncherTest(unittest.TestCase):
    def test_batch_help_prints_batch_1_targets(self):
        text = launcher.batch_help("cmb-accumulation", check_counts.load_batches(launcher.SCENARIOS)["cmb-accumulation"])
        for expected in ("Q-CMB-04", "Q-CMB-11", "100", "walkthroughs/f011-questions.md",
                         "Session B", "counter:attacker-before"):
            self.assertIn(expected, text)

    def test_batch_help_prints_batch_2_targets(self):
        text = launcher.batch_help("bomb-sampling", check_counts.load_batches(launcher.SCENARIOS)["bomb-sampling"])
        for expected in ("C-CRD-06", "Q-BON-08", "9", "3 games", "owner:victim"):
            self.assertIn(expected, text)

    def test_help_for_a_known_batch_exits_zero_without_wine(self):
        for name in ("cmb-accumulation", "bomb-sampling"):
            with self.subTest(batch=name):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(launcher.main(["--batch", name, "--help"]), 0)
                self.assertIn(name, out.getvalue())

    def test_help_for_an_unknown_batch_exits_non_zero_and_names_it(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertNotEqual(launcher.main(["--batch", "unknown-x", "--help"]), 0)
        self.assertIn("unknown-x", err.getvalue())

    def test_sitting_id_is_utc_compact(self):
        self.assertEqual(launcher.sitting_id(0), "19700101T000000Z")

    def test_sitting_paths_layout(self):
        paths = launcher.sitting_paths("/tmp/sittings", "20261008T120000Z")
        self.assertEqual(paths["root"].name, "20261008T120000Z")
        self.assertEqual(paths["frames"].name, "frames")
        self.assertEqual(paths["index"].name, "frames-index.jsonl")
        self.assertEqual(paths["actions"].name, "actions.jsonl")
        self.assertEqual(paths["log"].name, "watcher.log")

    def test_record_observations_refuses_a_field_outside_the_vocabulary(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = launcher.sitting_paths(tmp, "s")
            launcher.prepare_sitting(paths)
            paths["readings"].write_text(json.dumps(
                {"step": 1, "source": "screen", "field": "score:player", "value": "3"}) + "\n",
                encoding="utf-8")
            with self.assertRaises(SystemExit):
                launcher.record_observations(paths, "counter:attacker-before")

    def test_record_observations_keeps_frames_by_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = launcher.sitting_paths(tmp, "s")
            launcher.prepare_sitting(paths)
            paths["index"].write_text(json.dumps({"name": "0-1.png", "sha256": HEX64}) + "\n",
                                      encoding="utf-8")
            observations = launcher.record_observations(paths, "counter:attacker-before")
            self.assertEqual(observations, [{"step": 0, "source": "screen", "ref": f"sha256:{HEX64}"}])


class RecordShapeTest(unittest.TestCase):
    def test_a_built_record_is_a_valid_run_1_document(self):
        self.assertEqual(validate_records.validate_document(sample_record()), [])

    def test_a_built_record_passes_the_constraint_f_gate(self):
        table = check_no_originals.load_f019_table(ROOT)
        self.assertEqual(check_no_originals.check_wine_gate(sample_record(), table), ("", ""))

    def test_check_record_flags_a_wrong_platform(self):
        table = check_no_originals.load_f019_table(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "E020-r0001.json"
            bad = sample_record()
            bad["runtime"]["platform"] = "wine-on-user-machine-evil"
            path.write_text(json.dumps(bad), encoding="utf-8")
            problems = check_records.check_record(path, table)
            self.assertTrue(any("platform" in p for p in problems), problems)

    def test_check_record_flags_a_non_structural_field(self):
        table = check_no_originals.load_f019_table(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "E020-r0001.json"
            bad = sample_record()
            bad["observations"][0]["field"] = "counter attacker"
            path.write_text(json.dumps(bad), encoding="utf-8")
            problems = check_records.check_record(path, table)
            self.assertTrue(any("kind:role" in p for p in problems), problems)

    def test_check_record_passes_a_valid_record(self):
        table = check_no_originals.load_f019_table(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "E020-r0001.json"
            path.write_text(json.dumps(sample_record()), encoding="utf-8")
            self.assertEqual(check_records.check_record(path, table), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
