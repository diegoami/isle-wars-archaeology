# F009 DOS Isle Wars' ISLEWAR.SAV is seven groups of text lines (the production centres, the level and the starting armies, Speed and Sound, 46 owners, 46 armies, four card counts, four hands), every one shown by a pair of runs that differ in one action or by a crafted save the game loaded and showed; a writer encodes a decoded position into the same bytes, and the game loaded each crafted save and wrote it back byte for byte

- **Status**: proposed
- **Question**: What does each line of DOS *Isle Wars*' `ISLEWAR.SAV` mean, as shown by pairs of runs that differ in one stated action (F007 left the production-centre list, the two DFT values, the other colours' cards, the two constant lines and the last line as candidates or unknown, and R010 and R011 confounded the level with the starting armies); does a writer that encodes a decoded position give the game's own bytes for every natural save; and does the game load a save the writer wrote and show the written values (E007, task T16, W4b follow-on)?
- **Tests claims**: R010, R011, R017, R018, R019, R020, R021, R022, R023, R024, C-SET-05, C-SET-06 (the rows of F007 this finding settles or narrows; it makes no claim about a game rule)
- **Experiment and runs**: E007; runs E007-r0001 … E007-r0046, all in `runs/E007/`. 43 completed and 3 aborted (E007-r0013, E007-r0015, E007-r0024, all the arm `attack-pass`: a click that changed nothing at turn 3, and two attacks that never reached the move-in panel); the aborted records stay, and their saves are in the tables as natural saves. E007-r0028 … E007-r0046 are the 19 runs that load a crafted save (arms `load-*`); the others are natural. The five first records carry a correction (`runs/E007/CORRECTIONS.md`).
- **Artifact**: set `iw-dos-3.1-30121376`, variant none. No run changed a file of the set: every file the game wrote, and every crafted save, is a new file of the run copy, removed by the reset (every record: "run copy after reset equals the run copy before launch: yes"; `setup/iw-dos/iw-dos-runtime.sh` printed `ready` and `register_artifact.py check --strict` exited 0 after the runs: `experiments/E007-iw-dos-save-format/measurements/done-when/`).
- **Max intervention**: I3. The 19 `load-*` runs place a crafted save in the run copy (`vocabulary/interventions.md`: "a crafted or modified save" is I3); each declares it in its record with the sha256 of the position it was written from and of the save. Every other run is I1 (screenshots) and reads the game's own files (I0). Each I3 result is corroborated at I0 below, or says that it is not.
- **Tier reached**: V2 (the original, headless, under DOSBox-X; no real DOS hardware or other emulator, so no V3)
- **Confidence**: supported for every field of the layout, at the shareware 3.1 build under DOSBox-X on one machine, in one day. The level, the starting armies, Speed, Sound and the card counts each moved in line with a stated action in two or more runs and, for Speed, Sound and the counts, also in a crafted save that the game showed. The owners, armies and centres were shown by a crafted save and by natural saves read against the screen (66 natural saves against their screenshots, none differing). The card digits were shown by the picture of each digit's card in two crafted hands, two digits (Wild, 5 Bonus) also by a natural draw. Values outside what was tried (armies above 99, a hand above 5, a level or a starting-armies value other than the four offered, the order of the centres) are not claimed. A save that the game writes after loading a crafted one is the game's own output of what it loaded, not a natural save, and is kept apart in every table.

## Answer

### The layout, each line shown by runs

- **A save is text with CRLF line ends and nothing else.** Every one of the 50 distinct natural saves of E005 and E007 and the 17 distinct saves of the crafted runs decodes into the seven groups below and encodes back to the same bytes: E007-r0001, E007-r0003, E007-r0012, E007-r0014, E007-r0025, E005-r0011, E005-r0037.
- **Line 1 is the number N of production centres, and the next N lines are their country numbers.** The list equals the stars on the screen (the manual's "(*) below the City number") in all 66 natural saves compared with their screenshot, and the stars follow a list that was written: the control E007-r0028 shows stars at 4, 11 and 29, and the crafted list 1, 2, 3 shows them at 1, 2 and 3 and at no other country (E007-r0031). The list is that of the board, not of the turn or the level: it is the same in all the saves of one game, 4 saves and 7 saves (E007-r0012, E007-r0014), after a conquest and a card drawn (E007-r0025, E007-r0026, E007-r0027), and differs between two games started with the same choices (E007-r0001, E007-r0023). What moves a centre inside a game was not found: no action tried did.
- **The next two lines are the level and the starting armies of the game.** The first is 1 at Easy, 2 at Normal, 3 at Hard and 4 at Hardest, in six pairs of runs that change the level alone at 1 starting army: Normal E007-r0002 and E007-r0021, Hard E007-r0003 and E007-r0019, Hardest E007-r0004 and E007-r0020, each against Easy E007-r0001 or E007-r0023 (this settles R010 and R011 for the level). The second is 1, 3, 6 or 10, the starting armies, in the pairs that change the armies alone at Easy (E007-r0005, E007-r0022, E007-r0006, E007-r0007 against E007-r0001 and E007-r0023) and at Hard (E007-r0008 against E007-r0003). A crafted pair 3 and 6 was loaded and the game wrote it into `ISLEWAR.DFT` as ` 3 `, ` 6 `, ` 2 ` (E007-r0034, I3; the same file in the control E007-r0028 reads ` 1 `, ` 1 `, ` 2 `), which says that Load saved game takes the level and the starting armies from these two lines.
- **The next two lines are Speed and Sound.** The first is the Speed value (1 to 9; 2 at launch): Faster once gives 1 (E007-r0009, E007-r0017), Slower once gives 3 (E007-r0010, E007-r0018), and a crafted 5 makes the Speed panel read 5 (E007-r0037, I3). The second is Sound, 0 on and 1 off: one click on Sound gives 1 (E007-r0011, E007-r0016), and a crafted 1 makes the next click on Sound show `ON...` where the control's shows `OFF..` (E007-r0046 against E007-r0045, I3). The third value of `ISLEWAR.DFT` (F007 D4, D5, D6) is the Speed value: ` 1 `, ` 1 `, ` 1 ` after Faster and Save (E007-r0009, E007-r0017), ` 1 `, ` 1 `, ` 3 ` after Slower and Save (E007-r0010, E007-r0018), ` 1 `, ` 1 `, ` 5 ` after Load of the crafted 5 (E007-r0037).
- **The next 46 lines are the owners of countries 1 to 46, as codes 9 Blue, 4 Red, 2 Green and 8 Brown.** A crafted owner shows on the screen: country 2 from Red to Blue (E007-r0029: Blue 18 countries, Red 10, the prompt `PLACE 6 ARMIES`), and country 12 from Blue to Red, Green and Brown (E007-r0039, E007-r0040, E007-r0041); the owners read from the pixels equal the crafted owners in 46 of 46 countries in each of the 19 crafted runs, and every other field the screen shows equals the control's (the table in Observations).
- **The next 46 lines are the army counts of countries 1 to 46.** A crafted count shows: 7 (E007-r0030), 99 (E007-r0032) and 0 (E007-r0033) on country 12, and nothing else of the board differs from the control's but the pointer arrow and the prompt text.
- **The next line, `a , b , c , d`, is the number of cards held by Blue, Red, Green and Brown.** The scoreboard's `C>` figure of each colour equals it in all 68 natural saves that have a screenshot of the turn before the Save (the map from the figure's pixels to the count is one to one: 0, 1, 2 and 3), and a card count written for one colour shows in that colour's row and no other: Blue (E007-r0035), Red (E007-r0042), Green (E007-r0043), Brown (E007-r0044). Each count moves with the computers' turns: a colour's count goes up by one, and its hand grows by one digit, when it draws (E007-r0012, E007-r0014), and Blue's goes from 0 to 1 when Blue conquers a country and passes (E007-r0025, E007-r0026, E007-r0027) and stays 0 when Blue passes without attacking (E007-r0012, E007-r0014).
- **The last line is the cards held, one digit per card, in the order Blue, Green, Red, Brown.** The field of each colour is as long as that colour's count in all 50 natural saves, and no other order of the four fields fits them all (the best other order fits 39 of 50). The digits are the cards: 1 Air Move, 2 Double, 3 Wild, 4 Lose All Cards, 5 15 Bonus, 6 8 Bonus, 7 5 Bonus, 8 a bomb, 9 a bomb crossed out. Blue's hand shows them: a natural draw of 7 shows a `5 BONUS` card and a draw of 3 a `WILD` card (E007-r0025, E007-r0026, E007-r0027), and the hands crafted for Blue show the card of each digit (3, 7, 1, 2, 9: E007-r0036; 4, 5, 6, 8, 3: E007-r0038, I3). A new card is added at the end of the hand (E007-r0012, E007-r0014). Natural saves held only the digits 1, 2, 3 and 7 (E007-r0012, E007-r0014).
- **The game accepted every crafted save and wrote it back unchanged.** In 17 of the 17 crafted runs that did not change a setting after the load, the game's own second Save equals the crafted save byte for byte (E007-r0028, E007-r0029, E007-r0030, E007-r0031, E007-r0032, E007-r0033, E007-r0034, E007-r0035, E007-r0036, E007-r0037, E007-r0038, E007-r0039, E007-r0040, E007-r0041, E007-r0042, E007-r0043, E007-r0044); in the two runs that clicked Sound before the second Save, the second Save equals the crafted save but for the Sound line, as the click says (E007-r0045, E007-r0046). No crafted value was refused or changed by the game.

### The writer

- **The writer writes a position as the game's own bytes.** `runtime/iw-dos/save/savefmt.py` decodes the bytes of a save into a position and encodes a position back, and encode followed by decode returns the position; `encode(decode(bytes))` equals the bytes for each of the 50 distinct natural saves of E005 and E007 (E007-r0001, E007-r0003, E007-r0012, E007-r0014, E007-r0025, E005-r0011, E005-r0037, and the others in `saves/roundtrip.tsv`). It refuses a position outside the values that were seen or tried (the domain is in the module's constants, each with the runs it comes from: static:runtime/iw-dos/save/savefmt.py:35), as in E007-r0032 and E007-r0036.
- **The writer places a save only in a run copy, and only as `ISLEWAR.SAV`.** `runtime/iw-dos/save/writer.py` writes into `<run directory>/game` of a run directory outside every checkout that is not `IW_DOS_DIR` under any name and holds the registered set intact, creating the file new; the cycle's `put-save` step calls it after the launch checks and before Load saved game, and the reset removes the file (E007-r0028, E007-r0029).

## Method

**Artifact.** Set `iw-dos-3.1-30121376`. `setup/iw-dos/iw-dos-runtime.sh` printed `ready` before the runs and again after them; `IW_DOS_DIR` was read and hashed only. Every run is a T11 cycle with its seal unchanged: the run copy checked with `check --strict` before the launch and immediately before it, only the run copy mounted as C:, `IW_DOS_DIR` bound read-only, the whole run in a network namespace of its own, `completed` only on a clean finish. The run directory and the bundle folder were this task's own (another task ran DOSBox-X on the machine; the cycle refuses to start while another run's process is alive, so `scripts/run-arms.sh` waited and tried again, and touched no process but its own).

**Runtime.** `runtime/iw-dos/spike/cycle.py --experiment E007 --steps <script>` at the commit named in each record (E007-r0001 to E007-r0005 at 8edce92, E007-r0006 to E007-r0014 at 7a6faae, E007-r0015 to E007-r0038 at 05712d3, E007-r0039 to E007-r0044 at f815bcd, E007-r0045 and E007-r0046 at a65c1eb; the commits after 7a6faae changed the cycle not at all, and f815bcd narrowed the writer's domain), DOSBox-X 2024.03.01, Xvfb 800x600x24, no window manager. T16's additions to the cycle: `--experiment E007`, the step `put-save` and the argument `--crafted` (the position the step writes; refused when the script has one and the run the other, when the position cannot be encoded, and when the run copy is not a run copy), and the I3 declaration in the record. Each script's sha256 is an observation of its record.

**Arms** (the scripts are `experiments/E007-iw-dos-save-format/steps/*.steps`, written by `scripts/gen-steps.py`):

| Arm | Runs | What it does |
| --- | --- | --- |
| `sv-easy-1` | E007-r0001, E007-r0023 | Set level Easy, 1 starting army, start, Save at the first human turn (the control) |
| `sv-normal-1`, `sv-hard-1`, `sv-hardest-1` | E007-r0002, E007-r0021; E007-r0003, E007-r0019; E007-r0004, E007-r0020 | the control with the level changed alone |
| `sv-easy-3`, `sv-easy-6`, `sv-easy-10`, `sv-hard-6` | E007-r0005, E007-r0022; E007-r0006; E007-r0007; E007-r0008 | the control with the starting armies changed alone (and Hard 1 against Hard 6) |
| `sv-speed-faster`, `sv-speed-slower`, `sv-sound-off` | E007-r0009, E007-r0017; E007-r0010, E007-r0018; E007-r0011, E007-r0016 | the control with one click on Faster, on Slower (the Speed panel is closed by a click away from the buttons) or on Sound, then Save |
| `pass-3`, `pass-6-normal` | E007-r0012; E007-r0014 | Easy 1 (Normal 3), a Save at each turn's start, place all, the CARD button, PASS, no attack |
| `attack-2` | E007-r0025, E007-r0026, E007-r0027 | turn 1: Save, place all, attack until the move-in panel, move in, PASS; turn 2: Save, place all, the CARD button |
| `attack-pass` | E007-r0013, E007-r0015, E007-r0024 | the same for three turns; all three aborted (see the header), and `attack-2` replaced it |
| `load-<variant>` | E007-r0028 … E007-r0046 | the option box, `put-save`, Load saved game, the loaded board, Save again; the variants are in the table of Observations |

**Crafted saves.** Each is `experiments/E007-iw-dos-save-format/crafted/<variant>.position.json`, made by `runtime/iw-dos/save/writer.py craft` from the first save of E007-r0001 (sha256 `c18985b36966503d…`: Easy, 1 army, all armies 1; its centres 29, 4, 11) with the edit in the variant's name; the control `base` is that save unchanged (its bytes equal the natural save's: E007-r0028). A crafted save is a new file of the run copy placed after the launch checks, and the game's own second Save is read back.

**Observations.** The tables built from the records and the bundles are in `experiments/E007-iw-dos-save-format/measurements/analysis-20261005T140803Z/` (`scripts/analyze.sh` runs `save-tables.py`, `check-stars.py`, `check-cards.py`, `check-crafted.py`, `pair-diffs.py` and `hand-order.py`). Exploration before the runs (x01 to x06, not records) is in `measurements/explore/`; it found the Speed panel's way out, the CARD button's behaviour and the first Save that carried Speed and Sound. A first window of the star detector (`check-stars.py`) missed the star of country 19 (E007-r0022, 33 pixels below its number box) and was widened; the table is of the widened one.

## Observations

Bytes are written as the game wrote them; the decoded values are the output of `savefmt.decode`. `saves/saves.tsv` has every save (run, step file, sha256, decoded fields); `pairs/pair-diffs.tsv` has the 29 pairs.

### The pairs

| Pair | Action (one) | Field in the save without, with | Runs |
| --- | --- | --- | --- |
| L1, L2 | Set level Easy to Normal at 1 army | level 1, 2 | E007-r0001, E007-r0002; E007-r0023, E007-r0021 |
| L3, L4 | Easy to Hard at 1 army | level 1, 3 | E007-r0001, E007-r0003; E007-r0023, E007-r0019 |
| L5, L6 | Easy to Hardest at 1 army | level 1, 4 | E007-r0001, E007-r0004; E007-r0023, E007-r0020 |
| A1, A2 | starting armies 1 to 3 at Easy | armies 1, 3 | E007-r0001, E007-r0005; E007-r0023, E007-r0022 |
| A3, A4 | 1 to 6, 1 to 10 at Easy | armies 1, 6; 1, 10 | E007-r0001, E007-r0006; E007-r0001, E007-r0007 |
| A5 | 1 to 6 at Hard | armies 1, 6 | E007-r0003, E007-r0008 |
| S1, S2 | Speed Faster once | speed 2, 1 | E007-r0001, E007-r0009; E007-r0023, E007-r0017 |
| S3, S4 | Speed Slower once | speed 2, 3 | E007-r0001, E007-r0010; E007-r0023, E007-r0018 |
| M1, M2 | one click on Sound | sound 0, 1 | E007-r0001, E007-r0011; E007-r0023, E007-r0016 |
| T1 to T3 | a pass-only turn | Red draws a 7; Red draws a 7; Red draws a 2 and Brown a 1 | E007-r0012 (saves 1 to 4) |
| T4 to T9 | a pass-only turn | one to three cards added per round, always at the end of a hand | E007-r0014 (saves 1 to 7) |
| B5, B6, B7 | turn 1 with an attack, a conquest and PASS | Blue's hand empty, then 7; 3; 7 | E007-r0025, E007-r0026, E007-r0027 |

In every pair of the level, the armies, Speed and Sound the stated field changes and no other settings field does; the board's fields (owners, armies, the centres and the computers' cards) also differ between the two runs of a pair, because two starts draw two boards, and the table `pairs/pair-diffs.tsv` lists them rather than hiding them.

### The saves against the screen

| Check | Result | Runs |
| --- | --- | --- |
| centres against the stars (`stars/stars.tsv`) | 66 of 66 natural saves equal the stars the glyph matcher finds in the screenshot taken at the Save, over 9 different lists | E007-r0001, E007-r0003, E007-r0006, E007-r0012, E007-r0014, E005-r0011, E005-r0037 |
| counts against the `C>` figures (`cards/card-patterns.tsv`) | 272 figures of 68 natural saves; 4 pixel patterns, one count each, one pattern each (0: 158 figures, 1: 65, 2: 9, 3: 4) | E007-r0012, E007-r0014, E007-r0025, E005-r0037 |
| hands against the counts (`hand-order/hand-order.tsv`) | the order Blue, Green, Red, Brown fits 50 of 50 natural saves; the next best order fits 39 | E007-r0012, E007-r0014, E007-r0026 |
| digits seen in natural hands (`hand-order/card-digits-seen.tsv`) | 1, 2, 3, 7 only | E007-r0012, E007-r0014 |

The glyph matcher is a designed template (`scripts/check-stars.py`: the 8 by 5 star, searched near each number box), and the count patterns are bit strings with no reading of the font; the one-to-one map of patterns to counts is the check, and the values 0, 1 and 2 are also read by eye on the capture of E005-r0037 (Blue 1, Red 0, Green 2: its `human-turn-2.png`).

### The crafted runs (`crafted/crafted.tsv`)

| Run | Variant: the one change from the control's save | The game's second Save | Owners read, equal | Stars | `C>` | What the screen showed |
| --- | --- | --- | --- | --- | --- | --- |
| E007-r0028 | `base`: none (its bytes are a natural save's) | equal | 46 of 46 | 4, 11, 29 | 0, 0, 0, 0 | the control |
| E007-r0029 | `owner`: country 2 Red to Blue | equal | 46 of 46 | 4, 11, 29 | 0, 0, 0, 0 | country 2 Blue; scoreboard Blue 18, Red 10; `PLACE 6 ARMIES` |
| E007-r0039, E007-r0040, E007-r0041 | `ownerred`, `ownergreen`, `ownerbrown`: country 12 Blue to that colour | equal | 46 of 46 each | 4, 11, 29 | 0, 0, 0, 0 | country 12 in the colour |
| E007-r0030 | `armies`: country 12 from 1 to 7 | equal | 46 of 46 | 4, 11, 29 | 0, 0, 0, 0 | `7` on country 12 |
| E007-r0032, E007-r0033 | `armies99`, `armies0`: country 12 to 99, to 0 | equal | 46 of 46 each | 4, 11, 29 | 0, 0, 0, 0 | `99`, `0` on country 12 |
| E007-r0031 | `centres`: 1, 2, 3 for 29, 4, 11 | equal | 46 of 46 | 1, 2, 3 | 0, 0, 0, 0 | stars at 1, 2, 3 only |
| E007-r0035 | `cards`: Blue holds a 7 | equal | 46 of 46 | 4, 11, 29 | 1, 0, 0, 0 | Blue `C> 1` |
| E007-r0042, E007-r0043, E007-r0044 | `cardsred`, `cardsgreen`, `cardsbrown`: that colour holds a 7 | equal | 46 of 46 each | 4, 11, 29 | 0, 1, 0, 0; 0, 0, 1, 0; 0, 0, 0, 1 | that colour's `C> 1` |
| E007-r0036, E007-r0038 | `cards5`, `cards5b`: Blue holds 3, 7, 1, 2, 9; 4, 5, 6, 8, 3 | equal | 46 of 46 each | 4, 11, 29 | Blue 5 (no natural pattern for 5, read by eye) | the CARD button shows the five cards: Wild, 5 Bonus, Air Move, Double, a bomb crossed out; Lose All Cards, 15 Bonus, 8 Bonus, a bomb, Wild |
| E007-r0034 | `dft`: the pair 3 and 6 | equal | 46 of 46 | 4, 11, 29 | 0, 0, 0, 0 | `ISLEWAR.DFT` after the load: ` 3 `, ` 6 `, ` 2 ` |
| E007-r0037 | `speed`: the first setting 5 | equal | 46 of 46 | 4, 11, 29 | 0, 0, 0, 0 | the Speed panel reads 5; `ISLEWAR.DFT` ` 1 `, ` 1 `, ` 5 ` |
| E007-r0045, E007-r0046 | `soundctl` (Sound 0) and `sound` (Sound 1), then one click on Sound | equal but for the Sound line | 46 of 46 each | 4, 11, 29 | 0, 0, 0, 0 | `OFF..` after the click on 0; `ON...` after the click on 1 |

The pixels of each loaded board against the control's differ only near the changed countries, in the scoreboard where a count or a total changed, in the prompt boxes (the line `* SELECT COUNTRY *` is on one capture and not on another, and `PLACE 6 ARMIES` follows the 18 countries), and at the pointer arrow, which one capture draws and another does not (the boxes are in `crafted/crafted.tsv`); nothing else of the board differed.

## Inferences

- **The save is the position a Load restores, and the writer is complete for what was shown.** The game reproduced the position byte for byte from a position the writer encoded in 17 runs, one field changed each, so each field is read and written back by the game as the decoder says: E007-r0028, E007-r0029, E007-r0030, E007-r0031, E007-r0034, E007-r0035, E007-r0037, E007-r0039, E007-r0042.
- **The two lines F007 called constant are Speed and Sound.** They moved with a click on the button in two runs each and with a crafted value in one: E007-r0009, E007-r0017, E007-r0010, E007-r0018, E007-r0011, E007-r0016, E007-r0037, E007-r0046.
- **The DFT pair of the save is the level and the starting armies of the game, one by one.** Each moved with its own choice in two or more pairs, and the game wrote the crafted pair into `ISLEWAR.DFT` at Load, which shows that the save and the file are one setting: E007-r0002, E007-r0003, E007-r0004, E007-r0005, E007-r0006, E007-r0034.
- **The list of centres is the board's stars.** It matched the screen in every natural save, was drawn where it was written, and did not change inside a game under any action tried: E007-r0031, E007-r0012, E007-r0014, E007-r0025.
- **The last line is the hands, and the digits name the cards.** The order of its fields is fixed by the lengths in every natural save and by the crafted counts of each colour; the two natural digits that were matched to a card name by Blue's CARD screen agree with the pictures of the crafted hands: E007-r0025, E007-r0026, E007-r0036, E007-r0038, E007-r0042, E007-r0043, E007-r0044.
- **Positions can be set for an experiment.** An experiment that starts from a chosen position can write it and load it (owners, armies, the cards of each colour, the settings), and the game plays on from it; what the game does from such a position was not tested: E007-r0029, E007-r0030, E007-r0035, E007-r0042.

## Alternatives considered

- **A line follows the board, not the action.** For the settings, the level and the starting armies the pairs differ in one action and the field changes by the same step in every pair, while the board's fields differ at random between runs: excluded for these by the six level pairs, the six armies pairs, the four Speed pairs and the two Sound pairs; and for Speed and Sound again by a crafted value that the screen showed (E007-r0037, E007-r0046). It is the answer for the centres, which follow the board.
- **The crafted saves are shown by the game only because the writer and the decoder share a mistake.** Excluded for the owners, armies, centres, counts and Speed by the screen, which does not use the decoder (the board reader, the star matcher and the `C>` patterns are separate code), and for every field by the game's own second Save, which equals the crafted bytes: E007-r0029, E007-r0030, E007-r0031, E007-r0035, E007-r0037. Not excluded for the Sound and the level lines as the screen shows them: Sound is shown by the label after one click (E007-r0046), the level by the `ISLEWAR.DFT` the game writes (E007-r0034), not by the play.
- **The card digits are an order of the game's list and not its names.** Not excluded: the digit-to-card map rests on two natural draws and on the pictures of ten crafted cards (E007-r0036, E007-r0038); the icons of 8 and 9 have no text, and their names (a bomb, a bomb crossed out; the manual's Bomb and Anti-Bomb) are by the pictures.
- **A run was completed past a wait that had timed out.** Excluded: every wait is required in this cycle and a time-out aborts the run, as in E005 (the three aborted records are what a failed wait looks like): E007-r0013, E007-r0015, E007-r0024.
- **The second Save equals the crafted save because the game never re-wrote it.** Excluded: the Sound line of the second Save differs from the crafted one in the two runs that clicked Sound first, so the game wrote that file, and `ISLEWAR.DFT` is written at the Load with the loaded pair and speed: E007-r0045, E007-r0046, E007-r0034, E007-r0037.

## What this does not establish

- *Isle Wars Pro*: nothing; this finding is DOS *Isle Wars*' only (rule 19). The registered build is not measured either.
- Any game rule: what a production centre does in play (the manual says the armies on it double at a "Production Center increase", an event no run saw), what the level changes in the computers' play, what the card digits do when played, and what the game does from a crafted position beyond showing it.
- What moves a production centre inside a game: nothing tried did (pass-only turns, a conquest and a card drawn); a hazard, the loss of a centre's country or another action may.
- The order of the centres in the list (it is not sorted in natural saves, for example 29, 4, 11, and was sorted in the crafted one), and whether the order matters to the game.
- Values the writer refuses: more than 99 armies, a hand of more than 5 cards, a level or starting armies other than the four offered, a Speed outside 1 to 9, more than 5 centres. The game's own limits were not looked for. The cards 4, 5, 6, 8 and 9 were seen only in crafted hands.
- Which of the Speed click and the Save rewrote `ISLEWAR.DFT` (the file was one line before and three lines after both: E007-r0009).
- Whether a save is accepted at a turn other than the start of a human turn: the saves are all of that kind.
- Repeatability beyond one machine and one DOSBox-X build; the arms that ran once (Easy 6, Easy 10, Hard 6) are probes. The boards repeat across runs (the same centres in several games), and nothing here says why.
- Audio, real DOS hardware, another emulator.

## Where the evidence is

- Run records: `runs/E007/E007-r0001.json` … `E007-r0046.json`, with `runs/E007/CORRECTIONS.md`.
- Evidence manifests: `evidence/E007/E007-r0001.manifest.json` … `E007-r0046.manifest.json`.
- The bundles (screenshots, the saves and `ISLEWAR.DFT` and `ISLEWAR.SCR` the game wrote as `s<NN>-<NAME>` and `end-<NAME>`, `changes.log`, `run.log`, `dosbox.log`, `dosbox.conf.txt`) are kept locally outside the repository. The main session uploads them to release `E007` after review. Each file is named `<sha256[:16]>-<name>`, as its manifest says. No savestate was taken. A save is evidence recorded by its sha256, with its bytes in the bundle (the crafted ones are `s02-ISLEWAR.SAV` of each `load-*` run).
- The tables: `experiments/E007-iw-dos-save-format/measurements/analysis-20261005T140803Z/` (an earlier batch, `analysis-20261005T140448Z/`, was made before the last run and before the star matcher counted its origins; it stays and is not cited). The outputs of the Done-when commands: `experiments/E007-iw-dos-save-format/measurements/done-when/`. Exploration: `experiments/E007-iw-dos-save-format/measurements/explore/`.
- The crafted positions: `experiments/E007-iw-dos-save-format/crafted/*.position.json`; the pairs: `experiments/E007-iw-dos-save-format/pairs.json`.

## Reproduction

The machine needs DOSBox-X 2024.03.01, Xvfb, xdotool, ImageMagick and util-linux, `IW_DOS_DIR` set to the extracted archive, and `IW_DOS_RUN`, `E007_BUNDLES` (and `E005_BUNDLES` for the tables) set to locations outside every checkout and `IW_DOS_DIR`. Then:

```text
setup/iw-dos/iw-dos-runtime.sh
experiments/E007-iw-dos-save-format/scripts/run-arms.sh sv-easy-1 sv-speed-faster pass-3 attack-2
experiments/E007-iw-dos-save-format/scripts/run-crafted.sh owner
experiments/E007-iw-dos-save-format/scripts/analyze.sh
python3 runtime/iw-dos/save/writer.py roundtrip <a save the game wrote> ...
python3 tools/register_artifact.py check "$IW_DOS_DIR" iw-dos-3.1-30121376 --strict
```
