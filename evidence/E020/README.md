# evidence/E020 — model-driven first sitting

Evidence manifests of experiment E020, `evidence/E020/<run-id>.manifest.json`
(`evidence-manifest/1`). Every `files[].class` is `recording` (constraint C of the rule 18
carve-out): per-frame evidence from the model-driven sitting, never `screenshot` of a human
session. `tools/validate_wine_manifests.py` enforces that and the schema.

The bundles themselves (frames, action logs, optional dumps) are release `E020` assets named
`<sha256[:16]>-<name>`, never committed. The sitting directory on the user's machine is referenced
by sha256 only.
