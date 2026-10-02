"""check_no_originals.py: bytes matching a registered artifact set, and .x32, are failures."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "check_no_originals.py"


def run_tool(repo):
    return subprocess.run(
        [sys.executable, str(TOOL)], cwd=repo, capture_output=True, text=True
    )


def write(path, data):
    Path(path).write_bytes(data)


def git_add(repo, name):
    subprocess.run(["git", "add", name], cwd=repo, check=True)


def make_repo(tmp):
    repo = Path(tmp) / "repo"
    (repo / "artifacts").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


class CheckNoOriginalsTest(unittest.TestCase):
    def test_registered_bytes_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            payload = b"synthetic bytes for a registered artifact set, never a real game file"
            (repo / "artifacts" / "known.json").write_text(json.dumps({"sets": [{
                "manifest": {"files": [{
                    "path": "game.bin",
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }]},
                "notes": "test",
            }]}))
            write(repo / "probe.bin", payload)
            git_add(repo, "probe.bin")
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("probe.bin", result.stdout)

    def test_x32_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write(repo / "a.x32", b"a Director Xtra is a DLL")
            git_add(repo, "a.x32")
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("a.x32", result.stdout)

    def test_exe_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write(repo / "GAME.EXE", b"synthetic bytes, not a real executable")
            git_add(repo, "GAME.EXE")
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("GAME.EXE", result.stdout)

    def test_oversize_file_fails(self):
        # The MAX_BYTES branch: a tracked file over 1 MB fails even with a harmless
        # extension and unknown bytes. The payload is synthetic, in a temp repo only.
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write(repo / "big.bin", b"x" * (1024 * 1024 + 1))
            git_add(repo, "big.bin")
            result = run_tool(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("big.bin", result.stdout)
            self.assertIn("over 1048576", result.stdout)

    def test_clean_repo_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo(tmp)
            write(repo / "notes.txt", b"nothing original here")
            git_add(repo, "notes.txt")
            result = run_tool(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
