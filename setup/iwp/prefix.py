#!/usr/bin/env python3
"""The Wine prefix of the iwp-runtime profile (W3a): build it, fill it, clean it, check it.

Commands (machine-local values come from the environment, never from this file):
    build          create the prefix (WINEARCH=win32, the PE header's machine type) when it is absent
    sync-game      make <prefix>/drive_c/iwp equal to the registered set, copied from IWP_DIR
    strip-links    remove the Z: drive, the COM port links and every link that leaves the prefix,
                   and give every file with a second name (a hard link) a file of its own
    baseline       keep the registry files as they are now, for the cycle's reset (kept once)
    check          the prefix side of the profile: C: is drive_c, nothing else is mapped, no link
                   leaves the prefix, no file has a second name, nothing is mounted inside it or is
                   one of the install's own files, and the game copy is a real directory holding
                   the registered set as plain files of its own

IWP_PREFIX is the prefix (outside every checkout). IWP_DIR is the install; it is read and hashed
only, to copy files out of it into the prefix's C: drive (CLAUDE.md rule 18: it never enters the
repository). Nothing here writes to IWP_DIR. Before any command mutates anything the locations are
confined (locations.py): outside every checkout, not overlapping the install or each other. The
game copy is refused when it, or a directory above it, is a link, or when it overlaps the install.

Every write, removal and mode change goes through safeio.py: a copy is a new file renamed into
place, never a write through an existing name, so a link or a second name (a hard link to the
install, say) at the destination is replaced, not written through, and loses only its name.
"""
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import locations  # noqa: E402
import safeio  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SET_ID = "iwp-2.0-996e86c5"
WINE = "/usr/lib/wine/wine"
WINESERVER = "/usr/lib/wine/wineserver"
GAME_DIR = "iwp"                 # <prefix>/drive_c/iwp, the game's copy
REG_FILES = ("system.reg", "user.reg", "userdef.reg", ".update-timestamp")


def prefix_path():
    """The confined, canonical prefix (and, when set, the install and the baseline checked with it)."""
    return locations.locations(need_prefix=True)["IWP_PREFIX"]


def install_from_env():
    """The canonical install when IWP_DIR is set, else None (read only, for the inode checks)."""
    value = os.environ.get("IWP_DIR")
    return locations.real(value) if value and os.path.isabs(value) else None


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


# --- aliases: entries that are, or lead to, another place ---------------------------------------

def install_inodes(install):
    """{(st_dev, st_ino)} of the install and of every entry in it (read only, links not followed)."""
    if install is None or not Path(install).is_dir():
        return set()
    found = {(os.lstat(install).st_dev, os.lstat(install).st_ino)}
    for dirpath, dirnames, filenames in os.walk(install, followlinks=False):
        for name in dirnames + filenames:
            info = os.lstat(Path(dirpath) / name)
            found.add((info.st_dev, info.st_ino))
    return found


def mount_points():
    """Canonical mount points of this process's mount namespace, from /proc/self/mountinfo."""
    try:
        text = Path("/proc/self/mountinfo").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    points = []
    for line in text.splitlines():
        fields = line.split(" ")
        if len(fields) > 4:
            points.append(Path(re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), fields[4])))
    return points


def foreign_entries(base):
    """Relative paths (with why) under base, base included as ".", that belong to another place:
    a mount point (a bind mount of the install, say), or an entry on another filesystem than
    base's parent. Nothing may change or remove such an entry, since that would change the other
    place, and nothing under it is looked into."""
    base = Path(base)
    found = [f"{(p.relative_to(base).as_posix() if p != base else '.')} is a mount point"
             for p in mount_points() if locations.inside(p, base)]
    reference = os.lstat(base.parent).st_dev
    if os.lstat(base).st_dev != reference:
        return sorted(set(found) | {". is on another filesystem"})
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        keep = []
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            if os.lstat(path).st_dev != reference:
                found.append(f"{path.relative_to(base).as_posix()} is on another filesystem")
            elif name in dirnames:
                keep.append(name)
        dirnames[:] = keep
    return sorted(set(found))


def extra_name_entries(base):
    """[(relative path, lstat)] under base of regular files with more than one name (hard links),
    and of devices, fifos and sockets. Writing such a file, or changing its mode, changes it for its
    other names too, wherever they are (the install's own file, for a hard link to it)."""
    found = []
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            info = os.lstat(path)
            kind = stat.S_IFMT(info.st_mode)
            if (kind == stat.S_IFREG and info.st_nlink > 1) or kind not in (stat.S_IFREG, stat.S_IFDIR, stat.S_IFLNK):
                found.append((path.relative_to(base).as_posix(), info))
    return sorted(found, key=lambda item: item[0])


def extra_names(base, install=None):
    """extra_name_entries as messages; a file that is one of the install's own says so."""
    ids = install_inodes(install)
    messages = []
    for rel, info in extra_name_entries(base):
        if stat.S_ISREG(info.st_mode):
            whose = "; another is the install's" if (info.st_dev, info.st_ino) in ids else ""
            messages.append(f"{rel} has {info.st_nlink} names (a hard link{whose})")
        else:
            messages.append(f"{rel} is a device, fifo or socket")
    return messages


def verify_game_copy(game, install=None):
    """Problems (a list of strings, empty when it is right) with a game copy against the registered set.

    The same comparison as `register_artifact.py check --strict` (every listed file present with
    its size and sha256, and no file outside the set; a runtime write of the set is allowed; a
    special file or a link that leaves the copy is a failure, as the tool reports it), and
    every entry must be the copy's own: no link, no file with a second name, nothing mounted or
    belonging to the install (IWP_DIR when `install` is not given).
    """
    game = Path(game)
    if game.is_symlink() or not game.is_dir():
        return [f"the game copy {game.name} is not a real directory"]
    install = install_from_env() if install is None else install
    problems = foreign_entries(game)
    if problems:
        return problems
    problems += [f"{p.relative_to(game).as_posix()} is a link" for p in symlinks(game)]
    problems += extra_names(game, install)
    tool = _register_artifact()
    wanted = manifest()
    observed, unobservable = tool.hash_tree(game, wanted)
    differences, unlisted = tool.compare(observed, wanted, strict=True)
    return problems + unobservable + [d for d in differences if d not in unobservable]


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


def _entries(game):
    """{relative path: lstat} of everything under game, links not followed (top-down order)."""
    found = {}
    for dirpath, dirnames, filenames in os.walk(game, followlinks=False):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            found[path.relative_to(game).as_posix()] = os.lstat(path)
    return found


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
    # install with the registered sha256, and nothing in the copy belongs to another place (a mount
    # point, or another filesystem), or nothing is copied, removed or re-permissioned.
    for rel, entry in sorted(files.items()):
        src = source / rel
        if src.is_symlink() or not src.is_file():
            sys.exit(f"{rel}: the install has no such regular file; nothing changed")
        if sha256_file(src) != entry["sha256"]:
            sys.exit(f"{rel}: the install's file is not the registered one; nothing changed")
    if game.exists():
        foreign = foreign_entries(game)
        if foreign:
            sys.exit("the game copy holds another place's entries; nothing changed: " + "; ".join(foreign)[:300])
    copied, removed = [], []
    try:
        os.close(safeio.open_directory(game, create_below=prefix / "drive_c"))
        listed_dirs = {p.as_posix() for rel in files for p in Path(rel).parents} - {"."}
        # 1. Anything that is not a plain entry of the copy's own loses its name, and so does any
        #    entry the set does not list or that stands where the other kind belongs. Removing a
        #    name never changes what another name of the same file holds.
        for rel, info in _entries(game).items():
            plain_dir = stat.S_ISDIR(info.st_mode)
            if plain_dir and rel in listed_dirs:
                continue
            if safeio.plain_file(info) and rel in files:
                continue
            if safeio.remove(game, rel):
                removed.append(rel)
        # 2. Each listed file that is not already the registered one is written as a new file and
        #    renamed into place, its copied bytes checked against the registered sha256.
        for rel, entry in sorted(files.items()):
            if safeio.sha256_plain(game, rel) == entry["sha256"]:
                continue
            parent = game.joinpath(*Path(rel).parts[:-1])
            safeio.write_file(parent, Path(rel).name, source=source / rel, exist="replace", mode=0o644,
                              expect_sha256=entry["sha256"], create_below=game, times_from_source=True)
            copied.append(rel)
        # 3. Modes: writable files and directories, as on the Windows install (a read-only copy
        #    would hide the game's writes), set through descriptors, never on a second name.
        for rel, info in _entries(game).items():
            safeio.set_mode(game, rel, 0o755 if stat.S_ISDIR(info.st_mode) else 0o644)
        safeio.set_mode(game, "", 0o755)
    except safeio.Refused as exc:
        sys.exit(f"the game copy was not synchronised: {exc}")
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


def strip_links():
    prefix = prefix_path()
    foreign = foreign_entries(prefix)
    if foreign:
        sys.exit("the prefix holds another place's entries; nothing changed: " + "; ".join(foreign)[:300])
    removed = []
    devices = prefix / "dosdevices"
    if devices.is_symlink():
        sys.exit("dosdevices is a link; refused")
    try:
        if devices.is_dir():
            for entry in sorted(devices.iterdir()):
                if entry.name != "c:":
                    safeio.remove(prefix, f"dosdevices/{entry.name}")
                    removed.append(f"dosdevices/{entry.name}")
            mapped = devices / "c:"
            drive_c = locations.real(prefix / "drive_c")
            if not mapped.is_symlink() or locations.real(mapped) != drive_c:
                safeio.remove(prefix, "dosdevices/c:")
                safeio.make_link(prefix, "dosdevices/c:", "../drive_c")
                removed.append("dosdevices/c: (mapped again to drive_c)")
        for link in symlinks(prefix):
            rel = link.relative_to(prefix).as_posix()
            if rel.startswith("dosdevices/") or not escapes(link, prefix):
                continue
            safeio.remove(prefix, rel)
            if rel.startswith("drive_c/users/"):
                safeio.make_directory(prefix, rel)        # a profile folder the host does not see
            removed.append(rel)
        # A file with a second name gets a file of its own: the same bytes, written as a new file
        # and renamed over this name; the other name keeps its file untouched.
        for rel, info in extra_name_entries(prefix):
            if not stat.S_ISREG(info.st_mode):
                sys.exit(f"strip-links stopped: {rel} is a device, fifo or socket; remove it by hand")
            path = prefix / rel
            with safeio.open_source(path) as fh:
                data = fh.read()
            safeio.write_file(path.parent, path.name, data=data, exist="replace", mode=stat.S_IMODE(info.st_mode),
                              replace_shared=True)
            removed.append(f"{rel} (given a file of its own)")
    except safeio.Refused as exc:
        sys.exit(f"strip-links stopped: {exc}")
    print(f"links removed: {len(removed)}" + ("".join(f"\n  {r}" for r in removed)))
    return 0


def baseline():
    locs = locations.locations(need_prefix=True)
    prefix, target = locs["IWP_PREFIX"], locs["IWP_PREFIX.baseline"]
    if (target / "system.reg").is_file():
        print("baseline exists")
        return 0
    try:
        os.close(safeio.open_directory(target, create_below=target.parent))
        for name in REG_FILES:
            if (prefix / name).is_file() and not (prefix / name).is_symlink():
                safeio.write_file(target, name, source=prefix / name, exist="replace")
    except safeio.Refused as exc:
        sys.exit(f"baseline not kept: {exc}")
    print("baseline kept")
    return 0


def prefix_problems(prefix, install=None):
    """What is wrong with a prefix as a place to run the game; [] when nothing is. Nothing is changed.

    `install` defaults to IWP_DIR; its inodes may appear nowhere in the prefix.
    """
    install = install_from_env() if install is None else install
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
    foreign = foreign_entries(prefix)
    problems += [f"belongs to another place: {p}" for p in foreign]
    if foreign:
        return problems              # nothing under another place is looked into
    for link in symlinks(prefix):
        if escapes(link, prefix):
            problems.append(f"link leaves the prefix: {link.relative_to(prefix).as_posix()}")
    game = drive_c / GAME_DIR
    problems += [p for p in extra_names(prefix, install) if not p.startswith(f"drive_c/{GAME_DIR}/")]
    problems += [f"game copy: {p}" for p in verify_game_copy(game, install)]
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
