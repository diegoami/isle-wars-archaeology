"""E020's sitting directory: its one confined root, its layout, the binary's identity and
`sitting.json` (T38; rule 18 carve-out, constraints A and C).

The root is exactly `/mnt/c/Temp/iwp-shots/wine` (the task file's Owns). There is no option to
put a sitting anywhere else (T38 round 2, R4): `confine_root` refuses any other path, a path with
a link on it, a path inside a checkout or this repository, and a path that overlaps the install,
the prefix, its baseline or the bundles. A sitting directory is created new, below the root,
without following a link (setup/iwp/safeio.py), and a sitting that finds its directory already
there stops before anything is launched.

The binary's identity is measured, never assumed (R3): before the launch, the install's and the
run copy's `Islepro.exe` are hashed in place, and the sitting starts only when both equal the
F019 known-good row's sha256. `sitting.json` keeps that measurement with the session's own status,
its start and end times, the versions, the commit that ran and the sha256 of the block file; the
export reads all of it from there (e020_export.py) and supplies none of it itself.
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _sub in ("setup/iwp", "tools"):
    if str(ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(ROOT / _sub))
import locations  # noqa: E402
import safeio  # noqa: E402

EXPERIMENT = "E020"
PLATFORM = "wine-on-user-machine-iwp-2.0"
SET_ID = "iwp-2.0-996e86c5"
VARIANT = "unregistered"
SITTING_ROOT = Path("/mnt/c/Temp/iwp-shots/wine")
SITTING_ID = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")
SITTING_SCHEMA = "e020-sitting/1"
STATUS = re.compile(r"^(completed|aborted: .+)$")
TIME = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


class SittingRefused(SystemExit):
    """The sitting (or its export) is refused; nothing was launched or written."""


def confine_root(root=SITTING_ROOT, prescribed=SITTING_ROOT, others=()):
    """The sitting root as a canonical Path; SittingRefused unless it is exactly the prescribed one,
    with no link anywhere on it, outside every checkout and this repository, and overlapping none
    of `others` ((name, canonical path) pairs: the install, the prefix, its baseline, the bundles).
    `prescribed` is a parameter for the tests only; the launcher never passes it."""
    root, prescribed = Path(root), Path(prescribed)
    if root != prescribed:
        raise SittingRefused(f"the sitting root is {prescribed} and nothing else (constraint A); "
                             "nothing was started")
    if not root.is_absolute() or any(part in ("..", ".") for part in root.parts):
        raise SittingRefused("the sitting root must be a canonical absolute path; nothing was started")
    if Path(os.path.realpath(root)) != root:
        raise SittingRefused("the sitting root has a link on its path; nothing was started")
    try:
        return locations.confine("the E020 sitting root", str(root), others)
    except SystemExit as exc:
        raise SittingRefused(f"{exc}; nothing was started") from None


def sitting_paths(root, sid):
    """Every path of one sitting directory (constraint A's layout)."""
    sitting = Path(root) / sid
    return {
        "root": sitting,
        "frames": sitting / "frames",
        "dumps": sitting / "dumps",
        "session": sitting / "session",
        "index": sitting / "frames-index.jsonl",
        "actions": sitting / "actions.jsonl",
        "log": sitting / "watcher.log",
        "sitting_json": sitting / "sitting.json",
        "readings": sitting / "readings.jsonl",
    }


def create_sitting(root, sid):
    """Create the sitting directory and its sub-directories, new, without following a link; the
    paths. SittingRefused when the id is not a sitting id or the directory exists already."""
    if not SITTING_ID.fullmatch(sid):
        raise SittingRefused(f"{sid!r} is not a sitting id (YYYYMMDDTHHMMSSZ)")
    root = Path(root)
    paths = sitting_paths(root, sid)
    if os.path.lexists(paths["root"]):
        raise SittingRefused(f"the sitting directory {sid} exists already; a sitting is never written over")
    try:
        os.close(safeio.open_directory(paths["root"], create_below=root.parent))
        for key in ("frames", "dumps", "session"):
            safeio.make_directory(paths["root"], key)
    except (safeio.Refused, OSError) as exc:
        raise SittingRefused(f"the sitting directory could not be created: {exc}") from None
    if Path(os.path.realpath(paths["root"])) != paths["root"]:
        raise SittingRefused("the sitting directory is reached through a link")
    return paths


def sha256_of(path):
    """sha256 of a regular file read in place, its own name never followed (safeio.open_source)."""
    digest = hashlib.sha256()
    with safeio.open_source(path) as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def binary_identity(install, prefix, row):
    """The binary's identity, measured: the install's file and the run copy's (the prefix's game copy,
    drive_c/iwp) hashed in place. SittingRefused unless both equal the F019 row's sha256."""
    found = {}
    for where, path in (("install", Path(install) / row["file"]),
                        ("run copy", Path(prefix) / "drive_c" / "iwp" / row["file"])):
        try:
            found[where] = sha256_of(path)
        except (safeio.Refused, OSError) as exc:
            raise SittingRefused(f"the {where}'s {row['file']} could not be hashed: {exc}; nothing was started")
        if found[where] != row["sha256"]:
            raise SittingRefused(f"the {where}'s {row['file']} is not the F019 row's binary "
                                 f"({row['set']}/{row['variant']}); nothing was started")
    return {"file": row["file"], "sha256": row["sha256"], "measured": ["install", "run copy"]}


def write_sitting_json(paths, doc):
    """sitting.json, new (never written over)."""
    safeio.write_file(paths["root"], "sitting.json", data=(json.dumps(doc, indent=2, sort_keys=True) + "\n").encode(),
                      exist="new")


def sitting_problems(doc, sid, batch):
    """Why a sitting.json is not the proof of a sitting the export needs; [] when it is."""
    if not isinstance(doc, dict):
        return ["sitting.json is not an object"]
    problems = []
    expect = {"schema": SITTING_SCHEMA, "sitting_id": sid, "batch": batch, "platform": PLATFORM,
              "set": SET_ID, "variant": VARIANT}
    for key, value in expect.items():
        if doc.get(key) != value:
            problems.append(f"sitting.json {key} is {doc.get(key)!r}, not {value!r}")
    if not isinstance(doc.get("status"), str) or not STATUS.fullmatch(doc["status"]):
        problems.append("sitting.json carries no session status (completed or aborted: <reason>)")
    for key in ("started", "ended"):
        if not isinstance(doc.get(key), str) or not TIME.fullmatch(doc[key]):
            problems.append(f"sitting.json {key} is not the session's wall time")
    binary = doc.get("binary")
    if not isinstance(binary, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(binary.get("sha256", ""))) \
            or binary.get("measured") != ["install", "run copy"]:
        problems.append("sitting.json carries no measured binary identity")
    if not re.fullmatch(r"[0-9a-f]{7,40}", str(doc.get("driver_commit", ""))):
        problems.append("sitting.json carries no driver commit")
    if not re.fullmatch(r"[0-9a-f]{64}", str(doc.get("blocks_sha256", ""))):
        problems.append("sitting.json carries no block-file sha256")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(doc.get("machine", ""))):
        problems.append("sitting.json carries no machine id")
    if not isinstance(doc.get("versions"), dict):
        problems.append("sitting.json carries no versions")
    if not isinstance(doc.get("argv"), list) or not all(isinstance(a, str) for a in doc["argv"]):
        problems.append("sitting.json carries no argv")
    return problems
