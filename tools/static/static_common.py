"""What every static-analysis script (T26) does first: refuse to run unless it can keep what it makes
away from every checkout, and unless the original is the registered one.

CLAUDE.md rule 18 (U2): nothing unpacked, extracted or decompiled from an original ever enters the
repository, a commit, an issue or a comment. So this module holds the three refusals each script
calls before it reads or writes anything:

- `static_root`: `$IWA_STATIC`, where every output derived from an original goes, must be set, an
  absolute path, outside every checkout (no `.git` entry on the way up), not containing this
  repository, and not overlapping the original's own folder. It is checked by
  `setup/iwp/locations.py` `confine`, the same function the runtime profiles use.
- `original`: an original is read in place, never copied, and only when its size and sha256 equal
  its entry in `artifacts/known.json` (the set's manifest, validated by `tools/register_artifact.py`).
  The bytes the caller then uses are the bytes that were hashed.
- `new_run_dir` and `write_new`: every output is a new file in a new directory of its own, written
  through `setup/iwp/safeio.py` (no link followed, never overwritten).
- `inventory`: the sha256 and size of every file a run left in its directory (the tool's own files
  too: a Ghidra database, a listing, a dumped chunk), so that `check_derived_hashes.py` knows each
  one by its bytes, whatever name a copy of it might be given.

`write_record` is the one way a measurement reaches a tracked path: a JSON file under
`experiments/E008-static-triage/measurements/`, new, and refused when its text holds a machine path.
It carries hashes, sizes, counts, addresses and names, and never a line of an original's code.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _sub in ("setup/iwp", "tools"):
    if str(ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(ROOT / _sub))
import locations  # noqa: E402
import register_artifact  # noqa: E402
import safeio  # noqa: E402

# The checkout whose artifacts/known.json registers the sets: this one (a test points it at its own).
KNOWN_ROOT = ROOT
MEASUREMENTS = Path("experiments") / "E008-static-triage" / "measurements"

# key -> (registered set id, the environment variable that names the original's folder, the file)
ORIGINALS = {
    "iw-dos": ("iw-dos-3.1-30121376", "IW_DOS_DIR", "ISLEWAR.EXE"),
    # the set's second executable (PKLITE too; the main program names it among the files it needs)
    "iw-dos-ov6": ("iw-dos-3.1-30121376", "IW_DOS_DIR", "ISLEWAR.OV6"),
    "iwp": ("iwp-2.0-996e86c5", "IWP_DIR", "Islepro.exe"),
}

# A tracked record must name no machine path (Done-when 6 of T26 greps the same shapes).
LEAK = re.compile(r"program files|/mnt/|[A-Za-z]:\\|/home/|\.local/share|/Users/", re.IGNORECASE)


def die(message):
    raise SystemExit(f"static: {message}")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_path(path):
    """sha256 and size of a regular file, its own name not followed."""
    digest = hashlib.sha256()
    size = 0
    with safeio.open_source(path) as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def original_dir(key, env=None):
    env = os.environ if env is None else env
    _, var, _ = ORIGINALS[key]
    value = env.get(var)
    if not value:
        die(f"{var} is not set (the folder that holds the original, read in place)")
    if not os.path.isabs(value):
        die(f"{var} must be an absolute path")
    return locations.real(value)


def static_root(env=None, originals=()):
    """The canonical `$IWA_STATIC`, or SystemExit saying why it is refused.

    `originals` are the keys of the originals the script reads: the root must not overlap their
    folders (a tool run inside one would write next to the original)."""
    env = os.environ if env is None else env
    others = [(ORIGINALS[key][1], original_dir(key, env)) for key in originals]
    try:
        return locations.confine("IWA_STATIC", env.get("IWA_STATIC"), others)
    except SystemExit as exc:
        die(str(exc))


class Original:
    """An original that matched its registered hash: where it is, and its identity."""

    def __init__(self, key, set_id, rel, path, sha256, size):
        self.key, self.set_id, self.rel, self.path = key, set_id, rel, path
        self.sha256, self.size = sha256, size

    def read(self):
        """The bytes, read again and checked against the registered hash (so the bytes a script
        uses are the registered ones, even if the file changed since)."""
        with safeio.open_source(self.path) as fh:
            data = fh.read()
        if sha256_bytes(data) != self.sha256 or len(data) != self.size:
            die(f"{self.rel} changed after it was checked; nothing was read from it")
        return data

    def recheck(self):
        """Used after a tool read the file by its path: still the registered bytes."""
        sha, size = sha256_path(self.path)
        if (sha, size) != (self.sha256, self.size):
            die(f"{self.rel} is not the registered file after the tool ran")


def registered(key, known_root=None):
    """(set id, relative name, registered sha256, registered size) of an original, from the manifest."""
    set_id, _, rel = ORIGINALS[key]
    known_root = KNOWN_ROOT if known_root is None else Path(known_root)
    try:
        known = register_artifact.load_known(known_root / "artifacts" / "known.json")
    except (OSError, ValueError) as exc:
        die(f"artifacts/known.json: {exc}")
    manifest, errors = register_artifact.select_set(known, set_id)
    if manifest is None:
        die("; ".join(errors))
    for record in manifest["files"]:
        if record["path"] == rel:
            return set_id, rel, record["sha256"], record["bytes"]
    die(f"{set_id} lists no {rel}")


def original(key, env=None, known_root=None):
    """The original `key`, in place, when its size and sha256 are the registered ones; SystemExit
    otherwise. Nothing is copied."""
    set_id, rel, sha256, size = registered(key, known_root)
    path = original_dir(key, env) / rel
    try:
        observed_sha, observed_size = sha256_path(path)
    except safeio.Refused as exc:
        die(f"{rel}: {exc}")
    except OSError as exc:
        die(f"{rel} cannot be read: {exc.strerror}")
    if (observed_sha, observed_size) != (sha256, size):
        die(f"{rel} is not the registered file of {set_id} (sha256 {observed_sha}, {observed_size} bytes); "
            "nothing is read from it")
    return Original(key, set_id, rel, path, sha256, size)


SHA256 = re.compile(r"[0-9a-f]{64}")


def derived(root, name, sha256):
    """(path, size) of a file inside the static folder, made by an earlier run (the unpacked executable),
    when its sha256 is the one given; SystemExit otherwise. `name` is relative, without `..`, so the
    file is in the static folder and not an original or a file of a checkout."""
    if not sha256 or not SHA256.fullmatch(sha256):
        die("--file needs --sha256 with 64 lowercase hex digits")
    rel = Path(name)
    if rel.is_absolute() or ".." in rel.parts:
        die("--file is a name inside the static folder, relative and without ..")
    path = Path(root) / rel
    try:
        sha, size = sha256_path(path)
    except (safeio.Refused, OSError) as exc:
        die(f"{name} cannot be read: {exc}")
    if sha != sha256:
        die(f"{name} is not the file with the given sha256 (it is {sha}); nothing was analysed")
    return path, size


def inventory(directory):
    """[{path, sha256, bytes}] for every file under `directory`, sorted by its path relative to it.
    A link is listed as {path, link: true} and never followed (its target is not the run's).
    A folder that cannot be listed stops it (round 2, R1): os.walk would skip it silently, and the
    inventory would look complete without that folder's files."""
    base = Path(directory)
    found = []

    def unlistable(exc):
        where = exc.filename if getattr(exc, "filename", None) else base
        die(f"{anonymise(where)} cannot be listed for the inventory: {exc.strerror or exc}")

    for folder, dirs, files in os.walk(base, followlinks=False, onerror=unlistable):
        here = Path(folder)
        for name in files + [d for d in dirs if (here / d).is_symlink()]:
            path = here / name
            rel = path.relative_to(base).as_posix()
            if path.is_symlink():
                found.append({"path": rel, "link": True})
                continue
            try:
                sha, size = sha256_path(path)
            except (safeio.Refused, OSError) as exc:
                die(f"{rel} cannot be inventoried: {exc}")
            found.append({"path": rel, "sha256": sha, "bytes": size})
    return sorted(found, key=lambda item: item["path"])


def run_id():
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def new_run_dir(root, tool, rid=None):
    """A new, empty directory `<tool>-<run id>` in the canonical static root; refused when it exists."""
    rid = rid or run_id()
    name = f"{safeio.safe_name(tool, 'tool name')}-{safeio.identifier(rid, 'run id')}"
    try:
        safeio.make_directory(root, name)
    except FileExistsError:
        die(f"{name} already exists in the static root; a run never reuses a directory")
    except safeio.Refused as exc:
        die(str(exc))
    return Path(root) / name


def write_new(directory, name, data):
    """A new file in a canonical directory (never overwritten, no link followed)."""
    try:
        safeio.write_file(directory, name, data=data, exist="new")
    except safeio.Refused as exc:
        die(str(exc))


def anonymise(path):
    """A path with the home folder replaced by $HOME, for a record that must hold no machine path."""
    text = str(path)
    home = str(Path.home())
    return "$HOME" + text[len(home):] if text.startswith(home + os.sep) else text


def leaks(text):
    return LEAK.findall(text)


def write_record(name, obj, root=None):
    """Write a measurement under experiments/E008-static-triage/measurements/, as a new file.

    Refused when the text holds anything shaped like a machine path, or when the name exists."""
    root = ROOT if root is None else Path(root)
    text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    found = leaks(text)
    if found:
        die(f"the record {name} would hold a machine path ({found[0]!r}); nothing was written")
    base = locations.real(root)
    try:
        safeio.write_file(base / MEASUREMENTS, name, data=text.encode("ascii"), exist="new",
                          create_below=base)
    except safeio.Refused as exc:
        die(str(exc))
    return MEASUREMENTS / name


def tool_home(env_name, default_parts):
    """A tool's folder: the environment variable, else `$HOME/tools/<default>`."""
    value = os.environ.get(env_name)
    return Path(value) if value else Path.home().joinpath("tools", *default_parts)


def run(cmd, cwd, log_dir, log_name, env=None, timeout=3600):
    """Run a tool, its stdout and stderr in two new files of the run directory (they may hold
    derived text, so they stay in the static root). Returns (exit code, seconds)."""
    out = safeio.create_stream(log_dir, f"{log_name}.out")
    err = safeio.create_stream(log_dir, f"{log_name}.err")
    started = time.monotonic()
    try:
        with out, err:
            proc = subprocess.run([str(c) for c in cmd], cwd=str(cwd), env=env, stdout=out, stderr=err,
                                  timeout=timeout, check=False)
        return proc.returncode, round(time.monotonic() - started, 2)
    except subprocess.TimeoutExpired:
        die(f"{log_name} did not finish in {timeout} s")


def count_lines(path):
    with open(path, "rb") as fh:
        return sum(1 for _ in fh)
