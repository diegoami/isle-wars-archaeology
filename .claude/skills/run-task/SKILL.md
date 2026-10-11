---
name: run-task
description: Run tasks or fixes end to end. The main session (or a Claude agent it spawns) implements, one OpenCode model of another family reviews, the main session merges and reports. Main session only.
---

# /run-task [T<nn> | #<issue> ...]

Read `docs/process.md` §3–§6 first. Given ids, run them in order; given none, take the first
`status:ready` task in `docs/tasks/README.md`. Report after each task; stop at any escalation.
For `#<issue>` of a bug labelled `fix`, the bug body replaces the task file, the branch is
`fix/<issue>-<slug>`, and there is one review round.

Nothing is asked before a run (CLAUDE.md rule 6, the owner, 2026-10-11): the main session
implements, `harness.json`'s default reviewer reviews, and the user overrides either when they
want to. Ask only for design decisions and escalations.

0. **Check.** The issue is `status:ready` and every Merge-after task is merged. Run
   `gh issue list --label triage:needed --state open`; triage anything that names this task first.
   If `harness.json` has cutoffs for `breaks-play`, route those issues through Jev first (`/jev`
   step 4). Act on its confident ends and triage the middle yourself; exit 3 means triage it all.

   Run every Done-when line yourself: it must fail on `main` and pass on a mock fix (a scratch
   change, then discarded). A line that cannot is amended on `main` before dispatch (L45).

1. **Brief.** The task file **pasted in full**, then `docs/process.md` §4's block, then (on
   rework) the review comment's URL. Never a pointer to the task file. The main session
   implementing itself reads the same block as its contract.

2. **Implement.** Label `status:in-progress`. Either:
   - **The main session**, in its own worktree (`git worktree add ../isle-wars-archaeology-work/T<nn> -b task/T<nn>-<slug> origin/main`,
     never the main checkout): keep `RUN-NOTES.md` there (`docs/running-notes.md`: the plan, a
     line per commit, an END block), push after every commit, open the PR with the template body.
     This is the default for research, for anything that reads the user's install (L26), and for
     any task the session can do in one sitting.
   - **The `implementer` Claude agent**: `Agent(subagent_type: "implementer", isolation: "worktree")`
     with the brief, on the session's model (or another Claude model when the user names one;
     a Sonnet brief carries the tripwire paragraph from `docs/models.md`). Its agent file carries
     §4's block and the run mechanics; its hook refuses `git stash`, `git worktree`, a force-push
     and `gh pr merge`. Watch it by its transcript file's size and its worktree (CLAUDE.md
     rule 6.6); tell the user in plain language what it is doing. Read its final report in full
     before acting (rule 25), and post its `RUN-NOTES.md` on the issue. A report that stops on a
     Done-when it cannot meet gets an answer (amend the task on `main`, decide, or escalate),
     never a blind retry.

3. **Review.** Label `status:in-review`. Name the PR's head in the brief only after the push has
   landed (`git rev-parse <branch>`); a brief naming another commit exits 2 before anything runs
   (L33). Then, as a systemd unit, watched (CLAUDE.md rule 6.6):
   ```bash
   tools/harness/run-unit.sh review-<pr> <log> -- node tools/harness/review.mjs --pr <pr> --brief <file> --issue <n> --apply-label
   ```
   `reviewer.default` (GPT-5.6 Luna) reviews; add `--reviewer gpt-6.1-sol` for a guard, a gate or
   hard research, or `--reviewer <name>` when the user names one (never a Claude model: the
   implementer is Claude). One review per PR unless the user asks for more. Relay its findings
   in full (rule 8).
   - Exit 0: posted and labelled.
   - Exit 3: no review came back (OpenCode, the login, the model, a rejected path, or a review
     the script could not find). Nothing was posted. Read the run's final message first (rule 25,
     the snippet below), fix the cause (a wider grant in `.opencode/agents/reviewer.md`, a login,
     a brief line), and run again. Another model only when the provider does not answer, and the
     user names it.
   - Exit 4: a review was posted whole under a note (cut off, verdict unreadable, verdicts differ,
     a finding after the closing verdict, or an approve with a Done-when line unaccounted for or
     not run, L32). No label was applied. Read it on the PR and decide: apply the label it
     supports, ask for a supplementary review of the missing DW lines, or send it to rework.
     Never pay for a second review just because the first was flagged: OpenCode's models do not
     always follow the brief, and the script's reading is the safety net.
   - **Read before you act (L55).** The final message, read-only (never `auth.json` there), with
     the `session ses_…` id from the run's log:
     ```bash
     python3 - <<'PY'
     import sqlite3, json, os
     home = os.environ.get('HARNESS_OPENCODE_HOME') or os.path.expanduser('~/.local/share/harness-opencode')
     db = 'file:' + os.path.join(home, 'data', 'opencode', 'opencode.db') + '?mode=ro'   # the scripts' data directory
     c = sqlite3.connect(db, uri=True)
     sid = 'ses_...'   # the "session ses_..." line in the run's log
     parts = [json.loads(d) for (d,) in c.execute("select data from part where session_id=? order by time_created", (sid,))]
     texts = [p for p in parts if p.get('type') == 'text']
     print(texts[-1]['text'] if texts else 'no text part')
     PY
     ```
   - A Claude review (`/code-review <pr>`, always with the number, or the `reviewer` agent posted
     with `post-review.mjs`) only when the user asks: it is the implementer's family.

4. **Decide** on the label the reviewer applied.
   - `status:approved`:
     1. Wait for green CI.
     2. Re-run the check the approval rests on most (the Done-when line or the mutation that
        proves the task) on the PR's head yourself. A different result is rework, not a merge (L46).
     3. `gh pr merge <pr> --squash --delete-branch` (`--merge` for a research PR, rule 20), then
        label `status:merged`.
     4. File one `T<nn> follow-up` issue (`triage:needed`) for the non-blocking findings.
     5. Unblock the tasks whose Merge-after are now all merged.
     6. Leave the task's worktrees; the sweep removes old ones (CLAUDE.md rule 2a).
     7. Post §9's measurement comment on the PR, and a model-trials comment when the review taught
        something (rule 21).
     8. Report the merge, the findings, the follow-ups and what is ready next.
   - `status:rework`:
     1. Check that every finding names a file in `gh pr diff <pr> --name-only`. A review that
        does not reviewed the wrong tree: discard it, say so, and re-review.
     2. At `review-round:2` (at `review-round:1` for a fix), go to step 5.
        A reviewer that reports one blocking finding per round despite the brief's one-pass
        section (L49): after the second such round, stop. Request no further review until you
        have gone through the whole diff yourself for that class and fixed what you found, and
        recorded the pattern in the model-trials issue. The review after that is the task's last
        before escalation (step 5).
     3. A heavy review (three or more blocking findings, or a repeated class) is fixed by class,
        not by instance: the next round sweeps the implementer's own code for the same class and
        lists the sweep in the PR body, and changes the approach when the class needs it, saying
        so on the task file. The round count does not reset, and the Done-when is never weakened.
     4. Set the next round and return to step 1, with the full review's URL in the brief. The
        implementer resumes the pushed branch; it never starts over.

5. **Escalate** (`docs/process.md` §7): label `status:escalated`, comment the evidence on the issue,
   and bring the user the decision with options and a recommendation. Stop.
   A defect found in merged code outside the task is filed as a bug (`triage:needed`). If it
   blocks the task: a one-file mechanical fix may ride this PR, declared under Scope; otherwise
   label the task `status:blocked` and stop.

Never:
- merge without an approving review and green CI;
- weaken a Done-when;
- let the implementer's model family review its PR;
- relay part of a review;
- dispatch a `model-driven` task before its carve-out's table and gate are merged (process.md §10, L63).
  Here, that is the rule 18 carve-out's preconditions: the F019 hash table (T35) and the
  `check_no_originals.py` gate (T36) both merged; the T38 task file shape available; the
  implementer's `runtime.platform` set to `wine-on-user-machine-iwp-2.0` with
  `start_state.sha256` matching the F019 row's hash. Since 2026-10-09 (constraint E) model
  sittings count on their own, beside the owner's videos;
- force-push or rewrite `main`.
