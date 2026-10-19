# Claude CLI reviews

T60 (#267) ports the committed Malpaco Claude adapter and #264 dependency preparation. Claude is selectable through
the same review entry point as OpenCode. The existing Luna default remains unchanged.

```bash
mkdir -p .cache/harness-tmp
TMPDIR="$PWD/.cache/harness-tmp" HARNESS_SESSION_FAMILY=openai tools/harness/run-unit.sh review-PR /tmp/review-PR.log -- \
  node tools/harness/review.mjs --pr PR --brief /tmp/review-brief.md \
  --reviewer claude-sonnet --issue ISSUE --apply-label
```

Set `HARNESS_SESSION_FAMILY` to the actual implementer/orchestrator family; the example is for
Codex. Do not override it to bypass independence. Existing blocked-list, stale-head, task
Done-when parsing, final-review parsing, posting and status-label rules apply to both backends.
The main session still records the owner selection before dispatch. This port retains the existing runtime family checks; the broader Claude/Codex workflow audit is tracked in #268. Do not change defaults without the owner's choice.

The registered exact model was observed in Malpaco's retained CLI init events:
`anthropic/claude-sonnet-5-5`. The `anthropic/` prefix is the harness identity; Claude receives
`claude-sonnet-5-5`. An alias is insufficient for verified review identity. Discover future
models from installed CLI help and an explicit recorded trial; never guess their IDs.
Register an independently verified ID without changing defaults:

```bash
node tools/harness/switch-model.mjs --role reviewer --backend claude \
  --model anthropic/claude-sonnet-5-5 --name claude-sonnet --variant high --register-only
```

This checks CLI availability and provider configuration. It does not bill a discovery probe or
claim model availability: each actual review checks the returned init ID exactly. An unavailable
model fails visibly. `--probe` is refused for this backend; use an explicit retained review.
`--backend claude` may also select the default through switch-model, after owner authorization.

## Configuration and permissions

Install/authenticate Claude CLI with its own supported login or an existing Anthropic key.
`HARNESS_CLAUDE_EXE` selects an executable (a `.mjs` fake is supported for offline tests).
The adapter rejects non-direct Anthropic endpoints, alternate provider flags and conflicting
model-remapping environment variables before a model call. It never prints credentials or edits
global auth/settings. Existing OAuth environment authentication works in the measured trials.

`--setting-sources ''` excludes user, project and local settings; only invocation-generated
settings from the trusted launcher checkout are requested. Administrator-managed policies can
still apply; the adapter cannot override them and refuses conflicting identity or denied calls.
This prevents a PR's `.claude` settings
from selecting GLM or changing the reviewer hook. `--model` pins the exact ID, and the init event
must match it and the requested session UUID. Every assistant response model ID, when present,
must also match; a fallback after startup cannot approve. The adapter enables only Bash, Read, Grep and Glob. Claude's native Bash deny rules mirror
OpenCode's publishing restrictions and add common API mutation forms. Native permissions handle
compound commands; no separate Bash parser is installed in this backend. The trusted existing
PreToolUse hook still checks credential paths for Read/Grep/Glob, with the launcher's project
context pinned explicitly. Bash may build, test and mutate copies in its worktree.

These are safeguards against mistakes, matching OpenCode's coarse command policy, not an OS
sandbox. Arbitrary programs/scripts can execute code, access other files or invoke a publishing
API. The prompt still forbids publishing, subagents and global settings edits. No permission
bypass or checkout-supplied hooks are used. Claude refuses to launch when the optional credential
jail is enabled, because that mode has not been integrated; it never silently ignores it.
See the official [permission documentation](https://code.claude.com/docs/en/permissions) for
native deny precedence and compound-command handling. The default jail setting remains off.

Every permission denial or rejected hook invalidates the run. Read its full retained final,
fix the trusted grant, then decide whether another run is authorized. Never count exit0 alone.
The model can save scratch and mutations in its retained worktree, restoring source from saved
bytes. The canonical checkout and inherited dirty files are not its scratch space.

## Diff, coverage and evidence

The launcher records GitHub's base/head, fetches the PR head, creates an isolated detached tree,
and writes a complete local diff, bounded 240-line chunks [designed for readable tool output],
plus a changed-file inventory. It never needs the GitHub diff API's 20000-line response.
The brief includes these exact paths and Sonnet's tripwire. Worktrees are retained for Claude;
no inherited registrations are pruned. `HARNESS_REVIEW_WORKTREE_ROOT` can choose a writable
worktree directory for this invocation. Evidence lives in the launcher's `.cache/review-evidence/`.

A final must account for every Done-when and each changed path. Use `FILE: exact/path` for
inspected files; `EVIDENCE: docs/prototypes/task/` may group only known generated-data suffixes: JSON/JSONL, TXT, LOG, MD, PNG, JPG/JPEG,
GIF, WEBP, GZ, ZIP and PDF. Every other file type, including HTML, JSX, scripts and
extensionless files, requires a FILE line. `SCOPE: complete` is required, and `UNCOVERED:` holds the review.
These are reviewer claims, like DW lines, not proof of honest inspection. The main session must
still read the final and assess coverage. No software parser can prove the model understood a
file. Missing scope is posted with all findings under a note, without approval or a status label.

Retained: full prompt/settings/diff/inventory, stdout events, stderr, final and receipt containing
exact expected/actual model, session, exit/duration, failure, CLI version and prompt/settings/inventory/diff/output hashes. Raw CLI failures
and finals are retained as well. Review evidence must be copied into the task's owned tracked
path and pushed before cleanup; `.cache` is durable locally but is not published evidence.
Do not rerun historical trial runners: their paths identify the original measurement.

## Monitoring and exits

Run as one systemd unit with one `watch.sh` monitor. Track the printed stdout.jsonl path and
run log; `tools/harness/peek.sh <stdout.jsonl> -n 20` reads current Claude tool/message progress.
The log prints the UUID and exact model after init. Startup, idle and total timeouts use the
existing reviewer limits; timeout/cancellation kills this run's own process group and retains a
failure receipt. Claude children receive an evidence-local TMPDIR (and TEMP/TMP on Windows)
without changing the parent environment, keeping temporary outputs on the project disk. Set
the launcher TMPDIR as in the example so the parent poster also avoids a full system /tmp. There is no model/provider fallback. OpenCode continues to use its existing
session/export monitoring path.

Shared exits: 0 posted/labelled; 2 usage/stale brief; 3 no valid run (no label or post); 4 full
review posted but held for main-session assessment. `--dry-run` still bills a real review, but
prints the posting plan instead of publishing. Wrong identity, nonzero CLI exit, malformed
stream, missing/duplicate init/final, denied tools or hook rejection cannot approve code.

Validation: `node --test tools/harness/test/claude.test.mjs` includes the real entry point with
fake Claude/GitHub executables, family/blocked gates, scope/DW holds, error streams, retained
failures and startup/idle/total cleanup. The repository CI runs it alongside `tests/harness_clients.test.mjs`. Malpaco issue #155 carries the real
backend trial and adoption findings. This repository's validation in `docs/prototypes/T60/` is offline and does not establish live Claude availability. Other projects can port the Claude module and entry-point
branch, switch-model support, peek support, roster entry and tests together; preserve their own
guard, labels, family configuration and default reviewer. No agy dependency is needed.

## Research boundaries and port provenance

CLAUDE.md rules 18–20 still apply: original game files and decompiled listings are never published. Static analysis may be read only, never altered or pasted into review comments. Local-only checks remain the responsible main session's work. The CLI is not a cloud workspace. No original material is used by the offline transport tests.

Source: Malpaco committed adapter `eddc62a46898abf7120ff2662d9e73b3a7167d0e` and dependency preparation `00a944eb7fe033cf85d44ce0cd3221b2686c2562`. Goal2 uses the shared `post-review.mjs` approach; no native CLI adapter was found in its inspected checkout. This port preserves IWA's supported OpenCode backup selector and static-folder denials. Agy is separate (#266).
