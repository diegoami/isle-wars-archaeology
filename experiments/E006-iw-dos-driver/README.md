# E006 iw-dos-driver

Copied from the task's contract when the experiment was created. After the first run this file is
append-only. A changed design is a new experiment, or `v2/`.

- **Task**: T15 (#63), W5b
- **Question**: Does the minimal driver (`runtime/iw-dos/driver/`, W5b) take DOS *Isle Wars* (set
  `iw-dos-3.1-30121376`) from a known state to a known screen, give one input, observe before and after,
  terminate and reset, ten times in one command, with the same `before` screenshot every time? Does DOSBox-X
  killed in the middle of a cycle, by SIGKILL from outside the session or by closing its X client, make that
  repeat `aborted`, leave the run copy at its baseline and let the next repeat complete? How long does a repeat
  take?
- **Hypotheses**:
  - H0: the driver cannot repeat the cycle: some control repeat is not `completed`, or two `before` screenshots
    differ, or a repeat starts from a run copy that the one before did not reset.
  - H1: it can: ten `completed` control repeats with one `before` pixel hash and one `start_state.sha256`.
  - Side question: what varies across the repeats, if anything does.
- **Artifact**: set `iw-dos-3.1-30121376`, variant none. The game's own writes (`ISLEWAR.SCR` at the launch,
  F005) are new files of the run copy, removed by the reset.
- **Runtime**: `runtime/iw-dos/driver/repeat.py@<commit in each record>`, built on T11's cycle and T14's step
  language (`runtime/iw-dos/spike/`), on Linux (WSL2) with DOSBox-X 2024.03.01, Xvfb 800x600x24 (no window
  manager), xdotool and ImageMagick, inside private user, mount, PID and network namespaces (F005's seal: the run
  copy checked with `check --strict` before the launch, only `C:` mounted, `IW_DOS_DIR` bound read-only, no
  network but `lo`, alias and bind-mount refusal). Maximum intervention level I1: screenshots of the game window.
- **Design**:
  - start state: `S-run-copy-option-box`, the run copy as `setup/iw-dos/iw-dos-runtime.sh` leaves it and as each
    repeat's reset leaves it; each record carries the sha256 of the listing of every entry of the run copy (size,
    sha256, modification time), the baseline the command took at its start.
  - arms (arguments in each record's `actions.args`):
    - `control`: `--repeats 10`. Launch, the option box by its pixels, `before.png`, one click on Set level (the
      step `click 60 32`), the Select level dialog by its pixels, `after.png`, SIGTERM, reset.
    - `sigkill-mid-cycle`: `--repeats 3 --fault sigkill --fault-at after-before --fault-repeat 2`: in repeat 2,
      DOSBox-X is sent SIGKILL after `before.png`, before the click.
    - `close-mid-cycle`: `--repeats 3 --fault close --fault-at after-input --fault-repeat 2`: in repeat 2,
      DOSBox-X's X client is closed (`xdotool windowkill`) after the click.
  - n per arm: 10 repeats for `control` in one command; 3 for each fault arm (the second is the fault, the third
    shows the recovery). Stopping rule: none, the list is fixed. A repeat that does not end as expected stops the
    command; its record stays in `runs/E006/`.
- **Measurements**: screenshots (screen: ImageMagick `import`, PNG encoded by the spike's deterministic writer),
  the time of each stage of a repeat (process: monotonic clock, as observations), the seal's checks (file and
  process), DOSBox-X's exit status, the run copy before and after (file: size, sha256, modification time).
- **Outputs**:
  - run records: `runs/E006/`;
  - evidence manifests: `evidence/E006/`, bundles in release `E006` (screenshots, `changes.log`, `run.log`,
    `dosbox.log`, `dosbox.conf.txt`);
  - each command's output and the tables derived from the records: `measurements/` (rule 20);
  - `findings/F008-iw-dos-driver-cycle.md`, status `proposed`.

## Scripts

- `scripts/run-arm.sh ARM`: runs one arm's command and writes its output to
  `measurements/command-output/<UTC time>-<commit>-<arm>.out.txt` (never over an existing file); needs
  `IW_DOS_DIR`, `IW_DOS_RUN` and `E006_BUNDLES` in the environment.
- `scripts/tables.py FIRST LAST`: a new table of the records `E006-rFIRST` to `E006-rLAST` under
  `measurements/tables/` (never over an existing file).
