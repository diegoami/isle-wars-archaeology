"""The per-frame watcher of a model-driven sitting (T38, rule 18 carve-out; T42, a faster capture).

It attaches to the game window id the session already holds (Session.window), on the session's
own display: every command it runs gets the session's environment (Session.env, whose DISPLAY is
the session's private Xvfb), never the caller's (T38 round 2, R1). It captures *that* window on a
fixed schedule (ImageMagick `import -window <id>`, never `-window root`: the desktop is never captured),
names each stored frame `<step>-<epochms>.png`, sha256s it, and appends one line per capture to
`frames-index.jsonl` (name, sha256, wall time, epoch_ms, window geometry, capture_ms). `watcher.log`
carries the same structural names only: constraint D of the carve-out keeps the original's text (event
names, card names, screen labels, the title) out of the watcher's lines.

T42: the schedule is deadline-driven (the next capture is due one interval after the last was due, not
one interval after it finished), the window geometry is read once per GEOMETRY_REFRESH s, not per
frame, and a capture lands in a local staging directory first. A frame identical to the one before it
is stored once: its index line names the stored frame (same sha256) and says `duplicate`, so every
index line still names a file that exists with the sha256 it records. At most `max_frames` frames are
stored per sitting (disk bound). `--measure-rate` measures the sustained rate on a display of its own.

The command runner, clock and geometry reader are injected so this module is testable against
fakes, with no wine and no display; each is called with the session's environment. A failed capture is
logged and skipped, never written as a frame: a frame in the index is a file that exists and whose
sha256 is the one recorded.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_SPIKE = str(ROOT / "runtime" / "iwp" / "spike")
if _SPIKE not in sys.path:
    sys.path.insert(0, _SPIKE)
import cycle as spike  # noqa: E402  (the driver's checked command helpers, reused)

FRAME_SUFFIX = ".png"
CAPTURE_TIMEOUT = 30          # s, one capture bound (F006: every helper command has a bound)
DEFAULT_INTERVAL = 0.125      # s, the schedule period: 8 frames per second wanted, 5 required (T42)
GEOMETRY_REFRESH = 5.0        # s, how long a window geometry read is reused (a game window does not move)
MAX_FRAMES = 20000            # stored frames per sitting: ~8 GB at the 0.4 MB a game frame measured (T42)
REQUIRED_FPS = 5.0            # the sustained rate --measure-rate must reach (T42 Done-when 2)
MEASURE_DISPLAY_SIZE = "1024x768x24"
MEASURE_IMAGE_SIZE = "800x600"    # the game window's size (frames-index geometry of the T38 sittings)
MEASURE_IMAGES = 4            # distinct test images the animated window cycles through
MEASURE_DISPLAY_ATTEMPTS = 3  # displays tried when the one picked was taken meanwhile
START_TIMEOUT = 20            # s, for the measurement's Xvfb and test window to appear
STOP_TIMEOUT = 10             # s, for a started process to end after SIGTERM, before SIGKILL
MEASUREMENTS = ROOT / "experiments" / "E020-wine-first-run" / "measurements" / "capture"


class WatcherError(RuntimeError):
    """A capture or a geometry read that the watcher relies on did not do what it must."""


class FrameCapReached(WatcherError):
    """The sitting's stored-frame bound is reached: a new frame is not kept."""


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frame_name(step, epoch_ms):
    """The frame's file name: `<step>-<epochms>.png` (the sitting layout's naming rule)."""
    return f"{int(step)}-{int(epoch_ms)}{FRAME_SUFFIX}"


def wall_time():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def capture_command(window_id, path):
    """The one capture command: the game window by id, written to `path`. Never `-window root`."""
    return ["import", "-window", str(window_id), str(path)]


def _default_run(cmd, env):
    """The capture command through the spike's checked helper, bounded, on the session's display;
    WatcherError unless it exits 0."""
    try:
        spike.must(cmd, require_output=False, timeout=CAPTURE_TIMEOUT, env=env)
    except (spike.CommandFailed, spike.Unreaped, subprocess.TimeoutExpired, OSError) as exc:
        raise WatcherError(f"{' '.join(map(str, cmd[:2]))} failed: {exc}") from None
    return None


def _default_geometry(window_id, env):
    """The window's x, y, width and height, read with xdotool on the session's display; {} when it
    cannot be read.

    The geometry is a structural fact of the frame, kept in the index beside its sha256."""
    try:
        done = spike.must(["xdotool", "getwindowgeometry", "--shell", str(window_id)],
                          timeout=CAPTURE_TIMEOUT, env=env)
    except (spike.CommandFailed, spike.Unreaped, subprocess.TimeoutExpired, OSError):
        return {}
    geometry = {}
    for line in done.stdout.decode(errors="replace").splitlines():
        key, _, value = line.partition("=")
        if key in ("X", "Y", "WIDTH", "HEIGHT") and value.lstrip("-").isdigit():
            geometry[key.lower()] = int(value)
    return geometry


def _stage_root():
    """A fresh private directory on a local, fast place for a capture to land before it is hashed:
    /dev/shm when it is writable (RAM, no 9p round trip), else the temp dir."""
    base = "/dev/shm" if os.path.isdir("/dev/shm") and os.access("/dev/shm", os.W_OK) else None
    return Path(tempfile.mkdtemp(prefix="iwp-stage-", dir=base))


class Watcher:
    """One sitting's frame capture. `step_source()` returns the click-driver's current step.

    `env` is the session's environment (its DISPLAY is the session's own); `run(cmd, env)` raises
    when the capture fails; `geometry(window_id, env)` returns a dict. Both default to the real
    tools and are replaced by fakes in the tests.
    """

    def __init__(self, window_id, env, frames_dir, index_path, log_path, step_source,
                 run=None, geometry=None, clock=time.time, sleep=time.sleep,
                 interval=DEFAULT_INTERVAL, monotonic=time.monotonic, max_frames=MAX_FRAMES,
                 stage_dir=None):
        if not isinstance(window_id, str) or not window_id.strip() or window_id.strip().lower() == "root":
            raise WatcherError("the watcher captures the game window id, never the desktop")
        if not env or not str(env.get("DISPLAY", "")).startswith(":"):
            raise WatcherError("the watcher needs the session's environment, with the session's DISPLAY")
        self.window_id = window_id
        self.env = dict(env)
        self.frames_dir = Path(frames_dir)
        self.index_path = Path(index_path)
        self.log_path = Path(log_path)
        self.step_source = step_source
        self.run = run or _default_run
        self.geometry = geometry or _default_geometry
        self.clock = clock
        self.sleep = sleep
        self.monotonic = monotonic
        self.interval = interval
        self.max_frames = max_frames
        self.stage_dir = Path(stage_dir) if stage_dir else None
        self._own_stage = stage_dir is None
        self.count = 0              # captures indexed (stored or duplicate)
        self.stored = 0             # frames written to frames_dir
        self.failures = 0
        self._last = None           # (name, sha256) of the frame stored last
        self._geometry = None       # (read at, dict) of the last successful read

    def log(self, message):
        """One structural line in watcher.log: no original text ever reaches here (constraint D)."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{wall_time()} {message}\n")

    def close(self):
        """Remove the staging directory this watcher made (one it was given is left alone)."""
        if self._own_stage and self.stage_dir is not None:
            shutil.rmtree(self.stage_dir, ignore_errors=True)
            self.stage_dir = None

    def window_geometry(self):
        """The window's geometry, re-read at most once per GEOMETRY_REFRESH s; a failed read is retried
        on the next frame, never reused."""
        now = self.clock()
        if self._geometry is not None and now - self._geometry[0] < GEOMETRY_REFRESH:
            return dict(self._geometry[1])
        geometry = dict(self.geometry(self.window_id, self.env) or {})
        self._geometry = (now, geometry) if geometry else None
        return geometry

    def capture_once(self):
        """Capture one frame and append its index line. Returns the line (a dict).

        The frame lands in the staging directory and is hashed there. When it equals the frame stored
        last it is dropped and the line names that stored frame (`duplicate`); otherwise it moves into
        frames_dir under `<step>-<epochms>.png`, and its sha256 is checked again at the destination."""
        step = int(self.step_source())
        epoch_ms = int(self.clock() * 1000)
        if self.stage_dir is None:
            self.stage_dir = _stage_root()
        self.stage_dir.mkdir(parents=True, exist_ok=True)
        staged = self.stage_dir / f"stage{FRAME_SUFFIX}"
        staged.unlink(missing_ok=True)
        started = self.monotonic()
        self.run(capture_command(self.window_id, staged), self.env)
        capture_ms = round((self.monotonic() - started) * 1000)
        if not staged.is_file():
            raise WatcherError(f"the capture command exited 0 but wrote no frame at step {step}")
        digest = sha256_file(staged)
        line = {
            "sha256": digest,
            "wall_time": wall_time(),
            "epoch_ms": epoch_ms,
            "capture_ms": capture_ms,
            "window": str(self.window_id),
            "geometry": self.window_geometry(),
        }
        if self._last is not None and self._last[1] == digest:
            staged.unlink(missing_ok=True)
            line["name"] = self._last[0]
            line["duplicate"] = True
        else:
            if self.stored >= self.max_frames:
                staged.unlink(missing_ok=True)
                raise FrameCapReached(f"{self.max_frames} frames are stored; a new one is not kept")
            self.frames_dir.mkdir(parents=True, exist_ok=True)
            while (self.frames_dir / frame_name(step, epoch_ms)).exists():
                epoch_ms += 1                  # two frames in the same millisecond never collide
            name = frame_name(step, epoch_ms)
            path = self.frames_dir / name
            shutil.move(str(staged), str(path))
            if sha256_file(path) != digest:
                path.unlink(missing_ok=True)
                raise WatcherError(f"the frame changed on its way into the sitting at step {step}")
            line["name"] = name
            self._last = (name, digest)
            self.stored += 1
        with self.index_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, sort_keys=True) + "\n")
        self.count += 1
        self.log(f"frame step={step} name={line['name']} sha256={digest}"
                 + (" duplicate" if line.get("duplicate") else ""))
        return line

    def run_loop(self, stop_event):
        """Capture on the fixed schedule until stop_event is set; a failed capture is logged only.

        The next capture is due one interval after the previous one was due; when a capture ran late
        the schedule restarts from now, so a slow patch never turns into a burst afterwards."""
        due = self.monotonic()
        try:
            while not stop_event.is_set():
                try:
                    self.capture_once()
                except FrameCapReached as exc:
                    self.log(f"frame cap reached: {exc}")
                    return
                except Exception as exc:  # noqa: BLE001 - one failed frame never stops the sitting
                    self.failures += 1
                    self.log(f"capture failed step={self.step_source()}: {type(exc).__name__}")
                due += self.interval
                now = self.monotonic()
                if due < now:
                    due = now
                stop_event.wait(due - now)
        finally:
            self.close()

    def start(self):
        """Start the watcher on its own thread; returns (thread, stop_event)."""
        stop_event = threading.Event()
        thread = threading.Thread(target=self.run_loop, args=(stop_event,), daemon=True)
        thread.start()
        return thread, stop_event


# ---- the rate measurement (T42): its own Xvfb, a test window, no game

def rate_summary(lines):
    """The sustained rate of the index lines `lines` (dicts with epoch_ms): captures after the first
    divided by the time from the first to the last, so the first capture does not count for free.
    {} when fewer than two captures. Also the capture times' mean, median, 95th percentile and max."""
    stamps = sorted(int(line["epoch_ms"]) for line in lines)
    if len(stamps) < 2 or stamps[-1] == stamps[0]:
        return {}
    spans = sorted(int(line["capture_ms"]) for line in lines)
    return {
        "fps": round((len(stamps) - 1) / ((stamps[-1] - stamps[0]) / 1000.0), 2),
        "capture_ms": {
            "mean": round(sum(spans) / len(spans), 1),
            "median": spans[len(spans) // 2],
            "p95": spans[min(len(spans) - 1, int(len(spans) * 0.95))],
            "max": spans[-1],
        },
    }


def _stop(proc):
    """End a process this run started: SIGTERM, then SIGKILL after STOP_TIMEOUT s. Never raises."""
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(STOP_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            pass


def _start_own_xvfb(base_env):
    """(process, display, env) of an Xvfb this run starts on a display no other server holds; the env
    is built from `base_env` (never the caller's DISPLAY) plus the new DISPLAY. WatcherError when no
    display of its own could be held. Ready only when this process itself holds the display's socket."""
    sys.path.insert(0, str(ROOT / "runtime" / "iwp"))
    from driver import session as sessionlib   # free_display and the socket checks, reused
    tried = []
    for _ in range(MEASURE_DISPLAY_ATTEMPTS):
        display = sessionlib.free_display(exclude=tried)
        tried.append(display)
        env = dict(base_env, DISPLAY=display)
        proc = spike.spawn(["Xvfb", display, "-screen", "0", MEASURE_DISPLAY_SIZE, "-nolisten", "tcp"],
                           env=base_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        path = f"@/tmp/.X11-unix/X{display[1:]}"
        ours = lambda: (proc.poll() is None  # noqa: E731
                        and bool(sessionlib.listening_socket_inodes(path) & sessionlib.socket_inodes_of(proc.pid))
                        and spike.probe(["xdpyinfo"], timeout=CAPTURE_TIMEOUT, env=env)[0])
        spike.poll(lambda: proc.poll() is not None or ours(), START_TIMEOUT, 0.05)
        if ours():
            return proc, display, env
        _stop(proc)
    raise WatcherError(f"no X display of this run's own after {MEASURE_DISPLAY_ATTEMPTS} attempts ({', '.join(tried)})")


def _start_test_window(env, workdir):
    """(process, window id): an ImageMagick `animate` window of MEASURE_IMAGES distinct 800x600 noise
    images, so that every capture is a new frame (the worst case for storage) on the display of `env`."""
    images = []
    for number in range(MEASURE_IMAGES):
        image = workdir / f"test-{number}.png"
        spike.must(["convert", "-size", MEASURE_IMAGE_SIZE, "plasma:fractal", str(image)], require_output=False,
                   timeout=CAPTURE_TIMEOUT, env=env)
        images.append(str(image))
    proc = spike.spawn(["animate", "-delay", "5", "-geometry", "+0+0", "-title", "t42-test-window", *images],
                       env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    found = []

    def window():
        ok, out, _ = spike.probe(["xdotool", "search", "--onlyvisible", "--name", "t42-test-window"],
                                 timeout=CAPTURE_TIMEOUT, env=env)
        found[:] = out.decode(errors="replace").split() if ok else []
        return bool(found)
    if spike.poll(lambda: proc.poll() is not None or window(), START_TIMEOUT, 0.1) is None or not found:
        _stop(proc)
        raise WatcherError("the test window did not appear on the measurement's display")
    return proc, found[0]


def _tool_version(cmd):
    ok, out, err = spike.probe(cmd, timeout=CAPTURE_TIMEOUT)
    text = (out or err or b"").decode(errors="replace").strip().splitlines()
    return text[0][:120] if ok and text else "unknown"


def measure_rate(seconds, out_dir=None, frames_dir=None):
    """Capture a test window on an Xvfb of this run's own for `seconds`, with the Watcher exactly as a
    sitting uses it, and write the measurement under `out_dir` (default: a new, time-stamped folder
    of measurements/capture/): rate.json, frames-index.jsonl, watcher.log. Returns (document, passed).

    The display is never the caller's: every command here gets an environment built without the
    caller's DISPLAY. The test frames are synthetic pixels; they are kept only in a temporary folder
    (their sha256 are in the committed index) and removed at the end. Nothing is written over.

    `frames_dir` (a folder that does not exist yet) is where the stored test frames go, to measure a
    slower disk than the temporary folder (a sitting writes to /mnt/c); it is removed at the end too."""
    out_dir = Path(out_dir) if out_dir else MEASUREMENTS / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    if frames_dir and Path(frames_dir).exists():
        raise FileExistsError(f"{frames_dir} exists; the test frames go to a new folder")
    out_dir.mkdir(parents=True, exist_ok=False)
    base_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": os.environ.get("HOME", "/tmp")}
    workdir = Path(tempfile.mkdtemp(prefix="t42-measure-"))
    frames_dir = Path(frames_dir) if frames_dir else workdir / "frames"
    xvfb = window_proc = None
    try:
        xvfb, display, env = _start_own_xvfb(base_env)
        if display == os.environ.get("DISPLAY"):
            raise WatcherError("the measurement's display is the caller's; refusing to capture it")
        window_proc, window_id = _start_test_window(env, workdir)
        watcher = Watcher(window_id, env, frames_dir, out_dir / "frames-index.jsonl",
                          out_dir / "watcher.log", step_source=lambda: 0)
        started = time.monotonic()
        thread, stop = watcher.start()
        time.sleep(seconds)
        stop.set()
        thread.join(timeout=CAPTURE_TIMEOUT + 5)
        elapsed = round(time.monotonic() - started, 2)
        index = out_dir / "frames-index.jsonl"
        lines = [json.loads(text) for text in index.read_text().splitlines()] if index.is_file() else []
        summary = rate_summary(lines)
        fps = summary.get("fps", 0.0)
        doc = {
            "task": "T42",
            "method": "ImageMagick `import -window <id>`, deadline-driven schedule, duplicates stored once",
            "display": display,
            "display_owner": "an Xvfb this run started (never the caller's display)",
            "window": window_id,
            "geometry": lines[-1]["geometry"] if lines else {},
            "test_window": f"ImageMagick animate, {MEASURE_IMAGES} distinct {MEASURE_IMAGE_SIZE} plasma images, 50 ms each",
            "interval_s": watcher.interval,
            "frames_dir": "a temporary folder" if frames_dir.parent == workdir else str(frames_dir),
            "seconds_requested": seconds,
            "seconds_elapsed": elapsed,
            "captures": watcher.count,
            "stored": watcher.stored,
            "duplicates": watcher.count - watcher.stored,
            "failures": watcher.failures,
            "fps": fps,
            "required_fps": REQUIRED_FPS,
            "passed": fps >= REQUIRED_FPS and watcher.failures == 0,
            "capture_ms": summary.get("capture_ms", {}),
            "tools": {"import": _tool_version(["import", "-version"]),
                      "cpu_count": os.cpu_count()},
            "index_sha256": sha256_file(index) if index.is_file() else None,
            "log_sha256": sha256_file(out_dir / "watcher.log") if (out_dir / "watcher.log").is_file() else None,
        }
        with open(out_dir / "rate.json", "x", encoding="utf-8") as fh:
            fh.write(json.dumps(doc, indent=2, sort_keys=True) + "\n")
        return doc, doc["passed"]
    finally:
        _stop(window_proc)
        _stop(xvfb)
        shutil.rmtree(workdir, ignore_errors=True)
        shutil.rmtree(frames_dir, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="The E020 watcher's rate measurement (T42).")
    parser.add_argument("--measure-rate", action="store_true",
                        help="start an Xvfb of its own, capture a test window on it, print the sustained "
                             "frames per second; exit 0 only when it is at least %.0f" % REQUIRED_FPS)
    parser.add_argument("--seconds", type=float, default=20.0, help="how long to capture (default 20)")
    parser.add_argument("--frames-dir", help="a new folder for the stored test frames (default: a temporary one)")
    parser.add_argument("--out", help="the measurement folder (default: a new one under measurements/capture/)")
    args = parser.parse_args(argv)
    if not args.measure_rate:
        parser.error("the only thing to run here is --measure-rate; a sitting starts the watcher itself")
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    doc, passed = measure_rate(args.seconds, args.out, args.frames_dir)
    print(f"sustained {doc['fps']} frames per second over {doc['seconds_elapsed']} s "
          f"({doc['captures']} captures, {doc['stored']} stored, {doc['duplicates']} duplicates, "
          f"{doc['failures']} failures); required {doc['required_fps']}: {'PASS' if passed else 'FAIL'}")
    print(f"capture time (ms): {doc['capture_ms']}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
