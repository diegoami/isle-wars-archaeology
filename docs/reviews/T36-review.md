T36 review (Sol)

Review PR #111: https://github.com/diegoami/isle-wars-archaeology/pull/111
Branch: task/T36-check-no-originals-wine-gate
Head: cb34a06115f94d4a662815bf5cc70a5c081cb65a
Base: main
Issue: #108

## Task context

The rule 18 carve-out (CLAUDE.md 9cbf505, owner 2026-10-08) permits a
model agent to run the original Pro binary under Wine on the user's
machine, but the carve-out is only operational when
`tools/check_no_originals.py` enforces constraint F. T35 produced the
F019 hash table the gate reads. T36 is the gate itself.

This is a **hard** task (rule 6): a guard whose failure would let an
original or a copy through. The reviewer is **GPT-6.1 Sol on the
direct OpenAI route, effort `low`** (sparingly, per the owner note;
"medium only when the task file says why" — this gate does not need
medium; the contract is narrow). The implementer is DeepSeek V4.1
Flash on Go (different family from Sol, the rule-6 family check
holds).

The full task file is at `docs/tasks/T36.md` in the branch.

## What the PR does

- Adds `check_wine_gate(record, f019_table)` to
  `tools/check_no_originals.py`: refuses a record whose
  `runtime.platform` starts with `wine-on-user-machine` and whose
  `start_state.sha256` is not in the F019 table, OR whose set+variant
  does not match a table row.
- Refuses an all-zero `start_state.sha256` (the placeholder T28 used
  for "no save file" — the owner-plays path stays on its own
  carve-out, not on this gate).
- Passes a record whose `runtime.platform` is not
  `wine-on-user-machine` regardless of `start_state.sha256` (the
  existing checks do the rest).
- Mutation tests in `tools/tests/test_check_no_originals.py` cover
  the cases the brief's Done-when listed: removing the F019-row
  match, flipping the platform prefix case-sensitivity, flipping the
  F019 table to empty, the set+variant mismatch case, the all-zero
  placeholder case.
- The case-sensitivity contract is **case-sensitive `startswith`**
  (Sol's review may want to confirm this is the intended contract —
  it is what the brief said; cross-check with constraint C of the
  carve-out).

## Blocking means

Any one is enough; a blocking finding means rework, never approve.

1. A Done-when line fails, or cannot be run as written. The Done-when
   list is in `docs/tasks/T36.md` under "Done when": six numbered
   items covering the gate's behaviour, the F019-row match, the
   set+variant mismatch, the all-zero placeholder, the case-sensitivity
   contract, the platform-prefix matching, and CI being green.
2. What this task protects is the **rule 18 carve-out's guard**. The
   carve-out permits a model agent to run the original Pro binary
   under Wine on the user's machine. If the gate fails to refuse a
   `wine-on-user-machine` record whose `start_state.sha256` is not in
   the F019 table, a model could claim a `wine-on-user-machine` run,
   CI would accept it on the platform name alone, and the original
   binary would be in the run record's working memory without the
   carve-out's table-of-known-goods check. **A bypass you proved is
   blocking, even when it looks like an edge case.** The mutation
   tests are the proof: if removing a test does not make the test
   suite fail, that test is not proving behaviour, and the gate is
   not proving its contract.
3. Behaviour the task forbids: a check that does more than its
   contract (e.g. behaviour checks, sandbox probes, watcher-presence
   checks). The gate's only job is the F019 hash match. Anything
   beyond that is out of scope and T37's job.
4. Project-specific: a constant with no evidence (the F019 row's
   hash must trace to the F019 finding's pinning); a test that
   passes with the gate's logic deleted (rule 9); a status written
   into a document.

Not blocking: wording, style, defects in code the PR did not change.
File those as follow-ups.

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at
the first blocking finding: finish reading the whole diff and the
task file, check every Done-when line and every item under "Blocking
means", and report all blocking findings together.

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

- `tools/check_no_originals.py` — the new `check_wine_gate` function.
  Read the F019-row matching logic, the set+variant comparison, the
  all-zero placeholder check, the case-sensitivity on
  `wine-on-user-machine`. Verify the refusal messages name the row
  it expected and the row it got.
- `tools/tests/test_check_no_originals.py` — the mutation tests.
  **Run the tests, then run the tests with each mutation applied**
  (hash flip, table empty, set+variant mismatch, all-zero
  placeholder, case-sensitivity flip). Verify the test suite catches
  every mutation (rule 9).
- `findings/F019-pro-setup-rules.md` — the "Known-good binary hashes"
  table T35 produced. Verify the gate reads from the right path
  (`experiments/E017-pro-setup-reading/check_known_good_hashes.py` or
  the F019 file itself, whatever the implementer chose) and that
  the row's hash matches the F019 pinning.
- `formats/run-1.schema.json` — the `runtime.platform`,
  `start_state.sha256`, `artifact.set`, `artifact.variant` fields
  the gate reads.
- `docs/tasks/T36.md` and `docs/tasks/T35.md` — verify the gate's
  contract is consistent with what T35's table provides. If the gate
  expects a field the table does not have, that is a coordination
  defect; the T36 PR is the place to flag it.

## Effort and chain

- Effort: `low` (Sol sparingly per the owner note; "medium only when
  the task file says why" — this gate does not need medium; the
  contract is narrow).
- Chain: with `--hard --sol`, the harness's chain becomes
  `[reviewer.sol, ...reviewer.hard]` = `[gpt-6.1-sol, zai-glm-5.3,
  ali-glm, ali-qwen-max, deepseek-pro, luna]`. Sol first; if Sol
  fails, the chain falls through to the next model. The review's
  header names each model that failed before the verdict.
- Family check: DeepSeek (Go) implemented, OpenAI (Sol) reviews.
  Different families. No family conflict.

## Output

Post the verdict as one PR comment, in the format
`tools/harness/post-review.mjs` writes: a one-line header
("T36 review (Sol)"), then the body, then "Final pass done" as the
last line before the verdict, then `APPROVE` or `REQUEST CHANGES` (per
the review-brief blocking-means rule, a single blocking finding means
rework — never approve). The harness reads the verdict from the
comment.

Final pass done.
