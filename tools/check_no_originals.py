#!/usr/bin/env python3
"""Fail if a tracked file looks like an original game file, or is too large to be anything but one.

CLAUDE.md rule 18 (U2): original game files and patched builds never enter this repository. A
.gitignore can be bypassed with `git add -f`, so CI checks what is actually tracked. That means a
tracked file is a problem if its extension is an original-file or evidence-media type, if it is
larger than any source file should be, or if its bytes are one of the artifact sets registered by
hash in artifacts/known.json.

Constraint F of the rule 18 carve-out (CLAUDE.md, 2026-10-08) adds a second check. The carve-out
lets a model agent run the original Pro binary under Wine on the user's machine, and permits a run
record that says so only when the binary is the F019-known one: a record whose `runtime.platform`
is `wine-on-user-machine` or one of the recognised `wine-on-user-machine-<suffix>` variants the
task file names (`RECOGNISED_WINE_SUFFIXES`) is allowed iff its `start_state.sha256` is the
known-good `Islepro.exe` hash for the `artifact.set` and `artifact.variant` the record names, as
`findings/F019-pro-setup-rules.md` pins them. A platform that starts with the prefix but carries
an unrecognised suffix is refused by name. `--no-wine-gate` skips that check for local
development; CI never sets the flag.

Exit 0 clean, 1 not.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PATTERN = re.compile(r"\.(exe|com|dll|ovl|hlp|cnt|zip|iso|img|vhd|x32|sav|png|mp4|wav)$", re.IGNORECASE)
MAX_BYTES = 1024 * 1024

# Constraint F. The prefix is matched case-sensitively: `Wine-On-User-Machine` is not the
# carve-out platform and must not slip past the gate. The same contract is pinned on the row
# side by experiments/E017-pro-setup-reading/check_known_good_hashes.py (`WINE_PREFIX`).
WINE_PLATFORM_PREFIX = "wine-on-user-machine"
# Constraint C of the carve-out allows `wine-on-user-machine` or "a more specific token the task
# file names". T36 names exactly one, `wine-on-user-machine-iwp-2.0`; every legitimate variant is
# listed here so no other suffix passes. The list is matched exactly, never by prefix:
# `wine-on-user-machine-iwp-2.0-evil-suffix` *starts with* a recognised platform but is not one,
# and is refused (the case that let Sol's `==` mutation through before the suffix was checked).
# Add a suffix here when a future task file names another legitimate platform; the mutation tests
# in tools/tests/test_check_no_originals.py pin the contract this list expresses.
RECOGNISED_WINE_SUFFIXES = ("-iwp-2.0",)
PLACEHOLDER_SHA256 = "0" * 64
# The brief's `[E0XX]` placeholder, filled with the task's number (T36 -> E036).
WINE_GATE_CODE = "[E036]"

F019_FINDING = ("findings", "F019-pro-setup-rules.md")
F019_SECTION = re.compile(r"^## Known-good binary hashes\s*$", re.M)
F019_COLUMNS = ("set", "variant", "file", "sha256", "install_path", "signed_on")


def repo_root():
    """The git top level, as this script has always found it."""
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())


def known_hashes(root):
    """Every file hash of every artifact set in artifacts/known.json."""
    known = root / "artifacts" / "known.json"
    if not known.is_file():
        return set()
    hashes = set()
    for entry in json.loads(known.read_text(encoding="utf-8")).get("sets", []):
        for record in entry.get("manifest", {}).get("files", []):
            if isinstance(record.get("sha256"), str):
                hashes.add(record["sha256"])
    return hashes


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_f019_table(root):
    """The rows of F019's "Known-good binary hashes" table, as dicts, [] when absent.

    An absent finding or section yields no rows, so every `wine-on-user-machine` record is
    refused: the gate fails closed, never passing a record because the table could not be read.
    Each row is `{set, variant, file, sha256, install_path, signed_on}` with backticks stripped.
    """
    finding = root.joinpath(*F019_FINDING)
    if not finding.is_file():
        return []
    text = finding.read_text(encoding="utf-8")
    match = F019_SECTION.search(text)
    if not match:
        return []
    section = text[match.end():]
    nxt = re.search(r"^## ", section, re.M)
    if nxt:
        section = section[:nxt.start()]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):  # separator row
            continue
        if cells and cells[0].lower() == "set":  # header row
            continue
        if len(cells) != len(F019_COLUMNS):  # a reshaped row is the row contract's finding
            continue
        rows.append(dict(zip(F019_COLUMNS, (c.strip("`") for c in cells))))
    return rows


def _record_key(record):
    """(set, variant, sha256) as the run/1 record holds them; None where a field is absent."""
    artifact = record.get("artifact") or {}
    start_state = record.get("start_state") or {}
    return artifact.get("set"), artifact.get("variant"), start_state.get("sha256")


def _rows_text(rows):
    if not rows:
        return "no row (the F019 table is empty or missing)"
    return "; ".join(
        f"set={r.get('set')!r} variant={r.get('variant')!r} sha256={r.get('sha256')!r}"
        for r in rows
    )


def recognised_wine_platform(platform):
    """True only for `wine-on-user-machine` and `wine-on-user-machine<recognised suffix>`.

    The match is exact, not a prefix: a platform that merely starts with a recognised one
    (`wine-on-user-machine-iwp-2.0-evil-suffix`) is *not* recognised and must be refused. The
    task file names the more specific tokens (constraint C); `RECOGNISED_WINE_SUFFIXES` holds
    them, so this is the single place the recognised list is applied.
    """
    return platform == WINE_PLATFORM_PREFIX or any(
        platform == WINE_PLATFORM_PREFIX + suffix for suffix in RECOGNISED_WINE_SUFFIXES
    )


def check_wine_gate(record, f019_table):
    """Constraint F: decide one run record against the F019 known-good table.

    Returns `(problem, warning)`. `problem` is `""` when the record passes and `warning` is
    always `""` today: the signature leaves room for a non-fatal note without changing callers.

    A record whose `runtime.platform` does not start with `wine-on-user-machine` (case-
    sensitively) always passes, whatever its hash: the existing no-originals checks do the rest.
    A `wine-on-user-machine` record whose suffix is not one the task file names is refused by
    name, before any hash is considered — `wine-on-user-machine-iwp-2.0` passes this step,
    `wine-on-user-machine-evil-suffix` does not. A recognised record then passes only on an
    exact `(artifact.set, artifact.variant, start_state.sha256)` row. The all-zero placeholder
    T28 used for "no save file" is refused by name. The function reads the record and never
    mutates it (rule 20).
    """
    runtime = record.get("runtime") or {}
    platform = runtime.get("platform")
    if not isinstance(platform, str) or not platform.startswith(WINE_PLATFORM_PREFIX):
        return "", ""
    if not recognised_wine_platform(platform):
        suffix = platform[len(WINE_PLATFORM_PREFIX):]
        return (
            f"{WINE_GATE_CODE} wine-on-user-machine record uses the unrecognised platform "
            f"{platform!r}: suffix {suffix!r} is not one of the recognised suffixes "
            f"{list(RECOGNISED_WINE_SUFFIXES)!r}; expected {WINE_PLATFORM_PREFIX!r} or "
            f"{WINE_PLATFORM_PREFIX!r} plus a recognised suffix",
            "",
        )
    set_id, variant, sha = _record_key(record)
    got = f"set={set_id!r} variant={variant!r} sha256={sha!r}"
    if sha == PLACEHOLDER_SHA256:
        return (
            f"{WINE_GATE_CODE} wine-on-user-machine record carries the all-zero placeholder "
            f"start_state.sha256 {PLACEHOLDER_SHA256}; got {got}",
            "",
        )
    for row in f019_table:
        if row.get("set") == set_id and row.get("variant") == variant and row.get("sha256") == sha:
            return "", ""
    hash_rows = [r for r in f019_table if r.get("sha256") == sha]
    if hash_rows:
        row = hash_rows[0]
        return (
            f"{WINE_GATE_CODE} wine-on-user-machine record {got} matches F019 row "
            f"set={row.get('set')!r} variant={row.get('variant')!r} by sha256 but not by "
            f"set+variant",
            "",
        )
    return (
        f"{WINE_GATE_CODE} wine-on-user-machine record {got} is not in the F019 known-good "
        f"table; expected {_rows_text(f019_table)}",
        "",
    )


def run_records(root):
    """Every committed run record, `runs/**/*.json`, sorted."""
    runs = root / "runs"
    if not runs.is_dir():
        return []
    return sorted(p for p in runs.rglob("*.json") if p.is_file())


def check_files(root, tracked):
    """The original no-originals file checks, in their original order and wording."""
    registered = known_hashes(root)
    problems = []
    for name in filter(None, tracked):
        path = root / name
        if PATTERN.search(name) or name.startswith("originals/"):
            problems.append(f"{name}: an original-file or evidence-media type; it belongs on the user's machine or in a release")
        elif path.is_file() and path.stat().st_size > MAX_BYTES:
            problems.append(f"{name}: {path.stat().st_size} bytes, over {MAX_BYTES}; nothing here should be that large")
        elif registered and path.is_file() and sha256_file(path) in registered:
            problems.append(f"{name}: sha256 is in artifacts/known.json; the bytes of a registered artifact never enter this repository")
    return problems


def wine_gate_problems(root):
    """One problem line per committed run record that constraint F refuses."""
    table = load_f019_table(root)
    problems = []
    for path in run_records(root):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue  # a malformed record is the run validator's finding, not this gate's
        if not isinstance(record, dict):
            continue
        problem, _warning = check_wine_gate(record, table)
        if problem:
            problems.append(f"{path.relative_to(root).as_posix()}: {problem}")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--no-wine-gate",
        action="store_true",
        help="skip constraint F (local development only; CI never sets it)",
    )
    args = parser.parse_args(argv)
    root = repo_root()
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root, text=True).split("\0")
    problems = check_files(root, tracked)
    if not args.no_wine_gate:
        problems.extend(wine_gate_problems(root))
    print("\n".join(problems) if problems else f"no original files tracked ({len(tracked) - 1} files checked)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
