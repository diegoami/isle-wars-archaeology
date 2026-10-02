# Knowledge map

What is known about each area of *Isle Wars* (DOS, 1994) and *Isle Wars Pro* (Win9x), and how it
is known. **Everything starts `unknown`.** A cell moves only by evidence:
- to `documented`, when W2 finds a primary source;
- beyond that, only through a reviewed finding and its promotion into `spec/`.

Statuses, basis tags and scope follow game-archaeologist's `vocabulary/` (`status.md`, `basis.md`)
at the commit [`archaeology.json`](archaeology.json) pins. The two games are scoped separately: a
claim holds for both only when it is shown for each (CLAUDE.md rule 19). The reference copies are
the shareware/unregistered releases (U11), so what registration unlocks is `unknown` too.

## Areas

The Basis and Sources columns describe the *Isle Wars Pro* cell: the DOS cells are all `unknown` and have no source yet.

| Area | DOS *Isle Wars* | *Isle Wars Pro* | Basis | Sources and findings |
| --- | --- | --- | --- | --- |
| Setup | unknown | documented | doc | Pro: [options at the start of a game](sources/iwp-islepro-txt.md#setup) `Islepro.txt:19-22`. Options listed: difficulty, colour, starting armies, disaster frequency, game speed. Which the unregistered build locks is not stated (`Islepro.txt:225-226`). |
| Players | unknown | documented | doc | Pro, unregistered: [Blue against three computer players](sources/iwp-islepro-txt.md#setup) `Islepro.txt:21-22`. Registered: up to four humans ([registration](sources/iwp-islepro-txt.md#registration) `Islepro.txt:223-224`). |
| Map and topology | unknown | documented | doc | Pro: [nine islands](sources/iwp-islepro-txt.md#objective) `Islepro.txt:10`; [adjacency and island-to-island lines](sources/iwp-islepro-txt.md#attack-and-combat) `Islepro.txt:58-60`. Country count, adjacency list and island values are not given in the text. |
| Starting state | unknown | documented | doc | Pro: [armies are distributed at the start](sources/iwp-islepro-txt.md#starting-state-and-turn-order) `Islepro.txt:24`. How they are distributed is not stated; starting armies is an option ([setup](sources/iwp-islepro-txt.md#setup) `Islepro.txt:19-21`). |
| Turn sequence | unknown | documented | doc | Pro: [random first player](sources/iwp-islepro-txt.md#starting-state-and-turn-order) `Islepro.txt:25`; [placement](sources/iwp-islepro-txt.md#reinforcement-and-resources) `Islepro.txt:26-28`; [trade-in at the top of the turn](sources/iwp-islepro-txt.md#trading-in-cards) `Islepro.txt:152`; [attack](sources/iwp-islepro-txt.md#attack-and-combat) `Islepro.txt:56`; [move or pass ends the turn](sources/iwp-islepro-txt.md#losing-the-attacking-army-conquest-move) `Islepro.txt:90`. |
| Reinforcement and resources | unknown | documented | doc | Pro: [countries divided by 3, island bonus, minimum 2](sources/iwp-islepro-txt.md#reinforcement-and-resources) `Islepro.txt:26-29,42`. The island-value figure (`Islepro.txt:32-36`) names no islands; values are not attributed. |
| Movement | unknown | documented | doc | Pro: [move between two adjacent countries; move in at least one after conquest](sources/iwp-islepro-txt.md#losing-the-attacking-army-conquest-move) `Islepro.txt:88,95-96`. |
| Combat | unknown | documented | doc | Pro: [adjacency, attacker total, dice, tie goes to the defender](sources/iwp-islepro-txt.md#attack-and-combat) `Islepro.txt:58-73`; [attacker at 1 forfeits](sources/iwp-islepro-txt.md#losing-the-attacking-army-conquest-move) `Islepro.txt:80-81`. Read the lines for the dice rule; only fragments are quoted here. |
| Ownership change | unknown | documented | doc | Pro: [defender at 0 is taken; a failed attacker at 1 loses the country](sources/iwp-islepro-txt.md#losing-the-attacking-army-conquest-move) `Islepro.txt:80-85`; [rebels take a country](sources/iwp-islepro-txt.md#situations-disasters-and-production-centres) `Islepro.txt:174`. |
| Production centres | unknown | documented | doc | Pro: [move, doubled armies, light blue total](sources/iwp-islepro-txt.md#situations-disasters-and-production-centres) `Islepro.txt:175-178`. How often or where they move is not stated. |
| Bonuses (island/continent groups, cards) | unknown | documented | doc | Pro: island bonus ([island bonus](sources/iwp-islepro-txt.md#reinforcement-and-resources) `Islepro.txt:28-29`); cards ([cards](sources/iwp-islepro-txt.md#cards) `Islepro.txt:113-133`, [trading](sources/iwp-islepro-txt.md#trading-in-cards) `Islepro.txt:141-159`). A trade-in's value is not stated. |
| Hazards | unknown | documented | doc | Pro: [earthquake, flooding, rebellion](sources/iwp-islepro-txt.md#situations-disasters-and-production-centres) `Islepro.txt:166-174`. Effect sizes are not quoted here. |
| AI | unknown | unknown | — | Pro: `Islepro.txt` only says the computer plays the other players ([setup](sources/iwp-islepro-txt.md#setup) `Islepro.txt:21-22`) and that levels of difficulty exist ([setup](sources/iwp-islepro-txt.md#setup) `Islepro.txt:19-20`). It does not describe how the AI decides, so the cell stays `unknown`. |
| Randomness | unknown | documented | doc | Pro: [dice](sources/iwp-islepro-txt.md#attack-and-combat) `Islepro.txt:69`; [first turn](sources/iwp-islepro-txt.md#starting-state-and-turn-order) `Islepro.txt:25`; [events](sources/iwp-islepro-txt.md#situations-disasters-and-production-centres) `Islepro.txt:167`. Only that these are random; distributions are not stated. |
| Victory and loss | unknown | documented | doc | Pro: [conquer all nine islands](sources/iwp-islepro-txt.md#objective) `Islepro.txt:10`; [victor, elimination, quitting with fewer than 10 countries](sources/iwp-islepro-txt.md#end-of-game) `Islepro.txt:189-213`. |
| Surrender | unknown | documented | doc | Pro: [an eliminated player may concede](sources/iwp-islepro-txt.md#end-of-game) `Islepro.txt:189-190`. This is the player's concession; no collective AI offer appears in `Islepro.txt`. |
| User interface (screens, input, feedback, presentation) | unknown | documented | doc | Added 2026-10-02: malpaco's UI must be at least as good as Pro's. Behaviour is observed; timing, rendering and UI claims need V3 or V4 (U8). Pro: [button set](sources/iwp-islepro-txt.md#attack-and-combat) `Islepro.txt:56`; [light blue totals](sources/iwp-islepro-txt.md#situations-disasters-and-production-centres) `Islepro.txt:177-178`. Only what the directions say of the controls and colours; layout, timing and feedback stay unobserved. |
| Registration: what the unregistered build says it unlocks (Pro, as documented by the unregistered build) | unknown | documented | doc | Up to four human players, control of starting armies, disaster frequency, scoreboard clearing and colour, "and more" ([registration](sources/iwp-islepro-txt.md#registration) `Islepro.txt:223-226`); $15 ([price](sources/iwp-islepro-txt.md#registration) `Islepro.txt:228`, [Order.txt](sources/iwp-order-txt.md) `Order.txt:3`); unlock codes by e-mail, CD-ROM optional ([Order.txt](sources/iwp-order-txt.md#what-registration-delivers) `Order.txt:40-41`). What "and more" covers, and what the registered build really does, is `unknown`. |

## Secondary assertions (malpaco, unverified)

[malpaco](https://github.com/diegoami/malpaco) is an earlier re-take of the Isle Wars ruleset, not a
study of it. Its own `RULES.md` warns that "nothing in this document was reverse-engineered". These
are its statements about the original games, kept so that W2 and the research questions can test
them. **None is evidence. Each stays `unknown` until a primary source or a finding settles it.** All
citations are at malpaco `6b533d7`.

| Assertion | Game it names | Status | Source |
| --- | --- | --- | --- |
| *Isle Wars* is by Soleau Software, 1994; *Isle Wars Pro* is its Win9x sequel | both | unknown | `RULES.md:13-14`. Bears: [Pro's directions](sources/iwp-islepro-txt.md#title-and-publisher) give "Version 2.0 by Soleau Software, Inc." `Islepro.txt:2-3`; [the order form](sources/iwp-order-txt.md#what-is-sold-and-at-what-price) "GAMES FOR WINDOWS $15 Each" `Order.txt:3`. Neither gives a year, a DOS game or the word Win9x. |
| *Isle Wars* runs in DOSBox in a browser (playdosgames.com, Internet Archive) | DOS | unknown | `DECISIONS.md:27-28` |
| The ruleset's "shape" includes a match rule, hazards, production centres and a three-card idea | unspecified ("Isle Wars … and its sequel") | unknown | `RULES.md:14-15`. Bears (Pro only): a match of 3 equal cards ([trading](sources/iwp-islepro-txt.md#trading-in-cards) `Islepro.txt:141-142`), [hazards and production centres](sources/iwp-islepro-txt.md#situations-disasters-and-production-centres) `Islepro.txt:171-178`, [cards](sources/iwp-islepro-txt.md#cards) `Islepro.txt:113-133`. Nothing in `Islepro.txt` is about DOS. |
| Kept "from the original": the match rule, the failed-attack penalty, hazards, roaming production centres, the AI's collective surrender offer | unspecified ("the original") | unknown | `DECISIONS.md:399-401`. Bears (Pro only): [forfeiting the country when the attacker is down to 1](sources/iwp-islepro-txt.md#losing-the-attacking-army-conquest-move) `Islepro.txt:80-81`; [production centres move](sources/iwp-islepro-txt.md#situations-disasters-and-production-centres) `Islepro.txt:175`; hazards `Islepro.txt:171-174`. No collective AI surrender offer appears in `Islepro.txt`. |
| The AI's surrender offer is "*Isle Wars Pro*'s best idea" | Pro | unknown | `RULES.md:189`. Bears: `Islepro.txt` has no AI offer; the nearest is that an eliminated player may [concede](sources/iwp-islepro-txt.md#end-of-game) `Islepro.txt:189-190`. |
| The board is "46 countries divided between 9 continents" (landmasses subdivided, not separate islands) | DOS ("*Isle Wars*") | unknown | `DECISIONS.md:254`. Bears (Pro, not DOS): the directions say [nine islands](sources/iwp-islepro-txt.md#objective) `Islepro.txt:10` and give no country count. |
| *Isle Wars Pro* is not abandonware; Soleau still sells the registered version | Pro | unknown | `DECISIONS.md:512-513`. Bears: the unregistered build offered registration at ["only $15 (U.S.)"](sources/iwp-islepro-txt.md#registration) `Islepro.txt:228` and an [order form](sources/iwp-order-txt.md#where-to-order) `Order.txt:65`, which says the game was for sale when the text was written, not that it is now. **Contradicted by** [the user's report](sources/user-2026-10-02-availability.md) (2026-10-02): the game can no longer be bought, because Soleau Software no longer exists. Neither is verified; T05 tests this from public pages. |
