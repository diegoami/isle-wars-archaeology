#!/usr/bin/env python3
"""Register an artifact set by hash, and check a copy against artifacts/known.json.

Artifact identity is the artifact-set/1 rule no schema can express (formats/README.md, "Two rules
no schema can express"): id is ``<label>-<h8>`` where ``<h8>`` is the first 8 hex of the sha256 of
the canonical manifest. The canonical manifest drops ``id`` and ``acquired``, sorts ``files`` by
``path`` and serialises with sorted keys, separators ``(",", ":")``, UTF-8 and no ASCII escaping.

This tool never re-implements that rule: it imports ``validate``, ``semantic_errors`` and
``canonical_set_hash`` from the vendored tests/formats/check_examples.py (ADR-009: copied, not
forked). Only hashes and sizes are written; the bytes stay on the registering machine (U2).

Commands:
    manifest <dir> --label --title --version --how --when [--note]
             [--runtime-write GLOB]... [--exclude GLOB]...
        Print the artifact-set/1 manifest for <dir>. Files matching a runtime_writes glob or an
        --exclude glob are left out of ``files``; --exclude is not recorded.
    check (<dir> | --list <file>) <set-id> [--strict]
        Re-hash <dir> (or read a ``<sha256>  <bytes>  <path>`` listing) and compare it with the
        known.json entry for <set-id>. Exit 1 on any mismatch or missing file. A file outside the
        manifest is printed as ``unlisted: <path>``; that is a failure only with --strict.
    validate
        Check every artifacts/known.json entry against the vendored schema and recompute its id.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "tests" / "formats" / "check_examples.py"
SCHEMA_PATH = ROOT / "formats" / "artifact-set-1.schema.json"


def _load_vendored():
    """Import the vendored check_examples.py as a module (it is not a package)."""
    spec = importlib.util.spec_from_file_location("check_examples_vendored", VENDORED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_vendored = _load_vendored()
validate = _vendored.validate
semantic_errors = _vendored.semantic_errors
canonical_set_hash = _vendored.canonical_set_hash


def repo_root():
    """The repository git says we are in, so a test can drive the tool inside a temp repo."""
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ROOT


def known_path():
    return repo_root() / "artifacts" / "known.json"


def load_known(path=None):
    path = Path(path) if path else known_path()
    if not path.is_file():
        return {"sets": []}
    return json.loads(path.read_text(encoding="utf-8"))


def find_set(known, set_id):
    for entry in known.get("sets", []):
        if entry.get("manifest", {}).get("id") == set_id:
            return entry
    return None


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matches_any(path, patterns):
    return any(fnmatch(path, pattern) for pattern in patterns)


def build_manifest(directory, label, title, version, how, when, note=None,
                   runtime_writes=None, excludes=None):
    """The artifact-set/1 manifest for <directory>, id computed by the vendored canonical rule."""
    directory = Path(directory).resolve()
    runtime_writes = list(runtime_writes or [])
    excludes = list(excludes or [])
    files = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(directory).as_posix()
        if matches_any(rel, runtime_writes) or matches_any(rel, excludes):
            continue
        files.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    acquired = {"how": how, "when": when}
    if note:
        acquired["note"] = note
    manifest = {
        "schema": "artifact-set/1",
        "title": title,
        "version": version,
        "acquired": acquired,
        "files": files,
        "runtime_writes": runtime_writes,
    }
    manifest["id"] = f"{label}-{canonical_set_hash(manifest)[:8]}"
    return manifest


def manifest_errors(manifest):
    schema = load_schema()
    return validate(manifest, schema) + semantic_errors(schema["$id"], manifest)


def hash_tree(directory, manifest):
    """Observed {path: (bytes, sha256)} for the files of <directory>, honouring runtime_writes."""
    directory = Path(directory).resolve()
    runtime_writes = manifest.get("runtime_writes", [])
    observed = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(directory).as_posix()
        if rel not in {f["path"] for f in manifest.get("files", [])} and matches_any(rel, runtime_writes):
            continue
        observed[rel] = (path.stat().st_size, sha256_file(path))
    return observed


def read_listing(path):
    """Parse ``<sha256>  <bytes>  <relative/path>`` lines into {path: (bytes, sha256)}."""
    observed = {}
    problems = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) != 3:
            problems.append(f"line {number}: cannot parse {line!r}")
            continue
        digest, size, rel = parts
        try:
            size = int(size)
        except ValueError:
            problems.append(f"line {number}: bytes {parts[1]!r} is not an integer")
            continue
        observed[rel] = (size, digest.lower())
    return observed, problems


def compare(observed, manifest, strict=False):
    """Problems and unlisted paths for an observed set against a manifest."""
    listed = {f["path"]: (f["bytes"], f["sha256"]) for f in manifest.get("files", [])}
    runtime_writes = manifest.get("runtime_writes", [])
    problems = []
    unlisted = []
    for rel, (size, digest) in sorted(observed.items()):
        if rel in listed:
            want_size, want_digest = listed[rel]
            if size != want_size:
                problems.append(f"{rel}: {size} bytes, expected {want_size}")
            if digest != want_digest:
                problems.append(f"{rel}: sha256 {digest}, expected {want_digest}")
        elif matches_any(rel, runtime_writes):
            continue
        else:
            unlisted.append(rel)
    for rel in sorted(set(listed) - set(observed)):
        problems.append(f"{rel}: missing")
    if strict and unlisted:
        problems.extend(f"unlisted: {rel}" for rel in unlisted)
    return problems, unlisted


def cmd_manifest(args):
    manifest = build_manifest(
        args.directory, args.label, args.title, args.version, args.how, args.when,
        note=args.note, runtime_writes=args.runtime_write, excludes=args.exclude,
    )
    errors = manifest_errors(manifest)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def cmd_check(args):
    if args.list_path:
        set_id = args.source
    else:
        if args.set_id is None:
            print("check needs <set-id> after <dir>", file=sys.stderr)
            return 2
        set_id = args.set_id
    entry = find_set(load_known(), set_id)
    if entry is None:
        print(f"no artifacts/known.json entry for {set_id}", file=sys.stderr)
        return 1
    manifest = entry.get("manifest", {})
    if args.list_path:
        observed, base_problems = read_listing(args.list_path)
    else:
        observed, base_problems = hash_tree(args.source, manifest), []
    compared, unlisted = compare(observed, manifest, strict=args.strict)
    problems = base_problems + compared
    for rel in unlisted:
        print(f"unlisted: {rel}")
    for problem in problems:
        print(problem)
    failed = bool(problems) or (args.strict and bool(unlisted))
    if not failed:
        print(f"ok: {set_id}")
    return 1 if failed else 0


def known_errors(known):
    schema = load_schema()
    problems = []
    for index, entry in enumerate(known.get("sets", [])):
        manifest = entry.get("manifest")
        if not isinstance(manifest, dict):
            problems.append(f"sets[{index}]: no manifest object")
            continue
        errors = validate(manifest, schema) + semantic_errors(schema["$id"], manifest)
        problems.extend(f"sets[{index}] ({manifest.get('id', '?')}): {error}" for error in errors)
    return problems


def cmd_validate(args):
    known = load_known()
    problems = known_errors(known)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print(f"known.json ok ({len(known.get('sets', []))} sets)")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="register_artifact.py", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="print the artifact-set/1 manifest for a directory")
    manifest.add_argument("directory")
    manifest.add_argument("--label", required=True)
    manifest.add_argument("--title", required=True)
    manifest.add_argument("--version", required=True)
    manifest.add_argument("--how", required=True)
    manifest.add_argument("--when", required=True)
    manifest.add_argument("--note")
    manifest.add_argument("--runtime-write", action="append", default=[], metavar="GLOB")
    manifest.add_argument("--exclude", action="append", default=[], metavar="GLOB")
    manifest.set_defaults(func=cmd_manifest)

    check = commands.add_parser("check", help="check a directory or listing against a known set")
    check.add_argument("--list", dest="list_path", metavar="FILE")
    check.add_argument("--strict", action="store_true")
    check.add_argument("source", help="<dir>, or <set-id> when --list is given")
    check.add_argument("set_id", nargs="?", help="<set-id> when a <dir> is given")
    check.set_defaults(func=cmd_check)

    validate_cmd = commands.add_parser("validate", help="validate every artifacts/known.json entry")
    validate_cmd.set_defaults(func=cmd_validate)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check" and not args.list_path and args.set_id is None:
        parser.error("check needs (<dir> | --list <file>) <set-id>")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
