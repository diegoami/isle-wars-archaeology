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

**The goal is a fun game, not a copy** (the owner, 2026-10-11). malpaco should be fun, roughly
balanced and varied, with the cards adding some unbalance and surprise. It need not replicate Pro's
rules exactly: Pro's rules, as read from its code, are the starting point that the design keeps,
changes or replaces. So the research is good enough when a rule's reading is backed by the code and
the core of it has been seen in play:
- Corroboration counts are nice to have. A recording or a sitting adds to them when it happens to
  cover a question, and nobody chases a cell for its own sake (Session A stopped at 30/40 that day:
  the open cells needed defenders of 11–21 armies, and the rule as read does not depend on size).
- The questions and what covers each one are in `runs/coverage.md`, regenerated from the records
  (`python3 tools/coverage.py`), so each recording or sitting covers them incrementally and the
  owner can see what is still worth playing.
- The owner's recordings are most useful where only a human shows it: cards in real play, how a
  game feels (length, swings, the computers' strength), and notes after playing.
- The next step is malpaco's design: the spec's rules marked kept, changed for fun or balance, or
  new, with the choices listed for the owner.

The process is `docs/process.md`; read it before running a task. Tasks are `docs/tasks/T<nn>.md`,
indexed in `docs/tasks/README.md`.

## Codex compatibility

For the bounded local audit, known gaps and operating steps, read
[`docs/client-compatibility.md`](docs/client-compatibility.md).

`AGENTS.md` remains a pointer to this file: Claude and Codex share these rules.
Codex may be the main session and implement directly in its own worktree after the
rule 6.1 question. Claude's Agent tool, hooks and slash commands are Claude-specific;
Codex follows the same process with its available tools and reads the corresponding
`.claude/skills/<name>/SKILL.md` when needed. Do not invoke unavailable Claude tools.
Codex does not load Claude's hooks or agent permission grants; its own sandbox and
approval rules apply. Never disable them to imitate a Claude grant.

The harness identifies Codex through `CODEX_THREAD_ID` or `CODEX_SESSION_ID`, or
`HARNESS_CLIENT=codex` for detached jobs. Codex's family is `openai`; explicit
`HARNESS_SESSION_FAMILY` overrides retain precedence. `HARNESS_CLIENT=claude`
preserves Claude endpoint detection even when inherited Codex markers exist.
`CODEX_HOME` alone does not identify the current client.

Use `node tools/harness/opencode.mjs <arguments>` for direct OpenCode calls.
The harness checks the selected CLI before a model run and reports fallback to a
supported `opencode.bak` or `opencode.<version>.bak` beside the CLI, on PATH or in
`~/.opencode/bin`. `HARNESS_OPENCODE_BAK` selects a backup explicitly;
`HARNESS_OPENCODE_EXE` selects the primary. The fallback changes the executable,
never the model or credentials. Read-only commands (`models`, `export`, `--version`)
may retry with the backup after failure; model runs are never replayed automatically.
Read their final messages and diagnose failures under rule 25.

## Rules
1. The main session plans, runs `/run-task`, triages and talks to the user. A subagent it spawns
   implements (or it does itself), and OpenCode reviews, asking the user before each (rule 6). It delegates repeated decisions to Jev
   after a trial, and images and audio to OpenRouter or ElevenLabs models, whose ids come from live
   lists, never memory.
2. Nobody works in the main checkout but the main session: the main session implements in a
   worktree of its own, OpenCode's reviewer runs in the worktree the script makes, Claude agents run
   with worktree isolation. Never `git stash`.
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
6. **Who implements, who reviews** (the owner, 2026-10-11 and 2026-10-12, superseding every
   earlier model-choice rule; kept as history in `docs/models.md`). What worked: the main session
   implements, or a Claude Code agent it spawns does, and a separate OpenCode process of another
   family reviews. The roster is the owner's, and changes often: the defaults and the blocked list
   live in `harness.json` and change through `/switch-model`, never by a rule that names a model.
   No quota, tier or difficulty table picks a model.
   0. **For Claude, the orchestrator is set by the Anthropic environment variables alone** (`ANTHROPIC_BASE_URL`,
      `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL`): Claude by default; when Claude's tokens are out, another
      Anthropic-compatible provider such as Z.AI, MiniMax or Moonshot, which then works like Claude.
      The harness never names the orchestrator's model. It reads the orchestrator's **family**
      from that environment (`lib/common.mjs` `sessionFamily`: Claude when the base URL is unset
      or Anthropic's, GLM for Z.AI, MiniMax, Kimi for Moonshot; `HARNESS_SESSION_FAMILY` overrides, and an unknown endpoint
      refuses to review until it is set), because every subagent the session spawns, whatever
      its model, runs through the same endpoint and is of that provider's family.
   1. **Before each implementation, ask the user ONE question** with the question tool: which
      **subagent** implements, or does the main session implement directly? The implementer is
      a subagent spawned inside Claude Code with the Agent tool
      (`subagent_type: "implementer"`, `.claude/agents/implementer.md`, worktree isolation), an
      OpenCode model invoked as `opencode run --agent implementer --model <id>`, or the main
      session directly in its own worktree (never the main checkout). The model is whatever
      the user names: a Claude Code alias (`sonnet`, `opus`, `haiku`, `fable`), any model id
      the session's provider serves, or any OpenCode id the user has. Under another
      Anthropic-compatible provider (Z.AI's GLM, MiniMax, Kimi) the same alias resolves to
      whatever that provider maps it to, or the id names its model outright. Propose
      `harness.json`'s `implementer.default` first as a starting point, but any model the user
      names is acceptable. No model-choice rule binds: same-model implementations, same-family
      reviews, a model previously on the harness `blocked` list, and "Alibaba only when the
      user asks" are all lifted by the owner on 2026-10-13 (rule 6.3). The earlier
      `implement.mjs` (a wrapper around that same OpenCode invocation) was
      retired on 2026-10-11 because runs died on rejected paths and early ends; the
      historical note lives in `docs/models.md`, not in this rule. Whoever implements keeps `RUN-NOTES.md` in their worktree (the plan, a progress line
      per commit, an END block), pushes after every commit, and opens the PR. When a subagent
      ends, the main session reads its final report before acting (rule 25), and posts its notes
      on the issue.
   2. **Before each review, ask the user ONE question:** which reviewer (and, if they care, by which tool / harness) reviews this PR? The user picks a model — there is no family, blocked, or provider-route filter (owner 2026-10-13). The harness proposes `harness.json`'s `reviewer.default` first as a starting point, but any reviewer the user names is acceptable; the main session records the answer on the PR. The harness's own tool path is `tools/harness/review.mjs --pr <n> --brief <file> --issue <n> --apply-label [--reviewer <name>]`, run as a watched systemd unit (`run-unit.sh` + `watch.sh`); a reviewer that does not have OpenCode installed may review inline or via any other tool that reads the diff and posts a comment, with the same relayed-in-full expectation (rule 8). The script and OpenCode-side tooling do not always follow the brief: a flagged review (exit 4) is read by the main session, not paid for again. One review per PR unless the user asks for more.
   3. **The fixed rules (the owner, 2026-10-13):** no model-choice restriction on
      implementer or reviewer. The reviewer may be of the same family as the
      implementer; a model previously on the harness `blocked` list may run;
      Alibaba runs without an extra question. The owner still names the
      implementer and the reviewer at the rule 6.1 / 6.2 questions — the
      questions stay, the choice is unrestricted. Data-flow guards still bind:
      rule 18's originals bar; private code never to providers that train on
      prompts.
   4. **Permissions, not briefs** (the owner, 2026-10-11): an agent gets the permissions its work
      needs, in its agent file (`.opencode/agents/reviewer.md`: all of `/tmp`, the static folder
      read-only; `.claude/agents/*.md`: the guard hook refuses only a force-push, `git stash`,
      `git worktree`, a merge and, for the reviewer, every write). A run that dies on a rejected
      path is fixed by widening the grant, never by re-briefing (rule 13).
   5. A failed run is diagnosed and fixed, not silently re-routed: another model only when the
      provider does not answer, and the user names it. The PR records who implemented and which
      model reviewed.
   6. **Watching a review, a sitting or any other background job** (L48): start it as its own
      systemd unit, `tools/harness/run-unit.sh <name> <log> -- <command>` (unit `iwa-<name>`,
      memory cap, stdin from /dev/null), never with an inherited pipe (`opencode run` waits for
      stdin's end-of-file). Watch it with one monitor every 1–2 minutes,
      `tools/harness/watch.sh --label <name> --unit iwa-<name> --file <log>` (`--opencode-log <log>`
      for an OpenCode run, `--frames <sitting dir>` for a sitting: "game stuck" after 5 minutes
      without change means notify the user, look at the frame, and stop the sitting or file the
      fix), never `pgrep -f` in a loop (it matches the watching shell itself; 2026-10-11, 1.5 hours
      lost). As soon as the log shows `session ses_… started`, give the user the session id and
      `tools/harness/peek.sh ses_… [-n 20]`, and say in plain language what the agent is doing,
      never raw log lines or byte counts. "Possibly stuck" after 10 minutes without change: check
      the process and read its newest messages; a long build or test is not stuck. Dead, or
      silent for 20 minutes: stuck; kill it only if it is ours. For a Claude agent, the progress
      signal is its transcript file's size plus its worktree.
   7. **Still in force:** the effort rule (a heavy model, Opus, GPT-6.1 Sol, GLM-5.3, MiMo v2.6
      Pro or MiniMax-M3, runs at `medium` at most and at `low` when medium is not needed; a model
      with no medium takes its lowest variant at or below `high`; a light model stays at `high`);
      Sonnet's tripwire (`docs/models.md`) in every Sonnet brief; reach (L26: an OpenCode reviewer
      cannot reach the user's install or a cloud session, so the main session runs those lines
      and posts their output on the PR); a cloud brief starts by checking the hostname and that
      `/mnt/c` is absent, and stops if either check fails; every model id comes from a live
      source when one is reachable — `opencode models <provider>` where OpenCode is installed,
      the provider's own model list otherwise — never memory.

   The roster, how a run is made and what each model has shown are in `docs/models.md`; the main
   session keeps it current.
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
   copy inside your worktree (`<file>.saved`, deleted afterwards) or in a `mktemp -d` folder under
   `/tmp`. (The owner, 2026-10-11:
   in another project, a `git checkout <file>` used to undo a mutation wiped a whole rework round's
   uncommitted edits; here fix-87's implementer lost its uncommitted file the same way.)
10. A comment asserting behaviour at an edge arrives with the test that visits that edge.
11. Until the first playable build, schedule only bugs that break play; label the rest
    `post-playable`.
12. A bug whose fix stays in the files it names and changes no outcome is a `fix`; a blocking
    one-file mechanical fix may ride the PR that found it, declared under Scope.
13. Design decisions go to the user; nothing else waits for the user.
    - **Work autonomously** (the owner, 2026-10-05): chain write, run, review, merge and the next
      task. Ask only for design decisions, escalations, rule 6's two questions, and when every
      quota is out.
    - **Merge without asking** on an approving cross-family review and green CI (rule 7). Research
      PRs (those that add run records) merge with `gh pr merge --merge`, never squash, so their
      measurement commits survive; other PRs squash.
    - **Wine sittings run without a go-ahead** (the owner, 2026-10-08) once the driver is reviewed
      to stay on its own Xvfb display, off the desktop (`:0`). Report stuck points from the screenshots.
    - **Fix the cause, not the brief** (the owner, 2026-10-11, not happy): after the FIRST permission
      or setup failure of a delegated run, stop and fix the cause in the most practical way
      (relax a guard that protects nothing important, fix the runner or the setup), or propose the
      fix at once. Never re-brief and retry the same thing; a failure class that comes back is
      never retried a third time with a reworded brief. (M3's review of PR 166 was refused three
      times for writing in `/tmp`; the fix was opening `/tmp` to the reviewer, d30a137.)
    - **Memory cap**: every delegated run, and every test run on unreviewed code, goes under
      `systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 --` (`run-unit.sh` sets it).
      A looping test grew to ~13 GB and crashed WSL three times on 2026-10-09.
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
    may be read by the reviewing models' APIs (Anthropic, OpenAI, Z.ai, Alibaba since the
    owner chose Qwen for T21 on 2026-10-06, and MiniMax since 2026-10-12: it was missing only
    because the owner did not use MiniMax when the list was written), and is never published (the
    owner, 2026-10-05, T29).
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
      (Anthropic, OpenAI, Z.ai, Alibaba, and MiniMax since the owner's decision of 2026-10-12), to
      inspect a sitting or review its records. They hold no
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

    **The runtime** (the owner, 2026-10-10): Wine 10.0 is accepted on IT13 (Ubuntu 26.04 has no
    9.0); its fingerprints were re-pinned in #159. On another machine a different Wine version is
    re-pinned the same way before a sitting's records are trusted. Sittings run on their own Xvfb
    with xfwm4 and xdotool (WSLg's `:0` hangs on IT13). The sitting environment is
    `setup/iwp/iwp-env.example.sh`.
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
21. **Model trials** (the owner's decision, 2026-10-02; narrowed 2026-10-11). The record shows the
    user which reviewer models are viable. After a review run that taught something (a model missed
    a bypass, found a class of defects, failed on infrastructure), the main session adds one comment
    to the model-trials issue (reviewers post only on their own PR): the model, the task, the exit
    code, the duration, the round, and what the review caught or missed. A routine approve needs no
    comment. A model that fails is diagnosed and fixed before any fallback: its log, the brief, the
    agent file, the harness and the login. The diagnosis goes in the same comment.
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
    - OpenCode reviews (`review.mjs`): exit 3 looks the same for a model that never answered, one
      that stopped on a rejected path and one that wrote a review the script could not read, and the
      log's tail shows only the last tool output. Read the model's final message from the session
      record, read-only, with the session id from the run log's `session ses_…` line (never read
      `auth.json` in that directory):

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
      rest is not (easy). Each part gets its own reviewer (rule 6), so an easy part is not held to
      a hard review, and a hard part is not reviewed as easy. (T39's catalogue and the check's hash verification,
      #140, 2026-10-09.)
    - **Different hands:** one part reads the user's install (the main session, L26), and another
      is repository-only work a Claude agent can do unattended.
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
