# Models: who implements, who reviews, and how

This page is the main session's working strategy for routing work to models, for
[isle-wars-archaeology](https://github.com/diegoami/isle-wars-archaeology) and
[malpaco](https://github.com/diegoami/malpaco), which share the harness.

- **One page, two copies.** The page is kept identical in both repositories as `docs/models.md`.
  A change goes to both in the same session.
- **No status.** The run-by-run record is the model-trials issues,
  [isle-wars-archaeology#9](https://github.com/diegoami/isle-wars-archaeology/issues/9) and
  [malpaco#3](https://github.com/diegoami/malpaco/issues/3).
- **The binding rules** are CLAUDE.md rules 1, 6 and 21. Where this page and those rules differ,
  the rules win, and this page gets fixed.

## Who does what (the owner, 2026-10-11 and 2026-10-12)

What worked in practice, after ten days of chains, pairs and quota checks:

| Role | Who | How |
| --- | --- | --- |
| Orchestrator | The main session, set by the Anthropic environment variables alone (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL`): Claude; or GLM-5.3 through Z.AI's Anthropic-compatible endpoint, MiniMax, or Moonshot's Kimi when Claude's tokens are out | never named by the harness; its family is read from the environment (`lib/common.mjs` `sessionFamily`, `HARNESS_SESSION_FAMILY` overrides) |
| Implementer | The **`implementer` subagent** spawned inside Claude Code (worktree isolation) on a model of its own, not the orchestrator's: `sonnet` under Opus, which under Z.AI is GLM-5.3 Flash, or any model id the session's provider serves. **The main session** implements directly, in its own worktree, only where the provider cannot spawn a subagent. Asked before each implementation, `harness.json`'s `implementer.default` proposed first | `/run-task` step 2; `.claude/agents/implementer.md` |
| Reviewer | **One OpenCode run** of another family than the session's, on the model the user names at the question before the review, `harness.json`'s `reviewer.default` (GPT-5.6 Luna) proposed first; `gpt-6.1-sol` for a guard, a gate or hard research | `tools/harness/review.mjs [--reviewer <name>]`, as a systemd unit, watched |

The roster is the owner's and changes often: `harness.json`'s two defaults and its `blocked` list
change through `/switch-model`, never by a rule that names a model, and no quota, tier or
difficulty table picks one. The fixed rules: the reviewer is never of the session's family (so no
Claude reviewer under Claude, no GLM reviewer under Z.AI, unless the user asks for a same-family
review); a blocked model never runs (DeepSeek today); Alibaba only when the user asks.

**Why OpenCode does not implement any more.** Its implementer runs were the harness's main source
of lost work: runs ended by a rejected path outside the worktree (T13 three times, T21 and T22,
mm-m3 on goal2's T29), by the reset between chain attempts, by a 900 s idle kill during a long
command, by a model ending early, and by models that did not follow the brief (`cd /abs &&`,
scratch files in `/tmp`, scope nobody asked for). The main session and Claude agents, which run
in the same tool with the same permissions as the session, had none of these failure classes;
their misses were review findings, fixed in a round. `implement.mjs`, the chooser, the quota
check and the chains were removed on 2026-10-11 (this repository's history before that commit
holds them).

**Why OpenCode still reviews.** A reviewer of another family catches what the author's family
misses (Sol's bypass findings on T06 and T08; Luna's citation checks on T02–T04, T10), and a
review is read-only, so a run that misbehaves costs one review, not a branch. OpenCode's models do
not always follow the brief: `review.mjs` reads what came back, posts a review it cannot read
whole under a note with no label (exit 4), and the main session reads it and decides rather than
paying for another. It gets the permissions a review needs (all of `/tmp`, the static folder
read-only) in `.opencode/agents/reviewer.md`, so a loose scratch file no longer ends the run.

## The roster (`harness.json`)

| Name | Model and route | Family | Use |
| --- | --- | --- | --- |
| `luna` | GPT-5.6 Luna, `openai/gpt-5.6-luna`, effort `high`, the direct OpenAI route | OpenAI | **the default reviewer** (L51): fast, proves findings by mutation |
| `gpt-6.1-sol` | GPT-6.1 Sol, `openai/gpt-6.1-sol`, effort `low` | OpenAI | the adversarial reviewer for a guard, a gate or hard research; `medium` only when the task file says why, never `high` (the owner, 2026-10-03) |
| `gpt-6-sol`, `luna-6` | GPT-6 Sol and GPT-6 Luna | OpenAI | registered for an explicit `--reviewer`; they share OpenAI's pool with Sol |
| `zai-glm-5.3` | GLM-5.3, `zai-coding-plan/glm-5.3`, effort `low` (no medium) | GLM | a credible heavy reviewer when OpenAI is out (T08 round 2); 3x in weekday peak from 8 Oct 2026 |
| `zai-glm-5.3-flash` | GLM-5.3 Flash, `zai-coding-plan/glm-5.3-flash`, effort `high` | GLM | a light reviewer for small PRs |
| `mimo-flash`, `mimo-pro` | MiMo v2.6 Flash and Pro on OpenCode Go, no variant (they offer none) | MiMo | a family of its own; Go needs `opencode console login` in the scripts' data directory |
| `mm-m3`, `mm-m2.7` | MiniMax-M3 (variant `thinking`) and M2.7 (no variant) | MiniMax | a family of its own; key `MINIMAX_API_KEY` from `~/.config/ai-keys.env`, never `opencode auth login` |
| `ali-qwen-max`, `ali-qwen-flash`, `ali-glm` | Qwen 3.8 Max (`low`), Qwen 3.8 Flash (`medium`) and GLM-5.3 (`low`) on the Alibaba Token Plan | Qwen, GLM | only when the user asks (`--alibaba`); key `ALIBABA_TOKEN_PLAN_API_KEY` the same way |
| (the session's provider) | the orchestrator's model from the Anthropic environment; `sonnet`, `opus`, `haiku`, `fable` or a model id for the `implementer` subagent, which the orchestrator spawns on a model of its own | Claude; GLM, MiniMax or Kimi when the environment says so | implements; reviews only when the user asks |

**DeepSeek is blocked** (the owner, 2026-10-09), on any route: `harness.json`'s `blocked` list, which
`review.mjs` and `switch-model.mjs` refuse and `/switch-model --block` and `--unblock` change.
Every id comes from a live list (`opencode models <provider>`), never memory; `/switch-model`
changes a default with a probe.

**Effort.** A light model (Sonnet, GPT-5.6 Luna, GLM-5.3 Flash) runs at `high`; a heavy model
(Opus, GPT-6.1 Sol, GLM-5.3, MiMo v2.6 Pro, MiniMax-M3) at `medium` at most, and at `low` when
medium is not needed (the owner, 2026-10-05). A model that offers no medium takes its lowest
variant at or below `high`. Never `max`: slower, with no gain (L27). `--variant` on `review.mjs`
runs a registered model at another effort for one review.

**Sonnet's tripwire** (the owner, 2026-10-04). Models judge their own depth poorly. Every Sonnet
brief ends with this paragraph, and on an `ESCALATE` the main session answers the question itself
or takes the task over on the pushed branch:

```text
Out of your depth: stop and hand back, with an ESCALATE block, when any of these happens:
two hypotheses for the same question have failed; you would rely on bytes, code or behaviour
you cannot explain; you are about to write a claim you cannot back with evidence; or you have
made three attempts at one step without progress. Push your branch first. The ESCALATE block
gives what you tried, the evidence so far, and the exact question you could not answer. Never
guess a format or a cause.
```

**Beyond implementing and reviewing:** Jev (`jev-1.13` through OpenRouter) for repeated yes/no
decisions after a trial (`/jev`); OpenRouter models for images; ElevenLabs for audio. Their ids
come from live lists, never memory (`/delegate`).

## Faster game cycles (Isle Wars Pro)

These are not about models, but they set how long every research run takes, and so how much
implementer and reviewer time a driver costs. Measured in T08's control runs, r0028–r0030:

| Step | Seconds |
| --- | --- |
| Xvfb and the window manager ready | 0.1 |
| game window appears | 0.4–0.5 |
| title screen reached and stable | 6.6–6.7 |
| hover, click Options, Options screen | under 0.1 |
| exit through the game's Quit, then Exit Game | 14.7–14.8 |
| Wine processes gone | 2.1 |

- **The title screen is not a splash to skip.** "Unregistered Shareware Version" is the main menu.
  The 6.6 s before it is the Director projector unpacking its runtime and Xtras. No binary is
  patched to remove it: rule 18 stands, and stripping the unregistered notice would be a crack (the
  owner, 2026-10-03).
- **Terminate with Alt+F4 or `wineserver -k`,** not the menu's Quit:
  - Alt+F4 takes 0.3–3.4 s;
  - `wineserver -k` is immediate. It leaves Director's temp files, which reset removes.

  The full quit path is tested once (T08), not in every cycle. This takes a cycle from about 25 s
  to about 10 s.
- **Relaunch less often.** A driver keeps the game running between trials, and starts each one
  with New Game or a loaded save. The 6.6 s launch is paid once per session.
- **Run in parallel.** Each run has its own Xvfb and namespaces, so prefixes can run side by side.
- W5a, the minimal driver, adopts these, and measures the time per cycle over its 10 repeats.

## How a run is made

- **Every brief for a task that measures** (research, a runtime spike, a driver that times things,
  static reading) ends with this standing paragraph. It is CLAUDE.md rule 20, from
  game-archaeologist L207:

  ```text
  Measurements: write every output a finding or the PR may cite (run records, probe logs and
  tables, timings, evidence captures by hash, static extracts) under a tracked path this task
  owns, never only under scratch/, a cache or a machine-local folder. Originals stay out: record
  their hashes. Commit and push after each batch of runs or probes, and at least every 30
  minutes. Never delete or overwrite a measured output; a re-run writes new files beside the old,
  and the finding says which it cites.
  ```

  The task file's Owns must name that tracked path, for example `runs/E<nnn>/**` or
  `experiments/E<nnn>-*/measurements/**`.

- **The implementer**, asked before each implementation, is
  `Agent(subagent_type: "implementer", model: <alias or id>, isolation: "worktree")` with the brief,
  or, where the provider cannot spawn one, the main session in
  `../isle-wars-archaeology-work/<task>` on the task's branch: the task
  file pasted in full, then `docs/process.md` §4's block, then, on rework, the review's URL
  (rule 15). Either keeps `RUN-NOTES.md`, pushes after every commit and opens the PR. A cloud
  brief first checks the hostname and that `/mnt/c` is absent, and stops if either check fails.
- **The reviewer**, asked before each review: `tools/harness/run-unit.sh review-<pr> <log> -- node
  tools/harness/review.mjs --pr <n> --brief <file> --issue <n> --apply-label [--reviewer <name>]`, watched with
  `tools/harness/watch.sh` (CLAUDE.md rule 6.6). The brief is §5's block, filled in with the PR,
  its head sha and the issue, then the contract and `docs/review-brief.md`.
  - Exit 0: the review is posted and labelled.
  - Exit 3: no review came back; nothing posted. Read the final message (rule 25), fix the cause,
    run again.
  - Exit 4: a review was posted under a note, with no label. The main session reads it and applies
    the label it supports, without paying for a second review.
- **Reading a verdict:** `approve` maps to `status:approved`; `approve after named fixes` maps to
  `status:rework`, even when every finding is non-blocking (at the last round the main session
  escalates with options; in malpaco T02 the owner chose to merge and filed the findings as a
  follow-up).
- **After a review that taught something:** one comment on the trials issue (rule 21). A failing
  model is diagnosed and fixed before any fallback: its log, the brief, the agent file, the harness
  and the login.

## Adjustments that keep runs working

Each of these cost at least one wasted run, or a false result, before it was in place.

| Adjustment | Why | Learned |
| --- | --- | --- |
| OpenCode runs only through `review.mjs`, in its own data directory (`~/.local/share/harness-opencode`). Never `opencode upgrade`. | The desktop app migrates the database to a schema the 1.x CLI cannot read; an upgrade can reach for the Windows npm shim | IC2 #540; `docs/environment.md` |
| "database is locked" from OpenCode: retry | a transient lock, not a model failure | trials #9 |
| In briefs and task files, cite a commit as "commit `<sha>`", never "at `<40-hex>`" | `review.mjs` reads "at <sha>" as the commit to review, and refuses | harness_imperial#32 |
| A review brief's first line is exactly `<title> review (<model>)`; rounds are said in the body | `review.mjs`'s header parser refuses anything else, exit 2 before any model runs | T21 round 2, 2026-10-06 |
| Dry-run every Done-when line before a task starts: it fails on `main` and passes on a mock fix | twice, a line that no implementation could pass reached an implementer | 2026-10-03 |
| For a doc fix, name the exact lines to change and the lines that must not change, with a grep that proves the second | a repository-wide replace would rewrite claims under test and quoted sources | fix #21 |
| The `[C3]` lines (the install, the Wine prefix, the display) are run by the main session and posted on the PR | an OpenCode reviewer cannot reach outside its worktree, and a rejected tool call fails the run | L26; T03 |
| The reviewer gets all of `/tmp` and the static folder read-only in its agent file; a run that dies on a rejected path is fixed by widening the grant, never by re-briefing | three reviews of PR 166 were refused for writing in `/tmp` before the grant (d30a137); DeepSeek and GLM runs died on quoted `cat`/`cd` paths (T13, T23) | the owner, 2026-10-11 |
| The static-folder reading recipe is grep/sed -n/head/ls/sha256sum with the file's quoted `~` path, never `cd` or `cat` | `cd` and `cat` paths are permission-checked as raw command text, and a quoted path fails the match | T13 L57; T23 |
| Heavy models at effort `medium` at most, `low` when medium is not needed; light models at `high` | the owner's decision | the owner, 2026-10-05 |
| Keep a probed heavy reviewer from a third family registered (GLM-5.3, MiMo v2.6 Pro, MiniMax-M3) | both OpenAI reviewers share one quota: on T08's final round `The usage limit has been reached` stopped Sol mid-review | T08, 2026-10-03 |
| `isolation: "remote"` may run locally without saying so: a cloud brief checks where it runs before doing anything | T05's "remote" agents ran on this machine | 2026-10-03 |
| Node 24 on PATH for non-interactive shells | the harness needs Node 20 or later; the nvm default did not reach non-interactive shells | 2026-10-03 |
| Pass `--env PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright` to `review.mjs` (malpaco) | the harness sets its own `XDG_CACHE_HOME`, so Playwright cannot find Chromium | malpaco, 2026-10-03 |
| Golden screenshots are made and compared only in `mcr.microsoft.com/playwright:v<lock version>-noble`, run with `--user $(id -u):$(id -g)`; keep the targeted pixel checks beside the goldens | fonts and anti-aliasing drift between machines; at Playwright's default tolerance a hidden hatch still passed the board golden | malpaco T02 |

## What each model has shown so far

These are observations, each with its source. The trials issues hold the full record.

- **DeepSeek V4 Pro** (implementer, T13 round 3, 2026-10-05):
  - Three attempts ended on a path outside its worktree, which OpenCode rejects, ending the run.
    Two were the brief's fault: an outside TMPDIR asked for, and `.git/info/exclude` (in a worktree
    `.git` points into the main checkout). One was its own habit: scratch output redirected to `/tmp`.
    It also starts commands with `cd /abs &&` despite the agent file.
  - Its final messages (read from the session record, rule 25) show runs cut off mid-work, not a
    stop-and-report. Uncommitted work was lost to implement.mjs's reset until #87 (PR #88).
  - Briefs to an OpenCode implementer ask for nothing outside the worktree; such lines are the main
    session's `[C3]` lines. Ask it to commit and push after each step.
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
- **GLM-5.3 Flash** (implementer; the easy default since 2026-10-03):
  - malpaco T02: it followed an amended contract (golden screenshots in a container), and showed
    mutation evidence for every evasion. It missed stale counts in its own doc.
  - As the easy default, on fixes #25 and #33, it took about 2.5 min each. Each diff was exactly the
    contract's line, and Luna approved both with no findings.
  - L27's early stop has not recurred in its first runs.
- **GPT-6 Luna** (reviewer):
  - It proves findings by mutation, and is fast: 1–2 minutes on small PRs.
  - It caught T02's missing CLI test, T03's missing offsets and T04's paraphrase beyond the quotes.
  - On T10, it caught two inferences beyond their citations: archive timestamps read as creation
    dates, and a gameplay line filed as a registration limit. It recomputed the set id itself.
    Then it approved the round-1 fix in about 2 min.
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
- **GLM-5.3** (substitute hard reviewer, T08 round 2, about 19 min):
  - It stood in for GPT-6.1 Sol when the OpenAI quota ran out, with Sol's brief and Sol's earlier
    reviews.
  - It re-took all of Sol's attacks with its own script (13), and ran 12 mutants of its own, all
    killed. One mutant killed trivially at first, so it rewrote it as an `if False:` mutant.
  - It cross-checked every new record against F002 and its manifest, and found one new
    non-blocking hang (#27).
  - It approved. With the earlier T02 calibration, GLM-5.3 is a credible heavy reviewer when Sol is
    not available.
- **The T08 escalation converged.** Sonnet's two rounds drew 6, then 5, blocking findings. Opus's
  round drew none.
- **GLM-5.3, as a calibration reviewer** (T02's round-0 tree, a dry run):
  - It approved, missing Luna's blocking R1.
  - But it found two real gaps that Luna did not report.
- **Sonnet** (research implementer: T03, T04, T05, T08 rounds 0–1, T09, T10):
  - Reliable on research documents and fast on identity work: T10 took about 5 min, then 2 min for
    its rework.
  - Its typical miss is overreach: a statement that says more than its citation (T04's paraphrase,
    T10's dates and limits). The reviewers catch it, and a sweep for the same class in the rework
    fixes it.
  - On a safety seal (T08) it was out of its depth: two rounds drew 6, then 5, blocking findings of
    the same class. Opus converged it.
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

## Superseded model-choice rules

Kept as history, no longer rules (the owner, 2026-10-11). Their full text is in this
repository's history before the commit that removed them (`git log -1 --format=%H -- tools/harness/implement.mjs`,
then `git show <sha>^:docs/models.md`), and in `docs/lessons.md` L68:
- the fixed pairs by difficulty (2026-10-03: GLM-5.3 Flash and Luna for easy work, MiMo v2.6
  Flash and GPT-6.1 Sol for hard) and the escalation ladder after a heavy review (L38);
- quota first (L50, L52, L65): skipping an exhausted provider for the next model of a chain;
- `/recommend` decides (2026-10-10), then "the user decides, asked before every run" (the morning
  of 2026-10-11, L68) with `/recommend` as a suggestion;
- the implementer and reviewer chains, `choose.mjs`, the Claude fallbacks, `--hard`, `--sol` and
  `--second-opinion`; the afternoon of 2026-10-11's "nobody is asked" (the two questions came back
  on 2026-10-12, with the switchable roster);
- the exclusions by name (never Haiku, Gemini, Kimi, Grok; GLM only via Z.AI; Luna only direct),
  which `review.mjs --reviewer` no longer enforces: DeepSeek is the one blacklist.

## Keeping this page current

The main session updates this page in the same commit as any of these:
- the owner switches the default reviewer;
- a `harness.json` entry is added or removed;
- a run teaches a new adjustment;
- a trial changes what a model is known to do well or badly.

It stays a strategy and a set of observations. What is running now lives in the labels and in the
trials issues.
