# F002 Isle Wars Pro runs unattended under Wine 9.0, Xvfb and xfwm4 with no network: launch, a known screen, one click, observation, termination and reset all work

> **Correction (2026-10-03, review of PR #26):** the first version of this finding cited E001-r0001 to E001-r0014. Those records stay in `runs/E001/` unchanged but are superseded: their `start_state.sha256` covered only the game copy's listing and the registry key names, so it did not identify the starting prefix; one of them (E001-r0006) ran the game on the host's network, outside the N0 contract; and the driver then accepted machine-local locations without confining them. The host-network arm was not repeated and is not evidence for anything here.
>
> **Correction 2 (2026-10-03, second review of PR #26):** the second version cited E001-r0015 to E001-r0027. Those records also stay unchanged and are superseded. Their driver could record a run "completed" after a failed screenshot, did not check the prefix again immediately before the launch, and copied files without refusing a hard link or a symbolic link at the destination. None of E001-r0015 to E001-r0027 hit one of these faults, but their records cannot show that, so every claim below cites E001-r0028 to E001-r0040. These were made with the round-2 driver from a rebuilt prefix. That driver binds the install read-only for the run, checks the prefix before anything starts and again immediately before the launch, records "completed" only for a full cycle, and writes every file through one confined writer.

- **Status**: proposed
- **Question**: Can Isle Wars Pro (the unregistered 2.0 install) be launched, brought to a known screen, given one input, observed, terminated and reset without a human, on Wine 9.0 (32-bit prefix) under Xvfb and xfwm4, with the game cut off from the network? What does it write, and what does it need from the display and from audio?
- **Tests claims**: none (runtime feasibility; it feeds W4a, W5a and the experiments)
- **Experiment and runs**: E001; runs E001-r0028 to E001-r0040, in `runs/E001/` (E001-r0001 to E001-r0027 are superseded, see the corrections)
- **Artifact**: set `iwp-2.0-996e86c5`, variant none; the one run that clicks Save as default (E001-r0040) is recorded under the successor set `iwp-2.0-3694a782`, which declares `xtras/Isledft.dat` a runtime write
- **Max intervention**: I0
- **Tier reached**: V2 (the original, headless, under Wine; no native Windows run, so no V3)
- **Confidence**: not applicable as an outcome until review. The control arm ran 3 times, and the 3 runs agree on every measured quantity except elapsed seconds. Every other arm is one run, so it is a probe, not a measurement of variance. One machine (WSL2), one Wine build.

## Answer

- **Unattended launch.** The Wine path works unattended for the control arm. Three runs from a freshly built prefix completed with no human (E001-r0028, E001-r0029, E001-r0030), and each exited 0. Each ran launch, title screen, one click, screenshots, a stop through the game's own buttons, and a reset. In each, the driver saw the game in a network namespace of its own with only the loopback interface (observation "network interfaces the game sees" is `lo`).
- **The known screen** is the title screen of the unregistered build: the game name, a line marking the build as the unregistered shareware version, and a bottom bar of six menu labels. It appears 6.6 to 6.7 seconds after launch, and the driver recognises it by pixels, not by a delay. The `before` screenshot is byte-identical in all three control runs (PNG sha256 `ae6e98d28d379bb4d2a9c4793ce5aac51222be771f1c666d8a614c26758bab83`, E001-r0028 to E001-r0030). It is the same in every other 800x600x24 arm (E001-r0031 to E001-r0035, E001-r0040), and the same as in the superseded runs.
- **The same start.** The three control runs started from the same prefix: their `start_state.sha256` is the same, `34ac62c31ddaa5f4e9a1b975a956c94ebe935109189d0fffe8939dc2bddfa427`. That is the hash of the listing of every entry of the prefix: the size and sha256 of each file (the registry files included) and the target of each link. It is the same in all 13 records. It differs from the superseded runs' hash because the prefix was rebuilt, and a rebuilt prefix has new registry timestamps.
- **One click takes effect**, but only after the pointer has moved onto the label and the label has highlighted. A click sent right after the move was dropped (E001-r0033). With the wait on the highlight, the Options screen came up in 0.01 to 0.03 s in 11 of 11 runs that tried it (E001-r0028 to E001-r0032, E001-r0034 to E001-r0038, E001-r0040).
- **The game stops three ways.**
  - Its own Return, Quit and Exit Game buttons end the process with status 0 about 14.7 to 14.8 s after the last click (E001-r0028 to E001-r0030, E001-r0032, E001-r0036 to E001-r0038, E001-r0040; 16.7 s in E001-r0031).
  - Alt+F4 through xfwm4 ends it with status 0, after 3.4 s in E001-r0034 and 0.4 s in the superseded E001-r0021. Each is one run, so the delay is not a measurement.
  - `wineserver -k` ends it at once with status 0 (E001-r0035).

  Only the first two let the game remove its temporary files; the kill leaves them (see Observations).
- **Reset works.** After every run, including the 2 that aborted, the prefix tree (every file's size and hash, every link) equalled its state before the launch. The `reset:` line of each `run.log` says so, and the observation "prefix after reset equals prefix before launch" is `yes` in all 13 records.
- **The game copy** was not changed by any run except E001-r0040. That run clicked Save as default on the Options screen, and `xtras/Isledft.dat` grew from 15 to 16 bytes. This is the only write to the game's own files seen in E001's runs; `xtras/Islepro.dat` was not written in any arm.
- **The install was never writable during a run.** Each of the 13 runs bound it read-only in its own mount namespace before anything started (observation "install bound read-only in the run's mount namespace" is `yes` in all 13 records). Its check after all runs passed.
- **Not needed.** This game needed no window manager (E001-r0031 completed with none), unlike the IC2 game. It needed no audio drivers either (E001-r0028 ran with them off, E001-r0032 with Wine's defaults). Whether it needs the host's network was not tried: N0 is the contract, and every run kept it.
- **The display.** 800x600 is the minimum. At 640x480 the game did not start its title screen and showed a dialog about the screen size (E001-r0039). It works at 800x600 with 16 or 24 bits, and at 1024x768 and 1280x1024 with 24. On a larger screen the window becomes screen-sized and fullscreen, and the 800x600 stage sits centred on black (E001-r0037, E001-r0038).

### Per-path table

| Path | launch | known screen | input | observe | terminate | reset |
| --- | --- | --- | --- | --- | --- | --- |
| Wine 9.0 (win32 prefix) + Xvfb 800x600x24 + xfwm4, audio drivers off, game in a private network namespace (control) | works (E001-r0028, E001-r0029, E001-r0030) | works (E001-r0028 to E001-r0030: title screen, identical `before` hash) | works (E001-r0028 to E001-r0030: click on Options, Options screen) | works (E001-r0028 to E001-r0030: screenshots and pixel predicates) | works (E001-r0028 to E001-r0030: Return, Quit, Exit Game, status 0) | works (E001-r0028 to E001-r0030: `reset:` line) |
| same, no window manager | works (E001-r0031) | works (E001-r0031) | works (E001-r0031: no click dropped) | works (E001-r0031) | works (E001-r0031) | works (E001-r0031) |
| same, audio drivers left to Wine | works (E001-r0032) | works (E001-r0032) | works (E001-r0032) | works (E001-r0032) | works (E001-r0032) | works (E001-r0032) |
| same, click sent right after the pointer move | works (E001-r0033) | works (E001-r0033) | fails: Options screen never appeared in 20 s (E001-r0033 `run.log`: "options screen after click: None") | works (E001-r0033) | fails: the Quit click, sent the same way, was dropped too; no notice appeared, and the game did not exit in 60 s; `wineserver -k` stopped it (E001-r0033) | works (E001-r0033) |
| same, stopped with Alt+F4 | works (E001-r0034) | works (E001-r0034) | works (E001-r0034) | works (E001-r0034) | works (E001-r0034: exit in 3.4 s, status 0) | works (E001-r0034) |
| same, stopped with `wineserver -k` | works (E001-r0035) | works (E001-r0035) | works (E001-r0035) | works (E001-r0035) | works (E001-r0035: status 0, leaves a temporary folder) | works (E001-r0035: reset removes the folder) |
| same, Xvfb 800x600x16 | works (E001-r0036) | works (E001-r0036: a different `before` hash, 16-bit colour) | works (E001-r0036) | works (E001-r0036) | works (E001-r0036) | works (E001-r0036) |
| same, Xvfb 1024x768x24 and 1280x1024x24 | works (E001-r0037, E001-r0038) | works (E001-r0037, E001-r0038: stage centred on black) | works (E001-r0037, E001-r0038) | works (E001-r0037, E001-r0038) | works (E001-r0037, E001-r0038) | works (E001-r0037, E001-r0038) |
| same, Xvfb 640x480x16 | works (E001-r0039: process and window start) | fails: a dialog about the screen size, no title screen in 45 s (E001-r0039 `known-screen-timeout.png`) | not tried: no known screen to click on | works (E001-r0039: screenshot) | works (E001-r0039: `wineserver -k`, status 1) | works (E001-r0039) |
| same, with Save as default clicked (successor set) | works (E001-r0040) | works (E001-r0040) | works (E001-r0040: Options, then Save as default; the screen shows a short "saved" line) | works (E001-r0040: `changes.log` shows `xtras/Isledft.dat` 15 to 16 bytes) | works (E001-r0040) | works (E001-r0040: the file is copied back from the install) |
| same, the game on the host's network | not tried: the contract is N0, and the driver no longer has the option | not tried: same | not tried: same | not tried: same | not tried: same | not tried: same |
| Native Windows | not tried: the owner's direction (2026-10-02) makes native Windows the V3 confirmation path, and the task forbids starting the game on the Windows desktop | not tried: same | not tried: same | not tried: same | not tried: same | not tried: same |

## Method

**Artifact.** Set `iwp-2.0-996e86c5` ([`artifacts/known.json`](../artifacts/known.json)). `setup/iwp/iwp-runtime.sh` copies the user's install into the Wine prefix's C: drive, and every run checks that copy against the set before it starts. The install was read and hashed only. The final check of the install after all 13 runs passed, with only `unins000.dat` and `unins000.exe` unlisted. E001-r0040 is recorded under the successor set `iwp-2.0-3694a782` ([`artifacts/iwp/iwp-2.0-3694a782.md`](../artifacts/iwp/iwp-2.0-3694a782.md)).

**Runtime.** `runtime/iwp/spike/cycle.py` at the commit named in each record (`code_commit`). The platform was Linux 6.18 (WSL2) with:
- Wine 9.0 (Ubuntu 9.0~repack-4build3), a 32-bit prefix (`WINEARCH=win32`, because the PE header's machine type is i386, F001);
- Xvfb from package 2:21.1.12-1ubuntu1.8;
- xfwm4 4.18.0-1build3 (`--compositor=off`);
- xdotool 3.20160805.1, ImageMagick 6.9.12-98 and Python 3.12.3.

The exact fingerprint is in every record.

**Locations and the seal.** The prefix, its baseline, the evidence bundles and any exploration output are machine-local. The profile and the cycle confine them before they change or launch anything (`setup/iwp/locations.py`). Each must be absolute, must resolve (links followed) outside every checkout and worktree, must not contain this repository, and must not overlap the install or one another. The guarantees then hold at the point of use:
- **One writer.** Every file the profile and the cycle write, every name they remove and every mode they change goes through `setup/iwp/safeio.py`.
  - Names are one plain component.
  - Directories are reached from `/` with `O_NOFOLLOW` and used through their open descriptors.
  - A file is created as a new file and given its name by `link` (the name must be new) or by `rename` (the name is replaced).
  - An existing link, a file with a second name, or a directory at the destination is refused, never written through.
  - A copy is checked against the registered sha256 of the bytes actually written.
- **The game copy.** It is a real directory inside the prefix, never a link or behind one, and holds only plain files of its own. Synchronising it detaches a hard link (the name is removed; the other name, perhaps the install's file, keeps its bytes and mode) before anything is kept, written or re-permissioned. It refuses a copy that holds a mount.
- **The prefix check** (`prefix.py check`) requires:
  - `c:` maps to `drive_c`, and nothing else is mapped;
  - no link resolves outside the prefix;
  - no file has a second name, and no device or fifo is present;
  - nothing is mounted inside the prefix;
  - the game copy is the registered set.
- **The run.** Each run binds the install read-only in its own mount namespace. It applies that prefix check before anything starts, again immediately before the game starts, and in the outer process before the namespace is created. A run is recorded `completed` only when every stage ran and both screenshots exist. Any failure, crash or interruption, and any failed clean-up stage, records `aborted: <why>` and exits nonzero.

Each of these is exercised on synthetic fixtures by `tests/test_iwp_seal.py` and `tests/test_iwp_safety.py`.

**Start state.** `S-cold-prefix-title` (sha256 `34ac62c31dda...`, in full in each record) is the prefix as `setup/iwp/iwp-runtime.sh` leaves it, and as the previous run's reset leaves it. Its hash lists every entry of the prefix with the size and sha256 of each file and the target of each link, so the game copy and the registry files are part of it. The prefix was removed and rebuilt before E001-r0028.

**The profile** ran twice before the first cycle. It printed `ready` and exited 0 both times, and the second run changed no file of the game copy. It does the following:
- builds the prefix with `wineboot -u` as the user, with winemenubuilder, Mono and Gecko disabled;
- removes `Z:`, the eight COM port links and every link that resolves outside the prefix, and makes `c:` map to `drive_c`;
- copies the registered files from the install;
- keeps the three registry files and `.update-timestamp` as a baseline outside the prefix;
- ends by running the token checks of `capabilities.json` (`tool:python`, `tool:wine`, `tool:xvfb`, `tool:xfwm4`, `tool:xdotool`, `facility:display`, `artifact:iwp-2.0-996e86c5`, `facility:iwp-prefix`).

After the profile, `dosdevices` held only `c:`, and no absolute link existed under `dosdevices` or `drive_c/users`. The same check after all 13 runs found the same, and `prefix.py check` printed `prefix ok`.

**One run, in order:**
1. Bind the install read-only and check that it is read-only; check the prefix.
2. Start Xvfb on display 77 and wait until `xdpyinfo` answers. Start xfwm4 and wait until it registers (`_NET_SUPPORTING_WM_CHECK`).
3. Snapshot the game copy, the prefix (size and sha256 of every file, target of every link) and the registry. The registry snapshot has the key names with a hash of each key's values. It drops key timestamps and `#time` lines, because Wine rewrites them on every exit.
4. Check the prefix again, then launch `unshare -n wine Islepro.exe` in the game copy.
5. Find the game process, and require that its network namespace is not the driver's and that it sees only `lo`. The run aborts otherwise.
6. Wait for a window named `Islepro`. Wait until the title screen's subtitle colour is present in its rectangle, and the screen is unchanged between two captures 0.4 s apart. Capture `before.png`.
7. Move the pointer onto Options, wait until that label's pixels change, and click. Wait for the green Return button of the Options screen, and capture `after.png`.
8. Click Return, then Quit. Wait for the unregistered-version notice (`notice.png`), then click Exit Game.
9. Wait for the process to exit, and run `wineserver -k` if it has not. Wait until no Wine process remains, then stop xfwm4 and Xvfb.
10. Snapshot again, diff, and reset. Write the bundles, the manifest and the record.

`cycle.py` encodes the screenshots itself, because two ImageMagick conversions of the same pixels gave different PNG bytes.

**Namespaces.** Everything but the record runs in a private user, mount and PID namespace (`unshare -rmpf`):
- The mount namespace holds the read-only bind of the install and a private `/tmp`. The private `/tmp` is needed because `/tmp/.X11-unix` is a read-only mount under WSLg. Without it, Xvfb could listen only on the abstract socket, which the game cannot reach from its own network namespace.
- The private PID namespace means nothing of a run outlives it.

The outer process refuses to start when a process carrying the run marker, or a `WINEPREFIX` equal to the prefix, exists. It checks again after the namespace ends. None survived in 13 runs: the observation "processes of this run still alive after terminate" is 0 in every record.

**Waits.** Every wait is a poll on a condition with a timeout. The conditions are Xvfb, xfwm4, the game process, the window, the title screen, the hover highlight, the Options screen, the exit, and the Wine processes being gone. Poll intervals are 0.05 to 0.25 s. The only fixed sleep is the 0.4 s between the two captures of the stability test. Timeouts:
- 20 s for Xvfb, xfwm4, the game process and the Options screen;
- 90 s for the window;
- 45 s for the title screen;
- 60 s for the game to exit.

**Arms.** The arms and their arguments are in [`experiments/E001-iwp-runtime-spike/README.md`](../experiments/E001-iwp-runtime-spike/README.md) (read with its amendments) and in each record's `actions.args`.

**Network.**
- N0 for the game, always, by `unshare -n`. In every record, all 13, the observation "game in its own network namespace" is `yes` and "network interfaces the game sees" is `lo`.
- N3 for bootstrap installs: none. The main session installed the packages beforehand and this task installed nothing, so there are no hosts to log.
- N1: the pinned `game-archaeologist` files for the formats were fetched with `gh api` from the GitHub API.

The `.url` shortcuts were never opened, and the Soleau Games and order buttons were never clicked.

## Observations

Raw values, from the records (`observations`) and the `changes.log` bundle of each run.

Control runs:

| Quantity | E001-r0028 | E001-r0029 | E001-r0030 |
| --- | --- | --- | --- |
| Xvfb ready (s) | 0.1 | 0.11 | 0.11 |
| xfwm4 registered (s) | 0.11 | 0.12 | 0.12 |
| install bound read-only in the run's mount namespace | yes | yes | yes |
| prefix check: problems found before anything starts, and immediately before launch | 0, 0 | 0, 0 | 0, 0 |
| game in its own network namespace; interfaces it sees | yes; `lo` | yes; `lo` | yes; `lo` |
| `Islepro` window after launch (s) | 0.43 | 0.42 | 0.53 |
| window position and size | 0,0 800x600 | 0,0 800x600 | 0,0 800x600 |
| title screen reached and stable (s after launch) | 6.58 | 6.58 | 6.69 |
| `start_state.sha256` | `34ac62c31dda...` | same | same |
| `before.png` raw RGB8 pixel sha256 | `fecd0a984e0d2f36...` | same | same |
| `before.png` file sha256 | `ae6e98d28d379bb4...` | same | same |
| `after.png` file sha256 | `426d77e724d793dd...` | same | same |
| `notice.png` file sha256 | `47afc4d33b5450f9...` | same | same |
| Options label changed under the pointer (s) | 0.07 | 0.07 | 0.07 |
| Options screen after click (s) | 0.01 | 0.01 | 0.01 |
| game exit after the last click (s) | 14.8 | 14.73 | 14.73 |
| game exit status | 0 | 0 | 0 |
| Wine processes gone after the exit (s) | 2.06 | 2.17 | 2.14 |
| game copy: added / removed / changed entries | 0/0/0 | 0/0/0 | 0/0/0 |
| prefix: added / removed / changed entries | 9/0/2 | 9/0/2 | 9/0/2 |
| registry keys: added / removed / value-changed | 0/1/6 | 0/1/6 | 0/1/6 |

The window properties at the title screen were the same in every run that reached it:
- `_NET_WM_STATE` is `_NET_WM_STATE_FULLSCREEN`, plus `_NET_WM_STATE_FOCUSED` under xfwm4;
- `_MOTIF_WM_HINTS` is `0x3, 0x26, 0x0, 0x0, 0x0`;
- the root window stays at the size Xvfb was started with (no mode change).

What a clean run changes in the prefix (E001-r0028 to E001-r0030, and every arm that exited through the game or Alt+F4):
- Added: the eight COM links in `dosdevices`, and a file `wineserver` of 11 bytes in the prefix root.
- Changed: `system.reg` and `user.reg` (size and timestamps).
- In the registry, one key is removed (`Software\Microsoft\Windows NT\CurrentVersion\NetworkCards`). Six change values: the two `Fonts` keys of `system.reg`, three display-adapter class keys, and `Software\Wine\Fonts\External Fonts` in `user.reg`.
- Nothing is added or changed in the game copy.

Reset restored all of it.

Other arms:

| Run | Arm | Status | Notable |
| --- | --- | --- | --- |
| E001-r0031 | no window manager | completed | window 0,0 800x600; every `before`, `after` and `notice` hash as in the control; exit after 16.73 s |
| E001-r0032 | audio drivers left to Wine | completed | the same hashes; 13 registry keys added (audio endpoints of the host: MMDevices render and capture entries and `Software\Wine\Drivers\winepulse.drv\devices\...`); none in the control |
| E001-r0033 | click right after the move | aborted: the click did not bring up the Options screen | `options screen after click: None`; `after.png` hash `cb722841ca3c...` differs from the control's; the Quit click, sent the same way, was dropped too (no notice), no exit in 60 s, `wineserver -k` ended it; prefix added 31 entries (below) |
| E001-r0034 | Alt+F4 | completed | exit after 3.44 s, status 0 (0.41 s in the superseded E001-r0021); nothing added but the 9 usual entries |
| E001-r0035 | `wineserver -k` | completed | status 0; prefix added 31 entries: the usual 9 and a folder `drive_c/users/<user>/Temp/TempFolder.aaa` with 22 entries (3 DLLs and 17 Xtras of the Director runtime, plus the folder and its `xtras` subfolder) |
| E001-r0036 | Xvfb 800x600x16 | completed | `before` pixel hash `371453dbcc80c389...` (file `5152df08b58b...`), different from 24-bit; all else as the control |
| E001-r0037 | Xvfb 1024x768x24 | completed | window 0,0 1024x768, fullscreen; the stage origin that lets the predicates and clicks succeed is 112,84, which is `(1024-800)/2` and `(768-600)/2`; `before` file `84cbd7fc7b03...`; 8 registry values changed |
| E001-r0038 | Xvfb 1280x1024x24 | completed | window 0,0 1280x1024; stage origin 240,212; `before` file `a76f7b3f4158...`; Options screen after 0.03 s; 8 registry values changed |
| E001-r0039 | Xvfb 640x480x16 | aborted: the title screen's subtitle never appeared within 45 s | window 0,0 640x480; `known-screen-timeout.png` shows a dialog saying the game needs a resolution above 640x480 and at least 800x600; process exit status 1 after `wineserver -k`; prefix added 31 entries (a temp folder as in E001-r0035) |
| E001-r0040 | Save as default clicked | completed | `xtras/Isledft.dat` 15 to 16 bytes (`changes.log`: "changed xtras/Isledft.dat (15,) -> (16,)"); the screen after the click shows a short saved line at its foot (`after.png` file `e7b08d2235c3...`); reset copied the file back |

Hover waits in the runs that reached the stop buttons (E001-r0028 to E001-r0032, E001-r0036 to E001-r0038, E001-r0040):
- The Options and Quit labels highlight after 0.01 to 0.1 s.
- The Return button highlights after 0.07 to 0.1 s, except right after Save as default: 0.4 s in E001-r0040, and 0.39 s in the superseded E001-r0027. There the screen is still showing its "saved" line.
- The Exit Game label shows no highlight (observation "no change within 5 s" in every run that reached it). The click that follows exits the game anyway.

The game shows a farewell screen for about 12 s before the process ends. This was seen in the exploration that preceded the recorded runs, not in the records.

Exploration before the recorded runs is not records and not evidence for this finding. Earlier scratch runs of the same script with `--explore` reached the same screens. They found the hover requirement, the Exit Game route and the 640x480 dialog, and they are why the arms above exist. Their outputs are in a local directory only.

## Inferences

- From E001-r0028 to E001-r0030 (identical hashes, an identical start-state hash over the whole prefix, 3 of 3 completed): the Wine path is repeatable for the title screen and the Options screen at this display setting. The game's first screens have no run-to-run variation that this setup can see. The only variation seen is in seconds: the title at 6.58 to 6.69 s, the window at 0.42 to 0.53 s. The same hashes as in the superseded runs, from a prefix built again, point the same way.
- From E001-r0033 against E001-r0028: the game needs a mouse-move event over a label, and a short time for the label to highlight, before a press on it counts. The measured highlight delay is 0.01 to 0.4 s: 0.1 s at most, except for the Return button right after Save as default. So the requirement is about the order of events, not a long delay. Whether the delay or the order matters was not separated.
- From E001-r0031: this game needs no window manager under Wine, so the IC2 warning (clicks dropped without one) does not carry over. xfwm4 stays in the control because the owner directed it. The no-window-manager result is one run.
- From E001-r0028 against E001-r0035: a clean exit removes what the Director runtime unpacks into the prefix's user Temp folder at launch (3 DLLs and 17 Xtras), and a forced stop leaves it. The folder is in the prefix, not in the game copy. An experiment that kills the game must expect it and reset it.
- From E001-r0034 against the superseded E001-r0021: Alt+F4 ends the game, but how long it takes varied (3.4 s and 0.4 s, one run each). A driver must wait on the exit, not on a time.
- From E001-r0037 and E001-r0038: the projector asks for fullscreen and sizes its window to the screen, and its stage is fixed at 800x600. A driver must locate the stage by the window's size, or fix the Xvfb screen at 800x600 as the control does.
- From E001-r0039: 800x600 is the lowest screen the game accepts under Wine. It checks the screen size at start and says so in a dialog.
- From E001-r0040: Save as default writes `xtras/Isledft.dat`. This is the only game file the runs changed, so the set needed a successor that declares it (`iwp-2.0-3694a782`). It is a file of the game's own settings. Its role (default options) is inferred from its name, the button and the Options screen; it is not a decoded fact.
- From E001-r0028 to E001-r0030 against E001-r0031 to E001-r0040: the audio drivers and the window manager do not change what the game shows or writes in these screens. The audio drivers change what Wine registers (E001-r0032), and nothing else visible. The network was not varied.

## Alternatives considered

- **The Wine path needs a window manager (IC2).** Excluded for this game by E001-r0031, on one run. Not excluded for other screens, other input kinds or other Wine versions.
- **The click works with no wait, and E001-r0033 failed for another reason** (the screen changed under it, or the title was not yet ready). Partly excluded. E001-r0033 waited for the stable title screen exactly as E001-r0028 did, and sent the click right after the move, the only difference between the arms. But it is one run, so a race that happened that once is not excluded. The superseded E001-r0020 and E001-r0007 had the same result, one run each.
- **Runs 2 and 3 agree with run 1 only because the reset hid state that run 1 created.** Excluded by E001-r0028 itself. It started from a prefix the profile had just built. Its diff (9/0/2 prefix entries, 0/1/6 registry keys, nothing in the game copy) is the same as the diffs of E001-r0029 and E001-r0030, which started from reset states, and its start-state hash over the whole prefix is theirs. "Cold" here means a freshly built prefix on a machine that had run Wine before.
- **The game saw the host's network after all, because the namespace check was too weak.** Excluded for these runs by the check itself. It requires the game process to be found, to be in a namespace other than the driver's, and to see only `lo`, and it aborts otherwise (`tests/test_iwp_safety.py` covers each abort). Not excluded for the child processes Wine starts, which were not inspected one by one.
- **The game or Wine wrote to the install during a run.** Excluded for these runs. The install was bound read-only in each run's namespace, and the run checked that it was read-only before anything started (observation in every record). The install's check after all runs passed.
- **Identical `before` hashes only show that the screen is stable, not that it is the "right" one.** Not excluded. The screen is the title screen by eye (F002 does not claim a rule) and by the predicate the cycle waits on.
- **The game was cut off from the network by `unshare -n`, but could still reach the host's files through Wine.** Not excluded for the host in general. Removing `Z:` and every link that leaves the prefix closes the drive-letter route. Wine's own path syntax for host files (`\\?\unix`) was not tested. The install, and only the install, is read-only inside the run whatever the path.

## What this does not establish

- Native Windows: not tried, so nothing about V3 (timing, rendering, UI claims).
- DOS *Isle Wars*: nothing; this finding is Isle Wars Pro's only (CLAUDE.md rule 19).
- Whether the game needs, or tries to use, a network: it never had one. The superseded host-network run (E001-r0006) is outside the contract and is not evidence.
- Anything beyond the title, Options and unregistered-version screens. A New Game, the board, a turn, Help, Scores, Soleau Games and the order buttons were not opened. `xtras/Islepro.dat` was not written in any arm, and its role is still unknown. What the game writes while playing is open.
- Keyboard input into the game itself: only the mouse was used inside the game; the Alt+F4 key went to the window manager.
- Dialogs: the 640x480 dialog is a Wine-drawn window; whether xdotool can address dialog controls (01 §3) was not tried.
- Audio output: no sound was captured or heard. With the drivers disabled the game ran. Whether it behaves differently with sound (timing of effects, a toggle on the Options screen) is not shown.
- Repeatability beyond one machine, one Wine build and one day; the probe arms are single runs.
- The registered version: what registration unlocks is unknown (rule 19).
- Whether the user's copy equals the vendor's own distribution (F001).
- A sandbox. The prefix is checked at the point of use, but Wine itself works on paths. A process of the same user that changed the prefix between the launch-time check and Wine's own lookups would not be seen; no such process ran. Outside the read-only install, the game's process has the user's access to the host's files through Wine's own paths, untested here.
- A driver: this finding supports the claim that the cycle is feasible, not that `cycle.py` is a driver (W5a).
- The exploration runs that preceded the records are not evidence here.

## Where the evidence is

- Run records: `runs/E001/E001-r0028.json` to `E001-r0040.json`.
- Evidence manifests: `evidence/E001/E001-r0028.manifest.json` to `E001-r0040.manifest.json`.
- The superseded records `E001-r0001` to `E001-r0027` and their manifests stay in the same folders.
- The bundles (screenshots, `changes.log`, `run.log`, `wine.log`) are kept locally, outside the repository. The main session uploads them to release `E001` after review. Each file is named `<sha256[:16]>-<name>`, as its manifest says.

## Reproduction

The machine needs:
- Wine 9.0 with its 32-bit side, Xvfb, xfwm4, xdotool, ImageMagick and util-linux;
- `IWP_DIR` set to the install, and `IWP_PREFIX` and `E001_BUNDLES` set to two locations outside every checkout and the install;
- a `setup/iwp/iwp-runtime.sh` that prints `ready`.

Then:

```text
bash setup/iwp/iwp-runtime.sh
for i in 1 2 3; do python3 runtime/iwp/spike/cycle.py || exit 1; done
python3 runtime/iwp/spike/cycle.py --arm size-1024x768x24 --size 1024x768x24
```

The arms and their arguments are listed in the experiment README (with its amendments).
