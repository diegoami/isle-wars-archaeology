# malpaco computer opponent

How a computer seat plays malpaco: what it wants, what it may know, how it decides in each phase of
the turn, and how its difficulty levels differ. It is written so that a TypeScript implementer can
build it without reading `spec/`. It builds on [core-rules.md](core-rules.md) (T50: one attack rule
for every seat, ties re-rolled, one move, domination at 35 of 46, a seeded and replayable game) and
[variety.md](variety.md) (T51: the 40-card deck with 5/8/15 sets, the doubling Surge set, the Raid set
and the Shield, the hand-emptying Squall, three wandering centres, and the predecessor's events). It
plays by those rules exactly; it never adds one. Its turn presentation and speed settings are T52's.

The starting point is the predecessor's computer as read from its code (`spec/computer-opponent.md`,
9 claims). The [decision table](#decisions-claim-by-claim) gives one row per claim. The guiding
direction is the owner's (2026-10-11): fun, roughly balanced, varied; not a copy. In the standard
game three of the four seats are computers, so this file describes most of what a player meets.

This is a design, not an algorithm. It states the computer's goals, the information it may use, its
decision rules and the properties they must have; how to compute them well is malpaco's implementation
work, and malpaco's tests measure the result ([Measuring strength](#measuring-strength)). Every
feel-changing call is listed in [Choices for the owner](#choices-for-the-owner) as A1 to A12, with
options and a recommendation; values marked *(A<n>)* below are the recommended options, and the owner
decides each. Build every value behind a named constant (the names in capitals below).

## Terms

Terms of [core-rules.md](core-rules.md) and [variety.md](variety.md) (seat, country, island, border,
stack, turn, round, card, set, centre, event) hold here.

- **Computer seat**: a seat whose actions are chosen by this policy. A human seat that resigns and
  is turned over to the computer becomes one.
- **Level**: the computer strength setting of a computer seat ([Difficulty levels](#difficulty-levels)).
- **View**: what a computer seat may read when it decides ([Information](#information)).
- **Front country**: an own country with at least one enemy neighbour. **Interior country**: an own
  country with none.
- **Threat on a country**: the largest stack among its enemy neighbours.
- **Capture chance** `cap(a, d)`: the exact chance that an attacking stack of `a` captures a stack of
  `d` if the battle is fought to its end, under ties re-rolled
  ([core-rules.md, Combat odds](core-rules.md#combat-odds)). It is public arithmetic that a human
  could do with the same table.
- **Leader**: a seat that the leader check treats as running away ([The leader check](#the-leader-check)).

## Fairness and honesty

These are requirements on every level. A level that breaks one is a bug, whatever its win rate.

### One rule set

- The computer acts only through the engine's action interface, the one a human seat's UI uses:
  trade a set or skip, place armies, start a battle, roll the next exchange or stop, choose a
  move-in, make the move or end the turn, choose a raid target, choose a discard. The engine checks
  every action against the rules of core-rules.md and variety.md and refuses an illegal one. No
  action exists only for the computer, and no rule reads whether a seat is a computer.
- The computer is bound by T50's single attack rule (at least 2 armies, no comparison, no forfeit),
  one move per turn, one set per turn with at most two Wilds, the discard before a draw into a full
  hand, and every card and event rule, exactly as a human is.

### Information

- **A computer seat's view** holds what a human in that seat could see on the screen and remember:
  the board, every owner and stack, the centres, the round, the options, the seat order, every seat's
  hand count, its own hand, the discard pile as the UI shows it to every seat, and the history of
  public happenings (each battle and its result, each traded set, which reveals its three cards on the
  face-up discard pile, each raid and Shield cancellation, each event).
- **It may not read**: another seat's cards, the order or contents of the draw pile beyond what
  follows from public information, the state or the next values of any random stream, whether another
  seat is human or computer, or the plans or hands of other computer seats. Each computer seat is a
  separate player: computer seats share no information and make no plan together.
- **How to build it.** The decision code receives a view object built from the public state and the
  seat's own hand; it has no reference to the engine's internal state. A test changes only hidden
  things (another hand's kinds, the draw pile's order, the game stream's state, another seat's human
  or computer flag) and checks that the computer's next action does not change
  ([Behaviour tests](#behaviour-tests)).

### Randomness

- **A stream per computer seat** *(A8)*. A computer seat's own random choices (a tie between equally
  good actions, a planned mistake at a low level) come from its own seeded stream, derived from the
  game seed and the seat number, never from the game's stream. The game stream (dice, card draws,
  events, the deal) therefore yields the same sequence of raw values whatever the computer decides or
  how often it draws on its own stream. What the computer's choices do change is which battles are
  fought, so which of those values falls to which battle: that is play, not a change of the dice.
- **Replay.** Every computer action is recorded in the game's action list like a human's. A saved
  game ([core-rules.md, Stored files](core-rules.md#stored-files)) replays from settings, seed and
  actions without re-running the computer, so a later version of the computer cannot change a saved
  game. Re-running the computer from the same state, view and stream gives the same actions; the tests
  use this.
- This needs a change to core-rules.md, whose [Randomness](core-rules.md#randomness) section puts
  the computer's random choices in the one game stream: the proposed amendment is in A8.

### Levels change decisions only

A level changes how the computer decides: its foresight, aggression, card timing, deliberate
mistakes, leader check and card memory. It never changes a rule, a die, a card, an army count or the
view. There is no bonus army, no better die and no extra card at any level. The human share setting
([core-rules.md, decision 6](core-rules.md#the-owners-decisions-2026-10-12)) stays a separate
option: a player can face Hard computers with an even share, or Easy ones with a handicap.

### The predecessor's computer-only behaviours

Each behaviour the predecessor gave its computer alone is dropped or replaced:

| The predecessor's computer-only behaviour | Row | malpaco |
| --- | --- | --- |
| attacks in a drawn number of rounds (2 to 5, more with many countries) | C-AI-03 | dropped: the computer attacks while a battle is worth it, up to a pacing bound ([Attacks](#attacks)) |
| a drawn chance to skip a turn's attacks | C-AI-03 | dropped: a turn with no attack happens only when no battle is worth it |
| extra attack rounds once no human seat is left | C-AI-03 | dropped: the game ends when every human is out ([core-rules.md, Victory](core-rules.md#victory)), and the policy never reads seat kinds |
| a drawn minimum stack (3 to 5) and a drawn margin over the defender before it may attack | C-AI-04 | replaced: T50's one rule for every seat; the computer's caution is a capture-chance threshold in its policy |
| a uniform pick from a weighted list of candidate pairs | C-AI-02, C-AI-04 | replaced: the computer picks the battle worth most |
| placement by island ranks, fixed scores and drawn splits, with one-army seeds | C-AI-01, C-AI-02 | replaced: placement serves the turn's plan ([Placement](#placement)) |
| a fixed move table over 23 countries, corridor walks, and a centre source vetoed 7 times in 8 | C-AI-05 | replaced: one move chosen on the generated board by its purpose ([The move](#the-move)) |
| a fixed trade priority, always trading the first match | C-AI-06 | replaced: every seat may skip; the computer's card timing is its policy ([Cards](#cards)) |
| a fixed discard order on a full hand | C-AI-06 | replaced: the computer chooses its discard by what it keeps ([Discards](#discards)) |
| a different batching threshold for its exchanges | C-AI-06 | dropped: core-rules.md resolves every exchange one at a time for every seat |
| a capture split by fixed branches and drawn gates | C-AI-07 | replaced: a move-in chosen by the threats on the two countries ([Move-in after a capture](#move-in-after-a-capture)) |
| a difficulty level that changes only the human's dealt share | C-AI-08 | replaced: levels change the computer's decisions; the share is a separate setting |
| a stack cap of 999 in its placement | C-AI-01 | dropped: core-rules.md has no stack cap |

## How the computer judges a position

Every phase uses the same few quantities, all computed from the view:

- **Income next turn**: `max(floor(countries / 3), 2)` plus the bonuses of the islands it holds
  completely ([core-rules.md, Reinforcement](core-rules.md#reinforcement)).
- **Island progress**: for each island, how many of its countries the seat holds, how many it lacks,
  the island's bonus, and how many of its entrances (countries bordering another island) an owner
  would have to guard.
- **Exposure**: for each own country, `cap(threat, stack)`, the chance that its strongest enemy
  neighbour could take it in one battle. Exposure on an entrance of a held island puts the island's
  bonus at risk.
- **Card prospects**: the sets its hand makes or nearly makes, and the risk to them
  ([Cards](#cards)).
- **Standing**: every seat's country count, income and hand count, from which the leader check
  reads ([The leader check](#the-leader-check)).

A candidate action is judged by the change it makes to these quantities for the seat, weighed by
named per-level weights (`W_COUNTRY`, `W_BONUS`, `W_EXPOSURE`, `W_CARD`, `W_LEADER` and so on). The
weights are tuning constants, set so that each level meets its targets in
[Measuring strength](#measuring-strength); this file fixes what they weigh, not their values.
Foresight is how far a level chains its judgement inside its own turn
([Difficulty levels](#difficulty-levels)): it looks at the board after its own planned actions,
never at hidden information.

## The computer's turn

The computer follows T50's phases in order: income, cards, placement, attacks, the move, the end.

### Cards

In the cards phase it may trade one set, or skip ([variety.md, Trade-ins](variety.md#trade-ins)).

- **Army sets are traded at once, at every level.** A set of Anchors (5), Compasses (8) or Lanterns
  (15) never grows, so holding it gains nothing and risks the Squall and the hand limit. A seat whose
  hand makes an army set therefore trades a set that turn. Which one, when the hand makes several (they
  may share Wilds, and only one is traded a turn): the army set adding most armies, unless a Surge or
  Raid set is worth more now and its own rule below says to trade it; a Surge set is worth this turn's
  income, a Raid set its expected saving in attacking armies.
- **The Surge set waits for a big turn** *(A7)*. Three Surges add the turn's income once more (country
  part and island bonuses): worth exactly the income `I`, so more as the seat grows. From Normal up the
  computer trades a Surge set when any of these holds, and otherwise keeps it:
  - its income is at least `SURGE_INCOME` (8);
  - its hand holds 4 or more cards, so the next capture would risk a discard or more;
  - the Squall is in the draw pile and the pile holds `SQUALL_PILE` (15) cards or fewer, so each own
    draw has a 1 in 15 or greater chance of emptying the hand ([the model](#a-model-of-the-choices));
  - the doubled pool lets it complete an island or reach domination this turn (foresight).

  At Easy it trades a set in every turn it holds one, the one adding most armies, a Raid set last;
  an Easy raid hits the largest enemy stack adjacent to one of its countries.
- **The Raid set hits what it means to attack, or the leader** *(A10)*. A raid is traded in the cards
  phase, before placement, so its result shapes the rest of the turn. From Normal up the computer
  trades a Raid set when a target gives enough value:
  - an enemy stack it plans to attack this turn, where the expected loss (the stack becomes 1 to half
    of itself) turns a poor battle into a good one: the raid-then-attack combination a player can read;
  - the largest stack of a leader ([The leader check](#the-leader-check)), when it holds at least
    `RAID_MIN_STACK` (8) armies.

  The chance that the target's owner holds a Shield lowers the value. At Hard the computer estimates
  it from public counts ([the model](#a-model-of-the-choices)); below Hard it ignores it. A Raid set
  that finds no target worth it is kept, unless the hand needs the room.
- **Wilds**: at most two per set (the rule); the computer spends Wilds only when the set is traded.

### Placement

The whole pool is placed on the seat's own countries (the rule). Since the board is connected, every
seat that does not hold every country has at least one front country.

- **On front countries only.** An interior stack cannot attack and guards nothing directly, so the
  computer never places there; the end-of-turn move brings interior armies forward instead.
- **Concentrated.** Armies go to at most `MAX_PLACEMENT_STACKS` (3) countries a turn. One battle won
  by a large stack is worth more than three lost by small ones, and few placements are quick to watch.
- **The attack stack first.** It picks the turn's first battle (as in [Attacks](#attacks)) and places
  enough on its source to bring `cap(a, d)` to the level's attack threshold against that target, when
  the pool allows; the rest goes to the next battle of its plan or to defence.
- **Then defence.** An entrance of an island it holds, or a country whose loss would break an island
  bonus or a near-complete island, gets armies until its exposure falls below `DEFEND_RISK` (0.5), if
  the pool allows after the attack stack. When defence and attack compete, the level's weights decide.

### Attacks

- **A candidate battle** is an own country with at least 2 armies and an enemy neighbour. The
  computer values capturing the neighbour by what it adds: a country (income), an island completed
  (its bonus), an enemy bonus broken, a card if this is the turn's first capture, a seat eliminated,
  a centre held (worth something only through the harvest event, and less right after a shift), the
  leader check's weight, and in a round-limit game's last rounds the count for scoring (A11). It
  subtracts the exposure it leaves behind.
- **Starting a battle.** It starts the battle of highest value whose capture chance is at least the
  level's `ATTACK_THRESHOLD`; with none, its attacks are over for the turn.
- **During a battle**, after each exchange, it continues while `cap(current attacker, current
  defender)` is at least `STOP_THRESHOLD`, and stops otherwise. Armies already lost do not count: it
  judges only from the stacks as they stand. At 1 army the battle stops by rule.
- **The turn's card.** A seat draws one card for a turn with a capture. If it has not captured this
  turn and a battle with chance at least `CARD_THRESHOLD` exists, the card is part of that battle's
  value, so a turn rarely ends with no capture when an easy one is on the board.
- **The stop threshold stays below the attack threshold.** `STOP_THRESHOLD` never exceeds the
  current attack threshold minus `STOP_GAP` (0.10), so a battle the computer starts is not abandoned
  after one exchange by a stricter stop rule.
- **No stalling.** When the seat has made no capture in its last `STALL_TURNS` (2) own turns, its
  attack threshold drops by `STALL_STEP` (0.10) each further turn, down to `ATTACK_FLOOR` (0.40),
  and returns to the level's value after a capture. Every level reaches the floor within 5 own turns
  without a capture (Easy: 2 turns, then 0.70 to 0.40 in 3 steps). The floor is below the chance of
  equal stacks of 10 or more, so a border where both sides pile up equally is attacked
  ([No stalling](#no-stalling)).
- **Pace bound** *(A6)*. At most `MAX_BATTLES` (10) battles a turn. The bound is for the player
  watching ([Quick turns](#quick-turns)); it is a limit the computer puts on itself, not a rule.

### Move-in after a capture

The rule lets the attacker move in from 1 to all but one of its remaining armies. The computer
chooses by the threats on the two countries:

- if the source is left with no enemy neighbour, it moves all but one in;
- otherwise it keeps on the source what its exposure needs (up to `DEFEND_RISK`) and moves the rest,
  so the stack that goes on attacking is the larger;
- if the captured country completes an island, its entrances weigh as in placement.

### The move

At most one move, after the attacks, between neighbouring own countries; it ends the turn (the rule).

- The computer moves armies from an interior country to a neighbouring country nearer the front (fewer
  borders from an enemy country), preferring the largest such stack, so armies left behind by captures
  rejoin the fighting.
- If no interior stack can move forward, it may move from a front country with low exposure to a
  neighbouring country whose exposure is above `DEFEND_RISK`, keeping its own exposure below it.
- It moves all but one from an interior source, and only the surplus from a front source.
- No move is made when none improves its position. Any country may be the source, a centre included;
  nothing depends on a fixed list, so the rule works on every generated board.

### Discards

A seat drawing into a full hand discards one of its five first, without seeing the new card
([variety.md, The hand](variety.md#the-hand), V11). The computer discards the card that costs its prospects least:

- it keeps cards of a kind it holds two of, and Wilds, over single cards;
- it keeps a Shield while some opponent could still assemble a Raid set (an opponent holds 3 or more
  cards and not all four Raids have been seen on the discard pile since the last reshuffle, as far as
  its card memory reaches, A12);
- among the rest, it discards a card of the kind with the most copies already seen on the discard
  pile (as far as its card memory reaches), which is the kind least likely to complete.

### The leader check

*(A5.)* A seat is a **leader** when it holds at least `LEADER_COUNT` (28) countries, seven short of
the domination win, or at least `LEADER_RATIO` (1.5) times the countries of the next largest seat and
at least `LEADER_MIN` (22). Each computer seat adds `W_LEADER` (by level) to the value of battles and
raids against a leader. The test reads only counts: a human leader and a computer leader are treated
alike, and a computer seat that is itself the leader plays for the win. The view does not say which
seats are human, so the check cannot single one out.

No seat is a leader at the deal, whatever the human share setting: the largest starting counts, at
+4, are 16 against 10 with four seats, 20 against 13 with three and 27 against 19 with two
([core-rules.md, The deal](core-rules.md#the-deal)). All are below 28; the two that reach 1.5 times the
next seat (16 and 20) are below 22, and 27 is 1.42 times 19. A handicap the player chose is not
treated as a runaway.

### Near the end

- **Domination in reach.** When the seat's foresight shows battles this turn that can reach 35
  countries, it plays for them first.
- **A round-limit game's last rounds** *(A11)*. In the last `SCORE_ROUNDS` (3) rounds of a round-limit
  game, the computer values a country more than armies, since the count decides the result, and moves
  in 1 army after a capture where its exposure allows.

## Difficulty levels

*(A1, A2, A3.)* Three levels, set for each computer seat on the options screen; the default is
Normal for every computer seat. The proposed values:

| What changes | Easy | Normal | Hard |
| --- | --- | --- | --- |
| Foresight | each battle alone | its first battle and the placement that sets it up; island completion and the exposure it leaves | the whole turn: a chain of battles, the raid before them, the move after, and the board it leaves for the next seats |
| Aggression: `ATTACK_THRESHOLD` / `STOP_THRESHOLD` | 0.70 / 0.50 | 0.60 / 0.45 | 0.55 / 0.40, raised where the exposure left behind is high |
| Card timing (A7) | every set at once | army sets at once; the Surge waits; raids on a planned attack or the leader | as Normal, and the Shield chance in raid value |
| Deliberate mistakes (A4) | 25% of decisions | 8% of decisions | none |
| Leader check (A5): `W_LEADER` | none | moderate | strong |
| Card memory (A12) | none: only what is on screen now | the Squall's place (draw pile or discard pile) | every public card since the last reshuffle |

- **A deliberate mistake** replaces the best action by another among the three best whose value is
  within `MISTAKE_MARGIN` of it, drawn from the seat's own stream. A mistake is never an illegal action
  and never a battle below a capture chance of 0.25, so a low level plays loosely, not absurdly.
- **How a player feels the levels.** Easy attacks when clearly favoured, takes the nearest target,
  trades every set as it comes, and leaves island entrances thin: it is beatable by a player who
  holds an island and builds one stack. Normal completes and defends islands, saves the Surge for a
  big turn and raids what it then attacks. Hard plans whole turns, guards entrances with no armies
  wasted, keeps its hand away from the Squall and turns on a runaway seat early.
- **Options row.** core-rules.md's [Options](core-rules.md#options) row "Computer strength" reads
  Easy, Normal or Hard per computer seat, default Normal; the proposed amendment is in A1 and A3.

## Making it fun, argued

Every number in this section is a **model**, not a measurement of the predecessor or of malpaco,
except the counts of the predecessor's computer in the owner's recordings, which are counts cited as
context with their source.

### A model of the choices

Code is shown as an indented block, with its output after it.

    from fractions import Fraction as F
    from functools import lru_cache
    from math import comb, sqrt

    @lru_cache(None)
    def cap(a, d):                      # chance to capture, ties re-rolled (p = 1/2); the attacker keeps 1 army
        if d == 0: return F(1)
        if a == 1: return F(0)
        return (cap(a, d - 1) + cap(a - 1, d)) / 2

    print("smallest attacking stack with a capture chance of at least t, by defender d:")
    for t in (F(1, 2), F(3, 5), F(7, 10), F(4, 5)):
        print(f"  t={float(t):.1f}:", {d: next(a for a in range(2, 200) if cap(a, d) >= t) for d in (1, 2, 3, 5, 8, 12)})

    print("equal stacks, capture chance:", {n: f"{100 * float(cap(n, n)):.1f}%" for n in (2, 4, 6, 10, 20, 40)})

    def turns_to_break(s, income, k, t, limit=60):
        """Attacker and defender start at s on one border. Each turn the attacker adds its whole income
        to the one attacking stack; the defender, with the same income, splits it evenly over the k
        entrances it must cover (rounded down). Turns until cap >= t, or None within the limit."""
        a, d = s, s
        for n in range(1, limit + 1):
            a += income; d += income // k
            if cap(a, d) >= t: return n
        return None
    for t in (F(2, 5), F(1, 2), F(3, 5)):
        print(f"turns to reach t={float(t):.1f} from 3 v 3, income 5, defender covering k entrances:",
              {k: turns_to_break(3, 5, k, t) for k in (1, 2, 3)})

    print("chance the Squall is in this seat's next k draws, Squall in a draw pile of n (k/n):")
    for n in (10, 20, 30):
        print(f"  n={n}:", {k: f"{100 * k / n:.0f}%" for k in (1, 2, 3, 5)})

    def p_shield(u, s, h):              # u unseen cards (not this seat's, not public), s of them Shields, target hand h
        return 1 - comb(u - s, h) / comb(u, h)
    print("chance a target holds a Shield (unseen cards u, unseen Shields s, target hand h):")
    for u, s in ((30, 4), (30, 2), (20, 1)):
        print(f"  u={u}, s={s}:", {h: f"{100 * p_shield(u, s, h):.0f}%" for h in (1, 3, 5)})

    print("95% half-width of a win rate over n games (points):")
    for n in (200, 500, 2000):
        print(f"  n={n}:", {p: round(196 * sqrt(p * (1 - p) / n), 1) for p in (0.25, 0.4, 0.5)})

Its output:

    smallest attacking stack with a capture chance of at least t, by defender d:
      t=0.5: {1: 2, 2: 3, 3: 4, 5: 6, 8: 9, 12: 13}
      t=0.6: {1: 3, 2: 4, 3: 5, 5: 7, 8: 11, 12: 15}
      t=0.7: {1: 3, 2: 5, 3: 6, 5: 8, 8: 12, 12: 16}
      t=0.8: {1: 4, 2: 5, 3: 7, 5: 9, 8: 13, 12: 18}
    equal stacks, capture chance: {2: '25.0%', 4: '34.4%', 6: '37.7%', 10: '40.7%', 20: '43.6%', 40: '45.5%'}
    turns to reach t=0.4 from 3 v 3, income 5, defender covering k entrances: {1: 2, 2: 1, 3: 1}
    turns to reach t=0.5 from 3 v 3, income 5, defender covering k entrances: {1: None, 2: 1, 3: 1}
    turns to reach t=0.6 from 3 v 3, income 5, defender covering k entrances: {1: None, 2: 1, 3: 1}
    chance the Squall is in this seat's next k draws, Squall in a draw pile of n (k/n):
      n=10: {1: '10%', 2: '20%', 3: '30%', 5: '50%'}
      n=20: {1: '5%', 2: '10%', 3: '15%', 5: '25%'}
      n=30: {1: '3%', 2: '7%', 3: '10%', 5: '17%'}
    chance a target holds a Shield (unseen cards u, unseen Shields s, target hand h):
      u=30, s=4: {1: '13%', 3: '36%', 5: '54%'}
      u=30, s=2: {1: '7%', 3: '19%', 5: '31%'}
      u=20, s=1: {1: '5%', 3: '15%', 5: '25%'}
    95% half-width of a win rate over n games (points):
      n=200: {0.25: 6.0, 0.4: 6.8, 0.5: 6.9}
      n=500: {0.25: 3.8, 0.4: 4.3, 0.5: 4.4}
      n=2000: {0.25: 1.9, 0.4: 2.1, 0.5: 2.2}

What the thresholds mean on the board: at Normal's 0.60 the computer attacks a 1-army country with 3,
a 3-army one with 5 and an 8-army one with 11; at Easy's 0.70, with 3, 6 and 12. Every level's own
threshold (0.55 or more) needs a stack larger than its target, so its attacks are readable as "it
waited until it was bigger". Two cases attack at even strength or below, each on purpose: the
anti-stall drop (at its floor of 0.40, equal stacks of 10 or more qualify), and an Easy or Normal deliberate mistake (never
below a chance of 0.25).

### No stalling

- **The danger.** A threshold above one half can stall for ever against a defender who matches it
  army for army on one border: equal stacks never reach an even chance (25.0% at 2, 40.7% at 10,
  45.5% at 40), so in the model's mirrored border, from 3 against 3 with income 5 each, a threshold
  of 0.5 or 0.6 is never met within 60 turns.
- **The answer.** After 2 own turns without a capture the threshold steps down by 0.10 a turn to the
  floor of 0.40, which every level reaches within 5 own turns without a capture. In the same mirrored
  border a threshold of 0.40 is met after 2 turns (13 against 13, an even trade
  of armies on average). A defender covering two or three entrances, as most do on a board with 14 to
  18 crossings, falls below every threshold after 1 turn of the attacker's concentration.
- **What else ends stalls.** Raids and storms cut large stacks to half or less (variety.md), the
  domination win ends a decided game, and the round limit ends any game that has it on. A test fails
  if a game of computers runs past a fixed round cap ([Game length](#game-length)).

### Who it attacks

- **No ganging up on the human.** The view does not say which seats are human, so whatever the
  computers do to a human seat they would do to a computer seat in the same position. A behaviour
  test swaps the human and computer flags of two seats and checks that every computer action is
  unchanged ([Behaviour tests](#behaviour-tests)).
- **A check on any runaway.** A seat at 28 countries is 7 captures from the domination win. At
  core-rules.md's toy pace of about 1 to 1.3 countries a turn (a model with invented averages), that
  is about 6 to 7 of its own turns if nobody takes any back: time for the others to answer, which the
  leader weight makes them do. A seat with 1.5 times the next seat's count is the same signal earlier
  in a game. Each computer seat decides alone, so the check is several seats seeing the same board,
  not an alliance.
- **No mercy, no spite.** The computer does not spare a weak seat or punish the human for an earlier
  attack: it remembers battles only as public history, and nothing in its value counts who attacked
  whom.

### Swingy cards, played readably

- **Army sets at once.** A computer holding an army set trades a set that turn, every time, at every
  level: the sets never grow, so waiting would only risk the hand.
- **The Surge waits, and you can see why.** Three Surges add the turn's income: about 4 early, 8 or
  more for a seat with 24 countries, or fewer countries with island bonuses. Normal and Hard keep the set until income
  reaches 8, the hand fills, or the Squall is close: with the Squall in a draw pile of 15 cards, each
  own draw empties the hand with chance 1 in 15, and holding through three own draws from a pile of 20
  risks 15% (the model's k/n, while that pile lasts: no seat knows the pile's order, so each draw from
  it is the Squall with chance 1 in its size). A player who sees a computer with 4 cards and no trade can expect a big
  turn soon.
- **The raid shows its purpose.** A computer raids a stack it then attacks, or the leader's largest
  stack. A raid on an adjacent 20-army stack removes 14.5 armies on average (variety.md's model), and
  with ties re-rolled each defending army costs about one attacking army, so it saves about 14.5
  attacking armies when it lands; if the target holds a Shield with the model's chance of 36% (3
  cards, 4 Shields among 30 unseen cards), the expected saving is about 0.64 × 14.5, about 9.
- **The Squall is a risk it manages, not a card it plays.** The Squall is never held, and its place
  is public: on the discard pile it cannot be drawn until the next reshuffle; in the draw pile each
  draw finds it with chance 1 in the pile's size. Normal and Hard read that place and trade sooner when
  it is close, which a watching player can follow.

### Quick turns

A requirement for T52's presentation and for the computer itself. A computer turn holds at most:

| Action | At most |
| --- | --- |
| a trade-in (with a raid target if a Raid set) | 1 |
| placements (countries that receive armies) | 3 |
| battles, each with its move-in after a capture | 10 |
| the move | 1 |
| a discard before the end-of-turn draw | 1 |

- The predecessor's computer, in the owner's four recorded games, made 235 attacks in 131 turns
  (about 1.8 a turn), at most 8 in a turn, and none in 16 turns (counts from `runs/E018`). A bound
  of 10 is above every turn recorded there. malpaco's computer may want more battles than the
  predecessor's, which drew its rounds; a turn that reaches the bound stops attacking and moves.
- The exchanges inside a battle are not bounded by the policy; T52 shows them at its chosen pace.
- Each decision takes a bounded time: the engine's tests fix a time budget per decision and fail if
  a decision over many seeds exceeds it.

## Measuring strength

C-AI-09 holds for the predecessor: how well its computer played is not established, and nothing
here depends on it. malpaco measures its own computer in its own tests. These are requirements for
the implementation; their results come from malpaco, not from this file.

### The baseline

A **scripted seat**, simple and fixed, is the yardstick:

- it trades the set it holds that adds most armies, counting a Surge set as the turn's income, else a
  Raid set on the largest enemy stack adjacent to it;
- it places the whole pool on its front country with the largest stack (the first in board order on a
  tie);
- it attacks from its largest front stack the adjacent enemy country with the smallest stack, while
  its stack exceeds the defender's by at least 2, and continues each battle while its stack exceeds
  the defender's;
- it moves in all but one after a capture, makes no move, and discards the card it has held longest.

It draws on no random stream, so its games differ only through the game seed.

### Matchups

- **A level against the baseline**: one seat of the level and three scripted seats, 4 seats.
- **Levels against each other**: one seat of a level and three of the level below; and two-seat
  duels of each level against the level below.
- Every seed is played once per seat rotation, so each seat plays from every place in the turn order.
  Settings: domination on, no round limit, events Normal, human share 0, 46-country generated boards.
- **Sample sizes**: 2000 games per matchup for the release suite, giving a 95% interval of at most
  about ±2.2 points; 200 games in CI as a smoke test (about ±7 points), with targets loosened by that
  margin.

### Targets

*(A9.)* In a 4-seat game an even chance is 25%. The proposed targets:

| Matchup | Target |
| --- | --- |
| Easy against 3 scripted seats | 30% to 50% |
| Normal against 3 scripted seats | at least 55% |
| Hard against 3 scripted seats | at least 70% |
| Normal against 3 Easy | at least 40% |
| Hard against 3 Normal | at least 35% |
| two-seat duel, each level against the level below | at least 60% |

- The order Easy, Normal, Hard holds in every matchup, with 95% intervals that do not overlap in the
  release suite. Two levels that do not separate are one level, and the level table is retuned.
- Against a human the strength cannot be tested automatically. The owner's play-tests answer whether
  Easy is beatable on a first game and whether Hard stays a contest for a practised player.

### Game length

- In 4-seat games of Normal computers, the median game length is reported in rounds, with a target
  band of 15 to 30 rounds, to be revisited after the first play-tests (core-rules.md's toy model
  suggests a few dozen rounds; the owner's four recorded games of the predecessor ran 29 to 55
  player-turns, counts from `runs/E018`).
- At most 2% of those games last beyond 60 rounds with domination on and no round limit.
- Any game of computers that reaches 150 rounds fails the test: it is a stall the policy must not
  allow.
- Turn length: the largest number of actions in a computer turn stays within the bound of
  [Quick turns](#quick-turns), and the mean is reported.

### Behaviour tests

- **Legality**: over many seeds, every computer action is accepted by the engine.
- **Hidden information**: changing another seat's hand kinds, the draw pile's order, or the game
  stream's state leaves the computer's next action unchanged, given the same view and its own stream.
- **Seat kinds**: swapping the human and computer flags of two seats leaves every computer action
  unchanged.
- **Streams**: changing a computer seat's level, or its stream's seed, leaves the game stream's
  sequence of values unchanged; re-running a turn from the same state gives the same actions; a saved
  game replays identically.
- **Readable rules**: a seat holding an army set trades a set that turn, at every level; no placement
  on an interior country; at most 3 placements, 10 battles and 1 move a turn.

## Choices for the owner

Each entry names what it decides, the options, a recommendation and its reason. No row of the
decision table is `open`; these are the feel-changing calls inside the rows' new rules.

1. **A1. The levels** (C-AI-08).
   - (a) three levels, Easy, Normal and Hard, as in [Difficulty levels](#difficulty-levels); (b) four,
     adding an Expert level with no mistakes, full card memory and the strongest leader check; (c) a
     strength slider from 1 to 10 that moves every constant continuously.
   - Recommendation (a): three levels can each be made distinct and tested to separate (A9); a fourth
     is easy to add once three are tuned, and a slider would have neighbouring values a player cannot
     tell apart.
   - **Proposed amendments to core-rules.md**: the [Options](core-rules.md#options) row "Computer
     strength" reads the chosen levels, per computer seat (A3), default as A2; the record in
     [Stored files](core-rules.md#stored-files) is kept per seat count, human share and computer
     strength.
2. **A2. The default level** (C-AI-08).
   - (a) Easy; (b) Normal; (c) Hard.
   - Recommendation (b): Normal is the game the balance is tuned on; a new player can step down to
     Easy, and the human share setting gives a further handicap.
3. **A3. One strength for all, or per seat** (C-AI-08).
   - (a) one setting for every computer seat; (b) a setting per computer seat, default Normal for all.
   - Recommendation (b): the options screen already sets each seat human or computer, so a level beside
     each is one control more, and mixed tables (two Easy, one Hard) are variety for free.
4. **A4. Deliberate mistakes** (C-AI-08).
   - (a) none: levels differ only in foresight, aggression, card timing and the leader check; (b)
     Easy 25% and Normal 8% of decisions, among the three best actions, Hard none; (c) as (b), and
     Hard 3%.
   - Recommendation (b): small, plausible mistakes make a low level feel human rather than broken, and
     a top level without them gives a practised player a fixed target.
5. **A5. The leader check** (C-AI-03, C-AI-04).
   - (a) none: each computer plays only for its own gain; (b) a seat-blind leader weight, from 28
     countries or 1.5 times the next seat, scaled by level (none at Easy); (c) as (b), only within 4
     countries of a win (31 or more), where events already stop.
   - Recommendation (b): a runaway is answered while it can still be stopped, and because the view
     carries no seat kinds the check cannot single out the human. (c) acts when the game is nearly
     decided.
6. **A6. Battles per turn** (C-AI-03).
   - (a) no bound; (b) at most 10; (c) at most 6.
   - Recommendation (b): above every turn recorded of the predecessor's computer (at most 8), and it
     keeps a turn watchable; how often malpaco's computer reaches it is for the tests to report. (c)
     would cut chains of captures more often.
7. **A7. Card timing** (C-AI-06).
   - (a) a set traded in every turn the hand makes one, at every level; (b) army sets at once at every
     level; the Surge waits for a big turn and the Raid set for a target at Normal and Hard; Easy
     trades all at once; (c) as (b), and Hard also holds a Raid set for a turn when the leader is
     close to a win.
   - Recommendation (b): the timing a player can read (army sets now, Surge later, raid before an
     attack) and a clear difference between levels. (c) adds a rule few players would notice.
8. **A8. The computer's random streams** (C-AI-02, C-AI-03).
   - (a) a stream per computer seat, seeded from the game seed and the seat number; (b) one stream for
     all computer seats, seeded from the game seed.
   - Recommendation (a): changing one seat's level or policy then leaves every other seat's random
     choices as they were, which keeps the strength tests' comparisons clean. Both keep the game stream
     (dice, cards, events) apart from the computer's choices, as [Randomness](#randomness) requires.
   - **Proposed amendment to core-rules.md**: in [Randomness](core-rules.md#randomness), the first
     item's list drops "the computer's random choices", and a new item reads: "Each computer seat's own
     random choices come from a separate stream seeded from the game seed and the seat number
     (computer.md, A8); the game stream never serves them. The computer's actions are recorded in the
     action list like a human's."
9. **A9. Strength targets** (C-AI-09).
   - (a) the targets in [Targets](#targets): Normal at least 55% and Hard at least 70% against three
     scripted seats, Hard at least 35% against three Normal; (b) a steeper ladder: 65%, 80% and 45%;
     (c) a gentler one: 45%, 60% and 30%.
   - Recommendation (a): each level clearly better than the one below without Hard becoming a wall; the
     steeper ladder may need foresight the time budget does not allow, and the gentler one may leave
     levels a player cannot tell apart.
10. **A10. Raid targets** (C-AI-06).
    - (a) only a stack the computer attacks this turn; (b) that, or the largest stack of a leader (A5)
      of at least 8 armies; (c) the largest enemy stack anywhere.
    - Recommendation (b): the combination is readable, and the leader target is the raid's comeback
      use; (c) spends raids on stacks that matter little to the raider and hits whoever is biggest,
      even far away.
11. **A11. Playing for the score** (C-AI-03).
    - (a) no change near the end of a round-limit game; (b) in the last 3 rounds, value countries over
      armies.
    - Recommendation (b): the round limit counts countries, so a computer that ignores it would throw
      games a human can see are winnable.
12. **A12. Card memory** (C-AI-06).
    - (a) every level remembers every public card since the last reshuffle; (b) Easy none, Normal the
      Squall's place only, Hard every public card; (c) no level remembers more than the screen shows
      now.
    - Recommendation (b): what a human can see and remember is fair at every level, and how much is
      remembered is a natural difference between levels; (c) would make Hard forget what any careful
      player tracks.

The three proposed amendments to core-rules.md (A1's options row and record, A3's per-seat setting
in the same row, and A8's randomness item) are for the main session to apply on `main` once the owner
decides.

## Decisions, claim by claim

One row per in-scope spec claim (9). `keep` serves fun or balance as it is; `change` alters it;
`replace` swaps in a different rule; `drop` removes it; `open` would wait for the owner (no row is
`open`: the owner's calls are the choices above, inside each row's new rule). A claim that is not
`supported` or `corroborated` still gets a row; its decision is a design choice and the row says so.

| Claim | Decision | malpaco's rule | Why |
| --- | --- | --- | --- |
| C-AI-01 | replace | [Placement](#placement): the whole pool on at most 3 front countries, the attack stack first, then the entrances of held islands; no ranks, no fixed scores, no drawn splits, no cap | Ranks and drawn splits spread armies by formula; placing for the turn's plan concentrates force and defends bonuses in a way a player can read. The trade-in's armies join the pool by the shared rule (variety.md). |
| C-AI-02 | replace | [Placement](#placement), [Attacks](#attacks): no one-army seeds and no weighted uniform pick; the computer picks the battle worth most, with ties and planned mistakes from its own stream (A8) | Seeds and weighted draws made the computer's play a lottery over a fixed rank table; a value-based pick on the generated board makes it purposeful, and its own stream keeps the dice apart. |
| C-AI-03 | drop | [Attacks](#attacks): no drawn attack rounds, no skip draw, no extra rounds once the humans are out; the computer attacks while a battle meets its threshold, up to 10 battles (A6) | Drawn pacing made the computer attack or stop by lot, and the extra rounds served only a game the humans had left; T50 ends that game, and a threshold with an anti-stall floor keeps the computer from stalling. |
| C-AI-04 | replace | [Attacks](#attacks): T50's one rule (2 armies, no comparison); the computer's caution is a capture-chance threshold by level, a stop threshold inside the battle, and the leader check (A5) | Drawn floors and margins were rules only the computer followed and the player could not see; a threshold on the exact capture chance gives the same caution as a decision, readable as "it waits until it is bigger". |
| C-AI-05 | replace | [The move](#the-move): one move, interior armies forward or surplus to a threatened neighbour, all but one from an interior source; any country may be the source | A table over fixed countries cannot work on a generated board, and the centre veto and corridor walks were tied to one map; a move chosen by purpose works on every board. |
| C-AI-06 | change | [Cards](#cards), [Discards](#discards): kept, the shared income, dice and card rules; changed, army sets traded at once, the Surge held for a big turn, raids on a planned attack or the leader, discards by prospects (A7, A10, A12) | Kept: the computer earns and trades cards exactly as a human. Changed: the fixed trade and discard orders and the separate batching threshold go; every seat may skip a trade, and the computer's timing is its policy. |
| C-AI-07 | replace | [Move-in after a capture](#move-in-after-a-capture): all but one when the source is left interior, else what the source's exposure needs stays and the rest moves in | Fixed branches with drawn gates were a hidden recipe; reading the threats on both countries is the same decision a careful human makes. |
| C-AI-08 | replace | [Difficulty levels](#difficulty-levels): Easy, Normal and Hard change foresight, aggression, card timing, mistakes, the leader check and card memory; the human share is a separate option (A1 to A4) | A level that changed only the human's dealt share hid the handicap and left the computer the same; malpaco's levels make the computer play differently, and core-rules.md's decision 6 already made the share a setting of its own. |
| C-AI-09 | keep | [Measuring strength](#measuring-strength): nothing about the predecessor's playing strength is carried; malpaco measures its own computer against a scripted baseline and between levels, over many seeds (A9) | The claim is `unknown`, so this row is a design choice: a design does not rest on how well the predecessor played. Keeping it unknown, and testing malpaco's own levels, is the honest course. |
