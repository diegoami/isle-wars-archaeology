#!/usr/bin/env python3
"""The run directory of the iw-dos-runtime profile (W3b): make it, fill it, check it.

Commands (machine-local values come from the environment, never from this file):
    sync    make <IW_DOS_RUN>/game equal to the registered set, copied from IW_DOS_DIR
    check   the run copy is safe to launch from (run_problems): a real directory holding the
            registered set as plain files of its own, and `register_artifact.py check --strict`
            passes on it

    IW_DOS_DIR    the copy of DOS Isle Wars (the extracted archive); read and hashed only
    IW_DOS_RUN    the run directory, outside every checkout and worktree; the game runs from
                  <IW_DOS_RUN>/game, which DOSBox-X mounts as C: and nothing else
    E003_BUNDLES  the local directory for evidence bundles
    E003_EXPLORE  where an --explore run writes its output (optional)

Every location is confined first (setup/iwp/locations.py `confine`, imported as it is on main):
absolute, outside every checkout, not containing this repository, and not overlapping IW_DOS_DIR or
one another. Every write, removal and mode change goes through setup/iwp/safeio.py, so a link or a
second name (a hard link to the copy, say) at a destination loses its name and is never written
through. A run copy file with a second name would defeat the read-only bind of IW_DOS_DIR: the bind
guards a path, and the run's namespace root may write any inode the user owns (T11 resume note).
"""
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "setup" / "iwp"))
import locations  # noqa: E402
import safeio  # noqa: E402

SET_ID = "iw-dos-3.1-30121376"
# The checkout whose artifacts/known.json registers the set: this one (a test points it at its own).
KNOWN_ROOT = ROOT
GAME_DIR = "game"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest(root=None):
    root = KNOWN_ROOT if root is None else root
    known = json.loads((Path(root) / "artifacts" / "known.json").read_text(encoding="utf-8"))
    for entry in known["sets"]:
        if entry["manifest"]["id"] == SET_ID:
            return entry["manifest"]
    raise SystemExit(f"{SET_ID} is not in artifacts/known.json")


def run_locations(env=None, need_run=True, need_bundles=False, explore=False):
    """{name: canonical Path} of IW_DOS_DIR and the confined machine-local locations; SystemExit
    before anything is touched when one is missing or refused."""
    env = os.environ if env is None else env
    found = {}
    if not env.get("IW_DOS_DIR"):
        raise SystemExit("IW_DOS_DIR is not set")
    if not os.path.isabs(env["IW_DOS_DIR"]):
        raise SystemExit("IW_DOS_DIR must be an absolute path")
    found["IW_DOS_DIR"] = locations.real(env["IW_DOS_DIR"])
    seen = [("IW_DOS_DIR", found["IW_DOS_DIR"])]

    def add(name, required):
        if not env.get(name):
            if required:
                raise SystemExit(f"{name} is not set")
            return
        found[name] = locations.confine(name, env[name], seen)
        seen.append((name, found[name]))

    add("IW_DOS_RUN", need_run)
    add("E003_BUNDLES", need_bundles)
    if explore:
        add("E003_EXPLORE", False)
    return found


def install_inodes(install):
    """{(st_dev, st_ino)} of IW_DOS_DIR and every entry in it, links not followed."""
    install = Path(install)
    if not install.is_dir():
        return set()
    found = {(os.lstat(install).st_dev, os.lstat(install).st_ino)}
    for dirpath, dirnames, filenames in os.walk(install, followlinks=False):
        for name in dirnames + filenames:
            info = os.lstat(Path(dirpath) / name)
            found.add((info.st_dev, info.st_ino))
    return found


def mount_points():
    """Canonical mount points of this process's mount namespace (/proc/self/mountinfo)."""
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


def strict_check(game, root=None):
    """(ok, output) of `register_artifact.py check <game> <set> --strict`, run as the tool itself.
    The tool reads artifacts/known.json of the checkout it runs in (KNOWN_ROOT, or `root`)."""
    root = KNOWN_ROOT if root is None else root
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "register_artifact.py"), "check",
                             str(game), SET_ID, "--strict"], capture_output=True, text=True, cwd=root)
    text = (result.stdout + result.stderr).strip()
    return result.returncode == 0, text


def run_problems(run_dir, install, root=None):
    """What is wrong with <run_dir>/game as the C: drive of a run; [] when nothing is. Nothing is
    changed. Checked before every launch, and by the profile."""
    run_dir, install = Path(run_dir), Path(install)
    game = run_dir / GAME_DIR
    if run_dir.is_symlink() or not run_dir.is_dir():
        return ["the run directory is not a real directory"]
    if game.is_symlink() or not game.is_dir():
        return ["the run copy is not a real directory"]
    canonical = locations.real(game)
    if locations.inside(canonical, install) or locations.inside(install, canonical):
        return ["the run copy overlaps IW_DOS_DIR"]
    problems = [f"{(p.relative_to(game).as_posix() if p != game else '.')} is a mount point"
                for p in mount_points() if locations.inside(p, canonical)]
    if os.lstat(game).st_dev != os.lstat(run_dir).st_dev:
        problems.append(". is on another filesystem than the run directory")
    if problems:
        return problems                         # nothing under another place is looked into
    theirs = install_inodes(install)
    for dirpath, dirnames, filenames in os.walk(game, followlinks=False):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(game).as_posix()
            info = os.lstat(path)
            if info.st_dev != os.lstat(game).st_dev:
                problems.append(f"{rel} is on another filesystem")
            elif stat.S_ISLNK(info.st_mode):
                problems.append(f"{rel} is a link")
            elif stat.S_ISDIR(info.st_mode):
                problems.append(f"{rel} is a directory; the set has none")
            elif not stat.S_ISREG(info.st_mode):
                problems.append(f"{rel} is a device, fifo or socket")
            elif info.st_nlink != 1:
                whose = "; another is IW_DOS_DIR's" if (info.st_dev, info.st_ino) in theirs else ""
                problems.append(f"{rel} has {info.st_nlink} names (a hard link{whose})")
            elif (info.st_dev, info.st_ino) in theirs:
                problems.append(f"{rel} is one of IW_DOS_DIR's own files")
    if problems:
        return problems
    ok, text = strict_check(game, root)
    if not ok:
        problems.append("register_artifact.py check --strict failed: " + text.replace("\n", "; ")[:300])
    return problems


def sync(env=None, root=None):
    """Make <IW_DOS_RUN>/game the registered set: plain files of its own, copied from IW_DOS_DIR,
    with the copy's modification times, writable (so the game's runtime writes can be measured).
    Idempotent: a file that is already the registered one as a plain file of its own is kept."""
    locs = run_locations(env)
    install, run_dir = locs["IW_DOS_DIR"], locs["IW_DOS_RUN"]
    files = {f["path"]: f for f in manifest(root)["files"]}
    for rel in files:
        if "/" in rel:
            raise SystemExit(f"{rel}: the set has a subdirectory; this profile copies a flat set only")
        safeio.safe_name(rel, "set file")
    for rel, entry in sorted(files.items()):           # everything checked before anything changes
        src = install / rel
        if src.is_symlink() or not src.is_file():
            raise SystemExit(f"{rel}: IW_DOS_DIR has no such regular file; nothing changed")
        if sha256_file(src) != entry["sha256"]:
            raise SystemExit(f"{rel}: IW_DOS_DIR's file is not the registered one; nothing changed")
    game = run_dir / GAME_DIR
    for part in (run_dir, game):
        if part.is_symlink():
            raise SystemExit(f"{part.name} is a link; the run copy must be a real directory")
    copied, removed = [], []
    try:
        os.close(safeio.open_directory(game, create_below=run_dir.parent))
        theirs = install_inodes(install)
        for name in sorted(os.listdir(game)):
            info = os.lstat(game / name)
            own = safeio.plain_file(info) and (info.st_dev, info.st_ino) not in theirs
            if name in files and own:
                continue
            if safeio.remove(game, name):            # a link or a second name loses this name only
                removed.append(name)
        for rel, entry in sorted(files.items()):
            if safeio.sha256_plain(game, rel) == entry["sha256"]:
                continue
            safeio.write_file(game, rel, source=install / rel, exist="replace", mode=0o644,
                              expect_sha256=entry["sha256"], times_from_source=True)
            copied.append(rel)
        for rel in files:
            safeio.set_mode(game, rel, 0o644)
        safeio.set_mode(game, "", 0o755)
    except safeio.Refused as exc:
        raise SystemExit(f"the run copy was not synchronised: {exc}")
    print(f"run copy: copied {len(copied)}, removed {len(removed)}")
    return 0


def check(env=None, root=None):
    locs = run_locations(env)
    problems = run_problems(locs["IW_DOS_RUN"], locs["IW_DOS_DIR"], root)
    if problems:
        print("\n".join(problems))
        return 1
    print("run copy ok")
    return 0


COMMANDS = {"sync": sync, "check": check}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    sys.exit(COMMANDS[sys.argv[1]]())
