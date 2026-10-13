T50 re-review (Sol)

You re-check PR #195 at f77eb742c6050b1f6dbad4a5122b1b29e68fad7a, narrowly. Your last re-review at
6777086 asked for rework on R1 (the generator's 50-attempt bound), R2 (the bonus rule decided without
the owner) and R3 (a status line). The owner then clarified that T50 is a design document and the
generator is built in malpaco's own sessions; the owner also decided the bonus rule (decision 12).
The main session's fix is `git diff 6777086..f77eb74`, explained in its PR comment. Check only that
diff. Your working directory is the review worktree: run commands there with no `workdir` argument,
and use relative paths.

0. Prove the tree: HEAD is f77eb74….
1. R1: [Generation] now states requirements, not an algorithm. A board is seeded and reproducible,
   meets the invariants, and passes the fairness checks, which are not weakened. The engine's tests fix
   an attempt bound, and running out of attempts has defined behaviour. Your prototype is recorded as
   an implementation hazard. Is that a sound design-level requirement that an implementer can meet and
   test? Name any requirement that is still missing or that contradicts another.
2. R2: decision 12 lists the bonus rule with its options, a recommendation and the owner's decision;
   C-BRD-01's row and the Island bonuses section cite it.
3. R3: no status line remains.
4. Run `python3 tools/check_design.py`, `python3 -m unittest tools.tests.test_check_design`,
   `python3 tools/check_links.py` and `python3 tools/check_no_originals.py`.

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


