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
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


class ReexecTest(unittest.TestCase):
    """The recorder re-execs itself through the driver's inner wrapper when IWP_CYCLE_INNER is
    unset, and runs directly when it is set (T28 R3, defect 2).

    unshare and git are stubs on the PATH, the way tools/tests' profile tests stub the
    helper commands: the stub unshare logs its argv and the two environment pins, then
    exits 7, so the test sees exactly what the recorder would have run. Rule 9: the
    first test fails when the IWP_CYCLE_INNER check in main() is removed (the stub is
    then not called); the second fails when inner() is reached through unshare anyway
    (an empty PATH with no unshare at all, and the session patched out).
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="e018-reexec-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.bin = self.tmp / "stubs"
        self.bin.mkdir()
        self.log = self.tmp / "unshare.log"
        self.stub_unshare()
        self.stub(self.bin / "git", "printf 0123456789ab")

    @staticmethod
    def stub(path, body):
        path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
        path.chmod(0o755)

    def stub_unshare(self, status=7):
        self.stub(self.bin / "unshare",
                  "printf '%s\\n' \"$@\" >> " + str(self.log) + "\n"
                  "printf 'flag=%s\\n' \"$IWP_CYCLE_INNER\" >> " + str(self.log) + "\n"
                  "printf 'commit=%s\\n' \"$IWP_CYCLE_COMMIT\" >> " + str(self.log) + "\n"
                  "exit " + str(status))

    def log_lines(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_without_the_inner_flag_it_reexecs_through_the_wrapper(self):
        env = {"PATH": str(self.bin), "IWP_CYCLE_DISPLAY": ":77"}
        base = {k: v for k, v in os.environ.items() if k != record_f011.INNER_FLAG}
        with mock.patch.dict(os.environ, {**base, **env}, clear=True):
            code = record_f011.main(["Q-SET-04"])
        self.assertEqual(code, 7)                       # the stub's exit, propagated
        lines = self.log_lines()
        self.assertEqual(lines[0:8], ["-r", "-m", "-p", "-f", "--kill-child", "--mount-proc",
                                      sys.executable,
                                      str(ROOT / "experiments" / "E018-pro-corroboration" / "record_f011.py")])
        self.assertEqual(lines[8], "Q-SET-04")
        self.assertIn("flag=1", lines)
        self.assertIn("commit=0123456789ab", lines)

    def test_with_the_inner_flag_it_runs_directly(self):
        empty = self.tmp / "empty-bin"                  # no unshare anywhere: nothing may exec it
        empty.mkdir()
        ran = []
        locs = {"IWP_PREFIX": str(self.tmp / "prefix"), "E018_BUNDLES": str(self.tmp / "bundles"),
                "IWP_DIR": str(self.tmp / "install")}
        env = {"PATH": str(empty), record_f011.INNER_FLAG: "1", "IWP_CYCLE_COMMIT": "0123456789ab",
               "IWP_CYCLE_DISPLAY": ":77", "IWP_MACHINE": "local"}
        base = dict(os.environ)
        with mock.patch.dict(os.environ, {**base, **env}, clear=True), \
                mock.patch.object(record_f011, "mount_private_tmpfs",
                                  lambda: ran.append("mounted")), \
                mock.patch.object(record_f011, "confined", lambda *a, **k: locs), \
                mock.patch.object(record_f011.driver_session, "bind_install_readonly",
                                  lambda install: ran.append("bound")), \
                mock.patch.object(record_f011.driver_runner.spike, "versions", lambda: {}), \
                mock.patch.object(record_f011.driver_runner, "binary_sha256",
                                  lambda install: F019_BINARY_SHA), \
                mock.patch.object(record_f011.F011Recorder, "run",
                                  lambda self: ran.append("run")), \
                mock.patch.object(record_f011.F011Recorder, "write_record",
                                  lambda self, ctx=None: ran.append("write")):
            code = record_f011.main(["Q-SET-04"])
        self.assertEqual(code, 0)
        self.assertEqual(ran, ["mounted", "bound", "run", "write"])
        self.assertFalse(self.log.exists(), "unshare must not run when the flag is set")


class DryRunPlanTest(unittest.TestCase):
    """--dry-run for Q-SET-04 prints a plan whose every step exists in the E002 step language
    (T28 R3, defect 3: r0013 aborted on 'unknown step open_options'). Rule 9: adding a
    made-up step name to the plan fails this test.
    """

    def plan_of(self, question_id):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(record_f011.main([question_id, "--dry-run"]), 0)
        lines = [line.strip() for line in out.getvalue().splitlines()]
        start = lines.index("plan (E002 steps):")
        steps = lines[start + 1:]
        self.assertTrue(steps, "the plan printed no steps")
        return steps

    def test_every_q_set_04_plan_step_resolves_in_the_step_language(self):
        sys.path.insert(0, str(ROOT / "runtime" / "iwp" / "spike"))
        import steps as stepslib
        for text in self.plan_of("Q-SET-04"):
            with self.subTest(step=text):
                try:
                    step = stepslib.parse_line(text)
                except stepslib.StepError as exc:
                    self.fail(f"{text!r} is not a step the E002 language knows: {exc}")
                self.assertIsNotNone(step, f"{text!r} is not a step")
                self.assertEqual(step.op, text.split()[0])

    def test_the_plan_opens_the_options_screen_the_way_e004_does(self):
        steps = self.plan_of("Q-SET-04")
        self.assertIn("click! 320 585", steps)      # spike.OPTIONS_CLICK, runner.py's OPTIONS_STEP
        self.assertTrue(any(s.startswith("shot ") for s in steps), "no screenshot step")


class EntryPointTest(ReexecTest):
    """The executable entry point calls main() with no argument (Sol's R1, T28 R4).

    main() must normalize argv from sys.argv when it is omitted: with the local argv left
    None, the documented command crashed at list(argv) in the outer re-exec, and the inner
    process silently recorded [] as the record's actions.args — losing the command that
    actually ran. These tests call main() exactly as __main__ does; rule 9: removing the
    normalization line in main() fails both.
    """

    CLI = ["record_f011.py", "Q-SET-04", "--count-target", "7"]

    def test_entry_point_forwards_the_command_line_to_the_wrapper(self):
        env = {"PATH": str(self.bin), "IWP_CYCLE_DISPLAY": ":77"}
        base = {k: v for k, v in os.environ.items() if k != record_f011.INNER_FLAG}
        with mock.patch.dict(os.environ, {**base, **env}, clear=True), \
                mock.patch.object(sys, "argv", self.CLI):
            code = record_f011.main()
        self.assertEqual(code, 7)
        lines = self.log_lines()
        script = str(ROOT / "experiments" / "E018-pro-corroboration" / "record_f011.py")
        self.assertEqual(lines[lines.index(script) + 1:], ["Q-SET-04", "--count-target", "7",
                                                           "flag=1", "commit=0123456789ab"])

    def test_entry_point_records_the_command_line_it_ran_with(self):
        empty = self.tmp / "empty-bin"
        empty.mkdir()
        wrote = []
        locs = {"IWP_PREFIX": str(self.tmp / "prefix"), "E018_BUNDLES": str(self.tmp / "bundles"),
                "IWP_DIR": str(self.tmp / "install")}
        env = {"PATH": str(empty), record_f011.INNER_FLAG: "1", "IWP_CYCLE_COMMIT": "0123456789ab",
               "IWP_CYCLE_DISPLAY": ":77", "IWP_MACHINE": "local"}
        base = dict(os.environ)
        with mock.patch.dict(os.environ, {**base, **env}, clear=True), \
                mock.patch.object(sys, "argv", self.CLI), \
                mock.patch.object(record_f011, "mount_private_tmpfs", lambda: None), \
                mock.patch.object(record_f011, "confined", lambda *a, **k: locs), \
                mock.patch.object(record_f011.driver_session, "bind_install_readonly",
                                  lambda install: None), \
                mock.patch.object(record_f011.driver_runner.spike, "versions", lambda: {}), \
                mock.patch.object(record_f011.driver_runner, "binary_sha256",
                                  lambda install: F019_BINARY_SHA), \
                mock.patch.object(record_f011.F011Recorder, "run", lambda self: None), \
                mock.patch.object(record_f011.F011Recorder, "write_record",
                                  lambda self, ctx=None: wrote.append(ctx)):
            code = record_f011.main()
        self.assertEqual(code, 0)
        self.assertEqual([ctx["argv"] for ctx in wrote], [["Q-SET-04", "--count-target", "7"]])


if __name__ == "__main__":
    unittest.main()
