"""The vendored formats and tools, pinned to a game-archaeologist commit, and the pinned validator.

Everything under formats/ and the two tools tools/validate_records.py and tools/register_artifact.py
are upstream bytes at the commit archaeology.json pins. These tests fail when a vendored byte
changes, when a file under formats/ or a tool is not pinned, or when the validator stops refusing
what the examples say it must refuse.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_records  # noqa: E402  (the pinned validator, never a copy)

PIN = "69566be655fc35c36d19277db9b94f8300055c7b"
TOOLS = ["tools/validate_records.py", "tools/register_artifact.py"]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pinned():
    return read_json(ROOT / "archaeology.json")["game-archaeologist"]


def vendored_hashes():
    return {entry["path"]: entry["sha256"] for entry in pinned()["vendored"]}


def example_errors(path):
    return validate_records.validate_document(validate_records.load_file(path))


class PinnedBytesTest(unittest.TestCase):
    def test_archaeology_pins_the_commit_and_lists_both_tools_as_used(self):
        pin = pinned()
        self.assertEqual(pin["commit"], PIN)
        for tool in TOOLS:
            self.assertIn(tool, pin["uses"])

    def test_archaeology_pins_each_vendored_hash(self):
        vendored = vendored_hashes()
        for path, want in vendored.items():
            digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            self.assertEqual(want, digest, f"{path} hash differs from archaeology.json")

    def test_every_vendored_file_is_pinned_and_nothing_under_formats_or_the_tools_is_unpinned(self):
        vendored = set(vendored_hashes())
        present = {p.relative_to(ROOT).as_posix() for p in (ROOT / "formats").rglob("*") if p.is_file()}
        present |= {tool for tool in TOOLS if (ROOT / tool).is_file()}
        self.assertEqual(sorted(present), sorted(vendored))
        self.assertTrue(set(TOOLS) <= vendored)
        self.assertTrue(all(p.startswith(("formats/", "tools/")) for p in vendored), sorted(vendored))

    def test_no_vendored_validator_copy_is_left_under_tests(self):
        """The validator is tools/validate_records.py; a second copy under tests/formats would drift."""
        self.assertEqual(sorted((ROOT / "tests" / "formats").glob("*.py")) if (ROOT / "tests" / "formats").is_dir() else [], [])
        self.assertFalse([p for p in vendored_hashes() if p.startswith("tests/")])


class ValidatorExamplesTest(unittest.TestCase):
    """The pinned validator against the examples fetched with it."""

    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / "formats" / "examples"
        cls.expected = read_json(cls.root / "expected-errors.json")

    def test_every_valid_example_validates(self):
        valid = sorted((self.root / "valid").glob("*.json"))
        self.assertGreaterEqual(len(valid), 7)
        for path in valid:
            self.assertEqual(example_errors(path), [], path.name)

    def test_every_invalid_example_fails_with_its_expected_error(self):
        invalid = sorted((self.root / "invalid").glob("*.json"))
        self.assertEqual([p.name for p in invalid], sorted(self.expected))
        for path in invalid:
            errors = example_errors(path)
            self.assertTrue(any(self.expected[path.name] in e for e in errors), f"{path.name}: {errors}")

    def test_toy_example_recomputes_its_id(self):
        toy = read_json(self.root / "valid" / "artifact-set-1--toy.json")
        self.assertEqual(toy["id"], "toy-1.0-1ff31629")
        self.assertEqual(validate_records.canonical_set_hash(toy)[:8], "1ff31629")


class ValidatorStrictnessTest(unittest.TestCase):
    """What the validator refuses beyond json.loads (game-archaeologist formats/README.md)."""

    TOY = (ROOT / "formats" / "examples" / "valid" / "artifact-set-1--toy.json").read_text(encoding="utf-8")

    def run_cli(self, tmp, text):
        path = Path(tmp) / "doc.json"
        path.write_text(text, encoding="utf-8")
        done = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_records.py"), str(path)],
                              capture_output=True, text=True)
        return done.returncode, done.stdout

    def test_the_toy_example_passes_and_each_malformed_variant_fails_by_the_command_line(self):
        variants = {
            "duplicate key": (self.TOY.replace("{", '{"title": "again", ', 1), "duplicate key"),
            "NaN": (self.TOY.replace("{", '{"x": NaN, ', 1), "NaN is not JSON"),
            "lone surrogate": (self.TOY.replace("{", '{"x": "\\ud800", ', 1), "lone surrogate"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.run_cli(tmp, self.TOY)
            self.assertEqual((code, out.startswith("ok:")), (0, True), out)
            for label, (text, words) in variants.items():
                with self.subTest(label):
                    code, out = self.run_cli(tmp, text)
                    self.assertEqual(code, 1, out)
                    self.assertIn(words, out)


if __name__ == "__main__":
    unittest.main()
