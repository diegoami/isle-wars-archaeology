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


def _worktree_root(repo: Path) -> Path:
    cfg_path = repo / 'harness.json'
    if not cfg_path.is_file():
        raise SystemExit(f'harness.json not found at {cfg_path}')
    cfg = json.loads(cfg_path.read_text())
    rel = cfg.get('worktreeRoot', '../{repo}-work')
    if '{repo}' in rel:
        rel = rel.replace('{repo}', repo.name)
    return (repo / rel).resolve()


def _frontmatter(path: Path) -> str:
    """Return the YAML frontmatter text of a Markdown file (between the leading `---` fences)."""
    text = path.read_text()
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        raise SystemExit(f'no YAML frontmatter in {path}')
    return m.group(1)


def _parse_external_directory(yaml_text: str) -> tuple:
    """Parse only the `permission.external_directory` block.

    Tracks the indentation stack so a sibling `task:` / `bash:` block does not
    contaminate the parse, and a stray `external_directory:` line at the wrong nesting
    level is ignored. Returns (keys, errors) where keys is the allow/deny map and
    errors is a list of parse problems.
    """
    keys = {}
    errors = []

    in_permission = False
    permission_indent = -1
    in_ext = False
    ext_indent = -1

    for lineno, raw in enumerate(yaml_text.splitlines(), 1):
        # drop trailing comments; preserve leading whitespace
        s = raw.split('#', 1)[0].rstrip()
        if not s.strip():
            continue
        indent = len(s) - len(s.lstrip())
        head = s.lstrip()

        if head == 'permission:':
            in_permission = True
            permission_indent = indent
            in_ext = False
            ext_indent = -1
            continue

        if in_permission:
            # leaving permission: a sibling (same indent) ends the block
            if indent == permission_indent and head != 'permission:':
                in_permission = False
                in_ext = False
                ext_indent = -1
                # fall through so the line is not consumed silently

            if head == 'external_directory:':
                if not in_permission:
                    errors.append(f'line {lineno}: external_directory: outside permission:')
                    continue
                in_ext = True
                ext_indent = indent
                continue

            if in_ext:
                # leaving external_directory: a sibling (same indent as ext_indent) ends the block
                if indent <= ext_indent:
                    in_ext = False
                    ext_indent = -1
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
        # CI: assert the reviewer agent declares at least one allow entry under
        # permission.external_directory, so the whole grant is not silently removed.
        # The literal path varies per environment; the user's local install uses
        # /home/<user>/projects/..., GitHub Actions uses /home/runner/work/...
        allows = sorted(k for k, v in ext.items() if v == 'allow')
        if not allows:
            print(f'check_reviewer_grant: no allow entries in {reviewer}', file=sys.stderr)
            return 1
        print(f'check_reviewer_grant: CI lenient pass; allow entries: {allows}')
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
