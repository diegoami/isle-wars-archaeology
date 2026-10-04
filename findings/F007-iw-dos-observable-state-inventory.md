# F007 DOS Isle Wars shows its game state on the screen and writes three small text files: `ISLEWAR.DFT` (level and starting armies), `ISLEWAR.SCR` (won and lost per level) and, after Save, `ISLEWAR.SAV` (the whole board); it saves and loads one game

- **Status**: proposed
- **Question**: Where can the state of DOS *Isle Wars* (the shareware 3.1 archive) be seen, at what intervention level and at what cost: on the screen, in the files the game writes, in a savestate? Which files does it write, in what format, and which action moves which byte? Does the game save and load a game, and does a save change when the board changes (Q-SET-05)? Which screens can the unattended cycle reach? (E005, task T14, W4b; feeds the W5b driver and the research questions.)
- **Tests claims**: none (a source inventory; it proposes representation rows D1 to D16 below and makes no claim about a game rule)
- **Experiment and runs**: E005; runs E005-r0001 to E005-r0026, all in `runs/E005/`. Two of them aborted (r0016, r0017) and stay; the table in "Method" says why.
- **Artifact**: set `iw-dos-3.1-30121376`, variant none. No run changed a file of the set: every file the game wrote is a new file of the run copy, removed by the reset (`setup/iw-dos/iw-dos-runtime.sh` printed `ready` and `register_artifact.py check --strict` exited 0 after all runs: `measurements/done-when/`).
- **Max intervention**: I2 (the `savestate` arm, r0022, saves a DOSBox-X savestate and classifies its members; it is never restored). Every other run is I1 (screenshots; files the game wrote read after the fact, which is I0) with no input but the mouse and, for the game's own exit, two keys of its shareware notices.
- **Tier reached**: V2 (the original, headless, under DOSBox-X; no real DOS hardware or other emulator, so no V3)
- **Confidence**: for each parsed field, an action that moves it and two runs that agree with each other (the level and starting-armies fields of `ISLEWAR.DFT`: 2 runs each; the lost field of `ISLEWAR.SCR`: 2 runs at Easy and 2 at Normal; the owner codes, the armies, the production centres and the card counts of `ISLEWAR.SAV`: 8 saves in 6 runs, two of them with a known move between them). Fields that were not varied are listed as not decoded. One machine (WSL2), one DOSBox-X build, one day. The owner mapping rests on a reading of the screen by a script, checked against the game's own scoreboard (see "Alternatives considered").

## Answer

- **State is seen on the screen; three files carry parts of it.** The owner and army count of each of the 46 countries, whose turn it is, the phase, the cards, the result of an attack and the end of a game are all on the screen (screenshots of r0011 and r0012: one human turn, an attack, the computer turns). Three files are written, all comma-separated decimal text with CRLF line ends: `ISLEWAR.SCR` at every launch (26 of 26 runs here, 12 of 12 in F005), `ISLEWAR.DFT` after Set level or Default, and `ISLEWAR.SAV` after Save. `ISLEWAR.DAT` (shipped) was never written in any run.
- **`ISLEWAR.DFT` is the level and the starting armies.** After Set level it is one line ` L , A , 2 ` (spaces around the commas and at both ends, CRLF). The first field is the level (Easy 1, Normal 2, Hard 3, Hardest 4) and the second the starting armies chosen (1, 3, 6 or 10); the third was 2 in every run and is not decoded (rows D1 to D4). Default writes three lines `1`, `3`, `2` (9 bytes, r0001, r0002). After a conceded game, Another game and Load saved game the file is rewritten as three lines ` 1 `, ` 1 `, ` 2 ` (r0018, r0019).
- **`ISLEWAR.SCR` is the scoreboard.** Four lines, one per level, each `won,lost`: at launch `0,0` four times (20 bytes). Quit and Yes (conceding) at Easy makes line 1 `0, 1` (r0014, r0015); at Normal line 2 (r0023, r0024). The scoreboard screen shows the same figures (r0013, r0014). The loss is in the file by the time the scoreboard is on the screen (the next `files` step after the concession). A win was not produced, so the first number is not shown to be the wins (rows D7, D8).
- **The game saves and loads one game (Q-SET-05).** Save (top right, at the turn start, before any army is placed) shows `GAME SAVED` and writes `ISLEWAR.SAV` in the game folder: 523 to 531 bytes. Load saved game on the option box restores it: after Save, concede, Another game and Load saved game, the owner of every one of the 46 countries equals the saved board (r0018, r0019: 46 of 46) and the human turn is the saved one. With no save it says `NO SAVED GAME FOUND` and stays on the option box (r0020). Only one name was seen (`ISLEWAR.SAV`), as the manual says one game is kept. A save taken at the next turn changes (r0011, r0012): the country conquered at turn 1 changes owner and army count in both, and the card counts change (rows D9 to D16).
- **What the save holds**, from the eight saves (rows D9 to D16): the number of production centres and their country numbers; the level and the starting armies; the owner of each country as a code (9 Blue, 4 Red, 2 Green, 8 Brown; 46 of 46 on all 8 saves against the screen); the armies of each country; the cards each colour holds (a count per colour and one number per card type). Not decoded: the two constants `2` and `0` after the starting armies, and what the card-type numbers (2, 3, 7) mean.
- **No Help screen exists.** The game's text is its prompts and messages; they are listed in the screens table and the new ones are in the knowledge map. The Sound and Speed buttons change state on screen (`OFF..`, `ON...`, a Faster/Slower panel with the value) and neither writes a file (r0013: `ISLEWAR.DFT` unchanged after Speed was set to 1).
- **The game ends by itself.** Quit, Yes, Another game No, then the shareware notice; the key `c` leads to the registration notice; the key `e` (its `<E>xit To Dos`) ends the game and DOSBox-X ends 2.25 s later (r0021: observation "DOSBox-X ended by itself"). `u` and `r` (Upgrade, Registration) were never pressed.
- **The start of a game is not unique to a run.** Of the 25 runs that started a game, 20 different start pictures came up; the same pictures came up again for the same inputs in r0001 and r0002 (Default), r0004, r0021 and r0022 (Easy, 1 army), r0011 and r0015 (Easy), and r0016 and r0023 (Normal); the production centres of r0018 and r0025 (Easy and Normal) and of r0019 and r0026 (Easy and Normal) are the same lists. Why is unknown, and nothing here tests it.
- **Cost.** DOSBox-X's window is up 1.62 to 1.75 s after launch and the option box 16.90 to 17.12 s after launch (26 of 26 runs here; F005 has 16.92 to 17.07 s in its control runs). From the click that starts a game to the first human turn: 1.07 to 81.47 s (the computer's turns come first; 81.47 s was Hardest with 10 armies, r0010). A run takes 18 to 119 s. One reading of the board from a screenshot (owners and the borders between countries) takes 0.08 to 0.09 s in pure Python; the owners alone take under a millisecond (`measurements/analysis/timings.tsv`).

## Source table

Cheapest first. Level is the intervention level of the reading (`vocabulary/interventions.md` at the pin). Cost is what a reading needs, from the runs' own timings. "Runs" are the records that show it.

| # | Source | State it shows | Class | Level | Cost | Runs |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | DOSBox-X's process (exit status, whether it is running) | whether the game has ended: it ends DOSBox-X by itself after its own exit keys | directly-observable | I0 | milliseconds, in any run | r0021 (ended by itself 2.25 s after `e`); every other run: stopped by the cycle |
| 2 | Screen regions (one screenshot each, or the pixels of one) | everything a player sees: the owner and armies of each country; the scoreboard panel (a figure per colour, a cards figure `C>`, an arrow on the colour whose turn it is); the prompt panel (`PLACE 5 ARMIES`, `BLUE : 16 COUNTRIES`, `BLUE ARMY GETS: 5`, the attack and move-in panels with `5 AGAINST 0`, `GAME SAVED`, `NO SAVED GAME FOUND`, `CLICK TO CONTINUE`); the buttons (Scores, Sound `OFF..`/`ON...`, Speed with its value, Save, Quit); the scoreboard screen; the production centres (a `*` under a country's number) | directly-observable | I1 | 0.15 s per capture; the screen must be quiet first: 1.07 to 81.47 s of computer turns before the first human turn; a script that reads the owners from the pixels takes under 1 ms and the borders 0.08 s | r0011, r0012 (a whole turn); r0013 (Scores, Sound, Speed); r0014, r0015 (concede); r0020 (no save) |
| 3 | `ISLEWAR.SCR` (run copy, read after the run or after a step) | the scoreboard: lost games per level (won not varied) | parsed | I0 | exists from the launch; the loss is in the file once the concession's scoreboard is shown: about 45 s (set level, start, wait for the first human turn, Quit, Yes) | r0014, r0015 (Easy), r0023, r0024 (Normal); the 20-byte launch value in all 26 |
| 4 | `ISLEWAR.DFT` (run copy) | the saved options: level and starting armies decoded; the third field unvaried | parsed | I0 | written by the time the board appears after the last choice, about 20 s from launch (Set level, two clicks); Default alone writes it in 17 s plus one click | r0003 to r0010 (Set level), r0001, r0002 (Default), r0018, r0019 (after Another game and Load) |
| 5 | `ISLEWAR.SAV` (run copy) | the whole board at a turn start: production centres, level, starting armies, owner and armies of each country, the cards | parsed | I0 | one click on Save at a turn start (written by the next `files` step, under a second later); about 45 s a run to the first human turn; a save at turn 2 needs a whole turn, about 100 s | r0011, r0012 (two saves each), r0018, r0019, r0025, r0026 |
| 6 | `ISLEWAR.DAT` (shipped; never written) | unknown: comma-separated decimal text (F004); no run varies it, so nothing about it is decoded here | parsed (shipped bytes read, not decoded) | I0 | not measured | r0001 to r0026: the file equals the set's in every run (`changes.log` adds only the three files above) |
| 7 | Savestate members, DOSBox-X's F12+S (the file is never kept) | DOSBox-X's own components: 26 members (CPU, Vga, Mouse, Dos, Pic, Memory and others); the game's state is in Memory (182,098 bytes, inflating to 17,055,864) and perhaps in Vga | invasive | I2 | 0.4 s for the save, about 38 s a run | r0022 |
| 8 | Memory read from a savestate (I1 over an I2 capture) | the game's memory, whole; no game field was looked for (W5b) | invasive | I2 | not performed beyond classifying the members: F005 showed the images differ between identical starts | r0022; F005 r0008, r0009 |
| 9 | The save written by the game after Save, as a way to restore a position | a position to start an experiment from | invasive if edited, I3; as written by the game it is source 5 | I3 for a crafted or edited save | not performed (out of scope) | none |

Sources 1 to 5 each need no more than the cycle's own inputs. Where the same state exists in Pro, F003's inventory is the comparison: Pro's screen is the one source there too, and its files hold options and a scoreboard (`Isledft.dat`, `Islepro.skr`: scope Pro only). DOS also writes a save and loads it (Pro: none found, F003). The comparison is a statement about each artifact, not a claim for both (rule 19).

## Screens

Cheapest path first; every run that reached a screen is named, with one screenshot asset (release `E005`, see the manifests). `r0011` and `r0012` are the two runs of the `turn` arm.

| Screen | Reached | Runs and a screenshot |
| --- | --- | --- |
| The option box (Set level, Default, Load saved game) | reached | every run; `ce3d9ebda664b064-before.png` (r0001) |
| Set level, with every choice | reached | the dialog lists Easy, Normal, Hard, Hardest (`79ac1e16f5cc5df2-select-level.png`, r0003); each was chosen: Easy r0003, r0004, r0007, r0008; Normal r0005, r0006; Hard r0009; Hardest r0010 |
| Starting armies, with every choice | reached | 1, 3, 6, 10 (`4d03e6ad09594904-starting-armies.png`, r0003); each was chosen: 1 r0003 to r0006, 3 r0007, r0008, 6 r0009, 10 r0010 |
| Default | reached | r0001, r0002; the board with `ANYKEY TO START GAME` (`65b2d448c8bb7c88-board-before-start.png`) |
| Load saved game | reached | no save: `NO SAVED GAME FOUND` (`5fb90f1838cb0117-no-saved-game.png`, r0020); with a save: the saved board (`7b7e2b60d3b3fb50-after-load.png`, r0018; r0019) |
| The setup | reached | there is none beyond Set level and the starting armies: the start is the board with `ANYKEY TO START GAME` (`330e50f0b6dcf99f-board-before-start.png`, r0003); a click on it starts the game |
| The board at the start of a game | reached | `a83bf30d489aa71f-human-turn.png` (r0011); every run that started a game |
| One human turn: placing | reached | r0011, r0012: select a Blue country (left click), confirm (right click), `HOW MANY ?`, ALL (`ab8786549ae967d6-place-how-many.png`, `8e95a1ed60ae013d-place-turn-menu.png`, r0011) |
| One human turn: an attack and its result | reached | r0011: country 32 attacks 33; it took two ATTACK clicks (the observations read "after click 2"), and the message reads `5 AGAINST 0` (`f1a29561fd380111-attack-result.png`); r0012: country 20 attacks 19, also two clicks. Then `# TO MOVE` and ALL (`c100502a57028347-after-move-in.png`) |
| The turn menu | reached | ATTACK, MOVE, PASS, CARD, CANCEL (`8e95a1ed60ae013d-place-turn-menu.png`, r0011). MOVE and CANCEL were not used; CARD at turn 2 (`6fa6860f133839e5-cards-turn-2.png`, r0011) |
| An AI turn | reached | PASS, `BLUE DRAWS ONE CARD`, `CLICK TO CONTINUE`, then the computer turns with a colour's row marked and `<COLOUR> : 9 COUNTRIES`, `<COLOUR> ARMY GETS: 3`, `PLACING 3 ARMIES` (`4f7d70e140e0c7ae-draws-card.png`, `18ba9b5f9df705a6-click-to-continue.png`, `12271553e6940876-ai-turn-first.png`, `a62e6967244905c3-ai-turn-second.png`, r0011; r0012); then the next human turn (`a0b305c7a6d5f214-human-turn-2.png`) |
| Help or in-game text | not reached: the game has no Help screen (the buttons are Scores, Sound, Speed, Save, Quit). Its text is in the prompts and messages above and in the shareware notices (`06d117310d84e114-shareware-notice.png`, `ceedcdec94c8beb7-registration-notice.png`, r0021) | |
| Scores | reached | the scoreboard screen with Won, Lost and Percent per level (`653b2e9a566c09f6-scoreboard.png`, r0013); after a concession with `EASY : 0 1` (`018fd82faa47c644-scoreboard-after-concede.png`, r0014) |
| Sound | reached | `OFF..` and `ON...` after each click on the button (`0e0e3811f3fb7932-sound-clicked.png`, `4fbef221111835d2-sound-clicked-again.png`, r0013). No sound was produced or captured (F005: audio off) |
| Speed | reached | a Faster, value, Slower panel showing 2, then 1 after Faster (`cb91774c71cefd3a-speed-panel.png`, `e6c544bd0d03e228-speed-faster.png`, r0013) |
| Any save path | reached | Save: `GAME SAVED` (`ffd3ad8bd8d48121-save-turn1.png`, r0011; r0012, r0018, r0019, r0025, r0026); at turn 2 (`d17e7ce768e1da51-save-turn2.png`, r0011); Load: r0018, r0019 |
| Quit, concede, game over, another game | reached | `CONCEDE GAME ?` (`f8d6b90f27a7033e-concede-dialog.png`), the scoreboard, `GAME OVER` and `ANOTHER GAME ?` (`ae87e39e4f4ed180-game-over.png`), r0014, r0015, r0018, r0019, r0023, r0024 |
| The shareware notices and the game's own exit | reached | r0021: Another game No, `Shareware Version / Unregistered Copy` with `<C>ontinue` and `<U>pgrade`; key `c`; the registration notice with `<R>egistration` and `<E>xit To Dos`; key `e`: the game ends. The Upgrade and Registration choices were not taken; the mouse does not work on these notices (a click on `<C>ontinue` did nothing, exploration x22) |
| The end of a game (a win, or a loss by play) | not reached | no run played to the end; a win would show the scoreboard as the manual says |
| A hazard message (earthquake, flood, rebellion, a production centre increase) | not reached | none appeared in 26 runs of one to two turns |
| A card trade-in | not reached | no run held three matching cards |

## Proposed representation rows

These are proposals for `spec/representation.md`; IDs are assigned at promotion. Scope `DOS`, set `iw-dos-3.1-30121376`. Basis: observation of the game's own files at I0, with the screen as the check. The two-run column is the rule of the task: a row that says what a field means has two runs whose values change in line with a stated action. "Evidence" gives the tables in `measurements/analysis/`. Bytes are written as the game wrote them (`\r\n` is CRLF).

| Row | Representation | Basis | Runs |
| --- | --- | --- | --- |
| D1 | `ISLEWAR.DFT` after Set level is one text line ` L , A , 2 ` and CRLF: 13 bytes for one-digit values (`20 31 20 2c 20 31 20 2c 20 32 20 0d 0a` for L 1, A 1), 14 for starting armies 10 | the bytes of the file after the last choice | r0003 to r0010 |
| D2 | In that line, L (field 1) is the level: 1 Easy, 2 Normal, 3 Hard, 4 Hardest | choosing Easy writes ` 1 , 1 , 2 ` (r0003, r0004) and Normal ` 2 , 1 , 2 ` (r0005, r0006) with the same armies; Hard gives ` 3 , 6 , 2 ` (r0009) and Hardest ` 4 , 10 , 2 ` (r0010), one run each | r0003 to r0006 (two runs per value), r0009, r0010 |
| D3 | A (field 2) is the starting armies chosen: 1, 3, 6 or 10 | Easy with 1 gives ` 1 , 1 , 2 ` (r0003, r0004) and Easy with 3 ` 1 , 3 , 2 ` (r0007, r0008) with the same level; ` 3 , 6 , 2 ` (r0009), ` 4 , 10 , 2 ` (r0010) | r0003, r0004, r0007, r0008 (two runs per value), r0009, r0010 |
| D4 | The third field is `2` in every run that wrote the file. It is not decoded. It is not the game speed: r0013 set Speed to 1 (`e6c544bd0d03e228-speed-faster.png`) and the file still read ` 1 , 1 , 2 ` at the end | no run varied it | r0001 to r0026 (every run that wrote the file); r0013 |
| D5 | After Default the file is three lines `1`, `3`, `2` with CRLF (no spaces; 9 bytes `31 0d 0a 33 0d 0a 32 0d 0a`). The three values are not matched to fields by any action: Default is one action | the bytes of the file after Default | r0001, r0002 |
| D6 | After a conceded game, Another game and Load saved game the file is three lines ` 1 `, ` 1 `, ` 2 ` with CRLF (15 bytes `20 31 20 0d 0a 20 31 20 0d 0a 20 32 20 0d 0a`): the settings of the game, rewritten in the line layout. Which of those actions rewrote it was not isolated (the runs have no `files` step between them) | the bytes at the end of the run; the one-line form was still there after the concession | r0018, r0019 |
| D7 | `ISLEWAR.SCR` is four text lines `won,lost` with CRLF, one per level in the order Easy, Normal, Hard, Hardest. It is created at every launch with `0,0` four times (20 bytes `30 2c 30 0d 0a` four times). When a loss is credited the game writes the lost field as `, ` plus the number (`0, 1`, 21 bytes) | the bytes of the file at launch and after a concession | r0001 to r0026 (launch), r0014, r0015, r0023, r0024 |
| D8 | In `ISLEWAR.SCR`, the second number of line 1 is the Easy lost count and the second number of line 2 the Normal lost count: it goes from 0 to 1 when a game is conceded at that level. The scoreboard screen shows the same (`EASY : 0 1`). The first number (won) and lines 3 and 4 were never varied | Quit and Yes at Easy gives `0, 1` on line 1 (r0014, r0015), at Normal `0, 1` on line 2 (r0023, r0024), nothing else differs | r0014, r0015, r0023, r0024 |
| D9 | `ISLEWAR.SAV` is text with CRLF, one value per line, each line ` v ` (spaces before and after; the last two lines have commas): `N`, then N lines (the production centres), the level, the starting armies, `2`, `0`, then 46 owner lines, 46 army lines, a line `a , b , c , d`, a line of up to four numbers separated by commas. N is 3 or 4, so the file has 102 or 103 lines and is 523 to 531 bytes | the eight saves | r0011, r0012, r0018, r0019, r0025, r0026 |
| D10 | The owner lines are the army that holds country 1 to 46, as a code: 9 Blue, 4 Red, 2 Green, 8 Brown | the code of every country equals the army colour on the screenshot taken at the save: 46 of 46 on all 8 saves (368 pairs, no exception; the table of codes against colours is one-to-one); after the conquest of one country by Blue the code of that country goes from 4 to 9 in both runs with two saves (country 33 in r0011, 19 in r0012) | r0011, r0012 (two saves each), r0018, r0019, r0025, r0026 |
| D11 | The army lines are the number of armies on country 1 to 46 | the country conquered at turn 1 goes from 1 army to 4 in both runs with two saves, and the attack-result message of each reads `5 AGAINST 0` (the attacker's 5, all but one moved in); the other countries that differ in r0011 (3, 7, 25) show the changed counts on the screenshot of the second turn (`a0b305c7a6d5f214-human-turn-2.png`). Countries changed by the computer's turns are not separated from the action | r0011, r0012 |
| D12 | The N lines after the first are the production centres: the country numbers that show a `*` under their number on the board | read by eye on the screenshots: r0011 lists 8, 21, 1 (the stars are under 8, 21 and 1, `ffd3ad8bd8d48121-save-turn1.png`), r0019 lists 4, 44, 43 (`02d64db2c9feba40-save-turn1.png`); and r0012 and r0018 list 29, 4, 11 and 23, 17, 43, 8 (not checked by eye). N is the count | r0011, r0019 (checked); r0012, r0018, r0025, r0026 |
| D13 | The two lines after the production centres are the level (1 to 4) and the starting armies, the same values as `ISLEWAR.DFT` of the same run | Easy with 1 army: `1`, `1` in six saves (r0011, r0012, r0018, r0019); Normal with 3: `2`, `3` in r0025, r0026; each equals the DFT of its run | r0011, r0012, r0018, r0019, r0025, r0026 |
| D14 | The line `a , b , c , d` is the number of cards that Blue, Red, Green and Brown hold, the figures of the scoreboard's `C>` column | `0 , 0 , 0 , 0` at turn 1 and `1 , 0 , 0 , 0` at turn 2 in r0011 (the screen reads `C> 1` for Blue only); `0 , 0 , 1 , 0` and `1 , 1 , 1 , 1` in r0012 (the screen reads `C> 1` four times at turn 2) | r0011, r0012 |
| D15 | Not decoded: the two constants (`2`, `0`) after the starting armies (the same in all 8 saves); the last line (card types: `3,,,`, `7,3,7,2`, `,3,,7` ...): one number per colour that holds a card, with values 2, 3 and 7. What the numbers mean and how a colour holding several cards is written were not looked at | no run varied them in a known way | r0011, r0012, r0018, r0019, r0025, r0026 |
| D16 | Load saved game restores the saved board: the owner of all 46 countries on the board after Load equals the owner in the file | after Save, concede, Another game and Load, 46 of 46 owners equal (`1af654d4e9e2f5f0-loaded-human-turn.png`, r0018; r0019) | r0018, r0019 |

## Method

**Artifact.** Set `iw-dos-3.1-30121376`. `setup/iw-dos/iw-dos-runtime.sh` printed `ready` before the runs and again after them; `IW_DOS_DIR` was read and hashed only. Every run is a T11 cycle with its seal unchanged: the run copy checked with `check --strict` before the launch and immediately before it, only the run copy mounted as C:, `IW_DOS_DIR` bound read-only, the whole run in a network namespace of its own (the one interface DOSBox-X sees is `lo`), `completed` only on a clean finish.

**Runtime.** `runtime/iw-dos/spike/cycle.py --experiment E005 --steps <script>` at the commit named in each record, DOSBox-X 2024.03.01, Xvfb 800x600x24, no window manager. T14's additions: `--experiment` (records and bundles under E005), `--steps` (a step script in place of the one click on Set level: `navsteps.py`, parsed and refused before anything starts), `board.py` (reading owners and borders from a screenshot, to find a Blue country that touches an enemy on a board that differs in each run), and a record of every file the game adds or changes (size, sha256, the bytes in hex when at most 64, a copy kept in the bundle). Each script's sha256 is an observation of its record. A script can only click the game's window, press the keys `Return`, `space`, `Escape`, `c` and `e`, and wait; a line outside that grammar is refused (`tests/test_iw_dos_steps.py`; 30 mutants of the seal and of these additions are killed by `tests/mutants_iw_dos.py`).

**Arms** (the scripts are in `experiments/E005-iw-dos-state-inventory/steps/`):

| Arm | Runs | n | What it does |
| --- | --- | ---: | --- |
| `default` | r0001, r0002 | 2 | Default, start, first human turn |
| `level-easy-1`, `level-normal-1`, `level-easy-3` | r0003, r0004; r0005, r0006; r0007, r0008 | 2 each | Set level and starting armies, start, first human turn (the pairs vary one choice) |
| `level-hard-6`, `level-hardest-10` | r0009; r0010 | 1 each | the same, a probe |
| `turn` | r0011, r0012 | 2 | Easy, 1 army; Save; place all in a Blue country that touches an enemy; attack it until it falls; move in; Pass; the computer turns; Save at the next turn; place; the cards button |
| `buttons` | r0013 | 1 | Scores, Sound twice, Speed and Faster |
| `concede-easy`, `concede-normal` | r0014, r0015; r0016 to r0017 (aborted) and r0023, r0024 | 2 | Quit, Yes: the scoreboard and the game over dialog |
| `save-load` | r0018, r0019 | 2 | Save, concede, Another game Yes, the option box, Load saved game |
| `save-normal-3` | r0025, r0026 | 2 | Normal, 3 armies, Save at the first human turn |
| `load-none` | r0020 | 1 | Load saved game with no save |
| `exit` | r0021 | 1 | concede, Another game No, the shareware notices, `c`, `e`; the game ends by itself |
| `savestate` | r0022 | 1 | a DOSBox-X savestate at the first human turn, its members classified (I2) |

**Aborted records.** r0016 and r0017 (`concede-normal`): the click on Quit did not change the screen, three clicks each; the last screenshot of each shows the game's pointer in the middle of the screen, not on Quit. The cycle was changed so that a repeated click first steps the pointer off by one pixel (a test and a mutant for it), and the arm was run again as r0023 and r0024, which completed. Whether the pointer position or something else made the first clicks fail was not isolated. The aborted records stay.

**Manifests.** The 26 manifests first named the kept game files `"class": "file"`, which the manifest schema does not allow. The cycle now names a save `save` and the other files `measurement` (tests), and `experiments/E005-iw-dos-state-inventory/scripts/fix-manifest-classes.py` gave the 26 manifests that class. Nothing else in a manifest, and nothing in a run record, changed.

**Exploration** before the runs is in [`experiments/E005-iw-dos-state-inventory/measurements/explore/`](../experiments/E005-iw-dos-state-inventory/measurements/explore/) (runs `x01` to `x30` and `d-*`, one `--explore` run each: logs, observations and the sha256 of every capture; no record). It found the screens, the click coordinates, that a left click selects an attack country and a right click confirms a placement, that ALL moves all but one, that the Save click after placing wrote nothing in one exploration run (x26, not repeated in a record), and the shape of the save. It is not records. This finding cites it only where it says so.

**Observations.** The tables built from the records and the bundles (`experiments/E005-iw-dos-state-inventory/scripts/analyze.py`, `check-board-reader.py`) are in `measurements/analysis/`: the files each run wrote (`files-by-arm.tsv`), each save against the screen (`save-owner-check.tsv`, `save-codes.tsv`), the saves' fields (`save-fields.tsv`), the two saves of each turn run (`turn-diff.tsv`), the load check (`load-check.tsv`), timings (`timings.tsv`) and the board reader against the scoreboard (`board-owner-check.tsv`).

## Inferences

- From the tables of D1 to D3: the DFT's first two fields are the level and the starting armies, because they change with those two choices and with nothing else (two runs per value for four of the six).
- From D7 and D8: the scoreboard is stored per level, lost second; the first number is the wins by column order only.
- From D10: the owner codes 9, 4, 2, 8 match the EGA colour indexes of light blue, red, green and dark grey (the Brown army is drawn dark grey). That is a remark on the numbers; only the mapping is tested.
- From the 20 start pictures in 26 runs: the start of a game is not a fresh draw in every run. Whether the same inputs and the same timing give the same board is not tested.
- From D14 and the C> readings: the card counts are stored per colour in the order Blue, Red, Green, Brown.

## Alternatives considered

- **The owner mapping is circular: the screen reader and the codes were fitted to each other.** Not excluded as a fit, excluded as a coincidence. The codes were read off the first save and then tested unchanged on all 8 saves: 368 pairs, none against. The reader's totals equal the four figures of the game's own scoreboard panel, read by eye, on 7 of 8 screenshots (`measurements/analysis/board-owner-check.tsv`); the 8th (r0011 `attack-result.png`) shows the conquered country already Blue on the map while the panel still reads 17, and the panel reads 18 after the move in. The mapping from code to colour is one-to-one (`save-codes.tsv`).
- **The save's armies are read from the screen, not the file.** The armies of the countries that changed are checked against the digits on the screenshot by eye for r0011 (countries 3, 7, 25 and 33: 3, 3, 4, 4) and the conquered country in r0012; the other 40 or so countries were not compared one by one (a digit reader is not in this task).
- **A change in the second save is caused by the computer, not by the action.** For the conquered country the action explains the change in both runs (owner 4 to 9, armies 1 to 4); the other differences are in countries the computer's turns touched and are not claimed.
- **The runs agree because the reset hid what run 1 changed.** Excluded as in F005: every run starts from the same run copy (checked by `start_state.sha256`, every record) and every diff is the files the game added.
- **The savestate is the original's behaviour.** It is I2 and says so; nothing from it is claimed about the game.

## What this does not establish

- *Isle Wars Pro*: nothing; this finding is DOS *Isle Wars*' only (rule 19).
- Any game rule: the numbers above are what a save holds, not how the game plays. One roll per ATTACK click is how the two attacks went, not a rule.
- A win, a hazard, a card trade-in, MOVE and CANCEL, a level above Easy played past the first turn, more than one save in a run at one turn, and what the registered version does (unknown).
- The meaning of the DFT's third field, the two constants of the save, the card-type numbers, and the order of the won and lost numbers of the scoreboard (the lost number only is shown).
- Which action rewrites the DFT in the line layout (D6), and whether a Save after placing armies writes anything (one exploration run says no).
- What `ISLEWAR.DAT` holds.
- The memory image: no game field was looked for (W5b).
- Repeatability beyond one machine, one DOSBox-X build and one day; the arms that ran once are probes.
- Audio, real DOS hardware, another emulator.

## Where the evidence is

- Run records: `runs/E005/E005-r0001.json` to `E005-r0026.json`.
- Evidence manifests: `evidence/E005/E005-r0001.manifest.json` to `E005-r0026.manifest.json`.
- The bundles (screenshots, the files the game wrote as `s<NN>-<NAME>` and `end-<NAME>`, `changes.log`, `run.log`, `dosbox.log`, `dosbox.conf.txt`) are kept locally, outside the repository. The main session uploads them to release `E005` after review. Each file is named `<sha256[:16]>-<name>`, as its manifest says. No savestate is kept: it holds the game's memory (rule 18); its hash is in the record of r0022. The game-written files are small text files the game wrote from the player's own actions; they stay in the bundles, with their bytes in hex in the records when at most 64.
- The outputs of the Done-when commands: `experiments/E005-iw-dos-state-inventory/measurements/done-when/`.
- Exploration and the tables: `experiments/E005-iw-dos-state-inventory/measurements/`.

## Reproduction

The machine needs DOSBox-X 2024.03.01, Xvfb, xdotool, ImageMagick and util-linux, `IW_DOS_DIR` set to the extracted archive, and `IW_DOS_RUN`, `E005_BUNDLES` and `E005_EXPLORE` set to locations outside every checkout and `IW_DOS_DIR`. Then:

```text
setup/iw-dos/iw-dos-runtime.sh
experiments/E005-iw-dos-state-inventory/scripts/cyc.sh turn experiments/E005-iw-dos-state-inventory/steps/turn.steps
experiments/E005-iw-dos-state-inventory/scripts/analyze.py <out dir>
python3 tools/register_artifact.py check "$IW_DOS_DIR" iw-dos-3.1-30121376 --strict
```

The arms and their scripts are listed in the experiment README.
