# runs/E020 — model-driven first sitting

Run records of experiment E020, `runs/E020/<batch>/<run-id>.json`, valid against `run/1`. Raw and
immutable (rule 20); a re-read writes new files beside the old ones. `runtime.platform` is
`wine-on-user-machine-iwp-2.0` and `start_state.sha256` the F019-known `Islepro.exe` hash, so every
record passes the constraint-F gate in `tools/check_no_originals.py`.

An optional `outcome.json` beside a batch's records records that batch's declared outcome
(`corroborated`, `narrowed`, `unestablished`); `tools/check_counts.py` refuses `corroborated` below
the `walkthroughs/f011-questions.md` target.

The records are produced after a sitting on the owner's machine:
`bash tools/wine-driver.sh --records --sitting <sitting-dir> --batch <name>`. The sitting directory
itself (frames, index, actions) never enters the repository.
