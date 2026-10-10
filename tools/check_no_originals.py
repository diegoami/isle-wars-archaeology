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
classification: fail closed, never "no wine". The gate reads every tracked file whose content is a
JSON document with top-level `schema` `run/1`, wherever it lives and whatever its name or encoding
(round 3: not only `*.json`), as well as every file under `runs/` named `.json` in any casing, so a
record cannot leave the gate's walk by moving or by being renamed. And a symlink under `runs/` (file or directory), or `runs/`
itself being one, is refused by name instead of being silently skipped or followed.

T48's structural round (Sol's round-3 R1 and R2, PR #151; the owner's choice, 2026-10-09) closes the
JSON-shape bypasses as a class. Every candidate (each file under `runs/`, each tracked file) is
parsed with `object_pairs_hook`, and a JSON document that repeats a key anywhere is refused, naming
the file and the key, because a reader keeps only one of the values and the gate cannot know which
one another reader sees; the repository's own tracked JSON repeats none (measured 2026-10-09), so
the rule covers every tracked JSON document, not only run/1 candidates. And every JSON object,
anywhere in a parsed value, whose `schema` is `run/1` is gated like a top-level record; a nested
Wine record is refused, since the legacy listing names whole files. The walk is iterative and
bounded (`MAX_JSON_DEPTH`), and a document nested past the bound or past the parser's recursion
limit is refused, never skipped.

T49 (#154, the owner's decision of 2026-10-09) narrows the surface that round left open. T48's gate
looked for `run/1` objects in any tracked JSON, at any depth, under any name, and five review rounds
found ever-rarer shapes that slipped past or crashed it (an explicit `null` skipping the shape
checks, `wi\\u0000ne` hiding behind the escape `json.dumps` writes, a lone surrogate in a diagnostic
raising `UnicodeEncodeError` at `print`). None of those is a record that claims a Wine platform:
they exist because the gate interprets malformed JSON wherever it finds it. So records may live in
one place, and `tests/test_runs.py` already validates that place in CI. A `run/1` object is allowed
at the top level of a lowercase-`.json` file under `runs/`, or at the top level of a file under
`formats/examples/` — and nowhere else. Any other `run/1` object is refused, Wine or not, naming its
path and where it sits, whether it is nested (even inside an allowed file), in a `runs/` file with
another name, or in any other tracked file. Discovery is unchanged — by content, every JSON
encoding, a repeated key refused, the depth bound — it only finds such objects now, to refuse them.
The gate on an allowed record is T48's, unchanged (the F019 row, the legacy listing, a plain-ASCII
platform, no symlink under `runs/`), and it never raises on any shape: an odd shape at an allowed
place is the run validator's to refuse, so the gate either refuses it (when it names `wine`) or
leaves it. Every value a document holds that reaches a diagnostic goes through `esc`, so no input
can make the check crash while printing.

#158 (the owner's decision, 2026-10-10) raises the size limit for two path classes and nothing
else. A run record is one immutable JSON document (rule 20) and cannot be split, and E020's
multi-game sitting E020-r0009 holds a 1,334,538-byte record and a 1,474,068-byte evidence
manifest, so `runs/**/*.json` and `evidence/**/*.manifest.json` may be up to `MAX_RECORD_BYTES`
(8 MB), and every other tracked file keeps `MAX_BYTES`. The gate's size skip applies the same
limit (`size_limit`): a manifest of 1-8 MB now passes check_files, so it is still scanned, and
raising a limit never makes a file skip the wine gate.

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
# #158 (the owner's decision, 2026-10-10): `runs/**/*.json` and `evidence/**/*.manifest.json` —
# and exactly those two path classes — may be up to 8 MB, because a run record is one immutable
# JSON document (rule 20) that cannot be split and E020-r0009's record was 1,334,538 bytes with a
# 1,474,068-byte evidence manifest. Every other tracked file keeps MAX_BYTES; the other checks
# (the originals' extension pattern, artifacts/known.json hashes, the wine gate) are unchanged.
MAX_RECORD_BYTES = 8 * 1024 * 1024

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
# T48 structural round: how deep the gate walks a JSON value for run/1 objects. The repository's
# tracked JSON nests at most 8 levels (measured 2026-10-09); a document past this bound is refused,
# never skipped, so depth cannot hide a record.
MAX_JSON_DEPTH = 64
# The brief's `[E0XX]` placeholder, filled with the task's number (T36 -> E036).
WINE_GATE_CODE = "[E036]"

# T49 (#154): the two places a `run/1` object may live, both compared on the path exactly as `git
# ls-files` lists it. `RECORDS_DIR` and `EXAMPLES_DIR` are prefixes of the path, so `runs.json`,
# `runsx/a.json`, `docs/runs/a.json` and `formats/examples-x/a.json` are not them; `RECORD_SUFFIX`
# is matched case-sensitively, which is what `tests/test_runs.py`'s `rglob("*.json")` reads.
RECORDS_DIR = "runs/"
RECORD_SUFFIX = ".json"
EXAMPLES_DIR = "formats/examples/"
# #158: the second path class that reaches MAX_RECORD_BYTES, compared on the path exactly as git
# lists it: the first path component must be `evidence/` and the suffix exactly `.manifest.json`
# (lowercase), so `evidence-x/`, `evidence/…/x.json` and `x.manifest.json.bak` are not it.
EVIDENCE_DIR = "evidence/"
MANIFEST_SUFFIX = ".manifest.json"

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


def esc(value):
    """A value taken from a document, rendered so printing it can never raise.

    `ascii()` is `repr()` followed by an ASCII encode with backslash escapes: a lone surrogate, a
    NUL, a fullwidth or dotted letter becomes a `\\uXXXX` (or `\\xNN`) escape, so no record can reach
    `print` with a character the stream's encoding refuses (Sol's micro-round R3 on PR #151, which
    raised `UnicodeEncodeError` while printing a diagnostic). An ASCII value is unchanged, so the
    paths and hashes the tests look for still appear verbatim.
    """
    return ascii(value)


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
    artifact = record.get("artifact") if isinstance(record.get("artifact"), dict) else {}
    start_state = record.get("start_state") if isinstance(record.get("start_state"), dict) else {}
    return artifact.get("set"), artifact.get("variant"), start_state.get("sha256")


def _document_strings(value):
    """Every string in a parsed JSON value, its object keys included, in document order.

    The walk is iterative and reads the strings a reader sees, never a re-serialisation of them:
    `json.dumps` escapes a control character as `\\u0000` even with `ensure_ascii=False`, so a check
    on the serialised text cannot see what an escape hides (Sol's micro-round R2, PR #151).
    """
    found = []
    stack = [value]
    while stack:
        node = stack.pop()
        if isinstance(node, str):
            found.append(node)
        elif isinstance(node, dict):
            for key, child in node.items():
                stack.append(key)
                stack.append(child)
        elif isinstance(node, list):
            stack.extend(node)
    return found


def _odd_shape_problem(record, odd):
    """The refusal for a run/1 record whose fields `odd` are not the shapes the gate reads, or "".

    `odd` names fields present with the wrong type (`runtime` not an object, `runtime.platform` not
    a string, ...). The record is refused when its own characters name `wine` in any case, or when an
    odd field's characters are not plain printable ASCII (a look-alike could hide `wine`);
    otherwise it is left to the run validator, which owns malformed records.

    Both tests read the parsed strings (_document_strings), not the fields' JSON text, and every
    value the message shows goes through `esc` (T49, #154): a record sitting where a record may
    live is still this gate's to refuse when it names wine, and no shape can crash the check while
    its refusal is printed.
    """
    names_wine = any("wine" in text.lower() for text in _document_strings(record))
    fields = {}
    not_ascii = []
    for name in odd:
        node = record
        for part in name.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        text = "\n".join(_document_strings(node))
        fields[name] = text
        if not plain_ascii(text):
            not_ascii.append(name)
    if not (names_wine or not_ascii):
        return ""
    shown = ", ".join(f"{name}={esc(text[:80])}" for name, text in fields.items())
    why = ("the record names wine" if names_wine
           else f"{', '.join(not_ascii)} is not plain printable ASCII")
    return (
        f"{WINE_GATE_CODE} run/1 record has field(s) in a shape the gate cannot read ({shown}): "
        f"runtime, artifact and start_state must be objects and runtime.platform a string; {why}, "
        f"so the gate refuses it rather than guess (T48, #149)"
    )


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

    Before any of that, the shapes are checked (T48 micro-round, Sol's structural-round R2): the gate
    walks every nested run/1 object, so `runtime`, `artifact` and `start_state` may be anything. One
    that is present but not an object, or a `runtime.platform` that is present but not a string, is
    refused when the record names `wine` anywhere (any case) or the odd field is not plain ASCII:
    fail closed, never guess what a reader would make of it. Otherwise the record is left to the run
    validator, as before (formats/examples/invalid/ holds such documents on purpose).

    Since T49 (#154) the caller reaches this function only for a record at one of the two places a
    record may live; a `run/1` object anywhere else is refused by the allowlist before its content
    is read. Nothing here raises on any shape, and every value from the record that reaches a
    diagnostic goes through `esc`.

    The function reads the record and never mutates it (rule 20).
    """
    odd = [name for name in ("runtime", "artifact", "start_state")
           if record.get(name) is not None and not isinstance(record.get(name), dict)]
    runtime = record.get("runtime") if isinstance(record.get("runtime"), dict) else {}
    if runtime.get("platform") is not None and not isinstance(runtime.get("platform"), str):
        odd.append("runtime.platform")
    if odd:
        problem = _odd_shape_problem(record, odd)
        if problem:
            return problem, ""
    platform = runtime.get("platform")
    if not isinstance(platform, str):
        return "", ""
    if not plain_ascii(platform):
        return (
            f"{WINE_GATE_CODE} record carries the platform {esc(platform)}, which is not plain "
            f"printable ASCII, so the gate cannot tell whether it names wine (a Unicode look-alike, "
            f"a fullwidth or dotted letter, an invisible or control character); a run record's "
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
            f"{WINE_GATE_CODE} record carries the legacy Wine platform {esc(platform)}, which is not "
            f"the carve-out platform: {reason}; {LEGACY_LIST_TEXT} never grows (#149), so a new "
            f"Wine record uses {WINE_PLATFORM_PREFIX!r} and is checked against F019 instead",
            "",
        )
    if not recognised_wine_platform(platform):
        suffix = platform[len(WINE_PLATFORM_PREFIX):]
        return (
            f"{WINE_GATE_CODE} wine-on-user-machine record uses the unrecognised platform "
            f"{esc(platform)}: suffix {esc(suffix)} is not one of the recognised suffixes "
            f"{list(RECOGNISED_WINE_SUFFIXES)!r}; expected {WINE_PLATFORM_PREFIX!r} or "
            f"{WINE_PLATFORM_PREFIX!r} plus a recognised suffix",
            "",
        )
    set_id, variant, sha = _record_key(record)
    got = f"set={esc(set_id)} variant={esc(variant)} sha256={esc(sha)}"
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


def scan_json_document(path):
    """`(value, duplicate_keys, too_deep)` for the JSON document in `path`, or None where it is not JSON.

    The bytes go to `json.loads` as they are, so a UTF-8 file with a byte-order mark and a UTF-16 or
    UTF-32 file are read as JSON readers read them, not skipped as undecodable (T48 round 3). A file
    that is not JSON in any of those encodings cannot be read as a run record by anything, so it hides
    nothing from the gate.

    T48 structural round (Sol's round-3 R1, PR #151): every object is parsed through
    `object_pairs_hook`, so a key the document repeats is seen instead of being silently replaced by
    its last value; `duplicate_keys` lists each repeated key, in document order. `too_deep` is True
    when the parser gave up on the nesting (`RecursionError`: a document nested past Python's
    recursion limit); `value` is then None. Such a document cannot be walked for run records, so the
    caller refuses it rather than skip it.

    T48 micro-round (Sol's structural-round R1, PR #151): numbers are kept as their source text
    (`parse_int`, `parse_float`, `parse_constant` all `str`), so a valid document holding an integer
    past Python's digit limit is still parsed and walked; nothing downstream does arithmetic on a
    number. Only a syntax error (`JSONDecodeError`) or bytes in no JSON encoding (`UnicodeDecodeError`)
    mean "not JSON". Any other `ValueError` is a parser limit, not a verdict on the document: `too_deep`
    is then a string naming it, and the caller refuses the document rather than skip it.
    """
    duplicates = []

    def pairs_hook(pairs):
        seen = set()
        for key, _value in pairs:
            if key in seen:
                duplicates.append(key)
            seen.add(key)
        return dict(pairs)

    try:
        data = path.read_bytes()
    except OSError:
        return None
    try:
        value = json.loads(data, object_pairs_hook=pairs_hook, parse_int=str, parse_float=str,
                           parse_constant=str)
        return value, duplicates, False
    except RecursionError:
        return None, duplicates, True
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    except ValueError as exc:
        return None, duplicates, f"the JSON parser gave up on it ({type(exc).__name__}: {str(exc)[:120]})"


def load_json_document(path):
    """The JSON value in `path`, or None where its bytes are not JSON (or nest too deep to parse)."""
    scan = scan_json_document(path)
    return None if scan is None else scan[0]


def run_objects(value):
    """`(found, too_deep)`: every JSON object in `value` whose `schema` is `run/1`, wherever it sits.

    T48 structural round (Sol's round-3 R2, PR #151): a run record wrapped in an array or nested in
    another object is a run record all the same, so the gate walks the whole value, not only its top
    level. `found` holds `(where, record)` pairs in document order, `where` a JSONPath-like location
    (`$` for the top level, `$[0]`, `$["data"][0]`). The walk is iterative and bounded by
    `MAX_JSON_DEPTH`: past it, `too_deep` is True and the caller refuses the document, so nesting can
    neither crash the gate nor hide a record below the bound.

    T49 (#154) turns that walk into the allowlist's discovery: the caller gates an object found here
    only when it sits at the top level of a file `record_place` allows, and refuses every other one.
    """
    found = []
    stack = [(value, "$", 1)]
    while stack:
        node, where, depth = stack.pop()
        if depth > MAX_JSON_DEPTH:
            return found, True
        if isinstance(node, dict):
            if node.get("schema") == "run/1":
                found.append((where, node))
            children = [(child, f"{where}[{json.dumps(key)}]") for key, child in node.items()]
        elif isinstance(node, list):
            children = [(child, f"{where}[{i}]") for i, child in enumerate(node)]
        else:
            continue
        stack.extend((child, at, depth + 1) for child, at in reversed(children))
    return found, False


def gate_candidates(root, tracked):
    """Every file the gate reads, sorted: each file under `runs/` (tracked or not, links included so
    they can be refused) and every tracked path outside it.

    Discovery stays by content (Sol's R2 and round-2 R1, PR #151): each candidate is parsed and
    walked, and every run/1 object found is decided — gated at a place a record may live, refused
    anywhere else (T49, #154) — whatever the JSON around it looks like.
    """
    paths = set()
    runs = root / "runs"
    if runs.is_dir() and not runs.is_symlink():
        paths.update(p for p in runs.rglob("*") if p.is_file() or p.is_symlink())
    for name in filter(None, tracked):
        if not name.startswith("runs/"):
            paths.add(root / name)
    return sorted(paths)


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


def record_place(rel):
    """Whether `rel` (repo-relative, as git lists it) is a file a record may live in (T49, #154).

    Two places only, both compared on the path exactly, never on a basename: the top level of a
    lowercase-`.json` file under `runs/` — the files `tests/test_runs.py` validates — or the top
    level of a file under `formats/examples/`. `RECORDS_DIR` and `EXAMPLES_DIR` are prefixes of the
    path, so `runs.json`, `runsx/a.json`, `docs/runs/a.json` and `formats/examples-x/a.json` are not
    them, and the `.json` test is case-sensitive, as `rglob("*.json")` is.
    """
    return ((rel.startswith(RECORDS_DIR) and rel.endswith(RECORD_SUFFIX))
            or rel.startswith(EXAMPLES_DIR))


def allowlist_refusal(rel, where):
    """The refusal for a `run/1` object that does not sit at one of the two allowed places.

    `where` is the object's location in its file's JSON value (`$` for the top level). The message
    names the path and where the object sits, and no value the document holds: a place outside the
    allowlist is refused whatever the object says, Wine or not (the brief, T49, #154).
    """
    place = rel if where == "$" else f"{rel} at {where}"
    if where == "$":
        return (
            f"{place}: {WINE_GATE_CODE} the top level of this JSON document is gated like a run "
            f"record (T48, #149), and this file is not a place a record may live: a record is the "
            f"top level of a lowercase-.json file under {RECORDS_DIR} (what tests/test_runs.py "
            f"validates), or the top level of a file under {EXAMPLES_DIR} (T49, #154)"
        )
    return (
        f"{place}: {WINE_GATE_CODE} a run/1 object nested inside a JSON value; a record lives only "
        f"at the top level of a lowercase-.json file under {RECORDS_DIR}, or the top level of a "
        f"file under {EXAMPLES_DIR}, so a nested object is refused wherever it sits and whatever "
        f"the file is named (T49, #154)"
    )


def size_limit(name):
    """The byte limit check_files applies to the tracked path `name`, as git lists it.

    #158 (the owner's decision, 2026-10-10): exactly two path classes reach MAX_RECORD_BYTES — a
    lowercase-`.json` file whose first path component is `runs/`, and a `.manifest.json` file
    whose first path component is `evidence/`. Both are compared on the path exactly, never on a
    basename: `runsx/`, `docs/runs/` and `evidence-x/` are not them (a `RECORDS_DIR` or
    `EVIDENCE_DIR` prefix pins the first path component), `.JSON` is not `.json` (the case
    `tests/test_runs.py`'s `rglob("*.json")` reads), and `evidence/…/x.json` is a file, not a
    manifest. Every other tracked file keeps MAX_BYTES.
    """
    if name.startswith(RECORDS_DIR) and name.endswith(RECORD_SUFFIX):
        return MAX_RECORD_BYTES
    if name.startswith(EVIDENCE_DIR) and name.endswith(MANIFEST_SUFFIX):
        return MAX_RECORD_BYTES
    return MAX_BYTES


def check_files(root, tracked):
    """The original no-originals file checks, in their original order and wording."""
    registered = known_hashes(root)
    problems = []
    for name in filter(None, tracked):
        path = root / name
        limit = size_limit(name)
        if PATTERN.search(name) or name.startswith("originals/"):
            problems.append(f"{name}: an original-file or evidence-media type; it belongs on the user's machine or in a release")
        elif path.is_file() and path.stat().st_size > limit:
            problems.append(f"{name}: {path.stat().st_size} bytes, over {limit}; nothing here should be that large")
        elif registered and path.is_file() and sha256_file(path) in registered:
            problems.append(f"{name}: sha256 is in artifacts/known.json; the bytes of a registered artifact never enter this repository")
    return problems


def wine_gate_problems(root, tracked=None):
    """One problem line per committed run record that constraint F, and T49's allowlist, refuse.

    The allowlist decides first (T49, #154): a `run/1` object may sit only at the top level of a
    file `record_place` allows, and any other one is refused, Wine or not, naming its path and
    where it sits. Discovery is T48's — by content, every JSON encoding, a repeated key refused, the
    depth bound — and now only finds such objects, to refuse them.

    A record at an allowed place is then decided with the listing in hand: `legacy_ok` is True only
    for a record whose path and file sha256 are the ones tools/legacy_wine_records.txt holds, so a
    legacy record is refused (naming its path and the reason) unless it is listed unchanged.
    Carve-out records are decided against F019's table, as T36 wrote it, and are never rescued by
    the listing. No input raises: every value a document holds that reaches a diagnostic goes
    through `esc`.
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
    for path in gate_candidates(root, tracked):
        rel = path.relative_to(root).as_posix()
        under_runs = rel.startswith(RECORDS_DIR)
        place = record_place(rel)
        if path.is_symlink() or any(parent in linked for parent in path.parents):
            if path not in linked:
                problems.append(f"{rel}: {WINE_GATE_CODE} a run/1 document that is a symlink; the gate "
                                f"neither follows nor skips a link")
            continue
        if not path.is_file():
            continue
        # #158: the gate skips a file only when it is over the limit `size_limit` gives its path,
        # so check_files refuses it; every file that passes the size check — an evidence manifest
        # of 1-8 MB, now legal — is scanned, and raising a limit never hides a file from the gate.
        # A `runs/` `.json` (any casing, T48 round 3) is scanned whatever its size, as before.
        if (path.stat().st_size > size_limit(rel)
                and not (under_runs and path.suffix.lower() == ".json")):
            continue   # an oversized tracked file is check_files' finding
        scan = scan_json_document(path)
        if scan is None:
            continue   # not JSON: nothing can read a run record from it
        value, duplicates, too_deep = scan
        if duplicates:
            keys = ", ".join(esc(k) for k in dict.fromkeys(duplicates))
            problems.append(f"{rel}: {WINE_GATE_CODE} a JSON document that repeats the key(s) {keys}; "
                            f"a JSON reader keeps one value of a repeated key and drops the other, so "
                            f"the gate refuses the document rather than guess which value a reader sees "
                            f"(T48, #149)")
        found, walk_too_deep = ([], False) if too_deep else run_objects(value)
        if (under_runs and path.suffix.lower() == ".json" and isinstance(value, dict)
                and not any(where == "$" for where, _record in found)):
            # A `*.json` object under runs/ is a run record whatever its `schema` says, as before.
            found.insert(0, ("$", value))
        if isinstance(too_deep, str):
            problems.append(f"{rel}: {WINE_GATE_CODE} a document the gate cannot parse: {esc(too_deep)}; "
                            f"it cannot be walked for run/1 records, so it is refused rather than "
                            f"skipped as not JSON (T48, #149)")
        elif too_deep or walk_too_deep:
            problems.append(f"{rel}: {WINE_GATE_CODE} a JSON document nested deeper than "
                            f"{MAX_JSON_DEPTH} levels; the gate cannot walk it for run/1 records, so "
                            f"it is refused (T48, #149)")
        for where, record in found:
            if where != "$" or not place:
                problems.append(allowlist_refusal(rel, where))
                continue
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
