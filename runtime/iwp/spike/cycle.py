#!/usr/bin/env python3
"""E001 cycle: launch Isle Wars Pro under Wine, reach a known screen, give one input, observe,
terminate, reset, and write one run/1 record (W3a spike; the reusable driver is W5a).

One run is: the install bound read-only, the prefix sealed, Xvfb, xfwm4, snapshot, the prefix sealed
again, launch, window, known screen, before screenshot, one input, after screenshot, terminate,
snapshot, diff, reset, record. Only complete() marks a run completed; any other way out is recorded
as aborted. Every file is written through setup/iwp/safeio.py. Everything but the record and the
bundles happens inside a private user, mount and PID namespace (``unshare -rmpf``):

* a private /tmp, because the WSLg /tmp/.X11-unix is read-only and Xvfb could then only listen on
  the abstract socket, which a game inside its own network namespace cannot reach;
* a private PID namespace, so that nothing of the run (Xvfb, xfwm4, wineserver) outlives it;
* the game itself always runs under ``unshare -n`` (network N0: no interface but a down loopback);
  there is no option to run it otherwise, and the run aborts when the game's separate network
  namespace cannot be verified.

Machine-local values come from the environment and are never written to a record:
    IWP_PREFIX    the Wine prefix (outside every checkout); the game copy is <prefix>/drive_c/iwp
    E001_BUNDLES  the local directory for evidence bundles
    E001_EXPLORE  where --explore writes its output (default: E001_BUNDLES)
    All three are confined before anything is mutated or launched (setup/iwp/locations.py): outside
    every checkout, not overlapping the install or each other.
    IWP_DIR       the install (required); read and hashed only, to restore the game copy when it has
                  changed. Inside the run's mount namespace it is bound read-only before anything starts.
    E001_MACHINE  the machine id written to records (default: local)

Usage: cycle.py [--arm NAME] [--size WxHxD] [--wm xfwm4|none] [--audio off|default]
                [--click hover|immediate] [--terminate ui-quit|wm-close|kill]
                [--explore]   (--explore prints the result and writes no record)
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import signal
import stat
import subprocess
import sys
import struct
import tempfile
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "setup" / "iwp"))
import locations  # noqa: E402
import prefix as prefixlib  # noqa: E402
import safeio  # noqa: E402
SCRIPT = Path(__file__).resolve()
EXPERIMENT = "E001"
SET_ID = "iwp-2.0-996e86c5"
SUCCESSOR_ID = "iwp-2.0-3694a782"   # the same files with xtras/Isledft.dat declared a runtime write
WINE = "/usr/lib/wine/wine"          # not on PATH on this machine (T08 task file)
WINESERVER = "/usr/lib/wine/wineserver"
DISPLAY = ":77"
MARK = "IWP_CYCLE_RUN"               # env marker on every child, to find strays from outside

# The title screen's geometry at 800x600, read off the screenshots of the exploration runs
# (F002). Rectangles are x, y, w, h.
STAGE = (800, 600)                   # the game's stage; the window follows the screen when larger
SUBTITLE = (180, 335, 440, 25)       # "Unregistered Shareware Version", cyan text
OPTIONS_LABEL = (280, 572, 80, 26)   # "Options": turns light green under the pointer
OPTIONS_CLICK = (320, 585)
RETURN_BUTTON = (470, 515, 185, 40)  # green, on the Options screen
RETURN_CLICK = (565, 532)
QUIT_CLICK = (712, 585)
ORDER_BANNER = (14, 208, 772, 40)    # yellow banner of the unregistered-version notice shown by Quit
EXIT_GAME = (640, 574, 100, 26)      # "Exit Game" on that notice
EXIT_CLICK = (688, 586)
SAVE_DEFAULT = (135, 515, 187, 35)   # "Save as default" on the Options screen
SAVE_CLICK = (228, 532)
REG_FILES = ("system.reg", "user.reg", "userdef.reg", ".update-timestamp")


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


def poll(condition, timeout, interval=0.1):
    """Seconds until condition() is truthy, or None at the timeout. Never a fixed wait."""
    start = time.monotonic()
    while True:
        if condition():
            return round(time.monotonic() - start, 2)
        if time.monotonic() - start > timeout:
            return None
        time.sleep(interval)


def confined_locations(args):
    """The canonical, confined machine-local locations; SystemExit before anything is touched.

    IWP_DIR is required: the run binds it read-only, and the seal checks that no file of the prefix
    shares an inode with it."""
    found = locations.locations(need_prefix=True, need_bundles=True, explore=args.explore)
    if "IWP_DIR" not in found:
        raise SystemExit("IWP_DIR is not set; the run seals the install read-only and must know where it is")
    return found


def install_writable(path):
    """True unless the install is on a read-only mount for this process (checked, never written)."""
    return os.access(path, os.W_OK) or not (os.statvfs(path).f_flag & os.ST_RDONLY)


def netns_of(pid):
    """The network namespace identifier of a process (`net:[inode]`), read from /proc."""
    return os.readlink(f"/proc/{pid}/ns/net")


def interfaces_of(pid):
    """The network interfaces a process can see, read from /proc/<pid>/net/dev."""
    lines = Path(f"/proc/{pid}/net/dev").read_text().splitlines()[2:]
    return sorted(line.split(":")[0].strip() for line in lines if ":" in line)


def game_command():
    """The only way the game is started: in a network namespace of its own (N0)."""
    return ["unshare", "-n", WINE, "Islepro.exe"]


def start_state_sha(prefix_tree):
    """sha256 identifying the whole prefix as it is before the launch.

    It lists every entry of the prefix (the game copy is inside it): path, type, size and sha256 of
    each file, target of each link. That covers the registry files byte for byte, so two starting
    states with the same key names and different values get different hashes.
    """
    return listing_hash(prefix_tree)


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


def prefix_processes(prefix):
    """pids whose WINEPREFIX is this prefix (a wineserver left by setup, for instance)."""
    needle = f"WINEPREFIX={prefix}".encode()
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            env = (entry / "environ").read_bytes().split(b"\0")
        except OSError:
            continue
        if needle in env:
            found.append(int(entry.name))
    return found


# --- screen ----------------------------------------------------------------------------------

def png_bytes(width, height, rgb):
    """A deterministic 8-bit RGB PNG: filter 0 on every row, zlib level 9, no ancillary chunks."""
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    stride = width * 3
    rows = b"".join(b"\0" + rgb[y * stride:(y + 1) * stride] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


class Screen:
    def __init__(self, width, height, env):
        self.width, self.height, self.env = width, height, env
        self.ox = self.oy = 0       # where the game window's corner is on the root window

    def raw(self, crop=None):
        cmd = ["import", "-window", "root"]
        if crop:
            x, y, w, h = crop
            cmd += ["-crop", f"{w}x{h}+{x + self.ox}+{y + self.oy}", "+repage"]
        cmd += ["-depth", "8", "rgb:-"]
        return run(cmd, env=self.env).stdout

    def count(self, crop, predicate):
        data = self.raw(crop)
        return sum(1 for i in range(0, len(data) - 2, 3) if predicate(data[i], data[i + 1], data[i + 2]))

    def title_up(self):
        return self.count(SUBTITLE, lambda r, g, b: r < 80 and g > 150 and b > 200) > 300

    def notice_up(self):
        return self.count(ORDER_BANNER, lambda r, g, b: r > 200 and g > 200 and b < 100) > 5000

    def options_up(self):
        return self.count(RETURN_BUTTON, lambda r, g, b: g > 150 and r < 80 and b < 100) > 1000

    def stable(self):
        """Two captures 0.4 s apart identical (a poll condition, not a wait for a fixed time)."""
        first = self.raw()
        time.sleep(0.4)
        return first == self.raw()

    def capture(self, directory, name):
        """One capture into directory/name: (sha256 of the raw 8-bit RGB pixels, sha256 of the PNG file).

        The PNG is written here, not by ImageMagick, because ImageMagick 6.9.12 wrote different
        bytes for identical pixels (observed: two conversions of one capture differed), and the
        screenshots are compared by file hash.
        """
        data = self.raw()
        if len(data) != self.width * self.height * 3:
            raise RuntimeError(f"capture is {len(data)} bytes, not {self.width}x{self.height} RGB")
        png = png_bytes(self.width, self.height, data)
        safeio.write_file(directory, name, data=png, exist="new")
        return sha256_bytes(data), sha256_bytes(png)


# --- snapshots and diffs ---------------------------------------------------------------------

def snapshot_tree(base):
    """{relative path: ('f', bytes, sha256) | ('l', target) | ('d',)} for everything under base."""
    base = Path(base)
    out = {}
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(base).as_posix()
            if path.is_symlink():
                out[rel] = ("l", os.readlink(path))
            elif path.is_dir():
                out[rel] = ("d",)
            else:
                out[rel] = ("f", path.stat().st_size, sha256_file(path))
    return out


def diff_tree(before, after):
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])
    return added, removed, changed


def registry_keys(prefix):
    """{'hive: key name': sha256 of its value lines} from the prefix's three .reg files.

    Key timestamps and the file-level #time lines are dropped: Wine rewrites them on every exit.
    """
    out = {}
    for hive in ("system.reg", "user.reg", "userdef.reg"):
        path = Path(prefix) / hive
        if not path.is_file():
            continue
        key, lines = None, []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines() + ["["]:
            if line.startswith("["):
                if key is not None:
                    out[f"{hive}: {key}"] = sha256_bytes("\n".join(lines).encode())
                match = re.match(r"^\[(.*)\](?: \d+)?$", line)
                key, lines = (match.group(1) if match else None), []
            elif key is not None and not line.startswith("#time="):
                lines.append(line)
    return out


def listing_hash(tree):
    text = "\n".join(f"{p} {' '.join(map(str, v))}" for p, v in sorted(tree.items()))
    return sha256_bytes(text.encode())


# --- the cycle -------------------------------------------------------------------------------

class Cycle:
    def __init__(self, args, run_id, prefix, bundles, install=None):
        self.args, self.run_id, self.prefix, self.bundles = args, run_id, prefix, bundles
        self.install = install
        self.game = prefix / "drive_c" / "iwp"
        self.obs = []                # run/1 observations
        self.outputs = []            # (name, path, class) of bundle files
        self.log = []                # lines of the run log (a bundle file)
        self.procs = {}
        self.workdir = locations.real(tempfile.mkdtemp(prefix="iwp-cycle-"))
        width, height, depth = (int(v) for v in args.size.split("x"))
        self.size = (width, height, depth)
        self.env = dict(os.environ, DISPLAY=DISPLAY, WINEPREFIX=str(prefix), WINEARCH="win32",
                        WINEDEBUG="fixme-all", **{MARK: run_id})
        self.env["WINEDLLOVERRIDES"] = "winemenubuilder.exe=d"
        if args.audio == "off":
            # audio drivers disabled: no sound reaches the host. F002 compares E001-r0005 (drivers
            # left alone: Wine registered the host's audio endpoints) with the control (it did not).
            self.env["WINEDLLOVERRIDES"] += ";winepulse.drv=d;winealsa.drv=d;wineoss.drv=d"
            self.env.pop("PULSE_SERVER", None)
        self.screen = Screen(width, height, self.env)
        self.after_screen_ok = False
        # "completed" is given only by complete(), at the end of a cycle that did every stage. Any
        # other way out (fail(), an exception, an interruption) leaves an aborted status.
        self.status = "running"

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
        """An aborted status for a fault found after the stages (terminate, reset, storing the
        evidence). The first reason is the one recorded; every one is logged."""
        if not self.status.startswith("aborted: "):
            self.status = f"aborted: {reason}"
        self.say(f"ABORT {reason}")

    def complete(self):
        """The only place a run becomes completed: every stage done, both screenshots taken, and the
        click shown to have brought up the Options screen."""
        have = {name for name, _, _ in self.outputs}
        missing = [name for name in ("before.png", "after.png") if name not in have]
        if missing:
            self.fail("the cycle ended without " + " and ".join(missing))
        if not self.after_screen_ok or not self.screen.options_up():
            self.fail("the click did not bring up the Options screen")
        if self.status == "running":
            self.status = "completed"

    # ---- seals

    def protect_install(self):
        """Bind the install read-only in this run's mount namespace, and abort unless it then is
        read-only here: nothing in the run, the game included, can write to it."""
        install = str(self.install)
        bind = run(["mount", "--bind", install, install])
        remount = run(["mount", "-o", "remount,bind,ro", install])
        if bind.returncode != 0 or remount.returncode != 0 or install_writable(install):
            self.fail("the install could not be made read-only inside the run")
        self.observe(0, "process", "install bound read-only in the run's mount namespace", "yes")
        self.say("install read-only inside the run")

    def seal(self, when, step):
        """Abort unless the prefix is safe to launch from (setup/iwp/prefix.py prefix_problems): C:
        maps to drive_c and nothing else is mapped, no link leaves the prefix, no file has a second
        name, nothing is mounted in it, and the game copy is the registered set as plain files of its
        own. Run before anything starts, and again immediately before the game starts."""
        problems = prefixlib.prefix_problems(self.prefix, self.install)
        self.observe(step, "file", f"prefix seal {when}: problems found", len(problems))
        if problems:
            self.fail(f"the prefix is not safe to launch from ({when}): " + "; ".join(problems)[:300])
        self.say(f"prefix seal {when}: ok")

    # ---- stages

    def start_x(self):
        width, height, depth = self.size
        Path("/tmp/.X11-unix").mkdir(mode=0o1777, exist_ok=True)
        self.procs["xvfb"] = subprocess.Popen(
            ["Xvfb", DISPLAY, "-screen", "0", f"{width}x{height}x{depth}", "-nolisten", "tcp"],
            env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        waited = poll(lambda: run(["xdpyinfo"], env=self.env).returncode == 0, 20)
        if waited is None:
            self.fail("Xvfb did not accept connections within 20 s")
        info = run(["xdpyinfo"], env=self.env).stdout.decode()
        dims = re.search(r"dimensions:\s+(\d+x\d+)", info).group(1)
        planes = re.search(r"depth of root window:\s+(\d+)", info).group(1)
        self.observe(0, "process", "xvfb ready (s)", waited)
        self.observe(0, "process", "root window", f"{dims}x{planes}")
        self.say(f"Xvfb ready after {waited} s, root {dims}x{planes}")

    def start_wm(self):
        if self.args.wm == "none":
            self.observe(0, "process", "window manager", "none")
            return
        self.procs["wm"] = subprocess.Popen(["xfwm4", "--compositor=off"], env=self.env,
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        waited = poll(lambda: run(["xprop", "-root", "_NET_SUPPORTING_WM_CHECK"], env=self.env
                                  ).stdout.decode().find("window id") >= 0, 20)
        if waited is None:
            self.fail("xfwm4 did not register as the window manager within 20 s")
        self.observe(0, "process", "xfwm4 registered (s)", waited)
        self.say(f"xfwm4 registered after {waited} s")

    def launch(self):
        self.seal("immediately before launch", 1)
        cmd = game_command()
        self.t_launch = time.monotonic()
        with safeio.create_stream(self.workdir, "wine.log") as log:
            self.procs["game"] = subprocess.Popen(cmd, cwd=self.game, env=self.env, stdout=log, stderr=log)
        self.say("launched: " + " ".join(cmd[:-1] + ["<game>"]))
        self.verify_isolation()
        waited = poll(lambda: run(["xdotool", "search", "--name", "^Islepro$"], env=self.env).stdout.strip(), 90)
        if waited is None:
            self.fail("no Islepro window within 90 s")
        wid = run(["xdotool", "search", "--name", "^Islepro$"], env=self.env).stdout.split()[0].decode()
        geometry = run(["xdotool", "getwindowgeometry", wid], env=self.env).stdout.decode().replace("\n", " ")
        pos = re.search(r"Position: (\S+)", geometry).group(1)
        size = re.search(r"Geometry: (\S+)", geometry).group(1)
        self.window = wid
        wx, wy = (int(v) for v in pos.split(","))
        ww, wh = (int(v) for v in size.split("x"))
        # On a screen larger than 800x600 the window fills the screen and the 800x600 stage sits
        # centered in black (E001-r0011, 1024x768: stage at 112,84, which is what lets its title
        # screen predicate and clicks succeed). Content coordinates are shifted so.
        self.screen.ox, self.screen.oy = wx + max(0, (ww - STAGE[0]) // 2), wy + max(0, (wh - STAGE[1]) // 2)
        self.observe(1, "process", "stage origin assumed from a centered 800x600 stage", f"{self.screen.ox},{self.screen.oy}")
        self.observe(1, "process", "Islepro window after launch (s)", waited)
        self.observe(1, "process", "Islepro window position and size", f"{pos} {size}")
        self.say(f"window after {waited} s at {pos}, size {size}")

    def verify_isolation(self):
        """Abort unless the game process is found in a network namespace of its own with only `lo`.

        Nothing is recorded as isolated that was not looked at: no process found, the same
        namespace as this process, or an interface besides `lo` all abort the run.
        """
        found = []
        poll(lambda: found.append(self.find_game_pid()) or found[-1] is not None, 20, 0.1)
        pid = found[-1] if found else None
        if pid is None:
            self.fail("the game process was not found, so its network isolation could not be verified")
        try:
            theirs, mine = netns_of(pid), netns_of("self")
            interfaces = interfaces_of(pid)
        except OSError as exc:
            self.fail(f"the game's network namespace could not be read: {type(exc).__name__}")
        if theirs == mine:
            self.fail("the game shares this process's network namespace")
        if interfaces != ["lo"]:
            self.fail(f"the game sees network interfaces besides lo: {interfaces}")
        self.observe(1, "process", "game in its own network namespace", "yes")
        self.observe(1, "process", "network interfaces the game sees", ",".join(interfaces))
        self.say(f"game in a separate network namespace, interfaces seen: {interfaces}")

    def find_game_pid(self):
        for pid in marked_processes(self.run_id):
            try:
                if Path(f"/proc/{pid}/comm").read_text().strip().lower().startswith("islepro"):
                    return pid
            except OSError:
                pass
        return None

    def known_screen(self):
        waited = poll(self.screen.title_up, 45, 0.25)
        if waited is None:
            self.shot("known-screen-timeout.png", 2)
            self.fail("the title screen's subtitle never appeared within 45 s")
        stable = poll(self.screen.stable, 30, 0.1)
        if stable is None:
            self.fail("the screen never became stable")
        props = run(["xprop", "-id", self.window, "_NET_WM_STATE", "_MOTIF_WM_HINTS", "WM_TRANSIENT_FOR"],
                    env=self.env).stdout.decode().replace("\n", "; ")
        self.observe(2, "process", "Islepro window properties", props)
        info = run(["xdpyinfo"], env=self.env).stdout.decode()
        dims = re.search(r"dimensions:\s+(\d+x\d+)", info).group(1)
        planes = re.search(r"depth of root window:\s+(\d+)", info).group(1)
        self.observe(2, "process", "root window at the title screen", f"{dims}x{planes}")
        self.say(f"root window at the title screen: {dims}x{planes}; window {props}")
        since = round(time.monotonic() - self.t_launch, 2)
        self.observe(2, "screen", "title screen reached and stable, seconds after launch", since)
        self.say(f"title screen reached {since} s after launch")

    def hover_click(self, x, y, label, rect, step):
        """Move to (x, y), wait until the label under the pointer changes, then click.

        'immediate' skips the wait: in exploration a click sent right after the move was dropped.
        """
        before = self.screen.raw(rect)
        run(["xdotool", "mousemove", str(x + self.screen.ox), str(y + self.screen.oy)], env=self.env)
        if self.args.click == "hover":
            hovered = poll(lambda: self.screen.raw(rect) != before, 5, 0.05)
            self.observe(step, "screen", f"{label} changed under the pointer (s)",
                         "no change within 5 s" if hovered is None else hovered)
            self.say(f"{label}: hover change {hovered}")
        run(["xdotool", "click", "1"], env=self.env)

    def input(self):
        self.hover_click(*OPTIONS_CLICK, "Options label", OPTIONS_LABEL, 4)
        waited = poll(self.screen.options_up, 20, 0.1)
        self.say(f"options screen after click: {waited}")
        self.observe(5, "screen", "Options screen after click (s)", "absent" if waited is None else waited)
        if waited is None:
            self.after_screen_ok = False
            return
        stable = poll(self.screen.stable, 30, 0.1)
        self.after_screen_ok = stable is not None
        if self.args.input == "save-default" and self.after_screen_ok:
            self.hover_click(*SAVE_CLICK, "Save as default button", SAVE_DEFAULT, 6)
            self.after_screen_ok = poll(self.screen.stable, 30, 0.1) is not None

    def shot(self, name, step):
        path = self.workdir / name
        pixels, png = self.screen.capture(self.workdir, name)
        self.outputs.append((name, path, "screenshot"))
        self.observe(step, "screen", f"{name} raw RGB8 pixels sha256", pixels)
        self.say(f"{name}: pixels {pixels[:16]}, file {png[:16]}")
        return pixels, png

    def game_alive(self):
        return self.procs["game"].poll() is None

    def terminate(self):
        how = self.args.terminate
        if how == "ui-quit":
            if self.screen.options_up():
                self.hover_click(*RETURN_CLICK, "Return button", RETURN_BUTTON, 7)
                if poll(self.screen.title_up, 20, 0.1) is None:
                    self.say("Return did not bring the title screen back")
            self.hover_click(*QUIT_CLICK, "Quit label", (680, 572, 60, 26), 7)
            if poll(self.screen.notice_up, 20, 0.1) is None:
                self.say("the unregistered-version notice did not appear after Quit")
            else:
                poll(self.screen.stable, 20, 0.1)
                self.shot("notice.png", 8)
                self.hover_click(*EXIT_CLICK, "Exit Game label", EXIT_GAME, 8)
        elif how == "wm-close":
            run(["xdotool", "key", "alt+F4"], env=self.env)
        waited = None
        if how != "kill":
            waited = poll(lambda: not self.game_alive(), 60, 0.1)
            self.observe(9, "process", f"game exit after {how} (s)", "still running" if waited is None else waited)
            self.say(f"game exit after {how}: {waited}")
            if waited is None:
                self.shot("terminate-stuck.png", 9)
        if self.game_alive() or how == "kill":
            self.say("wineserver -k")
            run([WINESERVER, "-k"], env=self.env)
            poll(lambda: not self.game_alive(), 20, 0.1)
        code = self.procs["game"].poll()
        self.observe(9, "process", "game process exit status", code)
        self.say(f"game exit status {code}")
        # the whole Wine side must be gone before the display goes
        gone = poll(lambda: not self.wine_processes(), 30, 0.1)
        self.observe(9, "process", "wine processes gone after terminate (s)", "still running" if gone is None else gone)
        if gone is None:
            self.say("wineserver -k again, then SIGKILL")
            run([WINESERVER, "-k"], env=self.env)
            for pid in self.wine_processes():
                os.kill(pid, signal.SIGKILL)

    def wine_processes(self):
        mine = []
        for pid in marked_processes(self.run_id):
            comm = Path(f"/proc/{pid}/comm").read_text().strip() if Path(f"/proc/{pid}/comm").exists() else ""
            if comm not in ("Xvfb", "xfwm4"):
                mine.append(pid)
        return [p for p in mine if p != os.getpid() and Path(f"/proc/{p}").exists() and
                self.is_alive(p)]

    @staticmethod
    def is_alive(pid):
        try:
            return Path(f"/proc/{pid}/stat").read_text().split(") ")[-1].split()[0] != "Z"
        except OSError:
            return False

    def stop_x(self):
        for name in ("wm", "xvfb"):
            proc = self.procs.get(name)
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        left = [p for p in marked_processes(self.run_id) if self.is_alive(p)]
        self.observe(10, "process", "processes of this run still alive after terminate", len(left))
        self.say(f"processes still alive after terminate: {len(left)}")
        if left:
            self.abort_later(f"{len(left)} process(es) survived terminate")

    # ---- snapshots

    def take_snapshots(self, label):
        game = snapshot_tree(self.game)
        pfx = snapshot_tree(self.prefix)
        reg = registry_keys(self.prefix)
        setattr(self, f"snap_{label}", (game, pfx, reg))
        return game, pfx, reg

    def report_changes(self):
        gb, pb, rb = self.snap_before
        ga, pa, ra = self.snap_after
        lines = []
        for name, before, after in (("game copy", gb, ga), ("prefix", pb, pa)):
            added, removed, changed = diff_tree(before, after)
            lines.append(f"== {name}: {len(after)} entries after, added {len(added)}, removed {len(removed)}, changed {len(changed)}")
            lines += [f"added   {p} {after[p][1] if after[p][0] == 'f' else ''}".rstrip() for p in added]
            lines += [f"removed {p}" for p in removed]
            lines += [f"changed {p} {before[p][1:2]} -> {after[p][1:2]}" for p in changed]
            self.observe(8, "file", f"{name}: added/removed/changed entries",
                         f"{len(added)}/{len(removed)}/{len(changed)}")
        rkeys_added = sorted(set(ra) - set(rb))
        rkeys_removed = sorted(set(rb) - set(ra))
        rkeys_changed = sorted(k for k in set(ra) & set(rb) if ra[k] != rb[k])
        lines.append(f"== registry keys: {len(ra)} after, added {len(rkeys_added)}, removed {len(rkeys_removed)}, changed {len(rkeys_changed)}")
        lines += [f"added   {k}" for k in rkeys_added] + [f"removed {k}" for k in rkeys_removed]
        lines += [f"changed {k}" for k in rkeys_changed]
        self.observe(8, "file", "registry keys: added/removed/value-changed",
                     f"{len(rkeys_added)}/{len(rkeys_removed)}/{len(rkeys_changed)}")
        path = self.workdir / "changes.log"
        safeio.write_file(self.workdir, "changes.log", data=("\n".join(lines) + "\n").encode(), exist="new")
        self.outputs.append(("changes.log", path, "log"))
        self.changes = lines
        return lines

    def reset(self):
        """Put the game copy and the prefix back to the state they had before the launch."""
        _, pb, _ = self.snap_before
        _, pa, _ = self.snap_after
        added, _, _ = diff_tree(pb, pa)
        try:
            # What the run added loses its name, reached from the prefix without following any link:
            # a link is removed, never followed; a directory is removed through descriptors.
            for rel in sorted(added, reverse=True):
                safeio.remove(self.prefix, rel)
            baseline = Path(str(self.prefix) + ".baseline")
            for name in REG_FILES:
                source = baseline / name
                if source.is_file() and not source.is_symlink():
                    # a new file renamed over the prefix's, never a write through what is there
                    safeio.write_file(self.prefix, name, source=source, exist="replace",
                                      mode=stat.S_IMODE(source.stat().st_mode))
        except safeio.Refused as exc:
            self.abort_later(f"reset refused: {exc}")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                prefixlib.sync_game()
        except SystemExit as exc:
            self.abort_later(f"reset could not synchronise the game copy: {exc}")
        restored = snapshot_tree(self.prefix)
        added2, removed2, changed2 = diff_tree(pb, restored)
        ok = not (added2 or removed2 or changed2)
        self.observe(11, "file", "prefix after reset equals prefix before launch",
                     "yes" if ok else f"no: {len(added2)} added, {len(removed2)} removed, {len(changed2)} changed")
        self.say(f"reset: prefix equals its state before launch: {ok}")
        if not ok:
            self.abort_later("reset did not restore the prefix")
            self.say("  differing: " + ", ".join((added2 + removed2 + changed2)[:10]))

    # ---- main

    def execute(self):
        """The cycle's stages, then its clean-up. Whatever happens, the run ends with a status:
        "completed" from complete() only, "aborted: <why>" otherwise, and every clean-up stage runs."""
        started = now()
        try:
            self.protect_install()
            self.seal("before anything starts", 0)
            self.start_x()
            self.start_wm()
            self.take_snapshots("before")
            self.launch()                      # seals the prefix again, immediately before the game
            self.known_screen()
            self.before = self.shot("before.png", 3)
            self.input()
            self.after = self.shot("after.png", 6)
            self.complete()
        except Abort:
            pass                               # fail() has recorded why
        except BaseException as exc:           # a crash or an interruption: cleaned up, recorded, never completed
            self.abort_later(f"{type(exc).__name__}: {exc}")
        self.cleanup("terminate", self.terminate if "game" in self.procs else None)
        self.cleanup("stopping the display", self.stop_x)
        if hasattr(self, "snap_before"):
            self.cleanup("snapshot and reset", self.snapshot_and_reset)
        self.cleanup("keeping the logs", self.keep_logs)
        if self.status == "running":           # the last guard: nothing that did not complete() is completed
            self.status = "aborted: the cycle stopped before its end"
        self.started, self.ended = started, now()

    def cleanup(self, stage, action):
        """Run one clean-up stage; a failure of it aborts the run and does not stop the next stage."""
        if action is None:
            return
        try:
            action()
        except BaseException as exc:
            self.abort_later(f"{stage} failed: {type(exc).__name__}: {exc}")

    def snapshot_and_reset(self):
        self.take_snapshots("after")
        self.report_changes()
        self.reset()

    def keep_logs(self):
        log_path = self.workdir / "wine.log"
        if log_path.exists():
            self.outputs.append(("wine.log", log_path, "log"))
        safeio.write_file(self.workdir, "run.log", data=("\n".join(self.log) + "\n").encode(), exist="new")
        self.outputs.append(("run.log", self.workdir / "run.log", "log"))


# --- records ---------------------------------------------------------------------------------

def versions():
    def first(cmd, pattern):
        out = run(cmd)
        text = (out.stdout + out.stderr).decode(errors="replace")
        match = re.search(pattern, text)
        return match.group(1) if match else "unknown"
    return {
        "wine": first([WINE, "--version"], r"(wine-[^\n]+)"),
        "xvfb": first(["dpkg-query", "-W", "-f=${Version}", "xvfb"], r"(.+)"),
        "xfwm4": first(["dpkg-query", "-W", "-f=${Version}", "xfwm4"], r"(.+)"),
        "xdotool": first(["xdotool", "--version"], r"(\d+\.\d+\.\d+)"),
        "imagemagick": first(["import", "-version"], r"ImageMagick (\S+)"),
        "python": ".".join(map(str, sys.version_info[:3])),
        "kernel": os.uname().release,
    }


def next_run_id():
    folder = ROOT / "runs" / EXPERIMENT
    numbers = [int(m.group(1)) for p in folder.glob(f"{EXPERIMENT}-r*.json")
               if (m := re.match(rf"{EXPERIMENT}-r(\d+)\.json$", p.name))]
    return f"{EXPERIMENT}-r{(max(numbers) if numbers else 0) + 1:04d}"


def record_set(args):
    """The set a run is recorded under: the successor only when the run's input may write its file."""
    return SUCCESSOR_ID if args.input == "save-default" else SET_ID


def build_record(cycle, commit, machine, state_sha):
    args = cycle.args
    levels = [{"level": "I0", "what": "none"}]
    return {
        "schema": "run/1",
        "run_id": cycle.run_id,
        "experiment": EXPERIMENT,
        "arm": args.arm,
        "rep": int(os.environ["IWP_CYCLE_REP"]),
        "code_commit": commit,
        "machine": machine,
        "artifact": {"set": record_set(args), "variant": None},
        "runtime": {
            "driver": f"runtime/iwp/spike/cycle.py@{commit}",
            "platform": "linux-wsl2/wine-xvfb-xfwm4",
            "fingerprint": cycle.fingerprint,
        },
        "interventions": levels,
        "start_state": {
            "id": "S-cold-prefix-title",
            "sha256": state_sha,
            "restore": cycle.restore_text,
        },
        "seed": None,
        "actions": {
            "script": "runtime/iwp/spike/cycle.py",
            "sha256": sha256_file(SCRIPT),
            "args": cycle.argv,
        },
        "observations": cycle.obs,
        "outputs": [{"name": n, "sha256": sha256_file(p), "store": f"release:{EXPERIMENT}"}
                    for n, p, _ in cycle.outputs],
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
            "store": f"release:{EXPERIMENT}", "artifact": {"set": record_set(cycle.args), "variant": None},
            "files": files}


def arm_name(value):
    """--arm: a plain identifier, because it becomes part of file names (exploration output)."""
    try:
        return safeio.identifier(value, "arm")
    except safeio.Refused as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--arm", type=arm_name, default="control")
    ap.add_argument("--rep", type=int, default=None, help="default: one more than the records of this arm")
    ap.add_argument("--size", default="800x600x24")
    ap.add_argument("--wm", choices=["xfwm4", "none"], default="xfwm4")
    ap.add_argument("--audio", choices=["off", "default"], default="off")
    ap.add_argument("--click", choices=["hover", "immediate"], default="hover")
    ap.add_argument("--input", choices=["options", "save-default"], default="options",
                    help="options: click Options; save-default: also click Save as default (writes?)")
    ap.add_argument("--terminate", choices=["ui-quit", "wm-close", "kill"], default="ui-quit")
    ap.add_argument("--explore", action="store_true", help="print the result; write no record or bundle")
    return ap


def store_outputs(cycle, directory, name_of, exist):
    """Copy each output into a confined directory through the one writer (setup/iwp/safeio.py).

    An output that cannot be stored (its name, a link or a second name at its destination, a
    directory swapped for a link) is dropped and aborts the run: the record never names an output
    the store does not hold. Returns the outputs stored."""
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
    locs = confined_locations(args)
    prefix, bundles, install = locs["IWP_PREFIX"], locs["E001_BUNDLES"], locs["IWP_DIR"]
    run_id = os.environ["IWP_CYCLE_ID"]
    machine = os.environ.get("E001_MACHINE", "local")
    if not re.fullmatch(rf"{EXPERIMENT}-x[0-9]+" if args.explore else rf"{EXPERIMENT}-r[0-9]{{4,}}", run_id):
        sys.exit(f"{run_id!r} is not a run id of {EXPERIMENT}; nothing was started")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", machine):
        sys.exit("E001_MACHINE is not a machine id (lowercase letters, digits, dashes); nothing was started")
    try:
        safeio.identifier(args.arm, "arm")            # also when inner() is called without the parser
    except safeio.Refused as exc:
        sys.exit(f"{exc}; nothing was started")
    run(["mount", "-t", "tmpfs", "-o", "mode=1777", "tmpfs", "/tmp"], check=True)
    cycle = Cycle(args, run_id, prefix, bundles, install)
    cycle.argv = sys.argv[1:]
    cycle.fingerprint = versions()
    cycle.restore_text = ("fresh private user, mount and PID namespaces, the install bound read-only; the prefix "
                          "sealed (drive mapping, links, second names, mounts, the registered game copy) before "
                          "anything starts and again immediately before the launch; prefix as left by "
                          "setup/iwp/iwp-runtime.sh and by the previous run's reset; start_state.sha256 lists every "
                          "entry of the prefix with the size and sha256 of each file and the target of each link, "
                          "the registry files included")
    cycle.execute()
    commit = os.environ["IWP_CYCLE_COMMIT"]
    state_sha = start_state_sha(cycle.snap_before[1]) if hasattr(cycle, "snap_before") else "0" * 64
    if args.explore:
        out = locs.get("E001_EXPLORE", bundles)
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
    try:                                              # both record folders are reachable, or nothing is written
        for folder in names:
            os.close(safeio.open_directory(repo / folder / EXPERIMENT, create_below=repo))
    except (safeio.Refused, OSError) as exc:
        print(f"no record written: {exc}", file=sys.stderr)
        return 1
    cycle.outputs = store_outputs(cycle, bundles, lambda name, digest: f"{digest[:16]}-{name}", "same")
    manifest = build_manifest(cycle)
    record = build_record(cycle, commit, machine, state_sha)
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
    locs = confined_locations(args)
    prefix = locs["IWP_PREFIX"]
    strays = marked_processes() + prefix_processes(prefix)
    if strays:
        sys.exit(f"stale processes of an earlier run or of setup are alive: {sorted(set(strays))}; "
                 "stop them first (nothing was started)")
    problems = prefixlib.prefix_problems(prefix, locs["IWP_DIR"])
    if problems:
        sys.exit("the prefix is not safe to launch from; nothing was started: " + "; ".join(problems)[:400])
    commit_out = run(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT)
    dirty = run(["git", "status", "--porcelain", "--", "runtime", "setup", "tools", "formats"], cwd=ROOT).stdout
    if dirty and not args.explore:
        sys.exit("runtime/, setup/, tools/ or formats/ has uncommitted changes; commit before a recorded run")
    run_id = next_run_id() if not args.explore else f"{EXPERIMENT}-x{os.getpid()}"
    rep = args.rep or 1 + sum(
        1 for p in (ROOT / "runs" / EXPERIMENT).glob("*.json") if json.loads(p.read_text()).get("arm") == args.arm)
    env = dict(os.environ, IWP_CYCLE_ID=run_id, IWP_CYCLE_REP=str(rep), IWP_CYCLE_COMMIT=commit_out.stdout.decode().strip(),
               IWP_CYCLE_INNER="1")
    cmd = ["unshare", "-r", "-m", "-p", "-f", "--kill-child", "--mount-proc",
           sys.executable, str(SCRIPT)] + sys.argv[1:]
    code = subprocess.run(cmd, env=env).returncode
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
    if os.environ.get("IWP_CYCLE_INNER") == "1":
        return inner(args)
    return outer(args)


if __name__ == "__main__":
    sys.exit(main())
