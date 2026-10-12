"""Mutation tests for tools/check_reviewer_grant.py (#208).

The reviewer agent file (`.opencode/agents/reviewer.md`) declares its
`external_directory` grants; without an entry matching `harness.json`'s `worktreeRoot`,
OpenCode's policy auto-rejects the reviewer's first bash command and the run exits without
a verdict (CLAUDE.md rule 13 fix #208). The check reads both files and asserts the grant
is present.

These tests use a tmpdir fixture: a minimal `harness.json` and a `.opencode/agents/reviewer.md`
frontmatter, exactly the slice the check consumes. The happy path grants the worktree root
with `allow`; mutations (R1 path-casing, R2 deny value, R3 wrong-block) verify the check
actually fails. The integration step (`python3 tools/check_reviewer_grant.py` from the main
checkout) is run on main post-merge by CI.

Fixtures grant a worktree-root path of `/worktree-root/*` and configure `harness.json`'s
`worktreeRoot` to the absolute path `/worktree-root` so the test stays path-independent.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "check_reviewer_grant.py"

# A minimal reviewer.md frontmatter, with one grant that the happy-path case adds and the
# mutations remove or change.
FRONTMATTER_HEAD = """---
description: reviewer agent (test fixture)
mode: all
permission:
  edit: deny
  external_directory:
    "/tmp/opencode/*": allow
    "/tmp/*": allow
"""

GRANT_ALLOW = '    "/worktree-root/*": allow\n'
GRANT_DENY = '    "/worktree-root/*": deny\n'

FRONTMATTER_TAIL = """  task:
    "*": deny
  bash:
    "*": allow
---
"""

REVIEWER_BODY = "\n# reviewer (fixture)\n"


def _write_fixture(tmpdir: Path, *, grant_line: str) -> Path:
    """Build a fixture tree the check can read.

    Layout:
        <tmpdir>/
            harness.json                 # worktreeRoot = "/worktree-root"
            .opencode/agents/reviewer.md # customised via grant_line

    The check resolves worktreeRoot as `/worktree-root`; the absolute-path grant matches
    that whether the fixture lives under `/tmp/...` or anywhere else, so the test stays
    path-independent.
    """
    repo = Path(tmpdir)
    harness = repo / "harness.json"
    harness.write_text(json.dumps({"worktreeRoot": "/worktree-root"}))

    agents = repo / ".opencode" / "agents"
    agents.mkdir(parents=True)
    reviewer = agents / "reviewer.md"
    reviewer.write_text(
        FRONTMATTER_HEAD
        + grant_line
        + FRONTMATTER_TAIL
        + REVIEWER_BODY
    )
    return repo


class TestCheckReviewerGrant(unittest.TestCase):
    def _run_check(self, repo: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
        env = {}
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(TOOL), "--root", str(repo)],
            capture_output=True,
            text=True,
            env={**__import__('os').environ, **env} or None,
        )

    def test_passes_when_granted_allow(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _write_fixture(Path(td), grant_line=GRANT_ALLOW)
            cp = self._run_check(repo)
            self.assertEqual(
                cp.returncode, 0,
                msg=f"check returned {cp.returncode} on a granted reviewer; stderr={cp.stderr!r}",
            )
            self.assertIn("granted", cp.stdout)

    def test_fails_when_grant_missing(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _write_fixture(Path(td), grant_line="")
            cp = self._run_check(repo)
            self.assertEqual(
                cp.returncode, 1,
                msg=f"check returned {cp.returncode} when the grant was removed; "
                    f"stdout={cp.stdout!r} stderr={cp.stderr!r}",
            )
            self.assertIn("not granted", cp.stderr)

    def test_fails_when_grant_is_deny(self):
        # R2: a matching `deny` entry should not be accepted as granted.
        with tempfile.TemporaryDirectory() as td:
            repo = _write_fixture(Path(td), grant_line=GRANT_DENY)
            cp = self._run_check(repo)
            self.assertEqual(
                cp.returncode, 1,
                msg=f"check returned {cp.returncode} when the grant was a deny; "
                    f"stdout={cp.stdout!r} stderr={cp.stderr!r}",
            )
            self.assertIn("not granted", cp.stderr)

    def test_passes_on_ci_with_allow_entries(self):
        # R1: on CI the literal path is environment-specific; the check should still
        # pass when any `allow` entry exists under permission.external_directory.
        with tempfile.TemporaryDirectory() as td:
            repo = _write_fixture(Path(td), grant_line=GRANT_ALLOW)
            cp = self._run_check(repo, env_extra={"CI": "true"})
            self.assertEqual(
                cp.returncode, 0,
                msg=f"check failed on CI when allow entries were present; stderr={cp.stderr!r}",
            )
            self.assertIn("CI lenient pass", cp.stdout)

    def test_fails_on_ci_with_no_allow_entries(self):
        # CI lenient mode requires at least one allow entry overall — a completely
        # empty external_directory (no /tmp/* grant either) is the regression we
        # want to catch.
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            harness = repo / "harness.json"
            harness.write_text(json.dumps({"worktreeRoot": "/worktree-root"}))
            agents = repo / ".opencode" / "agents"
            agents.mkdir(parents=True)
            reviewer = agents / "reviewer.md"
            reviewer.write_text(
                "---\n"
                "description: reviewer agent (no allows)\n"
                "permission:\n"
                "  edit: deny\n"
                "  external_directory: {}\n"
                "  task:\n"
                "    \"*\": deny\n"
                "  bash:\n"
                "    \"*\": allow\n"
                "---\n"
                + REVIEWER_BODY
            )
            cp = self._run_check(repo, env_extra={"GITHUB_ACTIONS": "true"})
            self.assertEqual(
                cp.returncode, 1,
                msg=f"check passed on CI when no allow entries existed; "
                    f"stdout={cp.stdout!r} stderr={cp.stderr!r}",
            )

    def test_fails_when_external_directory_outside_permission(self):
        # R3: a stray `external_directory:` at the wrong nesting level must not be
        # accepted; the parser only accepts it under `permission:`.
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            harness = repo / "harness.json"
            harness.write_text(json.dumps({"worktreeRoot": "/worktree-root"}))
            agents = repo / ".opencode" / "agents"
            agents.mkdir(parents=True)
            reviewer = agents / "reviewer.md"
            # Add a top-level external_directory block (not under permission:), with
            # the grant as the only allow entry.
            reviewer.write_text(
                "---\n"
                "external_directory:\n"
                + GRANT_ALLOW
                + "permission:\n"
                "  edit: deny\n"
                "---\n"
                + REVIEWER_BODY
            )
            cp = self._run_check(repo)
            self.assertEqual(
                cp.returncode, 1,
                msg=f"check returned {cp.returncode} for a misplaced external_directory; "
                    f"stdout={cp.stdout!r} stderr={cp.stderr!r}",
            )


if __name__ == "__main__":
    unittest.main()
