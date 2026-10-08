# evidence/E020 — model-driven first sitting

Evidence manifests of experiment E020, `evidence/E020/<run-id>.manifest.json`
(`evidence-manifest/1`). Every `files[].class` is `recording` (constraint C of the rule 18
carve-out): per-frame evidence from the model-driven sitting, never `screenshot` of a human
session. `tools/validate_wine_manifests.py` enforces that and the schema, and refuses any document
that does not declare `evidence-manifest/1`.

The bundles themselves (frames, action logs, optional dumps) stay in the sitting directory on the
user's machine (constraint A): they are never committed, never uploaded, and no release asset is
made of them. A manifest references each file by sha256 only. Its `store: release:E020` and each
file's `asset` name are the fields the `evidence-manifest/1` schema requires: they name the
experiment and the file, and do not mean the file was, or will be, published.
