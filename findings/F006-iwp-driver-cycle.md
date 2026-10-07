# F006 The Isle Wars Pro driver repeats launch, known screen, one input, observation, termination and reset ten times in one command with one `before` hash, in 10 to 16 s a repeat; a game killed at either of the two checkpoints tried ends that repeat `aborted`, the reset still restores the prefix, and the next repeat completes

- **Status**: proposed
- **Question**: Can a reusable driver (`runtime/iwp/driver/`, W5a) take Isle Wars Pro from a known state to a known screen, give one input, observe before and after, terminate and reset, ten times in one command with an identical `before` screenshot? Does a game killed in the middle of a cycle make that repeat `aborted`, with the next repeat starting from the baseline? How long does a kill-terminated repeat take against E002's 40 to 46 s? (E004, task T13, W5a; folds #40's first two items.)
- **Tests claims**: none (runtime; no game rule)
- **Experiment and runs**: E004; runs E004-r0001 to E004-r0077, all in `runs/E004/`, in five batches. Each batch is one or more commands at one commit:
  - **B5, E004-r0062 to E004-r0077, at `74bfcb5a888b`: the driver of this PR after round 2 of its review, and the batch this finding's answers cite.** E004-r0062 to E004-r0071 are the `control` arm (one command of ten repeats); E004-r0072 to E004-r0074 `kill-mid-cycle`; E004-r0075 to E004-r0077 `sigkill-mid-cycle`.
  - B6, E004-r0126 to E004-r0141, at `286a4c57eb69`: round 4's driver, in which `Session` composes the spike's `Cycle` instead of inheriting it (below). Not a new answer: it shows round 4 keeps B5's results. Control E004-r0132 to E004-r0141, ten `completed`, every `before` screenshot the same pixels as B5's (sha256 `fecd0a984e0d2f36…`), a median of 9.45 s a repeat (8.95 to 12.29); `kill-mid-cycle` E004-r0129 to E004-r0131 and `sigkill-mid-cycle` E004-r0126 to E004-r0128, the middle repeat of each `aborted: game-died`, recovered, and the next one completed; the prefix's registry files equal to the baseline before and after ([`command-output/implementer-c3-round4-20261005T221256Z.txt`](../experiments/E004-iwp-driver/measurements/command-output/implementer-c3-round4-20261005T221256Z.txt)). E004-r0078 to E004-r0125 ran round 3's drivers and are reported on PR #54, not here. One of them, E004-r0109, is a session whose first seal refused a prefix off its baseline: its clean-up observation says `yes` (recovered) although no reset ran. Round 4 records `no` for that case (R2 of round 3's review).
  - B4, E004-r0046 to E004-r0061, at `7b665df2c361`: the main session's re-take of round 1. Control E004-r0046 to E004-r0055, `kill-mid-cycle` E004-r0056 to E004-r0058, `sigkill-mid-cycle` E004-r0059 to E004-r0061.
  - B3, E004-r0030 to E004-r0045, at `a464f266d8ae`: round 1. Control E004-r0030 to E004-r0039, `kill-mid-cycle` E004-r0040 to E004-r0042, `sigkill-mid-cycle` E004-r0043 to E004-r0045.
  - B2, E004-r0017 to E004-r0029, at `38e58720e091`: the main session's re-run of round 0. Control E004-r0017 to E004-r0026, and `sigkill-mid-cycle` E004-r0027 to E004-r0029 only.
  - B1, E004-r0001 to E004-r0016, at `c6588a95fc48`: round 0. Control E004-r0001 to E004-r0010, `kill-mid-cycle` E004-r0011 to E004-r0013, `sigkill-mid-cycle` E004-r0014 to E004-r0016.

  B1 to B4 ran earlier drivers. Rounds 0 and 1 of the review (PR #54) found that those drivers could accept, by these paths:
  - a failed reset after an abort (B1, B2);
  - `completed` without an input (B1, B2);
  - an input whose command failed (B1 to B4);
  - a game that died just before terminate (B1 to B4);
  - a registry change between the two seals (B1 to B4);
  - another server's display (B1 to B4).

  None of these paths is known to have occurred in their records. Their records stay, and are cited here as earlier measurements of the same cycle. Nine repeats aborted by design and stay: E004-r0012, E004-r0015, E004-r0028, E004-r0041, E004-r0044, E004-r0057, E004-r0060, E004-r0073, E004-r0076.
- **Artifact**: set `iwp-2.0-996e86c5`, variant none. No repeat clicked Save as default or played a game.
- **Max intervention**: I1 (screenshots of the display and read-only reads of `/proc` and of the game copy; no memory read, no modified file)
- **Tier reached**: V2 (the original, headless, under Wine; no native Windows run, so no V3)
- **Confidence**: the control is one command of ten repeats in each batch. Every measured quantity but time is the same in all fifty control repeats. The fault arms are one fault per command, so they probe the recovery path at two checkpoints; they do not measure its variance or cover other points. One machine (WSL2), one Wine build, one day.

## Answer

- **Ten repeats, one command, one state.** In B5, `python3 runtime/iwp/driver/run_cycle.py` exited 0 and wrote ten `completed` records, E004-r0062 to E004-r0071 ([`command-output/rework2-74bfcb5-control.out.txt`](../experiments/E004-iwp-driver/measurements/command-output/rework2-74bfcb5-control.out.txt)). In all ten:
  - the `before` screenshot has the same raw-pixel sha256, `fecd0a984e0d2f36...`, and the same PNG file sha256, `ae6e98d28d379bb4...`;
  - the `after` screenshot (the Options screen) has the same PNG sha256, `426d77e724d793dd...`;
  - `start_state.sha256` is the same, `b1df17775116d148...`;
  - one input step succeeded, with every helper command of it exiting 0; `before.png` was taken before it and `after.png` after it;
  - the display was held by this run's own Xvfb at the first attempt;
  - the game and the display were alive just before terminate;
  - the clean-up observation "every stage succeeded and the prefix was reset" is `yes`.

  **Only times vary** across the ten ([`tables/E004-r0062-E004-r0077-stage-times.md`](../experiments/E004-iwp-driver/measurements/tables/E004-r0062-E004-r0077-stage-times.md)). The same four hashes are those of every completed repeat of B1 to B4. The PNG hashes of `before` and `after` are the ones F002 reports for E001-E004-r0028 to E004-r0030, from another driver and another prefix build. The `start_state` differs from F002's (`34ac62c3...`); the cause was not investigated (the prefix has since been used by E002's runs and by `setup/iwp/iwp-runtime.sh`).
- **Time.** A repeat, from the first seal to the end of the reset, took a median of **9.88 s** (9.78 to 12.64, n=10) in B5's control. Every repeat is kill-terminated (`wineserver -k`). That is below E002's 40 to 46 s for a kill-terminated run. The earlier controls took 15.06 s (B1), 15.10 s (B2), 16.15 s (B3) and 11.12 s (B4). The time goes to (B5 control, medians):

  | Stage | Median s |
  | --- | --- |
  | Xvfb ready, xfwm4 registered | 0.05, 0.12 |
  | snapshot of the prefix before the launch | 0.46 |
  | game window after launch | 0.53 |
  | title screen reached and stable, after launch | 6.51 |
  | terminate (`wineserver -k`, the bounded wait) | 0.50 |
  | display side gone after Xvfb and xfwm4 stopped | 0.00 |
  | snapshot, diff and reset | 1.04 |

  The title screen is the largest measured stage: 6.5 to 9.6 s over the completed repeats of B1 to B5; F002 had 6.6 to 6.7 s. These records measure elapsed time. They do not show whether any stage could be shorter, nor why the batches differ: B1 to B3 spent about 3 s more each repeat on the display side (next point), and their other stages were slower too. B5's first repeat (12.64 s) spent 2.84 s on the snapshot before the launch, against 0.45 to 0.53 s in the others.
- **The game side is gone at once after `wineserver -k`. The display side took about 3 s to end in B1 to B3, and no measurable time in B4 and B5.** In all 77 records, "game side gone after terminate" is 0.00 or 0.01 s. In every record that reached it, "display side gone after the display was stopped" is 2.99 to 3.05 s in B1 to B3 and 0.00 s in B4 and B5. The batches differ in one recorded condition, among others not recorded: in every record of B1 to B3 the driver's own environment had a `DBUS_SESSION_BUS_ADDRESS` naming a bus that did not exist ("set, stale"), and in every record of B4 and B5 the address named a bus that existed ("set"). The driver unsets the address for its children in both cases. That the stale address is what made the display side take 3 s is a hypothesis (below): the batches were not a controlled comparison. The driver tells the two sides apart by a second marker, `IWP_CYCLE_SIDE`, inherited from what started each process, and waits with a bound for the game side only (#40's first item).
- **A game killed at either checkpoint aborts that repeat, the reset restores the prefix, and the next completes.** In B5:
  - E004-r0073 (an outside `wineserver -k` after the title screen) is `aborted: game-died: the game process exited before the screenshot before.png (status 0)`;
  - E004-r0076 (SIGKILL of the game process after the Options click, sent through the driver's marker check) is `aborted: game-died: the game process exited before the options screen appeared (status -9)`.

  In both, "prefix after reset equals prefix before launch" is `yes` and the clean-up observation is `yes`. The next repeat (E004-r0074, E004-r0077) completed with the same `start_state.sha256` and the same `before` hash as the control, and each command exited 0. The same held for every fault record of the earlier batches (listed under Inferences). The command exits 0 for a fault arm only when the faulted repeat is `aborted: game-died`, its clean-up succeeded, and every other repeat completed.
- **The seal is kept.** In all 16 records of B5:
  - the install read-only inside the run, the prefix sealed with 0 problems, and the registry files equal to their baseline, both before anything starts and again immediately before the launch;
  - the game in its own network namespace, seeing only `lo`;
  - no process of the run alive after terminate;
  - the prefix after reset equal to the prefix before the launch ([`tables/E004-r0062-E004-r0077-cycle-table.md`](../experiments/E004-iwp-driver/measurements/tables/E004-r0062-E004-r0077-cycle-table.md)).

  B1 to B4 recorded the same, except that their check immediately before the launch did not repeat the install and baseline comparisons.
- **The bus (#40's second item).** The driver unsets `DBUS_SESSION_BUS_ADDRESS` for its children, and says in the log and the record whether it was set and stale. xfwm4 registered within 0.12 to 0.49 s in all 77 records, with a stale address (B1 to B3) and with a live one (B4, B5). That a stale address is what kept E002's xfwm4 from registering (E004-r0002, E004-r0003) is a hypothesis, below.

## Method

**Artifact and prefix.** Set `iwp-2.0-996e86c5`. The prefix was the one E001 and E002 used, reset by each run. After B5, `setup/iwp/iwp-runtime.sh` printed `ready`, and `tools/register_artifact.py check` of the install against the set exited 0 with only `unins000.dat` and `unins000.exe` unlisted ([`measurements/done-when-5-rework2.txt`](../experiments/E004-iwp-driver/measurements/done-when-5-rework2.txt); after B3: `done-when-5-rework1.txt`; after B1: `done-when-5.txt`).

**The driver.** `runtime/iwp/driver/session.py` is built on the spike's `Cycle` (`runtime/iwp/spike/cycle.py`), whose seal, screens, step language, snapshots and reset it reuses. Since round 4, `Session` holds that machinery (an `Engine`, a subclass of `Cycle`) privately and does not inherit it. Its public methods are its own, each through one liveness guard or with a stated reason, and no method of `Cycle` (`complete_script()`, `run_step()`, …) is an attribute of a `Session`. So `complete()` is its only route to `completed`, and `perform()` its only way to send the game a step. B1 to B5 ran drivers in which `Session` inherited `Cycle`, so those methods were public. A caller could reach `completed` past `complete()`'s checks, or send a step to a dead game (round 3's review, R1 and R3). The E004 command calls neither, and the records show only `complete()`'s path. Since round 5, every public view of the session's state (the environment, the processes, the screens reached and expected, the observations, the outputs, the arguments) is an immutable copy made at each read, never the engine's live object: a caller cannot retarget `WINEPREFIX` after the seal, mark a screen reached by hand, widen or narrow what `complete()` requires (the expected screens are named through `expect()`), or delete the liveness guard's process entry (round 4's review, R1 to R3, each demonstrated on the round-4 views); and the command sweep pins every state probe (`spike.probe`) to its named sites and counts, so a checked `must()` replaced by a `probe()` is an offender like a raw command (R4). The driver adds:
- named errors (`errors.py`): `SealError`, `DisplayError`, `LaunchError`, `ScreenNotReached`, `GameDied`, `StepFailed`, `TerminateError`, `ResetError`, `RecordError`. A repeat that hits one is recorded `aborted: <kind>: <reason>`, with the first reason in the status and every later fault as an observation;
- a seal before anything starts, and the same checks again immediately before the launch: the install read-only, the prefix safe to launch from, and the registry files equal to their baseline (the reset can only bring the prefix back to the baseline; diagnosis 4 in the probes file);
- the display as this run's own: the display number picked is a hint only. Xvfb is ready only when it is alive, itself holds the display's listening socket, and answers; another server answering on the same number is never taken for it. When this run's Xvfb cannot hold the display, another display is tried, three in all, and then `DisplayError`;
- the game side and the display side checked alive at every stage boundary: before every step, every screenshot and every screen poll, at the end of the launch and of the body, and just before terminate. A death just before terminate makes the repeat `aborted`, and the clean-up and reset still run;
- every helper command whose result is used checked for its exit status (`spike.must`): the xdotool inputs, the `import` captures, `xdpyinfo`, the window's id and geometry, the window titles, and `git`. A failed input is a failed step, never an action. The exit status of `wineserver -k` is recorded and not relied on, because it is 1 when no server is left. What is relied on is that the game side is gone, checked with a bound;
- `completed` only when all of these hold:
  - the known screens the body expects were reached (by pixels);
  - at least one input step succeeded;
  - `before.png` was taken before the first input and `after.png` after the last;
  - both sides were alive at the end;
  - terminate, stopping the display and the reset all succeeded, and the reset was shown to restore the prefix;
- `recovered`, true only when every clean-up stage succeeded and the reset ran and was shown to restore the prefix: the command starts the next repeat only then, whatever the status of the last one. A session that ended before its snapshot (a seal that refused the prefix, no display) performed no reset and is never `recovered`. A prefix the seal refused is never reset to make it so;
- the side marker and the bounded wait described above: 10 s for the game side after `wineserver -k`; then a second `wineserver -k` and SIGKILL of the game side; then 5 s more, then `TerminateError`;
- a bound on every helper command (60 s, then SIGKILL and at most 5 s to reap it), on `wineserver -k` (15 s), on the reaps of Xvfb and xfwm4, and on the whole command (300 s a repeat);
- every signal sent through one function, `kill_marked`. It re-checks, through a pidfd, that the process still carries the markers it must: this run's id and side, or this command's token `IWP_CYCLE_INVOCATION`. Another run's or another command's process is never signalled, the injected SIGKILL included;
- for the children: no `DBUS_SESSION_BUS_ADDRESS` and no `TMPDIR`.

The spike changed in five ways:
- its launch is split into the seal and `start_game()`;
- its display number and the environment of Xvfb and the window manager are attributes the driver overrides;
- its `run()` helper is bounded, and a checked `must()` serves the helpers whose result is used, which also applies to the spike's own runs;
- its `reset()` returns whether the prefix was restored;
- the docstring of `attack_picked` no longer states game rules (R2 of the F003 research review).

`runtime/iwp/driver/runner.py` is the E004 command: one namespace for the whole command (`unshare -rmpf`; the install bound read-only once, a private `/tmp`), and for each repeat a new session with its own run id, its own Xvfb and xfwm4, and its own record. A repeat that does not end as expected stops the command with exit 1, so that a wrong state is not carried on.

**One repeat, in order.**
1. The install is read-only; the prefix is sealed and equals its baseline.
2. Xvfb starts and is shown to hold its display; xfwm4 starts.
3. The prefix is snapshotted.
4. The install, the seal and the baseline are checked again.
5. The game starts in its own network namespace.
6. The title screen is waited for by its pixels and for stability.
7. `before.png`.
8. The pointer goes onto Options, the label highlights, and a click is sent (`click! 320 585` in the E002 step language); every xdotool call exits 0.
9. The Options screen is waited for by its pixels.
10. `after.png`.
11. Both sides are checked alive.
12. `wineserver -k`, then the bounded wait.
13. The display stops.
14. The prefix is snapshotted, diffed and reset, and the reset is checked.

**Waits.** Every wait is a poll on a condition with a timeout (Xvfb, xfwm4, the game process, the window, the title and Options screens, stability, the Wine side and display side going away), and every helper command has a bound. The only fixed sleep is the 0.4 s between the two captures of the stability test, as in the spike.

**Faults.** `--fault kill-game` runs `wineserver -k`, and `--fault sigkill-game` sends SIGKILL to the game process through `kill_marked`. Both act from the command, not from a driver method, at the checkpoint `after-title` or `after-input`, in the repeat named by `--fault-repeat`. A fault that does not kill the game raises `FaultNotInjected`, and the command exits 1.

**Tests.** `tests/test_iwp_driver.py` runs the real session code with a fake game (a `sleep` process carrying the run's marker), a scripted screen, a fake `wineserver`, real processes holding abstract X sockets, and a recorded or real `run_step`. `tests/mutants_iwp_driver.py` removes each guarantee in turn and shows its tests failing. Each mutant is killed (a run of the script with a `TMPDIR` outside every checkout shows it; 63 through round 4, six more in round 5):
- round 0's twelve;
- round 0's review, fourteen: R1 the command's own token and the pidfd re-check; R2 the recovery gate; R3 the bounds; R4 the input between the screenshots;
- round 1's review and its class sweep, eighteen: A a signal without its markers; B a failed command taken as done (for key, click, the pointer moves, clicks, move, window titles, the capture, and `must` itself); C a death just before terminate, and the display side not checked; D the second install and baseline checks; E a display taken from another server, no retry, and failing open;
- round 2's review, nine: an incomplete baseline accepted; a game dead at terminate taken as a clean end, or the rest of its side left; the stability poll and the file observation without the liveness check; `xprop`'s exit status ignored; a failed version probe parsed; and the two sweeps (a method without the guard, a raw subprocess call);
- round 3's review, ten: R1 a `Session` that delegates to its engine, and an engine that no longer refuses `complete_script()`; R2 a session refused before its snapshot counted `recovered`; R3 a `Session` that inherits `Cycle` again, an unguarded `run_step()` on it, and `perform()` marked unguarded; R4 a raw `subprocess.run` (the reviewer's own mutant) and an unchecked `run()` for the key in the spike's `run_step`, a raw call in `setup/iwp/prefix.py`, and an excluded spike method brought back on the path. The guard sweep reads a real `Session`'s interface at runtime, inherited names included. The command sweep covers every file of this repository that the driver loads, the spike's `cycle.py` and `steps.py` and the setup modules included. Its exclusions are named, and each is shown off the driver's path;
- round 4's review, six: R1 a view that hands out the engine's live environment again; R2 a view that hands out the live `reached` and `expected` sets again; R3 a view that hands out the live process registry again; R4 a `must()` replaced by `probe()` at the spike's key command and at the read-only bind, and the probe sites unpinned again (every probe allowed anywhere).

## Observations

Per-repeat values are in the tables of each batch, made once by `make_tables.py` from the records:
- B5: `measurements/tables/E004-r0062-E004-r0077-*.md`;
- B4: `measurements/tables/E004-r0046-E004-r0061-*.md`;
- B3: `measurements/tables/E004-r0030-E004-r0045-*.md`;
- B2: `measurements/tables/E004-r0017-E004-r0029-*.md`;
- B1: `measurements/cycle-table.md` and `measurements/stage-times.md`.

The commands' own output is in `measurements/command-output/`.

| Quantity | B5 control (E004-r0062 to E004-r0071) | B5 fault arms (E004-r0072 to E004-r0077) | B1 to B4 control (40 repeats) |
| --- | --- | --- | --- |
| records, completed / aborted | 10 / 0 | 4 / 2 | 40 / 0 |
| `before` pixels sha256 distinct values | 1 | 1 (4 completed) | 1 |
| `start_state.sha256` distinct values | 1 | 1 (all 6, aborted included) | 1 |
| session seconds, median (range) | 9.88 (9.78 to 12.64) | 9.81 (9.74 to 9.85), completed only | 15.06, 15.10, 16.15, 11.12 |
| game side gone after terminate (s) | 0.00 | 0.00 | 0.00 to 0.01 |
| display side gone after the display stopped (s) | 0.00 | 0.00 | 2.99 to 3.05 (B1 to B3), 0.00 (B4) |
| prefix after reset equals the one before the launch | yes in 10 | yes in 6 | yes in 40 |
| clean-up: every stage succeeded | yes in 10 | yes in 6 | yes in 20 (B3, B4); not recorded before |
| display held by this run's Xvfb, attempt | 1 in 10 | 1 in 6 | not recorded (older driver) |

## Hypotheses and observations not backed by run records

These come from exploratory diagnoses made while the driver was built ([`measurements/probes/diagnoses.md`](../experiments/E004-iwp-driver/measurements/probes/diagnoses.md)), and from comparing batches that were not controlled. Each diagnosis was seen once or twice, without a run record or a downloadable raw output. None is a result of this finding, and the driver depends on none of them.

- **What E002's 30 s after `wineserver -k` was.** Hypothesis: the spike's poll ran to its 30 s timeout on processes of the display side, not on Wine. Seen once (diagnosis 1): right after `wineserver -k`, the processes carrying the run's marker were six non-Wine processes (`dbus-launch`, two `dbus-daemon`, `at-spi-bus-launcher`, `at-spi2-registryd`, `xfconfd`), the same in three listings 2 s apart. What started them was not read; that xfwm4 did, through `dbus-launch --autolaunch` for want of a bus, is a guess. E004 measures something else: how long this driver waits for its own game side and display side. That does not show what E002's poll waited for. A controlled test would run the spike's terminate with the processes listed and their parents read, in records.
- **The stale bus and the display side's 3 s.** Hypothesis: with a stale `DBUS_SESSION_BUS_ADDRESS` in the driver's environment, xfwm4 starts the daemons above, and they take about 3 s to end after the display stops. The batches agree with it: every record with a stale address (B1 to B3) took 2.99 to 3.05 s, and every record with a live one (B4, B5) took 0.00 s. The comparison was not controlled. The batches also differ in time of day, load and code, and no record lists the processes. A controlled test would alternate the two conditions within one command, with the display side's processes listed.
- **The stale bus and E002's E004-r0002 and E004-r0003.** Hypothesis: the stale address kept xfwm4 from registering there. Seen in exploration (diagnosis 2): with the stale address set for the children, the spike's xfwm4 did not register within 20 s; with it unset, it registered. No E004 arm sets the stale address for the children, so E004 shows only that xfwm4 registers with it unset.
- **`TMPDIR`.** Seen while building the driver, without records (diagnosis 3):
  - with `TMPDIR` set to a folder the run's private `/tmp` lacks, Wine stopped at once (`unable to create wineserver tmpdir`);
  - with `TMPDIR=/tmp` it aborted once (`free(): invalid pointer`, status -6);
  - with it unset, every launch worked.

  The driver passes the game no `TMPDIR`. Neither failing condition was replicated, and the cause is not known.

## Inferences

- On the game, recovery is shown only at the two checkpoints the fault arms use, by these records. In each case the faulted repeat aborted with `game-died`, its reset restored the prefix, and the next repeat completed.
  - `after-title`, `wineserver -k`: E004-r0012 then E004-r0013 (B1); E004-r0041 then E004-r0042 (B3); E004-r0057 then E004-r0058 (B4); E004-r0073 then E004-r0074 (B5).
  - `after-input`, SIGKILL: E004-r0015 then E004-r0016 (B1); E004-r0028 then E004-r0029 (B2, which has only this arm); E004-r0044 then E004-r0045 (B3); E004-r0060 then E004-r0061 (B4); E004-r0076 then E004-r0077 (B5).
- A death at any other point was not tried on the game: during the launch, during a screen wait, between the end of the body and terminate, during terminate. The unit tests visit the driver's handling of some of these points with a fake game (a game dead before its first screen, a game or a display dead just before terminate, a display dead mid-cycle). That shows the driver's logic, not what the game or Wine does there.

## Alternatives considered

- Cutting the cycle further by skipping the whole-prefix snapshots (about 1.5 s a repeat in B5) or the second seal: refused. They are the seal and the reset check, and a faster cycle that skips a check is a failure (T13 hazards).
- Starting the game once and keeping it between trials (models.md, "relaunch rarely"): the E004 cycle is defined as a launch from the baseline each time, so that the `before` hash shows the start is the same. A driver for later experiments can use `Session` that way; this finding does not test it.
- Leaving the 30 s poll and only lowering its timeout: it would still have counted processes that are not the game side.
- Letting Xvfb pick its own display (`-displayfd`): not tried. The driver picks a number and proves ownership of the socket instead, which the tests can exercise without an X server.

## What this does not establish

- Native Windows: not tried; nothing about V3.
- DOS *Isle Wars*: nothing (CLAUDE.md rule 19).
- Any game rule or a game played: the cycle goes only from the title screen to the Options screen.
- These remain hypotheses or unexplained observations (above): what E002's 30 s wait was; what started the display-side daemons; why the display side took 3 s in B1 to B3 and none in B4 and B5; why a stale bus or a `TMPDIR` breaks a launch.
- That any stage is as short as it can be: the records measure elapsed time. Why the batches differ in time was not investigated.
- That the driver recovers on the game from a death at any point but the two checkpoints, or from a crash of Xvfb or xfwm4 on the real display.
- A different machine, Wine build or prefix: one machine, one day. The `start_state` here is not F002's, and the cause was not investigated.
- That `H3`'s preflight is not needed: `setup/iwp/tokens.py --tokens` is still the preflight (`TODO(H3)`).
- A sandbox: the prefix is checked at the points of use, as in F002. A process of the same user that changed it between a check and Wine's own lookups would not be seen.

## Where the evidence is

- Run records: `runs/E004/E004-r0001.json` to `E004-r0077.json` (B5: E004-r0062 to E004-r0077).
- Evidence manifests: `evidence/E004/E004-r0001.manifest.json` to `E004-r0077.manifest.json`.
- The bundles (screenshots, `changes.log`, `run.log`, `wine.log`) are kept locally, outside the repository; the main session uploads them to release `E004` after review. Each file is named `<sha256[:16]>-<name>`, as its manifest says.
- Tables, diagnoses and the command output: `experiments/E004-iwp-driver/measurements/`.

## Reproduction

The machine needs what F002 lists. Set `IWP_DIR` to the install, and `IWP_PREFIX` and `E004_BUNDLES` to locations outside every checkout and the install. Then, after committing, run these from a checkout that is not under `/tmp` (the run's private `/tmp` hides it):

```text
bash setup/iwp/iwp-runtime.sh
python3 runtime/iwp/driver/run_cycle.py
python3 runtime/iwp/driver/run_cycle.py --arm kill-mid-cycle --repeats 3 --fault kill-game --fault-at after-title --fault-repeat 2
python3 runtime/iwp/driver/run_cycle.py --arm sigkill-mid-cycle --repeats 3 --fault sigkill-game --fault-at after-input --fault-repeat 2
python3 experiments/E004-iwp-driver/measurements/make_tables.py FIRST LAST    # the new batch's run numbers
```
