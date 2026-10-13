"""E018's records are run/1 documents (T28 round 3, defect 1).

The recorder (experiments/E018-pro-corroboration/record_f011.py) writes run/1
records like every other experiment under runs/ (tests/test_runs.py refuses
anything else), and the thirteen records the earlier rounds wrote as
`e018-record/1` were migrated value-preserving (runs/E018/CORRECTIONS.md names
the commits that hold the original bytes). These tests pin both: what the
recorder builds validates against the schema, and what is committed carries the
measured values the migration promised to keep.

Rule 9: each test here fails against the defect it guards — the build test fails
when build_record writes any other schema (checked with a saved-copy mutation
of the "schema" line), and the committed-records tests fail when a combat record
is not a run/1 document or no longer carries a field's original value.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import test_runs  # noqa: E402  (the suite's own record checker, reused, not copied)

spec = importlib.util.spec_from_file_location(
    "record_f011", ROOT / "experiments" / "E018-pro-corroboration" / "record_f011.py")
record_f011 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(record_f011)

COMBAT = ROOT / "runs" / "E018" / "combat"   # the committed combat records (migration tests)
F019_BINARY_SHA = "c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e"  # iwp-2.0-996e86c5 / unregistered


def test_context(argv=("Q-SET-04",)):
    """A record_context()-shaped dict, without touching git, the install or the environment."""
    return {"commit": "0123456789ab", "machine": "local", "fingerprint": {},
            "binary_sha": F019_BINARY_SHA, "argv": list(argv),
            "restore": record_f011.RESTORE_TEXT}


class BuiltRecordTest(unittest.TestCase):
    """What the recorder builds is a run/1 document, whatever the session's outcome."""

    def make_record(self, status="aborted: launch: unit test", **fields):
        rec = record_f011.make_recorder("Q-SET-04")
        rec.run_id = "E018-r0099"          # never the next id of the committed records
        rec.status = status
        rec.elapsed = fields.pop("elapsed", 12.3)
        rec.seal_ok = fields.pop("seal_ok", True)
        rec.started = fields.pop("started", "2026-10-13T15:04:32+02:00")
        rec.ended = fields.pop("ended", "2026-10-13T15:04:45+02:00")
        rec.obs = fields.pop("obs", [{"step": 0, "source": "process", "field": "unit", "value": "1"}])
        for name, value in fields.items():
            setattr(rec, name, value)
        return rec.build_record(test_context())

    def place(self, doc, run_id="E018-r0099"):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "runs" / "E018" / "combat"
            folder.mkdir(parents=True)
            path = folder / f"{run_id}.json"
            path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
            yield path

    def test_the_built_record_is_a_valid_run_1(self):
        for status in ("aborted: launch: unit test", "completed"):
            with self.subTest(status=status):
                doc = self.make_record(status=status)
                for path in self.place(doc):
                    self.assertEqual(test_runs.run_record_errors(path, None), [])

    def test_the_built_record_carries_the_recorder_fields_verbatim(self):
        doc = self.make_record()
        seen = {o["field"]: o["value"] for o in doc["observations"]}
        self.assertEqual(seen["question_id"], "Q-SET-04")
        self.assertEqual(seen["claim_id"], "C-SET-04")
        self.assertEqual(seen["count_target"], "1")
        self.assertEqual(json.loads(seen["per_arm_counts"]), {"controls_listed": 0})
        self.assertEqual(seen["screenshot_path"], "null")
        self.assertEqual(seen["screenshot_sha256"], "null")
        self.assertEqual(seen["seal_ok"], "true")
        self.assertEqual(json.loads(seen["elapsed_seconds"]), 12.3)
        self.assertEqual(seen["outcome"], "null")
        self.assertEqual(json.loads(seen["extra"]), {})
        self.assertEqual(doc["status"], "aborted: launch: unit test")

    def test_the_built_record_names_the_artifact_and_platform_the_gate_reads(self):
        doc = self.make_record()
        self.assertEqual(doc["artifact"], {"set": "iwp-2.0-996e86c5", "variant": "unregistered"})
        self.assertEqual(doc["runtime"]["platform"], "wine-on-user-machine-iwp-2.0")
        self.assertEqual(doc["start_state"]["sha256"], F019_BINARY_SHA)


class CommittedRecordsTest(unittest.TestCase):
    """The migrated combat records: run/1, and still carrying every original field's value."""

    def test_every_combat_record_is_a_valid_run_1(self):
        for path in sorted(COMBAT.glob("E018-r*.json")):
            with self.subTest(path=path.name):
                self.assertEqual(test_runs.run_record_errors(path), [],
                                 f"{path.name} is not a valid run/1 record")

    def test_every_combat_record_carries_the_recorder_fields(self):
        for path in sorted(COMBAT.glob("E018-r*.json")):
            with self.subTest(path=path.name):
                doc = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(doc["schema"], "run/1")
                self.assertEqual(doc["arm"], "combat")
                self.assertEqual(doc["experiment"], "E018")
                seen = {o["field"]: o["value"] for o in doc["observations"]}
                for field in ("question_id", "claim_id", "count_target", "per_arm_counts",
                              "screenshot_path", "screenshot_sha256", "seal_ok",
                              "elapsed_seconds", "outcome", "extra"):
                    self.assertIn(field, seen, f"{path.name} lost the {field} observation")
                self.assertEqual(seen["question_id"], "Q-SET-04")
                self.assertEqual(seen["claim_id"], "C-SET-04")

    def test_r0013_keeps_its_measured_values(self):
        """Spot pins (rule 9): values the original e018-record/1 documents held, kept as text."""
        doc = json.loads((COMBAT / "E018-r0013.json").read_text(encoding="utf-8"))
        seen = {o["field"]: o["value"] for o in doc["observations"]}
        self.assertEqual(doc["status"],
                         "aborted: step-failed: the steps are not usable: line 1: unknown step "
                         "'open_options'")
        self.assertEqual(json.loads(seen["per_arm_counts"]), {"controls_listed": 0})
        self.assertEqual(json.loads(seen["elapsed_seconds"]), 10.19)
        self.assertEqual(seen["seal_ok"], "true")

    def test_r0004_keeps_its_measured_values(self):
        doc = json.loads((COMBAT / "E018-r0004.json").read_text(encoding="utf-8"))
        seen = {o["field"]: o["value"] for o in doc["observations"]}
        self.assertTrue(doc["status"].startswith("aborted: seal: the prefix is not safe to launch from"))
        self.assertEqual(seen["seal_ok"], "false")
        self.assertEqual(json.loads(seen["elapsed_seconds"]), 0.22)

    def test_the_start_state_hash_is_the_f019_pin_not_a_measured_value(self):
        """The wine gate matches start_state.sha256 against F019; the restore text must say the
        migration pinned it (these runs never hashed the binary), so a reader cannot mistake
        it for a measurement."""
        for path in sorted(COMBAT.glob("E018-r*.json")):
            with self.subTest(path=path.name):
                doc = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(doc["start_state"]["sha256"], F019_BINARY_SHA)
                self.assertIn("not a hash this run measured", doc["start_state"]["restore"])


if __name__ == "__main__":
    unittest.main()
