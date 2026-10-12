# malpaco user interface

What a player of malpaco sees, hears and touches: the screens from launch to the result, the board,
the turn, combat, cards, events, the computer's turns, the standings and the log, sound and input. It
is written so that a TypeScript implementer can build the first UI, the **canonical** one, without
reading the evidence. It presents the rules of [core-rules.md](core-rules.md) (T50),
[variety.md](variety.md) (T51) and [computer.md](computer.md) (T53) as decided; it never changes a
rule. Where presenting a rule well would need a rule change, the change is a proposed amendment in
[Choices for the owner](#choices-for-the-owner).

This is a set of **requirements and testable properties**, not a mockup. It says what each screen
must show and allow, and how an automated check can tell that it does. Layout, pixels, art and sound
design are malpaco's implementer's and the owner's: every call that changes the look or the feel is a
choice for the owner (UI1 to UI18), with options, a recommendation and a reason. Where the text below
depends on such a call, it describes the recommended option and names the choice, *(UI<n>)*; the
owner's decision replaces it. Build every value behind a named constant (the names in capitals).
Numbers that are malpaco's own proposals say so; none is a measurement of the predecessor.

The bar is twofold (the owner's aim, 2026-10-02, and `questions/malpaco.md`, "User interface"): a UI
at least as good as the predecessor's, and one that clears the 19 weaknesses malpaco's proof of
concept recorded, UW-1 to UW-19. The predecessor is described here only in our own words, from the
UI catalogue of its screens, its control layout and the owner's recorded sittings; no screen text,
label, image or layout of it is used (rule 18). [At least as good, argued](#at-least-as-good-argued)
takes the weaknesses one by one; the [decision table](#decisions-question-by-question) gives one row
per UI spec claim and per UI question.

## Terms

Terms of the three rule files (seat, country, island, border, stack, turn, round, card, set, centre,
event, level, view) hold here.

- **Screen**: one full view with its own name (the start screen, setup, the board, the result).
- **Panel**: a part of the board screen (the phase bar, the standings, the hand, the log, the action
  panel).
- **Step**: one shown change of the board, held long enough to be seen, at the speed setting.
- **Active seat**: the seat whose turn it is. **Viewer**: the human seat whose private information
  (its hand) the screen may show; there is at most one at a time.
- **Owner cue**: what shows a country's owner besides colour *(UI3)*.
- **Speed**: the presentation setting Slow, Normal, Fast or Instant ([Pacing](#pacing)).

## Principles

Every screen obeys these. A screen that breaks one is a bug, whatever it looks like.

1. **The state is on the screen.** Everything a seat may know is visible or one action away: every
   owner and stack, the centres, the round, the phase, every seat's hand count, the viewer's own hand,
   the piles' counts and the top of the discard pile *(UI9)*, the standings and the history in the log. What
   no seat may know (another hand's kinds, the draw pile's order) is never shown, to anyone.
2. **What is legal is offered; what is illegal is explained.** Controls and countries that can act
   now are marked as such; an attempt at anything else changes nothing and says why
   ([Legal and illegal actions](#legal-and-illegal-actions)).
3. **Presentation never changes play.** Speed, animations, sound, fast-forward and every UI setting
   change only what is shown and when. The same settings, seed and actions give the same game at every
   speed (core-rules.md, Randomness; computer.md, Quick turns).
4. **No information by colour, hover or sound alone.** Ownership has a second cue; every hover effect
   has a click or key equivalent that shows the same; every sound has a visual counterpart.
5. **A switched-off feature leaves no trace** ([Disabled features](#disabled-features-leave-no-trace)).
6. **Every screen can be checked by a machine** ([Testability](#testability)).

## Screens and flow

### The screens

| Screen | What it must show and allow |
| --- | --- |
| Start | play at once with the last settings; a new game (to setup); continue the saved game, only when one exists; rules and help; presentation settings; the record |
| Setup | every option of T50, T51 and T53 on one screen, with its default, a one-line explanation and the resulting starting shares; start the game; back |
| Board | the board and its panels ([The board](#the-board), [The turn](#the-turn)); a menu with save, resign, settings, help and leave |
| Hand-over | only in hot-seat games: which seat plays next, with the private panels covered ([Hot-seat hand-over](#hot-seat-hand-over)) |
| Result | who won and how, the standings, the seed and settings, the record's change; play again, new setup, start |
| Help | the rules in malpaco's words, reachable from every screen, opened at the part that fits the current phase |
| Settings | speed, sound volumes and mute, palette, reduced motion, hints; reachable from every screen, also during a game |
| Record | wins and losses grouped as the stored record groups them (seat count, human share, the computer seats' levels) |

There is no locked option, no registration notice and no unregistered-copy marking on any screen
(core-rules.md, Options).

### From launch to the first move

- **One action to a game.** The start screen's first control starts a game at once with the last
  settings (on a first launch, the defaults: four seats, seat 1 human, three Normal computers, a
  random seed). Launch, one action, and the board is up with the first turn under way. A first-time
  player is never asked to read setup before playing (UW-7).
- **Two actions to a chosen game.** New game, change any option, start: setup needs one action to
  enter and one to start, plus the changes made.
- **Requirement for the first launch:** the start screen is interactive within `START_READY`
  seconds (2 proposed) on the reference machine, with no splash that must be waited out or clicked
  away. The predecessor took about 6.5 s from launch to its title, then two clicks to the board
  (`findings/F020-pro-ui-observations.md`, Q-UI-10; `walkthroughs/coordinates.md`).
- **Hints** *(UI12)*: in a player's first games, each phase shows one short hint the first time it
  comes, dismissed by any action and switched off in settings.

### Setup

All on one screen, in this order, each with its default shown and an explanation readable without
hover:

| Control | Values (from the rule files) | Shown when |
| --- | --- | --- |
| Seats | 2, 3 or 4; each human or computer (core-rules.md, Options) | always |
| Name | an optional name per human seat, for hot-seat play | the seat is human |
| Level | Easy, Normal or Hard, per computer seat, default Normal (computer.md, A1 to A3) | the seat is a computer |
| Human share | −4 to +4 countries per human seat, default 0 (core-rules.md, decision 6) | the game has at least one human and one computer seat |
| Starting armies per country | 1–2, 1–3, 1–4, default 1–3 | always |
| Event frequency | Off, Rare, Normal, Often, default Normal (variety.md, V9) | always |
| Domination win | on or off, default on; the threshold is shown (35 of 46) | always |
| Round limit | off, 20, 30 or 40, default off | always |
| Seed | random (drawn and shown) or typed; a control to copy it | always |
| Speed and sound | a link to the presentation settings; they never change a rule | always |

- **The resulting shares.** Setup shows each seat's starting country count as the deal's step 2
  computes it from the current settings and seed (the first seat comes from the seed), so a share
  setting shows its effect, including a transfer the rule skips because a computer seat would fall
  below 3. Changing a setting updates the counts at once.
- **The board preview.** Setup shows the board the current seed and settings generate, small, with
  island outlines and bonuses. A new seed gives a new preview. It shows the board only, not the deal.
- **The last settings** are restored at start (core-rules.md, Stored files); a control resets every
  option to its default. A settings file that fails validation is ignored and the player is told once.
- **Starting** a game while another is unfinished asks for confirmation and states the consequence
  under the saving rule *(UI14)*.

### Saving and loading

*(UI14; core-rules.md, decision 2.)* One save slot.

- **Save** is in the board's menu, available whenever a human seat is to act; it stores settings,
  seed and action list and says so. **Continue** on the start screen restores the slot by replay and
  opens the board at the saved point, with the log intact.
- **Recommended (UI14 c):** the game is also saved automatically at the end of every turn, so a crash
  or a closed window never loses a game, and overwriting the slot while it holds an unfinished game
  records a loss for that game's human seats, as resigning does (a proposed amendment to core-rules.md,
  in UI14). The confirmation before an overwrite says so.
- Loading never re-rolls anything: the restored game continues exactly as it would have.

### The end and result screen

- **The moment of the end.** When the victory check ends the game, the board stays visible with the
  final move shown, and a notice names the winner and how: total conquest, last seat standing,
  domination (with the count, for example 35 of 46), the round limit (with the tie-break used, if
  any), or every human eliminated. One action opens the result screen.
- **Every human eliminated** (core-rules.md, Victory, 5): the notice says the game is lost for the
  humans and offers two choices: watch the computers finish (at the current speed, with a control to
  jump to the end) or see the result now. Either way the record already holds the loss.
- **The result screen** shows: the winner with its colour and owner cue; every seat's final countries,
  armies, cards held and the round it was eliminated, ordered by finish; the number of rounds; the
  seed and the settings, with a control to copy them; the record's change for this setup, already
  updated when the screen appears. Actions: play again with the same settings and a new seed; replay
  the same seed; new setup; start screen.
- **Resigning** (core-rules.md, Leaving a game) is in the board's menu at all times for a human seat.
  Its confirmation states that it records a loss, and that the seat is then played by the computer
  if another human remains, at the level named in UI18, or that the game ends.

## The board

The board is drawn from the generated board's data: countries, islands, borders and positions
(core-rules.md, The board). Positions are display data; the layout never changes a rule.

### Ownership

- **Two cues, always** (UW-1, UW-3). A country shows its owner by colour **and** by the owner cue
  *(UI3; recommended: the shape of the badge that holds the army count, one shape per seat)*. With
  colour removed entirely (greyscale), every country's owner can be read from the cue alone.
- **The palette** *(UI2)*: one colour per seat for up to four seats. Under simulated deuteranopia,
  protanopia and tritanopia (Machado, Oliveira and Fernandes 2009, full severity), and with normal
  vision, no two seat colours are closer than `MIN_SEAT_DELTA_E` in CIEDE2000 (15 proposed: four
  colours of the published Okabe–Ito colour-blind-safe set reach about 20 under this check, as
  [the palette check](#the-palette-check) computes, so 15 leaves the art direction room). Greyscale
  is carried by the cue, not by the palette. A high-contrast palette is a setting (UI2 b).
- **The same seat looks the same everywhere**: on the board, in the standings, the log, the phase
  bar, the hand-over and the result, by the same colour and cue.
- **Change of owner** is shown as it happens: the country changes colour and cue in one visible step
  with a capture effect ([Combat feedback](#combat-feedback)), and the log records it.

### Army counts

- **Every country shows its stack** as a number in its badge, readable at a glance: at least
  `COUNT_TEXT_MIN` (14 px proposed) high at the smallest supported window, with a contrast of at least
  4.5 to 1 against the badge (the WCAG 2.x minimum for text), for every seat colour.
- **No stack cap** (core-rules.md, Reinforcement): counts up to 999 show in full; larger ones show
  compactly (for example 1.2k) within the same badge, and the exact count is shown on selecting the
  country and in every battle panel.
- **Changes are visible**: a count that changes steps or tweens to its new value, and the change
  (for example −3 or +5) shows beside the badge for a moment and is in the log.

### Islands and bonuses

- Each island is drawn as one landmass, distinct from the sea; borders between countries of an
  island are lines; borders crossing between islands are drawn as sea links, so the entrances that
  hold an island can be read off the map.
- **Each island shows its bonus** (core-rules.md, Island bonuses) as a number placed on or beside it.
  An island held completely by one seat shows that seat's colour and cue on its outline or label, so
  a held bonus reads at a glance, and the standings list it.
- Selecting an island (its label) shows its countries, bonus, entrances and who holds how many.

### Centres

- **A centre is marked** by a symbol that is the same for every owner and is neither a colour nor an
  owner cue *(UI4)*, visible at the smallest size, with a contrast of at least 3 to 1 against every
  seat colour (the WCAG 2.x minimum for graphics). Selecting a centre shows what a harvest would add
  to it now (its stack, at most 10; variety.md, Production centres).
- With events Off, centres do nothing; the recommended option hides their marks then *(UI17)*.

### Legibility and size

- **Smallest supported window** *(UI13; recommended 800 by 540 CSS pixels, desktop and tablet in
  landscape)*: the whole board fits with every panel collapsed to its compact form, and every property
  in this section holds there.
- **Hit areas.** Every country has a hit area at least `HIT_MIN` (40 CSS px proposed, near common
  platform touch guidance) in each direction at the smallest window, and hit areas do not overlap.
  46 such areas need 73,600 square px, a fifth of an 800 by 460 board area (the window less 80 px of
  compact panels, an assumed split), so the property is geometrically possible; meeting it for every
  generated board needs spaced positions *(UI15)*.
- **Nothing overlaps**: no badge, bonus label, centre mark or highlight covers another country's
  badge, at any supported size.
- A country is identified in the log and on selection by a short label of malpaco's own, derived
  from its island; its form is part of the art direction *(UI1)*.

### Resolution independence

- The board and every panel are drawn so that they stay sharp at any size and pixel density (vector
  shapes, text at device resolution).
- A window resize **reframes**: the board scales to fit the space left by the panels, keeping its
  aspect, never cropped and never needing scrolling; panels change between full and compact forms at
  named widths. A resize during a battle or a computer turn changes nothing in play.
- Below the smallest supported window the game shows a message asking for a larger window instead of
  a broken layout.

### The look

*(UI1, the owner's call.)* The recommended direction is a clean sea chart: islands with drawn
coastlines, flat seat fills, a light texture, thin borders and sea links, so the board reads as a
place and not as a form over a map (UW-18), while every property above holds. Art assets are out of
scope here.

## The turn

### The phase bar

- Always visible on the board screen: the active seat (colour, cue, name or seat number, human or
  computer and its level) and the six phases of the turn, income, cards, placement, attacks, move and
  end (core-rules.md, The turn), with the current phase marked and the remaining action stated in
  words (for example "place 7 armies", "attack or end attacks", "move once or end the turn").
- **Advancing**: one primary control per phase, always in the same place, named by what it does
  (confirm placement, end attacks, end turn without moving). Ending the turn with an attack still
  possible needs no confirmation; ending placement is impossible until the pool is placed.
- **The cards phase** is shown as passed, with a note, when the seat holds no set; it needs no action.
- The phase bar shows the computer's phases too, during its turns.

### Income and placement

- At the start of a human turn, the pool and its parts are shown: the country part with its count,
  each completely held island with its bonus, and a traded set's armies once traded
  (core-rules.md, Reinforcement).
- **Placing**: a click or tap on an own country adds armies from the pool, in an amount chosen beside
  the pool (1, 5 or all that remain); a key does the same for the selected country. Armies placed this
  phase can be taken back until the placement is confirmed; the confirmed placement is recorded as
  the turn's actions. The pool left is always shown.
- Confirm is enabled only when the pool is 0 (the whole pool is placed).

### Attacks

- **Choosing a battle**: own countries that can attack (at least 2 armies and an enemy neighbour) are
  marked; selecting one marks its enemy neighbours as targets. Other countries are dimmed, not hidden.
- **The odds** *(UI10)*: on choosing a target, the chance to capture if the battle is fought to the
  end, from core-rules.md's exact model with ties re-rolled, is shown beside it: the same public
  arithmetic the computer uses (computer.md, Terms).
- **The battle panel** opens: both stacks in full numbers, the controls of
  [Combat feedback](#combat-feedback), and stop. There is no limit on battles (core-rules.md, Combat).
- After a capture the move-in comes first ([below](#move-in-after-a-capture)); then the seat may start
  another battle, from any country, including the one just captured.

### Move-in after a capture

- A counter opens at the default, **all but one** of the attacker's remaining armies (core-rules.md,
  Ownership change), with controls for 1, one fewer, one more, all but one, and confirm; a number can
  be typed. The range (1 to all but one) is shown. When the attacker has exactly 2 armies the only
  move-in is 1 and the counter confirms it in one action.

### The move and the end of the turn

- A move control starts the move: own countries that can be a source (at least 2 armies and an own
  neighbour) are marked; then the own neighbours of the chosen source; then the counter, default all
  but one (core-rules.md, Movement). The confirm control says that the move ends the turn. Cancel
  returns to the attack phase with nothing changed.
- **End of turn**: a capturing turn draws its card first ([Cards](#cards)), then the victory check
  runs; the next seat's turn begins after any event at the turn change
  ([Events and centres](#events-and-centres)).

### Legal and illegal actions

*(UW-6.)* Illegal actions are not offered: their controls are disabled and their countries are not
marked. When one is tried anyway (a click on an unmarked country, a disabled control, a key), the
state does not change, a short reason appears next to where it was tried, the refusal sound plays
once, and the legal choices are marked again. The reasons cover at least:

| Attempt | Reason shown (in malpaco's words) |
| --- | --- |
| attack from a country with 1 army | an attack needs at least 2 armies |
| attack an own country, or one that is not a neighbour | the target must be an enemy neighbour |
| place on an enemy country | armies are placed on own countries |
| end placement with armies left | the whole pool must be placed, with the number left |
| move from a 1-army country, or to a non-neighbour or enemy country | the move rule that fails |
| trade three cards that are no set, or three Wilds | what a set is, and what is missing |
| trade a second set | one set per turn |
| any action outside its phase | which phase allows it |
| any action during another seat's turn | whose turn it is |

### Hot-seat hand-over

*(UI8; core-rules.md, decision 3.)* In a game with two or more human seats:

- Whenever the next human seat to act differs from the viewer whose hand was last shown, a hand-over
  screen appears before that seat's turn: it names the seat (colour, cue, name) and covers every
  private panel (the hand, a drawn card, a discard prompt). The board, the standings and the log stay
  visible, because they are public. One action by the incoming player reveals its hand and starts its
  income.
- During a computer turn no hand is shown.
- Everything private to the outgoing seat (its end-of-turn draw, a discard before the draw) happens
  before the hand-over, while that seat is still the viewer. An event at the turn change is shown on
  the board before the hand-over screen, so both players see it.
- **Four humans, no computer**: the hand-over appears at every turn change (four per round); the
  setup hides the share and level controls, which the rules ignore then.
- With one human seat, no hand-over appears: that seat is the viewer throughout.

## Combat feedback

*(UW-13; core-rules.md, Combat.)*

- **Dice**: each exchange shows both dice faces, attacker's and defender's, side by side in the seats'
  colours and cues, and which side lost an army.
- **Ties re-rolled, visibly**: a tie shows both equal faces, marked as a tie, and the re-roll follows
  as part of the same exchange, so a player sees that a tie favours no one. The battle panel keeps a
  tally: exchanges won by each side and ties re-rolled.
- **The exchange's result**: the losing stack's count steps down by one in the panel and on the board,
  with its sound.
- **Controls** *(UI5; recommended b)*: the main control fights on until the target is captured, the
  attacker is down to `N` armies, or the player stops, with `N` set beside it (default 2, remembered);
  a second control rolls a single exchange; stop ends the battle at once, at no cost. `N` runs from 1
  (fight to the end) to the attacking stack less one; a remembered value above that is lowered to it
  for the battle, so an attack from 2 armies fights to the end. At 1 army the battle stops by rule and
  the panel says so. The engine resolves exchanges one at a time either way.
- **Every stop is offered** (core-rules.md, Combat: the attacker may stop after every exchange). In
  the main control, each exchange is shown for `EXCHANGE_TIME` (0.4 s proposed at Normal; the
  predecessor's human exchanges came about 0.5 s apart, `runs/E018`), and the next exchange is resolved
  only after the previous one has been shown. Stop stays live throughout: pressed at any moment, it
  takes effect before the next exchange. The UI never resolves an exchange the player has not chosen
  to fight.
- **Long battles pause for a choice**: when a battle in the main control has run for
  `HUMAN_BATTLE_WATCH` (5 s proposed at Normal), it pauses, with the stacks and the tally, and waits
  for one of three choices: keep watching (another `HUMAN_BATTLE_WATCH`, with stop live as before),
  finish now (the rest of the battle, to a capture or `N` armies, in one step, with the tally), or
  stop. Finish now is the only way exchanges are resolved unseen, and only when the player picks it at
  the pause. A battle of 1000 against 100 with `N` = 1 shows 12 exchanges in 5 s at Normal, then
  pauses (at 1000 against 88 if the attacker won all 12); stop is offered there and after every
  further exchange the player chooses to watch, the 13th included.
- **At Instant** *(UI6)*, which the player chooses in settings, the main control runs the battle to its
  end (a capture or `N` armies) at once, with the last exchange's dice and the tally; the settings screen
  says so beside the Instant setting. The single-exchange control and stop are unchanged, so a player
  at Instant who wants to judge each exchange still can.
- **The capture**: the country changes colour and cue with a short effect *(UI16)* and its sound;
  the move-in counter follows.
- **Quitting** leaves both countries as they are; the panel and the log say "stopped" with the
  stacks as they stand.
- **Reduced motion** (a setting, every UI16 option): effects become instant changes with a highlight;
  nothing is lost.

## Cards

*(UW-12; variety.md, Cards.)* T51's cards are swingy by the owner's choice; each swing must be
visible as it happens and readable at a glance.

### The hand

- The viewer's hand is always on screen during its turn: up to five cards, each showing its kind by
  a picture and its name in malpaco's words, with a short effect line, and a counter of how many of
  the hand limit are used (for example 4 of 5).
- **Sets are found for the player**: the cards that make a set are marked as one group, with what it
  gives (5, 8 or 15 armies, the pool doubled with the amount, or a raid). Wilds in a set are shown
  standing for the kind.
- Shields show that they act by themselves; the hand never holds the Squall.

### Trade-ins

- In the cards phase, a seat holding a set sees a trade control on each set it can make, and skip.
  With several sets (they may share Wilds), each is offered separately and only one can be traded.
- Trading shows the three cards going face up to the discard pile and the pool rising by the set's
  value; a Surge set shows the pool doubling, with the added amount (variety.md, Trade-ins).
- A computer's trade is shown the same way, face up, as one step.

### The raid and the shield

- After a Raid set is traded, every enemy country is marked as a target; choosing one shows what the
  raid can do before it is confirmed: the stack becomes 1 to half of itself (for example 40 becomes 1
  to 20).
- **The result** is one step: the target's count drops to its new value with the loss shown, or, if
  its owner holds a Shield, a shield mark appears on the target, the Shield goes face up to the
  discard pile and the count stays. The log records either.

### The Squall

- When a seat draws the Squall, every seat sees it: the Squall and the drawer's whole hand go face up
  to the discard pile in one step, with the number of cards lost (variety.md, The hand). Drawn into an
  empty hand, it shows that nothing was lost.
- **An eliminated seat's hand** goes face up to the discard pile in the step that shows the
  elimination (variety.md, V6), and the log names the cards.

### A draw into a full hand

- When a capturing turn ends with five cards in the hand, a discard prompt opens before the draw
  (variety.md, V11): it says the hand is full, that one card must go before drawing, and that the new
  card is not seen first. The player picks any card; the discard goes face up. There is no skip.
- A computer's discard is shown face up, as one step, and logged.

### Drawing a card

- The drawn card is shown to its drawer only (the viewer); every other seat sees the hand count rise
  by one. A computer's draw shows only the count, unless it is the Squall.

### What is public

- Every seat's hand count, the draw pile's count and the discard pile's count are always shown; the
  top of the discard pile is shown face up *(UI9; recommended a)*. Every public card (traded, played,
  discarded, a Squall) is in the log. Another hand's kinds and the draw pile's order are never shown.

## Events and centres

*(UW-4; variety.md, Events and Production centres.)* Events happen only at a turn change, after the
victory check and before the next seat's income, never inside a turn.

- **Every event is shown on the countries it hits**, all at once, in one step: a banner names the
  event in malpaco's words, the hit countries are highlighted, and each shows its change.
  - **Storm**: the 3 or 4 struck countries are outlined as one group; each shows its count before
    and after.
  - **Revolt**: the country changes colour and cue from its old owner to the new one, with an arrow
    between their sides; the island bonus it breaks or completes is named.
  - **Harvest**: each of the three centres shows its gain (+n, at most 10).
  - **Shift**: the three old centre marks and the three new ones are shown together, linked, then the
    old ones fade.
- **How long**: the event step holds until the player acts or `EVENT_HOLD` passes (3 s proposed at
  Normal; the predecessor's event messages stayed about 6 to 7 s, `runs/E018`). At Instant it is not
  held. At every speed the hit countries keep a small mark until the next human turn begins, and the
  log records the event with every country and count.
- **Events and computer turns**: an event at the turn change after a computer turn is never part of
  that turn's watch budget or its fast-forward; it is shown at its own pace. A storm hitting three
  countries right after a fast-forwarded computer turn is therefore still shown, with its three
  before-and-after counts.
- **Paused events**: when events are on, the round counter shows when no event can come and why: round
  1, a seat within 4 countries of winning (31 of 46 with domination on, 42 with it off), or a
  round-limit game's last 3 rounds (core-rules.md, Victory; variety.md, V12).

## Computer turns

*(UW-10; computer.md, Quick turns, A6 and A17.)*

- **Who is playing**: the standings and the phase bar mark the active computer seat, with its level
  (Easy, Normal or Hard) beside it at all times (computer.md, A3).
- **What is shown**, step by step, within computer.md's bounds:

  | Step | At most a turn | What it shows |
  | --- | --- | --- |
  | trade-in | 1 | the three cards face up, the pool's change, a raid target and its result |
  | placement | 3 | each country that receives armies, with the number |
  | battle | 3 per battle, 10 battles | its start (both stacks, the target marked), the stacks part-way, its end with the tally, the capture and the move-in |
  | move | 1 | the source, the destination and the number |
  | discard | 1 | the discarded card face up |

  That is at most 1 + 3 + 30 + 1 + 1 = 36 steps (computer.md, Quick turns). A battle of 1000 against
  100 still takes 3 steps: 1000 against 100, the stacks part-way, the end. The end step's tally gives
  the exchanges each side won and the ties re-rolled.
- **Pacing** ([below](#pacing)): each step lasts `STEP_TIME`; a step that would end after
  `TURN_WATCH` seconds of the turn is not shown, and the rest of the turn is shown as one fast-forward
  step to its end state, with one log line per remaining action (A17). Play is unchanged.
- **Fast-forward by the player**: one control jumps the current computer turn to its end state, one
  step; a second shows every computer turn at Instant until a human seat is to act. Neither skips an
  event at a turn change, and both keep every log line.
- **Since your last turn**: when a human turn begins after computer turns, the countries that changed
  owner since that seat's last turn are marked until its first action, and a one-line summary
  (countries lost and gained, events) opens the log at that point.

### Pacing

*(UI6; recommended a.)* Speed is a presentation setting (core-rules.md, Options) that scales every
timing constant by one factor: Slow 1.5, Normal 1, Fast 0.5, Instant 0. It can be changed during a
game from the board.

| Constant | At Normal (proposed) | What it times |
| --- | --- | --- |
| `STEP_TIME` | 0.5 s | one step of a computer turn |
| `TURN_WATCH` | 15 s (computer.md's proposal) | a computer turn's watch budget |
| `EXCHANGE_TIME` | 0.4 s | one exchange of a human's battle |
| `HUMAN_BATTLE_WATCH` | 5 s | a human's battle before it pauses for the player's choice (keep watching, finish now, stop) |
| `EVENT_HOLD` | 3 s | an event step, unless the player acts first |

What follows at Normal, as arithmetic on computer.md's bounds:

- A turn with a trade, 3 placements, `B` battles, a move and a discard has 6 + 3B steps. 30 steps fit
  in 15 s at 0.5 s each, so every turn of up to 8 battles is shown whole; only a turn of 9 or 10
  battles reaches the budget.
- A turn of 2 battles with 3 placements and a move, and no trade or discard, is 10 steps: 5 s at
  Normal, 7.5 s at Slow. The predecessor's computer turns took 4.9 to 18.2 s at its slow speed, with
  a median of 7.6 s, in one of the owner's recorded games (`runs/E018`); over the four recorded games
  it made about 1.8 attacks a turn (computer.md, Quick turns).

## Information

### Standings

*(UW-5.)* Always visible on the board screen, in the compact form at the smallest window. One row per
seat, in turn order (so rows do not jump), each with:

- colour, owner cue, name or seat number, human or computer and its level;
- countries, with a bar towards the domination threshold (35 of 46) when domination is on;
- total armies, next turn's income, hand count, islands held, centres held (when centres are shown);
- a rank by countries, so who leads is read at once; an eliminated seat is greyed with the round it
  went out.

**The leader check** *(UI11; recommended a)*: a seat the computers' leader check names (computer.md,
The leader check: 28 or more countries, or an adjusted count of at least 22 and 1.5 times the next) is
marked in the standings, and selecting the mark gives the reason in words. A seat that the human share
settings gave or took countries at the deal shows that number, the handicap transfer the check
subtracts. The mark is seat-blind, as the check is: a human leader is marked too.

### The round counter

- Always visible: the round number; with the round limit on, "of 20" (or 30 or 40) beside it, and
  the last rounds counted down. The seat that plays first each round is marked in the standings.
- With events on, it carries the paused-events note of [Events and centres](#events-and-centres).

### The log

*(UW-11.)* A log of the whole game, kept for the game's length and restored with a saved game.

- One entry per public happening, of every seat: each round's start; a trade-in with its three cards;
  each placement; each battle's start and end with its tally, a capture and its move-in, a stop; a
  raid and its result or a Shield; the move; a card drawn (as a count, except to the drawer); a
  discard and a Squall with their cards; every event with every country and count; an elimination;
  the end. A fast-forwarded action has its line like any other.
- **Each entry names its countries** by their labels in the seat colours and cues; selecting an entry
  marks those countries on the board.
- The latest entries are visible on the board screen; the full log opens over the board and can be
  filtered by seat and by kind (battles, cards, events).
- The log never shows a hidden card's kind to anyone but its holder, and in hot-seat play never shows
  a drawn card's kind at all.

## Sound

*(UW-14; UI7.)* Requirements; the sounds themselves are art direction.

- **Every action and happening that matters has a sound**, distinct by kind: a control press, a
  refusal, a die roll, an exchange won and an exchange lost (from the attacker's side), a capture, an
  elimination, a card drawn, a set traded, a Surge, a raid landing, a Shield blocking, the Squall, each
  event kind, the turn coming to a human seat, a win and a loss.
- **Never the only carrier**: every sound has a visual counterpart on the screen.
- **No noise in bulk**: a grouped computer step plays one sound, a fast-forward step plays one summary
  sound, and the many exchanges of a long battle do not stack into a din (one roll sound per shown
  step).
- **Music** *(UI7)*: recommended off by default, with a setting to turn it on.
- **Controls**: a mute toggle reachable from every screen in one action (and a key), and separate
  volumes for effects and music; sound settings persist. With mute on, nothing plays.
- No sound plays before the player's first action in the session (browser autoplay rules).

## Input

*(UW-15.)*

- **Every action works by click or tap and by keyboard**, with no reliance on hover, double-click,
  right-click or drag. Hover may highlight what a click would do, never show anything a click or key
  cannot also show.
- **Hit areas** of `HIT_MIN` for countries ([Legibility and size](#legibility-and-size)) and for every
  control.
- **Keys** (named constants, listed in help): the phase's primary action (Enter or Space), cancel or
  back (Escape), cycle the marked countries forwards and back (Tab, Shift+Tab) and select one, the
  counters (arrow keys and typed numbers), roll one exchange, stop a battle, fast-forward a computer
  turn, open the log, mute, open help.
- **Touch** where the device has it: tap is a click; nothing needs a gesture beyond a tap; at the
  smallest window, panels open and close by tapping their headers.
- **Mistakes cost nothing before commit**: placement can be taken back until confirmed; a move or
  battle can be cancelled until its first roll or its confirm. A die is never re-rolled.

## Disabled features leave no trace

*(UW-19.)* A feature the setup switches off is absent from every screen, the log, the sounds and the
help shown in the game. An automated check runs a game with each off and finds none of its elements.

| Off | What is absent |
| --- | --- |
| Events (Off) | event banners, marks and sounds; the paused-events note; event entries and the event filter in the log; with UI17 (a), centre marks and centre columns, since centres then do nothing |
| Round limit (off) | "of N", the countdown and the quiet-rounds note; the tie-break text on the result screen |
| Domination (off) | the threshold bar and the 35 mark; the result screen's domination wording |
| Hot-seat (one human or none) | the hand-over screen and names other than the one human's |
| No computer seat | levels, the leader mark (no computer acts on it), the share controls |
| No human seat (watching) | the hand, hand-over, discard prompts and hints; resign; the record's change on the result screen |

Variant features (for example no centres, V7a) follow the same rule when a later version offers
them.

## Testability

*(UW-2.)* What an automated check can verify, so the gates can tell a blank screen from a working
one. malpaco's tests run in a pinned rendering environment.

- **Screen identity**: every screen and panel exposes a stable name and its state (screen, phase,
  active seat, viewer, speed) to the test harness, read from the rendered page, not from the engine.
- **The drawn board matches the engine**: for each country the harness reads back, from the rendered
  scene, its drawn owner (colour and cue), its count and its position, and compares them with the
  engine's state for the same seed and actions. A blank or half-drawn board fails at once.
- **Reference images**: for fixed seeds and actions, each screen at the smallest supported window and
  at one large size is compared with a reviewed reference image; a difference beyond a tolerance
  fails.
- **Properties computed from the scene**: every country's hit area at least `HIT_MIN` and no overlap;
  every count's text height and contrast; the palette's pairwise distance under the three simulations;
  ownership readable in greyscale (the cue's shapes differ); nothing drawn outside the window after
  resizes through the supported range.
- **Legal and illegal**: for scripted positions, the marked countries are exactly the legal ones, and
  each illegal attempt of the table above changes nothing and shows its reason.
- **Presentation never changes play**: one scripted game at every speed, with and without
  fast-forward and reduced motion, ends in the same state with the same action list.
- **Every stop offered**: in scripted human battles at every speed but Instant, no exchange is
  resolved before the previous one has been shown, unless the player picked finish now; a stop sent at
  any moment takes effect before the next exchange; a battle past `HUMAN_BATTLE_WATCH` waits at the
  pause until the player chooses.
- **Step bounds**: in many games of computers, no computer turn shows more than 36 steps or a battle
  more than 3, and the budget's fast-forward appears only past `TURN_WATCH`.
- **No trace**: the checks of [Disabled features](#disabled-features-leave-no-trace).
- **Privacy**: in a hot-seat game, no rendered element shows another seat's card kinds at any
  moment, including during the hand-over and computer turns.
- **Sound**: each sound event is emitted to a test hook with its kind; mute emits nothing audible;
  every sound kind has a visual counterpart in the same step.

## The palette check

Where `MIN_SEAT_DELTA_E`'s proposal comes from: the smallest CIEDE2000 distance between any two of
four colours, with normal vision and under each simulation, over every four of the seven coloured
entries of the Okabe–Ito set. The simulation matrices are Machado, Oliveira and Fernandes (2009) at
full severity, applied in linear RGB. A model of the check, not a chosen palette (UI2 is the owner's).
Shown as an indented block, with its output after it.

    import itertools, math
    import numpy as np
    SIM = {"normal": np.eye(3),
           "protan": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
           "deutan": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
           "tritan": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]])}
    def lin(c):
        c = np.array(c, float) / 255
        return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    def lab(rgb):
        xyz = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]) @ np.clip(rgb, 0, 1)
        t = xyz / np.array([0.95047, 1.0, 1.08883])
        f = np.where(t > (6 / 29) ** 3, np.cbrt(t), t / (3 * (6 / 29) ** 2) + 4 / 29)
        return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])
    def de00(p, q):                                   # CIEDE2000
        (L1, a1, b1), (L2, a2, b2) = p, q
        Cb = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
        G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
        a1, a2 = (1 + G) * a1, (1 + G) * a2
        C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
        h1, h2 = math.degrees(math.atan2(b1, a1)) % 360, math.degrees(math.atan2(b2, a2)) % 360
        dh = 0 if C1 * C2 == 0 else (h2 - h1 - 360 if h2 - h1 > 180 else h2 - h1 + 360 if h2 - h1 < -180 else h2 - h1)
        dH = 2 * math.sqrt(C1 * C2) * math.sin(math.radians(dh / 2))
        Lb, Cbp = (L1 + L2) / 2, (C1 + C2) / 2
        hb = h1 + h2 if C1 * C2 == 0 else (h1 + h2) / 2 if abs(h1 - h2) <= 180 else (h1 + h2 + 360) / 2 if h1 + h2 < 360 else (h1 + h2 - 360) / 2
        T = (1 - 0.17 * math.cos(math.radians(hb - 30)) + 0.24 * math.cos(math.radians(2 * hb))
             + 0.32 * math.cos(math.radians(3 * hb + 6)) - 0.20 * math.cos(math.radians(4 * hb - 63)))
        Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
        SL = 1 + 0.015 * (Lb - 50) ** 2 / math.sqrt(20 + (Lb - 50) ** 2)
        SC, SH = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
        RT = -math.sin(math.radians(60 * math.exp(-((hb - 275) / 25) ** 2))) * Rc
        dL, dC = L2 - L1, C2 - C1
        return math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH))
    OKABE_ITO = {"orange": (230, 159, 0), "sky blue": (86, 180, 233), "bluish green": (0, 158, 115), "yellow": (240, 228, 66),
                 "blue": (0, 114, 178), "vermillion": (213, 94, 0), "reddish purple": (204, 121, 167)}
    def worst(names):
        return {k: min(de00(lab(m @ lin(OKABE_ITO[x])), lab(m @ lin(OKABE_ITO[y]))) for x, y in itertools.combinations(names, 2))
                for k, m in SIM.items()}
    ranked = sorted(itertools.combinations(OKABE_ITO, 4), key=lambda n: -min(worst(n).values()))
    for names in ranked[:3]:
        print(names, {k: round(v, 1) for k, v in worst(names).items()})

Its output:

    ('sky blue', 'yellow', 'blue', 'vermillion') {'normal': 22.3, 'protan': 20.7, 'deutan': 22.5, 'tritan': 20.0}
    ('sky blue', 'yellow', 'vermillion', 'reddish purple') {'normal': 37.0, 'protan': 14.0, 'deutan': 15.7, 'tritan': 13.9}
    ('bluish green', 'yellow', 'vermillion', 'reddish purple') {'normal': 37.0, 'protan': 18.2, 'deutan': 15.9, 'tritan': 13.9}

- The best four of the set reaches about 20 in every condition (its smallest distance, 19.95 before
  rounding, is under tritanopia); the next fall to about 14. A threshold of 20 would rule out even
  that one; 15 admits it with margin and rules out the fours that the simulations bring within about
  14. A palette of malpaco's own may do better; the check is the same.
- A light colour (yellow, sky blue) needs dark count text and a dark one light text to keep the 4.5
  to 1 contrast of [Army counts](#army-counts); the badge's text colour follows the seat colour.

## Reconciled with T50, T51 and T53

Where presenting a decided rule needed a reading, the nearest consistent one was taken:

1. **The cards phase without a set** (core-rules.md, The turn). The phase exists for every seat; the
   UI passes it with a note when the seat holds no set, with no action needed.
2. **Card memory and the screen** (computer.md, A12). A computer's view is what a human in its seat
   could see and remember. If the screen showed the whole discard pile, Easy's "only what is on screen
   now" would equal Hard's memory; so the screen shows the discard pile's top and counts, and the log
   holds the history *(UI9)*.
3. **A resigned seat's level** (core-rules.md, Leaving a game). The rules turn a resigning seat over
   to the computer without naming a level; the UI needs one to show. UI18 proposes the default level,
   Normal (A2).
4. **Centres with events Off** (variety.md, V7 and V9). Centres act only through the harvest and the
   shift, both events; with events Off they do nothing, and marking them would leave a trace (UW-19).
   UI17 proposes hiding them, an amendment to variety.md's "marked for every seat".
5. **The overwrite of a saved unfinished game** (core-rules.md, decision 2 and Leaving a game).
   Starting a new game counts as resigning unless the game is saved first; but saving it and then
   saving the new game overwrites the one slot, so the first game is gone with no result recorded.
   UI14 proposes closing that gap.
6. **The computer's draw** (variety.md, The deck). Only the count is public; the UI shows the count's
   rise and nothing else, unless the card is the Squall, which every seat sees.

## At least as good, argued

For each recorded weakness: what the predecessor does (from its UI catalogue, control layout and the
owner's sittings), what malpaco's proof of concept had, and how this design meets or beats both.
Anything that falls short is named, with the choice that settles it.

| Weakness | The predecessor | The proof of concept | malpaco |
| --- | --- | --- | --- |
| UW-1 programmer art: flat colours, an initial, a dot | textured relief tiles in four tints, large outlined army digits, a centre shown only by a recoloured digit | flat colours, an owner initial, a gold dot | a drawn sea chart (UI1), colour plus an owner cue on every badge (UI3), a centre symbol that is neither colour nor cue (UI4): beats both |
| UW-2 a blank screen passes the gates | not applicable (no gates); its screens are catalogued as a reference | gates stayed green on a blank screen | screens named and read back from the rendered scene, reference images, scene-computed properties ([Testability](#testability)): meets the requirement |
| UW-3 colour-blind palette and a non-colour cue | four hues; three of them close in greyscale; no colour choice and no second cue | named as a need, not built | a palette checked under three simulations (UI2) and a cue that reads in greyscale (UI3): beats both |
| UW-4 events and centre moves perceivable | a typed message between turns, about 6 to 7 s, and by its code a flash on a centre; how the other events mark the map is not established | flash on the province, planned | every event shown on the countries it hits, before and after, with a lasting mark and a log line; shifts show old and new centres: beats both |
| UW-5 who is leading | a score box always shows each seat's countries and cards, in coloured names on black (weak contrast) | not built | standings with countries, armies, income, cards, islands, centres, a rank, the domination bar and the leader mark (UI11): beats both |
| UW-6 illegal actions not offered, reason shown | a click on an own country as a target was refused; whether legal targets are marked is not established | planned | legal choices marked, illegal ones disabled, every refusal with its reason ([table](#legal-and-illegal-actions)): beats both |
| UW-7 the start screen | about 6.5 s to the title, then two clicks to the board | a setup screen every player had to read | one action from the start screen to a game; setup in two actions plus changes; hints (UI12): beats both |
| UW-8 the result screen | a winner notice, then a scoreboard of wins and losses by level, whose new result appears about 2.3 s after it opens (`runs/E018`) | standings and the seed, planned | winner and how, full standings, seed and settings, the record already updated, play again or replay the seed: beats both |
| UW-9 phase bar, end turn, concede | a bottom panel with prompts, counters and a turn menu; no resign control (leaving through a new game) | planned | a phase bar with the remaining action in words, one primary control per phase, resign always in the menu: beats both |
| UW-10 computer turns presented | the computer places with no screen; its exchanges come about 0.2 s apart; turns 5 to 18 s at slow speed; a play-out after elimination ran in under 0.5 s with nothing to follow | all seats human | every placement, trade and battle shown within 36 steps, a watch budget, fast-forward, the level per seat, a since-your-last-turn summary: beats both. **Short of the predecessor in one way:** a large computer battle shows 3 steps, not its exchanges; the tally and the log carry the rest (A17, decided; UI6 sets the pace) |
| UW-11 the event log | none found | planned | a full, filterable log whose entries mark their countries: beats both |
| UW-12 the hand | a card screen after a capture and a hand screen of five slots behind a control; a set is offered to accept or decline | not built | the hand always on screen in its turn, sets found and grouped, every swing (Surge, raid, Shield, Squall, discard) shown as it happens: beats both |
| UW-13 juice | counts change in place; no dice shown; a capture flash; by its code, battles of large stacks resolve in batches of five | planned, not built | dice faces, visible re-rolled ties, stepped counts, a capture effect and sound; long battles pause for the player's choice, and stop is offered after every exchange (UI5, UI6, UI16): beats both |
| UW-14 audio | a sound on-off switch; its sounds are not established (the screen walks ran with no audio) | left to a later pass | a sound per kind of happening, music as a setting, mute and two volumes (UI7): meets the requirement; against the predecessor, beats its controls, and its sound content cannot be compared |
| UW-15 hit targets, no hover | mouse clicks; hover lights buttons, cosmetically; playing by keyboard is not established | named as a need | `HIT_MIN` areas, no hover reliance, full keyboard play, touch: beats both |
| UW-16 resolution independence | a fixed-size stage; it did not start at 640 by 480; whether it scales on larger desktops is not established | named as a need | vector drawing, reframing on resize, compact panels, a message below the minimum: beats both |
| UW-17 legibility | army digits clear on the tints; the score-box names and the centre digits are the weakest contrast | named as a need | measured text height and contrast for every seat colour, no overlaps, at the smallest window: beats both |
| UW-18 the board's look | a pleasant textured board, but a form-like set of panels below it | functional | a drawn sea chart with the panels kept small (UI1, the owner's call): meets the aim once the owner decides |
| UW-19 disabled features leave no trace | the only switchable feature, event frequency, is locked in the build studied, so its off state was not seen | a rule, not built | an absence table checked by automated games ([Disabled features](#disabled-features-leave-no-trace)): meets the requirement |

**The smallest window** (UI13): the recommended 800 by 540 is no larger than the predecessor's 800 by
600 stage in either direction, so malpaco runs wherever the predecessor's stage fits in width, and in
less height. Option (c), 1280 by 720, would fall short of the predecessor here.

## Choices for the owner

Every call that changes the look or the feel, and the one `open` row (Q-UI-21). Each has options, a
recommendation and a reason. The text above describes the recommended options; the owner's decisions
replace them. [variants.md](variants.md) keeps every option as a named variant.

1. **UI1. Art direction and the board's look** (Q-UI-21, `open`; UW-1, UW-18).
   - (a) a clean sea chart: islands with drawn coastlines, flat seat fills, a light texture, thin
     borders, sea links for crossings; (b) an illustrated, painted map with terrain; (c) an abstract
     diagram, countries as cells or nodes.
   - Recommendation (a): it reads as a place and stays legible, it is cheap to draw at any size, and it
     keeps colour free for the seats; (b) costs art and fights the counts for attention; (c) is legible
     but is the "form over a map" the proof of concept wanted to leave.
2. **UI2. The seat palette** (Q-UI-05; UW-3).
   - (a) one fixed palette of four hues that passes the three-simulation check; (b) as (a), plus a
     high-contrast palette as a setting; (c) each human picks from six checked colours, no two seats
     alike.
   - Recommendation (b): a fixed default keeps every screenshot and every game readable alike, and the
     high-contrast setting serves low vision; (c) adds a setup step and pairs to test.
3. **UI3. The owner cue** (Q-UI-01; UW-1, UW-3).
   - (a) the shape of the count's badge, one per seat (for example circle, square, triangle, diamond);
     (b) a fill pattern per seat (plain, stripes, dots, cross-hatch); (c) both.
   - Recommendation (a): it sits where the eye already reads the count and survives at the smallest
     size; patterns are noisy on small countries and under the count; (c) fits a high-contrast setting.
4. **UI4. The centre mark** (Q-UI-02).
   - (a) one symbol beside the count badge, the same for every owner; (b) a glow around the whole
     country; (c) as (a), with the next harvest's gain always printed on it.
   - Recommendation (a): small, owner-neutral and readable at any size, with the gain shown on
     selection; (b) competes with the ownership colour; (c) adds three more numbers to the board.
5. **UI5. A human's battle controls** (Q-UI-16; UW-13).
   - (a) the main control rolls one exchange, a second fights on to a capture or down to `N`; (b) the
     main control fights on to a capture or down to `N` (default 2, remembered), a second rolls one
     exchange; (c) as (b), with `N` defaulting to half the starting stack, rounded up. Every option
     keeps stop live after every exchange and the pause after `HUMAN_BATTLE_WATCH`
     ([Combat feedback](#combat-feedback)); none resolves an exchange the player has not chosen.
   - Recommendation (b): with large stacks (no cap) one click per exchange is tiring, and the owner's
     sittings of the predecessor show battles stopped at 2 or 3 armies (`runs/E018`), which `N` = 2
     serves; (c) stops early more often than most battles need.
6. **UI6. Pacing** (Q-UI-13, Q-UI-16; UW-10; A17's budget).
   - (a) Slow, Normal, Fast and Instant, scaling the constants of [Pacing](#pacing) by 1.5, 1, 0.5 and
     0, with `STEP_TIME` 0.5 s and `TURN_WATCH` 15 s at Normal; (b) the same with a quicker Normal,
     `STEP_TIME` 0.35 s and `TURN_WATCH` 10 s; (c) as (a) without Instant. In every option a human's
     long battle pauses for the player's choice instead of jumping; only at Instant, a setting the
     player picks, does the main battle control run to its end at once.
   - Recommendation (a): a typical computer turn takes about 5 s at Normal, close to the predecessor's
     at its slow speed, and every turn of up to 8 battles is shown whole; (b) shows a 2-battle turn in
     3.5 s, but 28 steps fit its 10 s budget, so turns of 8 battles or more (6 + 3 × 8 = 30 steps)
     are cut; (c) removes the choice of a game at full speed.
7. **UI7. Sound and music** (Q-UI-17; UW-14).
   - (a) effects on, music on at a low volume, by default; (b) effects on, music off by default; (c)
     effects only, no music at all.
   - Recommendation (b): a turn-based game is often played beside other audio, so music is an opt-in,
     while the effects carry feedback; (c) gives up a mood the owner may want.
8. **UI8. Hot-seat privacy** (Q-UI-15; core-rules.md decision 3).
   - (a) a hand-over screen covering the private panels whenever the next human differs from the last
     viewer; (b) the hand always hidden until its owner taps to show it, in every game; (c) no hiding.
   - Recommendation (a): privacy where it matters at the cost of one action per hand-over, and no cost
     with one human; (b) taxes the common single-player game; (c) breaks the rule that hands are hidden.
9. **UI9. What the discard pile shows** (Q-UI-15; computer.md A12).
   - (a) the top card and the counts, with every public card in the log; (b) a face-up summary of the
     whole discard pile by kind since the last reshuffle; (c) the top card and counts only, and no card
     kinds in the log.
   - Recommendation (a): it keeps A12's levels meaningful (a summary on screen would give Easy Hard's
     memory, since a computer's view is what the screen shows), while the log lets a careful human
     remember as Hard does; (c) leaves the human worse off than Hard.
10. **UI10. Showing the odds** (Q-UI-09, Q-UI-16).
    - (a) the capture chance on choosing a target; (b) on request only; (c) never.
    - Recommendation (a): the computer decides by the same public arithmetic, so showing it puts the
      human level with the computer and makes core-rules.md's "readable decision" literal; (c) hides
      what the rules call public.
11. **UI11. Showing the leader check** (Q-UI-08; UW-5; computer.md A5 and A16).
    - (a) a mark on any seat the check names, with the reason on selection; (b) the numbers only
      (counts and handicap transfers), the rule in help; (c) nothing beyond counts.
    - Recommendation (a): computer.md makes the computers' behaviour readable, and a player who sees
      the mark knows why the computers turn on the leader, human or not; (c) makes that turn look like
      ganging up.
12. **UI12. Helping a first game** (Q-UI-10; UW-7).
    - (a) one short hint per phase in a player's first games, dismissed by any action; (b) help screens
      only; (c) a guided tutorial game.
    - Recommendation (a): it costs no extra screen before play; (c) is a project of its own.
13. **UI13. The smallest window and platforms** (Q-UI-19, Q-UI-20; UW-16, UW-17).
    - (a) desktop and tablet in landscape, at 800 by 540 CSS px or more; (b) also phones in landscape,
      at 640 by 360, with panels as overlays; (c) desktop only, at 1280 by 720 or more.
    - Recommendation (a): no larger than the predecessor's stage in either direction, and the
      hit-area property is reachable there; (b) needs the board to fill the screen with panels over it,
      a layout of its own; (c) falls short of the predecessor's smallest stage.
14. **UI14. Saving** (core-rules.md decision 2 and Leaving a game; a proposed amendment).
    - (a) manual save only, as core-rules.md says, overwrites confirmed but recording nothing; (b)
      manual save, and overwriting the slot while it holds an unfinished game records a loss for its
      human seats; (c) as (b), plus an automatic save at the end of every turn.
    - Recommendation (c): no game is lost to a crash or a closed window, and no loss can be dodged by
      saving and starting over ([Reconciled](#reconciled-with-t50-t51-and-t53), item 5).
    - **Proposed amendment to core-rules.md** (for (b) and (c)): in [Leaving a game](core-rules.md#leaving-a-game),
      add "Overwriting the save slot while it holds an unfinished game records a loss for that game's
      human seats, as resigning does."
15. **UI15. Where country spacing is guaranteed** (UW-15, UW-17; a proposed amendment).
    - (a) the generator's positions keep every two countries' label points at least a set distance
      apart in its reference frame, so the hit areas fit at the smallest window; (b) the renderer
      spreads crowded positions itself at draw time, the generated positions unchanged.
    - Recommendation (a): the same seed then gives the same picture everywhere, and one test on the
      generator covers every screen; positions stay display data.
    - **Proposed amendment to core-rules.md** (for (a)): in [Generation](core-rules.md#generation),
      the requirements gain "positions keep every two countries at least `MIN_LABEL_GAP` apart in the
      reference frame; this is display data and no rule reads it".
16. **UI16. How lively** (Q-UI-16; UW-13).
    - (a) restrained: stepped counts, short tumbling dice, a capture pulse and sound, no screen shake;
      (b) full: also screen shake, particles and camera nudges; (c) minimal: instant changes with
      highlights.
    - Recommendation (a): satisfying without slowing a game of many battles; reduced motion is a
      setting in every option.
17. **UI17. Centres when events are Off** (UW-19; variety.md V7 and V9; a proposed amendment).
    - (a) not shown, since they do nothing without events; (b) shown anyway.
    - Recommendation (a): a mark that does nothing is a trace of a switched-off feature.
    - **Proposed amendment to variety.md** (for (a)): in [Production centres](variety.md#production-centres),
      "Centres are marked on the board for every seat" gains "while events are on". The deal still
      draws them, so the game stream is unchanged.
18. **UI18. The level of a resigned seat** (core-rules.md, Leaving a game).
    - (a) the default level, Normal (A2); (b) the level of the strongest computer seat in the game; (c)
      the resigning player picks it in the resign confirmation.
    - Recommendation (a): no extra question when leaving, and the default is the game the balance is
      tuned on; (c) adds a step to a moment that should be quick.

## Decisions, question by question

One row per UI spec claim (2) and per UI question of `questions/malpaco.md` (22). `keep` means malpaco
does as the predecessor does, and the row says why that works; `change` alters it; `replace` swaps in
something different; `drop` removes it; `open` waits for the owner (in
[Choices for the owner](#choices-for-the-owner)). The spec claim C-UI-02 is about the DOS game; rule
19 keeps it out of any reading of the Windows game, and its row says what that means for malpaco.

| Id | Decision | malpaco's design | What the predecessor does, and why |
| --- | --- | --- | --- |
| C-UI-01 | change | [Principles](#principles), [The board](#the-board), [Combat feedback](#combat-feedback): every owner, count, the active seat, the phase, the cards and each attack's result on screen, plus the dice, the log and the standings | Its screens show owners, counts, whose turn, the phase, the cards and an attack's result, but an attack shows counts before and after, not the dice; malpaco keeps the whole state on screen and adds the dice and history (UW-13, UW-11). |
| C-UI-02 | keep | [Principles](#principles): the state of play is on the screen | A DOS claim (rule 19): the same kinds of state on its screens. Nothing in the design rests on it; that the screen carries the whole state is kept because C-UI-01 shows it works for the predecessor too. |
| Q-UI-01 | change | [Ownership](#ownership): colour plus an owner cue on every country (UI3) | Four tints and no other cue; in greyscale three of them are hard to tell apart. A second cue makes ownership readable for every player (UW-1, UW-3). |
| Q-UI-02 | change | [Centres](#centres): an owner-neutral symbol with 3 to 1 contrast against every seat colour (UI4) | A centre is shown only by a recoloured army digit, one of the weakest contrasts on the board; a symbol is seen at a glance (UW-1). |
| Q-UI-03 | keep | [Army counts](#army-counts): a large count on every country, with text height and contrast measured; compact forms above 999 | Large outlined digits on every territory read clearly against the tints; that works, and malpaco keeps it, in the owner-cue badge and with no stack cap. |
| Q-UI-04 | change | [The screens](#the-screens), [Testability](#testability): eight named screens, each read back by the test harness | Nine screens were reached in a walk of its menus; malpaco names every screen and makes each machine-checkable, so a blank screen fails the gates (UW-2). |
| Q-UI-05 | change | [Ownership](#ownership): a palette checked under three colour-blind simulations, greyscale carried by the cue, a high-contrast setting (UI2) | Four fixed hues, no colour choice, no second cue; the check makes the palette safe by test (UW-3). |
| Q-UI-06 | change | [Events and centres](#events-and-centres): each event shown on the countries it hits, before and after, held, marked until the next human turn, logged | A typed message between turns, held about 6 to 7 s, with a flash; the hit countries are what a player needs to see (UW-4). |
| Q-UI-07 | change | [Events and centres](#events-and-centres): a shift shows the old and new centres together, linked, and is logged | A centre's move is announced by a message and a flash; showing old and new together lets a player tell where centres went (UW-4). |
| Q-UI-08 | change | [Standings](#standings): always-visible rows with countries, armies, income, cards, islands, centres, a rank, the domination bar and the leader mark (UI11) | A score box always shows each seat's countries and cards, in coloured names on black with weak contrast; malpaco keeps it always visible and adds what domination and the leader check read (UW-5). |
| Q-UI-09 | change | [Legal and illegal actions](#legal-and-illegal-actions): legal choices marked, illegal ones disabled, every refusal explained | A click on an own country as a target is refused; whether legal targets are marked is not established; offering the legal and explaining the illegal saves wasted clicks (UW-6). |
| Q-UI-10 | change | [From launch to the first move](#from-launch-to-the-first-move): one action from the start screen to a game; hints (UI12) | About 6.5 s to its title, then two clicks to the board; one action, and no setup to read first, beats it (UW-7). |
| Q-UI-11 | change | [The end and result screen](#the-end-and-result-screen): winner and how, full standings, seed and settings, the record already updated, play again | A winner notice, then a scoreboard of wins and losses by level whose new result appears about 2.3 s late, then the title; malpaco shows the whole result at once (UW-8). |
| Q-UI-12 | change | [The phase bar](#the-phase-bar): the active seat, six phases, the remaining action in words, one primary control per phase; resign in the menu | A bottom panel of prompts, counters and a turn menu, and no resign control; a phase bar makes the turn's shape visible (UW-9). |
| Q-UI-13 | change | [Computer turns](#computer-turns): placements, trades and battles shown within 36 steps and a watch budget, fast-forward, the level per seat (UI6) | The computer places with no screen and plays out a game in under half a second after the human's elimination; showing every decision within a budget makes computer turns followable (UW-10). |
| Q-UI-14 | replace | [The log](#the-log): a full, filterable log whose entries mark their countries | None found: only status texts; a log replaces them as the game's memory (UW-11). |
| Q-UI-15 | change | [Cards](#cards): the hand always on screen in its turn, sets found, every swing shown, hot-seat privacy (UI8, UI9) | A card screen after a capture, a hand of five slots behind a control, and an offer of a set to accept or decline; T51's swings need to be seen as they happen (UW-12). |
| Q-UI-16 | change | [Combat feedback](#combat-feedback): dice, visible re-rolled ties, stepped counts, a capture effect, stop after every exchange, long battles paused for the player's choice (UI5, UI6, UI16) | Counts change in place with no dice, about 0.5 s per exchange, and by its code battles of large stacks resolve in batches of five; malpaco shows why each army fell (UW-13). |
| Q-UI-17 | change | [Sound](#sound): a sound per kind of happening, never alone; music a setting; mute and two volumes (UI7) | A sound on-off switch; what it plays was not captured. malpaco makes sound part of the feedback and gives volume control (UW-14). |
| Q-UI-18 | change | [Input](#input): `HIT_MIN` hit areas, no hover reliance, full keyboard play, touch | Mouse clicks; hover only lights buttons; playing by keyboard is not established; malpaco serves keyboard and touch players (UW-15). |
| Q-UI-19 | replace | [Resolution independence](#resolution-independence): vector drawing, reframing on resize, compact panels, a message below the minimum (UI13) | A fixed-size stage that did not start at 640 by 480; a resolution-independent board replaces it (UW-16). |
| Q-UI-20 | change | [Legibility and size](#legibility-and-size), [Army counts](#army-counts): text height and contrast measured for every seat colour at the smallest window, no overlaps | Army digits are clear, but the score-box names and the centre digits are weak; malpaco tests every pair (UW-17). |
| Q-UI-21 | open | [The look](#the-look): recommended a clean sea chart (UI1) | Relief-textured tiles in four tints, with light straight lines across the sea between islands and form-like panels below; the board's look is the owner's call (UW-18). |
| Q-UI-22 | change | [Disabled features leave no trace](#disabled-features-leave-no-trace): an absence table, checked by automated games | The only switchable feature, event frequency, is locked in the build studied, so its off state is not known; malpaco states and tests the absence of every switched-off feature (UW-19). |
