# E005 iw-dos-state-inventory

Copied from the research task's contract when the experiment was created. After the first run this
file is append-only. A changed design is a new experiment, or `v2/`.

- **Task**: T14 (#52), W4b
- **Question**: Where can the state of DOS *Isle Wars* (set `iw-dos-3.1-30121376`) be seen, at what intervention level and at what cost: on the screen, in the files the game writes, in a savestate? Which files does it write, in what format, which action moves which byte, and does the game save and load a game (Q-SET-05)? Which screens can the unattended cycle reach?
- **Hypotheses**:
  - H0: the game's state can be seen only on the screen, and no file it writes changes in line with an action.
  - H1: at least one file the game writes (`ISLEWAR.DFT`, `ISLEWAR.SCR`, a save) has a field that changes in line with a known action, shown by two runs.
  - Side questions, each answered by the arms below: does the game save and load, under what name; what do Default, Set level and the starting armies write; what does a lost game write; what does a savestate hold (classified only).
- **Artifact**: set `iw-dos-3.1-30121376`, variant none (no run changes a file of the set: the game's writes are new files, removed by the reset).
- **Runtime**: `runtime/iw-dos/spike/cycle.py --experiment E005 --steps <script>@<commit in each record>`, the T11 cycle with its seal unchanged (run copy checked with `check --strict` before the launch, only the run copy mounted as C:, `IW_DOS_DIR` bound read-only, DOSBox-X in a network namespace of its own, `completed` only on a clean finish), DOSBox-X 2024.03.01, Xvfb, xdotool, ImageMagick. A script is a list of steps a player could take with the mouse (`navsteps.py`), plus the keys `c` and `e` for the game's shareware notices. Maximum intervention level I0 for every arm except `savestate` (I2: a savestate saved, never restored; its members are classified, its memory is not searched). The game's files and process are untouched.
- **Design**:
  - start state: the T11 run copy `S-run-copy-option-box` (the registered files as plain files of the run copy), restored after every run by `rundir.py sync` and checked equal to its start. The game's own writes (`ISLEWAR.SCR` at every launch, `ISLEWAR.DFT` after a level or Default, `ISLEWAR.SAV` after Save) are new files, kept as bundle outputs (`s<NN>-<NAME>` after a `files` step, `end-<NAME>` at the end of the run) and observed (size, sha256, and the bytes in hex when at most 64).
  - arms (each differs from the others in the action it takes; the scripts are `steps/<arm>.steps`):
    - `default`: Default, start, first human turn
    - `level-easy-1`, `level-normal-1`, `level-easy-3`, `level-hard-6`, `level-hardest-10`: Set level, starting armies, start, first human turn (the pairs vary the level and the armies one at a time)
    - `turn`: Easy and 1 army; Save at the turn start; place all in a Blue country that touches an enemy; attack it until it falls; move in; Pass; the computer turns; the next human turn; Save; the cards button
    - `buttons`: Scores, Sound, Speed at the first human turn
    - `concede-easy`, `concede-normal`: Quit, Yes: the `GAME OVER` picture and the game over dialog. The scripts name the capture after Yes `scoreboard-after-concede`; it shows `GAME OVER` over the board, not the scoreboard (correction, 2026-10-05, F007 round 2; the scripts and assets keep the name)
    - `save-load`: Save, concede, another game, Load saved game
    - `load-none`: Load saved game with no save
    - `exit`: concede, another game No, the shareware notices (`c`, `e`), the game ends by itself
    - `savestate`: a DOSBox-X savestate at the first human turn (I2), its members classified
  - n per arm: 2 for `default`, `level-easy-1`, `level-normal-1`, `level-easy-3`, `turn`, `concede-easy`, `concede-normal`, `save-load` (two runs per parsed field); 1 for the others, a probe; stopping rule: none, the list is fixed. The first board of a game is random: scripts read the board (`choose-attack`) instead of naming a country.
- **Measurements**: screen pixels and screenshots (screen); the run copy file by file before, during (`files` steps) and after a run (file: size, sha256, bytes); DOSBox-X's exit; the savestate's members (save).
- **Outputs**:
  - run records: `runs/E005/`;
  - evidence manifests: `evidence/E005/`, bundles in release `E005` (screenshots, the game-written files, `changes.log`, `run.log`, `dosbox.log`, `dosbox.conf.txt`; never a savestate);
  - exploration before the runs and probe logs: `measurements/` (rule 20);
  - `findings/F007-iw-dos-observable-state-inventory.md`, status `proposed`.

## Scripts

- `scripts/cyc.sh ARM STEPS [--explore]`: one run; needs `IW_DOS_DIR`, `IW_DOS_RUN`, `E005_BUNDLES` (and `E005_EXPLORE` with `--explore`) in the environment.
- `scripts/keep-explore.sh ARM...`: copies the text outputs of `--explore` runs into `measurements/explore/` and lists every capture and kept file by sha256.
- `steps/x*.steps` are the exploration scripts (not records); `steps/<arm>.steps` are the arms'.

## Round 1 (2026-10-05, PR #58; appended, the text above is unchanged)

- **Correction.** "Maximum intervention level I0 for every arm except `savestate`" above is wrong: every arm takes screenshots, which is I1, so every arm is I1 and `savestate` is I1 and I2. The records r0001 to r0026 declare I0 (`runs/E005/CORRECTIONS.md`); from r0027 the cycle declares I1.
- **Correction.** "The first board of a game is random" above is a claim that no run tested: the board differs between runs, and the same start picture came up in several runs (F007). Scripts still read the board (`choose-attack`).
- **Runs r0027 to r0038**, with the corrected cycle (required waits, the notices guarded, no probe with a script, times from the launch): `default` x2, `level-easy-1` x2, `concede-easy` x2, `save-normal-3` x2, `savestate`, `exit`, `turn`, `level-hardest-10`.
- **Scripts.** `scripts/keep-explore.sh` now runs `scripts/keep-explore.py KEY...` (never replaces or deletes); `scripts/analyze.py BATCH` creates a new batch directory; `scripts/notice-scan.py` and `scripts/board-constants.py` measure the notice detector and the board reader's constants; `scripts/fix-manifest-classes.py` only checks. The round-1 tables are in `measurements/round1/`.
