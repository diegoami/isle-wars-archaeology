T37 rework (GLM-5.3 Flash on Z.AI)

Re-dispatch after Luna's six blocking findings on the T38 task file.
PR: https://github.com/diegoami/isle-wars-archaeology/pull/112
Branch: task/T37-wine-driver-task-file
Head: 86eacedb3d3794c1e024d3d95963331bb8a32bce
Base: main
Issue: #109

## What Luna found

Luna ran every Done-when line in `docs/tasks/T38.md` and reported six
blocking findings. The pattern is the same across most of them: the
T38 task file describes what each check is *for* with the right
language (the constraints A–G of the rule 18 carve-out, the T36 gate
contract, the F019 row), but the literal commands are not runnable
as written.

- **R1 — DW1: locality check is incomplete.** `git status --porcelain`
  only reports worktree paths. A JSON sitting artefact under
  `/mnt/c/Temp/iwp-shots/wine/` would pass `git status` while still
  living outside the worktree. The check has to actually touch the
  path the constraint names.
- **R2 — DW2: recording-class constraint is unenforced.** The
  validator Luna found (`validate_records.py`) does not check the
  `class` field on evidence manifest entries; an `screenshot` class
  would pass. The carve-out's constraint C says recording, not
  screenshot.
- **R3 — DW2: `--batch <name>` is not runnable.** The shell parses
  `<name>` as a redirect; the command fails before any check runs.
- **R4 — DW5: `<base>` is undefined.** `git diff --name-only <base>
  -- runs/E018 ...` fails before `git diff` runs.
- **R5 — DW7: same `<base>` failure (shared cause with R4).**
- **R6 — DW9: `check_pro_question_map.py` exits non-zero on the
  pre-existing Q-TRN/Q-VIC/Q-SUR failures on `main`, the same class
  the T35 review caught. The T38 task file does not scope the gate
  to "files this PR touches" the way the T35 amendment did.

## What to fix

Rewrite the T38 task file's **Done when** section so every numbered
line is a runnable command that exits 0 when the constraint is met
and non-zero (or a clear failure) when it is not. No literal
placeholder syntax in the commands (`<name>`, `<base>`, `<foo>`).
No references to files that don't exist yet (`launch_sitting.py`,
`check_records.py`) — those are files a *follow-up* dispatch will
write, and the T38 Done-when is the contract that follow-up
implements against, not a check on its outputs.

### The two named batches

The T38 task file's earlier sections already name the two batches
the implementer intends: `cmb-accumulation` (Q-CMB-04/05/06/07/11,
the Session B computer-vs-computer accumulation targets) and
`bomb-sampling` (C-CRD-06, the computer's bomb-target sampling).
Use these two names **literally** in the Done-when commands. No
placeholder.

### The base for `git diff`

Use `origin/main` as the literal base for `git diff --name-only`
commands. The branch's base is `main`; `origin/main` is the same
thing. No placeholder.

### The concrete commands

A workable shape for each Done-when line:

1. **(A) Locality.** `find /mnt/c/Temp/iwp-shots/wine -type f 2>/dev/null | wc -l`
   counts the sitting artefacts on the user's machine (it must be
   non-zero: a sitting happened, the artefacts are on the user's
   machine, not in the worktree). The negation
   `! find ... -name '*.json' -path 'runs/E020/*'` is **not** the
   check (worktree-side `find` cannot see `/mnt/c/...`). The check
   is the *existence* of the sitting artefacts on the user's
   machine, paired with the worktree's `git status --porcelain`
   confirming nothing is staged in the worktree.
2. **(B) Batch list.** The T38 task file's "Why a run is made"
   section names the two batches. The Done-when is "the T38 PR
   includes a `tools/wine-driver.sh` (or equivalent) that accepts
   `--batch cmb-accumulation` and `--batch bomb-sampling` and
   refuses unknown batches with exit non-zero, naming the
   unknown batch." This is a *contract on the dispatcher*, not
   a check on a running wine session. Concretely:
   `bash tools/wine-driver.sh --batch cmb-accumulation --help` exits
   0 and prints the batch's expected exchanges count; same for
   `bomb-sampling`; `bash tools/wine-driver.sh --batch unknown-x
   --help` exits non-zero and names `unknown-x`.
3. **(C) Record + manifest shape.** Use `tools/validate_records.py`
   which already exists. Concretely:
   `find runs/E020 -name '*.json' -print0 | xargs -0 python3
   tools/validate_records.py` exits 0; every record's
   `runtime.platform` starts with `wine-on-user-machine` (case-
   sensitive, per T36); every record's `start_state.sha256`
   matches the F019 row's hash; every manifest's `files[].class`
   is `recording` (the carve-out's constraint C, not `screenshot`).
   The class check is a new addition: either extend
   `validate_records.py` to validate the manifest's `class`
   field, or write a new `tools/validate_wine_manifests.py` for
   it. The brief's scope says "tools/validate_records.py" is the
   shape; the class check is the same shape, in a new tool or
   the same tool with an extension.
4. **(D) Record-content shape.** Use `validate_records.py`'s
   schema-level checks: `observations[]` items have a `field`
   and either a `value` or a `ref`; `field` is a non-empty string
   that follows the structural names the batch list defines
   (e.g. `counter:attacker` is one of the schema's allowed
   `field` values; the implementer of T38 will document the
   batch's structural names in the per-scenario brief). This is
   a *contract* check, not a content-correctness check.
5. **(E) Per-claim wording.** `git diff --name-only origin/main
   -- spec/` is empty; per-claim amendments are proposed in
   F011's and F014's per-claim sections (each naming the claim id
   and the sitting's run ids) and reach `spec/` only by the
   main session's promotion, one claim at a time. Concretely:
   `git diff --name-only origin/main -- spec/ | wc -l` is 0.
6. **(F) Gate pass.** Re-run the T36 gate against every E020
   record with a synthetic record to prove the gate accepts the
   F019 row and refuses the four mutation cases. Concretely:
   `python3 -c "from tools.check_no_originals import
   check_wine_gate, load_f019_table; ...; assert ..."` (or a
   `tools/tests/test_wine_e020_records.py` with the four
   mutations). The synthetic records are: matching record (pass);
   wrong 64-hex hash (refused); all-zero placeholder (refused);
   unrecognised suffix `wine-on-user-machine-evil` (refused);
   right hash with wrong set+variant (refused). Five cases,
   one pass + four refusals.
7. **(G) Counts.** `python3 tools/check_counts.py
   experiments/E020-wine-first-run/scenarios.txt` (or equivalent)
   prints the batch's target counts and the sitting's observed
   counts; both meet the per-batch target. The implementer of T38
   writes the count checker; the contract is that one exists and
   passes. The path is concrete (no placeholder); the
   implementation is a follow-up.
8. **(H) Project-wide gates.** `python3 tools/check_links.py`
   exits 0. `python3 tools/check_no_originals.py` exits 0.
   `python3 tools/check_pro_question_map.py` exits 0 on the
   PR's touched files (per the T35 amendment pattern: scope the
   question-map gate to "files this PR touches"; pre-existing
   project-wide failures are out of scope and are named in the
   PR description).

### Per the brief's Hazards section

- Do NOT introduce a second F019 row.
- Do NOT change the recognised-suffix list (`RECOGNISED_WINE_SUFFIXES`
  in `tools/check_no_originals.py`) — the iwp-2.0 entry is the only
  one the brief names.
- Do NOT amend `spec/` or `findings/` in bulk. The T38 PR's
  wording-amendment contract is per-claim (constraint G).
- Do NOT add files under `formats/` (vendored upstream bytes,
  pinned via `archaeology.json`); any new schema goes next to the
  F019 table or as a sibling of `tools/validate_records.py`.

## Done when (the rework's own done-when)

1. The T38 task file's Done-when section has 8 numbered items (A
   through H above), each a runnable command (no literal
   placeholder syntax).
2. Each command either uses an existing tool (`git status`,
   `find`, `git diff --name-only origin/main -- <path>`, `python3
   tools/validate_records.py`, `python3 tools/check_links.py`,
   `python3 tools/check_no_originals.py`) or names a new tool the
   T38 implementer will write (a count checker, a wine-manifest
   class checker, a wine-driver dispatcher).
3. The question-map gate is scoped to "files this PR touches,"
   with pre-existing project-wide failures named in the PR
   description.
4. `python3 tools/check_links.py` and `python3 tools/check_no_originals.py`
   both exit 0 on the PR head.
5. The T38 task file's earlier sections (Implementer, Reviewer,
   "Why a run is made", Scope, Hazards) are unchanged from the
   current PR; only the Done-when section is rewritten.
6. The T38 task file's Merge-after list still references T35 and
   T36; both are merged.
7. CI is green; the PR has Luna's re-review (the same Luna,
   effort `high`).

## Effort and chain

- Implementer: GLM-5.3 Flash on Z.AI, effort `high` (the same model
  that did the original work; the rework is a small rewrite of
  the Done-when section).
- Reviewer: Luna again, effort `high`. The chain is `[luna]`.
- Family check: Z.AI (GLM) implemented, OpenAI (Luna) reviews.
  Different families. No family conflict.

## What NOT to change

- The T37 brief (`docs/tasks/T37.md`) — the brief was correct; the
  implementer's T38 didn't follow the brief's "every numbered
  line must be runnable as written" rule. Amend T38, not T37.
- The earlier sections of T38 (Implementer, Reviewer, "Why a run
  is made", Scope, Hazards) — they read correctly; only the
  Done-when section is rewritten.
- The `RECOGNISED_WINE_SUFFIXES` constant and the T36 gate — T38
  references them; T38 does not change them.

Final pass done.
