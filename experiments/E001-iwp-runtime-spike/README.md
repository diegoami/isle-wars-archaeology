# E001 iwp-runtime-spike

Copied from the research task's contract when the experiment was created. After the first run this
file is append-only. A changed design is a new experiment, or `v2/`.

- **Task**: T08 (#24)
- **Question**: Can Isle Wars Pro (set `iwp-2.0-996e86c5`) be launched, brought to a known screen, driven by one input, observed, terminated and reset unattended, under Wine 9.0 (32-bit prefix), Xvfb and the xfwm4 window manager, with no network (N0)?
- **Hypotheses**:
  - H0: it cannot be done unattended on this path: the cycle fails, or needs a human, or leaves state behind. Distinguished by any control run that aborts, needs a manual step, or leaves a process or a prefix difference after reset.
  - H1: it can. Distinguished by three control runs from a prefix built by `setup/iwp/iwp-runtime.sh` on a cold machine state, each completing the cycle with no human, the same `before` screenshot hash in all three, and a prefix identical to its starting state after each reset.
  - Side questions, each answered by one probe run (arms below): does the window manager matter; does audio matter; does the network matter; which screen sizes and depths work; how can the game be stopped; which files does the game write.
- **Artifact**: set `iwp-2.0-996e86c5`, variant none. The `save-default` arm is recorded under the successor set `iwp-2.0-3694a782` (the same files, with `xtras/Isledft.dat` declared a runtime write), because its input may write that file.
- **Runtime**: `runtime/iwp/spike/cycle.py@<commit in each record>`, Linux (WSL2) with Wine 9.0 (win32 prefix), Xvfb, xfwm4, xdotool; maximum intervention level I0: the game's files and process are untouched, and every input is one a player gives with the mouse. The environment (audio drivers disabled, a private network namespace) is part of the arguments and is not a modification of the game.
- **Design**:
  - start state: `S-cold-prefix-title`, the prefix as `setup/iwp/iwp-runtime.sh` leaves it (a freshly built win32 prefix, `Z:` and the COM links removed, the registered game copy) with the registry files kept as a baseline. Each run's record carries the sha256 of the tree listing it started from. Restored after each run by deleting what the run added to the prefix, copying the baseline registry files back, and re-copying the game's files from the install when they differ; the cycle then checks the prefix tree equals its start (`reset:` line of the run log).
  - control: arm `control`: 800x600x24, xfwm4, audio drivers disabled, game under `unshare -n`, hover then click on **Options**, stop through the game's own Return, Quit and Exit Game buttons.
  - arms (one run each unless stated; each differs from `control` in one thing):
    - `control` (3 runs)
    - `no-wm`: no window manager
    - `audio-default`: audio drivers left to Wine
    - `net-host`: the game keeps the host's network
    - `click-immediate`: the click is sent right after the pointer move, with no wait for the hover highlight
    - `term-wm-close`: stop with Alt+F4 through the window manager
    - `term-kill`: stop with `wineserver -k`
    - `size-800x600x16`, `size-1024x768x24`, `size-1280x1024x24`, `size-640x480x16`: other screens
    - `input-save-default`: after Options, also click Save as default
  - n per arm: 3 for `control`, 1 for the others (a probe, not a measurement of variance); stopping rule: none, the list is fixed.
- **Measurements**: window appearance and geometry (process: `xdotool`); screen pixels and screenshots (screen: ImageMagick `import`); the game's exit status and the survival of any process (process: `/proc`); the game's copy and the prefix, file by file (file: sha256 of every entry before and after), and the registry's keys by name with a hash of each key's values (file: the three `.reg` files); the game's log (log: Wine's stderr).
- **Outputs**:
  - run records: `runs/E001/`;
  - evidence manifests: `evidence/E001/`, bundles in release `E001` (screenshots, `changes.log`, `run.log`, `wine.log`);
  - `findings/F002-iwp-runtime-wine-xvfb.md`, status `proposed`.

## Scripts

- `runtime/iwp/spike/cycle.py [--arm NAME] [--size WxHxD] [--wm xfwm4|none] [--audio off|default] [--net n0|host] [--click hover|immediate] [--input options|save-default] [--terminate ui-quit|wm-close|kill]`. With no arguments it is the `control` arm. Needs `IWP_PREFIX` and `E001_BUNDLES` (and `IWP_DIR` for the reset to re-copy changed game files). It writes the next `runs/E001/E001-r<nnnn>.json` and `evidence/E001/E001-r<nnnn>.manifest.json`, and refuses to start if runtime, setup, tools or formats have uncommitted changes.
- `setup/iwp/iwp-runtime.sh`: the profile that makes the prefix. Run it before the cycle.
- The arms in this README are the arguments each record's `actions.args` lists.
