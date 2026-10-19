# Pro illustrated reference

Read the own-word [map/UI atlas](atlas.md), its [claim and annotation data](atlas.json),
and the [complete-manual subject/feature inventory](inventory.json). This is the T63
map and UI part of #265. T64 (#275) and T65 (#276) cover later manual material.
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
meaning remains source-qualified. The [r2 local verification](../../docs/prototypes/T63/local-visual-verification-r2.json)
records the earlier clipping correction; the revised source disclosure requires a
fresh local edition verification.
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
