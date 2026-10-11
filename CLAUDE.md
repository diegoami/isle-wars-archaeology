# isle-wars-archaeology

An evidence-backed behavioural specification of *Isle Wars* (DOS) and *Isle Wars Pro* (Windows),
both by Soleau Software, built by controlled experiments on the original games, using the method of
[game-archaeologist](https://github.com/diegoami/game-archaeologist).

**What it is for** (the owner's decision, 2026-10-02): the specification feeds
[malpaco](https://github.com/diegoami/malpaco), an original game inspired by *Isle Wars Pro*.
malpaco should know its predecessor's strengths, and have a UI at least as good as Pro's. On
2026-10-03 it restarted in TypeScript. The Godot proof of concept, whose rules and numbers were
guesses, is archived as [malpaco-godot-poc](https://github.com/diegoami/malpaco-godot-poc); its
research questions are in `questions/malpaco.md`. The game design will come from this
repository's reviewed findings. The research also targets what the
game needs. Everything learned, in both repositories, is recorded so that other projects can
learn from it too.

The process is `docs/process.md`; read it before running a task. Tasks are `docs/tasks/T<nn>.md`,
indexed in `docs/tasks/README.md`.

## Rules
1. The main session plans, runs `/run-task`, triages and talks to the user. Who implements and who
   reviews is the user's choice, asked each time (rule 6). It delegates repeated decisions to Jev after a trial, and
   images and audio to OpenRouter or ElevenLabs models, whose ids come from live lists, never memory.
2. Nobody works in the main checkout but the main session: OpenCode runs in the worktree the script
   makes, Claude agents run with worktree isolation. Never `git stash`.
2a. **Never remove a worktree** (the owner, 2026-10-11, from goal2-archaeology, where the main session
    removed a running review's worktree during a cleanup and the review was lost): not after a merge,
    not in a cleanup, not one that looks finished. This machine is shared, so a worktree may belong
    to another session's live run. The harness scripts' removal of their own worktree at the end of
    their own run is theirs. Old worktrees go only through the **sweep**, at session start (rule 14)
    and at least once a day. A worktree is old when ALL of these hold:
    - no process has its cwd or an open file in it (`ls -l /proc/*/cwd`, `lsof +D`);
    - no systemd unit or monitor of this or another session uses it;
    - its newest file and its last commit are more than 7 days old;
    - its branch is merged or gone on origin;
    - it is clean, or its diff is saved as a patch beside it first.

    Keep its run outputs (savestates, sitting logs, notes) before removing it. Anything in doubt
    stays, and the sweep reports what it removed and what it kept, and why.
3. Status lives in GitHub labels. No document carries a status snapshot.
4. A question is not a request to edit files. Answer it; propose any fix and wait.
5. The Done-when is not negotiable by the implementer. It stops and reports; it never weakens an
   assertion, skips a test or edits its task file. The main session amends a Done-when on `main`
   with the reason in the commit message.
6. **Choosing models: the user decides** (the owner, 2026-10-11). This replaces every earlier
   model-choice rule in this repository: the 2026-10-03 pairs, the 2026-10-10 "/recommend decides",
   `harness.json`'s chains and substitutes, the escalation ladder's named models, and #163. The old
   rule 6 is kept as history in `docs/models.md` ("Superseded model-choice rules"). It must work
   whatever model the orchestrator itself runs on, so it never names the orchestrator's model.
   1. **Before implementing anything** (a task, a fix, a plan change), ask the user ONE question
      with the question tool: does the main session implement it, or a subagent, and which model?
      - The main session implements itself, in its own git worktree (never the main checkout).
      - A subagent is the Agent tool with the model the user names (any model this session's
        backend offers), or an external run (OpenCode, `implement.mjs --model <name>`) with the
        model the user names.

      Whoever implements works in its own worktree and keeps a short running-notes file there
      (`RUN-NOTES.md`: the plan, a progress line per commit, an END block before stopping). It
      pushes after every commit, and opens the PR. When a subagent ends, the main session reads
      its final report before acting (rule 25), and posts its notes on the issue.
   2. **At every review** (a first review, a re-review, a re-check of named fixes), ask the user ONE
      question: which external model reviews? Run that review alone, one at a time
      (`review.mjs --reviewer <name>`), and relay its findings to the user in full (rule 8). A PR
      gets one review unless the user asks for more.
   3. With each question, show quota-tracker's recommendation as a **suggestion only**:
      `curl -s "http://localhost:8765/recommend?tier=heavy"` for heavy work (a hard task: a guard,
      a gate, a new mechanism across files, a new dependency, or a task whose last round found
      bypasses), `tier=light` for small work. Give its `pick`/`pair` with rank, outlook and
      reliability. If it does not answer, ask without the suggestion.
   4. **The only fixed rules:**
      - the reviewer is never of the implementer's family (`review.mjs` refuses it);
      - DeepSeek is never used, on any route;
      - Alibaba only when the user asks.
   5. Record each choice (who, which model, the suggestion and its reasons) on the issue or PR.
   6. A failed run is diagnosed and fixed, not silently re-routed: another model only when the
      provider does not answer, and the user names it.
   7. **Watching OpenCode runs, and any other background agent:**
      - Start every OpenCode run in the background, with stdin from a file or closed, never an
        inherited pipe. `opencode run` waits for stdin's end-of-file before it creates a session;
        the scripts close it. Never wait on a run blind.
      - Watch it with one monitor that checks every 1–2 minutes:
        - that the session started (the run log's `session ses_… started` line, or
          `opencode session list` in the run's directory), and the run's exit;
        - progress: the session's `updated` time, the worktree's changed files, new lines in
          `RUN-NOTES.md`, and new commits on the branch;
        - "possibly stuck" after about 10 minutes with no change;
        - "unpushed" when a commit sits on the branch but not on origin for about 15 minutes: push
          it for the run, and record that;
        - free memory, when the machine is short of it: run reviews and builds one at a time.

        For a Claude subagent, the progress signal is its transcript file's size plus its
        worktree.
      - Tell the user, in plain language, what each running agent is doing: the step it is on,
        what it committed, what it found (from its notes, commits and latest session messages).
        Never raw log lines or byte counts.
      - On a "possibly stuck" flag: check that the process is alive, and read its newest session
        messages (`opencode export <ses_…>`, or rule 25's reader). A long build or test step is
        not stuck. A run that is dead, or silent for 20 minutes, is stuck: kill it only if it is ours.
      - When a run ends, read its final message before doing anything else (rule 25). A run that
        stopped and reported a blocker gets an answer (fix the brief or the setup), not a retry on
        another model.
      - A run that our own limits interrupted (the idle or the total timeout) is resumed in its own
        session and worktree, not restarted: `implement.mjs … --model <same> --session <ses_…>
        [--idle-min N --total-min N]`, which sends a short "continue where you stopped" message.
   8. **Still in force**, because they are not model choices:
      - **Effort**: a heavy model (Opus, GPT-6.1 Sol, GLM-5.3, MiMo v2.6 Pro, MiniMax-M3) runs at
        `medium` at most, and at `low` when medium is not needed. A model with no medium takes its
        lowest variant at or below `high`. A light model stays at `high`.
      - **Sonnet's tripwire**: every Sonnet brief carries the paragraph in `docs/models.md`. On an
        `ESCALATE`, the main session asks the user who answers it, or who takes the task over.
      - **Reach** (L26): OpenCode cannot reach the user's install or a cloud session. The main
        session runs the lines that read the install and posts their output on the PR, so only
        choices that can do the work are offered.
      - **Cloud sessions**: a cloud brief starts by checking the hostname and that `/mnt/c` is
        absent, and stops if either check fails.
      - Every model id comes from a live list (`opencode models <provider>`), never memory.

   The working strategy, how runs are made and what each model has shown are in `docs/models.md`,
   kept identical to malpaco's copy; the main session keeps it current.
7. Merge only with an approving review and green CI. Two rework rounds, then escalate.
   Exception (the owner, 2026-10-05): when the remaining findings are small and change no result
   (wording, a narrowed claim, a missing test or correction note), the main session grants a third,
   narrow round for those findings only, without escalating. A finding that could change a result,
   or let a protected rule be bypassed, still escalates.
8. Relay review findings in full, never a subset.
9. A test proves behaviour only if it fails when the behaviour is removed; a claim that nothing
   failed is re-taken before it is believed.
   Undo a mutation or scratch edit by writing back the file's saved contents (read it first,
   restore it in a `finally`), or commit first; never `git checkout`, `git restore` or `git reset`
   a file with uncommitted work: they return the last commit and destroy the rest. Keep the saved
   copy inside your worktree (`<file>.saved`, deleted afterwards) or in your `mktemp -d` folder, never
   as a loose file in `/tmp`: OpenCode refuses writes outside the worktree except in that folder. (The owner, 2026-10-11:
   in another project, a `git checkout <file>` used to undo a mutation wiped a whole rework round's
   uncommitted edits; here fix-87's implementer lost its uncommitted file the same way.)
10. A comment asserting behaviour at an edge arrives with the test that visits that edge.
11. Until the first playable build, schedule only bugs that break play; label the rest
    `post-playable`.
12. A bug whose fix stays in the files it names and changes no outcome is a `fix`; a blocking
    one-file mechanical fix may ride the PR that found it, declared under Scope.
13. Design decisions go to the user; nothing else waits for the user.
14. At session start: `gh issue list --label triage:needed --state open`, any task in flight, and
    the worktree sweep (rule 2a).

## Token economy
15. A brief carries the task file pasted in full, never a pointer to it.
16. Keep every file an agent must read under ~20k tokens. Scope searches to the source and test
    directories; keep terminal output quiet; show diffs, not files.

## Conditional
17. [evidence-driven] Every constant in runtime or parser code (an address, an offset, a timing)
    traces to a finding or a representation claim; a guessed value says so and what was searched.

## This project
18. **No original game files, ever** (game-archaeologist ADR-006, U2: no licence; explored, never
    copied). The game is an original work inspired by the originals: their code, assets, text and
    name are never reused (owner, 2026-10-02). Only behaviour and design learned here passes to
    malpaco, and no evidence ever does. Executables, data and help files, and patched builds stay
    on the user's own machines. They are never in this repository, a release, an issue or a cloud
    session. `tools/check_no_originals.py` runs in CI. Derived output (decompiled code, listings)
    may be read by the reviewing models' APIs (Anthropic, OpenAI, Z.ai, and Alibaba since the
    owner chose Qwen for T21 on 2026-10-06), and is never published (the owner, 2026-10-05, T29).
    Free OpenRouter models never see it.

    **Carve-out (owner, 2026-10-08): model-driven run capture under Wine on the user's machine.**
    A model agent may run the original Pro binary under Wine for the purpose of T28-style run
    capture and T24-style UI observation, on the user's machine, with the following constraints.
    This carve-out does not apply to the DOS original (C2), to any non-Pro game, to free OpenRouter
    models, or to any cloud session.

    - **A. Locality.** The binary, the installer, the install directory, the run copy, savestates,
      memory dumps, screenshots, recordings, and any patched build stay on the user's machine.
      They are never in this repository, a release, an issue, a cloud session, or any tool input
      that leaves the user's machine, with one exception (the owner, 2026-10-08): the screenshots
      and frames of a model-driven sitting may be read by the same model APIs as derived output
      (Anthropic, OpenAI, Z.ai, Alibaba), to inspect a sitting or review its records. They hold no
      confidential information. Free OpenRouter models never see them, and they are still never
      committed, uploaded or posted. The binary, the install, the run copy, savestates, memory
      dumps and patched builds stay under the full bar. The carve-out adds the option of a Wine
      process under the agent's control, on the same machine, for run capture; it does not move
      the binary.
    - **B. Static-first gate.** A model agent that runs the original does so under the existing
      static-first rule (rule 24): the Lingo is read and the Lingo reading names the state and
      the input the model will probe before any run is made. A run is made because the static
      reading is exhausted, not because the tool is convenient.
    - **C. Per-run tagging.** Per-frame evidence from a model-driven run is recorded as class
      `recording` in the evidence manifest (formats/evidence-manifest-1), not as `screenshot` of
      a human session. The run record's `runtime.platform` is `wine-on-user-machine` (or a more
      specific token the task file names). The binary's sha256 is in `start_state.sha256` against
      the F019-known hash.
    - **D. Text handling.** The text of the original (event names, card names, screen labels, the
      title "Isle Wars Pro") is paraphrased or quoted only in the per-claim finding, not in run
      records' `observations[].field` or `observations[].value`. The rule's "their ... text and
      name are never reused" wording holds in the run record; the per-claim finding is where the
      original's text is cited, with the same rules as a static reading's quote.
    - **E. Two sources, both counted** (amended by the owner, 2026-10-09; it was "corroboration,
      not replacement"). Model-driven sittings may carry T28's per-claim counts on their own, and
      may be scheduled to run unattended. The owner's Bandicam videos stay open as a source at
      any time: a video the owner provides is processed by the playbook, and its counts add to
      the same per-claim totals. Each record names its source in `runtime.platform`
      (`wine-on-user-machine…` or `windows-native-bandicam`), and a finding says which records
      it cites. What only a human sitting shows (mistakes, hesitation, tactics, and the
      computer's answer to them) still rests on the owner's videos. The playbook
      (`walkthroughs/video-walkthrough.md`) says so.
    - **F. Tool check.** `tools/check_no_originals.py` gains a check: a model run with
      `runtime.platform` starting with `wine-on-user-machine` is allowed iff the run record's
      `start_state.sha256` matches the F019-known `Islepro.exe` hash for the set+variant the run
      record names. The existing case-insensitive `*.[eE][xX][eE]` bar remains.
    - **G. Per-claim wording.** "The human" / "the owner's play" wording in `spec/` and
      `findings/` is amended per claim, not in bulk. A bulk re-write would falsify readings that
      genuinely are about the human. The amendments are made by the per-claim finding's
      promotion, the same path every spec change takes (rule 20).

    **Out of scope of this carve-out (separate decisions if you want them).**
    - DOS Isle Wars (C2): not covered. The DOS original stays out per rule 18's body and
      rule 19's scoping.
    - Cloud sessions: not covered. Rule 6's cloud brief is unchanged.
    - Free OpenRouter models: not covered. The free-models bar in rule 18 is unchanged.
    - Anything outside the Isle Wars Pro binary: not covered.

    **What stays unchanged.**
    - Rule 18's first paragraph (the "no licence; explored, never copied" wording, the "their
      code, assets, text and name are never reused" wording, the "behaviour and design learned
      here passes to malpaco, and no evidence ever does" wording) is unchanged.
    - The no-originals-in-repo / no-originals-in-release / no-originals-in-issue /
      no-originals-in-cloud-session bar is unchanged.
    - Rule 20 (measurements are committed) is unchanged.
    - Rule 24 (static first) is unchanged.
    - The T29 carve-out for the decompiled Lingo is unchanged.

    **Companion changes (in follow-up commits, owner's call).**
    - `walkthroughs/video-walkthrough.md`: add a "Model plays under Wine" section that names the
      watcher, the click-driver, the per-frame evidence bundle, and the "corroboration, not
      primary evidence" framing.
    - `tools/check_no_originals.py`: add constraint F's check, behind a feature flag if you want
      to land this in two steps.
    - `F019` (pro setup rules): pin the known-good `Islepro.exe` sha256 for the set+variant the
      run records will name, in a table the new check reads.
    - A new T-number, `T<nn>`, for the Wine-driver work, with a task file naming the
      implementer, the reviewer, the difficulty, and the Done-when. Its Merge-after is the list
      of T-numbers whose claims depend on the "human plays" wording and which `T<nn>` will
      amend.
    - The harness copies in `docs/process.md`, `TEMPLATE.md`, the `run-task` and `delegate`
      skills, and `harness_imperial` propagate this rule change (memory:
      propagate-harness-fixes). They are amended when the next task that reads the carve-out is
      dispatched, not in this commit.
19. **Pro is the subject; DOS is history** (U3, U11; the owner, 2026-10-05). The research reads and
    corroborates Windows *Isle Wars Pro*, the shareware/unregistered release. DOS *Isle Wars* findings
    stay as they are, scoped to DOS, and no new DOS work is planned: the two games may differ, so a
    Pro claim never rests on DOS evidence. What registration unlocks is `unknown`, except what Pro's
    own code shows the unregistered build gates.
20. **Research follows game-archaeologist ADR-007/008.** Run records are raw and immutable
    (`formats/run-1.schema.json` at the commit `archaeology.json` pins), evidence bundles are release
    assets, and findings start `proposed`. Only the main session writes `spec/`, after review. Unknown
    stays `unknown`. This repository is private (U5).
    - **Measurements are committed as they are made, and never deleted** (game-archaeologist
      `lessons.md` L207, and `method/research-protocol.md` §2 on its main, 2026-10-04).
      - Every output a finding or a PR may cite is written under a tracked path the task owns, never
        only under `scratch/`, a cache or a machine-local folder. That covers run records, probe
        logs and tables, timings, evidence captures (by hash, with the bundle on the release) and
        static extracts.
      - Originals, and anything rule 18 keeps out, stay out: record their hashes instead.
      - Commit and push after each batch of runs or probes, and at least every 30 minutes.
      - Never delete or overwrite a measured output. A re-run writes new files beside the old
        ones, and the finding says which ones it cites.
      - This reaches every brief for a task that measures (research, runtime spikes, drivers that
        time things, static reading), as the standing paragraph in `docs/models.md`.
21. **Model trials** (the owner's decision, 2026-10-02). The record shows the user which models are
    viable. After every implement or review run, the main session adds one comment to
    the model-trials issue (implementers and reviewers post only on their own PR):
    - the model, its role and the task;
    - the exit code, the duration and the review round;
    - what the review caught or missed.

    A model that fails is diagnosed and fixed before any fallback: its log, the brief, the agent
    file, the harness and the login. It is then retried. The diagnosis goes in the same comment.
22. **Be practical** (the owner, 2026-10-05, a lesson from goal2-archaeology). Be flexible: when
    something is true with a probability of 80–90%, accept it rather than spend much more time
    proving it, and say how sure you are.
    - **Work:** stop investigating once the answer is clearly likely.
    - **Reviews:** blocking is for a likely problem that gets past what the task protects (a seal,
      rule 18's originals, a claim with no evidence). An unlikely edge case, or one a later run would
      expose loudly, is a follow-up.
    - **Research:** a likely reading is stated with its confidence, as a narrowed claim or a
      hypothesis. `spec/` still changes only by promotion of reviewed outcomes, and unknown stays
      unknown (rule 20).
23. **The plan is the task issues** (the owner, 2026-10-05). Every task, written or planned, is a
    GitHub issue labelled `task`, with its T-number in the title and its Merge-after in the body.
    Its `status:*` label is its status (rule 3); a task not yet written is `status:planned`. Nothing
    else holds the plan: `docs/tasks/README.md` only indexes the task files that exist. The main
    session keeps the issues current, whenever a task is written, merged, parked or re-planned, or
    the owner changes direction, and checks them at session start (rule 14) and end. To read the
    plan: `gh issue list --label task --state all`.
24. **Static first** (game-archaeologist U32 at `9a224a3`; the owner, 2026-10-05). A research
    question is answered by unpacking and decompiling or disassembling the executable first (Ghidra
    for DOS x86, a recorded Director decompiler for Pro's Lingo), on the owner's machine. Runs of
    the game are made only when static analysis cannot answer, or to corroborate a static answer.
    - A finding resting on runs says, in its Method, what static analysis was tried and why it was
      not enough.
    - A missing tool is never a reason: install it, or stop and report. Runs made because a tool
      was missing are a contract defect (research review gate G0a).
    - Rule 18 holds: unpacked executables, Ghidra projects, extracted casts and decompiled code stay
      on the owner's machine. Findings cite the binary's sha256 and the address or handler, and
      describe behaviour in our own words.

25. **Read a delegated run's result before acting on it** (the owner, 2026-10-05, from
    goal2-archaeology T23). Before retrying a delegated run, re-routing it to another model, or calling
    it a failure, read what it returned. Never retry blind.
    - OpenCode runs (`implement.mjs`, `review.mjs`): exit 1 with an empty diff looks the same for an
      early end and for a run that stopped and reported a blocker, and the log's tail shows only the
      last tool output. Read the model's final message from the session record, read-only, with the
      session id from the run log's `session ses_…` line (never read `auth.json` in that directory):

      ```bash
      python3 - <<'PY'
      import sqlite3, json
      db = 'file:' + __import__('os').path.expanduser('~/.local/share/harness-opencode/data/opencode/opencode.db') + '?mode=ro'
      c = sqlite3.connect(db, uri=True)
      sid = 'ses_...'
      parts = c.execute("select data from part where session_id=? order by time_created", (sid,)).fetchall()
      texts = [json.loads(d) for (d,) in parts if json.loads(d).get('type') == 'text']
      print(texts[-1]['text'] if texts else 'no text part')
      PY
      ```
    - Claude agents: read the agent's final report (its hand-back) in full before acting.
    - A run that stopped and reported gets an answer to its report: amend the task, decide, or
      escalate. Post the report on the task's issue so it is kept.
    - Any earlier "model X ends runs early" verdict is unconfirmed until its runs' final messages
      have been read.

26. **Split a task when its parts can merge on their own** (the owner, 2026-10-09; widens L58).
    When a task is planned, and again whenever its scope grows, the main session splits it into
    separate tasks or fixes if the parts can each merge on their own and each part's Done-when
    passes without the others. Split when any of these holds:
    - **Different difficulty or pair:** one part is a guard, gate or new mechanism (hard) and the
      rest is not (easy). Each part gets its own choice of models (rule 6), so an easy part is not held to a hard review,
      and a hard part is not reviewed as easy. (T39's catalogue and the check's hash verification,
      #140, 2026-10-09.)
    - **Different hands:** one part reads the user's install (a Claude agent or the main session, L26), and
      another is repository-only work OpenCode can do.
    - **One part can be blocked** (on the owner, on quota, on another task) while the others are
      ready.
    - **L58's case:** the task is likely to outlast one implementer run (about an hour), or its
      Done-when is all or nothing. Then split it into milestones, as L58 says.

    Limits:
    - Every part is a task issue or a `fix` with its own Done-when (rule 23). The order between
      parts goes in Merge-after, and every merge leaves `main` green and consistent.
    - Never split below a part a reviewer can judge alone, nor by function within one file (L5: 27
      PRs that only widened a list). Each extra part costs a review round, so a part that has none
      of the reasons above stays in its task.
    - A defect found mid-task is a separate fix, unless rule 12 lets it ride along.
    - The implementer never splits its own task. It stops and reports (rule 5), and the main
      session decides.
    - Not yet carried to `docs/process.md`, `TEMPLATE.md` or harness_imperial and malpaco: that
      happens in one pass with the MiMo switch (the owner, 2026-10-09).
