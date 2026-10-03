# Models: who implements, who reviews, and how

This page is the main session's working strategy for routing work to models. It covers
[isle-wars-archaeology](https://github.com/diegoami/isle-wars-archaeology) and
[malpaco](https://github.com/diegoami/malpaco), which share the roster and the harness.

- **One page, two copies.** The page is kept identical in both repositories as `docs/models.md`.
  A change goes to both in the same session.
- **Task and issue numbers** without a repository name are isle-wars-archaeology's. malpaco's are
  written `malpaco T02` or `malpaco#3`.
- **No status.** The run-by-run record is the model-trials issues,
  [isle-wars-archaeology#9](https://github.com/diegoami/isle-wars-archaeology/issues/9) and
  [malpaco#3](https://github.com/diegoami/malpaco/issues/3).
- **The binding rules** are CLAUDE.md rules 1, 6 and 21, numbered the same in both repositories.
  Where this page and those rules differ, the rules win, and this page gets fixed.

**Who decides.** The owner chooses the models and switches them often, as credits and prices
change. The main session never routes by budget. Its job is to keep a switch cheap:
- every candidate stays probed, with a `harness.json` entry;
- each task file names its implementer and its reviewer, one line each, and says `easy` or `hard`;
- a switch is applied to tasks not yet started, with the owner's reason in the commit message.

## The roster

| Name in `harness.json` | Model and route | Family | Used for |
| --- | --- | --- | --- |
| `zai-glm-5.3-flash` | GLM-5.3 Flash, `zai-coding-plan/glm-5.3-flash` | GLM | **easy implementer**, the `harness.json` default |
| `deepseek-flash` | DeepSeek V4.1 Flash, `opencode-go/deepseek-v4.1-flash` | DeepSeek | **hard implementer** (`--model deepseek-flash`) |
| `luna` | GPT-6 Luna, `openai/gpt-6-luna`, the direct OpenAI route | OpenAI | **easy reviewer**, the `harness.json` default |
| `gpt-6.1-sol` | GPT-6.1 Sol, `openai/gpt-6.1-sol` | OpenAI | **hard reviewer** (`--reviewer gpt-6.1-sol`); probed 2026-10-03, PONG in 5 s |
| `gpt-6-sol` | GPT-6 Sol, `openai/gpt-6-sol` | OpenAI | probed; the hard reviewer before 6.1 (T06, malpaco T02) |
| `deepseek-pro` | DeepSeek V4 Pro, `opencode-go/deepseek-v4-pro` | DeepSeek | probed, not in a pair |
| `zai-glm-5.3` | GLM-5.3, `zai-coding-plan/glm-5.3` | GLM | probed; implemented T06, and was tried as a calibration reviewer |
| (Claude) Sonnet | `task-agent`, `model: sonnet` | Claude | the implementer for research, the user's install and cloud sessions; the fallback implementer; the easy fallback reviewer |
| (Claude) Opus | `task-agent`, `model: opus` | Claude | the hard fallback reviewer; the cloud reviewer |
| (Claude) Fable | `task-agent`, `model: fable` | Claude | allowed, not used yet |

Every model runs at effort `high`, never `max`. `max` was slower, with no gain (L27).

**Never used:**
- Haiku;
- Gemini, because of its cost;
- Kimi and Grok.

**Routes that matter:**
- GLM runs only through the Z.AI Coding Plan, never through Go or pay-per-token Z.AI.
- Luna runs only on the direct OpenAI route. Go's Luna went through a proxy that returned
  `400 Bad Request` in long agent loops (L27).

**Beyond implementing and reviewing:**
- **Jev** (`jev-1.13` through OpenRouter): repeated yes/no decisions, after a trial (`/jev`). The
  key is set in the interactive shell, so it is run with `bash -ic`.
- **OpenRouter models:** images. **ElevenLabs:** audio.
- Their ids come from live lists, never from memory (`/delegate`).

## Routing: easy or hard

The owner decided on 2026-10-03 that the pair follows the task's difficulty:

| Difficulty | Implementer | If it is unavailable | Reviewer | If it is unavailable |
| --- | --- | --- | --- | --- |
| Easy, the default | GLM-5.3 Flash | Sonnet | GPT-6 Luna | Sonnet |
| Hard | DeepSeek V4.1 Flash | Sonnet | GPT-6.1 Sol | Opus |

**When a task is hard.** A task is hard if any of these holds:
- it is a guard, a gate, or a tool whose failure would let an original or a copy through (in
  malpaco: a gate or test that guards the UI or the rules core);
- it adds a new mechanism across several files, or a new external dependency;
- an earlier round found blocking bypasses.

Everything else is easy: doc and config fixes, exact-line contracts, and single-mechanism code
with clear tests. The main session decides, and the task file's Implementer and Reviewer lines say
`easy` or `hard` with the reason. `harness.json` holds the easy pair as the default; a hard task
passes `--model deepseek-flash` and `--reviewer gpt-6.1-sol`, and names Opus as its Claude
fallback.

**The family rule.** The reviewer always comes from another family than the implementer.
`review.mjs` refuses an OpenCode reviewer of the implementer's family, and
`--exclude <implementer>` says which one that is. Both pairs, and every fallback against the
other role's OpenCode model, keep the families apart.

**The exceptions:**

| Work | Implementer | Reviewer | Why | Examples |
| --- | --- | --- | --- | --- |
| Research, or anything that reads the user's install | **Sonnet** (`task-agent`, worktree isolation) | by difficulty, on the repository side | OpenCode cannot reach outside its worktree (L26). The main session runs the `[C3]` lines and posts their output on the PR. If no OpenCode reviewer is available, the Claude fallback would be the implementer's family: escalate | T03, T04; T08 (hard: GPT-6.1 Sol) |
| Cloud sessions | Sonnet | Opus | only Claude runs there, so the same family is forced, and the task file says so | T05 (planned for the cloud; it ran locally) |

**Escalation after a heavy review** (the owner, 2026-10-03). When a review shows that the
implementer is out of its depth, the next round goes to a stronger implementer. The task does not
spend its last round on the same model.

- **When.** Either of these:
  - a review asks for rework with three or more blocking findings;
  - a rework round brings new blocking findings of the same class as the last round's.
- **The steps.** GLM-5.3 Flash → DeepSeek V4.1 Flash → Opus, and Sonnet → Opus. An escalated
  implementer is always Claude Opus at the top, so the reviewer stays OpenAI. If that reviewer is
  unavailable, the Claude fallback would be the implementer's family: escalate to the owner.
- **The rounds.** The count does not reset: two rework rounds, then the owner (rule 7).
- **The hand-over.** The new implementer gets the task file, every review so far, and the previous
  implementer's unpushed work as a patch to weigh, never to apply blindly. It starts from the pushed
  branch.
- **First use: T08, round 2** (Opus's result is under "What each model has shown").
  - GPT-6.1 Sol found 6 blocking findings at round 0 and 5 new ones at round 1.
  - Both rounds were the same class: an alias or a side path at the moment of a write or a launch.
  - Sonnet was stopped mid-round, and Opus took the branch.

**Watch:** L27 records GLM-5.3 Flash stalling, and ending long implementer runs early, in IC2.
It ran malpaco T02's round 2 cleanly. Its first runs as the easy default are watched, and a stall
is diagnosed before any fallback (rule 21).

**Jev, for easy or hard (planned).** The owner cleared sending task-file text to OpenRouter for a
Jev trial (2026-10-03). A trial needs about 60 labelled items, and labels the main session makes
itself measure Jev against the main session, not against the truth. So every task file records
`easy` or `hard` with its reason, and the outcome adds the label: a hard task that went cleanly,
or an easy one whose review found blocking bypasses, says the call was wrong. At about 60 items,
the decision `task-hard` is defined and trialled (`/jev`). Until then, the main session decides.
Jev would give only the decision, so the main session still writes the reason.

## How a run is made

- **OpenCode implementer:**
  `node tools/harness/implement.mjs --task T<nn> --slug <slug> --issue <n> --brief <file> [--model <name>] [--env K=V]`,
  or `--fix <issue>` for a fix.
  - It runs in the background, and the main session waits for the completion notice, never
    polling with sleep.
  - The script makes the worktree under `../<repo>-work/`, and resumes a pushed branch on rework.
  - Exit 0: a PR is open. Exit 1: read the log; the implementer stopped and reported, or ended
    early. Exit 3: OpenCode, the model or the login is unavailable, and the Claude fallback runs.
- **OpenCode reviewer:**
  `node tools/harness/review.mjs --pr <n> --brief <file> --exclude <implementer> --issue <n> --apply-label [--reviewer <name>]`.
  - Exit 0: the review is posted and labelled.
  - Exit 3: no review came back, so the Claude reviewer runs (Opus).
  - Exit 4: a review was posted under a note, with no label. The main session reads it and
    applies the label it supports, without paying for a second review.
- **Claude implementer or reviewer:** `Agent(subagent_type: task-agent, model: <sonnet|opus|fable>, isolation: worktree)`.
  - The agent creates its branch from `origin/main`, pushes it, and opens the PR.
  - A cloud brief first checks the hostname and that `/mnt/c` is absent, and stops if either
    check fails.
- **Briefs:**
  - An implementer brief is the task file pasted in full, then `docs/process.md` §4's block, then,
    on rework, the review's URL (rule 15).
  - A reviewer brief is §5's block, filled in with the PR, its head sha and the issue, then the
    contract.
- **Reading a verdict:**
  - `approve` maps to `status:approved`.
  - `approve after named fixes` maps to `status:rework`, even when every finding is non-blocking.
    At the last round the main session escalates with options. In malpaco T02 the owner chose to
    merge, and filed the non-blocking findings as a follow-up.
- **After every run:** one comment on the trials issue, giving the model, its role, the task, the
  exit code, the duration, the round, and what the review caught or missed (rule 21). A failing
  model is diagnosed and fixed before any fallback: its log, the brief, the agent file, the harness
  and the login.

## Adjustments that keep runs working

Each of these cost at least one wasted run, or a false result, before it was in place.

| Adjustment | Why | Learned |
| --- | --- | --- |
| OpenCode runs only through `implement.mjs` and `review.mjs`, in their own data directory (`~/.local/share/harness-opencode`). Never `opencode upgrade`. | The desktop app migrates the database to a schema the 1.x CLI cannot read; an upgrade can reach for the Windows npm shim | IC2 #540; `docs/environment.md` |
| "database is locked" from OpenCode: retry | a transient lock, not a model failure; two runs in parallel worked on 2026-10-03 | trials #9 |
| Pass `--env PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright` to both scripts (malpaco) | the harness sets its own `XDG_CACHE_HOME`, so Playwright cannot find Chromium | malpaco, 2026-10-03 |
| In briefs and task files, cite a commit as "commit `<sha>`", never "at `<40-hex>`" | `review.mjs` reads "at <sha>" as the commit to review, and refuses | harness_imperial#32 |
| Dry-run every Done-when line before a task starts: it fails on `main` and passes on a mock fix | twice, a line that no implementation could pass reached an implementer | 2026-10-03 |
| For a doc fix, name the exact lines to change and the lines that must not change, with a grep that proves the second | a repository-wide replace would rewrite claims under test and quoted sources | fix #21 |
| Golden screenshots are made and compared only in `mcr.microsoft.com/playwright:v<lock version>-noble`, run with `--user $(id -u):$(id -g)` | fonts and anti-aliasing drift between machines; run as root, the container would leave root-owned files | malpaco T02 (the owner's choice) |
| Keep the targeted pixel checks beside the goldens | at Playwright's default tolerance, a hidden hatch still passed the board golden | malpaco T02, Sol's R1 |
| `isolation: "remote"` may run locally without saying so: a cloud brief checks where it runs before doing anything | T05's "remote" agents ran on this machine | 2026-10-03 |
| Node 24 on PATH for non-interactive shells | the harness needs Node 20 or later; the nvm default did not reach non-interactive shells | 2026-10-03 |
| The `[C3]` lines (the install, the Wine prefix, the display) are run by the main session and posted on the PR | an OpenCode reviewer cannot reach outside its worktree, and a rejected tool call fails the run | L26; T03 |
| One OpenCode model per role, then Claude: no long chains of cheap models | chains multiplied wasted attempts; one failure stopped the chain before the next model ran | L27 |

## What each model has shown so far

These are observations, each with its source. The trials issues hold the full record.

- **DeepSeek V4.1 Flash** (implementer):
  - Sound. It stops correctly on a Done-when it cannot meet.
  - It missed one test-coverage gap that Luna caught (T02: no CLI test for `check --list`), and
    once posted outside its own PR.
  - On exact-line fixes it is fast and exact: fixes #19 and #21 took about 1–1.5 minutes each.
- **GLM-5.3** (implementer, T06, on Go at the time):
  - It finished every run, with no early stop.
  - It added scope nobody asked for, the fence handling, and both blocking bypasses lived there.
  - It applies a directed fix exactly.
  - Earlier, in IC2, GLM models ended long runs early (L27). That has not recurred here.
- **GLM-5.3 Flash** (implementer, malpaco T02):
  - It followed an amended contract, golden screenshots in a container, and showed mutation
    evidence for every evasion.
  - It missed stale counts in its own doc.
- **GPT-6 Luna** (reviewer):
  - It proves findings by mutation, and is fast: 1–2 minutes on small PRs.
  - It caught T02's missing CLI test, T03's missing offsets and T04's paraphrase beyond the quotes.
- **GPT-6 Sol** (reviewer, heavy):
  - The adversary. It found two fence-parsing bypasses in T06, and new pixel evasions in each of
    malpaco T02's rounds.
  - In the last round it re-ran every Done-when line inside the image.
  - Patching evasion by evasion did not converge against it. Changing the strategy to golden
    screenshots did.
- **GPT-6.1 Sol** (hard reviewer; first real run on T08, 2026-10-03, about 8 min):
  - It reviewed the W3a runtime spike as an adversary. It asked for rework, with six blocking
    findings, each proven with a synthetic reproduction that never touched the install:
    - prefix and bundle locations were not confined to outside a checkout;
    - a symlinked game folder made the sync step delete files from the install;
    - relative links escaped the prefix, and the check still passed;
    - N0 was optional, and an isolation observation could be false;
    - the start-state hash left out registry values;
    - two safety checks could be deleted with all 53 tests still green.
  - These are the classes the hard tier exists for. The Sonnet implementer's own mutation checks
    had missed every one of them.
  - It stated the tier it reached honestly: V0, with no access to the install. It verified the
    vendored bytes against the pinned commit itself.
- **GLM-5.3, as a calibration reviewer** (T02's round-0 tree, a dry run):
  - It approved, missing Luna's blocking R1.
  - But it found two real gaps that Luna did not report.
- **Sonnet** (research implementer: T03, T04, T05):
  - Reliable on research documents.
  - Its typical miss is overreach, a cell paraphrased beyond its quote, which the reviewers catch.
- **Opus** (implementer, T08 round 2, escalated from Sonnet; about 47 min, 344k tokens):
  - It took over after GPT-6.1 Sol's two heavy reviews, and fixed the class, not the instances:
    - one confined writer (`O_NOFOLLOW`, `O_EXCL`, open-then-`fstat`, no shared inodes);
    - the prefix seal re-checked immediately before launch;
    - a run is `completed` only on a clean finish.
  - It added a guarantee nobody asked for, and it fits: the install is bound read-only inside each
    run's mount namespace, and the run aborts unless the bind really is read-only.
  - It swept its own code for the same class with synthetic fixtures, listed the sweep, and stated
    the gaps that remain. Its deletion mutants: 32, with no survivors.
  - It weighed Sonnet's unpushed partial patch, rather than applying it.
  - The main session reproduced its controls on the round-2 head (r0041–r0043: the same
    `before` and start-state hashes). GPT-6.1 Sol's final review decides whether the escalation
    converged.
- **Opus** (reviewer, T05): precise. It found a wrong date and dated the evidence, by checking
  Wayback captures itself.

## Keeping this page current

The main session updates this page in the same commit as any of these:
- the owner switches a model;
- a `harness.json` entry is added or removed;
- a run teaches a new adjustment;
- a trial changes what a model is known to do well or badly.

It stays a strategy and a set of observations. What is running now lives in the labels and in the
trials issues.
