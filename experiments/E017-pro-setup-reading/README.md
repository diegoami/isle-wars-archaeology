# E017 pro-setup-reading

- **Task**: T34 (#98). U32 (static first), CLAUDE.md rule 24.
- **Question**: What surrounds the rules of *Isle Wars Pro* as the decompiled Lingo holds them: the options screen and each option's choices and default (Q-SET-01), the registration gates the unregistered build shows (Q-SET-02), save/restore (Q-SET-05), export/import (Q-SET-06), the file layouts and version numbers (Q-SET-07), seat counts (Q-PLY-01), all-AI and hot-seat (Q-PLY-02), the default configuration (Q-PLY-03), and randomness: seed (Q-RND-01), replay (Q-RND-02), one stream and its seeding (Q-RND-03).
- **Method**: a reading, no run of the game. The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`, set `iwp-2.0-996e86c5`) were read in place in the owner's static folder, never copied (rule 18).
- **Artifact**: `iwp-2.0-996e86c5`, the unregistered build. Pro only (rule 19); the registered build stays out.
- **Outputs**: `findings/F019-pro-setup-rules.md`, status `proposed`.

## What was read

`scripts-read.json` lists the 47 scripts F019 cites (kind, number, name, handlers, line count) with the `ls_sha256` of the decompiled text from `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. Read in full: the movie-start handler (its file-presence scan and creations, the anti-tamper name check, and the delay helpers); the deal handler (its random call sites only — the deal is F018's); the two dice handlers; the computer's placement handler (its two speed-reading animation loops); the info rebuild; the bottom-menu rollover handler; the scores writer; the defaults handler (both handlers); the scores reader; the registration checker (all four handlers); the registration entry handler (both key handlers) and its trigger (the arming frame and the key watcher); both options-screen display frames (byte-identical texts — one shared `ls_sha256`); the four option buttons; both seat toggles; both sound toggles; the options save, play and return buttons; the end-of-game scores screen (the writer's only caller, and the cap); the scores screen, its cap notice and its rollover handler (the reset button's flag-keyed hover); the title screen's registration-line frame; the elimination prompt; the game-started flag's setter and clearers; the new-game button and the quit/exit buttons; the scores reset button; and the publisher screen's three buttons. Every handler named in the list was read in full, and every match of the five censuses (below) was read and classified.

## Searches

`measurements/searches-r1.json` records, as names, counts and booleans, the whole-corpus searches F019's absence claims rest on, each re-runnable by a terminal search over the run's folder: the seed search (all 213 scripts, case-insensitive, for the seed word and Director's random-seed property name — 0 matches); the random-value census (91 calls in 17 scripts, counted per script); the file-call census (6 scripts, each accounted for by one of the three files); the reader censuses for the speed, starting-armies, event-frequency and seat-table values; and the menu walk (every button handler reachable from the bottom menu and the screens it opens). The search terms are described in words; no decompiled line or identifier is kept (rule 18, and the T33 discipline that no rendered source text appears in tooling or records).

## Not read

The score (frame order, which sprite carries which script — the options screen's visual layout), the cast members (pictures and texts), and the 61 scripts that no cast member points at (F010) — the gap F019's absence claims name. The board tables (F017), the deal (F018), the computer's choices (F016), the events (F015, T23), the combat and card rules (F011 to F014). Where an answer needs the frame order, F019 says so.

## Scripts and measurements

- `check_cited_scripts.py`: Done-when 2 of T34 (a copy of E010's check, adapted to F019 and E017). Without arguments it checks that every script, name and handler F019 cites is in the E008 inventory, that `scripts-read.json` matches the inventory (name, handlers, `ls_sha256`) and that F019 cites nothing the list lacks. With `--disk` (and `IWA_STATIC` set to the static folder, outside every checkout) it hashes each listed decompiled script in place and compares it with the record, and writes `measurements/disk-check-<out>.json` (names, hashes and booleans; no path, no code).
- `scripts-read.json`: the list of the scripts read, at the experiment's root.
- `measurements/searches-r1.json`: the search record above.

## Append-only

After the first measurement this file is append-only. A changed design is a new experiment. A re-run writes new files beside the old ones, and the finding says which ones it cites.

## Rounds

- `searches-r1.json` (round 1): the first and only search run; F019 cites it.
- `disk-check-r1.json` (round 1): the on-disk `ls_sha256` check over the first 43 listed scripts, all matching the record; kept unmodified after the list grew.
- `disk-check-r1b.json` (round 1): the same check over all 47 listed scripts, all matching. **The file F019 cites.**
