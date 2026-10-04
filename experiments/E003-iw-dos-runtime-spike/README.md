# E003 iw-dos-runtime-spike

Copied from the research task's contract when the experiment was created. After the first run this
file is append-only. A changed design is a new experiment, or `v2/`.

- **Task**: T11 (#34)
- **Question**: Can DOS *Isle Wars* (set `iw-dos-3.1-30121376`) be launched, brought to a known screen, driven by one input, observed, terminated and reset unattended under DOSBox-X 2024.03.01 and Xvfb, with no network (N0), from a run copy that DOSBox-X mounts alone? Are its first screens the same in three runs from the same start? Can DOSBox-X's savestates (I2) and a memory read (I1) be used?
- **Hypotheses**:
  - H0: it cannot be done unattended on this path: the cycle fails, needs a human, or leaves the run copy changed after reset. Distinguished by any control run that aborts, or whose run copy after reset differs from its start.
  - H1: it can. Distinguished by three control runs, each completing the cycle with no human, the same `before` screenshot hash in all three, and a run copy equal to its start after each reset.
  - Side questions, each answered by one probe run (arms below): does the host's clock change the first screens; what do more cycles do to the time to the known screen; does a savestate restore the screen; can memory be read at the known screen without changing the run, and is it the same across two identical starts; is DOSBox-X's own screenshot the same as the window capture; how can DOSBox-X be stopped; which files does the game write.
- **Artifact**: set `iw-dos-3.1-30121376`, variant none.
- **Runtime**: `runtime/iw-dos/spike/cycle.py@<commit in each record>`, Linux (WSL2) with DOSBox-X 2024.03.01 (Ubuntu `2024.03.01+dfsg-1build2`), Xvfb, xdotool, ImageMagick. Maximum intervention level I0 for the control and every arm except `savestate` (I2: a savestate saved and restored) and `debugger` (I1: a savestate written and its memory read, never restored). The game's files and process are untouched; every input to the game is one a player gives with the mouse. DOSBox-X's settings (no sound devices, no network devices, the emulated clock set by DATE and TIME before the game) are the environment, not a modification of the game.
- **Design**:
  - start state: `S-run-copy-option-box`, the run copy `<IW_DOS_RUN>/game` as `setup/iw-dos/iw-dos-runtime.sh` leaves it (the registered files, plain files of its own, with the copy's modification times). Each record's `start_state.sha256` is the sha256 of the listing of every entry of the run copy (name, size, sha256, modification time). Restored after each run by `rundir.py sync` (what the run added loses its name; a changed file is copied again from `IW_DOS_DIR`); the cycle then checks the run copy equals its start (observation "run copy after reset equals the run copy before launch").
  - control: arm `control`: Xvfb 800x600x24, no window manager, DOSBox-X `cycles=fixed 3000`, the emulated clock set to 01-01-1994 12:00:00 with host synchronisation off, sound off, network devices off, the whole run in a private network namespace. Known screen: the option box (Set level, Default, Load saved game) on the map, by pixels. Input: the pointer onto Set level, then a click; the Select level dialog, by pixels. Stop: SIGTERM to DOSBox-X (`quit warning=false`).
  - arms (one run each unless stated; each differs from `control` in one thing):
    - `control` (3 runs): no arguments
    - `clock-host`: `--clock host` (DOSBox-X follows the host's clock)
    - `speed-max`: `--cycles max`; `speed-30000`: `--cycles fixed-30000`
    - `savestate`: `--probe savestate` (F12+S at the option box, the click, F12+L, `restored.png`)
    - `debugger` (2 runs): `--probe memory` (`-break-start` on DOSBox-X's command line; F12+S at the option box, the Memory member of the savestate inflated and hashed; no restore)
    - `dosbox-capture`: `--probe dosbox-capture` (F12+P at the option box; DOSBox-X's own PNG decoded and compared with `before.png`)
    - `term-kill`: `--terminate kill` (SIGKILL); `term-close`: `--terminate close` (`xdotool windowkill`)
  - n per arm: 3 for `control`, 2 for `debugger` (two identical starts to compare memory), 1 for the others (a probe, not a measurement of variance); stopping rule: none, the list is fixed.
- **Measurements**: the window and its geometry (process: `xdotool`); screen pixels and screenshots (screen: ImageMagick `import` of the 640x350 window, PNG encoded by the cycle); DOSBox-X's exit status and the survival of any process (process: `/proc`); DOSBox-X's network namespace and interfaces (process: `/proc`); the run copy, file by file (file: size, sha256 and modification time of every entry before and after); the savestate and its members (save; memory: the Memory member inflated); DOSBox-X's log (log).
- **Outputs**:
  - run records: `runs/E003/`;
  - evidence manifests: `evidence/E003/`, bundles in release `E003` (screenshots, `changes.log`, `run.log`, `dosbox.log`, `dosbox.conf.txt`; never a savestate, which holds the game's memory);
  - probe logs, tables and timings of the exploration before the runs: `measurements/` (rule 20);
  - `findings/F005-iw-dos-runtime-dosbox-x.md`, status `proposed`.

## Scripts

- `runtime/iw-dos/spike/cycle.py [--arm NAME] [--cycles fixed-3000|fixed-30000|max] [--clock fixed|host] [--probe none|savestate|memory|dosbox-capture] [--terminate term|kill|close]`. With no arguments it is the `control` arm. Needs `IW_DOS_DIR`, `IW_DOS_RUN` and `E003_BUNDLES`. It writes the next `runs/E003/E003-r<nnnn>.json` and `evidence/E003/E003-r<nnnn>.manifest.json`, and refuses to start if runtime, setup, tools or formats have uncommitted changes.
- `runtime/iw-dos/spike/dosconf.py`: the configuration each run generates, and the check that refuses any other.
- `setup/iw-dos/iw-dos-runtime.sh`: the profile that prepares the run copy. Run it before the cycle.
- The arms in this README are the arguments each record's `actions.args` lists.
