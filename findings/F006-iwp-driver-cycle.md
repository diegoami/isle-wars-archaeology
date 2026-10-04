# F006 The Isle Wars Pro driver repeats launch, known screen, one input, observation, termination and reset ten times in one command with one `before` hash, in about 15 s a repeat; a game killed in the middle ends that repeat `aborted` and the next one completes

- **Status**: proposed
- **Question**: Can a reusable driver (`runtime/iwp/driver/`, W5a) take Isle Wars Pro from a known state to a known screen, give one input, observe before and after, terminate and reset, ten times in one command with an identical `before` screenshot? Does a game killed in the middle of a cycle make that repeat `aborted`, with the next repeat starting from the baseline? How long does a kill-terminated repeat take against E002's 40 to 46 s, and what was the 30 s of that spent on? (E004, task T13, W5a; folds #40's first two items.)
- **Tests claims**: none (runtime; no game rule)
- **Experiment and runs**: E004; runs E004-r0001 to E004-r0016, all in `runs/E004/`. r0001 to r0010 are the `control` arm (one command); r0011 to r0013 are `kill-mid-cycle`, r0014 to r0016 `sigkill-mid-cycle`. Two of the sixteen aborted by design (r0012, r0015) and stay.
- **Artifact**: set `iwp-2.0-996e86c5`, variant none. No repeat clicked Save as default or played a game.
- **Max intervention**: I1 (screenshots of the display and read-only reads of `/proc` and of the game copy; no memory read, no modified file)
- **Tier reached**: V2 (the original, headless, under Wine; no native Windows run, so no V3)
- **Confidence**: the control is one command of ten repeats, and every measured quantity but time is the same in all ten. The two fault arms are one fault each, so they are probes of the recovery path, not measurements of its variance. One machine (WSL2), one Wine build, one day.

## Answer

- **Ten repeats, one command, one state.** `python3 runtime/iwp/driver/run_cycle.py` exited 0 and wrote ten `completed` records (E004-r0001 to r0010). In all ten:
  - the `before` screenshot has the same raw-pixel sha256, `fecd0a984e0d2f36...`, and the same PNG file sha256, `ae6e98d28d379bb4...`;
  - the `after` screenshot (the Options screen) has the same PNG sha256, `426d77e724d793dd...`;
  - `start_state.sha256` is the same, `b1df17775116d148...`.

  The PNG hashes of `before` and `after` are the ones F002 reports for E001-r0028 to r0030, from another driver and another prefix build. **Only times vary** across the ten: the table in [`measurements/stage-times.md`](../experiments/E004-iwp-driver/measurements/stage-times.md) gives each. The `start_state` differs from F002's (`34ac62c3...`); the cause was not investigated (the prefix has since been used by E002's runs and by `setup/iwp/iwp-runtime.sh`).
- **Time.** A repeat, from the first seal to the end of the reset, took a median of **15.06 s** (14.25 to 16.24, n=10) in the control, and 15.17 s (14.25 to 16.24, n=14) over every completed repeat of the three arms. Every repeat is kill-terminated (`wineserver -k`). That is below E002's 40 to 46 s for a kill-terminated run. The time goes to:

  | Stage | Median s (control, n=10) |
  | --- | --- |
  | Xvfb ready, xfwm4 registered | 0.11, 0.23 |
  | snapshot of the prefix before the launch | 0.67 |
  | game window after launch | 1.00 |
  | title screen reached and stable, after launch | 7.62 |
  | terminate (`wineserver -k`, the bounded wait) | 0.50 |
  | display side gone after Xvfb and xfwm4 stopped | 3.02 |
  | snapshot, diff and reset | 1.52 |

  The title screen is the one cost the driver cannot cut (the game's own start, F002, 6.6 to 6.7 s there; 7.2 to 8.1 s here). The 3.0 s wait for the display side is the next cost and was not removed: the processes end on their own about 3 s after the display stops, in all 16 records (3.00 to 3.04 s), and a driver could kill them at once (they are marked as the display side of this run).
- **What E002's 30 s was.** Not Wine. After `wineserver -k` the game and every Wine process were already gone (the observation "game side gone after terminate" is 0.00 s in all 16 records). What the spike's poll waited for, until its 30 s timeout, was six processes of the display side, which carry the run's marker because xfwm4 started them: `dbus-launch`, two `dbus-daemon`, `at-spi-bus-launcher`, `at-spi2-registryd` and `xfconfd` (diagnosis 1 in [`measurements/probes/diagnoses.md`](../experiments/E004-iwp-driver/measurements/probes/diagnoses.md); they are not Wine processes, and the spike's check excluded only `Xvfb` and `xfwm4`). The driver tells the two sides apart by a second marker, `IWP_CYCLE_SIDE`, and waits with a bound for the game side only.
- **A killed game aborts that repeat, and the next completes.** In r0012 an outside `wineserver -k` killed the game after the title screen: the record says `aborted: game-died: the game process exited before the screenshot before.png (status 0)`. In r0015 SIGKILL of the game process after the Options click: `aborted: game-died: the game process exited before the options screen appeared (status -9)`. In both, "prefix after reset equals prefix before launch" is `yes`, and the next repeat (r0013, r0016) completed with the same `start_state.sha256` and the same `before` hash as the control. The driver exits 0 for a fault arm only when the faulted repeat is `aborted: game-died` and the others completed.
- **The seal is kept.** In all 16 records: the install read-only inside the run, the prefix sealed with 0 problems before anything starts and again immediately before the launch, the registry files equal to their baseline, the game in its own network namespace seeing only `lo`, no process of the run alive after terminate, and the prefix after reset equal to the prefix before the launch ([`measurements/cycle-table.md`](../experiments/E004-iwp-driver/measurements/cycle-table.md)).
- **The stale bus.** In every record the shell's `DBUS_SESSION_BUS_ADDRESS` named a bus that does not exist (observation "set, stale: unset for the run"). The driver unsets it for its children and says so; xfwm4 registered after 0.22 to 0.24 s in all 16. E002's r0002 and r0003 (xfwm4 never registered) had this cause.
- **`TMPDIR`.** Observed while building the driver, not explained: with `TMPDIR` set to a folder that the run's private `/tmp` lacks, Wine stopped at once (`unable to create wineserver tmpdir`); with `TMPDIR=/tmp` it aborted (`free(): invalid pointer`, status -6); with it unset every launch worked. The driver passes the game no `TMPDIR` (diagnosis 3 in the probes file).

## Method

**Artifact and prefix.** Set `iwp-2.0-996e86c5`. The prefix was the one E001 and E002 used, reset by each run; `setup/iwp/iwp-runtime.sh` printed `ready` before the runs and after all of them, and `tools/register_artifact.py check` of the install against the set exited 0 after all runs, with only `unins000.dat` and `unins000.exe` unlisted ([`measurements/done-when-5.txt`](../experiments/E004-iwp-driver/measurements/done-when-5.txt)).

**The driver.** `runtime/iwp/driver/session.py` (`Session`) is built on the spike's `Cycle` (`runtime/iwp/spike/cycle.py`), whose seal, screens, step language, snapshots and reset it reuses, and adds:
- named errors (`errors.py`): `SealError`, `DisplayError`, `LaunchError`, `ScreenNotReached`, `GameDied`, `StepFailed`, `TerminateError`, `ResetError`, `RecordError`. A repeat that hits one is recorded `aborted: <kind>: <reason>`;
- a check, before anything starts, that the prefix's registry files equal their baseline, because the reset can only bring the prefix back to the baseline (diagnosis 4 in the probes file);
- a check that the game is alive before every step, every screenshot and at the end: a `completed` record needs the known screen reached (by pixels), both screenshots, and a live game;
- the side marker and the bounded wait described above (10 s for the game side after `wineserver -k`; then a second `wineserver -k` and SIGKILL of the game side; then 5 s more, then `TerminateError`);
- for the children: no `DBUS_SESSION_BUS_ADDRESS` and no `TMPDIR`; a free X display number instead of a fixed one (so as not to clash with another project's Xvfb on the same host).

The spike changed in three ways, none of behaviour: its launch is split into the seal and `start_game()`; its display number and the environment of Xvfb and the window manager are attributes the driver overrides; and the docstring of `attack_picked` no longer states game rules (R2 of the F003 research review).

`runtime/iwp/driver/runner.py` is the E004 command: one namespace for the whole command (`unshare -rmpf`; the install bound read-only once, a private `/tmp`), and for each repeat a new session with its own run id, its own Xvfb and xfwm4, and its own record. A repeat that does not end as expected stops the command with exit 1, so that a wrong state is not carried on.

**One repeat, in order.** The install is read-only; the prefix is sealed and equals its baseline; Xvfb and xfwm4 start; the prefix is snapshotted; the prefix is sealed again; the game starts in its own network namespace; the title screen is waited for by its pixels and for stability; `before.png`; the pointer goes onto Options, the label highlights, a click (`click! 320 585` in the E002 step language); the Options screen is waited for by its pixels; `after.png`; `wineserver -k`; the bounded wait; the display stops; the prefix is snapshotted, diffed and reset.

**Waits.** Every wait is a poll on a condition with a timeout (Xvfb, xfwm4, the game process, the window, the title and Options screens, stability, the Wine side and display side going away). The only fixed sleep is the 0.4 s between the two captures of the stability test, as in the spike.

**Faults.** `--fault kill-game` runs `wineserver -k` and `--fault sigkill-game` sends SIGKILL to the game process, from the command and not from a driver method, at the checkpoint `after-title` or `after-input`, in the repeat named by `--fault-repeat`.

**Tests.** `tests/test_iwp_driver.py` runs the real session code with a fake game (a `sleep` process carrying the run's marker), a scripted screen and a fake `wineserver`. `tests/mutants_iwp_driver.py` removes each guarantee in turn and shows its tests failing: the screen wait, the completion guard, kill detection, the reset after an abort, the first and the second prefix check, the bound of the wait, the wait on another run's processes, the wait on the display side, the stale bus and the baseline check. All 12 are killed.

## Observations

Per-repeat values are in [`measurements/cycle-table.md`](../experiments/E004-iwp-driver/measurements/cycle-table.md) and [`measurements/stage-times.md`](../experiments/E004-iwp-driver/measurements/stage-times.md), made by `make_tables.py` from the records. The command's own output is in `measurements/command-output/`.

| Quantity | Control (r0001 to r0010) | Fault arms (r0011 to r0016) |
| --- | --- | --- |
| records, completed / aborted | 10 / 0 | 4 / 2 |
| `before` pixels sha256 distinct values | 1 | 1 (4 completed) |
| `start_state.sha256` distinct values | 1 | 1 (all 6, aborted included) |
| session seconds, median (range) | 15.06 (14.25 to 16.24) | 15.43 (15.03 to 15.54), completed only |
| game side gone after terminate (s) | 0.00 in all | 0.00 in all |
| prefix after reset equals the one before the launch | yes in 10 | yes in 6 |

## Inferences

- The 30 s was the poll's timeout on display-side daemons. Observed: the six processes, their comm names and that they stayed through three listings at 2 s intervals while the game side was gone. Inferred: that xfwm4's missing bus caused `dbus-launch --autolaunch` (the parent of the launcher was not read); the driver does not depend on the cause, only on the side marker they inherit.
- The recovery is shown for two kinds of kill, at two points. A kill at another point (during the game's start, during terminate) is not tried; the driver's checks cover it (the game must be alive at every step), but only the two points were run on the game.

## Alternatives considered

- Cutting the cycle further by skipping the whole-prefix snapshots (about 2.2 s a repeat) or the second seal: refused. They are the seal and the reset check, and a faster cycle that skips a check is a failure (T13 hazards).
- Starting the game once and keeping it between trials (models.md, "relaunch rarely"): the E004 cycle is defined as launch from the baseline each time, so that the `before` hash shows the start is the same; a driver for later experiments can use `Session` that way, which this finding does not test.
- Leaving the 30 s poll and only lowering its timeout: it would still have waited for processes that are not Wine.

## What this does not establish

- Native Windows: not tried; nothing about V3.
- DOS *Isle Wars*: nothing (CLAUDE.md rule 19).
- Any game rule or a game played: the cycle goes only from the title screen to the Options screen.
- Why `TMPDIR` makes Wine abort, and why the display side takes 3 s to end.
- That the driver recovers from a kill at any point, or from a crash of Xvfb or xfwm4 (not tried).
- A different machine, Wine build or prefix: one machine, one day. The `start_state` here is not F002's, and the cause was not investigated.
- That `H3`'s preflight is not needed: `setup/iwp/tokens.py --tokens` is still the preflight (`TODO(H3)`).
- A sandbox: the prefix is checked at the points of use, as in F002; a process of the same user that changed it between a check and Wine's own lookups would not be seen.

## Where the evidence is

- Run records: `runs/E004/E004-r0001.json` to `E004-r0016.json`.
- Evidence manifests: `evidence/E004/E004-r0001.manifest.json` to `E004-r0016.manifest.json`.
- The bundles (screenshots, `changes.log`, `run.log`, `wine.log`) are kept locally, outside the repository; the main session uploads them to release `E004` after review. Each file is named `<sha256[:16]>-<name>`, as its manifest says.
- Tables, diagnoses and the command output: `experiments/E004-iwp-driver/measurements/`.

## Reproduction

The machine needs what F002 lists, `IWP_DIR` set to the install, and `IWP_PREFIX` and `E004_BUNDLES` set to locations outside every checkout and the install. Then, after committing:

```text
bash setup/iwp/iwp-runtime.sh
python3 runtime/iwp/driver/run_cycle.py
python3 runtime/iwp/driver/run_cycle.py --arm kill-mid-cycle --repeats 3 --fault kill-game --fault-at after-title --fault-repeat 2
python3 runtime/iwp/driver/run_cycle.py --arm sigkill-mid-cycle --repeats 3 --fault sigkill-game --fault-at after-input --fault-repeat 2
python3 experiments/E004-iwp-driver/measurements/make_tables.py
```
