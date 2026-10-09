# F020 What the unregistered Isle Wars Pro shows, sounds and accepts on its screens: a catalogue by question for malpaco's UI bar — observed on the running game, no rule claims

- **Status**: proposed
- **Question**: What does one screen walk of *Isle Wars Pro* show for each of the 22 `Q-UI-*` rows of [`questions/pro-static.md`](../questions/pro-static.md) and for Q-PLY-04 — the screens and their menu paths, the board and its pieces, the panels and status texts, the events' messages and flashes, the end screens, the inputs and their hit areas, the sound switch, and the timings the player waits through? (E019, task T24.) The static findings F011–F016, F018 and F019 cover the rules; this catalogue records the visible half, which no finding yet holds. The two rows the static map left `none found` — Q-UI-14 (no event log) and Q-UI-21 (the board look) — are recorded here by walking the game and looking.
- **Tests claims**: none. This is a catalogue: every entry is an observation of what a recorded walk shows, never a rule about how the game decides anything, and nothing here is promoted into `spec/`. Where an entry cites code, it cites the question row's sources (script kind, number, name and handler only, as the questions map does); the decompiled scripts are never quoted (CLAUDE.md rule 18).
- **Experiment and runs**: E019; the walk table, the recorder and the check are [`experiments/E019-pro-ui/`](../experiments/E019-pro-ui/README.md). The title-options and board-pieces records are named in their batch sections, with each record's path under `runs/E019/<batch>/` and each screenshot's hash. The walks are the main session's ([C3], the install is on the user's machine), and this catalogue is turned from the records when they exist (T39, #117; T24 delivers the recorder, the check and this structure). Nothing is fabricated: a question with no record stays pending below.
- **Artifact**: set `iwp-2.0-996e86c5`, variant none, for every walk that cannot write a file of the set; set `iwp-2.0-de5a82a2` for the walks that pass through the mid-game loss, which credits a loss and writes `xtras/Islepro.skr` (F003): Q-UI-04, Q-UI-11, Q-UI-21. Rule 19: Pro only; nothing here is claimed for DOS Isle Wars.
- **Max intervention**: I1 (screenshots of the display and read-only reads of `/proc` and of the game copy; the recorder's own screen reads are pixels-read only — quantised colour censuses, luminance censuses, text-row heights, hover maps, timed watches. No OCR pass anywhere, and no cast member or score byte is ever quoted)
- **Tier reached**: V0 pending completion of the catalogue (the batch sections say which questions carry observations; the tier becomes V2 — the original, headless, under Wine — when all 23 questions carry observations; no native Windows run, so no V3)
- **Confidence**: per entry, and it is written with each observation when the records are turned in. The look of every screen is in the cast and the score, which stay undecoded, so every entry that describes a look rests on the screenshots themselves (the rows' own `medium` and `low` confidences say the same).

## Method

One walk per question: one launch of the game through T13's driver, one `run/1` record under `runs/E019/<batch>/`, the screenshots as release assets named by hash. The recorder (`experiments/E019-pro-ui/run_walk.py`) performs the question's walk from the measured points of E002's recorded scripts (F003) and the driver's constants (F002's exploration), and reads the screen by pixels only. Timings are wall-clock readings at speed = normal, the unlocked default; each timing record observes the options file equal to the shipped one, which is that default (F003). Every board read happens after the deal (the deal is random, F018), so no two walks show the same board. The count targets are the rows' own where a row names one; a target is met by one record, never by adding records, and a walk that sees fewer records fewer and is re-run, never padded. Every timed watch polls its regions together in one loop.

The recorder writes measurements, never identifications. Each record's `observation` is the recorder's summary of what it measured — the screenshots, the counts, the reads and the timing observations — and the reading of them is this catalogue's. Three rows' targets need an identification the pixels cannot make and are proxied, with a `count note` in the record: Q-UI-06's events and Q-UI-07's centre moves are counted as flash candidates (large changes, each shot), and Q-UI-13's computer turns are derived from the walk's own PASS clicks; their entries can only be `narrowed`.

Batches, one commit each, in the task's order: title and options (Q-UI-04, Q-UI-10, Q-UI-19, Q-UI-22), board and pieces (Q-UI-01, Q-UI-02, Q-UI-03, Q-UI-05, Q-UI-20, Q-PLY-04), play (Q-UI-08, Q-UI-12, Q-UI-13, Q-UI-15, Q-UI-16), events and end (Q-UI-06, Q-UI-07, Q-UI-11, Q-UI-14, Q-UI-21), inputs and sounds (Q-UI-09, Q-UI-17, Q-UI-18).

The check `python3 experiments/E019-pro-ui/check_ui_catalogue.py` maps every recorded file to its question id and asserts the coverage, the targets, the observation lines and the citations. It fails, naming the questions, until the walks have run (T39).

## Observations

The table reads at a glance what each screen's entries show. It is filled in as the batches' records are turned in; until then it names the questions each screen carries.

| Screen | Questions | What the catalogue shows |
| --- | --- | --- |
| Title | Q-UI-04, Q-UI-10, Q-UI-18, Q-UI-19 | the title screen at three desktop sizes (800x600x24, 1024x768x24, 1280x1024x24) — Q-UI-04 (`E019-r0013`); Q-UI-19 (six records, two attempts each). 640x480 is below the game's first-frame geometry and is narrowed out. |
| Options | Q-UI-04, Q-UI-10, Q-UI-17, Q-UI-22, Q-PLY-04 | the Options screen at the default frequency (Q-UI-04 `E019-r0013`, Q-UI-22 `E019-r0004`) and at the same three desktop sizes (Q-UI-19, six records). Q-UI-10 times the round-trip without shots. |
| Board | Q-UI-01, Q-UI-02, Q-UI-03, Q-UI-05, Q-UI-12, Q-UI-13, Q-UI-14, Q-UI-20, Q-UI-21 | the board and its pieces in `E019-r0014`–`E019-r0019` (Q-UI-01, Q-UI-02, Q-UI-03, Q-UI-05, Q-UI-20, Q-PLY-04); Q-UI-12, Q-UI-13, Q-UI-14 and Q-UI-21 belong to later batches |
| Placement | Q-UI-08, Q-UI-12, Q-UI-15, Q-UI-16 | when the batch's records are turned in |
| Attack | Q-UI-08, Q-UI-09, Q-UI-12, Q-UI-16, Q-UI-21 | when the batch's records are turned in |
| End | Q-UI-11, Q-UI-14, Q-UI-21 | when the batch's records are turned in |
| Scores | Q-UI-04, Q-UI-11, Q-UI-14 | the Scores screen reached from the bottom menu (Q-UI-04 `E019-r0013`); the post-game tally screen is captured by Q-UI-11 on the events-end batch. |
| Help | Q-UI-04 | the three help pages reached from the bottom menu (Q-UI-04 `E019-r0013`). |
| Loss notice | Q-UI-04, Q-UI-21 | the post-elimination notice reached by clicking New Game mid-game with fewer than 10 human countries (Q-UI-04 `E019-r0013`; Q-UI-21 on the events-end batch). |
| Frequency-locked | Q-UI-22 | the Options screen after the frequency click in the unregistered build — the click is refused by the registration gate (F019), so the value does not change. Q-UI-22 `E019-r0004`. |

Per-question entries follow, one per row of the questions map, in the map's order. Each entry carries: the question, the row's cited sources, the walk's batch and what it does, the observation with its status (`observed` with the screen region and description; `narrowed` if the look depends on a cast member; `static-only` with what the walk looked for and did not find; `unestablished` if the walk could not visit), the recorded files and their hashes, the timings where the question is about timing, and what would change it. Until a batch's records exist, its entries say so and carry no observation.

### Title and options

#### Q-UI-04 A screenshot of every screen reached by walking each menu path

- **Sources (the row's):** `CastScript 347 newgame2` / `mouseUp()`; `CastScript 355 quit2` / `mouseDown()`; `CastScript 666 exit2` / `mouseUp()`; `CastScript 668 Help2` / `mouseUp()`; `CastScript 353 scores2` / `mouseDown()`; `CastScript 351 soleau2` / `mouseUp()`; `MovieScript 339 bottombuttons` / `Bottombuttons()`.
- **Walk**: batch `title-options`; the walk follows every menu path the measured points reach — Options, Help (three pages), Scores, New Game to the setup screen and the board, New Game again to the loss notice — and shots each screen. The walk stops at the loss notice; the earlier round's post-loss path (to start another game and capture the quit notice) aborted on no-change at the post-loss Play Game click, and the quit notice is captured by Q-UI-21 on the events-end batch.
- **Boundaries the walk states**: the Soleau Games label is a refused rectangle in the step language, so its screens are never walked (as in E002); the driver terminates by kill, so the Quit path stops at the notice, and the notice's exit button is never clicked inside a recorded walk (F003's tour reached the notice under the spike's `ui-quit` termination).
- **Observation**: observed. **Run**: `runs/E019/title-options/E019-r0013.json` (sha256 `afc5dcc036d56797…`, driver `e257bb1b395a`, display 800x600x24, 42.56 s). **Distinct screens**: 9 — title (`ae6e98d28d379bb4…`), options (`426d77e724d793dd…`), help-page-1 (`390756985586a01d…`), help-page-2 (`10842580b609d049…`), help-page-3 (`3d404526ba3d60a6…`), scores (`d816d6fb3ee277b0…`), newgame-setup (`154143a1bd739503…`), board (`cbe97bf2c065c4d3…`), loss-notice (`5ad6d9012cdce6b9…`). Count target ≥ 8 met. Set `iwp-2.0-de5a82a2` (the mid-game loss credits `xtras/Islepro.skr`, F003; the F019 row covers it).
- **What would change it**: a measured point for a screen the walk could not reach, or a menu path the walk did not follow.

#### Q-UI-10 Three timed walkthroughs with click counts

- **Sources (the row's):** `BehaviorScript 450` / `exitFrame()`; `BehaviorScript 3` / `exitFrame()`; `CastScript 347 newgame2` / `mouseUp()`; `MovieScript 1 Startmovie` / `startMovie()`.
- **Walk**: batch `title-options`; three rounds of title → Options → title, each timed with the monotonic clock, the inputs counted; the launch-to-title time is the session's own measurement.
- **Observation**: observed. **Run**: `runs/E019/title-options/E019-r0003.json` (sha256 `c6177267a5f66db0…`, driver `db6375203ad6`, display 800x600x24, 13.12 s). **Counts**: 3 walkthroughs. **Timing observations**: 6 — round-to-options at 0.68 s, 0.61 s, 0.61 s; round-back-to-title at 0.68 s, 0.62 s, 0.68 s. **Launch-to-title**: 6.53 s (recorded at step 2). The recorder does not shot title or options in this walk (the walk's goal is timing, not screenshots); the catalogue reads the timings above.
- **What would change it**: the timing and the screen order are in the score, which stays undecoded; a walk at another speed setting would time it differently.

#### Q-UI-19 Screenshots at each supported resolution

- **Sources (the row's):** `MovieScript 1 Startmovie` / `startMovie()` (a start-up check of the desktop size).
- **Walk**: batch `title-options`; one launch per desktop size (640x480, 800x600, 1024x768, 1280x1024), the title and the Options screen shot at each, and the display's pixel count measured beside the size asked for; the question is covered only by a record at each of the four sizes. The driver assumes the 800x600 stage is centred in the game window, so a size where the title is not detected is recorded as its own outcome, not skipped.
- **Boundary the catalogue states**: the projector-level windowing — what the projector does with the desktop size — belongs to the projector, not the Lingo, and this catalogue notes that and stops.
- **Observation**: narrowed. **Three sizes met** (one screen pair per launch, two attempts each as a re-run check): **800x600x24** — runs `runs/E019/title-options/E019-r0006.json` (sha256 `2a587d69046adf4d…`, driver `db6375203ad6`) and `runs/E019/title-options/E019-r0010.json`; `title-at-this-size.png` (sha256 `ae6e98d28d379bb4…`) and `options-at-this-size.png` (sha256 `426d77e724d793dd…`). **1024x768x24** — `runs/E019/title-options/E019-r0007.json` (sha256 `af54d69bb397299f…`) and `runs/E019/title-options/E019-r0011.json`; `title-at-this-size.png` (sha256 `84cbd7fc7b03a96d…`) and `options-at-this-size.png` (sha256 `9a753549fc73e463…`). **1280x1024x24** — `runs/E019/title-options/E019-r0008.json` (sha256 `777269828986b58f…`) and `runs/E019/title-options/E019-r0012.json`; `title-at-this-size.png` (sha256 `a76f7b3f4158bf6d…`) and `options-at-this-size.png` (sha256 `299f67c401de9320…`). The 640x480 size is below the game's first-frame geometry (the title screen was not seen within 45 s on both attempts — `E019-r0005.json` and `E019-r0009.json`, aborted); the walk's narrowed scope is the three reachable sizes.
- **What would change it**: a decode of the start-up check (the row's `low` confidence says the code is one handler), or a run on native Windows (V3).

#### Q-UI-22 Screenshots with the option on and off

- **Sources (the row's):** `BehaviorScript 499 FREQbehavior` / `mouseDown()`; `BehaviorScript 54` / `exitFrame()` (the event frequency option, the only switchable feature found).
- **Walk**: batch `title-options`; the Options screen is shot at the default, then the frequency control is clicked (the measured point of E002's opt-freq-never script) and the result shot. The option is locked in the unregistered build (F003's locked-frequency screens; F019's registration gates): on and off is reachable only at the file-write path, not at the click, and the record notes the locked state.
- **Observation**: observed with the locked state. **Run**: `runs/E019/title-options/E019-r0004.json` (sha256 `2a4cedff0117eef2…`, driver `db6375203ad6`, display 800x600x24). **Screenshots**: `frequency-default.png` (sha256 `426d77e724d793dd…`, the Options screen at the default frequency) and `frequency-locked.png` (sha256 `9160a38dd7b6cd83…`, the same screen after the frequency click — the click was refused by the registration gate, F019, so the value did not change). The "off" half (frequency = 4 / never) is reachable only on a registered build (rule 19 keeps it out of this repository's scope); what the walk captures is the locked refusal.
- **What would change it**: a registered build (rule 19 keeps it out of this repository's scope).

### Board and pieces

#### Q-UI-01 Screenshots of the board at the one player count the build allows, and in greyscale

- **Sources (the row's):** `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 1 Startmovie` / `startMovie()` (owner-keyed cast members per territory).
- **Walk**: batch `board-pieces`; the board is shot after the deal (the deal is random, F018; no two walks show the same board), at the one human seat the unregistered build allows (F003's locked seat toggles), with a quantised colour census and a luminance census of the board area beside the shot.
- **Observation**: observed, with high confidence. The main session's reading of `board-1.png` shows the board filling the stage above the bottom panels: about 46 numbered territories on ten islands connected by pale straight sea links. Territory tiles carry a relief texture and one of four owner tints — blue, yellow, red or green — while large white army digits with dark outlines sit over them. The upper-left black score box lists four players in their owner colours with territory and card counts; the upper-right title block includes the publisher and an unregistered-copy notice. The lower row has the pointer-and-prompt panel, an empty centre panel, the placement prompt, and the menu. In the shot's greyscale reading, the four tints collapse into close mid-greys: yellow is slightly lighter, but blue, red and green are hard to distinguish. Ownership is therefore conveyed by hue alone, with no pattern, border or shape marker; the army digits remain legible, while the coloured score-box names lose contrast against black. The recorded board-area colour census has 736 quantised colours across 396,000 pixels, and its greyscale census has 16 levels across the same 396,000 pixels. The initial screen settle was 0.44 s and the watched board area settled unchanged after 22.49 s; the session lasted 33.4 s. **Run**: `runs/E019/board-pieces/E019-r0014.json` (sha256 `b1e03cfc0e3cf79b…`, driver `f19135a10cf7`, display 800x600x24, 33.4 s). **Screenshot**: `board-1.png` (sha256 `97c26acddb43d158…`).
- **What would change it**: the look is in the cast, which is not decoded (the row's `medium` confidence).

#### Q-UI-02 Screenshots of boards with centres at the default size

- **Sources (the row's):** `MovieScript 51 putinproductioncenters` / `Putinproductioncenters()`; `MovieScript 363 addtoproductioncenter` / `addtoproductioncenter()` (a flash and a text colour change on the centre).
- **Walk**: batch `board-pieces`; the board is shot with whatever centre marks it carries, and the message strip and board area are watched for a short window so a centre flash, if one fires, is timestamped.
- **Observation**: narrowed. The main session's reading of the two shots finds exactly three cyan army digits on each board instead of white: territories 2, 3 and 30 in `board-with-centres-1.png`, and territories 9, 18 and 46 in `board-with-centres-2.png`. The cyan digit marks a production centre, about 80% likely; otherwise the territory's tile is unchanged. The 20 s timed watch, sampled every 0.25 s for 72 ticks, saw no change in either the message strip or board area, so no centre flash was observed during the placement prompt. The message-strip rectangle lies in the empty centre panel and may not cover where the game writes its messages (#138); the board-area watch, which covers the centres, is the one that supports this. The initial screen settle was 0.43 s and the watched board area settled unchanged after 22.73 s; the session lasted 53.05 s. **Run**: `runs/E019/board-pieces/E019-r0015.json` (sha256 `ea0f689e5a7f5c4a…`, driver `f19135a10cf7`, display 800x600x24, 53.05 s). **Screenshots**: `board-with-centres-1.png` (sha256 `34775bc4d7595235…`) and `board-with-centres-2.png` (sha256 `15e194a5c6c9b0bb…`).
- **What would change it**: the mark itself is in the cast (the row's `medium` confidence); the centres' positions are random, so the walk records what the shots show.

#### Q-UI-03 Annotated screenshots; measure the text height

- **Sources (the row's):** `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 23 Newgame` / `Newgame()` (a per-territory text field filled with the army count).
- **Walk**: batch `board-pieces`; the board is shot, and the text rows of the message strip and the phase panel — where the game writes at a known place — are measured by pixel bands. The territory numbers' font and size are in the cast, which is not decoded, so the catalogue describes them from the annotated shot and states the measured heights beside them.
- **Observation**: narrowed. The main session's reading of `board-armies.png` sees large white territory digits with dark outlines, roughly twice the height of the territory-number circles. No text height was measured: the `message-strip` read at `(265,530,270,26)` found 0 boxes, and the `phase-panel` read at `(262,502,276,70)` found one 70 px box covering the whole panel rather than a text row. The prompts are in the blue side panels, which this walk did not measure. The initial screen settle was 0.43 s and the watched board area settled unchanged after 15.78 s; the session lasted 26.19 s. **Run**: `runs/E019/board-pieces/E019-r0016.json` (sha256 `6097b2bc39217daf…`, driver `f19135a10cf7`, display 800x600x24, 26.19 s). **Screenshot**: `board-armies.png` (sha256 `c882697dd8881214…`).
- **What would change it**: a re-walk with text-row regions on the side panels (a follow-up to the walk table, not this task's file), or a decode of the cast's text members (none exists; ProjectorRays does not decode them).

#### Q-UI-05 Screenshots, sampled colours and simulated renderings

- **Sources (the row's):** `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the colour list and the colour-keyed text members).
- **Walk**: batch `board-pieces`; a quantised colour census of the Options screen and of the board area, with a board shot beside them. The census is a pixel count, not a colour claim; the colour values themselves stay in the cast.
- **Observation**: narrowed. The main session's reading pairs `board-colours.png` with the recorded censuses. The full-stage Options shot has 666 quantised colours across 480,000 pixels; its largest entry is the lavender-blue background, 176,155 pixels (about 37%). The board-area census has 728 quantised colours across 396,000 pixels; sea blues and black dominate, while the owner tints follow lower in the list and vary with the deal. The visible player colours are blue, yellow, red and green, with cyan used for centre digits and white for army digits. These are the catalogue's visual identifications; no colour values beyond the recorded quantised census and no simulated rendering are claimed. The run settled at 0.43 s after the first screen change, 0.45 s after the later screen change, and 29.91 s after the watched board area became unchanged; the session lasted 41.5 s. **Run**: `runs/E019/board-pieces/E019-r0017.json` (sha256 `bc75462204165a76…`, driver `f19135a10cf7`, display 800x600x24, 41.5 s). **Screenshot**: `board-colours.png` (sha256 `1b7a6a3059ed089b…`).
- **What would change it**: the colour values are in the cast (the row's `low` confidence); a simulated rendering is the catalogue's reading of the recorded values.

#### Q-UI-20 Screenshots with measured text height and contrast

- **Sources (the row's):** `MovieScript 5 Putinboard` / `Putinboard()` (the text colour set on the territory fields).
- **Walk**: batch `board-pieces`; the board is shot, with a colour census, a luminance census and the message strip's text-row heights beside it; the catalogue derives the contrast from the recorded distributions.
- **Observation**: narrowed. The main session's reading of `board-contrast.png` finds white, dark-outlined army digits clear against the mid-tone territory tints. The coloured score-box names on black and the cyan centre digits are the weakest contrast pairs. The board-area colour census contains 751 quantised colours and the greyscale census 16 levels, each across 396,000 pixels. No text height was measured: the `message-strip` read at `(265,530,270,26)` found 0 boxes. The initial screen settle was 0.43 s and the watched board area settled unchanged after 34.76 s; the session lasted 45.19 s. **Run**: `runs/E019/board-pieces/E019-r0018.json` (sha256 `95c4c6d044356fd3…`, driver `f19135a10cf7`, display 800x600x24, 45.19 s). **Screenshot**: `board-contrast.png` (sha256 `a15e6d0b696aeff1…`).
- **What would change it**: a re-walk with text-row regions on the side panels (a follow-up to the walk table, not this task's file), or a decode of the cast's text members (size, colour values and layout are in the cast and score; the row's `low` confidence).

#### Q-PLY-04 Count the colours on the board and the options screen

- **Sources (the row's):** `MovieScript 1 Startmovie` / `startMovie()`; `MovieScript 5 Putinboard` / `Putinboard()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the colour list and the colour-keyed cast members).
- **Walk**: batch `board-pieces`; the same two censuses as Q-UI-05, recorded under this question: the count is the recorded census, and which colours are the players' is the catalogue's reading of it, never a rule claim.
- **Observation**: observed. The main session's reading of `board-for-colour-count.png` confirms four player colours — blue, yellow, red and green — from the board and score box, with cyan for centre digits and white for army digits. The same record's full-stage Options census has 666 quantised colours across 480,000 pixels, including a lavender-blue background entry of 176,155 pixels (about 37%); its board-area census has 765 quantised colours across 396,000 pixels. The board census's leading entries are sea blues and black, with deal-dependent owner tints lower in the list. The initial Options settle was 0.43 s, the later board settle was 0.43 s, and the watched board area settled unchanged after 15.85 s; the session lasted 27.63 s. **Run**: `runs/E019/board-pieces/E019-r0019.json` (sha256 `d59a0490503b803a…`, driver `f19135a10cf7`, display 800x600x24, 27.63 s). **Screenshot**: `board-for-colour-count.png` (sha256 `c92e1be9a29cb0d8…`).
- **What would change it**: the look of the colours is in the cast and score, not decoded (the row's `medium` confidence).

### Play

#### Q-UI-08 Screenshots of every panel with per-player figures

- **Sources (the row's):** `MovieScript 75` / `PutinInfo()`; `BehaviorScript 463` / `exitFrame()` (the territory and card count text fields).
- **Walk**: batch `play`; the panels are shot at each phase of one human turn — the board at the human's turn, the placement panel at select, all-placed and placed, the attack panel at ready and after an exchange, and the turn menu — the tour's own sequence (F003).
- **Observation**: pending the [C3] walk.
- **What would change it**: the panel layout is in the score (the row's `medium` confidence).

#### Q-UI-12 Annotated screenshots through one full turn

- **Sources (the row's):** `BehaviorScript 26` / `exitFrame()`; `MovieScript 339 bottombuttons` / `Bottombuttons()`; `BehaviorScript 13` / `exitFrame()`; `BehaviorScript 43` / `exitFrame()`; `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the status texts and the button frames).
- **Walk**: batch `play`; the same turn as Q-UI-08, with the status texts shot at each phase and the strip's and turn panel's text rows measured by pixels.
- **Observation**: pending the [C3] walk.
- **What would change it**: the layout is in the score (the row's `medium` confidence).

#### Q-UI-13 Timed recordings of at least 20 computer turns

- **Sources (the row's):** `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 336 ATTACKHIM` / `ATTACKHIM()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `MovieScript 338 MakeComputerMove` / `MakeComputerMove()`; `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()` (the computer's status texts, flashes and busy-wait pauses).
- **Walk**: batch `play`; seven passes; the message strip, the phase panel and the board area are polled together after each PASS and every change is timestamped, so the pauses show as the gaps between changes. The computer turns are not identified on the screen: the record counts the PASS clicks the game took and derives the turns from the three default computer seats (21 for seven passes, F003), with a count note.
- **Timing caveat (the record carries it)**: the pause lengths depend on the speed setting; the walk times at speed = normal, the unlocked default (F003), and a future task can re-time at FAST or SLOW.
- **Observation**: pending the [C3] walk; the catalogue's entry will be `narrowed` (the row's "at least 20 computer turns" is derived from passes, never counted on the screen).
- **What would change it**: a decode of the busy-wait helpers, or timings at another speed.

#### Q-UI-15 Screenshots and recordings of holding, playing and discarding cards

- **Sources (the row's):** `MovieScript 344 PUTINCARDS` / `PUTINCARDS()`, `PUTINCARDSM()`; `BehaviorScript 526 pick3cards` / `mouseDown()`; `CastScript 376 CARDV1` / `mouseDown()`; `CastScript 528 tradein2` / `mouseDown()`; `BehaviorScript 342` / `exitFrame()` (the hand display, the selection, the trade-in and the discard click).
- **Walk**: batch `play`; up to ten aggressive turns; after each pass the recorder clicks Continue and records whether the message strip changed, with a shot when it did; whether a shot shows a card award is the catalogue's reading of it. The hand screen is not walked: the turn menu's CARD button has no measured point (E002's tour never used it; F003 says so), and it stays unmeasured rather than guessed.
- **Observation**: pending the [C3] walk.
- **What would change it**: the card images and layout are in the cast (the row's `medium` confidence); a measured point for the CARD button.

#### Q-UI-16 Frame-timed recordings of at least 20 attacks

- **Sources (the row's):** `MovieScript 50 Rolldice` / `RollDice()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `BehaviorScript 47` / `exitFrame()`; `BehaviorScript 48` / `exitFrame()`; `MovieScript 49 Showstrength` / `showstrength()` (the battle text updates and pauses).
- **Walk**: batch `play`; up to eight aggressive turns, three clicks on the attack button each, every click timed around the attack panel's change, until 20 exchanges are recorded. One attack is one click on the attack button (F011's reading); the exchanges a turn can give end when the game stops accepting.
- **Timing caveat**: as Q-UI-13 — wall clock at speed = normal.
- **Observation**: pending the [C3] walk.
- **What would change it**: the pause lengths depend on the speed setting (the row's `medium` confidence).

### Events and end

#### Q-UI-06 Frame-timed recordings of at least 5 events

- **Sources (the row's):** `BehaviorScript 54` / `exitFrame()`; `MovieScript 364 PutinFlood` / `putinflood()`; `MovieScript 365 Putinrebellion` / `putinrebellion()` (the typed event message, a flash and a sound).
- **Walk**: batch `events-end`; up to thirty turns with the message strip and the board area polled together; a flash candidate is a poll tick in which a watched region changed over a large share of its pixels, counted once per tick, timestamped and shot. A candidate is not an identified event — an ordinary redraw or either transition of a flash makes one — so the record emits `count: flash candidates`, never `count: events`, with a count note. Events are random at the one frequency the unregistered build allows (F019); a walk that sees fewer than the target records fewer and is re-run, never padded.
- **Observation**: pending the [C3] walk; the catalogue's entry will be `narrowed` (the row's "at least 5 events" is proxied by flash candidates; which shots show an event is the catalogue's reading of them).
- **What would change it**: the timing comes from busy-wait helpers whose length depends on the speed setting (the row's `medium` confidence).

#### Q-UI-07 Recordings of at least 5 centre moves

- **Sources (the row's):** `BehaviorScript 54` / `exitFrame()`; `MovieScript 51 putinproductioncenters` / `Putinproductioncenters()` (the event message and the centre flash).
- **Walk**: batch `events-end`; the same watch as Q-UI-06, but only the board-area changes are counted — the region where the centre flash of `Putinproductioncenters()` is drawn — and the strip's changes are recorded beside them. Which flash candidate is a centre move is not decidable by pixels: the record emits `count: centre-flash candidates`, never `count: centre moves`, and carries a `count note` saying the row's word is proxied. The catalogue describes what the shots and timestamps show.
- **Observation**: pending the [C3] walk; the catalogue's entry will be `narrowed` (the row's "at least 5 centre moves" is proxied by 5 board-area flash candidates, never claimed as identified centre moves).
- **What would change it**: a decode of the event messages' text, which the pixels-read rule keeps out, or a runtime signal that distinguishes the five event kinds.

#### Q-UI-11 Screenshots of the end screen after a win, a loss and a concession

- **Sources (the row's):** `BehaviorScript 463` / `exitFrame()`; `BehaviorScript 465` / `exitFrame()`; `BehaviorScript 470` / `exitFrame()`; `BehaviorScript 473` / `exitFrame()`; `BehaviorScript 506` / `exitFrame()` (the end and scores screens).
- **Walk**: batch `events-end`; the loss notice is shot (the end state this walk reaches). A win and a concession are not reached: no run in this repository has played to a win (F003), and the surrender offer depends on a position the walk cannot craft.
- **Observation**: pending the [C3] walk.
- **What would change it**: a walk that plays to a win, or a crafted position (the unregistered build cannot save, so none can be crafted — F003).

#### Q-UI-14 Screenshots of any log after a long game (the static map's `none found`)

- **Sources (the row's):** none found: searched all handlers for a stored list of events; only status text fields were found.
- **Walk**: batch `events-end`; an absence walk: the tour visits the title, options, scores, setup, board and the turn phases over a long session (five passes of computer turns), and shots each; the record names the screenshots and nothing more. Whether any of them shows a list-of-events control is the catalogue's reading, made by inspecting the shots: "absence confirmed on the screens visited" can be this entry's observation, never the recorder's, and never a proof.
- **Observation**: pending the [C3] walk; the catalogue's entry will be `static-only`, with what the walk looked for and did not find.
- **What would change it**: a screen the walk did not visit, or a control the shots show and the walk misread.

#### Q-UI-21 Reference screenshots in setup, mid-game, battle and end states (the static map's `none found`)

- **Sources (the row's):** none found: the board look is bitmaps in the cast, which is not decoded; the handlers only swap them.
- **Walk**: batch `events-end`; one session shots the four reference states — the setup screen, the board after the deal, the attack panel, and the loss notice. The board's look is in the bitmaps, and the observation is the reference screenshots themselves; a future task can adopt a score decoder if one becomes available.
- **Observation**: pending the [C3] walk; the catalogue's entry will be `static-only` in the row's sense — the look is not in the Lingo — with the four references as the record.
- **What would change it**: a decode of the cast's bitmaps (none exists; ProjectorRays does not decode them).

### Inputs and sounds

#### Q-UI-09 Recordings of attempts at each illegal action

- **Sources (the row's):** `BehaviorScript 400` / `mouseDown()`; `CastScript 74 Attack4` / `mouseDown()`; `BehaviorScript 43` / `exitFrame()`; `BehaviorScript 44` / `exitFrame()` (the error messages, the sound and the prompts).
- **Walk**: batch `inputs-sounds`; with the attack panel up, three groups of clicks the game may refuse or ignore (points over water and over the wrong side), each recorded with a shot and the message strip's census beside it. The attempts are what the measured points reach; the catalogue names each attempt and its message from the shots.
- **Observation**: pending the [C3] walk.
- **What would change it**: the highlights are in the cast (the row's `medium` confidence); attempts that need a crafted board (the unregistered build cannot save) stay out.

#### Q-UI-17 A table of events against sounds from recordings

- **Sources (the row's):** `CastScript 591 ear1` / `mouseUp()`; `BehaviorScript 400` / `mouseDown()`; `MovieScript 50 Rolldice` / `RollDice()`; `BehaviorScript 54` / `exitFrame()` (the sound switch and the places that play sounds).
- **Walk**: batch `inputs-sounds`; the Options screen is shot, the sound switch clicked and clicked back (the measured point of E002's committed exploration commands, verified at run time by the click's recorded reaction), each state shot. The driver runs with audio off — no sound device in its display namespace — so the record carries the switch's reaction on the screen and the note that sound capture needs a driver change.
- **Observation**: pending the [C3] walk.
- **What would change it**: a driver that captures audio, or a decode of the cast's sound members (the row's `medium` confidence).

#### Q-UI-18 A table of inputs against actions and measured hit areas

- **Sources (the row's):** `BehaviorScript 400` / `mouseDown()`; `MovieScript 339 bottombuttons` / `Bottombuttons()`; `BehaviorScript 495` / `exitFrame()`; `MovieScript 494 Getusernames` / `GETUSERNAME()` (the click and key handlers; hover is used for button images).
- **Walk**: batch `inputs-sounds`; hover maps of the title screen's bottom bar, the Options screen's return button and the turn menu's band: at each grid point the recorder moves the pointer and records whether the band reacted. No point is clicked, so the walk fires no action. The Soleau label's area is refused by the step language and its points are skipped. The hit areas proper are in the score (not decoded); the hover-reactive area is what this walk measures.
- **Observation**: pending the [C3] walk.
- **What would change it**: a decode of the score's button geometry (the row's `medium` confidence).

## What this does not establish

- Any rule of play: how combat, reinforcement, cards, hazards, the deal or the computer decide anything (the rule findings F011–F019 hold that half; T28 corroborates it).
- The registered build (rule 19): what registration unlocks stays `unknown` beyond what Pro's own code gates.
- The score's frame order and the cast members' bytes (ProjectorRays does not decode them): the catalogue describes what the player sees, in its own words, and cites the question rows' sources by kind, number, name and handler.
- The projector-level windowing (Q-UI-19): what the projector does with the desktop size is outside the Lingo; the catalogue notes this and stops.
- The *content* of any sound: the driver runs with audio off; Q-UI-17's record is the switch's reaction, not the sounds.
- The playback of a position: the unregistered build cannot save, so no position can be crafted or revisited.
- Anything about DOS Isle Wars (rule 19).

## Where the evidence is

- Run records: `runs/E019/<batch>/E019-r<nnnn>.json` (the title-options and board-pieces records are named in their sections; the walks are the main session's [C3] step, and later batches' records will be named here as they are turned in).
- Evidence manifests: `evidence/E019/<batch>/E019-r<nnnn>.manifest.json`, naming each screenshot by hash; the screenshots themselves are release assets of release `E019`, never committed (rule 20).
- The walk table, the recorder and the check: [`experiments/E019-pro-ui/`](../experiments/E019-pro-ui/README.md).

## Reproduction

From a clone whose runtime, setup, tools, formats and experiment folder are committed, on the machine that holds the install (the walks are that machine's), with `IWP_DIR` set to the install and `IWP_PREFIX` and `E019_BUNDLES` outside every checkout:

```text
python3 experiments/E019-pro-ui/run_walk.py --batch title-options
python3 experiments/E019-pro-ui/run_walk.py --question Q-UI-06
python3 experiments/E019-pro-ui/check_ui_catalogue.py
```

The command refuses to start when runtime, setup, tools, formats or the experiment folder have uncommitted changes, and the next walk starts only when the last one was recovered (the reset shown to restore the prefix), as in E004.
