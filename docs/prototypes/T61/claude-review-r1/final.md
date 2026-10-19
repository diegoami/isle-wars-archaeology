T61 review (Claude Sonnet medium)
rework

DW1: ran `python3 docs/prototypes/T61/preflight.py --output /tmp/iwa-T61-preflight.json` → exit 0, `completed: true`, `sameFamilyRejected` and `blockedRejected` both true.
DW2: ran `python3 docs/prototypes/T61/check_report.py` → exit 0, "15 audit areas accounted for". Mutation probes on a copy in `/tmp` show the checker is weaker than DW2 requires (see R1).
DW3: ran `node --test tests/harness_clients.test.mjs tools/harness/test/claude.test.mjs` → 13 of 13 pass. Ran `node tools/harness/review.mjs --self-test` → 35 of 35 samples and 77 of 77 checks pass.
DW4: ran `python3 tools/check_no_originals.py` → ok (2428 files). Ran `python3 tools/check_links.py` → ok. Ran `git diff --check cdde671...HEAD` → clean. I found no credentials, global settings contents or originals in the retained JSON. The guide separates SSH on the owner's host from cloud. It makes no claim of a live Claude result, and the native medium-effort invocation is documented.

Where I worked: the worktree for PR #272 at HEAD d337adf. The diff is merge-base cdde671...HEAD, 13 files. I did not run the live Codex smoke, call any model, or run the cloud hook.

Facts I checked and found true:
- `peek.sh` reads Claude `stream` files.
- `watch.sh --opencode-log` exists.
- `run-unit.sh NAME LOG -- CMD` has the shape the guide shows.
- `review.mjs` accepts `--reviewer`, `--variant`, `--issue`, `--apply-label` and `--brief`.
- The repository has no `.agents` directory and does have `.claude/skills`.
- The cited `learn.chatgpt.com` URL answers HTTP 200.

Findings:

**R1 (blocking): `docs/prototypes/T61/check_report.py:142` and `:140` accept the omissions DW2 says they reject.**
- DW2 requires "non-working paths name a follow-up and a usable alternative or explicit limitation". The checker only tests that `follow_up` is a string starting with `#`, and that `claude`, `codex` and `operator_action` are non-empty.
- I ran each of these mutations on a copy in `/tmp` and the checker exited 0 every time:
  - `follow_up: "#"`
  - `operator_action: "x"`
  - changing `model-choice-policy` from broken to works, which contradicts the retained preflight's `sameFamilyRejected: true`
  - citing only `codex-smoke-prompt.txt` as an area's evidence
  - replacing the Claude text of an area
- Fix:
  - Require `#\d+`.
  - Require the alternative or limitation text to be substantive for broken, untested and explicit-equivalent rows.
  - Require evidence that matches the area. Examples: monitoring needs the export diagnostic, and model-choice-policy needs a preflight that shows the filters.

**R2 (blocking, shares a cause with R1): `docs/prototypes/T61/accounting-controls-r1.json` asserts four controls were caught, but nothing reproduces them.**
- The controls are missing-area, missing-evidence, tampered-digest and untriaged-broken-route.
- The file is not hashed in `matrix-r1.json`. No script or test in the PR runs those mutations, and R1 shows weaker mutations pass.
- A hand-written "caught: true" claim therefore backs the checker's credibility.
- Fix: add a mutation self-test to the checker or a test file that actually exercises the four controls, or drop the file.

**R3 (blocking): the checker never compares `docs/client-compatibility.md` to the matrix.**
- The guide's table is the operator-facing deliverable. `matrix-r1.json` can drift from it with no failure.
- The checker also cannot fail if the guide drops an area, a disposition, or an issue link.
- Fix: parse the guide table and assert that area, disposition and follow-up match the matrix.

**R4 (non-blocking): `docs/client-compatibility.md:45` and `matrix-r1.json` (model-choice-policy) overstate the OpenAI case.**
- The guide says offline probes show that "same-family OpenAI reviews from Codex are refused".
- The retained probe only tests a Claude model with `HARNESS_CLIENT=claude`, plus a synthetic blocked list. No OpenAI same-family sample is recorded.
- Fix: add that sample to `preflight.py`, or narrow the wording.

**R5 (non-blocking): the retained evidence and the stated baseline disagree.**
- `preflight-r1.json` records `head: a88584a`, while the guide and matrix say the baseline is `cdde671`.
- Nothing ties `preflight-r1.json` to the current `preflight.py`, which may have changed after the run.
- Fix: record the baseline and the script hash.

**R6 (non-blocking): the checker uses bare `assert`, and `python -O` strips them.**
- Fix: use explicit raises.

**R7 (non-blocking): `preflight-r1.json` publishes the host name `WINDOWS-BJ0PUMB`.** This is not a credential. Consider dropping it from retained evidence.

SCOPE: complete
FILE: CLAUDE.md
FILE: docs/client-compatibility.md
FILE: docs/prototypes/T61/accounting-controls-r1.json
FILE: docs/prototypes/T61/check_report.py
FILE: docs/prototypes/T61/codex-smoke-prompt.txt
FILE: docs/prototypes/T61/codex-smoke-r1.json
FILE: docs/prototypes/T61/codex-smoke-schema.json
FILE: docs/prototypes/T61/export-diagnostic-r1.json
FILE: docs/prototypes/T61/matrix-r1.json
FILE: docs/prototypes/T61/preflight-r1.json
FILE: docs/prototypes/T61/preflight.py
FILE: docs/tasks/README.md
FILE: docs/tasks/T61.md

Final pass done
rework