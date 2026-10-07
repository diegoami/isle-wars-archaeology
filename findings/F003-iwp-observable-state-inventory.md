# F003 Isle Wars Pro shows its game state on the screen; the only game files seen to change hold the saved options and a scoreboard as short comma-separated text, and no save or load was found

- **Status**: proposed
- **Question**: Where can the state of Isle Wars Pro (the unregistered 2.0 install) be seen, at what intervention level and at what cost: on the screen, in files the game writes, in the registry, in the Temp folder, in the window title, in the process? Which files does it write, in what format, and does it save a game? (E002, task T09, W4a; feeds Q-SET-05 and the W5a driver.)
- **Tests claims**: none (a source inventory; it proposes representation rows 1 to 7 below and makes no claim about a game rule)
- **Experiment and runs**: E002; runs E002-r0001 to E002-r0024, all in `runs/E002/`. Four of them aborted (E002-r0002, E002-r0003, E002-r0018, E002-r0019) and stay; the table in "Method" says why and which each claim cites.
- **Artifact**: set `iwp-2.0-996e86c5`, variant none, for the two runs that cannot write a file of the set (E002-r0021, E002-r0022); set `iwp-2.0-de5a82a2`, variant none, for the other 22 ([`artifacts/iwp/iwp-2.0-de5a82a2.md`](../artifacts/iwp/iwp-2.0-de5a82a2.md)): the same files, with `xtras/Isledft.dat` and `xtras/Islepro.skr` declared runtime writes
- **Max intervention**: I1 (screenshots of the display, read-only reads of `/proc` and of the game copy, and a static byte count of the shipped `xtras/Islepro.dat`; no memory read, no modified file, no input but the mouse)
- **Tier reached**: V2 (the original, headless, under Wine; no native Windows run, so no V3)
- **Confidence**: for each parsed field, an action that moves the byte, two runs that agree with each other, and a control of two runs that leave it alone (the speed and level fields of `Isledft.dat`; the Normal-lost and Hard-lost fields of `Islepro.skr`, 2 runs each plus 2 tour runs for Normal-lost). Every other field of both files is unvaried and not decoded. One machine (WSL2), one Wine build, one install. The files were compared at a few points of each run, not traced while the game played (see the Answer). The "no save or load" answer is a negative over the screens and runs listed, not a proof.

## Answer

- **The game state was read from the screen, and no file read showed it.** The territory owners, the army numbers, whose turn it is, the phase, the cards and the result of an attack are all read from the screenshots of E002-r0001 and E002-r0020 (one human turn, an attack, the computer players' turns). The game copy was compared with the install at a few points only:
  - at the end of each of the 22 runs that launched the game, after it was stopped (E002-r0002 and E002-r0003 aborted before the launch and compared nothing);
  - before the stop, in the option arms after Save as default (E002-r0004 to E002-r0013, E002-r0023, E002-r0024) and in the loss arms after the loss was credited (E002-r0014 to E002-r0017);
  - in E002-r0001 and E002-r0020, at steps 111 to 120, after New Game had left the game in progress and the loss was credited;
  - in E002-r0021 and E002-r0022, at step 19, on the board after the computer players' opening turns (nothing had changed: 0/0/0).

  - At those points no file of the game copy had changed except `xtras/Isledft.dat` (E002-r0004 to E002-r0013) and `xtras/Islepro.skr` (E002-r0001, E002-r0014 to E002-r0017, E002-r0020). The registry differed by the same seven keys in each of the 22 runs that launched, and the Temp folder held the same entries whether or not a game was played (see the source table). No read fell inside the tour's placement, attack or computer turns. A file written during play and removed or restored before the next read, or a state kept only in memory, is therefore not excluded. The screen is the one source found that shows the position; that it is the only place the game holds it is not shown.
- **Two files are written, both comma-separated decimal text, and each has a field that moves with a known action.** (E002-r0004 to E002-r0017)
  - `xtras/Isledft.dat` holds the saved options. After Save as default the byte at offset 8 is the speed (`1` FAST, `2` NORMAL, `3` SLOW: E002-r0012, E002-r0013, E002-r0004, E002-r0005, E002-r0010, E002-r0011) and the byte at offset 14 is the starting level (`1` HARD, `2` NORMAL, `3` EASY: E002-r0006, E002-r0007, E002-r0004, E002-r0005, E002-r0008, E002-r0009). Clicking Save as default with nothing changed rewrites the 15-byte shipped file as 16 bytes by appending a comma (E002-r0004, E002-r0005).
  - `xtras/Islepro.skr` holds the scoreboard. Its bytes are consistent with each character shifted by 0x5e (three values seen; see P5). New Game in the middle of a game brought up the game's loss notice at NORMAL and at HARD. The notice's text says the player controls fewer than 10 countries; that condition is not tested here. Afterwards the scoreboard showed one loss at the level played, and one byte had moved (E002-r0001, E002-r0014 to E002-r0017, E002-r0020):
    - at NORMAL, the byte at offset 6 went from `0x8e` to `0x8f` (E002-r0014, E002-r0015, and the tours E002-r0001, E002-r0020, each with the scoreboard showing Normal lost 1);
    - at HARD, the byte at offset 10 did (E002-r0016, E002-r0017; the scoreboard shows Hard lost 1).

    - At EASY, with the same action, no loss notice appeared and no file changed (E002-r0018, E002-r0019, aborted by their own script, which expected the notice).
- **`xtras/Islepro.dat` (190 bytes, shipped) never changed.** It equalled the install's file in each of the 18 records that read it (E002-r0001, E002-r0004 to E002-r0017, E002-r0020, E002-r0023, E002-r0024). In E002-r0018, E002-r0019, E002-r0021 and E002-r0022 it was not read on its own, but the whole-copy comparison reports no file changed (0/0/0), so it is inferred unchanged there too. E002-r0002 and E002-r0003 did not launch the game. F002 reports that it was not written in any arm of E001. Its role is unknown; a static count of its bytes is in `measurements/static-islepro-dat.md`.
- **No save or load was found.** No title-screen or board label offers one (the bottom bar of both reads New Game, Help, Options, Soleau Games, Scores, Quit), after a game quit in the middle the game copy shows only the scoreboard credit, and the directions (`Islepro.txt`) never mention saving. Keyboard shortcuts were not tried, and the registered build was not available. Q-SET-05 for the unregistered build: no save or load was found; it is not shown that none exists (E002-r0001 to E002-r0024).
- **Every screen asked for was reached except the end of a game** (see the screens table). The game's dice are not drawn: an attack shows only the army counts before and after (E002-r0001, E002-r0014 to E002-r0022).
- **The Help text is the text of `Islepro.txt` with three differences**, hand-checked against the screenshots (E002-r0001 help-06 and help-11): the Bomb card line, a paragraph asking players to pass the shareware version along, and a paragraph about upgrading by credit card over the internet. They are added to the knowledge map.
- **Cost.** A run that reads the option file takes 40 to 46 s, of which 30 s is the driver waiting for Wine processes that do not end after `wineserver -k` (see Speed; E002-r0004 to E002-r0024).

## Source table

Cheapest first. Level is the intervention level of the reading. Cost is what a reading needs, from the runs' own timings. "Runs" are the records that show it.

| # | Source | State it shows | Class | Level | Cost | Runs |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Window title (read from the window manager) | nothing about play: the title is `Islepro` on the title screen, the setup screen and the board | directly-observable | I1 | milliseconds, in any run | E002-r0021, E002-r0022 |
| 2 | Process threads and resident memory (`/proc`) | nothing usable: 1 thread; resident memory 43.2 to 43.3 MB on the title screen, 43.5 MB on the setup screen, 44.1 to 44.3 MB on the board | directly-observable | I1 | milliseconds, in any run | E002-r0021, E002-r0022 |
| 3 | Screen regions (one screenshot each) | what the recorded screenshots show: territory colours and army numbers; the four-colour panel top left (a figure beside each colour whose meaning is not identified here, a cards figure, an arrow on the colour whose turn it is); the message areas at the bottom (phase prompts, `Counting...`, army counts of an attack, the result); the placing, attacking, moving and turn-menu panels; the scoreboard and the notices | directly-observable | I1 | under 1 s per capture; the screen must be quiet first: 15 to 33 s until the board is quiet for 4 s before the first human turn (the computer players' turns; the 10 runs that reached it, E002-r0001, E002-r0014 to E002-r0022), 23 to 24 s for three computer turns after a pass (E002-r0001, E002-r0020) | E002-r0001, E002-r0020 (tour), E002-r0014 to E002-r0017 (setup, board, notice, scoreboard) |
| 4 | `xtras/Isledft.dat` (game copy, read after the run) | the saved options: speed and level decoded; the other six fields unvaried | parsed | I0 | one run of about 43 s: Options, one control, Save as default; no other arm changed it | E002-r0004 to E002-r0013 |
| 5 | `xtras/Islepro.skr` (game copy, read after the run) | the scoreboard: Normal lost and Hard lost decoded; the other five fields unvaried | parsed | I0 | one run of 62 to 72 s: New Game, Play Game, wait for the human turn, New Game again; it changed only in the runs that credited a loss | E002-r0001, E002-r0014 to E002-r0017, E002-r0020 |
| 6a | `xtras/Islepro.dat` in the game copy (size and sha256 compared with the install's file, after the run) | nothing that changed: the file equalled the install's at every read, so it shows no state of a run; its meaning is unknown | directly-observable (filesystem state of the game copy, read at I0), no game-state field | I0 | free: part of a run's file reads | E002-r0001, E002-r0004 to E002-r0017, E002-r0020, E002-r0023, E002-r0024: the 18 records with the observation `xtras/Islepro.dat: equals the install's file`, each "yes". E002-r0018, E002-r0019, E002-r0021 and E002-r0022 hold only a whole-copy comparison (0/0/0), from which equality is inferred; E002-r0002 and E002-r0003 never launched the game |
| 6b | `xtras/Islepro.dat` as shipped (a static byte count of the install's file, read in place) | nothing decoded: 190 bytes, 185 printable ASCII, no comma, 20 distinct values from 13 to 119; its meaning is unknown | invasive (static analysis of a shipped file) | I1 (static analysis) | one command, no run | none: `measurements/static-islepro-dat.md` |
| 7 | Registry (key names and a hash of each key's values, before and after) | nothing of the game: the same seven keys change in each of the 22 runs that launched (`NetworkCards` removed; the font keys, two device-class keys of `system.reg` and `External Fonts` of `user.reg` changed), whether or not a game was played. Which process wrote them is not established. No action of any arm varied them, so there is no field to decode and no representation row | directly-observable (filesystem state of the prefix, a diff read at I0), no game-state field | I0 | free: part of every launched run's snapshot | E002-r0001, E002-r0004 to E002-r0024 (the 22 records with a `changes.log`; E002-r0002 and E002-r0003 never launched) |
| 8 | Temp folder of the prefix's user | nothing: Director unpacks 3 DLLs and 17 Xtras into `TempFolder.aaa`; the same entries and sizes whether the run played a game (E002-r0014, E002-r0016) or only opened Options (E002-r0004); removed when the game exits through its own buttons (E002-r0001, E002-r0020), left by `wineserver -k`. The names are consistent with the Director runtime unpacking its own files; that is not established. No action varied it, so there is no representation row | directly-observable (filesystem state of the prefix), no game-state field | I0 | free | E002-r0001, E002-r0004, E002-r0014, E002-r0016, E002-r0020 |
| 9 | Process memory | not read: whether it holds the state the screen draws is unknown | invasive | I1 (read-only memory) | not measured: classified only, not performed | none |
| 10 | The Director movie and its Lingo scripts | not read: what they hold is not established here | invasive | I1 (static analysis) | not measured: classified only, not performed | none |
| 11 | A crafted save | not applicable: no save was found | invasive | I3 | not performed | none |

## Screens

Cheapest path first; every run that reached a screen and the screenshot asset (release `E002`, see the manifests) are named. `E002-r0001` and `E002-r0020` are the two runs of the `tour` arm.

| Screen | Reached | Runs and a screenshot |
| --- | --- | --- |
| Title | reached | every run that started; `ae6e98d28d379bb4-title.png` (E002-r0001, E002-r0020) |
| Options | reached | E002-r0001, E002-r0020, E002-r0004 to E002-r0013, E002-r0023, E002-r0024; `426d77e724d793dd-options-defaults.png` (E002-r0001) |
| Options: the locked controls | reached | the message "available only in the Registered Version" for starting armies 5 (`9160a38dd7b6cd83-locked-armies.png`, E002-r0001), for Yellow set to human (`55067d5ed102d7d9-locked-human.png`, E002-r0001), and for frequency LESS, MORE and NEVER (E002-r0001, E002-r0020, E002-r0023, E002-r0024); the speed and level controls are not locked |
| New Game setup | reached | E002-r0001, E002-r0020, E002-r0014 to E002-r0019, E002-r0021, E002-r0022; `154143a1bd739503-newgame-setup.png` (E002-r0001). Every control and its default: see below |
| Board at the start of a game | reached | E002-r0001, E002-r0020, E002-r0014 to E002-r0019, E002-r0021, E002-r0022; `448ea9478fd85814-board-human-turn.png` (E002-r0001). The start varies: no two of the 10 first-human-turn boards (E002-r0001, E002-r0014 to E002-r0022) were alike |
| One human turn: placing | reached | E002-r0001, E002-r0020: select a Blue country, ALL, PLACE; `fd1480253c2908f3-place-selected.png`, `59c1753667d72c5e-place-all.png`, `99f47a518cb3b7b4-place-done.png` (E002-r0001) |
| One human turn: an attack and its result | reached | E002-r0001: Blue country 2 attacks country 1, "4 Against 1" becomes "3 Against 1" (`7ca1db9ca3019e7a-attack-ready.png`, `84b4b1f44ff09610-attack-result-1.png`); E002-r0020: country 3 takes country 2, the message reads that Red has been defeated and a "Move in how many?" panel appears (`865937d28607e468-attack-ready.png`, `11098950c70c269d-attack-result-1.png`). The dice themselves are not shown |
| The turn menu | reached | Attack, MOVE, PASS, CARD, Cancel; `1cceb5b18427a7d4-turn-menu.png` (E002-r0001), `167a0391...-turn-menu.png` (E002-r0020, another board). MOVE, CARD and the Cancel path were not used |
| A computer turn passing | reached | PASS, then `Counting...` with a colour's row highlighted and `<colour> has no islands. Placing 3 Armies` (E002-r0001 `26a839a2b8888a56-pass-1.png`, `8ff170974272705e-after-pass.png`; E002-r0020 `6d3a0f7b702bae2e-ai-turn.png`); then the next human turn (`abf0427833780aca-human-turn-2.png`, E002-r0001) |
| Help | reached | 12 pages (`390756985586a01d-help-01.png` to `2088424b236a2607-help-12.png`, E002-r0001; E002-r0020 has the same files); two more page-down sequences end on the last page (identical bytes) |
| Scores | reached | before and after a credited loss: `d816d6fb3ee277b0-scores-before.png`, `f30ee66289086dc6-scores-after.png` (E002-r0001, E002-r0020); after a loss also E002-r0014 and E002-r0015 (`f30ee662...`) and E002-r0016 and E002-r0017 (`694651be...`); a Reset Scores button appears on the scoreboard (never clicked) |
| The loss notice | reached | New Game in the middle of a game at NORMAL or HARD (`5ad6d9012cdce6b9-loss-notice.png`, the same file in E002-r0001, E002-r0014 to E002-r0017 and E002-r0020). At EASY the click went straight to the setup screen: no notice (E002-r0018, E002-r0019) |
| The unregistered notice | reached | on quitting through Return, Quit (`47afc4d33b5450f9-notice.png`, E002-r0001 and E002-r0020); its Exit Game label was clicked; Order Online Information and Go To were not |
| Soleau Games, the order and website buttons | not reached | forbidden by the task (hazard) and never clicked; the title screen's label is a refused rectangle in `steps.py` |
| The end of a game (a win, or a loss by play) | not reached | no run played to the end |
| Registered-only screens (more than one human, set starting armies, set frequency, clear scoreboards) | not reached | the unregistered build refuses them |

**The Options and New Game setup screens share one layout.** Every control and its default, read from `426d77e724d793dd-options-defaults.png` (E002-r0001) and `154143a1bd739503-newgame-setup.png` (E002-r0001):

| Control (on-screen label) | Choices | Default |
| --- | --- | --- |
| Number of Starting Armies Possible | 1, 3, 5, 7, 10 | 3 |
| Colors of Human or Computer Opponents | BLUE, YELLOW, RED, GREEN, each H or C | BLUE H, the others C |
| Starting Level Position Strength | HARD, NORMAL, EASY | NORMAL |
| Frequency of Production and Disaster Messages | MORE, NORMAL, LESS, NEVER | NORMAL |
| Game Playing Speed | FAST, NORMAL, SLOW | NORMAL |
| Buttons | SAVE AS DEFAULT, an ear icon (not clicked), RETURN (Options) or PLAY GAME (setup) | |

## Proposed representation rows

These are proposals for `spec/representation.md`; IDs are assigned at promotion. Scope `Pro`, set `iwp-2.0-de5a82a2`. Basis: observation of the game's own files at I0, with the screen as the check. The parsed sources of the table are rows 4 and 5, and P1 to P7 cover them. Rows 6a and 6b (`Islepro.dat`, never seen to change, and its static byte count), row 7 (the registry) and row 8 (the Temp folder) are not parsed sources and have no row: nothing in them changed with an action, so there is no field to propose.

| Row | Representation | Basis | Runs |
| --- | --- | --- | --- |
| P1 | `xtras/Isledft.dat` is text: in every file the game was seen to write, eight decimal fields, each followed by a comma, as `1,0,0,0,2,2,3,2,` when saved with the default options. The shipped file is the same without its last comma (15 bytes). Every Save as default that took effect in these runs (E002-r0004 to E002-r0013) left 16 bytes, including the control, which changed nothing; writes in other situations were not seen. | the control arm: the driver's diff of the game copy against the install's file says "appended at 0xf: 2c" and nothing else | E002-r0004, E002-r0005 |
| P2 | In `xtras/Isledft.dat`, the byte at offset 8 is the game speed: `0x31` FAST, `0x32` NORMAL, `0x33` SLOW | Options, click the speed label, Save as default: FAST gives `1,0,0,0,1,2,3,2,` (E002-r0012, E002-r0013), SLOW gives `1,0,0,0,3,2,3,2,` (E002-r0010, E002-r0011), the controls give `...2,2,3,2,` (E002-r0004, E002-r0005); nothing else differs | E002-r0004, E002-r0005, E002-r0010 to E002-r0013 |
| P3 | In `xtras/Isledft.dat`, the byte at offset 14 is the starting level: `0x31` HARD, `0x32` NORMAL, `0x33` EASY | the same action with the level label: HARD gives `...,3,1,` (E002-r0006, E002-r0007), EASY gives `...,3,3,` (E002-r0008, E002-r0009) | E002-r0004 to E002-r0009 |
| P4 | `xtras/Isledft.dat`: the bytes at offsets 0, 2, 4, 6, 10 and 12 (fields `1,0,0,0`, `2`, `3` in the default file) are not decoded. They did not change in any run. The other controls (starting armies, a human Yellow, frequency) are locked in the unregistered build, so no run could vary them, and what the bytes mean is unknown. The default file's `1,0,0,0` and `3` match the defaults H C C C and 3 starting armies on the Options screen, and nothing tests the match. | no run varied them: E002-r0001, E002-r0020, E002-r0023, E002-r0024 show the lock message | E002-r0001, E002-r0020, E002-r0023, E002-r0024 |
| P5 | `xtras/Islepro.skr` is the scoreboard: seven decimal fields, each followed by a comma, each byte proposed to be stored as its ASCII value plus `0x5e` (`0x8e` for `0`, `0x8f` for `1`, `0x8a` for the comma). Only these three values were seen, so the shift is shown for them only and the general encoding is a proposal. The shipped file is 13 bytes (all counters `0`, no last comma); the first write makes it 14 bytes by appending the comma. | the bytes `8e 8a 8e 8a 8e 8a 8f 8a 8e 8a 8e 8a 8e 8a` after one credited loss at NORMAL, with a scoreboard that shows exactly one non-zero cell (Normal lost 1); the digit values step by one, as digits do | E002-r0001, E002-r0014, E002-r0015, E002-r0020 |
| P6 | In `xtras/Islepro.skr`, the byte at offset 6 is proposed as the Normal-lost count and the byte at offset 10 as the Hard-lost count: each went from `0x8e` to `0x8f` as the displayed count went from 0 to 1 (one step each; larger counts were not seen) | New Game in the middle of a game, followed by the game's loss notice: at NORMAL offset 6 changes and the scoreboard's Normal Lost cell reads 1 (E002-r0001, E002-r0014, E002-r0015, E002-r0020); at HARD offset 10 changes and Hard Lost reads 1 (E002-r0016, E002-r0017); nothing else differs | E002-r0001, E002-r0014 to E002-r0017, E002-r0020 |
| P7 | `xtras/Islepro.skr`: the bytes at offsets 0, 2, 4, 8 and 12 are not decoded. A won game and an Easy loss were not produced. A hypothesis, untested: if the fields are Won and Lost per level, offset 2 would be Easy lost; no run shows it. | no run changed them (each credited-loss run's diff names only offset 6 or 10 and the appended byte) | E002-r0001, E002-r0014 to E002-r0017, E002-r0020 (unchanged) |

## Speed

- The kill path (`wineserver -k`) leaves processes that the driver waits 30 s for, then ends with a second `wineserver -k` and SIGKILL: "wine processes gone after terminate" is `still running` in every kill-terminated record that launched (E002-r0004 to E002-r0019, E002-r0021 to E002-r0024), 2.06 s after the game's own Quit in E002-r0001 (`ui-quit`), and `still running` in E002-r0020, the other `ui-quit` run. A kill run therefore takes 40 to 46 s for six visible steps, and about 13 s without that wait. The driver was not changed (not in this task's scope); a later task can end the wait early.
- Launch to the title screen: 6.25 to 6.92 s (22 of 22 runs that started).
- Quitting through the game's buttons: 14.03 to 14.73 s (E002-r0001, E002-r0020), as in F002.
- A loss run (New Game, Play Game, a quiet board, New Game): 62 to 72 s, almost all of it the wait for a quiet board before the first human turn (15.5 to 27.7 s in E002-r0014 to E002-r0017, the computer players' turns) plus the 30 s tail. The whole `tour` takes 137 s (E002-r0001) and 170 s (E002-r0020).
- The table of every run is `experiments/E002-iwp-state-inventory/measurements/run-table.md`.

## Method

**Artifact.** Set `iwp-2.0-996e86c5` for E002-r0021 and E002-r0022; set `iwp-2.0-de5a82a2` for the rest. `setup/iwp/iwp-runtime.sh` printed `ready` before the runs; the install was read and hashed, never written. The driver binds the install read-only for each run, seals the prefix before anything starts and again immediately before the launch, writes through `safeio.py`, and records `completed` only on a clean finish.

**Runtime.** `runtime/iwp/spike/cycle.py` at the commit named in each record (`code_commit`; E002-r0001 at 8b80795, whose runtime code is unchanged to the later commits), `--experiment E002` and a step script (`steps.py`: click, settle, shot, file, changes). Platform as in F002: Wine 9.0, Xvfb 800x600x24, xfwm4, xdotool, the game in a network namespace of its own (the one interface it sees is `lo`). Start state `S-cold-prefix-title`, `start_state.sha256` `34ac62c31ddaa5f4e9a1b975a956c94ebe935109189d0fffe8939dc2bddfa427` in all 22 runs that started. Each script's sha256 is the first observation of its record.

**Arms** (the scripts are in `experiments/E002-iwp-state-inventory/scripts/`):

| Arm | Runs | n | Terminated by |
| --- | --- | ---: | --- |
| `opt-control` (Options, Save as default, nothing changed) | E002-r0004, E002-r0005 | 2 | kill |
| `opt-level-hard`, `opt-level-easy` | E002-r0006, E002-r0007; E002-r0008, E002-r0009 | 2 each | kill |
| `opt-speed-slow`, `opt-speed-fast` | E002-r0010, E002-r0011; E002-r0012, E002-r0013 | 2 each | kill |
| `opt-freq-more`, `opt-freq-never` (added after the first series, to vary the one control not yet varied) | E002-r0023; E002-r0024 | 1 each | kill |
| `loss-normal`, `loss-hard` | E002-r0014, E002-r0015; E002-r0016, E002-r0017 | 2 each | kill |
| `loss-easy` | E002-r0018, E002-r0019 (aborted) | 2 | kill |
| `tour` | E002-r0001, E002-r0020 | 2 | the game's own Quit |
| `probe-process` (added: window title, threads and memory on three screens) | E002-r0021, E002-r0022 | 2 | kill |

**Aborted records.** E002-r0002 and E002-r0003 (`opt-control`): xfwm4 did not register within 20 s. The shell the driver ran from carried a `DBUS_SESSION_BUS_ADDRESS` that pointed at a bus that no longer existed (`/run/user/1000` was gone), and `xfwm4` printed "Xfconf could not be initialized" on a manual start; with the variable unset it registered at once, so the later runs were started with it unset. E002-r0018 and E002-r0019 (`loss-easy`): the script clicked Continue on a notice that did not appear at EASY (the New Game click had gone straight to the setup screen); the game copy was unchanged (0/0/0) in both.

**Not a rule claim.** This finding says where the state can be seen. It says nothing about how the game decides an outcome, and the Easy result above is an observation about a notice, not a rule about the 10-country threshold.

**Static reading.** The shipped `xtras/Islepro.dat` was read in place for byte counts only (`measurements/static-islepro-dat.md`). The Director movie and the Lingo scripts were not extracted or read.

## Observations

Raw only. Hashes are the first 16 hex digits of the screenshot's sha256, as in the assets' names.

**`Isledft.dat` as written by the game** (`measurements/file-bytes.md`, generated from the records; `raw:bytes[0x0:0x10]` observation of each run):

| Run | Arm | Bytes (hex) | As text |
| --- | --- | --- | --- |
| E002-r0004, E002-r0005 | opt-control | `31 2c 30 2c 30 2c 30 2c 32 2c 32 2c 33 2c 32 2c` | `1,0,0,0,2,2,3,2,` |
| E002-r0006, E002-r0007 | opt-level-hard | `31 2c 30 2c 30 2c 30 2c 32 2c 32 2c 33 2c 31 2c` | `1,0,0,0,2,2,3,1,` |
| E002-r0008, E002-r0009 | opt-level-easy | `31 2c 30 2c 30 2c 30 2c 32 2c 32 2c 33 2c 33 2c` | `1,0,0,0,2,2,3,3,` |
| E002-r0010, E002-r0011 | opt-speed-slow | `31 2c 30 2c 30 2c 30 2c 33 2c 32 2c 33 2c 32 2c` | `1,0,0,0,3,2,3,2,` |
| E002-r0012, E002-r0013 | opt-speed-fast | `31 2c 30 2c 30 2c 30 2c 31 2c 32 2c 33 2c 32 2c` | `1,0,0,0,1,2,3,2,` |
| E002-r0023, E002-r0024 | opt-freq-more, opt-freq-never | not written: the game copy equals the install's (15 bytes, sha256 `1750f915ae4ea473d6b21493b7fe3d289fe45f2ea0d779f3cce3c40c309550df`). The first click after a lock message only dismissed it, and Save as default was not applied (the Save button is lit, no file changed) | |

The driver's own diff against the install's file, in every run that wrote it: "appended at 0xf: 2c" (control, level and speed arms) and no other offset except the one the table shows.

**`Islepro.skr` as written by the game** (the first 14 bytes, the whole file):

| Run | Arm | Bytes (hex) | Driver's diff against the install's 13-byte file |
| --- | --- | --- | --- |
| E002-r0001, E002-r0020 | tour | `8e 8a 8e 8a 8e 8a 8f 8a 8e 8a 8e 8a 8e 8a` | `0x6 8e>8f; appended at 0xd: 8a` |
| E002-r0014, E002-r0015 | loss-normal | the same | the same |
| E002-r0016, E002-r0017 | loss-hard | `8e 8a 8e 8a 8e 8a 8e 8a 8e 8a 8f 8a 8e 8a` | `0xa 8e>8f; appended at 0xd: 8a` |

Scoreboard screenshots after the loss: Normal lost 1, the rest 0 (E002-r0001 `f30ee66289086dc6-scores-after.png`; E002-r0014, E002-r0015 and E002-r0020 the same file hash); Hard lost 1, the rest 0 (E002-r0016 `694651bede62cb5d-scores.png`; E002-r0017 the same file hash). Before any game the scoreboard is all zeros (E002-r0001 `d816d6fb3ee277b0-scores-before.png`).

**The game copy and the prefix, whole runs.** E002-r0021 and E002-r0022: nothing of the game copy changed (0/0/0). The 20 runs on `iwp-2.0-de5a82a2` that launched the game changed only the two files above (0/0/1) or nothing (E002-r0018, E002-r0019, E002-r0023, E002-r0024); E002-r0002 and E002-r0003 aborted before the launch and have no comparison. At the end, the prefix had gained the same 31 entries in each of the 20 runs stopped by kill (`dosdevices/com1` to `com8`, `wineserver`, and `TempFolder.aaa` with its `xtras` folder, 3 DLLs and 17 Xtras); the two tours, which quit through the game's buttons, end with 9 (the same without `TempFolder.aaa`), after 31 at step 120. `system.reg` and `user.reg` changed size in all 22. The registry diff in the `changes.log` of all 22 launched records (release `E002`, four distinct files) lists the same seven keys.

**Window title and process** (E002-r0021, E002-r0022): `client window titles: 'Islepro'` at the title screen, the setup screen and the board; threads 1 each time; resident memory in kB: title 43284 (E002-r0021), setup 43540 (E002-r0021), board 44316 (E002-r0021) (E002-r0022's three readings are in its record).

**Screens and text.** The screenshots named in the Screens table. In the Help pages (E002-r0001), page 6 (`c84434ef3cb45451-help-06.png`) reads "Allows you to bomb any country diminishing their troops." where `Islepro.txt` says the effects of the bomb are shown in the new troop value; page 11 (`fdc269c5d5fc243f-help-11.png`) holds the paragraph asking players to pass the shareware version on, and the credit-card upgrade paragraph; page 12 (`2088424b236a2607-help-12.png`) ends with the publisher's address block. `Islepro.txt` has a paragraph on ordering by phone and on cards accepted, which the Help pages do not have (a difference in the other direction, not added to the map).

## Inferences

- **The files seen to change hold settings and a score; no file read showed the state of a game.** At the points where the game copy was compared (listed in the Answer), only `Isledft.dat` and `Islepro.skr` had changed, and only in runs that clicked Save as default or credited a loss. These are snapshots, not a trace of writes during play: no read fell inside the tour's placement, attack or computer turns (E002-r0001, E002-r0020 read the files first at step 111, after leaving the game). A file that held the position during play and was removed or restored before the next read fits them, and so does a state kept only in memory (rows 9 and 10). Where the game keeps the position is therefore not established; the screen is the one source found that shows it.
- **Speed and level are bytes 8 and 14 of `Isledft.dat`.** The only action that differs between E002-r0004/E002-r0005 and E002-r0010 to E002-r0013 is the speed label clicked, and the only byte that differs is offset 8, taking the value of the label's position in its row (FAST 1, NORMAL 2, SLOW 3). The same holds for the level and offset 14. The runs agree with each other (2 and 2) and with the control.
- **`Islepro.skr` stores `0x5e` plus the ASCII of a comma-separated list.** The distinct values `0x8a`, `0x8e` and `0x8f` stand in the pattern of a list of one-digit numbers separated by a separator; after a credited loss one byte goes from `0x8e` to `0x8f` while one scoreboard cell goes from 0 to 1, and the displayed scoreboard has one cell of 1 and the rest 0. A different encoding with the same three values would fit the data; the shift is proposed, and it is checked on three values only (E002-r0001, E002-r0014 to E002-r0017, E002-r0020).
- **The game writes the trailing comma that the shipped files lack.** Both shipped files are one byte shorter than the game's own output (15 and 13 bytes, against 16 and 14): every write seen left the file one byte longer, ending in that byte (`Isledft.dat` E002-r0004 to E002-r0013, `Islepro.skr` E002-r0001, E002-r0014 to E002-r0017, E002-r0020). Writes in other situations were not seen.
- **Frequency is unvaried.** MORE, NEVER and LESS all show the lock message (E002-r0001, E002-r0023, E002-r0024), so no run could move its byte, which is why the frequency field of `Isledft.dat` has no offset.
- **The panel's figure beside a colour does not track the board turn by turn.** In E002-r0020 the figure beside Blue is 9 when the attack is ready and 1 after the conquest, in the same turn, and in E002-r0018 it reads 1 at the start of a human turn while the board shows several Blue countries (E002-r0018 `21ec1cc6a5b27ea0-human-turn.png`). This is a caution for anyone reading the panel as a count; what the figure counts is not established here.

## Alternatives considered

- **The two files, or another file, hold game state during play.** Not excluded. The game copy was compared only at the points listed in the Answer, never during the tour's placement, attack, conquest, pass or computer turns, and no run played to the end. At those points no file but the two had changed, and the two only by Save as default or a credited loss. A write during play that was undone before the next read would not show.
- **The byte at offset 8 is not the speed but another option that the speed click side-effects.** Excluded by the other arms: the only action that moves offset 8 is the speed, and the level and control arms leave it at `2`; but a hidden coupling inside the speed row is not excluded.
- **The Easy loss notice is absent because the click missed.** Excluded by the screenshot: the screen after the click equals the setup screen (`fc16ec81edd4a681`, E002-r0018), which is where New Game leads. A different cause for no notice (a threshold on the number of countries held, as the notice text says) is consistent with the boards, but this finding does not test it.
- **The kill path's 30 s wait is the game's.** Not excluded: the processes that remain were not named. It is the driver's wait, not a measurement of the game.
- **Offsets 10 and 12 of `Isledft.dat` are the frequency and the starting armies.** Not tested and not claimed: only the order of the Options screen suggests it, and the lock means no run could vary either.

## What this does not establish

- Any rule: how combat, reinforcement, cards or hazards work (out of scope; sources only).
- Where the game keeps the position during play: the game copy was compared at sampled points only (see the Answer), and memory was not read.
- What any byte of `Isledft.dat` other than offsets 8 and 14 means, what any byte of `Islepro.skr` other than offsets 6 and 10 means, or what `Islepro.dat` holds.
- That a won game credits a win in `Islepro.skr`, or that an Easy loss does. Neither was produced.
- That there is no save or load in the registered build, or behind a keyboard shortcut, or after a game ends.
- Anything about the DOS game (rule 19; its inventory is a separate task) or about the registered Windows build.
- Anything about native Windows (V3): timings are Wine's.
- What the memory or the Director movie would show (classified, not read).
- That the board's start is random in the statistical sense: only that no two of the 10 board screenshots at the first human turn (E002-r0001, E002-r0014 to E002-r0022) were alike.

## Where the evidence is

The run records are `runs/E002/E002-r0001.json` to `E002-r0024.json`; the manifests are `evidence/E002/E002-r0001.manifest.json` to `E002-r0024.manifest.json`, naming the bundles of release `E002` (screenshots, `changes.log`, `run.log`, `wine.log`); no bundle is committed. Machine-local exploration outputs (sessions that found the click positions) are committed under `experiments/E002-iwp-state-inventory/measurements/explore/`, with a table of the captures by hash; they are not evidence for this finding. The run table and the file bytes are `experiments/E002-iwp-state-inventory/measurements/run-table.md` and `file-bytes.md`.

## Reproduction

From a clean clone on a machine whose preflight passes for the task's `Runs on`, with `IWP_PREFIX`, `IWP_DIR` and `E002_BUNDLES` exported and the shell's `DBUS_SESSION_BUS_ADDRESS` unset or valid:

```text
bash setup/iwp/iwp-runtime.sh
python3 runtime/iwp/spike/cycle.py --experiment E002 --arm <arm> \
  --script experiments/E002-iwp-state-inventory/scripts/<arm>.steps [--may-write-saved-files] --terminate kill
python3 experiments/E002-iwp-state-inventory/measurements/make_tables.py
python3 tools/register_artifact.py check "$IWP_DIR" iwp-2.0-996e86c5
```

`--may-write-saved-files` is for the `opt-*`, `loss-*` and `tour` arms, and `--terminate ui-quit` for `tour`; each script's first lines name its own arguments.
