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
1. The main session plans, runs `/run-task`, triages and talks to the user. It delegates (`/delegate`):
   code to OpenCode, review to another model (rule 6), repeated decisions to Jev after a trial, and
   images and audio to OpenRouter or ElevenLabs models, whose ids come from live lists, never memory.
2. Nobody works in the main checkout but the main session: OpenCode runs in the worktree the script
   makes, Claude agents run with worktree isolation. Never `git stash`.
3. Status lives in GitHub labels. No document carries a status snapshot.
4. A question is not a request to edit files. Answer it; propose any fix and wait.
5. The Done-when is not negotiable by the implementer. It stops and reports; it never weakens an
   assertion, skips a test or edits its task file. The main session amends a Done-when on `main`
   with the reason in the commit message.
6. Each task file names its implementer and its reviewer, at the effort below, and says
   whether the task is `easy` or `hard`, and why. The pairs (the owner's decision, 2026-10-03):

   | Difficulty | Implementer | Its fallback | Reviewer | Its fallback |
   | --- | --- | --- | --- | --- |
   | Easy, the default | GLM-5.3 Flash (Z.AI Coding Plan only) | Sonnet | GPT-5.6 Luna (direct OpenAI) | Sonnet |
   | Hard | MiMo v2.6 Flash (Go) | Sonnet | GPT-6.1 Sol (direct OpenAI) | Opus |

   - **Hard** is any of:
     - a guard, a gate, or a tool whose failure would let an original or a copy through (in T06
       Sol found two bypasses that the implementer's own mutation tests missed, #9);
     - a new mechanism across several files, or a new external dependency;
     - a task whose earlier round found blocking bypasses.

     Everything else is easy.
   - **Family:** the reviewer comes from another family than the implementer. When a constraint
     forces the same family, the task file names it: OpenCode cannot reach the user's install or a
     cloud session (L26).
   - **Research, or anything on the user's install:** Sonnet implements, because OpenCode cannot
     reach the install (L26). The reviewer follows the difficulty and reviews the repository side.
     The main session runs the lines that read the install, and posts their output on the PR. If
     no OpenCode reviewer is available, the Claude fallback would be the implementer's family:
     escalate.
   - **Other probed models** (`harness.json`, for an explicit `--model` or a switch): MiMo v2.6
     Pro (Go), GLM-5.3 and GPT-6 Sol, and on the Alibaba Token Plan (2026-10-05; its key is an
     environment variable, `docs/models.md`) Qwen 3.8 Max and Flash, and GLM-5.3; Opus and Fable
     implement only when a task file says why.
   - **MiMo replaces DeepSeek** (the owner, 2026-10-09). OpenCode Go's heavy model is
     `opencode-go/mimo-v2.6-pro`, its light one `opencode-go/mimo-v2.6-flash`; MiMo is a family of
     its own for the family rule. DeepSeek (V4 Pro, V4.1 Flash, on any route, Alibaba included) is
     blacklisted: never used, and removed from `harness.json`.
   - **GPT-6.1 Sol, sparingly** (the owner, 2026-10-03): only for hard reviews, at effort `low`;
     `medium` only when the task file says why; never `high`.
   - **Effort** (the owner, 2026-10-05): a heavy model (Opus, GPT-6.1 Sol, GLM-5.3, MiMo v2.6 Pro)
     runs at `medium` at most, and at `low` when medium is not needed. A model that offers no
     medium takes its lowest variant at or below `high`: GLM-5.3 `low`. MiMo offers no variant on
     Go, so it runs without one. Opus runs as `task-agent-heavy` (effort `medium`). A light model
     (Sonnet, GPT-5.6 Luna, GLM-5.3 Flash) stays at `high`.
   - **Luna** (harness_imperial L51): the light OpenAI model, and the reviewer `luna`, is GPT-5.6
     Luna on the direct OpenAI route (`openai/gpt-5.6-luna`, effort `high`). As of 2026-10-09, Luna
     shares OpenAI's main quota with Sol — the `gpt-5.6-luna:7d` window of its own is gone; its own
     limit surfaces only as `when_exhausted.usable_models` in `/quota/openai` (harness's L65).
     GPT-6 Luna draws on OpenAI's main pool with Sol: it stays registered as `luna-6`, outside
     every chain, never the reviewer. Never a Luna on OpenCode Go (`opencode-go/…`).
   - **Quota first** (harness_imperial L50; the owner, 2026-10-05, superseding every earlier limit
     on which models may be used): before choosing, recommending or delegating to a model, check
     its provider with quota-tracker (`docs/environment.md`). A provider that is `exhausted` is not
     used until it is usable again: take the next model of the pair or chain whose provider has
     quota, pass it explicitly (`--model`, `--reviewer`, the Agent's model, `opencode -m`), and say
     so in the run's report or the PR body ("GLM skipped: zai exhausted until 21:40; reviewed by
     Luna"). Without the service, count a usage-limit error as `exhausted`. Ids still come from the
     live list (`opencode models <provider>`), never memory.
   - **Sonnet's tripwire** (the owner, 2026-10-04). Every Sonnet brief carries the paragraph in
     `docs/models.md`. Sonnet stops and hands back an `ESCALATE` block when:
     - two hypotheses for the same question have failed;
     - it would rely on bytes, code or behaviour it cannot explain;
     - it is about to write a claim it cannot back;
     - it has made three attempts at one step without progress.

     The main session then brings in Opus, to answer the question (consult) or to take the task
     (takeover), on the pushed branch.
   - **Escalation after a heavy review** (the owner, 2026-10-03). The implementer moves up one step
     for the next round when either holds:
     - a review asks for rework with three or more blocking findings;
     - a rework round brings new blocking findings of the class the last round raised.

     The steps are GLM-5.3 Flash → MiMo v2.6 Flash → Opus, and Sonnet → Opus. The round count
     does not reset (rule 7). The new implementer gets the task file, every review so far, and the
     previous implementer's unpushed work as a patch to weigh, never to apply blindly.
   - **Cloud sessions:** Sonnet implements, and Opus reviews. Only Claude runs there, so the same
     family is forced. On 2026-10-03, `isolation: "remote"` silently ran T05's agents locally. A
     cloud brief therefore starts by checking the hostname and that `/mnt/c` is absent, and stops
     if either check fails.
   - **Excluded:** never Haiku. Gemini (cost), Kimi and Grok are not used.
   - **Switching** (the owner's decision, 2026-10-02): the owner decides which models are in use,
     and switches them often, as credits and prices change. The main session does not choose
     models by budget; it checks only whether a provider has quota (Quota first, above). It keeps
     every switch cheap:
     - every candidate stays probed, with a `harness.json` entry;
     - each task file names its implementer and reviewer, one line each;
     - when the owner calls a switch, it is applied to tasks not yet started (and to
       `harness.json`'s defaults when asked), with the owner's reason in the commit message.

   The families and switching were the owner's decisions on 2026-10-02; the difficulty pairs on
   2026-10-03. They override the family rule in the harness copies
   (`docs/process.md`, `TEMPLATE.md`, the `run-task` and `delegate` skills), which `harness.lock`
   pins. `review.mjs` refuses an OpenCode reviewer of the implementer's family.

   The working strategy, how runs are made, the adjustments and what each model has shown are in
   `docs/models.md`, kept identical to malpaco's copy; the main session keeps it current.
7. Merge only with an approving review and green CI. Two rework rounds, then escalate.
   Exception (the owner, 2026-10-05): when the remaining findings are small and change no result
   (wording, a narrowed claim, a missing test or correction note), the main session grants a third,
   narrow round for those findings only, without escalating. A finding that could change a result,
   or let a protected rule be bypassed, still escalates.
8. Relay review findings in full, never a subset.
9. A test proves behaviour only if it fails when the behaviour is removed; a claim that nothing
   failed is re-taken before it is believed.
10. A comment asserting behaviour at an edge arrives with the test that visits that edge.
11. Until the first playable build, schedule only bugs that break play; label the rest
    `post-playable`.
12. A bug whose fix stays in the files it names and changes no outcome is a `fix`; a blocking
    one-file mechanical fix may ride the PR that found it, declared under Scope.
13. Design decisions go to the user; nothing else waits for the user.
14. At session start: `gh issue list --label triage:needed --state open`, and any task in flight.

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
    - **E. Corroboration, not replacement.** The model-driven run does not replace the owner's
      Bandicam captures. T28's owner-plays model stays. Model-driven runs are corroboration and
      per-action timing; owner's recordings are the play-length, game-sense, and mistake-rich
      record. The playbook (`walkthroughs/video-walkthrough.md`) is updated to say so.
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
21. **Model trials** (the owner's decision, 2026-10-02). Rule 6's list exists to find out which
    models are viable. After every implement or review run, the main session adds one comment to
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
