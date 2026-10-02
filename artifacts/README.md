# artifacts/

`known.json`: every artifact set ever used, as `{"manifest": <artifact-set/1>, "notes": "…"}`. Hashes only. The bytes stay on the user's machines (U2).

`tools/register_artifact.py manifest <dir> …` prints a manifest. Its `check` re-hashes a copy, or
reads a `<sha256>  <bytes>  <relative/path>` listing, against the entry for a set id; `validate`
checks every entry against the vendored `formats/artifact-set-1.schema.json` and recomputes its id.
