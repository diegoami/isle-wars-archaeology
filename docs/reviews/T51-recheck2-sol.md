T51 re-review (Sol)

You check PR #197's third, narrow round at 74bacd6d48b73f2a427e3ca1aaed217b752775e7. Your last re-check (at a030702) found two bypasses
of the inactive-text handling in check_design.py. The owner escalated and chose three things:
1. the check fails closed on any code fence or HTML comment in a design file, instead of parsing
   around them;
2. the owner's V1–V12 decisions are written in as the canonical variant (PR comment of 2026-10-12;
   V5 confirmed as a set of three Raid cards);
3. a new design/variants.md catalogues every T50 and T51 choice's alternatives.
Done-when 4 was amended on main (fe1a7f9) to accept the decisions heading. The same Claude (Opus)
implementer did the round in 8ed6ebf and 74bacd6 (its PR comment lists the mutation proofs). Check
`git diff a030702..74bacd6`. Your working directory is the review worktree: run commands there with no
`workdir` argument, and use relative paths.

0. Prove the tree: HEAD is 74bacd6….
1. The fail-closed check: re-try your two bypasses (fence closers; a comment inside a fence) and any
   other way to hide a decision row: indentation tricks, a `<!--` split across lines, Unicode
   look-alikes for backticks. Re-take at least two of the listed mutations, restoring each by writing
   back the saved contents in a `finally`.
2. The decisions: every V1–V12 decision in variety.md matches the owner's PR comment and is described
   as decided. No `open` row remains. Each "Reconciled with T50" reading is consistent with T50's
   decisions and with the owner's choice. Re-run the re-done models and check the stated swing sizes.
   The conversion of fenced blocks to indented code kept every number.
3. variants.md: every choice from T50 (1–12) and T51 (V1–V12) is there, with the canonical option, its
   alternatives and their interactions; it links the rules rather than restating them; and it has no
   status snapshot.
4. Re-run every Done-when line of the amended task file
   (`git show origin/main:docs/tasks/T51.md`).

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
