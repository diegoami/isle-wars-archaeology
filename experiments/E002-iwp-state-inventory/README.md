# E002 iwp-state-inventory

Copied from the research task's contract when the experiment was created. After the first run this
file is append-only. A changed design is a new experiment, or `v2/`.

- **Task**: T09 (#29), which folds #27
- **Question**: Where can the state of *Isle Wars Pro* (the unregistered 2.0 install) be seen, at what
  intervention level and at what cost: on the screen, in files the game writes, in the registry, in the
  Temp folder, in the window title, in the process? Which files does it write, in which format, and does
  it save a game?
- **Hypotheses**:
  - H0: the game's files hold no state that changes with play: what a player does shows only on the
    screen. Distinguished by every run: no file of the game copy changes except by "Save as default".
  - H1: some file holds a record that changes with play, in a format that two runs with different actions
    can decode. Distinguished by two runs with different known actions whose bytes differ at the offsets
    that the actions explain.
  - Side questions, answered by the screens a run reaches: what the game says about itself (Help, the
    unregistered notices, the locked options); whether it has a save and load; how the computer players'
    turns look on the screen.
- **Artifact**: set `iwp-2.0-996e86c5` for runs that cannot write a file of the set. Runs that may click
  Save as default or lose a game are recorded under `iwp-2.0-de5a82a2`
  ([`artifacts/iwp/iwp-2.0-de5a82a2.md`](../../artifacts/iwp/iwp-2.0-de5a82a2.md)): the same files, with
  `xtras/Isledft.dat` and `xtras/Islepro.skr` declared runtime writes. Variant none.
- **Runtime**: `runtime/iwp/spike/cycle.py@<commit in each record>` with `--experiment E002`, on Linux
  (WSL2) with Wine 9.0 (win32 prefix), Xvfb 800x600x24, xfwm4 and xdotool, the game in a network namespace
  of its own, as in E001 ([F002](../../findings/F002-iwp-runtime-wine-xvfb.md)). Maximum intervention
  level I1: the runs take screenshots of the display (`vocabulary/interventions.md` lists screenshots as
  I1) and read `/proc` and the game copy; no memory is read, no file is modified, and every input is one a
  player gives with the mouse.
- **Design**:
  - start state: `S-cold-prefix-title`, the prefix as `setup/iwp/iwp-runtime.sh` leaves it, restored after
    each run as in E001; the run record carries the sha256 of the listing of every entry of the prefix.
  - control: arm `opt-control`, Options then Save as default with nothing changed.
  - arms (each a step script in `scripts/`, named in the record's `actions.args`):
    - `opt-control`, `opt-level-hard`, `opt-level-easy`, `opt-speed-slow`, `opt-speed-fast`: Options, one
      control changed, Save as default, then `xtras/Isledft.dat` read;
    - `loss-normal`, `loss-hard`, `loss-easy`: New Game, the level chosen, Play Game, wait for the human
      turn, New Game in the middle of the game (a loss is credited when fewer than 10 countries are
      held), Scores; then `xtras/Islepro.skr` read;
    - `tour`: title, Options with every control at its default, the controls the unregistered build locks,
      Help paged to the end, Scores, New Game, the board, one human turn (place all the armies on a Blue
      country, attack, finish the turn), the computer players' turns passing, a game quit in the middle,
      Scores, and the quit path through the unregistered notice.
  - n per arm: 2 for the `opt-*` and `loss-*` arms, 2 for `tour`; stopping rule: none, the list is fixed.
    A run in which a step that must change the screen did not change it is recorded `aborted: <why>`;
    it stays in `runs/E002/`.
- **Measurements**: screenshots (screen: ImageMagick `import`, PNG encoded by the driver); the window
  title and the game process's threads and resident memory (process: `xdotool`, `/proc`); the game
  copy and the prefix, file by file (file: sha256 of every entry before and after, and `changes`); the
  bytes of the files the game wrote, and the offsets that differ from the install's file (file); the
  registry's keys by name with a hash of each key's values (file).
- **Outputs**:
  - run records: `runs/E002/`;
  - evidence manifests: `evidence/E002/`, bundles in release `E002` (screenshots, `changes.log`, `run.log`,
    `wine.log`); the files the game wrote are read into the record's observations, never bundled;
  - `findings/F003-*.md`, status `proposed`.

## Scripts

- `runtime/iwp/spike/cycle.py --experiment E002 --arm <name> --script experiments/E002-iwp-state-inventory/scripts/<name>.steps [--may-write-saved-files] [--terminate kill|ui-quit]`.
  Needs `IWP_PREFIX`, `IWP_DIR` and `E002_BUNDLES`. It writes the next `runs/E002/E002-r<nnnn>.json` and
  `evidence/E002/E002-r<nnnn>.manifest.json`, and refuses to start when runtime, setup, tools or formats
  have uncommitted changes. The step language is described at the top of `runtime/iwp/spike/steps.py`.
- `scripts/*.steps`: the arms above. Each file's own first lines give the arguments it is run with. A
  record names its script in `actions.args` and holds the script's sha256 as its first observation.
- `--explore --session` (no record): the interactive exploration that found the screens and click
  positions; its screenshots and notes are machine-local and are not evidence.
