"""The vendored formats: the artifact-set schema, its examples and the canonical rule.

These tests exercise the vendored bytes in place. If a vendored file is edited, its archaeology.json
sha256 stops matching and the toy id stops recomputing.
"""
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "tests" / "formats" / "check_examples.py"
VENDORED_PATHS = [
    "formats/artifact-set-1.schema.json",
    "formats/examples/valid/artifact-set-1--toy.json",
    "formats/examples/invalid/artifact-set-1--bad-id-hash.json",
    "formats/examples/invalid/artifact-set-1--unknown-acquisition.json",
    "formats/run-1.schema.json",
    "formats/evidence-manifest-1.schema.json",
    "formats/examples/valid/run-1--pure-observation-aborted.json",
    "formats/examples/valid/run-1--seeded-crafted-state.json",
    "formats/examples/invalid/run-1--decoded-without-via.json",
    "formats/examples/invalid/run-1--interpretation-field.json",
    "formats/examples/invalid/run-1--missing-interventions.json",
    "formats/examples/invalid/run-1--observation-without-value-or-ref.json",
    "formats/examples/invalid/run-1--output-in-repo.json",
    "formats/examples/invalid/run-1--path-in-fingerprint.json",
    "formats/examples/invalid/run-1--truncated-hash.json",
    "formats/examples/invalid/run-1--unknown-intervention-level.json",
    "formats/examples/invalid/run-1--value-without-location.json",
    "formats/examples/valid/evidence-manifest-1--toy-run.json",
    "formats/examples/invalid/evidence-manifest-1--bad-asset-name.json",
    "formats/examples/invalid/evidence-manifest-1--no-artifact.json",
    "formats/examples/invalid/evidence-manifest-1--repo-store.json",
    "formats/examples/invalid/evidence-manifest-1--untraced-class.json",
    "tests/formats/check_examples.py",
]


def load_vendored():
    spec = importlib.util.spec_from_file_location("check_examples_vendored", VENDORED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def example_errors(check, schema, doc):
    return check.validate(doc, schema) + check.semantic_errors(schema["$id"], doc)


class VendoredFormatsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check = load_vendored()
        cls.schema = read_json(ROOT / "formats" / "artifact-set-1.schema.json")

    def test_toy_example_recomputes_its_id(self):
        toy = read_json(ROOT / "formats" / "examples" / "valid" / "artifact-set-1--toy.json")
        self.assertEqual(toy["id"], "toy-1.0-1ff31629")
        self.assertEqual(self.check.canonical_set_hash(toy)[:8], "1ff31629")

    def test_both_invalid_examples_fail(self):
        for name in ("artifact-set-1--bad-id-hash.json", "artifact-set-1--unknown-acquisition.json"):
            doc = read_json(ROOT / "formats" / "examples" / "invalid" / name)
            errors = self.check.validate(doc, self.schema) + self.check.semantic_errors(
                self.schema["$id"], doc
            )
            self.assertTrue(errors, f"{name} validates but should fail")

    def test_valid_toy_example_passes(self):
        toy = read_json(ROOT / "formats" / "examples" / "valid" / "artifact-set-1--toy.json")
        errors = self.check.validate(toy, self.schema) + self.check.semantic_errors(
            self.schema["$id"], toy
        )
        self.assertEqual(errors, [])

    def test_archaeology_pins_each_vendored_hash(self):
        vendored = {
            entry["path"]: entry["sha256"]
            for entry in read_json(ROOT / "archaeology.json")["game-archaeologist"]["vendored"]
        }
        self.assertEqual(sorted(vendored), sorted(VENDORED_PATHS))
        for path in VENDORED_PATHS:
            digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            self.assertEqual(vendored[path], digest, f"{path} hash differs from archaeology.json")


class VendoredExamplesTest(unittest.TestCase):
    """Every vendored example of run/1 and evidence-manifest/1: valid ones pass, invalid ones fail.

    The counts are those at the pinned game-archaeologist commit; a missing example fails the count.
    """

    COUNTS = {"run-1": (2, 9), "evidence-manifest-1": (1, 4)}

    @classmethod
    def setUpClass(cls):
        cls.check = load_vendored()

    def examples(self, schema_name, kind):
        folder = ROOT / "formats" / "examples" / kind
        return sorted(folder.glob(f"{schema_name}--*.json"))

    def test_each_schema_has_the_pinned_example_counts(self):
        for name, (valid, invalid) in self.COUNTS.items():
            self.assertEqual(len(self.examples(name, "valid")), valid, name)
            self.assertEqual(len(self.examples(name, "invalid")), invalid, name)

    def test_valid_examples_pass_and_invalid_examples_fail(self):
        for name in self.COUNTS:
            schema = read_json(ROOT / "formats" / f"{name}.schema.json")
            for path in self.examples(name, "valid"):
                errors = example_errors(self.check, schema, read_json(path))
                self.assertEqual(errors, [], f"{path.name} should be valid")
            for path in self.examples(name, "invalid"):
                errors = example_errors(self.check, schema, read_json(path))
                self.assertTrue(errors, f"{path.name} validates but should fail")


if __name__ == "__main__":
    unittest.main()
