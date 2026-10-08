"""Tests for runtime/iwp/driver/watcher.py (T38).

The watcher is the per-frame capture of a model-driven sitting (rule 18 carve-out). These tests
use fakes only: no wine, no display, no `import`. They pin the contract the task names — the game
window is captured (never the desktop), frames are named `<step>-<epochms>.png`, each is sha256'd
into `frames-index.jsonl` with its geometry, and no original text reaches `watcher.log`
(constraint D).
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime" / "iwp"))
from driver.watcher import Watcher, WatcherError, frame_name, sha256_file  # noqa: E402

EPOCH = 1_700_000_000_000


class WatcherTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.frames = self.dir / "frames"
        self.calls = []

    def watcher(self, step=3, epoch_ms=EPOCH, run=None, geometry=None):
        def capture(cmd):
            self.calls.append(list(cmd))
            Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
            Path(cmd[-1]).write_bytes(b"synthetic frame bytes, never a real capture")
        return Watcher(
            "0x2a",
            self.frames,
            self.dir / "frames-index.jsonl",
            self.dir / "watcher.log",
            step_source=lambda: step,
            run=run or capture,
            geometry=geometry or (lambda wid: {"x": 1, "y": 2, "width": 800, "height": 600}),
            clock=lambda: epoch_ms / 1000.0,
        )

    def test_frame_name_is_step_then_epochms(self):
        self.assertEqual(frame_name(7, 1700), "7-1700.png")

    def test_capture_names_hashes_and_indexes_the_frame(self):
        line = self.watcher().capture_once()
        self.assertEqual(line["name"], f"3-{EPOCH}.png")
        self.assertEqual(line["sha256"], sha256_file(self.frames / f"3-{EPOCH}.png"))
        self.assertEqual(line["geometry"], {"x": 1, "y": 2, "width": 800, "height": 600})
        indexed = json.loads((self.dir / "frames-index.jsonl").read_text().splitlines()[0])
        self.assertEqual(indexed, line)

    def test_the_game_window_is_captured_never_the_desktop(self):
        self.watcher().capture_once()
        self.assertEqual(self.calls[0][:2], ["import", "-window"])
        self.assertNotIn("root", self.calls[0])
        self.assertIn("0x2a", self.calls[0])

    def test_two_frames_in_the_same_millisecond_never_collide(self):
        w = self.watcher()
        first = w.capture_once()
        second = w.capture_once()
        self.assertNotEqual(first["name"], second["name"])
        self.assertEqual(len((self.dir / "frames-index.jsonl").read_text().splitlines()), 2)

    def test_a_failed_capture_is_not_indexed(self):
        def failing(cmd):
            raise WatcherError("capture failed")
        w = self.watcher(run=failing)
        with self.assertRaises(WatcherError):
            w.capture_once()
        self.assertFalse((self.dir / "frames-index.jsonl").exists())

    def test_an_empty_or_root_window_is_refused(self):
        for bad in ("", "   ", "root"):
            with self.subTest(window=bad):
                with self.assertRaises(WatcherError):
                    Watcher(bad, self.frames, self.dir / "i.jsonl", self.dir / "w.log",
                            step_source=lambda: 0)

    def test_log_lines_carry_structural_names_only(self):
        self.watcher().capture_once()
        text = (self.dir / "watcher.log").read_text()
        self.assertIn("step=3", text)
        self.assertIn("sha256=", text)
        for original_text in ("Isle", "Wars", "Pro", "Shareware", "/mnt/c/Users/"):
            self.assertNotIn(original_text, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
