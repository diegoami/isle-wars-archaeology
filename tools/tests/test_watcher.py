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
                            capture_command, capture_ms_summary, timed_capture, sustained_fps,
                            rate_passes, REQUIRED_FPS, GEOMETRY_REFRESH)

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

    # ---- T42 round 3 (Sol's round-2 R1 and R2): every index line names a file holding its sha256

    def test_a_duplicate_of_a_changed_stored_frame_is_stored_afresh(self):
        """Sol's R1: capture A, the stored file becomes B, capture A again. The new line must not name the
        changed file; the capture is stored under a new name and the old file is left as it is."""
        w = self.watcher(payload=lambda: b"A", stage_dir=self.dir / "stage")
        first = w.capture_once()
        (self.frames / first["name"]).write_bytes(b"B")
        second = w.capture_once()
        self.assertNotIn("duplicate", second)
        self.assertNotEqual(second["name"], first["name"])
        self.assertEqual(sha256_file(self.frames / second["name"]), second["sha256"])
        self.assertEqual((self.frames / first["name"]).read_bytes(), b"B")     # never written over
        self.assertEqual(w.stored, 2)
        self.assertIn("missing or changed", (self.dir / "watcher.log").read_text())

    def test_a_duplicate_of_a_missing_stored_frame_is_stored_afresh(self):
        w = self.watcher(payload=lambda: b"A", stage_dir=self.dir / "stage")
        first = w.capture_once()
        (self.frames / first["name"]).unlink()
        second = w.capture_once()
        self.assertNotIn("duplicate", second)
        self.assertEqual(sha256_file(self.frames / second["name"]), second["sha256"])
        third = w.capture_once()                       # an intact stored frame is a duplicate again
        self.assertTrue(third["duplicate"])
        self.assertEqual(third["name"], second["name"])

    def test_a_frame_changed_on_its_way_into_the_sitting_is_removed_and_not_indexed(self):
        """Sol's R2: the move delivers other bytes. WatcherError, no file left at the destination, no index line."""
        import shutil
        from unittest import mock
        real_move = shutil.move
        def corrupting_move(src, dst):
            real_move(src, dst)
            Path(dst).write_bytes(b"other bytes")
            return dst
        w = self.watcher()
        with mock.patch.object(watcher_module.shutil, "move", corrupting_move):
            with self.assertRaises(WatcherError):
                w.capture_once()
        self.assertEqual(list(self.frames.iterdir()), [])
        self.assertFalse((self.dir / "frames-index.jsonl").exists())
        self.assertEqual((w.count, w.stored), (0, 0))

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

    def test_capture_ms_summary_reports_the_capture_times(self):
        lines = [{"epoch_ms": 1000 + i * 125, "capture_ms": 80 + i} for i in range(9)]
        self.assertEqual(capture_ms_summary(lines)["median"], 84)
        self.assertEqual(capture_ms_summary(lines)["max"], 88)
        self.assertEqual(capture_ms_summary([]), {})

    # ---- T42 round 2, R1 and R2: the gate measures captures over the real interval, unrounded

    def timed(self, durations_us, seconds, interval):
        """Run the real Watcher loop through timed_capture on a fake clock counted in whole microseconds
        (so the arithmetic of the test is exact): the n-th capture takes durations_us(n) us."""
        clock = [0]
        n = [0]
        def capture(cmd, env):
            clock[0] += durations_us(n[0])
            n[0] += 1
            Path(cmd[-1]).write_bytes(str(n[0]).encode())
        def sleep(t):
            clock[0] += round(t * 1_000_000)
        w = self.watcher(run=capture, interval=interval, monotonic=lambda: clock[0] / 1e6, sleep=sleep)
        captures, interval_s = timed_capture(w, seconds)
        return w, captures, interval_s

    def test_r1_a_capture_running_past_the_deadline_counts_with_its_time(self):
        """Sol's R1: three captures, the last taking 19,750 ms. The old gate divided by the 250 ms between
        the capture starts (8 fps, passed); over the real interval it is 3 / 20 s."""
        durations = [10_000, 10_000, 19_750_000]
        w, captures, interval_s = self.timed(lambda n: durations[n], 20.0, 0.125)
        self.assertEqual(captures, 3)
        self.assertGreaterEqual(interval_s, 20.0)
        fps = sustained_fps(captures, interval_s)
        self.assertLess(fps, 0.2)
        self.assertFalse(rate_passes(fps, w.failures))

    def test_r1_the_interval_reaches_the_end_of_a_capture_past_the_deadline(self):
        durations = [10_000, 10_000, 20_000_000]               # the third ends at 20.25 s
        _, captures, interval_s = self.timed(lambda n: durations[n], 20.0, 0.125)
        self.assertEqual(captures, 3)
        self.assertAlmostEqual(interval_s, 20.25, places=6)

    def test_r1_a_tail_with_no_capture_counts_as_time(self):
        """A loop that stops early (the frame cap) still measures to the deadline."""
        frames = iter(str(i).encode() for i in range(100))
        clock = [0]
        def capture(cmd, env):
            clock[0] += 10_000
            Path(cmd[-1]).write_bytes(next(frames))
        w = self.watcher(run=capture, interval=0.125, monotonic=lambda: clock[0] / 1e6,
                         sleep=lambda t: clock.__setitem__(0, clock[0] + round(t * 1e6)), max_frames=2)
        captures, interval_s = timed_capture(w, 20.0)
        self.assertEqual(captures, 2)
        self.assertEqual(interval_s, 20.0)

    def test_r2_just_below_the_threshold_fails(self):
        """Sol's R2: 100 captures over 20.001 s is 4.99975 fps; the old gate rounded it to 5.0 and passed."""
        durations = lambda n: 201_000 if n == 99 else 10_000          # the 100th ends at 19.8 + 0.201 s
        w, captures, interval_s = self.timed(durations, 20.0, 0.2)
        self.assertEqual(captures, 100)
        self.assertAlmostEqual(interval_s, 20.001, places=6)
        fps = sustained_fps(captures, interval_s)
        self.assertLess(fps, REQUIRED_FPS)
        self.assertFalse(rate_passes(fps, w.failures))
        self.assertFalse(rate_passes(100 / 20.001, 0))

    def test_r2_exactly_at_the_threshold_passes(self):
        durations = lambda n: 200_000 if n == 99 else 10_000          # the 100th ends at 20.0 s
        w, captures, interval_s = self.timed(durations, 20.0, 0.2)
        self.assertEqual(captures, 100)
        self.assertEqual(interval_s, 20.0)
        self.assertEqual(sustained_fps(captures, interval_s), REQUIRED_FPS)
        self.assertTrue(rate_passes(sustained_fps(captures, interval_s), w.failures))

    def test_a_failed_capture_fails_the_gate_and_is_not_counted(self):
        self.assertFalse(rate_passes(8.0, 1))
        n = [0]
        clock = [0]
        def capture(cmd, env):
            clock[0] += 10_000
            n[0] += 1
            if n[0] == 2:
                raise WatcherError("capture failed")
            Path(cmd[-1]).write_bytes(str(n[0]).encode())
        w = self.watcher(run=capture, interval=0.125, monotonic=lambda: clock[0] / 1e6,
                         sleep=lambda t: clock.__setitem__(0, clock[0] + round(t * 1e6)))
        captures, _ = timed_capture(w, 1.0)
        self.assertEqual((captures, w.failures), (7, 1))

    def test_the_cli_runs_nothing_without_measure_rate(self):
        import contextlib, io
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            watcher_module.main([])
        self.assertEqual(caught.exception.code, 2)


class _Reached(Exception):
    """The measurement reached its test window on a display of its own (the guard tests stop there)."""


class _FakeProc:
    """A spawned process that stays alive until it is stopped."""
    pids = iter(range(40000, 41000))

    def __init__(self):
        self.pid = next(self.pids)
        self.stopped = False

    def poll(self):
        return 0 if self.stopped else None

    def terminate(self):
        self.stopped = True

    kill = terminate

    def wait(self, timeout=None):
        return 0


class OwnDisplayGuardTest(unittest.TestCase):
    """T42 round 2, R3: the measurement's display is accepted only when the Xvfb this run spawned holds
    the display's listening socket. These fakes make the spawned Xvfb alive and xdpyinfo answer, while
    the socket that answers belongs to `owner(display)`; nothing real is started."""

    def run_measurement(self, owner, caller_display=":0"):
        import os
        from unittest import mock
        import driver.session as sessionlib
        calls = []
        procs = {}
        displays = iter([":71", ":72", ":73", ":74"])

        def spawn(cmd, **kw):
            calls.append(("spawn", list(cmd), dict(kw.get("env") or {})))
            proc = _FakeProc()
            procs[cmd[1]] = proc
            return proc

        def probe(cmd, **kw):
            calls.append(("probe", list(cmd), dict(kw.get("env") or {})))
            return True, b"", b""

        def must(cmd, **kw):
            calls.append(("must", list(cmd), dict(kw.get("env") or {})))
            return mock.MagicMock(stdout=b"")

        def listening(path):
            display = ":" + path.rsplit("X", 1)[1]
            return {1000 + int(display[1:])} if display in procs else set()

        def held_by(pid):
            return {1000 + int(d[1:]) for d, p in procs.items() if owner(d) == "ours" and p.pid == pid}

        def start_window(env, workdir):
            display = env.get("DISPLAY")
            if owner(display) != "ours" or procs[display].stopped:
                raise AssertionError(f"a test window on {display}, a display not this run's")
            raise _Reached(display)                    # the window would start here; the test ends
        window = mock.MagicMock(side_effect=start_window)
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"DISPLAY": caller_display}), \
                mock.patch.object(watcher_module, "START_TIMEOUT", 0.1), \
                mock.patch.object(watcher_module.spike, "spawn", spawn), \
                mock.patch.object(watcher_module.spike, "probe", probe), \
                mock.patch.object(watcher_module.spike, "must", must), \
                mock.patch.object(sessionlib, "free_display", lambda exclude=(): next(displays)), \
                mock.patch.object(sessionlib, "listening_socket_inodes", listening), \
                mock.patch.object(sessionlib, "socket_inodes_of", held_by), \
                mock.patch.object(watcher_module, "_start_test_window", window), \
                mock.patch.object(watcher_module, "timed_capture",
                                  mock.MagicMock(side_effect=AssertionError("a capture on a display not this run's"))):
            try:
                watcher_module.measure_rate(1.0, Path(tmp) / "m")
                error = None
            except (WatcherError, _Reached) as exc:
                error = exc
        return error, calls, procs, window

    def test_a_display_whose_socket_another_process_holds_is_rejected(self):
        """Sol's R3: Xvfb alive and xdpyinfo answering, but the socket is another process's: every
        display is rejected, each spawned Xvfb is stopped, and no test window or capture runs."""
        error, calls, procs, window = self.run_measurement(owner=lambda d: "other")
        self.assertIsInstance(error, WatcherError)
        self.assertEqual(sorted(procs), [":71", ":72", ":73"])
        self.assertTrue(all(p.stopped for p in procs.values()))
        window.assert_not_called()
        self.assertLessEqual({c[1][0] for c in calls}, {"Xvfb", "xdpyinfo"})   # nothing else ran on them

    def test_a_taken_display_is_retried_and_the_next_one_of_its_own_is_used(self):
        """The first display's socket is another's; the second is this run's Xvfb's and is the one used."""
        error, calls, procs, window = self.run_measurement(owner=lambda d: "ours" if d == ":72" else "other")
        self.assertIsInstance(error, _Reached)
        window.assert_called_once()
        self.assertEqual(window.call_args.args[0]["DISPLAY"], ":72")
        self.assertTrue(procs[":71"].stopped)
        self.assertEqual({c[2].get("DISPLAY") for c in calls if c[1][0] == "xdpyinfo"} - {":71", ":72"}, set())

    def test_the_callers_display_is_never_used_even_when_it_looks_like_ours(self):
        """Sweep: if the display this run holds is the caller's DISPLAY, the measurement refuses it."""
        error, calls, procs, window = self.run_measurement(owner=lambda d: "ours", caller_display=":71")
        self.assertIsInstance(error, WatcherError)
        self.assertIn("caller", str(error))
        window.assert_not_called()

    def test_the_xvfb_and_its_probe_never_inherit_the_callers_display(self):
        """Sweep: the Xvfb is spawned without the caller's DISPLAY, and the readiness probe asks the new one."""
        error, calls, procs, window = self.run_measurement(owner=lambda d: "ours")
        self.assertIsInstance(error, _Reached)
        spawned = [c for c in calls if c[0] == "spawn"]
        self.assertEqual(len(spawned), 1)
        self.assertNotIn("DISPLAY", spawned[0][2])
        self.assertEqual({c[2]["DISPLAY"] for c in calls if c[1][0] == "xdpyinfo"}, {":71"})
        self.assertEqual(window.call_args.args[0]["DISPLAY"], ":71")


class MeasureRateGateTest(unittest.TestCase):
    """R1 and R2 swept to what the command reports and exits with: main() --measure-rate on fakes (no
    display, no tool), the real Watcher loop on a clock counted in whole microseconds. rate.json's fps,
    seconds_elapsed, captures and passed, and the exit code, must all follow the real interval, unrounded."""

    def measure(self, durations_us, interval):
        import contextlib, io
        from unittest import mock
        clock = [0]
        n = [0]

        def capture(cmd, env):
            clock[0] += durations_us(n[0])
            n[0] += 1
            Path(cmd[-1]).write_bytes(str(n[0]).encode())

        def make_watcher(*args, **kw):
            return Watcher(*args, run=capture, geometry=lambda wid, env: {"width": 800, "height": 600},
                           monotonic=lambda: clock[0] / 1e6, clock=lambda: 1_700_000_000 + clock[0] / 1e6,
                           sleep=lambda t: clock.__setitem__(0, clock[0] + round(t * 1e6)),
                           interval=interval, **kw)

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(watcher_module, "_start_own_xvfb",
                                  lambda env: (_FakeProc(), ":71", dict(env, DISPLAY=":71"))), \
                mock.patch.object(watcher_module, "_start_test_window", lambda env, wd: (_FakeProc(), "0x2a")), \
                mock.patch.object(watcher_module, "_tool_version", lambda cmd: "fake"), \
                mock.patch.object(watcher_module, "Watcher", make_watcher), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            code = watcher_module.main(["--measure-rate", "--seconds", "20", "--out", str(Path(tmp) / "m")])
            doc = json.loads((Path(tmp) / "m" / "rate.json").read_text())
        return code, doc, out.getvalue()

    def test_sols_r1_case_fails_the_command(self):
        durations = [10_000, 10_000, 19_750_000]
        code, doc, text = self.measure(lambda n: durations[n], 0.125)
        self.assertEqual((code, doc["passed"], doc["captures"]), (1, False, 3))
        self.assertGreaterEqual(doc["seconds_elapsed"], 20.0)
        self.assertAlmostEqual(doc["fps"], 3 / doc["seconds_elapsed"])
        self.assertIn("FAIL", text)

    def test_sols_r2_case_fails_the_command_and_reports_the_unrounded_rate(self):
        code, doc, text = self.measure(lambda n: 201_000 if n == 99 else 10_000, 0.2)
        self.assertEqual((code, doc["passed"], doc["captures"]), (1, False, 100))
        self.assertAlmostEqual(doc["seconds_elapsed"], 20.001, places=6)
        self.assertAlmostEqual(doc["fps"], 100 / 20.001, places=9)
        self.assertLess(doc["fps"], REQUIRED_FPS)
        self.assertIn("FAIL", text)

    def test_exactly_at_the_threshold_the_command_passes(self):
        code, doc, text = self.measure(lambda n: 200_000 if n == 99 else 10_000, 0.2)
        self.assertEqual((code, doc["passed"], doc["captures"], doc["fps"]), (0, True, 100, 5.0))
        self.assertIn("PASS", text)


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
