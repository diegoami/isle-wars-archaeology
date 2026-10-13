PR #189 re-review (GPT-6.1 Sol)

You re-check PR #189 at 9db638b24a0d1f7e13a2a342bbbd423ba5f7278a. Round 1 was your own review at b849026 (rework, R1–R7), with the main session's review after it; both are comments on the PR (`gh pr view 189 --comments`). The fix is commit 9db638b, by a Claude agent, and its PR comment lists each fix and a mutation table. Check those fixes, plus any new code in 9db638b. Do not re-review the rest of the PR.

0. Prove the tree: HEAD is 9db638b…, and `git diff b849026..9db638b` is the fix.
1. Re-run every line of the PR body's Done-when block, and `node tools/harness/switch-model.mjs --role implementer --model deepseek-v4-pro --dry-run` (it must refuse).
2. For each of R1–R7, repeat your round-1 reproduction against the new code, and say fixed / not fixed / partly.
3. Re-take at least three rows of the agent's mutation table yourself (M1, M2, M8 at least): delete the behaviour, run `node tools/harness/review.mjs --self-test`, see it fail, then restore by writing back the saved contents in a `finally` (never git checkout/restore/reset). Explain M5b (exit 0) and say whether it hides a gap.
4. Look for a bypass the fix itself opened: `canonicalFamily`, the hostname parse (ports, userinfo such as `https://anthropic.com@api.z.ai/`, IDN, uppercase), and the session-family union on every path.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this PR protects can be got past: the family rule (a reviewer of the implementer's or
   the session's family is refused by `review.mjs` and `switch-model.mjs`; an unknown endpoint
   refuses to review until `HARNESS_SESSION_FAMILY` is set), and the blocked list (a blocked
   model, e.g. DeepSeek on any route, is refused as reviewer or default). A bypass you proved is
   blocking, even when it looks like an edge case. (L47)
3. Behaviour nobody asked for, or a file left broken by a removal (a script, skill, hook, test
   or CI step that still calls a removed file or flag). (L44)
4. A test that passes with the behaviour deleted; a status snapshot written into a document
   (CLAUDE.md rule 3); a rule that names the orchestrator's own model.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the PR protects; otherwise it is a follow-up. (L53)

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
