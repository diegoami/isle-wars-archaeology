# Running notes: `RUN-NOTES.md`

An implementer keeps a file of its own progress in its worktree. If a run is interrupted (wall
clock, a killed process, a crash, the owner), the next round reads it as the handover. It carries
over the goal2-archaeology convention (007ac3a, 2026-10-10), with two corrections for this
repository's git worktrees (below).

## The file
- **Path:** `RUN-NOTES.md` at the worktree root. Never committed, never in a PR body.
- **Ignored:** through the repository's shared exclude, `.git/info/exclude` in the main
  checkout, which every worktree reads. The main session added the line once. An agent checks
  `git check-ignore -q RUN-NOTES.md` and stops and reports if it fails. It never writes the
  exclude itself.
- **Created** by the implementer on its first step.

```
# RUN-NOTES — <task id>

## Plan
1. <step one>
2. ...

## Progress
- <timestamp> <one line: what was done>

## Notes
- <timestamp> <one line: anything the next round needs>

## END
- last commit: <sha>
- PR state: <open / draft / ready / merged>
- deferred: <bullets, or "none">
```

- **Plan:** written once, from the brief's steps.
- **Progress:** one line after each commit, or each meaningful cluster of tool calls.
- **Notes:** abandoned approaches, decisions, surprises, blockers.
- **END:** the last block, before the agent detaches its worktree or stops.

Progress and Notes are append-only: a line that turns out wrong gets a new line saying so.

## The rules
- **Implementer** (`.opencode/agents/implementer.md`): read it first; append, never rewrite; write
  the END block before detaching. Never stage it.
- **Reviewer** (`.opencode/agents/reviewer.md`): when the brief carries the implementer's notes,
  read them before the diff, and grade against the design as well as the result. The notes are
  the implementer's account, not evidence.
- **Main session:** the reviewer's worktree is a fresh checkout of the PR head, so the
  implementer's untracked file is not in it. Paste the implementer's `RUN-NOTES.md` (from
  `~/projects/isle-wars-archaeology-work/<worktree>/RUN-NOTES.md`) into the review brief under
  "The implementer's RUN-NOTES". When a run is interrupted, read it before resuming or re-routing
  (rule 25).

## The two corrections to the goal2 text
1. In a git worktree, `.git` is a file (`gitdir: …/.git/worktrees/<name>`), so
   `printf 'RUN-NOTES.md\n' >> .git/info/exclude` fails there. The exclude that applies is the
   shared one in the main checkout's `.git/`, which is outside the agent's worktree. OpenCode's
   `external_directory` rule could reject a write to it and discard the run.
2. A reviewer never finds the file at its own worktree root, because the file is untracked in the
   implementer's worktree. It reaches the reviewer only through the brief.

## Why
- **An interrupted run** (today's WSL crashes cost fix #141 two rounds of work): the next round
  reads what was tried, what landed and what did not.
- **A long run:** `cat` the file mid-run to see where the agent is, instead of reading the
  OpenCode database.
- **The reviewer** gets the design rationale and the deferred items.
