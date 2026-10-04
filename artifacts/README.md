# artifacts/

`known.json`: every artifact set ever used, as `{"manifest": <artifact-set/1>, "notes": "…"}`. Hashes only. The bytes stay on the user's machines (U2).

`tools/register_artifact.py manifest <dir> …` prints a manifest. Its `check` re-hashes a copy, or
reads a `<sha256>  <bytes>  <relative/path>` listing, against the entry for a set id; `validate`
checks every entry against the pinned `formats/artifact-set-1.schema.json` and recomputes its id.
The tool is game-archaeologist's own, at the commit `archaeology.json` pins, with
`tools/validate_records.py` and `formats/`; never edited here (`tests/test_formats.py` pins the
bytes). It reads `artifacts/known.json` of the working directory, or the file `--known` names.
