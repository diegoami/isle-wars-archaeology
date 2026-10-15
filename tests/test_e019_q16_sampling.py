"""Main-seeded integration checks for the owner's twenty-completed-run Q-UI-16 policy."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_e019_ui_catalogue import (
    drive_one, records_of, rewrite, write_f020, check_ui_catalogue, walks,
    QUESTIONS, INVENTORY,
)


class QUi16SamplingContractTest(unittest.TestCase):
    def make(self, root, count):
        for _ in range(count):
            status, recovered = drive_one(root, "Q-UI-16", None)
            self.assertEqual(status, "completed")
            self.assertTrue(recovered)

    def errors(self, root, f020=False):
        batches = dict(walks.BATCHES, play=["Q-UI-16"])
        with mock.patch.object(walks, "BATCHES", batches):
            return check_ui_catalogue.run_checks(
                Path(root), questions_path=QUESTIONS, inventory_path=INVENTORY,
                batch="play", f020=f020,
            )

    def test_one_high_count_run_does_not_replace_twenty_completed_runs(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 1)
            self.assertTrue(self.errors(root), "one run must not satisfy twenty completed runs")

    def test_nineteen_positive_completed_runs_are_not_twenty(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 19)
            self.assertTrue(self.errors(root), "nineteen runs must fail even with many attacks")

    def test_twenty_positive_completed_runs_pass(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 20)
            self.assertEqual(self.errors(root), [])

    def test_aborted_twentieth_run_cannot_help(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 20)
            path, _ = records_of(root, "Q-UI-16")[-1]
            rewrite(path, lambda r: r.update(status="aborted: step-failed: synthetic"))
            self.assertTrue(self.errors(root), "an aborted twentieth run cannot contribute")

    def test_zero_attack_twentieth_run_cannot_help(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 20)
            path, _ = records_of(root, "Q-UI-16")[-1]
            def zero(record):
                for obs in record["observations"]:
                    if obs["field"] == "count: attacks":
                        obs["value"] = "0"
            rewrite(path, zero)
            self.assertTrue(self.errors(root), "a zero-attack completed run cannot contribute")

    def test_unproved_timing_twentieth_run_cannot_help(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 20)
            path, _ = records_of(root, "Q-UI-16")[-1]
            def unproved(record):
                for obs in record["observations"]:
                    if obs["field"] == "timing: attack exchange":
                        timing = json.loads(obs["value"])
                        timing["input proved"] = False
                        obs["value"] = json.dumps(timing)
            rewrite(path, unproved)
            self.assertTrue(self.errors(root), "unproved inputs cannot make a qualifying run")

    def test_different_speed_twentieth_run_cannot_help(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 20)
            path, _ = records_of(root, "Q-UI-16")[-1]
            def speed(record):
                for obs in record["observations"]:
                    if obs["field"] == "speed setting":
                        obs["value"] = "fast (synthetic mismatched setting)"
            rewrite(path, speed)
            self.assertTrue(self.errors(root), "twentieth run at a different speed cannot contribute")

    def test_mismatched_binary_platform_or_artifact_cannot_help(self):
        for label, mutate in (
                ("binary", lambda r: r["start_state"].update(sha256="f" * 64)),
                ("platform", lambda r: r["runtime"].update(platform="other-platform")),
                ("artifact", lambda r: r["artifact"].update(set="other-artifact"))):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as root:
                self.make(root, 20)
                path, _ = records_of(root, "Q-UI-16")[-1]
                rewrite(path, mutate)
                self.assertTrue(self.errors(root), f"a mismatched {label} cannot contribute")

    def test_nonfinite_timing_cannot_help(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 20)
            path, _ = records_of(root, "Q-UI-16")[-1]

            def nonfinite(record):
                for obs in record["observations"]:
                    if obs["field"] == "timing: attack exchange":
                        timing = json.loads(obs["value"])
                        timing["at_s"] = float("nan")
                        obs["value"] = json.dumps(timing)
                        break

            rewrite(path, nonfinite)
            self.assertTrue(self.errors(root), "a non-finite timing cannot contribute")

    def test_twenty_runs_but_only_one_citation_cannot_pass_f020(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 20)
            write_f020(root, q16_all=False)
            self.assertTrue(self.errors(root, f020=True), "all twenty contributing runs need citations")

    def test_citation_needs_a_png_recording_class_for_each_run(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 20)
            write_f020(root)
            path, _ = records_of(root, "Q-UI-16")[-1]
            manifest = Path(root) / "evidence" / "E019" / "play" / f"{path.stem}.manifest.json"
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["files"][0]["class"] = "other"
            manifest.write_text(json.dumps(doc), encoding="utf-8")
            self.assertTrue(self.errors(root, f020=True), "a non-recording PNG cannot satisfy the citation gate")


if __name__ == "__main__":
    unittest.main()
