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

    def test_a_sitting_without_readings_is_exported_raw_with_its_frames_and_no_events(self):
        """Round 4 (DW1, DW3): the first sitting has no readings.jsonl (T40 builds the reader) and
        aborted. Its record keeps the real status and provenance, every frame by hash, and no event."""
        frames = (b"frame one", b"frame two", b"frame one", b"frame three")    # a repeated frame, as on a quiet board
        sitting, digests = make_sitting(self.wine, status="aborted: step-failed: step on line 1: the screen did not change",
                                        games=(1, 2), frames=frames)
        self.assertFalse((sitting / "readings.jsonl").exists())
        written = self.export(sitting)
        self.assertEqual(written, ["evidence/E020/E020-r0001.manifest.json", "runs/E020/cmb-accumulation/E020-r0001.json"])
        record = self.record("cmb-accumulation", "E020-r0001")
        self.assertEqual(record["status"], "aborted: step-failed: step on line 1: the screen did not change")
        self.assertEqual(record["observations"], [{"step": 0, "source": "process", "field": "sitting:epoch",
                                                   "value": str(1791460800)}])
        outputs = {o["sha256"] for o in record["outputs"]}
        self.assertTrue(set(digests) <= outputs, "every indexed frame is in the record by hash")
        self.assertNotIn("readings.jsonl", [o["name"] for o in record["outputs"]])
        self.assertEqual(validate_records.validate_document(record), [])
        self.assertEqual(check_records.check_record(self.repo / written[1], TABLE), [])
        manifest = json.loads((self.repo / written[0]).read_text())
        self.assertEqual({f["sha256"] for f in manifest["files"]}, outputs)
        self.assertEqual({f["class"] for f in manifest["files"]}, {"recording"})

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

    def test_a_game_started_after_a_credited_loss_is_never_recorded_under_the_shipped_set(self):
        """T41: after `loss-credited` the game has written its scoreboard file, so a later game ran on the
        successor set, which F019 has no row for. Refused, nothing written; a credit that came last is not."""
        def with_lines(sitting, *lines):
            path = sitting / "actions.jsonl"
            path.write_text(path.read_text() + "".join(json.dumps(l) + "\n" for l in lines))
        refused, _ = make_sitting(self.wine, sid="20261008T120000Z")
        with_lines(refused, {"seq": 5, "game": 1, "turn": 3, "event": "loss-credited"},
                   {"seq": 6, "game": 2, "turn": 0, "event": "game-start"})
        with self.assertRaises(e020_export.ExportRefused) as caught:
            self.export(refused)
        self.assertIn("never the shipped set", str(caught.exception))
        self.assertIn("iwp-2.0-de5a82a2", str(caught.exception))
        self.assertFalse((self.repo / "runs").exists() and any((self.repo / "runs").rglob("*.json")))
        self.assertFalse((self.repo / "evidence").exists() and any((self.repo / "evidence").rglob("*.json")))
        last, _ = make_sitting(self.wine, sid="20261008T130000Z")
        with_lines(last, {"seq": 5, "game": 1, "turn": 3, "event": "loss-credited"})
        record = self.record("cmb-accumulation", self.export(last)[1].split("/")[-1][:-5])
        self.assertEqual(record["artifact"], {"set": "iwp-2.0-996e86c5", "variant": "unregistered"})

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

    def test_the_scoreboards_continue_is_one_click_inside_its_button(self):
        """T41: the button's centre (401,526), E002's "Continue (after loss)" is 400,526; one click, which
        must change the screen."""
        from driver import screens
        self.assertEqual(self.ops("scoreboard-continue"), [("watch", ()), ("click!", screens.SCOREBOARD_CONTINUE_CLICK)])
        x, y, w, h = 327, 514, 148, 25          # the button as measured (walkthroughs/coordinates.md)
        cx, cy = screens.SCOREBOARD_CONTINUE_CLICK
        self.assertTrue(x <= cx < x + w and y <= cy < y + h)
        self.assertNotEqual(screens.SCOREBOARD_CONTINUE_CLICK, screens.CONTINUE_CLICK)   # not the winner notice's

    def test_no_block_attacks_and_every_wait_is_a_settle(self):
        for name, steps in self.blocks.items():
            for step in steps:
                self.assertNotEqual(step.op, "attack-picked")
        self.assertEqual(self.ops("quiet"), [("watch", (0, 0, 800, 495)), ("settle", (4,))])


class FakeDriver:
    """Plays a scripted game: `place_results` are the picked outcomes of successive `place` blocks;
    `quiet` is quiet after `noisy` attempts."""

    def __init__(self, place_results, noisy=0, raises=False, quiet_script=None, screens=None):
        self.place_results = list(place_results)
        self.screens = ["title"] if screens is None else list(screens)   # successive readings; `board-menu` once spent
        self.readings, self.frames, self.trail, self.sleeps = [], [], [], []   # trail: blocks and readings, in order
        self.noisy = noisy
        self.raises = raises                 # a noisy board raises NotReady, as the click-driver's settle does
        self.quiet_script = quiet_script     # successive quiet results; noisy once it is spent
        self.blocks, self.notes, self.context = [], [], {}
        self.after = {}                      # trail item -> callable run right after it (time passing in a wait)

    def run_block(self, name):
        self.blocks.append((name, dict(self.context)))
        self.trail.append(name)
        if name in self.after:
            self.after[name](self)
        if name == "place":
            return {"picked": self.place_results.pop(0) if self.place_results else None}
        if name == "quiet":
            if self.quiet_script is not None:
                quiet = self.quiet_script.pop(0) if self.quiet_script else False
            else:
                self.noisy -= 1
                quiet = self.noisy < 0
            if not quiet and self.raises:
                raise e020_loop.NotReady("the watched area did not settle within its time")
            return {"quiet": quiet}
        return {}

    def note(self, **fields):
        self.notes.append(dict(self.context, **fields))
        if fields.get("event") == "loss-credited":
            self.trail.append("note:loss-credited")

    def read_screen(self):
        screen = self.screens.pop(0) if self.screens else "board-menu"
        self.readings.append(screen)
        self.trail.append("read:" + screen)
        if "read:" + screen in self.after:
            self.after["read:" + screen](self)
        return screen

    def final_frame(self, name):
        self.frames.append(name)
        return "f" * 64

    def read_winner(self):
        self.trail.append("winner")
        return self.winner

    winner = "red"


class LoopTest(unittest.TestCase):
    batch = {"games_max": "2", "sitting_seconds": "1000"}

    def test_a_game_has_no_turn_limit(self):
        """T41: `turns_max` (a batch of the earlier design may still carry it) no longer ends a game. Sitting
        20261008T204817Z stopped game 1 at turn 30 and sent New Game from the board, which credited a loss;
        now the game is played past it, to its end (here the winner notice, at the 8th turn)."""
        driver = FakeDriver([1] * 7, screens=["title"] + ["board-menu"] * 7 + ["game-over", "title"])
        loop = e020_loop.BatchLoop(driver, dict(self.batch, games_max="1", turns_max="3"), clock=lambda: 0)
        summary = loop.run()
        names = [n for n, _ in driver.blocks]
        self.assertEqual(names.count("place"), 7)
        self.assertEqual(summary, {"games": 1, "turns": 7, "placements": 7, "ended": "games-max"})
        self.assertEqual([n["reason"] for n in driver.notes if n["event"] == "game-end"], ["game-over"])
        self.assertEqual(names.count("new-game"), 1)

    def test_a_refused_placement_stops_the_sitting_and_never_sends_new_game(self):
        """T41: the human cannot place on the board with its menu row lit, so the game is live: a last
        frame, no click, and no next game (New Game from that board is what credited the loss)."""
        driver = FakeDriver([1, None, None], screens=["title", "board-menu", "board-menu", "board-menu", "board-menu"])
        summary = e020_loop.BatchLoop(driver, self.batch, clock=lambda: 0).run()
        names = [n for n, _ in driver.blocks]
        self.assertEqual(names.count("new-game"), 1)
        self.assertEqual(names[-3:], ["dismiss", "quiet", "place"])  # the last placement try; nothing after it
        self.assertEqual((summary["ended"], summary["screen"], summary["games"]), ("placement-refused", "board-menu", 1))
        self.assertEqual(driver.frames, [e020_loop.FINAL_FRAME])
        self.assertEqual([n["reason"] for n in driver.notes if n["event"] == "game-end"], ["placement-refused"])

    def test_no_commit_without_a_placement(self):
        driver = FakeDriver([None, None])
        e020_loop.BatchLoop(driver, dict(self.batch, games_max="1"), clock=lambda: 0).run()
        self.assertNotIn("commit", [n for n, _ in driver.blocks])

    def test_waits_are_state_aware_and_bounded(self):
        driver = FakeDriver([None, None], noisy=2)
        e020_loop.BatchLoop(driver, dict(self.batch, games_max="1"), clock=lambda: 0).run()
        names = [n for n, _ in driver.blocks]
        self.assertEqual(names[1:4], ["quiet", "quiet", "quiet"])

    def test_an_exhausted_wait_sends_no_placement_or_commit(self):
        """Round 3, R1: when the board never goes quiet, the loop sends nothing more (no place, no
        commit), raises NotReady, and its summary is not a normal one; whether the driver answers a
        noisy board with `quiet: False` or with the click-driver's NotReady."""
        for raises in (False, True):
            with self.subTest(raises=raises):
                driver = FakeDriver([1, 1, 1], noisy=100, raises=raises)
                loop = e020_loop.BatchLoop(driver, dict(self.batch, games_max="1"), clock=lambda: 0)
                with self.assertRaises(e020_loop.NotReady):
                    loop.run()
                self.assertEqual([n for n, _ in driver.blocks], ["new-game"] + ["quiet"] * e020_loop.QUIET_ATTEMPTS)
                self.assertTrue(loop.summary["ended"].startswith("aborted: not-ready: the board was not quiet"),
                                loop.summary)
                self.assertNotIn("game-end", [n.get("event") for n in driver.notes])

    def test_an_exhausted_wait_after_a_turn_stops_the_game_too(self):
        """Round 3, R1: the wait after a commit, and the one after a dismiss, are not ignored either."""
        for places, stop_after in (([1, 1, 1], ["new-game", "quiet", "place", "commit"]),
                                   ([None, 1, 1], ["new-game", "quiet", "place", "dismiss"])):
            with self.subTest(places=places):
                driver = FakeDriver(places, quiet_script=[True])
                with self.assertRaises(e020_loop.NotReady):
                    e020_loop.BatchLoop(driver, dict(self.batch, games_max="1"), clock=lambda: 0).run()
                names = [n for n, _ in driver.blocks]
                self.assertEqual(names, stop_after + ["quiet"] * e020_loop.QUIET_ATTEMPTS)

    def test_the_sitting_stops_at_its_seconds_and_says_so(self):
        times = iter([0, 0, 0, 2000, 2000, 2000, 2000])
        driver = FakeDriver([1, 1, 1])
        summary = e020_loop.BatchLoop(driver, self.batch, clock=lambda: next(times)).run()
        self.assertEqual(summary["ended"], "sitting-seconds")

    def test_time_running_out_in_a_live_game_ends_the_sitting_with_no_click(self):
        """T41: the clock passes `sitting_seconds` after the second turn, in the middle of game 1. The
        loop sends nothing more: no placement, no New Game, and no next game (games_max is 4)."""
        driver = FakeDriver([1] * 9)
        clock = lambda: 2000 if [n for n, _ in driver.blocks].count("commit") >= 2 else 0
        summary = e020_loop.BatchLoop(driver, self.batch, clock=clock).run()
        names = [n for n, _ in driver.blocks]
        self.assertEqual(names, ["new-game", "quiet", "place", "commit", "quiet", "place", "commit", "quiet"])
        self.assertEqual((summary["ended"], summary["games"], summary["turns"]), ("sitting-seconds", 1, 2))
        self.assertEqual([n["reason"] for n in driver.notes if n["event"] == "game-end"], ["sitting-seconds"])
        self.assertEqual(driver.frames, [])

    def test_every_game_start_names_its_ordinal(self):
        driver = FakeDriver([1, 1], screens=["title", "game-over", "title", "game-over", "title"])
        e020_loop.BatchLoop(driver, dict(self.batch, games_max="2"), clock=lambda: 0).run()
        self.assertEqual([n["game"] for n in driver.notes if n["event"] == "game-start"], [1, 2])


class ScreenLoopTest(unittest.TestCase):
    """T38 round 4: the elimination notice (keep playing), clean stops on unknown screens, and New
    Game only on a screen proven to be the title or the board with its menu row."""
    batch = {"games_max": "4", "sitting_seconds": "1000"}

    def loop(self, driver, clock=lambda: 0, **batch):
        made = e020_loop.BatchLoop(driver, dict(self.batch, **batch), clock=clock,
                                   sleep=lambda s: driver.sleeps.append(s))
        return made, made.run()

    def test_the_first_sittings_turn_16_is_answered_with_keep_playing(self):
        """Sitting 20261008T184505Z: the notice was up at turn 16's start; the loop tried 44 placement
        points and then clicked New Game where it is not. Now: KEEP PLAYING once, then only readings."""
        screens = ["title"] + ["board-menu"] * 15 + ["eliminated", "board", "board", "unknown"]
        driver = FakeDriver([1] * 15, screens=screens)
        _, summary = self.loop(driver)
        after = driver.trail[driver.trail.index("read:eliminated") + 1:]
        self.assertEqual(after, ["eliminated-keep-playing", "read:board", "read:board", "read:unknown"])
        self.assertEqual([n for n, _ in driver.blocks].count("new-game"), 1)
        self.assertEqual(driver.sleeps, [e020_loop.PLAYOUT_POLL] * 3)
        self.assertEqual(summary, {"games": 1, "turns": 15, "placements": 15, "ended": "unknown-screen",
                                   "eliminated": True, "screen": "unknown", "final_frame": "f" * 64})
        self.assertEqual(driver.frames, [e020_loop.FINAL_FRAME])
        ended = [n for n in driver.notes if n.get("event") == "ended"]
        self.assertEqual([(n["ended"], n["sha256"], n["turn"]) for n in ended], [("unknown-screen", "f" * 64, 16)])
        self.assertEqual([n["reason"] for n in driver.notes if n.get("event") == "game-end"],
                         ["played-out: unknown-screen"])

    def test_the_notice_after_a_dismiss_is_answered_before_a_second_placement(self):
        driver = FakeDriver([None], screens=["title", "board-menu", "eliminated", "unknown"])
        _, summary = self.loop(driver)
        self.assertEqual(driver.trail, ["read:title", "new-game", "quiet", "read:board-menu", "place", "dismiss",
                                        "quiet", "read:eliminated", "eliminated-keep-playing", "read:unknown"])
        self.assertEqual(summary["ended"], "unknown-screen")

    def test_the_play_out_sends_nothing_and_ends_at_the_sitting_seconds(self):
        times = iter([0] + [0] * 6 + list(range(1, 10000)))
        driver = FakeDriver([1], screens=["title", "board-menu", "eliminated"] + ["board"] * 10000)
        _, summary = self.loop(driver, clock=lambda: next(times), sitting_seconds="50")
        after = driver.trail[driver.trail.index("eliminated-keep-playing") + 1:]
        self.assertTrue(after and set(after) == {"read:board"}, after)
        self.assertEqual(summary["ended"], "sitting-seconds")
        self.assertEqual(driver.frames, [])
        self.assertEqual([n["reason"] for n in driver.notes if n.get("event") == "game-end"],
                         ["played-out: sitting-seconds"])

    def test_an_unknown_screen_at_a_turns_start_ends_the_sitting_unclicked(self):
        for screen in ("unknown", "title"):
            with self.subTest(screen=screen):
                driver = FakeDriver([1, 1], screens=["title", screen])
                _, summary = self.loop(driver)
                self.assertEqual(driver.trail, ["read:title", "new-game", "quiet", "read:" + screen])
                self.assertEqual((summary["ended"], summary["screen"], summary["final_frame"]),
                                 ("unknown-screen", screen, "f" * 64))
                self.assertEqual([n["reason"] for n in driver.notes if n.get("event") == "game-end"],
                                 ["unknown-screen"])

    def test_an_unknown_screen_that_never_settles_ends_the_sitting_unclicked(self):
        """Round 4 review, R1: the screen is read between quiet blocks that were not quiet, so an
        unknown screen that never settles ends as `unknown-screen` (its final frame, no click), not as
        `not-ready`; whether the driver answers it with `quiet: False` or with NotReady."""
        for raises in (False, True):
            with self.subTest(raises=raises):
                driver = FakeDriver([1, 1], noisy=99, raises=raises, screens=["title", "unknown"])
                loop, summary = self.loop(driver)
                self.assertEqual(driver.trail, ["read:title", "new-game", "quiet", "read:unknown"])
                self.assertEqual((summary["ended"], summary["screen"], summary["final_frame"]),
                                 ("unknown-screen", "unknown", "f" * 64))
                self.assertEqual(driver.frames, [e020_loop.FINAL_FRAME])
                self.assertEqual([n["reason"] for n in driver.notes if n.get("event") == "game-end"],
                                 ["unknown-screen"])

    def test_a_known_screen_that_never_settles_still_aborts_not_ready(self):
        """The round 3 guard holds: the board, with or without its menu, and the notice are waited on,
        read between the blocks, and never acted on when they do not settle."""
        for screen in e020_loop.WAIT_ON:
            with self.subTest(screen=screen):
                driver = FakeDriver([1], noisy=99, raises=True, screens=["title"] + [screen] * 99)
                loop = e020_loop.BatchLoop(driver, dict(self.batch, games_max="1"), clock=lambda: 0)
                with self.assertRaises(e020_loop.NotReady):
                    loop.run()
                self.assertEqual([n for n, _ in driver.blocks], ["new-game"] + ["quiet"] * e020_loop.QUIET_ATTEMPTS)
                self.assertEqual(driver.readings, ["title"] + [screen] * e020_loop.QUIET_ATTEMPTS)
                self.assertTrue(loop.summary["ended"].startswith("aborted: not-ready"), loop.summary)
                self.assertEqual(driver.frames, [])

    def test_new_game_is_sent_only_on_the_title(self):
        """Before game 1 any other screen ends the sitting, and so does the board with its menu row lit
        (T41): from it New Game quits a live game. After a game, the next one starts on the title only."""
        for before_first in ("unknown", "board", "board-menu", "eliminated", "game-over", "scoreboard"):
            with self.subTest(before_first=before_first):
                driver = FakeDriver([], screens=[before_first])
                _, summary = self.loop(driver)
                self.assertEqual(driver.blocks, [])
                self.assertEqual((summary["games"], summary["ended"]), (0, "unknown-screen"))
                self.assertNotIn("game-start", [n.get("event") for n in driver.notes])

    def test_the_second_sittings_winner_notice_ends_the_game_and_continue_is_clicked_once(self):
        """Sitting 20261008T195537Z: after KEEP PLAYING the winner notice came up and was read as the
        board, so the play-out would have polled to `sitting_seconds`. Now (round 6): the game ends,
        its game-end line names the winner by colour word, CONTINUE once, then the screen decides."""
        screens = ["title"] + ["board-menu"] * 14 + ["eliminated", "board", "game-over", "title", "unknown"]
        driver = FakeDriver([1] * 14, screens=screens)
        _, summary = self.loop(driver)
        after = driver.trail[driver.trail.index("eliminated-keep-playing") + 1:]
        self.assertEqual(after[:6], ["read:board", "read:game-over", "winner", "game-over-continue", "read:title",
                                     "new-game"])
        self.assertEqual([n for n, _ in driver.blocks].count("game-over-continue"), 1)
        ends = [n for n in driver.notes if n.get("event") == "game-end"]
        self.assertEqual([(n["game"], n["reason"], n.get("ended"), n.get("winner")) for n in ends[:1]],
                         [(1, "played-out: game-over", "game-over", "red")])
        self.assertEqual([n["game"] for n in driver.notes if n.get("event") == "game-start"], [1, 2])
        self.assertEqual(summary["games"], 2)
        self.assertEqual(driver.readings.count("title"), 2)      # the screen after CONTINUE is the next game's

    def test_the_winner_notice_at_a_turns_start_ends_the_game(self):
        for winner in ("green", None):
            with self.subTest(winner=winner):
                driver = FakeDriver([1, 1], screens=["title", "board-menu", "game-over", "title"])
                driver.winner = winner
                _, summary = self.loop(driver, games_max="1")
                self.assertEqual(driver.trail, ["read:title", "new-game", "quiet", "read:board-menu", "place", "commit",
                                                "quiet", "read:game-over", "winner", "game-over-continue",
                                                "read:title"])
                ends = [n for n in driver.notes if n.get("event") == "game-end"]
                self.assertEqual([(n["reason"], n["ended"], n["winner"], n["turn"]) for n in ends],
                                 [("game-over", "game-over", winner, 2)])
                self.assertEqual(summary["ended"], "games-max")
                self.assertEqual(driver.frames, [])

    def test_after_continue_only_a_proven_new_game_screen_starts_the_next_game(self):
        for screen in ("unknown", "board", "board-menu", "eliminated", "game-over"):
            with self.subTest(screen=screen):
                driver = FakeDriver([1], screens=["title", "board-menu", "game-over", screen])
                _, summary = self.loop(driver)
                self.assertEqual(driver.trail[-3:], ["winner", "game-over-continue", "read:" + screen])
                self.assertEqual([n for n, _ in driver.blocks].count("new-game"), 1)
                self.assertEqual((summary["games"], summary["ended"], summary["screen"]), (1, "unknown-screen", screen))
                self.assertEqual(driver.frames, [e020_loop.FINAL_FRAME])
                self.assertEqual([n.get("ended") for n in driver.notes if n.get("event") == "game-end"], ["game-over"])

    def test_the_winner_notice_between_quiet_blocks_is_waited_on_not_unknown(self):
        """A wait that reads the winner notice keeps waiting (round 6); the turn's start then ends the game."""
        driver = FakeDriver([1], screens=["title", "board-menu", "game-over", "game-over", "title"],
                            quiet_script=[True, False, True])
        _, summary = self.loop(driver, games_max="1")
        self.assertEqual(driver.trail, ["read:title", "new-game", "quiet", "read:board-menu", "place", "commit",
                                        "quiet", "read:game-over", "quiet", "read:game-over", "winner",
                                        "game-over-continue", "read:title"])
        self.assertEqual(summary["ended"], "games-max")
        self.assertEqual(driver.frames, [])

    def test_a_refused_placement_on_a_board_without_its_menu_is_not_a_game_end(self):
        """No menu row: the game is not the human's turn, so the loop stops instead of starting a game."""
        driver = FakeDriver([None, None], screens=["title", "board-menu", "board", "board"])
        _, summary = self.loop(driver)
        self.assertEqual([n for n, _ in driver.blocks].count("new-game"), 1)
        self.assertEqual((summary["ended"], summary["screen"]), ("unknown-screen", "board"))

    # --- T41 round 1: the deadline is rechecked before every input ---------------------------------

    def timed(self, driver, **batch):
        """A loop whose clock says 0 until `expire()` is called, and whose sleep (the play-out poll) is
        recorded. Returns (loop, expire): `expire` is also what a driver hook calls, as time passing."""
        now = [0]
        loop = e020_loop.BatchLoop(driver, dict(self.batch, **batch), clock=lambda: now[0],
                                   sleep=lambda s: driver.sleeps.append(s))
        return loop, lambda *_: now.__setitem__(0, 2000)

    def assert_sent_nothing_after(self, driver, loop, last, ended="sitting-seconds"):
        """The deadline ran out in a wait: no input block after `last`, no last frame, a clean end."""
        sent = [n for n, _ in driver.blocks if n != "quiet"]
        self.assertEqual(sent[-1], last, sent)
        self.assertEqual(loop.summary["ended"], ended)
        self.assertEqual(driver.frames, [])

    def test_the_deadline_passing_during_the_play_out_poll_sends_no_continue_after_the_winner_notice(self):
        """Luna R1: PLAYOUT_POLL sleeps, the time runs out in it, the next reading is the winner notice.
        The notice ends the game (logged), but CONTINUE is not clicked: no click on timeout."""
        driver = FakeDriver([1], screens=["title", "board-menu", "eliminated", "board", "game-over", "title"])
        loop, expire = self.timed(driver)
        loop.sleep = lambda s: (driver.sleeps.append(s), expire() if len(driver.sleeps) == 2 else None)
        summary = loop.run()
        self.assertEqual(driver.sleeps, [e020_loop.PLAYOUT_POLL] * 2)
        self.assertEqual(driver.trail[-2:], ["read:game-over", "winner"])
        self.assertNotIn("game-over-continue", [n for n, _ in driver.blocks])
        self.assert_sent_nothing_after(driver, loop, "eliminated-keep-playing")
        self.assertEqual([(n["reason"], n.get("ended")) for n in driver.notes if n.get("event") == "game-end"],
                         [("played-out: game-over", "game-over")])
        self.assertEqual(summary["games"], 1)

    def test_the_deadline_passing_during_the_play_out_poll_sends_no_continue_after_the_scoreboard(self):
        driver = FakeDriver([1], screens=["title", "board-menu", "eliminated", "scoreboard", "title"])
        loop, expire = self.timed(driver)
        loop.sleep = lambda s: (driver.sleeps.append(s), expire())
        loop.run()
        self.assert_sent_nothing_after(driver, loop, "eliminated-keep-playing")
        self.assertNotIn("scoreboard-continue", [n for n, _ in driver.blocks])
        self.assertEqual([n["reason"] for n in driver.notes if n.get("event") == "game-end"], ["played-out: scoreboard"])

    def test_the_deadline_passing_during_the_wait_after_a_dismiss_sends_no_second_placement(self):
        driver = FakeDriver([None, 1], screens=["title", "board-menu", "board-menu"])
        loop, expire = self.timed(driver)
        driver.after["quiet"] = lambda d: expire() if d.trail[-2:-1] == ["dismiss"] else None
        loop.run()
        self.assert_sent_nothing_after(driver, loop, "dismiss")
        self.assertEqual([n for n, _ in driver.blocks].count("place"), 1)
        self.assertEqual([n["reason"] for n in driver.notes if n.get("event") == "game-end"], ["sitting-seconds"])

    def test_the_deadline_passing_in_the_placement_sends_no_commit_and_none_after_a_failed_one_no_dismiss(self):
        for results, last in (([1], "place"), ([None], "place")):
            with self.subTest(results=results):
                driver = FakeDriver(results, screens=["title", "board-menu"])
                loop, expire = self.timed(driver)
                driver.after["place"] = expire
                loop.run()
                self.assert_sent_nothing_after(driver, loop, last)
                self.assertNotIn("commit", [n for n, _ in driver.blocks])
                self.assertNotIn("dismiss", [n for n, _ in driver.blocks])

    def test_the_deadline_passing_in_the_screen_read_sends_no_keep_playing(self):
        driver = FakeDriver([1], screens=["title", "board-menu", "eliminated", "board"])
        loop, expire = self.timed(driver)
        driver.after["read:eliminated"] = expire
        loop.run()
        self.assert_sent_nothing_after(driver, loop, "commit")
        self.assertNotIn("eliminated-keep-playing", [n for n, _ in driver.blocks])

    def test_the_deadline_passing_in_the_read_after_the_winners_continue_sends_no_scoreboard_continue(self):
        driver = FakeDriver([1], screens=["title", "board-menu", "game-over", "scoreboard", "title"])
        loop, expire = self.timed(driver)
        driver.after["read:scoreboard"] = expire
        loop.run()
        self.assert_sent_nothing_after(driver, loop, "game-over-continue")
        self.assertNotIn("scoreboard-continue", [n for n, _ in driver.blocks])
        self.assertEqual([e for e in (n.get("event") for n in driver.notes) if e == "loss-credited"], ["loss-credited"])

    def test_the_deadline_passing_in_the_read_of_the_title_sends_no_new_game_and_logs_no_game(self):
        driver = FakeDriver([], screens=["title"])
        loop, expire = self.timed(driver)
        driver.after["read:title"] = expire
        loop.run()
        self.assertEqual(driver.blocks, [])
        self.assertEqual(loop.summary["ended"], "sitting-seconds")
        self.assertNotIn("game-start", [n.get("event") for n in driver.notes])
        self.assertEqual((loop.summary["games"], driver.frames), (0, []))

    def test_the_deadline_passing_in_the_wait_before_the_next_game_sends_no_new_game(self):
        driver = FakeDriver([1], screens=["title", "board-menu", "game-over", "title"])
        loop, expire = self.timed(driver, games_max="2")
        driver.after["game-over-continue"] = expire
        loop.run()
        self.assert_sent_nothing_after(driver, loop, "game-over-continue")
        self.assertEqual([n for n, _ in driver.blocks].count("new-game"), 1)
        self.assertEqual([n["game"] for n in driver.notes if n.get("event") == "game-start"], [1])

    # --- T41: the Scoreboard ---------------------------------------------------------------------

    def test_the_scoreboard_after_the_winner_notice_is_left_once_and_the_title_starts_the_next_game(self):
        """The game credited a loss: `loss-credited` is logged before the click, CONTINUE (block
        `scoreboard-continue`) once, then the screen is read, and New Game is sent on the title only."""
        driver = FakeDriver([1], screens=["title", "board-menu", "game-over", "scoreboard", "title", "unknown"])
        _, summary = self.loop(driver, games_max="2")
        self.assertEqual(driver.trail[driver.trail.index("game-over-continue"):][:6],
                         ["game-over-continue", "read:scoreboard", "note:loss-credited", "scoreboard-continue",
                          "read:title", "new-game"])
        self.assertEqual([n for n, _ in driver.blocks].count("scoreboard-continue"), 1)
        self.assertEqual((summary["games"], summary["loss_credited"], summary["ended"]), (2, 1, "unknown-screen"))

    def test_the_scoreboard_at_a_turns_start_and_in_the_play_out_ends_the_game(self):
        for screens, reason in ((["title", "board-menu", "scoreboard", "title", "unknown"], "scoreboard"),
                                (["title", "board-menu", "eliminated", "board", "scoreboard", "title", "unknown"],
                                 "played-out: scoreboard")):
            with self.subTest(reason=reason):
                driver = FakeDriver([1], screens=screens)
                _, summary = self.loop(driver, games_max="2")
                ends = [n["reason"] for n in driver.notes if n.get("event") == "game-end"]
                self.assertEqual(ends[0], reason)
                self.assertEqual([n for n, _ in driver.blocks].count("scoreboard-continue"), 1)
                self.assertEqual([n for n, _ in driver.blocks].count("new-game"), 2)       # game 2: from the title
                self.assertEqual(driver.trail[driver.trail.index("note:loss-credited"):][:3],
                                 ["note:loss-credited", "scoreboard-continue", "read:title"])
                self.assertEqual(summary["loss_credited"], 1)

    def test_after_the_scoreboards_continue_only_the_title_starts_the_next_game(self):
        for screen, games_max in [(s, g) for s in ("unknown", "board", "board-menu", "eliminated", "game-over", "scoreboard")
                                  for g in ("1", "4")]:      # the last game too: never "games-max" after an unproven screen
            with self.subTest(screen=screen, games_max=games_max):
                driver = FakeDriver([1], screens=["title", "board-menu", "scoreboard", screen])
                _, summary = self.loop(driver, games_max=games_max)
                self.assertEqual(driver.trail[-3:], ["note:loss-credited", "scoreboard-continue", "read:" + screen])
                self.assertEqual([n for n, _ in driver.blocks].count("scoreboard-continue"), 1)   # clicked once
                self.assertEqual([n for n, _ in driver.blocks].count("new-game"), 1)
                self.assertEqual((summary["ended"], summary["screen"]), ("unknown-screen", screen))
                self.assertEqual(driver.frames, [e020_loop.FINAL_FRAME])

    def test_the_scoreboard_between_quiet_blocks_is_waited_on_not_unknown(self):
        driver = FakeDriver([1], screens=["title", "board-menu", "scoreboard", "scoreboard", "title"],
                            quiet_script=[True, False, True])
        _, summary = self.loop(driver, games_max="1")
        self.assertEqual(driver.trail[:9], ["read:title", "new-game", "quiet", "read:board-menu", "place", "commit",
                                            "quiet", "read:scoreboard", "quiet"])
        self.assertEqual(driver.frames, [])
        self.assertEqual(summary["ended"], "games-max")


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
