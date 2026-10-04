#!/usr/bin/env python3
"""E003 cycle: launch DOS Isle Wars under DOSBox-X, reach a known screen, give one input, observe,
terminate, reset, and write one run/1 record (W3b spike; the reusable driver is W5b).

One run is: IW_DOS_DIR bound read-only, the run copy sealed, the configuration written and checked,
Xvfb, snapshot, the run copy and the configuration checked again, launch, window, known screen (the
option box: Set level, Default, Load saved game), before screenshot, one click on Set level, after
screenshot (the Select level dialog), terminate, snapshot, diff, reset, record. Only complete()
marks a run completed; any other way out is recorded as aborted. Every file is written through
setup/iwp/safeio.py. Everything but the outer checks happens inside private user, mount, PID and
network namespaces (``unshare -rmpfn``):

* a private /tmp, where the run's work directory, Xvfb's socket and DOSBox-X's home are;
* a private PID namespace, so that nothing of the run outlives it;
* a private network namespace for the whole run (N0: no interface but a loopback); the run aborts
  unless DOSBox-X is seen in a namespace other than the outer process's, with only `lo`.

DOSBox-X mounts the run copy, <IW_DOS_RUN>/game, as C: and nothing else (dosconf.py).

Machine-local values come from the environment and are never written to a record:
    IW_DOS_DIR    the copy of the game (required); read and hashed only, bound read-only in the run
    IW_DOS_RUN    the run directory (setup/iw-dos/iw-dos-runtime.sh prepares it)
    E003_BUNDLES  the local directory for evidence bundles
    E003_EXPLORE  where --explore writes its output (default: E003_BUNDLES)
    All are confined before anything is mutated or launched (setup/iw-dos/rundir.py).
    E003_MACHINE  the machine id written to records (default: local)

    E005 runs (T14) use --experiment E005 and E005_BUNDLES / E005_EXPLORE in their place.

Usage: cycle.py [--arm NAME] [--cycles fixed-3000|fixed-30000|max] [--clock fixed|host]
                [--probe none|savestate|memory|dosbox-capture] [--terminate term|kill|close]
                [--experiment E003|E005] [--steps FILE]
                [--explore]   (--explore prints the result and writes no record)
With --steps the one click on Set level is replaced by the script's steps (navsteps.py): the seal
around them, the launch checks, the reset and the "completed only when" rule are the same.
"""
import argparse
import hashlib
import io
import json
import os
import re
import signal
import subprocess
import sys
import struct
import time
import zipfile
import zlib
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "setup" / "iwp"))
sys.path.insert(0, str(ROOT / "setup" / "iw-dos"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import locations  # noqa: E402
import safeio  # noqa: E402
import rundir  # noqa: E402
import dosconf  # noqa: E402
import navsteps as stepscript  # noqa: E402

SCRIPT = Path(__file__).resolve()
EXPERIMENT = "E003"                   # --experiment sets it (E005: T14); every record and path follows it
EXPERIMENTS = ("E003", "E005")
SET_ID = rundir.SET_ID
DOSBOX = "dosbox-x"
DISPLAY = ":61"                       # inside the run's own network namespace and /tmp: no clash
ROOT_SCREEN = "800x600x24"
MARK = "IW_DOS_CYCLE_RUN"             # env marker on every child, to find strays from outside
WORK = Path("/tmp/w")                 # the run's work directory, on the private /tmp
FLAGS = ["-nogui", "-nomenu", "-fastlaunch", "-nopromptfolder"]
CLOCK = ("01-01-1994", "12:00:00")    # the emulated clock of --clock fixed (any fixed value would do)
CYCLES = {"fixed-3000": "fixed 3000", "fixed-30000": "fixed 30000", "max": "max"}

# The game's screens are 640x350 (EGA). Rectangles are x, y, w, h inside the game's window, read
# off the exploration captures (measurements/explore-round1 m_never, explore-round2 pred.py).
GAME_SIZE = (640, 350)
SET_LEVEL_TEXT = (28, 22, 66, 18)     # "SET LEVEL": red text on grey
CHOOSE_TEXT = (108, 46, 52, 22)       # "CHOOSE OPTION": light cyan on blue
DIALOG_TITLE = (272, 138, 80, 18)     # "Select level": the dialog's orange title bar
SET_LEVEL_CLICK = (60, 32)
RED, CYAN, ORANGE = (170, 0, 0), (85, 255, 255), (170, 85, 0)
WRITTEN_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,11}")   # a file the game wrote, DOS 8.3 and plain
HEX_LIMIT = 64                        # bytes of a game-written file put in an observation as hex


class Abort(RuntimeError):
    """A deliberate stop: `Cycle.fail()` has set the aborted status, with its reason, before raising it."""


# --- small helpers ---------------------------------------------------------------------------

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(cmd, **kw):
    kw.setdefault("capture_output", True)
    return subprocess.run(cmd, **kw)


def popen(cmd, **kw):
    """Every long-lived child of the cycle (Xvfb, DOSBox-X) starts here."""
    return subprocess.Popen(cmd, **kw)


def run_namespace(cmd, env):
    """The outer process starts the run's namespaces here, and nowhere else."""
    return subprocess.run(cmd, env=env).returncode


def poll(condition, timeout, interval=0.1):
    """Seconds until condition() is truthy, or None at the timeout. Never a fixed wait."""
    start = time.monotonic()
    while True:
        if condition():
            return round(time.monotonic() - start, 2)
        if time.monotonic() - start > timeout:
            return None
        time.sleep(interval)


def install_writable(path):
    """True unless IW_DOS_DIR is on a read-only mount for this process (checked, never written)."""
    return os.access(path, os.W_OK) or not (os.statvfs(path).f_flag & os.ST_RDONLY)


def netns_of(pid):
    return os.readlink(f"/proc/{pid}/ns/net")


def interfaces_of(pid):
    lines = Path(f"/proc/{pid}/net/dev").read_text().splitlines()[2:]
    return sorted(line.split(":")[0].strip() for line in lines if ":" in line)


def marked_processes(value=None):
    """pids whose environment carries the run marker (any run, or this value), read from /proc."""
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            env = (entry / "environ").read_bytes().split(b"\0")
        except OSError:
            continue
        for item in env:
            if item.startswith(MARK.encode() + b"=") and (value is None or item == f"{MARK}={value}".encode()):
                found.append(int(entry.name))
    return found


def is_alive(pid):
    try:
        return Path(f"/proc/{pid}/stat").read_text().split(") ")[-1].split()[0] != "Z"
    except OSError:
        return False


def png_bytes(width, height, rgb):
    """A deterministic 8-bit RGB PNG: filter 0 on every row, zlib level 9, no ancillary chunks.
    (ImageMagick 6.9.12 wrote different bytes for identical pixels, F002.)"""
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    stride = width * 3
    rows = b"".join(b"\0" + rgb[y * stride:(y + 1) * stride] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def snapshot_tree(base):
    """{name: (size, sha256, mtime_ns) | ('link', target) | ('dir',) | ('other',)} of the run copy,
    links not followed. The modification time is kept because DOS programs see file dates."""
    out = {}
    base = Path(base)
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(base).as_posix()
            info = os.lstat(path)
            if path.is_symlink():
                out[rel] = ("link", os.readlink(path))
            elif path.is_dir():
                out[rel] = ("dir",)
            elif path.is_file():
                out[rel] = (info.st_size, sha256_file(path), info.st_mtime_ns)
            else:
                out[rel] = ("other",)
    return out


def diff_tree(before, after):
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])
    return added, removed, changed


def listing_hash(tree):
    text = "\n".join(f"{p} {' '.join(map(str, v))}" for p, v in sorted(tree.items()))
    return sha256_bytes(text.encode())


def savestate_members(path):
    """{member: (bytes, sha256)} of a DOSBox-X savestate (a zip), plus ('Memory', inflated) where
    the Memory member is a zlib stream (exploration round 2): (members, inflated memory or None)."""
    with zipfile.ZipFile(path) as z:
        members = {i.filename: (i.file_size, sha256_bytes(z.read(i))) for i in z.infolist()}
        memory = None
        if "Memory" in members:
            try:
                memory = zlib.decompressobj().decompress(z.read("Memory"))
            except zlib.error:
                memory = None
    return members, memory


# --- screen ----------------------------------------------------------------------------------

class Screen:
    def __init__(self, env):
        self.env = env
        self.ox = self.oy = 0       # where the game window's corner is on the root window

    def raw(self, crop=None):
        x, y, w, h = crop or (0, 0) + GAME_SIZE
        cmd = ["import", "-window", "root", "-crop", f"{w}x{h}+{x + self.ox}+{y + self.oy}", "+repage",
               "-depth", "8", "rgb:-"]
        return run(cmd, env=self.env).stdout

    def count(self, rect, colour):
        data = self.raw(rect)
        return sum(1 for i in range(0, len(data) - 2, 3) if tuple(data[i:i + 3]) == colour)

    def menu_up(self):
        return self.count(SET_LEVEL_TEXT, RED) > 150 and self.count(CHOOSE_TEXT, CYAN) > 250

    def dialog_up(self):
        return self.count(DIALOG_TITLE, ORANGE) > 800

    def stable(self):
        """Two captures 0.4 s apart identical (a poll condition, not a wait for a fixed time)."""
        first = self.raw()
        time.sleep(0.4)
        return first == self.raw()

    def capture(self, directory, name):
        """One capture of the game window into directory/name: (sha256 of the raw 8-bit RGB
        pixels, sha256 of the PNG file, the pixels)."""
        data = self.raw()
        if len(data) != GAME_SIZE[0] * GAME_SIZE[1] * 3:
            raise RuntimeError(f"capture is {len(data)} bytes, not {GAME_SIZE[0]}x{GAME_SIZE[1]} RGB")
        png = png_bytes(*GAME_SIZE, data)
        safeio.write_file(directory, name, data=png, exist="new")
        return sha256_bytes(data), sha256_bytes(png), data


# --- the cycle -------------------------------------------------------------------------------

class Cycle:
    def __init__(self, args, run_id, run_dir, install, workdir=WORK, outer_netns=None):
        self.args, self.run_id = args, run_id
        self.run_dir, self.install, self.workdir = Path(run_dir), Path(install), Path(workdir)
        self.game = locations.real(self.run_dir / rundir.GAME_DIR)
        self.outer_netns = outer_netns
        self.obs, self.outputs, self.log, self.procs = [], [], [], {}
        self.env = dict(os.environ, DISPLAY=DISPLAY, HOME=str(self.workdir / "h"),
                        XDG_CONFIG_HOME=str(self.workdir / "h" / "config"), SDL_AUDIODRIVER="dummy",
                        **{MARK: run_id})
        self.env.pop("PULSE_SERVER", None)
        self.screen = Screen(self.env)
        self.shots = {}
        self.after_screen_ok = False
        self.ref = None             # the screen as the last step left it (navsteps.py: wait-change)
        self.script = []            # the parsed --steps script, [] for the E003 cycle
        self.used_savestate = False
        # "completed" is given only by complete(); any other way out leaves an aborted status.
        self.status = "running"

    # ---- bookkeeping

    def say(self, text):
        self.log.append(f"{time.strftime('%H:%M:%S')} {text}")
        print(text, flush=True)

    def observe(self, step, source, field, value):
        self.obs.append({"step": step, "source": source, "field": field, "value": str(value)})

    def fail(self, reason):
        self.status = f"aborted: {reason}"
        self.say(f"ABORT {reason}")
        raise Abort(reason)

    def abort_later(self, reason):
        if not self.status.startswith("aborted: "):
            self.status = f"aborted: {reason}"
        self.say(f"ABORT {reason}")

    def complete(self):
        """The only place a run becomes completed: every stage done, both screenshots taken, the
        click shown to have opened the Select level dialog, and the probe's own outputs taken."""
        have = {name for name, _, _ in self.outputs}
        wanted = (["before.png"] + stepscript.shot_names(self.script) if self.script else ["before.png", "after.png"])
        wanted += {"savestate": ["restored.png"], "dosbox-capture": ["dosbox-before.png"]}.get(self.args.probe, [])
        missing = [name for name in wanted if name not in have]
        if missing:
            self.fail("the cycle ended without " + " and ".join(missing))
        if not self.after_screen_ok:
            self.fail("the steps did not all finish" if self.script
                      else "the click did not bring up the Select level dialog")
        if self.status == "running":
            self.status = "completed"

    # ---- seals

    def protect_install(self):
        """Bind IW_DOS_DIR read-only in this run's mount namespace, and abort unless it then is."""
        install = str(self.install)
        bind = run(["mount", "--bind", install, install])
        remount = run(["mount", "-o", "remount,bind,ro", install])
        if bind.returncode != 0 or remount.returncode != 0 or install_writable(install):
            self.fail("IW_DOS_DIR could not be made read-only inside the run")
        self.observe(0, "process", "IW_DOS_DIR bound read-only in the run's mount namespace", "yes")
        self.say("IW_DOS_DIR read-only inside the run")

    def command(self):
        return [DOSBOX, "-conf", str(self.workdir / "dosbox.conf")] + FLAGS + (
            ["-break-start"] if self.args.probe == "memory" else [])

    def write_conf(self):
        for name in ("cap", "save", "h"):
            safeio.make_directory(self.workdir, name)
        clock = CLOCK if self.args.clock == "fixed" else None
        text = dosconf.generate(self.game, self.workdir, CYCLES[self.args.cycles], clock)
        safeio.write_file(self.workdir, "dosbox.conf", data=text.encode(), exist="new")
        self.observe(0, "file", "DOSBox-X configuration, sha256 with the run copy's path as <IW_DOS_RUN>/game",
                     sha256_bytes(self.sanitise(text).encode()))

    def check_launch(self, when, step):
        """Abort unless the run copy is safe to launch from and the configuration mounts the run copy
        only: rundir.run_problems (a real directory of plain files of its own, none of them one of
        IW_DOS_DIR's, nothing mounted in it, and `register_artifact.py check --strict` passing), then
        dosconf.problems on the configuration as it is on disk and on the command line."""
        problems = rundir.run_problems(self.run_dir, self.install)
        self.observe(step, "file", f"run copy check {when}: problems found", len(problems))
        if problems:
            self.fail(f"the run copy is not safe to launch from ({when}): " + "; ".join(problems)[:300])
        try:
            with safeio.open_source(self.workdir / "dosbox.conf") as fh:
                text = fh.read().decode("utf-8")
        except (OSError, safeio.Refused, UnicodeDecodeError) as exc:
            self.fail(f"the configuration cannot be read ({when}): {exc}")
        problems = dosconf.problems(text, self.game, self.workdir, self.command())
        self.observe(step, "file", f"configuration check {when}: problems found", len(problems))
        if problems:
            self.fail(f"the configuration may not be launched ({when}): " + "; ".join(problems)[:300])
        self.say(f"run copy and configuration {when}: ok")

    # ---- stages

    def start_x(self):
        Path("/tmp/.X11-unix").mkdir(mode=0o1777, exist_ok=True)
        self.procs["xvfb"] = popen(["Xvfb", DISPLAY, "-screen", "0", ROOT_SCREEN, "-nolisten", "tcp"],
                                              env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        waited = poll(lambda: run(["xdpyinfo"], env=self.env).returncode == 0, 20)
        if waited is None:
            self.fail("Xvfb did not accept connections within 20 s")
        self.observe(0, "process", "xvfb ready (s)", waited)
        self.say(f"Xvfb ready after {waited} s")

    def launch(self):
        self.check_launch("immediately before launch", 1)
        cmd = self.command()
        self.t_launch = time.monotonic()
        with safeio.create_stream(self.workdir, "dosbox.raw.log") as log:
            self.procs["game"] = popen(cmd, cwd=self.workdir, env=self.env, stdout=log, stderr=log)
        self.say("launched: " + " ".join(cmd))
        self.verify_isolation()
        waited = poll(lambda: self.window_geometry() is not None, 30)
        if waited is None:
            self.fail(f"no {GAME_SIZE[0]}x{GAME_SIZE[1]} DOSBox-X window within 30 s")
        wid, pos = self.window_geometry()
        self.window = wid
        self.screen.ox, self.screen.oy = pos
        self.observe(1, "process", f"DOSBox-X window at {GAME_SIZE[0]}x{GAME_SIZE[1]} after launch (s)", waited)
        self.observe(1, "process", "DOSBox-X window position", f"{pos[0]},{pos[1]}")
        self.say(f"window {wid} at {pos} after {waited} s")

    def window_geometry(self):
        """(window id, (x, y)) of DOSBox-X's window once it is the game's size, else None."""
        ids = run(["xdotool", "search", "--class", "dosbox"], env=self.env).stdout.split()
        for wid in ids:
            text = run(["xdotool", "getwindowgeometry", wid], env=self.env).stdout.decode()
            pos = re.search(r"Position: (-?\d+),(-?\d+)", text)
            size = re.search(r"Geometry: (\d+)x(\d+)", text)
            if pos and size and (int(size.group(1)), int(size.group(2))) == GAME_SIZE:
                return wid.decode(), (int(pos.group(1)), int(pos.group(2)))
        return None

    def verify_isolation(self):
        """Abort unless DOSBox-X is in a network namespace other than the outer process's, seeing
        only `lo`. Nothing is recorded as isolated that was not looked at."""
        pid = self.procs["game"].pid
        try:
            theirs = netns_of(pid)
            interfaces = interfaces_of(pid)
        except OSError as exc:
            self.fail(f"DOSBox-X's network namespace could not be read: {type(exc).__name__}")
        if not self.outer_netns or theirs == self.outer_netns:
            self.fail("DOSBox-X shares the outer process's network namespace, or it is unknown")
        if interfaces != ["lo"]:
            self.fail(f"DOSBox-X sees network interfaces besides lo: {interfaces}")
        self.observe(1, "process", "DOSBox-X in a network namespace other than the outer process's", "yes")
        self.observe(1, "process", "network interfaces DOSBox-X sees", ",".join(interfaces))
        self.say(f"DOSBox-X in a separate network namespace, interfaces seen: {interfaces}")

    def known_screen(self):
        waited = poll(self.screen.menu_up, 120, 0.25)
        if waited is None:
            self.shot("known-screen-timeout.png", 2)
            self.fail("the option box never appeared within 120 s")
        if poll(self.screen.stable, 30, 0.1) is None:
            self.fail("the option box never became stable")
        since = round(time.monotonic() - self.t_launch, 2)
        self.observe(2, "screen", "option box reached and stable, seconds after launch", since)
        self.say(f"option box reached {since} s after launch")

    def hotkey(self, key):
        """DOSBox-X's host key (F12) held while `key` goes down and up. The 0.15 s holds are key
        timings, not waits for a state: exploration round 1 found shorter presses not taken."""
        for action in (["keydown", "F12"], ["keydown", key], ["keyup", key], ["keyup", "F12"]):
            run(["xdotool"] + action, env=self.env)
            time.sleep(0.15)

    def shot(self, name, step):
        pixels, png, data = self.screen.capture(self.workdir, name)
        self.outputs.append((name, self.workdir / name, "screenshot"))
        self.observe(step, "screen", f"{name} raw RGB8 pixels sha256", pixels)
        self.say(f"{name}: pixels {pixels[:16]}, file {png[:16]}")
        self.shots[name] = pixels
        return pixels

    def input(self):
        """Move the pointer onto Set level, wait until the game has drawn its pointer there, click,
        and wait for the Select level dialog."""
        before = self.screen.raw()
        run(["xdotool", "mousemove", str(SET_LEVEL_CLICK[0] + self.screen.ox),
             str(SET_LEVEL_CLICK[1] + self.screen.oy)], env=self.env)
        drawn = poll(lambda: self.screen.raw() != before, 5, 0.05)
        self.observe(4, "screen", "pointer drawn at Set level (s)", "no change within 5 s" if drawn is None else drawn)
        run(["xdotool", "click", "1"], env=self.env)
        waited = poll(self.screen.dialog_up, 20, 0.1)
        self.observe(5, "screen", "Select level dialog after click (s)", "absent" if waited is None else waited)
        self.say(f"pointer drawn {drawn}; dialog after click {waited}")
        self.after_screen_ok = waited is not None and poll(self.screen.stable, 30, 0.1) is not None

    # ---- steps (--steps: T14's navigation; every step is one a player could take with the mouse)

    def load_script(self):
        """Parse the --steps script before anything is launched; a line the grammar refuses stops the run
        with nothing started."""
        path = Path(self.args.steps)
        try:
            text = path.read_text(encoding="utf-8")
            self.script = stepscript.parse(text)
        except (OSError, UnicodeDecodeError, stepscript.Refused) as exc:
            self.fail(f"the steps script is refused: {exc}")
        self.observe(0, "file", "steps script sha256", sha256_bytes(text.encode()))

    def navigate(self):
        """Run the script's steps in order, each recorded; the run is not completed unless all finish."""
        for n, (verb, args) in enumerate(self.script, 1):
            self.say(f"step {n}: {verb} {' '.join(map(str, args))}".rstrip())
            getattr(self, "step_" + verb.replace("-", "_"))(100 + n, *args)
        self.after_screen_ok = True

    def step_click(self, step, x, y):
        before = self.screen.raw()
        run(["xdotool", "mousemove", str(x + self.screen.ox), str(y + self.screen.oy)], env=self.env)
        drawn = poll(lambda: self.screen.raw() != before, 5, 0.05)
        self.observe(step, "screen", f"pointer drawn at {x},{y} (s)", "no change within 5 s" if drawn is None else drawn)
        self.ref = self.screen.raw()
        run(["xdotool", "click", "1"], env=self.env)
        self.observe(step, "process", f"click at {x},{y}", "sent")

    def step_wait_stable(self, step):
        waited = poll(self.screen.stable, 30, 0.1)
        self.observe(step, "screen", "screen stable after (s)", "not stable within 30 s" if waited is None else waited)
        self.ref = self.screen.raw()

    def step_wait_change(self, step, seconds):
        waited = poll(lambda: self.screen.raw() != self.ref, seconds, 0.1)
        self.observe(step, "screen", "screen changed after (s)", f"no change within {seconds} s" if waited is None else waited)
        if waited is not None:
            self.step_wait_stable(step)

    def step_until(self, step, rect, colour, count, seconds):
        seen = poll(lambda: self.screen.count(rect, colour) > count, seconds, 0.1)
        self.observe(step, "screen", f"more than {count} pixels of {colour} in {rect} after (s)",
                     "not seen" if seen is None else seen)
        if seen is None:
            self.shot(f"until-failed-{step}.png", step)
            self.fail(f"step {step - 100}: the expected screen did not appear within {seconds} s")

    def step_shot(self, step, name):
        self.shot(name, step)
        self.ref = self.screen.raw()

    def step_files(self, step):
        self.record_written(f"step {step - 100}", step, f"s{step - 100:02d}")

    def step_key(self, step, key):
        run(["xdotool", "key", key], env=self.env)
        self.observe(step, "process", f"key {key}", "sent")

    def step_savestate(self, step):
        """F12+S, then classify what the savestate holds (I2; the file is never kept, it holds the game's memory)."""
        path = self.workdir / "save" / "state.sav"
        if path.is_file():
            safeio.remove(self.workdir / "save", "state.sav")      # an older file must not satisfy the wait
        self.used_savestate = True
        self.save_state(step)
        members, _ = savestate_members(path)
        self.observe(step, "save", "savestate members (name: bytes)", ", ".join(f"{k}: {v[0]}" for k, v in members.items()))

    def record_written(self, label, step, prefix):
        """The run copy against its state before launch, now: each file the game added or changed is
        observed (size, sha256, and its bytes in hex when at most HEX_LIMIT) and kept as the bundle
        output `<prefix>-<NAME>`. A game-written file is evidence for a parsed source; it is never committed."""
        now_ = snapshot_tree(self.game)
        added, removed, changed = diff_tree(self.snap_before, now_)
        self.observe(step, "file", f"run copy at {label}: added/removed/changed", f"{len(added)}/{len(removed)}/{len(changed)}")
        for p in removed:
            self.observe(step, "file", f"run copy at {label}: removed {p}", "removed")
        for p in added + changed:
            entry = now_[p]
            if len(entry) != 3 or not WRITTEN_NAME.fullmatch(p):
                self.observe(step, "file", f"run copy at {label}: {p}", f"not a plain file of the top directory: {entry[0]}")
                continue
            with safeio.open_source(self.game / p) as fh:
                data = fh.read()
            how = "added" if p in added else "changed"
            self.observe(step, "file", f"run copy at {label}: {how} {p}: bytes, sha256", f"{len(data)} {sha256_bytes(data)}")
            if len(data) <= HEX_LIMIT:
                self.observe(step, "file", f"run copy at {label}: {how} {p}: hex", data.hex())
            kept = f"{prefix}-{p}"
            safeio.write_file(self.workdir, kept, data=data, exist="new")
            self.outputs.append((kept, self.workdir / kept, "file"))

    # ---- probes

    def save_state(self, step):
        """F12+S with [dosbox] savefile set: wait until the savestate file exists and its size holds."""
        path = self.workdir / "save" / "state.sav"
        self.hotkey("s")
        sizes = []
        saved = poll(lambda: path.is_file() and (sizes.append(path.stat().st_size) or len(sizes) > 2)
                     and sizes[-1] == sizes[-2] and zipfile.is_zipfile(path), 30, 0.2)
        if saved is None:
            self.fail("DOSBox-X wrote no savestate within 30 s of F12+S")
        self.observe(step, "save", "savestate written after F12+S (s)", saved)
        members, memory = savestate_members(path)
        self.observe(step, "save", "savestate sha256", sha256_file(path))
        self.observe(step, "save", "savestate members", len(members))
        for name in ("Memory", "Vga", "CPU"):
            if name in members:
                self.observe(step, "save", f"savestate member {name}: bytes, sha256", "%d %s" % members[name])
        if memory is not None:
            self.observe(step, "memory", "savestate Memory member inflated (zlib): bytes", len(memory))
            self.observe(step, "memory", "savestate Memory member inflated (zlib): sha256", sha256_bytes(memory))
        return memory

    def probe_at_known_screen(self):
        if self.args.probe in ("savestate", "memory"):
            self.save_state(3)
            pixels = self.shot("postsave.png", 3)
            self.observe(3, "screen", "screen after the save equals before.png", pixels == self.shots["before.png"])
        elif self.args.probe == "dosbox-capture":
            self.hotkey("p")
            found = []
            got = poll(lambda: found.extend(sorted((self.workdir / "cap").glob("*.png"))) or found, 20, 0.2)
            if got is None:
                self.fail("DOSBox-X wrote no screenshot within 20 s of F12+P")
            source = found[0]
            pixels = run(["convert", str(source), "-depth", "8", "rgb:-"]).stdout
            safeio.write_file(self.workdir, "dosbox-before.png", source=source, exist="new")
            self.outputs.append(("dosbox-before.png", self.workdir / "dosbox-before.png", "screenshot"))
            self.observe(3, "screen", "DOSBox-X screenshot after F12+P (s)", got)
            self.observe(3, "screen", "dosbox-before.png file sha256", sha256_file(source))
            self.observe(3, "screen", "dosbox-before.png decoded RGB8 pixels sha256", sha256_bytes(pixels))
            self.observe(3, "screen", "dosbox-before.png pixels equal before.png's",
                         sha256_bytes(pixels) == self.shots["before.png"])

    def probe_after_input(self):
        if self.args.probe != "savestate":
            return
        self.hotkey("l")
        back = poll(self.screen.menu_up, 30, 0.1)
        self.observe(7, "screen", "option box back after F12+L (s)", "absent" if back is None else back)
        if back is None or poll(self.screen.stable, 30, 0.1) is None:
            self.shot("restore-failed.png", 7)
            self.fail("the option box did not come back after F12+L")
        pixels = self.shot("restored.png", 7)
        self.observe(7, "screen", "restored.png equals before.png", pixels == self.shots["before.png"])

    # ---- terminate

    def game_alive(self):
        return self.procs["game"].poll() is None

    def terminate(self):
        how = self.args.terminate
        t0 = time.monotonic()
        if how == "term":
            self.procs["game"].send_signal(signal.SIGTERM)
        elif how == "kill":
            self.procs["game"].kill()
        elif how == "close" and getattr(self, "window", None):
            run(["xdotool", "windowkill", self.window], env=self.env)
        waited = poll(lambda: not self.game_alive(), 15, 0.05)
        self.observe(9, "process", f"DOSBox-X exit after {how} (s)", "still running" if waited is None else waited)
        if waited is None:
            self.say(f"DOSBox-X still running 15 s after {how}: SIGKILL")
            self.abort_later(f"DOSBox-X did not stop within 15 s of {how}")
            self.procs["game"].kill()
            self.procs["game"].wait(10)
        code = self.procs["game"].poll()
        self.observe(9, "process", "DOSBox-X exit status", code)
        self.say(f"DOSBox-X exit status {code}, {round(time.monotonic() - t0, 2)} s after {how}")

    def stop_x(self):
        proc = self.procs.get("xvfb")
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        left = [p for p in marked_processes(self.run_id) if is_alive(p)]
        self.observe(10, "process", "processes of this run still alive after terminate", len(left))
        self.say(f"processes still alive after terminate: {len(left)}")
        if left:
            self.abort_later(f"{len(left)} process(es) survived terminate")

    # ---- snapshots and reset

    def take_snapshot(self, label):
        setattr(self, f"snap_{label}", snapshot_tree(self.game))

    def report_changes(self):
        before, after = self.snap_before, self.snap_after
        added, removed, changed = diff_tree(before, after)
        lines = [f"== run copy: {len(after)} entries after, added {len(added)}, removed {len(removed)}, "
                 f"changed {len(changed)}"]
        lines += [f"added   {p} {after[p][0]} bytes sha256 {after[p][1]}" if len(after[p]) == 3 else f"added   {p} {after[p]}"
                  for p in added]
        lines += [f"removed {p}" for p in removed]
        lines += [f"changed {p} {before[p][:2]} -> {after[p][:2]}" for p in changed]
        self.observe(8, "file", "run copy: added/removed/changed entries", f"{len(added)}/{len(removed)}/{len(changed)}")
        for p in added:
            if len(after[p]) == 3:
                self.observe(8, "file", f"run copy: added {p}: bytes, sha256", f"{after[p][0]} {after[p][1]}")
        safeio.write_file(self.workdir, "changes.log", data=("\n".join(lines) + "\n").encode(), exist="new")
        self.outputs.append(("changes.log", self.workdir / "changes.log", "log"))
        if self.script:
            self.record_written("the end of the run", 8, "end")

    def reset(self):
        """Put the run copy back to the registered set (rundir.sync: what the run added loses its
        name, a changed file is copied again from IW_DOS_DIR), then check it equals its start."""
        env = {"IW_DOS_DIR": str(self.install), "IW_DOS_RUN": str(self.run_dir)}
        try:
            with redirect_stdout(io.StringIO()) as out:
                rundir.sync(env)
            self.say("reset: " + out.getvalue().strip())
        except SystemExit as exc:
            self.abort_later(f"reset could not synchronise the run copy: {exc}")
        restored = snapshot_tree(self.game)
        added, removed, changed = diff_tree(self.snap_before, restored)
        ok = not (added or removed or changed)
        self.observe(11, "file", "run copy after reset equals the run copy before launch",
                     "yes" if ok else f"no: {len(added)} added, {len(removed)} removed, {len(changed)} changed")
        self.say(f"reset: run copy equals its state before launch: {ok}")
        if not ok:
            self.abort_later("reset did not restore the run copy")

    # ---- main

    def execute(self):
        """The stages, then the clean-up. "completed" from complete() only, "aborted: <why>"
        otherwise, and every clean-up stage runs."""
        started = now()
        try:
            if self.args.steps:
                self.load_script()
            self.protect_install()
            self.check_seal_only("before anything starts", 0)
            self.write_conf()
            self.start_x()
            self.take_snapshot("before")
            self.launch()                      # checks the run copy and the configuration again first
            self.known_screen()
            self.shot("before.png", 3)
            self.probe_at_known_screen()
            if self.script:
                self.navigate()
            else:
                self.input()
                self.shot("after.png", 6)
            self.probe_after_input()
            self.complete()
        except Abort:
            pass
        except BaseException as exc:
            self.abort_later(f"{type(exc).__name__}: {exc}")
        self.cleanup("terminate", self.terminate if "game" in self.procs else None)
        self.cleanup("stopping the display", self.stop_x)
        if hasattr(self, "snap_before"):
            self.cleanup("snapshot and reset", self.snapshot_and_reset)
        self.cleanup("keeping the logs", self.keep_logs)
        if self.status == "running":
            self.status = "aborted: the cycle stopped before its end"
        self.started, self.ended = started, now()
        self.observe(12, "process", "cycle seconds, start to end of clean-up",
                     round((datetime.strptime(self.ended, "%Y-%m-%dT%H:%M:%SZ")
                            - datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ")).total_seconds()))

    def check_seal_only(self, when, step):
        problems = rundir.run_problems(self.run_dir, self.install)
        self.observe(step, "file", f"run copy check {when}: problems found", len(problems))
        if problems:
            self.fail(f"the run copy is not safe to launch from ({when}): " + "; ".join(problems)[:300])
        self.say(f"run copy {when}: ok")

    def cleanup(self, stage, action):
        if action is None:
            return
        try:
            action()
        except BaseException as exc:
            self.abort_later(f"{stage} failed: {type(exc).__name__}: {exc}")

    def snapshot_and_reset(self):
        self.take_snapshot("after")
        self.report_changes()
        self.reset()

    def sanitise(self, text):
        """Machine-local paths replaced by their names, for anything that leaves the run."""
        for path, name in ((self.run_dir, "<IW_DOS_RUN>"), (self.install, "<IW_DOS_DIR>")):
            text = text.replace(str(path), name)
        return text

    def keep_logs(self):
        for raw, name in ((self.workdir / "dosbox.raw.log", "dosbox.log"), (self.workdir / "dosbox.conf", "dosbox.conf")):
            if raw.is_file() and not raw.is_symlink():
                with safeio.open_source(raw) as fh:
                    text = fh.read().decode("utf-8", errors="replace")
                safeio.write_file(self.workdir, name if name != "dosbox.conf" else "dosbox.conf.txt",
                                  data=self.sanitise(text).encode(), exist="new")
                kept = name if name != "dosbox.conf" else "dosbox.conf.txt"
                self.outputs.append((kept, self.workdir / kept, "log"))
        safeio.write_file(self.workdir, "run.log", data=("\n".join(self.log) + "\n").encode(), exist="new")
        self.outputs.append(("run.log", self.workdir / "run.log", "log"))


# --- records ---------------------------------------------------------------------------------

def versions():
    def first(cmd, pattern):
        try:
            out = run(cmd)
        except OSError:
            return "unknown"
        text = (out.stdout + out.stderr).decode(errors="replace")
        match = re.search(pattern, text)
        return match.group(1) if match else "unknown"
    return {
        "dosbox-x": first([DOSBOX, "-version"], r"DOSBox-X version (\S+ \S+)"),
        "dosbox-x-package": first(["dpkg-query", "-W", "-f=${Version}", "dosbox-x"], r"(.+)"),
        "xvfb": first(["dpkg-query", "-W", "-f=${Version}", "xvfb"], r"(.+)"),
        "xdotool": first(["xdotool", "--version"], r"(\d+\.\d+\.\d+)"),
        "imagemagick": first(["import", "-version"], r"ImageMagick (\S+)"),
        "python": ".".join(map(str, sys.version_info[:3])),
        "kernel": os.uname().release,
    }


def interventions(args, used_savestate=False):
    if used_savestate:
        return [{"level": "I2", "what": "DOSBox-X savestate saved (F12+S) at a step of the script, its members "
                                        "and memory classified; never restored"}]
    if args.probe == "savestate":
        return [{"level": "I2", "what": "DOSBox-X savestate saved at the option box (F12+S) and restored "
                                        "after the click (F12+L)"}]
    if args.probe == "memory":
        return [{"level": "I1", "what": "DOSBox-X savestate written at the option box (F12+S) and its Memory "
                                        "member read; never restored"}]
    return [{"level": "I0", "what": "none"}]


def next_run_id():
    folder = ROOT / "runs" / EXPERIMENT
    numbers = [int(m.group(1)) for p in folder.glob(f"{EXPERIMENT}-r*.json")
               if (m := re.match(rf"{EXPERIMENT}-r(\d+)\.json$", p.name))]
    return f"{EXPERIMENT}-r{(max(numbers) if numbers else 0) + 1:04d}"


def build_record(cycle, commit, machine):
    state_sha = listing_hash(cycle.snap_before) if hasattr(cycle, "snap_before") else "0" * 64
    return {
        "schema": "run/1",
        "run_id": cycle.run_id,
        "experiment": EXPERIMENT,
        "arm": cycle.args.arm,
        "rep": int(os.environ["IW_DOS_CYCLE_REP"]),
        "code_commit": commit,
        "machine": machine,
        "artifact": {"set": SET_ID, "variant": None},
        "runtime": {
            "driver": f"runtime/iw-dos/spike/cycle.py@{commit}",
            "platform": "linux-wsl2/dosbox-x-xvfb",
            "fingerprint": cycle.fingerprint,
        },
        "interventions": interventions(cycle.args, cycle.used_savestate),
        "start_state": {
            "id": "S-run-copy-option-box",
            "sha256": state_sha,
            "restore": ("fresh private user, mount, PID and network namespaces; IW_DOS_DIR bound read-only; a fresh "
                        "DOSBox-X process from a generated configuration mounting only the run copy; the run copy as "
                        "left by setup/iw-dos/iw-dos-runtime.sh and by the previous run's reset, checked with "
                        "register_artifact.py check --strict before anything starts and again immediately before "
                        "the launch; start_state.sha256 lists every entry of the run copy with its size, sha256 "
                        "and modification time"),
        },
        "seed": None,
        "actions": {"script": "runtime/iw-dos/spike/cycle.py", "sha256": sha256_file(SCRIPT), "args": cycle.argv},
        "observations": cycle.obs,
        "outputs": [{"name": n, "sha256": sha256_file(p), "store": f"release:{EXPERIMENT}"} for n, p, _ in cycle.outputs],
        "started": cycle.started,
        "ended": cycle.ended,
        "status": cycle.status,
    }


def build_manifest(cycle):
    files = []
    for name, path, klass in cycle.outputs:
        digest = sha256_file(path)
        files.append({"name": name, "bytes": path.stat().st_size, "sha256": digest,
                      "asset": f"{digest[:16]}-{name}", "class": klass})
    return {"schema": "evidence-manifest/1", "run_id": cycle.run_id, "experiment": EXPERIMENT,
            "store": f"release:{EXPERIMENT}", "artifact": {"set": SET_ID, "variant": None}, "files": files}


def arm_name(value):
    try:
        return safeio.identifier(value, "arm")
    except safeio.Refused as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--arm", type=arm_name, default="control")
    ap.add_argument("--rep", type=int, default=None, help="default: one more than the records of this arm")
    ap.add_argument("--cycles", choices=sorted(CYCLES), default="fixed-3000")
    ap.add_argument("--clock", choices=["fixed", "host"], default="fixed")
    ap.add_argument("--probe", choices=["none", "savestate", "memory", "dosbox-capture"], default="none")
    ap.add_argument("--terminate", choices=["term", "kill", "close"], default="term")
    ap.add_argument("--experiment", choices=EXPERIMENTS, default="E003",
                    help="the experiment whose records, manifests and bundles the run writes (default E003)")
    ap.add_argument("--steps", default=None, help="a step script (navsteps.py) in place of the one click on Set level")
    ap.add_argument("--explore", action="store_true", help="print the result; write no record or bundle")
    return ap


def store_outputs(cycle, directory, name_of, exist):
    """Copy each output into a confined directory through the one writer; an output that cannot be
    stored is dropped and aborts the run, so the record never names an output the store lacks."""
    stored = []
    for name, path, klass in cycle.outputs:
        digest = sha256_file(path)
        try:
            safeio.write_file(directory, name_of(name, digest), source=path, exist=exist,
                              expect_sha256=digest, create_below=directory.parent)
        except (safeio.Refused, OSError) as exc:
            cycle.abort_later(f"{name} was not stored: {exc}")
            continue
        stored.append((name, path, klass))
    return stored


def inner(args):
    """Runs as PID 1 of the private namespaces: does the cycle and writes the record."""
    global EXPERIMENT
    EXPERIMENT = args.experiment
    locs = rundir.run_locations(need_bundles=True, explore=args.explore, experiment=EXPERIMENT)
    run_dir, bundles, install = locs["IW_DOS_RUN"], locs[f"{EXPERIMENT}_BUNDLES"], locs["IW_DOS_DIR"]
    run_id = os.environ["IW_DOS_CYCLE_ID"]
    machine = os.environ.get("E003_MACHINE", "local")
    if not re.fullmatch(rf"{EXPERIMENT}-x[0-9]+" if args.explore else rf"{EXPERIMENT}-r[0-9]{{4,}}", run_id):
        sys.exit(f"{run_id!r} is not a run id of {EXPERIMENT}; nothing was started")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", machine):
        sys.exit("E003_MACHINE is not a machine id (lowercase letters, digits, dashes); nothing was started")
    try:
        safeio.identifier(args.arm, "arm")
    except safeio.Refused as exc:
        sys.exit(f"{exc}; nothing was started")
    run(["mount", "-t", "tmpfs", "-o", "mode=1777", "tmpfs", "/tmp"], check=True)
    os.close(safeio.open_directory(WORK, create_below=Path("/tmp")))
    cycle = Cycle(args, run_id, run_dir, install, WORK, os.environ.get("IW_DOS_OUTER_NETNS"))
    cycle.argv = sys.argv[1:]
    cycle.fingerprint = versions()
    cycle.execute()
    commit = os.environ["IW_DOS_CYCLE_COMMIT"]
    if args.explore:
        out = locs.get(f"{EXPERIMENT}_EXPLORE", bundles)
        cycle.outputs = store_outputs(cycle, out, lambda name, _: f"{args.arm}.{name}", "replace")
        try:
            safeio.write_file(out, f"{args.arm}.observations.json", data=json.dumps(cycle.obs, indent=1).encode(),
                              exist="replace", create_below=out.parent)
        except (safeio.Refused, OSError) as exc:
            cycle.abort_later(f"the observations were not stored: {exc}")
        print(json.dumps({"run_id": run_id, "status": cycle.status}))
        return 0 if cycle.status == "completed" else 1
    repo = locations.real(ROOT)
    names = {"runs": f"{run_id}.json", "evidence": f"{run_id}.manifest.json"}
    taken = [f"{folder}/{EXPERIMENT}/{name}" for folder, name in names.items()
             if os.path.lexists(repo / folder / EXPERIMENT / name)]
    if taken:
        print(f"no record written: {', '.join(taken)} already exist(s); records are never overwritten", file=sys.stderr)
        return 1
    try:
        for folder in names:
            os.close(safeio.open_directory(repo / folder / EXPERIMENT, create_below=repo))
    except (safeio.Refused, OSError) as exc:
        print(f"no record written: {exc}", file=sys.stderr)
        return 1
    cycle.outputs = store_outputs(cycle, bundles, lambda name, digest: f"{digest[:16]}-{name}", "same")
    manifest = build_manifest(cycle)
    record = build_record(cycle, commit, machine)
    try:
        safeio.write_file(repo / "evidence" / EXPERIMENT, names["evidence"],
                          data=(json.dumps(manifest, indent=2) + "\n").encode(), exist="new", create_below=repo)
        safeio.write_file(repo / "runs" / EXPERIMENT, names["runs"],
                          data=(json.dumps(record, indent=2) + "\n").encode(), exist="new", create_below=repo)
    except (safeio.Refused, OSError) as exc:
        print(f"no record written: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"run_id": run_id, "status": cycle.status}))
    return 0 if cycle.status == "completed" else 1


def outer(args):
    global EXPERIMENT
    EXPERIMENT = args.experiment
    locs = rundir.run_locations(need_bundles=True, explore=args.explore, experiment=EXPERIMENT)
    strays = marked_processes()
    if strays:
        sys.exit(f"stale processes of an earlier run are alive: {sorted(set(strays))}; stop them first "
                 "(nothing was started)")
    problems = rundir.run_problems(locs["IW_DOS_RUN"], locs["IW_DOS_DIR"])
    if problems:
        sys.exit("the run copy is not safe to launch from; nothing was started: " + "; ".join(problems)[:400])
    commit_out = run(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT)
    dirty = run(["git", "status", "--porcelain", "--", "runtime", "setup", "tools", "formats"], cwd=ROOT).stdout
    if dirty and not args.explore:
        sys.exit("runtime/, setup/, tools/ or formats/ has uncommitted changes; commit before a recorded run")
    run_id = next_run_id() if not args.explore else f"{EXPERIMENT}-x{os.getpid()}"
    rep = args.rep or 1 + sum(
        1 for p in (ROOT / "runs" / EXPERIMENT).glob("*.json") if json.loads(p.read_text()).get("arm") == args.arm)
    env = dict(os.environ, IW_DOS_CYCLE_ID=run_id, IW_DOS_CYCLE_REP=str(rep),
               IW_DOS_CYCLE_COMMIT=commit_out.stdout.decode().strip(), IW_DOS_CYCLE_INNER="1",
               IW_DOS_OUTER_NETNS=netns_of("self"))
    cmd = ["unshare", "-r", "-m", "-p", "-n", "-f", "--kill-child", "--mount-proc",
           sys.executable, str(SCRIPT)] + sys.argv[1:]
    code = run_namespace(cmd, env)
    left = marked_processes(run_id)
    if left:
        for pid in left:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        print(f"processes of the run survived its namespace: {left}", file=sys.stderr)
        return 1
    return code


def main():
    args = parser().parse_args()
    if os.environ.get("IW_DOS_CYCLE_INNER") == "1":
        return inner(args)
    return outer(args)


if __name__ == "__main__":
    sys.exit(main())
