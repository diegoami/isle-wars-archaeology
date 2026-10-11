"""T45: a Session A sitting to its run record (experiments/E021-pro-session-a/e021_export.py) and the
progress number of what it met, offline: a synthetic sitting directory (frames are bytes the test
made, never a PNG of the game, rule 18), the pinned run/1 validator, and the carve-out's gate.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "tests"))
import e021_fixtures as fx  # noqa: E402,F401  (sys.path)
import e020_fixtures as e20  # noqa: E402
import check_no_originals  # noqa: E402
import e021_export  # noqa: E402
import e021_progress  # noqa: E402
import validate_records  # noqa: E402

SID = e20.SID


def load_e021_launcher():
    spec = importlib.util.spec_from_file_location(
        "e021_launcher", ROOT / "experiments" / "E021-pro-session-a" / "launcher.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Sitting:
    """A sitting directory under a temporary root, as the E021 launcher leaves it."""

    def __init__(self, directory, lines=(), shots=(b"read one", b"read two", b"read three"), experiment="E021"):
        self.root = Path(directory) / "wine"
        self.repo = Path(directory) / "repo"
        self.root.mkdir()
        (self.repo / "artifacts").mkdir(parents=True)
        (self.repo / "artifacts" / "known.json").write_text((ROOT / "artifacts" / "known.json").read_text())
        self.dir, _ = e20.make_sitting(self.root, batch="session-a",
                                       doc_changes={"experiment": experiment, "session_run_id": f"E021-sitting-{SID}",
                                                    "loop": {"exchange_clicks": 2, "clicks_one_army": 2}})
        self.shots = []
        for i, data in enumerate(shots, start=1):
            (self.dir / "session" / f"e021-read-{i:05d}.png").write_bytes(data)
            self.shots.append(e20.sha(data))
        with open(self.dir / "actions.jsonl", "a") as fh:
            for line in lines:
                fh.write(json.dumps(line(self.shots) if callable(line) else line) + "\n")

    def export(self):
        return e021_export.export(self.dir, "session-a", root=self.repo, sitting_root=self.root,
                                  prescribed=self.root, table=e20.TABLE)

    def record(self):
        return json.loads((self.repo / "runs" / "E021" / "session-a" / "E021-r0001.json").read_text())


def attempt(shots, **changes):
    line = {"seq": 10, "game": 1, "turn": 2, "event": "attack-attempt", "attempt": 1, "case": "even", "cell": 1,
            "attacker": 3, "defender": 4, "before": [2, "blue", 1, "red"], "after": [1, "blue", 1, "blue"],
            "battle": True, "clicks": 1, "lost": 1, "outcome": "capture", "frames": shots[:2]}
    line.update(changes)
    return line


def click(shots):
    return {"seq": 9, "game": 1, "turn": 2, "event": "exchange-click", "attempt": 1, "click": 1,
            "before": [2, "blue", 1, "red"], "after": [1, "blue", 1, "blue"], "lost": 1, "frames": shots[1:3],
            "moved_in": True}


MET = {"seq": 11, "game": 1, "turn": 2, "event": "case-met", "case": "even", "cell": 1, "attempt": 1, "battle": 1}
BUSY = {"seq": 12, "game": 1, "turn": 2, "event": "case-met", "case": "busy", "cell": 1, "battles": 3, "end": "pass"}
TURN = {"seq": 13, "game": 1, "turn": 2, "event": "turn-end", "battles": 3, "end": "pass"}


class ExportTest(unittest.TestCase):
    def test_a_sitting_exports_a_valid_record_the_gate_and_the_progress_counter_accept(self):
        with tempfile.TemporaryDirectory() as directory:
            s = Sitting(directory, [click, attempt, MET, BUSY, TURN])
            written = s.export()
            self.assertEqual(written, ["evidence/E021/E021-r0001.manifest.json", "runs/E021/session-a/E021-r0001.json"])
            record = s.record()
            self.assertEqual(validate_records.validate_document(record), [])
            self.assertEqual(record["runtime"]["platform"], "wine-on-user-machine-iwp-2.0")
            self.assertEqual(record["start_state"]["sha256"], e20.F019_SHA)
            self.assertEqual(record["actions"]["script"], "experiments/E021-pro-session-a/session-a.steps")
            self.assertEqual(check_no_originals.check_wine_gate(record, e20.TABLE)[0], "")
            manifest = json.loads((s.repo / "evidence" / "E021" / "E021-r0001.manifest.json").read_text())
            self.assertEqual({f["class"] for f in manifest["files"]}, {"recording"})
            names = {f["name"] for f in manifest["files"]}
            self.assertTrue({"e021-read-00001.png", "sitting.json", "actions.jsonl"} <= names)
            fields = {(o["step"], o.get("field")): o.get("value") for o in record["observations"]}
            self.assertEqual(fields[(0, "counter:clicks-one-army")], "2")
            self.assertIn((1, "counter:moved-in"), fields)
            self.assertEqual(fields[(2, "outcome:attack")], "capture")
            self.assertEqual(fields[(2, "aim:case")], "even")
            # only case-met groups name case:kind, so the counter sees two cells, not the aim too
            progress = e021_progress.count([s.repo / "runs" / "E021" / "session-a" / "E021-r0001.json"])
            self.assertEqual(progress["met"], 2)
            self.assertEqual(progress["rows"]["even"]["cells"], [1])
            self.assertEqual(progress["rows"]["busy"]["cells"], [1])

    def test_no_original_text_and_no_unknown_word_reaches_a_record(self):
        for bad in ({"outcome": "Not enough armies"}, {"case": "Even"}, {"before": [2, "Blue", 1, "red"]},
                    {"attacker": 47}):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as directory:
                s = Sitting(directory, [lambda shots, bad=bad: attempt(shots, **bad)])
                with self.assertRaises(e021_export.ExportRefused):
                    s.export()
                self.assertFalse((s.repo / "runs").exists())

    def test_a_cited_frame_must_be_a_file_of_the_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            s = Sitting(directory, [lambda shots: attempt(shots, frames=["0" * 64])])
            with self.assertRaises(e021_export.ExportRefused):
                s.export()

    def test_a_line_of_a_game_the_driver_never_started_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            s = Sitting(directory, [lambda shots: attempt(shots, game=2)])
            with self.assertRaises(e021_export.ExportRefused):
                s.export()

    def test_an_e020_sitting_is_never_exported_as_e021(self):
        with tempfile.TemporaryDirectory() as directory:
            s = Sitting(directory, [MET], experiment="E020")
            with self.assertRaises(e021_export.ExportRefused):
                s.export()

    def test_an_unread_count_stays_out_of_the_record(self):
        with tempfile.TemporaryDirectory() as directory:
            s = Sitting(directory, [lambda shots: attempt(shots, after=[None, None, 1, "blue"])])
            s.export()
            fields = {o.get("field") for o in s.record()["observations"]}
            self.assertNotIn("counter:attacker-after", fields)
            self.assertIn("counter:defender-after", fields)

    def test_an_unresolved_attempt_and_an_unknown_count_carry_no_cell_and_no_total(self):
        with tempfile.TemporaryDirectory() as directory:
            s = Sitting(directory, [lambda shots: attempt(shots, outcome="unresolved", answered=False, lost=None,
                                                          unknown=1, battle=False)])
            s.export()
            record = s.record()
            fields = {o.get("field"): o.get("value") for o in record["observations"] if o["step"] == 1}
            self.assertEqual(fields["outcome:attack"], "unresolved")
            self.assertEqual(fields["counter:attacker-answered"], "0")
            self.assertEqual(fields["counter:clicks-unknown"], "1")
            self.assertNotIn("counter:lost", fields)
            path = s.repo / "runs" / "E021" / "session-a" / "E021-r0001.json"
            self.assertEqual(e021_progress.count([path])["met"], 0)

    def test_run_ids_go_on_and_nothing_is_written_over(self):
        with tempfile.TemporaryDirectory() as directory:
            s = Sitting(directory, [MET])
            s.export()
            second = s.export()
            self.assertEqual(second[1], "runs/E021/session-a/E021-r0002.json")


class LauncherTest(unittest.TestCase):
    def setUp(self):
        self.launcher = load_e021_launcher()

    def test_help_prints_the_batch_and_an_unknown_batch_is_refused(self):
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(self.launcher.main(["--batch", "session-a", "--help"]), 0)
            self.assertEqual(self.launcher.main(["--batch", "cmb-accumulation", "--help"]), 2)
        self.assertIn("runs/E021/session-a/", out.getvalue())
        self.assertIn("unknown batch", err.getvalue())

    def test_missing_templates_refuse_the_sitting_before_anything_starts(self):
        with self.assertRaises(SystemExit):
            self.launcher.load_templates(Path("/nonexistent/reader-templates.json"))

    def test_the_stage_origin_is_read_from_the_sessions_observation(self):
        obs = [{"field": "other", "value": "1,2"}, {"field": self.launcher.ORIGIN_FIELD, "value": "40,12"}]
        self.assertEqual(self.launcher.stage_origin(obs), (40, 12))
        self.assertIsNone(self.launcher.stage_origin([]))

    def test_the_capture_is_cropped_to_the_stage(self):
        import numpy as np
        import pngdecode
        with tempfile.TemporaryDirectory() as directory:
            rgb = np.zeros((620, 840, 3), dtype=np.uint8)
            rgb[12, 40] = (1, 2, 3)

            class Active:
                obs = [{"field": self.launcher.ORIGIN_FIELD, "value": "40,12"}]
                outputs = []

                def observe_screenshot(inner, name):
                    path = Path(directory) / name
                    path.write_bytes(pngdecode.encode(rgb))
                    inner.outputs.append((name, str(path), "screenshot"))
                    return "p" * 64, "q" * 64
            stage, digest = self.launcher.session_capture(Active())()
            self.assertEqual(stage.shape, (600, 800, 3))
            self.assertEqual(tuple(stage[0, 0]), (1, 2, 3))
            self.assertEqual(digest, "q" * 64)

    def test_the_body_runs_the_session_a_loop_with_the_cells_met(self):
        seen = {}

        class Loop:
            def __init__(self, clicks, batch, restore=None, shipped_skr=None, reader=None, met=()):
                seen.update(reader=reader, met=set(met), batch=batch)
                self.summary = {"ended": "games-max"}

            def run(self):
                return self.summary

        class Watcher:
            def __init__(self, *args):
                pass

            def start(self):
                import threading
                thread = threading.Thread(target=lambda: None)
                thread.start()
                return thread, threading.Event()

        class Active:
            obs, env, window = [], {}, "0x1"

            def expect(self, name):
                pass

            def known_screen(self):
                pass

            def observe_screenshot(self, name):
                return "p" * 64, "q" * 64

            perform = screen_name = screen_winner = None

        with tempfile.TemporaryDirectory() as directory:
            paths = {k: Path(directory) / k for k in ("actions", "frames", "index", "log")}
            summary = {}
            blocks = (ROOT / "experiments" / "E021-pro-session-a" / "session-a.steps").read_text()
            body = self.launcher.make_body(paths, {"games_max": 1}, blocks, summary, templates=None,
                                           met={("even", 1)}, watcher_factory=Watcher, loop_factory=Loop,
                                           reader_factory=lambda active: "the reader")
            body(Active())
        self.assertEqual(seen["reader"], "the reader")
        self.assertEqual(seen["met"], {("even", 1)})
        self.assertEqual(summary, {"ended": "games-max"})


if __name__ == "__main__":
    unittest.main()
