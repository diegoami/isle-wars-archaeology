#!/usr/bin/env python3
"""The Wine prefix of the iwp-runtime profile (W3a): build it, fill it, clean it, check it.

Commands (machine-local values come from the environment, never from this file):
    build          create the prefix (WINEARCH=win32, the PE header's machine type) when it is absent
    sync-game      make <prefix>/drive_c/iwp equal to the registered set, copied from IWP_DIR
    strip-links    remove the Z: drive, the COM port links and every link that leaves the prefix
    baseline       keep the registry files as they are now, for the cycle's reset (kept once)
    check          the prefix side of the profile: C: is drive_c, nothing else is mapped, no link
                   leaves the prefix, the game copy is a real directory holding the registered set

IWP_PREFIX is the prefix (outside every checkout). IWP_DIR is the install; it is read and hashed
only, to copy files out of it into the prefix's C: drive (CLAUDE.md rule 18: it never enters the
repository). Nothing here writes to IWP_DIR. Before any command mutates anything the locations are
confined (locations.py): outside every checkout, not overlapping the install or each other. The
game copy is refused when it, or a directory above it, is a link, or when it overlaps the install.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import locations  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SET_ID = "iwp-2.0-996e86c5"
WINE = "/usr/lib/wine/wine"
WINESERVER = "/usr/lib/wine/wineserver"
GAME_DIR = "iwp"                 # <prefix>/drive_c/iwp, the game's copy
REG_FILES = ("system.reg", "user.reg", "userdef.reg", ".update-timestamp")


def prefix_path():
    """The confined, canonical prefix (and, when set, the install and the baseline checked with it)."""
    return locations.locations(need_prefix=True)["IWP_PREFIX"]


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


def _register_artifact():
    spec = importlib.util.spec_from_file_location("register_artifact_tool", ROOT / "tools" / "register_artifact.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_game_copy(game):
    """Problems (a list of strings, empty when it is right) with a game copy against the registered set.

    The same comparison as `register_artifact.py check --strict`: every listed file present with
    its size and sha256, and no file outside the set (a runtime write of the set is allowed).
    """
    game = Path(game)
    if game.is_symlink() or not game.is_dir():
        return [f"the game copy {game.name} is not a real directory"]
    tool = _register_artifact()
    wanted = manifest()
    problems, unlisted = tool.compare(tool.hash_tree(game, wanted), wanted, strict=True)
    return problems


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


def game_destination(prefix, install):
    """The confined game directory of a prefix, or SystemExit. Nothing is changed.

    Refused: a link at drive_c or at the game directory, a game directory that is not a directory,
    one whose canonical path is not strictly inside the prefix, and any overlap with the install.
    """
    cdrive = prefix / "drive_c"
    game = cdrive / GAME_DIR
    if not cdrive.is_dir():
        raise SystemExit("the prefix has no drive_c; build it first")
    for part in (cdrive, game):
        if part.is_symlink():
            raise SystemExit(f"{part.name} is a link; the game copy must be a separate real directory")
    if game.exists() and not game.is_dir():
        raise SystemExit(f"{GAME_DIR} exists and is not a directory")
    canonical = locations.real(game)
    if canonical == prefix or not locations.inside(canonical, prefix):
        raise SystemExit("the game copy resolves outside the prefix")
    if locations.inside(canonical, install) or locations.inside(install, canonical):
        raise SystemExit("the game copy overlaps the install")
    return game


def sync_game():
    locs = locations.locations(need_prefix=True)
    prefix = locs["IWP_PREFIX"]
    if "IWP_DIR" not in locs:
        sys.exit("IWP_DIR is not set")
    source = locs["IWP_DIR"]
    game = game_destination(prefix, source)
    files = {f["path"]: f for f in manifest()["files"]}
    for rel in files:
        parts = Path(rel).parts
        if Path(rel).is_absolute() or ".." in parts or not parts:
            sys.exit(f"{rel}: not a path inside the set")
    # Everything is checked before anything is changed: each source file is a regular file of the
    # install with the registered sha256, or nothing is copied, removed or re-permissioned.
    for rel, entry in sorted(files.items()):
        src = source / rel
        if src.is_symlink() or not src.is_file():
            sys.exit(f"{rel}: the install has no such regular file; nothing changed")
        if sha256_file(src) != entry["sha256"]:
            sys.exit(f"{rel}: the install's file is not the registered one; nothing changed")
    copied, removed = [], []
    game.mkdir(parents=True, exist_ok=True)
    game_real = locations.real(game)
    # The copy holds no links at all: a link is removed itself, never followed.
    for dirpath, dirnames, filenames in os.walk(game, followlinks=False):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            if path.is_symlink():
                path.unlink()
                removed.append(path.relative_to(game).as_posix())
    for rel, entry in sorted(files.items()):
        src, dst = source / rel, game / rel
        if dst.is_file() and sha256_file(dst) == entry["sha256"]:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not locations.inside(locations.real(dst.parent), game_real):
            sys.exit(f"{rel}: resolves outside the game copy")
        if dst.exists():
            dst.chmod(0o644)
        shutil.copyfile(src, dst)
        shutil.copystat(src, dst)
        dst.chmod(0o644)     # writable: the Windows install is, and a read-only copy would hide writes
        copied.append(rel)
    for dirpath, dirnames, filenames in os.walk(game, topdown=False, followlinks=False):
        for name in filenames + dirnames:
            path = Path(dirpath) / name
            rel = path.relative_to(game).as_posix()
            if path.is_symlink():
                path.unlink()                      # the link itself; never what it points at
                removed.append(rel)
            elif path.is_file() and rel not in files:
                path.unlink()
                removed.append(rel)
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    for dirpath, dirnames, _ in os.walk(game, followlinks=False):
        for name in dirnames:
            (Path(dirpath) / name).chmod(0o755)
    game.chmod(0o755)
    print(f"game copy: copied {len(copied)}, removed {len(removed)}")
    return 0


def symlinks(prefix):
    """Every link inside the prefix, found without following any of them."""
    found = []
    for dirpath, dirnames, filenames in os.walk(prefix, followlinks=False):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            if path.is_symlink():
                found.append(path)
    return sorted(found)


def escapes(link, prefix):
    """True when a link, resolved however many hops and however it is written, ends outside the prefix."""
    return not locations.inside(locations.real(link), locations.real(prefix))


def remove_entry(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def strip_links():
    prefix = prefix_path()
    removed = []
    devices = prefix / "dosdevices"
    if devices.is_symlink():
        sys.exit("dosdevices is a link; refused")
    if devices.is_dir():
        for entry in sorted(devices.iterdir()):
            if entry.name != "c:":
                remove_entry(entry)
                removed.append(f"dosdevices/{entry.name}")
        mapped = devices / "c:"
        drive_c = locations.real(prefix / "drive_c")
        if not mapped.is_symlink() or locations.real(mapped) != drive_c:
            remove_entry(mapped)
            os.symlink("../drive_c", mapped)
            removed.append("dosdevices/c: (mapped again to drive_c)")
    for link in symlinks(prefix):
        rel = link.relative_to(prefix).as_posix()
        if rel.startswith("dosdevices/") or not escapes(link, prefix):
            continue
        link.unlink()
        if rel.startswith("drive_c/users/"):
            link.mkdir()                 # a profile folder the host does not see
        removed.append(rel)
    print(f"links removed: {len(removed)}" + ("".join(f"\n  {r}" for r in removed)))
    return 0


def baseline():
    locs = locations.locations(need_prefix=True)
    prefix, target = locs["IWP_PREFIX"], locs["IWP_PREFIX.baseline"]
    if (target / "system.reg").is_file():
        print("baseline exists")
        return 0
    target.mkdir(parents=True, exist_ok=True)
    for name in REG_FILES:
        if (prefix / name).is_file():
            shutil.copyfile(prefix / name, target / name)
    print("baseline kept")
    return 0


def prefix_problems(prefix):
    """What is wrong with a prefix as a place to run the game; [] when nothing is. Nothing is changed."""
    problems = []
    if not (prefix / "system.reg").is_file():
        problems.append("the prefix does not exist")
    devices = prefix / "dosdevices"
    drive_c = prefix / "drive_c"
    if drive_c.is_symlink() or not drive_c.is_dir():
        problems.append("drive_c is not a real directory")
    if devices.is_symlink() or not devices.is_dir():
        problems.append("dosdevices is not a real directory")
    else:
        for entry in sorted(devices.iterdir()):
            if entry.name != "c:":
                problems.append(f"dosdevices/{entry.name} is mapped; only c: may be")
        mapped = devices / "c:"
        if not mapped.is_symlink():
            problems.append("dosdevices/c: is not a link")
        elif locations.real(mapped) != locations.real(drive_c):
            problems.append("dosdevices/c: does not map to drive_c")
    for link in symlinks(prefix):
        if escapes(link, prefix):
            problems.append(f"link leaves the prefix: {link.relative_to(prefix).as_posix()}")
    game = drive_c / GAME_DIR
    problems += [f"game copy: {p}" for p in verify_game_copy(game)]
    return problems


def check():
    prefix = prefix_path()
    problems = prefix_problems(prefix)
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
