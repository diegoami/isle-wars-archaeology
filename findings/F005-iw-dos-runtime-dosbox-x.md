# F005 DOS Isle Wars runs unattended under DOSBox-X 2024.03.01 and Xvfb with no network: launch, a known screen, one click, observation, termination and reset all work, and three runs show identical screens

- **Status**: proposed
- **Question**: Can DOS *Isle Wars* (the shareware 3.1 archive) be launched, brought to a known screen, given one input, observed, terminated and reset without a human, under DOSBox-X headless on Xvfb, with DOSBox-X mounting only a run copy of the game and the whole run cut off from the network? Do three runs from the same start show identical screens? What does the game write? Can DOSBox-X's savestates (I2) and a memory read (I1) be used, and does this build have a debugger?
- **Tests claims**: none (runtime feasibility; it feeds W4b, W5b and the experiments)
- **Experiment and runs**: E003; runs E003-r0001 to E003-r0012, in `runs/E003/`
- **Artifact**: set `iw-dos-3.1-30121376`, variant none
- **Max intervention**: I2 (the `savestate` arm, E003-r0007, saves and restores a DOSBox-X savestate; the `debugger` arm, E003-r0008 and E003-r0009, is I1; every other run is I0)
- **Tier reached**: V2 (the original, headless, under an emulator; no run on real DOS hardware or another emulator, so no V3)
- **Confidence**: not applicable as an outcome until review. The control arm ran 3 times, and the 3 runs agree on every observation except the timings, and on every output except the driver's `run.log`. The `debugger` arm ran twice; every other arm is one run, a probe, not a measurement of variance. One machine (WSL2), one DOSBox-X build, one day.

## Answer

- **Unattended launch.** The DOSBox-X path works unattended for the control arm. Three runs completed with no human (E003-r0001, E003-r0002, E003-r0003), each exiting 0 from the loop of the Done-when. Each ran launch, the known screen, one click, two screenshots, a stop, and a reset. In each, the driver saw DOSBox-X in a network namespace other than its own, seeing only the loopback interface (observation "network interfaces DOSBox-X sees" is `lo`).
- **The known screen** is the game's map with its option box: three buttons, Set level, Default and a load-saved-game button, and the words "choose option". It is the first screen at which the game was seen to wait for input. It appears 16.92 to 17.07 s after launch at `cycles=fixed 3000` (observation "option box reached and stable", E003-r0001 to E003-r0003, E003-r0007 to E003-r0012). Before it, exploration round 1 (`p2`, a capture every 2 s, not a record) saw a publisher logo, a "presents" screen and the title screen (the last with a credit line and a shareware mark), which went by with no input. The records do not capture these screens. The driver recognises the option box by pixels, not by a delay.
- **Identical screens.** The `before` screenshot is byte-identical in all three control runs: raw RGB pixel sha256 `6d7d28500a9562d2a5bf939c7ef1f404e4945f6b7e3beaf6bb33b8a59af6196f`, PNG file sha256 `ce3d9ebda664b0646809249e2aa7c7e5714061a09f13c0e26db2da6984caf839`. The `after` screenshot is identical too (pixels `c38316e1b2d6fcaf...`, file `79ac1e16f5cc5df2...`). Both are the same in all 12 records, whatever the arm: the host's clock (E003-r0004), more cycles (E003-r0005, E003-r0006), a savestate (E003-r0007), the debugger flag (E003-r0008, E003-r0009), DOSBox-X's own screenshot (E003-r0010), or another way to stop (E003-r0011, E003-r0012).
- **What varies** between runs, in these records, is time, the driver's log and the savestate's memory image, not the captured screen:
  - the seconds to the option box (16.92 to 17.07 s in the fixed-3000 runs) and the other timings (E003-r0003's pointer at 0.08 s against 0.07 s);
  - the driver's `run.log`, a different hash in every record's outputs. DOSBox-X's `dosbox.log` is byte-identical in the three control runs and in E003-r0011 (`db94d26adeb85548`). It differs in the other arms, and between the two `debugger` runs (E003-r0008 `24d5805d3c74b677`, E003-r0009 `fbbc957bead1a89f`); what differs in it was not examined;
  - the savestate's memory image (E003-r0007, E003-r0008 and E003-r0009 all differ; see the probes). Why it differs is unknown.
  
  With the host's clock (E003-r0004, one run) the captured screens were those of the fixed clock 01-01-1994 12:00:00. So no fixed clock was needed for identical captures up to the Select level dialog in these runs; whether the first screens read the clock at all is not shown. The control fixes it anyway, so that a later screen that reads the clock starts from the same value.
- **The same start.** All 12 runs started from the same run copy: `start_state.sha256` is `ea77bd8651b51f116403b139098f890704d4af652c82b6137ac439b880a0b8f9` in every record. It hashes the listing of every entry of the run copy, with each file's size, sha256 and modification time. It covers the run copy only: DOSBox-X's own state at the start is not hashed, and each run starts a fresh DOSBox-X process from a generated configuration (the record's restore procedure).
- **One click takes effect.** The game is mouse-driven only (its documentation says the keyboard is never needed). The driver moves the X pointer onto Set level and waits until the game has drawn its own pointer there (0.07 s in E003-r0001 and E003-r0002, 0.08 s in E003-r0003), then clicks. The Select level dialog (Easy, Normal, Hard, Hardest) is up 0.01 s after the click in E003-r0001 to E003-r0003. This needs DOSBox-X's `[sdl] mouse_emulation=never` and `autolock=false`, found in exploration round 1 (`m_never` against `m_always`).
- **Observation.** The driver captures the 640x350 window from the X root with ImageMagick `import` and writes the PNG itself. DOSBox-X's own screenshot (F12+P) gives the same pixels: in E003-r0010 its PNG decodes to the pixel sha256 of `before.png` (observation "dosbox-before.png pixels equal before.png's" is `True`). Two of DOSBox-X's own PNGs of the same screen were byte-identical (exploration round 2, `cap-1`, `cap-2`). Either path gives stable bytes.
- **Terminate.** SIGTERM ends DOSBox-X in 0.05 s with status 0 when its configuration has `[dosbox] quit warning=false` (E003-r0001 to E003-r0010). SIGKILL ends it in 0.05 s, status -9 (E003-r0011). Closing its X client (`xdotool windowkill`) ends it in 0.05 s, status 1 (E003-r0012). Without `quit warning=false`, SIGTERM took 79.5 s and gave status 1 (exploration round 1, `t1/term.txt`). The game's keys Escape, q, x, Ctrl+C, Ctrl+Break, Alt+X and F10 did not end it (same file). No process of a run survived its stop in any record (observation "processes of this run still alive after terminate" is 0). The exit wait polls every 0.05 s, so 0.05 s means the process had gone by the first check after the signal; differences below that interval would not show.
- **Reset works.** After every run the run copy equalled its state before the launch (observation "run copy after reset equals the run copy before launch" is `yes` in all 12 records). The reset removes what the game added.
- **What the game writes.** Every run added one file to the run copy, `ISLEWAR.SCR`: 20 bytes, sha256 `1cc857c57bc83a00ef11c24b0abaf5ea4c3650292c649650fefd399e7354ab50` in all 12 runs (observation "run copy: added ISLEWAR.SCR"). No file of the set changed (`changes.log`: added 1, removed 0, changed 0). The run copy is snapshotted before the launch and after the stop, so the records do not say when during the run the file was written. Its role is not known; nothing here reads it. Clicking Default instead of Set level also wrote `ISLEWAR.DFT`, 9 bytes, in round-1 exploration only (resume note of T11); no record clicks Default.
- **The copy was bound read-only in every run.** Each of the 12 runs bound `IW_DOS_DIR` read-only in its own mount namespace before anything started (observation "IW_DOS_DIR bound read-only in the run's mount namespace" is `yes`). `register_artifact.py check "$IW_DOS_DIR" iw-dos-3.1-30121376 --strict` exits 0 after all runs (`measurements/done-when/check-*.txt`).
- **Audio off.** Every run's configuration turns off the mixer output, the PC speaker, Sound Blaster, Gravis and MIDI, and SDL's audio driver is `dummy`. The configuration gave the game no sound device. No audio was captured, so the silence is configured, not measured. Whether the game behaves differently with sound was not tried.
- **Speed.** At `fixed 3000` the option box is at about 17 s and a whole cycle takes 17 to 18 s (observation "cycle seconds"). At `fixed 30000` it is at 13.62 s, cycle 15 s (E003-r0006). At `max` it is at 12.88 s, cycle 14 s (E003-r0005). The screens are the same. Ten times the cycles shortened the wait by about 3.4 s and `max` by about 4.1 s, one run each. Why the rest remains is not measured: the cycle rate `max` reached, the CPU use and the spread of these timings were not recorded. A delay of the shareware build is one hypothesis (the game's documentation says the registered version loads faster); emulator or host overhead is another.

### Per-path table

| Path | launch | known screen | input | observe | terminate | reset |
| --- | --- | --- | --- | --- | --- | --- |
| DOSBox-X 2024.03.01 + Xvfb 800x600x24, no window manager, `cycles=fixed 3000`, fixed clock, sound off, private network namespace, stop by SIGTERM (control) | works (E003-r0001, E003-r0002, E003-r0003) | works (E003-r0001 to E003-r0003: option box, identical `before` hash) | works (E003-r0001 to E003-r0003: click on Set level, Select level dialog) | works (E003-r0001 to E003-r0003: window capture and pixel tests) | works (E003-r0001 to E003-r0003: 0.05 s, status 0) | works (E003-r0001 to E003-r0003: observation "run copy after reset equals the run copy before launch" `yes`) |
| same, the host's clock | works (E003-r0004) | works (E003-r0004: the same `before` hash) | works (E003-r0004) | works (E003-r0004) | works (E003-r0004) | works (E003-r0004) |
| same, `cycles=max` | works (E003-r0005) | works (E003-r0005: 12.88 s, the same hash) | works (E003-r0005) | works (E003-r0005) | works (E003-r0005) | works (E003-r0005) |
| same, `cycles=fixed 30000` | works (E003-r0006) | works (E003-r0006: 13.62 s, the same hash) | works (E003-r0006) | works (E003-r0006) | works (E003-r0006) | works (E003-r0006) |
| same, observed by DOSBox-X's own screenshot (F12+P) | works (E003-r0010) | works (E003-r0010) | works (E003-r0010) | works (E003-r0010: its pixels equal `before.png`'s) | works (E003-r0010) | works (E003-r0010) |
| same, stopped by SIGKILL | works (E003-r0011) | works (E003-r0011) | works (E003-r0011) | works (E003-r0011) | works (E003-r0011: 0.05 s, status -9) | works (E003-r0011) |
| same, stopped by closing the X client | works (E003-r0012) | works (E003-r0012) | works (E003-r0012) | works (E003-r0012) | works (E003-r0012: 0.05 s, status 1) | works (E003-r0012) |
| same, stopped by the game's keys (Escape, q, x, Ctrl+C, Ctrl+Break, Alt+X, F10), exploration | not tried: exploration of the stop only (round 1 `t1`) | not tried: same | not tried: same | not tried: same | fails: DOSBox-X still alive after each key (round 1 `out/t1/term.txt`: "Escape: alive" ... "F10: alive") | not tried: same |
| same, SIGTERM with DOSBox-X's default `quit warning`, exploration | not tried: exploration of the stop only (round 1 `t1`) | not tried: same | not tried: same | not tried: same | fails: 79.5 s, status 1 (round 1 `out/t1/term.txt`: "SIGTERM status 1 after 79.511813821") | not tried: same |
| round 2's probe configuration (host clock, run copy at `/tmp/w/game`) with three lines added before `c:` in [autoexec]: `config -securemode`, `mount d /tmp`, `echo after-mount`; exploration | fails: no window was found and the option box was not recognised (round 2 `out/secure/shots.txt`: "window none", "menu timeout"). The same probe configuration without those lines reached the option box (`det-host-1` to `-3`). Which of the three lines, or what else, caused the failure was not isolated | not tried: no launch | not tried: no launch | not tried: no launch | not tried: no launch | not tried: no launch |
| Real DOS hardware, or another emulator | not tried: the task's path is DOSBox-X (07 W3b); no other was available | not tried: same | not tried: same | not tried: same | not tried: same | not tried: same |

### Probe table

| Probe | Result |
| --- | --- |
| Savestate (I2), arm `savestate` | works for the screen (E003-r0007): F12+S at the option box wrote a savestate (observation "savestate written after F12+S"); the screen after the save equals `before.png`; after the click and F12+L the option box is back in 0.02 s, and `restored.png` equals `before.png` (observations `True`). That the restored game or machine state equals the saved one is not shown |
| Memory read (I1), arm `debugger` | works as a read (E003-r0008, E003-r0009): the savestate's Memory member is a zlib stream that inflates to 17055864 bytes, and the screen after the save equals `before.png`, so the read did not change the captured screen; identical across two identical starts: fails: the inflated images differ (E003-r0008 `bd8f2257b8fadab7...`, E003-r0009 `4c2294a7aeb6676c...`; E003-r0007 `90a8bf307cfa73ec...`). In exploration (round 2 `savestate-members.txt`, every image compared with `det-host-1`'s): the two other host-clock starts with the same steps differed from it in 2651 (`det-host-2`) and 2841 (`det-host-3`) bytes; the three fixed-clock starts, another setting, in 3073 to 3106 bytes; `a1`, another script (save, click, restore), in 2312 bytes. The differing bytes lie at the start of memory, near 0x2a000 to 0x2d000 and 0x91000 to 0x93000, and past 16 MiB. Within each group of three the inflated hashes all differ. What the differing bytes are, and why they differ, is unknown |
| Debugger (I1), arm `debugger` | fails at every entry point tried: `-break-start` changed nothing (E003-r0008, E003-r0009 reached the option box at 16.93 and 17.04 s with the control's screens); the shell answers `DEBUGBOX` with `Bad command or filename - "DEBUGBOX"` (round 2 `dbg-text2`, release `E003` asset `b5d15a9aade867ce-dbg-text2-text.rgb`, raw 800x600x24 RGB, sha256 `b5d15a9aade867ce2a5f003fb62cb66e32be4f079a23b28cbf30c6a0665855e1`); `dosbox-x -help` lists no debugger option. Other ways in (a key combination, another build) were not tried |
| Determinism, all arms | works for the captured screens: one `before` hash and one `after` hash in all 12 records, from one start-state hash. Not shown for DOSBox-X's state: the memory images differ (row above) |
| Network N0 | works: every record observes DOSBox-X in a network namespace other than the outer process's, seeing only `lo`; the configuration turns off IPX, NE2000, every serial and parallel port and the printer |
| Runtime writes | works (diff of the run copy): `ISLEWAR.SCR`, 20 bytes, the same bytes in all 12 runs; nothing else |

## Method

**Artifact.** Set `iw-dos-3.1-30121376` ([`artifacts/known.json`](../artifacts/known.json), F004). `setup/iw-dos/iw-dos-runtime.sh` copies `IW_DOS_DIR` into the run copy, and every run checks that copy against the set before it starts. `IW_DOS_DIR` was read and hashed only.

**Runtime.** `runtime/iw-dos/spike/cycle.py` at the commit named in each record (`code_commit`: `c95ab816e71d` for E003-r0001 to E003-r0003, `238d54c32846` for E003-r0004 to E003-r0012; the cycle and its configuration module are the same at both). The platform was Linux 6.18 (WSL2) with:
- DOSBox-X 2024.03.01 SDL2 (Ubuntu `2024.03.01+dfsg-1build2`);
- Xvfb from package 2:21.1.12-1ubuntu1.8;
- xdotool 3.20160805.1, ImageMagick 6.9.12-98 and Python 3.12.3.

The exact fingerprint is in every record.

**Locations and the seal.** The run directory (`IW_DOS_RUN`), the evidence bundles (`E003_BUNDLES`) and any exploration output are machine-local. The profile and the cycle confine them before they change or launch anything (`setup/iw-dos/rundir.py`, with `setup/iwp/locations.py`'s `confine` as it is on `main`). Each must be absolute, must resolve outside every checkout and worktree, must not contain this repository, and must not overlap `IW_DOS_DIR` or one another. The guarantees then hold at the point of use:
- **One writer.** Every file the profile and the cycle write goes through `setup/iwp/safeio.py`, as on `main`.
- **The run copy** `<IW_DOS_RUN>/game` is a real directory holding the registered files as plain files of its own: no link, no subdirectory, no file with a second name, none of `IW_DOS_DIR`'s own inodes, and nothing mounted in it. Then `tools/register_artifact.py check <run copy> iw-dos-3.1-30121376 --strict` must exit 0. A hard link to the copy matters: the read-only bind guards a path, and the run's namespace root may write any inode the user owns.
- **No alias of the copy** (added in the first rework of PR #37, after the runs). A bind mount does not show in a canonical path, so `rundir.py` also refuses, by mounts and by device and inode:
  - a mount point at or under the run directory;
  - a run copy, run directory or directory above them that is `IW_DOS_DIR`;
  - `IW_DOS_DIR`, or a directory above it, that is the run copy or the run directory;
  - an entry of the run copy that is the only name of one of `IW_DOS_DIR`'s files or directories.

  `sync` checks this before it creates, removes or re-permissions anything, and again once the run copy exists. Before the rework, a run copy that was a writable bind mount of the copy would have lost the copy's files to `sync` (the review's reproduction). No run was affected: every record observes 0 problems in the run copy before and immediately before the launch, and `register_artifact.py check --strict` on `IW_DOS_DIR` passed after the runs.
- **The configuration** is generated by `runtime/iw-dos/spike/dosconf.py` and checked by it before the launch. [autoexec] must hold exactly one `mount`, of drive C, of the run copy's canonical path. Every other line must be one of `@echo off`, `date`, `time`, `c:`, `ISLEWAR` and `exit`. `imgmount`, `subst`, a second mount and any other line abort the run. Automount, IPX, NE2000, the serial and parallel ports, the printer and every sound device are fixed off. The paths DOSBox-X writes (captures, savefile, mapper file) must lie in the run's private work directory. The command line may name that one configuration and a fixed list of flags, and no `-c`, `-set` or second `-conf`.
- **The run.** Each run binds `IW_DOS_DIR` read-only in its own mount namespace. It checks the run copy before anything starts, and the run copy and the configuration (read back from disk) immediately before DOSBox-X starts. The outer process checks the run copy too, before the namespaces exist. A run is recorded `completed` only when every stage ran, both screenshots (and the probe's own outputs) exist, and the Select level dialog was seen. Any failure, crash or interruption, and any failed clean-up stage, records `aborted: <why>` and exits nonzero.

Each guarantee is exercised on synthetic fixtures by `tests/test_iw_dos_seal.py`. `tests/mutants_iw_dos.py` removes each in turn and shows its tests failing (11 of 11 mutants killed; it stops with exit 2 when a target test skips). The alias refusal is tested with real bind mounts under `unshare -rm` (`MountAliasTest`).

**One run, in order:**
1. Inside `unshare -rmpfn`, mount a tmpfs on `/tmp`, bind `IW_DOS_DIR` read-only, check it is read-only, and check the run copy.
2. Write the configuration to `/tmp/w/dosbox.conf`. Start Xvfb `:61` at 800x600x24 and wait until `xdpyinfo` answers.
3. Snapshot the run copy: the size, sha256 and modification time of every file.
4. Check the run copy and the configuration again, then start `dosbox-x -conf /tmp/w/dosbox.conf -nogui -nomenu -fastlaunch -nopromptfolder` (plus `-break-start` in the `debugger` arm), with `HOME` in the work directory.
5. Require that DOSBox-X's network namespace is not the outer process's and that it sees only `lo`. Wait for its window at 640x350 (it is at 80,100 on the 800x600 screen).
6. Wait until the option box's colours are present (the red Set level text and the cyan "choose option" text) and two captures 0.4 s apart are equal. Capture `before.png`.
7. Move the pointer onto Set level, wait until the screen changes (the game draws its pointer), click, wait for the orange title of the Select level dialog and a stable screen, and capture `after.png`.
8. Stop DOSBox-X (SIGTERM; SIGKILL or a window close in their arms) and wait for its exit. Stop Xvfb.
9. Snapshot again, diff into `changes.log`, and reset with `rundir.py sync`. Check the run copy equals its first snapshot. Write the bundles, the manifest and the record.

**DOSBox-X settings that matter.** Found in exploration and kept in every run:
- `mouse_emulation=never` and `autolock=false`: the click reaches the game (round 1, `m_never` against `m_always`);
- `quit warning=false`: SIGTERM ends DOSBox-X at once (round 2, `term-sigterm`, against round 1 `t1`);
- `[dosbox] savefile`: F12+S writes a savestate file there, a zip of DOSBox-X's components (round 2, `a1`);
- `synchronize time=false` with DATE and TIME in [autoexec]: the fixed clock of the control.

**Waits.** Every wait is a poll on a condition with a timeout:
- Xvfb, 20 s;
- the 640x350 window, 30 s;
- the option box, 120 s;
- the pointer drawn, 5 s;
- the dialog, 20 s;
- a stable screen, 30 s;
- the savestate file and DOSBox-X's screenshot, 30 and 20 s;
- the exit, 15 s, then SIGKILL and an aborted status.

Poll intervals are 0.05 to 0.25 s. The fixed sleeps are the 0.4 s between the two captures of the stability test, and the 0.15 s key holds of DOSBox-X's F12 host-key combinations (exploration round 1 sent them so, and they were taken).

**Arms.** The arms and their arguments are in [`experiments/E003-iw-dos-runtime-spike/README.md`](../experiments/E003-iw-dos-runtime-spike/README.md) and in each record's `actions.args`.

**Network.**
- N0 for the game, always. The whole run (Xvfb, xdotool, DOSBox-X) is in a private network namespace. In all 12 records the observation "DOSBox-X in a network namespace other than the outer process's" is `yes`, and "network interfaces DOSBox-X sees" is `lo`.
- N3: none; this task installed nothing.
- N1: `git push` and `gh` for the branch and the PR.

## Observations

Raw values, from the records (`observations`); the full list for each run is in [`measurements/records-r0001-r0012.txt`](../experiments/E003-iw-dos-runtime-spike/measurements/records-r0001-r0012.txt).

Control runs:

| Quantity | E003-r0001 | E003-r0002 | E003-r0003 |
| --- | --- | --- | --- |
| `IW_DOS_DIR` bound read-only in the run's mount namespace | yes | yes | yes |
| run copy check: problems before anything starts, and immediately before launch | 0, 0 | 0, 0 | 0, 0 |
| configuration check immediately before launch: problems | 0 | 0 | 0 |
| configuration sha256 (run copy path as `<IW_DOS_RUN>/game`) | `45eeaf10a0f0488b...` | same | same |
| Xvfb ready (s) | 0.11 | 0.1 | 0.1 |
| DOSBox-X in its own network namespace; interfaces it sees | yes; `lo` | yes; `lo` | yes; `lo` |
| window at 640x350 after launch (s); position | 1.6; 80,100 | 1.6; 80,100 | 1.61; 80,100 |
| option box reached and stable (s after launch) | 17.02 | 16.97 | 16.99 |
| `start_state.sha256` | `ea77bd8651b51f11...` | same | same |
| `before.png` raw RGB8 pixel sha256 | `6d7d28500a9562d2...` | same | same |
| `before.png` file sha256 | `ce3d9ebda664b064...` | same | same |
| `after.png` raw RGB8 pixel sha256 | `c38316e1b2d6fcaf...` | same | same |
| `after.png` file sha256 | `79ac1e16f5cc5df2...` | same | same |
| pointer drawn at Set level (s) | 0.07 | 0.07 | 0.08 |
| Select level dialog after click (s) | 0.01 | 0.01 | 0.01 |
| DOSBox-X exit after SIGTERM (s); status | 0.05; 0 | 0.05; 0 | 0.05; 0 |
| processes of the run alive after terminate | 0 | 0 | 0 |
| run copy: added / removed / changed | 1/0/0 (`ISLEWAR.SCR`) | 1/0/0 | 1/0/0 |
| run copy after reset equals its state before launch | yes | yes | yes |
| cycle seconds | 17 | 18 | 18 |

Other arms:

| Run | Arm | Status | Notable |
| --- | --- | --- | --- |
| E003-r0004 | `clock-host` | completed | the control's `before` and `after` hashes; window at 640x350 after 0.64 s and the option box at 15.99 s (no DATE and TIME commands before the game); configuration `61340e17fa4b...` |
| E003-r0005 | `speed-max` | completed | option box at 12.88 s; the same hashes; cycle 14 s |
| E003-r0006 | `speed-30000` | completed | option box at 13.62 s; the same hashes; cycle 15 s |
| E003-r0007 | `savestate` | completed | savestate `22a69214084e...`; `postsave.png` and `restored.png` equal `before.png`; option box back 0.02 s after F12+L; cycle 20 s |
| E003-r0008, E003-r0009 | `debugger` | completed | `-break-start` passed; the option box at 16.93 and 17.04 s; Memory inflated to 17055864 bytes in both, sha256 `bd8f2257b8fa...` and `4c2294a7aeb6...`; the screen after the save equals `before.png` |
| E003-r0010 | `dosbox-capture` | completed | DOSBox-X's PNG (`093f8db4268b...`, 640x350) decodes to `before.png`'s pixels |
| E003-r0011 | `term-kill` | completed | SIGKILL, exit status -9 after 0.05 s; reset as usual |
| E003-r0012 | `term-close` | completed | `xdotool windowkill`, exit status 1 after 0.05 s |

Exploration before the recorded runs is in [`experiments/E003-iw-dos-runtime-spike/measurements/`](../experiments/E003-iw-dos-runtime-spike/measurements/): round 1 (`explore-round1/`, T11's first round, by hand) and round 2 (`explore-round2/`, scripted probes). It is not records. This finding cites it only where it says so: the mouse settings, the stop by keys and by SIGTERM without `quit warning=false`, secure mode, the debugger's absence, and the memory images' differences. One round-1 probe (`q1`, an Xvfb screen of 640x350) showed the map's sea and the bottom panel in swapped colours, with the window placed at 0,-25 (`out/q1/wid.txt`). It was not repeated at that screen size, and no record or round-2 probe at 800x600 showed it. Its cause is unknown.

## Inferences

- From E003-r0001 to E003-r0003 (identical hashes, one start-state hash, 3 of 3 completed): the DOSBox-X path is repeatable up to the Select level dialog at this setting, as far as the captured screens show. The game's first screens show no run-to-run variation that this setup can see. The only variation seen is in the timings, in the driver's `run.log`, and, in the arms that save a state, in the memory image.
- From E003-r0004 against E003-r0001 to E003-r0003: one run with the host's clock gave the same captured screens as the fixed clock. Whether the first screens read the clock at all, and whether a later screen (the board, a battle) depends on it, is open, so the control keeps the clock fixed.
- From E003-r0005 and E003-r0006 against the control: the time to the option box falls from about 17 s to 13.62 s with ten times the cycles and to 12.88 s at `max`, one run each. What the remaining 12.9 to 13.6 s is spent on is not measured: neither the cycle rate reached at `max` nor the CPU use was recorded. Two hypotheses fit: a delay of the shareware build (its documentation says the registered version loads faster), and emulator or host overhead; neither is shown.
- From E003-r0007 (one run): a DOSBox-X savestate taken at the option box restores the same captured screen after the game has moved on to the dialog. That makes savestates a candidate cheap way back to a known screen for W4b and W5b; that the restored state equals the saved one beyond the screen is not shown. It is I2: a restored state is DOSBox-X's reconstruction of the machine, and nothing about the original game's behaviour follows from it.
- From E003-r0008 and E003-r0009, with exploration round 2: a memory image can be read at the option box without changing the captured screen. It is not the same across identical starts (E003-r0008 against E003-r0009; `det-host-2` and `-3` against `-1`). Why is unknown, and what the differing bytes are was not looked at. Hypotheses, none tested: the save is taken at a real-time moment rather than at a fixed point of emulated time, so timer or buffer contents differ; uninitialised bytes; an effect of how DOSBox-X serialises its state; or game state that differs although the screen does not. Which bytes hold game state was not looked at (W4b), so a comparison of memory across runs has first to find out what varies and why.
- From E003-r0010: DOSBox-X's own screenshot and the X window capture give the same pixels here. Either can observe; the window capture needs no key sent to DOSBox-X.
- From E003-r0011 and E003-r0012 against the control: each of the three stops was recorded at 0.05 s, the exit wait's poll interval, so they are not told apart at that resolution. SIGTERM is the only one with status 0. After each stop the diff of the run copy was the same (one added `ISLEWAR.SCR`, the same bytes) and the reset restored the run copy. When the file is written within a run is not shown by the records (snapshots before the launch and after the stop).
- From the 12 diffs: in runs that go to these screens the game writes one 20-byte file, the same bytes every time, including with the host's clock (E003-r0004) and at the other speeds (E003-r0005, E003-r0006), one run each. The set needs no successor for these runs, because no file of the set changed. The record's set is the one that ran.

## Alternatives considered

- **Identical hashes only show the capture is stable, not the game.** Not excluded as such. The `before` screen is the option box by eye and by the predicate the cycle waits on. DOSBox-X's own screenshot gives the same pixels (E003-r0010), so the X capture adds nothing that DOSBox-X's own capture does not show.
- **The runs agree only because the reset hid what run 1 changed.** Excluded. Every run, the first included, started from the same start-state hash over the whole run copy, and every diff is the same one added file.
- **DOSBox-X reached the host's files or network after all.** Network: excluded for these runs by the check, which requires another namespace and only `lo`, and aborts otherwise. Files: the configuration mounts only the run copy, and `IW_DOS_DIR` is read-only inside the run. But DOSBox-X itself is a process with the user's access to every other host file. A DOS program could reach more only through DOSBox-X's own commands (`MOUNT` on its Z: drive), which the game was not seen to use. A probe that added `config -securemode`, `mount d /tmp` and `echo after-mount` to [autoexec] did not reach a recognised window or the option box (round 2 `secure`); which line caused that was not isolated, so whether secure mode works here is open.
- **The savestate restored an older screen by chance.** Excluded for E003-r0007. The dialog was up before F12+L (`after.png`), and after it the option box came back with the pixels of `before.png`.
- **`-break-start` was taken but the debugger runs silently.** Not excluded by E003-r0008 and E003-r0009 alone, which ran as the control did. The shell's answer to `DEBUGBOX` (round 2, release `E003` asset `b5d15a9aade867ce-dbg-text2-text.rgb`) and the help text, which lists no debugger flag, both find no debugger at these entry points; other entry points were not tried.

## What this does not establish

- Real DOS hardware or another emulator: not tried, so nothing about V3 (timing, rendering).
- *Isle Wars Pro*: nothing; this finding is DOS *Isle Wars*' only (CLAUDE.md rule 19).
- Whether the game needs, or tries to use, a network: it never had one.
- Anything beyond the logo screens, the option box and the Select level dialog. A level, Default, Load saved game, the board, a turn, the Sound, Scores, Speed, Save and Quit buttons, and the game's own way out were not tried. What `ISLEWAR.SCR` holds, and what the game writes while playing, are open.
- Keyboard input into the game: none was sent; the game is mouse-driven. The F12 combinations went to DOSBox-X.
- Audio output: no sound was produced or captured.
- What the timing of the logo screens is, or whether a registered build is faster: the registered version is unknown (rule 19).
- Game state in memory: not looked for (W4b). The memory image's layout is DOSBox-X's, read only as a whole.
- Repeatability beyond one machine, one DOSBox-X build and one day; the probe arms are single runs (the `debugger` arm two).
- A sandbox: DOSBox-X is not confined beyond the read-only `IW_DOS_DIR`, the private namespaces and its configuration.
- A driver: this finding supports the claim that the cycle is feasible, not that `cycle.py` is a driver (W5b).

## Where the evidence is

- Run records: `runs/E003/E003-r0001.json` to `E003-r0012.json`.
- Evidence manifests: `evidence/E003/E003-r0001.manifest.json` to `E003-r0012.manifest.json`.
- The bundles (screenshots, `changes.log`, `run.log`, `dosbox.log`, `dosbox.conf.txt`) are release `E003` assets, each named `<sha256[:16]>-<name>`, as its manifest says; no bundle is committed. Release `E003` also holds the round-2 `dbg-text2` capture, `b5d15a9aade867ce-dbg-text2-text.rgb`. The savestates are not kept: they hold the game's memory (rule 18). Their hashes are in the records.
- The outputs of the Done-when commands: `experiments/E003-iw-dos-runtime-spike/measurements/done-when/`.
- Exploration: `experiments/E003-iw-dos-runtime-spike/measurements/explore-round1/`, `explore-round2/` and `explore-cycle/` (one `--explore` run of the cycle before the records).

## Reproduction

The machine needs:
- DOSBox-X 2024.03.01, Xvfb, xdotool, ImageMagick and util-linux;
- `IW_DOS_DIR` set to the extracted archive, and `IW_DOS_RUN` and `E003_BUNDLES` set to two locations outside every checkout and `IW_DOS_DIR`;
- a `setup/iw-dos/iw-dos-runtime.sh` that prints `ready`.

Then:

```text
setup/iw-dos/iw-dos-runtime.sh
for i in 1 2 3; do python3 runtime/iw-dos/spike/cycle.py || exit 1; done
python3 runtime/iw-dos/spike/cycle.py --arm savestate --probe savestate
python3 tools/register_artifact.py check "$IW_DOS_DIR" iw-dos-3.1-30121376 --strict
```

The arms and their arguments are listed in the experiment README.
