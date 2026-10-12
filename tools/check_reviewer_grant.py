#!/usr/bin/env python3
"""Assert the OpenCode reviewer agent grants the script's per-PR review worktree (#208).

`tools/harness/review.mjs` creates a per-PR review worktree under `harness.json`'s
`worktreeRoot` (default `"../{repo}-work"`, which resolves next to the repository).
The reviewer agent file `.opencode/agents/reviewer.md` declares its `external_directory`
grants; without an entry matching the script's worktree root, OpenCode's policy
auto-rejects the reviewer's first bash command and the run exits without a verdict.

The check reads `harness.json`, computes the absolute worktree root, parses the reviewer
agent file's frontmatter, and fails unless the worktree-root pattern is granted. With
`--root`, it points at another repository's tree (the tests use it).

A failure prints one line and exits 1.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def _worktree_root(repo: Path) -> Path:
    cfg_path = repo / 'harness.json'
    if not cfg_path.is_file():
        raise SystemExit(f'harness.json not found at {cfg_path}')
    cfg = json.loads(cfg_path.read_text())
    rel = cfg.get('worktreeRoot', '../{repo}-work')
    # {repo} -> the repo directory's leaf name
    if '{repo}' in rel:
        rel = rel.replace('{repo}', repo.name)
    return (repo / rel).resolve()


def _frontmatter(path: Path) -> str:
    """Return the YAML frontmatter text of a Markdown file (between the leading `---` fences)."""
    text = path.read_text()
    # Split on the first two `---` lines (per common frontmatter convention).
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        raise SystemExit(f'no YAML frontmatter in {path}')
    return m.group(1)


def _parse_external_directory(yaml_text: str) -> dict:
    """Tiny parse of the permission.external_directory mapping: one key per line, ": allow/deny".

    Avoids a PyYAML dependency. Each line is `    "<key>": allow`. Other permissions
    (`edit`, `task`, `bash`) are ignored. Comments (`#`) are stripped.
    """
    keys = {}
    in_ext = False
    block_indent = 0
    for line in yaml_text.splitlines():
        s = line.split('#', 1)[0].rstrip()  # drop trailing comments
        if not s.strip():
            continue
        head = s.lstrip()
        if head.startswith('external_directory:') or head == 'external_directory':
            in_ext = True
            # record the leading indent of this key so the grant lines are also indented further
            block_indent = len(s) - len(head)
            continue
        if in_ext:
            # a line at exactly the parent block's indent ends the external_directory block
            indent = len(s) - len(s.lstrip())
            if indent <= block_indent and s.lstrip():
                in_ext = False
                # fall through to handle this line at the parent level (no-op here)
                continue
            if ':' in s:
                stripped = s.lstrip()
                m = re.match(r'^"([^"]+)"\s*:\s*(allow|deny)\s*$', stripped)
                if m:
                    keys[m.group(1)] = m.group(2)
    return keys


def check(repo: Path) -> int:
    wt_root = _worktree_root(repo)
    pattern = str(wt_root) + '/*'
    reviewer = repo / '.opencode/agents/reviewer.md'
    if not reviewer.is_file():
        print(f'check_reviewer_grant: {reviewer} not found', file=sys.stderr)
        return 1
    fm = _frontmatter(reviewer)
    ext = _parse_external_directory(fm)
    if pattern not in ext:
        print(f'check_reviewer_grant: {pattern!r} not granted in {reviewer}', file=sys.stderr)
        print(f'  granted external_directories: {sorted(ext)}', file=sys.stderr)
        return 1
    print(f'check_reviewer_grant: {pattern} granted (allow={ext[pattern]})')
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
