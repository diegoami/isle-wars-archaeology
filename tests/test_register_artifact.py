"""register_artifact.py: the canonical manifest, check (directory and listing) and validate."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "register_artifact.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("register_artifact", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ra = load_tool()


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(data)


def manifest_for(directory, **overrides):
    options = dict(label="toy", title="Toy", version="1.0", how="generated", when="2026-10-02")
    options.update(overrides)
    return ra.build_manifest(directory, **options)


def run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=cwd, capture_output=True, text=True
    )


def make_repo(root):
    root = Path(root)
    (root / "artifacts").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return root


class ManifestTest(unittest.TestCase):
    def test_manifest_then_check_roundtrips(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            write(data / "sub" / "b.bin", b"bravo")
            manifest = manifest_for(data)
            self.assertTrue(manifest["id"].startswith("toy-"))
            self.assertEqual(manifest["id"], "toy-" + ra.canonical_set_hash(manifest)[:8])
            self.assertEqual(ra.manifest_errors(manifest), [])
            problems, unlisted = ra.compare(ra.hash_tree(data, manifest), manifest)
            self.assertEqual(problems, [])
            self.assertEqual(unlisted, [])

    def test_one_flipped_byte_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            manifest = manifest_for(data)
            write(data / "a.txt", b"alphb")
            problems, unlisted = ra.compare(ra.hash_tree(data, manifest), manifest)
            self.assertTrue(any("sha256" in p for p in problems), problems)
            self.assertEqual(unlisted, [])

    def test_runtime_writes_are_excluded_and_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "game.txt", b"game")
            write(data / "SAVE1.sav", b"runtime state")
            manifest = manifest_for(data, runtime_writes=["*.sav"])
            self.assertEqual([f["path"] for f in manifest["files"]], ["game.txt"])
            problems, unlisted = ra.compare(ra.hash_tree(data, manifest), manifest)
            self.assertEqual(problems, [])
            self.assertEqual(unlisted, [])

    def test_exclude_is_not_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "game.txt", b"game")
            write(data / "unins000.dat", b"installer")
            manifest = manifest_for(data, excludes=["unins*"])
            self.assertEqual([f["path"] for f in manifest["files"]], ["game.txt"])
            self.assertNotIn("unins", json.dumps(manifest))

    def test_listing_of_same_files_passes_and_changed_hash_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            write(data / "b.txt", b"bravo")
            manifest = manifest_for(data)
            listing = Path(tmp) / "list.txt"
            listing.write_text(
                "".join(f"{f['sha256']}  {f['bytes']}  {f['path']}\n" for f in manifest["files"])
            )
            observed, problems = ra.read_listing(listing)
            self.assertEqual(problems, [])
            problems, unlisted = ra.compare(observed, manifest)
            self.assertEqual(problems, [])
            self.assertEqual(unlisted, [])
            bad = observed.copy()
            path = manifest["files"][0]["path"]
            size, digest = bad[path]
            bad[path] = (size, "0" * 64)
            problems, _ = ra.compare(bad, manifest)
            self.assertTrue(any("sha256" in p for p in problems), problems)

    def test_unlisted_only_fails_with_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            manifest = manifest_for(data)
            write(data / "extra.txt", b"not registered")
            observed = ra.hash_tree(data, manifest)
            problems, unlisted = ra.compare(observed, manifest)
            self.assertEqual(problems, [])
            self.assertEqual(unlisted, ["extra.txt"])
            problems, unlisted = ra.compare(observed, manifest, strict=True)
            self.assertTrue(any(p.startswith("unlisted:") for p in problems), problems)

    def test_known_errors_recompute_the_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            manifest = manifest_for(data)
            good = {"sets": [{"manifest": manifest, "notes": "test"}]}
            self.assertEqual(ra.known_errors(good), [])
            tampered = json.loads(json.dumps(good))
            tampered["sets"][0]["manifest"]["id"] = "toy-00000000"
            self.assertTrue(ra.known_errors(tampered))


class CliTest(unittest.TestCase):
    def test_manifest_check_and_strict_in_a_temp_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            write(data / "b.bin", b"bravo")

            built = run_cli(
                "manifest", str(data), "--label", "toy", "--title", "Toy", "--version", "1.0",
                "--how", "generated", "--when", "2026-10-02", cwd=repo,
            )
            self.assertEqual(built.returncode, 0, built.stderr)
            manifest = json.loads(built.stdout)
            (repo / "artifacts" / "known.json").write_text(
                json.dumps({"sets": [{"manifest": manifest, "notes": "test"}]})
            )

            checked = run_cli("check", str(data), manifest["id"], cwd=repo)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

            write(data / "a.txt", b"alphb")
            flipped = run_cli("check", str(data), manifest["id"], cwd=repo)
            self.assertEqual(flipped.returncode, 1, flipped.stdout + flipped.stderr)

            write(data / "a.txt", b"alpha")
            write(data / "extra.txt", b"extra")
            unlisted = run_cli("check", str(data), manifest["id"], cwd=repo)
            self.assertEqual(unlisted.returncode, 0, unlisted.stdout + unlisted.stderr)
            self.assertIn("unlisted: extra.txt", unlisted.stdout)
            strict = run_cli("check", str(data), manifest["id"], "--strict", cwd=repo)
            self.assertEqual(strict.returncode, 1, strict.stdout + strict.stderr)

    def test_validate_real_known_json_exits_zero(self):
        result = run_cli("validate", cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
