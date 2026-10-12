# malpaco variants

Every design choice of [core-rules.md](core-rules.md) (T50, the owner's decisions 1 to 12),
[variety.md](variety.md) (T51, the owner's decisions V1 to V12) and [computer.md](computer.md) (T53,
the choices A1 to A12), with its decided option, the **canonical** variant malpaco builds first, and
every other option kept as a named variant that a later version may offer as a setting. This file is
a catalogue: it claims no spec rows, and the rule text lives in the design files, linked from each
entry. Options, recommendations and reasons are in each file's owner's section. For T53 the
canonical option is the owner's to choose; each entry names the recommended option, and the
canonical line is filled in with the owner's decision.

A variant name is the choice's number and the option's letter (for example **T50-11a**, **V2b**,
**A5c**).
"Interacts with" names the other choices a variant changes the balance of, so that a later settings
screen offers them together or warns.

## T50: the core rules

### T50-1 Which boards ship
- **Canonical (c): a generated board** each game, from the seed, under fixed invariants and fairness
  checks. [The board](core-rules.md#the-board).
- **T50-1a Fixed board.** One hand-made board meeting the invariants: the same map every game, so
  players learn its chokepoints; bonuses could be hand-tuned.
- **T50-1b Board set.** Two to four hand-made boards: variety by board choice, with each board tested.
- Interacts with: T50-12 (the bonus rule exists for generated boards; a fixed board could use
  hand-set values), V7 (centres drawn on whatever board), V8 (storm groups need borders, not
  numbering), T50-2 (a seed reproduces the board only when it is generated).

### T50-2 Saving a game
- **Canonical (b): one save slot**, restored by replaying settings, seed and actions.
  [Stored files](core-rules.md#stored-files).
- **T50-2a No saving.** Every game in one sitting.
- **T50-2c Several slots and an undo.** An undo lets a player re-roll dice and card draws by reloading.
- Interacts with: V1 and V4 (with an undo, a Squall or a bad draw can be taken back), T50-11.

### T50-3 Seats
- **Canonical (b): 2 to 4 seats**, each human or computer, hot-seat allowed. [Seats](core-rules.md#seats).
- **T50-3a Four seats, one human.** The standard game only.
- **T50-3c 2 to 6 seats.** Needs a larger board (more countries and islands).
- Interacts with: T50-5 (the deal's remainder), V7 (three centres among two seats is a larger share
  each), V8 (a revolt needs two seats with 3 or more countries), V1 (draws per pass of the deck).

### T50-4 The fair start
- **Canonical (b): even shares, equal armies per country placed at random, no complete island at
  start.** [The deal](core-rules.md#the-deal).
- **T50-4a Random start.** Uneven shares and armies drawn per country: more starting luck.
- **T50-4c Placed start.** As (b), then each seat places its starting armies itself, in turn.
- Interacts with: T50-5, T50-6, V7 (random centres add starting luck even with an even deal).

### T50-5 First-mover compensation
- **Canonical (b): a random first seat; the deal's leftover countries go to the seats that play last.**
  [The deal](core-rules.md#the-deal), step 2.
- **T50-5a No compensation.** The first seat keeps its head start.
- **T50-5c Extra armies.** As (b), plus one starting army per place in turn order.
- Interacts with: T50-3, T50-4.

### T50-6 The human handicap
- **Canonical (b): even shares, and a per-human share setting from −4 to +4 countries.**
  [Options](core-rules.md#options), [The deal](core-rules.md#the-deal).
- **T50-6a No handicap.** Only the computer's strength sets difficulty.
- **T50-6c Shares by difficulty level.** Fixed shares per level, as the predecessor did: the handicap
  is hidden in the level.
- Interacts with: A1 to A3 (the computer's strength, a separate setting), A5 (a handicap the player
  chose is never treated as a runaway at the deal).

### T50-7 Attack rules: the gate and the forfeit
- **Canonical (b): one rule, at least 2 armies, no comparison, no forfeit; a failed attack does not
  end the turn.** [Combat](core-rules.md#combat).
- **T50-7a The predecessor's split.** The human needs at least the defender's count and forfeits its
  country at 1 army; the computer needs more and never forfeits.
- **T50-7c Gate without forfeit.** At least 2 and at least the defender's count, for every seat.
- Interacts with: T50-11 (the gate is harsher with ties to the defender), V5 (a raid can lower a
  stack below an attacker's count, opening a gated attack), C-CRD-03 (with a forfeit, the
  predecessor cancelled the capture card).

### T50-8 The move
- **Canonical (a): one move between neighbouring countries, ending the turn.**
  [Movement](core-rules.md#movement).
- **T50-8b Chain move.** One move along a chain of the seat's own countries.
- **T50-8c Several moves.** Several neighbour moves per turn.
- Interacts with: V5 and V8 (with longer moves, a seat refills a raided or storm-struck front faster).

### T50-9 How a game is won
- **Canonical (b): total conquest, or domination at three quarters (35 of 46) for any seat**, on by
  default. [Victory](core-rules.md#victory).
- **T50-9a Conquest and concession.** Total conquest only, plus a concession offered to a human.
- **T50-9c Domination at two thirds.** Shorter games.
- Interacts with: the near-win event pause (its threshold follows the win), V3 (a Surge set near the
  threshold can finish a game), T50-10.

### T50-10 Round limit and draws
- **Canonical (b): an optional round limit of 20, 30 or 40, off by default, with tie-breaks.**
  [Victory](core-rules.md#victory).
- **T50-10a No limit.** Games end by conquest or domination only.
- **T50-10c Limit on by default.**
- Interacts with: V12 (the quiet last rounds exist for the limit), V9 (events per game scale with the
  limit), V8 (Off events with a limit makes the last rounds pure play).

### T50-11 Combat odds: ties
- **Canonical (b): ties re-rolled** (p = 1/2). [Combat](core-rules.md#combat).
- **T50-11a Ties to the defender** (p = 5/12): defence 1.4 times as efficient; boards lock.
- **T50-11c Ties to the attacker** (p = 7/12): attack dominates; position matters less.
- Interacts with: T50-7, V5 and V8 (the worth of a removed defending army), the game-length model.

### T50-12 Island bonuses on a generated board
- **Canonical (a): `floor(size / 2) + entrances`, at least 2, never above the size.**
  [Island bonuses](core-rules.md#island-bonuses).
- **T50-12b Proportional.** `round(0.75 × size)`, at least 2, ignoring entrances.
- **T50-12c Left to T51.** Superseded: T51 kept (a) (V10).
- Interacts with: V10 (tuning), V3 (a Surge set doubles bonuses too), T50-1.

## T51: variety

### V1 The deck
- **Canonical (a): a finite shuffled deck, discards reshuffled.** [The deck](variety.md#the-deck).
- **V1b Independent draws.** No deck memory; long runs of one kind possible.
- **V1c No reshuffle.** Cards stop when the pile runs out; late game without cards.
- Interacts with: V2 to V5 (the composition), T50-3 (seats share one deck), T50-10 (long games pass
  the deck more often).

### V2 Trade-in values
- **Canonical (c): fixed 5, 8 and 15 by kind, up to two Wilds per set.** [Trade-ins](variety.md#trade-ins).
- **V2a Small fixed sets.** 4, 6, 8, and 6 for one of each kind, one Wild: sets are frequent and
  modest.
- **V2b Escalating sets.** 4, 6, 8, 10, 12, 15, then 5 more each, counted over the game: late sets
  decide games.
- Interacts with: V3 (escalating sets with a doubling set compound), V6 (taking a beaten seat's cards
  feeds escalation), V1 (the composition must change with V2a's one-of-each set).

### V3 A pool-doubling card
- **Canonical (c): a set that doubles the whole pool.** [Trade-ins](variety.md#trade-ins).
- **V3a None.**
- **V3b Capped Surge.** The set adds the country income again, at most 8.
- Interacts with: V2, T50-9 (a Surge near the win threshold), T50-12 and V10 (doubled bonuses).

### V4 A card that empties its drawer's hand
- **Canonical (c): the Squall empties the whole hand.** [The hand](variety.md#the-hand).
- **V4a None.**
- **V4b Mild Squall.** It discards one random card.
- Interacts with: V11 (with discard-first, a full hand loses a card and then possibly all), V2 (the
  rarer the sets, the more a Squall costs), T50-2c (an undo would cancel it).

### V5 The raid
- **Canonical (c): three Raids replace any enemy stack with 1 to half, no cap.**
  [The raid and the shield](variety.md#the-raid-and-the-shield).
- **V5a Neighbour raid.** A single card, on an enemy country bordering the raider, half lost, at most
  10, as the turn's one card action.
- **V5b Distant raid.** As V5a, on any enemy country.
- Interacts with: T50-11 and T50-7 (what a removed army is worth), V1 (V5a needs a single-card
  action and its own counts), T50-8.

### V6 An eliminated seat's cards
- **Canonical (a): discarded.** [An eliminated seat's cards](variety.md#an-eliminated-seats-cards).
- **V6b Taken.** The eliminating seat takes them and may trade at once.
- **V6c Taken up to the limit.** As V6b, the excess discarded.
- Interacts with: V2b (the classic runaway), V3, T50-3 (more seats, more eliminations).

### V7 Production centres
- **Canonical (c): three random centres, no income, a harvest that doubles adding at most 10, and a
  shift event.** [Production centres](variety.md#production-centres).
- **V7a No centres.** No harvest and no shift events.
- **V7b Home centres.** One per seat, placed in tiers, paying 1 a turn, never moved, a harvest of +3;
  needs a pool-formula change in core-rules.md.
- Interacts with: V8 and V9 (harvest and shift are events; with events off, centres do nothing),
  T50-3, T50-4.

### V8 The kinds of event and their sizes
- **Canonical (c): the predecessor's set and sizes**, storm, revolt, harvest and shift.
  [The kinds of event](variety.md#the-kinds-of-event).
- **V8a Small events.** A capped storm, a revolt of small stacks only, a harvest.
- **V8b No ownership changes.** Storm and harvest only.
- Interacts with: V7 (harvest and shift exist only with centres), V9, V12, T50-10.

### V9 Event frequency
- **Canonical: the predecessor's rates**, Off, 1 in 21, 1 in 14 (default) and 1 in 8.
  [When an event is drawn](variety.md#when-an-event-is-drawn).
- **V9a Lower rates.** Off, 1 in 32, 1 in 16 (default) and 1 in 8.
- **V9b Rare by default.** V9a's settings, Rare as the default.
- **V9c Per round.** One draw per round, at the start of the round: puts the first seat right after
  every event.
- Interacts with: V8, V7, T50-10 and V12 (events per game).

### V10 Tuning the island bonus constants
- **Canonical (a): decision 12 as it is**, board totals 34 to 46. [Island bonuses](variety.md#island-bonuses).
- **V10b Halved entrances.** `floor(size / 2) + ceil(entrances / 2)`, totals 28 to 34.
- **V10c Band check.** (a), plus a fairness check on the board's total.
- Interacts with: T50-12, V3.

### V11 A draw into a full hand
- **Canonical (b): discard one of five, then draw.** [The hand](variety.md#the-hand).
- **V11a Draw first.** See the new card, then discard any of six.
- **V11c No draw.** A seat with five cards earns no card.
- Interacts with: V4 (discard-first then a Squall), V2 (rare sets fill hands).

### V12 Events near the end of a round-limit game
- **Canonical (a): none in the last 3 rounds.** [When an event is drawn](variety.md#when-an-event-is-drawn).
- **V12b Last 5 rounds.**
- **V12c Conditional.** None in the last 5 rounds while the top two seats are within 4 countries.
- Interacts with: T50-10, V8, V9.

## T53: the computer opponent

Every T53 option keeps [computer.md](computer.md)'s requirements: the same rules as a human, a human
seat's view, its own random stream, and levels that change only decisions. No variant may relax them.

### A1 The levels
- **Canonical: the owner's choice.** Recommended (a): Easy, Normal and Hard.
  [Difficulty levels](computer.md#difficulty-levels).
- **A1a Three levels.** Easy, Normal and Hard.
- **A1b Four levels.** Adds Expert: no mistakes, full card memory, the strongest leader check.
- **A1c Slider.** A strength from 1 to 10 that moves every constant continuously.
- Interacts with: A4, A9 (each level must separate from its neighbours in the tests), T50-6 (the human
  share is the other difficulty control).

### A2 The default level
- **Canonical: the owner's choice.** Recommended (b): Normal. [Difficulty levels](computer.md#difficulty-levels).
- **A2a Easy.** **A2b Normal.** **A2c Hard.**
- Interacts with: A1, T50-6.

### A3 One strength for all, or per seat
- **Canonical: the owner's choice.** Recommended (b): per computer seat, default Normal for all.
  [Difficulty levels](computer.md#difficulty-levels).
- **A3a One setting.** Every computer seat at the same level.
- **A3b Per seat.** A level beside each computer seat on the options screen.
- Interacts with: T50-3 (seats and who plays them), A5 (mixed levels check a leader unequally).

### A4 Deliberate mistakes
- **Canonical: the owner's choice.** Recommended (b). [Difficulty levels](computer.md#difficulty-levels).
- **A4a None.** Levels differ only in foresight, aggression, card timing and the leader check.
- **A4b Low levels only.** Easy 25%, Normal 8% of decisions, among the three best actions; Hard none.
- **A4c Every level.** As A4b, and Hard 3%.
- Interacts with: A1, A9 (mistakes move win rates), A8 (mistakes draw on the seat's own stream).

### A5 The leader check
- **Canonical: the owner's choice.** Recommended (b). [The leader check](computer.md#the-leader-check).
- **A5a None.** Each computer plays only for its own gain.
- **A5b Seat-blind leader weight.** From 28 countries, or 1.5 times the next seat and at least 22,
  scaled by level, none at Easy.
- **A5c Near a win only.** As A5b, only from 31 countries, where events stop.
- Interacts with: T50-9 (the domination threshold sets the leader count), T50-3 (in a two-seat game
  the leader is the only opponent), A10, V3 (a Surge set near the threshold).

### A6 Battles per turn
- **Canonical: the owner's choice.** Recommended (b): at most 10. [Quick turns](computer.md#quick-turns).
- **A6a No bound.**
- **A6b At most 10.**
- **A6c At most 6.**
- Interacts with: T52's presentation speed, T50-9 (a bound can delay a domination finish by a turn).

### A7 Card timing
- **Canonical: the owner's choice.** Recommended (b). [Cards](computer.md#cards).
- **A7a Always at once.** A set traded in every turn the hand makes one, at every level.
- **A7b By level.** Army sets at once everywhere; at Normal and Hard the Surge waits for a big turn and
  the Raid set for a target; Easy trades all at once.
- **A7c Hard holds raids.** As A7b, and Hard keeps a Raid set for a leader close to a win.
- Interacts with: V2 and V3 (fixed army sets give no reason to wait; the Surge grows with income), V4
  and V11 (holding risks the Squall and the discard), A12 (the Squall's place).

### A8 The computer's random streams
- **Canonical: the owner's choice.** Recommended (a). [Randomness](computer.md#randomness).
- **A8a A stream per computer seat**, seeded from the game seed and the seat number.
- **A8b One computer stream** for all computer seats, seeded from the game seed.
- Interacts with: T50-2 (a saved game replays from the action list either way), A3 and A9 (with
  A8a, changing one seat leaves the others' random choices as they were). Either needs the proposed
  amendment to core-rules.md's Randomness section.

### A9 Strength targets
- **Canonical: the owner's choice.** Recommended (a). [Targets](computer.md#targets).
- **A9a The proposed ladder.** Normal 55% and Hard 70% against three scripted seats; Hard 35%
  against three Normal.
- **A9b Steeper.** 65%, 80% and 45%.
- **A9c Gentler.** 45%, 60% and 30%.
- Interacts with: A1, A4, A6 (a battle bound can cap Hard's strength).

### A10 Raid targets
- **Canonical: the owner's choice.** Recommended (b). [Cards](computer.md#cards).
- **A10a Planned attacks only.** A stack the computer attacks this turn.
- **A10b Planned attacks or the leader.** Also the largest stack of a leader (A5) of 8 or more.
- **A10c Largest anywhere.** The largest enemy stack on the board.
- Interacts with: V5 (the raid's reach and size), A5, A12 (the Shield estimate).

### A11 Playing for the score
- **Canonical: the owner's choice.** Recommended (b). [Near the end](computer.md#near-the-end).
- **A11a No change.**
- **A11b The last 3 rounds.** Countries valued over armies in a round-limit game.
- Interacts with: T50-10 (only with the round limit on), V12 (no events in those rounds).

### A12 Card memory
- **Canonical: the owner's choice.** Recommended (b). [Difficulty levels](computer.md#difficulty-levels).
- **A12a Every level remembers** every public card since the last reshuffle.
- **A12b By level.** Easy none, Normal the Squall's place, Hard every public card.
- **A12c None.** Only what the screen shows now.
- Interacts with: V1 (the reshuffle resets what is known), V4 (the Squall's place), A7, A10.
