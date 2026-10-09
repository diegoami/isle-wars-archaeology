T42 verification review (Luna)
You review PR #132 at 267345edc196e0ee0fd86e980476ec0dafe65734. You did not write it. The data-only follow-up to T42 (PR #129) follows: it exports the 4th sitting and runs T40's reader, to answer T42's "is 2.3 fps enough?" question. No task file: the verification was the next-step T42 named ("the main session runs the next sitting after the merge, then T40's reader reports whether single exchanges separate", `docs/tasks/T42.md` Scope §"Out of scope"). The PR body names the four files added and the table that compares sitting 3 to the 4th.
0. Prove the tree: HEAD is 267345e, branch `task/T42-fps4-verification`, the diff against origin/main is the PR's; findings name its files.
1. Re-run every gate the PR body claims yourself, and account for each. The PR's evidence is no proof.
2. The PR's data must be valid: the record against `formats/run-1.schema.json`; the manifest's `files[]` set equal to the record's `outputs[]`; the per-frame readings in `experiments/E020-wine-first-run/measurements/frame-readings-20261008T230637Z.jsonl` in the same order as the sitting's `frames-index.jsonl`; the summary consistent with the per-frame readings.
3. Constraint F holds: `runs/E020/cmb-accumulation/E020-r0007.json` carries `start_state.sha256` = c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e, which must match the F019 known-good row for `set = iwp-2.0-996e86c5, variant = unregistered`.
4. Intervention level is I1 (T40 round-1 R4), declared in the record, with a test that pins it.
5. `python3 -m unittest discover -s tests` passes; `python3 tools/check_no_originals.py` exits 0; `python3 tools/check_links.py` exits 0.
6. The numbers behind the table: 1265 frames / 11 computer windows / 20 `net` observations; many-changes 90 → 1, counter-rise 6 → 1, one-change 79 → 142, no-change 230 → 454 vs sitting 3.
7. The PR's `check_counts.py` exit-1 is a pre-existing T40 R2 artefact, not a regression from this PR: confirm by running the same on `origin/main` and seeing the same FAIL lines (`0 exchanges, short of 100`).
8. `outcomes.json` declares all 7 claims `unestablished`; the PR does not change that. The 20 nets in r0007 add to the descriptive notes; they do not promote any claim.

Prove each finding (run it, or delete the behaviour and name the test that fails) or label it unverified. Your final message is the review: the header; the verdict (approve | approve after named fixes | rework | user decision); per gate line `DW<k>: ran <command> → <result>` or `DW<k>: not run — <reason>`; the findings R1..Rn (file:line, blocking or not); the verdict again last. Never post it: the script posts it and applies the label.

```text
## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A gate line above fails, or cannot be run as written.
2. What this task protects can be got past: the data must be raw, immutable and citable (rule 20); the sitting's start_state.sha256 must match F019 (constraint F); the intervention level must reflect what the sitting did (I0/I1/I2 from `vocabulary/interventions.md`). A bypass you proved is blocking, even when it looks like an edge case. Never "follow-up hardening" or "outside the threat model" unless the task says so; if it does, quote the line. (L47)
3. Behaviour the task forbids, or behaviour nobody asked for, inside a file the task requires. (L44)
4. <project-specific items: a constant with no evidence, a test that passes with the behaviour deleted, a status written into a document; a record whose observations do not match its sitting's readings.jsonl; a frame whose sha256 in the index does not match the file on disk>
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get past what the task protects; otherwise it is a follow-up. (L53)

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the whole diff and the PR body, check every gate line and every item under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the full diff for anything you have not yet rated, and say "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review checks those fixes and new code only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not approve in that case.
```

## What the PR adds

- `runs/E020/cmb-accumulation/E020-r0007.json` — the 4th-sitting record (driver `1ce83d5`, batch 1, 11 turns / 1 game, recovered from KeyboardInterrupt, `start_state.sha256` = c4d7a248...).
- `evidence/E020/E020-r0007.manifest.json` — the export manifest.
- `experiments/E020-wine-first-run/measurements/frame-readings-20261008T230637Z.jsonl` — 1265 per-frame readings (sha256, name, step, game, computer_turn flag, seat in turn, per-country army / owner / cyan tag, unread reasons).
- `experiments/E020-wine-first-run/measurements/readings-summary-20261008T230637Z.json` — the small summary.

## What the PR does not change

- `runtime/iwp/driver/*`, `experiments/E020-wine-first-run/{reader,launcher,e020_export,e020_sitting}.py`: untouched. The PR uses T40/T42-reviewed code paths only.
- `experiments/E020-wine-first-run/outcomes.json`: untouched. All 7 claims stay `unestablished`.
- `tools/check_counts.py`: untouched. The T40 R2 rename (`event:seq` → `net:seq`) and the floor-of-100 arithmetic are unchanged; the same FAIL lines print on `origin/main` and on this PR.
