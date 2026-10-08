"""The per-frame watcher of a model-driven sitting (T38, rule 18 carve-out).

It attaches to the game window id the session already holds, captures *that* window on a fixed
interval (ImageMagick `import -window <id>`, never `-window root`: the desktop is never captured),
names each frame `<step>-<epochms>.png`, sha256s it, and appends one line per frame to
`frames-index.jsonl` (name, sha256, wall time, window geometry). `watcher.log` carries the same
structural names only: constraint D of the carve-out keeps the original's text (event names, card
names, screen labels, the title) out of the watcher's lines.

The command runner, clock and geometry reader are injected so this module is testable against
fakes, with no wine and no display. A failed capture is logged and skipped, never written as a
frame: a frame in the index is a file that exists and whose sha256 is the one recorded.
"""
import hashlib
import json
import subprocess
import sys
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
DEFAULT_INTERVAL = 1.0        # s, the fixed interval between frames


class WatcherError(RuntimeError):
    """A capture or a geometry read that the watcher relies on did not do what it must."""


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


def _default_run(cmd):
    """The capture command through the spike's checked helper, bounded; WatcherError unless it exits 0."""
    try:
        spike.must(cmd, require_output=False, timeout=CAPTURE_TIMEOUT)
    except (spike.CommandFailed, spike.Unreaped, subprocess.TimeoutExpired, OSError) as exc:
        raise WatcherError(f"{' '.join(map(str, cmd[:2]))} failed: {exc}") from None
    return None


def _default_geometry(window_id):
    """The window's x, y, width and height, read with xdotool; {} when it cannot be read.

    The geometry is a structural fact of the frame, kept in the index beside its sha256."""
    try:
        done = spike.must(["xdotool", "getwindowgeometry", "--shell", str(window_id)],
                          timeout=CAPTURE_TIMEOUT)
    except (spike.CommandFailed, spike.Unreaped, subprocess.TimeoutExpired, OSError):
        return {}
    geometry = {}
    for line in done.stdout.decode(errors="replace").splitlines():
        key, _, value = line.partition("=")
        if key in ("X", "Y", "WIDTH", "HEIGHT") and value.lstrip("-").isdigit():
            geometry[key.lower()] = int(value)
    return geometry


class Watcher:
    """One sitting's frame capture. `step_source()` returns the click-driver's current step.

    `run(cmd)` raises when the capture fails; `geometry(window_id)` returns a dict. Both default
    to the real tools and are replaced by fakes in the tests.
    """

    def __init__(self, window_id, frames_dir, index_path, log_path, step_source,
                 run=None, geometry=None, clock=time.time, sleep=time.sleep,
                 interval=DEFAULT_INTERVAL):
        if not isinstance(window_id, str) or not window_id.strip() or window_id.strip() == "root":
            raise WatcherError("the watcher captures the game window id, never the desktop")
        self.window_id = window_id
        self.frames_dir = Path(frames_dir)
        self.index_path = Path(index_path)
        self.log_path = Path(log_path)
        self.step_source = step_source
        self.run = run or _default_run
        self.geometry = geometry or _default_geometry
        self.clock = clock
        self.sleep = sleep
        self.interval = interval
        self.count = 0

    def log(self, message):
        """One structural line in watcher.log: no original text ever reaches here (constraint D)."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{wall_time()} {message}\n")

    def capture_once(self):
        """Capture one frame, hash it, and append its index line. Returns the line (a dict)."""
        step = int(self.step_source())
        epoch_ms = int(self.clock() * 1000)
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        while (self.frames_dir / frame_name(step, epoch_ms)).exists():
            epoch_ms += 1                      # two frames in the same millisecond never collide
        name = frame_name(step, epoch_ms)
        path = self.frames_dir / name
        self.run(["import", "-window", str(self.window_id), str(path)])
        if not path.is_file():
            raise WatcherError(f"the capture command exited 0 but wrote no frame at step {step}")
        digest = sha256_file(path)
        line = {
            "name": name,
            "sha256": digest,
            "wall_time": wall_time(),
            "window": str(self.window_id),
            "geometry": dict(self.geometry(self.window_id) or {}),
        }
        with self.index_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, sort_keys=True) + "\n")
        self.count += 1
        self.log(f"frame step={step} name={name} sha256={digest}")
        return line

    def run_loop(self, stop_event):
        """Capture on the fixed interval until stop_event is set; a failed capture is logged only."""
        while not stop_event.is_set():
            try:
                self.capture_once()
            except Exception as exc:  # noqa: BLE001 - one failed frame never stops the sitting
                self.log(f"capture failed step={self.step_source()}: {type(exc).__name__}")
            stop_event.wait(self.interval)

    def start(self):
        """Start the watcher on its own thread; returns (thread, stop_event)."""
        stop_event = threading.Event()
        thread = threading.Thread(target=self.run_loop, args=(stop_event,), daemon=True)
        thread.start()
        return thread, stop_event
