# Pro player guide and worked turn

This guide covers preserved unregistered Windows Pro screens and source-qualified human procedures. It supplies no DOS or registered-build claims, exhaustive hitboxes, sound/timing proof or invented missing screens. #259 visual-island grouping and #278 centre-colour source conflict remain explicit in the retained atlas. The accompanying reference supplies detailed rules; Parent acceptance is tracked under #265; main owns final acceptance.

Read [the map/UI atlas](atlas.md) for map vocabulary and its open evidence questions. The [local edition instructions](README.md) describe the illustrated guide and atlas; the repository prose below remains useful without original pixels.

## Start a game and adjust options

**What you can see.** Open the settings before starting. The setup and options pages group starting armies, the four seats, difficulty, event/message frequency and speed. Their footers differ: setup offers a start-play control, while options offers a return control. A highlighted choice is not proof that every alternative is enabled.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**What to do.** In this unregistered build you play Blue against three computers. F019 reads the seat switches, starting-army quantity and event frequency as locked; strength and speed remain adjustable. Use the setup play control to begin. The preference-default control stores options, not the current board.

Evidence: static; confidence: static-bounded. [F019-options](../../findings/F019-pro-setup-rules.md#the-options-screen), [F019-gates](../../findings/F019-pro-setup-rules.md#the-registration-gates).

**What changes.** The publisher lists setup choices and describes one human Blue seat in the unregistered edition. Treat that as intended behavior; a locked-control response is not illustrated by this guide’s settings stills.

Evidence: documented; confidence: documented. [D-setup](../../sources/iwp-islepro-txt.md#setup).

**Back out and confirm.** Use the return control shown on the options page to leave that page. The start-play control on the new-game page starts play instead, so check which screen you are on before confirming. Keyboard alternatives and exact hit areas are not measured here.

Evidence: static; confidence: static-bounded. [F019-options](../../findings/F019-pro-setup-rules.md#the-options-screen).

## Read the board and changing panels

**What you can see.** Read the selected-country information and remaining armies in the lower side panels, with the current action controls between them. The player summary marks the active row. In the worked example that marker later moves from Blue to Yellow.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**What to do.** Follow the current turn stage. Placement comes before the free-action menu; that menu offers attacks, movement, passing and cards. An ordinary troop move ends the turn, so it is not a way to rearrange armies and then resume attacking.

Evidence: static; confidence: static-bounded. [F012-turn](../../findings/F012-pro-turn-victory-rules.md#turn-sequence), [F011-move](../../findings/F011-pro-combat-rules.md#movement).

**What changes.** The lower centre changes from a quantity chooser to a five-choice action menu, then to combat controls. The panel state tells you what is being chosen; simply seeing the action menu again does not mean your turn is over.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**Back out and confirm.** Use the separate atlas for the map’s visual vocabulary. This guide does not provide measured country hitboxes, keyboard equivalents, a complete legal-target overlay, or an undo procedure for arbitrary board clicks.

Evidence: unobserved; confidence: unknown. [L-atlas](../../manual/pro/atlas.md#evidence-boundaries), [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

## Choose and commit reinforcements

**What you can see.** The example starts with country 17 selected, 2 armies already on it, 0 chosen for placement and 2 available. The chosen amount is a separate number from the armies already on the board.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**What to do.** Place your turn’s reinforcement pool on your own countries before using the action menu. Select a country, choose an amount with the quantity controls, and commit it with the placement confirmation. The sampled all-available choice is illustrated below; it is not a fixed income of 2 for every turn.

Evidence: static; confidence: static-bounded. [F013-place](../../findings/F013-pro-reinforcement-rules.md#placement), [F012-turn](../../findings/F012-pro-turn-victory-rules.md#turn-sequence).

**What changes.** Choosing all available changes the allocation display to 2 while country 17 still shows 2. After commitment, country 17 shows 4 and the action menu replaces the placement controls. Chosen allocation and committed placement are different states.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**Back out and confirm.** Adjust the chosen amount before committing it. F013 reads the plus/minus/all controls and no early Done, Pass or Cancel exit while reinforcement armies remain. This is a placement commitment, not the separate captured-country move-in confirmation. Reversing an already committed placement is not demonstrated here.

Evidence: static; confidence: static-bounded. [F013-place](../../findings/F013-pro-reinforcement-rules.md#placement).

## Select a battle and recognize its result

**What you can see.** The attack-ready example names source 17 and target 18, compares 4 against 3, and shows attack and leave-combat controls. The lowest source line is clipped in the original frame; no missing wording is reconstructed.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**What to do.** Choose the enemy target first, then your own bordering source. The human source must hold at least 2 armies and at least as many as the target. Continue with the battle control while the game permits it. F011 warns that being reduced to 1 forfeits the attacking country and ends the human turn.

Evidence: static; confidence: static-bounded. [F011-combat](../../findings/F011-pro-combat-rules.md#combat).

**What changes.** The sampled result panel now compares 4 against 2, and country 18 also shows 2 on the board, down from 3 in the attack-ready frame. Source 17 remains at 4 and ownership is unchanged. This illustrates one defender decrement, not a territory capture or a timing measurement; no capture/move-in screen is shown.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**Back out and confirm.** The leave-combat control returns from the battle mode without itself ending the turn. On an actual capture, F011 describes a separate choice of how many armies to move into the conquered country, leaving at least one behind; this guide has no capture-screen illustration or tested capture-cancel procedure.

Evidence: static; confidence: static-bounded. [F011-combat](../../findings/F011-pro-combat-rules.md#combat), [F011-capture](../../findings/F011-pro-combat-rules.md#ownership-change).

## Relocate armies at the end of a turn

**What you can see.** No ordinary movement-selection or movement-quantity screen is illustrated in this evidence set. The action menu has a movement choice, but that alone is not a visual walkthrough of a completed move.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

**What to do.** F011 reads the human flow as selecting an owned source with more than one army and an owned adjacent destination, then choosing a quantity. Leave at least one army at the source. A completed ordinary move ends the turn; movement after capture is a separate choice.

Evidence: static; confidence: static-bounded. [F011-move](../../findings/F011-pro-combat-rules.md#movement).

**What changes.** The static flow returns through the same turn-ending routes as Pass: it may show a card award if the capture flag was earned, or advance to the next seat. This describes the code reading, not a sampled movement transition in the pictures below.

Evidence: static; confidence: static-bounded. [F011-move](../../findings/F011-pro-combat-rules.md#movement), [F012-turn](../../findings/F012-pro-turn-victory-rules.md#turn-sequence).

**Back out and confirm.** No movement cancellation or confirmation still has been inspected for this guide. The code reading establishes the quantity-confirmation path, but the evidence does not justify inventing its full button layout, keyboard controls or an undo-after-move procedure.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

## Inspect cards and distinguish a trade

**What you can see.** There is no illustrated hand, trade-selection or discard screen here. The action menu’s card choice does not prove the shape of those screens. Do not read any battle result in this walkthrough as a card award.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

**What to do.** F014 places a possible three-card trade at the top of the human turn, before placement. A matching set may use up to two wildcards for detection. Clicks toggle eligible card selections, and three selections arm the trade control. The anti-bomb is not a trade selection. Detailed card effects are in the accompanying rules reference.

Evidence: static; confidence: static-bounded. [F014-trade](../../findings/F014-pro-cards-rules.md#matches-and-trade-ins).

**What changes.** The hand has five slots. F014 reads a full-hand draw as requiring a chosen discard before the new card arrives. For trading, a valid set is consumed; an invalid three-card selection gives no bonus and consumes nothing before continuing to placement. These are static results, not observed feedback in this guide’s stills.

Evidence: static; confidence: static-bounded. [F014-limit](../../findings/F014-pro-cards-rules.md#the-hand-limit), [F014-trade](../../findings/F014-pro-cards-rules.md#matches-and-trade-ins).

**Back out and confirm.** Before a trade is confirmed, selected cards can be toggled off. F014 identifies a skip-trade exit that leaves the hand intact and proceeds to placement. The directions’ wording about mandatory trades does not substitute for this code reading; a visual test of trade/skip behavior is still missing.

Evidence: static; confidence: static-bounded. [F014-trade](../../findings/F014-pro-cards-rules.md#matches-and-trade-ins), [D-trade](../../sources/iwp-islepro-txt.md#trading-in-cards).

## Pass control to the next player

**What you can see.** The action menu returns after the sampled combat exchange. In the after-pass frame, Yellow is marked active and the right panel shows country-counting feedback; the central action area is blank. This is an early next-turn state, not a completed computer turn.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**What to do.** Choose Pass when you have finished attacking and do not want the optional ordinary troop move. Placement must be completed first. F012 reads both Pass and the completed move as turn-ending paths; a failed human attack is another way to lose the rest of the turn.

Evidence: static; confidence: static-bounded. [F012-turn](../../findings/F012-pro-turn-victory-rules.md#turn-sequence), [F011-combat](../../findings/F011-pro-combat-rules.md#combat).

**What changes.** The worked sequence ends at the first recorded hand-off frame. The active-row pointer and country-counting status show a change of seat; they do not time the computer’s thinking, identify all later actions or establish a game result.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**Back out and confirm.** The evidence does not demonstrate a Pass confirmation dialog or a way to take back Pass. Do not invent an extra confirmation step or promise that turn-ending actions can be undone.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

## Back out before committing a choice

**What you can see.** Read the current panel before choosing a confirmation: allocation has quantity controls, attack readiness has a leave-combat control, and the action menu has a backing-out choice. These are different contexts, not one universal confirmation dialog.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**What to do.** F011 reads quit-attack and cancel paths as returns to the human action screen without ending the turn. Use a confirmation only for the action it names. Placement, captured-country move-in, ordinary relocation and card trade have different commitments; this guide does not imply a global undo.

Evidence: static; confidence: static-bounded. [F011-combat](../../findings/F011-pro-combat-rules.md#combat).

**What changes.** After leaving the sampled combat mode, the five-choice action menu is visible again. That visible return is narrower evidence than a claim that the entire battle or its losses were reversed.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**Back out and confirm.** No exhaustive illegal-input/cancellation study is available here. A button’s picture is not a measured hit area, and no still proves keyboard shortcuts, confirmation prompts for every action, or recovery after a committed move or trade.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish), [L-atlas](../../manual/pro/atlas.md#evidence-boundaries).

## Find help and return to play

**What you can see.** The title page retains six bottom navigation choices. Help opens an inset document with a scrollbar and a green return control. The ordinary score view also has a return control. Original help prose is visible only in the local edition and is not transcribed into the repository.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**What to do.** The bottom menu routes to new game, options, publisher material, scores, quit and help. Use the help page’s return control to leave it. This guide does not follow publisher website/order-form actions or provide current purchasing advice.

Evidence: static; confidence: static-bounded. [F019-options](../../findings/F019-pro-setup-rules.md#the-options-screen).

**What changes.** Options and new-game settings look similar but their green footer controls have different purposes. Help and score pages replace the central content. Check the screen context rather than assuming a fixed footer action.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**Back out and confirm.** Scrollbar appearance does not establish keyboard scrolling, every help-page transition or precise clickable geometry. The guide illustrates one help page and does not claim all navigation routes were re-tested.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

## Separate preferences from a saved game

**What you can see.** No save-current-position or load-position screen is included. The default-saving control pictured in options/setup is a preferences control, not evidence of a resumable game.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

**What to do.** F019’s bounded file/menu census finds no position-saving or position-loading handler in this unregistered build. It accounts for preferences, score tallies and registration files instead. Do not rely on leaving and reopening the program to resume the board.

Evidence: unsupported; confidence: unsupported. [F019-save](../../findings/F019-pro-setup-rules.md#no-save-no-load).

**What changes.** Saving defaults writes option values; scorekeeping stores results. Neither is a board position, move history or visible seed. This is the static file reading, not a persistence test performed by the guide.

Evidence: unsupported; confidence: unsupported. [F019-save](../../findings/F019-pro-setup-rules.md#no-save-no-load).

**Back out and confirm.** A save/load cancellation or overwrite dialog has no evidenced procedure here. Registered-build possibilities and unknown runtime behavior do not justify inventing one.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

## Leave a game and interpret result screens

**What you can see.** The score page shows difficulty rows with win/loss/percentage columns; all totals are zero in this sample. The separate loss-notice frame has a continuation control and a clipped cyan line about crediting a loss. Its complete threshold and subsequent persistence cannot be read from that still.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**What to do.** For the unregistered Blue human, F012 reads New Game during a live weak position of 1–9 countries as a credited-loss route. This threshold comes from the static reading, not the clipped picture. The collective computer-concession offer is a different route: accepting ends with a human win; refusing continues play. No concession-offer screen is illustrated here.

Evidence: static; confidence: static-bounded. [F012-surrender](../../findings/F012-pro-turn-victory-rules.md#surrender).

**What changes.** F012 reads refusal of the concession offer as disabling later offers for that game. It also distinguishes leaving a game from elimination and from all-country victory. A visible score table is not proof that a particular result has been written, and this guide does not reconstruct missing terminal screens.

Evidence: static; confidence: static-bounded. [F012-surrender](../../findings/F012-pro-turn-victory-rules.md#surrender).

**Back out and confirm.** The selected loss notice does not establish its continuation’s full follow-up, a cancel-resignation dialog, or every quit/exit confirmation. Treat abandoning the current board as distinct from backing out of a battle selection; no resumable-game guarantee is offered.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

## Understand the unregistered build boundary

**What you can see.** The title page identifies the unregistered edition. The settings stills show Blue as the human and three computer seats, but visible choices alone do not prove that they can all be changed.

Evidence: local-visual; confidence: observed-bounded. [V-guide](../../docs/prototypes/T64/visual-source-survey-r2.json).

**What to do.** F019 reads the unregistered build as locking the seat switches, starting armies and event frequency, while leaving strength and speed available. A registration notice is feedback to a locked action; this guide does not supply registration codes or a bypass procedure.

Evidence: static; confidence: static-bounded. [F019-gates](../../findings/F019-pro-setup-rules.md#the-registration-gates).

**What changes.** The publisher describes additional human players and option control in the registered edition. Those are documented promises, not proof of a tested registered build, extra maps or changed combat rules.

Evidence: documented; confidence: documented. [D-registration](../../sources/iwp-islepro-txt.md#registration).

**Back out and confirm.** No registered-build entry, confirmation or successful-unlock sequence is illustrated. Nothing here extends the unregistered observations to DOS Isle Wars or establishes current registration availability.

Evidence: unobserved; confidence: unknown. [L-catalogue](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

## A sampled placement-to-pass turn

Follow one preserved human turn from placement selection to the immediate hand-off after Pass. All seven pictures come from E019-r0026 in the recorded order. The setup/help/result pictures come from r0013 and are separate context, not earlier moments of this deal. These samples are not a continuous recording, a capture example or a completed game.

1. **G08** Check the selection: country 17 has 2 armies, the chosen placement amount is 0 and the pool is 2. The side panels and quantity chooser describe the current choice.

2. **G09** Choose the available allocation. The quantity becomes 2, but the map still shows 2 at country 17. Choosing the amount has not yet committed it.

3. **G10** Commit placement. Country 17 now shows 4 and the centre panel offers the turn actions. These displayed numbers belong to this deal, not every turn.

4. **G11** Read the opposing pair before attacking: source 17 and target 18 are compared as 4 against 3. The picture shows attack readiness and a leave-combat control; the lowest source text is partly clipped.

5. **G12** Inspect both feedback locations: the result panel compares 4 against 2 and country 18 now shows 2 on the map, down from 3. Source 17 remains 4. This sampled defender decrement does not establish a capture, a complete battle or update latency.

6. **G13** Return to the action menu. Seeing those choices again means the combat panel has been left; it does not mean that the turn has ended or that a territory was captured.

7. **G14** End with Pass. Yellow is now marked active, the lower right shows country-counting feedback and the central action panel is blank. Stop this example at that early hand-off; do not infer the rest of the computer turn.

## Illustrated screen directory

| Image | Context |
| --- | --- |
| G01 | Title context from r0013; original branding remains local. This is not the starting board of the worked r0026 turn. |
| G02 | Options from r0013. Saving defaults means preferences; enabled-state and persistence claims need separate evidence. |
| G03 | New-game setup from r0013; the green footer starts play. This screen belongs to another record, not the setup of the walkthrough deal. |
| G04 | One help page from r0013. The local original prose is not transcribed; scrolling and keyboard controls remain bounded. |
| G05 | Ordinary score navigation from r0013. The displayed zeros are sample values, not proof of a stored game result. |
| G06 | Loss-notice view from r0013. The bottom line is clipped; no exact threshold is reconstructed from its pixels. |
| G08 | Worked turn, step 1: country 17 selected; board total 2, allocation 0, available pool 2. |
| G09 | Worked turn, step 2: allocation 2 chosen; the board country and available pool still show 2. |
| G10 | Worked turn, step 3: placement committed; country 17 shows 4 and the action menu is visible. |
| G11 | Worked turn, step 4: attack-ready source 17 versus target 18, compared as 4 against 3. Readiness is not capture. |
| G12 | Worked turn, step 5: the comparison changes to 4 against 2 and country 18 now shows 2 on the board. Source 17 remains 4; ownership is unchanged. |
| G13 | Worked turn, step 6: action menu returned. No whole-turn completion or captured-country transfer is inferred. |
| G14 | Worked turn, step 7: immediately after Pass, Yellow is active and country-counting feedback is shown. No completed computer turn is depicted. |

Every one of the twenty-one survey observations is retained verbatim from main’s own-word [visual survey](../../docs/prototypes/T64/visual-source-survey-r2.json) in [guide.json](guide.json), with a bounded annotation. The local edition adds those observations and unchanged screenshots; their original help text is not transcribed here. Sources establish distinct evidence tiers, not a promise that every procedure has been visually tested.

Read the [rules/reference](reference.md), [coverage and gaps](coverage.md) and [planning checklist](checklist.md) for the full manual context.
