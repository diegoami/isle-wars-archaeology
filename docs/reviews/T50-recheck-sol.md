T50 re-review (Sol)

You re-check PR #195 at 6777086c4b45bf4a5c9184a05cac8b445ae7ac9e. Round 1 was MiniMax-M3's review at 469d224 (approve, notes R1–R4),
posted on the PR. After it the owner decided all 11 choices (PR comment, 2026-10-12): every
recommendation except decision 1, where the owner chose a generator over one hand-made board. The
same Claude (Opus) implementer wrote them in, in fb5b849 and 6777086. Check `git diff 469d224..HEAD`
and the parts of design/core-rules.md it touches; do not re-review untouched rows. Your working
directory is the review worktree: run commands there with no `workdir` argument, and use relative paths.

0. Prove the tree: HEAD is 6777086….
1. Re-run every Done-when line of the task file below, and account for each (L32). DW4 is a reading
   line: write `DW4: ran a read of the decisions section → <result>`.
2. Each of the 11 decisions in the doc matches the owner's comment on the PR, and the rules describe
   the chosen options as settled. No `open` row remains, and none was decided silently.
3. **The generator** (new design). Check that it is buildable and sound:
   - its fixed invariants agree with the kept spec claims (C-BRD-02 to 04);
   - the generation steps can always meet the invariants, or the redraw bound (a valid board within 50
     attempts) is plausible. Argue it, or try a quick prototype in your mktemp folder;
   - a seed reproduces the board;
   - the fairness checks are well defined and not contradictory: could they reject every board?
   - bonuses of floor(size/2)+entrances, minimum 2, keep islands comparable, with no island paying more
     than its size;
   - every place that assumed a fixed board was updated.
   Name any gap a TypeScript implementer would hit.
4. R1–R3: the new combat figures are right (re-run the doc's Python); the share step handles several
   humans; the event-pause thresholds are stated for both the on and off cases.
5. check_design.py's change (it accepts the decisions heading): mutation-proven. Delete the new branch,
   run the tests, see one fail, and restore in a `finally`.
6. Rule 18: no original names in design/.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: a spec claim with no row, or with a wrong decision word,
   that check_design.py accepts; a feel-changing decision made without being listed for the owner;
   original game text in design/ (rule 18). A bypass you proved is blocking, even when it looks like
   an edge case. (L47)
3. Behaviour nobody asked for inside a file the task owns: cards, centres, hazards or the computer
   opponent designed here instead of in T51; or any edit outside Owns. (L44)
4. A test that passes with its check deleted; a wrong number that a balance argument rests on; a
   status written into a document.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the task protects; otherwise it is a follow-up. (L53)

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


The task file, in full:

# T50 malpaco's design, the core rules: what is kept from Pro, changed or new

- **Kind**: feature (design; no code in malpaco, no research run)
- **Issue**: #192 · **Branch**: `task/T50-design-core` · **Merge after**: —
- **Implementer**: the user's choice, asked before the run (CLAUDE.md rule 6), recorded here and on
  the issue.
- **Reviewer**: the user's choice at review: an external model, never the implementer's family.
- **Evidence**: the promoted spec only, at the commit the branch starts from: `spec/board.md`,
  `setup.md`, `seats.md`, `starting-state.md`, `turn-sequence.md`, `reinforcement.md`,
  `movement.md`, `combat.md`, `ownership.md`, `victory.md`, `surrender.md` (59 claims: C-BRD,
  C-SET and C-RND, C-PLY, C-STA, C-TRN, C-REI, C-MOV, C-CMB, C-OWN, C-VIC, C-SUR). Also the coverage of each
  question in play, from `runs/coverage.md`, and the direction in CLAUDE.md, "The goal is a fun game,
  not a copy" (the owner, 2026-10-11). malpaco's earlier guesses are in `questions/malpaco.md`, but
  only as history: they are not evidence.
- **Owns**: `design/README.md`, `design/core-rules.md`, `tools/check_design.py`,
  `tools/tests/test_check_design.py`, and one line in CI's check step if the check is not already
  picked up there. Not `spec/**`, `findings/**`, `runs/**` or `questions/**`.
- **Why**: the research has answered the core rules well enough for design (CLAUDE.md: a reading
  backed by the code, with its core seen in play). malpaco needs rules it can build. The owner wants
  a game that is fun, roughly balanced and varied, not a copy, so each of Pro's rules is the
  starting point for a decision, not a target.
- **Scope**:
  - **`design/core-rules.md`**: malpaco's core rules, written as rules a TypeScript implementer can
    build without reading the spec. The order is setup, seats, the board's shape, the deal, the turn,
    reinforcement, movement, combat, ownership, victory and surrender. Each rule is in our own words
    and our own names. No text, name or label of the original appears (rule 18). Constants are given
    as numbers, or as `open` with the choices.
  - **The decision table**: one row per in-scope spec claim, in the form
    `| C-<AREA>-<nn> | decision | malpaco's rule (§ link) | why |`. A decision is exactly one of
    `keep`, `change`, `replace`, `drop` or `open`:
    - `change` and `replace` say what changes, and why it makes the game more fun, balanced or
      varied;
    - `drop` says why the game is better without the rule;
    - `open` names the choice and goes into the owner's list.
    A claim whose status is not `supported` or `corroborated` (inconclusive, unknown) still gets a
    row; its decision is a design choice, and it says so.
  - **Fun and balance, argued**: for the rules that drive balance (combat odds, income, the
    attacker's minimum, the human/computer asymmetries C-CMB-01 to C-CMB-03 and C-CMB-09, game length
    and the end), a short argument with numbers. Where a number is a model and not a measurement, it
    says so: for example, capture odds by stack sizes under uniform dice, or expected income by
    territory count.
  - **The owner's choices**: a section `## Choices for the owner` that lists every `open` row and
    every `change` or `replace` that alters the feel of play. Each one has 2–3 options, a
    recommendation and its reason. The owner decides these; the implementer never does.
  - **`design/README.md`**: what `design/` is (malpaco's rules, derived from the spec, with no
    evidence), and that only behaviour and design pass to malpaco (rule 18). T51 (#193: cards, bonuses,
    centres, hazards, the computer opponent) and T52 (#194: the UI against Pro's and malpaco's recorded
    weaknesses) add their own files later.
  - **`tools/check_design.py`**: it reads the in-scope spec files' claim tables and
    `design/core-rules.md`'s decision table. It fails if any of these holds:
    - an in-scope claim has no row, or more than one;
    - a row names an id that is not in the spec;
    - a decision is not one of the five words;
    - a `change`, `replace` or `drop` row has an empty "why";
    - an `open` row is missing from `## Choices for the owner`.
    Its tests visit each failure: each one has a test that fails when the behaviour is removed
    (rule 9).
  - Out of scope: cards, island bonuses, production centres, hazards and the computer opponent (T51);
    the UI (T52); any edit in the malpaco repository (a later malpaco task ports the approved
    design); new runs or recordings.
- **Done when**:
  1. `python3 tools/check_design.py` prints `design ok: 59 claims, 59 rows` and exits 0. It exits 1
     on `main` today, because there is no design.
  2. `python3 -m unittest tools.tests.test_check_design` passes: one test per failure listed in
     Scope, each with a fixture that trips that failure alone.
  3. `grep -c '^| C-' design/core-rules.md` prints 59.
  4. `## Choices for the owner` exists, and every entry has options, a recommendation and a reason.
     The reviewer reads each one; the check confirms only that the `open` rows are there.
  5. `python3 tools/check_links.py` and `python3 tools/check_no_originals.py` pass, and the full test
     suite is green.
- **Hazards**:
  - **Copying instead of designing.** A table of `keep` with "Pro does it" as the reason fails the
    task's purpose. Keep a rule when it serves fun or balance, and say how. Change it where Pro's
    asymmetries (the human attacks at equality, the computer needs more; only the human forfeits a
    country) make the game worse for a player of malpaco.
  - **Rule 18.** The original's names, labels, screen text and title stay out, as do any quotes from
    the findings. Describe behaviour in our own words, and give island and country names of our own,
    or none.
  - **Over-reach.** Leave cards and the computer opponent to T51, even where combat touches them, and
    note the link instead.
  - **Deciding for the owner.** Every feel-changing call is listed as a choice with a
    recommendation, never made silently.
