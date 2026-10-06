# Board

Written by the main session at promotion, never by a research task. The summary describes only
`supported` and `corroborated` claims. Everything else stays in the table.

## Summary

*Isle Wars Pro*, unregistered, as read from its code: one fixed board of **46 countries** and
**nine islands**, built once at movie start as plain number tables by a single setter, with no
second board, no generator and no board-size option — the new-game and deal handlers never touch
it, so every game of this build plays the same shape (C-BRD-01, C-BRD-02). The nine islands are
consecutive ranges of country numbers (sizes 3, 5, 5, 10, 3, 7, 3, 7, 3), encoded twice over and
in exact agreement (C-BRD-03). Adjacency is five 46-entry border tables (an empty neighbour slot
holds zero): 160 directed entries, perfectly symmetric (80 undirected links), every country with 2
to 5 neighbours, the whole graph connected, 16 links crossing between islands (C-BRD-04).
**Nothing in the code distinguishes land from water** — a crossing is an ordinary border entry,
and every adjacency test reads the same five slots, with one exception: the computer's move
destinations come from a hard-coded country-pair table, not the slots (C-BRD-05). Each country
has one fixed screen position, read for display only (C-BRD-06). The per-island key-country lists
are stored but never read; the handlers that use keys read the single 23-country list (C-BRD-07).

## Claims

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-BRD-01 | The whole board is built once, in the movie-start handler, as plain number tables: a per-country island-number table, nine island member lists, nine per-island key-country lists (zero-padded), one 23-country key list, five border tables (the five neighbour slots of every country, an empty slot written as zero) and two position tables (one screen coordinate pair per country). A search over all 213 decompiled scripts finds exactly one setter and no reader that rewrites any table; the new-game handler resets pieces and the deal handler redistributes ownership without touching a board table, and there is no board-size option. | supported | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), every table entry cross-checked against the bytecode listing by a committed script (E015, tabulation r1e, 31 checks); not yet corroborated by play (T28); Q-MAP-06 (board half), Q-MAP-07, Q-MAP-08, Q-MAP-11 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F017](../findings/F017-pro-board-rules.md) |
| C-BRD-02 | There are exactly 46 countries. Three independent structures agree: the island-number table, each of the five border tables and the income, deal and new-game loops all run to 46, and the island member lists partition exactly the numbers 1 to 46. The third-party "46 countries, 9 continents" catalogue figure is thereby confirmed by the code independently of the catalogue. | supported | as C-BRD-01; Q-MAP-02, Q-MAP-14; about 95% | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F017](../findings/F017-pro-board-rules.md) |
| C-BRD-03 | There are nine islands, each a consecutive range of country numbers, sizes 3, 5, 5, 10, 3, 7, 3, 7, 3 (no single-country island, no other size). The per-country island-number table and the nine member lists encode the same partition and agree entry for entry. This confirms the directions' "conquer all nine islands" with the count the code holds. | supported | as C-BRD-01; Q-MAP-03, Q-MAP-11; about 95% | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F017](../findings/F017-pro-board-rules.md) |
| C-BRD-04 | Adjacency: five border tables hold each country's up-to-five neighbour slots (zero = empty), together 160 non-zero directed entries that are perfectly symmetric (80 undirected links; the tabulation checks every entry against its reverse). Every country has 2 to 5 neighbours (8 countries with 2, 12 with 3, 22 with 4, 4 with 5); the whole board is one connected graph (every country reachable from every other), and 16 of the 80 links run between different islands, the other 64 within one. | supported | as C-BRD-01; Q-MAP-04, Q-MAP-05, Q-MAP-09, Q-MAP-12; about 95% for the data (machine-checked), the reader list about 85% | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F017](../findings/F017-pro-board-rules.md) |
| C-BRD-05 | No land or water distinction exists in the code: an inter-island crossing is an ordinary border entry, and a token search over all 213 decompiled scripts finds no water/sea/ocean/land term outside the word "island". Every consumer that tests adjacency reads the same five slots, as a neighbourhood test or a pair test - the human's attack and move clicks, and the computer's placement, attack builder, picker, dice and move handlers (the last for source eligibility only). The computer's move destinations are the one exception: a hard-coded per-source country-pair table with island-combination fallbacks (F016). Any land or water look the drawn map has is rendering, not data. | supported | as C-BRD-01; Q-MAP-04, Q-MAP-09; the absence claim is a search result over the decompiled text | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F017](../findings/F017-pro-board-rules.md) |
| C-BRD-06 | Each of the 46 countries has one fixed screen position (a coordinate pair in the position tables, 46 distinct entries), read only to place markers and pieces; the positions are display data, never inputs to a rule. | supported | as C-BRD-01; Q-MAP-08, Q-MAP-14; about 95% | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F017](../findings/F017-pro-board-rules.md) |
| C-BRD-07 | The nine per-island key-country lists are stored (zero-padded; the fourth island's stored out of ascending order - real, confirmed in the bytecode) but never read: across all 213 scripts they appear only in the movie-start build and in `global` declarations, never in an expression. The key list the handlers actually read is the single 23-country list (F016's VIPC). What the per-island lists were kept for is unknown. | supported | as C-BRD-01; Q-MAP-03's reader half; the "never read" is a search result with declarations distinguished from reads | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F017](../findings/F017-pro-board-rules.md) |
