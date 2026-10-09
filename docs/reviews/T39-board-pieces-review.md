T39 board-pieces review (Sonnet, claude fallback for Luna: Luna implemented this round, so the reviewer comes from another family)
You review PR #139 at efc571ec83840663333cd6cc6427d8e785ad3d03 (branch task/T39-board-pieces, issue #117). You did not write it. The task file follows.
0. Prove the tree: HEAD is efc571ec83840663333cd6cc6427d8e785ad3d03 and the diff against origin/main is the PR's; findings name its files.
1. Re-run every Done-when line yourself for the six board-pieces questions (Q-UI-01, Q-UI-02, Q-UI-03, Q-UI-05, Q-UI-20, Q-PLY-04), and account for each (L32). The PR's evidence is no proof. DW1 is the main session's: check that the PR comment's record paths and sha256s match the files on the branch (sha256sum), and that each screenshot hash F020 cites is in that record's outputs[]. DW3: `python3 experiments/E019-pro-ui/check_ui_catalogue.py --batch board-pieces`, plus one mutation: drop one board-pieces Observation status or cited hash from F020 in your worktree and show the check fails, then restore. DW4: run the grep on the PR's diff (`git diff origin/main...HEAD -- findings experiments/E019-pro-ui runs/E019 evidence/E019 | grep -n -i -E '^\+.*(/home/|/mnt/|\.local/share)'`); note that two F019 lines on main already match the whole-tree grep and are not this PR's. DW5: check_no_originals, check_links, `python3 -m unittest discover -s tests`, and CI (`gh pr checks 139`).
2. [evidence-driven] Every number in F020's new entries (counts, pixels, seconds, rects, territory numbers) traces to a record field on the branch; the screenshot readings (layout, cyan digits on territories 2/3/30 and 9/18/46, the greyscale reading) are the main session's reading of PNGs that stay on the user's machine, and F020 must say they are readings: check the wording says so, and that no claim goes beyond them. You cannot see the PNGs; do not ask for them.
3. n/a (no rule code).
4. Every changed file is one the task asks for (L44). The PR changes, besides runs/ and evidence/ (the main session's data) and F020, `tests/test_e019_ui_catalogue.py`: a one-file mechanical fix declared under Scope (rule 12), because the test hard-coded Q-UI-01 as an unwalked question. Check it is mechanical, still fails when the check stops reporting unwalked questions, and is declared.
5. Sweep the diff: statuses honest for what the records hold (Q-UI-03/Q-UI-20 measured no text height: narrowed; Q-UI-02 saw no flash: narrowed); no original text in run records' observations (rule 18 D; F020 is the per-claim finding and may name screen labels); no status snapshot written into a document (rule 3).

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: an F020 Observation line that claims more than its cited record (or the main session's stated screenshot reading) supports, cites a record or hash that is not on the branch, or a path / original file / decompiled Lingo entering the repository (rule 18). A bypass you proved is blocking, even when it looks like an edge case.
3. Behaviour the task forbids, or behaviour nobody asked for, inside a file the task requires. (L44)
4. A number in F020 with no record field behind it; a test that passes with the behaviour deleted; a status written into a document.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the task protects; otherwise it is a follow-up. (L53)
## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking
finding: finish reading the whole diff and the task file, check every Done-when line and
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

Prove each finding (run it, or delete the behaviour and name the test that fails) or label it
unverified. Your final message is the review: the header; the verdict (approve | approve after
named fixes | rework | user decision); per Done-when line `DW<k>: ran <command> → <result>` or
`DW<k>: not run — <reason>`; the findings R1..Rn (file:line, blocking or not); the verdict again
last. Never post it: the main session posts it.

Out of your depth: stop and hand back, with an ESCALATE block, when any of these happens:
two hypotheses for the same question have failed; you would rely on bytes, code or behaviour
you cannot explain; you are about to write a claim you cannot back with evidence; or you have
made three attempts at one step without progress. Push your branch first. The ESCALATE block
gives what you tried, the evidence so far, and the exact question you could not answer. Never
guess a format or a cause.

# The task file
# T39 E019-pro-ui [C3] walks: the records and the full UI catalogue (F020)

- **Kind**: research (a screen-walk under the rule 18 carve-out, taking the F020 catalogue from
  proposed to V2)
- **Issue**: #117 · **Branch**: `task/T39-e019-walks` (one commit per walk, in the order
  T24 fixes) · **Merge after**: T24 (merged)
- **Implementer**: opencode `luna` (GPT-5.6 Luna, easy reviewer as implementer, effort
  `high`), after the quota check (rule 6 / L50). The implementer takes the records the main
  session posts, fills the per-question `## Observation` line in `findings/F020-pro-ui-observations.md`,
  updates the by-screen `## Observations` table, runs `check_ui_catalogue.py`, and pushes the
  per-walk commit. **The walks themselves are the main session's, not the implementer's** (L26,
  T24's hazard "The C3 lines are not the implementer's": the install is on the user's machine,
  and OpenCode cannot reach it). The reviewer follows.
  - **Reviewer**: opencode `luna` (another family, effort `high`). The reviewer re-runs
    `check_ui_catalogue.py` from the PR's commit and the catalogue's per-row `## Observation`
    line, and traces the cited screenshots to the record's `outputs[]` by hash. Cross-family
    rule satisfied; the same model as the implementer is allowed here because Luna is the
    easy reviewer and the data is small, low-risk observations.
- **Easy** (rule 6): research, not a guard. A wrong observation is a finding, not a bypass of
  a protected rule (rule 18 source-statement rule, rule 19 Pro-only scope, rule 20
  measurement-immutability). The volume is 23 walks but each walk's data is small.
- **Why**: T24 (PR #72) merged as the recorder, the walk table, `check_ui_catalogue.py` and
  F020's structure, with every per-question `## Observation` line still `pending the [C3] walk`
  (T24 Done-when 1, "no observation is stated as made"). F020 stays tier V0 until the walks'
  records are turned into observations. T39 runs those walks under the carve-out (the install is
  on the user's machine, the model cannot reach it) and turns the records into the catalogue
  T24's structure was waiting for.
- **Evidence**:
  - **T24 task file** (`docs/tasks/T24.md`): the recorder spec, the per-screen batches, the
    Done-when 4 grep (`git grep -n -i -E '/home/|/mnt/|\.local/share' -- findings
    experiments/E019-pro-ui runs/E019 evidence/E019`), the hazard that "The C3 lines are not
    the implementer's".
  - **F020** (`findings/F020-pro-ui-observations.md`): the structure, the by-screen
    `## Observations` table, the per-question section order, the 23 questions of
    `questions/pro-static.md` (22 `Q-UI-*` + `Q-PLY-04`).
  - **E019** (`experiments/E019-pro-ui/`): `walks.py` (the per-question walk table and
    `BATCHES`), `run_walk.py` (one record per question or per batch), `records.py`, `pixels.py`,
    `check_ui_catalogue.py` (the per-question coverage, the count targets, the field set).
  - **T13 / F006**: the driver API; **F002 / F003**: the cycle and the screens; **F019 Q-SET-02**:
    the registration gate; **E004**: the E004 record format T24 inherits.
  - **E019-bundles** is the per-walk evidence bundle path (set in env, like `E020-bundles` for
    the cmb-accumulation sittings). Constraint A keeps it machine-local.
- **Owns**: `findings/F020-pro-ui-observations.md` (the per-question `## Observation` lines
  become `observed` / `narrowed` / `static-only` / `unestablished` as the records come in; the
  by-screen table is filled), `runs/E019/<batch>/E019-r<NNNN>.json` (one per walk), the
  matching `evidence/E019/<batch>/E019-r<NNNN>.manifest.json`. T39 does **not** own
  `experiments/E019-pro-ui/*` (T24 owns the recorder and the check), and does **not** own
  `spec/` (the catalogue is descriptive, no rule claim).
- **Scope** (per T24's per-screen batches, one commit per walk, in the order T24 fixes):
  1. **`title-options`** (Q-UI-04, Q-UI-10, Q-UI-19, Q-UI-22): 4 walks, the menu paths and the
     three title-screen walkthroughs; the size of the first batch is the menu paths' width, not
     arbitrary.
  2. **`board-pieces`** (Q-UI-01, Q-UI-02, Q-UI-03, Q-UI-05, Q-UI-20, Q-PLY-04): 6 walks, the
     board at the one player count the build allows and the colour / text fields.
  3. **`play`** (Q-UI-08, Q-UI-12, Q-UI-13, Q-UI-15, Q-UI-16): 5 walks, one full turn's panels
     and the computer's busy-wait timings.
  4. **`events-end`** (Q-UI-06, Q-UI-07, Q-UI-11, Q-UI-14, Q-UI-21): 5 walks, the event
     flashes, the centre moves, the end screens and the two `none found` rows.
  5. **`inputs-sounds`** (Q-UI-09, Q-UI-17, Q-UI-18): 3 walks, illegal-action error texts, the
     sound switch, the hit areas.
  - **Per walk (each commit / each PR):** the main session runs `run_walk.py --question
    <id>` once, recovers, posts the run/1 record's path and sha256 on the PR with the
    screenshot's hash; the implementer reads the record, fills the per-question
    `## Observation` line in F020, updates the by-screen `## Observations` table for the screens
    the walk visited, runs `check_ui_catalogue.py`, and pushes the commit. (`--question` and
    `--batch` are mutually exclusive; the batch is the walk's own, looked up from
    `experiments/E019-pro-ui/walks.py`.)
  - **Tier V2 reached** when all 23 questions carry an observation; the check is the gate.
    V3 is not in scope (no native Windows run, by the owner's rule 19 carve-out).
  - **What this does not establish:** the registered build (rule 19); a `spec/` page; the score
    or cast members' decoded bytes (the catalogue describes in our own words, never quotes
    bytes); the *playback* of a position (no save in the unregistered build); the projector-
    level windowing (Q-UI-19's window and scaling settings are not in the Lingo).
  - **Out of scope:** any rule claim; rewriting the recorder; rewriting the check; a Wine /
    Xvfb / driver change; the [C3] walks themselves (the main session, not the implementer,
    L26); the model's reading of the install (a model agent does not run `run_walk.py`).
- **Done when** (per walk, so 23 Done-whens total; the per-walk one is the only one the
  review checks; the per-batch roll-up is informational):
  1. The main session ran `run_walk.py --question <id>` once, recovered, and posted the
     record's path and sha256, and every screenshot's hash, on the PR. (`--question` and
     `--batch` are mutually exclusive; the batch is the walk's own, looked up from
     `experiments/E019-pro-ui/walks.py`.) **Out of the PR's diff** sits only the data the
     recorder wrote.
  2. `findings/F020-pro-ui-observations.md` carries, for `<id>`, an `## Observation` line
     whose status is one of `observed` / `narrowed` / `static-only` / `unestablished`, cites
     the run/1 record's path and sha256, and (for `observed` / `narrowed`) names the
     screenshot's hash. The by-screen `## Observations` table is updated for the screens the
     walk visited.
  3. `python3 experiments/E019-pro-ui/check_ui_catalogue.py --batch <batch>` exits 0 on the
     PR's commit, with `<id>` mapped and the row's count target met (the target is the row's
     own when the row names one — "at least 5 events" for Q-UI-06, "at least 20 computer turns"
     for Q-UI-13, "at least 20 attacks" for Q-UI-16, "at least 5 centre moves" for Q-UI-07,
     and a count per display size for Q-UI-19 — else the walk table's). `--batch` limits the
     per-row checks to one batch's questions; the global checks (walk-table coverage, count
     targets) still span every question. A mutation that drops the observation field, the
     cited hash, or the screenshot's hash from the catalogue makes the check fail.
  4. The T24 Done-when 4 grep stays empty on the PR's diff:
     `git grep -n -i -E '/home/|/mnt/|\.local/share' -- findings experiments/E019-pro-ui runs/E019 evidence/E019`
     prints nothing. No line of decompiled Lingo; no original PNG; the OCR layer is forbidden
     (the recorder's reads are pixels-only).
  5. `python3 tools/check_no_originals.py` exits 0; `python3 tools/check_links.py` exits 0;
     CI is green.
- **Per-batch merge gate** (informational; the per-walk merge is the gate the rule 7 review
  checks): the last walk of the batch is preceded by the four prior walks' merges, the
  `## Observations` table reflects the whole batch's screens, and the `## Observation` lines
  for the five questions in the batch are all filled.
- **Hazards**:
  - **The model cannot reach the install** (L26, T24). The walks are `run_walk.py` runs the
    main session posts. The implementer's diff is the catalogue text, the record's data is the
    walk's, the implementer never reads `/mnt/c` or the prefix. Rule 18 holds: no decompiled
    Lingo, no PNG, no install path in the PR.
  - **Per-frame timings depend on speed** (Q-UI-06, Q-UI-13, Q-UI-16). The walks observe
    `speed = normal` (the unlocked default), read from the recorded options file
    (`xtras/Islepro.skr`), and the record names the speed. A future task can re-time at fast
    or slow if a question needs it.
  - **The deal is random** (F018). The board read happens after the deal; no two board reads
    show the same board; the catalogue says so.
  - **The event-frequency option** is locked in the unregistered build (F019 Q-SET-02);
    Q-UI-22 reaches the option on / off by editing the options file, not by clicking, and the
    record says so.
  - **Q-UI-14 (`none found`, no event log) and Q-UI-21 (`none found`, board look is in the
    cast).** The walk's observation is `static-only`; the absence is the result, recorded as
    the walk's `## Observation` line; the row stays `none found` in the catalogue. A
    "absence confirmed" reading is the observation, not "an absence claim is supported".
  - **The "registered" walks** (Q-UI-04, Q-UI-11, Q-UI-21): a mid-game loss credits a loss
    and writes `xtras/Islepro.skr`; the install becomes the successor set `iwp-2.0-de5a82a2`.
    F019's known-good table holds only the shipped row today; the export refuses a sitting
    that plays a game after a credited loss (T36's constraint F, #125 closed as
    `post-playable` until the row is added). Until that row is added, Q-UI-04, Q-UI-11 and
    Q-UI-21 are walked on the shipped set only.
  - **The next batch needs the prior batch merged first.** A walk that runs before its
    predecessor's commit is a reviewer defect: a row's `## Observation` line that cites a
    record that is not yet on the main branch fails the catalogue check. One walk per
    commit, the order T24 fixes.
- **Runs on**: `artifact:iwp-2.0-996e86c5` (the unregistered build; through `run_walk.py`) ·
  cloud: C3 only (the install is on the user's machine) · network: N1 for push · GitHub:
  `gh:push gh:pr`. Driver commit pinned in the record's `runtime.driver`. The record's
  `start_state.sha256` is the F019 row's; constraint F is the gate.
