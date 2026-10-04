# E002 measurements

Everything here is a measured output of the exploration sessions (`cycle.py --explore --session`), copied
from the machine-local `<machine-local>/E002-explore/` (rule 20, L207). The
originals there are untouched and stay.

- `explore/`: sessions `s2`, `s3`, `s4` and `tourdry`, each with its `<s>.run.log` (timed driver log),
  `<s>.changes.log` (file-by-file change list of the game copy and prefix), `<s>.observations.json`,
  `<s>.wine.log`, and `<s>.cmd-NNNN.txt` / `<s>.out-NNNN.txt` (the commands sent to the session and the
  driver's reply to each). Names are kept as made.
- `explore-screenshots.md`: the captures of those sessions, listed by sha256. No PNG is committed.
- Scrub: in the four `*.wine.log` files, the drive letter of the one line that names the Windows folder
  (the winemenubuilder error at wineboot) was replaced by `<drive>`, because Done-when 6's grep matches a
  drive letter followed by a colon and backslashes. Nothing else was altered.
- Exploration sessions are not run records and are not evidence for a finding on their own; a finding
  cites a recorded run under `runs/E002/`, and may cite a session file only as the place a click position
  or a screen was first found.
- `run-table.md` and `file-bytes.md`: generated from `runs/E002/*.json` by `make_tables.py`
  (`python3 experiments/E002-iwp-state-inventory/measurements/make_tables.py`); regenerate after a new run.
- `static-islepro-dat.md`: byte counts of the shipped `xtras/Islepro.dat`, read in place (no content).
