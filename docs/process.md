# Process

`CLAUDE.md` holds the rules, this file how they run, `/run-task` the procedure; each rule cites its lesson.

## 0. Order of work

1. **Evidence first** (for a rebuild): decode, decompile, and write the design with every claim
   tagged `[confirmed]`, `[derived]` or `[designed]`.
2. **A walking skeleton before the fan-out**: scaffolding, the seams the rules plug into, one rule
   end to end, a CLI, and a thin screen a person can use. (L1)
3. **The fan-out**: rules behind the seams, best-evidenced first.
4. **The first playable build**: once the skeleton exists, the UI chain goes before more rules.
   Until it ships, only a bug that breaks play is scheduled (crash, stall, unwinnable game, save
   that will not load, order that can never succeed). (L1)

Tag capability jumps, not phases. Release notes come from GitHub when the tag is cut.

## 1. Roles

| Role | Who | Does |
| --- | --- | --- |
| Main session | Claude or Codex, the session the user talks to | Plans, writes task files, runs `/run-task`, triages, merges, reports |
| Implementer | The **`implementer` subagent** spawned inside Claude Code (worktree isolation) on any model the user names at the rule 6.1 question (a Claude Code alias like `sonnet`, an OpenCode id, or whatever the session's provider serves), an **OpenCode model** invoked as `opencode run --agent implementer --model <id>`, or **the main session** directly in its own worktree when the provider cannot spawn one — no model-choice rule applies (the owner lifts the family / blocked / Alibaba gates on 2026-10-13); asked before each implementation (CLAUDE.md rule 6). *History: an earlier `implement.mjs` wrapper around that OpenCode path was retired 2026-10-11 (runs died on rejected paths); `opencode run` directly is the current path, named in CLAUDE.md rule 6.1. Superseded chains: GLM/MiMo/Sonnet chains (L42).* | One task, one branch, one PR, in its own worktree |
| Reviewer | **One review run** of a different model than the implementer's (the family / blocked gates are gone, owner 2026-10-13), on the model the user names at the question before the review. `harness.json`'s `reviewer.default` is the proposal when the user does not pick; **any reviewer tool** the user has may stand in. The harness-provided default is one OpenCode run via `tools/harness/review.mjs [--reviewer <name>]`; agents without OpenCode can review inline or via any tool that reads the diff and posts a comment. Exit 3: read the final message, fix the cause, run again; exit 4: the main session reads the flagged review and decides (L28). *Superseded: the reviewer chains, the Claude fallback, the user asked at every review.* | Re-runs the Done-when, audits scope and evidence, posts one PR comment, applies the label |
| Decider | Jev via `tools/harness/jev.mjs` (the `/jev` skill) | Repeated yes/no decisions over many items, at the confident ends only (§12) |
| Generator | Models on OpenRouter (images, other families) and ElevenLabs (speech, sound, music) | Assets, each committed with a sidecar naming provider, model, prompt, date and cost |

Before each implementation and each review the main session asks the user one question, with
`harness.json`'s default proposed first (CLAUDE.md rule 6); no quota, tier or chain picks a model, and the
roster changes through `/switch-model`. The implementer's family is the session's: native Codex markers or
`HARNESS_CLIENT=codex` identify OpenAI; Claude retains Anthropic endpoint detection.
`HARNESS_SESSION_FAMILY` overrides that detection. Carry `HARNESS_CLIENT` into detached
jobs. Reviewer selection follows CLAUDE.md rule 6. Model ids come from `harness.json`,
`models.mjs` or `node tools/harness/opencode.mjs models`, never memory (L25).
See CLAUDE.md's Codex compatibility section for tool mapping and backup selection.


## 2. Task files

`docs/tasks/T<nn>.md`, 150–400 words, from `docs/tasks/TEMPLATE.md`: Kind, Evidence, Owns,
Scope, Done when, Hazards, Implementer, Reviewer, Merge after. Rules:
- **Owns** names directories or files. Go finer only when two tasks run at once in one file: function-level Owns made one project open 27 PRs that only widened a list. (L5)
- **Done when**: each line is one check a command can run. The main session runs each line before dispatch: it fails on `main` and passes on a mock fix. (L45) For a guard (a gate, check or tool whose failure lets a protected rule be bypassed), each constraint it enforces is its own numbered line, and the main session pushes the guard's tests to the task branch before dispatch, one mutation test per bypass class the design predicts, failing until the guard lands. (L64)
- **Milestones**: a task likely to outlast one implementer run (about an hour), or whose Done-when is
  all or nothing (an exact match, a whole model), is split into tasks that each merge on their own:
  the static reading, any tool that produces ground truth, then the deliverable piece by piece. A
  milestone's Done-when measures progress as a number (records matched, first divergent minute),
  committed with each push, so a resumed run starts from it; the boundary sits where the evidence
  already has a number, not at an arbitrary half of the scope. (L58)
- The main session edits task files directly on `main`, the reason in the commit; the reviewer sees it. (L6)

## 3. The loop

`ready → implement → review → approved + green CI → squash merge → follow-up → unblock → report`.
Rework sends the full review back to the same branch, at most two rounds (one for a fix), then
escalates. The implementer script resumes a pushed branch; it never starts over. Before a merge the
main session re-runs the check the approval rests on most; a different result is rework. (L46)

What the review script guarantees, and why:
- OpenCode starts with stdin closed; without it a run hangs before it starts. (L10)
- No session in 180 s, no progress in 600 s, or no exit in 1 h kills the run's process tree. (L10)
- The agent is checked on OpenCode's session record (L11); a rejected tool call fails the run (L26),
  and the fix is a wider grant in the agent file, not a re-brief (CLAUDE.md rule 6.4).
- The model runs at the effort its `harness.json` entry names (a heavy model at medium or low, a
  light one at high), in the scripts' own data directory (L27, L29). One model, one run; no chain.
- Exit 0: posted and labelled. 3: no review, nothing posted: read the final message (rule 25), fix
  the cause, run again. 4: posted under a note, no label: the main session reads it and decides.

## 4. The implementer brief

The brief is the task file pasted in full, then this block, then on a rework round the review's URL.
The `implementer` agent file repeats the run mechanics; this block is the contract, for the main
session implementing directly as much as for the subagent. A line that needs the user's install or a
cloud session is the main session's (L26).

```text
You implement <T<nn>>. The task file above is the contract.
- Build only what the task asks for, even inside a file it requires; say why for each changed file. (L44)
- A Done-when you cannot meet: stop and report. Never weaken an assertion, skip a test or edit the task file.
- Every new test fails before your change and passes after it; say how you checked.
- Undo a mutation or scratch edit by writing back the file's saved contents (read it first,
  restore it in a `finally`), or commit first; never `git checkout`, `git restore` or `git reset`
  a file with uncommitted work: they return the last commit and destroy the rest. Keep the saved
  copy inside your worktree (`<file>.saved`, deleted afterwards) or in a `mktemp -d` folder under
  `/tmp`, never as a loose file elsewhere.
- If you measure: every output a finding or the PR may cite goes under a tracked path the task owns,
  pushed per batch and every 30 min, never deleted or overwritten; originals out, hashes recorded. (L40)
- A comment that asserts behaviour at an edge comes with the test that visits that edge.
- A defect you find outside the task: report it. A one-file mechanical fix that blocks you may
  ride this PR, declared under Scope in the PR body.
- Update any document your change makes wrong, in this PR. Never write status into a document.
- PR body: Closes #<issue>; Scope (files and why); a fenced block with each Done-when command and
  the tail of its output; Docs changed.
```

## 5. The reviewer brief

```text
<T<nn>> review (<model>)
You review PR #<n> at <sha>. You did not write it. The task file follows.
0. Prove the tree: HEAD is <sha> and the diff against origin/main is the PR's; findings name its files.
1. Re-run every Done-when line yourself, and account for each (L32). The PR's evidence is no proof.
2. [evidence-driven] Every constant traces to a fixture, report or investigation; a [designed] one says what was searched.
3. [seeded] No wall clock, unseeded random or order-dependent iteration in rule code.
4. Every changed file and behaviour is one the task asks for (L44); docs it makes wrong are updated.
5. Sweep the diff: tests that pass with the behaviour deleted (mutate, rebuild clean, re-take any
   negative result), branches no input reaches, edge comments without a test, <project classes>.
   Undo a mutation or scratch edit by writing back the file's saved contents (read it first,
   restore it in a `finally`), or commit first; never `git checkout`, `git restore` or `git reset`
   a file with uncommitted work: they return the last commit and destroy the rest. Keep the saved
   copy inside your worktree (`<file>.saved`, deleted afterwards) or in a `mktemp -d` folder under
   `/tmp`, never as a loose file elsewhere.
6. <docs/review-brief.md in full: "Blocking means" for this task, then its one-pass section (L47, L49)>
Prove each finding (run it, or delete the behaviour and name the test that fails) or label it
unverified. Your final message is the review: the header; the verdict (approve | approve after
named fixes | rework | user decision); per Done-when line `DW<k>: ran <command> → <result>` or
`DW<k>: not run — <reason>`; the findings R1..Rn (file:line, blocking or not); the verdict again
last. Never post it: the script posts it and applies the label.
```

A further review, such as `/code-review <pr>` on an architecture task, runs only when the user asks
for it and names the model (CLAUDE.md rule 6.2: one review unless the user asks for more); then
always with the PR number, since a bare invocation from an agent reviews the wrong tree. (L8)

## 6. Bugs, fixes, triage

Bugs and non-blocking review findings are filed with `triage:needed`: one `T<nn> follow-up` issue
per merge. Triage decides one of:
- **fix**: no ruleset value, fixture value, seeded measurement or golden line changes outside the
  bug's own reproduction. The bug issue is the contract; its Done-when is its reproduction as a
  failing-then-passing test; one review round. (L4)
- **correction task**: anything that changes an outcome.
- **fold** into a task not yet ready, or **close**, with the reason.

Once `breaks-play` is trialled (§12), Jev settles the gate's confident ends; the main session the middle.

## 7. Escalate to the user when

A design question; a Done-when would have to weaken; a third rework round; anything destructive
(force-push, rewriting `main`, deleting an issue); a new external dependency.

## 8. Labels

`task`, `bug`, `fix`, `triage:needed`, `post-playable`,
`status:{ready,in-progress,in-review,rework,approved,blocked,escalated,merged}`,
`review-round:{1,2}`, and `model:<name>` on a PR whose implementer was not Claude (then `review.mjs`
reads the family to exclude from it).

## 9. Measure

After each merge, one PR comment records the implementer (the main session or an agent, with the
agent's token total from its completion notice), the review's model and duration, and the review
rounds. After 10–20 tasks, compare the rework rate with the baseline in `docs/lessons.md` before
changing the default reviewer. (L13)

## 10. Adding a rule

A rule enters `CLAUDE.md` or this file only with a lesson in `docs/lessons.md`: a failure in a real
run, or the owner's decision with its basis. Plausible rules without either stay out. (L14) A rule may carry a **carve-out**: an addendum that loosens it under named conditions, its wording unchanged, with lettered preconditions (A, B, …) a reviewer checks one by one, a gate in `tools/` that enforces them, and what stays forbidden; a project's `CLAUDE.md` holds the instance. (L63)

## 11. For a reverse-engineering project

- Transcribe every number from the research into one fixtures corpus with provenance, and assert
  against it: each re-read of a report is another chance to misread it. (L15)
- New evidence runs in two stages: findings to the research repository, then a check of every
  document claim it touches. Each finding is a doc fix, a bug, a task-file edit, or a question for the user; research never decides design. (L16)
- The original files never enter the repository. CI fetches them from a private fixtures
  repository holding the whole corpus; tests find fixtures by name; local tests skip without them. (L17) A *model-driven run* of the original is a carve-out of this (§10): a known-good hash table in a finding, a gate that refuses any run record off that table, then a `model-driven` task (`docs/tasks/TEMPLATE.md`); it corroborates the owner's runs, never replaces them, and what it shows amends `spec/` and `findings/` one claim at a time, never in bulk. (L63)
  Here: CLAUDE.md rule 18's carve-out (the owner, 2026-10-08; table F019, gate T36, platform `wine-on-user-machine-iwp-2.0`, evidence `class: recording`). Since 2026-10-09, constraint E counts model sittings on their own, beside the owner's videos.

## 12. Delegating decisions to Jev

Jev takes a decision only when it recurs over many items, its answers are known up front, and a
trial against labels has set its cutoffs, recorded in `harness.json` with the numbers. It answers
the confident ends and the main session the middle; a person's decision outranks both. Without its
key it is off. `/jev` has the procedure. (L24)
