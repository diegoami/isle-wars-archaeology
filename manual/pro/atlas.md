# Pro map and UI atlas

This own-word reference covers unregistered Windows Pro. The illustrated local edition pairs the prose below with six preserved E019 images, seventeen observational callouts and bounded detail views. Original pixels stay outside every checkout. See [the edition instructions](README.md) and [whole-manual inventory](inventory.json).

The four same-record interaction views V02–V05 show selection, chosen allocation, attack readiness and the action menu. V01 is a full-board overview from another deal; V06 is a separate colour-cue reference. There is no implied before/after continuity between those separate records.

## Map

**M-size** Treat a country as the numbered unit that owns armies. F017 counts 46 such units in the fixed board tables; this is a static result, not a new visual census.

Layer: topology; confidence: static-high. Sources: [F017-size](../../findings/F017-pro-board-rules.md#the-boards-size).

**M-groups** The rules partition those countries into nine logical island groups. Their sizes are 3, 5, 5, 10, 3, 7, 3, 7 and 3; complete-group ownership is a rules concept, so use the recorded memberships rather than counting separated land silhouettes.

Layer: topology; confidence: static-high. Sources: [F017-groups](../../findings/F017-pro-board-rules.md#the-islands).

**M-objective** The publisher describes taking control of all nine island groups as the objective. That is documented intent; the atlas does not re-test victory handling.

Layer: scope; confidence: documented. Sources: [D-objective](../../sources/iwp-islepro-txt.md#objective).

**M-links** F017 tabulates 80 undirected border links, represented by 160 directed entries. Every link is reciprocal and the graph is connected. A water crossing uses the ordinary adjacency relation; the tables do not label a special sea-movement category.

Layer: topology; confidence: static-high. Sources: [F017-links](../../findings/F017-pro-board-rules.md#adjacency).

**M-fixed** F017 finds one fixed board and fixed per-country marker positions in this unregistered build. A new deal can change owners and armies without supplying another layout. Marker coordinates locate a selection cue; they do not define a country outline or its click region.

Layer: topology; confidence: static-high. Sources: [F017-fixed](../../findings/F017-pro-board-rules.md#one-board-fixed).

## Reading the board

**B-look** F020 reports relief-textured country fills above the lower control panels, with pale straight strokes crossing blue water. The fills use blue, yellow, red and green ownership tints. These are reported visual observations of the preserved Pro screens, not reusable map artwork.

Layer: appearance; confidence: high-bounded. Sources: [F020-board](../../findings/F020-pro-ui-observations.md#board-and-pieces).

**B-numbers** Distinguish the small country-index circles from the larger army digits. F020 describes ordinary army digits as white with dark outlines; these labels answer different questions: which country is this, and how many armies does it display?

Layer: appearance; confidence: high-bounded. Sources: [F020-board](../../findings/F020-pro-ui-observations.md#board-and-pieces).

**B-centres** The directions associate light-blue army totals with production centres. F020 Q-UI-02 separately reports three cyan digits in each of two inspected centre frames and rates that interpretation about 80% likely. V06 separately shows a cyan numeral, while centre identity remains an interpretation qualified by those sources; neither a centre flash nor a mechanical effect is established by the stills.

Layer: appearance; confidence: moderate-bounded. Sources: [D-centres](../../sources/iwp-islepro-txt.md#situations-disasters-and-production-centres), [F020-board](../../findings/F020-pro-ui-observations.md#board-and-pieces).

**B-totals** F020 Q-UI-08 describes a persistent upper-left box with four colour-coded player rows, territory/card figures and an active-row marker. Its figures belong to the captured deal; neither their displayed values nor the active row are atlas constants.

Layer: appearance; confidence: high-bounded. Sources: [F020-play](../../findings/F020-pro-ui-observations.md#play).

**B-crossings** A visible water stroke is a route cue, while graph legality comes from the border tables. F022 identifies shore contact, straight continuation and nearby country-index circles as useful cues in selected examples; it does not establish that every endpoint is equally clear.

Layer: appearance; confidence: high-bounded. Sources: [F022](../../findings/F022-pro-map-presentation.md#answers), [F017-links](../../findings/F017-pro-board-rules.md#adjacency).

**V-O01** The map occupies almost the full width above the lower control strip. Irregular land clusters are separated by blue water; the entire scene has a silver-blue beveled surround.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O02** Land has a strongly embossed, mottled relief appearance with jagged bright coastlines and a cyan-white coastal glow. This is visible artwork; no claim is made about 3D geometry or how the original engine stores it.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O03** The sea has a mottled square-like blue texture, with brighter blue around the coast; it is visually distinct from the coloured relief land.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O04** Solid pale straight strokes span water between land areas; their ends meet or disappear against the coastal artwork. No arrowheads, path animation, exact endpoint construction or procedural midpoint rule is established by this still frame.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O05** Territory regions carry red, green, yellow/ochre and blue/purple tints. Dark relief seams and colour transitions partition the land. The screenshot does not establish the logical grouping or adjacency of every apparent cluster.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O06** Small black circular labels with fine white identifiers are visually separate from much larger light army-count digits over the territories. The two text scales make identity and army strength distinct.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O07** A black framed overlay in the upper-left lists four colour-coded player rows, each with a territory total and a card total. A small pale pointer marks the top player row in this image.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O08** A large light title is centered toward the upper-right, with a smaller publisher/edition notice at the top-right. These are reference-image branding, not reusable malpaco assets.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O09** Three framed panels run along the bottom: instruction/context at left, phase-dependent controls at center, and player/phase information at right. Their dark blue backgrounds and bright text separate them from the board.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O10** A persistent row of six text navigation choices runs along the bottom edge beneath the phase panels; the board remains visible above them.

Layer: appearance; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O17** Some large army-count numerals are pale cyan rather than ordinary light white; the numeral 3 on territory 18 is a bounded visible example. Territory 2 has a white numeral in this frame, contrary to r1. The production-site interpretation is source-qualified to F020 Q-UI-02 and the manual; the screenshot alone does not establish that mechanism or a flashing animation.

Layer: appearance; confidence: moderate-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

## Interaction states

**I-selected** A selected-country arrow and lower-panel country identifier are evidenced placement feedback in F020 Q-UI-08 and F022. They identify a selected country; they do not establish a display of every legal neighbour.

Layer: interaction; confidence: high-bounded. Sources: [F020-play](../../findings/F020-pro-ui-observations.md#play), [F022](../../findings/F022-pro-map-presentation.md#answers).

**I-allocation** F020 Q-UI-08 distinguishes the quantity allocated in the lower controls from the armies already displayed on the selected country. In its recorded example the allocation changes before the committed-placement frame changes the board total. This is one observed sequence, not a general timing guarantee.

Layer: interaction; confidence: high-bounded. Sources: [F020-play](../../findings/F020-pro-ui-observations.md#play).

**I-combat** The recorded attack-ready panel identifies an attacking country and a defending country, presents battle controls and compares their stacks. F020 Q-UI-08 notes a clipped lower line; the atlas does not reconstruct obscured wording or treat every line as readable.

Layer: interaction; confidence: high-bounded. Sources: [F020-play](../../findings/F020-pro-ui-observations.md#play).

**I-return** F020 Q-UI-08/Q-UI-12 show a return from combat-side feedback to the turn-action panel. Returning to that panel does not by itself mean that the whole human turn or game has finished.

Layer: interaction; confidence: high-bounded. Sources: [F020-play](../../findings/F020-pro-ui-observations.md#play).

**V-O11** The left panel identifies the selected territory; the central panel becomes an allocation amount with an all-available choice, increment/decrement controls and a placement confirmation. The right panel reports the remaining allocation. The amount is zero in this frame.

Layer: interaction; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O12** The same allocation panel now displays an amount of two, with the all-available control highlighted. The right panel still reports two available armies. This is an allocation-choice view, not proof that those armies have already been committed.

Layer: interaction; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O13** A yellow rightward arrow with a red outline is visible just to the right of the player overlay. Its visual presence is established; this still image alone does not prove its timing, animation or hit area.

Layer: interaction; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O14** The center panel changes to a prominent red attack control and a yellow control for leaving that mode. The side panels identify the two selected countries and display their opposing army totals; this is a pre-attack/attack-ready view, not a capture result.

Layer: interaction; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O16** Across V02–V05 the same board deal remains recognizable while the bottom controls and status texts change. V01 and V06 come from other records/deals and must not be presented as before/after frames of that sequence.

Layer: interaction; confidence: moderate-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

**V-O15** The central bottom panel instead presents five compact phase/action choices, visibly using red, cyan, white, green and yellow surfaces. This is a distinct turn-menu state, not the allocation or attack-ready panel.

Layer: interaction; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json).

## Evidence boundaries

**E-hit** The annotated rectangles are approximate native-pixel regions observed by main in preserved screenshots. They are viewing aids only. A drawn button, a country marker, and the actual active input area are three different things; the atlas supplies no measured hitboxes.

Layer: hit-area; confidence: high-bounded. Sources: [V-survey](../../docs/prototypes/T63/visual-source-survey-r2.json), [F017-fixed](../../findings/F017-pro-board-rules.md#one-board-fixed).

**E-render** The local edition places unchanged, hash-verified PNG files behind code-native SVG rectangles and detail images explicitly clipped to their observed native-coordinate rectangles. This describes the atlas renderer only; it supplies no evidence for how the original game stores or draws its map.

Layer: rendering; confidence: high-bounded. Sources: [R-tool](../../tools/manual/render_atlas.py).

**E-scope** This atlas covers preserved unregistered Windows Pro evidence. It makes no DOS, registered-build, native-Windows accessibility, sound-content or complete-game claim. T64 and T65 carry later manual material; an inventoried subject is not a claim that its chapter has already been written.

Layer: scope; confidence: high-bounded. Sources: [D-whole](../../sources/iwp-islepro-txt.md), [F020-limits](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

**U-islands** The relationship between visually separated land masses and the nine logical groups remains unresolved under #259. F020 describes ten apparent islands; the atlas retains that discrepancy instead of silently changing the static group count or presenting a new visual census.

Layer: topology; confidence: unknown. Limitation references: [F022-audit](../../findings/F022-pro-map-presentation.md#affected-claims).

**U-hit** Exact country/button hit regions, keyboard alternatives and exhaustive illegal-input feedback remain unestablished here. Pending F020 input walks and the original score layout cannot be replaced by the atlas callout rectangles.

Layer: hit-area; confidence: unknown. Limitation references: [F020-limits](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish), [F017-fixed](../../findings/F017-pro-board-rules.md#one-board-fixed).

**U-mechanism** Whether individual water strokes are baked into background artwork, independent score objects, or another rendering arrangement remains unknown. Straight appearance and fixed adjacency cannot select a storage mechanism or prove a coastline-midpoint algorithm.

Layer: rendering; confidence: unknown. Limitation references: [F022-limits](../../findings/F022-pro-map-presentation.md#limitations).

**U-neighbours** A comprehensive legal-target overlay and crossing-specific selection feedback remain unestablished. The cited sampled pair feedback does not prove that such overlays never occur in another phase, nor demonstrate a cross-water interaction.

Layer: interaction; confidence: unknown. Limitation references: [F022-limits](../../findings/F022-pro-map-presentation.md#limitations).

**U-events** Random-event identity, event animation durations and event-history presentation are not established by these six atlas frames. Candidate pixel changes in narrowed F020 watches are not identified disasters; pending catalogue entries remain pending.

Layer: interaction; confidence: unknown. Limitation references: [F020-limits](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

**U-registration** The atlas does not establish the registered build or every locked-option transition. The directions list registration features, but a documented possibility is not an observed control state in this unregistered evidence.

Layer: scope; confidence: unknown. Limitation references: [F020-limits](../../findings/F020-pro-ui-observations.md#what-this-does-not-establish).

## Views and feature inventory

| View | Preserved state | Role |
| --- | --- | --- |
| V01 | initial-placement-separate-deal | full-board |
| V02 | placement-selection | interaction-state |
| V03 | placement-allocation-chosen | interaction-state |
| V04 | attack-ready | interaction-state |
| V05 | turn-menu | interaction-state |
| V06 | centre-colour-reference-separate-deal | detail-reference |

Every observation in main’s [immutable visual survey](../../docs/prototypes/T63/visual-source-survey-r2.json) is represented as a visual feature in [inventory.json](inventory.json), an appearance/interaction claim above, and a rectangular annotation in [atlas.json](atlas.json). This is completeness relative to the inspected survey, not a claim to have found every feature or screen in the game. The manual subjects cover all fifteen paraphrased document ranges; later-part assignments are evidence boundaries, not finished chapters.
