PR #187 re-review (GPT-5.6 Luna)

You re-check PR #187 at 04915d188409f274221db392acca8d1d594e4ae6, narrowly. Your round-2 re-review at 64a0fdd found one remaining blocking item: the R1 correction note in runs/E018/CORRECTIONS.md missed derived observations (r0011 obs[1], obs[88]). The main session rebuilt that note in 04915d1 from a full read of every observation value in r0010–r0014 (see its PR comment). Check only `git diff 64a0fdd..04915d1`. Your working directory is the review worktree: run commands there with no `workdir` argument, and use relative paths.
0. Prove the tree: HEAD is 04915d1…, the diff touches only runs/E018/CORRECTIONS.md, and no run record changed.
1. Read every observation value in runs/E018/E018-r0010.json to r0014.json yourself. For each one that carries a finding, question or static-list reference, a fitted formula or rule reading, a comparison with another sitting or source, or a derivation, check that the note names it. Name any it misses, with its observation index.
2. Your round-2 confirmations of R2, R3 and R4 stand; do not re-review them.
3. Run `python3 tools/coverage.py --check` and `python3 tools/check_links.py`.

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
