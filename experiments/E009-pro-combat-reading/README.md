# E009 pro-combat-reading

- **Task**: T20 (#68). U32 (static first), CLAUDE.md rule 24.
- **Question**: What combat, movement and capture rules does the decompiled Lingo of *Isle Wars Pro* contain, for the human's code path and the computer's? The 17 questions of `questions/pro-static.md` marked T20: Q-MOV-01 to Q-MOV-03, Q-CMB-01 to Q-CMB-12, Q-OWN-01, Q-SET-04.
- **Method**: a reading, no run of the game. The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, set `iwp-2.0-996e86c5`) were read in place in the owner's static folder, never copied (rule 18). Their bytecode listings were used as a second view of the same tool's output.
- **Artifact**: `iwp-2.0-996e86c5`, the unregistered build. Pro only (rule 19).
- **Outputs**: `findings/F011-pro-combat-rules.md`, status `proposed`.

## What was read

`scripts-read.json` lists the 46 scripts F011 cites (kind, number, name, handlers, line count) with the `ls_sha256` of the decompiled text from `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. A handful more were opened to settle an answer and are not cited (the board set-up `MovieScript 5`, the file handlers, the shared bottom buttons, `BehaviorScript 4`, 11 and 13). All of the handlers named in the list were read in full. The decompiled text is not kept anywhere in the repository (rule 18); the list carries only identity and hashes. The bytecode listings of `RollDice`, `ComputerRollDice` and the battle frame script were compared with the text at each comparison operator and draw.

Terminal-only searches over the decompiled folder (nothing kept): the callers of the failure handler and of the two dice handlers; the uses of the level global; the places that set the pace flag; the places that jump to the move, capture and failure frames.

## Not read

The score (frame order, which sprite carries which button), the cast members (pictures and texts) and the 61 scripts that no cast member points at (F010). Where an answer needs the frame order, F011 says so.

## Scripts and measurements

- `check_cited_scripts.py`: Done-when 2 of T20. Without arguments it checks that every script, name and handler F011 cites is in the E008 inventory, that `scripts-read.json` matches the inventory (name, handlers, `ls_sha256`) and that F011 cites nothing the list lacks. With `--disk` (and `IWA_STATIC` set to the static folder, outside every checkout) it hashes each listed decompiled script in place and compares it with the record, and writes `measurements/disk-check-<run>.json` (names, hashes and booleans; no path, no code).
- `win_probability.py`: an exact calculation (a model, not a measurement) of the capture chance and the armies lost in one human attack, from the rule F011 reads, assuming uniform independent dice. Output `measurements/win-probability-r1.json`. A re-run takes a new run id and writes a new file.
- `scripts-read.json`: the list of the scripts read, at the experiment's root.

## Append-only

After the first measurement this file is append-only. A changed design is a new experiment. A re-run writes new files beside the old ones, and the finding says which ones it cites.
