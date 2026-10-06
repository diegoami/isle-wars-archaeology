# E012 pro-cards-reading

- **Task**: T22 (#70). U32 (static first), CLAUDE.md rule 24.
- **Question**: What card rules does the decompiled Lingo of *Isle Wars Pro* contain — when a card is given, the kinds and their weights, the capture draw, the hand limit, the match and trade-in rules, the bomb and the anti-bomb — for the human's code path and the computer's? The 7 questions of `questions/pro-static.md` taken by T22: Q-BON-03, Q-BON-04, Q-BON-05, Q-BON-06, Q-BON-07, Q-BON-08, Q-BON-09.
- **Method**: a reading, no run of the game. The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, set `iwp-2.0-996e86c5`) were read in place in the owner's static folder, never copied (rule 18).
- **Artifact**: `iwp-2.0-996e86c5`, the unregistered build. Pro only (rule 19).
- **Outputs**: `findings/F014-pro-cards-rules.md`, status `proposed`.

## What was read

`scripts-read.json` lists the 38 scripts F014 cites (kind, number, name, handlers, line count) with the `ls_sha256` of the decompiled text from `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. The decompiled text is not kept anywhere in the repository (rule 18); the list carries only identity and hashes.

Read in full: the human's draw handler (`MovieScript 345`), the computer's draw handler (`MovieScript 398`), the hand-display pair (`MovieScript 344`), the human's match check (`MovieScript 366`), the computer's match check with its priority and removal (`MovieScript 397`), the removal-and-compaction pair (`MovieScript 532`), the pick handler (`BehaviorScript 526`), the trade-in and skip buttons (`CastScript 528`, `CastScript 530`), the turn-start frame's card steps (`BehaviorScript 14`; the whole frame was read in E011's round), the human's card frames (`BehaviorScript 453`, `342`, `341`, `358`), the trade-in screen's two frame scripts (`BehaviorScript 369`, `367`), the bomb-arming and bomb-return frames (`BehaviorScript 372`, `389`), the bombing-click state of the board click handler (`BehaviorScript 400`; the rest of the handler was fully read for F011/E009), the seven identical discard cast scripts (`CastScript 376` to `381` and `383`), the pass button (`CastScript 66`), the move-end routing frame (`BehaviorScript 331`), the failed-attack frame's flag clear (`BehaviorScript 97`), the two card-screen `exitFrame` handlers that clear the capture flag (`BehaviorScript 340`, `BehaviorScript 343`), the new-game reset's card half (`MovieScript 23`; read in full in E010's round) and its frame caller (`BehaviorScript 24`), and the deck literal in the movie-start handler (`MovieScript 1`; read in full in E011's round).

Read in part: the computer's placement handler (`MovieScript 333`, 903 lines) — its trade-in head and its complete bombing branch (candidate list, nine-draw victim pick, protection test, halving draw) in full; the middle country-selection scoring belongs to T27, as bounded in F013. The two dice handlers (`MovieScript 50`, `337`) at their capture-flag writes and their context (both fully read for F011/E009); the info handler (`MovieScript 75`) at its dead-seat card wipe (fully read for E010).

Bytecode comparisons (`.lasm` listings beside the decompiled text): the 34-entry deck literal in `MovieScript 1` (the same entries in the same order as the decompiled text, the bomb last); the trade-in's four written bonus values in `CastScript 528` (5, 8, 15 and the 1000 sentinel, as immediates); the wildcard cap in `MovieScript 366` (a strict greater-than two, then a store of two); the deck-minus-flag draw bound in `MovieScript 345` and `MovieScript 398`.

Terminal-only searches over the decompiled folder (nothing kept): every reader and writer of the deck list (one writer: `MovieScript 1`); every writer of a card hand (fifteen scripts, all read and listed: the two draw handlers, the seven discard cast scripts, `MovieScript 532`, `MovieScript 397`, `MovieScript 75`, `MovieScript 23`, plus the anti-bomb consumption inside `BehaviorScript 400` and `MovieScript 333`); the complete writer list of the capture flag (seven scripts: the two setters `MovieScript 50`, `MovieScript 337`, and the five clears `BehaviorScript 14`, `BehaviorScript 97`, `MovieScript 23`, `BehaviorScript 340`, `BehaviorScript 343`); the callers of both draw handlers and of both match checks (one each: `BehaviorScript 358`, `BehaviorScript 14`); and every jump to the trade-in, card, discard, draw and bombing frame labels.

## Not read

The score (frame order, which sprite carries which script), the cast members (card faces, sounds) and the 61 scripts that no cast member points at (F010). Where an answer needs the frame order, F014 says so. The trade-in's adds as income and their place in the turn belong to F013 (here only the kinds behind F013's numbers); combat and captures to F011; turn order, eliminations and the dead-seat card wipe to F012; the computer's placement and attack choices to T27.

## Scripts and measurements

- `check_cited_scripts.py`: Done-when 2 of T22. Without arguments it checks that every script, name and handler F014 cites is in the E008 inventory, that `scripts-read.json` matches the inventory (name, handlers, `ls_sha256`) and that F014 cites nothing the list lacks. With `--disk` (and `IWA_STATIC` set to the static folder, outside every checkout) it hashes each listed decompiled script in place and compares it with the record, and writes `measurements/disk-check-<run>.json` (names, hashes and booleans only; no path, no code).
- `scripts-read.json`: the list of the scripts read, at the experiment's root.
- `measurements/disk-check-r1.json`: the in-place hash check of the 36 scripts listed before the round-2 correction (36 of 36 match); kept as written.
- `measurements/disk-check-r2.json`: the re-check after `BehaviorScript 340` and `BehaviorScript 343` were added (38 of 38 match). The check's `--out r2` wrote it beside r1; nothing was overwritten.

## Append-only

After the first measurement this file is append-only. A changed design is a new experiment. A re-run writes new files beside the old ones, and the finding says which ones it cites.
