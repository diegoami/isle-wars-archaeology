# Coverage and evidence boundaries

Coverage means a subject has an explanation or an explicit gap. It does not mean every screen was observed, every static path exercised, or an unknown resolved. Source ranges are paraphrased structure from main’s survey; no original text is reproduced.

## Original-manual subjects

| ID | Subject and source lines | Reference sections |
| --- | --- | --- |
| M01 | front-matter and version identity (1–7) | [history](reference.md#history) |
| M02 | winning condition (8–16) | [objective](reference.md#objective), [endings](reference.md#endings) |
| M03 | new-game setup, starting state and turn resources (17–38) | [setup](reference.md#setup), [income](reference.md#income) |
| M04 | placing reinforcements (39–50) | [income](reference.md#income) |
| M05 | combat selection and exchanges (51–92) | [combat](reference.md#combat), [capture](reference.md#capture) |
| M06 | troop relocation step (93–98) | [movement](reference.md#movement) |
| M07 | ending a turn (99–104) | [turns](reference.md#turns) |
| M08 | backing out of a selection (105–110) | [interface](reference.md#interface), [capture](reference.md#capture) |
| M09 | card awards and effects (111–137) | [cards](reference.md#cards), [bombs](reference.md#bombs) |
| M10 | exchanging sets of cards (138–163) | [trades](reference.md#trades) |
| M11 | random events and production locations (164–185) | [events](reference.md#events), [centres](reference.md#centres) |
| M12 | game ending and result handling (186–198) | [endings](reference.md#endings), [persistence](reference.md#persistence) |
| M13 | persistent game navigation controls (199–220) | [interface](reference.md#interface), [persistence](reference.md#persistence) |
| M14 | registered-edition distinctions (221–234) | [setup](reference.md#setup), [history](reference.md#history) |
| M15 | historical ordering appendix, not gameplay or current purchase advice (235–252) | [history](reference.md#history) |

## Nineteen Pro spec areas

Shared files can include DOS rows; those do not support Pro rules. Representation and runtime are covered with their experimental boundaries.

| Area | Reference sections | Source |
| --- | --- | --- |
| board | [board](reference.md#board) | [S-board](../../spec/board.md) |
| cards | [cards](reference.md#cards), [trades](reference.md#trades), [bombs](reference.md#bombs) | [S-cards](../../spec/cards.md) |
| combat | [combat](reference.md#combat), [capture](reference.md#capture) | [S-combat](../../spec/combat.md) |
| computer-opponent | [ai](reference.md#ai) | [S-computer-opponent](../../spec/computer-opponent.md) |
| hazards | [events](reference.md#events) | [S-hazards](../../spec/hazards.md) |
| island-bonuses | [board](reference.md#board), [income](reference.md#income) | [S-island-bonuses](../../spec/island-bonuses.md) |
| movement | [movement](reference.md#movement) | [S-movement](../../spec/movement.md) |
| ownership | [capture](reference.md#capture), [endings](reference.md#endings) | [S-ownership](../../spec/ownership.md) |
| production-centres | [centres](reference.md#centres) | [S-production-centres](../../spec/production-centres.md) |
| reinforcement | [income](reference.md#income) | [S-reinforcement](../../spec/reinforcement.md) |
| representation | [persistence](reference.md#persistence), [history](reference.md#history) | [S-representation](../../spec/representation.md) |
| runtime | [history](reference.md#history) | [S-runtime](../../spec/runtime.md) |
| seats | [setup](reference.md#setup), [turns](reference.md#turns) | [S-seats](../../spec/seats.md) |
| setup | [setup](reference.md#setup), [persistence](reference.md#persistence) | [S-setup](../../spec/setup.md) |
| starting-state | [setup](reference.md#setup) | [S-starting-state](../../spec/starting-state.md) |
| surrender | [endings](reference.md#endings) | [S-surrender](../../spec/surrender.md) |
| turn-sequence | [turns](reference.md#turns), [events](reference.md#events) | [S-turn-sequence](../../spec/turn-sequence.md) |
| user-interface | [interface](reference.md#interface) | [S-user-interface](../../spec/user-interface.md) |
| victory | [objective](reference.md#objective), [endings](reference.md#endings) | [S-victory](../../spec/victory.md) |

## Major screens and feedback

| Area | Evidence state | Boundary | Reference |
| --- | --- | --- | --- |
| Title, options and setup | recorded | G01 G02 G03; static lock details F019. | [setup](reference.md#setup), [interface](reference.md#interface) |
| Board, status and action panels | recorded | V01–V06 and G08–G14 bounded states, separate deals explicit. | [board](reference.md#board), [interface](reference.md#interface) |
| Placement and allocation confirmation | recorded | G08–G10 shows selection and commit; no carryover rule from stills. | [income](reference.md#income) |
| Attack selection and result panel | recorded | G11–G12 sampled defender decrement; no capture shown. | [combat](reference.md#combat) |
| Capture and split dialogue | unobserved | Static intended amount path; zero-choice reachability open. | [capture](reference.md#capture) |
| Movement selection and amount dialogue | unobserved | Static-only ordinary move path, no illustrated completion. | [movement](reference.md#movement) |
| Hand, discard, trade, bomb and protection dialogue | unobserved | Static effects do not establish exact screen controls or animations. | [cards](reference.md#cards), [trades](reference.md#trades), [bombs](reference.md#bombs) |
| Turn menu, pass and next-seat status | recorded | G13–G14 ends human sample; only early next-seat feedback. | [turns](reference.md#turns) |
| Event announcement and damage feedback | unobserved | No verified event screen or timing; effects static only. | [events](reference.md#events) |
| Production increase and relocation feedback | unobserved | Cyan reference is not an illustrated production event. | [centres](reference.md#centres), [events](reference.md#events) |
| Cancel, back, commit and confirmation dialogues | partial | Some selection/menu returns recorded, not all modal confirmations. | [interface](reference.md#interface), [capture](reference.md#capture) |
| Help navigation, scores and result notice | partial | One help page, scores and clipped loss notice; no full help or terminal paths. | [interface](reference.md#interface), [endings](reference.md#endings), [persistence](reference.md#persistence) |
| Concession, elimination and victory dialogue | unobserved | Static routes only; no unseen registered or terminal dialogue invented. | [endings](reference.md#endings) |
| Position save and load screen | unsupported | No selected control; whole-corpus static search supports absence in this build. Defaults save is separate. | [persistence](reference.md#persistence) |
| Registration and unlocked controls | unobserved | Unregistered gates static; registered screen layouts not established. | [setup](reference.md#setup), [history](reference.md#history) |
| Keyboard and disabled-control feedback | unobserved | No exhaustive shortcut, focus, disabled response or hitbox evidence. | [interface](reference.md#interface) |
| Audio, animation and timing feedback | unobserved | Stills and driver cycles do not prove native audio or timing behaviour. | [interface](reference.md#interface), [history](reference.md#history) |

## Source discrepancies

These entries preserve conflicts rather than silently choosing a universal rule. #259 and #278 remain open research; event and trade wording is source-qualified.

- T04 mandatory-trade wording differs from the static human skip path. No recorded trade screen resolves every input route. [T04](../../sources/iwp-islepro-txt.md), [F014](../../findings/F014-pro-cards-rules.md).
- F015 counter arithmetic forces one empty transition after an event; F012’s loose immediate-soon gloss must not replace that arithmetic. [F015](../../findings/F015-pro-centres-hazards-rules.md), [F012](../../findings/F012-pro-turn-victory-rules.md).
- #259: logical nine-group topology does not settle apparent physical island count. [ATLAS](../../manual/pro/atlas.json), [F017](../../findings/F017-pro-board-rules.md).
- #278: main crosscheck of both images conflicts with F020 first-image colour list; neither source is silently harmonized. [V3](../../docs/prototypes/T63/visual-source-survey-r3.json), [F020](../../findings/F020-pro-ui-observations.md).

The machine-readable [manual data](manual.json) holds all section, source, gap, screen and checklist references. Structural checks cannot certify semantic truth; independent review and local visual verification remain required.
