PR #188 research review (GPT-5.6 Luna)

You review PR #188 at f293b87463abf63780767c0c2a6a9951b98cfd62. It is a records-only research PR:
the owner's Bandicam sitting IP1 029 (easy level, slow speed), processed into run records E018-r0015
to r0018, their evidence manifests, and an "IP1 029 sitting" section in `runs/E018/CORRECTIONS.md`
with two correction notes. A Claude agent wrote it; you did not. Read the PR body with `gh pr view 188`.
#186 and #187 are merged now, so `git diff origin/main...HEAD` is IP1 029's part, plus the main
session's merge commits and the regenerated `runs/coverage.md`.
Your working directory is the review worktree: run commands there with no `workdir` argument, and use
relative paths. Your job is to try to falsify it.

Check, in order:
G0 Tree and records: HEAD is f293b87…. Run `python3 -m unittest tests.test_runs tests.test_formats`,
   `python3 tools/check_no_originals.py`, `python3 tools/check_links.py` and
   `python3 tools/coverage.py --check`. No record from r0001 to r0014 is changed by IP1 029's commits.
G1 Artifact identity: r0015–r0018 agree with each other, with the video sha256 in the PR body, and
   with the earlier E018 records; the easy level and slow speed are recorded.
G3 Reproduction: the video and frames are machine-local, so that tier is not reached. Recompute from
   the records: 54 attacks (31 human, 23 computer), the exchange and loss totals, 39 captures
   conserving the total, 4 moves and 2 cancelled, the two trade-in offers, and the four-sitting total
   (1,208 exchanges, 56.3%). Every p-value must use Pearson with no continuity correction, the
   convention of the earlier sections. Look for duplicated observations.
G4 Raw vs interpretation: no record observation carries a conclusion, a finding or question
   reference (F0nn, Q-…, C-…), or a causal reading. #186's and #187's reviews found these, and they
   were fixed as correction notes. Name every one you find here. Every outcome cites records and
   offsets that exist, and no outcome word is stronger than its records.
G5 Alternatives: for the attacker-loss share, and for "the scoreboard adds a concession win about
   1.7 s after it appears", give at least two other explanations each, and say whether the records
   exclude them.
G7 Scope: one unregistered Pro sitting at easy level and slow speed. Nothing is generalised to other
   levels without saying so.
Move controls: r0017 confirms the 028 rows within 1 stage pixel. Check that the coordinates in the PR
   body match r0017. ATTACK at 305 was settled in #187's review.
Correction notes: the two notes (IP1 028's scoreboard reading, and the "+1 army" case) are notes
   only, and leave r0013 and the other committed records unchanged.
Rule 18 D: no original game text in any record's `observations[].field` or `.value`.

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
