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
by this synthesis. The [E023 source survey](../experiments/E023-pro-map-presentation/measurements/source-survey-r1.json)
adds main's local checks: S01–S12 identify static sources by SHA-256, V01–V06 identify
preserved frames by record/manifest/output hashes, and O01–O07 give own-word observations.
The immutable survey was preserved in commit `941db8e`, SHA-256
`4b31fdd2da536c91d295afe279716e5bf5e7eeac905b3f8d22fcab8e71190791`.
All inspected frames are 800 by 600 native pixels. A source identifier or image hash proves
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
claimed. E023 `static_search` reports no hits for six named drawing/shape primitives
over 213 decompiled scripts (corpus manifest SHA-256 recorded there). Its `cast_metadata`
log, SHA-256 `453642556bf437afe72ef56174934d5e13a325f1d872f4ac81be0e8e988aa6e2`,
does not associate any visible stroke with a verified asset type or score channel.
This favours no direct handler drawing by those searched primitives, not a proof that
all possible drawing is absent. Baked artwork versus independent score sprites/shapes
remains unknown: no score/bitmap decoder was run. Seeing a straight line cannot choose
among these mechanisms.

### 2. What identifies an endpoint, and is a midpoint rule evidenced?

**Existing static evidence:** F017 Q-MAP-08 says position tables place a selection marker;
its Alternatives considered explicitly leaves hit-area mapping to undecoded score layout.
Neither country marker coordinates nor adjacency entries are a coastline endpoint.

**Reported visual observation:** F020 Q-UI-01 describes links at board scale but does not
identify endpoint-specific coast locations, orientations, inward extensions or endpoint
symbols. Q-UI-08's selected-country arrow is a selection cue, not evidence of an endpoint
marker on every crossing.

**Survey observation:** E023 O01/O02 (V01) identifies shore contact, straight continuation
and nearby country-index circles as cues. The short 26–27 crossing is isolated; the
diagonal 1–13 contacts the upper country above country 12. These identifications use
F017 adjacency as a cross-check, not a blind perceptual test. Confidence is high for
main's interpretation of these examples, not for universal player comprehension.

**Answer/confidence/limit:** these sources do not establish midpoint placement, a
coast-normal orientation rule, or a general inward-extension rule (O04).
Confidence is high that the cited sources
cannot support an algorithmic midpoint claim; the game's actual authoring method is
unknown, not disproved. A coastline midpoint is only a possible original-design choice.

### 3. Which alternatives are clear or ambiguous, and what are the measured ranges?

**Existing source boundary:** F017's inter-island edge table identifies graph pairs.
Its What this does not establish explicitly excludes country shapes and correspondence
between visible touching/lines and the graph. F020 Q-UI-01's overview does not enumerate
visually identified pairs or nearby competing countries.

**Clear examples (O02/V01):** 26–27's isolation and adjacent index circles distinguish
its ends; 1–13's diagonal continuation to the upper country distinguishes it from 12.
These are high-confidence observer interpretations with table context, not player-error
measurements. **Ambiguous alternatives (O03/V01):** 43–44 is longer and slanted with
contacts at textured margins; nearly vertical 23–38 meets a multi-country island where
nearby countries are plausible alternatives without labels/table context. Confidence
in this ambiguity judgment is moderate. It is not a measured failure rate or a claim
that the graph link is wrong.

**Approximate visible water spans (E023 `measurements`, V01):**

| Sample edge | Native pixels | Fraction of 800-pixel stage width |
| --- | ---: | ---: |
| 26–27 | 33.1 | 0.0414 |
| 23–38 | 54.0 | 0.0675 |
| 43–44 | 62.4 | 0.0780 |

Main manually picked centreline shore contacts and measured Euclidean distance; each
span has stated uncertainty of 4 pixels. The observed sample range is approximately
33.1–62.4 pixels (0.0414–0.0780 stage widths), for three deliberately selected spans
in one image, not a complete-board minimum/maximum or a full route length. Confidence
is moderate for approximate contact-based lengths; exact contact locations are visually
judged. No geometry is offered as a replacement map.

O04 sees no curved detour in the selected visible spans, but does not establish hidden
full-path endpoints. Minimum clearance to unrelated coasts remains unestablished without
decoded coastlines or exhaustive segmentation. A detour ratio against a coastline
midpoint baseline is unestablished because neither that baseline nor hidden path geometry
is verified. No universal gap, clearance or detour threshold follows.

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

**Survey corroboration and bounded negative case:** O05 (V02, S04–S06) links the
placement arrow at country 2 and its panel identifier to fixed-coordinate sprite 130
placement/reset in the examined branches. O06 (V03–V06, S04, S07–S12) observes defender 1
and attacker 2 identified in the panel, with counts updated, but no newly highlighted
neighbour set or changed crossing strokes in these same-run frames. The examined click
branches contain no neighbour-wide highlighting loop. Confidence is high for that bounded
static/visual correspondence, not a general absence. O07 explicitly limits this to a
same-island exchange: cross-water selection, intermediate target-selection frames, all
legal/illegal inputs, keyboard behaviour and other phases are not established.

## Limitations

- Pro/unregistered only; no DOS or registered-build claim.
- Local inspection is main's E023 survey, not direct inspection by this synthesis or a
  repository-only reviewer. Selected examples are not a completed crossing census.
- Three approximate water spans do not supply clearance, detour or midpoint rules.
  A fixed graph does not prove fixed endpoint authoring.
- Existing frame sequences sample selected states, not continuous interaction. Clipping,
  occlusion and catalogue omissions limit both positive and absence claims.
- Original bytes, images, layouts and exact geometry do not pass to malpaco.

## Affected claims

| Source / claim | Audit and permitted consequence |
| --- | --- |
| F017 Q-MAP-08/Q-MAP-09 and Alternatives: cast art / drawn lines | Retain graph and fixed-position conclusions; do not promote the general art description into proof that every crossing is baked into the background. E023 leaves artwork versus independent score objects unknown. |
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

The E023 survey supports these bounded answers, including evidenced unknowns, without a
new mechanism or run. Only reviewed, merged findings at stable commit/section citations may be returned
as research results on #255 and diegoami/malpaco#110. Malpaco owns adoption and consumer
closure. This finding changes no spec/design, constraints, topology or owner decision.
