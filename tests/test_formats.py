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
    "tests/formats/check_examples.py",
]


def load_vendored():
    spec = importlib.util.spec_from_file_location("check_examples_vendored", VENDORED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


if __name__ == "__main__":
    unittest.main()
