PR #187 research review (GPT-5.6 Luna)

You review PR #187 at cee729de35a01f5d74c76bbfa01dee100167b75d. It is a records-only research PR:
the owner's Bandicam sitting IP1 028, processed into run records E018-r0010 to r0014, their
evidence manifests, and an "IP1 028 sitting" section in `runs/E018/CORRECTIONS.md`, including a
"Move controls seen" subsection. A Claude agent wrote it; you did not. Read the PR body with
`gh pr view 187`. #186 (IP1 027) is merged now, so the diff against origin/main is IP1 028's alone,
plus the main session's merge commit cee729d and the regenerated `runs/coverage.md`. Your job is to
try to falsify it.

Your working directory is the review worktree: run commands there with no `workdir` argument, and use relative paths. A mistyped absolute worktree path is refused and ends the run (it ended the first attempt).

Check, in order:
G0 Tree and records: HEAD is cee729d…, and the diff against origin/main is the PR's. Run
   `python3 -m unittest tests.test_runs tests.test_formats`, `python3 tools/check_no_originals.py`,
   `python3 tools/check_links.py` and `python3 tools/coverage.py --check`.
G1 Artifact identity: records r0010–r0014 agree with each other, with the video sha256 in the PR
   body, and with the earlier E018 records on main (`runtime.platform` `windows-native-bandicam`).
G3 Reproduction: the video and its frames are machine-local, so that tier is not reached. Recompute
   from the records:
   - 76 attacks (32 human, 44 computer) and 319 exchanges (attacker lost 183, 57.4%);
   - the three-sitting totals (555/998), using IP1 026 and 027 on main;
   - captures, quits and stops;
   - 28 human move-ins;
   - the bomb results (9 became 4, 3 became 1).
   Check every p-value's convention: Pearson with no continuity correction, as in the IP1 026 and
   027 sections. Look for duplicated observations, like attack 87 in r0006.
G4 Raw vs interpretation: records' observations carry no interpretation. Every outcome cites
   records and offsets that exist, and no outcome word is stronger than the records. Attack 41's
   "+1 army after a capture" stays flagged and unexplained, not explained away.
G5 Alternatives: for the 57.4% loss rate, and for attack 41's +1, give at least two other
   explanations each, and say whether the records exclude them.
G7 Scope: one unregistered Pro sitting at its recorded level and speed.
Move controls: the "Move controls seen" mapping (stage x = (frame x - 125) / 2.169, stage y =
   (frame y - 85) / 1.532) is said to reproduce the existing `walkthroughs/coordinates.md` rows for
   attack (337, 531) and pass (419, 530). Yet the proposed ATTACK row is (305, 530), and #188
   confirms 305. Work out from the records which ATTACK x is right, and whether the two are
   different buttons or states, and say so.
Rule 18 D: no original game text in any record's `observations[].field` or `.value`. Commits
   3cbbaa0 and 938b80b reworded r0012 and r0011 before review: check with `git show` that they
   changed wording only.

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
