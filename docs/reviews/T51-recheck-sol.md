T51 re-review (Sol)

You re-check PR #197 at a03070282e0780de3d25c3065cd35492a42df86a, narrowly. Your review at 646cb32 asked for rework on R1–R7. The same
Claude (Opus) implementer fixed them in 018164b and a030702; its PR comment lists each fix (file:line)
and its mutation proofs (`gh pr view 197 --comments`). Check only `git diff 646cb32..a030702`, plus any
new code in it. Your working directory is the review worktree: run commands there with no `workdir`
argument, and use relative paths.

0. Prove the tree: HEAD is a030702….
1. For each of R1–R7, repeat your round-1 reproduction against the new text and code, and say fixed,
   not fixed, or partly:
   - R1: the 24–22 revolt case at the round limit;
   - R2: an HTML-commented row, plus a multi-line comment and a fenced block;
   - R3: V11 and C-CRD-04's link;
   - R4: recompute the bonus totals (34–46, and 28–34 for the alternative);
   - R5: the set-versus-income figures and the revised argument;
   - R6: the tiered centre placement, defined for every deal;
   - R7: re-take the cell-count mutation.
   Restore every mutation by writing back the saved contents in a `finally`.
2. Look for a bypass or contradiction the fixes opened: the active_text() stripping, such as a row
   after an unclosed comment, or a fence inside a table; V11 and V12 against T50's decisions; the
   placement tiers against V7's options.
3. Re-run Done-when 1–3 and 5, and read the 12 choices for options, a recommendation and a reason.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: a spec claim with no row, or a wrong decision word, that
   check_design.py accepts for either design file; a feel-changing decision made without being listed
   for the owner; original game text in design/ (rule 18). A bypass you proved is blocking, even when
   it looks like an edge case. (L47)
3. Behaviour nobody asked for inside a file the task owns: the computer opponent's policy designed here
   instead of in T53; an edit outside Owns, such as to design/core-rules.md. (L44)
4. A test that passes with its check deleted; a wrong number that a balance argument rests on; a status
   written into a document; a weakened existing test.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the task protects; otherwise it is a follow-up. (L53)


## Report every blocking finding in this one review

Report every blocking finding in this one pass, numbered R1, R2, … by severity, and make a last pass
over the fix diff before the verdict ("Final pass done"). Your final message is the review: the
header; the verdict (approve | approve after named fixes | rework | user decision); the DW lines; the
findings; the verdict again last. Never post it: the script posts it.
