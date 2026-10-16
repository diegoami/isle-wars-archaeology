# E023 Pro map presentation source survey and synthesis

- **Task:** T57; request #255, consumer diegoami/malpaco#110 (T59).
- **Question:** crossing-mark construction, endpoint cues, clear/ambiguous alternatives,
  and source/target/legal-neighbour feedback, each answered separately in
  [F022](../../findings/F022-pro-map-presentation.md).
- **Scope:** Windows Pro, unregistered build; reuse of existing static findings and
  preserved captures only. No new game run, decoder, topology proof or design change.
- **Artifact:** F017's `iwp-2.0-996e86c5`, variant none; executable SHA-256
  `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`.

## Method and division of evidence

Static first: reuse F017/E015's distinction between adjacency, marker coordinates and
undecoded cast/score presentation. F020/E019 supplies already-written visual observations
and committed run/manifest identifiers. A repository-only reader can check those
citations, but cannot turn a manifest hash into a fresh visual observation.

The main session owns the local survey and its immutable
`measurements/source-survey-r1.json`: checked source identifiers and hashes, committed
record/manifest/output hashes for reused captures, own-word observations, display geometry,
and any measurement method. Do not create a placeholder survey, copy original bytes or
include local install paths. Later survey batches get new filenames, never overwrite r1.
The synthesis must identify which survey entries support each new visual/static claim.

## Repository-only source index

- [F017](../../findings/F017-pro-board-rules.md): Q-MAP-04, Q-MAP-08, Q-MAP-09 and
  Method / What was not read. Fixed marker positions do not define coastline endpoints.
- [E015 tabulation](../E015-pro-board-reading/measurements/board-tabulation-r1e.json):
  existing graph data only; not coastlines, route polylines or hit-area geometry.
- [F020 UI catalogue](../../findings/F020-pro-ui-observations.md): Q-UI-01's pale
  straight links, Q-UI-08/Q-UI-12's selected-country and combat panels; no established
  legal-neighbour highlighting claim.
- [E019-r0014](../../runs/E019/board-pieces/E019-r0014.json) and
  [manifest](../../evidence/E019/board-pieces/E019-r0014.manifest.json): board image provenance.
- [E019-r0025](../../runs/E019/play/E019-r0025.json) and
  [manifest](../../evidence/E019/play/E019-r0025.manifest.json): placement and combat sequence.
- [E019-r0026](../../runs/E019/play/E019-r0026.json) and
  [manifest](../../evidence/E019/play/E019-r0026.manifest.json): a second phase sequence.
- [UI design](../../design/ui.md): predecessor limitations versus malpaco's designed feedback.

## Measurement boundaries

No gap, clearance or detour range is inferred from country marker coordinates: these
are not coast or route endpoints. Pixel counts in E019 are colour/luminance censuses,
not water distances. Reliable visual measures require identified shores and routes,
known capture geometry and a stated tracing/error method in main's survey. If these
cannot be supplied, the measures stay unestablished; no universal threshold follows.
An occluded or unidentified line is not a negative adjacency observation.

## Validation

The task commands are `python3 -m json.tool` on the main-owned survey, the F022
nonempty/heading checks, `python3 tools/check_links.py`,
`python3 tools/check_no_originals.py`, and `git diff --check`. No new executable tests
are needed for prose. CI and source-tracing judgment remain separate completion gates.
