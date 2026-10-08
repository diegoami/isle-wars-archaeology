T37 review (Luna)

Review PR #112: https://github.com/diegoami/isle-wars-archaeology/pull/112
Branch: task/T37-wine-driver-task-file
Head: 86eacedb3d3794c1e024d3d95963331bb8a32bce
Base: main
Issue: #109 (T37, the meta-task; this PR writes T38, the concrete task file)

## Task context

T37 is the **meta-task** that produces the **concrete task file** for
the first model-driven Wine run. The rule 18 carve-out (CLAUDE.md
9cbf505, owner 2026-10-08) permits a model agent to run the original
Pro binary under Wine on the user's machine, under constraints A–G.
T35 produced the F019 hash table the gate reads. T36 produced the
gate in `tools/check_no_originals.py`. T37's deliverable is the
*next* task file — **T38** — that names the implementer, the
reviewer, the difficulty, the "Why a run is made" section, the
Done-when, and the Merge-after list, ready to be dispatched.

The full T37 brief is at `docs/tasks/T37.md` (in `main`). The
concrete T38 task file is at `docs/tasks/T38.md` (in this PR).

This is an **easy** task (rule 6): a markdown task file plus a
one-line cross-reference in `walkthroughs/video-walkthrough.md`.
The implementer is **GLM-5.3 Flash on Z.AI** (the harness's default
chain's first rung). The reviewer is **GPT-5.6 Luna on OpenAI**
(cross-family).

## What the PR does

- Writes `docs/tasks/T38.md` per the T37 brief, naming the implementer,
  the reviewer, the difficulty, the "Why a run is made" section, the
  Done-when (respecting constraints A–G of the rule 18 carve-out), and
  the Merge-after list. The task file references the F019 hash table
  (T35) and the `check_no_originals.py` gate (T36) as preconditions.
- Adds the T38 row to `docs/tasks/README.md`.
- Adds a one-line cross-reference in `walkthroughs/video-walkthrough.md`
  under the "Model plays under Wine" section's "Where to start"
  subsection.
- Closes issue #109 (T37's meta-task is done; the deliverable is T38).
- Confirmed a synthetic wine-on-user-machine record passes the T36
  gate (per the brief's "Why a run is made" gate-keeping step).

## Blocking means

Any one is enough; a blocking finding means rework, never approve.

1. A Done-when line fails, or cannot be run as written. The T37
   brief's Done-when has six items; the T38 task file's Done-when
   should also have a numbered list with checkable conditions. Every
   numbered line must be runnable as written.
2. What this task protects is the **shape of the entry gate for the
   first model-driven Wine run**. T38's task file is the contract
   that future dispatches (the first model-driven run) will follow.
   If T38 names the wrong implementer, the wrong reviewer, the wrong
   difficulty, or the wrong "Why a run is made" — i.e. anything that
   doesn't respect the rule 18 carve-out's constraints A–G — the
   first Wine run will be mis-dispatched and CI will either reject
   it (because of the T36 gate) or, worse, accept it without the
   right safeguards.
3. Behaviour the task forbids: a "the human" wording amendment in
   bulk across `spec/` or `findings/`. The carve-out's constraint G
   says wording is amended per claim, not in bulk. The T38 task
   file should say so, and the implementer should not have
   bulk-edited anything in this PR.
4. Project-specific: a constant with no evidence; a status written
   into a document; a missing cross-reference between the T38 task
   file and the F019 table / T36 gate.

Not blocking: wording, style, defects in code the PR did not
change. File those as follow-ups.

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop
at the first blocking finding: finish reading the whole diff and the
task files (T37 and T38), check every Done-when line and every item
under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the full
  diff for anything you have not yet rated, and say "Final pass
  done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding
  you held back because an earlier one was already blocking is a
  review defect: if two problems share a cause, list both and say
  so.
- Do not rely on a later round. The author fixes everything you
  list, and the next review checks those fixes and new code only,
  not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff,
  say which files or sections you did not cover. Do not approve in
  that case.

## What to look at

- `docs/tasks/T38.md` — the new task file. Read in full. Verify it
  names the implementer, the reviewer, the difficulty, the "Why a
  run is made" section, the Done-when, and the Merge-after list.
  Verify the Done-when respects constraints A–G of the rule 18
  carve-out. Verify the task file references T35 (F019 table) and
  T36 (gate) as preconditions. Verify the "Why a run is made"
  section names the static reading (rule 24) the run corroborates.
- `docs/tasks/README.md` — the new T38 row.
- `walkthroughs/video-walkthrough.md` — the one-line cross-reference
  in the "Where to start" subsection.
- `findings/F019-pro-setup-rules.md` and `tools/check_no_originals.py`
  — verify the T38 task file's references to the F019 table and the
  T36 gate are accurate.
- The T37 brief (at `docs/tasks/T37.md`) — verify the T38 task file
  matches the shape the T37 brief specified (implementer/reviewer/
  difficulty/Why/Done-when/Merge-after).

## What NOT to check

- T38's *future* dispatches (the actual model-driven run) are not
  in scope. T38 is a task file; the dispatch that uses it comes
  after this PR merges.
- T35, T36 — already merged; not the subject of this review.

## Effort and chain

- Effort: `high` (Luna's default).
- Chain: harness.json's `reviewer.chain` = `[luna]`. Family check:
  Z.AI (GLM) implemented, OpenAI (Luna) reviews. Different
  families. No family conflict.

## Output

Post the verdict as one PR comment, in the format
`tools/harness/post-review.mjs` writes: a one-line header ("T37
review (Luna)"), then the body, then "Final pass done" as the last
line before the verdict, then `APPROVE` or `REQUEST CHANGES` (per
the review-brief blocking-means rule, a single blocking finding
means rework — never approve). The harness reads the verdict from
the comment.

Final pass done.
