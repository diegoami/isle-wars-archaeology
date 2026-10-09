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

T48 (#149) widens it: two emitters wrote `linux-wsl2/wine-xvfb-xfwm4` instead of the carve-out's
token, so constraint F never saw their records and their `start_state.sha256` is a prefix listing's
hash, not the binary's. Records are immutable (rule 20), so those records are listed, not rewritten:
any record whose platform names `wine` in any case and is not a recognised carve-out platform passes
only when its own repo-relative path and its own file sha256 are the ones
`tools/legacy_wine_records.txt` holds. The list never grows; a new Wine record uses a recognised
carve-out platform and is checked against F019 instead. A platform that names no `wine`
(for example `windows-native-bandicam`) is not this gate's business, as before.

T48 round 2 (Sol's R1 and R2 on PR #151) closes three ways around that classification. A platform
the gate cannot classify in plain ASCII (fullwidth `ＷＩＮＥ`, the dotted capital `İ`, a Cyrillic
look-alike, a zero-width space, an ASCII control character) is refused outright, before any
classification: fail closed, never "no wine". The gate reads every tracked JSON document whose
top-level `schema` is `run/1`, wherever it lives, as well as every `runs/**/*.json`, so a record
cannot leave the gate's walk by moving. And a symlink under `runs/` (file or directory), or `runs/`
itself being one, is refused by name instead of being silently skipped or followed.

Exit 0 clean, 1 not.
"""
import argparse
import hashlib
import json
import os
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

# T48 (#149): the records that named `linux-wsl2/wine-xvfb-xfwm4` before the carve-out's token was
# written into their emitters. They are immutable (rule 20), so they are listed here, one line each,
# as `<file sha256>  <repo-relative path>`, and a legacy record passes only on its exact path *and*
# its exact bytes. The list never grows: a new Wine record uses a recognised carve-out platform.
LEGACY_LIST = Path("tools") / "legacy_wine_records.txt"
LEGACY_LIST_TEXT = LEGACY_LIST.as_posix()
SHA256_LINE = re.compile(r"^([0-9a-f]{64})  (\S.*)$")

F019_FINDING = ("findings", "F019-pro-setup-rules.md")
F019_SECTION = re.compile(r"^## Known-good binary hashes\s*$", re.M)
F019_COLUMNS = ("set", "variant", "file", "sha256", "install_path", "signed_on")


def repo_root():
    """The git top level, as this script has always found it."""
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())


def tracked_files(root):
    """Every path git tracks under `root`, as `git ls-files -z` lists it (empty names included)."""
    return subprocess.check_output(["git", "ls-files", "-z"], cwd=root, text=True).split("\0")


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


def legacy_wine_entries(root):
    """{repo-relative path: file sha256} from tools/legacy_wine_records.txt; {} when it is absent.

    The list holds one `<file sha256>  <repo-relative path>` line per legacy record (#149). A line
    that is not of that shape lists nothing, so an absent or malformed list refuses every legacy
    record: fail closed, never pass one because the list could not be read. A path listed twice
    keeps its first line; this repository's list is asserted to hold 274 distinct paths, each with
    its file's sha256, by tools/tests/test_check_no_originals.py.
    """
    path = root / LEGACY_LIST
    if not path.is_file():
        return {}
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = SHA256_LINE.fullmatch(line)
        if match:
            entries.setdefault(match.group(2), match.group(1))
    return entries


def legacy_listing(root, path, rel, entries):
    """Whether tools/legacy_wine_records.txt lists this record with these bytes, and why not.

    `(listed, reason)`: `listed` is True only for an exact path match whose file sha256 is the one
    listed. Never a prefix, never a name alone: a copy of a listed record at another path is not
    listed, and a listed record whose bytes changed is not the record that was listed (Sol's R1 in
    T36). Only a listed path is hashed, so an unlisted record costs a dict lookup.
    """
    listed = entries.get(rel)
    if listed is None:
        return False, f"its path {rel} is not listed in {LEGACY_LIST_TEXT}"
    got = sha256_file(path)
    if got != listed:
        return False, (f"{LEGACY_LIST_TEXT} lists sha256 {listed} for {rel} but the file's sha256 "
                       f"is {got}, so it is not the record that was listed")
    return True, ""


def plain_ascii(platform):
    """True only for a platform made of printable ASCII (space to `~`).

    `.lower()` and a substring test cannot see `wine` in `ＷＩＮＥ`, `WİNE`, `wіne` (Cyrillic i)
    or `wi\u200bne`, and no normalisation is trusted to catch every look-alike, so anything outside
    printable ASCII is refused before the gate classifies the platform (Sol's R1, PR #151). Every
    platform the repository's records carry is plain ASCII.
    """
    return all(" " <= ch <= "~" for ch in platform)


def check_wine_gate(record, f019_table, legacy_ok=False, legacy_reason=""):
    """Constraint F: decide one run record against the F019 known-good table.

    Returns `(problem, warning)`. `problem` is `""` when the record passes and `warning` is
    always `""` today: the signature leaves room for a non-fatal note without changing callers.

    Three kinds of record, decided in this order.

    1. A `runtime.platform` that is not a string, or that names no `wine` in any case
       (`windows-native-bandicam`), always passes, whatever its hash: the existing no-originals
       checks do the rest.
    2. A platform that starts with `wine-on-user-machine` (case-sensitively) is the carve-out's.
       A suffix the task file does not name is refused by name before any hash is considered —
       `wine-on-user-machine-iwp-2.0` passes this step, `wine-on-user-machine-evil-suffix` does
       not — and a recognised one passes only on an exact
       `(artifact.set, artifact.variant, start_state.sha256)` row, with the all-zero placeholder
       T28 used for "no save file" refused by name.
    3. Any other platform that names `wine` in any case (`linux-wsl2/wine-xvfb-xfwm4`, `WINE`,
       `Wine-On-User-Machine`) is a legacy record (#149): it passes only when `legacy_ok` says its
       own path and its own bytes are the ones tools/legacy_wine_records.txt lists, and
       `legacy_reason` then names why it does not when it does not. `legacy_ok` defaults to False,
       so a caller that supplies no listing refuses such a record.

    The function reads the record and never mutates it (rule 20).
    """
    runtime = record.get("runtime") or {}
    platform = runtime.get("platform")
    if not isinstance(platform, str):
        return "", ""
    if not plain_ascii(platform):
        return (
            f"{WINE_GATE_CODE} record carries the platform {platform!r}, which is not plain printable "
            f"ASCII, so the gate cannot tell whether it names wine (a Unicode look-alike, a "
            f"fullwidth or dotted letter, an invisible or control character); a run record's "
            f"platform is plain ASCII (T48, #149)",
            "",
        )
    if not platform.startswith(WINE_PLATFORM_PREFIX):
        if "wine" not in platform.lower():          # in any case: `WINE`, `x-Wine-y`, never a prefix
            return "", ""
        if legacy_ok:
            return "", ""
        reason = legacy_reason or (f"its path is not listed in {LEGACY_LIST_TEXT} with the file's "
                                   f"sha256")
        return (
            f"{WINE_GATE_CODE} record carries the legacy Wine platform {platform!r}, which is not "
            f"the carve-out platform: {reason}; {LEGACY_LIST_TEXT} never grows (#149), so a new "
            f"Wine record uses {WINE_PLATFORM_PREFIX!r} and is checked against F019 instead",
            "",
        )
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


def runs_symlinks(root):
    """Every symlink under `runs/` (file or directory, `runs/` itself included), sorted, as paths.

    `rglob` does not descend into a symlinked directory and `is_file()` follows a symlinked file, so
    a link could hide a record from the gate or point it at bytes outside the repository (Sol's R2,
    PR #151). Run records are regular files under real directories, so every link is refused by
    name; none is followed. The walk never follows a link, so it cannot loop.
    """
    runs = root / "runs"
    if runs.is_symlink():
        return [runs]
    if not runs.is_dir():
        return []
    links = []
    for dirpath, dirnames, filenames in os.walk(runs, followlinks=False):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            if path.is_symlink():
                links.append(path)
    return sorted(links)


def tracked_run_documents(root, tracked):
    """Every tracked `*.json` outside `runs/` whose top-level `schema` is `run/1`, sorted.

    The gate must not depend on where a record lives (Sol's R2, PR #151): a run/1 document moved out
    of `runs/` is gated exactly like one inside it. A tracked symlink is not read here; it is
    returned so the gate refuses it (a link could point at a record outside the repository). The
    format examples under `formats/examples/` are run/1 documents too; they name no `wine`, so the
    gate passes them, as it would anywhere.
    """
    docs = []
    for name in filter(None, tracked):
        if name.startswith("runs/") or not name.lower().endswith(".json"):
            continue
        path = root / name
        if path.is_symlink():
            docs.append(path)
            continue
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            continue   # an oversized file is check_files' finding
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(doc, dict) and doc.get("schema") == "run/1":
            docs.append(path)
    return sorted(docs)


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


def wine_gate_problems(root, tracked=None):
    """One problem line per committed run record that constraint F refuses.

    Each record is decided with the listing in hand: `legacy_ok` is True only for a record whose
    path and file sha256 are the ones tools/legacy_wine_records.txt holds, so a legacy record is
    refused (naming its path and the reason) unless it is listed unchanged. Carve-out records are
    decided against F019's table, as T36 wrote it, and are never rescued by the listing.
    """
    table = load_f019_table(root)
    entries = legacy_wine_entries(root)
    problems = []
    for link in runs_symlinks(root):
        rel = link.relative_to(root).as_posix()
        problems.append(f"{rel}: {WINE_GATE_CODE} a symlink under runs/; run records are regular files "
                        f"under real directories, and the gate neither follows nor skips a link")
    linked = set(runs_symlinks(root))
    if tracked is None:
        tracked = tracked_files(root)
    others = tracked_run_documents(root, tracked)
    for path in sorted(set(run_records(root)) | set(others)):
        if path.is_symlink() or any(parent in linked for parent in path.parents):
            if path not in linked:
                rel = path.relative_to(root).as_posix()
                problems.append(f"{rel}: {WINE_GATE_CODE} a run/1 document that is a symlink; the gate "
                                f"neither follows nor skips a link")
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue  # a malformed record is the run validator's finding, not this gate's
        if not isinstance(record, dict):
            continue
        rel = path.relative_to(root).as_posix()
        listed, why_not = legacy_listing(root, path, rel, entries)
        problem, _warning = check_wine_gate(record, table, legacy_ok=listed, legacy_reason=why_not)
        if problem:
            problems.append(f"{rel}: {problem}")
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
    tracked = tracked_files(root)
    problems = check_files(root, tracked)
    if not args.no_wine_gate:
        problems.extend(wine_gate_problems(root, tracked))
    print("\n".join(problems) if problems else f"no original files tracked ({len(tracked) - 1} files checked)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
