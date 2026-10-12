"""Mutation tests for tools/check_reviewer_grant.py (#208).

The reviewer agent file (`.opencode/agents/reviewer.md`) declares its
`external_directory` grants; without an entry matching `harness.json`'s `worktreeRoot`,
OpenCode's policy auto-rejects the reviewer's first bash command and the run exits without
a verdict (CLAUDE.md rule 13 fix #208). The check reads both files and asserts the grant
is present.

These tests use a tmpdir fixture: a minimal `harness.json` and a `.opencode/agents/reviewer.md`
frontmatter, exactly the slice the check consumes. The happy path grants the worktree root;
the mutation removes that grant and expects exit 1. The integration step (`python3 tools/
check_reviewer_grant.py` from the main checkout) is run on main post-merge by CI; it would
fail in a worktree because `{repo}` substitutes the branch's leaf, not the main checkout's.

Fixtures grant a worktree-root path of `/worktree-root/*` and configure `harness.json`'s
`worktreeRoot` to point at a directory called `worktree-root` next to the fixture root.
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
# mutation removes. `external_directory` block uses four-space indent to match the project's
# YAML style.
FRONTMATTER_HEAD = """---
description: reviewer agent (test fixture)
mode: all
permission:
  edit: deny
  external_directory:
    "/tmp/opencode/*": allow
    "/tmp/*": allow
"""

GRANT_LINE = '    "/worktree-root/*": allow\n'

FRONTMATTER_TAIL = """  task:
    "*": deny
  bash:
    "*": allow
---
"""

REVIEWER_BODY = "\n# reviewer (fixture)\n"


def _write_fixture(tmpdir: Path, *, with_grant: bool) -> Path:
    """Build a fixture tree the check can read.

    Layout:
        <tmpdir>/
            harness.json           # worktreeRoot = "/worktree-root" (absolute, stable)
            .opencode/agents/reviewer.md   # with or without the worktree grant

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
        + (GRANT_LINE if with_grant else "")
        + FRONTMATTER_TAIL
        + REVIEWER_BODY
    )
    return repo


class TestCheckReviewerGrant(unittest.TestCase):
    def _run_check(self, repo: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(TOOL), "--root", str(repo)],
            capture_output=True,
            text=True,
        )

    def test_passes_when_granted(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _write_fixture(Path(td), with_grant=True)
            cp = self._run_check(repo)
            self.assertEqual(
                cp.returncode, 0,
                msg=f"check returned {cp.returncode} on a granted reviewer; stderr={cp.stderr!r}",
            )
            self.assertIn("granted", cp.stdout)

    def test_fails_when_grant_missing(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _write_fixture(Path(td), with_grant=False)
            cp = self._run_check(repo)
            self.assertEqual(
                cp.returncode, 1,
                msg=f"check returned {cp.returncode} when the grant was removed; "
                    f"stdout={cp.stdout!r} stderr={cp.stderr!r}",
            )
            self.assertIn("not granted", cp.stderr)


if __name__ == "__main__":
    unittest.main()
