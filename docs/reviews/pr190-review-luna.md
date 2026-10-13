PR #190 review (GPT-5.6 Luna)

You review PR #190 at a76c88260ac336bcfd3c07cd4425ec1c17a4bf0e. It is a docs fix: a new section
"Move and turn controls (owner videos)" in `walkthroughs/coordinates.md`, with the move and turn
buttons read from the owner's videos IP1 028 and IP1 029. Those are E018 records r0012 and r0017,
merged today with PRs #187 and #188. The implementer subagent on Sonnet wrote it; you did not. Read
the PR body and its comments (`gh pr view 190 --comments`). Your working directory is the review
worktree: run commands there with no `workdir` argument, and use relative paths.

Check:
1. Prove the tree: HEAD is a76c882…, and the diff against origin/main touches only
   walkthroughs/coordinates.md.
2. Every coordinate in the new section equals the stage coordinates in E018-r0012 obs[26] and
   E018-r0017 obs[18] (read them on origin/main: `git show origin/main:runs/E018/E018-r0017.json`):
   ATTACK (305, 530), MOVE (369, 530), PASS (419, 530), CARD (468, 531), CANCEL (514, 528),
   counter ALL (309, 539), + (373, 539), − (420, 539), DONE (495, 539). The move sequence the section
   states also matches r0012 obs[25] (MOVE, source, destination, counter starting at 1, ALL/+/−, DONE;
   CANCEL abandons).
3. The section notes the existing rows that differ, and leaves them unchanged:
   - ATTACK 337,531 vs 305,530 — your review of #187 found 305 is the centre and 337 an older reading
     of the same button;
   - PASS 417 vs 419;
   - the placement panel at y 543 vs the move counter at y 539.
   Say whether the new section's wording about these differences is accurate, and whether a reader or
   driver could be misled (337 has been clicked successfully in earlier sittings, E002 s4). Leaving the
   old rows is the implementer's brief; a recommendation to update them is a follow-up, not blocking.
4. Rule 18 D: button names are given as our own labels, and no original screen text is quoted.
5. Run `python3 tools/check_links.py` and `python3 tools/check_no_originals.py`.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A check above that fails, or cannot be run as written (except G3's frames, which are
   machine-local).
2. What this PR protects can be got past: a coordinate that does not follow from the cited records, or
   that a driver following the file would click wrongly; an original file or frame committed (rule 18 A). A bypass you proved is blocking,
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
