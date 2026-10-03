"""Every record under runs/ is valid run/1; every manifest under evidence/ is valid evidence-manifest/1.

The checks use the vendored validator (tests/formats/check_examples.py). A record must also sit at
runs/E<nnn>/<run-id>.json with its own run id and experiment, and its artifact set must be one
registered in artifacts/known.json.
"""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "tests" / "formats" / "check_examples.py"


def load_vendored():
    spec = importlib.util.spec_from_file_location("check_examples_vendored", VENDORED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load_vendored()
RUN_SCHEMA = json.loads((ROOT / "formats" / "run-1.schema.json").read_text(encoding="utf-8"))
MANIFEST_SCHEMA = json.loads(
    (ROOT / "formats" / "evidence-manifest-1.schema.json").read_text(encoding="utf-8")
)
KNOWN_SETS = {
    entry["manifest"]["id"]
    for entry in json.loads((ROOT / "artifacts" / "known.json").read_text(encoding="utf-8"))["sets"]
}


def schema_errors(path, schema):
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"unreadable: {exc}"], None
    return CHECK.validate(doc, schema) + CHECK.semantic_errors(schema["$id"], doc), doc


def run_record_errors(path, known_sets=KNOWN_SETS):
    """All problems with one run record at <...>/runs/E<nnn>/<run-id>.json, [] when valid."""
    path = Path(path)
    errors, doc = schema_errors(path, RUN_SCHEMA)
    if doc is None or not isinstance(doc, dict):
        return errors
    if doc.get("run_id") != path.stem:
        errors.append(f"run_id {doc.get('run_id')!r} is not the file name {path.stem!r}")
    if doc.get("experiment") != path.parent.name:
        errors.append(f"experiment {doc.get('experiment')!r} is not the folder {path.parent.name!r}")
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
        if doc is not None and doc.get("run_id") != path.name[: -len(".manifest.json")]:
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
        self.assertEqual(len(invalid), 9)
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
            good = Path(tmp) / "E002" / "E002-r0001.json"
            good.parent.mkdir()
            shutil.copy(valid, good)
            self.assertEqual(run_record_errors(good, known), [])
            wrong = Path(tmp) / "E003" / "E002-r0001.json"
            wrong.parent.mkdir()
            shutil.copy(valid, wrong)
            self.assertTrue(run_record_errors(wrong, known))
            renamed = Path(tmp) / "E002" / "E002-r0002.json"
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


if __name__ == "__main__":
    unittest.main()
