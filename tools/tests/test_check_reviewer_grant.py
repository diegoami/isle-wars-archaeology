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
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "check_reviewer_grant.py"

# Import the check's helpers directly so the worktree-name substitution can be tested
# without spawning a subprocess.
sys.path.insert(0, str(ROOT / "tools"))
import check_reviewer_grant as crg  # noqa: E402  (the tool under test, beside this file)
_main_repo_path = crg._main_repo_path
_main_repo_name = crg._main_repo_name
_worktree_root = crg._worktree_root

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
GRANT_ALLOW_DEEP = '      "/worktree-root/*": allow\n'  # 6-space indent, for nested fixtures

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


def _write_fixture_with_marker_grant(tmpdir: Path) -> Path:
    """Fixture where the worktreeRoot uses the project name, so the CI lenient
    path's `<project>-work` marker matches.

    worktreeRoot = `../<project>-work` resolves relative to the tmpdir, but the
    check only matches the literal substring, so we add an explicit allow entry
    whose key contains `<project>-work` and the tmpdir's path is the canonical
    name. The grant marker is `Path(<tmpdir>).name + '-work'`, which the check
    picks up directly.
    """
    project_name = Path(tmpdir).name
    repo = Path(tmpdir)
    harness = repo / "harness.json"
    harness.write_text(json.dumps({"worktreeRoot": f"../{project_name}-work"}))

    agents = repo / ".opencode" / "agents"
    agents.mkdir(parents=True)
    reviewer = agents / "reviewer.md"
    grant = f'    "/home/diego/projects/{project_name}-work/*": allow\n'
    reviewer.write_text(
        FRONTMATTER_HEAD
        + grant
        + FRONTMATTER_TAIL
        + REVIEWER_BODY
    )
    return repo


class TestCheckReviewerGrant(unittest.TestCase):
    def test_worktree_root_resolves_against_main_checkout(self):
        # R3 (round 4 + R1 round 5): `_worktree_root` must resolve the
        # worktreeRoot relative to the main checkout, not the worktree the check
        # happens to be invoked from. The test runs in the real worktree
        # (`fix-208/`), a sibling of the main checkout, and asserts the
        # computed path matches the main checkout's expectations.
        #
        # Skipped on CI: on CI the worktree is at /home/runner/work/... and the
        # assertion would diverge; the CI step has its own coverage via
        # test_passes_on_ci_with_marker_grant.
        if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
            self.skipTest('worktree-specific path; not meaningful under CI')
        wt = _worktree_root(ROOT)
        # expected path computed the same way the check does, not hard-coded.
        cfg = json.loads((ROOT / 'harness.json').read_text())
        rel = cfg.get('worktreeRoot', '../{repo}-work').replace(
            '{repo}', _main_repo_name(ROOT),
        )
        expected = (_main_repo_path(ROOT) / rel).resolve()
        self.assertEqual(wt, expected)

    def test_main_repo_path_picks_first_worktree(self):
        # When `repo` is a worktree, `_main_repo_path` returns the main checkout's
        # path (git-worktree-list porcelain's first `worktree` line). Mutating
        # callers' failures on detached worktrees imply they were resolving
        # relative paths against the wrong directory. Skipped on CI where this
        # worktree is not a worktree of the runtime checkout.
        if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
            self.skipTest('worktree-specific path; not meaningful under CI')
        main = _main_repo_path(ROOT)
        self.assertNotEqual(main.resolve(), ROOT.resolve(),
                             msg='_main_repo_path returned the current worktree, '
                                 'not the main checkout')
        # the first worktree line must be the main checkout (the leaf is not
        # a review branch like 'fix-208')
        self.assertNotIn(main.name, ('fix-208', 'T44-task-file', 'T47-task-file'))

    def test_main_repo_name_expands_to_main_checkout(self):
        # `{repo}` in `harness.json`'s worktreeRoot should expand to the main
        # checkout's leaf (e.g., `isle-wars-archaeology`), regardless of which
        # worktree the check runs from. Skipped on CI.
        if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
            self.skipTest('worktree-specific path; not meaningful under CI')
        # the main checkout's name is `isle-wars-archaeology` — the resolved
        # path's leaf, not the current worktree's.
        self.assertEqual(_main_repo_name(ROOT), 'isle-wars-archaeology')

    def _run_check(self, repo: Path, ci: bool = False) -> subprocess.CompletedProcess:
        """Run the check as a subprocess with the test's intended CI mode.

        CI mode is set explicitly per test; it does not inherit from the parent
        process environment, since that would make the non-CI tests run in CI
        mode under any CI host.
        """
        env = {
            k: v
            for k, v in __import__('os').environ.items()
            if k not in ('CI', 'GITHUB_ACTIONS')
        }
        if ci:
            env['CI'] = 'true'
        return subprocess.run(
            [sys.executable, str(TOOL), "--root", str(repo)],
            capture_output=True,
            text=True,
            env=env,
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

    def test_passes_on_ci_with_marker_grant(self):
        # R1 (round 4): CI requires an allow entry whose key contains the project's
        # `<project>-work` marker — `/tmp/*` alone must NOT pass CI.
        with tempfile.TemporaryDirectory() as td:
            repo = _write_fixture_with_marker_grant(Path(td))
            cp = self._run_check(repo, ci=True)
            self.assertEqual(
                cp.returncode, 0,
                msg=f"check failed on CI when the marker grant was present; stderr={cp.stderr!r}",
            )
            self.assertIn("CI lenient pass", cp.stdout)

    def test_fails_on_ci_without_marker_grant(self):
        # R1: a fixture with only /tmp/* allows must fail CI: those are not the
        # script's review worktree grant.
        with tempfile.TemporaryDirectory() as td:
            repo = _write_fixture(Path(td), grant_line=GRANT_ALLOW)
            cp = self._run_check(repo, ci=True)
            self.assertEqual(
                cp.returncode, 1,
                msg=f"check passed on CI when only unrelated allows existed; "
                    f"stdout={cp.stdout!r} stderr={cp.stderr!r}",
            )

    def test_fails_on_ci_with_nonrecursive_marker_grant(self):
        # R1 (round 6): a non-recursive grant (`/path/<marker>` without /* or *)
        # must fail CI — only recursive glob forms actually open the worktree's
        # children to OpenCode, so accepting a literal-only grant is a bypass.
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            project_name = Path(td).name
            harness = repo / "harness.json"
            harness.write_text(json.dumps({"worktreeRoot": f"../{project_name}-work"}))
            agents = repo / ".opencode" / "agents"
            agents.mkdir(parents=True)
            reviewer = agents / "reviewer.md"
            # non-recursive grant: literal directory, no /* or *
            nonrecursive = f'    "/home/diego/projects/{project_name}-work": allow\n'
            reviewer.write_text(
                FRONTMATTER_HEAD
                + nonrecursive
                + FRONTMATTER_TAIL
                + REVIEWER_BODY
            )
            cp = self._run_check(repo, ci=True)
            self.assertEqual(
                cp.returncode, 1,
                msg=f"check passed on CI when the marker grant was non-recursive; "
                    f"stdout={cp.stdout!r} stderr={cp.stderr!r}",
            )

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
            cp = self._run_check(repo, ci=True)
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

    def test_ignores_external_directory_nested_under_permission_child(self):
        # R2 (round 3): an `external_directory:` nested below a *child* of permission
        # (e.g., under `edit:`) is not permission's external_directory; the parser
        # must not collect grants from it.
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            harness = repo / "harness.json"
            harness.write_text(json.dumps({"worktreeRoot": "/worktree-root"}))
            agents = repo / ".opencode" / "agents"
            agents.mkdir(parents=True)
            reviewer = agents / "reviewer.md"
            # permission -> edit -> external_directory with the grant indented to
            # two spaces below the `external_directory:` key (6-space indent); the
            # user's grant is here at the wrong nesting level, so the parser must
            # not pick it up and must report the worktree-root grant as missing.
            reviewer.write_text(
                "---\n"
                "description: nested external_directory\n"
                "permission:\n"
                "  edit:\n"
                "    external_directory:\n"
                + GRANT_ALLOW_DEEP
                + "  task:\n"
                "    \"*\": deny\n"
                "---\n"
                + REVIEWER_BODY
            )
            cp = self._run_check(repo)
            self.assertEqual(
                cp.returncode, 1,
                msg=f"check accepted a nested external_directory grant; "
                    f"stdout={cp.stdout!r} stderr={cp.stderr!r}",
            )
            self.assertIn("not granted", cp.stderr)


if __name__ == "__main__":
    unittest.main()
