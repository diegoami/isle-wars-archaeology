# F017 Isle Wars Pro holds exactly one fixed board, built once at movie start: 46 countries in nine consecutive-range islands of 3, 5, 5, 10, 3, 7, 3, 7 and 3 countries with 23 key countries, joined by 80 undirected border links (160 directed entries; 2 to 5 neighbours per country) that a checked tabulation shows perfectly symmetric and wholly connected, with no land or water distinction of any kind in the code, at 46 fixed screen positions — and nothing in the unregistered build varies the board's shape or layout between games

- **Status**: proposed
- **Question**: What board and adjacency structure does the decompiled Lingo of *Isle Wars Pro* hold — how many territories there are, which islands hold which territories, which territories border which and in which directions, whether the border tables are symmetric, whether adjacency distinguishes land from water crossings, and whether the board or its layout varies between games? The 12 questions of T32: Q-MAP-02, Q-MAP-03, Q-MAP-04, Q-MAP-05, Q-MAP-06 and Q-MAP-10 in their board halves only, Q-MAP-07, Q-MAP-08, Q-MAP-09, Q-MAP-11, Q-MAP-12, Q-MAP-14 (`questions/pro-static.md`, `questions/malpaco.md`). This is a static reading: every answer says what the code says, and none says what the running game does.
- **Tests claims**: none. `spec/` has no board or adjacency claim, and no run is made. The reading is set against F013, which read the island tables as a means to the bonus loop, and against the `Islepro.txt` fragments `knowledge-map.md` lists under Map and topology; where this reading sharpens or corrects what F013 skimmed, it says so (Observations, "Agreement with the findings and the documents").
- **Experiment and runs**: E015 (static only; no run). Its list of the scripts read, the checks and the tabulation are in `experiments/E015-pro-board-reading/`.
- **Artifact**: set `iwp-2.0-996e86c5`, `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e` (the unregistered build; the same file in all three registered Pro sets, F010). Variant none. Rule 19: Pro only; nothing here is claimed for DOS Isle Wars.
- **Max intervention**: I0 (the decompiled scripts were only read, in place; nothing was run)
- **Tier reached**: V0 (static)
- **Confidence**: for the tables' contents — the counts, the island membership, the key lists and every border entry (Q-MAP-02, Q-MAP-03, Q-MAP-04's data, Q-MAP-11, Q-MAP-14): about 95% that the code says what is stated here — every one of the 27 board tables was parsed by script and matched entry by entry against the bytecode listing's push arguments, and the two decompiler renderers agree. For the checked properties — symmetry (Q-MAP-05), connectivity (Q-MAP-12), the partition, the distinct positions: about 95% (exact checks over a bytecode-backed parse). For the reader lists and the absence claims — one board, no board-size control, no layout variation, no land-or-water distinction (Q-MAP-04's who, Q-MAP-06 and Q-MAP-08, Q-MAP-07, Q-MAP-09): about 85% each, an absence being only as strong as the handlers read and the search over the 213 decompiled scripts. For Q-MAP-10's board half: about 90% (the deal handler read in full; its arithmetic is T33's). Every answer carries its own figure below.

## Answer

Every source below is `static:decompile` of `Islepro.exe`, sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; scripts are cited as in `questions/pro-static.md` (kind, number, name when it has one, handler). Nothing is quoted: the structure is described in our words (rule 18), and the tables themselves are reproduced only as our-words tabulations or as the checked output of `experiments/E015-pro-board-reading/tabulate_board.py` (rule 20). "Country" is the code's unit — the numbers 1 to 46 that index every board table; the directions' "territory" and "grid" name the same thing (the directions file itself notes it mixes the words). "Island" is the code's group — nine of them. The full tabulated data this finding cites is `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json`.

**In one paragraph.** The whole board is built once, in the movie-start handler, as plain number tables: a per-country island-number table (46 entries), nine island member lists, nine per-island key-country lists (zero-padded), one 23-country key list, five border tables of 46 entries each (the five neighbour slots of every country, an empty slot written as zero), and two 46-entry position tables holding a screen coordinate pair per country. The numbers are this board's and nothing else reads or rewrites them: a search over all 213 decompiled scripts finds exactly one setter (the movie-start handler) and no second board, no generator and no board-size option. The tabulation checks the tables' properties: the member lists partition the 46 countries into consecutive ranges (sizes 3, 5, 5, 10, 3, 7, 3, 7, 3); the border tables hold 160 non-zero directed entries, every one matched by its reverse (perfect symmetry, 80 undirected links); every country has 2 to 5 neighbours; the whole board is one connected graph; and the 46 positions are distinct. Nothing in the tables or in any reader distinguishes land from water: an inter-island crossing is an ordinary border entry, and every adjacency test — the human's attack and move clicks, and the computer's placement, attack builder, picker, dice and move handlers — gathers the same five neighbour slots. The computer's move handler is the one place where a destination is not looked up in those slots: its *source eligibility* is a five-slot test, but the *destination* comes from a hard-coded country-pair table (Q-MAP-04). The new-game handler resets pieces and the deal handler redistributes ownership without touching any board table, so the shape and the layout are identical in every game of this build.

### The board's size

#### Q-MAP-02 How many territories are there?

- **As read (about 95%).** 46. Three independent structures agree: the per-country island-number table has exactly 46 entries; each of the five border tables has exactly 46 entries, one neighbour slot per country; and the income handler's counting loop runs from 1 to 46 over the ownership table, as does the deal handler's assignment loop and the new-game handler's reset loop. The 46 entries of the island member lists taken together cover exactly the numbers 1 to 46 (the partition check). No other count appears anywhere in the board code.
- **Same rule?** Not applicable (one board, shared by every seat).
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (the island-number and border tables, 46 entries each, bytecode-confirmed); `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the 1-to-46 count loop and the all-46 win test); `MovieScript 5 Putinboard` / `Putinboard()` (the deal fills 46 entries); `MovieScript 23 Newgame` / `Newgame()` (the reset loop over the same 46).
- **What would change it.** A decompiler misrender of a table length — checked against the bytecode listing, where the same 46 pushes precede each store.
- **T28.** Count the territories on the board display in at least 2 recorded games (the question map's plan): expect 46 selectable countries each time.

#### Q-MAP-14 How many territories are on the board (the tables in full)?

- **As read (about 95%).** The same 46; this question asks for the tables themselves, and they are all listed in the movie-start handler: the island-number table, the nine member lists, the nine key lists, the key list, the five border tables and the two position tables. The tabulation in `board-tabulation-r1e.json` reproduces all 27 of them as plain number lists under `tables` — the island table and the full country-by-country adjacency appear under Observations below as well — including the 46 coordinate pairs and the zero-padded per-island key lists, and every entry was read back from the bytecode listing's push arguments. The directions' own text gives no country count; the "46 countries, 9 continents" figure that circulates is a third-party catalogue's (`knowledge-map.md`, Map and topology), and the code now confirms the numbers independently of it.
- **Same rule?** Not applicable.
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (every board table); `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json` (the checked tabulation and the bytecode match).
- **What would change it.** As Q-MAP-02.
- **T28.** As Q-MAP-02.

### The islands

#### Q-MAP-03 Which territories belong to which island?

- **As read (about 95%).** Nine islands, each a consecutive range of country numbers, given twice over in the movie-start handler — once as the per-country island-number table, once as nine member lists — and the two agree entry for entry (a tabulation check, not a reading). The partition is exact: disjoint, covering all 46. The table below is the tabulated result; the key-country column is the per-island key list with its zero padding dropped (the lists are stored, and the fourth island's is stored out of ascending order — 15 before 14 — which the bytecode confirms is real, not a render). The per-island key lists are board data the decompiled scripts never read: across all 213 scripts they appear only in the movie-start handler that builds them and in the `global` declarations of the placement, attack-builder and picker handlers, never in an expression; the key list those handlers actually use is the single 23-country list (Q-MAP-04's reader table). What the per-island lists were kept for is therefore unknown; the 23-country list's role is F016's reading.
- **Same rule?** Not applicable (one board; the island tables are read for every seat's income and by the computer's decisions alike).
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (both the member lists and the island-number table, bytecode-confirmed); `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the bonus loop that walks the member lists consecutively — the property the ranges' order matters for, F013's reading).
- **What would change it.** A misrender of one list — the bytecode match covers every entry, and the island-number table independently encodes the same partition.
- **T28.** List each island and its member territories on the board display (the question map's plan): the drawn map should group exactly the ranges of the table under Observations; expect 9 groups.

#### Q-MAP-11 How many islands are there?

- **As read (about 95%).** Nine, and only nine: nine member lists, nine key lists, an island-number table whose values run from 1 to 9 with all nine used, and a bonus loop with nine fixed parts (F013). Sizes 3, 5, 5, 10, 3, 7, 3, 7, 3 — no single-country island and no other size. This confirms the directions' "conquer all nine islands" (`Islepro.txt:10`, `knowledge-map.md`, Map and topology) with the count the code holds.
- **Same rule?** Not applicable.
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (the nine lists and the number table); `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (the nine-part bonus loop).
- **What would change it.** As Q-MAP-03.
- **T28.** Count the named groups on the board display (with Q-MAP-03's plan): expect 9.

### Adjacency

#### Q-MAP-04 Which territories border which, and how does the game use the border tables?

- **As read (the data about 95%; the reader list about 85%).** The borders are five tables of 46 entries each — the first through fifth neighbour slots of every country; an empty slot holds zero. The tabulation gathers each country's non-zero slots in slot order into the adjacency of the table under Observations: 160 non-zero directed entries, 80 undirected links, every country 2 to 5 neighbours (8 countries have 2, 12 have 3, 22 have 4, and 4 have 5 — countries 15, 17, 20 and 23). Sixteen of the 80 links run between different islands (the crossings, Q-MAP-09); the other 64 are within-island links.
  Every consumer that tests adjacency reads these same five slots, in one of two shapes: a *neighbourhood test* (gather the country's non-zero slots, then test each) or a *pair test* (compare the slots one by one against a fixed country). All of them, with the kind of test:
  - the human's attack: the clicked enemy country must have at least one neighbour owned by the seat whose turn it is (neighbourhood test, otherwise a refusal message), then the clicked own source must list the defender in one of its slots (pair test, otherwise the same refusal), then its armies must be at least the defender's and above one (F011's gate);
  - the human's move: the source must be the seat's own, hold more than one army and have at least one neighbour of its own colour (neighbourhood test — an isolated own country cannot be a move source), and the destination must be the seat's own and list the source (pair test);
  - the computer's front-line list: the seat's countries with at least one enemy neighbour (neighbourhood test);
  - the computer's attack builder: for each front-line country, each enemy-listing slot yields a candidate pair (pair test, F016's gates around it);
  - the computer's dice handler, after a capture: whether the captured country is isolated (neighbourhood test) and which enemy neighbour is strongest (pair walk, F016's split rules around it);
  - the computer's move handler, in two separate steps: *source eligibility* is a neighbourhood test over the slots — a safe-interior source is an own country with more than two armies, no enemy neighbour (the slots supply the own/enemy terms and the strongest enemy count) and not one of the 23 key countries, and the handler then takes its best-stacked safe country; the *destination*, by contrast, is not read from the slots at all: a hard-coded per-source country-pair table maps the source directly to a destination (or to a small fixed set it draws from), with five fallback pairs gated on which islands the seat owns and a centre veto (F016's reading of the decision).
  The border tables are the board's only stored neighbour list: every adjacency *test* in the decompiled scripts reads them. The move handler's hard-coded destination pairs are a second, separate encoding of selected moves (F016's 23-entry destination table), not a read of the border slots, so movement selection is not wholly attributable to the border tables. Nothing in any reader distinguishes one kind of link from another (Q-MAP-09).
- **Same rule?** Yes in the data (one set of tables for every seat); the *checks* differ per side exactly as F011 documented (the human's gate is "at least equal and above one", the computer's a strict excess over a drawn floor).
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (the five border tables, bytecode-confirmed); `BehaviorScript 400` / `mouseDown()` (the human's attack and move tests, both shapes, and the refusal messages); `MovieScript 335 GetValidArmys` / `GetvalidArmys()` (the front-line neighbourhood test); `MovieScript 334 Computerattack` / `Computerattack()` and `MovieScript 336 ATTACKHIM` / `ATTACKHIM()` and `MovieScript 337 computerrolldice` / `ComputerRollDice()` and `MovieScript 338 MakeComputerMove` / `MakeComputerMove()` and `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()` (the computer's five readers — read at their table-feeding passages; the decisions around them are F016's).
- **What would change it.** A misrender of one border entry (bytecode-checked); a seventh reader in the 61 scripts no cast member points at (F010) — the reader list is a search over the 213 decompiled scripts, which is why it is 85% and the data 95%.
- **T28.** Select a territory and try each neighbour, including across water (the question map's plan): expect every table neighbour to be accepted (an attack needs the army gate too) and every non-neighbour refused with the border message, in both directions for a sample of at least 10 pairs.

#### Q-MAP-05 Is the adjacency symmetric — does A bordering B always mean B borders A?

- **As read (about 95%; a checked property, not a reading).** Yes, exactly. The tabulation compares, for every country, the set of its listed neighbours with the set of countries that list it: all 160 directed entries pair up, giving 80 undirected links with no one-way link and no duplicated entry within a country. The check is exact and its input is bytecode-backed (every entry matched the listing's push arguments), so this is stronger than F013's side remark that the tables "are symmetric" — that remark, made while counting crossings for the bonus work, is here verified over the whole table. This matters mechanically: the human's attack uses a neighbourhood test on the defender and a pair test on the attacker (Q-MAP-04), and the human's move a neighbourhood test on the source and a pair test on the destination — two different directions of the same data. Under symmetry the two steps agree; if the tables were asymmetric, the game could admit a source whose target does not list it, or refuse one that does. No such case exists in this build's data.
  Which claims rest on the table's *order*: the slot order (first through fifth neighbour) is preserved in the tabulation's lists, and it has minor mechanical effects only — the computer's strict comparisons keep the earlier slot's candidate on ties (F016's strongest-enemy walk and its slip), and the attack builder's list is built in slot order before its uniform draw. No human-side check depends on slot order, only on membership.
- **Same rule?** Not applicable (a property of the shared data).
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (the tables the check parses); `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json` (the symmetry check over all 160 entries, and the bytecode match); `BehaviorScript 400` / `mouseDown()` (the two-direction checks whose agreement symmetry guarantees).
- **What would change it.** One misrendered or one genuinely asymmetric entry would fail the check; the bytecode match makes a misrender unlikely, and none failed.
- **T28.** Test a sample of pairs in both directions (the question map's plan): pick at least 10 links (including all four 5-neighbour countries' links) and confirm each is accepted as A-attacks-B and as B-attacks-A, and each non-pair refused both ways.

#### Q-MAP-12 Can every territory be reached from every other (is the board connected)?

- **As read (about 95%; a checked property).** Yes. A breadth-first walk over the tabulated adjacency from country 1 reaches all 46 countries; no country or island is cut off. The island crossing graph is connected too: all nine islands hang together through the 16 crossing links (Q-MAP-09), so the board is one piece at both granularities. There is no ferry, boat or special movement that the connectivity depends on — the check uses the same ordinary border entries every consumer reads.
- **Same rule?** Not applicable.
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (the tables); `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json` (the connectivity check).
- **What would change it.** As Q-MAP-05 (one wrong entry could disconnect a country; none did).
- **T28.** Move along a path between sample territories (the question map's plan): e.g. walk armies from country 1 to country 36 (a cross-board path through at least five links) and confirm each single-link step is accepted.

### One board, fixed

#### Q-MAP-06 (board half) Is the board the same in every game?

- **As read (about 90%).** Yes in this build. The movie-start handler is the only setter of every board table — a search over all 213 decompiled scripts finds no other assignment to any of them, no generator and no second table set. The new-game handler resets the display (empty-cast members per country, cleared army texts, cleared card hands) and the deal handler writes ownership and starting armies into fresh per-seat lists, and neither touches a board table. So the shape — countries, islands, borders, key lists, positions — is identical in every game and every launch of the unregistered build. What *does* vary per game is who owns what and where the armies start: that is the deal, T33's subject, and this answer deliberately does not cover it.
- **Same rule?** Not applicable.
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (the only setter, found by search); `MovieScript 23 Newgame` / `Newgame()` (the reset that leaves the tables alone); `MovieScript 5 Putinboard` / `Putinboard()` (the deal that leaves the tables alone).
- **What would change it.** A second setter in the 61 scripts no cast member points at (F010), or one in the registered build (rule 19: `unknown`) — neither searched space can be closed by this build's decompile alone, hence 90%.
- **T28.** Start at least 10 games and compare the board shape and the deal (the question map's plan): expect identical shape every time; the deal's variation is T33's to predict.

#### Q-MAP-07 Is there any board-size control on the options screen?

- **As read (about 85%, an absence claim).** No. Both options-screen display frames were read in full and are identical: they place exactly five option groups plus the sound switch — starting armies (five values), the four seat toggles, the strength level (three entries), the event frequency (four entries) and the speed (three entries) — and no other control. No frame script or option handler writes anything a board table reads; the movie-start handler takes no option input for the board; and the search found no board-size global anywhere. The directions' setup list matches (`Islepro.txt:19-21`: difficulty, colour, starting armies, disaster frequency, speed — no board control). The board is not a parameter of this build.
- **Same rule?** Not applicable.
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `BehaviorScript 457` / `exitFrame()` and `BehaviorScript 479` / `exitFrame()` (the complete control lists); `MovieScript 1 Startmovie` / `startMovie()` (the board tables take no option input); the search for any second board-table setter.
- **What would change it.** A control carried by a sprite whose behaviour no cast member points at (F010), or one unlocked by registration (rule 19: `unknown`).
- **T24/T28 screen.** Walk the options screen and count the controls (the question map's plan): expect exactly the five groups and the sound switch, no board size.

#### Q-MAP-08 Does the board's layout vary between games?

- **As read (about 85%, an absence claim).** No. The position tables — one x and one y coordinate per country, all 46 pairs distinct (a tabulation check) — are built once in the movie-start handler alongside the rest of the board and never rewritten. Their only readers use them for display: the board click handler and the computer's placement handler move a marker sprite to the chosen country's coordinates (five placements in total). The attack-builder and picker handlers declare the tables in their `global` lines but never read them. Nothing gameplay-relevant reads a position; the layout cannot drift because nothing writes it after movie start. The drawn map itself is bitmap art in the cast (not decoded, rule 18) and is likewise never swapped for an alternative board in any script this reading searched.
- **Same rule?** Not applicable.
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (the position tables, 46 distinct pairs, bytecode-confirmed); `BehaviorScript 400` / `mouseDown()` (marker placement on selection); `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()` (marker placement on the computer's placement choices — display uses only); the search for any second setter.
- **What would change it.** As Q-MAP-06 (the 61 unreferenced scripts; the registered build).
- **T28.** Start several games and compare the board layout (the question map's plan): expect the countries at the same positions every game.

### What the tables encode

#### Q-MAP-09 Do the tables distinguish land from water crossings, and what else do they encode or not encode?

- **As read (the encoding description about 90%; the no-land-or-water-rule absence about 85%).** The border tables encode one thing only: which countries neighbour which, as up to five unordered-in-effect slots per country, zero meaning empty. They carry no edge type, no cost, no direction and no land or water tag; an inter-island crossing is an entry exactly like a within-island link, and every adjacency test reads all slots alike (Q-MAP-04). A search of all 213 decompiled scripts for water, sea, ocean and land (the latter only ever inside "island") finds nothing. The island tables do carry the island grouping — that is how the crossings can be counted, and how the bonus and the computer's island scoring work — but no handler reads the grouping to *modulate* adjacency: the grouping affects income and AI scoring, never who can attack or move whom. So for malpaco: Pro's movement graph is a plain undirected graph; "travel across the water" exists in the directions as the drawn map's presentation (`Islepro.txt:59-60`, `knowledge-map.md`, Map and topology) and has no counterpart in the code read.
  What the tables do encode, in sum: neighbour lists (border tables), island membership and per-country island numbers (island tables), per-island key countries and the key list (key tables), and fixed display coordinates (position tables). What they do not encode: any cost or distance, any terrain, any direction, any per-edge rule, any second board, and anything about ownership or armies (separate tables).
- **Same rule?** Not applicable.
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 1 Startmovie` / `startMovie()` (the tables and their shapes); `BehaviorScript 400` / `mouseDown()` and `MovieScript 335 GetValidArmys` / `GetvalidArmys()` and `MovieScript 337 computerrolldice` / `ComputerRollDice()` (every adjacency test's uniform five-slot walk); the token search over all decompiled scripts; `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json` (the 16 crossing links, indistinguishable in kind from the other 64).
- **What would change it.** A distinction living outside the Lingo (Director runtime or the projector) cannot be excluded by this reading; or a reader in the 61 unreferenced scripts. Within the decompiled build, no such code was found.
- **T28.** Count the crossings on the board display (the question map's plan): expect 16 drawn inter-island links (the table under Observations), and expect play across them to behave exactly like play within an island.

#### Q-MAP-10 (board half) Are all territories always in play, or can any start neutral?

- **As read (about 90%).** All 46 are always dealt; no territory stays neutral. The deal handler's assignment loop runs until its board list holds 46 entries (with a separate all-human branch that fills 46 directly), and every entry receives one of the four seat numbers; the per-seat counts are then balanced by a cap-and-minimum pass whose arithmetic is the deal, T33's subject. The ownership table always ends with 46 owned countries, which is also why the income handler can treat "all 46" as the whole board (F012's win test).
- **Same rule?** Not applicable at the board half (the per-seat distribution is T33's and does differ by level and seats).
- **Sources:** `static:decompile` `Islepro.exe` sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`; `MovieScript 5 Putinboard` / `Putinboard()` (the fill-to-46 loops and the per-seat assignment, read in full; the cap-and-minimum arithmetic is T33's).
- **What would change it.** A neutral-value branch in the deal (none found in the handler read in full); the deal's registered-build behaviour is rule 19's `unknown`.
- **T28.** Compare the starting holdings over at least 10 starts (the question map's plan, here for the board half): expect every one of the 46 countries coloured for some seat in every start — the counts per seat are T33's predictions, not this finding's.

## Method

- **Artifact and tools.** The decompiled scripts of F010's run `pro-r1` (ProjectorRays 0.2.0 on the movie of `Islepro.exe`, sha256 above), read in place on the owner's machine in the folder `$IWA_STATIC` names; nothing was copied into the repository (rule 18). The scripts' hashes (`ls_sha256`) are those of `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`; E015 lists the 13 scripts read with them, and `experiments/E015-pro-board-reading/check_cited_scripts.py` checks that this finding cites no script, name or handler the record does not have, and (with `--disk`) that each listed script on disk, hashed in place, has the record's hash.
- **What was read.** In full, in order: the movie-start handler (all 27 board tables it builds, its file-presence checks, its registration scratch files and its eight delay helpers); the income handler (the island bonus loop and the 46-country count); the deal handler (the whole deal, for the board half and to confirm it touches no board table); the new-game handler (the reset, likewise); the front-line candidate handler; the board click handler (all six click states: bombing, placement select, attack target, attack source, move source, move destination, and their refusals); and both options-screen display frames. At their table-feeding passages: the computer's placement, attack-builder, picker, dice and move handlers (the decisions around those passages are F016's, read there in full).
- **The tabulation and its checks (rule 20).** `experiments/E015-pro-board-reading/tabulate_board.py` parses the board tables out of the start handler **in place** (nothing copied), tabulates them, and checks: table lengths and entry ranges; no self-neighbour, with the detector itself exercised against an injected self-edge (the round-2 fix: the predicate had compared a text country key with integer neighbours and always passed); no duplicate neighbour within a country; symmetry over all 160 directed entries; connectivity from country 1; the member lists' disjoint cover; the island-number table's agreement with the member lists; the key lists' concatenation equalling the key list in order; every key country inside its island; the key count and its complement's count; the 46 distinct positions. It then reads the same tables back out of the bytecode listing's push arguments and compares them table by table: all 27 match entry by entry. Its output, `measurements/board-tabulation-r1e.json`, is the checked measurement this finding cites (31 checks, and all 27 tables as plain number lists); four earlier runs of the same script are kept beside it with their bugs documented in the experiment's README (rule 20: never overwritten).
- **What was searched, in the terminal only and with nothing kept.** Every assignment to each board table name (the movie-start handler only). Then, over all 213 decompiled scripts, every occurrence of each board table name, classified as a *declaration* (a `global` line), an *initialisation* (the start handler's table build) or a *read* (any expression that uses the table's value) — the classification the reader table below is rebuilt from:
  - border tables: 8 scripts name them — the setter and 7 readers (board click, front-line list, placement, attack builder, picker, dice, move);
  - island member lists: 5 scripts name them — the setter and the income, placement and attack-builder readers; the picker declares them but does not read them;
  - island-number table: 2 scripts, both read it — the setter and placement;
  - key list (23): 5 scripts name it — the setter, the attack-builder, dice and move readers, and the picker, which declares it but does not read it;
  - per-island key lists: 4 scripts name them — the setter and the declaration-only placement, attack builder and picker — and no script reads them;
  - position tables: 5 scripts name them — the setter, the board-click and placement readers (marker placement), and the declaration-only attack builder and picker.
  And the tokens water, sea, ocean and land over all decompiled text (none; "land" only inside "island").
- **What was not read.** The score (frame order, which sprite carries which button), the cast members (the drawn map is art there, not decoded), and the 61 scripts that no cast member points at (F010). The deal's arithmetic (T33), the computer's decisions (F016), the cards (T22), the centres and hazards (T23). Where an answer needs the frame order it says so.
- **Static first (rule 24).** This finding is the static answer; no run was made or cited for it. T28 corroborates everything from recorded play, with the counts above.

## Observations

### The island table (as tabulated and bytecode-checked; what the bonuses pay is F013's)

Sizes and crossings are this finding's; the bonus column repeats F013's read values for completeness. "Crossings out" counts a country's border entries that point at another island (directed; with symmetry every crossing appears on both sides).

| Island | Countries | Size | Key countries | Bonus (F013) | Crossings out (to islands) |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 to 3 | 3 | 1, 3 | 2 | 2 (2, 3) |
| 2 | 4 to 8 | 5 | 5, 7, 8 | 4 | 3 (1, 3, 8) |
| 3 | 9 to 13 | 5 | 9, 13 | 4 | 4 (1, 2, 4 twice) |
| 4 | 14 to 23 | 10 | 15, 14, 23 (stored in this order) | 8 | 6 (3 twice, 5, 8, 9 twice) |
| 5 | 24 to 26 | 3 | 24, 26 | 2 | 3 (4, 6 twice) |
| 6 | 27 to 33 | 7 | 27, 32, 33 | 5 | 4 (5 twice, 7, 8) |
| 7 | 34 to 36 | 3 | 34, 36 | 2 | 2 (6, 8) |
| 8 | 37 to 43 | 7 | 37, 38, 43 | 5 | 5 (2, 4, 6, 7, 9) |
| 9 | 44 to 46 | 3 | 44, 45, 46 (the whole island) | 3 | 3 (4 twice, 8) |

The 16 inter-island links (undirected): 1-13 (islands 1-3), 3-5 (1-2), 7-9 (2-3), 8-43 (2-8), 9-14 (3-4), 13-15 (3-4), 14-46 (4-9), 23-24 (4-5), 23-38 (4-8), 23-45 (4-9), 24-33 (5-6), 26-27 (5-6), 32-34 (6-7), 33-38 (6-8), 36-37 (7-8), 43-44 (8-9).

### The adjacency table (as tabulated; neighbours in border-slot order)

The full country-by-country table is `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json` (`adjacency`, with `degrees`, `island_of_country` and the crossing edges beside it); the table below is the same data. Island is the island number; degree the neighbour count.

| Country | Island | Degree | Borders |
| --- | --- | --- | --- |
| 1 | 1 | 2 | 2, 13 |
| 2 | 1 | 2 | 1, 3 |
| 3 | 1 | 2 | 2, 5 |
| 4 | 2 | 2 | 5, 6 |
| 5 | 2 | 4 | 7, 6, 4, 3 |
| 6 | 2 | 4 | 4, 5, 7, 8 |
| 7 | 2 | 4 | 5, 6, 8, 9 |
| 8 | 2 | 3 | 7, 6, 43 |
| 9 | 3 | 4 | 10, 11, 7, 14 |
| 10 | 3 | 3 | 12, 11, 9 |
| 11 | 3 | 4 | 13, 12, 10, 9 |
| 12 | 3 | 3 | 13, 11, 10 |
| 13 | 3 | 4 | 12, 11, 1, 15 |
| 14 | 4 | 4 | 15, 18, 9, 46 |
| 15 | 4 | 5 | 16, 17, 18, 14, 13 |
| 16 | 4 | 3 | 15, 17, 20 |
| 17 | 4 | 5 | 16, 15, 18, 19, 20 |
| 18 | 4 | 4 | 14, 15, 17, 19 |
| 19 | 4 | 4 | 18, 17, 20, 22 |
| 20 | 4 | 5 | 16, 17, 19, 22, 21 |
| 21 | 4 | 3 | 20, 22, 23 |
| 22 | 4 | 4 | 19, 20, 21, 23 |
| 23 | 4 | 5 | 22, 21, 24, 38, 45 |
| 24 | 5 | 4 | 25, 26, 23, 33 |
| 25 | 5 | 2 | 24, 26 |
| 26 | 5 | 3 | 24, 25, 27 |
| 27 | 6 | 3 | 28, 29, 26 |
| 28 | 6 | 3 | 27, 29, 30 |
| 29 | 6 | 4 | 27, 28, 30, 31 |
| 30 | 6 | 4 | 28, 29, 31, 32 |
| 31 | 6 | 4 | 29, 30, 32, 33 |
| 32 | 6 | 4 | 30, 31, 33, 34 |
| 33 | 6 | 4 | 32, 31, 24, 38 |
| 34 | 7 | 2 | 35, 32 |
| 35 | 7 | 2 | 36, 34 |
| 36 | 7 | 2 | 35, 37 |
| 37 | 8 | 4 | 38, 39, 40, 36 |
| 38 | 8 | 4 | 39, 37, 23, 33 |
| 39 | 8 | 4 | 38, 37, 40, 42 |
| 40 | 8 | 4 | 37, 39, 42, 41 |
| 41 | 8 | 3 | 40, 42, 43 |
| 42 | 8 | 4 | 39, 40, 41, 43 |
| 43 | 8 | 4 | 41, 42, 8, 44 |
| 44 | 9 | 3 | 45, 46, 43 |
| 45 | 9 | 3 | 46, 44, 23 |
| 46 | 9 | 3 | 44, 45, 14 |

### Where each board table is read (the complete reader lists from the search)

| Table | Set by | Read by (actual expressions only) |
| --- | --- | --- |
| Border tables (5) | `MovieScript 1 Startmovie` / `startMovie()` | `BehaviorScript 400` / `mouseDown()` (human attack/move); `MovieScript 335 GetValidArmys` / `GetvalidArmys()`; `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()`; `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 336 ATTACKHIM` / `ATTACKHIM()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `MovieScript 338 MakeComputerMove` / `MakeComputerMove()` (source eligibility only; the destination is a hard-coded pair table) |
| Island member lists (9) | `MovieScript 1 Startmovie` / `startMovie()` | `MovieScript 6 CheckNumberofArmies` / `CheckNumberofArmies()` (bonus loop); `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()`; `MovieScript 334 Computerattack` / `Computerattack()` |
| Island-number table | `MovieScript 1 Startmovie` / `startMovie()` | `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()` (same-island tests) |
| Per-island key lists (9) | `MovieScript 1 Startmovie` / `startMovie()` | none. `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()`, `MovieScript 334 Computerattack` / `Computerattack()` and `MovieScript 336 ATTACKHIM` / `ATTACKHIM()` name them in their `global` lines and never read them |
| Key list (23) | `MovieScript 1 Startmovie` / `startMovie()` | `MovieScript 334 Computerattack` / `Computerattack()`; `MovieScript 337 computerrolldice` / `ComputerRollDice()`; `MovieScript 338 MakeComputerMove` / `MakeComputerMove()` |
| Position tables (2) | `MovieScript 1 Startmovie` / `startMovie()` | `BehaviorScript 400` / `mouseDown()`; `MovieScript 333 ComputerPlaceArmies` / `computerplacearmies()` (marker placement only — display) |

Declarations are not reads: a handler's `global` line names a table without using it. Besides the per-island key lists above, the picker declares the island member lists and the 23-country key list, and the attack builder and picker declare the position tables — none of which they read. The lists above count only expressions that read a table's value, extracted over all 213 decompiled scripts; the move handler's destination selection is deliberately not counted as a border read because it reads no slot.

### Agreement with the findings and the documents

- **F013** read the island tables to reach the bonus loop. Everything it stated there is confirmed and sharpened: the member ranges, the sizes, the degree distribution (2:8, 3:12, 4:22, 5:4), and its per-island crossing counts (this reading adds the per-island-pair breakdown — its "4 crossings to islands 1, 2, 4" for island 3 splits as 1+1+2, the doubled pair being island 3's two links to island 4). Its claim that "the tables are symmetric" was a side remark; Q-MAP-05 verifies it over all 160 entries. No contradiction was found.
- **F016** read the key list and the border tables as the AI's inputs. The 23-country key list above — the one the computer's handlers actually read — is exactly the union of the per-island lists in island order, including island 4's stored order and island 9's whole-island keying (the per-island lists themselves are never read, Q-MAP-03), and the four 5-neighbour countries (15, 17, 20, 23) sit consistently with its move-table and defence readings.
- **F010** inventoried the board cast: 46 territory members and the empty-country members the new-game handler swaps in — consistent with the 46 of the tables.
- **`Islepro.txt`** (`knowledge-map.md`, Map and topology): "conquer all nine islands" (agrees: Q-MAP-11); the defender "must be adjacent to the country you're attacking from" (agrees: Q-MAP-04's pair test); "lines from island to island which allow you to travel across the water" (agrees that inter-island links exist — 16 of them — but the code knows no water: Q-MAP-09); "move troops between two adjacent countries" (agrees: Q-MAP-04). The directions give no counts; the third-party "46 countries, 9 continents" figure is now independently confirmed by the code (Q-MAP-02, Q-MAP-11).

## Inferences

- **The board is a map of corridors and hubs, not a mesh.** 80 links over 46 countries with a maximum degree of 5 makes every island's interior a chain or a small web; four countries (15, 17, 20, 23) carry five links each and three of them sit in island 4, the 10-country island worth 8 bonus armies (F013). Country 23 in particular is the board's one true hub: five links into four different islands (its two within-island links plus crossings to islands 5, 8 and 9). Whoever holds 23 straddles the board's centre; the computer's key-country weighting treats it accordingly (F016). From Q-MAP-04 and the island table.
- **Island 7 is a corridor between islands 6 and 8.** Its three countries form a chain (32-34-35-36-37 counting the crossing links at both ends), every country of degree 2, no side exit. It is not unique: island 1 is another three-country, degree-2 chain (13-1-2-3-5) between islands 3 and 2. An attacker who takes country 34 interrupts the route *through island 7* — that corridor's island-6 end and island-8 end are then separated along it — but the board does not depend on that corridor: 32-33-38-37 is an alternative island-6 to island-8 path that avoids island 7 entirely, so the board's connectivity (Q-MAP-12) does not rest on it. From the adjacency table.
- **The 2-degree countries are the natural stalemate corners.** Eight countries have exactly two neighbours; combined with the floor of 2 income (F013), a seat pushed into a 2-degree corner (e.g. 25 on island 5, or 1-3 on island 1) is hard to finish off without crossing attack links. From the adjacency table and F013.
- **Malpaco can take the board as pure data.** The whole playable structure — 46 countries, the undirected adjacency, the island partition, the key countries — is in one checked JSON with no hidden rules attached to the edges: any land/water flavour is presentation (Q-MAP-09), and the bonuses that make the islands worth holding are fixed per-island values (F013), not edge properties. From Q-MAP-04, Q-MAP-09.

## Alternatives considered

- **The border tables might be asymmetric with the text hiding it.** Excluded as far as this build's decompile can: the tabulation's symmetry check runs over all 160 directed entries, and every entry was read back from the bytecode listing's push arguments independently of the text renderer. A defect shared by both renderers (one decoder) cannot be excluded by statics alone — that residual is the 5%.
- **Zero entries might mean something other than "no neighbour".** Excluded: every reader skips zero slots before testing (the neighbourhood and pair tests are both gated on non-zero), and no reader treats 0 as a country.
- **The islands might be computed from connectivity rather than stored.** Excluded: the member lists and the island-number table are stored data built at movie start; nothing derives them, and they agree with each other.
- **A second board or a generator might exist.** Not excluded with certainty: the search covers the 213 decompiled scripts of the unregistered build; the 61 scripts no cast member points at (F010) and the registered build (rule 19) are open. Stated as an absence claim at about 85-90% per answer.
- **A land/water rule might live outside the Lingo** (in Director's runtime or the projector). Cannot be excluded by this reading; nothing in the decompiled code points at one, and the directions' "across the water" describes the drawn map's lines, which are cast art.
- **The positions might matter to play** (e.g. hit areas following them). Not established either way here: the readers found use them only to place a marker; the click-to-country mapping itself comes from the score's sprite layout, which is not decoded (a screen question, T24).

## What this does not establish

- **That the decompiler is faithful in every handler.** One decompiler (ProjectorRays 0.2.0); the board tables were cross-checked between its two renderers and against the bytecode listing's push arguments (27 of 27 tables), but the checks share one decoder, and no run of this finding corroborates any behaviour.
- **How the board appears or plays.** The drawn map, the countries' shapes, hit areas and the marker are cast and score, not decoded; whether the drawn map's shapes touch exactly where the tables say neighbours is a screen question (T24, T28).
- **The registered build,** and anything gated by the upgrade check or the registration global (rule 19). Whether registration adds a board, a board size or a layout variant is `unknown`.
- **The deal.** Q-MAP-06 and Q-MAP-10 are answered in their board halves only: who gets how many countries, with what caps and minimums, is T33's.
- **The computer's use of the tables:** where it places, attacks and moves is F016's; this finding cites only how its handlers read the board's tables, and notes that the move handler's destination selection does not read them (Q-MAP-04).
- **DOS Isle Wars.** Nothing here is claimed for it (rule 19); the DOS board's country count and adjacency are a different, unread structure.
- **Any observed rate or play pattern:** every number here is a constant or a checked property of the code's tables, not a measurement (T28).

## Where the evidence is

- The scripts read, with the record's `ls_sha256`: `experiments/E015-pro-board-reading/scripts-read.json`; the record they come from: `experiments/E008-static-triage/measurements/iwp-extract-pro-r1.json`. Both are tracked; the decompiled scripts themselves are not (rule 18).
- The tabulation the finding cites: `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json` (all 27 board tables as plain number lists, counts, the island table, the full adjacency, the crossing edges, 31 checks, and the bytecode match of all 27 tables). Four earlier runs of the tabulation are kept beside it with their bugs documented in the experiment's README; none is cited here.
- The in-place hash check: `experiments/E015-pro-board-reading/measurements/disk-check-r1e.json` (13 scripts, all matching the record on disk; the earlier `disk-check-r1.json` is kept beside it).
- No evidence bundle and no run record exist (no run was made).

## Reproduction

```bash
python3 experiments/E015-pro-board-reading/check_cited_scripts.py            # F017's citations against the inventory
IWA_STATIC=<folder outside every checkout> \
  python3 experiments/E015-pro-board-reading/check_cited_scripts.py --disk   # the on-disk hash check
IWA_STATIC=<folder outside every checkout> \
  python3 experiments/E015-pro-board-reading/tabulate_board.py --run r1 --out r1f   # re-tabulate under a fresh tag (r1e is never overwritten)
```

To re-read, open the listed scripts in the run's folder on the owner's machine (`iwp-extract-pro-r1`, under its `movie-01-out` folder) and compare with the answers above; no copy of them is kept anywhere in the repository.
