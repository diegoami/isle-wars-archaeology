# E016 pro-deal-reading

- **Task**: T33 (#97). U32 (static first), CLAUDE.md rule 24.
- **Question**: How does the decompiled Lingo of *Isle Wars Pro* deal the board's 46 countries to the seats and set the starting state — how the territories are dealt, the cap on territories per player, the starting armies on each territory, what the difficulty setting changes in the human's dealt share, and whether any setup step happens after the deal? The 7 questions of `questions/pro-static.md` taken by T33: Q-STA-01, Q-STA-02, Q-STA-03, Q-STA-04, Q-STA-05, Q-AI-03, and the deal halves of Q-MAP-06 and Q-MAP-10.
- **Method**: a reading, no run of the game. The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, set `iwp-2.0-996e86c5`) were read in place in the owner's static folder, never copied (rule 18).
- **Artifact**: `iwp-2.0-996e86c5`, the unregistered build. Pro only (rule 19); the registered all-human deal stays out.
- **Outputs**: `findings/F018-pro-deal-rules.md`, status `proposed`.

## What was read

`scripts-read.json` lists the 19 scripts F018 cites (kind, number, name, handlers, line count) with the `ls_sha256` of the decompiled text from `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. Read in full: the deal handler; the start-of-movie handler (its file checks, the defaults and scores calls, the colour-letter table, and the delay helpers); the new-game handler; the centre-placement handler; the first-turn handler; the defaults handler (both handlers); the scores reader; the registration checker (all four handlers); the scores writer; the two start-of-game frame scripts; both options-screen display frames (their decompiled texts are byte-identical — one shared `ls_sha256`); the starting-armies and difficulty option buttons; both seat-toggle cast scripts; and the two battle-display scripts whose name or call matches the word "strength" (neither reads the level — cited to close the reader search). Every handler named in the list was read in full.

Terminal-only searches over the decompiled folder (nothing kept): every caller of the deal, centre-placement and first-turn handlers (one each, all in the start-of-game frame script; the centres handler has a second caller, the event frame, F015's); every script naming the deal list (the deal handler only — the list leaves no global); every script naming the starting-armies value (the deal, the defaults handler, the two display frames, the option button); every script naming the difficulty value (the deal, the defaults handler, the score writer, the two display frames, the option button, plus the movie-start handler's declaration-only `global` line and the two battle-display scripts cited above, which match the word without reading the level).

## Not read

The score (frame order beyond what the handlers' calls fix), the cast members (pictures and texts) and the 61 scripts that no cast member points at (F010). The board tables' contents are F017's; the centres' rules and the events are F015's; the turn advance and the end screens are F012's; the difficulty's absence from the AI is F016's (re-verified here at the reader level). Where an answer needs the frame order, F018 says so.

## Scripts and measurements

- `check_cited_scripts.py`: Done-when 2 of T33. Without arguments it checks that every script, name and handler F018 cites is in the E008 inventory, that `scripts-read.json` matches the inventory (name, handlers, `ls_sha256`) and that F018 cites nothing the list lacks. With `--disk` (and `IWA_STATIC` set to the static folder, outside every checkout) it hashes each listed decompiled script in place and compares it with the record, and writes `measurements/disk-check-<out>.json` (names, hashes and booleans; no path, no code).
- `check_deal_constants.py`: the rule-20 cross-check of the reading's numbers. With `IWA_STATIC` set it parses the bytecode listings of the deal handler, the first-turn handler and the centre-placement handler **in place**, and checks every constant and draw F018 names — the deal's draws and their counts (seat draw, the 8 cap redraws, the all-human fill, the dead turn draw, the shuffle, the army draw — 13 in all, with no unnamed extra), the 8 cap comparisons at 15 and their pairing with the redraws, the dealt minimums 5/9/14/16 and the all-human 11 in source order, the board total 46, the first-turn handler's 10+8 length draw, its three seat draws and its final decrement and wrap, and the centres' shuffle and slots 12/24/37 — and writes `measurements/deal-constants-<out>.json` (counts, offsets and booleans; no path, no code).
- `scripts-read.json`: the list of the scripts read, at the experiment's root.

## Append-only

After the first measurement this file is append-only. A changed design is a new experiment. A re-run writes new files beside the old ones, and the finding says which ones it cites.

## Rounds

- `deal-constants-r1.json` (round 0): the first run. Its draw regex stopped at the first close-parenthesis of the rendered argument, so the two shuffle draws were extracted as a truncated key and the two shuffle checks wrongly failed while the listings hold exactly one shuffle draw each. Kept as measured, never overwritten (rule 20); F018 does not cite it.
- `deal-constants-r1b.json` (round 1): the draw regex fixed; all 19 checks hold. **The file F018 cites.**
- `disk-check-r1.json` (round 1): the on-disk `ls_sha256` check over the 19 listed scripts, all matching the record.
