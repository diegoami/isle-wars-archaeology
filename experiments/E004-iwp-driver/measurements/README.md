# E004 measurements

Everything here is made from the records under `runs/E004/` (rule 20), or is a log of a diagnosis kept as it was made.

- `cycle-table.md`, `stage-times.md`: made by `make_tables.py` from `runs/E004/*.json`
  (`python3 experiments/E004-iwp-driver/measurements/make_tables.py`); regenerate after a new run.
- `probes/`: the logs of the diagnoses made while the driver was built (what outlives `wineserver -k`, the
  stale bus, the `TMPDIR` abort), copied as they were made.
