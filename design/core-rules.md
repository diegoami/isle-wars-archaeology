# malpaco core rules

The core rules of malpaco: setup, seats, the board's shape, the deal, the turn, reinforcement,
movement, combat, ownership, victory and leaving a game. They are written so that a TypeScript
implementer can build them without reading `spec/`. Cards, island bonus values, production centres and
hazards (random events) are T51's; the computer opponent's behaviour is T53's; the UI is T52's. (The
island bonus rule is settled here, because the board generator needs it; T51 may tune its constants.) Where a
core rule touches them, it says so and stops.

The starting point is the predecessor's rules as read from its code (the in-scope `spec/` files, 59
claims). Each was kept, changed, replaced or dropped for malpaco's sake: the
[decision table](#decisions-claim-by-claim) gives one row per claim. The guiding direction
is the owner's (2026-10-11): fun, roughly balanced, varied; not a copy.

The owner decided every feel-changing choice on 2026-10-12. Values marked *(decision N)* are those
decisions, listed with their options and reasons in
[The owner's decisions](#the-owners-decisions-2026-10-12). Build each behind a named constant.

## Terms

- **Seat**: a player position, controlled by a human or by the computer.
- **Country**: a space on the board. Every country is owned by exactly one seat and holds at least
  one army, at all times after the deal.
- **Island**: a group of countries, fixed for the game. Holding every country of an island pays its
  bonus ([Island bonuses](#island-bonuses)).
- **Border**: an undirected link between two countries. Two countries are neighbours if a border
  joins them.
- **Stack**: the armies in one country.
- **Turn**: one seat's play. **Round**: every live seat's turn once, from the first seat.

## Setup

### Options

A new game is set up on one options screen. Every option is open to every player: there is no
locked option and no registration.

| Option | Values | Default |
| --- | --- | --- |
| Seats | 2, 3 or 4 seats; each seat human or computer *(decision 3)* | 4 seats: seat 1 human, seats 2–4 computer |
| Board | generated from the game seed, a new one each game *(decision 1)* | generated |
| Starting armies per country | 1–2, 1–3, 1–4 (range of the per-country spread, see [the deal](#the-deal)) | 1–3 |
| Human share | −4 to +4 countries per human seat, relative to an even share *(decision 6)* | 0 |
| Computer strength | Easy, Normal or Hard, per computer seat; how each plays is in [computer.md](computer.md#difficulty-levels) *(computer.md, decisions A1 and A3)* | Normal for every computer seat *(computer.md, decision A2)* |
| Event frequency | Off, Rare (1 in 21 per eligible turn change), Normal (1 in 14) or Often (1 in 8); the events are in [variety.md](variety.md#events) *(variety.md, decision V9)* | Normal |
| Domination win | on (threshold [below](#victory)) or off *(decision 9)* | on |
| Round limit | off, or 20 / 30 / 40 rounds *(decision 10)* | off |
| Game seed | any 32-bit number, or random | random, shown in the game |
| Animation speed, sound | presentation only (T52); never change a rule | normal, on |

### Randomness

- Every random value of the rules (the board, the deal, the starting armies, the first seat, dice, card
  draws, events) comes from **one seeded pseudo-random stream**, the game stream. The seed is set at
  setup, shown during the game, and can be typed in to replay the same board and deal.
- Each computer seat's own random choices come from a **separate stream**, seeded from the game seed and
  the seat number; the game stream never serves them, so the computer's choices never change the game
  stream's sequence of values. The computer's actions are recorded in the action list like a human's
  *(computer.md, decision A8)*.
- A draw of an integer in `[a, b]` is uniform. The engine's tests check uniformity and that the same
  seed and the same actions give the same game.
- The engine is deterministic: a game is fully described by its settings, its seed and the list of
  actions taken.

### Stored files

- **Settings**: the last options chosen, restored at the next start.
- **Record**: wins and losses, per seat count, human-share setting and the computer seats' levels, with
  no cap *(computer.md, decision A1)*.
- **Saved game** *(decision 2)*: one slot, stored as settings + seed + action list and restored by
  replaying them, so a saved game cannot be re-rolled by reloading. The game in play is also saved
  automatically at the end of every turn *(T52 UI14, the owner, 2026-10-12)*; what replacing the slot's
  game records is in [Leaving a game](#leaving-a-game).
- Every stored file carries a format version. A file that fails validation (wrong version, missing
  field, value out of range) is ignored and the defaults are used; the player is told once.
- Plain, readable storage; no obfuscation.

There is no board or scenario file to exchange: a board is generated from the seed, so sharing the
seed and the settings shares the board and the deal.

## Seats

- A game has 2 to 4 seats *(decision 3)*. Each is human or computer. Several humans share one screen
  (hot-seat); a game with no human is allowed (watching, testing).
- Seats play in a fixed order, seat 1 to seat N, wrapping. A seat with no countries is skipped
  for the rest of the game.
- Each seat has its own colour (malpaco's palette, T52).
- The default is one human (seat 1) and three computer seats.

## The board

Every game is played on a **new board, generated from the game seed** (the owner's decision 1). The
same seed and settings always give the same board, so a seed reproduces the whole game, board
included. malpaco never reproduces the predecessor's map; it keeps only the shape properties the
spec reports, as the generator's invariants.

### What is fixed and what is generated

| Fixed (constants, same every game) | Generated (from the seed, each game) |
| --- | --- |
| 46 countries | which countries form each island |
| 9 islands, of sizes 3, 3, 3, 3, 5, 5, 7, 7, 10 | where the islands lie, and which islands touch |
| 2 to 5 neighbours per country; borders symmetric; the board connected | the borders inside each island |
| 14 to 18 borders crossing between islands (about one in five) | which countries carry the crossings |
| the bonus rule ([below](#island-bonuses)) | each island's bonus (from its size and entrances) |
| the fairness checks ([below](#fairness-checks)) | each country's screen position (display only) |

- 46 countries give four seats an even share of 11–12 countries and a starting income of 3–4. The
  win threshold follows the count: `ceil(0.75 × C)`, 35 when C = 46.
- Mixed island sizes give a ladder of goals: small islands are early, cheap bonus targets; the large
  ones are valuable and hard to hold. No island has one country.
- Few crossings make island entrances: chokepoints that can be held or forced.

A board is **data**: countries, islands (a partition of the countries), borders, bonuses and
positions. It is made at game start and never changes during a game. Positions are display data
only; no rule reads them.

### Generation

What a board must satisfy is the requirement; how to build one is malpaco's implementation work.

- **Requirements.** All draws come from the game's seeded stream, before the deal, so a seed
  reproduces the board, including any redraws. Every board meets the invariants above (country
  count, island sizes, degree 2–5, symmetry, connectedness, 14–18 crossings) and passes the
  [fairness checks](#fairness-checks). The fairness checks are not weakened to make generation
  easier. Positions keep every two countries at least `MIN_LABEL_GAP` apart in the reference frame;
  this is display data and no rule reads it *(T52 UI15, the owner, 2026-10-12)*.
- **What the engine's tests show.** Over many seeds, the generator finds a valid board within a
  stated, small number of attempts, and the test fixes that number. When attempts run out, the
  behaviour is defined (for example, falling back to a known-valid board for that seed), never a
  hang.
- **Implementation hazard** (GPT-6.1 Sol's re-review of PR #195; a prototype, not a measurement). A
  naive build fails often: island centres by spaced rejection sampling, a minimum spanning tree of
  the centres, then the next-shortest island pairs until 14–18 crossings. Adding the shortest pairs
  without limiting each island's crossings creates hub islands, which the fairness checks reject. At
  a middle spacing, only 14 of 200 seeds gave a valid board within 50 attempts, though valid boards
  do occur, so the checks do not contradict each other. Build with the limits enforced as the board
  grows (island degree at most 4, at most 2 crossings per country), or repair and backtrack, rather
  than generate and reject.

### Island bonuses

An island's bonus, paid while one seat holds every country of it, is

`bonus = floor(size / 2) + entrances`, with a minimum of 2,

where **entrances** is the number of the island's countries that border another island. A larger
island pays more, and an island with more entrances, harder to hold, pays more than one of the same
size that is easy to close. Examples: 3 countries with 1 entrance pay 2; 7 with 3 pay 6; 10 with 4
pay 9. The owner chose this rule (decision 12, 2026-10-12). T51 may tune its constants when it designs
the bonuses' place among cards and events.

### Fairness checks

A generated board is rejected if any of these holds, because each would let the even deal hand one
seat an advantage it did nothing for:

- **An island bonus out of proportion**: an island whose bonus is greater than its size (a small
  island with many entrances). A cheap, rich island makes whichever seat is dealt next to it the
  favourite.
- **A fortress**: an island of 7 or more countries with a single entrance, or more than 3 islands
  with a single entrance. One country can hold such an island against the whole board.
- **Easy bonuses concentrated**: single-entrance islands that together pay more than a quarter of
  all bonuses.
- **A remote island**: an island more than 4 crossings from some other island in the island graph,
  or an island touching more than 4 others. Remote islands are safe havens; hub islands are traps.
- **A crowded crossing country**: a country that carries more than 2 crossings.

The deal then adds its own check: no seat starts holding a complete island ([The deal](#the-deal),
step 4).

### Borders and special countries

- A border between islands is an ordinary border: there is no land or water rule, and every seat,
  human or computer, uses the same borders for every attack and move.
- There are no special countries in the core rules. Any "key country" the computer prefers is the
  computer's own policy (T53), computed on the generated board, not stored data.

## The deal

A new game makes its starting state in this order, all from the game seed:

1. **First seat.** The seat that plays first is drawn uniformly; turn order then follows the seat
   numbers from it, wrapping.
2. **Shares.** Each seat gets an even share of the countries: `floor(C / N)` each, and the
   remaining `C mod N` countries go one each to the **last** seats in turn order (the seats that play
   later), as compensation for moving later *(decision 5)*. On 46 countries: 4 seats get 11, 11, 12,
   12 (in turn order); 3 seats 15, 15, 16; 2 seats 23, 23. Then each human seat's share setting
   (−4 to +4, *decision 6*) is applied, one human after another in turn order: a positive setting
   takes that many countries from the computer seats, one at a time from the computer seat with the
   largest share (the later seat on a tie); a negative setting gives them, one at a time, to the
   computer seat with the smallest share (the earlier seat on a tie). Human shares never move
   between humans. A transfer that would leave a computer seat with fewer than 3 countries is
   skipped, and in a game with no computer seat the settings are ignored.
3. **Countries.** The countries are shuffled uniformly (Fisher–Yates) and dealt in that order to fill
   each seat's share.
4. **No complete island at start.** While some seat holds every country of an island, swap one of
   those countries with a random country of another seat, choosing a pair whose swap completes no
   island for either seat *(decision 4)*.
5. **Armies.** Each seat gets `2 × its countries` armies when the option is 1–3 (generally the
   range's midpoint times its countries, rounded down), placed as 1 per country and the rest spread
   at random with no country above the range's top. Every seat thus starts with the same armies per
   country *(decision 4)*.

6. **Production centres.** Three distinct countries are drawn uniformly as the production centres,
   after step 5 and with no spacing, island or owner condition; what a centre does is in
   [variety.md](variety.md#production-centres) *(variety.md, decision V7)*. The pool formula of
   step 5 is unchanged.

Starting cards, if any, are T51's.

## The turn

A turn has these phases, in order. Every seat follows the same phases; the computer only chooses
differently (T53).

1. **Income**: the reinforcement pool is computed ([Reinforcement](#reinforcement)).
2. **Cards**: a trade-in, if the seat holds a valid set (T51).
3. **Placement**: the whole pool is placed.
4. **Attacks**: any number, from any of the seat's countries ([Combat](#combat)).
5. **Move**: at most one ([Movement](#movement)).
6. **End**: the turn ends after the move, or when the seat ends it. A failed attack never ends the
   turn by itself. End-of-turn effects (a card for a capturing turn, T51) and the
   [victory](#victory) check run here.

A **round counter** starts at 1, increases when the first seat's turn comes round again, and is
always shown. Events (T51) are not drawn in round 1.

## Reinforcement

- The pool is computed once, at the start of the turn, and never recomputed during it: captures made
  this turn raise only the next turn's income.
- `pool = max(floor(countries / 3), 2) + sum of the bonuses of the islands held completely + trade-in`.
  The floor of 2 applies to the country part only. Island bonuses are set by the board
  ([Island bonuses](#island-bonuses)); trade-in values are T51's.
- The whole pool must be placed this turn, on the seat's own countries, in any split. Nothing carries
  over, and there is no way to keep armies back.
- There is no stack cap. A stack can hold any number of armies; the UI (T52) shows large numbers
  compactly.
- The computer places under exactly the same rule; only its choice of countries is T53's.

## Movement

- At most **one move** per turn, made after the attacks; making it ends the turn *(decision 8)*.
- A move goes from one of the seat's countries to a **neighbouring** country the seat owns.
- The source keeps at least 1 army: a 1-army country cannot be a source, and the most that can move
  is all but one. The seat chooses how many (default: all but one).
- A country captured this turn may attack again this turn, and may be the source or the destination
  of the move.

## Combat

- **Who may attack.** A seat may attack an enemy country that borders one of its own countries, from
  that country, if the attacking stack has **at least 2 armies**. There is no other requirement: no
  comparison with the defender's stack *(decision 7)*. The rule is the same for every seat.
- **An exchange.** The attacker and the defender each roll one six-sided die.
  - The higher die wins; the loser of the exchange loses **one** army.
  - **Ties** are re-rolled until the dice differ, so each exchange is a fair coin for both sides
    *(decision 11)*.
- Nothing but the two stacks and the dice enters an exchange: no level, setting, speed or hidden
  modifier. A card that changes combat is T51's and must say so on the card.
- **A battle** is a sequence of exchanges between the same two countries. After every exchange the
  attacker may stop, at no cost. The battle ends when:
  - the defender reaches 0 armies: the country is captured ([Ownership change](#ownership-change));
  - the attacker is down to 1 army: the battle stops, and the attacker keeps its country with 1 army
    *(decision 7)*; or
  - the attacker stops.
- The UI (T52) offers one exchange per action and "continue until captured, stopped, or down to N".
  The engine resolves exchanges one at a time either way, so results do not depend on pace.
- There is no limit on attacks or battles per turn, for any seat. How often the computer attacks is
  its policy (T53), not a rule.
- No setup option changes combat. Difficulty comes from the deal and from the computer's strength
  (T53), never from the dice.

## Ownership change

- When a defender reaches 0 armies, the country changes owner at once.
- The attacker moves armies in from the attacking country: at least 1, at most all but one of the
  attacker's remaining armies. The seat chooses; the default is all but one. Armies are conserved:
  no stack cap clips them.
- The computer follows the same rule; how many it moves is its policy (T53).
- A seat left with no countries is **eliminated**: it is skipped for the rest of the game. What
  happens to its cards is T51's.

## Victory

At the end of every turn (after the move, before the next seat's income), in this order:

1. **Total conquest**: a seat holding every country wins.
2. **Last seat standing**: if only one seat has countries, it wins (the same as 1, stated for 2- and
   3-seat games where elimination is the usual end).
3. **Domination** (when the option is on, the default): a seat holding at least `ceil(0.75 × C)`
   countries, **35 of 46**, at the end of its own turn wins *(decision 9)*.
   The rule is the same for humans and computers; a human who wants to fight on turns the option off
   at setup.
4. **Round limit** (when the option is on): at the end of the last round's last turn, the seat with
   the most countries wins; ties are broken by total armies, then by turn order (the later seat
   wins) *(decision 10)*.
5. **No human left** (only in a game with at least one human): when every human seat is eliminated,
   the game ends as a loss for the humans; the player may watch the computers finish or stop.

There is no draw. A game with the domination win or the round limit on always ends; with both off
it ends by total conquest only.

Events (T51) are not drawn while any seat is within 4 countries of winning: holding
`ceil(0.75 × C) − 4` or more countries (31 of 46) when domination is on, or `C − 4` or more (42 of
46) when it is off. When the round limit is on, no events are drawn in its last 3 rounds either
([variety.md](variety.md#when-an-event-is-drawn), decision V12). The last turns are decided by play,
not luck.

A finished game adds one win or loss per human seat to the record.

## Leaving a game

- A **resign** control is always available to a human seat. Resigning records a loss, whatever the
  seat holds, and turns the seat over to the computer (if other humans remain) or ends the game. A
  seat turned over this way is played at Normal *(T52 UI18, the owner, 2026-10-12)*.
- Starting a new game while one is in progress asks for confirmation and counts as resigning, unless
  the game is saved first *(decision 2)*.
- Each game has an identity fixed when it starts and kept in its save; it is not drawn from the game
  stream. Saving a game into the slot while the slot holds a different, unfinished game records a loss
  for each human seat of that game that has no result yet, as resigning does; saving the same game
  again records nothing. The record keeps, for each game identity, the human seats whose result it
  holds, and never records a second result for one *(T52 UI14, the owner, 2026-10-12)*.
- The computer seats never concede; domination (above) replaces a concession offer.

## Fun and balance, argued

Every number in this section is a **model**, not a measurement of the predecessor or of malpaco.
Recorded play has not measured game length or army growth yet (`runs/coverage.md`: Q-TRN-05 and
Q-REI-05 are unestablished).

### Combat odds

Computed **exactly**, by the Markov recursion over (attacker, defender) stacks under uniform dice:
the attacker can lose `A − 1` exchanges (one army stays behind) and must win `D`. The code, run as
pasted, prints the two tables below (percent chance to capture, rounded); the equal-stack figures
quoted after them are `cap(n, n, p)` from the same function.

    from fractions import Fraction as F
    from functools import lru_cache
    def cap(A, D, p):
        @lru_cache(None)
        def P(a, d):
            if d == 0: return F(1)
            if a == 1: return F(0)
            return p * P(a, d - 1) + (1 - p) * P(a - 1, d)
        return P(A, D)
    for p in (F(5, 12), F(1, 2)):
        for A in [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30]:
            print(A, [round(100 * float(cap(A, d, p))) for d in [1, 2, 3, 4, 5, 6, 8, 10, 15]])

**Ties to the defender** (attacker wins an exchange with p = 5/12):

| A \ D | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 42 | 17 | 7 | 3 | 1 | 1 | 0 | 0 | 0 |
| 3 | 66 | 38 | 20 | 10 | 5 | 2 | 1 | 0 | 0 |
| 4 | 80 | 55 | 35 | 20 | 11 | 6 | 2 | 0 | 0 |
| 5 | 88 | 69 | 49 | 32 | 20 | 12 | 4 | 1 | 0 |
| 6 | 93 | 79 | 62 | 44 | 30 | 20 | 7 | 2 | 0 |
| 8 | 98 | 91 | 80 | 66 | 51 | 38 | 18 | 8 | 1 |
| 10 | 99 | 96 | 90 | 81 | 69 | 57 | 33 | 17 | 2 |
| 12 | 100 | 99 | 95 | 90 | 82 | 72 | 49 | 30 | 5 |
| 15 | 100 | 100 | 99 | 97 | 93 | 87 | 71 | 51 | 14 |
| 20 | 100 | 100 | 100 | 100 | 99 | 97 | 91 | 80 | 39 |
| 30 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 98 | 86 |

**Ties re-rolled** (p = 1/2):

| A \ D | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 50 | 25 | 12 | 6 | 3 | 2 | 0 | 0 | 0 |
| 3 | 75 | 50 | 31 | 19 | 11 | 6 | 2 | 1 | 0 |
| 4 | 88 | 69 | 50 | 34 | 23 | 14 | 5 | 2 | 0 |
| 5 | 94 | 81 | 66 | 50 | 36 | 25 | 11 | 5 | 0 |
| 6 | 97 | 89 | 77 | 64 | 50 | 38 | 19 | 9 | 1 |
| 8 | 99 | 96 | 91 | 83 | 73 | 61 | 40 | 23 | 4 |
| 10 | 100 | 99 | 97 | 93 | 87 | 79 | 60 | 41 | 11 |
| 12 | 100 | 100 | 99 | 97 | 94 | 89 | 76 | 59 | 21 |
| 15 | 100 | 100 | 100 | 99 | 98 | 97 | 91 | 80 | 43 |
| 20 | 100 | 100 | 100 | 100 | 100 | 100 | 99 | 96 | 76 |
| 30 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 98 |

What they say:

- With ties to the defender, an attack is a coin flip only at about **twice** the defender's armies
  (8 against 5: 51%; 15 against 10: 51%). Equal stacks capture, by stack size (exact, rounded to
  0.1%): 2 against 2, 17.4%; 3, 19.9%; 4, 20.3%; 5, 20.1%; 6, 19.5%; 8, 18.3%; 10, 16.9%; 15,
  13.9%; 20, 11.4%. The chance peaks near 4 and falls as stacks grow, because the attacker's one
  army left behind matters less than the defender's edge in every exchange. Each defending
  army costs the attacker 7/5 = **1.4** armies on average in a long battle. Placing an army on a
  border is worth 1.4 attacking armies, so turtling pays, and with no ending rule a turtled board
  never resolves.
- With ties re-rolled, the coin flip is at **one more** army than the defender (5 against 4: 50%;
  11 against 10: 50%, exactly, by symmetry), and a 2-to-1 attack captures 69–96%. Equal stacks
  capture 25.0% at 2, 34.4% at 4, 37.7% at 6, 40.7% at 10 and 43.6% at 20, rising towards one half. Each defending
  army costs one attacking army. Defence keeps a small edge (the army left behind, and the armies
  that must move in), so a clearly larger stack wins and an even one is a gamble. That makes an
  attack a readable decision: bigger stack, better odds, and a real chance of an upset.
- The owner chose ties re-rolled (decision 11).

### The attacker's minimum and the gates

- The predecessor let a human attack only with at least as many armies as the target, and its
  computer needed more than the target and 3 to 5 armies. In malpaco every seat needs only 2.
- Dropping the comparison is safe: a small stack attacking a big one loses on average (with ties
  re-rolled, 3 against 6 captures 6% of the time). What it allows is **attrition**: several small
  stacks can wear a big one down before the main attack, at an even trade of armies. That is a
  tactic, not a trap, because a battle can be stopped after any exchange and a failed attack costs
  only the armies spent.
- With the predecessor's forfeit (a human attacker worn down to 1 army lost its own country), the
  equality gate was a trap: a human attacking 4 against 4 with ties to the defender captures 20% of
  the time and, fought to the end, **loses its own country 80% of the time**; the computer, which
  never attacks at equality and never forfeits, faced neither risk. malpaco removes the forfeit for
  every seat (decision 7).

### Income

`max(floor(n / 3), 2)` by countries held (island bonuses, [set by the board](#island-bonuses), come on top):

| Countries | 1–8 | 9–11 | 12–14 | 15–17 | 18–20 | 21–23 | 24–26 | 27–29 | 30–32 | 33–35 | 46 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Income | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 15 |

- Divisor 3 and floor 2 are kept. Income grows with the board held, which rewards expansion; the
  floor of 2 keeps a seat with 1–8 countries playing without rescuing it. A runaway leader is
  checked by the domination win (the game ends rather than dragging on) and by T51's cards
  (surprise).
- **The even deal's rounding matters.** On 46 countries, four even shares are 12, 12, 11, 11: income
  4, 4, 3, 3. A seat with 11 starts with a quarter less income than a seat with 12. malpaco gives the
  two 12-shares to the seats that play **last**, so the extra income offsets moving later (decision 5).
  With 3 seats (15, 15, 16) every seat earns 5; with 2 seats (23, 23) both earn 7.
- **Starting armies.** The predecessor drew 1–3 per country independently. For 11 countries that is
  22 armies on average with a standard deviation of about 2.7, so two seats can start 5 or more
  armies apart by luck alone (24% for a given pair, computed exactly over the 3^11 draws of each seat).
  malpaco gives every seat the same armies per country and randomises only where they stand
  (decision 4).

### Asymmetries removed

The predecessor's human and computer played under different rules: the attack gate (equality
against a margin), the minimum stack (2 against 3–5), the forfeit (human only), the attack pacing
(unlimited against drawn rounds), the concession (offered only to a human), and the dealt share
(fixed by the human's difficulty level). malpaco has **one rule set for every seat**. The computer's
strength is a matter of its decisions (T53), and the human's handicap is an explicit setting
(decision 6), so a player can see what is hard and why.

### Game length and the end

- **A toy model of pace.** A battle costs the attacker about `D × (1 − p) / p` armies plus at least
  1 moved in. Early on (income 3–4, defenders 1–3 armies, about 2 on average) a capture costs about
  3 armies with ties re-rolled and about 3.8 with ties to the defender, so a seat gains roughly 1 to
  1.3 countries a turn with ties re-rolled (0.8 to 1.05 with ties to the defender) before the others
  take any back. A leader starting from 11–12 then needs a
  couple of dozen net gains to reach 35, which suggests games of a few dozen rounds. This is a model
  with invented averages, to be replaced by play-tests.
- **The mop-up.** From 35 countries to 46 is 11 more captures against a beaten field: about a third
  of a game's captures, with the result already clear. The domination win at three quarters cuts
  that part off; total conquest stays available by turning the option off.
- **Stalls.** The predecessor had no ending but total conquest, the computers' concession and the
  loss of every human; nothing ended a stalled board. malpaco ends every game that has domination or
  a round limit on, and combat with ties re-rolled makes stalls less likely in the first place.

## The owner's decisions (2026-10-12)

The owner decided all twelve choices on 2026-10-12 (the twelfth, the island bonus rule, after GPT-6.1 Sol's re-review). Each entry keeps the claims it settles, the
options offered, the recommendation and its reason, and adds the decision. Eleven decisions follow the
recommendation; **decision 1 went against it** (a generator, not hand-made boards). The rules above
describe the decided options.

1. **Which boards ship** (C-BRD-01).
   - (a) one hand-made board meeting the invariants; (b) two to four hand-made boards of different
     shapes; (c) a generator that makes a new board meeting the invariants each game.
   - Recommendation was (a) for the first playable, then (b): one board is enough to tune the
     balance, and hand-made boards avoid the risk of a generator making dull or lopsided maps.
   - **Decided: (c), against the recommendation.** Every game gets a new board from the seed, which
     gives the most variety. The risk the recommendation named is handled by the generator's
     invariants and its [fairness checks](#fairness-checks), which reject lopsided boards.
2. **Saving a game** (C-SET-05, C-RND-02).
   - (a) no saving; (b) one save slot, restored by replaying seed and actions; (c) several slots and
     an undo.
   - Recommendation (b): a game of a few dozen rounds is long for one sitting, and replay from the
     seed means reloading cannot change a die; an undo (c) would.
   - **Decided: (b).**
3. **Number of seats and who plays them** (C-PLY-01, C-PLY-02).
   - (a) four seats, one human; (b) 2–4 seats, each human or computer, hot-seat allowed; (c) 2–6
     seats (needs a larger board).
   - Recommendation (b): two- and three-seat games are shorter and play differently (a duel, a
     three-way balance), which is variety for free.
   - **Decided: (b).**
4. **The fair start** (C-STA-02, C-STA-05).
   - (a) uneven random shares and 1–3 armies per country drawn independently; (b) even shares, equal
     armies per country placed at random, no complete island at start; (c) as (b), and each seat then
     places its starting armies itself, in turn.
   - Recommendation (b): starting luck a player cannot answer is not fun; (c) adds an opening
     decision but slows the start.
   - **Decided: (b).**
5. **First-mover compensation** (C-STA-06).
   - (a) a random first seat, no compensation; (b) a random first seat, and the leftover countries of
     the even deal go to the seats that play last; (c) as (b), plus one starting army per place in
     turn order.
   - Recommendation (b): the deal's remainder (two countries on 46 with four seats) is a free
     counterweight worth one army a turn; (c) is a guess at a size not measured.
   - **Decided: (b).**
6. **The human handicap** (C-STA-03, C-STA-07).
   - (a) no handicap; (b) even shares by default, and a per-human share setting from −4 to +4
     countries; (c) fixed shares per difficulty level.
   - Recommendation (b): separating "how strong is the computer" from "how big is my start" lets a
     new player ease in and a strong one take a visible handicap.
   - **Decided: (b).**
7. **Attack rules: the gate and the forfeit** (C-CMB-01, C-CMB-02, C-CMB-03, C-CMB-09, C-TRN-01).
   - (a) a human needs 2 and at least the defender's count and forfeits its country at 1 army; the
     computer needs more and never forfeits; (b) one rule: at least 2 armies, no comparison, no
     forfeit, a failed attack does not end the turn; (c) one rule with the gate: at least 2 and at
     least the defender's count, no forfeit.
   - Recommendation (b): the same rule for everyone is fairer and easier to learn, and without the
     forfeit a failed attack costs only the armies spent.
   - **Decided: (b).**
8. **The move** (C-MOV-01).
   - (a) one move between neighbouring countries, ending the turn; (b) one move along a chain of the
     seat's own countries; (c) several neighbour moves per turn.
   - Recommendation (a): one short move makes positioning a real decision and keeps turns quick.
   - **Decided: (a).**
9. **How a game is won** (C-VIC-01, C-SUR-01, C-SUR-02).
   - (a) total conquest only, plus a concession offered to a human; (b) total conquest, or domination
     at three quarters of the board for any seat, on by default and switchable off; (c) as (b) at two
     thirds.
   - Recommendation (b): the last quarter is a mop-up with the winner known, and one threshold for
     all seats is fair.
   - **Decided: (b)**: `ceil(0.75 × C)`, 35 of 46.
10. **Round limit and draws** (C-VIC-02).
    - (a) no limit and no draw; (b) an optional round limit (20, 30 or 40), off by default, with
      tie-breaks; (c) a round limit on by default.
    - Recommendation (b): a short game when wanted, without changing the standard one; tie-breaks
      always name a winner.
    - **Decided: (b).**
11. **Combat odds: ties** (C-CMB-05, C-CMB-12).
    - (a) ties to the defender (p = 5/12); (b) ties re-rolled (p = 1/2); (c) ties to the attacker
      (p = 7/12).
    - Recommendation (b): with (a) defence is 1.4 times as efficient as attack and boards lock; with
      (c) attacking is so strong that position stops mattering.
    - **Decided: (b).**
12. **Island bonuses on a generated board** (part of C-BRD-01's replacement; raised by GPT-6.1 Sol's
    re-review, because decision 1 does not itself choose a bonus rule).
    - (a) `floor(size / 2) + entrances`, minimum 2, never above the size; (b) `round(0.75 × size)`,
      minimum 2, the predecessor's proportion, ignoring entrances; (c) left to T51.
    - Recommendation (a): an island that is harder to hold pays more, and a single-entrance island is
      not cheap to hold for its value.
    - **Decided: (a).**

## Decisions, claim by claim

One row per in-scope spec claim (59). `keep` serves fun or balance as it is; `change` alters it;
`replace` swaps in a different rule; `drop` removes it; `open` would wait for the owner (none is left
since the owner's decisions of 2026-10-12). A claim that is
not `supported` or `corroborated` still gets a row; its decision is a design choice and the row says
so.

| Claim | Decision | malpaco's rule | Why |
| --- | --- | --- | --- |
| C-BRD-01 | replace | [The board](#the-board): a new board generated from the seed each game, under fixed invariants and fairness checks; bonuses by size and entrances | One fixed map is the same game every time; a seeded generator gives a new board each game while the invariants and fairness checks keep it fair (decisions 1 and 12). Replace, not change: the fixed board itself is gone, only its shape properties stay. |
| C-BRD-02 | keep | [What is fixed](#what-is-fixed-and-what-is-generated): 46 countries on every generated board | About 11–12 countries per seat for four seats gives a starting income of 3–4 and enough room to manoeuvre without long games; a fixed count also fixes the win threshold at 35. |
| C-BRD-03 | keep | [What is fixed](#what-is-fixed-and-what-is-generated): 9 islands of sizes 3, 3, 3, 3, 5, 5, 7, 7, 10, none of one country | Mixed sizes give a ladder of goals: cheap small bonuses early, large valuable ones later. The generator keeps the sizes; their places and shapes are new each game. |
| C-BRD-04 | keep | [Generation](#generation): symmetric borders, 2–5 neighbours, connected, 14–18 crossings | Few crossings make island entrances chokepoints worth holding or forcing; symmetry and connectedness keep every country reachable. These are the generator's invariants. |
| C-BRD-05 | change | [The board](#the-board): crossings are ordinary borders, and every seat uses the same borders | Kept: no land or water rule. Changed: the computer's moves no longer follow a hard-coded pair table; one border graph for everyone works on any board and hides no rule from the player. |
| C-BRD-06 | keep | [The board](#the-board): positions are generated with the board and are display data only | A rule that reads screen positions would tie play to layout; keeping them display-only lets T52 lay out freely. |
| C-BRD-07 | drop | [The board](#the-board): no special countries in the core rules | Per-island key lists that nothing reads are dead data. A preferred-country list is the computer's policy, T53's to design. |
| C-SET-01 | change | [Options](#options): seats, board (generated), starting armies, human share, computer strength, events, domination, round limit, seed, speed, sound | The options are where variety comes from: player count, handicap, game length and end conditions are added; strength stays and is T53's, events stay and are T51's. |
| C-SET-02 | drop | [Options](#options): every option open | The locks served a registration scheme; in malpaco they would only remove variety. |
| C-SET-04 | drop | [Options](#options): no registration; speed is presentation only | A registration check has no purpose in malpaco; the speed helpers become a UI setting (T52) that never changes a rule. |
| C-SET-05 | change | [Stored files](#stored-files): settings, an uncapped record, one saved game restored by replay | The record's cap and cipher served registration; plain storage and saving a long game help the player (decision 2). |
| C-SET-06 | keep | [Stored files](#stored-files): no board or scenario file; the seed reproduces board and deal | The absence is kept on purpose: with a generated board, a seed and the settings already reproduce a whole game, so a separate exchange format would add nothing. |
| C-SET-07 | change | [Stored files](#stored-files): versioned, validated files; invalid files fall back to defaults | Unvalidated files let bad values into a game; a version and validation make old or edited files safe. |
| C-RND-01 | change | [Randomness](#randomness): one seeded stream; the seed is shown and can be set | A visible seed lets players replay or share a deal and makes the engine testable; nothing about play changes. |
| C-RND-02 | change | [Randomness](#randomness), [Stored files](#stored-files): deterministic engine; a saved game is restored by replay | Replay from seed and actions restores a game exactly, so reloading cannot re-roll luck. |
| C-RND-03 | keep | [Randomness](#randomness): one game stream for the rules' draws, uniform integer draws; each computer seat's choices use a stream of its own from the same seed (computer.md, decision A8) | One stream keeps replay exact; malpaco requires uniform draws and tests them, where the predecessor's uniformity was not established. The computer's separate streams keep its choices from shifting the dice, and its actions are in the action list. |
| C-PLY-01 | change | [Seats](#seats): 2 to 4 seats | Two- and three-seat games are shorter and play differently, which adds variety (decision 3). |
| C-PLY-02 | change | [Seats](#seats): each seat human or computer; hot-seat and all-computer allowed | The lock served registration; several humans on one screen and watch-only games add ways to play (decision 3). |
| C-PLY-03 | keep | [Seats](#seats): default one human, three computers | A full four-seat game against the computer is the standard single-player game and the base the balance is tuned for. |
| C-STA-01 | change | [The deal](#the-deal): a fixed order from the seed; what varies is the board, the shares, the countries, the armies and the first seat | Kept: a short, fixed setup chain, easy to test and to replay from a seed. Changed: the board now varies too (decision 1), which is the largest source of each game's freshness. |
| C-STA-02 | replace | [The deal](#the-deal), steps 2–4: even shares, uniform shuffle, no complete island at start | The predecessor's fill gave uneven shares by luck through a soft threshold; even shares make the start fair and readable (decision 4). |
| C-STA-03 | replace | [The deal](#the-deal), step 2, and [Options](#options): an explicit human share setting, even by default | Tying the human's share to a difficulty level hid the handicap; a visible share setting separates handicap from computer strength (decision 6). |
| C-STA-04 | keep | [The deal](#the-deal), step 3: a uniform shuffle | A uniform shuffle is the fair way to place countries; it is the right tool and costs nothing. |
| C-STA-05 | change | [The deal](#the-deal), step 5: equal armies per country, spread at random | Independent draws can leave two seats five or more armies apart by luck; equal totals keep the start fair while placement stays random (decision 4). |
| C-STA-06 | change | [The deal](#the-deal), steps 1–2: a uniform first-seat draw, and the deal's remainder goes to the last seats | The draw's off-by-one detour has no purpose; giving the remainder to the later seats offsets the first mover's head start (decision 5). |
| C-STA-07 | keep | [Stored files](#stored-files), [The deal](#the-deal): no prescribed starting position; settings and seed decide the start | Fewer ways to start means fewer edge cases; the share now comes from a visible setting, not a stored difficulty. |
| C-TRN-01 | change | [The turn](#the-turn): income, cards, placement, attacks, one move, end; a failed attack never ends the turn | Ending the turn on a failed attack punished trying on top of the armies lost and pushed play towards waiting (decision 7). |
| C-TRN-02 | keep | [Seats](#seats): fixed order, wrapping, eliminated seats skipped, random first seat | A fixed order is easy to follow and plan around; the random first seat and its compensation keep it fair. |
| C-TRN-03 | change | [The turn](#the-turn): a round counter, always shown; no events in round 1 | Players judge pace and plan for a round limit by the round number; a hidden counter gave them nothing. |
| C-REI-01 | keep | [Reinforcement](#reinforcement): countries divided by 3, rounded down, once per turn | Income that grows with land held rewards expansion; computing it once per turn keeps the turn's budget clear. Numbers in [Income](#income). |
| C-REI-02 | keep | [Reinforcement](#reinforcement): a floor of 2 on the country part | The floor keeps a small seat playing without rescuing it, so eliminations still happen and games end. |
| C-REI-03 | keep | [Reinforcement](#reinforcement): country part + complete-island bonuses + trade-in | Three readable sources of income, each a goal: land, islands, cards. Bonuses follow the board's rule ([Island bonuses](#island-bonuses)); trade-in values are T51's and the computer's trade choices T53's. |
| C-REI-04 | change | [Reinforcement](#reinforcement): the whole pool is placed, nothing carries over, no stack cap | Kept: place everything, no carry-over (no hoarding). Changed: the 999 clamp silently destroyed armies; malpaco has no cap. |
| C-REI-05 | change | [Reinforcement](#reinforcement): the computer places under the same rule, with exact accounting | One placement rule for every seat; the computer's leftover pool and clamp losses were accounting slips, not design. Where it places is T53's. |
| C-MOV-01 | keep | [Movement](#movement): at most one move, after attacks, ending the turn | One short move makes positioning a real decision and keeps turns quick (decision 8). |
| C-MOV-02 | keep | [Movement](#movement): at least 1 army stays; the seat chooses how many move | Every country must hold an army; letting each seat choose the number is one rule for all. How many the computer moves is T53's. |
| C-MOV-03 | keep | [Movement](#movement): neighbours only; a just-captured country may attack and move | Chained captures let a strong stack build momentum across a front, which is exciting and rewards concentration. |
| C-CMB-01 | replace | [Combat](#combat): every seat attacks with at least 2 armies, no comparison with the defender | Two different gates for human and computer were unfair and hidden; one minimum for all is fair, and attrition attacks become a tactic (decision 7). |
| C-CMB-02 | replace | [Combat](#combat): no ratio or difference gate for anyone | With no comparison gate, its form no longer matters; the dice already make a weak attack costly ([The attacker's minimum](#the-attackers-minimum-and-the-gates)) (decision 7). |
| C-CMB-03 | replace | [Combat](#combat): minimum attacking stack 2 for every seat | The computer's larger minimums are its caution, which belongs in its policy (T53), not in a rule the human cannot see (decision 7). |
| C-CMB-04 | keep | [Combat](#combat): one six-sided die each per exchange, no stack cap; pace is a UI choice | One die against one is easy to read, and each exchange is a visible event; batching only changed pace and becomes a UI control (T52). |
| C-CMB-05 | change | [Combat](#combat): ties are re-rolled | With ties to the defender a defending army is worth 1.4 attacking ones and boards lock; re-rolled ties make each exchange fair, so a larger stack is favoured and upsets stay possible (decision 11). |
| C-CMB-06 | keep | [Combat](#combat): the exchange's loser loses one army | One army per exchange keeps battles granular, so the attacker can stop at any point with a clear picture. |
| C-CMB-07 | keep | [Combat](#combat): only the two stacks and the dice enter an exchange | No hidden modifiers: players can reason about odds. A combat card (T51) must state its effect openly. |
| C-CMB-08 | change | [Combat](#combat): every seat resolves one exchange at a time and may stop after any | The same rule for all seats; the computer's choice when to stop is its policy (T53). The UI's continue control (T52) changes pace, not results. |
| C-CMB-09 | replace | [Combat](#combat): an attacker at 1 army stops and keeps its country, for every seat | The human-only forfeit made attacking a trap (80% loss of the country at 4 against 4) and favoured waiting; no forfeit for anyone (decision 7). |
| C-CMB-10 | change | [Combat](#combat): no limit on attacks per turn for any seat | Unlimited attacks allow momentum; the computer's drawn rounds were pacing, which becomes its policy (T53). |
| C-CMB-11 | keep | [Combat](#combat): no setup option changes combat | One set of odds to learn; difficulty comes from the deal's handicap and the computer's strength, never from the dice. |
| C-CMB-12 | change | [Combat odds](#combat-odds): the exact model under uniform dice, with ties re-rolled | Inconclusive in the spec, so this row is a design choice: malpaco sets the odds deliberately. With ties re-rolled a coin flip needs one army more than the defender, not about twice (decision 11). |
| C-OWN-01 | change | [Ownership change](#ownership-change): every capturing seat moves in at least 1, at most all but one; no clipping | One rule for all seats; a captured country is never empty; armies are conserved instead of clipped at 999. |
| C-VIC-01 | change | [Victory](#victory): total conquest, last seat standing, or domination at 35 of 46 | Total conquest alone ends with a long mop-up; domination for every seat ends the game when it is decided (decision 9). |
| C-VIC-02 | change | [Victory](#victory): an optional round limit (20, 30 or 40), off by default, tie-broken, no draw | A round limit offers short games without changing the standard one; the tie-breaks always name a winner, so no draw is needed (decision 10). |
| C-VIC-03 | change | [Victory](#victory): domination and the round limit end stalled games | Nothing ended a stalled board; with domination or a round limit on, every game ends. |
| C-VIC-04 | change | [Victory](#victory): events paused in round 1 and within 4 countries of winning (31 or 42 of 46) | Kept: no luck at the very start or end. Changed: the threshold follows malpaco's win condition. Event odds are T51's. |
| C-VIC-05 | keep | [Ownership change](#ownership-change): a seat with no countries is eliminated and skipped | Elimination is the clear consequence of losing everything; what happens to its cards is T51's and may change there. |
| C-VIC-06 | change | [Stored files](#stored-files): the record per seat count, share setting and computer levels, no cap | The cap served registration; a record grouped by setup shows progress honestly. |
| C-SUR-01 | replace | [Victory](#victory): a domination win for any seat replaces the concession | An offer only a human receives is an asymmetry; one automatic threshold for all is simpler and fair (decision 9). |
| C-SUR-02 | replace | [Victory](#victory): no offer; a human who wants to fight on turns domination off at setup | The accept-or-refuse step is replaced by a setup option, so the choice is made once and known to all (decision 9). |
| C-SUR-03 | replace | [Leaving a game](#leaving-a-game): an explicit resign that records a loss whatever the seat holds | Leaving through a new game, charged only at 1–9 countries and not for one seat, was unclear and uneven; an explicit resign is honest. |
