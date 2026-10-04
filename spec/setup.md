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
levels (C-SET-04).

## Claims

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-SET-01 | No way to save or load a game was found: no title-screen or board label offers one, a game quit in the middle leaves only the scoreboard credit in the game's files, and the directions never mention saving. Not shown: that none exists (keyboard shortcuts, the end of a game and the registered build were not tried), or where the position is held during play. | supported | Pro, set `iwp-2.0-de5a82a2`, unregistered; Wine 9.0; the screens and runs of E002 (Q-SET-05) | observed | [F003](../findings/F003-iwp-observable-state-inventory.md) |
| C-SET-02 | The Options and New Game setup screens share one layout: Number of Starting Armies Possible (1, 3, 5, 7, 10; default 3), Colors of Human or Computer Opponents (BLUE, YELLOW, RED, GREEN, each H or C; BLUE H, the others C), Starting Level Position Strength (HARD, NORMAL, EASY; NORMAL), Frequency of Production and Disaster Messages (MORE, NORMAL, LESS, NEVER; NORMAL), Game Playing Speed (FAST, NORMAL, SLOW; NORMAL). Changing the starting armies, a colour to human, or the frequency shows "available only in the Registered Version"; speed and level are not locked. | supported | Pro, as C-SET-01; the controls named were clicked (starting armies 5; Yellow human; frequency LESS, MORE, NEVER) | observed | [F003](../findings/F003-iwp-observable-state-inventory.md) |
| C-SET-03 | Save as default writes the options to `xtras/Isledft.dat` (speed and starting level decoded: R002, R003), and a loss credited by New Game in the middle of a game at NORMAL or HARD is written to `xtras/Islepro.skr` (R006). At EASY the same action brought no loss notice and changed no file. These two are the only game files seen to change, at the sampled comparison points. | supported | Pro, as C-SET-01; files compared at sampled points only, not traced during play | observed, parsed | [F003](../findings/F003-iwp-observable-state-inventory.md) |
| C-SET-04 | The first screen at which the game waits for input is its map with an option box: three buttons, Set level, Default and a load-saved-game button, and the words "choose option". A click on Set level brings up the Select level dialog: Easy, Normal, Hard, Hardest. The screens before it (a publisher logo, a "presents" screen, the title) pass with no input; they were seen in exploration, not in the run records. Default and the load-saved-game button were not tried by a record. | supported | DOS, set `iw-dos-3.1-30121376`, shareware 3.1; DOSBox-X 2024.03.01 on Xvfb (V2) | observed | [F005](../findings/F005-iw-dos-runtime-dosbox-x.md) |
