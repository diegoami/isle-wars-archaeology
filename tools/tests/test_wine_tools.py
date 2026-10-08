"""Tests for T38's wine tools (round 2): validate_wine_manifests, the E020 launcher, its sitting
root, its export, its loop and its block file, and check_records.

Synthetic documents and directories only; nothing here starts wine or a display. Each test names the
round-1 finding it pins (R3 to R7, R11, R13, R14) or the Done-when line (2, 3, 4, 6).
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e020_fixtures import BOMB, F019_SHA, ROOT, SID, TABLE, bomb_reading, exchange_reading, make_sitting  # noqa: E402

import check_counts  # noqa: E402
import check_no_originals  # noqa: E402
import validate_records  # noqa: E402
import validate_wine_manifests  # noqa: E402
import e020_export  # noqa: E402
import e020_loop  # noqa: E402
import e020_sitting  # noqa: E402
import locations  # noqa: E402
from driver.clicks import parse_blocks  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


launcher = load("t38_launcher", "experiments/E020-wine-first-run/launcher.py")
check_records = load("t38_check_records", "experiments/E020-wine-first-run/check_records.py")
BATCHES = check_counts.load_batches(ROOT / "experiments" / "E020-wine-first-run" / "scenarios.txt")


class TmpWorld(unittest.TestCase):
    """A temporary directory outside every checkout: a sitting root `wine/` and a repository `repo/`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(os.path.realpath(self._tmp.name))
        if locations.checkout_of(self.tmp) is not None:
            self.skipTest("the temporary directory is inside a checkout (TMPDIR?)")
        self.wine = self.tmp / "wine"
        self.wine.mkdir()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()

    def export(self, sitting, batch="cmb-accumulation"):
        return e020_export.export(sitting, batch, BATCHES[batch], root=self.repo, sitting_root=self.wine,
                                  prescribed=self.wine, table=TABLE)

    def record(self, batch, run_id):
        return json.loads((self.repo / "runs" / "E020" / batch / f"{run_id}.json").read_text())


# --- R5: the manifest guard --------------------------------------------------------------------

class ManifestTest(TmpWorld):
    def manifest(self):
        sitting, _ = make_sitting(self.wine)
        self.export(sitting)
        return json.loads((self.repo / "evidence" / "E020" / "E020-r0001.manifest.json").read_text())

    def test_an_exported_manifest_is_valid_and_all_recording(self):
        manifest = self.manifest()
        self.assertEqual(validate_wine_manifests.errors_for(manifest), [])
        self.assertEqual({f["class"] for f in manifest["files"]}, {"recording"})

    def test_a_screenshot_class_is_refused(self):
        manifest = self.manifest()
        manifest["files"][0]["class"] = "screenshot"
        self.assertTrue(any("screenshot" in e for e in validate_wine_manifests.errors_for(manifest)))

    def test_a_valid_document_of_another_schema_is_refused(self):
        """R5: a valid run/1 record under a manifest's name passed round 1's guard."""
        sitting, _ = make_sitting(self.wine)
        self.export(sitting)
        run = self.record("cmb-accumulation", "E020-r0001")
        self.assertEqual(validate_records.validate_document(run), [], "the sample is a valid run/1")
        errors = validate_wine_manifests.errors_for(run)
        self.assertTrue(errors and "evidence-manifest/1" in errors[0], errors)
        for other in ({"schema": "artifact-set/1"}, [], "text", {"files": []}):
            self.assertTrue(validate_wine_manifests.errors_for(other), other)

    def test_a_manifest_without_files_is_refused(self):
        manifest = self.manifest()
        del manifest["files"]
        self.assertTrue(validate_wine_manifests.errors_for(manifest))


# --- Done-when 2: the dispatcher's help, and R4's refused option ------------------------------

class LauncherTest(unittest.TestCase):
    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.object(launcher, "outer", side_effect=AssertionError("wine would start")), \
                mock.patch.object(launcher, "inner", side_effect=AssertionError("wine would start")):
            code = launcher.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_batch_help_prints_batch_1_targets(self):
        code, out, _ = self.run_main("--batch", "cmb-accumulation", "--help")
        self.assertEqual(code, 0)
        for text in ("Q-CMB-04", "Q-CMB-11", "Session B computer-vs-computer", "at least 100 exchanges",
                     "first sitting", "walkthroughs/f011-questions.md"):
            self.assertIn(text, out)

    def test_batch_help_prints_batch_2_targets(self):
        code, out, _ = self.run_main("--batch", "bomb-sampling", "--help")
        self.assertEqual(code, 0)
        self.assertIn("C-CRD-06", out)
        self.assertIn("at least 9 computer bomb plays across at least 3 games", out)

    def test_an_unknown_batch_is_refused_by_name_before_wine(self):
        for argv in (("--batch", "unknown-x", "--help"), ("--batch", "unknown-x")):
            code, _, err = self.run_main(*argv)
            self.assertNotEqual(code, 0)
            self.assertIn("unknown-x", err)

    def test_no_option_moves_the_sitting_root(self):
        """R4: round 1's --sitting-root put a sitting anywhere; there is no such option now."""
        for argv in (("--batch", "cmb-accumulation", "--sitting-root", "/tmp/x"),
                     ("--batch", "cmb-accumulation", "--sitting-r", "/tmp/x"),
                     ("--batch", "cmb-accumulation", "--sitting", "/tmp/x")):
            code, _, _ = self.run_main(*argv)
            self.assertEqual(code, 2, argv)


# --- R4: the confined sitting root -------------------------------------------------------------

class SittingRootTest(TmpWorld):
    def test_the_prescribed_root_is_accepted(self):
        self.assertEqual(e020_sitting.confine_root(self.wine, self.wine), self.wine)

    def test_another_path_is_refused(self):
        with self.assertRaises(e020_sitting.SittingRefused):
            e020_sitting.confine_root(self.tmp / "elsewhere", self.wine)

    def test_the_launcher_passes_no_root_but_the_task_files(self):
        self.assertEqual(e020_sitting.SITTING_ROOT, Path("/mnt/c/Temp/iwp-shots/wine"))
        with self.assertRaises(e020_sitting.SittingRefused):
            e020_sitting.confine_root(self.wine)          # the default prescribed root is the fixed one

    def test_a_root_with_a_link_on_its_path_is_refused(self):
        real = self.tmp / "real"
        real.mkdir()
        link = self.tmp / "link"
        link.symlink_to(real)
        with self.assertRaises(e020_sitting.SittingRefused):
            e020_sitting.confine_root(link / "wine", link / "wine")

    def test_a_root_inside_a_checkout_or_this_repository_is_refused(self):
        checkout = self.tmp / "checkout"
        (checkout / ".git").mkdir(parents=True)
        for root in (checkout / "wine", ROOT / "scratch-wine"):
            with self.subTest(root=root):
                with self.assertRaises(e020_sitting.SittingRefused):
                    e020_sitting.confine_root(root, root)

    def test_a_root_overlapping_the_install_or_the_prefix_is_refused(self):
        with self.assertRaises(e020_sitting.SittingRefused):
            e020_sitting.confine_root(self.wine, self.wine, others=[("IWP_PREFIX", self.tmp)])

    def test_a_sitting_directory_is_created_new_and_never_reused(self):
        paths = e020_sitting.create_sitting(self.wine, SID)
        self.assertTrue(paths["frames"].is_dir() and paths["dumps"].is_dir())
        with self.assertRaises(e020_sitting.SittingRefused):
            e020_sitting.create_sitting(self.wine, SID)
        with self.assertRaises(e020_sitting.SittingRefused):
            e020_sitting.create_sitting(self.wine, "../escape")


# --- R3: the binary identity is measured; the export keeps the sitting's own status and provenance

class BinaryIdentityTest(TmpWorld):
    def test_both_copies_must_be_the_f019_binary(self):
        install, prefix = self.tmp / "install", self.tmp / "prefix"
        (prefix / "drive_c" / "iwp").mkdir(parents=True)
        install.mkdir()
        data = b"synthetic binary bytes"
        row = dict(TABLE[0], sha256=__import__("hashlib").sha256(data).hexdigest())
        (install / "Islepro.exe").write_bytes(data)
        (prefix / "drive_c" / "iwp" / "Islepro.exe").write_bytes(data)
        self.assertEqual(e020_sitting.binary_identity(install, prefix, row)["sha256"], row["sha256"])
        (prefix / "drive_c" / "iwp" / "Islepro.exe").write_bytes(b"another binary")
        with self.assertRaises(e020_sitting.SittingRefused):
            e020_sitting.binary_identity(install, prefix, row)
        with self.assertRaises(e020_sitting.SittingRefused):
            e020_sitting.binary_identity(install, prefix, TABLE[0])


class ExportTest(TmpWorld):
    def test_an_aborted_sitting_is_exported_aborted_with_its_own_times_and_commit(self):
        """R3: round 1 wrote `completed` and export-time provenance for a sitting marked aborted."""
        sitting, _ = make_sitting(self.wine, status="aborted: seal: the prefix is not at its baseline",
                                  doc_changes={"driver_commit": "0123456789ab", "started": "2026-10-08T12:00:00Z",
                                               "ended": "2026-10-08T12:00:09Z"})
        self.export(sitting)
        record = self.record("cmb-accumulation", "E020-r0001")
        self.assertEqual(record["status"], "aborted: seal: the prefix is not at its baseline")
        self.assertEqual((record["started"], record["ended"]), ("2026-10-08T12:00:00Z", "2026-10-08T12:00:09Z"))
        self.assertEqual(record["code_commit"], "0123456789ab")
        self.assertEqual(record["start_state"]["sha256"], F019_SHA)
        self.assertEqual(validate_records.validate_document(record), [])
        self.assertEqual(check_no_originals.check_wine_gate(record, TABLE), ("", ""))

    def test_a_directory_without_proof_of_a_sitting_is_refused(self):
        bare = self.wine / "20261008T130000Z"
        (bare / "frames").mkdir(parents=True)
        with self.assertRaises(e020_export.ExportRefused):
            self.export(bare)
        self.assertFalse((self.repo / "runs").exists())

    def test_a_sitting_json_without_status_or_measured_binary_is_refused(self):
        for i, changes in enumerate(({"status": None}, {"status": "done"},
                                     {"binary": {"file": "Islepro.exe", "sha256": F019_SHA}},
                                     {"binary": None}, {"batch": "bomb-sampling"}, {"started": "yesterday"})):
            with self.subTest(changes=changes):
                sid = f"20261008T10{i:02d}00Z"
                sitting, _ = make_sitting(self.wine, sid=sid, doc_changes=changes)
                with self.assertRaises(e020_export.ExportRefused):
                    self.export(sitting)
        self.assertFalse((self.repo / "runs").exists())

    def test_a_measured_binary_that_is_not_the_f019_row_is_refused(self):
        sitting, _ = make_sitting(self.wine, doc_changes={"binary": {"file": "Islepro.exe", "sha256": "ab" + "0" * 62,
                                                                     "measured": ["install", "run copy"]}})
        with self.assertRaises(e020_export.ExportRefused):
            self.export(sitting)

    def test_a_sitting_outside_the_root_or_a_frame_that_changed_is_refused(self):
        other = self.tmp / "other"
        other.mkdir()
        sitting, _ = make_sitting(other)
        with self.assertRaises(e020_export.ExportRefused):
            self.export(sitting)
        sitting, _ = make_sitting(self.wine)
        next((sitting / "frames").iterdir()).write_bytes(b"changed after it was indexed")
        with self.assertRaises(e020_export.ExportRefused):
            self.export(sitting)

    def test_events_become_one_step_each_with_their_frames(self):
        sitting, digests = make_sitting(self.wine, readings=[exchange_reading(1, 1), exchange_reading(1, 2)])
        self.export(sitting)
        record = self.record("cmb-accumulation", "E020-r0001")
        steps = {o["step"] for o in record["observations"]}
        self.assertEqual(steps, {0, 1, 2})
        self.assertEqual(check_records.check_record(
            self.repo / "runs" / "E020" / "cmb-accumulation" / "E020-r0001.json", TABLE), [])
        events, problems = check_counts.events_of(record, "cmb-accumulation", BATCHES["cmb-accumulation"])
        self.assertEqual((len(events), problems), (2, []))

    def test_text_in_a_reading_is_refused_before_a_record_is_written(self):
        """R6: round 1 kept a counter value 'synthetic forbidden screen label' verbatim."""
        for i, values in enumerate(({"counter:attacker-before": "synthetic forbidden screen label"},
                                    {"owner:defender": "synthetic forbidden screen label"},
                                    {"country:defender": "99"})):
            with self.subTest(values=values):
                sid = f"20261008T14{i:02d}00Z"
                sitting, _ = make_sitting(self.wine, sid=sid, readings=[exchange_reading(1, 1, **values)])
                with self.assertRaises(e020_export.ExportRefused):
                    self.export(sitting)
        self.assertFalse((self.repo / "runs").exists())

    def test_an_event_that_is_not_a_complete_event_of_a_real_game_is_refused(self):
        bad = [exchange_reading(2, 1),                                     # game 2 never started
               {"game": 1, "seq": 1, "values": {"counter:attacker-before": "3"}},   # incomplete
               dict(exchange_reading(1, 1), frames=["c" * 64, "d" * 64])]  # frames not in the index
        for i, reading in enumerate(bad):
            with self.subTest(i=i):
                sitting, _ = make_sitting(self.wine, sid=f"20261008T15{i:02d}00Z", readings=[reading])
                with self.assertRaises(e020_export.ExportRefused):
                    self.export(sitting)
        sitting, _ = make_sitting(self.wine, sid="20261008T155900Z",
                                  readings=[exchange_reading(1, 1), exchange_reading(1, 1)])
        with self.assertRaises(e020_export.ExportRefused):
            self.export(sitting)

    def test_run_ids_are_experiment_wide(self):
        """R7: the first bomb export after a cmb export collided on E020-r0001 in round 1."""
        a, _ = make_sitting(self.wine, sid="20261008T120000Z")
        b, _ = make_sitting(self.wine, sid="20261008T130000Z", batch="bomb-sampling",
                            readings=[bomb_reading(1, 1)])
        self.assertEqual(self.export(a)[1], "runs/E020/cmb-accumulation/E020-r0001.json")
        self.assertEqual(self.export(b, "bomb-sampling")[1], "runs/E020/bomb-sampling/E020-r0002.json")
        self.assertEqual(self.export(a)[1], "runs/E020/cmb-accumulation/E020-r0003.json")   # a re-read: beside
        self.assertEqual(e020_export.next_run_id(self.repo), "E020-r0004")

    def test_a_record_is_never_written_over(self):
        sitting, _ = make_sitting(self.wine)
        with mock.patch.object(e020_export, "next_run_id", return_value="E020-r0001"):
            self.export(sitting)
            with self.assertRaises(e020_export.ExportRefused):
                self.export(sitting)


# --- R11, R13, R14: the blocks and the loop ----------------------------------------------------

class BlocksTest(unittest.TestCase):
    blocks = parse_blocks((ROOT / "experiments" / "E020-wine-first-run" / "play.steps").read_text())

    def ops(self, name):
        return [(s.op, s.args) for s in self.blocks[name]]

    def test_new_game_follows_the_recorded_loss_easy_order(self):
        """R13: New Game, EASY, Play Game, in E002 loss-easy.steps' order and points (E002-r0018: the
        mid-game New Game at EASY changed the screen with no notice). Round 1 clicked Play Game first."""
        steps = (ROOT / "experiments" / "E002-iwp-state-inventory" / "scripts" / "loss-easy.steps").read_text()
        recorded = [(s.op.rstrip("!"), s.args) for s in parse_blocks("# --- block a\n" + "\n".join(
            line for line in steps.splitlines() if line.split("#")[0].strip().split()[:1] in (["click"], ["click!"])))["a"]]
        self.assertEqual(recorded[:3], [("click", (100, 585)), ("click", (533, 311)), ("click", (565, 532))])
        mine = [(op.rstrip("!"), args) for op, args in self.ops("new-game") if op.startswith("click")]
        self.assertEqual(mine, recorded[:3])
        self.assertEqual(self.ops("new-game")[1], ("click!", (100, 585)))
        self.assertEqual(self.ops("new-game")[-1], ("click!", (565, 532)))

    def test_placement_reads_the_screen_over_every_proven_country_point(self):
        """R11: a country the human owns, by the placement row lighting, over every country point of
        the proven E002 set (walkthroughs/coordinates.md); round 1 clicked one fixed point."""
        coordinates = (ROOT / "walkthroughs" / "coordinates.md").read_text().split("```")[1].replace(",", " ").split()
        place = self.ops("place")
        self.assertEqual(place[0], ("watch", (265, 530, 270, 26)))
        op, args = place[1]
        self.assertEqual(op, "click-until?")
        self.assertEqual(args[:5], (168, 168, 168, 24, 1000))
        self.assertEqual([str(a) for a in args[5:]], coordinates)
        self.assertEqual(len(args[5:]), 88)        # 44 points: the list coordinates.md holds (it says 46)

    def test_no_block_attacks_and_every_wait_is_a_settle(self):
        for name, steps in self.blocks.items():
            for step in steps:
                self.assertNotEqual(step.op, "attack-picked")
        self.assertEqual(self.ops("quiet"), [("watch", (0, 0, 800, 495)), ("settle", (4,))])


class FakeDriver:
    """Plays a scripted game: `place_results` are the picked outcomes of successive `place` blocks;
    `quiet` is quiet after `noisy` attempts."""

    def __init__(self, place_results, noisy=0):
        self.place_results = list(place_results)
        self.noisy = noisy
        self.blocks, self.notes, self.context = [], [], {}

    def run_block(self, name):
        self.blocks.append((name, dict(self.context)))
        if name == "place":
            return {"picked": self.place_results.pop(0) if self.place_results else None}
        if name == "quiet":
            self.noisy -= 1
            return {"quiet": self.noisy < 0}
        return {}

    def note(self, **fields):
        self.notes.append(dict(self.context, **fields))


class LoopTest(unittest.TestCase):
    batch = {"games_max": "2", "turns_max": "3", "sitting_seconds": "1000"}

    def test_a_game_plays_turns_until_the_human_cannot_place(self):
        driver = FakeDriver([5, 9, None, None, 1, 1, 1])
        summary = e020_loop.BatchLoop(driver, self.batch, clock=lambda: 0).run()
        names = [n for n, _ in driver.blocks]
        self.assertEqual(names[:2], ["new-game", "quiet"])
        self.assertEqual(summary, {"games": 2, "turns": 5, "placements": 5, "ended": "games-max"})
        self.assertEqual([n["reason"] for n in driver.notes if n["event"] == "game-end"],
                         ["placement-refused", "turns-max"])
        self.assertIn("dismiss", names)

    def test_no_commit_without_a_placement(self):
        driver = FakeDriver([None, None])
        e020_loop.BatchLoop(driver, dict(self.batch, games_max="1"), clock=lambda: 0).run()
        self.assertNotIn("commit", [n for n, _ in driver.blocks])

    def test_waits_are_state_aware_and_bounded(self):
        driver = FakeDriver([None, None], noisy=2)
        e020_loop.BatchLoop(driver, dict(self.batch, games_max="1"), clock=lambda: 0).run()
        names = [n for n, _ in driver.blocks]
        self.assertEqual(names[1:4], ["quiet", "quiet", "quiet"])
        driver = FakeDriver([None, None], noisy=100)
        e020_loop.BatchLoop(driver, dict(self.batch, games_max="1"), clock=lambda: 0).run()
        self.assertEqual(sum(1 for n, _ in driver.blocks if n == "quiet"), 2 * e020_loop.QUIET_ATTEMPTS)

    def test_the_sitting_stops_at_its_seconds_and_says_so(self):
        times = iter([0, 0, 0, 2000, 2000, 2000, 2000])
        driver = FakeDriver([1, 1, 1])
        summary = e020_loop.BatchLoop(driver, self.batch, clock=lambda: next(times)).run()
        self.assertEqual(summary["ended"], "sitting-seconds")

    def test_every_game_start_names_its_ordinal(self):
        driver = FakeDriver([None, None, None, None])
        e020_loop.BatchLoop(driver, self.batch, clock=lambda: 0).run()
        self.assertEqual([n["game"] for n in driver.notes if n["event"] == "game-start"], [1, 2])


# --- Done-when 3/4/6 through check_records ------------------------------------------------------

class CheckRecordsTest(TmpWorld):
    def exported(self, **kw):
        sitting, _ = make_sitting(self.wine, readings=[exchange_reading(1, 1)], **kw)
        self.export(sitting)
        return self.repo / "runs" / "E020" / "cmb-accumulation" / "E020-r0001.json"

    def test_an_exported_record_passes(self):
        self.assertEqual(check_records.check_record(self.exported(), TABLE), [])

    def test_a_wrong_platform_or_a_text_value_is_flagged(self):
        path = self.exported()
        doc = json.loads(path.read_text())
        doc["runtime"]["platform"] = "wine-on-user-machine"
        path.write_text(json.dumps(doc))
        self.assertTrue(any("platform" in p for p in check_records.check_record(path, TABLE)))
        doc["runtime"]["platform"] = "wine-on-user-machine-iwp-2.0"
        for o in doc["observations"]:
            if o.get("field") == "owner:attacker":
                o["value"] = "synthetic forbidden screen label"
        path.write_text(json.dumps(doc))
        self.assertTrue(any("colour word" in p for p in check_records.check_record(path, TABLE)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
