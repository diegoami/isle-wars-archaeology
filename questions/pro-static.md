# Pro questions mapped to their Lingo handlers

The 131 questions of [malpaco.md](malpaco.md), mapped for *Isle Wars Pro* (the Windows game) to the decompiled Lingo that most likely answers each, to the planned task that reads it, and to the way ordinary play on Pro can corroborate it. It is built for the reading tasks (T20, T21, T22, T23, T24, T27, T32, T33, T34) and for T28, which corroborates their readings from recorded play. **A map is not a finding.** No row says what a rule is; a row says where to look. Every question stays `unknown` until a reviewed finding answers it, and nothing here changes [knowledge-map.md](../knowledge-map.md) or `spec/`.

Basis: the scripts of `Islepro.exe` (sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`) as inventoried in [E008](../experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json): 213 scripts, of which 34 are movie scripts, 87 behaviour scripts and 92 cast scripts. The map was made by reading the decompiled scripts on the owner's machine. No line of them is quoted here (CLAUDE.md rule 18): scripts and handlers are cited by kind, number, name and handler name only. The stage score, which fixes the order of frames, and the cast members, which hold the images, sounds and text styles, are not decoded, so a flow or a look question is never rated `high` on the scripts alone.

## How to read a row

- **Sources.** A script is cited as `` `Kind N Name` `` and its handler as `` `handler()` ``. A short phrase says why it is a source, never what it does. `none found` says what was searched.
- **Task.** The planned task that reads it (T32 board, T33 deal and starting state, T34 setup, seats, files and randomness, T20 combat, T21 reinforcement and islands, T22 cards, T23 centres and hazards, T24 UI, T27 the computer), or `none` with why.
- **Corroboration on Pro.** `play`: recorded ordinary play on the unregistered build can show it, and the cell says what to count. `static-only`: rare, or locked by registration (the registration flag is 0 in the unregistered build), or needing a position that cannot be crafted because the build cannot save. `screen`: a question needing observed screens (T24).
- **Confidence.** `high`, `medium` or `low` that the cited sources answer the question, with the reason (rule 22).

Checked by `python3 tools/check_pro_question_map.py`: the ids and their order against malpaco.md, and that every cited script number, name and handler exists in the E008 inventory.

## Summary

129 questions mapped, 2 dropped as DOS-only (below).

| Task | Questions |
| --- | --- |
| T32 | 12 |
| T33 | 7 |
| T34 | 11 |
| T20 | 17 |
| T21 | 7 |
| T22 | 9 |
| T23 | 15 |
| T24 | 23 |
| T27 | 5 |
| none | 24 |

| Corroboration on Pro | Questions |
| --- | --- |
| play | 75 |
| static-only | 18 |
| screen | 36 |

| Confidence | Questions |
| --- | --- |
| high | 56 |
| medium | 59 |
| low | 14 |

- **P1 questions with no source** (`none found`): Q-AI-07. Of the 43 P1 questions, 11 are `none`-tasked.
- **Questions with no source at any priority:** Q-AI-07, Q-RND-01, Q-UI-14, Q-UI-21.
- **A gap in the plan.** The 21 questions on turn order, victory, and concession have no planned task: no task in T20 to T34 reads the turn frames, the end-of-game and concession scripts. They include 9 P1 questions (the stalemate cluster: Q-VIC-01, Q-VIC-02, Q-VIC-03, Q-VIC-04, Q-VIC-05, Q-VIC-06, Q-SUR-01, Q-SUR-03, Q-SUR-04). They need a task before T28 can corroborate them.
- **Questions that are results rather than rules** (`none` with a reason): Q-TRN-05, Q-REI-05, Q-AI-07. The handlers give inputs and mechanisms; the answer is measured over many games.

## Rules and constants

### Setup

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-SET-01 | `BehaviorScript 457` / `exitFrame()`; `BehaviorScript 479` / `exitFrame()`; `BehaviorScript 496 startingnumarmybehavior` / `mouseDown()`; `BehaviorScript 498 STRENGTHbehavior` / `mouseDown()`; `BehaviorScript 499 FREQbehavior` / `mouseDown()`; `BehaviorScript 500 SPEEDbehavior` / `mouseDown()`; `MovieScript 458 getdefaults` / `Getdefaults()` (the options screen and its option buttons) | T34 | screen: walk the options screen and count each control, its choices and its default | high: the option handlers are small and read in full |
| Q-SET-02 | `MovieScript 480 checkupg` / `CHECKUPG()`; `MovieScript 458 getdefaults` / `Getdefaults()`; `CastScript 568 HumanH` / `mouseDown()`; `CastScript 569 ComputerC` / `mouseDown()`; `BehaviorScript 496 startingnumarmybehavior` / `mouseDown()`; `BehaviorScript 499 FREQbehavior` / `mouseDown()`; `BehaviorScript 473` / `exitFrame()` (the registration check and the notices it gates) | T34 | static-only: the locks follow from the registration check; the notices can also be seen on screen | medium: the gates found are listed, what registration unlocks beyond them stays unknown |
| Q-SET-03 | `BehaviorScript 499 FREQbehavior` / `mouseDown()`; `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 3` / `exitFrame()` (event frequency option and the start-of-game frame) | T23 | static-only: the frequency option is locked in the unregistered build; count whether any control exists | medium: an option for events was found; none was found for centres or cards, an absence claim |
| Q-SET-04 | `BehaviorScript 457` / `exitFrame()`; `BehaviorScript 479` / `exitFrame()`; `BehaviorScript 496 startingnumarmybehavior` / `mouseDown()`; `BehaviorScript 498 STRENGTHbehavior` / `mouseDown()`; `BehaviorScript 499 FREQbehavior` / `mouseDown()`; `BehaviorScript 500 SPEEDbehavior` / `mouseDown()` (every option handler read; the list of options is the evidence) | T20 | screen: list the controls on the options screen | high: the option handlers are small and fully read |
| Q-SET-05 | `MovieScript 458 getdefaults` / `Getdefaults()`, `SaveDefaults()`; `MovieScript 455 WRITESCORES` / `writescores()`; `MovieScript 471 READSCORES` / `READSCORES()`; `MovieScript 339 bottombuttons` / `Bottombuttons()` (the only file handlers and the menu buttons) | T34 | screen: walk the menu bar and the options screen for a save or load control | medium: absence claim from the file handlers; the registered build is not read |
| Q-SET-06 | `MovieScript 458 getdefaults` / `Getdefaults()`, `SaveDefaults()`; `MovieScript 455 WRITESCORES` / `writescores()`; `MovieScript 471 READSCORES` / `READSCORES()`; `MovieScript 339 bottombuttons` / `Bottombuttons()` (the only file handlers and the menu buttons) | T34 | screen: walk the menus for an export or import control | medium: absence claim from the file handlers |
| Q-SET-07 | `MovieScript 458 getdefaults` / `Getdefaults()`; `MovieScript 471 READSCORES` / `READSCORES()`; `MovieScript 480 checkupg` / `CHECKUPG()` (the three small files the game reads) | T34 | static-only: the file layouts are in the code; loading across games needs DOS, which is dropped (rule 19) | medium: the Pro half only |

### Players

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-PLY-01 | `MovieScript 1 Startmovie` / `startMovie()`; `CastScript 568 HumanH` / `mouseDown()`; `CastScript 569 ComputerC` / `mouseDown()`; `BehaviorScript 457` / `exitFrame()` (the seat slots and the seat toggles) | T34 | static-only: seat counts are fixed by the code and the toggles are locked by registration | high: the seat code is short and read in full |
| Q-PLY-02 | `CastScript 568 HumanH` / `mouseDown()`; `CastScript 569 ComputerC` / `mouseDown()`; `MovieScript 458 getdefaults` / `Getdefaults()`; `MovieScript 75` / `PutinInfo()`; `BehaviorScript 506` / `exitFrame()` (seat toggles, the defaults reset and the play-out after elimination) | T34 | static-only: the seat toggles are locked by registration; the play-out after elimination can be recorded | high: the handlers are short and read in full |
| Q-PLY-03 | `MovieScript 458 getdefaults` / `Getdefaults()`; `MovieScript 1 Startmovie` / `startMovie()` (defaults read from the defaults file, which startMovie creates if missing) | T34 | screen: open the options screen from a fresh state and note the defaults | high: short handlers read in full |
| Q-PLY-04 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the colour list and the colour-keyed cast members) | T24 | screen: count the colours on the board and the options screen | medium: the look of the colours is in the cast and score, not decoded |

### Map and topology

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-MAP-02 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (island and border tables built at start) | T32 | play: count the territories and the islands on the board display | high: the tables are listed in full |
| Q-MAP-03 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (island member tables and the island bonus loop) | T32 | play: list each island and its member territories on the board | high: the tables are listed in full |
| Q-MAP-04 | `MovieScript 1 Startmovie` / `startMovie()`; `BehaviorScript 400` / `mouseDown()`; `MovieScript 335 GetValidArmys` / `GetvalidArmys()` (border tables and the adjacency checks that use them) | T32 | play: select a territory and try each neighbour, including across water | medium: the tables hold only neighbour lists; any land or water distinction is not visible in them |
| Q-MAP-05 | `MovieScript 1 Startmovie` / `startMovie()` (the border tables) | T32 | play: test a sample of pairs in both directions | high: a table property that a script over the extracted tables can check |
| Q-MAP-06 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 23 Newgame` / `Newgame()` (the board tables and the deal) | T32 (board half), T33 (deal half) | play: start at least 10 games and compare the board shape and the deal | high: the tables and the deal are read in full |
| Q-MAP-07 | `BehaviorScript 457` / `exitFrame()`; `BehaviorScript 479` / `exitFrame()`; `MovieScript 1 Startmovie` / `startMovie()` (the options screen and the board tables) | T32 | screen: look for a board size control on the options screen | medium: absence claim |
| Q-MAP-08 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 5 Putinboard` / `Putinboard()` (the board tables and the deal) | T32 | play: start several games and compare the board layout | medium: absence claim |
| Q-MAP-09 | `MovieScript 1 Startmovie` / `startMovie()` (the border tables) | T32 | play: count the crossings on the board display | medium: absence claim |
| Q-MAP-10 | `MovieScript 5 Putinboard` / `Putinboard()` (the deal and the cap on territories per player) | T32 (board half), T33 (deal half) | play: compare the starting holdings over at least 10 starts | medium: the deal is read in full but its balance is a statistical property |
| Q-MAP-11 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 5 Putinboard` / `Putinboard()` (the board tables and the deal) | T32 | play: start at least 20 games and compare the counts | medium: absence claim |
| Q-MAP-12 | `MovieScript 1 Startmovie` / `startMovie()` (the border tables) | T32 | play: move along a path between sample territories | high: a table property that a script over the extracted tables can check |
| Q-MAP-13 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (island tables and the bonus loop) | T21 | play: read the bonus message when a small island is held | high: the tables and the loop are read in full |
| Q-MAP-14 | `MovieScript 1 Startmovie` / `startMovie()` (the board tables) | T32 | play: count the territories on the board display | high: the tables are listed in full |

### Starting state

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-STA-01 | `MovieScript 5 Putinboard` / `Putinboard()`; `BehaviorScript 3` / `exitFrame()` (the deal and the start-of-game frame) | T33 | play: record each seat's initial territories over at least 10 games | high: the deal is read in full |
| Q-STA-02 | `MovieScript 5 Putinboard` / `Putinboard()`; `BehaviorScript 496 startingnumarmybehavior` / `mouseDown()` (the deal and the starting-armies option) | T33 | play: read the army figure on every territory straight after the deal, over at least 10 games | high: the deal is read in full |
| Q-STA-03 | `MovieScript 5 Putinboard` / `Putinboard()`; `BehaviorScript 3` / `exitFrame()`; `BehaviorScript 2` / `exitFrame()` (the start-of-game frames) | T33 | play: watch the start of games and count any placement steps | medium: absence claim; the frame order is in the score, not decoded |
| Q-STA-04 | `MovieScript 5 Putinboard` / `Putinboard()`; `BehaviorScript 498 STRENGTHbehavior` / `mouseDown()` (the deal and the difficulty option that it reads) | T33 | play: record each seat's territories and armies after setup at each difficulty | medium: the answer depends on how the difficulty value is used in the deal |
| Q-STA-05 | `MovieScript 458 getdefaults` / `Getdefaults()`; `MovieScript 471 READSCORES` / `READSCORES()` (the only file handlers) | T33 | screen: search the menus for a load or scenario entry | medium: absence claim |

### Turn sequence

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-TRN-01 | `MovieScript 10 Checkturn` / `CheckTurn()`; `BehaviorScript 14` / `exitFrame()`; `BehaviorScript 26` / `exitFrame()`; `BehaviorScript 43` / `exitFrame()`; `BehaviorScript 76` / `exitFrame()`; `BehaviorScript 342` / `exitFrame()` (the turn frame scripts) | none: no planned task reads the turn, victory and concession scripts | play: record the order of actions over several full turns | medium: the jumps between frames are labels in the score, which is not decoded |
| Q-TRN-02 | `MovieScript 10 Checkturn` / `CheckTurn()`; `MovieScript 399 WHOGOESFIRST` / `WHOGOESFIRST()`; `MovieScript 5 Putinboard` / `Putinboard()` (next-player step and the first-turn draw) | none: no planned task reads the turn, victory and concession scripts | play: record the order of turns over at least 10 rounds | high: short handlers read in full |
| Q-TRN-03 | `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 54` / `exitFrame()` (the event frames) | T23 | screen: play with events set to never and note the turn display | low: depends on Q-SET-03, which is locked in the unregistered build |
| Q-TRN-04 | `MovieScript 10 Checkturn` / `CheckTurn()`; `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 461` / `exitFrame()` (a turn counter and where it is used) | none: no planned task reads the turn, victory and concession scripts | play: watch for a displayed counter over two rounds | medium: whether it is displayed is not in the code read |
| Q-TRN-05 | `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 463` / `exitFrame()`; `MovieScript 10 Checkturn` / `CheckTurn()` (the end-of-game conditions only) | none: a game length is measured over many games, not read from a handler | play: record the turns and minutes per game | low: the handlers give end conditions, not lengths |

### Reinforcement and resources

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-REI-01 | `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the income calculation) | T21 | play: read the placement message at several territory counts | high: one handler, read in full |
| Q-REI-02 | `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the income calculation) | T21 | play: read the placement message at 1, 2 and 3 territories | high: one handler, read in full |
| Q-REI-03 | `BehaviorScript 11` / `exitFrame()`; `BehaviorScript 13` / `exitFrame()`; `BehaviorScript 400` / `mouseDown()`; `CastScript 89 place2` / `mouseDown()`; `CastScript 85 plus2` / `mouseDown()`; `CastScript 87 min2` / `mouseDown()`; `CastScript 83 Pall2` / `mouseDown()`; `CastScript 96 DONE2` / `mouseDown()` (the placement frame and its buttons) | T21 | play: place armies on several territories and try to end with some unplaced | high: short handlers read in full |
| Q-REI-04 | `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()`; `CastScript 528 tradein2` / `mouseDown()` (income parts and the card trade-in that adds to it) | T21 | play: record the placement message with one component varied | high: both handlers read in full |
| Q-REI-05 | `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()`; `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the inputs to army growth and loss) | none: growth over a game is an emergent result, not one handler | play: record each player's total armies and largest stack each round | low: the code gives the inputs only |

### Movement

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-MOV-01 | `BehaviorScript 76` / `exitFrame()`; `BehaviorScript 400` / `mouseDown()`; `CastScript 64 Movebut2` / `mouseDown()`; `CastScript 332 DONE3` / `mouseDown()`; `MovieScript 338 MakeComputerMove` / `MakeComputerMove()` (the move frames and the computer's move step) | T20 | play: make successive moves in one turn and note when the game stops them | medium: the frame order is in the score, not decoded |
| Q-MOV-02 | `BehaviorScript 400` / `mouseDown()`; `CastScript 332 DONE3` / `mouseDown()`; `CastScript 96 DONE2` / `mouseDown()`; `BehaviorScript 60` / `exitFrame()` (the move and move-in handlers) | T20 | play: try to move all, all but one and all but two armies from stacks of 2, 3 and 10 | high: short handlers read in full |
| Q-MOV-03 | `BehaviorScript 400` / `mouseDown()`; `BehaviorScript 76` / `exitFrame()`; `BehaviorScript 77` / `exitFrame()`; `BehaviorScript 78` / `exitFrame()`; `CastScript 332 DONE3` / `mouseDown()` (the move selection frames) | T20 | play: move a stack and try to move it on, and to a territory two away | medium: the frame order is in the score, not decoded |

### Combat

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-CMB-01 | `BehaviorScript 400` / `mouseDown()`; `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 335 GetValidArmys` / `GetvalidArmys()`; `CastScript 74 Attack4` / `mouseDown()` (the human attack-from check and the computer's candidate test) | T20 | play: attack from N armies against N-1, N, N+1 and N+2 and note which are offered | high: the checks are read in full |
| Q-CMB-02 | `BehaviorScript 400` / `mouseDown()`; `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the compared quantities in the human and computer checks) | T20 | play: repeat the boundary test at N = 4, 8, 12 and 20 | medium: each check uses fixed quantities, so scaling follows from reading them |
| Q-CMB-03 | `BehaviorScript 400` / `mouseDown()`; `MovieScript 335 GetValidArmys` / `GetvalidArmys()`; `MovieScript 334 Computerattack` / `Computerattack()` (the minimum tests) | T20 | play: try to attack from territories of 1, 2 and 3 armies | high: the checks are read in full |
| Q-CMB-04 | `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the two dice handlers) | T20 | play: count exchanges and losses per exchange at several army sizes | high: both handlers read in full |
| Q-CMB-05 | `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the two dice handlers) | T20 | play: count exchanges and losses per exchange at several defender sizes | high: both handlers read in full |
| Q-CMB-06 | `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the two dice handlers) | T20 | play: tabulate losses for equal results over at least 500 exchanges | high: both handlers read in full |
| Q-CMB-07 | `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the two dice handlers) | T20 | play: record losses per exchange for at least 200 exchanges at several sizes | high: both handlers read in full |
| Q-CMB-08 | `CastScript 74 Attack4` / `mouseDown()`; `BehaviorScript 47` / `exitFrame()`; `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the attack button, the battle frame and the computer's battle loop) | T20 | play: issue one attack and note whether more exchanges follow without input | high: the handlers are read in full |
| Q-CMB-09 | `MovieScript 81 Lostit` / `Lostit()`; `BehaviorScript 97` / `exitFrame()`; `BehaviorScript 47` / `exitFrame()` (the failed-attack handler and the frames that lead to it) | T20 | play: attack with weak stacks until one fails and record ownership and armies | high: short handlers read in full |
| Q-CMB-10 | `BehaviorScript 14` / `exitFrame()`; `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `BehaviorScript 26` / `exitFrame()`; `BehaviorScript 27` / `exitFrame()` (the computer's attack count per turn (T27 reads it) and the human attack frames) | T20 | play: make as many attacks as allowed in several turns and record what stops them | medium: the human frame order is in the score, not decoded |
| Q-CMB-11 | `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the two dice handlers) | T20 | play: record outcomes at fixed army counts split by condition, at least 500 per condition | medium: absence claim |
| Q-CMB-12 | `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()`; `MovieScript 363 addtoproductioncenter` / `addtoproductioncenter()` (losses, income and bonuses) | T20 | play: record at least 100 attacks per ratio band and the games where one seat never attacks | low: the code gives expected losses, but whether attacking pays also depends on the computer's play |

### Ownership change

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-OWN-01 | `BehaviorScript 60` / `exitFrame()`; `CastScript 96 DONE2` / `mouseDown()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `CastScript 85 plus2` / `mouseDown()` (the human move-in and the computer's split after a capture) | T20 | play: capture from stacks of 2, 3, 5 and 10 and record armies on both territories | high: the handlers are read in full |

### Production centres

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-CEN-01 | `MovieScript 51 putinproductioncenters` / `Putinproductioncenters()`; `BehaviorScript 3` / `exitFrame()` (the centre set-up at the start of a game) | T23 | play: record the number and positions of centres at the start of at least 10 games | high: short handler read in full |
| Q-CEN-02 | `MovieScript 363 addtoproductioncenter` / `addtoproductioncenter()`; `BehaviorScript 54` / `exitFrame()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the centre event; the income handler was searched and holds no centre term) | T23 | static-only: the centre effect appears only in a rare event | medium: absence claim in the income handler |
| Q-CEN-03 | `BehaviorScript 54` / `exitFrame()`; `MovieScript 51 putinproductioncenters` / `Putinproductioncenters()`; `BehaviorScript 4` / `exitFrame()` (the event that re-places centres and the frame that triggers events) | T23 | static-only: centre moves are rare events | high: short handlers read in full |
| Q-CEN-04 | `MovieScript 51 putinproductioncenters` / `Putinproductioncenters()`; `BehaviorScript 3` / `exitFrame()` (the centre set-up) | T23 | play: restart at least 10 times and record the centre positions | high: short handler read in full |
| Q-CEN-05 | `MovieScript 363 addtoproductioncenter` / `addtoproductioncenter()`; `MovieScript 51 putinproductioncenters` / `Putinproductioncenters()`; `BehaviorScript 54` / `exitFrame()` (the centre event and the re-placement) | T23 | static-only: centre moves are rare events | medium: depends on how the effect is tied to the position, read from a short handler |

### Bonuses (island/continent groups, cards)

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-BON-01 | `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the island loop) | T21 | play: compare the placement message with all of an island and all but one | high: one handler, read in full |
| Q-BON-02 | `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()`; `MovieScript 1 Startmovie` / `startMovie()` (the island loop and the island tables) | T21 | play: read the placement message for each island held | high: the loop and the tables are read in full |
| Q-BON-03 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 345 SELECTACARD` / `SELECTACARD()`; `MovieScript 344 PUTINCARDS` / `PUTINCARDS()`; `BehaviorScript 358` / `exitFrame()` (the card list, the draw and the display) | T22 | play: play until cards appear and note the kinds | high: the handlers are read in full |
| Q-BON-04 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 345 SELECTACARD` / `SELECTACARD()`; `MovieScript 398 CompCards` / `CompCards()` (the card list and the draw) | T22 | play: tabulate at least 100 draws by kind | high: the list and the draws are read in full |
| Q-BON-05 | `BehaviorScript 14` / `exitFrame()`; `MovieScript 398 CompCards` / `CompCards()`; `CastScript 66 Pass2` / `mouseDown()`; `BehaviorScript 331` / `exitFrame()`; `BehaviorScript 358` / `exitFrame()` (the computer's card step, the human end-of-attack button and the draw frame) | T22 | play: record card gains over turns with 0, 1 and 2 or more captures | high: the handlers are read in full |
| Q-BON-06 | `MovieScript 398 CompCards` / `CompCards()`; `BehaviorScript 342` / `exitFrame()`; `CastScript 376 CARDV1` / `mouseDown()`; `MovieScript 345 SELECTACARD` / `SELECTACARD()` (the full-hand branches) | T22 | play: collect cards until the limit and note the effect on a further draw | high: the handlers are read in full |
| Q-BON-07 | `MovieScript 366 CheckCardMatch` / `CheckCardMatch()`; `BehaviorScript 526 pick3cards` / `mouseDown()`; `CastScript 528 tradein2` / `mouseDown()`; `BehaviorScript 367` / `exitFrame()` (the match check, the card selection and the trade-in) | T22 | play: hold several matches and try more than one trade-in in a turn | medium: the frame order is in the score, not decoded |
| Q-BON-08 | `BehaviorScript 372` / `exitFrame()`; `BehaviorScript 400` / `mouseDown()`; `CastScript 528 tradein2` / `mouseDown()`; `MovieScript 397 CompCheckCardMatch` / `CompCheckCardMatch()`; `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()` (the bomb branches for the human and the computer) | T22 | play: play the bomb card and record its effect | high: the handlers are read in full |
| Q-BON-09 | `BehaviorScript 400` / `mouseDown()`; `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()`; `MovieScript 532 Reordercards` / `Reordercards()` (the anti-bomb checks and the card removal) | T22 | play: bomb a player holding the protective card and record the outcome | medium: only the protection against bombing was found |
| Q-BON-10 | `CastScript 528 tradein2` / `mouseDown()`; `MovieScript 397 CompCheckCardMatch` / `CompCheckCardMatch()`; `MovieScript 366 CheckCardMatch` / `CheckCardMatch()` (the trade-in effect branches) | T22 | play: trade in each match kind and record the effect | medium: absence claim for a movement card |
| Q-BON-11 | `CastScript 528 tradein2` / `mouseDown()`; `MovieScript 366 CheckCardMatch` / `CheckCardMatch()`; `BehaviorScript 526 pick3cards` / `mouseDown()`; `MovieScript 397 CompCheckCardMatch` / `CompCheckCardMatch()` (the trade-in and match code) | T22 | play: collect cards and trade in at least three times, recording the armies | high: the handlers are read in full |

### Hazards

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-HAZ-01 | `BehaviorScript 54` / `exitFrame()`; `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 364 PutinFlood` / `putinflood()`; `MovieScript 365 Putinrebellion` / `putinrebellion()`; `MovieScript 363 addtoproductioncenter` / `addtoproductioncenter()` (the event table and the event handlers) | T23 | play: play at least 30 turns, logging every event message | high: the handlers are read in full |
| Q-HAZ-02 | `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 54` / `exitFrame()` (the frame that decides events and the event frame) | T23 | play: timestamp each event against the turn sequence | medium: the frame order is in the score, not decoded |
| Q-HAZ-03 | `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 54` / `exitFrame()`; `BehaviorScript 499 FREQbehavior` / `mouseDown()`; `MovieScript 458 getdefaults` / `Getdefaults()` (the event chance, its setting and the unregistered lock) | T23 | play: count events over at least 500 player-turns at the one setting the unregistered build allows | high: the handlers are read in full |
| Q-HAZ-04 | `MovieScript 364 PutinFlood` / `putinflood()`; `BehaviorScript 54` / `exitFrame()` (the event handler) | T23 | static-only: rare event; log the victims if enough are seen | high: one handler, read in full |
| Q-HAZ-05 | `MovieScript 364 PutinFlood` / `putinflood()`; `BehaviorScript 54` / `exitFrame()` (the event frame sends the earthquake and flood messages to one handler) | T23 | static-only: rare event | medium: no separate earthquake code was found |
| Q-HAZ-06 | `MovieScript 365 Putinrebellion` / `putinrebellion()`; `MovieScript 364 PutinFlood` / `putinflood()`; `BehaviorScript 54` / `exitFrame()` (the two harm handlers and how each picks its victim) | T23 | static-only: rare events; compare victim rank over many events | high: the handlers are read in full |
| Q-HAZ-07 | `MovieScript 364 PutinFlood` / `putinflood()`; `MovieScript 365 Putinrebellion` / `putinrebellion()`; `BehaviorScript 54` / `exitFrame()` (the floors and eligibility tests in the harm handlers) | T23 | static-only: rare events | high: the handlers are read in full |
| Q-HAZ-08 | `BehaviorScript 54` / `exitFrame()`; `MovieScript 363 addtoproductioncenter` / `addtoproductioncenter()`; `MovieScript 365 Putinrebellion` / `putinrebellion()` (the helping and harming events) | T23 | static-only: rare events | high: the handlers are read in full |

### AI

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-AI-01 | `BehaviorScript 14` / `exitFrame()`; `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 335 GetValidArmys` / `GetvalidArmys()`; `MovieScript 336 ATTACKHIM` / `ATTACKHIM()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the computer turn frame and its attack handlers) | T27 | play: record every computer attack (source, target, owner, result) over at least 20 games | high: the handlers are read in full |
| Q-AI-02 | `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()`; `MovieScript 397 CompCheckCardMatch` / `CompCheckCardMatch()` (the shared income handler and the two dice handlers) | T27 | play: compare the computer's dice results and income with the human formula | medium: the handlers are long; a hidden advantage is an absence claim |
| Q-AI-03 | `BehaviorScript 498 STRENGTHbehavior` / `mouseDown()`; `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 455 WRITESCORES` / `writescores()`; `BehaviorScript 457` / `exitFrame()` (the difficulty option and its only other readers) | T33 | play: start at each difficulty and record the initial holdings | high: the readers of the option are few and read in full |
| Q-AI-04 | `BehaviorScript 14` / `exitFrame()`; `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 335 GetValidArmys` / `GetvalidArmys()` (the computer turn frame and the attack candidate step) | T27 | play: count the computer turns with no attack in recorded games | high: the handlers are read in full |
| Q-AI-05 | `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()` (the long placement handler) | T27 | play: record each computer placement with the neighbouring enemy armies, over at least 100 placements | medium: 903 lines with many branches |
| Q-AI-06 | `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 336 ATTACKHIM` / `ATTACKHIM()`; `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()` (the target scoring in the attack handlers and the island ranking in placement) | T27 | play: log the alternatives and the chosen target for at least 100 attacks | medium: the weighting is spread across handlers |
| Q-AI-07 | none found: strength against scripted opponents is a result of whole games; the computer handlers (searched) give its behaviour, not a win rate | none: a win rate is measured, not read from a handler | play: the driver plays the human seat as a scripted policy against the three computers | low: no handler states a win rate |

### Randomness

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-RND-01 | none found: searched all 213 decompiled scripts for a seed call or seed field; the setup handlers were read | T34 | static-only: no save exists in the unregistered build to compare | medium: absence claim |
| Q-RND-02 | `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()` (the places that draw random values) | T34 | static-only: the unregistered build has no save, so no position can be repeated | medium: the generator itself is outside the Lingo |
| Q-RND-03 | `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 1 Startmovie` / `startMovie()` (the random calls and the absence of a seed call) | T34 | static-only: the generator is inside Director's runtime | medium: the engine side is not in the Lingo |

### Victory and loss

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-VIC-01 | `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 14` / `exitFrame()`; `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 10 Checkturn` / `CheckTurn()` (the end-of-game conditions and the computer's attack frame) | none: no planned task reads the turn, victory and concession scripts | play: record the share of games with no winner at a round cap and the board in each | low: how often a game stalls is a result, the code gives only the mechanisms |
| Q-VIC-02 | `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 463` / `exitFrame()`; `MovieScript 10 Checkturn` / `CheckTurn()` (the end-of-game frames) | none: no planned task reads the turn, victory and concession scripts | play: look for a limit in the options and run a long game | medium: the frame order is in the score, not decoded |
| Q-VIC-03 | `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 470` / `exitFrame()`; `BehaviorScript 4` / `exitFrame()` (the winner selection on the end frames) | none: no planned task reads the turn, victory and concession scripts | static-only: a tie at a limit is rare and a position cannot be crafted in the unregistered build | medium: the handlers are read in full; the frame order is not decoded |
| Q-VIC-04 | `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 54` / `exitFrame()`; `MovieScript 10 Checkturn` / `CheckTurn()` (the events and the end-of-game frame) | none: no planned task reads the turn, victory and concession scripts | play: watch games with no attacks and log what occurs for at least 100 rounds | low: what happens on a locked board is a result of play |
| Q-VIC-05 | `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 465` / `exitFrame()`; `BehaviorScript 470` / `exitFrame()`; `BehaviorScript 4` / `exitFrame()` (the end screens) | none: no planned task reads the turn, victory and concession scripts | play: reach each end screen and note the wording | medium: the screens are in the score |
| Q-VIC-06 | `BehaviorScript 470` / `exitFrame()`; `BehaviorScript 463` / `exitFrame()` (the winner selection) | none: no planned task reads the turn, victory and concession scripts | static-only: needs a limit position that cannot be crafted in the unregistered build | medium: the handlers are read in full |
| Q-VIC-07 | `MovieScript 10 Checkturn` / `CheckTurn()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()`; `BehaviorScript 26` / `exitFrame()`; `BehaviorScript 47` / `exitFrame()` (the all-territories test in several places) | none: no planned task reads the turn, victory and concession scripts | play: capture the last territory partway through a turn and note whether the turn continues | high: the tests are read in full |
| Q-VIC-08 | `MovieScript 10 Checkturn` / `CheckTurn()`; `MovieScript 75` / `PutinInfo()`; `BehaviorScript 506` / `exitFrame()` (the zero-territory handling) | none: no planned task reads the turn, victory and concession scripts | play: eliminate a player holding cards and watch the cards and the turn order | high: short handlers read in full |
| Q-VIC-09 | `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 470` / `exitFrame()` (the territory-count thresholds) | none: no planned task reads the turn, victory and concession scripts | play: reach each count and note when the game ends | high: short handlers read in full |
| Q-VIC-10 | `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 470` / `exitFrame()`; `MovieScript 10 Checkturn` / `CheckTurn()` (the win tests read in full; no objective test was found) | none: no planned task reads the turn, victory and concession scripts | screen: look at the options screen for an objective option | medium: absence claim |
| Q-VIC-11 | `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 4` / `exitFrame()` (the win tests; no income test was found) | none: no planned task reads the turn, victory and concession scripts | screen: look at the options screen for such an option | medium: absence claim |
| Q-VIC-12 | `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 4` / `exitFrame()` (the win tests; no survival test was found) | none: no planned task reads the turn, victory and concession scripts | screen: look at the options screen for such an option | medium: absence claim |
| Q-VIC-13 | `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 4` / `exitFrame()` (the win tests; no named-player test was found) | none: no planned task reads the turn, victory and concession scripts | screen: look at the options screen for such an option | medium: absence claim |
| Q-VIC-14 | `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 470` / `exitFrame()`; `MovieScript 5 Putinboard` / `Putinboard()` (the single winner selection) | none: no planned task reads the turn, victory and concession scripts | screen: look at the setup and briefing screens for per-player goals | medium: absence claim |

### Surrender

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-SUR-01 | `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 465` / `exitFrame()`; `CastScript 609 ACCEPT2` / `mouseUp()`; `CastScript 611 KEEP2` / `mouseUp()`; `BehaviorScript 469` / `exitFrame()` (the frame that raises the offer and its accept and refuse buttons) | none: no planned task reads the turn, victory and concession scripts | play: play toward a winning position and record every prompt | high: short handlers read in full |
| Q-SUR-03 | `BehaviorScript 4` / `exitFrame()`; `BehaviorScript 465` / `exitFrame()` (the trigger test) | none: no planned task reads the turn, victory and concession scripts | play: reach positions with known territory counts and record when the offer appears | high: short handlers read in full |
| Q-SUR-04 | `BehaviorScript 465` / `exitFrame()`; `CastScript 609 ACCEPT2` / `mouseUp()`; `CastScript 611 KEEP2` / `mouseUp()`; `CastScript 615 KEEP3` / `mouseUp()`; `BehaviorScript 469` / `exitFrame()`; `BehaviorScript 4` / `exitFrame()` (the offer text, its two buttons and the flag the refusal sets) | none: no planned task reads the turn, victory and concession scripts | play: accept in some games and refuse in others and record the sequel | high: short handlers read in full |
| Q-SUR-05 | `BehaviorScript 506` / `exitFrame()`; `CastScript 632 ACCEPTLOSS2` / `mouseUp()`; `CastScript 637 HALT1` / `mouseDown()`; `CastScript 347 newgame2` / `mouseUp()`; `BehaviorScript 507` / `exitFrame()`; `MovieScript 75` / `PutinInfo()` (the elimination prompt, the quit-mid-game credit and the play-out) | none: no planned task reads the turn, victory and concession scripts | play: let the human be eliminated and use new game mid-game; record the outcomes | high: short handlers read in full |

## User interface

| Id | Sources | Task | Corroboration on Pro | Confidence |
| --- | --- | --- | --- | --- |
| Q-UI-01 | `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 1 Startmovie` / `startMovie()` (owner-keyed cast members per territory) | T24 | screen: screenshots of the board at the one player count the build allows, and in greyscale | medium: the look is in the cast, which is not decoded |
| Q-UI-02 | `MovieScript 51 putinproductioncenters` / `Putinproductioncenters()`; `MovieScript 363 addtoproductioncenter` / `addtoproductioncenter()` (a flash and a text colour change on the centre) | T24 | screen: screenshots of boards with centres at the default size | medium: the mark itself is in the cast |
| Q-UI-03 | `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 23 Newgame` / `Newgame()` (a per-territory text field filled with the army count) | T24 | screen: annotated screenshots; measure the text height | medium: font and size are in the cast |
| Q-UI-04 | `CastScript 347 newgame2` / `mouseUp()`; `CastScript 355 quit2` / `mouseDown()`; `CastScript 666 exit2` / `mouseUp()`; `CastScript 668 Help2` / `mouseUp()`; `CastScript 353 scores2` / `mouseDown()`; `CastScript 351 soleau2` / `mouseUp()`; `MovieScript 339 bottombuttons` / `Bottombuttons()` (the menu buttons and the screens they open) | T24 | screen: a screenshot of every screen reached by walking each menu path | low: the frame labels and layout are in the score |
| Q-UI-05 | `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the colour list and the colour-keyed text members) | T24 | screen: screenshots, sampled colours and simulated renderings | low: the colour values are in the cast |
| Q-UI-06 | `BehaviorScript 54` / `exitFrame()`; `MovieScript 364 PutinFlood` / `putinflood()`; `MovieScript 365 Putinrebellion` / `putinrebellion()` (the typed event message, a flash and a sound) | T24 | screen: frame-timed recordings of at least 5 events | medium: the timing comes from busy-wait helpers whose length depends on the speed setting |
| Q-UI-07 | `BehaviorScript 54` / `exitFrame()`; `MovieScript 51 putinproductioncenters` / `Putinproductioncenters()` (the event message and the centre flash) | T24 | screen: recordings of at least 5 centre moves | medium: the handlers are read in full |
| Q-UI-08 | `MovieScript 75` / `PutinInfo()`; `BehaviorScript 463` / `exitFrame()` (the territory and card count text fields) | T24 | screen: screenshots of every panel with per-player figures | medium: panel layout is in the score |
| Q-UI-09 | `BehaviorScript 400` / `mouseDown()`; `CastScript 74 Attack4` / `mouseDown()`; `BehaviorScript 43` / `exitFrame()`; `BehaviorScript 44` / `exitFrame()` (the error messages, the sound and the prompts) | T24 | screen: recordings of attempts at each illegal action | medium: highlights are in the cast |
| Q-UI-10 | `BehaviorScript 450` / `exitFrame()`; `BehaviorScript 3` / `exitFrame()`; `CastScript 347 newgame2` / `mouseUp()`; `MovieScript 1 Startmovie` / `startMovie()` (the title, the start and the new-game button) | T24 | screen: three timed walkthroughs with click counts | low: timing and screen order are in the score |
| Q-UI-11 | `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 465` / `exitFrame()`; `BehaviorScript 470` / `exitFrame()`; `BehaviorScript 473` / `exitFrame()`; `BehaviorScript 506` / `exitFrame()` (the end and scores screens) | T24 | screen: screenshots of the end screen after a win, a loss and a concession | medium: the screen layouts are in the score |
| Q-UI-12 | `BehaviorScript 26` / `exitFrame()`; `MovieScript 339 bottombuttons` / `Bottombuttons()`; `BehaviorScript 13` / `exitFrame()`; `BehaviorScript 43` / `exitFrame()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the status texts and the button frames) | T24 | screen: annotated screenshots through one full turn | medium: the layout is in the score |
| Q-UI-13 | `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 336 ATTACKHIM` / `ATTACKHIM()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `MovieScript 338 MakeComputerMove` / `MakeComputerMove()`; `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()` (the computer's status texts, flashes and busy-wait pauses) | T24 | screen: timed recordings of at least 20 computer turns | medium: the pause lengths depend on the speed setting |
| Q-UI-14 | none found: searched all handlers for a stored list of events; only status text fields were found | T24 | screen: screenshots of any log after a long game | medium: absence claim |
| Q-UI-15 | `MovieScript 344 PUTINCARDS` / `PUTINCARDS()`, `PUTINCARDSM()`; `BehaviorScript 526 pick3cards` / `mouseDown()`; `CastScript 376 CARDV1` / `mouseDown()`; `CastScript 528 tradein2` / `mouseDown()`; `BehaviorScript 342` / `exitFrame()` (the hand display, the selection, the trade-in and the discard click) | T24 | screen: screenshots and recordings of holding, playing and discarding cards | medium: the card images and layout are in the cast |
| Q-UI-16 | `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `BehaviorScript 47` / `exitFrame()`; `BehaviorScript 48` / `exitFrame()`; `MovieScript 49 Showstrength` / `showstrength()` (the battle text updates and pauses) | T24 | screen: frame-timed recordings of at least 20 attacks | medium: the pause lengths depend on the speed setting |
| Q-UI-17 | `CastScript 591 ear1` / `mouseUp()`; `BehaviorScript 400` / `mouseDown()`; `MovieScript 50 Rolldice` / `RollDice()`; `BehaviorScript 54` / `exitFrame()` (the sound switch and the places that play sounds) | T24 | screen: a table of events against sounds from recordings | medium: the sound files are in the cast |
| Q-UI-18 | `BehaviorScript 400` / `mouseDown()`; `MovieScript 339 bottombuttons` / `Bottombuttons()`; `BehaviorScript 495` / `exitFrame()`; `MovieScript 494 Getusernames` / `GETUSERNAME()` (the click and key handlers; hover is used for button images) | T24 | screen: a table of inputs against actions and measured hit areas | medium: hit areas are in the score |
| Q-UI-19 | `MovieScript 1 Startmovie` / `startMovie()` (a start-up check of the desktop size) | T24 | screen: screenshots at each supported resolution | low: window and scaling settings belong to the projector, not the Lingo |
| Q-UI-20 | `MovieScript 5 Putinboard` / `Putinboard()` (the text colour set on the territory fields) | T24 | screen: screenshots with measured text height and contrast | low: size, colour values and layout are in the cast and score |
| Q-UI-21 | none found: the board look is bitmaps in the cast, which is not decoded; the handlers only swap them | T24 | screen: reference screenshots in setup, mid-game, battle and end states | low: the look is not in the Lingo |
| Q-UI-22 | `BehaviorScript 499 FREQbehavior` / `mouseDown()`; `BehaviorScript 54` / `exitFrame()` (the event frequency option, the only switchable feature found) | T24 | screen: screenshots with the option on and off | low: the screens are in the score |

## Dropped as DOS-only

These two questions are asked of DOS alone and are dropped from the Pro lane (rule 19): Q-MAP-01, Q-SUR-02.
