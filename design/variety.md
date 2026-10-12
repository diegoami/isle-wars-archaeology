# malpaco variety

The parts of malpaco that make one game differ from the last: cards, island bonuses, production
centres and events. They are written so that a TypeScript implementer can build them without reading
`spec/`. They build on [core-rules.md](core-rules.md) (T50): a board generated from the seed, one
attack rule for every seat, ties re-rolled, domination at three quarters, one seeded random stream.
The computer opponent's choices (which set to trade, whom to raid, what to discard) are T53's (#196);
the UI of cards, the hand and events is T52's. This file states only the rules that bind every seat.

The starting point is the predecessor's rules as read from its code (the in-scope `spec/` files:
cards, island bonuses, production centres and hazards, 23 claims). The
[decision table](#decisions-claim-by-claim) gives one row per claim. The direction is the owner's
(2026-10-11): cards add some unbalance and surprise, and no game is decided by luck alone.

**What is proposed and what is decided.** The rules below are the recommended options. Every rule that
changes the feel of play, and every `open` row, is listed in [Choices for the owner](#choices-for-the-owner)
with its options, and is marked *(choice Vn)* where it appears. None of them is decided until the owner
decides it. Where a choice would amend [core-rules.md](core-rules.md), the amendment is stated in that
choice; this file does not change the core rules. Build each value behind a named constant.

## Terms

Terms of [core-rules.md](core-rules.md) (seat, country, island, border, stack, turn, round) hold here.

- **Card**: a card in a seat's hand. A seat's **hand** holds at most five.
- **Set**: three cards traded together for armies.
- **Card action**: a trade-in or a raid, at most one per turn.
- **Centre**: a production centre, a country that pays its owner an extra army each turn.
- **Event**: a random happening between turns that changes armies or owners on the board.
- **Turn change**: the moment after one seat's turn (after its victory check) and before the next
  seat's income.

## Cards

### The kinds

malpaco has six kinds of card, with names of its own:

| Kind | Copies | What it does |
| --- | --- | --- |
| Anchor | 11 | army card: three Anchors are a set worth 4 |
| Compass | 10 | army card: three Compasses are a set worth 6 |
| Lantern | 8 | army card: three Lanterns are a set worth 8 |
| Wild | 4 | stands for any army card in a set, at most one per set |
| Raid | 4 | played as the card action: an enemy stack loses up to half its armies ([The raid](#the-raid-and-the-shield)) |
| Shield | 3 | held: cancels the next raid against its holder, then is discarded |

40 cards in all *(choices V1 to V5)*. There is no card that doubles the pool *(choice V3)*, and no card
that empties its drawer's hand *(choice V4)*.

### The deck

- At game start, the 40 cards are shuffled (from the game's seeded stream, after the deal and the
  centres) into a face-down **draw pile**. Every hand starts empty.
- A drawn card leaves the pile. Traded, played and discarded cards go to a face-up **discard pile**.
- When the draw pile is empty and a card must be drawn, the discard pile is shuffled (from the same
  stream) into a new draw pile. Cards in hands stay in hands.
- The draw pile and the discard pile can never both be empty when a card is due: at most 4 × 5 = 20
  cards are in hands, and the deck has 40.
- The number of cards in each hand and in each pile is public. The kinds in a hand are seen only by
  that hand's seat; no seat, human or computer, reads another seat's hidden cards
  ([Fairness](#fairness-between-seats)).

### Earning a card

- A seat that captured at least one country during its turn draws **one** card at the end of that turn
  (the end-of-turn effect of [core-rules.md, The turn](core-rules.md#the-turn)), before the victory
  check. One card, however many countries it captured.
- Nothing cancels the draw: a failed attack later in the same turn does not.
- A seat earns cards in no other way: no card at game start, none for an island, none from an event.

### The hand

- A hand holds at most **five** cards.
- A seat that draws while holding five looks at the drawn card, then discards one of its six cards,
  any one, its own choice. Every seat follows this rule; which card the computer discards is its
  policy (T53).

### Trade-ins

- **When.** In the cards phase of its turn (after income, before placement), a seat may make **one
  card action**: trade one set, or play one Raid, or neither. It is never forced.
- **What a set is.** Three cards that are either
  - three of the same army kind (Anchor, Compass or Lantern), or
  - one of each army kind,
  where at most one of the three may be a Wild, standing for the missing card. Raids and Shields are
  never part of a set. Two or three Wilds are never a set.
- **What a set gives**, added to this turn's pool *(choice V2)*:

  | Set | Armies |
  | --- | --- |
  | three Anchors | 4 |
  | three Compasses | 6 |
  | three Lanterns | 8 |
  | one of each | 6 |

  The value is fixed for the whole game; it does not grow with the number of sets traded *(choice V2)*.
- The traded cards go to the discard pile. The armies are placed this turn like the rest of the pool
  ([core-rules.md, Reinforcement](core-rules.md#reinforcement)).
- Every seat trades under this rule, including the computer: it may skip a trade, and it may use at
  most one Wild. Which set it trades, and when, is its policy (T53).

### The raid and the shield

- **The raid** *(choice V5)*. Playing a Raid is the turn's card action. The seat chooses an enemy
  country that borders one of its own and holds at least 2 armies. That stack loses half its armies,
  rounded down, **at most 10**: 2 → 1, 5 → 3, 9 → 5, 20 → 10, 40 → 30. Ownership does not change, no
  stack drops below 1, and the raiding seat's pool is unchanged.
- **The shield.** If the target country's owner holds a Shield, the Shield is discarded and the raid
  has no effect. This happens automatically: holding a Shield is the choice. The Raid is discarded
  either way, and nothing else in either hand changes.
- Every seat raids under the same rule. Whom the computer raids is its policy (T53).
- **Counter-play.** A raid needs a border, so a seat sees which of its stacks can be raided. Hand
  counts are public, so a seat can see who might hold one. The cap of 10 means splitting armies does
  not help against a raid on a big stack; holding a Shield, or keeping the main stack away from a
  border with a seat that may hold a raid, does. A raid takes the place of a trade-in that turn.

### An eliminated seat's cards

A seat that loses its last country puts its hand on the discard pile *(choice V6)*. Nobody takes it.
(This settles what [core-rules.md, Ownership change](core-rules.md#ownership-change) left to T51.)

## Island bonuses

The rule is the owner's decision 12 in [core-rules.md, Island bonuses](core-rules.md#island-bonuses),
unchanged here: an island held completely pays `floor(size / 2) + entrances`, at least 2, and the
generator's fairness checks reject a board with an island whose bonus exceeds its size *(choice V10
proposes only whether to tune it)*.

- A bonus needs every country of the island; partial control pays nothing. Several islands held add
  up, with no extra for a set of islands and no reduction.
- The bonus enters the pool at income ([core-rules.md, Reinforcement](core-rules.md#reinforcement)).
- An event or a raid that changes no owner leaves bonuses as they are; a revolt
  ([Events](#events)) can break or complete one.
- Bonuses are the board's: no card or event changes a bonus value during a game.

How bonuses compare on a generated board is in
[Island bonuses on a generated board](#island-bonuses-on-a-generated-board).

## Production centres

*(choice V7: whether malpaco has centres at all, and in which form.)* The recommended form:

- **How many and where.** One centre per seat (2 to 4). After the deal ([core-rules.md, The deal](core-rules.md#the-deal),
  step 5), each seat's centre is drawn from the game stream among that seat's own countries, so every
  seat starts with exactly one. No two centres are on the same island, and no two are neighbours. The
  placement satisfies these from the seed; the engine's tests show that every generated board and deal
  admits a valid placement within a stated number of draws, and define what happens when draws run
  out (for example, relaxing the island condition before the neighbour one), never a hang.
- **What a centre gives.** Its owner adds **1 army** to its pool at income for each centre it holds.
  (This needs a proposed amendment to core-rules.md's pool formula, stated in choice V7.)
- **What a centre costs.** Nothing to build: a centre is a country worth holding and worth taking.
  It is marked on the board for every seat.
- **Ownership.** A centre belongs to whoever owns its country. Capturing the country takes the
  centre; it never moves and is never destroyed.
- **The harvest.** The harvest event ([Events](#events)) adds **3 armies** to each centre's stack,
  whoever owns it. There is no doubling and so no cap is needed: a stack can hold any number of
  armies (core rules), and the harvest adds a fixed amount.

## Events

### When an event is drawn

- An event may happen at a turn change. At each eligible turn change, one draw from the game stream
  decides whether an event happens, with the chance set by the **event frequency** option
  *(choice V9)*:

  | Option | Chance per eligible turn change |
  | --- | --- |
  | Off | none |
  | Rare | 1 in 32 |
  | Normal (default) | 1 in 16 |
  | Often | 1 in 8 |

- A turn change is **not eligible** in round 1, while any seat is within 4 countries of winning
  ([core-rules.md, Victory](core-rules.md#victory)), after the game has ended, or right after a turn
  change that had an event (so two events never come back to back).
- The check is the same at every turn change, whoever has played and whoever plays next. No route
  skips it for one kind of seat.
- When an event happens, its kind is drawn by weight *(choice V8)*: Storm 2, Revolt 1, Harvest 2
  (Harvest only when the game has centres). A draw of the same kind as the previous event is drawn
  again once, so repeats are rarer without being impossible.

### The kinds of event

*(choice V8 for the kinds and their sizes.)*

- **Storm.** One country is drawn uniformly from all countries; the storm strikes it and up to two of
  its neighbours on the same island, drawn at random. Each struck stack loses half its armies,
  rounded down, **at most 5** (so a 1-army stack loses nothing, 4 → 2, 10 → 5, 30 → 25). Owners do not
  change.
- **Revolt.** One country is drawn uniformly among those that hold 1 to 3 armies, border a country
  of another seat, and whose owner holds at least 3 countries. It passes to one of the other seats it
  borders (drawn uniformly), with its armies unchanged. When no country qualifies, nothing happens.
- **Harvest** (only with centres). Each centre's stack gains 3 armies.

### What no event does

- No event leaves a stack at 0, eliminates a seat, removes or moves a centre, or changes an island's
  bonus value.
- No event chooses a seat, by rank, by count or by being human or computer: storms and revolts draw
  countries, and every country is equally likely to be the storm's centre. A seat with more countries
  is struck more often only because it has more countries.
- No event can end a game: events stop within 4 countries of a win, and a revolt moves one country.

## Fairness between seats

Every card, bonus, centre and event rule above applies alike to human and computer seats. The
computer differs only in what it chooses (T53), never in what it may do or what it knows. Each of the
predecessor's asymmetries in these areas is dropped:

| The predecessor's asymmetry | Row | malpaco |
| --- | --- | --- |
| the computer trades automatically by a fixed priority and never skips | C-CRD-05 | every seat may trade or skip; the computer's choice is its policy (T53) |
| the computer's removal step can spend more than two wildcards on one set | C-CRD-05 | at most one Wild per set, for every seat |
| the computer discards by a fixed priority on a full hand; the human clicks one away | C-CRD-04 | every seat chooses one of six cards to discard |
| a failed human attack cancels the turn's card draw | C-CRD-03 | nothing cancels a seat's draw |
| the computer's bomb target is chosen through a mis-indexed comparison | C-CRD-06 | one targeting rule (an enemy neighbour with 2 or more armies) for every seat |
| the human's protected branch reorders the bomber's own hand and can clear its cards | C-CRD-07 | a cancelled raid discards the Raid and the Shield and touches nothing else |
| the between-turn routes can pre-empt an event draw depending on human-seat conditions | C-HAZ-02 | one eligibility rule at every turn change |
| only the computer's handlers read the centre list | C-CEN-05 | centres are marked and pay the same for every seat; how the computer values them is T53's |

## Surprise and balance, argued

Every number in this section is a **model**, not a measurement of the predecessor or of malpaco. The
models assume a 4-seat game of 20 or 30 rounds (core-rules.md's toy model says a few dozen rounds; the
owner's recorded games of the predecessor, which ended at its concession, ran 29 to 55 turns, 7 to 14
rounds, in `runs/E018`), a capture in 75% of a seat's turns (an assumption), and a seat that trades
its best set whenever it holds one, else raids if it can (a neutral stand-in, not T53's policy).

### The deck in a game

```python
import random
from collections import Counter
DECK = {"anchor": 11, "compass": 10, "lantern": 8, "wild": 4, "raid": 4, "shield": 3}
SET_VALUE = {"anchor": 4, "compass": 6, "lantern": 8, "mixed": 6}
ARMY = ("anchor", "compass", "lantern")
LIMIT = 5

def best_set(hand):
    """Best set in hand: three alike or one of each army kind, at most one wild. -> (value, cards)."""
    c = Counter(hand); w = c["wild"] >= 1
    opts = []
    for k in ARMY:
        if c[k] >= 3: opts.append((SET_VALUE[k], [k] * 3))
        elif c[k] == 2 and w: opts.append((SET_VALUE[k], [k, k, "wild"]))
    have = [k for k in ARMY if c[k] >= 1]
    if len(have) == 3: opts.append((SET_VALUE["mixed"], list(ARMY)))
    elif len(have) == 2 and w: opts.append((SET_VALUE["mixed"], have + ["wild"]))
    return max(opts) if opts else None

def game(rng, seats=4, rounds=20, p_capture=0.75):
    pile = [k for k, n in DECK.items() for _ in range(n)]; rng.shuffle(pile); discard = []
    hands = [[] for _ in range(seats)]
    trades = []; draws = Counter(); raids = 0; full = 0; reshuffles = 0
    for r in range(1, rounds + 1):
        for s in range(seats):
            h = hands[s]
            b = best_set(h)
            if b:                                   # one card action: the best set, else a raid
                for card in b[1]: h.remove(card)
                discard += b[1]; trades.append((r, b[0]))
            elif "raid" in h:
                h.remove("raid"); discard.append("raid"); raids += 1
            if rng.random() < p_capture:            # one draw per capturing turn
                if not pile:
                    pile, discard = discard, []; rng.shuffle(pile); reshuffles += 1
                card = pile.pop(); draws[card] += 1
                if len(h) == LIMIT:                 # discard one: the model drops a shield, else the first card
                    full += 1; drop = "shield" if "shield" in h else h[0]
                    h.remove(drop); discard.append(drop)
                h.append(card)
    return trades, draws, raids, full, reshuffles

def report(rounds, N=20000, seats=4):
  rng = random.Random(51)
  T = []; D = Counter(); S = F = R = 0
  for _ in range(N):
    t, d, s, f, r = game(rng, rounds=rounds); T += t; D += d; S += s; F += f; R += r
  print(f"--- {rounds} rounds, 4 seats, a capture in 75% of turns")
  print("draws per game:", round(sum(D.values()) / N, 1))
  print("draws per game by kind:", {k: round(D[k] / N, 1) for k in DECK})
  print("reshuffles per game:", round(R / N, 2))
  print("trade-ins per seat per game:", round(len(T) / N / seats, 2))
  print("mean trade-in value:", round(sum(v for _, v in T) / len(T), 2))
  print("trade-in values:", {v: round(100 * c / len(T), 1) for v, c in sorted(Counter(v for _, v in T).items())}, "% of trade-ins")
  print("raids played per seat per game:", round(S / N / seats, 2))
  print("draws into a full hand per seat per game:", round(F / N / seats, 2))
  for lo, hi in ((1, 5), (6, 12), (13, rounds)):
      n = sum(1 for r, _ in T if lo <= r <= hi); v = sum(v for r, v in T if lo <= r <= hi)
      turns = N * seats * (hi - lo + 1)
      print(f"rounds {lo}-{hi}: card armies per seat-turn {v / turns:.2f}, trade-in in {100 * n / turns:.0f}% of turns")

for rounds in (20, 30):
    report(rounds)
```

Its output:

```text
--- 20 rounds, 4 seats, a capture in 75% of turns
draws per game: 60.0
draws per game by kind: {'anchor': 16.5, 'compass': 15.1, 'lantern': 12.1, 'wild': 6.3, 'raid': 6.6, 'shield': 3.4}
reshuffles per game: 1.02
trade-ins per seat per game: 3.41
mean trade-in value: 5.85
trade-in values: {4: 16.9, 6: 73.7, 8: 9.4} % of trade-ins
raids played per seat per game: 1.56
draws into a full hand per seat per game: 0.32
rounds 1-5: card armies per seat-turn 0.37, trade-in in 6% of turns
rounds 6-12: card armies per seat-turn 1.18, trade-in in 20% of turns
rounds 13-20: card armies per seat-turn 1.23, trade-in in 21% of turns
--- 30 rounds, 4 seats, a capture in 75% of turns
draws per game: 90.0
draws per game by kind: {'anchor': 24.8, 'compass': 22.7, 'lantern': 18.2, 'wild': 9.7, 'raid': 10.5, 'shield': 4.3}
reshuffles per game: 2.07
trade-ins per seat per game: 5.52
mean trade-in value: 5.85
trade-in values: {4: 17.1, 6: 73.3, 8: 9.6} % of trade-ins
raids played per seat per game: 2.52
draws into a full hand per seat per game: 0.53
rounds 1-5: card armies per seat-turn 0.37, trade-in in 6% of turns
rounds 6-12: card armies per seat-turn 1.18, trade-in in 20% of turns
rounds 13-30: card armies per seat-turn 1.23, trade-in in 21% of turns
```

What it says:

- A 20-round game draws about 60 cards, so the deck goes round about once and every kind turns up:
  about 6 Raids, 3 Shields and 6 Wilds per game across the four seats. Each seat sees about 15 cards.
- A seat trades about once every five or six turns once its hand has filled (20% of turns from round
  6), 3 to 6 times a game. Most sets are one of each (about three in four), so a trade-in is usually 6;
  saving for three Lanterns (8) is a gamble against a smaller sure set.
- Cards add about 1.2 armies per turn on average after round 5: a steady extra of a tenth to a fifth
  of mid-game income, delivered in lumps.
- A draw into a full hand is rare (one every two or three games per seat), because three army kinds
  in a hand of five almost always make a set; the discard rule matters mainly for a seat that hoards.
- Every game has a new order (the deck is shuffled from the seed); the predecessor's list was fixed and
  never shuffled, so its draws were independent and the same kind could come round any number of
  times (C-CRD-02). A finite deck limits streaks: there are only 4 Raids in a pass.

### Trade-ins against income

```python
SET = 6                                    # the usual set (one of each kind)
INCOME = {"early (rounds 1-5)": (3, 5), "mid (rounds 6-12)": (6, 12),
          "late, leader": (15, 25), "late, trailing seat": (3, 6)}
for stage, (lo, hi) in INCOME.items():
    print(f"{stage:22} income {lo:2}-{hi:2}: a set of {SET} is {SET / hi:.2f}-{SET / lo:.2f} turns of income;"
          f" a set of 8 is {8 / hi:.2f}-{8 / lo:.2f}")

def escalating(n):                         # the classic sequence: 4, 6, 8, 10, 12, 15, then +5 each
    seq = [4, 6, 8, 10, 12, 15]
    return seq[n] if n < len(seq) else 15 + 5 * (n - len(seq) + 1)
trades = 14                                # about 3.4 trade-ins per seat x 4 seats in a 20-round game
print("escalating, the game's trade-ins:", [escalating(i) for i in range(trades)])
```

```text
early (rounds 1-5)     income  3- 5: a set of 6 is 1.20-2.00 turns of income; a set of 8 is 1.60-2.67
mid (rounds 6-12)      income  6-12: a set of 6 is 0.50-1.00 turns of income; a set of 8 is 0.67-1.33
late, leader           income 15-25: a set of 6 is 0.24-0.40 turns of income; a set of 8 is 0.32-0.53
late, trailing seat    income  3- 6: a set of 6 is 1.00-2.00 turns of income; a set of 8 is 1.33-2.67
escalating, the game's trade-ins: [4, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 55]
```

The income bands are invented from core-rules.md's income table plus a few bonus armies; they are a
model.

- **A swing, not a decider.** A set is worth one to two turns of income early (when few seats have
  one: a trade-in in 6% of turns before round 6), about one turn mid-game, and a third of a turn for a
  late leader. After the opening, a set is worth at most about one turn's income (1.33 turns at worst:
  a set of 8 against an income of 6).
- **Why the value does not grow.** With escalating sets, the game's later trade-ins are worth 30 to 55
  armies, two or three times even a leader's income, so the game is decided by who holds a set when
  the counter is high. That is a game decided by the deck, which the owner's direction rules out.
  Fixed values keep a set's worth tied to its cards (choice V2).
- **Why sets are small.** The predecessor's largest set added 15 armies, three to five turns of
  early income, and a doubling set added the whole pool (C-CRD-05). malpaco's largest set is 8.

### The raid and the shield

```python
def raid(stack): return max(stack - min(stack // 2, 10), 1), min(stack // 2, 10)
print("raid (left, lost):", {s: raid(s) for s in (2, 3, 4, 6, 9, 15, 20, 40)})
```

```text
raid (left, lost): {2: (1, 1), 3: (2, 1), 4: (2, 2), 6: (3, 3), 9: (5, 4), 15: (8, 7), 20: (10, 10), 40: (30, 10)}
```

- With ties re-rolled, a defending army costs one attacking army on average
  ([core-rules.md, Combat odds](core-rules.md#combat-odds)), so a raid that removes k armies is worth
  about k attacking armies at that border, at most 10: about one mid-game turn's income, spent on one
  stack. It opens a hole for the attack that follows in the same turn, which is its point.
- The predecessor's bomb replaced the stack with a uniform draw from 1 to half (C-CRD-06): from 40,
  a loss of 20 to 39. The cap of 10 keeps a raid from undoing several turns of building.
- About 6 raids a game, against 3 Shields: a raid meets a Shield rarely, so a Shield is a pleasant
  surprise, not a wall.

### Comebacks and runaways

- **Cards lean slightly to the trailing seat.** A card comes per capturing turn, not per capture, so a
  leader that takes six countries earns what a small seat earns for one. A set is a fixed number of
  armies, worth one to two turns of income to a seat with 3 to 6 income and a third of a turn to a
  leader with 15 to 25 (above).
- **The rule that stops a runaway on cards:** one card per turn, one card action per turn, fixed set
  values, and an eliminated seat's cards discarded rather than taken (choice V6; in the classic game,
  taking a beaten seat's cards is the strongest snowball there is).
- **Raids are not aimed at the leader by rule,** but a trailing seat bordering the leader's big stack
  can take 10 from it, and the cap stops the leader from doing more to a small seat than the stack
  holds.
- **A late swing has limited room.** Domination ends the game at 35 of 46, and events stop at 31. A
  set of 8 or a raid of 10 near the end moves one battle; it cannot by itself turn a seat with 15
  countries into one with 35.

### Island bonuses on a generated board

```python
def bonus(size, e): return max(size // 2 + e, 2)
print("bonus by size (rows) and entrances (columns 1-5); * = rejected by the fairness checks")
for size in (3, 5, 7, 10):
    row = []
    for e in range(1, 6):
        b = bonus(size, e)
        bad = b > size or (size >= 7 and e == 1)
        row.append(f"{b}{'*' if bad else ''}")
    print(size, row)
base = sum(s // 2 for s in (3, 3, 3, 3, 5, 5, 7, 7, 10))
print("sum of floor(size/2):", base, "; total bonuses = that + entrance countries:",
      {E: base + E for E in (14, 20, 26, 30, 36)})
print("alternative floor(size/2) + ceil(e/2), same entrance counts:",
      {E: base + -(-E // 2) for E in (14, 20, 26, 30, 36)}, "(per island ceil; the total is approximate)")
```

```text
bonus by size (rows) and entrances (columns 1-5); * = rejected by the fairness checks
3 ['2', '3', '4*', '5*', '6*']
5 ['3', '4', '5', '6*', '7*']
7 ['4*', '5', '6', '7', '8*']
10 ['6*', '7', '8', '9', '10']
sum of floor(size/2): 19 ; total bonuses = that + entrance countries: {14: 33, 20: 39, 26: 45, 30: 49, 36: 55}
alternative floor(size/2) + ceil(e/2), same entrance counts: {14: 26, 20: 29, 26: 32, 30: 34, 36: 37} (per island ceil; the total is approximate)
```

- **Value against size and entrances.** After the fairness checks, every island pays 0.6 to 1.0 armies
  per country (3 countries pay 2 or 3; 5 pay 3 to 5; 7 pay 5 to 7; 10 pay 7 to 10), and among islands
  of one size, the one with more entrances, harder to hold, pays more.
- **How the generator keeps bonuses comparable.** Within a board, the checks of
  [core-rules.md, Fairness checks](core-rules.md#fairness-checks) (no bonus above the size, no fortress,
  easy bonuses at most a quarter of the total) keep every island's bonus within that band. Across
  boards, the total is 19 plus the number of entrance countries: with 14 to 18 crossings and at most
  2 crossings per country, between 33 and 55, likely in the middle. That is more than the
  predecessor's 35 (C-BON-02), so islands weigh a little more in malpaco; choice V10 asks whether to
  tune that before play-tests.
- **Against income.** A small island (2 or 3) matches the country part of the income of a seat with
  up to 11 countries, a cheap first goal; the 10-country island (7 to 10) is a late prize worth a set every turn.

### Production centres

- One centre per seat, dealt one each, gives every seat the same start and a home worth defending.
  Its +1 a turn is a quarter to a third of a starting income of 3 to 4, and a twelfth of a 12-army
  mid-game income: a reason to fight over centres, not a decider.
- A seat holding all four centres earns +4 a turn, less than one set; centres alone do not snowball.
- The predecessor's centres paid nothing per turn, and their increase event doubled the stacks on
  them, up to 999 (C-CEN-02): a doubled 60 is +60, three to six turns of a 10- to 20-army income in one
  event, given to whoever stood there. The harvest's +3 per centre is a fixed, small gift, the same for every centre.
- The predecessor's centres were placed anywhere and moved by an event (C-CEN-01, C-CEN-03, C-CEN-04),
  so one seat could start with none, or with two side by side. Dealing one per seat on different
  islands removes that luck; fixed centres can be planned around.

### Events

```python
eligible = 20 * 4 - 4 - 4                  # 20 rounds of 4 seats, no events in round 1 nor in the last round (model)
for name, p in (("rare", 1 / 32), ("normal", 1 / 16), ("often", 1 / 8)):
    spacing = 1 + 1 / p                    # one forced empty transition after an event, then geometric waiting
    print(f"events {name:6} p=1/{round(1 / p)}: mean spacing {spacing:.0f} turn changes, about {eligible / spacing:.1f} per 20-round game")
def storm(stack): return min(stack // 2, 5)
print("storm loss per country:", {s: storm(s) for s in (1, 2, 3, 4, 6, 10, 20)}, "at most 3 countries, 15 armies")
```

```text
events rare   p=1/32: mean spacing 33 turn changes, about 2.2 per 20-round game
events normal p=1/16: mean spacing 17 turn changes, about 4.2 per 20-round game
events often  p=1/8: mean spacing 9 turn changes, about 8.0 per 20-round game
storm loss per country: {1: 0, 2: 1, 3: 1, 4: 2, 6: 3, 10: 5, 20: 5} at most 3 countries, 15 armies
```

- **How often.** Normal gives about one event every four rounds, four or so a game: enough to be
  remembered, not enough to steer. (In the owner's recordings of the predecessor at its default
  setting, 8 of 157 turn changes had an event, about one in twenty, `runs/coverage.md` and
  `runs/E018`.)
- **How big.** A storm costs at most 5 armies per country and 15 in all, spread over one to three
  stacks of possibly different seats: early, 1 or 2 armies per stack; at most a mid-game turn's
  income. A revolt moves one country of 1 to 3 armies, about one cheap capture, though it can break an
  island bonus, which is its surprise. A harvest gives 3 per centre to whoever holds them.
- **Why none decides a game.** No event zeroes a stack or eliminates a seat (C-HAZ-07 kept), none
  targets a seat, and none is drawn in round 1 or within 4 countries of a win. The predecessor's
  flood could take a 20-army stack to 1 to 9 (C-HAZ-05); malpaco's storm takes it to 15.
- **Who they hit.** Storms and revolts draw countries, so they fall on seats in proportion to what
  they hold: the leader is hit most often in absolute terms, without any rule that aims at it.

## Choices for the owner

Each choice lists the claims it settles, the options, a recommendation and its reason. The rules
above describe the recommended option. When the owner decides, this section becomes
`## The owner's decisions (<date>)`, keeping the options and reasons.

1. **V1. The deck** (C-CRD-01, C-CRD-02).
   - (a) a finite deck of 40 (Anchor 11, Compass 10, Lantern 8, Wild 4, Raid 4, Shield 3), shuffled
     from the seed, with the discard pile reshuffled when the draw pile runs out; (b) each draw
     independent, with the same proportions (no deck, no memory); (c) as (a), but no reshuffle: when
     the pile is empty, no more cards are drawn.
   - Recommendation (a): a new order every game, streaks limited by the deck (only 4 Raids in a pass),
     and a deck a player can count. (b) allows long runs of one kind; (c) turns cards off in a long
     game's late part.
2. **V2. Trade-in values** (C-CRD-05).
   - (a) fixed: three Anchors 4, three Compasses 6, three Lanterns 8, one of each 6, at most one Wild
     per set; (b) escalating with the game's trade-in count: 4, 6, 8, 10, 12, 15, then 5 more each;
     (c) larger fixed values like the predecessor's (5, 8 and 15 by kind), with up to two Wilds per set.
   - Recommendation (a): a set is a swing of one to two turns of income early and less later; (b) makes
     late sets worth 30 to 55 armies, so the deck decides; (c) makes an early 15-set worth three to
     five turns of income.
3. **V3. A pool-doubling card** (C-CRD-01, C-CRD-05).
   - (a) none; (b) a Surge kind whose set adds the seat's country income again, at most 8; (c) a set
     that doubles the whole pool, as the predecessor's did.
   - Recommendation (a): doubling pays most to the seat with the largest pool, the leader, which is a
     runaway lever; (b) is a capped version if the owner wants a big-swing card.
4. **V4. A card that empties its drawer's hand** (C-CRD-01, C-CRD-04).
   - (a) none; (b) a Squall card: drawing it discards one random card of the hand, and the Squall too;
     (c) a card that empties the whole hand, as the predecessor's did.
   - Recommendation (a): a punishment with no counter-play is bad luck without a decision; (b) is a mild
     version if the owner wants a bad-luck card in the deck.
5. **V5. The raid** (C-CRD-06, C-CRD-07).
   - (a) on an enemy country bordering one of the raider's own, with 2 or more armies: it loses half,
     rounded down, at most 10; a raid is the turn's one card action; a Shield cancels it automatically;
     (b) as (a), but on any enemy country, anywhere; (c) as the predecessor: any enemy country, its
     stack replaced by a random 1 to half, no cap.
   - Recommendation (a): a raid next to the raider sets up an attack the same turn, which is tactics,
     and the cap keeps one card from undoing several turns of building; (b) is mostly spite at a
     distance; (c) can remove 39 of 40 armies on one card.
   - **Proposed amendment to core-rules.md** (all options): in [The turn](core-rules.md#the-turn),
     phase 2 becomes "Cards: one card action, a trade-in or a raid, or none".
6. **V6. An eliminated seat's cards** (no claim in this file; the question core-rules.md left to T51).
   - (a) discarded; (b) taken by the seat that eliminated it, which may trade at once; (c) taken by
     that seat up to the hand limit, the rest discarded.
   - Recommendation (a): taking a beaten seat's cards is the classic runaway, rewarding the leader for
     being the leader; (b) and (c) add a reason to finish a seat off, at that cost.
7. **V7. Production centres** (C-CEN-01, C-CEN-02, C-CEN-03, C-CEN-04, C-HAZ-08).
   - (a) no centres, and no harvest event; (b) one centre per seat, dealt one each, on different
     islands and not neighbours, paying 1 army a turn to its owner, never moved; the harvest adds 3 to
     each centre's stack; (c) three centres drawn anywhere, paying nothing; the harvest doubles each
     centre's stack, adding at most 10, and a further event moves all three.
   - Recommendation (b): centres give each seat a home to defend and every board extra places worth
     fighting for, at a size that never decides a game; (a) is simpler; (c) keeps the predecessor's
     luck of placement and moving.
   - **Proposed amendments to core-rules.md**, if (b) is chosen: in
     [Reinforcement](core-rules.md#reinforcement), the pool becomes `max(floor(countries / 3), 2) + the
     bonuses of the islands held completely + 1 per centre held + trade-in`; in
     [The deal](core-rules.md#the-deal), "Production centres ... are placed after step 5" becomes
     step 6, one centre per seat as in [Production centres](#production-centres). With (c), the pool is
     unchanged and step 6 places three centres. With (a), the sentence on centres is removed.
8. **V8. The kinds of event and their sizes** (C-HAZ-01, C-HAZ-04, C-HAZ-05, C-HAZ-06).
   - (a) storm (up to 3 neighbouring countries on one island, each losing half, at most 5), revolt
     (one country of 1 to 3 armies passes to a bordering seat), harvest (with centres), weights 2, 1,
     2; (b) storm and harvest only: no event changes an owner; (c) the predecessor's sizes: a storm
     leaves each struck stack at most half less one, with no cap, and a revolt can turn any country,
     whatever its armies.
   - Recommendation (a): three kinds, each small, one of which can break an island bonus, give surprise
     without a decider; (b) is calmer, if the owner finds revolts unfair; (c) can cost a 40-army stack
     up to 39 armies in one draw.
9. **V9. Event frequency** (C-HAZ-03).
   - (a) Off / Rare 1 in 32 / Normal 1 in 16 / Often 1 in 8 per eligible turn change, Normal by
     default, never two in a row; (b) the same settings, Rare by default; (c) one draw per round
     instead of per turn change, at the start of the round, with the same expected rate.
   - Recommendation (a): about four events in a 20-round game is enough to notice and plan around,
     close to what the owner saw of the predecessor; (b) suits a player who wants little luck; (c)
     always puts the first seat right after an event, a small unfairness the per-turn draw avoids.
   - core-rules.md's [Options](core-rules.md#options) leave the event frequency to T51; with (a) or
     (b) its row reads: Off, Rare, Normal, Often; default Normal (a) or Rare (b).
10. **V10. Tuning the island bonus constants** (C-BON-02; the owner's decision 12 in core-rules.md).
    - (a) keep decision 12 as it is: `floor(size / 2) + entrances`, at least 2, no island above its
      size; (b) halve the entrance term, `floor(size / 2) + ceil(entrances / 2)`, for board totals near
      the predecessor's (26 to 37 instead of 33 to 55); (c) keep (a) and add a fairness check that a
      board's total bonus lies in a band (for example 38 to 50).
    - Recommendation (a): the owner chose it on 2026-10-12, and its total is only a model until
      play-tests; (b) and (c) are the levers if play-tests show islands dominate income or boards differ
      too much. Either would be an amendment to core-rules.md, Island bonuses or Fairness checks.

## Decisions, claim by claim

One row per in-scope spec claim (23). `keep` serves fun or balance as it is; `change` alters it;
`replace` swaps in a different rule; `drop` removes it; `open` waits for the owner. A row whose rule
changes the feel of play names its choice; the rule it links is the recommended option.

| Claim | Decision | malpaco's rule | Why |
| --- | --- | --- | --- |
| C-CRD-01 | change | [The kinds](#the-kinds): six kinds of malpaco's own (three army kinds, Wild, Raid, Shield), hands of five, empty at game start (choices V1, V3, V4) | Kept: cards, a hand of five, empty hands at start. Changed: no doubling card and no hand-emptying card, so every card is either armies, a tactical strike or a defence; the card screen is T52's. |
| C-CRD-02 | replace | [The deck](#the-deck): a finite 40-card deck, shuffled from the seed, discards reshuffled (choice V1) | A fixed list never shuffled is the same sequence of chances every game; a shuffled deck gives a new order each game, limits streaks and can be counted. |
| C-CRD-03 | change | [Earning a card](#earning-a-card): one card per capturing turn for every seat, never cancelled | Kept: a card for a turn with a capture, which rewards attacking without rewarding the leader per capture. Changed: the failed-attack cancel belonged to the forfeit, dropped in core-rules.md (decision 7). |
| C-CRD-04 | change | [The hand](#the-hand): limit five; on a full hand every seat discards one of six of its choice; no hand-emptying card (choice V4) | Kept: the limit of five, which stops hoarding. Changed: one discard rule for every seat (the computer's fixed priority goes), and the hand-emptying card is gone, because it punished with no counter-play. |
| C-CRD-05 | change | [Trade-ins](#trade-ins): one optional set per turn at the cards phase; three alike or one of each, one Wild at most; fixed 4, 6, 8 or 6 (choices V2, V3) | Kept: one set per turn, after income and before placement. Changed: smaller fixed values and no doubling, so a set is a swing and not a decider; every seat may skip; the computer's fixed priority and uncapped Wild use go. |
| C-CRD-06 | replace | [The raid](#the-raid-and-the-shield): a Raid card takes half of a bordering enemy stack, at most 10 (choice V5) | The predecessor's bomb could leave a 40-army stack at 1, and the computer's targeting was mis-indexed; a capped raid next to the raider is a readable tactic, the same for every seat. |
| C-CRD-07 | change | [The shield](#the-raid-and-the-shield): a Shield cancels one raid automatically and is discarded, with no other effect | Kept: a held defence that cancels one strike. Changed: the side effect on the bomber's hand was a defect, not a rule. |
| C-BON-01 | keep | [Island bonuses](#island-bonuses): every country of an island needed; complete islands add up | Holding a whole island is a clear goal, and a partial island paying nothing makes entrances worth fighting over. |
| C-BON-02 | replace | [Island bonuses](#island-bonuses): `floor(size / 2) + entrances`, at least 2, no island above its size (core-rules.md decision 12; tuning is choice V10) | Hand-written values fit one fixed map; a generated board needs a rule, and this one pays more for islands that are harder to hold (the owner's decision 12). |
| C-BON-03 | replace | [Island bonuses on a generated board](#island-bonuses-on-a-generated-board): a new board each game under core-rules.md's invariants and fairness checks | One fixed board is the same game every time; the owner chose a generated board (core-rules.md decision 1), whose checks keep bonuses comparable. |
| C-CEN-01 | open | [Production centres](#production-centres): one per seat, dealt one each, recommended (choice V7) | Whether malpaco has centres, and how many, changes the feel of play; the owner decides. Three centres drawn anywhere can leave a seat with none. |
| C-CEN-02 | open | [Production centres](#production-centres): +1 army a turn per centre held; the harvest adds 3, no doubling (choice V7) | A doubling up to 999 could add three to six turns of income in one event; a small, steady income and a fixed harvest make centres worth fighting for without deciding games. The owner decides. |
| C-CEN-03 | open | [Production centres](#production-centres): centres never move (choice V7) | Moving every centre at random undoes the planning around them; fixed centres can be attacked and defended. The owner decides. |
| C-CEN-04 | open | [Production centres](#production-centres): no two centres on one island or neighbours (choice V7) | Unconstrained placement can bunch centres; spacing them keeps the start even. The owner decides. |
| C-CEN-05 | keep | [Production centres](#production-centres): a centre belongs to whoever owns its country, survives capture, and is marked for every seat | Capturing a centre is the reason to attack it; marking it for everyone removes the predecessor's computer-only use of the list (T53 values it for the computer). |
| C-HAZ-01 | change | [Events](#events): storm, revolt and harvest, weights 2, 1, 2; a repeat redrawn once (choice V8) | Kept: a few kinds and the redraw of a repeat. Changed: earthquake and flood were one effect under two names; the centre move goes with fixed centres. |
| C-HAZ-02 | change | [When an event is drawn](#when-an-event-is-drawn): one eligibility rule at every turn change, for every seat | Kept: one dispatch and one set of effects for every seat. Changed: no route that depends on human seats can pre-empt a draw, so events are seat-blind. |
| C-HAZ-03 | change | [When an event is drawn](#when-an-event-is-drawn): 1 in 32, 16 or 8 by setting, Normal default; none in round 1, near a win or right after an event (choice V9) | Kept: a frequency setting, no events at the start or the end, no two in a row. Changed: the near-win pause follows malpaco's win rule (core-rules.md), and the rates are malpaco's. |
| C-HAZ-04 | replace | [Storm](#the-kinds-of-event): a drawn country and up to two neighbours on its island (choice V8) | A block of consecutively numbered countries means nothing on a generated board, and excluding one country was an artefact; neighbours on one island are a place on the map. |
| C-HAZ-05 | change | [Storm](#the-kinds-of-event): each struck stack loses half, at most 5, never below 1 (choice V8) | Kept: a storm thins stacks and never empties one. Changed: the loss is capped, so a storm costs at most a mid-game turn's income instead of most of a big stack. |
| C-HAZ-06 | change | [Revolt](#the-kinds-of-event): one country of 1 to 3 armies, of a seat with 3 or more, passes to a bordering seat (choice V8) | Kept: a revolt turns one country and changes no armies, and draws without regard to rank. Changed: only small stacks revolt and they go to a neighbour, so the swing is about one capture. |
| C-HAZ-07 | keep | [What no event does](#what-no-event-does): no stack to 0, no elimination, no centre removed, no seat targeted | The floor keeps events a surprise and never a decider; it is the owner's direction exactly. |
| C-HAZ-08 | open | [Harvest](#the-kinds-of-event): 3 armies on each centre, whoever owns it; how the computer values centres is T53's (choice V7) | The harvest exists only if centres do, and its size is part of the centre choice; the owner decides. The computer's use of centres in its moves is its policy (T53), not a rule. |
