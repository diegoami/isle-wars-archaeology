# E015 pro-board-reading

- **Task**: T32 (#96). U32 (static first), CLAUDE.md rule 24.
- **Question**: What board and adjacency structure does the decompiled Lingo of *Isle Wars Pro* hold — how many territories, which islands hold which, which territories border which and in which directions, whether adjacency distinguishes land from water crossings, and whether the board or its layout varies between games? The 12 questions of `questions/pro-static.md` taken by T32: Q-MAP-02, Q-MAP-03, Q-MAP-04, Q-MAP-05, Q-MAP-06 (board half), Q-MAP-07, Q-MAP-08, Q-MAP-09, Q-MAP-10 (board half), Q-MAP-11, Q-MAP-12, Q-MAP-14.
- **Method**: a reading, no run of the game. The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, set `iwp-2.0-996e86c5`) were read in place in the owner's static folder, never copied (rule 18).
- **Artifact**: `iwp-2.0-996e86c5`, the unregistered build. Pro only (rule 19).
- **Outputs**: `findings/F017-pro-board-rules.md`, status `proposed`.

## What was read

`scripts-read.json` lists the 13 scripts F017 cites (kind, number, name, handlers, line count) with the `ls_sha256` of the decompiled text from `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. Read in full: the movie-start handler (every table it builds and every helper it holds), the income handler, the deal handler, the new-game handler, the front-line candidate handler, the board click handler (all nine click states), and both options-screen display frames. Read at their table-feeding sections (their full behaviour is F016's): the computer's placement, attack builder, attack picker, dice and move handlers. All of the handlers named in the list were read at the passages where the board tables enter.

Terminal-only searches over the decompiled folder (nothing kept): every assignment to each board table (the movie-start handler only); every script naming the border tables (the 8 listed in F017's Q-MAP-04); every naming of the position tables (display placement only); the words water, sea, ocean and land (none found anywhere — `land` only inside `island`).

## Not read

The score (frame order, which sprite carries which button), the cast members (pictures and texts) and the 61 scripts that no cast member points at (F010). Where an answer needs the frame order, F017 says so. The deal's arithmetic, the computer's choices, the cards, the centres and the hazards belong to T33, F016, T22, T23.

## Scripts and measurements

- `check_cited_scripts.py`: Done-when 2 of T32. Without arguments it checks that every script, name and handler F017 cites is in the E008 inventory, that `scripts-read.json` matches the inventory (name, handlers, `ls_sha256`) and that F017 cites nothing the list lacks. With `--disk` (and `IWA_STATIC` set to the static folder, outside every checkout) it hashes each listed decompiled script in place and compares it with the record, and writes `measurements/disk-check-<run>.json` (names, hashes and booleans; no path, no code).
- `tabulate_board.py`: parses the board tables out of the decompiled start handler **in place** (nothing copied), tabulates them, and checks the table properties (counts, entry ranges, no self or duplicate neighbour, symmetry, connectivity, the island partition, the key lists, distinct positions). It writes `measurements/board-tabulation-<tag>.json` — the checked output the finding cites, never a line of the decompiled text.
- `scripts-read.json`: the list of the scripts read, at the experiment's root.

## Append-only

After the first measurement this file is append-only. A changed design is a new experiment. A re-run writes new files beside the old ones, and the finding says which ones it cites.

## Rounds

- `board-tabulation-r1.json` (round 0): the first run. Its symmetry comparison held a bug (the country key taken from the dict iteration as text, so every reverse lookup missed) and the check wrongly failed while all 160 directed border entries do pair up. Kept as measured, never overwritten (rule 20); F017 does not cite it.
- `board-tabulation-r1b.json` (round 1): the comparison fixed; all 28 checks hold. Superseded within the hour by the bytecode cross-check below; F017 does not cite it.
- `board-tabulation-r1c.json` (round 2): a bytecode cross-check added (every board table entry read back from the push instructions of the `.lasm` listing, in order). Its push regex missed the listing's rendered zero arguments, so four key lists and the three sparse border tables compared short. Kept; F017 does not cite it.
- `board-tabulation-r1d.json` (round 3): the push regex fixed; all 30 checks hold, and all 27 board tables match the bytecode listing entry by entry. Superseded by r1e; F017 no longer cites it.
- `board-tabulation-r1e.json` (round 4, T32 rework round 2): the `no_self_neighbour` predicate fixed (it compared a text country key with integer neighbours and always passed; R4) and the detector exercised against an injected self-edge; the output now also holds all 27 board tables as plain number lists, including the coordinate values and the zero-padded per-island key lists (R5). All 31 checks hold and all 27 tables match the bytecode listing. **The file F017 cites.**
- `disk-check-r1e.json` (round 4, T32 rework round 2): the on-disk `ls_sha256` check over the 13 cited scripts, all matching the record; the earlier `disk-check-r1.json` is kept beside it.
