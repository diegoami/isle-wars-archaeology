PR #189 review (GPT-6.1 Sol)

You review PR #189 at b8490264e775ad4770551ff10a05a7e01a26d10b. You did not write it; a Claude
session did. The PR body is the task: read it with `gh pr view 189`. There is no task file; the
PR body's Scope and "Done when" block stand in for one.

What the PR does, in short: it cuts the harness back to what worked in practice. A Claude
subagent (or the main session) implements, and one OpenCode model of another family reviews.
Before each implementation and each review, the owner is asked one question. The roster is
switchable with `switch-model.mjs` (`implementer.default`, `reviewer.default`, `blocked`). The
session's family comes from `ANTHROPIC_BASE_URL` (`sessionFamily()`). It removes `implement.mjs`,
`choose.mjs`, the quota chooser and the chains, and rewrites CLAUDE.md rule 6, `docs/process.md`,
`docs/models.md` and the skills.

0. Prove the tree: HEAD is b8490264e775ad4770551ff10a05a7e01a26d10b and the diff against
   origin/main is the PR's; findings name its files.
1. Re-run every line of the PR body's "Done when" block yourself, and account for each (L32).
   The PR's evidence is no proof.
2. Every changed file and behaviour is one the PR body's Scope names (L44); docs it makes wrong
   are updated. Look for references the PR left behind to removed files (`implement.mjs`,
   `choose.mjs`, `lib/quota.mjs`, `task-agent*.md`, `--hard`, `--sol`, `--second-opinion`) in
   docs, skills, hooks, tests and CI.
3. Sweep the diff: tests that pass with the behaviour deleted (mutate, re-run, re-take any
   negative result), branches no input reaches, edge comments without a test.
   Undo a mutation or scratch edit by writing back the file's saved contents (read it first,
   restore it in a `finally`), or commit first; never `git checkout`, `git restore` or `git reset`
   a file with uncommitted work: they return the last commit and destroy the rest. Keep the saved
   copy inside your worktree (`<file>.saved`, deleted afterwards) or in your `mktemp -d` folder.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this PR protects can be got past: the family rule (a reviewer of the implementer's or
   the session's family is refused by `review.mjs` and `switch-model.mjs`; an unknown endpoint
   refuses to review until `HARNESS_SESSION_FAMILY` is set), and the blocked list (a blocked
   model, e.g. DeepSeek on any route, is refused as reviewer or default). A bypass you proved is
   blocking, even when it looks like an edge case. (L47)
3. Behaviour nobody asked for, or a file left broken by a removal (a script, skill, hook, test
   or CI step that still calls a removed file or flag). (L44)
4. A test that passes with the behaviour deleted; a status snapshot written into a document
   (CLAUDE.md rule 3); a rule that names the orchestrator's own model.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the PR protects; otherwise it is a follow-up. (L53)

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking
finding: finish reading the whole diff and the PR body, check every Done-when line and
every item under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the full diff for anything you have
  not yet rated, and say "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an
  earlier one was already blocking is a review defect: if two problems share a cause, list
  both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review
  checks those fixes and new code only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or
  sections you did not cover. Do not approve in that case.

Your final message is the review: the header; the verdict (approve | approve after named fixes |
rework | user decision); per Done-when line `DW<k>: ran <command> → <result>` or
`DW<k>: not run — <reason>`; the findings R1..Rn (file:line, blocking or not); the verdict again
last. Never post it: the script posts it.
