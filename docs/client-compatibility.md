# Claude Code and Codex: local workflow audit

Observed 2026-10-19 against `cdde67142ffc15d7af7432f89b24aabcd16b9b70` on the owner’s SSH-connected host. The supported route for this task is a main Codex session in its own worktree, followed by an owner-selected native Claude Sonnet medium review. This is a bounded audit, with known gaps below; it does not certify every client/provider/cloud combination.

The [machine-readable matrix](prototypes/T61/matrix-r2.json) and [preflight evidence](prototypes/T61/preflight-r2.json) separate observations from limitations. “Works” applies to the described local path; “explicit equivalent” means the operator must take the stated action. These are observations at the baseline, not a live task-status dashboard.

## Compatibility matrix

Historical T61 snapshot at the pinned baseline above. The model-choice guidance and #270
workarounds in this table are superseded by [Owner-selected models after T62](#owner-selected-models-after-t62).
The recorded T61 observations and evidence remain unchanged.

| Area | Disposition | Claude Code | Codex | Operator action | Alternative/limitation | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| instructions | works | Shared CLAUDE.md is the project rules entry point. Native review additionally receives the full task contract. | AGENTS.md points to CLAUDE.md. Live readonly exec actually read both and returned the required rules. | Read CLAUDE.md and docs/process.md before acting; AGENTS.md stays a pointer. | — | — |
| skills | explicit-equivalent | Repository skills are in .claude/skills. Older model-choice prose has drifted. | No repository .agents/skills entries: use the explicitly documented manual reading of .claude/skills/<name>/SKILL.md; no automatic Claude slash commands. | Use available native tools and the shared process; read the named skill manually. Do not pretend its Claude-only tool syntax exists. Model-selection prose needs #270. | Read the existing Claude skill manually; automatic Codex skill discovery is not provided here. | [#270](https://github.com/diegoami/isle-wars-archaeology/issues/270) |
| agent-tools | explicit-equivalent | Claude Agent calls and profiles are available only in a Claude session that exposes them. | This main Codex session implements directly in its isolated worktree; no Claude Agent tool is assumed. | Honor the owner-selected implementer and reviewer. An available tool is not permission to spawn extra implementers. | Use the owner-selected main session directly when the other client’s agent tool is unavailable. | [#268](https://github.com/diegoami/isle-wars-archaeology/issues/268) |
| worktrees | works | Use an isolated implementer/reviewer worktree. Native Claude reviews retain their own tree. | The main session created task/T61-client-compatibility in .claude/worktrees/T61-client-compatibility. Live smoke confirms the own-worktree rule. | Create a dedicated branch/worktree; never stash or clean another session. A sandbox may need approval to create sibling worktrees. | — | — |
| permissions-hooks | explicit-equivalent | Agent profiles have hooks; the native CLI backend uses trusted generated settings and a hook for Read/Grep/Glob plus native Bash permissions. | Claude hooks and agent grants do not load into Codex. Its actual sandbox/approvals apply. A sandbox-denied systemctl check worked after explicit host escalation in T60. | Use the actual client permissions; never bypass them to imitate another client. Tests inherit the required memory cap. Native Bash safeguards are not an OS sandbox. | Use Codex’s own sandbox and approval flow; Claude hooks are not imported into it. | — |
| client-provider | works | HARNESS_CLIENT=claude preserves endpoint-based detection even with inherited Codex markers. | CODEX_THREAD_ID/CODEX_SESSION_ID or HARNESS_CLIENT=codex identify OpenAI. CODEX_HOME alone does not. | Set HARNESS_CLIENT to the actual orchestrator for detached jobs. Never falsify HARNESS_SESSION_FAMILY to evade an old filter. | — | — |
| headless-supervision | works | Installed CLI 2.1.292 exposes noninteractive output/effort/settings options. The native review below is the live Claude check, not this preflight. | Installed CLI 0.163.0 supports read-only exec, JSON events, ephemeral mode and output schemas; live read-only smoke completed. | Use run-unit.sh with closed stdin and 6G cap, one watch.sh monitor, and retained output. SSH on this host does not require desktop forwarding. | — | — |
| monitoring | broken | Native Claude can be observed using its stdout.jsonl file through peek.sh. This is exercised by the owner-selected review, not inferred from a version string. | OpenCode export for the previous live MiniMax session exits zero with malformed JSON; peek.sh fails although watch.sh SQLite progress remains usable. | Use watch.sh --opencode-log plus a targeted read-only SQLite final query under rule 25 for this known failure; never rerun a healthy model merely because peek failed. Do not use the export helper as a required gate until #261 is fixed. | Use watch.sh SQLite progress and the targeted read-only final query when OpenCode export is malformed. | [#261](https://github.com/diegoami/isle-wars-archaeology/issues/261) |
| discovery-auth | explicit-equivalent | CLI version/help works; auth status was checked separately in T60. Catalogue availability is not an authenticated review. Exact native identity is verified on every actual run. | codex login status reported ChatGPT login; the bounded exec call actually completed. No auth/config contents were read. | Discover exact model IDs live where supported; distinguish discovery from an actual successful call. Cloud startup incorrectly equates model listings with login (#271). | Only a successful authorized call establishes usability; a catalogue or version string does not. | [#271](https://github.com/diegoami/isle-wars-archaeology/issues/271) |
| implementation | works | The owner can select the main session or an available isolated implementer. Only the main session merges. | The owner selected this main Codex session; it created, committed and pushed this audit branch. | Write RUN-NOTES.md without overwriting inherited notes, commit/push each meaningful step, open a PR. A question alone does not authorize edits. | — | — |
| review | explicit-equivalent | Use the native backend with --reviewer claude-sonnet --variant medium for this owner selection. No default change. Live review outcome and receipt are attached to the PR after this snapshot. | Codex main plus native Claude is an allowed route in the current runner. T60 live MiniMax review also demonstrated the existing route from Codex. | Record the selection, pin the PR head in a full brief, run the chosen reviewer once, inspect the full final and denials. Identity/coverage/DW holds remain mandatory. No live Claude result is claimed by this pre-review snapshot. | Use the current Codex main plus native Claude route; this snapshot does not assert its later verdict. | [#268](https://github.com/diegoami/isle-wars-archaeology/issues/268) |
| publication-ci | works | Reviewers return findings; the trusted parent posts and labels. Approving review and green CI precede merge. | T60 Codex main opened PR #269, relayed the full M3 review and merged the exact approved head after CI and rerun. Current scripts share the poster. | Use gh from the parent only for authorized publication. The current audit has not tested every client as a publisher; shared poster tests and the T60 run establish the described route. | — | — |
| local-research | explicit-equivalent | Local original-game access is subject to rules 18–24 and permitted API routes. Native CLI does not itself make a session local or safe for originals. | The connected host has static and E019 capture directories. This audit probes existence only; it does not run the game or inspect originals. | Keep binaries/assets/saves/captures/derived code under their stated boundaries. Static first; local captures via the responsible main session. Do not transfer them to cloud or malpaco. | Only directory existence was checked; original-game access and Wine readiness need separate authorized checks. | — |
| cloud | untested | Session-start hook is web-only, not this SSH preflight; its metadata defects are #271. No live web runtime tested. | This is an SSH-connected local host, not evidence of a cloud environment. No cloud originals/runtime tested. | Perform clean cloud-only checks separately, without originals. Do not run the install-capable web hook as a local smoke test. | No clean cloud session was exercised; retain the local path and prohibit uploading originals there. | [#271](https://github.com/diegoami/isle-wars-archaeology/issues/271) |
| model-choice-policy | broken | Current runtime rejects a same-family reviewer even when explicitly owner-selected, contrary to rule 6.3. | Retained probes directly show OpenAI same-family rejection from Codex, Claude same-family rejection from Claude, and a synthetic blocked-list refusal. | Until #270 lands, use a genuinely allowed alternative selected by the owner or the permitted external reviewer/post-review route with honest identity metadata. Do not alter family markers or claim the runner supports unrestricted choices. | Use an honestly identified owner-selected alternative route; unrestricted native same-family dispatch needs the separate fix. | [#270](https://github.com/diegoami/isle-wars-archaeology/issues/270) |

## Owner-selected models after T62

T62 aligns current registration and dispatch with CLAUDE.md rule 6.3: an owner-selected
reviewer may share the implementer's family, and legacy `blocked` family/fragment metadata
never prevents selecting an implementer or reviewer. Editing that list remains supported,
including entries naming the default. Alibaba needs no additional selection question.
Model identity must still resolve; contradictory declarations and unknown raw identities
are refused. The actual client and endpoint remain provenance, including labels/`--exclude`.
Do not change them to obtain a choice. Native Claude still requires its exact direct-Anthropic
transport, model/session identity, clean permission outcomes and complete approval evidence.

The operator still enforces originals restrictions and privacy clearance: private code never
goes to providers that train on prompts. There is no automatic training-provider guard in the
harness. Selection acceptance does not establish that clearance or live model availability.
Defaults are unchanged. The audit matrix and retained T61 probes above describe their pinned
historical runtime; their #270 workaround is superseded for the T62 runtime.

## Running a task from either client

1. Read [CLAUDE.md](../CLAUDE.md) and [process.md](process.md). Honor the owner’s existing implementer/reviewer selection; ask only when that required selection is missing. Read a relevant `.claude/skills/<name>/SKILL.md` manually in Codex; do not invoke Claude-only slash commands or Agent syntax.
2. Start in your own branch/worktree. This audit uses `.claude/worktrees/T61-client-compatibility`. Preserve inherited notes and uncommitted work; never stash or remove other worktrees. Keep measurements under the task’s owned tracked path, originals excluded.
3. Use the actual client sandbox and approval system. Claude permissions/hooks are not inherited by Codex. A blocked host service/socket check needs the normal escalation flow, not a permission bypass. Do not run original-game observations as part of this preflight.
4. Set `HARNESS_CLIENT=codex` or `HARNESS_CLIENT=claude` to the real orchestrator for detached jobs. `HARNESS_SESSION_FAMILY` is an honest exceptional override for unresolved endpoint identity. For Claude, the endpoint determines the family; inherited Codex markers alone must not be allowed to misidentify it.
5. Run meaningful task checks. The main session commits/pushes, opens the PR, pastes the full task contract and process review requirements into the review brief, and pins the exact PR head after pushing.
6. Start one memory-capped review unit with closed stdin and one monitor. This owner selected native Claude Sonnet medium, so invoke:

```bash
HARNESS_CLIENT=codex tools/harness/run-unit.sh review-PR /tmp/iwa-review-PR.log -- \
  node tools/harness/review.mjs --pr PR --brief /tmp/review-brief.md \
  --reviewer claude-sonnet --variant medium --issue ISSUE --apply-label
```

The variant override copies the model entry for this invocation; it does not change `harness.json`. See [native Claude operations](harness-claude.md) for direct-provider, identity, settings, scope and evidence gates. For a Claude orchestrator, set `HARNESS_CLIENT=claude`; same-family native review is permitted with the same transport checks.

7. For native Claude, watch the run log and the printed `stdout.jsonl` path; `tools/harness/peek.sh <stdout.jsonl> -n 20` reads it without a provider database. For OpenCode, use `watch.sh --opencode-log <run-log>` for SQLite progress. The previous T60 session’s export is malformed despite exit zero ([structural diagnostic](prototypes/T61/export-diagnostic-r1.json)); use only the named session’s read-only final query from CLAUDE.md rule 25 when necessary. A failed progress display is not a reason to pay for another review.
8. Read the complete final and all findings, including a failed run’s final, before acting. No approval from identity mismatches, denied tools, incomplete scope or missing Done-when checks. The parent alone publishes. Merge only after approval and green CI, with a final rerun of the principal check. Retain evidence and worktrees.

## Reproducing the bounded checks

```bash
python3 docs/prototypes/T61/preflight.py --output /tmp/iwa-T61-preflight.json
python3 docs/prototypes/T61/check_report.py
python3 docs/prototypes/T61/check_report.py --self-test
node --test tests/harness_clients.test.mjs tools/harness/test/claude.test.mjs
node tools/harness/review.mjs --self-test
```

The preflight writes only the requested temporary report; it makes no model request, installation, hook execution or publication. Run it within the project’s memory-capped supervisor. A zero exit means the listed probes completed, not that every workflow is compatible. It records existing policy restrictions instead of masking them.

The [live Codex smoke](prototypes/T61/codex-smoke-r1.json) used the checked-in [prompt](prototypes/T61/codex-smoke-prompt.txt) and [schema](prototypes/T61/codex-smoke-schema.json): `codex exec --ignore-user-config --sandbox read-only --ephemeral --json --output-schema <schema> -o <temporary-final> <prompt>` within the supervised audit worktree. It executed only `cat AGENTS.md` and `cat CLAUDE.md`, exited each command successfully, and completed the turn. It followed the pointer; this does not prove every implicit instruction-loading variation. The model default was not pinned or identity-verified; this was a CLI smoke, not an implementation or independent review. No config/auth contents or raw model trace is published; selected safe events and a raw-log hash are retained.

The live Claude check for this task is the owner-selected Sonnet medium PR review, whose receipt and full final will be linked from the issue/PR. This pre-review snapshot does not claim that call has succeeded. A fake-CLI test, a version string, or catalogue availability cannot establish a live review. Normal interactive Claude onboarding and cloud sessions are not exercised here.

## Boundaries and follow-up work

- [#270](https://github.com/diegoami/isle-wars-archaeology/issues/270): T62 aligns runtime model choice with rule 6.3. The retained T61 preflight reproduces the historical filters; broad operational skill/template cleanup is tracked in [#283](https://github.com/diegoami/isle-wars-archaeology/issues/283). No identity override is needed for a same-family choice.
- [#261](https://github.com/diegoami/isle-wars-archaeology/issues/261): validate complete session export and monitoring during the OpenCode migration. The retained diagnostic establishes malformed output, not its underlying cause.
- [#271](https://github.com/diegoami/isle-wars-archaeology/issues/271): truthful, client-aware cloud startup metadata. The hook currently labels model catalogue entries as logged in; it is web-only and can install tools. It was inspected but never run as this local preflight.

This SSH connection executes on the owner’s host. Its accessible research directories do not establish cloud availability or authorize copying originals. No game launch, original manual/capture reading, Wine prefix validation or decompiled-source transfer was part of this audit. The manual task still needs its own bounded static/visual evidence work. Game rules, assets, model defaults and global settings are unchanged.

## Official documentation and local limits

The official [instruction guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md) documents project `AGENTS.md` discovery; [noninteractive mode](https://learn.chatgpt.com/docs/non-interactive-mode) documents explicit sandbox selection and JSON events; [skill discovery](https://learn.chatgpt.com/docs/build-skills) documents `.agents/skills`. Local CLI help, source and actual probes determine the claims above. In particular, this repository uses an explicit pointer/manual skill-reading convention; it does not assume that Claude profiles or hooks become Codex controls.

## Evidence revision and checker limits

R2 follows the [full first Sonnet review](prototypes/T61/claude-review-r1/final.md). The new preflight records the runtime baseline, collection HEAD, source-script SHA-256, unchanged-runtime comparison and direct same-family samples for both clients. The audit baseline identifies the runtime being assessed; the collection HEAD identifies the audit branch, and the script hash identifies its exact uncommitted probe bytes. Original R1 measurements remain unchanged as historical evidence, including their host metadata. New R2 records omit the host name.

The checker verifies role-appropriate outcome artifacts, issue-number syntax, known probe/disposition relationships, source and artifact hashes, and an exact comparison of every table column with the matrix. Its designed eight-word floor rejects trivial placeholders; it cannot establish that longer prose is true. Independent source review still establishes meaning. The reproducible `--self-test` exercises the original four omission controls and the R1–R3 counterexamples without changing tracked files. Explicit exceptions remain effective with Python optimization; `python3 -O .../check_report.py --self-test` runs the same controls. The original four-control file is now hashed in the R2 manifest and is not used as self-authenticating proof.
