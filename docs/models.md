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
| `gpt-6.1-sol` | GPT-6.1 Sol, `openai/gpt-6.1-sol`, effort `low` | OpenAI | **hard reviewer** (`--reviewer gpt-6.1-sol`), used sparingly; probed 2026-10-03 at `high`, PONG in 5 s |
| `gpt-6-sol` | GPT-6 Sol, `openai/gpt-6-sol` | OpenAI | probed; the hard reviewer before 6.1 (T06, malpaco T02) |
| `deepseek-pro` | DeepSeek V4 Pro, `opencode-go/deepseek-v4-pro` | DeepSeek | probed, not in a pair |
| `zai-glm-5.3` | GLM-5.3, `zai-coding-plan/glm-5.3` | GLM | probed; implemented T06, and was tried as a calibration reviewer |
| (Claude) Sonnet | `task-agent`, `model: sonnet` | Claude | the implementer for research, the user's install and cloud sessions; the fallback implementer; the easy fallback reviewer |
| (Claude) Opus | `task-agent`, `model: opus` | Claude | the hard fallback reviewer; the cloud reviewer |
| (Claude) Fable | `task-agent`, `model: fable` | Claude | allowed, not used yet |

Every model runs at effort `high`, never `max`. `max` was slower, with no gain (L27). **The
exception is GPT-6.1 Sol** (the owner, 2026-10-03), which is used sparingly:
- only for hard reviews;
- at effort `low` (`harness.json`'s `gpt-6.1-sol` and `gpt-6-sol` entries);
- at `medium` only when the task file says why;
- never at `high`.

Credit is not the reason, and is not a reason to raise it.

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
| Research, or anything that reads the user's install | **Sonnet** (`task-agent`, worktree isolation) | by difficulty, on the repository side | OpenCode cannot reach outside its worktree (L26). The main session runs the `[C3]` lines and posts their output on the PR. If no OpenCode reviewer is available, the Claude fallback would be the implementer's family: escalate | T03, T04, T10 (easy: Luna); T08, T09 (hard: GPT-6.1 Sol) |
| A safety seal around the originals, or reverse-engineering probes (savestates, debuggers, unpacked or undocumented formats) | **Opus** from the start, with the task file saying why (rule 6) | by difficulty, usually hard | T08's seal converged only under Opus. The owner saw Sonnet struggle with reverse engineering in IC2 | T11, the DOSBox-X spike (first use, 2026-10-04) |
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

**When GPT-6.1 Sol cannot review.** The review goes to a substitute instead of waiting, unless
the owner says to wait.

- **Diagnose first.** Read the run's `/tmp/harness-opencode/<session>.err.txt`, and probe
  `openai/gpt-6.1-sol` with `switch-model.mjs --probe --dry-run`.
  - `The usage limit has been reached` means the whole OpenAI account is out of quota. Luna is
    blocked too, so confirm with a probe of `openai/gpt-6-luna`.
  - If only Sol fails (the model is unavailable, or its cost is to be avoided), Luna is still an
    option.
- **Substitutes, in order,** skipping the implementer's family:

  | Situation | Hard review | Easy review |
  | --- | --- | --- |
  | Only Sol is unavailable | GLM-5.3 (`zai-glm-5.3`), then DeepSeek V4 Pro (`deepseek-pro`), then Luna, with the reason stated | Luna, as usual |
  | The OpenAI account is out of quota | GLM-5.3, then DeepSeek V4 Pro | GLM-5.3, then DeepSeek V4 Pro |
  | The implementer is GLM | DeepSeek V4 Pro | DeepSeek V4 Pro |
  | The implementer is DeepSeek | GLM-5.3 | GLM-5.3 |

  Luna stands in for Sol on a hard task only when no heavy third-family reviewer can run, and the
  review's header says so. Never fall back to a Claude reviewer when Claude implemented the task:
  escalate instead.
- **How:**
  1. Probe the substitute: `switch-model.mjs --role reviewer --model zai-coding-plan/glm-5.3 --name zai-glm-5.3 --probe --dry-run`.
     Add `--force` only when the refusal concerns the default implementer's family, not this
     task's.
  2. Reuse Sol's brief unchanged, except:
     - the header names the substitute;
     - one sentence says it reviews in Sol's place, and why;
     - Sol's earlier reviews are linked, so it re-takes their attacks.
  3. Run `review.mjs --pr <n> --reviewer zai-glm-5.3 --issue <n> --apply-label --brief <file>`.
     On exit 3, run it again with `--reviewer deepseek-pro`.
  4. Record the change on the task file's Reviewer line, with the date and reason.
  5. Log it on the trials issue.
- **First use: T08, round 2.** On the owner's decision of 2026-10-03, after the OpenAI quota
  stopped Sol mid-review: GLM-5.3 reviews, and DeepSeek V4 Pro is its fallback. Both answered their
  probe (PONG in 4 s and 5 s).

**The `[C4]` re-hash can run through WSL interop** (T10, at the owner's request).
`powershell.exe` from WSL runs Windows PowerShell's `Get-FileHash` over `\\wsl.localhost\…`.
That gives another OS and another tool on the same copy. The one-liner must use
`(Resolve-Path $dir).ProviderPath`: `.Path` breaks on a UNC path (#33).

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
| When the implementer is Claude, keep a probed heavy reviewer from a third family ready (DeepSeek V4 Pro, GLM-5.3) | both OpenAI reviewers share one account quota: on T08's final round `The usage limit has been reached` stopped GPT-6.1 Sol mid-review and failed the probe of Luna too, and a Claude fallback was not allowed | T08, 2026-10-03 |
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

## Keeping this page current

The main session updates this page in the same commit as any of these:
- the owner switches a model;
- a `harness.json` entry is added or removed;
- a run teaches a new adjustment;
- a trial changes what a model is known to do well or badly.

It stays a strategy and a set of observations. What is running now lives in the labels and in the
trials issues.
