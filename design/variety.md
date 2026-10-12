# malpaco variety

The parts of malpaco that make one game differ from the last: cards, island bonuses, production
centres and events. They are written so that a TypeScript implementer can build them without reading
`spec/`. They build on [core-rules.md](core-rules.md) (T50): a board generated from the seed, one
attack rule for every seat, ties re-rolled, domination at three quarters, one seeded random stream.
The computer opponent's choices (which set to trade, whom to raid, what to discard) are T53's (#196);
the UI of cards, the hand and events is T52's. This file states only the rules that bind every seat.

The starting point is the predecessor's rules as read from its code (the in-scope `spec/` files:
cards, island bonuses, production centres and hazards, 23 claims). The
[decision table](#decisions-claim-by-claim) gives one row per claim.

**Decided.** The owner decided all twelve choices on 2026-10-12. For surprise, the owner chose the
predecessor's sharper card and event mechanics over most of the recommendations: large fixed sets, a
pool-doubling set, a card that empties its drawer's hand, an uncapped raid, three wandering centres
and the predecessor's events. Values marked *(V<n>)* are those decisions, listed with their options,
recommendations and reasons in [The owner's decisions](#the-owners-decisions-2026-10-12). The rules
below describe the decided game, the **canonical** variant; the other options are kept as variants
in [variants.md](variants.md). Where a decided option met a T50 rule, the nearest consistent reading
was taken; [Reconciled with T50](#reconciled-with-t50) lists each. Where a decision needs a change to
[core-rules.md](core-rules.md), the change is stated as a proposed amendment in that decision; this
file does not edit the core rules. Build each value behind a named constant.

## Terms

Terms of [core-rules.md](core-rules.md) (seat, country, island, border, stack, turn, round) hold here.

- **Card**: a card in a seat's hand. A seat's **hand** holds at most five.
- **Set**: three cards traded together, at most one set per turn.
- **Centre**: a production centre, a country that events can enrich or move.
- **Event**: a random happening between turns that changes armies, owners or centres.
- **Turn change**: the moment after one seat's turn (after its victory check) and before the next
  seat's income.

## Cards

### The kinds

malpaco has eight kinds of card, with names of its own:

| Kind | Copies | What it does |
| --- | --- | --- |
| Anchor | 11 | three Anchors are a set worth 5 armies |
| Compass | 7 | three Compasses are a set worth 8 armies |
| Lantern | 4 | three Lanterns are a set worth 15 armies |
| Surge | 4 | three Surges are a set that doubles the turn's pool *(V3)* |
| Raid | 4 | three Raids are a set that raids any enemy country ([The raid](#the-raid-and-the-shield)) *(V5)* |
| Wild | 5 | stands for any card in a set, up to two per set *(V2)* |
| Shield | 4 | held: cancels the next raid against its holder, then is discarded |
| Squall | 1 | never held: drawing it empties the drawer's hand *(V4)* |

40 cards in all. The counts are malpaco's own *(V1)*.

### The deck

- At game start, the 40 cards are shuffled (from the game's seeded stream, after the deal and the
  centres) into a face-down **draw pile** *(V1)*. Every hand starts empty.
- A drawn card leaves the pile. Traded, played and discarded cards, and a drawn Squall, go to a
  face-up **discard pile**.
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
- A seat that must draw while holding five first discards one of its five, any one, its own choice,
  and then draws, without seeing the new card first *(V11)*. Every seat follows this rule; which card
  the computer discards is its policy (T53).
- **The Squall.** A seat that draws the Squall puts its whole hand, and the Squall, on the discard
  pile *(V4)*. Drawn into an empty hand it costs nothing. It is never held and never part of a set.

### Trade-ins

- **When.** In the cards phase of its turn (after income, before placement), a seat may trade **one
  set**. It is never forced.
- **What a set is.** Three cards of one tradeable kind (Anchor, Compass, Lantern, Surge or Raid),
  of which up to two may be Wilds standing for the missing cards *(V2)*. At least one card must be of
  the kind itself: three Wilds are no set. Shields and the Squall are never part of a set.
- **What a set gives** *(V2, V3, V5)*:

  | Set | Effect |
  | --- | --- |
  | three Anchors | 5 armies added to the pool |
  | three Compasses | 8 armies added to the pool |
  | three Lanterns | 15 armies added to the pool |
  | three Surges | the pool is doubled: the turn's income (country part and island bonuses) is added again |
  | three Raids | a raid ([below](#the-raid-and-the-shield)); no armies |

  Values are fixed for the whole game; they do not grow with the number of sets traded.
- The traded cards go to the discard pile. The armies are placed this turn like the rest of the pool
  ([core-rules.md, Reinforcement](core-rules.md#reinforcement)).
- Every seat trades under this rule, including the computer: it may skip a trade, and it may use at
  most two Wilds. Which set it trades, and when, is its policy (T53).

### The raid and the shield

- **The raid** *(V5)*. Trading three Raids, the seat chooses **any enemy country**, anywhere on the
  board. That stack is replaced by a whole number drawn uniformly from 1 to half its armies, rounded
  down (at least 1): 9 becomes 1 to 4, 40 becomes 1 to 20. A 1-army stack is unchanged. Ownership does
  not change, and the raiding seat's pool is unchanged.
- **The shield.** If the target country's owner holds a Shield, the Shield is discarded and the raid
  has no effect. This happens automatically: holding a Shield is the choice. The three traded cards
  are discarded either way, and nothing else in either hand changes.
- Every seat raids under the same rule. Whom the computer raids is its policy (T53).
- **Counter-play.** A raid needs a set of three, so it is rare and its build-up can be watched: hand
  counts are public. A Shield stops one. Distance does not protect a stack, and the loss grows with
  the stack (half or more of it), so one huge stack is the most exposed; several medium stacks lose
  less to any one raid.

### An eliminated seat's cards

A seat that loses its last country puts its hand on the discard pile *(V6)*. Nobody takes it. (This
settles what [core-rules.md, Ownership change](core-rules.md#ownership-change) left to T51.)

## Island bonuses

The rule is the owner's decision 12 in [core-rules.md, Island bonuses](core-rules.md#island-bonuses),
unchanged here *(V10)*: an island held completely pays `floor(size / 2) + entrances`, at least 2, and
the generator's fairness checks reject a board with an island whose bonus exceeds its size.

- A bonus needs every country of the island; partial control pays nothing. Several islands held add
  up, with no extra for a set of islands and no reduction.
- The bonus enters the pool at income ([core-rules.md, Reinforcement](core-rules.md#reinforcement)),
  so a Surge set doubles it too.
- A raid or an event that changes no owner leaves bonuses as they are; a revolt
  ([Events](#events)) can break or complete one.
- Bonuses are the board's: no card or event changes a bonus value during a game.

How bonuses compare on a generated board is in
[Island bonuses on a generated board](#island-bonuses-on-a-generated-board).

## Production centres

*(V7.)*

- **How many and where.** Three centres, drawn from the game stream as three distinct countries of
  the board, uniformly, after the deal ([core-rules.md, The deal](core-rules.md#the-deal), step 5).
  There is no spacing, island or owner condition: a seat may start with none, one or several.
- **What a centre gives.** Nothing per turn: income is countries, island bonuses and sets only. A
  centre matters through the harvest and the shift events.
- **Ownership.** A centre belongs to whoever owns its country. Capturing the country takes the
  centre. Centres are marked on the board for every seat.
- **The harvest.** The harvest event doubles each centre's stack, adding **at most 10** armies per
  centre, whoever owns it.
- **The shift.** The shift event draws the three centres again, the same way as at the start (a
  centre may be drawn where it was).

## Events

### When an event is drawn

- An event may happen at a turn change. At each eligible turn change, one draw from the game stream
  decides whether an event happens, with the chance set by the **event frequency** option *(V9)*:

  | Option | Chance per eligible turn change |
  | --- | --- |
  | Off | none |
  | Rare | 1 in 21 |
  | Normal (default) | 1 in 14 |
  | Often | 1 in 8 |

- A turn change is **not eligible** in round 1, while any seat is within 4 countries of winning
  ([core-rules.md, Victory](core-rules.md#victory)), after the game has ended, or right after a turn
  change that had an event (so two events never come back to back).
- **The round limit** *(V12)*. When the round limit is on, no turn change in the last **3** rounds is
  eligible (rounds 18 to 20 of a 20-round limit), so every seat has at least three turns to answer
  the last event before the game is scored.
- The check is the same at every turn change, whoever has played and whoever plays next. No route
  skips it for one kind of seat.
- When an event happens, its kind is drawn by weight *(V8)*: Storm 4, Revolt 2, Shift 2, Harvest 6
  (of 14). A draw of the same kind as the previous event is drawn again once, so repeats are rarer
  without being impossible.

### The kinds of event

*(V8.)*

- **Storm.** One country is drawn uniformly, and a size of 3 or 4, equally likely. The storm strikes
  a connected group of countries of that size containing the drawn country, drawn uniformly among
  all such groups. Each struck stack is replaced by a whole number drawn uniformly from 1 to a bound:
  for a stack above 6, half the stack rounded down, minus one; for a stack of 1 to 6, the stack minus
  one; the bound is at least 1. From 20 armies a stack keeps 1 to 9; a 6-army stack keeps 1 to 5; a
  1-army stack is unchanged. Owners do not change.
- **Revolt.** The eligible seats are those holding 3 or more countries; with fewer than two, nothing
  happens. One eligible seat is drawn uniformly. One of its countries that borders another seat is
  drawn uniformly, among those holding more than 1 army if there are any. It passes to one of the
  other seats it borders, drawn uniformly, with its armies unchanged.
- **Harvest.** Each centre's stack doubles, adding at most 10 armies per centre.
- **Shift.** The three centres are drawn again ([Production centres](#production-centres)).

### What no event does

- No event leaves a stack at 0, eliminates a seat (a revolt's seat keeps at least 2 countries),
  removes a centre, or changes an island's bonus value.
- No event chooses a seat by rank, by count or by being human or computer: storms draw countries, and
  a revolt draws its seat by equal lot among the eligible.
- No event can end a game or settle its scoring: events stop within 4 countries of a win and for the
  last 3 rounds of a round-limit game *(V12)*, and a revolt moves one country.

## Fairness between seats

Every card, bonus, centre and event rule above applies alike to human and computer seats. The
computer differs only in what it chooses (T53), never in what it may do or what it knows. Each of the
predecessor's asymmetries in these areas is dropped:

| The predecessor's asymmetry | Row | malpaco |
| --- | --- | --- |
| the computer trades automatically by a fixed priority and never skips | C-CRD-05 | every seat may trade or skip; the computer's choice is its policy (T53) |
| the computer's removal step can spend three wildcards on one set | C-CRD-05 | at most two Wilds per set, for every seat |
| the computer discards by a fixed priority on a full hand; the human clicks one away | C-CRD-04 | every seat chooses which of its five to discard before drawing |
| a failed human attack cancels the turn's card draw | C-CRD-03 | nothing cancels a seat's draw |
| the computer's bomb target is chosen through a mis-indexed comparison | C-CRD-06 | one targeting rule (any enemy country) for every seat |
| the human's protected branch reorders the bomber's own hand and can clear its cards | C-CRD-07 | a cancelled raid discards the three Raid-set cards and the Shield and touches nothing else |
| the between-turn routes can pre-empt an event draw depending on human-seat conditions | C-HAZ-02 | one eligibility rule at every turn change |
| only the computer's handlers read the centre list | C-CEN-05 | centres are marked for every seat; how the computer values them is T53's |

## Reconciled with T50

Where a decided option, taken from the predecessor, met a T50 rule or the generated board, the nearest
consistent reading was taken:

1. **Storms on a generated board** (V8, C-HAZ-04). The predecessor struck a block of 3 or 4
   consecutively numbered countries and never the first one. Numbers mean nothing on a generated
   board, so a storm strikes a connected group of 3 or 4 countries; the first-country exception goes.
2. **Whom a revolt's country joins** (V8, C-HAZ-06). The spec reads the flip but not the receiving
   seat; malpaco gives the country to a seat it borders. The predecessor's search of up to eight draws
   for a country with more than one army becomes a uniform draw among such countries.
3. **The harvest's doubling** (V7, C-CEN-02). The predecessor doubled up to a stored cap of 999; T50
   has no stack cap, and V7's option capped the gain at 10 per centre.
4. **When events are paused** (V9, C-HAZ-03). The predecessor paused events for the first six
   player-turns and while any seat held more than 38 countries; T50 pauses them in round 1 and within
   4 countries of a win, and V12 adds the round limit's last 3 rounds. The rates and the one-turn
   cooldown are the predecessor's; its "never" setting is the Off option.
5. **Seat-blind events** (C-HAZ-02). The predecessor's dispatch could be pre-empted by routes that
   depend on human seats; T50 has one rule for every seat, so the check is the same at every turn
   change.
6. **The Squall and an empty hand** (V4, C-CRD-02). The predecessor's draw skipped the hand-emptying
   card when the hand was empty; with a finite deck the card is drawn like any other and empties an
   empty hand harmlessly.
7. **The raid's trigger** (V5). V5's predecessor option is read in full: the raid is a set of three
   Raid cards (Wilds count, as in V2), traded as the turn's one set, not a single card.
8. **Centre placement** (V7, C-CEN-01). The predecessor picked fixed positions of a fresh permutation;
   malpaco draws three distinct countries uniformly, which is the same distribution, on the generated
   board.

T50's protections hold throughout: no event wipes a stack or eliminates a seat, events pause in round
1, near a win and before a round limit's scoring, and every rule is the same for every seat.

## Surprise and balance, argued

Every number in this section is a **model**, not a measurement of the predecessor or of malpaco. The
models assume a 4-seat game of 20 or 30 rounds (core-rules.md's toy model says a few dozen rounds; the
owner's recorded games of the predecessor, which ended at its concession, ran 29 to 55 turns, 7 to 14
rounds, in `runs/E018`), a capture in 75% of a seat's turns (an assumption), a pool before cards of
4, 9 and 15 in rounds 1–5, 6–12 and 13 on (invented from core-rules.md's income table), and a seat
that trades the set worth most armies whenever it holds one, else a raid (a neutral stand-in, not
T53's policy). The decided options make the game swingier than the recommendations would have; that
is the owner's intent (cards add surprise), and the numbers below say by how much.

Code is shown as indented blocks, with its output after it.

### The deck in a game

    import random
    from collections import Counter
    DECK = {"anchor": 11, "compass": 7, "lantern": 4, "wild": 5, "raid": 4, "surge": 4, "shield": 4, "squall": 1}
    ARMY_SET = {"lantern": 15, "compass": 8, "anchor": 5}
    LIMIT = 5

    def income(r):                        # a model of one seat's pool before cards, by round
        return 4 if r <= 5 else 9 if r <= 12 else 15

    def sets(hand):
        """Every set in hand: three of one tradeable kind, up to two of them Wilds (at least one real card)."""
        c = Counter(hand); out = []
        for k in ("lantern", "compass", "anchor", "surge", "raid"):
            if c[k] >= 1 and c[k] + min(c["wild"], 2) >= 3:
                real = min(c[k], 3)
                out.append((k, [k] * real + ["wild"] * (3 - real)))
        return out

    def choose(hand, r):
        """A neutral stand-in, not T53's policy: the set worth most armies now, else a raid."""
        best = None
        for k, cards in sets(hand):
            value = ARMY_SET.get(k, income(r) if k == "surge" else 0)
            if k != "raid" and (best is None or value > best[0]):
                best = (value, k, cards)
        if best is None:
            for k, cards in sets(hand):
                if k == "raid":
                    best = (0, k, cards)
        return best

    def game(rng, seats=4, rounds=20, p_capture=0.75):
        pile = [k for k, n in DECK.items() for _ in range(n)]; rng.shuffle(pile); discard = []
        hands = [[] for _ in range(seats)]
        stats = Counter(); draws = Counter(); by_round = Counter()
        for r in range(1, rounds + 1):
            for s in range(seats):
                h = hands[s]
                b = choose(h, r)
                if b:
                    value, k, cards = b
                    for card in cards: h.remove(card)
                    discard += cards; stats["trade:" + k] += 1; by_round[r] += value
                if rng.random() < p_capture:            # one draw per capturing turn
                    if len(h) == LIMIT:                 # discard first; the model drops a shield, else a lone card
                        stats["full"] += 1
                        c = Counter(h)
                        drop = "shield" if c["shield"] else min(h, key=lambda k: (k == "wild", c[k]))
                        h.remove(drop); discard.append(drop)
                    if not pile:
                        pile, discard = discard, []; rng.shuffle(pile); stats["reshuffle"] += 1
                    card = pile.pop(); draws[card] += 1
                    if card == "squall":                # the drawer's whole hand goes
                        stats["squall"] += 1; stats["squall_lost"] += len(h)
                        discard += h + ["squall"]; h.clear()
                    else:
                        h.append(card)
        return stats, draws, by_round

    def report(rounds, N=20000, seats=4):
        rng = random.Random(51)
        S = Counter(); D = Counter(); B = Counter()
        for _ in range(N):
            s, d, b = game(rng, rounds=rounds); S += s; D += d; B += b
        per = N * seats
        print(f"--- {rounds} rounds, 4 seats, a capture in 75% of turns")
        print("draws per game by kind:", {k: round(D[k] / N, 1) for k in DECK}, "total", round(sum(D.values()) / N, 1))
        print("reshuffles per game:", round(S["reshuffle"] / N, 2))
        trades = {k: S["trade:" + k] / per for k in ("anchor", "compass", "lantern", "surge", "raid")}
        print("sets per seat per game:", {k: round(v, 2) for k, v in trades.items()}, "total", round(sum(trades.values()), 2))
        print("hand-emptying draws per seat per game:", round(S["squall"] / per, 2),
              "; cards lost per such draw:", round(S["squall_lost"] / max(S["squall"], 1), 2))
        print("discards on a full hand per seat per game:", round(S["full"] / per, 2))
        for lo, hi in ((1, 5), (6, 12), (13, rounds)):
            v = sum(B[r] for r in range(lo, hi + 1)); turns = per * (hi - lo + 1)
            print(f"rounds {lo}-{hi}: income {income(lo)}, card armies per seat-turn {v / turns:.2f}")

    for rounds in (20, 30):
        report(rounds)

Its output:

    --- 20 rounds, 4 seats, a capture in 75% of turns
    draws per game by kind: {'anchor': 16.8, 'compass': 10.2, 'lantern': 5.6, 'wild': 8.3, 'raid': 5.5, 'surge': 5.6, 'shield': 6.2, 'squall': 1.8} total 60.0
    reshuffles per game: 1.08
    sets per seat per game: {'anchor': 1.1, 'compass': 0.58, 'lantern': 0.26, 'surge': 0.24, 'raid': 0.17} total 2.35
    hand-emptying draws per seat per game: 0.45 ; cards lost per such draw: 2.67
    discards on a full hand per seat per game: 2.87
    rounds 1-5: income 4, card armies per seat-turn 0.15
    rounds 6-12: income 9, card armies per seat-turn 0.95
    rounds 13-20: income 15, card armies per seat-turn 1.18
    --- 30 rounds, 4 seats, a capture in 75% of turns
    draws per game by kind: {'anchor': 25.3, 'compass': 15.2, 'lantern': 8.3, 'wild': 12.8, 'raid': 7.9, 'surge': 8.2, 'shield': 9.4, 'squall': 2.9} total 90.1
    reshuffles per game: 2.29
    sets per seat per game: {'anchor': 1.8, 'compass': 0.95, 'lantern': 0.43, 'surge': 0.4, 'raid': 0.29} total 3.87
    hand-emptying draws per seat per game: 0.73 ; cards lost per such draw: 2.79
    discards on a full hand per seat per game: 4.67
    rounds 1-5: income 4, card armies per seat-turn 0.16
    rounds 6-12: income 9, card armies per seat-turn 0.96
    rounds 13-30: income 15, card armies per seat-turn 1.16

What it says:

- A 20-round game draws about 60 cards, so the deck goes round about once. Each seat sees about 15.
- **Sets are rarer than in a mixed-set design.** With three alike needed, a seat trades about 2.4
  sets in 20 rounds (3.9 in 30): mostly Anchors, about one Lantern set in four games per seat, and a
  Surge or a raid about once in four to six games per seat. A set is an event when it comes.
- **Hands fill and churn.** A seat discards into a full hand about three times a game: holding out
  for three alike costs cards. Discarding before the draw (V11) makes that discard a small gamble.
- **The Squall** empties a hand about once in two games per seat, costing about 2.7 cards when it
  does: a sharp, rare setback, as the owner chose.
- Cards add about 1 army per turn on average after round 5, in large lumps.

### Sets against income

    INCOME = {"early (rounds 1-5)": (3, 5), "mid (rounds 6-12)": (6, 12), "late, leader": (15, 25),
              "late, trailing seat": (3, 6), "smallest seat (floor)": (2, 3)}
    for stage, (lo, hi) in INCOME.items():
        cells = "; ".join(f"{v} is {v / hi:.1f}-{v / lo:.1f}" for v in (5, 8, 15))
        print(f"{stage:22} income {lo:2}-{hi:2}: sets of {cells} turns; a doubling adds {lo}-{hi} (1 turn)")

    def raid_loss(n):                  # the stack becomes a uniform draw from 1 to max(n // 2, 1)
        top = max(n // 2, 1)
        return n - (1 + top) / 2, n - top, n - 1   # mean, least and most lost
    print("raid loss (mean, least, most):", {n: tuple(round(x, 1) for x in raid_loss(n)) for n in (2, 4, 9, 20, 40)})

    def storm_left_top(n):             # the struck stack becomes a uniform draw from 1 to this
        return max(n // 2 - 1, 1) if n > 6 else max(n - 1, 1)
    def storm_loss(n):
        top = storm_left_top(n)
        return n - (1 + top) / 2, n - top, n - 1
    print("storm loss per country (mean, least, most):", {n: tuple(round(x, 1) for x in storm_loss(n)) for n in (1, 2, 4, 6, 10, 20, 40)})
    print("harvest per centre (stack: added):", {n: min(n, 10) for n in (2, 5, 10, 30)}, "three centres: at most 30")

    def eligible(rounds, quiet_rounds):        # turn changes of 4 seats, none in round 1 nor in the quiet rounds at the end
        return (rounds - 1 - quiet_rounds) * 4
    for name, p in (("rare", 1 / 21), ("normal", 1 / 14), ("often", 1 / 8)):
        spacing = 1 + 1 / p                    # one forced empty transition after an event, then geometric waiting
        print(f"events {name:6} p=1/{round(1 / p)}: mean spacing {spacing:.0f} turn changes; per game:"
              f" {eligible(20, 1) / spacing:.1f} (20 rounds, domination, ~1 round paused near the end),"
              f" {eligible(20, 3) / spacing:.1f} (round limit 20, last 3 quiet), {eligible(30, 3) / spacing:.1f} (limit 30)")
    weights = {"storm": 4, "revolt": 2, "shift": 2, "harvest": 6}
    print("share of events by kind:", {k: f"{100 * w / 14:.0f}%" for k, w in weights.items()})

Its output:

    early (rounds 1-5)     income  3- 5: sets of 5 is 1.0-1.7; 8 is 1.6-2.7; 15 is 3.0-5.0 turns; a doubling adds 3-5 (1 turn)
    mid (rounds 6-12)      income  6-12: sets of 5 is 0.4-0.8; 8 is 0.7-1.3; 15 is 1.2-2.5 turns; a doubling adds 6-12 (1 turn)
    late, leader           income 15-25: sets of 5 is 0.2-0.3; 8 is 0.3-0.5; 15 is 0.6-1.0 turns; a doubling adds 15-25 (1 turn)
    late, trailing seat    income  3- 6: sets of 5 is 0.8-1.7; 8 is 1.3-2.7; 15 is 2.5-5.0 turns; a doubling adds 3-6 (1 turn)
    smallest seat (floor)  income  2- 3: sets of 5 is 1.7-2.5; 8 is 2.7-4.0; 15 is 5.0-7.5 turns; a doubling adds 2-3 (1 turn)
    raid loss (mean, least, most): {2: (1.0, 1, 1), 4: (2.5, 2, 3), 9: (6.5, 5, 8), 20: (14.5, 10, 19), 40: (29.5, 20, 39)}
    storm loss per country (mean, least, most): {1: (0.0, 0, 0), 2: (1.0, 1, 1), 4: (2.0, 1, 3), 6: (3.0, 1, 5), 10: (7.5, 6, 9), 20: (15.0, 11, 19), 40: (30.0, 21, 39)}
    harvest per centre (stack: added): {2: 2, 5: 5, 10: 10, 30: 10} three centres: at most 30
    events rare   p=1/21: mean spacing 22 turn changes; per game: 3.3 (20 rounds, domination, ~1 round paused near the end), 2.9 (round limit 20, last 3 quiet), 4.7 (limit 30)
    events normal p=1/14: mean spacing 15 turn changes; per game: 4.8 (20 rounds, domination, ~1 round paused near the end), 4.3 (round limit 20, last 3 quiet), 6.9 (limit 30)
    events often  p=1/8: mean spacing 9 turn changes; per game: 8.0 (20 rounds, domination, ~1 round paused near the end), 7.1 (round limit 20, last 3 quiet), 11.6 (limit 30)
    share of events by kind: {'storm': '29%', 'revolt': '14%', 'shift': '14%', 'harvest': '43%'}

What it says:

- **A set's size depends on who trades it.** A 15-set is three to five turns of early income, one
  turn or less of a late leader's, and **five to seven and a half turns** of the smallest seat's. A
  Surge adds exactly one turn's income for anyone, so it is worth most to the seat with the largest
  pool: 15 to 25 armies for a late leader.
- **Comebacks.** The large fixed sets and the uncapped raid help a trailing seat most: a 15-set
  multiplies the smallest seat's placement five- to sevenfold for a turn, and a raid on the leader's main stack of 40 removes 20 to
  39 armies (about 30 on average). These swings can change who leads.
- **Runaways.** The Surge set helps the leader most, and nothing in the cards is paused near a win:
  a leader at 33 countries with a Surge set can double a pool of 20 or more and finish the game. The
  domination win and the event pause bound the end, not the cards. One card per turn, one set per
  turn and an eliminated seat's cards discarded (V6) are the brakes that remain.
- **Is one card ever a decider?** More often than in the recommended design. A Lantern set or a raid
  at the right moment can decide a close game; neither can by itself turn a seat with 15 countries
  into one with 35, because a set is one turn's placement and the captures still have to be fought.
  Sets are rare (about 2.4 per seat per game), so most turns are decided by the dice and the board.

### The raid and the shield

- The predecessor's bomb and malpaco's raid are the same effect: the stack keeps 1 to half. From 9,
  a loss of 5 to 8; from 40, 20 to 39. With ties re-rolled a defending army costs one attacking army
  on average ([core-rules.md, Combat odds](core-rules.md#combat-odds)), so a raid on a large stack is
  worth many turns of income to an attacker at that border.
- About 0.2 raid sets per seat per game (one raid every one to two games across the four seats),
  against 4 Shields in the deck (about 6 drawn per game): a raid meets a Shield often enough to keep
  a Shield worth holding.

### Island bonuses on a generated board

The bonus of one island, by size and entrances:

    def bonus(size, e): return max(size // 2 + e, 2)
    print("bonus by size (rows) and entrances (columns 1-5); * = rejected by the fairness checks")
    for size in (3, 5, 7, 10):
        row = []
        for e in range(1, 6):
            b = bonus(size, e)
            bad = b > size or (size >= 7 and e == 1)
            row.append(f"{b}{'*' if bad else ''}")
        print(size, row)

Its output:

    bonus by size (rows) and entrances (columns 1-5); * = rejected by the fairness checks
    3 ['2', '3', '4*', '5*', '6*']
    5 ['3', '4', '5', '6*', '7*']
    7 ['4*', '5', '6', '7', '8*']
    10 ['6*', '7', '8', '9', '10']

The board's total bonus, over every vector of entrance counts (one count per island) that passes the
island-level fairness checks of [core-rules.md, Fairness checks](core-rules.md#fairness-checks):

    # Board bonus totals over admissible entrance counts (a model of the checks, not of the generator).
    from itertools import product
    SIZES = (3, 3, 3, 3, 5, 5, 7, 7, 10)

    def rule_a(s, e): return max(s // 2 + e, 2)                 # decision 12
    def rule_b(s, e): return max(s // 2 + -(-e // 2), 2)        # the alternative, rounded per island

    def admissible(es):
        """core-rules.md's island-level fairness checks, as far as entrance counts decide them."""
        if any(rule_a(s, e) > s for s, e in zip(SIZES, es)):      # no bonus above the size
            return False
        if any(s >= 7 and e == 1 for s, e in zip(SIZES, es)):     # fortress: 7+ countries, one entrance
            return False
        singles = [i for i, e in enumerate(es) if e == 1]
        if len(singles) > 3:                                      # more than 3 single-entrance islands
            return False
        total = sum(rule_a(s, e) for s, e in zip(SIZES, es))
        if 4 * sum(rule_a(SIZES[i], 1) for i in singles) > total: # easy bonuses over a quarter
            return False
        return 14 <= sum(es) <= 36                                # entrance countries: 14-18 crossings, <= 2 per country

    ok = [es for es in product(*(range(1, s + 1) for s in SIZES)) if admissible(es)]
    for name, rule in (("(a) floor(size/2) + entrances", rule_a), ("(b) floor(size/2) + ceil(entrances/2)", rule_b)):
        totals = sorted({sum(rule(s, e) for s, e in zip(SIZES, es)) for es in ok})
        print(f"{name}: totals {totals[0]} to {totals[-1]}; every value between occurs: {totals == list(range(totals[0], totals[-1] + 1))}")
    print("entrance countries on admissible vectors:", min(map(sum, ok)), "to", max(map(sum, ok)))
    print("most entrances per island under the checks:", [max(es[i] for es in ok) for i in range(len(SIZES))])
    print("bonus per country, (a):", round(min(rule_a(s, e) / s for es in ok for s, e in zip(SIZES, es)), 2), "to",
          round(max(rule_a(s, e) / s for es in ok for s, e in zip(SIZES, es)), 2))

Its output:

    (a) floor(size/2) + entrances: totals 34 to 46; every value between occurs: True
    (b) floor(size/2) + ceil(entrances/2): totals 28 to 34; every value between occurs: True
    entrance countries on admissible vectors: 15 to 27
    most entrances per island under the checks: [2, 2, 2, 2, 3, 3, 4, 4, 5]
    bonus per country, (a): 0.6 to 1.0

- **Bounds, not achieved boards.** These are bounds over entrance vectors that pass the checks an
  entrance count decides (no bonus above the size, no fortress, at most 3 single-entrance islands, easy
  bonuses at most a quarter, 14 to 36 entrance countries). Every total in each range occurs for some
  such vector. Whether a generated board reaches every one also depends on the island-graph checks
  (an island touching at most 4 others, at most 4 crossings apart, at most 2 crossings per country),
  which this model does not build; the achieved range can only be the same or narrower.
- **Value against size and entrances.** After the checks, every island pays 0.6 to 1.0 armies per
  country (3 countries pay 2 or 3; 5 pay 3 to 5; 7 pay 5 to 7; 10 pay 7 to 10), and among islands of
  one size, the one with more entrances, harder to hold, pays more.
- **How the generator keeps bonuses comparable.** Within a board, those checks keep every island's
  bonus in that band. Across boards, decision 12's total lies between **34 and 46**, against the
  predecessor's 35 (C-BON-02). The halved entrance term (a variant, V10) gives 28 to 34.
- **With the Surge set,** island bonuses are doubled too, so a seat holding several islands gains the
  most from a Surge: another reason it favours the leader.

### Production centres

- Three centres drawn anywhere: one seat may start with two and another with none. They pay nothing
  per turn, so the start stays even in income; the difference is who stands to gain from the
  harvest.
- The harvest is the commonest event (6 of 14, 43%): about two harvests in a 20-round game at Normal.
  Each adds up to 10 per centre, up to 30 armies to one seat if it holds all three, two turns of mid
  income. That is a large, lucky gift, the predecessor's character with its cap of 999 brought down to
  10 per centre.
- The shift (14% of events) moves all three, so holding centres is a gamble on the next harvest
  coming before the next shift.

### Events

- **How often.** Normal gives about one event every 15 turn changes, about five in a 20-round game
  (a little over four with a 20-round limit and its quiet last 3 rounds, about seven with a 30-round
  limit). In the owner's recordings of the predecessor at its default setting, 8 of 157 turn changes
  had an event, about one in twenty (`runs/coverage.md` and `runs/E018`).
- **How big.** A storm strikes 3 or 4 countries and leaves each big stack at under half: from 20, a
  loss of 11 to 19 per country, so a storm can cost a seat 40 or more armies on a crowded front. A
  revolt moves one country with all its armies, which can break an island bonus. A harvest gives up
  to 30 armies. These are the largest swings in the game after the cards.
- **Why none decides a game by itself.** No event zeroes a stack or eliminates a seat, none targets
  a seat, and none is drawn in round 1, within 4 countries of a win, or in a round-limit game's last 3
  rounds (V12): in a two-seat game at 24 against 22 countries before the last turn, a revolt could
  make it 23 against 23 and hand the tie-break to the last placement; the pause rules that out. Every
  seat has at least three turns to answer the last event.
- **Who they hit.** Storms fall on countries uniformly, so they hit seats in proportion to what they
  hold; a revolt draws its seat by equal lot among those with 3 or more countries, so a small seat is
  as likely a victim as the leader.

## The owner's decisions (2026-10-12)

The owner decided all twelve choices on 2026-10-12. Each entry keeps the claims it settles, the
options offered, the recommendation and its reason, and adds the decision. Four follow the
recommendation (V1, V6, V10, V12); **eight go against it** (V2, V3, V4, V5, V7, V8, V9,
V11), choosing the predecessor's mechanics for surprise. The rules above describe the decided
options; [variants.md](variants.md) keeps the others.

1. **V1. The deck** (C-CRD-01, C-CRD-02).
   - (a) a finite deck, shuffled from the seed, with the discard pile reshuffled when the draw pile runs
     out; (b) each draw independent, with fixed proportions (no deck, no memory); (c) as (a), but no
     reshuffle: when the pile is empty, no more cards are drawn.
   - Recommendation (a): a new order every game, streaks limited by the deck, and a deck a player can
     count. (b) allows long runs of one kind; (c) turns cards off in a long game's late part.
   - **Decided: (a).** The composition follows the other decisions ([The kinds](#the-kinds)).
2. **V2. Trade-in values** (C-CRD-05).
   - (a) fixed: three Anchors 4, three Compasses 6, three Lanterns 8, one of each 6, at most one Wild
     per set; (b) escalating with the game's trade-in count: 4, 6, 8, 10, 12, 15, then 5 more each;
     (c) larger fixed values like the predecessor's (5, 8 and 15 by kind), with up to two Wilds per set.
   - Recommendation (a): a set was one to two turns of the trader's income early and less later; (b)
     makes late sets worth 30 to 55 armies, so the deck decides; (c) makes a 15-set worth three to five
     turns of early income and 5 to 7.5 of a small seat's.
   - **Decided: (c), against the recommendation.** Large sets are rarer and bigger surprises. There
     is no one-of-each set.
3. **V3. A pool-doubling card** (C-CRD-01, C-CRD-05).
   - (a) none; (b) a Surge kind whose set adds the seat's country income again, at most 8; (c) a set
     that doubles the whole pool, as the predecessor's did.
   - Recommendation (a): doubling pays most to the seat with the largest pool, the leader.
   - **Decided: (c), against the recommendation.** The Surge set doubles the whole pool.
4. **V4. A card that empties its drawer's hand** (C-CRD-01, C-CRD-04).
   - (a) none; (b) a Squall card: drawing it discards one random card of the hand, and the Squall too;
     (c) a card that empties the whole hand, as the predecessor's did.
   - Recommendation (a): a punishment with no counter-play is bad luck without a decision.
   - **Decided: (c), against the recommendation.** One Squall in the deck empties its drawer's hand.
5. **V5. The raid** (C-CRD-06, C-CRD-07).
   - (a) on an enemy country bordering one of the raider's own, with 2 or more armies: it loses half,
     rounded down, at most 10; a Shield cancels it automatically; (b) as (a), but on any enemy
     country, anywhere; (c) as the predecessor: any enemy country, its stack replaced by a random 1 to
     half, no cap.
   - Recommendation (a): a raid next to the raider sets up an attack the same turn, and the cap keeps
     one card from undoing several turns of building.
   - **Decided: (c), against the recommendation.** Read in full as the predecessor's raid: a set of
     three Raid cards ([Reconciled with T50](#reconciled-with-t50), item 7). The Shield is unchanged.
6. **V6. An eliminated seat's cards** (no claim in this file; the question core-rules.md left to T51).
   - (a) discarded; (b) taken by the seat that eliminated it, which may trade at once; (c) taken by
     that seat up to the hand limit, the rest discarded.
   - Recommendation (a): taking a beaten seat's cards is the classic runaway.
   - **Decided: (a).**
7. **V7. Production centres** (C-CEN-01, C-CEN-02, C-CEN-03, C-CEN-04, C-CEN-05, C-HAZ-08).
   - (a) no centres, and no harvest event; promises nothing to place. (b) one centre per seat, paying
     1 army a turn, never moved, the harvest adding 3; placed in tiers (one per seat always, apart and
     on different islands whenever a placement allows). (c) three centres drawn uniformly as three
     distinct countries anywhere, paying nothing; the harvest doubles each centre's stack, adding at
     most 10, and a further event moves all three; promises only three distinct countries.
   - Recommendation (b): a home to defend for each seat, at a size that never decides a game.
   - **Decided: (c), against the recommendation.**
   - **Proposed amendment to core-rules.md**: in [The deal](core-rules.md#the-deal), "Production
     centres ... are placed after step 5" becomes a step 6 that draws three distinct countries
     uniformly as centres. The pool formula is unchanged.
8. **V8. The kinds of event and their sizes** (C-HAZ-01, C-HAZ-04, C-HAZ-05, C-HAZ-06).
   - (a) a small storm (up to 3 countries, each losing half, at most 5), a small revolt (1 to 3
     armies), and a harvest; (b) storm and harvest only: no event changes an owner; (c) the
     predecessor's set and sizes: a storm leaves each struck stack at most half less one, with no cap,
     and a revolt can turn any country, whatever its armies.
   - Recommendation (a): three kinds, each small, give surprise without a decider.
   - **Decided: (c), against the recommendation.** The kinds are storm, revolt, harvest and shift,
     weighted 4, 2, 6 and 2 of 14, read onto the generated board as in
     [Reconciled with T50](#reconciled-with-t50).
9. **V9. Event frequency** (C-HAZ-03).
   - (a) Off / Rare 1 in 32 / Normal 1 in 16 / Often 1 in 8 per eligible turn change, Normal by
     default; (b) the same settings, Rare by default; (c) one draw per round instead of per turn
     change, with the same expected rate.
   - Recommendation (a): about four events in a 20-round game, close to what the owner saw of the
     predecessor.
   - **Decided: the predecessor's rates, an option beside the three offered:** Off / Rare 1 in 21 /
     Normal 1 in 14 / Often 1 in 8, Normal by default, never two in a row.
   - **Proposed amendment to core-rules.md**: the [Options](core-rules.md#options) row "Event
     frequency" reads: Off, Rare, Normal, Often; default Normal.
10. **V10. Tuning the island bonus constants** (C-BON-02; the owner's decision 12 in core-rules.md).
    - (a) keep decision 12 as it is: totals 34 to 46 over the admissible entrance vectors; (b) halve
      the entrance term, rounded per island: totals 28 to 34; (c) keep (a) and add a fairness check on
      the board's total (a band inside 34 to 46).
    - Recommendation (a): the owner chose it on 2026-10-12, and its total is only a model until
      play-tests.
    - **Decided: (a).** No amendment.
11. **V11. A draw into a full hand** (C-CRD-04).
    - (a) draw first, then discard any one of six; (b) discard first, as the predecessor, without
      seeing the new card; (c) no draw for a seat with five cards.
    - Recommendation (a): the seat decides with all the facts.
    - **Decided: (b), against the recommendation.** A small gamble, and a reason to trade before the
      hand fills.
12. **V12. Events near the end of a round-limit game** (C-HAZ-03, C-HAZ-07).
    - (a) when the round limit is on, no events in the last 3 rounds; (b) the same, in the last 5
      rounds; (c) no events in the last 5 rounds while the two seats with the most countries are within
      4 countries of each other.
    - Recommendation (a): every seat keeps at least three turns after the last event, and the rule is
      fixed and visible.
    - **Decided: (a).**
    - **Proposed amendment to core-rules.md**: in [Victory](core-rules.md#victory), the sentence on
      events not drawn near a win gains "and, when the round limit is on, in its last 3 rounds".

The three proposed amendments to core-rules.md (V7, V9, V12; the turn's cards phase needs none,
since a raid is a set) are for the main session to apply on `main`.

## Decisions, claim by claim

One row per in-scope spec claim (23). `keep` serves fun or balance as it is; `change` alters it;
`replace` swaps in a different rule; `drop` removes it. No row is `open`: the owner decided every
choice on 2026-10-12.

| Claim | Decision | malpaco's rule | Why |
| --- | --- | --- | --- |
| C-CRD-01 | keep | [The kinds](#the-kinds): eight kinds in the same roles (three army sets, a doubling set, a raid set, a Wild, a Shield, a hand-emptying card), names of malpaco's own; hands of five, empty at game start (V2 to V5) | The owner chose the predecessor's roles for surprise (V2 to V5); the card screen is T52's. |
| C-CRD-02 | replace | [The deck](#the-deck): a finite 40-card deck of malpaco's own composition, shuffled from the seed, discards reshuffled (V1) | A fixed list never shuffled is the same sequence of chances every game; a shuffled deck gives a new order each game, limits streaks and can be counted. |
| C-CRD-03 | change | [Earning a card](#earning-a-card): one card per capturing turn for every seat, never cancelled | Kept: a card for a turn with a capture. Changed: the failed-attack cancel belonged to the forfeit, dropped in core-rules.md (decision 7). |
| C-CRD-04 | change | [The hand](#the-hand): limit five; discard one of five before drawing (V11); the Squall empties the hand (V4) | Kept: the limit, the discard before the draw and the hand-emptying card, as the owner chose. Changed: every seat chooses its discard; the computer's fixed priority goes. |
| C-CRD-05 | change | [Trade-ins](#trade-ins): one optional set per turn; three of a kind, up to two Wilds; 5, 8 or 15 armies, a doubled pool, or a raid (V2, V3) | Kept: the predecessor's set rule and values, as the owner chose. Changed: every seat may skip, and the computer's fixed priority and uncapped Wild use go. |
| C-CRD-06 | change | [The raid](#the-raid-and-the-shield): three Raids replace any enemy stack with 1 to half (V5) | Kept: the predecessor's effect and reach, as the owner chose. Changed: one targeting rule for every seat; the computer's mis-indexed comparison goes and its choice is T53's. |
| C-CRD-07 | change | [The shield](#the-raid-and-the-shield): a Shield cancels one raid automatically and is discarded, with no other effect | Kept: a held defence that cancels one raid. Changed: the side effect on the raider's hand was a defect, not a rule. |
| C-BON-01 | keep | [Island bonuses](#island-bonuses): every country of an island needed; complete islands add up | Holding a whole island is a clear goal, and a partial island paying nothing makes entrances worth fighting over. |
| C-BON-02 | replace | [Island bonuses](#island-bonuses): `floor(size / 2) + entrances`, at least 2, no island above its size (core-rules.md decision 12; V10) | Hand-written values fit one fixed map; a generated board needs a rule, and this one pays more for islands that are harder to hold (the owner's decision 12). |
| C-BON-03 | replace | [Island bonuses on a generated board](#island-bonuses-on-a-generated-board): a new board each game under core-rules.md's invariants and fairness checks | One fixed board is the same game every time; the owner chose a generated board (core-rules.md decision 1), whose checks keep bonuses comparable. |
| C-CEN-01 | keep | [Production centres](#production-centres): three distinct countries drawn uniformly after the deal (V7) | The owner chose the predecessor's three random centres (V7); a uniform draw of three distinct countries is the same distribution on the generated board. |
| C-CEN-02 | change | [Production centres](#production-centres): no income; the harvest doubles each centre's stack, adding at most 10 (V7) | Kept: centres pay nothing per turn and the harvest doubles. Changed: the gain is capped at 10 per centre instead of a stored cap of 999, as V7 offered, since T50 has no stack cap. |
| C-CEN-03 | keep | [Production centres](#production-centres): the shift draws all three again, the same way (V7) | The owner chose the moving centres (V7): holding them is a gamble on the next harvest. |
| C-CEN-04 | keep | [Production centres](#production-centres): no spacing, island or owner condition (V7) | Part of the predecessor's centres as the owner chose them (V7); the luck of placement is the surprise. |
| C-CEN-05 | change | [Production centres](#production-centres): a centre belongs to whoever owns its country, survives capture, and is marked for every seat | Kept: capturing a centre takes it. Changed: the predecessor's computer-only use of the list goes; every seat sees the centres, and the computer's valuation is T53's. |
| C-HAZ-01 | change | [Events](#events): storm, revolt, shift and harvest, weights 4, 2, 2, 6 of 14; a repeat redrawn once (V8) | Kept: the predecessor's kinds, weights and redraw, as the owner chose. Changed: earthquake and flood were one effect under two names, so they are one kind with their two weights together. |
| C-HAZ-02 | change | [When an event is drawn](#when-an-event-is-drawn): one eligibility rule at every turn change, for every seat | Kept: one dispatch and one set of effects for every seat. Changed: no route that depends on human seats can pre-empt a draw, so events are seat-blind. |
| C-HAZ-03 | change | [When an event is drawn](#when-an-event-is-drawn): 1 in 21, 14 or 8 by setting, Normal default; none in round 1, near a win, in a round-limit game's last 3 rounds, or right after an event (V9, V12) | Kept: the predecessor's rates and cooldown, as the owner chose. Changed: the pauses follow malpaco's rules (round 1 and the near-win pause of core-rules.md, and V12). |
| C-HAZ-04 | change | [Storm](#the-kinds-of-event): a connected group of 3 or 4 countries around a drawn country (V8) | Kept: 3 or 4 countries struck. Changed: consecutive numbers mean nothing on a generated board, so the group is connected; the first-country exception was an artefact. |
| C-HAZ-05 | keep | [Storm](#the-kinds-of-event): each struck stack keeps a uniform 1 to half minus one (above 6) or to one less (1 to 6), at least 1 (V8) | The owner chose the predecessor's sizes (V8); the floor of 1 keeps T50's protection. |
| C-HAZ-06 | change | [Revolt](#the-kinds-of-event): a seat drawn by equal lot among those with 3 or more countries loses one border country, with its armies, to a bordering seat (V8) | Kept: the predecessor's eligibility, equal lot and unchanged armies. Changed: the receiving seat is defined (a bordering seat), and the country draw is a uniform draw instead of an eight-try search. |
| C-HAZ-07 | keep | [What no event does](#what-no-event-does): no stack to 0, no elimination, no centre removed, no seat targeted | The floor keeps events a surprise and never a decider by themselves, the owner's direction and T50's protection. |
| C-HAZ-08 | change | [Harvest](#the-kinds-of-event): doubling each centre's stack, adding at most 10, whoever owns it; how the computer values centres is T53's | Kept: the harvest helps whoever holds the centres, with no behind-player test. Changed: the gain is capped; the computer's use of centres in its moves is its policy (T53), not a rule. |
