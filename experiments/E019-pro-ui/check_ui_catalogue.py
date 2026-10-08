#!/usr/bin/env python3
"""E019 (T24): the catalogue check — Done-when 3 of the task.

    python3 experiments/E019-pro-ui/check_ui_catalogue.py

Exits 0 when every piece holds:
- every `Q-UI-*` row of questions/pro-static.md and Q-PLY-04 has at least one completed E019
  record, under runs/E019/<batch>/, whose arm names the question;
- every such record carries the per-question observation, meets its question's count target (the
  row's "at least N <word>" when the row names one, else the walk table's), carries timing
  observations when the walk is frame-timed, hit-area observations for Q-UI-18, the reads its
  spec names, and the four reference states for Q-UI-21; its evidence manifest exists and names
  every output's hash;
- findings/F020-pro-ui-observations.md has a section per question with an Observation line whose
  status is one of observed, narrowed, static-only, unestablished (a pending section fails);
- no record's observations, and no F020 section, cites a script or handler that the E008
  inventory does not have (kind, number, name, handler — the same rule
  tools/check_pro_question_map.py enforces for the questions map).

The check reads recorded files; it does not run the game.
"""
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
SCRIPT = re.compile(r"(MovieScript|BehaviorScript|CastScript) (\d+)(?: ([A-Za-z][A-Za-z0-9_]*))?")
HANDLER = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\(\)")
AT_LEAST = re.compile(r"at least (\d+) ([a-z ]+)")


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
    target is a proxy the recorder cannot identify exactly (Q-UI-07's centre moves), else its word."""
    declared = spec.get("count") or {}
    return declared.get("measured", declared.get("word"))


def run_checks(root, questions_path=QUESTIONS, inventory_path=INVENTORY, f020_path=None):
    """Every failure of the catalogue as a line; [] when the Done-when 3 holds."""
    root = Path(root)
    f020_path = Path(f020_path) if f020_path else root / "findings" / "F020-pro-ui-observations.md"
    errors = []

    rows = walks.question_rows(questions_path)
    ids = catalogue_ids(rows)
    scripts = {(s["kind"], s["number"]): s
               for s in json.loads(Path(inventory_path).read_text(encoding="utf-8"))["movies"][0]["scripts"]}

    # the walk table covers every question, and its count targets do not drift from the rows
    if set(walks.WALKS) != set(ids):
        errors.append(f"walk table covers {sorted(set(walks.WALKS) ^ set(ids))} wrong")
    for qid in ids:
        spec = walks.WALKS.get(qid)
        if not spec:
            continue
        word, minimum, drift = count_target(spec, rows[qid]["corroboration"])
        if drift:
            errors.append(f"{qid}: {drift}")

    # the records: one file per question walk under runs/E019/<batch>/
    counts = {}                         # qid -> summed count of its measured field
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
            if record.get("schema") != "run/1" or record.get("experiment") != "E019":
                errors.append(f"{where}: not an E019 run/1 record")
                continue
            if record.get("run_id") != path.stem:
                errors.append(f"{where}: run_id is not the file name")
                continue
            qid = record.get("arm", "").upper()
            spec = walks.WALKS.get(qid)
            if spec is None:
                errors.append(f"{where}: arm {record.get('arm')!r} names no catalogue question")
                continue
            where = f"{where} ({qid})"
            present.setdefault(qid, []).append(path)

            # R1: the record's identity and the properties the task requires of it. A record of the
            # wrong artifact set (a DOS set, or the wrong Pro successor) is never this walk's.
            want_set = e019_records.artifact_set_for(spec)
            got_set = (record.get("artifact") or {}).get("set")
            if got_set != want_set:
                errors.append(f"{where}: artifact set {got_set!r} is not the walk's {want_set!r}")
            if (record.get("artifact") or {}).get("variant") is not None:
                errors.append(f"{where}: artifact variant {(record.get('artifact') or {}).get('variant')!r} "
                              "is not None")
            if not isinstance(record.get("start_state"), dict) or not record["start_state"].get("sha256"):
                errors.append(f"{where}: no start_state sha256 (the seal)")
            observations = record.get("observations")
            if not isinstance(observations, list) or not all(isinstance(o, dict) for o in observations):
                errors.append(f"{where}: observations is not a list of objects")
                observations = []
            outputs = record.get("outputs")
            if not isinstance(outputs, list) or not all(isinstance(o, dict) for o in outputs):
                errors.append(f"{where}: outputs is not a list of objects")
                outputs = []
            if record.get("status") != "completed":
                continue                      # data, but it does not cover the question

            # R2: only a completed record covers the question; it is added to `seen` after this test
            seen.setdefault(qid, []).append(record)
            batch = folder.name
            if batch != spec["batch"]:
                errors.append(f"{where}: sits in {batch}, its walk's batch is {spec['batch']}")
            fields = [o.get("field", "") for o in observations]
            values = [o.get("value", "") for o in observations]
            if not any(f == "observation" for f in fields):
                errors.append(f"{where}: no per-question observation")
            word, minimum, _ = count_target(spec, rows[qid]["corroboration"])
            if word:
                field = count_field(spec)
                got = sum(int(o["value"]) for o in observations
                          if o.get("field") == f"count: {field}"
                          and str(o.get("value", "")).isdigit())
                counts[qid] = counts.get(qid, 0) + got
                declared = spec.get("count") or {}
                if declared.get("measured") and field != declared["word"]:
                    if not any(f == f"count note: {declared['word']}" for f in fields):
                        errors.append(f"{where}: counts {field!r} in place of {declared['word']!r} "
                                      "and carries no count note")
            if spec.get("timing") and not any(f.startswith("timing:") for f in fields):
                errors.append(f"{where}: its walk is frame-timed and no timing is recorded")
            if spec.get("hit_areas") and not any(f.startswith("hit-area:") for f in fields):
                errors.append(f"{where}: its walk measures hit areas and none is recorded")
            for kind, minimum_reads in spec.get("reads", {}).items():
                have = sum(1 for f in fields if f == f"read: {kind}")
                if have < minimum_reads:
                    errors.append(f"{where}: read {kind} recorded {have} times, its spec wants {minimum_reads}")
            for state in spec.get("states", []):
                if not any(o.get("name") == f"state-{state}.png" for o in outputs):
                    errors.append(f"{where}: no state-{state}.png among its outputs")
            for cycle_png in ("before.png", "after.png"):
                if not any(o.get("name") == cycle_png for o in outputs):
                    errors.append(f"{where}: no {cycle_png} among its outputs (the cycle's before/after)")
            manifest = root / "evidence" / "E019" / batch / f"{path.stem}.manifest.json"
            if not manifest.is_file():
                errors.append(f"{where}: no evidence manifest at {manifest.relative_to(root)}")
            else:
                try:
                    doc = json.loads(manifest.read_text(encoding="utf-8"))
                    named = {f["sha256"] for f in doc["files"]}
                    manifest_set = (doc.get("artifact") or {}).get("set")
                except (ValueError, KeyError, TypeError) as exc:
                    errors.append(f"{manifest.relative_to(root)}: unreadable manifest: {exc}")
                    named, manifest_set = set(), None
                if manifest_set != want_set:
                    errors.append(f"{manifest.relative_to(root)}: artifact set {manifest_set!r} is not "
                                  f"the walk's {want_set!r}")
                if (doc.get("artifact") or {}).get("variant") is not None:
                    errors.append(f"{manifest.relative_to(root)}: artifact variant "
                                  f"{(doc.get('artifact') or {}).get('variant')!r} is not None")
                for out in outputs:
                    if out.get("sha256") not in named:
                        errors.append(f"{where}: output {out.get('name')} is not in its manifest by hash")
            for value in values:
                errors.extend(citation_errors(value, scripts, where))

    # coverage and the targets, over the completed records only
    for qid in ids:
        spec = walks.WALKS.get(qid, {})
        if qid not in seen:
            why = "its records were aborted" if qid in present else "the walk has not run"
            errors.append(f"{qid}: no completed record under runs/E019 ({why})")
            continue
        word, minimum, _ = count_target(spec, rows[qid]["corroboration"])
        if word:
            field = count_field(spec)
            if counts.get(qid, 0) < minimum:
                errors.append(f"{qid}: count {field} is {counts.get(qid, 0)}, the row wants at least {minimum}")

    # F020: a section per question, each with an Observation line of the catalogue's vocabulary
    if not f020_path.is_file():
        errors.append(f"F020: {f020_path} does not exist")
    else:
        text = f020_path.read_text(encoding="utf-8")
        sections = dict((m.group(1), m.group(2)) for m in
                        re.finditer(r"^#### (Q-[A-Z]+-\d+).*?\n(.*?)(?=^#### |\Z)", text, re.S | re.M))
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
            declared = (walks.WALKS.get(qid) or {}).get("count") or {}
            if (declared.get("measured") and declared["measured"] != declared.get("word")
                    and m.group(1) == "observed"):
                errors.append(f"{qid}: F020 is observed, but the walk counts {declared['measured']!r} "
                              f"as a proxy for {declared['word']!r}; a narrowed observation is the "
                              "honest one")

    return errors


def main():
    errors = run_checks(ROOT)
    for error in errors:
        print("FAIL", error)
    if errors:
        print(f"{len(errors)} failure(s); the catalogue is not complete")
        return 1
    print("ok: every catalogue question has a completed record, an observation, its targets met, "
          "and an F020 section; every citation is in the E008 inventory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
