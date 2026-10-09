#!/usr/bin/env python3
"""E019 (T24): the catalogue check.

    python3 experiments/E019-pro-ui/check_ui_catalogue.py

It fails until the walks have run and the catalogue is turned from their records (T39, #117); this
task's own Done-when runs its checks on the recorder's output in tests/test_e019_ui_catalogue.py.

Exits 0 when every piece holds:
- every record under runs/E019/<batch>/, whatever its status, is an E019 run/1 record of its walk's
  artifact set and variant, sits in its walk's batch, has an evidence manifest of the same set that
  names every output by hash, and cites no script or handler outside the E008 inventory;
- every `Q-UI-*` row of questions/pro-static.md and Q-PLY-04 has at least one completed record,
  whose arm names the question;
- every completed record carries the seal (a start_state sha256), every field of
  required_fields() (the walk question, the speed setting, the measured display size, the
  per-question observation, the declared count and, for a proxy, its count note, timings when the
  walk is frame-timed, hit areas for Q-UI-18, the reads its spec names) and the outputs of
  required_outputs(); its observation is the recorder's summary and names only screenshots the
  record holds; its display size was measured equal to the size it asked for;
- a count target is met by one completed record (the row's "at least N <word>" when the row names
  one, else the walk table's), never by adding records; Q-UI-19 has a completed record at every
  display size its walk names;
- findings/F020-pro-ui-observations.md has a section per question with an Observation line whose
  status is one of observed, narrowed, static-only, unestablished (a pending section fails);
- no record's observations, and no F020 section, cites a script or handler that the E008
  inventory does not have (kind, number, name, handler — the same rule
  tools/check_pro_question_map.py enforces for the questions map);
- an F020 section whose status is observed or narrowed cites its evidence (#140, T39 DW2): every
  backticked token holding a record name is one of the two forms F020 uses — the strict full path
  runs/E019/<batch>/E019-r<digits>.json (one path segment, no `..`), which must exist under the
  root being checked and whose sha256 prefix must be a prefix of that file's sha256, or the bare
  file name, which is not checked; anything else is refused — the section cites at least one
  record with its sha, and every hash it cites (backticked lowercase hex immediately followed by
  an ellipsis) is a prefix of the sha256 computed from a record it cites by full path, or of an
  output of such a record. The cited sha text itself is never trusted for that (#140 round 2): a
  hash is matched against the file, not against another citation, so neither an invented extension
  of a cited prefix nor a shorter hash passing as one gets through. A record's own sha field is the
  subject of the two rules above, which compare it with that same file, and error 4 does not repeat
  their line for it. A bare file name and backticked hex without the ellipsis are not citations.

The check reads recorded files; it does not run the game.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import walks  # noqa: E402
import records as e019_records  # noqa: E402

QUESTIONS = ROOT / "questions" / "pro-static.md"
INVENTORY = ROOT / "experiments" / "E008-static-triage" / "measurements" / "iwp-extract-pro-r1.json"
F020 = ROOT / "findings" / "F020-pro-ui-observations.md"
STATUSES = ("observed", "narrowed", "static-only", "unestablished")
# the statuses whose sections the citation rule checks (#140); pending, static-only and
# unestablished sections cite nothing the rule reads
CITED_STATUSES = ("observed", "narrowed")
SCRIPT = re.compile(r"(MovieScript|BehaviorScript|CastScript) (\d+)(?: ([A-Za-z][A-Za-z0-9_]*))?")
HANDLER = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\(\)")
AT_LEAST = re.compile(r"at least (\d+) ([a-z ]+)")
SIZE = re.compile(r"(\d+)x(\d+)(?:x\d+)?")
HEX64 = re.compile(r"[0-9a-f]{64}")
# F020's citation formats (#140, round 2): a record citation is a backticked token that holds a
# record name (`E019-r<digits>.json`) in one of exactly two forms — the strict full path
# `runs/E019/<batch>/E019-r<digits>.json` (one path segment for the batch, no `..`, so a citation
# names a file of a batch folder and nothing else), which then goes through errors 1 and 2, or the
# bare file name `E019-r0005.json` (as Q-UI-19 cites its two aborted attempts), which is allowed
# and not checked. Any other token holding a record name is error 5. A manifest path
# (`E019-r<digits>.manifest.json`) holds no record name, so it is not a record citation. A record
# path may be followed directly by ` (sha256 `<prefix>…`)`, its sha citation. A hash is any
# backticked lowercase hex prefix of 8-64 chars immediately followed by `…` (U+2026), e.g.
# `ae6e98d28d379bb4…`; backticked hex without the ellipsis (a driver id like `e257bb1b395a`) is
# not a hash citation, and is ignored. Round 2 (R1): a hash citation is matched against the sha256
# computed from a cited record's file, never against the cited sha text — a citation must not be
# able to vouch for itself, nor for an invented extension of itself.
RECORD_NAME = re.compile(r"E019-r\d+\.json")
BARE_NAME = re.compile(r"E019-r\d+\.json\Z")
STRICT_PATH = re.compile(r"runs/E019/[A-Za-z0-9][A-Za-z0-9._-]*/E019-r\d+\.json")
CITED_TOKEN = re.compile(r"`([^`\n]+)`")
# the sha field after a record path: F020 writes `(sha256 `<prefix>…`, driver `…`, display …)`,
# so the field ends at its closing backtick, not at the parenthesis
SHA_AFTER_PATH = re.compile(r"\s*\(sha256 `([0-9a-f]{8,64})…`")
HASH_CITE = re.compile(r"`([0-9a-f]{8,64})…`")


def catalogue_ids(rows):
    """The questions of the catalogue, in file order, Q-PLY-04 last (the task names it beside the
    Q-UI rows)."""
    ids = [qid for qid in rows if qid.startswith("Q-UI-")]
    return ids + ["Q-PLY-04"]


def citation_errors(text, scripts, where):
    """Errors for the script and handler citations in one piece of text: every cited script must
    exist with the cited name, and every handler must belong to the script cited before it."""
    errors = []
    tokens = sorted([(m.start(), "script", m) for m in SCRIPT.finditer(text)]
                    + [(m.start(), "handler", m) for m in HANDLER.finditer(text)])
    current = None
    for _, kind, m in tokens:
        if kind == "script":
            kind_name, number, name = m.group(1), int(m.group(2)), m.group(3) or ""
            current = scripts.get((kind_name, number))
            if current is None:
                errors.append(f"{where}: no script {kind_name} {number} in the E008 inventory")
                current = None
            elif (name or "") != current["name"]:
                errors.append(f"{where}: {kind_name} {number} is named {current['name']!r}, cited {name!r}")
        else:
            handler = m.group(1)
            if current is None or handler not in current["handlers"]:
                errors.append(f"{where}: handler {handler}() is not in the script cited before it")
    return errors


def f020_citation_errors(body, root, where):
    """Errors for the record and hash citations of one F020 section whose status is observed or
    narrowed (#140): the section's evidence must be checkable. A record citation is one of the two
    forms above (error 5 otherwise), exists under `root` (error 1), and carries a sha256 prefix
    that is a prefix of that file's sha256 (error 2); the section cites at least one record with
    its sha (T39 DW2, error 3); and every hash cited is a prefix of the sha256 computed from a
    record cited by full path in the section, or of an output of such a record (error 4) — the
    cited sha text is never trusted for that (round 2, R1). One line per error, numbered 1-5 in
    the issue (#140)."""
    errors = []
    cited = []                              # (path, sha prefix or None), in text order
    digests = []                            # the sha256 of every cited record's file, from the file
    fields = set()                          # the (start, end) of each record's own sha field
    for token in CITED_TOKEN.finditer(body):
        text = token.group(1)
        if not RECORD_NAME.search(text):
            continue                          # not a record citation (a manifest path holds none)
        if BARE_NAME.fullmatch(text):
            continue                          # a bare file name: allowed, not checked
        if not STRICT_PATH.fullmatch(text) or ".." in text:
            errors.append(f"{where} cites a record path outside runs/E019/<batch>/ or malformed: "
                          f"{text}")                                                     # 5
            continue
        after = SHA_AFTER_PATH.match(body, token.end())
        sha = after.group(1) if after else None
        if after:
            fields.add((after.start(1), after.end(1)))
        path = Path(root) / text
        cited.append((path, sha))
        if not path.is_file():
            errors.append(f"{where} cites {text}, which does not exist")                 # 1
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        digests.append(digest)
        if sha and not digest.startswith(sha):
            errors.append(f"{where} cites {text} with sha256 {sha}…, "
                          "which is not a prefix of the file's sha256")                  # 2
    if not any(sha for _, sha in cited):
        errors.append(f"{where} cites no record with its sha256 "
                      "(T39's DW2 requires the record's sha)")                           # 3
    outputs = []
    for path, _ in cited:
        if not path.is_file():
            continue                          # the missing path is reported above
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue                          # the record loop reports it
        if isinstance(record, dict):
            for out in record.get("outputs") or []:
                if isinstance(out, dict) and isinstance(out.get("sha256"), str):
                    outputs.append(out["sha256"])
    for m in HASH_CITE.finditer(body):
        h = m.group(1)
        if (m.start(1), m.end(1)) in fields:
            continue                          # a record's own sha field: errors 1 and 2 compare
                                              # it with that same file's sha256, and error 4 could
                                              # only repeat their line — a text that prefixes no
                                              # cited record's digest prefixes this record's
                                              # neither, so it never catches what they missed and a
                                              # wrong record sha draws error 2 alone (the error-2
                                              # test visits that edge)
        if any(digest.startswith(h) for digest in digests):   # a cited record's own sha256
            continue
        if any(o.startswith(h) for o in outputs):             # an output of a cited record
            continue
        errors.append(f"{where} cites the hash {h}…, which is neither a record sha256 "
                      "computed from a cited file nor a prefix of an output of a record cited "
                      "here")                                                        # 4
    return errors


def count_target(spec, cell):
    """(word, minimum) a question's records must meet: the row's own "at least N <word>" when it
    names one, else the walk table's target, else None."""
    m = AT_LEAST.search(cell)
    if m:
        word = m.group(2).strip()
        if spec.get("count") and spec["count"]["word"] != word:
            return (word, int(m.group(1)),
                    f"walk table says {spec['count']['word']!r}, the row says {word!r}")
        return (word, int(m.group(1)), None)
    if spec.get("count"):
        return (spec["count"]["word"], spec["count"]["at_least"], None)
    return (None, 0, None)


def count_field(spec):
    """The observation field a spec's count target is measured under: its `measured` word when the
    target is a proxy the recorder cannot identify exactly (Q-UI-06's events, Q-UI-07's centre moves,
    Q-UI-13's computer turns), else its word."""
    declared = spec.get("count") or {}
    return declared.get("measured", declared.get("word"))


def is_proxy(spec):
    declared = spec.get("count") or {}
    return bool(declared.get("measured")) and declared["measured"] != declared.get("word")


def required_fields(spec):
    """The observation fields a completed record of this walk must carry, as (field, match) with
    match "exact" or "prefix". The check refuses a completed record that lacks any of them, and the
    end-to-end test drops each one from the recorder's own output to show that it does."""
    fields = [("walk question", "exact"), ("speed setting", "exact"), ("display size", "exact"),
              ("observation", "exact")]
    declared = spec.get("count")
    if declared:
        fields.append((f"count: {count_field(spec)}", "exact"))
        if is_proxy(spec):
            fields.append((f"count note: {declared['word']}", "exact"))
    if spec.get("timing"):
        fields.append(("timing:", "prefix"))
    if spec.get("hit_areas"):
        fields.append(("hit-area:", "prefix"))
    for kind in spec.get("reads", {}):
        fields.append((f"read: {kind}", "exact"))
    return fields


def required_outputs(spec):
    """The outputs a completed record of this walk must name: the cycle's before/after and, for
    Q-UI-21, the four reference states."""
    return ["before.png", "after.png"] + [f"state-{state}.png" for state in spec.get("states", [])]


def has_field(fields, field, match):
    return any(f == field for f in fields) if match == "exact" else any(f.startswith(field) for f in fields)


def size_pixels(size):
    """Pixel count of a size like 800x600x24 (None when it is not one)."""
    m = SIZE.fullmatch(str(size))
    return int(m.group(1)) * int(m.group(2)) if m else None


def run_checks(root, questions_path=QUESTIONS, inventory_path=INVENTORY, f020_path=None, f020=True,
                batch=None):
    """Every failure of the catalogue as a line; [] when the catalogue is complete. With f020=False
    only the records are checked (the end-to-end test of the recorder's own output).

    `batch` (a name in walks.BATCHES, e.g. `title-options`) limits the per-row checks to the
    questions that batch contains, while the global checks (count targets, walk-table coverage)
    still span every question. The per-batch exit is the per-walk Done-when 3 gate for a
    one-batch PR; the no-batch exit is the roll-up the per-batch Done-when calls informational.
    """
    root = Path(root)
    f020_path = Path(f020_path) if f020_path else root / "findings" / "F020-pro-ui-observations.md"
    errors = []

    rows = walks.question_rows(questions_path)
    all_ids = catalogue_ids(rows)
    if batch is not None:
        if batch not in walks.BATCHES:
            errors.append(f"--batch {batch!r} is not one of {list(walks.BATCHES)}")
            return errors
        ids = [qid for qid in all_ids if qid in walks.BATCHES[batch]]
    else:
        ids = all_ids
    scripts = {(s["kind"], s["number"]): s
               for s in json.loads(Path(inventory_path).read_text(encoding="utf-8"))["movies"][0]["scripts"]}

    # the walk table covers every question, and its count targets do not drift from the rows
    if set(walks.WALKS) != set(all_ids):
        errors.append(f"walk table covers {sorted(set(walks.WALKS) ^ set(all_ids))} wrong")
    for qid in all_ids:
        spec = walks.WALKS.get(qid)
        if not spec:
            continue
        word, minimum, drift = count_target(spec, rows[qid]["corroboration"])
        if drift:
            errors.append(f"{qid}: {drift}")

    # the records: one file per question walk under runs/E019/<batch>/
    best = {}                           # qid -> the highest count one completed record reached
    sizes = {}                          # qid -> the display sizes its completed records showed
    present = {}                        # qid -> [paths of any record, any status]
    seen = {}                           # qid -> [completed records] (only these cover a question)
    record_dirs = sorted((root / "runs" / "E019").glob("*") if (root / "runs" / "E019").is_dir() else [])
    for folder in record_dirs:
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except ValueError as exc:
                errors.append(f"{path.relative_to(root)}: not JSON: {exc}")
                continue
            where = path.relative_to(root)
            if not isinstance(record, dict) or record.get("schema") != "run/1" or record.get("experiment") != "E019":
                errors.append(f"{where}: not an E019 run/1 record")
                continue
            if record.get("run_id") != path.stem:
                errors.append(f"{where}: run_id is not the file name")
                continue
            qid = str(record.get("arm", "")).upper()
            spec = walks.WALKS.get(qid)
            if spec is None:
                errors.append(f"{where}: arm {record.get('arm')!r} names no catalogue question")
                continue
            where = f"{where} ({qid})"
            present.setdefault(qid, []).append(path)

            # --- every record, whatever its status: identity, place, manifest, citations ------------
            # (round 2, R6: an aborted record is data the repository keeps, so it is checked like any
            # other; only coverage and the targets wait for a completed one)
            want_set = e019_records.artifact_set_for(spec)
            artifact = record.get("artifact") if isinstance(record.get("artifact"), dict) else {}
            if artifact.get("set") != want_set:
                errors.append(f"{where}: artifact set {artifact.get('set')!r} is not the walk's {want_set!r}")
            if artifact.get("variant") is not None:
                errors.append(f"{where}: artifact variant {artifact.get('variant')!r} is not None")
            observations = record.get("observations")
            if not isinstance(observations, list) or not all(isinstance(o, dict) for o in observations):
                errors.append(f"{where}: observations is not a list of objects")
                observations = []
            outputs = record.get("outputs")
            if not isinstance(outputs, list) or not all(isinstance(o, dict) for o in outputs):
                errors.append(f"{where}: outputs is not a list of objects")
                outputs = []
            for out in outputs:
                if not HEX64.fullmatch(str(out.get("sha256", ""))):
                    errors.append(f"{where}: output {out.get('name')} has no sha256")
            batch = folder.name
            if batch != spec["batch"]:
                errors.append(f"{where}: sits in {batch}, its walk's batch is {spec['batch']}")
            manifest = root / "evidence" / "E019" / batch / f"{path.stem}.manifest.json"
            if not manifest.is_file():
                errors.append(f"{where}: no evidence manifest at {manifest.relative_to(root)}")
            else:
                try:
                    doc = json.loads(manifest.read_text(encoding="utf-8"))
                    named = {f["sha256"] for f in doc["files"]}
                    manifest_artifact = doc.get("artifact") if isinstance(doc.get("artifact"), dict) else {}
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    errors.append(f"{manifest.relative_to(root)}: unreadable manifest: {exc}")
                    named, manifest_artifact = set(), {}
                if manifest_artifact.get("set") != want_set:
                    errors.append(f"{manifest.relative_to(root)}: artifact set {manifest_artifact.get('set')!r} "
                                  f"is not the walk's {want_set!r}")
                if manifest_artifact.get("variant") is not None:
                    errors.append(f"{manifest.relative_to(root)}: artifact variant "
                                  f"{manifest_artifact.get('variant')!r} is not None")
                for out in outputs:
                    if out.get("sha256") not in named:
                        errors.append(f"{where}: output {out.get('name')} is not in its manifest by hash")
            for o in observations:
                errors.extend(citation_errors(str(o.get("value", "")), scripts, where))

            if record.get("status") != "completed":
                continue                      # data, but it does not cover the question

            # --- a completed record: it covers its question only if it carries everything ----------
            seen.setdefault(qid, []).append(record)
            start_state = record.get("start_state") if isinstance(record.get("start_state"), dict) else {}
            seal = str(start_state.get("sha256", ""))
            if not HEX64.fullmatch(seal) or seal == "0" * 64:
                errors.append(f"{where}: no start_state sha256 (the seal)")
            fields = [str(o.get("field", "")) for o in observations]
            by_field = {}
            for o in observations:
                by_field.setdefault(str(o.get("field", "")), []).append(str(o.get("value", "")))
            for field, match in required_fields(spec):
                if not has_field(fields, field, match):
                    errors.append(f"{where}: no {field!r} observation"
                                  + (" (no per-question observation)" if field == "observation" else ""))
            for name in required_outputs(spec):
                if not any(o.get("name") == name for o in outputs):
                    errors.append(f"{where}: no {name} among its outputs")
            if by_field.get("walk question", [qid])[0] != qid:
                errors.append(f"{where}: its walk question is {by_field['walk question'][0]!r}")

            # the per-question observation: the recorder's summary of what it measured, which names
            # the question and only screenshots the record holds
            for value in by_field.get("observation", [])[:1]:
                try:
                    summary = json.loads(value)
                    shots = summary["screenshots"]
                    if summary.get("question") != qid:
                        errors.append(f"{where}: its observation names {summary.get('question')!r}")
                    names = {o.get("name") for o in outputs}
                    for shot in shots:
                        if shot not in names:
                            errors.append(f"{where}: its observation names {shot}, which is not among its outputs")
                except (ValueError, KeyError, TypeError) as exc:
                    errors.append(f"{where}: its observation is not the recorder's summary: {exc!r}")

            # the count: one value per record, and a target is met by one record (a re-run is a new
            # record, never added to an old one: R5's class, a repeat is not a second instance)
            word, minimum, _ = count_target(spec, rows[qid]["corroboration"])
            if word:
                field = count_field(spec)
                values = by_field.get(f"count: {field}", [])
                if len(values) > 1:
                    errors.append(f"{where}: {len(values)} 'count: {field}' observations, one wanted")
                elif values and not values[0].isdigit():
                    errors.append(f"{where}: count {field} is {values[0]!r}, not a number")
                elif values:
                    best[qid] = max(best.get(qid, 0), int(values[0]))

            for kind, minimum_reads in spec.get("reads", {}).items():
                have = len(by_field.get(f"read: {kind}", []))
                if have < minimum_reads:
                    errors.append(f"{where}: read {kind} recorded {have} times, its spec wants {minimum_reads}")

            # the display size: measured, and equal to the size the walk asked for (R5)
            for value in by_field.get("display size", [])[:1]:
                try:
                    shown = json.loads(value)
                    requested, measured = shown["requested"], shown["display pixels"]
                except (ValueError, KeyError, TypeError) as exc:
                    errors.append(f"{where}: its display size is not a measurement: {exc!r}")
                    continue
                if size_pixels(requested) is None or size_pixels(requested) != measured:
                    errors.append(f"{where}: display size {requested!r} measured {measured!r} pixels")
                    continue
                if spec.get("sizes") and requested not in spec["sizes"]:
                    errors.append(f"{where}: display size {requested!r} is not one its walk names")
                    continue
                sizes.setdefault(qid, set()).add(requested)

    # coverage and the targets, over the completed records only
    for qid in ids:
        spec = walks.WALKS.get(qid, {})
        if qid not in seen:
            why = "its records were aborted" if qid in present else "the walk has not run"
            errors.append(f"{qid}: no completed record under runs/E019 ({why})")
            continue
        word, minimum, _ = count_target(spec, rows[qid]["corroboration"])
        if word and best.get(qid, 0) < minimum:
            errors.append(f"{qid}: count {count_field(spec)} reached {best.get(qid, 0)} in its best record, "
                          f"the target is at least {minimum}")
        for size in spec.get("sizes") or []:
            if size not in sizes.get(qid, set()):
                errors.append(f"{qid}: no completed record shows the display size {size}")

    if not f020:
        return errors

    # F020: a section per question, each with an Observation line of the catalogue's vocabulary
    if not f020_path.is_file():
        errors.append(f"F020: {f020_path} does not exist")
    else:
        text = f020_path.read_text(encoding="utf-8")
        # a section runs to the next heading of level 2-4 (`^#{2,4} `) or the end of the file, so
        # the last question's section does not take in the `##` sections after it (#140 round 2)
        sections = dict((m.group(1), m.group(2)) for m in
                        re.finditer(r"^#### (Q-[A-Z]+-\d+).*?\n(.*?)(?=^#{2,4} |\Z)",
                                    text, re.S | re.M))
        for qid in ids:
            body = sections.get(qid)
            if body is None:
                errors.append(f"{qid}: F020 has no section for it")
                continue
            m = re.search(r"-\s*\*\*Observation\*\*:\s*([a-z-]+)", body)
            if not m or m.group(1) not in STATUSES:
                errors.append(f"{qid}: F020's Observation line has no status of {list(STATUSES)} "
                              "(the walk's record may be missing, or the section is still pending)")
                continue
            errors.extend(citation_errors(body, scripts, f"F020 {qid}"))
            if m.group(1) in CITED_STATUSES:
                errors.extend(f020_citation_errors(body, root, f"{qid}: F020"))
            declared = (walks.WALKS.get(qid) or {}).get("count") or {}
            if (declared.get("measured") and declared["measured"] != declared.get("word")
                    and m.group(1) == "observed"):
                errors.append(f"{qid}: F020 is observed, but the walk counts {declared['measured']!r} "
                              f"as a proxy for {declared['word']!r}; a narrowed observation is the "
                              "honest one")

    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1] if __doc__ else None)
    parser.add_argument("--batch", default=None,
                        help="limit the per-row checks to one batch's questions "
                             "(one of walks.BATCHES); the global checks still span every question")
    parser.add_argument("--no-f020", action="store_true",
                        help="check only the records (the recorder's own output), not F020")
    args = parser.parse_args()

    errors = run_checks(ROOT, f020=not args.no_f020, batch=args.batch)
    for error in errors:
        print("FAIL", error)
    if errors:
        if args.batch is not None:
            print(f"{len(errors)} failure(s); the {args.batch!r} batch is not complete")
        else:
            print(f"{len(errors)} failure(s); the catalogue is not complete")
        return 1
    if args.batch is not None:
        print(f"ok: every {args.batch!r} question has a completed record, an observation, "
              "its targets met, and an F020 section; every citation is in the E008 inventory")
    else:
        print("ok: every catalogue question has a completed record, an observation, its targets met, "
              "and an F020 section; every citation is in the E008 inventory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
