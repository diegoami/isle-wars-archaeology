"""Tests for runtime/iwp/driver/watcher.py (T38).

The watcher is the per-frame capture of a model-driven sitting (rule 18 carve-out). These tests
use fakes only: no wine, no display, no `import`. They pin the contract the task names — the game
window is captured (never the desktop), frames are named `<step>-<epochms>.png`, each is sha256'd
into `frames-index.jsonl` with its geometry, and no original text reaches `watcher.log`
(constraint D). T38 round 2, R1: every command gets the session's environment, so it acts on the
session's own display, never the caller's.
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
SESSION_ENV = {"DISPLAY": ":88", "WINEPREFIX": "/synthetic/prefix"}


class WatcherTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.frames = self.dir / "frames"
        self.calls = []
        self.envs = []
        self.geometry_envs = []

    def watcher(self, step=3, epoch_ms=EPOCH, run=None, geometry=None):
        def capture(cmd, env):
            self.calls.append(list(cmd))
            self.envs.append(env)
            Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
            Path(cmd[-1]).write_bytes(b"synthetic frame bytes, never a real capture")
        def read_geometry(wid, env):
            self.geometry_envs.append(env)
            return {"x": 1, "y": 2, "width": 800, "height": 600}
        return Watcher(
            "0x2a",
            SESSION_ENV,
            self.frames,
            self.dir / "frames-index.jsonl",
            self.dir / "watcher.log",
            step_source=lambda: step,
            run=run or capture,
            geometry=geometry or read_geometry,
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
        def failing(cmd, env):
            raise WatcherError("capture failed")
        w = self.watcher(run=failing)
        with self.assertRaises(WatcherError):
            w.capture_once()
        self.assertFalse((self.dir / "frames-index.jsonl").exists())

    def test_an_empty_or_root_window_is_refused(self):
        for bad in ("", "   ", "root"):
            with self.subTest(window=bad):
                with self.assertRaises(WatcherError):
                    Watcher(bad, SESSION_ENV, self.frames, self.dir / "i.jsonl", self.dir / "w.log",
                            step_source=lambda: 0)

    def test_every_command_runs_on_the_sessions_display(self):
        """R1: the capture and the geometry read get the session's environment, whatever the caller's
        DISPLAY is; without it they would act on the caller's display."""
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"DISPLAY": ":wrong"}):
            self.watcher().capture_once()
        self.assertEqual([e["DISPLAY"] for e in self.envs], [":88"])
        self.assertEqual([e["DISPLAY"] for e in self.geometry_envs], [":88"])

    def test_the_default_helpers_pass_the_sessions_environment_to_the_checked_helper(self):
        """R1 at the real helpers: spike.must receives env= with the session's DISPLAY."""
        from unittest import mock
        import driver.watcher as watcher
        with mock.patch.object(watcher.spike, "must") as must:
            must.return_value = mock.MagicMock(stdout=b"X=1\nY=2\nWIDTH=800\nHEIGHT=600\n")
            watcher._default_run(["import", "-window", "0x2a", "f.png"], SESSION_ENV)
            watcher._default_geometry("0x2a", SESSION_ENV)
        for call in must.call_args_list:
            self.assertEqual(call.kwargs.get("env"), SESSION_ENV)

    def test_a_watcher_without_the_sessions_display_is_refused(self):
        for env in (None, {}, {"DISPLAY": ""}):
            with self.subTest(env=env):
                with self.assertRaises(WatcherError):
                    Watcher("0x2a", env, self.frames, self.dir / "i.jsonl", self.dir / "w.log",
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
