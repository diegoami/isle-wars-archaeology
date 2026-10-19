# Pro manual: guide, atlas and rules

Begin with the [player guide and worked turn](guide.md), then consult the substantive
[rules/reference](reference.md), [coverage and gaps](coverage.md), and
[UI/map planning checklist](checklist.md). The reference has eighteen sections,
covering all fifteen original-manual subject ranges and nineteen Pro spec areas.
Each paragraph identifies its sources, evidence tier and confidence. Coverage
includes missing screens; it never turns an unobserved procedure into visual proof.

The checklist gives eleven player benefits and observable comparison scenarios.
It is planning input only for [malpaco #191](https://github.com/diegoami/malpaco/issues/191)
after 0.1.x: the owner must approve a proposal and separately authorize implementation.
No adoption, design or original-asset transfer is implied. Main alone accepts and
closes parent #265 after review and its full acceptance audit.

The guide covers twelve topics and thirteen distinct recorded screens with twenty-one
callouts, including seven ordered placement-to-pass steps. Context pictures belong
to a separate record. Its [data](guide.json) keeps per-aspect evidence and unknowns.
The [manual data](manual.json) carries reference paragraphs, subject/spec/screen
coverage, conflicts and checklist entries. Documentation intent, static behaviour,
observed stills, conditional calculations and unresolved gaps remain separate.

Read the own-word [map/UI atlas](atlas.md), its [claim and annotation data](atlas.json),
and the [complete-manual subject/feature inventory](inventory.json). The atlas retains the T63 map/UI scope alongside the T64 guide and T65 reference.
Subject ranges derive from main's local reading of the original directions structure;
the repository contains paraphrases and existing T04 source notes only.

The checked edition contains six preserved image references: a full-board overview,
four distinct interaction states from one E019 record, and a separate colour reference.
It adds seventeen callouts and bounded detail views. V01 and V06 are separate deals;
they are not before/after frames of V02–V05. Every claim carries a source and bounded
confidence; unknowns carry limitation references instead of affirmative evidence.
Appearance, graph topology, input areas and original rendering are kept separate.
The active visual survey is r3; r1/r2 remain unchanged. Main reopened both
hash-verified Q-UI-02 centre images: both show cyan digits on 9, 18 and 46, with
white digits on 2, 3 and 30. This conflicts with F020's first-image list; follow-up
[#278](https://github.com/diegoami/isle-wars-archaeology/issues/278) tracks that
out-of-scope finding correction. V06 annotates territory 18's cyan 3; production-site
meaning remains source-qualified. The [r3 local verification](../../docs/prototypes/T63/local-visual-verification-r3.json)
confirms the explicit source-conflict disclosure, neutral arrow label and preserved
clipping across all six views and seventeen callout/detail regions. Earlier local
verification records remain unchanged.
#259's physical/visual island-count discrepancy remains open in the prose.

## Repository-only checks

Run test/render subprocesses on this host with the repository's memory cap:

```sh
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/check_atlas.py
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/check_atlas.py --self-test
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/render_atlas.py --self-test
```

The checker reconciles claims, text, inventory, survey observations, image manifests,
records and annotation rectangles. Synthetic controls remove a feature/source, corrupt
bounds, promote an unknown, alter hashes, remove a subject and introduce filler prose.
The renderer uses an invented two-pixel PNG for its location/hash/dimension refusal
controls. Synthetic fixtures use `/tmp` explicitly, so an inherited `TMPDIR` inside a checkout
does not make the renderer refusal controls reject their own baseline. No original
image is needed by these checks or by the reviewer. Wide and tall detail
controls also verify that the source image binds to an exact `userSpaceOnUse`
clip rectangle, and reject eight mutations that remove its binding/definition, change
its coordinate space or expose surrounding pixels.

These checks prove structural accounting. They cannot judge whether the prose faithfully
interprets an image or whether main's selected rectangle aligns with the intended feature.
Independent prose review and main's local visual check are required.

## Local illustrated edition — main session only

Keep E019 bundles and output outside **every** checkout. Do not fetch, unpack or copy
original images into a worktree. Main alone prepares a local JSON object mapping survey
frame IDs to absolute PNG paths. Use the hash-prefixed `asset` names in the
[visual survey](../../docs/prototypes/T63/visual-source-survey-r3.json) to identify files;
paths in the following example are illustrative and do not name an install:

```json
{"V01":"/outside-checkouts/E019/97c26acddb43d158-board-1.png",
 "V02":"/outside-checkouts/E019/480ec09a4122b12d-place-selected.png",
 "V03":"/outside-checkouts/E019/fc13a7505e755551-place-all.png",
 "V04":"/outside-checkouts/E019/ecd0ce15458e533f-attack-ready.png",
 "V05":"/outside-checkouts/E019/40c2a0ef169bc360-status-turn-menu.png",
 "V06":"/outside-checkouts/E019/34775bc4d7595235-board-with-centres-1.png"}
```

Choose a new, nonexistent output directory, also outside every checkout:

```sh
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/render_atlas.py --bundle-map /outside-checkouts/bundle-map.json --output /outside-checkouts/pro-atlas-r3
```

Before creating output or copying any image, the renderer validates all atlas metadata,
all mapped image SHA-256 values, PNG dimensions and locations. It resolves symlinks,
rejects paths within registered worktrees, and detects another checkout through its
`.git` marker. Missing/bad hashes, wrong dimensions and in-checkout output all fail
before copying. An existing output is refused so editions are not overwritten.

The output contains `index.html`, unchanged images and `render-receipt.json`. If a
source changes after preflight, the copy-time hash check aborts before writing
`index.html`; the partial output and copied bytes remain for diagnosis. This is not
atomic publication. Preserve that failed directory and choose a new output path for
a retry. HTML uses
code-native SVG overlays and detail images clipped explicitly to their observed native
coordinate rectangles over the same original image files; it
performs no pixel editing, image generation, original extraction or map reconstruction.
The edition is local reference evidence. Original pixels, original branding and exact
map presentation do not pass into malpaco or any public repository artifact.

Main opens `index.html` in a local browser and checks the full board, all four distinct
interaction views, the separate colour reference and all seventeen callout/detail
regions. Check that SVG regions point to the observed features, dimensions agree with
the native 800×600 source images, text is readable and separate-deal captions are clear.
Keep screenshots of this local visual check outside every checkout. Commit an own-word
verification record under `docs/prototypes/T63/` with image hashes/dimensions, edition
HTML hash, screenshot hashes, observations and limitations; no pixels or local install
paths. A successful renderer receipt is not a substitute for this visual verification.

## Player guide, worked turn and retained atlas

Add the guide checks to the repository-only commands above:

```sh
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/check_guide.py
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/check_guide.py --self-test
```

Guide controls use invented metadata and images only. They reject missing topics or
sources, a coherent set below ten images, stale observations, invented visual proof
for a registered gap, reused image bytes with valid manifest/record provenance,
and inconsistent or reversed walkthrough provenance. Both the old atlas checks and
renderer controls remain required. Synthetic combined rendering also checks every
chapter, source, walkthrough and atlas return link and a bad guide hash before any
copy. Fixture directories explicitly use `/tmp`, independently of inherited TMPDIR.

Main alone prepares a combined local bundle map with all six atlas `V` IDs and all
thirteen `G` IDs in the [T64 survey](../../docs/prototypes/T64/visual-source-survey-r2.json).
The IDs deliberately omit G07: the source’s `before.png` is a title screen, so it
is not presented as a board or counted again. Keep every PNG and the bundle map
outside all checkouts. The source files use the survey’s hash-prefixed asset names.

```sh
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/render_atlas.py --include-guide --bundle-map /outside-checkouts/combined-map.json --output /outside-checkouts/pro-guide-r3
```

`index.html` contains clickable chapter navigation, all thirteen annotated screen
sections and the seven illustrated walkthrough steps. `atlas.html` retains the
six atlas views and links back to the guide/walkthrough. Every referenced image is
hash/dimension/location checked before output is created; the original pixels remain
unchanged. The receipt records guide and atlas HTML hashes, nineteen image references,
the separate atlas/guide annotation counts and the ordered walkthrough IDs.

Main opens both pages, checks all chapter and return links, all twenty-one new callouts
and detail regions, the same-record step order, separate-deal captions and the retained
atlas. In particular, the original loss notice and source line remain clipped, the
sampled panel/map agreement is bounded to one defender decrement, preference saving is distinguished from
a game save, and no static-only procedure is presented as visually demonstrated.
Main keeps browser captures outside every checkout and commits only an own-word
verification record under `docs/prototypes/T64/` with source/HTML/capture hashes,
dimensions, alignment/link checks and limitations. Rendering success alone is not a
visual verification pass. Preserve each local failed/intermediate output and use a
new edition path for any rerender.

The [passing T64 local verification](../../docs/prototypes/T64/local-visual-verification-r2.json)
records the final T64-r3 edition, all thirteen guide sections, twenty-one callouts,
chapter/step/atlas links and retained image dimensions/hashes. Main reopened the
corrected G12 browser/native view; the other twelve final image sections have the
same HTML as the previously inspected sections. This is not a claim of identical
browser screenshot pixels. Earlier needs-correction and source-survey revisions
remain unchanged.


## Complete local book — main session only

The default renderer builds the atlas alone. `--include-guide` builds the guide and
atlas companion edition. **Use `--complete-book` for the complete manual**; it implies
the guide and preflights its thirteen frames plus the atlas’s six references before
creating output or copying originals. It also validates the reference/coverage/checklist.
Use the same private combined V/G bundle map, with a new output outside every checkout:

```sh
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/render_atlas.py --complete-book --bundle-map /outside-checkouts/combined-map.json --output /outside-checkouts/pro-complete-r1
```

The six pages are `index.html` (contents), `guide.html` (chapters and
`#walkthrough`), `atlas.html`, `reference.html`, `coverage.html` and `checklist.html`.
Every page has book navigation; the contents links to all eighteen reference sections.
Source identifiers on the text chapters point to on-page scope notes, with repository
paths as provenance identifiers. The receipt records every page’s SHA-256, retained
image hashes/dimensions, guide and atlas callout counts and walkthrough order.
No new screen is reconstructed. Prior local edition and measurement directories
remain unchanged, including failed/intermediate editions.

Main opens all six pages, all chapter/section links, reference paragraphs and checklist
scenarios, and confirms retained annotated illustrations and detail clipping. New
screenshots remain outside all checkouts. Main commits a new own-word verification
under `docs/prototypes/T65/`; renderer success is not visual or semantic proof. The
stable owner-host preview remains outside Git and is published by main only.

Add these synthetic/repository checks:

```sh
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/check_manual.py
systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- python3 tools/manual/check_manual.py --self-test
```

The manual controls reject omitted topics/subjects/spec areas/screens, missing
citations, promoted unknowns, stale ranges, absent checklist benefits/scenarios,
broken section references and silently resolved discrepancies. Synthetic combined-book
rendering verifies six pages, every chapter link, retained illustrations and page hashes,
and refuses invalid reference data before copying. All fixtures use `/tmp` explicitly.
The T65 guide refinement controls also cover source anchors, stored prose, nonvisual
proof claims, local visual proof, record/manifest digests, surveyed walkthrough record,
step prose and retained scope boundaries; copied omissions must make self-test fail.
These are structural controls. The independent reviewer audits numerical rules and
conflicts, and main checks the illustrated edition and full parent acceptance.


The manual checker binds each reference paragraph to its canonical evidence line
(basis, confidence and source IDs), and checks whole subject-range rows,
screen-state rows and conflict bullets in the Markdown. This protects the
GitHub-readable edition alongside JSON-generated HTML. Unknown paragraphs use
“Limitation sources” in both editions. Synthetic controls corrupt those lines,
exercise valid and invalid source anchors, and test each scope/adoption boundary term.
These checks compare declared provenance and stored prose; coordinated JSON/Markdown
changes still require independent semantic review and do not prove a claim true.
