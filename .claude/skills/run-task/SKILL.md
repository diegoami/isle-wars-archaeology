---
name: run-task
description: Run tasks or fixes end to end. OpenCode (or Claude) implements, a reviewer of another model family reviews, the main session merges and reports. Main session only.
---

# /run-task [T<nn> | #<issue> ...]

Read `docs/process.md` §3–§6 first. Given ids, run them in order; given none, take the first
`status:ready` task in `docs/tasks/README.md`. Report after each task; stop at any escalation.
For `#<issue>` of a bug labelled `fix`, the bug body replaces the task file, the branch is
`fix/<issue>-<slug>` (`--fix <issue>` in the scripts), and there is one review round.

0. **Check.** The issue is `status:ready` and every Merge-after task is merged. Run
   `gh issue list --label triage:needed --state open`; triage anything that names this task first.
   If `harness.json` has cutoffs for `breaks-play`, route those issues through Jev first (`/jev`
   step 4). Act on its confident ends and triage the middle yourself; exit 3 means triage it all.

   Run every Done-when line yourself: it must fail on `main` and pass on a mock fix (a scratch
   change, then discarded). A line that cannot is amended on `main` before dispatch (L45).

1. **Brief.** Write it to a temp file: the task file **pasted in full**, then `docs/process.md` §4's
   block, then (on rework) the review comment's URL. Never a pointer to the task file.

   **Watching background work (CLAUDE.md rule 6.7; L48).** Start every OpenCode run in the
   background with stdin closed (the scripts do it). Watch it with one Monitor (30 minutes,
   re-armed until the run ends) that checks every 1–2 minutes:
   - the session started (the log's `session ses_… started` line), and the run's exit;
   - progress: the session's `updated` time, the worktree's changed files, new `RUN-NOTES.md`
     lines, new commits;
   - "possibly stuck" after about 10 minutes with no change, and "unpushed" when a commit has sat
     unpushed for about 15 minutes (push it for the run, and record that);
   - free memory when the machine is short: reviews and builds one at a time.

   For a Claude agent, the signal is its transcript file's size plus its worktree. Never wait with
   `while pgrep -f '<pattern>'` (it matches itself); wait on the PID with `while kill -0 <pid>`.
   Tell the user, in plain language, what each agent is doing (its step, its commits, what it
   found), never raw log lines or byte counts. On a "possibly stuck" flag, check the process is
   alive and read its newest session messages; a long build or test is not stuck. A run that is
   dead, or 20 minutes silent, is stuck: kill it only if it is ours. A run our own idle or total
   limit interrupted resumes in its own session: `implement.mjs … --model <same> --session <ses_…>
   [--idle-min N --total-min N]`.


2. **Implement.** First ask the user ONE question (CLAUDE.md rule 6.1): does the main session
   implement it, or a subagent, and with which model? Show `/recommend?tier=heavy` (hard work) or
   `tier=light` (small work) as a suggestion only, with its rank, outlook and reliability. Record the
   answer and the suggestion's reasons on the issue. Label `status:in-progress`.
   - **The main session**: it implements in its own worktree (never the main checkout), keeps
     `RUN-NOTES.md` there (the plan, a line per commit, an END block), pushes after every commit,
     and opens the PR.
   - **OpenCode**: run
     `node tools/harness/implement.mjs --task T<nn> --slug <slug> --issue <n> --brief <file> --model <the user's>`
     (`--family`/`--variant` for a model not in `harness.json`) with `run_in_background`, and watch
     it (above); never poll with sleep.
     - Exit 0: a PR is open. Note the `implemented by:` line.
     - Exit 1: read the log it names. An implementer that stopped and reported gets an answer:
       fix the brief or the setup, or amend the task file on `main`, and resume.
     - Exit 3: OpenCode or the model unavailable, or not logged in (the message gives the login
       command). Diagnose and fix it. Another model only when the provider does not answer, and the
       user names it.
   - **Read before you act (L55).** When a run ends, read what it returned before anything else;
     never retry blind. An OpenCode exit 1 with an empty
     diff looks the same for an early end and for a run that stopped and reported a blocker, and
     the log's tail shows only the last tool output. Read the model's final message from the
     session record, read-only (never `auth.json` in that directory), with the `session ses_…` id
     from the run's log:
     ```bash
     python3 - <<'EOF'
     import sqlite3, json, os
     home = os.environ.get('HARNESS_OPENCODE_HOME') or os.path.expanduser('~/.local/share/harness-opencode')
     db = 'file:' + os.path.join(home, 'data', 'opencode', 'opencode.db') + '?mode=ro'   # the scripts' data directory
     c = sqlite3.connect(db, uri=True)
     sid = 'ses_...'   # the "session ses_..." line in the run's log
     parts = [json.loads(d) for (d,) in c.execute("select data from part where session_id=? order by time_created", (sid,))]
     texts = [p for p in parts if p.get('type') == 'text']
     print(texts[-1]['text'] if texts else 'no text part')
     EOF
     ```
     For a Claude agent, read its final report in full. A run that stopped and reported gets an
     answer to its report (amend the task, decide, or escalate), and the report is posted on the
     task's issue so it is kept.
   - **A Claude agent**: `Agent(subagent_type: "implementer", isolation: "worktree")` with the
     model the user named, and the brief. The agent file (`.claude/agents/implementer.md`) carries
     §4's block and the run mechanics, and its hook refuses `git stash`, `git worktree`, a
     force-push and `gh pr merge`. Read its final report, and post its notes on the issue.


3. **Review.** At every review (a first review, a re-review, a re-check of named fixes) ask the
   user ONE question (CLAUDE.md rule 6.2): which external model reviews? Show `/recommend`'s
   suggestion (add `&exclude_family=<the implementer's family>`) as a suggestion only, and record
   the answer on the PR. Never the implementer's family. Run that review alone, one at a time, and
   relay its findings to the user in full. A PR gets one review unless the user asks for more.
   Label `status:in-review`.
   - `node tools/harness/review.mjs --pr <pr> --brief <file> --reviewer <the user's> --exclude
     <implemented by> --issue <n> --apply-label`, in the background. (`--hard`, `--sol` and
     `--second-opinion` picked reviewers from chains, and are refused since 2026-10-11.) Name the
     PR's head in the brief only after the push has landed: take it from the local branch
     (`git rev-parse <branch>`). A brief whose block before the task file names another commit
     exits 2 before anything runs (L33).
     - Exit 0: posted and labelled.
     - Exit 3: no review came back, or OpenCode or its login is unavailable. Read the run's final
       message first. Nothing was posted: diagnose and fix it, then ask the user again.
     - Exit 4: a review was posted whole under a note (it may be cut off, its verdict is
       unreadable, its verdicts differ, or a finding follows its closing verdict), or an approve
       left a Done-when line unaccounted for or not run (L32). No label was applied. For a
       missing `DW` line, run a supplementary review of those lines alone (asking the user which
       model), or send it to rework. Read it on the PR and decide. Never pay for a second review
       just because the first was flagged.
   - A Claude reviewer, when the user names one: first `git fetch origin pull/<pr>/head`, since the
     reviewer has no GitHub credentials (#68); then `Agent(subagent_type: "reviewer", isolation: "worktree")`
     with that model and §5's brief filled in. The agent file carries the rest; its hook refuses every write. It
     **returns** its review: save its final message to a file, then post it with
     `node tools/harness/post-review.mjs --pr <pr> --brief <brief> --review <file>
     --by "claude (<model>)" --issue <n> --apply-label`. Its exits are review.mjs's, but 1 means no
     review was in the message: re-run the reviewer once, then escalate.
   - A further review (`/code-review <pr>` on an architecture task, a second opinion) only when the
     user asks for it and names the model; then always with the PR number.


4. **Decide** on the label the reviewer applied.
   - `status:approved`:
     1. Wait for green CI.
     2. Re-run the check the approval rests on most (the Done-when line or the mutation that
        proves the task) on the PR's head yourself. A different result is rework, not a merge (L46).
     3. `gh pr merge <pr> --squash --delete-branch`, then label `status:merged`.
     4. File one `T<nn> follow-up` issue (`triage:needed`) for the non-blocking findings.
     5. Unblock the tasks whose Merge-after are now all merged.
     6. Remove the task's worktrees.
     7. Post §9's measurement comment on the PR.
     8. Report the merge, the findings, the follow-ups and what is ready next.
   - `status:rework`:
     1. Check that every finding names a file in `gh pr diff <pr> --name-only`. A review that
        does not reviewed the wrong tree: discard it, say so, and re-review.
     2. At `review-round:2` (at `review-round:1` for a fix), go to step 5.
        A reviewer that reports one blocking finding per round despite the brief's one-pass
        section (L49): after the second such round, stop. Request no further review until you
        have gone through the whole diff yourself for that class and fixed what you found, and
        recorded the pattern in the model-trials record. The review after that is the task's last
        before escalation (step 5).
     3. **A heavy review moves the implementer up (L38)**, decided before the next round starts.
        The review just posted is heavy when it asks for rework with three or more blocking
        findings, or when it brings new blocking findings of a class the previous round raised:
        the same kind of defect again, in new or unchanged code (a sibling the last round missed
        counts). Then tell the user, and ask (step 2's question) who implements the next round,
        suggesting a stronger model than the last one. The user's answer decides (CLAUDE.md
        rule 6; *superseded: the fixed ladder GLM-5.3 Flash → MiMo V2.6 Flash → Opus, and
        Sonnet → Opus*). When no stronger model is wanted, the round fixes the class as below, and
        changes the approach when the class needs it (as golden screenshots did in malpaco T02),
        saying so on the task file.
        - The round count does not reset, and the reviewer stays of another family.
          The Done-when is never weakened for the stronger model.
        - Hand-over: stop the current implementer if it is mid-round; save its unpushed work as a
          patch (`git add -N` new files, then `git diff > <patch>`); start the new implementer on
          the pushed branch with the task file pasted in full, every review so far (the current
          one pasted in full), the patch path "to weigh, never to apply blindly", and the
          instruction to fix the class of the findings, not each instance, then sweep its own
          code for the same class and list the sweep in the PR body.
        - Record the change on the task file's Implementer line, committed on `main`, with the
          reason: the blocking counts, and for a repeated class, the class and the finding ids of
          both rounds (e.g. "R1–R2 of round 0 and R3 of round 1: an alias at write time"). After
          the round, the measurement comment (§9) gives the models, the trigger, the classes, the
          blocking counts before and after, and whether it converged.
     4. Set the next round and return to step 1, with the full review's URL in the brief (and,
        after step 3, the hand-over's). The implementer script resumes the branch.

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
