# T12 measurements

Outputs of the migration to game-archaeologist's pinned tools (commit `69566be655fc35c36d19277db9b94f8300055c7b`,
`archaeology.json`). Nothing here changed a record, a manifest or a set; the stricter tools only re-checked them.

| File | Command (from the repository root) | Result |
| --- | --- | --- |
| `validate-runs-evidence.txt`, `.exit` | `python3 tools/validate_records.py $(find runs evidence -name '*.json' \| sort)` | 158 files, every line `ok:`, exit 0 |
| `validate-known.txt`, `.exit` | `python3 tools/register_artifact.py validate` | `known.json ok (4 sets)`, exit 0 |
| `mutants.txt` | `TMPDIR=<short dir outside every checkout> python3 experiments/T12-tool-migration/measurements/mutants.py` | 7 of 7 mutants killed |

`mutants.py` removes one guarantee at a time (a seal's changed-byte or unlisted-file check, `--strict`,
duplicate-key refusal, a vendored byte) and shows the named tests failing; it restores each file.

The run records and manifests were validated against the pinned schemas, whose `run-1.schema.json` differs from
the copy pinned before (`79bede9`); every record still validates.
