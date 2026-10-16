# F022 Pro crossing endpoints and interaction cues: bounded evidence synthesis

- **Status:** proposed
- **Question:** the four presentation questions in request #255, for malpaco T59
  (diegoami/malpaco#110); no adoption decision is made here.
- **Experiment:** [E023](../experiments/E023-pro-map-presentation/README.md), reusing
  F017/E015 and F020/E019; no new game run.
- **Artifact:** Windows Pro unregistered `iwp-2.0-996e86c5`, variant none;
  `Islepro.exe` SHA-256
  `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`.
- **Evidence classes:** static mechanism, reported visual observation, and original-design
  inference are labelled separately below. Unknown is not an absence claim.

## Method

This repository-only synthesis reads existing findings and committed evidence metadata;
it does not inspect original captures, decompiled material or the install. Its source
baseline is commit `58cf9fe`. Static-first work already in
[F017](F017-pro-board-rules.md), especially Q-MAP-08/Q-MAP-09 and Method, establishes
the limits of script-only presentation claims: the score and cast appearance were not
decoded. Reusing that work avoids re-proving the fixed topology.

[F020](F020-pro-ui-observations.md) reports the main session's earlier visual readings
of preserved E019 frames. Those are cited as reported observations, not fresh inspection
by this synthesis. The E023 main-owned survey is required before adding new claims about
individual crossings or their construction. A source identifier or image hash proves
provenance, not what a line depicts.

Confidence below concerns only the stated, bounded claim. Static confidence is inherited
from F017, not raised by repeating it. No extra numerical confidence is assigned to
uninspected images or unknown presentation mechanisms.

## Answers

### 1. Artwork, separate sprites/shapes, or handler drawing?

**Existing static evidence:** F017 Q-MAP-08 identifies a fixed board and marker-coordinate
tables; its Method explicitly excludes cast and score decoding. Q-MAP-09 establishes
ordinary adjacency entries, not a crossing-rendering representation. Its general
description of the map as cast bitmap art does not, on its own, identify the storage or
construction of each visible sea link.

**Reported visual observation:** F020 Q-UI-01 describes pale straight sea links in
`E019-r0014`, `board-1.png`; see the
[record](../runs/E019/board-pieces/E019-r0014.json) and
[manifest](../evidence/E019/board-pieces/E019-r0014.manifest.json).
That supports visible lines only, not whether the lines share a bitmap with the sea,
are independent sprites/shapes, or are drawn by a handler.

**Answer/confidence/limit:** construction is unestablished by these repository sources.
Confidence is high in that evidentiary limitation; no positive construction choice is
claimed. Main's static source survey must delimit any stronger reading and undecoded
score/cast remainder. Seeing a straight line cannot choose among these mechanisms.

### 2. What identifies an endpoint, and is a midpoint rule evidenced?

**Existing static evidence:** F017 Q-MAP-08 says position tables place a selection marker;
its Alternatives considered explicitly leaves hit-area mapping to undecoded score layout.
Neither country marker coordinates nor adjacency entries are a coastline endpoint.

**Reported visual observation:** F020 Q-UI-01 describes links at board scale but does not
identify endpoint-specific coast locations, orientations, inward extensions or endpoint
symbols. Q-UI-08's selected-country arrow is a selection cue, not evidence of an endpoint
marker on every crossing.

**Answer/confidence/limit:** these sources do not establish midpoint placement, a
coast-normal orientation rule, or a general inward-extension rule. Endpoint-by-endpoint
visual identification requires main's survey. Confidence is high that the cited sources
cannot support an algorithmic midpoint claim; the game's actual authoring method is
unknown, not disproved. A coastline midpoint is only a possible original-design choice.

### 3. Which alternatives are clear or ambiguous, and what are the measured ranges?

**Existing source boundary:** F017's inter-island edge table identifies graph pairs.
Its What this does not establish explicitly excludes country shapes and correspondence
between visible touching/lines and the graph. F020 Q-UI-01's overview does not enumerate
visually identified pairs or nearby competing countries.

**Answer/confidence/limit:** no individual clear or ambiguous crossing is newly asserted
from that overview. Main's survey must supply identified positive cases and ambiguous or
occluded cases before a case comparison is warranted. Graph membership alone cannot
decide which of two nearby shores a viewer perceives as attached.

Water gaps, route clearance and detours are unestablished by the cited repository-only
sources. There is no defensible range or normalization to report from marker-coordinate
distances or E019's colour censuses. Confidence is high in this measurement limitation;
there is no claim that Pro has zero detours or uniformly clear endpoints. Measurements
require known display geometry, identified shores/routes, units and sample/error limits,
as explained in E023. No universal threshold is inferred.

### 4. What feedback clarifies source, target and legal neighbours?

**Static mechanism:** F017 Q-MAP-04 reports adjacency validation and refusal paths in
`BehaviorScript 400 / mouseDown()`; Q-MAP-08 reports marker placement. This does not
prove that all legal neighbours or crossings receive a visible highlight at runtime.
Confidence remains F017's bounded static reading (about 85% for reader/absence scope).

**Reported observations:** F020 Q-UI-08, `E019-r0025`, describes a selected-country arrow
during placement and source/target identification plus stack comparison in attack-ready
and result panels. It also notes a partially clipped source line. Q-UI-12, `E019-r0026`,
reports another source/target panel sequence and clearing of side texts at turn-menu
return. These are positive cases for explicit pair feedback; neither establishes a
legal-neighbour overlay or crossing-specific feedback. Confidence is bounded to the
catalogue's recorded sequences, not all phases or pairs.

**Negative/unknown boundary:** [design/ui.md](../design/ui.md), UW-6, explicitly says whether
Pro marks legal targets is not established. Absence from a catalogue description is not
proof that the feature never appears. Neither cited attack pair is presented here as a
demonstration of an inter-island crossing. Crossing-selection changes and comprehensive
legal-neighbour feedback remain unknown from these sources.

## Limitations

- Pro/unregistered only; no DOS or registered-build claim.
- No fresh local visual/static survey is supplied by this repository-only synthesis.
  The four answers above delimit existing evidence, not a completed crossing census.
- No source geometry, route tracing, coast sampling, pixel-derived range, or rendering
  mechanism has been fabricated. A fixed graph does not prove fixed endpoint authoring.
- Existing frame sequences sample selected states, not continuous interaction. Clipping,
  occlusion and catalogue omissions limit both positive and absence claims.
- Original bytes, images, layouts and exact geometry do not pass to malpaco.

## Affected claims

| Source / claim | Audit and permitted consequence |
| --- | --- |
| F017 Q-MAP-08/Q-MAP-09 and Alternatives: cast art / drawn lines | Retain graph and fixed-position conclusions; do not promote the general art description into proof that every crossing is baked into the background. Main's survey must qualify construction separately. |
| F017 Q-MAP-09's proposed display check | A proposed corroboration is not an observed census. No completeness claim follows from it. |
| F020 Q-UI-01: about 46 territories on ten islands | F017's static grouping is nine islands. The visual wording is not a new topology result; retain this discrepancy explicitly for main's claim-level follow-up, not an out-of-scope edit here. |
| F020 Q-UI-08/Q-UI-12: selection and combat panels | Supports pair feedback in those sequences; not a legal-neighbour or sea-link highlighting claim. |
| design/ui.md UW-6: legal-target marking unestablished | Remains an appropriate predecessor limitation from the existing corpus. |
| design/ui.md Attacks / Move / Legal and illegal actions | Malpaco's marked legal choices are designed requirements, not observed Pro behaviour. No design change authorized. |
| design/ui.md Islands and bonuses / The look | Sea-link clarity is a malpaco requirement/art direction, not evidence of a Pro midpoint or clearance algorithm. |

## Handoff

**Permitted original-design implications (inferences, not Pro facts):** keep graph legality
separate from visual attachment; assess whether each endpoint identifies the intended
country rather than merely avoiding geometric intersections. Explicit source/target
feedback can complement passive route cues, as the reported combat panels illustrate.
Midpoint placement, extra endpoint marks, neighbour overlays and clearance thresholds
would be malpaco design choices requiring its own evaluation, not copied predecessor rules.

Main's E023 source survey and its per-answer synthesis are required for a completed T57
return. Only reviewed, merged findings at stable commit/section citations may be returned
as research results on #255 and diegoami/malpaco#110. Malpaco owns adoption and consumer
closure. This finding changes no spec/design, constraints, topology or owner decision.
