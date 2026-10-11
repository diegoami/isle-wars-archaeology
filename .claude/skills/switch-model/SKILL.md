---
name: switch-model
description: Switch the default OpenCode reviewer (harness.json's reviewer.default), safely - live ids, the right login, the effort rule, the family rule, and a one-word probe before anything is written. Use when the user wants another default reviewer, when the reviewer keeps failing (exit 3, early stops, Bad Request), or before trying a new model on real reviews.
---

# /switch-model: change the default reviewer

The implementer is the main session or a Claude agent (CLAUDE.md rule 6), so the one model to
switch is the OpenCode reviewer: today GPT-5.6 Luna on the direct OpenAI route. A one-off review
on another model needs no switch (`review.mjs --reviewer <name>`); a switch changes the default,
and it is the user's decision, so you propose it and the user says yes.

1. **Why.** Name the reason: a measured failure (the run logs, the measurement comments, the
   model-trials issue), a cheaper or better candidate, or the user's request. A model that failed
   once on a strange task is not yet a reason (L14).
2. **What runs now.** `node tools/harness/switch-model.mjs --show`.
3. **Candidates, live** (L25), never from memory: `opencode models openai`, `opencode models
   zai-coding-plan`, `opencode models opencode-go`, and so on, each with its own login. Leave out
   Claude models (the implementer's family), DeepSeek (never used), Alibaba unless the user asks,
   and models ruled out in `docs/lessons.md` (L27: Go's own GPT-6 Luna returns `Bad Request` in
   long loops). `--show` lists the registered models, each with its note in `harness.json`.
4. **Dry run with a probe:**
   `node tools/harness/switch-model.mjs --model PROVIDER/ID --probe --dry-run`.
   - It checks the id against OpenCode's list in the scripts' data directory. On exit 3, give
     the user the login command it prints; the user runs it.
   - The effort, unless `--variant` gives one: `high` for a light model; for a heavy one (Sol,
     GLM-5.3, MiMo V2.6 Pro, MiniMax-M3) `low`, else `medium`, else the lowest OpenCode offers
     (L54). `max` is refused.
   - It refuses a Claude model and DeepSeek.
   - The probe is one billed one-word call at that effort.
5. **Ask.** Show the user the before and after lines and the probe's time, with your
   recommendation. Switch only on their yes.
6. **Switch.** Run the same command without `--dry-run` (and without `--probe`, which already
   passed). Then commit `harness.json` on `main` with the reason and the probe in the message
   (L6, L25). Keep the old model's entry: an explicit `--reviewer` can still use it.
7. **Watch the first review** on the new model: the log's tail and the posted review. Afterwards,
   add a line to the model-trials issue (CLAUDE.md rule 21). Switch back the same way if it fails.

Exits: 0 switched (or shown, or a dry run); 1 refused (the family rule, DeepSeek, or a taken name);
2 usage; 3 OpenCode, the login or the probe failed, and nothing was written.
