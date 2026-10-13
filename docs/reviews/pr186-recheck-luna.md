PR #186 re-review (GPT-5.6 Luna)

You re-check PR #186 at 20c5ec4e1d26e1bdb59ae2e9db9aa1a908d79e99. Round 1 was your own review at a2f98c7 (rework: R1, attack 87 listed twice; R2, p = 0.57 vs your 0.476). The main session's fix is commit 20c5ec4; its PR comment explains it (`gh pr view 186 --comments`). Check only the fix (`git diff a2f98c7..20c5ec4`):
0. Prove the tree: HEAD is 20c5ec4….
1. R1: r0006 is unchanged (records are immutable); the correction note in runs/E018/CORRECTIONS.md says attack 87 is one attack, and that every count treats it as one; the duplicated table row is gone. Check the counts in CORRECTIONS.md and the PR body against r0006 counted with step 87 once.
2. R2: recompute the chi-square for list 54/109 vs off-list 55/101 attacker losses, Pearson without continuity correction, and check that the IP1 026 section (list 146/259 vs 99/183, p = 0.64) uses the same convention.
3. Run `python3 tools/coverage.py --check`, `python3 tools/check_links.py`, `python3 tools/check_no_originals.py` and `python3 -m unittest tests.test_runs tests.test_formats`.

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
