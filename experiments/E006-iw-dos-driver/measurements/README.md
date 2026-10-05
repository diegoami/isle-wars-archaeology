# E006 measurements

Never deleted or overwritten (CLAUDE.md rule 20); a re-run writes a new file beside the old.

- `command-output/<UTC time>-<commit>-<arm>.out.txt`: the output of each arm's command (`scripts/run-arm.sh`), with
  its exit status.
- `tables/E006-rFIRST-rLAST.md`: per repeat, the status, hashes, times and exit status (`scripts/tables.py`).
- `varies-E006-rFIRST-rLAST[-<UTC time>].md`: what varies across records (`scripts/varies.py`; the first one's
  normaliser missed a display number, see the experiment's README, round 1).
