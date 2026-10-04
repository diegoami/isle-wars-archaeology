# E005 measurements

Every output that F007 or the PR may cite, kept in the repository (CLAUDE.md rule 20). Nothing here is an original file, a savestate or a memory image; the images and the game-written files themselves stay in the local evidence bundles and are named here by sha256.

- `explore/`: the text outputs of the `--explore` runs made before and between the records (`x01` to `x30`: exploration of the screens, the clicks and the files; `d-*`: dry runs of the arms), copied by `scripts/keep-explore.sh`. Per run: `<run>.run.log`, `<run>.observations.json`, `<run>.changes.log`, `<run>.dosbox.log`, `<run>.dosbox.conf.txt` and `<run>.captures.sha256.tsv` (sha256, bytes and name of every screenshot and kept game-written file). They are not run records.
- `analysis/`: the tables built from the run records and the bundles by `scripts/analyze.py` and `scripts/check-board-reader.py` (see F007, "Method").
- `done-when/`: the output of each Done-when command of T14, run on this machine.

**Not kept.** `--explore` writes its outputs under the arm name and replaces an earlier run of the same name. The dry-run arm `d-turn` was run five times while its script was corrected; the first three ended in `aborted` on script faults (a right click that the game does not need, a battle that needs several ATTACK clicks, a move-in that ALL completes by itself), the fourth completed, and their logs were replaced before they were copied here, so only the fifth, completed, run is kept. Nothing in F007 cites them. Every run after `d-turn`'s fifth (the 26 records) writes new files, never replacing.
