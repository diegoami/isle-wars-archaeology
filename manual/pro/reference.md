# Isle Wars Pro rules and reference

Own-word Isle Wars Pro 2.0 unregistered reference. Static rules are not observed play; registered screens remain unseen. #259 and #278 remain unresolved. Historical DOS evidence is segregated. Parent #265 requires independent acceptance after T65.

Read the [player guide](guide.md), [worked turn](guide.md#a-sampled-placement-to-pass-turn), [atlas](atlas.md), [coverage register](coverage.md) and [planning checklist](checklist.md).

<a id="objective"></a>
## Aim and how to read this book

Win by taking all 46 countries. There is also a computer concession route when the sole human is sufficiently far ahead. The game has no demonstrated alternate objective based on income, surviving a time limit, or holding a smaller fraction of the board. A stalled game is not automatically a draw.

Evidence: static · static-bounded; [F012](../../findings/F012-pro-turn-victory-rules.md), [S-victory](../../spec/victory.md).

Start with the player guide for screen actions and the worked placement-to-pass turn. Use this reference for arithmetic and exceptions, and the atlas for map appearance. Here, documented means the directions say it; static means handlers or tables support it; observed means an identified recorded view supports only the visible state; derived means stated arithmetic assumptions; unknown means evidence is missing.

Evidence: derived · conditional; [GUIDE](../../manual/pro/guide.json), [ATLAS](../../manual/pro/atlas.json).

The illustrations cover the unregistered Pro release. They do not demonstrate every rule, timing, dialogue or registered option. Historical DOS Isle Wars is a separate implementation; its save files, owner colours and card codes must not be used as instructions for Pro.

Evidence: derived · conditional; [GUIDE](../../manual/pro/guide.json), [S-representation](../../spec/representation.md).

<a id="setup"></a>
## Choose a game and understand the deal

The four fixed seats are Blue, Yellow, Red and Green. In the unregistered build Blue is the one human and the other three seats are computers. The seat switches are locked here; the code contains other arrangements but this book does not illustrate a registered multiplayer or all-computer setup.

Evidence: static · static-bounded; [F018](../../findings/F018-pro-deal-rules.md), [F019](../../findings/F019-pro-setup-rules.md), [S-seats](../../spec/seats.md).

Choose Hard, Normal or Easy to change the human’s initial territory share: exactly 5, 9 or 14 countries respectively in this unregistered layout. Difficulty does not change the AI algorithm or the initial army range. Every country starts with a separate draw of 1 to 3 armies, because the starting-armies option is locked to 3.

Evidence: static · static-bounded; [F018](../../findings/F018-pro-deal-rules.md), [F016](../../findings/F016-pro-ai-rules.md).

The computers divide the remaining 41, 37 or 32 countries unevenly. The deal uses seat draws with a soft redraw rule, then a 46-country draw-and-remove shuffle; it does not promise equal computer holdings or compact starts. All countries are owned at the start. Three production locations are chosen after the deal, then a seat marker determines who starts; Blue is not guaranteed first.

Evidence: static · static-bounded; [F018](../../findings/F018-pro-deal-rules.md), [F017](../../findings/F017-pro-board-rules.md).

Options also expose speed and sound. Speed has Fast, Normal and Slow choices and changes waiting helpers; sound is a session toggle. Starting armies lists 1, 3, 5, 7 and 10, and event frequency lists More, Normal, Less and Never, but these two controls are locked to 3 and Normal in the unregistered build. Saving defaults saves preferences, not the current game.

Evidence: static · static-bounded; [F019](../../findings/F019-pro-setup-rules.md), [G2](../../docs/prototypes/T64/visual-source-survey-r2.json).

An internal fourth strength branch would assign 16 human countries, but the GUI has only three choices. Values 5 through 10 can survive part of the defaults reader without a corresponding deal branch; their runtime outcome is unestablished. Do not treat malformed defaults as extra supported difficulty settings.

Evidence: static · static-bounded; [F018](../../findings/F018-pro-deal-rules.md), [F019](../../findings/F019-pro-setup-rules.md).

<a id="board"></a>
## Read the board and complete islands

The fixed map has 46 numbered countries in nine logical bonus groups. Every country has two to five neighbours; the reciprocal connected graph contains 80 undirected borders. Sixteen links join different groups and use the ordinary adjacency rules. Crossing water does not add a separate combat or movement cost in these tables.

Evidence: static · static-bounded; [F017](../../findings/F017-pro-board-rules.md), [S-board](../../spec/board.md).

Full ownership earns these fixed bonuses: countries 1–3: 2; 4–8: 4; 9–13: 4; 14–23: 8; 24–26: 2; 27–33: 5; 34–36: 2; 37–43: 5; 44–46: 3. Partial control earns zero. The bonuses sum to 35; they are constants, not a size formula to recompute.

Evidence: static · static-bounded; [F013](../../findings/F013-pro-reinforcement-rules.md), [F017](../../findings/F017-pro-board-rules.md), [S-island-bonuses](../../spec/island-bonuses.md).

Use the atlas to distinguish coloured land, country numerals, ownership and selection cues from the logical border graph. Twenty-three key countries matter to computer choices; they are not an extra kind of human move. Board coordinates used for labels do not define coastline geometry or clickable areas.

Evidence: derived · conditional; [ATLAS](../../manual/pro/atlas.json), [F017](../../findings/F017-pro-board-rules.md), [F022](../../findings/F022-pro-map-presentation.md).

#259 remains unresolved: the nine logical bonus groups do not by themselves establish the number of apparent physical island clusters. Neither the map drawing mechanism nor exact input hit areas has been reconstructed. An illustrated observation rectangle is not a hitbox.

Evidence: unknown · unknown; [ATLAS](../../manual/pro/atlas.json), [F022](../../findings/F022-pro-map-presentation.md).

<a id="income"></a>
## Calculate income and place every army

At the start of a seat’s turn, income = max(floor(countries / 3), 2) + bonuses for every complete island. The minimum applies only to the country component. Thus one to five countries earn 2 before bonuses; holding the complete three-country first island earns 2 + 2 = 4. Production centres add no passive income, and difficulty and existing army stacks add no term.

Evidence: static · static-bounded; [F013](../../findings/F013-pro-reinforcement-rules.md), [S-reinforcement](../../spec/reinforcement.md).

Income is calculated once for the new turn, before any card trade. Capturing an island later does not recalculate this turn’s pool. A trade can add 5, 8 or 15, double the whole pool including island bonuses, or bomb without adding armies. For example a pool of 7 becomes 14 under doubling; it is not merely the country component that doubles.

Evidence: static · static-bounded; [F013](../../findings/F013-pro-reinforcement-rules.md), [F014](../../findings/F014-pro-cards-rules.md).

Place the entire pool on your own countries, in any split and order. The chooser’s plus cannot exceed the remaining pool; minus stops at zero; All chooses the remainder. Place commits the allocation, subtracts it from the pool and resets the chooser. You cannot carry unused armies to another turn or leave placement early with a positive pool.

Evidence: static · static-bounded; [F013](../../findings/F013-pro-reinforcement-rules.md), [GUIDE](../../manual/pro/guide.json).

A country’s stored stack is capped at 999 after addition. Allocating 2 onto 998 therefore credits only 1, while consuming both allocated armies. The computer likewise credits its pool, although an internal pool variable may stay nonzero in one split branch; the next turn resets and recomputes it, so that is not carryover.

Evidence: static · static-bounded; [F013](../../findings/F013-pro-reinforcement-rules.md).

<a id="turns"></a>
## Take a turn and finish it deliberately

Seats advance Blue, Yellow, Red, Green, wrapping and skipping eliminated seats. A turn runs income, a possible card trade, placement, attacks and then either one ordinary move or Pass. The human can make any number of legal attacks, including none. An ordinary move ends the turn; you cannot move and then resume attacking.

Evidence: static · static-bounded; [F012](../../findings/F012-pro-turn-victory-rules.md), [F011](../../findings/F011-pro-combat-rules.md), [S-turn-sequence](../../spec/turn-sequence.md).

Use the action menu after placement to attack, move or pass. Returning from a battle or selection to that menu is not itself a pass. The worked turn shows one placement, a bounded attack-result change, a return to the menu and an early next-seat frame. It does not illustrate a capture, a full computer turn or an entire round.

Evidence: observed · observed-bounded; [GUIDE](../../manual/pro/guide.json), [G2](../../docs/prototypes/T64/visual-source-survey-r2.json).

The event counter advances per occupied player-turn transition, not once per four-seat round, and is not a displayed round clock. Events and concession checks can occur between turns. A capture card is normally awarded at the end of a capturing turn; the human forfeit exception can erase that entitlement.

Evidence: static · static-bounded; [F012](../../findings/F012-pro-turn-victory-rules.md), [F014](../../findings/F014-pro-cards-rules.md), [F015](../../findings/F015-pro-centres-hazards-rules.md).

<a id="combat"></a>
## Attack: choose a target, then a source

For a human attack, choose an enemy target and then an adjacent owned source. The source needs at least 2 armies and at least as many as the defender when the attack begins. Each exchange draws one six-sided result for each side; the attacker wins only if strictly higher. A tie costs the attacker one army, otherwise the losing side loses one.

Evidence: static · static-bounded; [F011](../../findings/F011-pro-combat-rules.md), [S-combat](../../spec/combat.md).

With independent uniform dice, the attacker wins an exchange in 15 of 36 pairs, or 5/12; it loses in 21 of 36, or 7/12. This is a conditional calculation, not a measured Director random distribution or the probability of winning a whole battle. A large army advantage changes the number of losses you can survive, not the tie rule.

Evidence: derived · conditional; [F011](../../findings/F011-pro-combat-rules.md).

A human click runs five exchanges when the attacker exceeds 35 and the defender exceeds 15; otherwise it runs one. The computer uses five when its attacker exceeds 40 and defender exceeds 15. Stop tests follow the pass, so batching can run beyond a threshold inside that pass. Do not infer exchange timing from one before/after still.

Evidence: static · static-bounded; [F011](../../findings/F011-pro-combat-rules.md).

The G11 to G12 sample shows the defending country 18 and lower-right defender count falling from 3 to 2, while the source remains 4 and ownership remains unchanged. That proves the sampled displayed decrement, not capture odds, a complete battle or immediate timing of every animation.

Evidence: observed · observed-bounded; [G2](../../docs/prototypes/T64/visual-source-survey-r2.json), [GUIDE](../../manual/pro/guide.json).

<a id="capture"></a>
## Capture, retreat and the human forfeit

When the defender reaches zero, ownership transfers. The intended human split chooser moves 1 through source armies minus 1 into the new country, leaving one behind; the computer performs an automatic split instead. A newly captured country can attack onward if it meets the ordinary gate; no special “already used” marker forbids that.

Evidence: static · static-bounded; [F011](../../findings/F011-pro-combat-rules.md), [S-ownership](../../spec/ownership.md).

Human zero-choice reachability remains open because the intended positive chooser limits do not prove every score path enforces them. This book does not assert that a zero transfer is either a usable procedure or exhaustively impossible. No retained illustration shows the capture split dialogue.

Evidence: unknown · unknown; [S-ownership](../../spec/ownership.md), [GUIDE](../../manual/pro/guide.json).

You may stop an attack and return to the action menu while the human source is still viable. If it falls to one army on the human battle path, the forfeit branch gives that source country to the defender’s owner with one army and ends the turn. It also clears the capture-card flag, even if you captured another country earlier that turn. This is more costly than voluntarily backing out.

Evidence: static · static-bounded; [F011](../../findings/F011-pro-combat-rules.md), [F014](../../findings/F014-pro-cards-rules.md).

The computer does not use the human forfeit. It starts from a stronger gate than the human: a source must exceed a drawn floor and beat the defender by a drawn margin. It stops according to stack, key-country and other-neighbour tests. Its post-capture split is not a universal keep-three rule; a final strongest-enemy comparison can override intermediate choices. Separate 999 caps can discard excess armies.

Evidence: static · static-bounded; [F011](../../findings/F011-pro-combat-rules.md), [F016](../../findings/F016-pro-ai-rules.md).

<a id="movement"></a>
## Move once, or pass

An ordinary move transfers armies between two adjacent countries you own. The source must have more than one army, and the intended amount is 1 through all but one. The move ends the turn. A connected chain of owned countries does not make non-neighbours a legal pair, and there is no second ordinary move after the first. Pass ends a turn without this relocation.

Evidence: static · static-bounded; [F011](../../findings/F011-pro-combat-rules.md), [F012](../../findings/F012-pro-turn-victory-rules.md), [S-movement](../../spec/movement.md).

Capture redistribution belongs to the battle that just won a country; it is different from the optional end-of-turn move. The guide gives source-qualified selection and cancellation instructions, but no retained G image demonstrates a completed move, its amount dialogue, or destination feedback. Treat those as static-only procedures.

Evidence: derived · conditional; [GUIDE](../../manual/pro/guide.json), [F011](../../findings/F011-pro-combat-rules.md).

<a id="cards"></a>
## Earn and hold cards

Capture at least one country in a turn to earn one card at turn end, however many captures you make. The human forfeit can cancel it; the computer draws after its movement. A hand holds five cards. Before a further draw the human must discard a chosen card; the computer discards anti-bomb first, then bomb-match, then +5, otherwise a random slot.

Evidence: static · static-bounded; [F014](../../findings/F014-pro-cards-rules.md), [S-cards](../../spec/cards.md).

The draw list has 34 entries: three bomb-match, two anti-bomb, eight +5, six +8, three +15, six wildcards, one hand-clearing bomb and five doubling cards. Each draw samples the fixed list again; there is no depleting deck or reshuffle. An empty hand has only 33 eligible entries, excluding the hand-clearing bomb.

Evidence: static · static-bounded; [F014](../../findings/F014-pro-cards-rules.md).

Keep the two bomb roles separate. A bomb-match card is an ordinary tradeable kind used in a three-card attack set. Drawing the hand-clearing bomb immediately empties that hand and is never a held card. Anti-bomb is a protection card, not a tradeable match. The eight roles do not establish an observed card-screen layout here.

Evidence: static · static-bounded; [F014](../../findings/F014-pro-cards-rules.md), [GUIDE](../../manual/pro/guide.json).

<a id="trades"></a>
## Trade at most one set at turn start

After income and before placement, a match is three of one tradeable kind, allowing at most two wildcards to complete it. Three wildcards alone are not a valid match. The effects are +5, +8, +15, double the whole reinforcement pool, or a bomb attack without reinforcement addition. Anti-bomb cannot be picked as a match kind.

Evidence: static · static-bounded; [F014](../../findings/F014-pro-cards-rules.md).

The directions describe trade-in as mandatory when a match is held, but F014 finds a human skip path. Keep this discrepancy visible: documentation intent and static behaviour differ. Human card choices toggle; submitting an invalid triple consumes no cards, grants nothing and proceeds to placement rather than offering unlimited retries. This guide has no recorded trade screen to settle all input paths.

Evidence: documented · documented; [T04](../../sources/iwp-islepro-txt.md), [F014](../../findings/F014-pro-cards-rules.md).

The computer tries +15, +8, doubling, +5 and bomb in that priority order; it does not compare the resulting reinforcement payoff. Human matching and computer removal are asymmetric: the computer’s detector caps wildcard contribution at two, but its removal takes the first three qualifying cards without that cap. A hand ordered wildcard, wildcard, wildcard, +15, empty can detect +15 using two wildcards and +15, yet remove the three wildcards and retain +15.

Evidence: static · static-bounded; [F014](../../findings/F014-pro-cards-rules.md).

<a id="bombs"></a>
## Bomb effects and anti-bomb protection

A traded bomb targets an enemy country without an adjacency requirement on the human path. It replaces that stack with a draw from 1 through floor(old / 2), with a minimum upper bound of 1. It never transfers ownership or awards a capture, and adds no reinforcements. A 9-army target becomes 1 through 4; a one-army target remains one.

Evidence: static · static-bounded; [F014](../../findings/F014-pro-cards-rules.md).

An anti-bomb held by the target’s owner cancels one bomb attack and is consumed. It protects that owner’s targeted country rather than a permanently chosen location. A static human protection branch also reorders the bomber’s own hand through stale selections and may clear retained cards; particular runtime cases have not been demonstrated.

Evidence: static · static-bounded; [F014](../../findings/F014-pro-cards-rules.md).

The computer bomb candidate code indexes army values by a candidate count rather than the candidate country in part of its filtering. Actual selection behaviour for empty or out-of-range candidate cases is unknown. Do not turn the static suspicion into a reliable targeting strategy or a visually verified error.

Evidence: unknown · unknown; [F014](../../findings/F014-pro-cards-rules.md).

<a id="centres"></a>
## Production locations are event opportunities

There are three distinct production locations, chosen anew after the deal from shuffled country positions 12, 24 and 37. There is no spacing, island or owner constraint. They do not grant passive armies during turn income. Their benefit is the production-increase event: all three current centre stacks double, whoever owns them, capped at 999 each.

Evidence: static · static-bounded; [F015](../../findings/F015-pro-centres-hazards-rules.md), [F013](../../findings/F013-pro-reinforcement-rules.md), [S-production-centres](../../spec/production-centres.md).

The move-centres event replaces all three with fresh distinct countries; overlap with earlier locations is possible. Capture and rebellion change ownership without moving or destroying a centre. A centre’s potential future increase therefore passes with its country, not through a separate captured-site inventory.

Evidence: static · static-bounded; [F015](../../findings/F015-pro-centres-hazards-rules.md).

The reviewed V06 view includes a cyan 3 at country 18. Main’s crosscheck of both centre-reference images found cyan at 9, 18 and 46 and white at 2, 3 and 30. This conflicts with F020’s first-image list and remains #278. The centre interpretation is source-qualified by static colouring logic; these stills do not demonstrate an increase or move event.

Evidence: observed · observed-bounded; [V3](../../docs/prototypes/T63/visual-source-survey-r3.json), [F020](../../findings/F020-pro-ui-observations.md), [F015](../../findings/F015-pro-centres-hazards-rules.md).

<a id="events"></a>
## Random events: eligibility before probability

Five event kinds occupy fourteen slots: two earthquake, two flood, two rebellion, six production increase and two production move. If the previous slot repeats, it is redrawn once; this does not forbid the previous event kind. More, Normal and Less give an eligible-transition chance of 1/8, 1/14 and 1/21. Never overrides the draw; unregistered play is locked to Normal.

Evidence: static · static-bounded; [F015](../../findings/F015-pro-centres-hazards-rules.md), [S-hazards](../../spec/hazards.md).

No event dispatch occurs in the first six player-turns, while any seat owns 39 or more countries, or after game over. The ownership threshold is tested again each transition rather than latched permanently. A concession or stop route can pre-empt the event draw. These conditions make the eligible chance different from an unconditional per-turn or per-round event frequency.

Evidence: static · static-bounded; [F015](../../findings/F015-pro-centres-hazards-rules.md), [F012](../../findings/F012-pro-turn-victory-rules.md).

After an event the counter resets to 5. The next advance makes 6 and is ineligible; the following makes 7 and can draw. F015’s arithmetic therefore requires one forced empty transition, unlike F012’s loose “soon again” gloss. Under continuous eligibility and independent constant-probability assumptions, the mean interval is 1 + 1/p, hence 9, 15 or 22 transitions for the three settings. These are derived conditional averages, not measured play rates.

Evidence: derived · conditional; [F015](../../findings/F015-pro-centres-hazards-rules.md), [F012](../../findings/F012-pro-turn-victory-rules.md).

Earthquake and flood share the damage handler. It strikes a consecutive block of three or four countries after a stack-seeking window search; country 1 is never struck. If old armies exceed 6, the new stack is drawn from 1 through max(1, floor(old / 2) - 1); otherwise from 1 through max(1, old - 1). Thus 20 becomes 1–9, while 6 can become 5. This is not fixed halving or a fixed loss.

Evidence: static · static-bounded; [F015](../../findings/F015-pro-centres-hazards-rules.md).

Rebellion needs at least two seats each holding at least three countries. It draws a victim and recipient equally among eligible seats, then transfers one victim country with its army count unchanged; it is not explicitly aimed at the leader. No event reduces a positive stack to zero, eliminates a seat or destroys a centre. Beneficial production events are not a rule that always helps whoever is behind.

Evidence: static · static-bounded; [F015](../../findings/F015-pro-centres-hazards-rules.md).

No retained guide illustration establishes an event announcement, damage animation, production doubling feedback or centre relocation dialogue. The reference supplies static effects and bounds, not fabricated examples of those screens. Their exact display ordering and timing remain unobserved here.

Evidence: unknown · unknown; [GUIDE](../../manual/pro/guide.json), [F015](../../findings/F015-pro-centres-hazards-rules.md).

<a id="ai"></a>
## What the computer changes

Computers receive the same income formula, card values and dice comparison as the human, but choose by separate rules. Difficulty changes the human starting territory share, not these algorithms. Placement ranks islands by the computer’s ownership share, seeds threatened key countries on completed islands and sometimes centres, then splits the remainder among up to five strong candidates. It does not promise evenly distributed reinforcements.

Evidence: static · static-bounded; [F016](../../findings/F016-pro-ai-rules.md), [F018](../../findings/F018-pro-deal-rules.md).

Attack pairs within an island get double list weight, or fourfold on an island assigned rank value 4. A computer normally draws two to five attack rounds, adds one above 16 countries and three more above 25, and adds four after the last human is eliminated; below eight countries a two-to-four override replaces those terms. A one-in-22 no-attack branch applies only at 18 or fewer countries. These branches are choice rules, not measured attack rates.

Evidence: static · static-bounded; [F016](../../findings/F016-pro-ai-rules.md).

After attacks, the normal relocation uses the largest safe interior source above two armies, a non-key source and a hard-coded 23-country route table. Five corridor fallbacks can move from key countries, so “never move a key country” is false. A centre-source veto usually blocks departure; a successful move sends all but one and caps the destination. No empirical AI strength, win rate or optimal counterstrategy is claimed.

Evidence: static · static-bounded; [F016](../../findings/F016-pro-ai-rules.md).

<a id="endings"></a>
## Victory, elimination, concession and losses

Owning all 46 countries wins. Human conquest is checked on the following frame; a computer’s final conquest is detected at the next turn advance after its own movement and card draw. At zero countries a seat is marked eliminated during rebuilding and skipped. Its cards are later wiped, no later than the next advance; they are not transferred to the conqueror.

Evidence: static · static-bounded; [F012](../../findings/F012-pro-turn-victory-rules.md), [S-victory](../../spec/victory.md), [S-ownership](../../spec/ownership.md).

When the sole human owns at least 33 countries and the live-state conditions permit, the computers can offer collective concession between turns. Accepting records a win; refusal continues play and suppresses another offer that game. It costs no armies or cards. This is different from giving up a weak game yourself and from a human combat forfeit.

Evidence: static · static-bounded; [F012](../../findings/F012-pro-turn-victory-rules.md), [S-surrender](../../spec/surrender.md).

After human elimination, the code offers accepting the loss or watching computers continue. Starting a new game with a live Blue, Yellow or Red human on 1–9 countries marks a loss; 10 or more, or zero, does not newly set that flag unless an earlier quit-early route already did. A Green-human local-store quirk is static-only and unreachable in this unregistered one-human layout; do not use it to promise registered scoring behaviour.

Evidence: static · static-bounded; [F012](../../findings/F012-pro-turn-victory-rules.md).

The G06 recorded loss notice has a clipped bottom line and the scores frame shows zero counters. Those stills do not establish the exact weak-game threshold, persistence, victory dialogue or concession choices; the numerical rules above come from static evidence. Terminal-route score ordering has remaining bounds, so this is not an exhaustive recipe for avoiding a recorded loss.

Evidence: observed · observed-bounded; [G2](../../docs/prototypes/T64/visual-source-survey-r2.json), [F012](../../findings/F012-pro-turn-victory-rules.md).

<a id="persistence"></a>
## Preferences and scores, not a saved position

Save as default stores eight comma-separated preference fields: seat flags, speed, event frequency, starting armies and strength. Sound is not saved by that handler. There is no game save, load, position export or import handler in the reviewed Pro corpus. The absence of a button in the selected screenshots alone would not prove this; the bounded negative claim comes from F019’s whole-corpus search.

Evidence: static · static-bounded; [F019](../../findings/F019-pro-setup-rules.md), [S-representation](../../spec/representation.md).

Scores have six counters: wins and losses for Easy, Normal and Hard. The unregistered write check admits an existing sum at or below 50, so a result can take the total to 51 before later updates stop. This is not an exactly-50-result cap. A seventh stored field is zero on the writer path. The character-shift encoding is score storage, not an encrypted game position.

Evidence: static · static-bounded; [F012](../../findings/F012-pro-turn-victory-rules.md), [F019](../../findings/F019-pro-setup-rules.md), [S-representation](../../spec/representation.md).

Observed representation values cover only the recorded comma, zero and one cases and selected loss increments; broader encoding rules come from static reading. Malformed or foreign defaults and scores have incomplete runtime bounds and no format/version validation. Do not edit files to infer supported options, replayability or a safe restore procedure.

Evidence: static · static-bounded; [F019](../../findings/F019-pro-setup-rules.md), [S-representation](../../spec/representation.md).

<a id="interface"></a>
## Navigation, confirmation and missing screens

The guide’s title, options, new-game setup, help page, scores and clipped loss notice are recorded context screens. Board views show owners, armies, the active seat and phase, action panels, selected allocation and a sampled battle panel. Use the clickable guide chapters and atlas callouts for those views; their observation regions are approximate and cannot certify legal click boundaries.

Evidence: observed · observed-bounded; [GUIDE](../../manual/pro/guide.json), [ATLAS](../../manual/pro/atlas.json), [G2](../../docs/prototypes/T64/visual-source-survey-r2.json), [V3](../../docs/prototypes/T63/visual-source-survey-r3.json).

Selection cancellation is state-specific. Backing out of an attack target or amount selection can return to an earlier panel, while committing placement consumes the chosen pool and committing an ordinary move ends the turn. Neither a return arrow nor a menu transition universally means undo. The guide distinguishes each supported instruction from an unrecorded dialogue.

Evidence: derived · conditional; [GUIDE](../../manual/pro/guide.json), [F011](../../findings/F011-pro-combat-rules.md), [F013](../../findings/F013-pro-reinforcement-rules.md).

Keyboard shortcuts, exact disabled-control feedback, all confirmation prompts, full help paging, event presentation, capture/move/card dialogues, registered screens, audio and original-renderer timing are not exhaustively observed. The screen coverage register keeps these gaps explicit. Static handler names and visible shapes do not fill them in.

Evidence: unknown · unknown; [GUIDE](../../manual/pro/guide.json), [ATLAS](../../manual/pro/atlas.json), [F020](../../findings/F020-pro-ui-observations.md), [F022](../../findings/F022-pro-map-presentation.md).

<a id="history"></a>
## Historical appendix and evidence boundary

The original directions include version/front matter, registered-edition distinctions and an ordering appendix. This reference covers their subjects in own words without reproducing addresses, order forms, branding or treating historical ordering as current purchase advice. Registration gates explain current restrictions; unseen registered options and screens remain unknown.

Evidence: documented · documented; [T04](../../sources/iwp-islepro-txt.md), [F019](../../findings/F019-pro-setup-rules.md).

Historical DOS Isle Wars has its own save/load representation, level numbering, colours and runtime. Pro’s four seats include Yellow where DOS representation uses Brown; Pro difficulty numbering is Hard 1, Normal 2, Easy 3. Do not import DOS file or control instructions into this Pro reference. DOS rows in shared spec tables are historical context only.

Evidence: derived · conditional; [S-representation](../../spec/representation.md), [F018](../../findings/F018-pro-deal-rules.md).

Pro runtime evidence demonstrates repeatable launch, screenshot and reset cycles under Wine 9.0, Xvfb 800×600 and xfwm4 in the recorded environment. Equal captured screens and prefix hashes do not prove internal random-state determinism, native Windows timing, universal compatibility or a replayable seed. No new run is performed for this manual.

Evidence: derived · conditional; [S-runtime](../../spec/runtime.md), [F019](../../findings/F019-pro-setup-rules.md).

The malpaco checklist is research handoff for planning only after 0.1.x. Consumer issue #191 may use it to prepare concrete design proposals or optional unscheduled backlog; the owner selects and approves a proposal, then separately authorizes and prioritizes implementation. No adoption, design decision, asset transfer or code change in malpaco is authorized by this manual.

Evidence: derived · conditional; [ATLAS](../../manual/pro/atlas.json), [GUIDE](../../manual/pro/guide.json).

