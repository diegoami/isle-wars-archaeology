---
name: delegate
description: Choose who does a piece of work, and on which model. Claude agents review and judge; OpenCode implements and reviews code; Jev takes repeated decisions; models on OpenRouter make images and give other model families; ElevenLabs makes speech, sound effects and music. Use before doing work yourself that a cheaper or better-suited model could do, whenever a task needs an image, a sound or a voice, and whenever you are about to name a model id.
---

# /delegate: who does the work, and on which model

You are the main session. Your time and tokens are the scarce resource. Before doing work
yourself, check whether a delegate below does it better or cheaper.

## The delegates

| Work | Delegate | How | Key |
| --- | --- | --- | --- |
| Code: implement a task or a fix | **The user's choice** (CLAUDE.md rule 6): the main session in its own worktree, a Claude agent, or OpenCode | `/run-task` → `tools/harness/implement.mjs --model <name>`, or Agent | Z.AI's login (`opencode auth login`) and OpenCode Go's (`opencode console login`) to implement; OpenAI's (`opencode auth login`) to review |
| Review a PR | **The user's choice** at every review: an external model, never the implementer's family | `/run-task` → `tools/harness/review.mjs --reviewer <name>` | as above |
| Repeated decisions with known answers (triage, routing, gating, labelling) | Jev | `/jev` → `tools/harness/jev.mjs` | `OPENROUTER_API_KEY` |
| Images: sprites, icons, maps, mockups, illustrations | An image model on OpenRouter | pick one with `models.mjs openrouter --output image` | `OPENROUTER_API_KEY` |
| A second opinion from another model family, or reading audio or images | A model on OpenRouter | `models.mjs openrouter --input image` (or `audio`) | `OPENROUTER_API_KEY` |
| Speech, voices, sound effects, music | ElevenLabs | `models.mjs elevenlabs` | `ELEVENLABS_API_KEY` |
| Judgment that needs a written reason, design, planning | You, or a Claude agent | — | — |

The session-start report says which keys are set. A delegate without its key is off; do the work
another way, or tell the user what is missing (`docs/environment.md`).

## Picking a model

1. **Never from memory.** Model ids and prices change faster than any document. List them live:
   - `node tools/harness/models.mjs openrouter --output image`;
   - `node tools/harness/models.mjs elevenlabs`;
   - `opencode models opencode-go` for implementers (OpenCode Go), `opencode models openai` for the
     reviewer.

   Do the same when you are unsure a model still exists. (L25)
   To change the implementer's or reviewer's model itself, use `/switch-model`.
2. **Ask the user** (CLAUDE.md rule 6, the owner, 2026-10-11). For code and reviews the user
   chooses, with ONE question each time:
   - before implementing: does the main session implement it, or a subagent (a Claude agent, or
     OpenCode), and with which model?
   - at every review: which external model reviews?

   Show quota-tracker's suggestion with the question, as a suggestion only:
   `curl -s 'localhost:8765/recommend?tier=heavy'` for heavy work, `tier=light` for small work.
   Give its `pick`/`pair` with rank, outlook and reliability, and ask without it when it does not
   answer. The only fixed rules: the reviewer is never of the implementer's family, DeepSeek is
   never used, and Alibaba only when the user asks. Record the choice and the suggestion's reasons
   on the issue or PR. A failed run is diagnosed and fixed; another model only when its provider does
   not answer, and the user names it.
   *Superseded on 2026-10-11 and kept as history:* checking the quota and taking the next model of a
   chain (L50, L52); `/recommend`'s `pair` as the choice; `choose.mjs`.
3. **Choose on the evidence you have.** In order of preference:
   - this project's own measurements (review rounds and tokens per task, from the merge comments);
   - a small trial;
   - the listed price and capabilities.

   Vendor benchmarks come last.
4. **Record the choice where it is used.** An implementer or reviewer choice goes on the issue or PR,
   and in the task file, with the date and the reason in the commit
   message. A generated asset gets a sidecar next to it, `<asset>.json`, with the provider, the
   model id, the prompt, the date and the cost. That records where it came from, and lets it be
   made again.
5. **Say the cost first.** Before a batch (many images, a long narration), tell the user the
   estimated cost from the listed prices, and ask when it is more than a few dollars.

## Making media

Call the provider's API directly, with `fetch` from Node. Read the API reference for the endpoint
before the first call in a project, because request shapes change. Then keep the working call in a
small script under `tools/`, so the next asset is one command. Starting points (check them first):
- **OpenRouter images:** `POST https://openrouter.ai/api/v1/chat/completions`, with an image-output
  model and `"modalities": ["image", "text"]`. The image comes back in the assistant message.
- **ElevenLabs:** `POST https://api.elevenlabs.io/v1/text-to-speech/<voice_id>` for speech, and
  `POST https://api.elevenlabs.io/v1/sound-generation` for sound effects. Both use the `xi-api-key`
  header and return audio bytes.

Generated assets are project content: commit them with their sidecar, and review them the way the
project reviews its UI (a person looks at the screen).

## Never

- Name a model id you have not just seen in a live list.
- Send private repository content or personal data to a provider the user has not cleared for it.
- Spend on a batch without saying the cost first.

## A rule's carve-out (process.md §10)

When a project's `CLAUDE.md` loosens a rule by carve-out, three changes merge before the first
task that uses it: the known-good table in a finding, the gate in `tools/` that checks every
record against it, and the task file for the first run, which names the carve-out's lettered
preconditions as Done-when lines. Delegate a `model-driven` task only once the gate accepts the
implementer's run records; such a run corroborates the owner's runs, never replaces them, and its
results amend the wording one claim at a time, never in bulk. (L63)

### This project: the rule 18 carve-out (CLAUDE.md, owner 2026-10-08; constraint E amended 2026-10-09)

A model agent may run the original Pro binary under Wine on the user's machine for run capture
and UI observation, under constraints A–G. Since the owner's amendment of 2026-10-09 (constraint
E), model sittings and the owner's Bandicam videos both count toward T28's per-claim totals, and
sittings may be scheduled to run unattended; what only a human sitting shows (mistakes,
hesitation, tactics) still rests on the owner's videos. Companion changes T35, T36, T37 are merged.
When delegating a `model-driven` task (TEMPLATE.md's `Kind` enum), the implementer's
`runtime.platform` must be `wine-on-user-machine-iwp-2.0` (the only recognised token)
and `start_state.sha256` must match the F019 row's hash for the named set+variant; the T36
gate enforces this. The binary, the install, the run copy, savestates, memory dumps,
screenshots, recordings and any patched build stay on the user's machine — never in the
repo, a release, an issue, a cloud session, or any tool input that leaves the user's
machine. Exception (the owner, 2026-10-08): a model-driven sitting's screenshots and frames may be read by the same model APIs as derived output (Anthropic, OpenAI, Z.ai, Alibaba), never by free OpenRouter models, and are still never committed, uploaded or posted. Per-claim wording amendment is per-claim, not in bulk (constraint G).
