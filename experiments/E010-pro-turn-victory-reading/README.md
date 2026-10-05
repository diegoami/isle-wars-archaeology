# E010 pro-turn-victory-reading

- **Task**: T30 (#85). U32 (static first), CLAUDE.md rule 24.
- **Question**: What turn order, victory, end-of-game and concession rules does the decompiled Lingo of *Isle Wars Pro* contain, for the human's code path and the computer's? The 21 questions of `questions/pro-static.md` taken by T30: Q-TRN-01, Q-TRN-02, Q-TRN-04, Q-VIC-01 to Q-VIC-14, Q-SUR-01, Q-SUR-03, Q-SUR-04, Q-SUR-05.
- **Method**: a reading, no run of the game. The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, set `iwp-2.0-996e86c5`) were read in place in the owner's static folder, never copied (rule 18).
- **Artifact**: `iwp-2.0-996e86c5`, the unregistered build. Pro only (rule 19).
- **Outputs**: `findings/F012-pro-turn-victory-rules.md`, status `proposed`.

## What was read

`scripts-read.json` lists the 32 scripts F012 cites (kind, number, name, handlers, line count) with the `ls_sha256` of the decompiled text from `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. All of the handlers named in the list were read in full. The decompiled text is not kept anywhere in the repository (rule 18); the list carries only identity and hashes.

Terminal-only searches over the decompiled folder (nothing kept): every place that sets or clears the game-over global; every user of the turn counter; every user of the concession, quit-early, stop and do-not-score globals; the callers of the first-turn draw; and every jump to the between-turn, begin, start, event, concede, game-over and scores frames.

## Not read

The score (frame order, which sprite carries which button), the cast members (pictures and texts) and the 61 scripts that no cast member points at (F010). Where an answer needs the frame order, F012 says so. The events themselves, the cards, the bombs and the computer's choices belong to T23, T22 and T27.

## Scripts and measurements

- `check_cited_scripts.py`: Done-when 2 of T30. Without arguments it checks that every script, name and handler F012 cites is in the E008 inventory, that `scripts-read.json` matches the inventory (name, handlers, `ls_sha256`) and that F012 cites nothing the list lacks. With `--disk` (and `IWA_STATIC` set to the static folder, outside every checkout) it hashes each listed decompiled script in place and compares it with the record, and writes `measurements/disk-check-<run>.json` (names, hashes and booleans; no path, no code).
- `scripts-read.json`: the list of the scripts read, at the experiment's root.

## Append-only

After the first measurement this file is append-only. A changed design is a new experiment. A re-run writes new files beside the old ones, and the finding says which ones it cites.
