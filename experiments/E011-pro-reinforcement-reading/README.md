# E011 pro-reinforcement-reading

- **Task**: T21 (#69). U32 (static first), CLAUDE.md rule 24.
- **Question**: What reinforcement, income and island-bonus rules does the decompiled Lingo of *Isle Wars Pro* contain, for the human's code path and the computer's? The 7 questions of `questions/pro-static.md` taken by T21: Q-MAP-13, Q-REI-01, Q-REI-02, Q-REI-03, Q-REI-04, Q-BON-01, Q-BON-02.
- **Method**: a reading, no run of the game. The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, set `iwp-2.0-996e86c5`) were read in place in the owner's static folder, never copied (rule 18).
- **Artifact**: `iwp-2.0-996e86c5`, the unregistered build. Pro only (rule 19).
- **Outputs**: `findings/F013-pro-reinforcement-rules.md`, status `proposed`.

## What was read

`scripts-read.json` lists the 24 scripts F013 cites (kind, number, name, handlers, line count) with the `ls_sha256` of the decompiled text from `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. The decompiled text is not kept anywhere in the repository (rule 18); the list carries only identity and hashes.

Read in full: the income handler (`MovieScript 6`), the board and island tables (`MovieScript 1`, `startMovie` and its delay helpers), the turn-advance (`MovieScript 10`), the turn-start frame with the human/computer branch (`BehaviorScript 14`), the placement frames (`BehaviorScript 13`, `BehaviorScript 11`), the board click handler's placement and bomb states (`BehaviorScript 400`), the placement buttons (`CastScript 83`, `85`, `87`, `89`), the capture move-in confirm (`CastScript 96`), the move confirm (`CastScript 332`), the move counter frame (`BehaviorScript 100`), the human card-match check (`MovieScript 366`), the human trade-in and its skip button (`CastScript 528`, `CastScript 530`), the bomb arming and bomb-to-placement frames (`BehaviorScript 372`, `BehaviorScript 389`), the computer's card-match check (`MovieScript 397`) and the computer's front-line list (`MovieScript 335`).

Read in part: the computer's placement handler (`MovieScript 333`, 903 lines) — its card trade-in head (the COMPBONUS add, the doubling, the bomb branch), its conquest tests and message, and its pool-consumption tail were read in full; the middle country-selection scoring was skimmed only, and belongs to T27. The capture frames' scratch reuse of the pool global (`BehaviorScript 60`, `MovieScript 337`) was read at the write line and its context; both scripts were read in full for F011/E009.

Bytecode comparisons (`.lasm` listings beside the decompiled text): `MovieScript 6`'s division of the country count (an integer `div`) and the order of the minimum test and the bonus add (a strict less-than, then the add) were confirmed in the bytecode.

Terminal-only searches over the decompiled folder (nothing kept): every caller of the income handler (one: `BehaviorScript 14`); every writer of the pool global `placearmies` (nine scripts, all accounted for: income, trade-in, placement button, computer placement, and the battle/move scratch uses); every reader of `islandsowned` and of `NewArmies`; every setter of the island tables (only `startMovie`); the setters of `opp` (seat toggles and the defaults handler); and every reference to the `PlaceA`, `PlaceD`, `SELECTMATCH` and `BOMB` frame labels.

## Not read

The score (frame order, which sprite carries which button), the cast members (pictures and texts) and the 61 scripts that no cast member points at (F010). Where an answer needs the frame order, F013 says so. The card kinds, deck and draws belong to T22 (here only what a trade-in adds to the pool); the centre event handlers to T23; the computer's placement scoring to T27.

## Scripts and measurements

- `check_cited_scripts.py`: Done-when 2 of T21. Without arguments it checks that every script, name and handler F013 cites is in the E008 inventory, that `scripts-read.json` matches the inventory (name, handlers, `ls_sha256`) and that F013 cites nothing the list lacks. With `--disk` (and `IWA_STATIC` set to the static folder, outside every checkout) it hashes each listed decompiled script in place and compares it with the record, and writes `measurements/disk-check-<run>.json` (names, hashes and booleans only; no path, no code).
- `scripts-read.json`: the list of the scripts read, at the experiment's root.
- `measurements/disk-check-r1.json`: the in-place hash check of all 24 listed scripts against the record (24 of 24 match).

## Append-only

After the first measurement this file is append-only. A changed design is a new experiment. A re-run writes new files beside the old ones, and the finding says which ones it cites.
