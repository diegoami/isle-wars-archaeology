# E001 iwp-runtime-spike

Copied from the research task's contract when the experiment was created. After the first run this
file is append-only. A changed design is a new experiment, or `v2/`.

> Amendment 1 (rework of PR #26): the start-state definition, the `net-host` arm and the choice of runs are superseded; see the end of this file.

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

## Amendment 1 (rework of PR #26 after review; appended, nothing above is rewritten)

Three statements above are superseded. Read them as follows.

- **Start state.** The text above says each record's `start_state.sha256` identified the starting prefix. For E001-r0001 to r0014 it did not: that hash covered the game copy's listing and the registry key names only, so two prefixes with the same key names and different registry values got the same hash. From E001-r0015 the hash is the sha256 of the listing of every entry of the prefix before the launch (path, type, size and sha256 of each file, target of each link), the game copy and the registry files included. The id is still `S-cold-prefix-title`. Claims about identical starting states cite E001-r0015 onward only.
- **Network.** N0 is part of the contract: the game runs only under `unshare -n`. The arm `net-host` (E001-r0006, run with the host's network) was outside that contract. The option was removed from `cycle.py`; the record stays as recorded and is not evidence for anything in F002. The driver now looks at the game's network namespace (it is not this process's, and it sees only `lo`) and aborts the run when it cannot establish that.
- **Which runs count.** E001-r0001 to r0014 were produced by the driver as it was before the rework. They stay in `runs/E001/`, immutable. E001-r0015 to r0027 repeat the `control` arm 3 times and every other arm once (except `net-host`) with the reworked driver, from a prefix rebuilt by `setup/iwp/iwp-runtime.sh`; F002 cites them.

Also changed by the rework, not by this experiment's design: the machine-local locations (prefix, its baseline, bundles, exploration output) are refused when inside a checkout or overlapping the install or one another, and the profile's link checks resolve where a link ends instead of reading how it is written.

## Amendment 2 (second rework of PR #26; appended, nothing above is rewritten)

- **Which runs count.** E001-r0015 to r0027 stay in `runs/E001/`, immutable, and are superseded like r0001 to r0014. Their driver could record a run "completed" after a failed screenshot, did not check the prefix again immediately before the launch, and did not refuse a hard or symbolic link at a file it wrote. E001-r0028 to r0040 repeat the `control` arm 3 times and every other arm once (except `net-host`), with the round-2 driver, from a prefix removed and rebuilt by `setup/iwp/iwp-runtime.sh`. F002 cites them.
- **The run, as now done.**
  - Each run binds the install read-only in its own mount namespace and records that it did ("install bound read-only in the run's mount namespace").
  - It checks the prefix before anything starts and again immediately before the launch (`prefix.py` `prefix_problems`: drive mapping, links, second names, mounts, the registered game copy). The outer process checks it once more before it creates the namespace.
  - A run is `completed` only when every stage ran and both screenshots exist. Any other way out records `aborted: <why>`.
  - The start state's definition is unchanged. Its hash differs from r0015 to r0027's because the prefix was rebuilt.
- **Writes.** Every file the profile and the cycle write goes through `setup/iwp/safeio.py`. This holds for the game copy, the baseline, the reset, the bundles, the exploration output and the records. Records are created, never overwritten.
