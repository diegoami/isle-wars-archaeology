# runs/E020 — model-driven first sitting

Run records of experiment E020, `runs/E020/<batch>/<run-id>.json`, valid against `run/1`. Raw and
immutable (rule 20); a re-read of a sitting writes a new record beside the old ones, with a new run
id (run ids are experiment-wide), and the finding says which it cites. `runtime.platform` is
`wine-on-user-machine-iwp-2.0` and `start_state.sha256` the `Islepro.exe` hash the sitting measured
before its launch, which the export accepts only when it is the F019 row's, so every record passes
the constraint-F gate in `tools/check_no_originals.py`. `status` is the session's own: an aborted
sitting is recorded aborted.

The records are produced after a sitting on the owner's machine:
`bash tools/wine-driver.sh --records --sitting <sitting-dir> --batch <name>`. The sitting directory
itself (frames, index, actions) never enters the repository. Per-claim outcomes are declared in
`experiments/E020-wine-first-run/outcomes.json`, never here (every `.json` here is a run record);
`tools/check_counts.py` refuses `corroborated` below a claim's own per-arm target.
