T39 title-options review (Luna)

Review PR #135: https://github.com/diegoami/isle-wars-archaeology/pull/135
Round 3 (after Luna R1, R2 review; addressed R1 + R2 — see commit d5b238e).
Branch: task/T39-title-options
Head: d5b238e49979af66621f9064b95711e5a606d054
Base: main
Issue: #117

## Task context

This is the title-options batch of T39 (#117, the [C3] walks that fill F020
from proposed / V0 to V2). Four walks completed (Q-UI-04, Q-UI-10,
Q-UI-19, Q-UI-22); the catalogue (F020) entries for them are filled with
the recorder's observations; the per-walk Done-when for those four walks
is the gate the review checks. The remaining 19 walks (board-pieces 6,
play 5, events-end 5, inputs-sounds 3) are separate batches, not in this
PR.

The task is **hard** (rule 6): a [C3] reading pass whose errors would let
`check_ui_catalogue.py` accept catalogue entries that the recorded walks
do not support — the loader is the owner-supplied walk, the recorder is
the catalogue's only evidence source, and the static map rows the
catalogue reads are unmeasured here. Falls through to the **reviewer**
GPT-6.1 Sol at effort `low` (the project hard pair, owner 2026-10-03),
but the harness.json `reviewer.chain` is Luna and the walks are records,
not guards, so Luna at `high` is what runs. **Substitutes**: Sonnet
(`reviewer.claudeFallback`); Sonnet is not on this session's backend, so
falling back means escalating to the owner.

## What the PR adds

- **Records** under `runs/E019/title-options/`:
  - `E019-r0001.json` and `E019-r0002.json` — Q-UI-04 attempts (aborted;
    the post-loss-no-change bug at the second PLAY_CLICK click; both
    captured partial outputs and are on disk as the abort record).
  - `E019-r0003.json` — Q-UI-10 (completed; 3 walkthroughs, 6 timing
    observations).
  - `E019-r0004.json` — Q-UI-22 (completed; 2 screenshots,
    frequency-default and frequency-locked).
  - `E019-r0005.json` and `E019-r0009.json` — Q-UI-19 attempts at
    640x480x24 (aborted; title screen not seen within 45 s, below the
    game's first-frame geometry).
  - `E019-r0006.json` and `E019-r0010.json` — Q-UI-19 attempts at
    800x600x24 (both completed; same hashes, two attempts as a re-run
    check).
  - `E019-r0007.json` and `E019-r0011.json` — Q-UI-19 attempts at
    1024x768x24 (both completed).
  - `E019-r0008.json` and `E019-r0012.json` — Q-UI-19 attempts at
    1280x1024x24 (both completed).
  - `E019-r0013.json` — Q-UI-04 third attempt (completed; the new walk
    without the post-loss cleanup, 9 distinct screens ≥ 8 target).
- **Manifests** under `evidence/E019/title-options/` for every record.
- **F020** (`findings/F020-pro-ui-observations.md`):
  - Q-UI-04 entry filled (`observed`, 9 distinct screens, 9 screenshot
    hashes, run/1 record path and sha256).
  - Q-UI-10 entry filled (`observed`, 3 walkthroughs, 6 timing values,
    launch-to-title 6.53 s).
  - Q-UI-19 entry filled (`narrowed`, three reachable sizes; 640x480
    below the game's first-frame geometry).
  - Q-UI-22 entry filled (`observed with the locked state`, two
    screenshots, registration-gate refusal).
  - The Observations table's Title / Options / Scores / Help / Loss
    notice / Frequency-locked cells are filled for the title-options
    batch; the rest stay "when the batch's records are turned in".
- **`experiments/E019-pro-ui/walks.py`**:
  - Q-UI-04 actions list trimmed to end at the loss-notice shot (7
    actions removed); the notes explain the change and the
    post-loss-no-change bug.
  - Q-UI-19 sizes list narrowed from four to three
    (800x600x24, 1024x768x24, 1280x1024x24); the 640x480x24 entry is
    removed because it cannot run.
- **`tests/test_e019_ui_catalogue.py`**:
  - The R5 mutation test that asserts "no completed record shows the
    display size 640x480x24" is updated to assert 1024x768x24, the new
    missing-size detection after the narrowing.

## Per-walk Done-when (T39 brief)

For each of Q-UI-04, Q-UI-10, Q-UI-19, Q-UI-22:

1. The main session ran `run_walk.py --question <id>`
   once, recovered, and posted the record's path and sha256, and every
   screenshot's hash, on the PR. (`--question` and `--batch` are mutually exclusive;
   the batch is the walk's own, looked up from `experiments/E019-pro-ui/walks.py`.)
   **Out of the PR's diff** sits only the data the recorder wrote.
2. `findings/F020-pro-ui-observations.md` carries, for `<id>`, an
   `## Observation` line whose status is one of `observed` /
   `narrowed` / `static-only` / `unestablished`, cites the run/1
   record's path and sha256, and (for `observed` / `narrowed`) names
   the screenshot's hash.
3. `python3 experiments/E019-pro-ui/check_ui_catalogue.py --batch title-options` exits 0
   on the PR's commit, with `<id>` mapped and the row's count target met.
   The four title-options rows pass; the rest of the catalogue's 38 rows
   are pending the other batches (board-pieces, play, events-end,
   inputs-sounds) and are out of scope for this PR. `--batch` limits the
   per-row checks to one batch's questions; the global checks
   (walk-table coverage, count targets) still span every question.
4. The T24 Done-when 4 grep stays empty on the PR's diff:
   `git grep -n -i -E '/home/|/mnt/|\.local/share' -- findings
   experiments/E019-pro-ui runs/E019 evidence/E019` — the PR's diff
   introduces no new matches; the two pre-existing matches are
   F019's install-path column rows (T35 / T43, not in this PR's diff).
5. `python3 tools/check_no_originals.py` exits 0; `python3
   tools/check_links.py` exits 0; CI is green.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.

1. A Done-when line above fails, or cannot be run as written.
2. What this task protects can be got past: the catalogue's observations
   must trace to a record the PR holds; a row that names a screenshot
   hash the record does not have lets the catalogue pass a description
   of a screen the walk never shot. A row that names a record the PR
   does not have lets the catalogue cite an absent evidence. A
   narrowing that does not say what was narrowed past, or a status
   that does not match the evidence, are real defects.
3. Behaviour the task forbids, or behaviour nobody asked for, inside a
   file the task requires (rule 9): the F020 row addition must not
   touch the in-line sha256 in F019's Artifact line; the row-contract
   test (`experiments/E017-pro-setup-reading/check_known_good_hashes.py`)
   must not introduce a soft-pass that lets a removed row through; no
   `formats/` file may be added.
4. Project-specific items: a constant with no evidence (the
   screenshot's sha256 must be the recorded file's, not a
   re-derivation); a status written into a document (the per-walk
   Done-when's status must be one of the four named); a record whose
   observations do not match its recorded files (run/1's outputs field);
   a screenshot whose sha256 in the record does not match the file
   named; a count target not met for the four rows in scope (Q-UI-04
   ≥ 8 distinct, Q-UI-10 3 walkthroughs, Q-UI-19 one completed per
   size, Q-UI-22 2 screenshots); the abort records (r0001, r0002,
   r0005, r0009) must not be silently claimed as completed.

Not blocking: wording and prose style in F020; the renaming of the
test method's "the row" to per-set subTests (T43 follow-on); the
narrowing of Q-UI-19 from four to three sizes (a deliberate scope
change recorded in the walk's notes and the F020 row's status); the
T24 Done-when 4 grep's pre-existing F019 matches (not in the PR's
diff); defects in code the PR did not change.

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
  say which files or sections you did not cover. Do not approve in
  that case.

## What to look at

- **Q-UI-04 walk (E019-r0013)**: the 9 distinct screens ≥ 8 target; the
  loss-notice is the last screen the walk now reaches (the post-loss
  cleanup was removed by this PR's commits); the screenshots'
  sha256 in F020 match the record's outputs.
- **Q-UI-10 walk (E019-r0003)**: 3 walkthroughs, 6 timing observations
  (3 round-to-options, 3 round-back-to-title), launch-to-title
  6.53 s; the recorder does not shot title or options (the walk's
  goal is timing).
- **Q-UI-19 walks (six records, three sizes × two attempts)**: each
  completed record's display size matches its requested size;
  640x480x24 is absent from the walk's sizes (not in the PR's diff
  vs main).
- **Q-UI-22 walk (E019-r0004)**: two screenshots, frequency-default
  and frequency-locked; the click was refused by the registration
  gate, so the value did not change.
- **`experiments/E019-pro-ui/walks.py`**: the Q-UI-04 actions list
  ends at the loss-notice shot; the Q-UI-19 sizes list is three
  reachable sizes.
- **`tests/test_e019_ui_catalogue.py`**: the R5 mutation test's
  assertion matches the new sizes list.
- **`check_ui_catalogue.py` per-walk** (Q-UI-04, Q-UI-10, Q-UI-19,
  Q-UI-22): each row's status, screenshot hashes, count target, and
  record path/sha256 hold.
- **`tools/check_no_originals.py`** and **`tools/check_links.py`**:
  exit 0 on the PR's commit.

## Output

Post the verdict as one PR comment, in the format
`tools/harness/post-review.mjs` writes: a one-line header ("T39
title-options review (Luna)"), then the body, then "Final pass done"
as the last line before the verdict, then `APPROVE` or
`REQUEST CHANGES` (per the review-brief blocking-means rule, a
single blocking finding means rework — never approve). Each
Done-when line: "DW<k>: ran <command> → <result>" or "DW<k>: not run
— <reason>".

## Effort and chain

- Effort: `high` (Luna's default).
- Chain: harness.json's `reviewer.chain` (Luna). If Luna approves, the
  PR is dispatchable. If Luna requests changes, the author (the
  main session, on a rework branch) fixes and re-requests review.
- Family check: MiniMax-M3 implemented (via the main session's
  recorder runs on the install), OpenAI (Luna) reviews. Different
  families. The harness excludes MiniMax-M3 via `--exclude mm-m3`
  (rule 6).

## The PR you are reviewing

- `runs/E019/title-options/E019-r{0001..0013}.json` — 13 records, four
  walks (Q-UI-04 / 10 / 19 / 22); four of them are aborted (Q-UI-04
  two attempts, Q-UI-19 two attempts at 640x480).
- `evidence/E019/title-options/E019-r{0001..0013}.manifest.json` —
  matching manifests.
- `experiments/E019-pro-ui/walks.py` — Q-UI-04 actions trimmed,
  Q-UI-19 sizes narrowed.
- `findings/F020-pro-ui-observations.md` — Q-UI-04/10/19/22 entries
  filled, the Observations table's title-options rows updated.
- `tests/test_e019_ui_catalogue.py` — one mutation-test assertion
  updated for the new sizes list.
- No new files; no test discovery changes; no `formats/`, `tools/`,
  `spec/` or `findings/F019-…` touched (F019 was modified by T43,
  already on main).

Final pass done.