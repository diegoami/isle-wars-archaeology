#!/usr/bin/env python3
"""E001 cycle: launch Isle Wars Pro under Wine, reach a known screen, give one input, observe,
terminate, reset, and write one run/1 record (W3a spike; the reusable driver is W5a).

One run is: cold state check, Xvfb, xfwm4, snapshot, launch, window, known screen, before
screenshot, one input, after screenshot, terminate, snapshot, diff, record. Everything but the
record and the bundles happens inside a private user, mount and PID namespace (``unshare -rmpf``):

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
    IWP_DIR       the install; read and hashed only, to restore the game copy when it has changed
    E001_MACHINE  the machine id written to records (default: local)

Usage: cycle.py [--arm NAME] [--size WxHxD] [--wm xfwm4|none] [--audio off|default]
                [--click hover|immediate] [--terminate ui-quit|wm-close|kill]
                [--explore]   (--explore prints the result and writes no record)
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import signal
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
    """The canonical, confined machine-local locations; SystemExit before anything is touched."""
    return locations.locations(need_prefix=True, need_bundles=True, explore=args.explore)


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

    def capture(self, path):
        """One capture: returns (sha256 of the raw 8-bit RGB pixels, sha256 of the PNG file).

        The PNG is written here, not by ImageMagick, because ImageMagick 6.9.12 wrote different
        bytes for identical pixels (observed: two conversions of one capture differed), and the
        screenshots are compared by file hash.
        """
        data = self.raw()
        if len(data) != self.width * self.height * 3:
            raise RuntimeError(f"capture is {len(data)} bytes, not {self.width}x{self.height} RGB")
        Path(path).write_bytes(png_bytes(self.width, self.height, data))
        return sha256_bytes(data), sha256_file(path)


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
    def __init__(self, args, run_id, prefix, bundles):
        self.args, self.run_id, self.prefix, self.bundles = args, run_id, prefix, bundles
        self.game = prefix / "drive_c" / "iwp"
        self.obs = []                # run/1 observations
        self.outputs = []            # (name, path, class) of bundle files
        self.log = []                # lines of the run log (a bundle file)
        self.procs = {}
        self.workdir = Path(tempfile.mkdtemp(prefix="iwp-cycle-"))
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
        self.status = "completed"

    def say(self, text):
        self.log.append(f"{time.strftime('%H:%M:%S')} {text}")
        print(text, flush=True)

    def observe(self, step, source, field, value):
        self.obs.append({"step": step, "source": source, "field": field, "value": str(value)})

    def fail(self, reason):
        self.status = f"aborted: {reason}"
        self.say(f"ABORT {reason}")
        raise RuntimeError(reason)

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
        cmd = game_command()
        self.t_launch = time.monotonic()
        with open(self.workdir / "wine.log", "wb") as log:
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
        pixels, png = self.screen.capture(path)
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
            self.status = f"aborted: {len(left)} process(es) survived terminate"

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
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.outputs.append(("changes.log", path, "log"))
        self.changes = lines
        return lines

    def reset(self):
        """Put the game copy and the prefix back to the state they had before the launch."""
        _, pb, _ = self.snap_before
        _, pa, _ = self.snap_after
        added, _, _ = diff_tree(pb, pa)
        for rel in sorted(added, reverse=True):
            path = self.prefix / rel
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        baseline = Path(str(self.prefix) + ".baseline")
        for name in REG_FILES:
            if (baseline / name).is_file():
                shutil.copyfile(baseline / name, self.prefix / name)
        if os.environ.get("IWP_DIR"):
            run([sys.executable, str(ROOT / "setup" / "iwp" / "prefix.py"), "sync-game"], cwd=ROOT)
        restored = snapshot_tree(self.prefix)
        added2, removed2, changed2 = diff_tree(pb, restored)
        ok = not (added2 or removed2 or changed2)
        self.observe(11, "file", "prefix after reset equals prefix before launch",
                     "yes" if ok else f"no: {len(added2)} added, {len(removed2)} removed, {len(changed2)} changed")
        self.say(f"reset: prefix equals its state before launch: {ok}")
        if not ok:
            self.status = "aborted: reset did not restore the prefix"
            self.say("  differing: " + ", ".join((added2 + removed2 + changed2)[:10]))

    # ---- main

    def execute(self):
        started = now()
        try:
            self.cold_state_check()
            self.start_x()
            self.start_wm()
            self.take_snapshots("before")
            self.launch()
            self.known_screen()
            self.before = self.shot("before.png", 3)
            self.input()
            self.after = self.shot("after.png", 6)
            if not self.after_screen_ok or not self.screen.options_up():
                self.fail("the click did not bring up the Options screen")
        except RuntimeError:
            pass
        except Exception as exc:     # a crash must still clean up and leave a record
            self.status = f"aborted: {type(exc).__name__}: {exc}"
            self.say(self.status)
        finally:
            try:
                if "game" in self.procs:
                    self.terminate()
            finally:
                self.stop_x()
            if hasattr(self, "snap_before"):
                self.take_snapshots("after")
                self.report_changes()
                self.reset()
            log_path = self.workdir / "wine.log"
            if log_path.exists():
                self.outputs.append(("wine.log", log_path, "log"))
            run_log = self.workdir / "run.log"
            run_log.write_text("\n".join(self.log) + "\n", encoding="utf-8")
            self.outputs.append(("run.log", run_log, "log"))
        self.started, self.ended = started, now()

    def cold_state_check(self):
        check = run([sys.executable, str(ROOT / "tools" / "register_artifact.py"), "check", str(self.game), SET_ID],
                    cwd=ROOT)
        text = (check.stdout + check.stderr).decode()
        self.observe(0, "file", "game copy checked against the registered set", "exit " + str(check.returncode))
        unlisted = [l for l in text.splitlines() if l.startswith("unlisted:")]
        self.observe(0, "file", "game copy files outside the set", len(unlisted))
        if check.returncode != 0 or unlisted:
            self.fail("the game copy differs from the registered set: " + " ".join(text.split())[:200])
        self.say("game copy matches the registered set")


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


def parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--arm", default="control")
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


def inner(args):
    """Runs as PID 1 of the private namespaces: does the cycle and writes the record."""
    locs = confined_locations(args)
    prefix, bundles = locs["IWP_PREFIX"], locs["E001_BUNDLES"]
    run_id = os.environ["IWP_CYCLE_ID"]
    run(["mount", "-t", "tmpfs", "-o", "mode=1777", "tmpfs", "/tmp"], check=True)
    cycle = Cycle(args, run_id, prefix, bundles)
    cycle.argv = sys.argv[1:]
    cycle.fingerprint = versions()
    cycle.restore_text = ("fresh private user, mount and PID namespaces; game copy verified against the set "
                          "before launch; prefix as left by setup/iwp/iwp-runtime.sh and by the previous run's "
                          "reset; start_state.sha256 lists every entry of the prefix with the size and sha256 of "
                          "each file and the target of each link, the registry files included")
    cycle.execute()
    commit = os.environ["IWP_CYCLE_COMMIT"]
    machine = os.environ.get("E001_MACHINE", "local")
    state_sha = start_state_sha(cycle.snap_before[1]) if hasattr(cycle, "snap_before") else "0" * 64
    summary = {"run_id": run_id, "status": cycle.status}
    if args.explore:
        out = locs.get("E001_EXPLORE", bundles)
        out.mkdir(parents=True, exist_ok=True)
        for name, path, _ in cycle.outputs:
            shutil.copy(path, out / f"{args.arm}.{name}")
        (out / f"{args.arm}.observations.json").write_text(json.dumps(cycle.obs, indent=1))
        print(json.dumps(summary))
        return 0 if cycle.status == "completed" else 1
    bundles.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(cycle)
    for entry, (name, path, _) in zip(manifest["files"], cycle.outputs):
        shutil.copy(path, bundles / entry["asset"])
    record = build_record(cycle, commit, machine, state_sha)
    (ROOT / "evidence" / EXPERIMENT).mkdir(parents=True, exist_ok=True)
    (ROOT / "runs" / EXPERIMENT).mkdir(parents=True, exist_ok=True)
    (ROOT / "evidence" / EXPERIMENT / f"{run_id}.manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (ROOT / "runs" / EXPERIMENT / f"{run_id}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(summary))
    return 0 if cycle.status == "completed" else 1


def outer(args):
    locs = confined_locations(args)
    prefix = locs["IWP_PREFIX"]
    strays = marked_processes() + prefix_processes(prefix)
    if strays:
        sys.exit(f"stale processes of an earlier run or of setup are alive: {sorted(set(strays))}; "
                 "stop them first (nothing was started)")
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
