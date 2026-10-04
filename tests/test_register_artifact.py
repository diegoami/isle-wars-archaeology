"""The pinned tools/register_artifact.py (upstream bytes), and the two seals that call it.

The tool is game-archaeologist's (archaeology.json pins its commit, tests/test_formats.py pins its
bytes), so its own rules are tested upstream. Here: the repository's use of it. The manifest, check
(directory and listing) and validate commands round-trip; what the stricter rules refuse stays
refused; `artifacts/known.json` validates; and the two seals that depend on it keep refusing:
`prefix.verify_game_copy` (the Pro prefix's game copy, which calls `hash_tree` and `compare`
in-process) and `rundir.strict_check` (the DOS run copy, which runs `check --strict`).
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "register_artifact.py"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "setup" / "iwp"))
sys.path.insert(0, str(ROOT / "setup" / "iw-dos"))


def load_tool():
    spec = importlib.util.spec_from_file_location("register_artifact", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ra = load_tool()
import prefix  # noqa: E402
import rundir  # noqa: E402


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(data)


def manifest_for(directory, **overrides):
    options = dict(label="toy", title="Toy", version="1.0", how="generated", when="2026-10-02")
    options.update(overrides)
    return ra.build_manifest(directory, **options)


def check_tree(directory, manifest, strict=False):
    """(problems, unlisted) of a directory against a manifest: the tree's own problems, then the comparison's."""
    observed, tree_problems = ra.hash_tree(directory, manifest)
    problems, unlisted = ra.compare(observed, manifest, strict=strict)
    return tree_problems + problems, unlisted


def run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=cwd, capture_output=True, text=True
    )


def make_repo(root):
    """A working directory whose artifacts/known.json the tool reads (it reads the working directory's)."""
    root = Path(root)
    (root / "artifacts").mkdir(parents=True, exist_ok=True)
    return root


def register(repo, manifest):
    (repo / "artifacts" / "known.json").write_text(
        json.dumps({"sets": [{"manifest": manifest, "notes": "test"}]})
    )


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
            problems, unlisted = check_tree(data, manifest)
            self.assertEqual(problems, [])
            self.assertEqual(unlisted, [])

    def test_one_flipped_byte_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            manifest = manifest_for(data)
            write(data / "a.txt", b"alphb")
            problems, unlisted = check_tree(data, manifest)
            self.assertTrue(any("sha256" in p for p in problems), problems)
            self.assertEqual(unlisted, [])

    def test_runtime_writes_are_excluded_and_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "game.txt", b"game")
            write(data / "SAVE1.sav", b"runtime state")
            manifest = manifest_for(data, runtime_writes=["*.sav"])
            self.assertEqual([f["path"] for f in manifest["files"]], ["game.txt"])
            self.assertEqual(manifest["runtime_writes"], ["*.sav"])
            problems, unlisted = check_tree(data, manifest, strict=True)
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
            problems, unlisted = check_tree(data, manifest)
            self.assertEqual(problems, [])
            self.assertEqual(unlisted, ["extra.txt"])
            problems, unlisted = check_tree(data, manifest, strict=True)
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


class StricterRulesTest(unittest.TestCase):
    """What the pinned tool refuses that this repository's copy accepted (game-archaeologist U21, U24)."""

    def test_a_manifest_naming_a_path_that_leaves_the_set_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            manifest = manifest_for(data)
            for bad_path in ("../a.txt", "/etc/a.txt", "dir\\a.txt", "C:/a.txt"):
                with self.subTest(bad_path):
                    bad = json.loads(json.dumps(manifest))
                    bad["files"][0]["path"] = bad_path
                    bad["id"] = "toy-" + ra.canonical_set_hash(bad)[:8]    # the id is canonical: only the path is wrong
                    self.assertTrue(any("path" in e for e in ra.manifest_errors(bad)), bad_path)
                    problems, _ = ra.compare({"a.txt": (5, manifest["files"][0]["sha256"])}, bad)
                    self.assertTrue(problems)

    def test_a_symbolic_link_out_of_the_directory_and_a_special_file_fail_check_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            manifest = manifest_for(data)
            register(repo, manifest)
            write(Path(tmp) / "outside.txt", b"elsewhere")
            os.symlink(Path(tmp) / "outside.txt", data / "link.txt")
            os.mkfifo(data / "pipe")
            checked = run_cli("check", str(data), manifest["id"], cwd=repo)
            self.assertEqual(checked.returncode, 1, checked.stdout)
            self.assertIn("link.txt: symbolic link to outside the directory", checked.stdout)
            self.assertIn("pipe: not a regular file or a directory", checked.stdout)
            built = run_cli("manifest", str(data), "--label", "toy", "--title", "Toy", "--version", "1.0",
                            "--how", "generated", "--when", "2026-10-02", "--exclude", "link.txt",
                            "--exclude", "pipe", cwd=repo)
            self.assertEqual(built.returncode, 1, "an excluded special file still refuses the directory")
            self.assertIn("pipe", built.stdout)

    def test_writes_is_an_alias_of_runtime_write_and_when_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            write(data / "s.sav", b"state")
            built = run_cli("manifest", str(data), "--label", "toy", "--title", "Toy", "--version", "1.0",
                            "--how", "generated", "--writes", "*.sav", cwd=repo)
            self.assertEqual(built.returncode, 0, built.stdout)
            manifest = json.loads(built.stdout)
            self.assertEqual(manifest["runtime_writes"], ["*.sav"])
            self.assertEqual([f["path"] for f in manifest["files"]], ["a.txt"])
            self.assertRegex(manifest["acquired"]["when"], r"^\d{4}-\d{2}-\d{2}$")


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
            self.assertEqual(built.returncode, 0, built.stdout)
            manifest = json.loads(built.stdout)
            register(repo, manifest)

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

    def test_check_list_against_known_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            write(data / "sub" / "b.bin", b"bravo")
            manifest = manifest_for(data)
            register(repo, manifest)
            listing = Path(tmp) / "list.txt"
            listing.write_text(
                "".join(f"{f['sha256']}  {f['bytes']}  {f['path']}\n" for f in manifest["files"])
            )

            checked = run_cli("check", "--list", str(listing), manifest["id"], cwd=repo)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertIn(f"ok: {manifest['id']}", checked.stdout)

            changed_path = manifest["files"][0]["path"]
            listing.write_text(
                "".join(
                    f"{'0' * 64 if f['path'] == changed_path else f['sha256']}  {f['bytes']}  {f['path']}\n"
                    for f in manifest["files"]
                )
            )
            changed = run_cli("check", "--list", str(listing), manifest["id"], cwd=repo)
            self.assertEqual(changed.returncode, 1, changed.stdout + changed.stderr)
            self.assertIn("sha256", changed.stdout)

    def test_missing_listed_file_fails_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            data = Path(tmp) / "set"
            write(data / "a.txt", b"alpha")
            write(data / "b.txt", b"bravo")
            manifest = manifest_for(data)
            register(repo, manifest)

            (data / "b.txt").unlink()
            missing = run_cli("check", str(data), manifest["id"], cwd=repo)
            self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
            self.assertIn("b.txt: missing", missing.stdout)
            self.assertNotIn(f"ok: {manifest['id']}", missing.stdout)

    def test_validate_real_known_json_exits_zero(self):
        result = run_cli("validate", cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validate_refuses_a_known_json_with_a_duplicate_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            text = (ROOT / "artifacts" / "known.json").read_text(encoding="utf-8")
            (repo / "artifacts" / "known.json").write_text(text.replace("{", '{"sets": [], ', 1), encoding="utf-8")
            result = run_cli("validate", cwd=repo)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("duplicate key", result.stdout)


class SealCallersTest(unittest.TestCase):
    """The two seals' copy checks, driven through the real callers on a synthetic set.

    Each case damages a verified copy in one way, so removing the check that refuses it is seen:
    a changed byte (same size, so only the sha256 differs), an unlisted file, a missing file, and
    for the DOS copy the `--strict` that makes an unlisted file a failure."""

    FILES = {"a.txt": b"alpha", "xtras/b.dat": b"beta"}

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(os.path.realpath(self._tmp.name))
        self.game = self.tmp / "game"
        for name, data in self.FILES.items():
            write(self.game / name, data)
        self.manifest = manifest_for(self.game, label="synthetic-1.0")
        self.repo = make_repo(self.tmp / "repo")
        register(self.repo, self.manifest)
        for patcher in (mock.patch.object(prefix, "manifest", return_value=self.manifest),
                        mock.patch.object(rundir, "SET_ID", self.manifest["id"])):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.install = self.tmp / "install"        # nothing there: the copy is its own, whatever IWP_DIR says

    def damages(self):
        return {
            "a changed byte of the same size": (lambda: write(self.game / "a.txt", b"alphb"), "a.txt: sha256"),
            "a changed size": (lambda: write(self.game / "xtras/b.dat", b"be"), "xtras/b.dat: 2 bytes"),
            "an unlisted file": (lambda: write(self.game / "extra.txt", b"x"), "extra.txt"),
            "a missing file": (lambda: (self.game / "a.txt").unlink(), "a.txt: missing"),
        }

    def test_the_prefix_game_copy_check_passes_the_registered_files(self):
        self.assertEqual(prefix.verify_game_copy(self.game, self.install), [])

    def test_the_prefix_game_copy_check_refuses_each_damage(self):
        for label, (damage, words) in self.damages().items():
            with self.subTest(label):
                self.setUp_copy()
                damage()
                problems = prefix.verify_game_copy(self.game, self.install)
                self.assertTrue(any(words in p for p in problems), problems)

    def test_the_prefix_game_copy_check_refuses_a_special_file_and_a_link_out_of_the_copy(self):
        os.mkfifo(self.game / "pipe")
        self.assertTrue(any("pipe" in p for p in prefix.verify_game_copy(self.game, self.install)))
        (self.game / "pipe").unlink()
        write(self.tmp / "outside.txt", b"elsewhere")
        os.symlink(self.tmp / "outside.txt", self.game / "link.txt")
        problems = prefix.verify_game_copy(self.game, self.install)
        self.assertTrue(any("link.txt" in p for p in problems), problems)

    def test_the_prefix_game_copy_check_reports_what_the_tool_cannot_observe(self):
        """A name the tool refuses (a backslash) is in no listing and no hash, so only the tool's own
        report of it stops the copy: dropping that report would let it pass unseen."""
        write(self.game / "back\\slash.txt", b"x")
        problems = prefix.verify_game_copy(self.game, self.install)
        self.assertTrue(any("backslash" in p for p in problems), problems)

    def test_the_prefix_game_copy_check_allows_a_runtime_write_of_the_set(self):
        manifest = manifest_for(self.game, label="synthetic-1.0", runtime_writes=["*.sav"])
        write(self.game / "SAVE1.sav", b"grown by the game")
        with mock.patch.object(prefix, "manifest", return_value=manifest):
            self.assertEqual(prefix.verify_game_copy(self.game, self.install), [])

    def setUp_copy(self):
        for name, data in self.FILES.items():
            write(self.game / name, data)
        for stray in ("extra.txt",):
            if (self.game / stray).exists():
                (self.game / stray).unlink()

    def test_the_dos_run_copy_check_passes_and_refuses_each_damage(self):
        ok, text = rundir.strict_check(self.game, self.repo)
        self.assertTrue(ok, text)
        for label, (damage, words) in self.damages().items():
            with self.subTest(label):
                self.setUp_copy()
                damage()
                ok, text = rundir.strict_check(self.game, self.repo)
                self.assertFalse(ok, f"{label} was accepted: {text}")
                self.assertIn(words, text)

    def test_the_dos_run_copy_check_runs_strict(self):
        """An unlisted file is only a failure under --strict; without it the tool prints it and exits 0."""
        write(self.game / "extra.txt", b"x")
        self.assertEqual(run_cli("check", str(self.game), self.manifest["id"], cwd=self.repo).returncode, 0)
        ok, text = rundir.strict_check(self.game, self.repo)
        self.assertFalse(ok)
        self.assertIn("unlisted: extra.txt", text)


if __name__ == "__main__":
    unittest.main()
