"""Tests for runtime/iwp/driver/watcher.py (T38).

The watcher is the per-frame capture of a model-driven sitting (rule 18 carve-out). These tests
use fakes only: no wine, no display, no `import`. They pin the contract the task names — the game
window is captured (never the desktop), frames are named `<step>-<epochms>.png`, each is sha256'd
into `frames-index.jsonl` with its geometry, and no original text reaches `watcher.log`
(constraint D). T38 round 2, R1: every command gets the session's environment, so it acts on the
session's own display, never the caller's. T42 adds the faster capture: identical consecutive frames are
stored once, the frame count is bounded, the schedule is deadline-driven, the geometry is read once per
few seconds, and the rate measurement runs on a display of its own.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime" / "iwp"))
import driver.watcher as watcher_module  # noqa: E402
from driver.watcher import (Watcher, WatcherError, FrameCapReached, frame_name, sha256_file,  # noqa: E402
                            capture_command, rate_summary, GEOMETRY_REFRESH)

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

    def watcher(self, step=3, epoch_ms=EPOCH, run=None, geometry=None, payload=None, **kw):
        def capture(cmd, env):
            self.calls.append(list(cmd))
            self.envs.append(env)
            Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
            Path(cmd[-1]).write_bytes(payload() if payload else b"synthetic frame bytes, never a real capture")
        def read_geometry(wid, env):
            self.geometry_envs.append(env)
            return {"x": 1, "y": 2, "width": 800, "height": 600}
        w = Watcher(
            "0x2a",
            SESSION_ENV,
            self.frames,
            self.dir / "frames-index.jsonl",
            self.dir / "watcher.log",
            step_source=lambda: step,
            run=run or capture,
            geometry=geometry or read_geometry,
            clock=kw.pop("clock", lambda: epoch_ms / 1000.0),
            **kw,
        )
        self.addCleanup(w.close)
        return w

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
        frames = iter([b"first different frame", b"second different frame"])
        w = self.watcher(payload=lambda: next(frames))
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


    # ---- T42: the faster capture

    def index_lines(self):
        return [json.loads(t) for t in (self.dir / "frames-index.jsonl").read_text().splitlines()]

    def test_identical_consecutive_frames_are_stored_once(self):
        w = self.watcher(payload=lambda: b"a still screen")
        lines = [w.capture_once() for _ in range(3)]
        self.assertEqual(len(list(self.frames.iterdir())), 1)
        self.assertEqual({l["name"] for l in lines}, {lines[0]["name"]})
        self.assertEqual([l.get("duplicate", False) for l in lines], [False, True, True])
        self.assertEqual({l["sha256"] for l in lines}, {sha256_file(self.frames / lines[0]["name"])})
        self.assertEqual(len(self.index_lines()), 3)           # every capture is still indexed
        self.assertEqual((w.count, w.stored), (3, 1))

    def test_only_consecutive_duplicates_are_dropped(self):
        frames = iter([b"A", b"B", b"A"])
        w = self.watcher(payload=lambda: next(frames))
        lines = [w.capture_once() for _ in range(3)]
        self.assertEqual(len(list(self.frames.iterdir())), 3)
        self.assertEqual(len({l["name"] for l in lines}), 3)

    def test_every_index_line_names_a_stored_file_with_its_sha256(self):
        frames = iter([b"A", b"A", b"B", b"B", b"B"])
        w = self.watcher(payload=lambda: next(frames))
        for _ in range(5):
            w.capture_once()
        for line in self.index_lines():
            self.assertEqual(sha256_file(self.frames / line["name"]), line["sha256"])

    def test_a_frame_lands_in_the_staging_directory_first_and_leaves_none_behind(self):
        w = self.watcher()
        w.capture_once()
        w.capture_once()
        self.assertNotEqual(Path(self.calls[0][-1]).parent, self.frames)
        self.assertEqual([p.suffix for p in self.frames.iterdir()], [".png"])      # no stage file in the sitting
        stage = w.stage_dir
        w.close()
        self.assertFalse(stage.exists())

    def test_the_frame_count_is_bounded_and_a_new_frame_past_it_is_not_kept(self):
        frames = iter([b"1", b"2", b"3", b"3"])
        w = self.watcher(payload=lambda: next(frames), max_frames=2)
        w.capture_once()
        w.capture_once()
        with self.assertRaises(FrameCapReached):
            w.capture_once()                                    # a third distinct frame
        self.assertEqual(len(list(self.frames.iterdir())), 2)
        self.assertEqual(len(self.index_lines()), 2)

    def test_a_duplicate_past_the_bound_is_still_indexed(self):
        w = self.watcher(payload=lambda: b"still", max_frames=1)
        w.capture_once()
        line = w.capture_once()
        self.assertTrue(line["duplicate"])
        self.assertEqual(len(self.index_lines()), 2)

    def test_the_loop_stops_at_the_bound_and_says_so(self):
        import threading
        frames = iter(str(i).encode() for i in range(10))
        w = self.watcher(payload=lambda: next(frames), max_frames=2, interval=0.001)
        thread, stop = w.start()
        thread.join(timeout=10)
        stop.set()
        self.assertFalse(thread.is_alive())
        self.assertIn("frame cap reached", (self.dir / "watcher.log").read_text())
        self.assertEqual(len(list(self.frames.iterdir())), 2)

    def test_the_geometry_is_read_once_per_refresh_not_per_frame(self):
        now = [1000.0]
        reads = []
        def read(wid, env):
            reads.append(now[0])
            return {"x": 0, "y": 0, "width": 800, "height": 600}
        w = self.watcher(geometry=read, clock=lambda: now[0], payload=lambda: str(now[0]).encode())
        for _ in range(5):
            w.capture_once()
            now[0] += 0.125
        self.assertEqual(len(reads), 1)
        now[0] += GEOMETRY_REFRESH
        line = w.capture_once()
        self.assertEqual(len(reads), 2)
        self.assertEqual(line["geometry"]["width"], 800)

    def test_a_failed_geometry_read_is_retried_on_the_next_frame(self):
        results = iter([{}, {"width": 800}, {"width": 800}])
        reads = []
        def read(wid, env):
            reads.append(1)
            return next(results)
        w = self.watcher(geometry=read, payload=iter(str(i).encode() for i in range(9)).__next__)
        first, second, third = w.capture_once(), w.capture_once(), w.capture_once()
        self.assertEqual((first["geometry"], second["geometry"], third["geometry"]),
                         ({}, {"width": 800}, {"width": 800}))
        self.assertEqual(len(reads), 2)

    def test_the_schedule_is_deadline_driven_not_a_pause_after_each_capture(self):
        """A capture of 40 ms on a 125 ms interval waits 85 ms, so the period stays 125 ms."""
        mono = [0.0]
        waits = []
        class Stop:
            def __init__(self): self.n = 0
            def is_set(self): return self.n >= 4
            def wait(self, t):
                waits.append(round(t, 3)); mono[0] += t; self.n += 1
        def capture(cmd, env):
            mono[0] += 0.040
            Path(cmd[-1]).write_bytes(str(mono[0]).encode())
        w = self.watcher(run=capture, interval=0.125, monotonic=lambda: mono[0])
        w.run_loop(Stop())
        self.assertEqual(waits, [0.085] * 4)

    def test_a_slow_capture_does_not_turn_into_a_burst_afterwards(self):
        mono = [0.0]
        waits = []
        slow = iter([0.5, 0.01, 0.01])
        class Stop:
            def __init__(self): self.n = 0
            def is_set(self): return self.n >= 3
            def wait(self, t):
                waits.append(round(t, 3)); mono[0] += t; self.n += 1
        def capture(cmd, env):
            mono[0] += next(slow)
            Path(cmd[-1]).write_bytes(str(mono[0]).encode())
        w = self.watcher(run=capture, interval=0.125, monotonic=lambda: mono[0])
        w.run_loop(Stop())
        self.assertEqual(waits, [0.0, 0.115, 0.115])          # late: restart from now, then back on the period

    def test_the_root_window_is_refused_in_any_case(self):
        for bad in ("root", "ROOT", " Root "):
            with self.subTest(window=bad):
                with self.assertRaises(WatcherError):
                    Watcher(bad, SESSION_ENV, self.frames, self.dir / "i.jsonl", self.dir / "w.log",
                            step_source=lambda: 0)

    def test_the_capture_command_targets_the_window_id_never_root(self):
        cmd = capture_command("0x2a", "/x/f.png")
        self.assertEqual(cmd, ["import", "-window", "0x2a", "/x/f.png"])
        self.assertNotIn("root", cmd)

    def test_the_real_capture_runs_on_the_sessions_display_whatever_the_callers_is(self):
        """Through the real subprocess helper: a stand-in `import` records the DISPLAY and the arguments it
        was started with. The caller's DISPLAY is :wrong; the capture must see the session's, and the window id."""
        import os
        from unittest import mock
        bindir = self.dir / "bin"
        bindir.mkdir()
        fake = bindir / "import"
        fake.write_text('#!/bin/sh\nprintf "DISPLAY=%s ARGS=%s" "$DISPLAY" "$*" > "$3"\n')
        fake.chmod(0o755)
        env = dict(SESSION_ENV, PATH=f"{bindir}:/usr/bin:/bin")
        w = Watcher("0x2a", env, self.frames, self.dir / "i.jsonl", self.dir / "w.log",
                    step_source=lambda: 0, geometry=lambda wid, e: {})
        self.addCleanup(w.close)
        with mock.patch.dict(os.environ, {"DISPLAY": ":wrong"}):
            line = w.capture_once()
        text = (self.frames / line["name"]).read_text()
        self.assertTrue(text.startswith("DISPLAY=:88 ARGS=-window 0x2a "), text)
        self.assertNotIn("root", text)
        self.assertNotIn(":wrong", text)

    def test_rate_summary_counts_captures_after_the_first_over_the_time_between(self):
        lines = [{"epoch_ms": 1000 + i * 125, "capture_ms": 80} for i in range(9)]    # 8 intervals, 1 s
        self.assertEqual(rate_summary(lines)["fps"], 8.0)
        self.assertEqual(rate_summary(lines)["capture_ms"]["median"], 80)
        self.assertEqual(rate_summary(lines[:1]), {})
        self.assertEqual(rate_summary([]), {})

    def test_the_cli_runs_nothing_without_measure_rate(self):
        import contextlib, io
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            watcher_module.main([])
        self.assertEqual(caught.exception.code, 2)


def _have(*tools):
    import shutil
    return all(shutil.which(t) for t in tools)


@unittest.skipUnless(_have("Xvfb", "xdpyinfo", "xdotool", "animate", "convert", "import"),
                     "needs Xvfb, xdotool and ImageMagick (the rate measurement starts its own display)")
class MeasureRateTest(unittest.TestCase):
    def test_the_measurement_runs_on_a_display_of_its_own_and_writes_its_files(self):
        import os
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "m"
            with mock.patch.dict(os.environ, {"DISPLAY": ":0"}):        # the caller's desktop: must not be touched
                doc, _ = watcher_module.measure_rate(2.0, out, frames_dir=Path(tmp) / "test-frames")
            self.assertFalse((Path(tmp) / "test-frames").exists())     # the synthetic frames are removed
            self.assertNotEqual(doc["display"], ":0")
            self.assertGreaterEqual(doc["captures"], 4)
            self.assertEqual(doc["failures"], 0)
            self.assertTrue((out / "rate.json").is_file())
            self.assertTrue((out / "frames-index.jsonl").is_file())
            for line in (json.loads(t) for t in (out / "frames-index.jsonl").read_text().splitlines()):
                self.assertEqual(line["window"], doc["window"])
            with self.assertRaises(FileExistsError):                   # a measurement is never written over
                watcher_module.measure_rate(1.0, out)
            (Path(tmp) / "taken").mkdir()
            with self.assertRaises(FileExistsError):                   # nor are the test frames put in an old folder
                watcher_module.measure_rate(1.0, Path(tmp) / "m2", frames_dir=Path(tmp) / "taken")


if __name__ == "__main__":
    unittest.main(verbosity=2)
