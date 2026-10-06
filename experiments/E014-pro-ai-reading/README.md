# E014 pro-ai-reading

- **Task**: T27 (#79). U32 (static first), CLAUDE.md rule 24.
- **Question**: How does the decompiled Lingo of *Isle Wars Pro* make the computer opponent decide — where it places, when and where it attacks, how it moves, how it plays cards, and what the difficulty setting changes? The 5 questions of `questions/pro-static.md` taken by T27: Q-AI-01, Q-AI-02, Q-AI-04, Q-AI-05, Q-AI-06, plus the difficulty's effect in any of it (Q-AI-03's sources re-read at their boundaries; the deal itself is T18's).
- **Method**: a reading, no run of the game. The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, set `iwp-2.0-996e86c5`) were read in place in the owner's static folder, never copied (rule 18).
- **Artifact**: `iwp-2.0-996e86c5`, the unregistered build. Pro only (rule 19).
- **Outputs**: `findings/F016-pro-ai-rules.md`, status `proposed`.

## What was read

`scripts-read.json` lists the 21 scripts F016 cites (kind, number, name, handlers, line count) with the `ls_sha256` of the decompiled text from `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. The decompiled text is not kept anywhere in the repository (rule 18); the list carries only identity and hashes.

Read in full, in order: the computer's placement handler (`MovieScript 333`, all 903 lines — the trade-in head, the bomb branch, the island-share ranking, the candidate scoring, the island-defence branches, the production-centre branch, the seed loop and the remainder splits); the attack-candidate handler (`MovieScript 334`), the candidate-list handler (`MovieScript 335`), the attack picker (`MovieScript 336`), the computer's dice handler (`MovieScript 337`, including the capture-split cascade), the human's dice handler (`MovieScript 50`, for the fairness comparison), the computer's move (`MovieScript 338`), the computer's card-match check (`MovieScript 397`), the computer's draw (`MovieScript 398`), the computer's turn frame (`BehaviorScript 14`), the movie-start tables (`MovieScript 1`, the board, island, key-country and per-country island tables), the deal handler at its strength branches (`MovieScript 5`), the info rebuild at its fast-forward flag write (`MovieScript 75`), the defaults handler (`MovieScript 458`, both handlers), the score writer at its per-level branches (`MovieScript 455`), the strength option button (`BehaviorScript 498`), the two options-screen display frames (`BehaviorScript 457` and `BehaviorScript 479`, both `exitFrame`), the speed option button (`BehaviorScript 500`) and the elimination prompt (`BehaviorScript 506`).

Bytecode comparisons (`.lasm` listings beside the decompiled text): the turn frame's round number (`random(4) + 1`, the additions of 1, 3 and 4 as immediates, the `SPD = 1` test before the 4, `random(22)`, the forcing of 8 above 18 countries, and `random(3) + 1` under 8 countries), and the placement handler's draws (`random(8)`, `random(14)`, `random(10)`, `random(4) + 5`, `random(2)`, `random(3)` all present as drawn in the listing).

Terminal-only searches over the decompiled folder (nothing kept): every writer of `BestIsland`, `FinalBest` and `TPosC` (only the placement handler writes the first two; the candidate-list handler aliases the seat's list into the third); every writer of `SPD` (the start, deal, reset and end-frame paths set 0; one writer sets 1: the info rebuild, when no human seat remains and the quit flag is clear); every reader of `strength` (the option button `BehaviorScript 498`, the two options-screen frames `BehaviorScript 457` and `BehaviorScript 479`, the defaults handler, the score writer and the deal handler — no AI handler); every caller of the six computer handlers (one caller each, all in the turn frame or the attack chain); the `speed` writers (the speed option and the defaults, never the AI).

## Not read

The score (frame order, which sprite carries which script), the cast members, and the 61 scripts that no cast member points at (F010). The human's placement, combat and card paths (F011 to F014); the deal's full arithmetic (T18); the centre events (T23). Where an answer needs the frame order, F016 says so.

## Scripts and measurements

- `check_cited_scripts.py`: Done-when 2 of T27. Without arguments it checks that every script, name and handler F016 cites is in the E008 inventory, that `scripts-read.json` matches the inventory (name, handlers, `ls_sha256`) and that F016 cites nothing the list lacks. With `--disk` (and `IWA_STATIC` set to the static folder, outside every checkout) it hashes each listed decompiled script in place and compares it with the record, and writes `measurements/disk-check-<run>.json` (names, hashes and booleans only; no path, no code).
- `scripts-read.json`: the list of the scripts read, at the experiment's root.
- `measurements/disk-check-r1.json`: the in-place hash check of the 19 scripts first listed (round 1); `measurements/disk-check-r2.json`: the re-check of all 21 listed scripts after `BehaviorScript 457` and `BehaviorScript 479` were added. A re-run writes a new file; the old one is kept.

## Append-only

After the first measurement this file is append-only. A changed design is a new experiment. A re-run writes new files beside the old ones, and the finding says which ones it cites.
