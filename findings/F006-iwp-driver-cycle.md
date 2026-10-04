# F006 The Isle Wars Pro driver repeats launch, known screen, one input, observation, termination and reset ten times in one command with one `before` hash, in 15 to 16 s a repeat; a game killed in the middle ends that repeat `aborted`, the reset still restores the prefix, and the next repeat completes

- **Status**: proposed
- **Question**: Can a reusable driver (`runtime/iwp/driver/`, W5a) take Isle Wars Pro from a known state to a known screen, give one input, observe before and after, terminate and reset, ten times in one command with an identical `before` screenshot? Does a game killed in the middle of a cycle make that repeat `aborted`, with the next repeat starting from the baseline? How long does a kill-terminated repeat take against E002's 40 to 46 s? (E004, task T13, W5a; folds #40's first two items.)
- **Tests claims**: none (runtime; no game rule)
- **Experiment and runs**: E004; runs E004-r0001 to E004-r0045, all in `runs/E004/`, in three batches, each one or more commands at one commit:
  - **B3, E004-r0030 to r0045, at `a464f266d8ae`: the driver of this PR, and the batch this finding's answers cite.** r0030 to r0039 are the `control` arm (one command of ten repeats); r0040 to r0042 `kill-mid-cycle`; r0043 to r0045 `sigkill-mid-cycle`.
  - B2, E004-r0017 to r0029, at `38e58720e091`: the main session's re-run of round 0 (control r0017 to r0026, `sigkill-mid-cycle` r0027 to r0029).
  - B1, E004-r0001 to r0016, at `c6588a95fc48`: round 0's first runs (control r0001 to r0010, `kill-mid-cycle` r0011 to r0013, `sigkill-mid-cycle` r0014 to r0016).

  B1 and B2 ran a driver that round 0's review found able to accept a failed reset after an abort and to record `completed` without checking an input (PR #54, R2 and R4); their records stay, and are cited here only as earlier measurements of the same cycle. Four repeats aborted by design (r0012, r0015, r0028 in B1 and B2; r0041, r0044 in B3) and stay.
- **Artifact**: set `iwp-2.0-996e86c5`, variant none. No repeat clicked Save as default or played a game.
- **Max intervention**: I1 (screenshots of the display and read-only reads of `/proc` and of the game copy; no memory read, no modified file)
- **Tier reached**: V2 (the original, headless, under Wine; no native Windows run, so no V3)
- **Confidence**: the control is one command of ten repeats in each batch, and every measured quantity but time is the same in all thirty control repeats. The fault arms are one fault each per command, so they are probes of the recovery path, not measurements of its variance. One machine (WSL2), one Wine build, one day.

## Answer

- **Ten repeats, one command, one state.** In B3, `python3 runtime/iwp/driver/run_cycle.py` exited 0 and wrote ten `completed` records (E004-r0030 to r0039; [`command-output/rework1-a464f266d8ae-control.out.txt`](../experiments/E004-iwp-driver/measurements/command-output/rework1-a464f266d8ae-control.out.txt)). In all ten:
  - the `before` screenshot has the same raw-pixel sha256, `fecd0a984e0d2f36...`, and the same PNG file sha256, `ae6e98d28d379bb4...`;
  - the `after` screenshot (the Options screen) has the same PNG sha256, `426d77e724d793dd...`;
  - `start_state.sha256` is the same, `b1df17775116d148...`;
  - one input step succeeded, `before.png` was taken before it and `after.png` after it, and the clean-up observation "every stage succeeded and the prefix was reset" is `yes`.

  **Only times vary** across the ten ([`tables/E004-r0030-r0045-stage-times.md`](../experiments/E004-iwp-driver/measurements/tables/E004-r0030-r0045-stage-times.md)). The same four hashes are those of every completed repeat of B1 and B2. The PNG hashes of `before` and `after` are the ones F002 reports for E001-r0028 to r0030, from another driver and another prefix build. The `start_state` differs from F002's (`34ac62c3...`); the cause was not investigated (the prefix has since been used by E002's runs and by `setup/iwp/iwp-runtime.sh`).
- **Time.** A repeat, from the first seal to the end of the reset, took a median of **16.15 s** (15.16 to 21.34, n=10) in B3's control. Every repeat is kill-terminated (`wineserver -k`). That is below E002's 40 to 46 s for a kill-terminated run. B1's control took 15.06 s (14.25 to 16.24) and B2's 15.10 s (14.68 to 15.53). The time goes to (B3 control, medians):

  | Stage | Median s |
  | --- | --- |
  | Xvfb ready, xfwm4 registered | 0.11, 0.23 |
  | snapshot of the prefix before the launch | 0.82 |
  | game window after launch | 1.12 |
  | title screen reached and stable, after launch | 7.88 |
  | terminate (`wineserver -k`, the bounded wait) | 0.76 |
  | display side gone after Xvfb and xfwm4 stopped | 3.02 |
  | snapshot, diff and reset | 1.84 |

  The title screen is the largest measured stage (7.1 to 9.6 s over the completed repeats of B1 to B3; F002 had 6.6 to 6.7 s). These records measure elapsed time; they do not show whether any stage could be shorter. The 3.0 s for the display side to end is the next largest; the driver waits for it with a bound and does not kill those processes at once, which a later driver could try. B3's first repeat (21.34 s) spent 4.38 s on the snapshot before the launch, against 0.66 to 1.35 s in the others. Why B3 is about 1 s slower than B1 and B2 was not investigated: B3 ran with other projects' processes on the same machine (a DOSBox-X run and another Wine server were listed by `ps` before it; that listing was not recorded), and its code differs from B2's.
- **The game side is gone at once after `wineserver -k`; the display side ends about 3 s after the display stops.** In all 45 records the observation "game side gone after terminate" is 0.00 or 0.01 s, and in every record that reached it "display side gone after the display was stopped" is 3.00 to 3.05 s. The driver tells the two sides apart by a second marker, `IWP_CYCLE_SIDE`, inherited from what started each process, and waits with a bound for the game side only (#40's first item).
- **A killed game aborts that repeat, the reset restores the prefix, and the next completes.** In B3, r0041 (an outside `wineserver -k` after the title screen) is `aborted: game-died: the game process exited before the screenshot before.png (status 0)`, and r0044 (SIGKILL of the game process after the Options click) is `aborted: game-died: the game process exited before the options screen appeared (status -9)`. In both, "prefix after reset equals prefix before launch" is `yes` and the clean-up observation is `yes`; the next repeat (r0042, r0045) completed with the same `start_state.sha256` and the same `before` hash as the control, and each command exited 0. The command exits 0 for a fault arm only when the faulted repeat is `aborted: game-died`, its clean-up succeeded, and every other repeat completed.
- **The seal is kept.** In all 16 records of B3, as in B1 and B2: the install read-only inside the run, the prefix sealed with 0 problems before anything starts and again immediately before the launch, the registry files equal to their baseline, the game in its own network namespace seeing only `lo`, no process of the run alive after terminate, and the prefix after reset equal to the prefix before the launch ([`tables/E004-r0030-r0045-cycle-table.md`](../experiments/E004-iwp-driver/measurements/tables/E004-r0030-r0045-cycle-table.md)).
- **The stale bus (#40's second item).** In every record the driver's own environment had a `DBUS_SESSION_BUS_ADDRESS` naming a bus that does not exist (observation "set, stale: unset for the run"). The driver unsets it for its children and says so in the log and the record, and xfwm4 registered within 0.22 to 0.49 s in all 45 records. That a stale bus is what kept E002's xfwm4 from registering (r0002, r0003) is a hypothesis, below.

## Method

**Artifact and prefix.** Set `iwp-2.0-996e86c5`. The prefix was the one E001 and E002 used, reset by each run. After B3, `setup/iwp/iwp-runtime.sh` printed `ready` and `tools/register_artifact.py check` of the install against the set exited 0 with only `unins000.dat` and `unins000.exe` unlisted ([`measurements/done-when-5-rework1.txt`](../experiments/E004-iwp-driver/measurements/done-when-5-rework1.txt); after B1: `done-when-5.txt`).

**The driver.** `runtime/iwp/driver/session.py` (`Session`) is built on the spike's `Cycle` (`runtime/iwp/spike/cycle.py`), whose seal, screens, step language, snapshots and reset it reuses, and adds:
- named errors (`errors.py`): `SealError`, `DisplayError`, `LaunchError`, `ScreenNotReached`, `GameDied`, `StepFailed`, `TerminateError`, `ResetError`, `RecordError`. A repeat that hits one is recorded `aborted: <kind>: <reason>`, with the first reason in the status and every later fault as an observation;
- a check, before anything starts, that the prefix's registry files equal their baseline, because the reset can only bring the prefix back to the baseline (diagnosis 4 in the probes file);
- `completed` only when the known screens the body expects were reached (by pixels), at least one input step succeeded, `before.png` was taken before the first input and `after.png` after the last, and the game was alive at the end; and then only when terminate, stopping the display and the reset all succeeded and the reset was shown to restore the prefix;
- `recovered`, true only when every clean-up stage succeeded: the command starts the next repeat only then, whatever the status of the last one;
- the side marker and the bounded wait described above (10 s for the game side after `wineserver -k`; then a second `wineserver -k` and SIGKILL of the game side; then 5 s more, then `TerminateError`);
- a bound on every helper command (60 s, then SIGKILL and at most 5 s to reap it), on `wineserver -k` (15 s), on the reaps of Xvfb and xfwm4, and on the whole command (300 s a repeat);
- a token per command, `IWP_CYCLE_INVOCATION`, which every process of the command inherits: what survives the command's namespace is killed only if it carries that token, checked again through a pidfd before the signal, so another E004 command's processes are never signalled;
- for the children: no `DBUS_SESSION_BUS_ADDRESS` and no `TMPDIR`; a free X display number instead of a fixed one (so as not to clash with another project's Xvfb on the same host).

The spike changed in four ways: its launch is split into the seal and `start_game()`; its display number and the environment of Xvfb and the window manager are attributes the driver overrides; its `run()` helper is bounded (above), which also bounds the spike's own runs; its `reset()` returns whether the prefix was restored; and the docstring of `attack_picked` no longer states game rules (R2 of the F003 research review).

`runtime/iwp/driver/runner.py` is the E004 command: one namespace for the whole command (`unshare -rmpf`; the install bound read-only once, a private `/tmp`), and for each repeat a new session with its own run id, its own Xvfb and xfwm4, and its own record. A repeat that does not end as expected stops the command with exit 1, so that a wrong state is not carried on.

**One repeat, in order.** The install is read-only; the prefix is sealed and equals its baseline; Xvfb and xfwm4 start; the prefix is snapshotted; the prefix is sealed again; the game starts in its own network namespace; the title screen is waited for by its pixels and for stability; `before.png`; the pointer goes onto Options, the label highlights, a click (`click! 320 585` in the E002 step language); the Options screen is waited for by its pixels; `after.png`; `wineserver -k`; the bounded wait; the display stops; the prefix is snapshotted, diffed and reset, and the reset is checked.

**Waits.** Every wait is a poll on a condition with a timeout (Xvfb, xfwm4, the game process, the window, the title and Options screens, stability, the Wine side and display side going away), and every helper command has a bound. The only fixed sleep is the 0.4 s between the two captures of the stability test, as in the spike.

**Faults.** `--fault kill-game` runs `wineserver -k` and `--fault sigkill-game` sends SIGKILL to the game process, from the command and not from a driver method, at the checkpoint `after-title` or `after-input`, in the repeat named by `--fault-repeat`.

**Tests.** `tests/test_iwp_driver.py` runs the real session code with a fake game (a `sleep` process carrying the run's marker), a scripted screen, a fake `wineserver` and a recorded `run_step`. `tests/mutants_iwp_driver.py` removes each guarantee in turn and shows its tests failing; all 26 are killed: the screen wait, the completion guard, kill detection, the reset after an abort, the first and the second prefix check, the bound of the wait, the wait on another run's processes, the wait on the display side, the stale bus, the baseline check, and, from round 0's review, the command's own token in the outer clean-up and the pidfd re-check (R1), the recovery gate and the reset check (R2), the bounds on helpers, reaps, `wineserver -k` and the command (R3), and the input between the two screenshots (R4).

## Observations

Per-repeat values are in the tables of each batch, made once by `make_tables.py` from the records: B3 in `measurements/tables/E004-r0030-r0045-*.md`, B2 in `measurements/tables/E004-r0017-r0029-*.md`, B1 in `measurements/cycle-table.md` and `measurements/stage-times.md`. The commands' own output is in `measurements/command-output/`.

| Quantity | B3 control (r0030 to r0039) | B3 fault arms (r0040 to r0045) | B1 and B2 control (r0001 to r0010, r0017 to r0026) |
| --- | --- | --- | --- |
| records, completed / aborted | 10 / 0 | 4 / 2 | 20 / 0 |
| `before` pixels sha256 distinct values | 1 | 1 (4 completed) | 1 |
| `start_state.sha256` distinct values | 1 | 1 (all 6, aborted included) | 1 |
| session seconds, median (range) | 16.15 (15.16 to 21.34) | 17.69 (16.01 to 19.58), completed only | 15.06 (14.25 to 16.24) and 15.10 (14.68 to 15.53) |
| game side gone after terminate (s) | 0.00 to 0.01 | 0.00 | 0.00 |
| prefix after reset equals the one before the launch | yes in 10 | yes in 6 | yes in 20 |
| clean-up: every stage succeeded | yes in 10 | yes in 6 | not recorded (older driver) |

## Hypotheses and observations not backed by run records

These come from exploratory diagnoses made while the driver was built ([`measurements/probes/diagnoses.md`](../experiments/E004-iwp-driver/measurements/probes/diagnoses.md)). Each was seen once or twice, without a run record or a downloadable raw output, so none is a result of this finding, and the driver depends on none of them.

- **What E002's 30 s after `wineserver -k` was.** Hypothesis: the spike's poll ran to its 30 s timeout on processes of the display side, not on Wine. Seen once (diagnosis 1): right after `wineserver -k`, the processes carrying the run's marker were six non-Wine processes (`dbus-launch`, two `dbus-daemon`, `at-spi-bus-launcher`, `at-spi2-registryd`, `xfconfd`), the same in three listings 2 s apart. What started them was not read: that xfwm4 did (through `dbus-launch --autolaunch`, for want of a bus) is a guess. E004 measures something else: how long this driver waits for its own game side (0.00 s) and display side (about 3 s after the display stops). Neither shows what E002's poll waited for. A controlled test would run the spike's terminate with the processes listed, their parents read, in records.
- **The stale bus and E002's r0002 and r0003.** Hypothesis: the stale `DBUS_SESSION_BUS_ADDRESS` kept xfwm4 from registering there. Seen in exploration (diagnosis 2): with the stale address set, the spike's xfwm4 did not register within 20 s; with it unset, it registered. No E004 arm sets the stale address for the children, so E004 shows only that xfwm4 registers with it unset.
- **`TMPDIR`.** Seen while building the driver, without records: with `TMPDIR` set to a folder the run's private `/tmp` lacks, Wine stopped at once (`unable to create wineserver tmpdir`); with `TMPDIR=/tmp` it aborted once (`free(): invalid pointer`, status -6); with it unset every launch worked (diagnosis 3). The driver passes the game no `TMPDIR`. Neither failing condition was replicated, and the cause is not known.

## Inferences

- The recovery is shown for two kinds of kill, at two points, once each per batch. A kill at another point (during the game's start, during terminate) is not tried on the game; the driver's checks cover it (the game must be alive at every step, and the clean-up must succeed), and the unit tests visit it with a fake game.

## Alternatives considered

- Cutting the cycle further by skipping the whole-prefix snapshots (about 2.7 s a repeat in B3) or the second seal: refused. They are the seal and the reset check, and a faster cycle that skips a check is a failure (T13 hazards).
- Starting the game once and keeping it between trials (models.md, "relaunch rarely"): the E004 cycle is defined as launch from the baseline each time, so that the `before` hash shows the start is the same; a driver for later experiments can use `Session` that way, which this finding does not test.
- Leaving the 30 s poll and only lowering its timeout: it would still have counted processes that are not the game side.

## What this does not establish

- Native Windows: not tried; nothing about V3.
- DOS *Isle Wars*: nothing (CLAUDE.md rule 19).
- Any game rule or a game played: the cycle goes only from the title screen to the Options screen.
- What E002's 30 s wait was, what started the display-side daemons, why they take about 3 s to end, why a stale bus or a `TMPDIR` breaks a launch: hypotheses or unexplained observations, above.
- That any stage is as short as it can be: the records measure elapsed time.
- That the driver recovers from a kill at any point, or from a crash of Xvfb or xfwm4 (not tried on the game).
- A different machine, Wine build or prefix: one machine, one day. The `start_state` here is not F002's, and the cause was not investigated.
- Why B3's repeats are about 1 s slower than B1's and B2's.
- That `H3`'s preflight is not needed: `setup/iwp/tokens.py --tokens` is still the preflight (`TODO(H3)`).
- A sandbox: the prefix is checked at the points of use, as in F002; a process of the same user that changed it between a check and Wine's own lookups would not be seen.

## Where the evidence is

- Run records: `runs/E004/E004-r0001.json` to `E004-r0045.json` (B3: r0030 to r0045).
- Evidence manifests: `evidence/E004/E004-r0001.manifest.json` to `E004-r0045.manifest.json`.
- The bundles (screenshots, `changes.log`, `run.log`, `wine.log`) are kept locally, outside the repository; the main session uploads them to release `E004` after review. Each file is named `<sha256[:16]>-<name>`, as its manifest says.
- Tables, diagnoses and the command output: `experiments/E004-iwp-driver/measurements/`.

## Reproduction

The machine needs what F002 lists, `IWP_DIR` set to the install, and `IWP_PREFIX` and `E004_BUNDLES` set to locations outside every checkout and the install. Then, after committing, from a checkout that is not under `/tmp` (the run's private `/tmp` hides it):

```text
bash setup/iwp/iwp-runtime.sh
python3 runtime/iwp/driver/run_cycle.py
python3 runtime/iwp/driver/run_cycle.py --arm kill-mid-cycle --repeats 3 --fault kill-game --fault-at after-title --fault-repeat 2
python3 runtime/iwp/driver/run_cycle.py --arm sigkill-mid-cycle --repeats 3 --fault sigkill-game --fault-at after-input --fault-repeat 2
python3 experiments/E004-iwp-driver/measurements/make_tables.py FIRST LAST    # the new batch's run numbers
```
