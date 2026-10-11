# Environment

What a session needs so the main session can delegate. Everything here is optional: each missing
piece turns one delegate off. The scripts then exit 3, and the main session diagnoses and fixes it,
or asks the user for another choice (CLAUDE.md rule 6, 2026-10-11). *Superseded: "the main session
falls back to Claude".*

## On your desktop

Locally there is no network policy and no environment settings, and the session-start hook does
nothing. You need:
- Node 20 or later.
- `gh`, logged in (`gh auth login`). It needs no `GH_TOKEN`.
- OpenCode 1.18 (`opencode --version`), logged in to OpenCode Go (next section).
- Optional: the credential jail (`tools/harness/lib/jail.mjs`, #68), off by default. With
  `"jail": { "enabled": true }` in `harness.json` and bubblewrap installed on Linux or WSL
  (`sudo apt install bubblewrap`), reviewers run without your GitHub credentials; enabled where
  bwrap cannot run, the review hook and `review.mjs` print a warning. Off, only the guard stops a push.
- The other keys below, as user environment variables. On Windows, in PowerShell:
  `[Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", "<key>", "User")`.
  Then restart the terminal and Claude Code, so they see it.

**In WSL** (Claude Code, or the desktop app, working in a WSL folder), use OpenCode's Linux binary.
OpenCode's own installer puts it in `~/.opencode/bin`; the release tarball `opencode-linux-x64.tar.gz`
works too. Avoid `opencode upgrade`, which may reach for the Windows npm. The `opencode` that WSL
finds on PATH is often the Windows npm shim under `/mnt/c`. That shim runs the Windows OpenCode,
which cannot use the run's Linux paths and survives the kill of a timed-out run: both real-OpenCode
tests failed through it. The runner skips the shim and falls back to `~/.opencode/bin/opencode`;
`HARNESS_OPENCODE_EXE` overrides both. WSL and Windows keep separate logins: log in from WSL.

**On Windows**, `npm install -g opencode-ai@1.18`.

Then run `npm test` in the harness repository. The tests against the real OpenCode run wherever
`opencode` is installed. Then do the first-session check at the end of this page.

## OpenCode Go

The MiMo v2.6 reviewers are OpenCode Go's (`opencode-go/…`), a subscription (DeepSeek, Go's earlier model, is blacklisted: the owner, 2026-10-09). They are not OpenCode Zen's pay-per-token `opencode/…` models. Go comes from a console
(organisation) login, not from a key; `opencode auth login` and `OPENCODE_API_KEY` reach only Zen
(IC2 #551):
1. `opencode console login`, then approve the URL and code it prints in the browser;
2. `opencode models opencode-go` lists the models; without the login it lists none, although
   `opencode console orgs` still exits 0 ("No accounts found"). If a login lists none, run
   `opencode models --refresh`.

The login is stored in the database of OpenCode's data directory, not in `auth.json`. Another data
directory, another machine, WSL beside Windows, or a new cloud session each needs its own
`opencode console login`.

## OpenAI, for the reviewer

The default reviewer is GPT-5.6 Luna on the direct OpenAI route (`openai/gpt-5.6-luna`, L51,
`harness.json`'s `reviewer.default`), never a Luna on Go (`opencode-go/…`): a third-party proxy behind Go's returned `Bad Request` in long agent loops
(L27). OpenAI is an ordinary OpenCode provider: log in once with `opencode auth login`, choose
OpenAI (a ChatGPT login or an API key), and check with `opencode models openai`. The login is kept in
`auth.json`, which the scripts copy into their own data directory (next section) whenever theirs is
missing or older. If OpenAI later asks for a new login, log in again in your usual OpenCode; the
next run copies it.

## Z.AI, for the GLM reviewers

GLM-5.3 and GLM-5.3 Flash, reviewers for an explicit `--reviewer`, run on Z.AI's coding plan
(`zai-coding-plan/…`). Log in once with `opencode auth login` and choose Z.AI Coding Plan (an API
key; OpenCode also reads `ZHIPU_API_KEY`), then check with `opencode models zai-coding-plan`. The
key is kept in `auth.json`, which the scripts copy like OpenAI's. GLM-5.3-highspeed is refused by
the plan.

## Quota: quota-tracker

**The harness no longer reads it** (the owner, 2026-10-11, CLAUDE.md rule 6): `review.mjs` runs the
model named whatever the quota, `lib/quota.mjs` and `choose.mjs` were removed, and no model question
shows `/recommend`. The service stays useful to the user, and to the main session when a provider
answers with a usage-limit error: then read `/quota/<provider>` and say when it is usable again.

Where the machine runs quota-tracker, a local service, it reports how much subscription quota is
left on each provider: `claude` (the main session and Claude agents), `openai` (Sol and Luna, via
OpenCode), `zai` (GLM-5.3 and GLM-5.3 Flash), `opencode_go` (MiMo), `openrouter` (prepaid credit)
and `minimax` (the MiniMax Token Plan's own pool). Alibaba's Token Plan (Qwen and GLM;
its DeepSeek models are blacklisted, the owner 2026-10-09; its Kimi and MiniMax models are Team-edition only and unused) is one of those, and it is missing
from this list: quota-tracker stopped checking it (Alibaba flagged the console checks as unusual
activity), so `/quota/alibaba` returns `not_monitored` with `pricing` only — see the Alibaba
Token Plan section below for what this means and how to use those models.
It is read-only, on
localhost, with no auth; results are cached 60 s, and `?refresh` bypasses the cache:
- `curl -s localhost:8765/quota`, or `/quota/<provider>` for one (alibaba's still carries a
  `pricing` object, even though the rest of its entry is empty; zai's carries `pricing` too);
- OpenCode's `external_directory` is a coarse guard, not a sandbox (L61, the owner accepted
  2026-10-06): it path-checks the agent's file tools and, as raw command text, `cd` and `cat`
  (L59) — not `git -C` or grep/sed/head/ls, so an agent with bash allowed can read any directory.
  Secrets are the credential jail's business; a grant is for deliberate reads (L59's recipe).
- `curl -s 'localhost:8765/recommend?tier=heavy'` (or `tier=light`): which model to use.
  `ranking` is best first, each row with `provider`, `model`, `command`, `score` (spare calls per
  day until the pool's reset; negative means the pool would run out before its reset at the current
  demand), `confidence` and `reasons`; `pick` is the first row; `skipped` lists the exhausted or
  nearly full providers, with why. OpenRouter scores 0 (prepaid); Alibaba is not ranked (occasional
  use only, in its discount hours). Right after the service restarts, `note` says the statistics
  are loading: retry after a minute or two. Do not rank by `/best` or `headroom_pct`: percentages
  are not comparable between providers, whose pools differ hugely in size, are monthly or weekly,
  and are partly used by Claude sessions running on them as their main model;
- `curl -s localhost:8765/avoid`: the providers out of quota, with when each is usable again.

Each provider has a `status`: `ok` (under 80% used), `low` (80% or more), `exhausted` (95% or
more: usable again at `available_at` / `available_in`; shown with the question, and the user decides,
CLAUDE.md rule 6; *superseded: "do not use it"*), `error` (it could not be checked;
`error` says why) or `not_configured`. `headroom_pct` is the percent left on its most-used window;
`windows[]` lists every limit with `used_pct` and when it resets. OpenRouter is prepaid: its
windows never reset, and `remaining_usd` is the balance. Every model is judged on its
provider's main window, GPT-5.6 Luna included: it draws on OpenAI's main quota like Sol. Only when a
provider is `exhausted` can a model still run on a limit of its own, and then the provider's
`when_exhausted.usable_models` names it (today `gpt-5.6-luna` on OpenAI; L65). Read which pools
exist from the windows the endpoint returns, not from this page.

Free models on OpenRouter are usable when the user names one (CLAUDE.md rule 6). *Superseded on
2026-10-11, kept as history: "a supplement, for smaller tasks and additional reviews, never the main
model for important work" (the owner, 2026-10-06).* Their privacy limit still holds (below):

| Model | Use |
| --- | --- |
| `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | the stronger one |
| `openrouter/cohere/north-mini-code:free` | coding-focused, faster |
| `openrouter/thinkingmachines/inkling:free` | usable, through OpenCode only (not the raw API) |
| `openrouter/poolside/laguna-s-2.1:free` | usable, often rate-limited |

They share one allowance of 1,000 requests a day and about 20 a minute, and each agent step is one
request: `free_model_daily_requests` in `/quota/openrouter` gives what remains. Free providers may log and train on prompts: never
send private or client code, secrets, or anything under NDA. They come and go and get rate-limited:
on a 429, do not retry; tell the user, who names another model or waits (CLAUDE.md rule 6; *superseded:
"fall back to the next model"*). Check their output like any unreviewed
contribution; they have been tried only on small tasks.

The models per provider, heavy and light:

| Provider | Heavy | Light |
| --- | --- | --- |
| claude | `claude --model opus` | `claude --model sonnet` |
| openai | `opencode -m openai/gpt-6.1-sol` | `opencode -m openai/gpt-5.6-luna` |
| zai | `opencode -m zai-coding-plan/glm-5.3` | `opencode -m zai-coding-plan/glm-5.3-flash` |
| opencode_go | `opencode -m opencode-go/mimo-v2.6-pro` | `opencode -m opencode-go/mimo-v2.6-flash` |
| openrouter | blacklisted (DeepSeek, 2026-10-09); the paid credit is kept anyway | blacklisted (DeepSeek) |
| alibaba (DeepSeek) | blacklisted (the owner, 2026-10-09) | blacklisted |
| alibaba (Qwen) | `opencode -m alibaba-token-plan/qwen3.8-max` | `opencode -m alibaba-token-plan/qwen3.8-flash` |
| alibaba (GLM) | `opencode -m alibaba-token-plan/glm-5.3` | none on alibaba (zai has `glm-5.3-flash`) |
| minimax | `opencode -m minimax/MiniMax-M3` | `opencode -m minimax/MiniMax-M2.7` |

Alibaba's Token Plan is no longer in quota-tracker: `/quota/alibaba` returns `not_monitored` with
`pricing` only — there is no `month` window, and Alibaba is absent from `/quota` and
`/avoid`, and `/recommend` does not rank it. Use Alibaba only when the user asks for it (CLAUDE.md rule 6.4; the scripts need `--alibaba`).
*Superseded, kept as history: "only as a supplement or an extra reviewer, not as a main or default
model, and not in long loops".* OpenCode's key for it comes only from the environment variable
`ALIBABA_TOKEN_PLAN_API_KEY` (in WSL from `~/.config/ai-keys.env`, which `~/.bashrc` and
`~/.profile` load, and through WSLENV for commands started from Windows; on Windows a user
variable), so it works in every OpenCode data directory, the scripts' own included. Never add it
with `opencode auth login`: an `auth.json` entry overrides the variable, and a bad one breaks the
provider for that directory. Never print, copy or edit the key or an `auth.json`. If a call fails:
- a quota or rate error: stop using Alibaba until the next day and tell the owner; do not retry.
- "Provider not found: alibaba-token-plan": the variable is not in this environment. Restart the
  session or shell so it picks it up; if it is still missing, tell the owner. Do not retry.
- "Invalid API-key": the data directory's `auth.json` may hold a stale Alibaba entry (the scripts
  copy yours into theirs). Tell the owner which `XDG_DATA_HOME` the run used.
The owner's plan is the Personal edition: the Kimi and MiniMax models OpenCode lists for this
provider are Team-only and fail. From 22:00 to 08:00 UTC+8, Qwen models use 60% fewer
credits. A quick check that the key works:
`opencode run -m alibaba-token-plan/qwen3.8-flash "Reply with just: ok"`.

The MiniMax Token Plan (the `minimax` provider's models above) is separate from Alibaba's pool: its key comes only
from the environment variable `MINIMAX_API_KEY` (same sources as Alibaba's), never
`opencode auth login`; "Provider not found: minimax" means the variable is missing from the
environment — restart the shell, and tell the owner if it is still missing. Its quota is a 5-hour
and a weekly window (`/quota/minimax`); MiniMax-M3 offers only `none` and `thinking` (the heavy
one, run at `thinking`), MiniMax-M2.7 no variants. A quick check that the key works:
`opencode run -m minimax/MiniMax-M2.7 "Reply with just: ok"`.

The tracker also keeps the usage history: `curl -s 'localhost:8765/usage?since=7d'` gives, per
provider, the models called with their `calls`, `sessions`, `tokens` and `effort` (OpenCode's
`variant`, Claude Code's effort; `default` when none was set), and
`curl -s 'localhost:8765/usage/sessions?since=7d&model=glm-5.3&effort=high'` the sessions behind
them (`title`, `project`, `tool`, `data_dir`, `launched_by`). `since` takes `90m`, `24h`, `7d`, `4w`
or `all`. Use it to check that heavy models ran at the effort L54 asks for.

GPT-5.6 Luna, the reviewer (L51), uses OpenAI's main quota like Sol. When OpenAI is `exhausted`,
Luna alone can still run while `/quota/openai`'s `when_exhausted.usable_models` lists
`gpt-5.6-luna` (L65).

If `curl -sf localhost:8765/health` fails where the service is installed:
1. `systemctl --user restart quota-tracker`, wait a few seconds, and check `/health` again.
2. If systemctl says `Failed to connect to bus`, the user's systemd instance is not running: ask
   the user to run `sudo loginctl enable-linger $USER`, then retry step 1.
3. If it still fails, read `journalctl --user -u quota-tracker -n 50` and tell the user what it says.
4. To run it without the service: `cd ~/projects/models_quota_tracker && uv run quota-tracker serve`
   in the background (it stops when the session ends).

`review.mjs` does not ask the service (above). *Superseded: the quota check before a chain ran
(L52), the warning of 2026-10-11, and `HARNESS_QUOTA_URL`.*

Never read or edit `~/.config/quota-tracker/config.toml`: it holds account tokens. A provider in
`error` over an expired cookie or token goes to the user, since renewing it needs their browser or
login. Where the service is not installed, go on without it, and count a usage-limit error as
`exhausted`.

## The scripts' own data directory

`review.mjs` and `switch-model.mjs` run OpenCode with a data directory of their own, so OpenCode's
desktop app (2.x) can never migrate their database to a schema the 1.x CLI cannot read (IC2 #540,
"no such column: project_id"). It is `~/.local/share/harness-opencode`, with `data/`, `cache/` and
`state/` set as `XDG_DATA_HOME`, `XDG_CACHE_HOME` and `XDG_STATE_HOME` for OpenCode's processes only.
`HARNESS_OPENCODE_HOME` moves it (a relative path is made absolute). `auth.json`, the API-key
providers, is copied in from `~/.local/share/opencode` (or `HARNESS_OPENCODE_AUTH_SOURCE`) when the
copy is missing or older; it is never read or printed.

Go's login does not travel with `auth.json`, so log in once for this directory. In bash (WSL, Linux):

```bash
XDG_DATA_HOME="$HOME/.local/share/harness-opencode/data" opencode console login
```

In PowerShell (Windows), in a new window afterwards:

```powershell
$env:XDG_DATA_HOME = "$HOME\.local\share\harness-opencode\data"; opencode console login
```

Check it with the same `XDG_DATA_HOME` and `opencode models opencode-go`. Before any run, each script
checks that OpenCode lists its model there; if not, it exits 3 with the command that fixes it (this
one for Go, `opencode auth login` for OpenAI), and nothing is billed. The scripts never change their
own process's environment, only that of the OpenCode processes they start, so nothing needs
restoring afterwards.

## What the OpenCode reviewer may reach outside its worktree

`.opencode/agents/reviewer.md` grants two places, and only these (T29; the owner, 2026-10-05):

- **The static folder**, `~/.local/share/isle-wars-archaeology/static/`, the default `$IWA_STATIC`,
  to read: static readings are checked against the decompiled output there, which stays off the
  repository (CLAUDE.md rule 18). OpenCode 1.18.34 expands the leading `~/` (and `$HOME/`) of a
  permission pattern to the home directory, so the tracked file holds no machine path. It expands
  no other variable: a `$IWA_STATIC` set elsewhere is not granted, and a review that reads it is
  rejected. Keep the static folder at the default place, or extend the grant first.
- **One scratch TMPDIR** matching `/tmp/iwa-review-*`, which the reviewer makes with
  `mktemp -d /tmp/iwa-review-XXXXXX` and removes afterwards.

The edit tool is denied everywhere, and the plain shell writes into the static folder (`rm`, `mv`,
`cp`, `touch`, `mkdir`, `chmod`, `tee`, `sed -i`, a `>` redirection and a few more) are denied by
the agent's `bash` patterns. Those patterns read command text, so a write through a script, a
variable other than `IWA_STATIC`, `find -delete`, `sh -c` or a relative path is not stopped: the
grant guards against mistakes, not against a reviewer set on writing there. The same holds for
every outside path: OpenCode checks its file tools, and only `cd`, `rm`, `cp`, `mv`, `mkdir`,
`touch`, `chmod`, `chown` and `cat` among shell commands, against these rules; `head`, `grep` or
`sha256sum` on a path elsewhere, or a `>` redirection's target, is not rejected (OpenCode 1.18.34's
shell tool, as read from its source).
`tests/test_reviewer_permissions.py` checks the rules.

### The OpenCode implementer (T31; removed 2026-10-11)

`.opencode/agents/implementer.md` and `tests/test_implementer_permissions.py` were removed with
`implement.mjs` (CLAUDE.md rule 6: the main session or a Claude agent implements, with the
session's own permissions). The static folder's rules for a Claude implementer are CLAUDE.md
rule 18's: read it in place, hash it, never copy a line of it into the worktree.

## Keys

In **Claude Code on the web**, set these in the environment's settings: the cloud environment menu
in the session's title bar, then **Edit**, then the environment variables (or API credentials, where
that section is offered). A new session picks them up. On **your machine**, set them in your shell.
Never paste a key into a chat, and never commit one.

| Variable | Used by | Without it |
| --- | --- | --- |
| `OPENCODE_API_KEY` | OpenCode Zen's `opencode/*` models, if `harness.json` names any. The default models are Go's, which need `opencode console login` instead (above) | nothing, while `harness.json` names only Go models |
| `OPENROUTER_API_KEY` | Jev, through OpenRouter (`jev.mjs`); also OpenCode's `openrouter/*` models, if `harness.json` names any | `jev.mjs` exits 3; the main session decides every item itself |
| `ELEVENLABS_API_KEY` | ElevenLabs: speech, voices, sound effects, music (`/delegate`, `models.mjs elevenlabs`) | no generated audio; the main session says so |
| `GH_TOKEN` | `gh`, inside the tools and inside OpenCode's runs: finding the PR, `gh pr create`, posting a review, labels | the scripts cannot find or post to PRs |

For `GH_TOKEN`, use a fine-grained token limited to the project's repository, with read and write on
Contents, Pull requests and Issues.

OpenCode reads both `OPENCODE_API_KEY` and `OPENROUTER_API_KEY` from the environment (checked with
`opencode auth list` on 1.18.33), so those need no `opencode auth login`. Go is the exception: without
its console login, `review.mjs` exits 3. Log in (`opencode console login`, in both
data directories) and run again; another model only when the user names it (CLAUDE.md rule 6).
*Superseded: "and Claude agents take the work".*

## Network

A cloud environment's network policy must allow:

| Host | For |
| --- | --- |
| `opencode.ai` | OpenCode's own providers (Zen, Go) |
| `openrouter.ai` | Jev, OpenRouter models, image generation |
| `api.z.ai` | the GLM reviewers, GLM-5.3 and GLM-5.3 Flash |
| `api.elevenlabs.io` | ElevenLabs |
| `registry.npmjs.org` | installing OpenCode |
| `api.github.com`, `github.com` | `gh` and git |
| the Ubuntu package archive | installing `gh` with apt |
| `models.dev` | OpenCode's model list. Optional: runs worked without it, but allow it if `opencode models` shows stale ids. |

## The session-start hook

`.claude/hooks/session-start.sh`, registered in `.claude/settings.json`, runs at the start of every
session on the web (and does nothing locally). It:
- installs `opencode-ai@1.18` with npm and `gh` with apt, if they are missing;
- reports which keys are set, as the session's first context.

It never fails the session. OpenCode is pinned to the 1.18 line because the runner's assumptions were
checked against it:
- the `run` flags;
- `session list --format json`, with `id`, `title`, `directory`, `created` and `updated`;
- `export`, whose `info.agent` names the agent that actually ran.

Change the pin only after running the tools against the new version.

On your machine, install the same things yourself: `npm install -g opencode-ai@1.18`, `gh`, and
Node 20 or later.

## First session: check it works

1. The hook's report shows every key `set`, and no setup notes.
2. The hook's report says OpenAI is logged in (the default reviewer), and `opencode models openai`
   lists `harness.json`'s `luna` id. If an id differs, edit `harness.json`.
3. Jev: put two lines such as `{"id": 1, "state": {"title": "Game crashes on load"}}` in
   `items.jsonl`, then run `node tools/harness/jev.mjs ask --decision breaks-play --in items.jsonl`.
   It should print `asked 2 of 2`.
4. OpenCode: run `/run-task` on a small `fix`, and watch the first review: the tail of its log and
   the posted review.


## Static analysis tools

U32 (static first, CLAUDE.md rule 24): a research question is answered by unpacking, decompiling and
reading the executable before any run. The tools below do that for both games, on the user's machine
only (C3). Everything they derive from an original (an unpacked executable, a carved movie, a
decompiled script, a Ghidra project) goes to `$IWA_STATIC`, a folder outside every checkout, and is
never tracked (rule 18); what a finding or a record may hold is hashes, sizes, counts, addresses
and names (`tools/static/static_common.py`, T26).

The tools folder is `$IWA_TOOLS`, else `$HOME/tools`. `python3 setup/static/check_tools.py` compares each
tool with `setup/static/tools.json` (the files that identify it and their sha256) and prints `ready`.
Files below are identified by one or more files inside the tool, because the owner installed Ghidra
and the JDK from their official archives.

| Tool | Version | Where (below the tools folder) | Identified by (sha256) | Source |
| --- | --- | --- | --- | --- |
| Ghidra | 12.1.4 PUBLIC, build 2026-09-21, revision `8b6bbb857accdfa20dc5b2f5dea471178c2e9fbc` | `ghidra_12.1.4_PUBLIC` | `Ghidra/application.properties` `e84c26b08545eee63d24a1a8a4dd7905e4209538e2e7192093877c435c64eb67`; `support/analyzeHeadless` `302880328a0024ee24cfe0326d4d9a61c2237116d95f2e0e0df090f747f95e30`; the rest in `tools.json`. The release archive `ghidra_12.1.4_PUBLIC_20260921.zip` is published with sha256 `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`; the owner's archive was not available to compare | github.com/NationalSecurityAgency/ghidra, release `Ghidra_12.1.4_build` |
| Java (JDK) | Eclipse Temurin 21.0.12.1+1-LTS, x86-64 Linux | `jdk-21.0.12.1+1` | `lib/modules` `70c5465dabf8e1bec2860631ea3ffd342f0ec23a5e2efd3a389d2abe32448f98`; `release` `ebbd70bf00bab6d39addf51969c5ff244030b86b29de400b9fb10612ebd3ceec`; `bin/java` `2a207f5e7d075afa01d97f8048389a64432a44c4a5af0f5e77d6e286ec5f401d` | adoptium.net, Temurin 21; the tarball's published checksum was not compared |
| ProjectorRays (Director decompiler) | 0.2.0, commit `8a3d3b4211575170276fc6be350b6b52e96d4750`, MPL-2.0 | `projectorrays-0.2.0/bin/projectorrays` | `d1c2235bd5f32f4a268a2cd09d2260e143b8caf51124e0da8d9f54fd113c0ea3`; built by `setup/static/build-projectorrays.sh` with the headers of `libboost1.83-dev` 1.83.0-2.1ubuntu3.2 (deb sha256 `519ecf2c64308527e15b6582955681d192a832250baa4bc424967aaf7d02d68f`) and `libmpg123-dev` 1.32.5-1ubuntu1.1 (`5fe2e9a221025ddd526baf2c2e3a0df5aacc8626f927d14fcb9585414a2d6d40`), and the system `libmpg123.so.0` | github.com/ProjectorRays/ProjectorRays, tag `v0.2.0`; its only release asset is a Windows executable, so it is built from source |
| Deark (the PKLITE and EXEPACK unpacker) | 1.7.3 (`deark -version` prints `Deark version: 1.7.3`), commit `e3c0ef3c6b6b8b697146a4016eb796ac02744785`, an MIT-style licence | `src/deark-1.7.3/deark` | `deark` `70c93ae2755a4682bf249b91c76e088d47225e1bda867916f3a3dae5d4bb8e23` | github.com/jsummers/deark, tag `v1.7.3`, built with `make` in the source tree without changes (the owner's choice and the main session's build, 2026-10-05) |

One more tool was used in T26, in the terminal only, and no script runs it: **GNU objdump**, `GNU
objdump (GNU Binutils for Ubuntu) 2.42`. It is the system's `objdump` on PATH, the distribution's link
to its x86-64 binutils binary (not below the tools folder), from the Ubuntu package
`binutils-x86-64-linux-gnu` 2.42-4ubuntu2.8 (source package `binutils`); the binary
`x86_64-linux-gnu-objdump` has sha256 `d0041e7511460b9ebfd95ce4f9d93c7ffea398ffc1cb2c316a220dd8e533db3d`,
and its md5 equals the package's own `md5sums` entry. The implementer looked at bytes of the unpacked
DOS image with `objdump -m i8086` while locating the places that push a file name; nothing it printed
was kept or tracked. It is recorded under `terminal_only` in `tools.json`, which `check_tools.py`
does not check.

**Environment variables.** `IWA_STATIC` (the folder for everything derived; every script refuses it
unset, relative, inside a checkout, containing this repository, or overlapping an original's folder),
`IW_DOS_DIR` and `IWP_DIR` (the folders of the originals, read in place, hashed against
`artifacts/known.json` before any read), and, to move a tool, `IWA_GHIDRA`, `IWA_JAVA_HOME`,
`IWA_PROJECTORRAYS`, `IWA_DEARK`.

**Running them headless** (no game is run):

```bash
IWA_STATIC=<folder outside every checkout> IWP_DIR=<the Pro install> \
  python3 tools/static/iwp_extract.py --probe Isledft.dat --record iwp-extract-<run>.json
IWA_STATIC=<folder> IW_DOS_DIR=<the DOS copy> \
  python3 tools/static/dos_unpack.py [--original iw-dos-ov6] --run <run> --record dos-unpack-<run>.json
IWA_STATIC=<folder> python3 tools/static/dos_probe.py --file deark-<run>/stage2-exepack.000.exe \
  --sha256 <its sha256> --needle ISLEWAR.SAV --record dos-probe-<run>.json
IWA_STATIC=<folder> python3 tools/static/ghidra_import.py --file deark-<run>/stage2-exepack.000.exe \
  --sha256 <its sha256> [--range 1000:9b33-1000:9d5f] --run <run> --record ghidra-<run>.json
IWA_STATIC=<folder> python3 tools/static/inventory_derived.py (--dir <run folder>... | --all) --prefix <prefix>
IWA_STATIC=<folder> python3 tools/static/iwp_markers.py --dir iwp-extract-<run> \
  --against iwp-extract-<run>.json --record iwp-markers-<run>.json
python3 tools/static/check_derived_hashes.py      # no tracked file is an output derived from an original
```

- `tools/static/iwp_extract.py` reads `Islepro.exe` (a Director projector for Windows), carves each
  embedded Director movie, gives ProjectorRays a work copy of it at its original offset (the
  movie's internal offsets are the executable's), decompiles it with `--dump-scripts`, and counts
  chunks, scripts and handlers. `--probe NAME` lists the handlers that mention a file name.
- `tools/static/dos_unpack.py` unpacks `ISLEWAR.EXE` (or `ISLEWAR.OV6`) in two Deark runs:
  `-m pklite` on the original, read in place, then `-m exepack` on that output (the PKLITE layer
  holds an image packed by Microsoft LINK's EXEPACK). Both outputs go to `deark-<run>/` in
  `$IWA_STATIC`; the script checks that the last one is a plain DOS executable (relocations and entry
  point inside the load module, no packer left).
- `tools/static/dos_probe.py` reads an unpacked image in `$IWA_STATIC` (by sha256): which run-time
  library's marker texts it holds, and where the code pushes the string descriptor of a file name.
- `tools/static/ghidra_import.py` runs `analyzeHeadless` with `-processor "x86:LE:16:Real Mode"
  -cspec default` and the post-script `tools/static/ghidra/T26Report.java`, which writes counts and
  addresses (no instruction) to the run's folder. Ghidra refuses a project path with a folder whose
  name starts with a dot (`.local`, say), so the script gives it a link to the project folder in a
  temporary folder. `--range START-END` has the post-script disassemble from START and write the
  instructions up to END to `listing-<START>.txt` in the run's folder, for a person to read there;
  the record gets only the range and its counts.
- Every run is a new folder `<tool>-<run id>` in `$IWA_STATIC`; nothing is overwritten, and
  `--record NAME` writes a new file under `experiments/E008-static-triage/measurements/`, refused when
  its text holds a machine path. The record lists every file the run left in its folder (the tool's
  own files too: a Ghidra database, a listing, a dumped chunk) by sha256 and size, as
  `derived_files`.
- `tools/static/inventory_derived.py` writes the same `derived_files` list, as a new record, for run
  folders made before the scripts listed them; `check_derived_hashes.py` then fails on a tracked
  copy of any listed file, whatever its name.
- `tools/static/iwp_markers.py` counts ProjectorRays' error markers (the word `ERROR` in a script,
  an opcode named `unk` and two hex digits in a bytecode listing) in the scripts an extraction
  record lists, checked by their sha256; it records counts only.
- `tools/static/dos_identify.py` reads the PKLITE header of `ISLEWAR.EXE` in place and writes nothing
  derived; it still refuses an unset or in-checkout `IWA_STATIC`, as every script does.

A missing tool is a step to finish, never a reason to fall back to runs (U32): every script stops
with that message when its tool is not there.
