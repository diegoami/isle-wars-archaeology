# Setup

Written by the main session at promotion, never by a research task. The summary describes only
`supported` and `corroborated` claims. Everything else stays in the table.

## Summary

*Isle Wars Pro*, unregistered 2.0 under Wine: the Options and New Game setup screens share one
layout of five controls, and the build locks three of them (C-SET-02). Save as default writes the
speed and the starting level to `xtras/Isledft.dat`, and a credited loss is written to the scoreboard
file `xtras/Islepro.skr` (C-SET-03; the layouts are R001 to R007). No save or load was found on the
screens and runs tried; that none exists is not shown (C-SET-01).

DOS *Isle Wars*, shareware 3.1 under DOSBox-X: the first screen that waits for input is the map with
an option box of Set level, Default and a load-saved-game button; Set level opens a dialog of four
levels (C-SET-04). Set level then offers starting armies 1, 3, 6 or 10, written to `ISLEWAR.DFT`
(C-SET-05). Unlike Pro, DOS *Isle Wars* saves a position to `ISLEWAR.SAV` and loads it back, with
the owners of all 46 countries restored (C-SET-06).

## Claims

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-SET-01 | No way to save or load a game was found: no title-screen or board label offers one, a game quit in the middle leaves only the scoreboard credit in the game's files, and the directions never mention saving. Not shown: that none exists (keyboard shortcuts, the end of a game and the registered build were not tried), or where the position is held during play. | supported | Pro, set `iwp-2.0-de5a82a2`, unregistered; Wine 9.0; the screens and runs of E002 (Q-SET-05) | observed | [F003](../findings/F003-iwp-observable-state-inventory.md) |
| C-SET-02 | The Options and New Game setup screens share one layout: Number of Starting Armies Possible (1, 3, 5, 7, 10; default 3), Colors of Human or Computer Opponents (BLUE, YELLOW, RED, GREEN, each H or C; BLUE H, the others C), Starting Level Position Strength (HARD, NORMAL, EASY; NORMAL), Frequency of Production and Disaster Messages (MORE, NORMAL, LESS, NEVER; NORMAL), Game Playing Speed (FAST, NORMAL, SLOW; NORMAL). Changing the starting armies, a colour to human, or the frequency shows "available only in the Registered Version"; speed and level are not locked. | supported | Pro, as C-SET-01; the controls named were clicked (starting armies 5; Yellow human; frequency LESS, MORE, NEVER) | observed | [F003](../findings/F003-iwp-observable-state-inventory.md) |
| C-SET-03 | Save as default writes the options to `xtras/Isledft.dat` (speed and starting level decoded: R002, R003), and a loss credited by New Game in the middle of a game at NORMAL or HARD is written to `xtras/Islepro.skr` (R006). At EASY the same action brought no loss notice and changed no file. These two are the only game files seen to change, at the sampled comparison points. | supported | Pro, as C-SET-01; files compared at sampled points only, not traced during play | observed, parsed | [F003](../findings/F003-iwp-observable-state-inventory.md) |
| C-SET-04 | The first screen at which the game waits for input is its map with an option box: three buttons, Set level, Default and a load-saved-game button, and the words "choose option". A click on Set level brings up the Select level dialog: Easy, Normal, Hard, Hardest. The screens before it (a publisher logo, a "presents" screen, the title) pass with no input; they were seen in exploration, not in the run records. Default and the load-saved-game button were not tried by a record. | supported | DOS, set `iw-dos-3.1-30121376`, shareware 3.1; DOSBox-X 2024.03.01 on Xvfb (V2) | observed | [F005](../findings/F005-iw-dos-runtime-dosbox-x.md) |
| C-SET-05 | Set level offers Easy, Normal, Hard and Hardest, then starting armies 1, 3, 6 or 10; Default skips both. The choice is written to `ISLEWAR.DFT` (R009–R014), and the next screen is the board with `ANYKEY TO START GAME`. | supported | DOS, set `iw-dos-3.1-30121376`, shareware 3.1; DOSBox-X 2024.03.01 on Xvfb (V2) | observed | [F007](../findings/F007-iw-dos-observable-state-inventory.md) |
| C-SET-06 | The game saves and loads a position. Save, at the start of a human turn, shows `GAME SAVED` and writes `ISLEWAR.SAV` (R017–R023); Load saved game on the option box brings back the saved owners (R024); with no save it shows `NO SAVED GAME FOUND`. Armies, cards and the turn after a load were not compared. Contrast C-SET-01: none was found in *Isle Wars Pro*'s unregistered build. | supported | DOS, set `iw-dos-3.1-30121376`, shareware 3.1; DOSBox-X 2024.03.01 on Xvfb (V2); Q-SET-05 | observed, parsed | [F007](../findings/F007-iw-dos-observable-state-inventory.md) |
