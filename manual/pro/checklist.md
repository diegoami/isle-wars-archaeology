# UI and map planning checklist

Research handoff for [malpaco issue #191](https://github.com/diegoami/malpaco/issues/191), planning only after 0.1.x. These are qualities to assess and scenarios to discuss, not a proposed design or authorization to implement. The owner selects and approves a concrete design proposal, then separately authorizes and prioritizes implementation. Original pixels, branding, art and exact presentation remain outside Git and are not transferred.

<a id="country-readability"></a>
## Readable country identity and ownership

Player benefit: Players can distinguish who holds a country and how many armies defend it without confusing terrain with state.

Observable scenario: Inspect a crowded border in a full-board view, then a selected country; identify its number, owner and stack independently without relying on colour alone.

Evidence: derived planning consideration; [ATLAS](../../manual/pro/atlas.json), [GUIDE](../../manual/pro/guide.json). Reference: [board](reference.md#board), [interface](reference.md#interface).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="topology"></a>
## Legible adjacency and group membership

Player benefit: Players can assess a legal neighbouring attack and the income consequence of completing a group.

Observable scenario: Compare two visually close countries and one cross-group link against legal adjacency; explain the bonus that changes on full ownership.

Evidence: derived planning consideration; [F017](../../findings/F017-pro-board-rules.md), [ATLAS](../../manual/pro/atlas.json). Reference: [board](reference.md#board), [income](reference.md#income).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="active-phase"></a>
## Clear active seat and phase

Player benefit: Players know whose decision is pending and whether armies are still unplaced.

Observable scenario: Follow placement commit through the action menu and next-seat frame without treating a return arrow as the end of the current human turn.

Evidence: derived planning consideration; [GUIDE](../../manual/pro/guide.json), [G2](../../docs/prototypes/T64/visual-source-survey-r2.json). Reference: [turns](reference.md#turns), [interface](reference.md#interface).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="allocation"></a>
## Allocation amount and remainder feedback

Player benefit: Players can commit the intended reinforcement split and notice waste at a stack cap.

Observable scenario: Choose part of a pool, cancel a selection, then commit; distinguish chooser amount, country count and remaining pool, including 998 plus 2.

Evidence: derived planning consideration; [GUIDE](../../manual/pro/guide.json), [F013](../../findings/F013-pro-reinforcement-rules.md). Reference: [income](reference.md#income).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="combat-feedback"></a>
## Separate selection, exchange and ownership feedback

Player benefit: Players can tell a casualty from capture and assess the cost of continuing an attack.

Observable scenario: Compare G11 and G12: defender decreases but owner does not change; separately list the unillustrated capture and human-forfeit consequences that would require different feedback.

Evidence: derived planning consideration; [GUIDE](../../manual/pro/guide.json), [F011](../../findings/F011-pro-combat-rules.md). Reference: [combat](reference.md#combat), [capture](reference.md#capture).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="movement-boundary"></a>
## Visible commitment and end-turn boundary

Player benefit: Players do not accidentally end a turn while trying to reposition or return to a menu.

Observable scenario: At a move choice, explain what can be cancelled before commit and that a completed ordinary move ends the turn; original completed-move screen is unobserved.

Evidence: derived planning consideration; [GUIDE](../../manual/pro/guide.json), [F011](../../findings/F011-pro-combat-rules.md). Reference: [movement](reference.md#movement), [interface](reference.md#interface).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="cards-effects"></a>
## Distinct card roles, matching and pool arithmetic

Player benefit: Players can distinguish the draw hazard, traded bomb, protection and reinforcement effects.

Observable scenario: Describe a two-wildcard match, invalid three-wildcard hand and doubling after bonuses; identify the missing illustrated trade screen and the limit on using this static comparison.

Evidence: derived planning consideration; [F014](../../findings/F014-pro-cards-rules.md), [GUIDE](../../manual/pro/guide.json). Reference: [cards](reference.md#cards), [trades](reference.md#trades), [bombs](reference.md#bombs).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="centre-events"></a>
## Explain centre benefit and event conditions

Player benefit: Players avoid expecting passive centre income or treating event probability as a guarantee.

Observable scenario: Before and after a hypothetical eligible transition, state passive income unchanged and possible capped centre doubling; no original event screen is supplied.

Evidence: derived planning consideration; [F013](../../findings/F013-pro-reinforcement-rules.md), [F015](../../findings/F015-pro-centres-hazards-rules.md), [V3](../../docs/prototypes/T63/visual-source-survey-r3.json). Reference: [centres](reference.md#centres), [events](reference.md#events).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="results-persistence"></a>
## Distinguish result, preferences and position persistence

Player benefit: Players know whether leaving a game loses progress and what a default-save action preserves.

Observable scenario: Read defaults save, score counters and loss notice separately; explain why none of those three recorded views offers a demonstrated Pro position restore.

Evidence: derived planning consideration; [GUIDE](../../manual/pro/guide.json), [F019](../../findings/F019-pro-setup-rules.md), [F012](../../findings/F012-pro-turn-victory-rules.md). Reference: [persistence](reference.md#persistence), [endings](reference.md#endings).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="navigation"></a>
## Readable chapters with explicit evidence gaps

Player benefit: Players can reach the action guide, rules and map and recognize when an instruction is static-only.

Observable scenario: Use book contents to open placement, worked turn, atlas, rules and coverage; inspect an unobserved capture or event topic without a fabricated image.

Evidence: derived planning consideration; [GUIDE](../../manual/pro/guide.json), [ATLAS](../../manual/pro/atlas.json). Reference: [interface](reference.md#interface), [history](reference.md#history).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

<a id="limits"></a>
## Honest locked-control and unknown-state boundaries

Player benefit: Players do not mistake unavailable registered choices or historical DOS procedures for usable Pro controls.

Observable scenario: Compare unregistered setup with stated locks, then locate keyboard/disabled-state and registered-screen gaps; no unseen screen is reconstructed or assumed to behave like an unlocked registered control.

Evidence: derived planning consideration; [F019](../../findings/F019-pro-setup-rules.md), [GUIDE](../../manual/pro/guide.json). Reference: [setup](reference.md#setup), [history](reference.md#history), [interface](reference.md#interface).

Planning input only for malpaco #191 after 0.1.x; owner approves proposal and separately authorizes implementation. No original assets or exact presentation transfer.

