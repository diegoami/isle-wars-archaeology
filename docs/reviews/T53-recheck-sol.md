T53 re-review (Sol)

You re-check PR #200 at 352b1d47b3b2bee943bd390e4f8b25facf678b0b, narrowly. Your review at daf8c57 asked for rework on R1–R4 (R5–R7 were
follow-ups). The Opus implementer fixed all seven in cf261bf and wrote in the owner's A1–A12 (its PR
comment lists each fix, file:line). Then the owner decided the new calls A13–A17, all as recommended,
and the main session wrote them in at 352b1d4. Check `git diff daf8c57..352b1d4`. Your working
directory is the review worktree: run commands there with no `workdir` argument, and use relative paths.

0. Prove the tree: HEAD is 352b1d4….
1. For each of R1–R7, repeat your reproduction against the new text, and say fixed, not fixed, or partly:
   - R1: A13–A15 offered and now decided;
   - R2: your 3-against-1 move-in case with a 10-army neighbour, now a legal split;
   - R3: re-run the 3726-setup enumeration, and check adjusted counts against your [11,11,24] case and
     A16's decision;
   - R4: the 36-step bound and the watch budget, with the 1000-against-100 battle;
   - R5: the placement fallback;
   - R6: unseen copies;
   - R7: seed-clustered intervals.
2. The owner's decisions A1–A17 match the PR comments, A11 against the recommendation. No `open` row and
   no undecided choice remains. variants.md's canonical lines match.
3. The two core-rules amendments (A1/A3 Options and the record; A8 Randomness) say what the decisions
   say and nothing more.
4. Look for any contradiction or new gap the fixes opened: the adjusted-count formula and seat-blindness,
   the watch budget changing play, the move-in priority.
5. Re-run Done-when 1–3 and 5 of the amended task file (`git show origin/main:docs/tasks/T53.md`), and
   read the decisions section and the variants section for Done-when 4.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: a spec claim with no row, or a wrong decision word, that
   check_design.py accepts for the third file; a computer that cheats (extra information, rules only it
   follows, or randomness that alters the shared dice); a feel-changing decision made without being
   listed for the owner; original game text (rule 18). A bypass you proved is blocking, even when it
   looks like an edge case. (L47)
3. Behaviour nobody asked for inside a file the task owns, or an edit outside Owns. (L44)
4. A test that passes with its check deleted; a wrong number that an argument rests on; a status written
   into a document.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the task protects; otherwise it is a follow-up. (L53)


## Report every blocking finding in this one review

Report every blocking finding in this one pass, numbered R1, R2, … by severity, and make a last pass
over the fix diff before the verdict ("Final pass done"). Your final message is the review: the
header; the verdict (approve | approve after named fixes | rework | user decision); the DW lines; the
findings; the verdict again last. Never post it: the script posts it.
