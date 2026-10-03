# F002 Isle Wars Pro runs unattended under Wine 9.0, Xvfb and xfwm4 with no network: launch, a known screen, one click, observation, termination and reset all work

> **Correction (2026-10-03, review of PR #26):** the first version of this finding cited E001-r0001 to r0014. Those records stay in `runs/E001/` unchanged but are superseded: their `start_state.sha256` covered only the game copy's listing and the registry key names, so it did not identify the starting prefix; one of them (r0006) ran the game on the host's network, outside the N0 contract; and the driver then accepted machine-local locations without confining them. Every claim below cites E001-r0015 to r0027, made with the reworked driver from a rebuilt prefix. The host-network arm was not repeated and is not evidence for anything here.

- **Status**: proposed
- **Question**: Can Isle Wars Pro (the unregistered 2.0 install) be launched, brought to a known screen, given one input, observed, terminated and reset without a human, on Wine 9.0 (32-bit prefix) under Xvfb and xfwm4, with the game cut off from the network? What does it write, and what does it need from the display and from audio?
- **Tests claims**: none (runtime feasibility; it feeds W4a, W5a and the experiments)
- **Experiment and runs**: E001; runs E001-r0015 to E001-r0027, in `runs/E001/` (E001-r0001 to r0014 are superseded, see the correction)
- **Artifact**: set `iwp-2.0-996e86c5`, variant none; the one run that clicks Save as default (E001-r0027) is recorded under the successor set `iwp-2.0-3694a782`, which declares `xtras/Isledft.dat` a runtime write
- **Max intervention**: I0
- **Tier reached**: V2 (the original, headless, under Wine; no native Windows run, so no V3)
- **Confidence**: not applicable as an outcome until review. The control arm ran 3 times with 3 of 3 agreeing on every measured quantity except elapsed seconds; every other arm is one run, so a probe, not a measurement of variance. One machine (WSL2), one Wine build.

## Answer

- The Wine path works unattended for the control arm: three runs from a freshly built prefix completed with no human (E001-r0015, r0016, r0017). Each ran launch, title screen, one click, screenshots, a stop through the game's own buttons, and a reset, and exited 0. In each the driver saw the game in a network namespace of its own with only the loopback interface (observation "network interfaces the game sees" is `lo`).
- The known screen is the title screen of the unregistered build: the game name, a line marking the build as the unregistered shareware version, and a bottom bar of six menu labels. It appears 6.6 to 6.8 seconds after launch and is recognised by pixels, not by a delay. The `before` screenshot is byte-identical in all three control runs (PNG sha256 `ae6e98d28d379bb4d2a9c4793ce5aac51222be771f1c666d8a614c26758bab83`, E001-r0015 to r0017) and in every other 800x600x24 arm (r0018 to r0022, r0027).
- The three control runs started from the same prefix: their `start_state.sha256` is the same, `3f6e8c05d7a94f882c5cef84759f618f14d8a0fcfb80c0f8eec18e16be368b91`, which is the hash of the listing of every entry of the prefix (size and sha256 of each file, the registry files included, target of each link). It is the same in all 13 records.
- One click takes effect, but only after the pointer has been moved onto the label and the label has highlighted: a click sent right after the move was dropped (E001-r0020), and with the wait on the highlight the Options screen came up in 0.01 to 0.02 s in 11 of 11 runs that tried it (r0015 to r0019, r0021 to r0025, r0027).
- The game stops three ways. Its own Return, Quit and Exit Game buttons end the process with status 0 about 14.8 s after the last click (r0015 to r0017, r0019, r0023 to r0025, r0027; 16.9 s in r0018). Alt+F4 through xfwm4 ends it in 0.4 s with status 0 (r0021). `wineserver -k` ends it at once with status 0 (r0022). Only the first two let the game remove its temporary files; the kill leaves them (see Observations).
- Reset works: after every run, including the 2 that aborted, the prefix tree (every file's size and hash, every link) equalled its state before the launch (`reset:` line of each `run.log`; observation "prefix after reset equals prefix before launch" is `yes` in all 13 records).
- The game copy was not changed by any run except r0027. That run clicked Save as default on the Options screen and `xtras/Isledft.dat` grew from 15 to 16 bytes. This is the only write to the game's own files seen in E001's reworked runs; `xtras/Islepro.dat` was not written in any arm.
- The window manager was not needed for this game (r0018 completed with none), unlike the IC2 game; the audio drivers were not needed either (r0015 audio off, r0019 default). Whether the game needs the host's network was not tried: N0 is the contract, and every run kept it.
- The display: 800x600 is the minimum. At 640x480 the game refused to start its title screen and showed a dialog about the screen size (r0026). At 800x600 with 16 or 24 bits, and at 1024x768 and 1280x1024 with 24, it works; on a larger screen the window becomes screen-sized and fullscreen and the 800x600 stage sits centred on black (r0024, r0025).

### Per-path table

| Path | launch | known screen | input | observe | terminate | reset |
| --- | --- | --- | --- | --- | --- | --- |
| Wine 9.0 (win32 prefix) + Xvfb 800x600x24 + xfwm4, audio drivers off, game in a private network namespace (control) | works (E001-r0015, r0016, r0017) | works (r0015 to r0017: title screen, identical `before` hash) | works (r0015 to r0017: click on Options, Options screen) | works (r0015 to r0017: screenshots and pixel predicates) | works (r0015 to r0017: Return, Quit, Exit Game, status 0) | works (r0015 to r0017: `reset:` line) |
| same, no window manager | works (r0018) | works (r0018) | works (r0018: no click dropped) | works (r0018) | works (r0018) | works (r0018) |
| same, audio drivers left to Wine | works (r0019) | works (r0019) | works (r0019) | works (r0019) | works (r0019) | works (r0019) |
| same, click sent right after the pointer move | works (r0020) | works (r0020) | fails: Options screen never appeared in 20 s (r0020 `run.log`: "options screen after click: None") | works (r0020) | fails: the Quit click, sent the same way, was dropped too, no notice appeared and the game did not exit in 60 s; `wineserver -k` stopped it (r0020) | works (r0020) |
| same, stopped with Alt+F4 | works (r0021) | works (r0021) | works (r0021) | works (r0021) | works (r0021: exit in 0.4 s, status 0) | works (r0021) |
| same, stopped with `wineserver -k` | works (r0022) | works (r0022) | works (r0022) | works (r0022) | works (r0022: status 0, leaves a temporary folder) | works (r0022: the folder is removed by reset) |
| same, Xvfb 800x600x16 | works (r0023) | works (r0023: a different `before` hash, 16-bit colour) | works (r0023) | works (r0023) | works (r0023) | works (r0023) |
| same, Xvfb 1024x768x24 and 1280x1024x24 | works (r0024, r0025) | works (r0024, r0025: stage centred on black) | works (r0024, r0025) | works (r0024, r0025) | works (r0024, r0025) | works (r0024, r0025) |
| same, Xvfb 640x480x16 | works (r0026: process and window start) | fails: a dialog about the screen size, no title screen in 45 s (r0026 `known-screen-timeout.png`) | not tried: no known screen to click on | works (r0026: screenshot) | works (r0026: `wineserver -k`, status 1) | works (r0026) |
| same, with Save as default clicked (successor set) | works (r0027) | works (r0027) | works (r0027: Options, then Save as default; the screen shows a short "saved" line) | works (r0027: `changes.log` shows `xtras/Isledft.dat` 15 to 16 bytes) | works (r0027) | works (r0027: the file is copied back from the install) |
| same, the game on the host's network | not tried: the contract is N0, and the driver no longer has the option | not tried: same | not tried: same | not tried: same | not tried: same | not tried: same |
| Native Windows | not tried: the owner's direction (2026-10-02) makes native Windows the V3 confirmation path, and the task forbids starting the game on the Windows desktop | not tried: same | not tried: same | not tried: same | not tried: same | not tried: same |

## Method

Artifact: set `iwp-2.0-996e86c5` ([`artifacts/known.json`](../artifacts/known.json)), a copy of the user's install made into the Wine prefix's C: drive by `setup/iwp/iwp-runtime.sh` and verified with `tools/register_artifact.py check` before every run. The install was read and hashed only; the final check of the install after all 13 runs passed with only `unins000.dat` and `unins000.exe` unlisted. r0027 is recorded under the successor set `iwp-2.0-3694a782` ([`artifacts/iwp/iwp-2.0-3694a782.md`](../artifacts/iwp/iwp-2.0-3694a782.md)).

Runtime: `runtime/iwp/spike/cycle.py` at the commit named in each record (`code_commit`), on Linux 6.18 (WSL2), Wine 9.0 (Ubuntu 9.0~repack-4build3, 32-bit prefix, `WINEARCH=win32` because the PE header's machine type is i386, F001), Xvfb from package 2:21.1.12-1ubuntu1.8, xfwm4 4.18.0-1build3 (`--compositor=off`), xdotool 3.20160805.1, ImageMagick 6.9.12-98, Python 3.12.3. The exact fingerprint is in every record.

Locations. The prefix, its baseline, the evidence bundles and any exploration output are machine-local. The profile and the cycle confine them before they change or launch anything (`setup/iwp/locations.py`): each must be absolute, resolve (links followed) outside every checkout and worktree, not contain this repository, and not overlap the install or one another. The game copy must be a real directory inside the prefix, never a link or behind one, and the sync checks every source file's hash before it changes the copy, removes links inside the copy without following them, and never writes to the install. The reworked driver's tests exercise each of these on synthetic fixtures (`tests/test_iwp_safety.py`).

Start state `S-cold-prefix-title` (sha256 `3f6e8c05d7a9...`, in full in each record): the prefix as `setup/iwp/iwp-runtime.sh` leaves it, and as the previous run's reset leaves it. Its hash lists every entry of the prefix with the size and sha256 of each file and the target of each link, so the game copy and the registry files are part of it. The profile ran twice before the first cycle and printed `ready` and exited 0 both times; the second changed no file of the game copy. It builds the prefix with `wineboot -u` as the user (with winemenubuilder, Mono and Gecko disabled), removes `Z:`, the eight COM port links and every link that resolves outside the prefix, makes `c:` map to `drive_c`, copies the registered files from the install, keeps the three registry files and `.update-timestamp` as a baseline outside the prefix, and ends by running the token checks of `capabilities.json` (`tool:python`, `tool:wine`, `tool:xvfb`, `tool:xfwm4`, `tool:xdotool`, `facility:display`, `artifact:iwp-2.0-996e86c5`, `facility:iwp-prefix`). After the profile, `dosdevices` held only `c:` and no absolute link existed under `dosdevices` or `drive_c/users`; the same check after all 13 runs found the same.

One run, in order: check the game copy against the set; start Xvfb on display 77 and wait until `xdpyinfo` answers; start xfwm4 and wait until it registers (`_NET_SUPPORTING_WM_CHECK`); snapshot the game copy, the prefix (size and sha256 of every file, target of every link) and the registry (key names with a hash of each key's values; key timestamps and `#time` lines dropped, because Wine rewrites them on every exit); launch `unshare -n wine Islepro.exe` in the game copy; find the game process and require that its network namespace is not the driver's and that it sees only `lo` (the run aborts otherwise); wait for a window named `Islepro`; wait until the title screen's subtitle colour is present in its rectangle and the screen is unchanged between two captures 0.4 s apart; capture `before.png`; move the pointer onto Options, wait until that label's pixels change, click; wait for the green Return button of the Options screen; capture `after.png`; click Return, Quit, wait for the unregistered-version notice (`notice.png`), click Exit Game; wait for the process to exit; `wineserver -k` if it has not; wait until no Wine process remains; stop xfwm4 and Xvfb; snapshot again; diff; reset; write the record and the manifest. The screenshots are encoded by `cycle.py` itself, because two ImageMagick conversions of the same pixels gave different PNG bytes.

Everything but the record runs in a private user, mount and PID namespace (`unshare -rmpf`). The mount namespace is needed because `/tmp/.X11-unix` is a read-only mount under WSLg: Xvfb could only listen on the abstract socket, which the game cannot reach from its own network namespace. A private PID namespace means nothing of a run outlives it. The outer process refuses to start when a process carrying the run marker or a `WINEPREFIX` equal to the prefix exists, and checks again after the namespace ends (none survived in 13 runs: observation "processes of this run still alive after terminate" is 0 in every record).

Waits: every wait is a poll on a condition with a timeout (Xvfb, xfwm4, the game process, window, title screen, hover highlight, Options screen, exit, Wine processes gone). Poll intervals are 0.05 to 0.25 s. There is no fixed sleep except the 0.4 s between the two captures of the stability test. Timeouts: 20 s for Xvfb, xfwm4 and the game process, 90 s for the window, 45 s for the title screen, 20 s for the Options screen, 60 s for the game to exit.

Arms and their arguments are in [`experiments/E001-iwp-runtime-spike/README.md`](../experiments/E001-iwp-runtime-spike/README.md) (read with its Amendment 1) and in each record's `actions.args`.

Network: N0 for the game, always, by `unshare -n` (every run; observation "game in its own network namespace" is `yes` and "network interfaces the game sees" is `lo` in each record that got that far, all 13). N3 for bootstrap installs: none; the packages were installed beforehand by the main session and this task installed nothing, so there are no hosts to log. The pinned `game-archaeologist` files for the formats were fetched with `gh api` from the GitHub API (N1). The `.url` shortcuts were never opened and the Soleau Games and order buttons were never clicked.

## Observations

Raw values, from the records (`observations`) and the `changes.log` bundle of each run.

Control runs:

| Quantity | r0015 | r0016 | r0017 |
| --- | --- | --- | --- |
| Xvfb ready (s) | 0.11 | 0.11 | 0.1 |
| xfwm4 registered (s) | 0.12 | 0.12 | 0.12 |
| game in its own network namespace; interfaces it sees | yes; `lo` | yes; `lo` | yes; `lo` |
| `Islepro` window after launch (s) | 0.54 | 0.43 | 0.53 |
| window position and size | 0,0 800x600 | 0,0 800x600 | 0,0 800x600 |
| title screen reached and stable (s after launch) | 6.72 | 6.6 | 6.8 |
| `start_state.sha256` | `3f6e8c05d7a9...` | same | same |
| `before.png` raw RGB8 pixel sha256 | `fecd0a984e0d2f36...` | same | same |
| `before.png` file sha256 | `ae6e98d28d379bb4...` | same | same |
| `after.png` file sha256 | `426d77e724d793dd...` | same | same |
| `notice.png` file sha256 | `47afc4d33b5450f9...` | same | same |
| Options label changed under the pointer (s) | 0.07 | 0.07 | 0.07 |
| Options screen after click (s) | 0.01 | 0.01 | 0.01 |
| game exit after the last click (s) | 14.8 | 14.77 | 14.79 |
| game exit status | 0 | 0 | 0 |
| Wine processes gone after the exit (s) | 2.11 | 2.17 | 2.06 |
| game copy: added / removed / changed entries | 0/0/0 | 0/0/0 | 0/0/0 |
| prefix: added / removed / changed entries | 9/0/2 | 9/0/2 | 9/0/2 |
| registry keys: added / removed / value-changed | 0/1/6 | 0/1/6 | 0/1/6 |

The window properties at the title screen, in every run that reached it: `_NET_WM_STATE` is `_NET_WM_STATE_FULLSCREEN` (plus `_NET_WM_STATE_FOCUSED` under xfwm4), `_MOTIF_WM_HINTS` is `0x3, 0x26, 0x0, 0x0, 0x0`, and the root window stays at the size Xvfb was started with (no mode change).

What a clean run changes in the prefix (r0015 to r0017, and every arm that exited through the game or Alt+F4): added, the eight COM links in `dosdevices` and a file `wineserver` of 11 bytes in the prefix root; changed, `system.reg` and `user.reg` (size and timestamps). In the registry, one key is removed (`Software\Microsoft\Windows NT\CurrentVersion\NetworkCards`), six change values (the two `Fonts` keys of `system.reg`, three display-adapter class keys, and `Software\Wine\Fonts\External Fonts` in `user.reg`). Nothing is added or changed in the game copy. Reset restored all of it.

Other arms:

| Run | Arm | Status | Notable |
| --- | --- | --- | --- |
| r0018 | no window manager | completed | window 0,0 800x600; every `before`, `after` and `notice` hash as in the control; exit after 16.87 s |
| r0019 | audio drivers left to Wine | completed | the same hashes; 13 registry keys added (audio endpoints of the host: MMDevices render and capture entries and `Software\Wine\Drivers\winepulse.drv\devices\...`); none in the control |
| r0020 | click right after the move | aborted: the click did not bring up the Options screen | `options screen after click: None`; `after.png` hash `cb722841ca3c...` differs from the control's; the Quit click, sent the same way, was dropped too (no notice), no exit in 60 s, `wineserver -k` ended it; prefix added 31 entries (below) |
| r0021 | Alt+F4 | completed | exit after 0.41 s, status 0; nothing added but the 9 usual entries |
| r0022 | `wineserver -k` | completed | status 0; prefix added 31 entries: the usual 9 and a folder `drive_c/users/<user>/Temp/TempFolder.aaa` with 22 entries (3 DLLs and 17 Xtras of the Director runtime, plus the folder and its `xtras` subfolder) |
| r0023 | Xvfb 800x600x16 | completed | `before` pixel hash `371453dbcc80c389...` (file `5152df08b58b1c30...`), different from 24-bit; all else as the control |
| r0024 | Xvfb 1024x768x24 | completed | window 0,0 1024x768, fullscreen; the stage origin that lets the predicates and clicks succeed is 112,84, which is `(1024-800)/2` and `(768-600)/2`; `before` file `84cbd7fc7b03...`; 8 registry values changed |
| r0025 | Xvfb 1280x1024x24 | completed | window 0,0 1280x1024; stage origin 240,212; `before` file `a76f7b3f4158...`; 8 registry values changed |
| r0026 | Xvfb 640x480x16 | aborted: the title screen's subtitle never appeared within 45 s | window 0,0 640x480; `known-screen-timeout.png` shows a dialog saying the game needs a resolution above 640x480 and at least 800x600; process exit status 1 after `wineserver -k`; prefix added 31 entries (a temp folder as in r0022) |
| r0027 | Save as default clicked | completed | `xtras/Isledft.dat` 15 to 16 bytes (`changes.log`: "changed xtras/Isledft.dat (15,) -> (16,)"); the screen after the click shows a short saved line at its foot (`after.png` file `e7b08d2235c3...`); reset copied the file back |

Hover wait values for the three buttons of the stop sequence are 0.01 to 0.09 s (Options, Return, Quit) in every run that reached them; the Exit Game label shows no highlight (observation "no change within 5 s" in every run that reached it), and the click that follows exits the game anyway. The game shows a farewell screen for about 12 s before the process ends (seen in the exploration that preceded the recorded runs; not in the records).

Exploration before the recorded runs (not records, not evidence of this finding): the same screens were reached in earlier scratch runs of the same script with `--explore`; those runs found the hover requirement, the Exit Game route and the 640x480 dialog, and are the reason the arms above exist. Their outputs are in a local directory only.

## Inferences

- From r0015 to r0017 (identical hashes, identical start-state hash over the whole prefix, 3 of 3 completed): the Wine path is repeatable for the title screen and the Options screen at this display setting; the game's first screens have no run-to-run variation that this setup can see. The variation seen is in seconds only (title 6.6 to 6.8 s, window 0.43 to 0.54 s).
- From r0020 against r0015: the game needs a mouse-move event over a label, and a short time for the label to highlight, before a press on it counts. The measured highlight delay is 0.01 to 0.09 s, so the requirement is about the order of events, not a long delay. Whether the delay or the order matters was not separated.
- From r0018: this game needs no window manager under Wine, so the IC2 warning (clicks dropped without one) does not carry over. xfwm4 stays in the control because the owner directed it; the no-window-manager result is one run.
- From r0015 against r0022: a clean exit removes what the Director runtime unpacks into the prefix's user Temp folder at launch (3 DLLs and 17 Xtras), and a forced stop leaves it. The folder is in the prefix, not in the game copy. An experiment that kills the game must expect it and reset it.
- From r0024 and r0025: the projector asks for fullscreen and sizes its window to the screen, and its stage is fixed at 800x600. A driver must locate the stage by the window's size, or fix the Xvfb screen at 800x600 as the control does.
- From r0026: 800x600 is the lowest screen the game accepts under Wine; it checks the screen size at start and says so in a dialog.
- From r0027: Save as default writes `xtras/Isledft.dat`. This is the only game file the reworked runs changed, so the set needed a successor that declares it (`iwp-2.0-3694a782`). It is a file of the game's own settings; its role (default options) is an inference from its name, the button, and the Options screen, not a decoded fact.
- From r0015 to r0017 against r0018 to r0027: the audio drivers and the window manager do not change what the game shows or writes in these screens; the audio drivers change what Wine registers (r0019) and nothing else visible. The network was not varied.

## Alternatives considered

- The Wine path needs a window manager (IC2): excluded for this game by r0018, on one run. Not excluded for other screens, other input kinds or other Wine versions.
- The click works with no wait, and r0020 failed for another reason (the screen changed under it, or the title was not yet ready): partly excluded; r0020 waited for the stable title screen exactly as r0015 did and sent the click right after the move, the only difference between the arms, but it is one run, so a race that happened that once is not excluded. The superseded set has the same result in one run (r0007).
- Runs 2 and 3 agree with run 1 only because the reset hid state that run 1 created: excluded by r0015 itself. It started from a prefix the profile had just built, and its diff (9/0/2 prefix entries, 0/1/6 registry keys, nothing in the game copy) is the same as the diffs of r0016 and r0017, which started from reset states, and its start-state hash (over the whole prefix) is theirs. "Cold" here means a freshly built prefix on a machine that had run Wine before.
- The game saw the host's network after all because the namespace check was too weak: excluded for these runs by the check itself, which requires the game process to be found, to be in a namespace other than the driver's, and to see only `lo`, and aborts otherwise (tests in `tests/test_iwp_safety.py` cover each abort); not excluded for the child processes Wine starts, which were not inspected one by one.
- Identical `before` hashes only show the screen is stable, not that it is the "right" one: not excluded; the screen is the title screen by eye (F002 does not claim a rule), and by the predicate the cycle waits on.
- The game was cut off from the network by `unshare -n`, but could still reach the host's files through Wine: not excluded. `Z:` and every link that leaves the prefix were removed, which closes the drive-letter route; Wine's own path syntax for host files (`\\?\unix`) was not tested.

## What this does not establish

- Native Windows: not tried, so nothing about V3 (timing, rendering, UI claims).
- DOS *Isle Wars*: nothing; this finding is Isle Wars Pro's only (CLAUDE.md rule 19).
- Whether the game needs, or tries to use, a network: it never had one. The superseded host-network run (r0006) is outside the contract and is not evidence.
- Anything beyond the title, Options and unregistered-version screens: a New Game, the board, a turn, Help, Scores, Soleau Games and the order buttons were not opened. `xtras/Islepro.dat` was not written in any arm and its role is still unknown. What the game writes while playing is open.
- Keyboard input into the game itself: only the mouse was used inside the game; the Alt+F4 key went to the window manager.
- Dialogs: the 640x480 dialog is a Wine-drawn window; whether dialog controls can be addressed by xdotool (01 §3) was not tried.
- Audio output: no sound was captured or heard. With the drivers disabled the game ran; whether it behaves differently with sound (timing of effects, a toggle on the Options screen) is not shown.
- Repeatability beyond one machine, one Wine build and one day; the probe arms are single runs.
- The registered version: what registration unlocks is unknown (rule 19).
- Whether the user's copy equals the vendor's own distribution (F001).
- A driver: this finding supports the claim that the cycle is feasible, not that `cycle.py` is a driver (W5a).
- The exploration runs that preceded the records are not evidence here.

## Where the evidence is

Run records `runs/E001/E001-r0015.json` to `E001-r0027.json`; evidence manifests `evidence/E001/E001-r0015.manifest.json` to `E001-r0027.manifest.json`. The superseded records `E001-r0001` to `E001-r0014` and their manifests stay in the same folders. The bundles (screenshots, `changes.log`, `run.log`, `wine.log`) are kept locally outside the repository and are uploaded by the main session to release `E001` after review; each file is named `<sha256[:16]>-<name>` as its manifest says.

## Reproduction

On a machine whose `setup/iwp/iwp-runtime.sh` prints `ready` (it needs Wine 9.0 with its 32-bit side, Xvfb, xfwm4, xdotool, ImageMagick and util-linux, and `IWP_PREFIX` and `IWP_DIR` set to a prefix location outside every checkout and the install, and `E001_BUNDLES` to a third such location):

```text
bash setup/iwp/iwp-runtime.sh
for i in 1 2 3; do python3 runtime/iwp/spike/cycle.py || exit 1; done
python3 runtime/iwp/spike/cycle.py --arm size-1024x768x24 --size 1024x768x24
```

The arms and their arguments are listed in the experiment README (with its Amendment 1).
