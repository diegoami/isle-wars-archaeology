PR #191 research review (GPT-5.6 Luna)

You review PR #191 at a6fad5659312acc58782f6c58c04f08b5d4463a8. It is a records-only research PR:
two model-driven sittings of the original Pro under Wine on the owner's machine (CLAUDE.md rule 18's
carve-out), as run records E021-r0006 (sitting 8) and E021-r0007 (sitting 9), their evidence
manifests, and `experiments/E021-pro-session-a/measurements/progress-r07.json` (Session A at 30/40).
The main session ran the sittings; you did not. Read the PR body with `gh pr view 191`. The last
commits are merges of main and a regenerated `runs/coverage.md`. Your working directory is the
review worktree: run commands there with no `workdir` argument, and use relative paths. Your job is
to try to falsify it.

Check, in order:
G0 Tree and records: HEAD is a6fad56…. Run `python3 -m unittest tests.test_runs tests.test_formats`,
   `python3 tools/check_no_originals.py` (constraint F: each record's `runtime.platform` starts with
   `wine-on-user-machine` and its `start_state.sha256` matches F019's `Islepro.exe` row),
   `python3 tools/check_links.py` and `python3 tools/coverage.py --check`.
G1 Artifact identity: both records name the set and variant, the Wine runtime and the binary hash.
   Each names the driver commit it ran from (7470a27 for sitting 8, 08a5765 for sitting 9), and those
   commits exist on main.
G3 Reproduction: the frames and savestates are machine-local, so that tier is not reached. Recompute
   from the records what the PR body says:
   - sitting 8: one exact placement landed (3 to 4), then the placement panel was read as the turn
     menu and PASS failed;
   - sitting 9: 9 of 9 exact placements, 5 of them with the rest on a second country; no fight in 11
     turns; no abandon; stopped by SIGINT with the prefix reset OK.
   Check that progress-r07's cells (30/40) follow from r0001–r0007, and that progress-r01 to r06 and
   records r0001–r0005 are unchanged (`git diff origin/main...HEAD --stat`).
G4 Raw vs interpretation: no record observation carries a conclusion, a finding or question
   reference, or a causal reading. Name every one you find, with its index. Every claim in the PR body
   cites a record that exists.
G5 Alternatives: for "no fight in 11 turns", give at least two other explanations besides growth
   toward sizes no adjacent defender fits (#184), and say whether the records exclude them.
G7 Scope: unregistered Pro under Wine 10.0, at the recorded options.
Rule 18 A and D: no frame, savestate or binary is committed, and no original game text appears in any
   record's observation field or value.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A check above that fails, or cannot be run as written (except G3's frames, which are
   machine-local).
2. What this PR protects can be got past: a run record that does not validate, original game text
   in a record's observation field or value (rule 18 D), an original file or frame committed (rule
   18 A), or a count or outcome that the records do not support. A bypass you proved is blocking,
   even when it looks like an edge case. (L47)
3. A committed record on main edited by this PR (records are immutable; corrections go in as
   notes), or the pre-review wording commit changing anything but wording.
4. An outcome word stronger than its evidence; a status written into a document.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the PR protects; otherwise it is a follow-up. (L53)

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking
finding: finish reading the whole diff and the PR body, check every item above and every item
under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the full diff for anything you have
  not yet rated, and say "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an
  earlier one was already blocking is a review defect: if two problems share a cause, list
  both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review
  checks those fixes and new code only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or
  sections you did not cover. Do not approve in that case.

Your final message is the review:
- line 1: the header above;
- line 2: the record verdict (approve | approve after named fixes | rework | user decision);
- then one line per check: `G<k>: <what you did> → <result>`;
- then `Tier reached: V<k>`, and why not higher;
- then the findings R1..Rn (file:line, blocking or not, and the class: implementation defect,
  contract defect, research uncertainty);
- last line: the verdict again.
Never post it: the script posts it.
