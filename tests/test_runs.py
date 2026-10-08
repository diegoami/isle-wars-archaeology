"""Every record under runs/ is valid run/1; every manifest under evidence/ is valid evidence-manifest/1.

The checks use the pinned validator (tools/validate_records.py, fetched from game-archaeologist).
A record must also sit at runs/E<nnn>/<run-id>.json or runs/E<nnn>/<batch>/<run-id>.json (E019's
per-screen batches are the one experiment with batch folders), with its own run id and experiment,
and its artifact set must be one registered in artifacts/known.json.
"""
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_records  # noqa: E402  (the pinned validator, never a copy)

RUN_SCHEMA = "run/1"
MANIFEST_SCHEMA = "evidence-manifest/1"
KNOWN_SETS = {
    entry["manifest"]["id"]
    for entry in json.loads((ROOT / "artifacts" / "known.json").read_text(encoding="utf-8"))["sets"]
}


def schema_errors(path, schema_id):
    """(errors, document) for one file under the pinned validator, which reads it the way every
    repository does: UTF-8 JSON without NaN, Infinity or a duplicate key. The document must name
    `schema_id`, so a record of another kind cannot sit in runs/ or evidence/."""
    try:
        doc = validate_records.load_file(path)
    except (OSError, ValueError) as exc:
        return [f"unreadable: {exc}"], None
    errors = validate_records.validate_document(doc)
    if not errors and doc.get("schema") != schema_id:
        errors.append(f"$.schema: {doc.get('schema')!r} is not {schema_id!r}")
    return errors, doc


def record_experiment(path):
    """The experiment folder a record path sits under: runs/E<nnn>/, or runs/E<nnn>/<batch>/ for a
    batched experiment (one batch level at most), or None when the path is neither."""
    chain = []
    for parent in Path(path).parents:
        if parent.name == "runs":
            break
        chain.append(parent.name)
        if len(chain) > 2:
            return None
    else:
        return None
    if not chain or not re.fullmatch(r"E\d{3,}", chain[-1]):
        return None
    return chain[-1]


def run_record_errors(path, known_sets=KNOWN_SETS):
    """All problems with one run record at <...>/runs/E<nnn>[/<batch>]/<run-id>.json, [] when valid."""
    path = Path(path)
    errors, doc = schema_errors(path, RUN_SCHEMA)
    if doc is None or not isinstance(doc, dict):
        return errors
    if doc.get("run_id") != path.stem:
        errors.append(f"run_id {doc.get('run_id')!r} is not the file name {path.stem!r}")
    folder = record_experiment(path)
    if folder is None:
        errors.append(f"the record does not sit at runs/E<nnn>[/<batch>]/<run id>.json (here {path})")
    elif doc.get("experiment") != folder:
        errors.append(f"experiment {doc.get('experiment')!r} is not the experiment folder {folder!r}")
    if isinstance(doc.get("run_id"), str) and not doc["run_id"].startswith(str(doc.get("experiment")) + "-"):
        errors.append("run_id does not start with the experiment id")
    set_id = (doc.get("artifact") or {}).get("set")
    if known_sets is not None and set_id is not None and set_id not in known_sets:
        errors.append(f"artifact set {set_id!r} is not in artifacts/known.json")
    return errors


def check_runs(root, known_sets=KNOWN_SETS):
    """{relative path: errors} for every runs/**/*.json under <root> that has errors.

    known_sets=None skips the registry check, so a test can isolate the schema's verdict."""
    root = Path(root)
    bad = {}
    for path in sorted((root / "runs").rglob("*.json")):
        errors = run_record_errors(path, known_sets)
        if errors:
            bad[path.relative_to(root).as_posix()] = errors
    return bad


def check_manifests(root):
    root = Path(root)
    bad = {}
    for path in sorted((root / "evidence").rglob("*.manifest.json")):
        errors, doc = schema_errors(path, MANIFEST_SCHEMA)
        if isinstance(doc, dict) and doc.get("run_id") != path.name[: -len(".manifest.json")]:
            errors.append("run_id is not the file name")
        if errors:
            bad[path.relative_to(root).as_posix()] = errors
    return bad


class RunRecordsTest(unittest.TestCase):
    def test_every_committed_run_record_is_valid(self):
        self.assertEqual(check_runs(ROOT), {})

    def test_every_committed_evidence_manifest_is_valid(self):
        self.assertEqual(check_manifests(ROOT), {})

    def place(self, tmp, source):
        """Copy an example to runs/<experiment>/<run_id>.json, so only its content can fail."""
        doc = json.loads(source.read_text(encoding="utf-8"))
        target = Path(tmp) / "runs" / doc["experiment"] / f"{doc['run_id']}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, target)
        return target

    def test_an_invalid_example_copied_into_runs_fails(self):
        invalid = sorted((ROOT / "formats" / "examples" / "invalid").glob("run-1--*.json"))
        expected = json.loads((ROOT / "formats" / "examples" / "expected-errors.json").read_text(encoding="utf-8"))
        self.assertEqual([p.name for p in invalid], sorted(n for n in expected if n.startswith("run-1--")))
        self.assertGreaterEqual(len(invalid), 12)
        for source in invalid:
            with tempfile.TemporaryDirectory() as tmp:
                self.place(tmp, source)
                self.assertTrue(check_runs(tmp, known_sets=None), f"{source.name} passed")

    def test_a_valid_example_copied_into_runs_passes(self):
        for source in sorted((ROOT / "formats" / "examples" / "valid").glob("run-1--*.json")):
            with tempfile.TemporaryDirectory() as tmp:
                self.place(tmp, source)
                self.assertEqual(check_runs(tmp, known_sets=None), {}, source.name)

    def test_a_valid_example_with_the_right_name_passes_and_a_wrong_name_fails(self):
        valid = ROOT / "formats" / "examples" / "valid" / "run-1--pure-observation-aborted.json"
        doc = json.loads(valid.read_text(encoding="utf-8"))
        known = {doc["artifact"]["set"]}
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "runs" / "E002" / "E002-r0001.json"
            good.parent.mkdir(parents=True)
            shutil.copy(valid, good)
            self.assertEqual(run_record_errors(good, known), [])
            wrong = Path(tmp) / "runs" / "E003" / "E002-r0001.json"
            wrong.parent.mkdir(parents=True)
            shutil.copy(valid, wrong)
            self.assertTrue(run_record_errors(wrong, known))
            renamed = Path(tmp) / "runs" / "E002" / "E002-r0002.json"
            shutil.copy(valid, renamed)
            self.assertTrue(any("file name" in e for e in run_record_errors(renamed, known)),
                            "a record whose run_id is not its file name must fail")
            self.assertTrue(run_record_errors(good, set()), "an unregistered set must fail")

    def test_an_invalid_manifest_example_copied_into_evidence_fails(self):
        source = ROOT / "formats" / "examples" / "invalid" / "evidence-manifest-1--bad-asset-name.json"
        doc = json.loads(source.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "evidence" / doc["experiment"]
            folder.mkdir(parents=True)
            shutil.copy(source, folder / f"{doc['run_id']}.manifest.json")
            errors = check_manifests(tmp)
        self.assertTrue(errors)
        self.assertFalse(any("file name" in e for es in errors.values() for e in es), errors)

    def test_a_valid_manifest_example_copied_into_evidence_passes(self):
        source = ROOT / "formats" / "examples" / "valid" / "evidence-manifest-1--toy-run.json"
        doc = json.loads(source.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "evidence" / doc["experiment"]
            folder.mkdir(parents=True)
            shutil.copy(source, folder / f"{doc['run_id']}.manifest.json")
            self.assertEqual(check_manifests(tmp), {})

    def place_text(self, tmp, text):
        """Write `text` as runs/E002/E002-r0001.json and return its path."""
        target = Path(tmp) / "runs" / "E002" / "E002-r0001.json"
        target.parent.mkdir(parents=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_a_record_with_a_duplicate_key_fails(self):
        """Which value counts depends on the reader, so the pinned reader refuses a duplicate key."""
        valid = ROOT / "formats" / "examples" / "valid" / "run-1--pure-observation-aborted.json"
        text = valid.read_text(encoding="utf-8")
        known = {json.loads(text)["artifact"]["set"]}
        doubled = text.replace("{", '{"run_id": "E002-r0001", ', 1)
        self.assertEqual(json.loads(doubled)["run_id"], "E002-r0001")    # json.loads reads it without complaint
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_record_errors(self.place_text(tmp, text), known), [])
        with tempfile.TemporaryDirectory() as tmp:
            errors = run_record_errors(self.place_text(tmp, doubled), known)
        self.assertTrue(any("duplicate key" in e for e in errors), errors)

    def test_a_record_with_nan_or_a_lone_surrogate_fails(self):
        valid = ROOT / "formats" / "examples" / "valid" / "run-1--pure-observation-aborted.json"
        text = valid.read_text(encoding="utf-8")
        known = {json.loads(text)["artifact"]["set"]}
        broken = {"NaN": text.replace("{", '{"x": NaN, ', 1),
                  "lone surrogate": text.replace("{", '{"note": "\\ud800", ', 1)}
        for label, bad in broken.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as tmp:
                self.assertTrue(run_record_errors(self.place_text(tmp, bad), known), f"{label} validated")

    def test_a_record_of_another_schema_does_not_pass_as_a_run(self):
        source = ROOT / "formats" / "examples" / "valid" / "evidence-manifest-1--toy-run.json"
        doc = json.loads(source.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "runs" / doc["experiment"] / f"{doc['run_id']}.json"
            target.parent.mkdir(parents=True)
            shutil.copy(source, target)
            errors = run_record_errors(target, None)
        self.assertTrue(any("is not 'run/1'" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
