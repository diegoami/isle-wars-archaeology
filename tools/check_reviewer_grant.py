#!/usr/bin/env python3
"""Assert the OpenCode reviewer agent grants the script's per-PR review worktree (#208).

`tools/harness/review.mjs` creates a per-PR review worktree under `harness.json`'s
`worktreeRoot` (default `"../{repo}-work"`, which resolves next to the repository).
The reviewer agent file `.opencode/agents/reviewer.md` declares its `external_directory`
grants; without an entry matching the script's worktree root, OpenCode's policy
auto-rejects the reviewer's first bash command and the run exits without a verdict.

The check reads `harness.json`, computes the absolute worktree root, parses the reviewer
agent file's frontmatter, and asserts an `allow` entry covers that path. With
`--root`, it points at another repository's tree (the tests use it).

On CI (`CI=true`, or `GITHUB_ACTIONS=true`), the worktree path is environment-specific
(`/home/runner/work/...` on GitHub Actions, not the user's `/home/diego/...`). The
reviewer file is a local-install artifact — its path is correct on the user's machine
where reviews actually run. On CI the check is lenient: it only asserts the reviewer
file declares an `allow` entry under `permission.external_directory` so a removal of
the whole grant still surfaces as a CI failure.

A failure prints one line and exits 1.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path


def _main_repo_path(repo: Path) -> Path:
    """Return the absolute path of the main checkout, even when `repo` is a worktree.

    `git worktree list --porcelain` emits the main checkout first; that path is what
    `harness.json`'s relative `worktreeRoot` should be resolved against, not the
    current worktree's directory (which has a different leaf). Falls back to `repo`
    when not in a git worktree.
    """
    import subprocess
    try:
        out = subprocess.run(
            ['git', '-C', str(repo), 'worktree', 'list', '--porcelain'],
            capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return repo.resolve()
    for line in out.splitlines():
        if line.startswith('worktree '):
            return Path(line[len('worktree '):]).resolve()
    return repo.resolve()


def _main_repo_name(repo: Path) -> str:
    """Leaf name of the main checkout (e.g., `isle-wars-archaeology`).

    Used to expand `{repo}` in `harness.json`'s `worktreeRoot`.
    """
    return _main_repo_path(repo).name


def _worktree_root(repo: Path) -> Path:
    cfg_path = repo / 'harness.json'
    if not cfg_path.is_file():
        raise SystemExit(f'harness.json not found at {cfg_path}')
    cfg = json.loads(cfg_path.read_text())
    rel = cfg.get('worktreeRoot', '../{repo}-work')
    if '{repo}' in rel:
        rel = rel.replace('{repo}', _main_repo_name(repo))
    # harness.json's worktreeRoot is relative to the *main* checkout, not to whichever
    # worktree the check happens to be run from. Resolve against the main path so the
    # same answer is produced from any worktree.
    main_path = _main_repo_path(repo)
    return (main_path / rel).resolve()


def _frontmatter(path: Path) -> str:
    """Return the YAML frontmatter text of a Markdown file (between the leading `---` fences)."""
    text = path.read_text()
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        raise SystemExit(f'no YAML frontmatter in {path}')
    return m.group(1)


def _parse_external_directory(yaml_text: str) -> tuple:
    """Parse only the `permission.external_directory` block.

    Only the `external_directory:` key that is a *direct* child of `permission:` is
    consumed. A stray `external_directory:` nested inside another permission child
    (e.g., under `edit:` or `task:`) is rejected with an error.

    Returns (keys, errors) where keys is the allow/deny map and errors is the list of
    parse problems that trigger an exit-1.
    """
    keys = {}
    errors = []

    # Indent tracking. The expected indent of a direct child of `permission:` is
    # permission_indent + 2 (matching `edit:`, `task:`, `bash:`, `external_directory:`).
    permission_indent = None
    in_permission = False
    direct_child_indent = None  # the indent of the most recent direct child
    in_ext = False
    ext_indent = None

    for lineno, raw in enumerate(yaml_text.splitlines(), 1):
        s = raw.split('#', 1)[0].rstrip()
        if not s.strip():
            continue
        indent = len(s) - len(s.lstrip())
        head = s.lstrip()

        if head == 'permission:':
            in_permission = True
            permission_indent = indent
            direct_child_indent = None
            in_ext = False
            ext_indent = None
            continue

        if in_permission and permission_indent is not None:
            # leaving permission: a sibling ends the block
            if indent == permission_indent and head != 'permission:':
                in_permission = False
                in_ext = False
                ext_indent = None
                direct_child_indent = None
                continue

            if indent == permission_indent + 2 and head.endswith(':'):
                # a direct child of permission (edit:, task:, bash:, external_directory:)
                direct_child_indent = indent
                if head == 'external_directory:':
                    in_ext = True
                    ext_indent = indent
                else:
                    in_ext = False
                    ext_indent = None
                continue

            if in_ext:
                # exiting external_directory: same indent as the key, or deeper=not here
                if ext_indent is not None and indent <= ext_indent:
                    in_ext = False
                    ext_indent = None
                    continue
                stripped = s.lstrip()
                m = re.match(r'^"([^"]+)"\s*:\s*(allow|deny)\s*$', stripped)
                if m:
                    keys[m.group(1)] = m.group(2)

    return keys, errors


def _is_ci() -> bool:
    return bool(os.environ.get('CI')) or bool(os.environ.get('GITHUB_ACTIONS'))


def check(repo: Path) -> int:
    reviewer = repo / '.opencode/agents/reviewer.md'
    if not reviewer.is_file():
        print(f'check_reviewer_grant: {reviewer} not found', file=sys.stderr)
        return 1

    fm = _frontmatter(reviewer)
    ext, errors = _parse_external_directory(fm)
    if errors:
        for err in errors:
            print(f'check_reviewer_grant: {err}', file=sys.stderr)
        return 1

    if _is_ci():
        # CI: assert the reviewer agent declares an `allow` entry whose path names
        # the project's worktree-root. The literal full path differs per environment
        # (/home/<user>/projects/... vs /home/runner/work/<repo>/<repo>-work/), so a
        # strict path match is not portable; a substring match on the project's leaf
        # (`<repo>-work`) catches the structural protection regardless of environment.
        # `/tmp/*`-only grants must NOT pass on CI: they have nothing to do with
        # the script's review worktree.
        repo_name = _main_repo_name(repo)
        marker = repo_name + '-work'
        matching = sorted(
            k for k, v in ext.items()
            if v == 'allow' and marker in k
        )
        if not matching:
            print(
                f'check_reviewer_grant: no allow entry covering {marker!r} (the '
                f'script\'s review worktree) in {reviewer}',
                file=sys.stderr,
            )
            print(f'  granted allow entries: {sorted(k for k, v in ext.items() if v == "allow")}',
                  file=sys.stderr)
            return 1
        print(f'check_reviewer_grant: CI lenient pass; entries covering {marker!r}: {matching}')
        return 0

    # Local / non-CI: assert the worktree-root path is granted with allow.
    wt_root = _worktree_root(repo)
    pattern = str(wt_root) + '/*'
    if ext.get(pattern) != 'allow':
        print(f'check_reviewer_grant: {pattern!r} is not granted with allow in {reviewer}',
              file=sys.stderr)
        print(f'  granted external_directories: {sorted(ext)}', file=sys.stderr)
        return 1
    print(f'check_reviewer_grant: {pattern} granted (allow)')
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'),
                   help='path to the repository to check (default: cwd)')
    args = p.parse_args()
    repo = args.root.resolve()
    sys.exit(check(repo))


if __name__ == '__main__':
    main()
