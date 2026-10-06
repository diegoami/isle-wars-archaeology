# E013 pro-centres-hazards-reading

- **Task**: T23 (#71). U32 (static first), CLAUDE.md rule 24.
- **Question**: What production-centre and random-event (hazard) rules does the decompiled Lingo of *Isle Wars Pro* contain, for the human's code path and the computer's? The 15 questions of `questions/pro-static.md` taken by T23: Q-SET-03, Q-TRN-03, Q-CEN-01 to Q-CEN-05, Q-HAZ-01 to Q-HAZ-08.
- **Method**: a reading, no run of the game. The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, set `iwp-2.0-996e86c5`) were read in place in the owner's static folder, never copied (rule 18).
- **Artifact**: `iwp-2.0-996e86c5`, the unregistered build. Pro only (rule 19).
- **Outputs**: `findings/F015-pro-centres-hazards-rules.md`, status `proposed`.

## What was read

`scripts-read.json` lists the 18 scripts F015 cites (kind, number, name, handlers, line count) with the `ls_sha256` of the decompiled text from `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. All of the handlers named in the list were read in full, except the three computer handlers (`MovieScript 333`, `337`, `338`), of which only the lines that read the centre list, with their surrounding branches, were read — their scoring as a whole is T27's. The decompiled text is not kept anywhere in the repository (rule 18); the list carries only identity and hashes.

Bytecode comparisons, made against the `.lasm` listings beside the decompiled texts: the flood handler's window sums, struck-block indices, board bound, integer division, floor and bounded redraw; the dispatch frame's draw ranges, draw-before-override order under the fourth setting, strict 38- and 32-country gates, counter gate and event outcome; the rebellion's thresholds, attempt count and ownership store; the event frame's slot draw with its repeat redraw and the move branch's repaint order.

Terminal-only searches over the decompiled folder (nothing kept): every mention of the centre list (six scripts — no human-path reader); every caller of the four event routines and the placement routine; every mention of the event table, the previous-slot global and the turn counter; and every mention of the two marker colours.

## Not read

The score (frame order, including the counter-reset frame's exact position on the event path), the cast members (marker colours, button pictures, sounds), the computer handlers' scoring as a whole (T27) and the 61 scripts that no cast member points at (F010). Where an answer needs the frame order, F015 says so. The income formula, combat, cards, the deal and the turn order belong to F013, F011, T22, T18 and F012; F015 takes only the centre absence from the income handler.

## Scripts and measurements

- `check_cited_scripts.py`: Done-when 2 of T23. Without arguments it checks that every script, name and handler F015 cites is in the E008 inventory, that `scripts-read.json` matches the inventory (name, handlers, `ls_sha256`) and that F015 cites nothing the list lacks. With `--disk` (and `IWA_STATIC` set to the static folder, outside every checkout) it hashes each listed decompiled script in place and compares it with the record, and writes `measurements/disk-check-<run>.json` (names, hashes and booleans; no path, no code).
- `scripts-read.json`: the list of the scripts read, at the experiment's root.

## Append-only

After the first measurement this file is append-only. A changed design is a new experiment. A re-run writes new files beside the old ones, and the finding says which ones it cites.
