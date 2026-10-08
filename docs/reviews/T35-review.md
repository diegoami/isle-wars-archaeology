T35 review (Luna)

Review PR #110: https://github.com/diegoami/isle-wars-archaeology/pull/110
Branch: task/T35-f019-known-good-hash-table
Head: 783eb12dac9ca4d7a0fa741c1cec2614f2c8b6de
Base: main
Issue: #107

## Task context

This is the F019 hash-table companion change to the rule 18 carve-out
(CLAUDE.md 9cbf505, owner 2026-10-08). The carve-out permits a model
agent to run the original Pro binary under Wine on the user's machine,
but the carve-out is only operational when `tools/check_no_originals.py`
enforces constraint F. T36 (the gate, in the dispatch queue) reads the
F019 table this PR produces. T37 (the wine-driver task file) is the
follow-up that consumes the table.

The task is **easy** (rule 6): one-row addition to a markdown finding,
with a contract test that pins the row's shape. The full task file
is at `docs/tasks/T35.md` in the branch.

## What the PR does

- Adds a "Known-good binary hashes" section to
  `findings/F019-pro-setup-rules.md` with one row: set id
  `iwp-2.0-996e86c5`, variant `unregistered`, sha256
  `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`,
  install path, signed-on date.
- Adds a contract test (`experiments/E017-pro-setup-reading/`) that
  fails on a record whose `start_state.sha256` does not match the row,
  and passes on a record whose hash matches.
- Updates `spec/setup.md` to point at the new table; the in-line hash
  stays as the citation for the static reading.
- Brings in two E018 path fixes (cherry-pick of `72c11e7`): the E018
  run records and manifests move to the paths the test_runs invariant
  requires, and the IP1 025.mp4 asset field gets its literal name.
- One empty commit (`783eb12`) on the tip nudges CI to re-run after
  the cherry-pick. The empty commit is a CI-forcing artefact, not
  semantic content.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.

1. A Done-when line fails, or cannot be run as written. The Done-when
   list is in `docs/tasks/T35.md` under "Done when": six numbered
   items covering the F019 row, the contract test, the cross-references
   in `spec/setup.md`, the gates (`check_links.py`,
   `check_pro_question_map.py`, `check_no_originals.py`), and the
   optional `known-good-iwp-set.schema.json`.
2. What this task protects is the **shape of the F019 row the T36 gate
   reads**. The gate's contract is: a record's `start_state.sha256`
   must match an F019 table row's sha256 for the named set+variant.
   A row whose hash is wrong, whose variant is wrong, or whose set id
   is wrong, lets the gate bypass the original. A row whose install
   path is `<owner>` or `<date>` rather than the real path is a real
   defect (the task's hazards list).
3. Behaviour the task forbids: the task explicitly refuses a
   `formats/known-good-iwp-set.schema.json` if the implementer would
   have added one (the `formats/` directory is strictly vendored
   upstream bytes, pinned via `archaeology.json`). If a schema file
   appears in the PR, that is blocking.
4. Project-specific: a test that passes with the row removed (rule 9:
   "a test proves behaviour only if it fails when the behaviour is
   removed"); a status written into a document (none expected here,
   but check the F019 changes); a constant with no evidence (the
   row's sha256 must be the F019-pinned
   `c4d7a248…594e`, not a re-derivation).

Not blocking: wording, style, defects in code the PR did not change.
File those as follow-ups. The empty commit on the tip is a CI-forcing
artefact — not blocking, but worth a follow-up so the main session
removes it after merge.

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at
the first blocking finding: finish reading the whole diff and the task
file, check every Done-when line and every item under "Blocking means",
and report all blocking findings together.

- Before you write the verdict, make one last pass over the full diff
  for anything you have not yet rated, and say "Final pass done" as
  the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you
  held back because an earlier one was already blocking is a review
  defect: if two problems share a cause, list both and say so.
- Do not rely on a later round. The author fixes everything you list,
  and the next review checks those fixes and new code only, not
  anything you saw but did not report.
- If you ran out of time or context before covering the whole diff,
  say which files or sections you did not cover. Do not approve in
  that case.

## What to look at

- `findings/F019-pro-setup-rules.md` — the new section. Verify the
  row's sha256 against three sources (F019 itself, `spec/setup.md`'s
  in-line hash, the bytecode-pinned reading).
- `experiments/E017-pro-setup-reading/` — the contract test. Run it
  both before and after flipping the row's hash; verify the test
  catches the flip (rule 9 mutation).
- `spec/setup.md` — the cross-reference update. Verify the in-line
  hash is unchanged and the table is referenced correctly.
- `runs/E018/E018-r0001.json` and `evidence/E018/E018-r0001.manifest.json`
  — the E018 path fixes. Verify the records validate against
  `tests/test_runs.py` and the manifest's `asset` field matches the
  literal file name (`IP1 025.mp4` with a space, not `IP1_025.mp4`
  with an underscore).
- `docs/tasks/T35.md` and `docs/tasks/T36.md` — verify the gate's
  contract (T36) is consistent with what the table (T35) provides. If
  T36 expects a field the table does not have, that is a coordination
  defect; the T35 PR is the place to flag it (T36 is not yet
  implemented).
- The empty commit `783eb12` — confirm it is content-free (no
  changes, just a marker). It is a follow-up, not blocking.

## Output

Post the verdict as one PR comment, in the format
`tools/harness/post-review.mjs` writes: a one-line header
("T35 review (Luna)"), then the body, then "Final pass done" as the
last line before the verdict, then `APPROVE` or `REQUEST CHANGES` (per
the review-brief blocking-means rule, a single blocking finding means
rework — never approve). The harness reads the verdict from the
comment.

## Effort and chain

- Effort: `high` (Luna's default).
- Chain: harness.json's `reviewer.chain` (Luna first, then
  `claudeFallback`). If Luna approves, the PR is dispatchable. If
  Luna requests changes, the author (the main session, on a rework
  branch) fixes and re-requests review.
- Family check: GLM (Z.AI) implemented, OpenAI (Luna) reviews.
  Different families. No family conflict.

## The PR you are reviewing

- `findings/F019-pro-setup-rules.md` — modified (the F019 row + a
  Reproduction line linking to the contract test).
- `experiments/E017-pro-setup-reading/` — new (the contract test
  suite, plus a `scripts-read.json` or equivalent shape).
- `spec/setup.md` — modified (one-line cross-reference update).
- `runs/E018/E018-r0001.json`, `runs/E018/E018-r0002.json`,
  `runs/E018/CORRECTIONS.md` — renamed from `runs/E018/combat/` to
  the test_runs-invariant paths.
- `evidence/E018/E018-r0001.manifest.json`,
  `evidence/E018/E018-r0002.manifest.json` — renamed similarly, plus
  the IP1 025.mp4 asset field fix.
- `docs/tasks/T35.md` and `docs/tasks/T36.md` — not modified by T35
  (they are the inputs; verify the gate's expected shape against the
  table the PR provides).

Final pass done.
