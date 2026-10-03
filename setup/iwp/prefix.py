#!/usr/bin/env python3
"""The Wine prefix of the iwp-runtime profile (W3a): build it, fill it, clean it, check it.

Commands (machine-local values come from the environment, never from this file):
    build          create the prefix (WINEARCH=win32, the PE header's machine type) when it is absent
    sync-game      make <prefix>/drive_c/iwp equal to the registered set, copied from IWP_DIR
    strip-links    remove the Z: drive, the COM port links and any absolute link in the user profile
    baseline       keep the registry files as they are now, for the cycle's reset (kept once)
    check          the prefix side of the profile: no Z:, no absolute links, the game copy matches

IWP_PREFIX is the prefix (outside every checkout). IWP_DIR is the install; it is read and hashed
only, to copy files out of it into the prefix's C: drive (CLAUDE.md rule 18: it never enters the
repository). Nothing here writes to IWP_DIR.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SET_ID = "iwp-2.0-996e86c5"
WINE = "/usr/lib/wine/wine"
WINESERVER = "/usr/lib/wine/wineserver"
GAME_DIR = "iwp"                 # <prefix>/drive_c/iwp, the game's copy
REG_FILES = ("system.reg", "user.reg", "userdef.reg", ".update-timestamp")


def prefix_path():
    value = os.environ.get("IWP_PREFIX")
    if not value:
        sys.exit("IWP_PREFIX is not set")
    return Path(value)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest():
    known = json.loads((ROOT / "artifacts" / "known.json").read_text(encoding="utf-8"))
    for entry in known["sets"]:
        if entry["manifest"]["id"] == SET_ID:
            return entry["manifest"]
    sys.exit(f"{SET_ID} is not in artifacts/known.json")


def wine_env(prefix, display=None):
    env = dict(os.environ, WINEPREFIX=str(prefix), WINEARCH="win32", WINEDEBUG="-all")
    # no menu entries or file associations on the host; no Mono or Gecko download prompts
    env["WINEDLLOVERRIDES"] = "winemenubuilder.exe=d;mscoree=d;mshtml=d"
    if display:
        env["DISPLAY"] = display
    return env


def free_display():
    """A display number nobody uses: no lock file and no abstract socket (read from /proc/net/unix).

    Xvfb -displayfd was tried first; on this machine, where /tmp/.X11-unix is a read-only mount,
    it printed nothing (every number failed to bind its filesystem socket), so numbers are chosen here.
    """
    try:
        sockets = Path("/proc/net/unix").read_text(errors="replace")
    except OSError:
        sockets = ""
    for number in range(100, 200):
        if not Path(f"/tmp/.X{number}-lock").exists() and f"@/tmp/.X11-unix/X{number}" not in sockets:
            return f":{number}"
    sys.exit("no free X display number between 100 and 199")


def start_xvfb(size="800x600x16"):
    """Start Xvfb on a free display and wait until xdpyinfo answers. Returns (process, display)."""
    display = free_display()
    proc = subprocess.Popen(["Xvfb", display, "-screen", "0", size, "-nolisten", "tcp"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if subprocess.run(["xdpyinfo", "-display", display], capture_output=True).returncode == 0:
            return proc, display
        if proc.poll() is not None:
            break
        time.sleep(0.1)
    proc.terminate()
    sys.exit(f"Xvfb did not accept connections on {display}")


def build():
    prefix = prefix_path()
    if (prefix / "system.reg").is_file():
        print(f"prefix exists: {prefix.name}")
        return 0
    prefix.parent.mkdir(parents=True, exist_ok=True)
    xvfb, display = start_xvfb()
    try:
        env = wine_env(prefix, display)
        # `wineboot -u` as the user, as the IC2 notes say it was required
        subprocess.run([WINE, "wineboot", "-u"], env=env, check=True, timeout=300)
        subprocess.run([WINESERVER, "-w"], env=env, timeout=120)
    finally:
        subprocess.run([WINESERVER, "-k"], env=wine_env(prefix), check=False)
        xvfb.terminate()
        xvfb.wait(10)
    if not (prefix / "system.reg").is_file():
        sys.exit("wineboot did not create the prefix")
    print(f"prefix built: {prefix.name}")
    return 0


def sync_game():
    prefix = prefix_path()
    source = os.environ.get("IWP_DIR")
    if not source:
        sys.exit("IWP_DIR is not set")
    source, game = Path(source), prefix / "drive_c" / GAME_DIR
    files = {f["path"]: f for f in manifest()["files"]}
    copied, removed = [], []
    for rel, entry in sorted(files.items()):
        src, dst = source / rel, game / rel
        if dst.is_file() and sha256_file(dst) == entry["sha256"]:
            continue
        if sha256_file(src) != entry["sha256"]:
            sys.exit(f"{rel}: the install's file is not the registered one; nothing copied")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.chmod(0o644)
        shutil.copyfile(src, dst)
        shutil.copystat(src, dst)
        dst.chmod(0o644)     # writable: the Windows install is, and a read-only copy would hide writes
        copied.append(rel)
    if game.is_dir():
        for path in sorted(game.rglob("*"), reverse=True):
            rel = path.relative_to(game).as_posix()
            if path.is_file() or path.is_symlink():
                if rel not in files:
                    path.unlink()
                    removed.append(rel)
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
        for path in game.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
    print(f"game copy: copied {len(copied)}, removed {len(removed)}")
    return 0


def strip_links():
    prefix = prefix_path()
    removed = []
    devices = prefix / "dosdevices"
    if devices.is_dir():
        for entry in devices.iterdir():
            if entry.name != "c:":
                entry.unlink()
                removed.append(f"dosdevices/{entry.name}")
    users = prefix / "drive_c" / "users"
    if users.is_dir():
        for path in sorted(users.rglob("*")):
            if path.is_symlink() and os.readlink(path).startswith("/"):
                path.unlink()
                path.mkdir()
                removed.append(path.relative_to(prefix).as_posix())
    print(f"links removed: {len(removed)}" + ("".join(f"\n  {r}" for r in removed)))
    return 0


def baseline():
    prefix = prefix_path()
    target = Path(str(prefix) + ".baseline")
    if (target / "system.reg").is_file():
        print("baseline exists")
        return 0
    target.mkdir(parents=True, exist_ok=True)
    for name in REG_FILES:
        if (prefix / name).is_file():
            shutil.copyfile(prefix / name, target / name)
    print("baseline kept")
    return 0


def absolute_links(prefix):
    found = []
    for base in (prefix / "dosdevices", prefix / "drive_c" / "users"):
        if base.is_dir():
            found += [p for p in base.rglob("*") if p.is_symlink() and os.readlink(p).startswith("/")]
    return found


def check():
    prefix = prefix_path()
    problems = []
    if not (prefix / "system.reg").is_file():
        problems.append("the prefix does not exist")
    if (prefix / "dosdevices" / "z:").exists() or (prefix / "dosdevices" / "z:").is_symlink():
        problems.append("dosdevices/z: exists")
    problems += [f"absolute link: {p.relative_to(prefix).as_posix()}" for p in absolute_links(prefix)]
    game = prefix / "drive_c" / GAME_DIR
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "register_artifact.py"), "check", str(game), SET_ID, "--strict"],
                            capture_output=True, text=True, cwd=ROOT)
    if result.returncode != 0:
        problems.append("the game copy is not the registered set")
    if problems:
        print("\n".join(problems))
        return 1
    print("prefix ok")
    return 0


COMMANDS = {"build": build, "sync-game": sync_game, "strip-links": strip_links, "baseline": baseline, "check": check}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    sys.exit(COMMANDS[sys.argv[1]]())
