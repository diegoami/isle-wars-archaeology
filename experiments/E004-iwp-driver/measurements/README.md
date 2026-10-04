# E004 measurements

Everything here is made from the records under `runs/E004/` (rule 20), or is a log of a diagnosis kept as it was made.
No file here is ever overwritten: a new batch of runs gets new tables beside the old ones.

- `cycle-table.md`, `stage-times.md`: the tables of the first batch, E004-r0001 to E004-r0016, made at 38e5872 by
  the first version of `make_tables.py`. Kept as they were made.
- `tables/E004-r<first>-r<last>-cycle-table.md`, `tables/E004-r<first>-r<last>-stage-times.md`: the tables of one
  batch, made once by `python3 experiments/E004-iwp-driver/measurements/make_tables.py FIRST LAST`, which refuses
  to write a batch whose tables exist. F006 names the batch it cites.
- `command-output/`: what each recorded command printed, one file per command.
- `probes/`: the logs of the diagnoses made while the driver was built (what outlives `wineserver -k`, the
  stale bus, the `TMPDIR` abort), copied as they were made. They are exploration, not run records.
