# isle-wars-archaeology

An evidence-backed behavioural specification of *Isle Wars* (DOS, 1994) and *Isle Wars Pro* (Win9x),
both by Soleau Software, built by controlled experiments on the original games, using the method of
[game-archaeologist](https://github.com/diegoami/game-archaeologist). The process is
`docs/process.md`; read it before running a task. Tasks are `docs/tasks/T<nn>.md`, indexed in
`docs/tasks/README.md`.

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
6. Each task file names its implementer and its reviewer, two different models, at effort `high`
   at most. The family need not differ, so Opus may review Sonnet. The reviewer re-runs every
   Done-when line itself. The models allowed:
   - Claude Sonnet, Opus and Fable, as the `task-agent` type, which caps them at `high`;
   - OpenAI models, on the direct route;
   - GLM and DeepSeek models, on OpenCode Go.

   An OpenCode model is probed (`switch-model.mjs --probe --dry-run`) before its first task. A task
   that reads the user's install, or runs in a cloud session, goes to Claude: OpenCode keeps every
   model in its worktree (L26). Gemini (billed per token on OpenRouter) is out on cost. Kimi and
   Grok are not on the owner's list. This was the owner's decision on
   2026-10-02. It overrides the family rule in the harness copies (`docs/process.md`,
   `TEMPLATE.md`, the `run-task` and `delegate` skills), which `harness.lock` pins. `review.mjs`
   still refuses an OpenCode reviewer of the implementer's family.
7. Merge only with an approving review and green CI. Two rework rounds, then escalate.
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
    replicated). Executables, data and help files, and patched builds stay on the user's own
    machines. They are never in this repository, a release, an issue or a cloud session. Tasks that
    need them are C3/C4 only. `tools/check_no_originals.py` runs in CI.
19. **Two artifacts, every claim scoped** (U3, U11). DOS *Isle Wars* and Win9x *Isle Wars Pro*, the
    shareware/unregistered releases. A claim holds for both only when it is shown for each. What
    registration unlocks is `unknown`.
20. **Research follows game-archaeologist ADR-007/008.** Run records are raw and immutable
    (`formats/run-1.schema.json` at the commit `archaeology.json` pins), evidence bundles are release
    assets, and findings start `proposed`. Only the main session writes `spec/`, after review. Unknown
    stays `unknown`. This repository is private (U5).
21. **Model trials** (the owner's decision, 2026-10-02). Rule 6's list exists to find out which
    models are viable. After every implement or review run, add one comment to the model-trials
    issue:
    - the model, its role and the task;
    - the exit code, the duration and the review round;
    - what the review caught or missed.

    A model that fails is diagnosed and fixed before any fallback: its log, the brief, the agent
    file, the harness and the login. It is then retried. The diagnosis goes in the same comment.
