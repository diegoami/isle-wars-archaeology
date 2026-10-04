# E003 measurements

Every output of T11 that F005 or the PR may cite, tracked as it was made (rule 20). Nothing here is
an original file: captures and savestates are listed by size and sha256 only, and machine-local
paths are replaced by placeholders (`<EXPLORE>`, `<WORKTREE>`, `<MACHINE-LOCAL>`, `<IW_DOS_RUN>`,
`<IW_DOS_DIR>`; each folder's README says which).

- `explore-round1/`: T11's first round, by hand, before any code ([README](explore-round1/README.md)).
- `explore-round2/`: the scripted probes that settled determinism, speed, savestate, debugger,
  secure mode, the stop and DOSBox-X's screenshots ([README](explore-round2/README.md)).
- `explore-cycle/`: the one `cycle.py --explore` run (`E003-x255009`) made before the first record,
  as the cycle stored it in `E003_EXPLORE` (`control.*`), with `captures.sha256.tsv` for its two
  screenshots.
- `done-when/`: the output of each Done-when command and arm run, as `scripts/dw.sh` (with
  `scripts/arms.sh`) wrote it, named `<what>-<UTC time>.txt`. The profile's first two runs, before
  `dw.sh` saved its output, printed the same lines (`ready`); they are not kept.
- `records-r0001-r0012.txt`: every observation of the records E003-r0001 to r0012, printed by
  `summarise_runs.py 1 12` from `runs/E003/`.
