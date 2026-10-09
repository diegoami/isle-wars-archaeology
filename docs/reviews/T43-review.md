T43 review (Luna)

Review PR #137: https://github.com/diegoami/isle-wars-archaeology/pull/137
Branch: task/T43-de5a82a2-row
Head: 759a111df426d842eaca6c0eaf654705bf556e42
Base: main
Issue: #125

## Task context

This is the F019 known-good-hashes table's row for the successor Pro set
`iwp-2.0-de5a82a2` (T41, #123; from F003: a credited loss writes
`xtras/Islepro.skr`, and the install becomes the successor set). The
table T36's gate reads must cover every set+variant the carve-out allows
to land; until this row lands, the gate refuses every wine-on-user-machine
record that names the successor set (T39's Q-UI-04/11/21, where
`may_write_saved_files: True`).

The task is **easy** (rule 6): a row addition to a markdown finding,
with a contract test that pins the row's shape. No new mechanism, no new
file, no run. There is no `docs/tasks/T43.md` — the work was a direct
main-session fix in place of a delegated implementer (the issue's
narrative and scope are in the issue body and below).

## What the PR does

- Adds a row for `iwp-2.0-de5a82a2` to F019's "Known-good binary hashes"
  table (`findings/F019-pro-setup-rules.md`): same `Islepro.exe` sha256
  `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`
  (the binary does not change between the shipped set and its successor),
  `unregistered` variant, install path same as the existing row,
  signed-on `2026-10-09`.
- Updates the prose around the table: "the table holds exactly one row"
  is replaced with "the table holds the Pro set+variant the carve-out
  covers; today that is two rows"; the "three independent records, one
  value" line is broadened to cover the registry lookup for every set
  the table names; the contract-test description is generalised to
  "every row's contract is pinned".
- Extends the row-contract test (`experiments/E017-pro-setup-reading/
  check_known_good_hashes.py`):
  - `KNOWN_SETS` lists both (set, variant, signed_on) tuples; the
    "the row" tests now iterate over them with `subTest`, named for
    the set.
  - `registry_hash()` looks up the binary hash in any of the table's
    sets (the binary is the same, so one lookup suffices).
  - `wine_record()` defaults to the first known set so single-row
    callers (the gate's mutation tests in `tools/tests/`) keep working
    unchanged.
  - `test_every_row_hash_is_the_static_reading_pin` was `any(...)` →
    now `all(...)` (rule 17: every row's hash traces to the pin).
- The 17 T36 gate mutation tests (`tools/tests/test_check_no_originals.py`)
  continue to pass unmodified: the gate iterates over the table rows;
  adding a row does not break the existing tests.

## Done-when lines (the issue's narrative)

1. F019 has a row for `iwp-2.0-de5a82a2` whose `Islepro.exe` sha256
   matches `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`,
   whose install path and signed-on date are filled in (not placeholders).
2. The contract test fails on a record whose `start_state.sha256` does
   not match either row, and passes on a record whose hash matches.
3. `python3 tools/check_no_originals.py`,
   `python3 tools/check_links.py`, and
   `python3 tools/check_pro_question_map.py` exit 0 on the changed
   files. (Pre-existing project-wide failures are out of scope; the PR
   body lists any pre-existing failure the gate reports with its
   source.)
4. CI is green.
5. An approving cross-family review is posted (this review).

## Blocking means

Any one is enough; a blocking finding means rework, never approve.

1. A Done-when line above fails, or cannot be run as written.
2. What this task protects is the **shape of the F019 row the T36 gate
   reads**. The gate's contract: a record's `start_state.sha256` must
   match an F019 row's sha256 for the named set+variant. A row whose
   hash is wrong, whose variant is wrong, or whose set id is wrong,
   lets the gate bypass the original. A row whose install path or
   signed-on date is a placeholder (`<date>`, `<placeholder>`, etc.)
   rather than the real value is a real defect (the task's hazards
   list, and the contract test's `PLACEHOLDER_TOKENS`).
3. Behaviour the task forbids, or behaviour nobody asked for, inside a
   file the task requires (rule 9): the F019 row addition must not
   touch the in-line sha256 in the Artifact line (the static reading's
   citation stays); the contract test must not introduce a soft-pass
   that lets a removed row through (rule 9: a test proves behaviour
   only if it fails when the behaviour is removed); no `formats/` file
   may be added (formats are vendored upstream bytes, pinned via
   `archaeology.json`).
4. Project-specific items: a constant with no evidence (the row's
   sha256 must be the F019-pinned hash, not a re-derivation); a status
   written into a document (no status labels added by this PR); a test
   that passes with a row removed.

Not blocking: wording and prose style in the F019 finding; the renaming
of the test methods from "the row" to "every row" / "every known set"
(a naming change, not a contract change); the addition of `subTest`
block-IDs (they appear in failure messages only); defects in code the
PR did not change.

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at
the first blocking finding: finish reading the whole diff and the
referenced files, check every Done-when line and every item under
"Blocking means", and report all blocking findings together.

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
  say which files or sections you did not cover. Do not approve in that
  case.

## What to look at

- `findings/F019-pro-setup-rules.md` — the new row. Verify the row's
  sha256 matches three sources (F019's own Artifact line,
  `artifacts/known.json`'s `iwp-2.0-de5a82a2` `Islepro.exe`, and the
  registry's `iwp-2.0-996e86c5` `Islepro.exe` — both have the same
  binary, both `7150739` bytes). Verify the install path matches the
  existing row's wording, the signed-on date parses as an ISO date, and
  the prose around the table still says the same things the table's
  presence requires (no "exactly one row" wording left).
- `experiments/E017-pro-setup-reading/check_known_good_hashes.py` —
  the extended test. Run it both before and after flipping one row's
  hash; verify it catches the flip (rule 9 mutation). Verify a removed
  row fails `test_every_known_set_has_a_row_with_every_column`. Verify
  the gate-accept tests still cover the existing set AND the new set
  (a regression where the new set is accepted without the test would
  be a bypass).
- `tools/tests/test_check_no_originals.py` — the 17 gate mutation
  tests still pass unchanged. Run them; they are the load-bearing
  piece of the rule 18 carve-out.
- `tools/check_no_originals.py` — confirm the gate's table-reader
  picks up both rows (it iterates over the table; no change is needed
  there, but a sanity check is cheap).

## Output

Post the verdict as one PR comment, in the format
`tools/harness/post-review.mjs` writes: a one-line header
("T43 review (Luna)"), then the body, then "Final pass done" as the
last line before the verdict, then `APPROVE` or `REQUEST CHANGES`
(per the review-brief blocking-means rule, a single blocking finding
means rework — never approve). The harness reads the verdict from the
comment. Each Done-when line: "DW<k>: ran <command> → <result>" or
"DW<k>: not run — <reason>".

## Effort and chain

- Effort: `high` (Luna's default).
- Chain: harness.json's `reviewer.chain` (Luna). If Luna approves, the
  PR is dispatchable. If Luna requests changes, the author (the main
  session, on a rework branch) fixes and re-requests review.
- Family check: MiniMax-M3 implemented, OpenAI (Luna) reviews.
  Different families. No family conflict. The harness excludes
  MiniMax-M3 via `--exclude mm-m3` (or `--exclude minimax`, whichever
  maps the chain's family) — confirm `--exclude` is set in the
  invocation, per rule 6.

## The PR you are reviewing

- `findings/F019-pro-setup-rules.md` — modified (one new row, prose
  updated around the table).
- `experiments/E017-pro-setup-reading/check_known_good_hashes.py` —
  modified (the row-contract test now walks both sets via `KNOWN_SETS`
  and per-set `subTest`s).
- No new files; no test discovery changes; no `formats/`, `tools/`,
  `tests/` or `spec/` touched.

Final pass done.