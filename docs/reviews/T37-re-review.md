T37 review (Luna) (rework)

Re-review PR #112 against the rework's new commit.
PR: https://github.com/diegoami/isle-wars-archaeology/pull/112
Branch: task/T37-wine-driver-task-file
Head: d4228c8213af937f6d3a5d6e5cad63e86a4dc05b (verify on the PR's actual head — the worktree shows `d4228c8`)
Base: main
Issue: #109

## What changed since the original review

The original review (Luna, effort `high`, posted
2026-10-08T15:00:52Z) returned six blocking findings on the T38
task file's Done-when section. The pattern was the same across most
of them: literal placeholder syntax (`<name>`, `<base>`), references
to files that don't exist yet, and a project-wide question-map gate
that exits non-zero on pre-existing failures.

One new commit on the branch fixes all six:

- `d4228c8` — `T37 rework: T38's Done-when rewritten as runnable
  commands (Luna's six findings)`. The implementer rewrote the
  Done-when section to use existing tools (`git status`, `find`,
  `git diff --name-only origin/main -- <path>`, `tools/validate_records.py`,
  `tools/check_links.py`, `tools/check_no_originals.py`) and named
  the new tools the T38 implementer will write (a count checker, a
  wine-manifest class checker, a wine-driver dispatcher). The
  question-map gate is scoped to PR-touched files per the T35
  amendment pattern, with pre-existing failures named.

## What I want from the re-review

For each of your six original findings, **re-verify the fix on the
new head**:

- **R1 (DW1 locality):** the new DW1 should actually touch
  `/mnt/c/Temp/iwp-shots/wine/`, not just the worktree. Confirm the
  command is runnable; if you can run it (worktrees may not have
  the path), confirm it would work.
- **R2 (DW2 recording-class constraint):** the new DW should
  enforce `class: "recording"` (not `screenshot`). Confirm a checker
  exists or is named, and that the new check is in the chain.
- **R3 (DW2 `--batch <name>`):** the new DW should not use literal
  placeholder syntax. Confirm the named batches (`cmb-accumulation`
  and `bomb-sampling`) appear in the commands, and the dispatcher
  contract is testable.
- **R4 (DW5 `<base>`):** the new DW should use a concrete base
  (`origin/main` is the simplest). Confirm.
- **R5 (DW7 same `<base>`):** same as R4.
- **R6 (DW9 question-map gate):** the new DW should scope the gate
  to PR-touched files and name the pre-existing failures in the PR
  description (or omit the gate from "must exit 0" and put it in a
  follow-up). Confirm the scoping is applied.

If all six are fixed, approve. If any fails, REQUEST CHANGES with
the specific command that still doesn't run and what it should do.

## What NOT to verify

- The T38 task file's earlier sections (Implementer, Reviewer, "Why
  a run is made", Scope, Hazards) — your original review found no
  defects there; the rework is scoped to the Done-when section.
- T35, T36 — already merged; not the subject of this review.

## Effort and chain

- Effort: `high` (Luna's default).
- Chain: `[luna]`. Family check: Z.AI (GLM) implemented, OpenAI
  (Luna) reviews. Different families.

Final pass done.
