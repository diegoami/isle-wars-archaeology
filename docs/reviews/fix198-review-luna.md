fix 198 review (Luna)

You review PR #199 at 48be2317909403269e266902b26df54e89e22711. It is a small doc fix by a Claude (Sonnet) subagent. It applies the owner's
decided amendments V7, V9 and V12, from design/variety.md's section "The owner's decisions
(2026-10-12)" and its "Reconciled with T50" note, to design/core-rules.md, and it corrects one comment
in .github/workflows/ci.yml. Read the issue: `gh issue view 198`. Your working directory is the review
worktree: run commands there with no `workdir` argument, and use relative paths.

0. Prove the tree: HEAD is 48be231…, and `git diff origin/main --stat` lists only design/core-rules.md
   and .github/workflows/ci.yml.
1. Each of the three edits says exactly what variety.md's decided V7, V9 or V12 says, and adds no new rule:
   - the event-frequency Options row;
   - deal step 6, placing the centres;
   - the round-limit event pause in Victory.
   Each cites its decision, and the links resolve.
2. Nothing else in core-rules.md changed. The T51 references for the computer are left for T53.
3. The ci.yml change is a comment only.
4. Run `python3 tools/check_design.py`, `python3 tools/check_links.py` and `python3 tools/check_no_originals.py`.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A check above fails.
2. An edit that changes a rule beyond the owner's decided text, or a new rule nobody decided.
3. An edit outside the two files, or ci.yml changed beyond its comment.
Not blocking: wording and style; file those as follow-ups.

Report every blocking finding in one pass, numbered R1, R2, …, and make a last pass before the verdict
("Final pass done"). Your final message is the review: the header; the verdict (approve | approve after
named fixes | rework | user decision); the checks; the findings; the verdict again last. Never post it:
the script posts it.
