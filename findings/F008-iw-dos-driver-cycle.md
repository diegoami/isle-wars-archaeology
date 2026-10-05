# F008 The DOS Isle Wars driver repeats launch, option box, one click, observation, termination and reset ten times in one command with one `before` hash, in 18.38 to 18.64 s a repeat; DOSBox-X killed by SIGKILL or by closing its X client ends that repeat `aborted`, the reset restores the run copy, and the next repeat completes

- **Status**: proposed
- **Question**: Can a reusable driver (`runtime/iw-dos/driver/`, W5b) take DOS *Isle Wars* from a known state to a known screen, give one input, observe before and after, terminate and reset, ten times in one command with an identical `before` screenshot? Does DOSBox-X killed in the middle of a cycle make that repeat `aborted`, with the next repeat starting from the baseline? How long does a repeat take? (E006, task T15, W5b.)
- **Tests claims**: none (runtime; no game rule)
- **Experiment and runs**: E006; runs E006-r0001 to E006-r0016, all in `runs/E006/`. `control` E006-r0001 to E006-r0010 (one command, at `bb91e85d3230`); `sigkill-mid-cycle` E006-r0011 to E006-r0013 and `close-mid-cycle` E006-r0014 to E006-r0016 (one command each, at `f974f52207a0`, which changes no source of the driver: it adds the control's records).
- **Artifact**: set `iw-dos-3.1-30121376`, variant none. No repeat chose a level or played a game.
- **Max intervention**: I1 (screenshots of the game window; read-only reads of `/proc` and of the run copy)
- **Tier reached**: V2 (the original, headless, under DOSBox-X; no run on DOS hardware or another emulator, so no V3)
- **Confidence**: the control is one command of ten repeats. Every observation but times, the repeat's own work directory and its display number is the same in all ten. Each fault arm is one fault at one checkpoint: it shows the recovery path once, not its variance or other points. One machine (WSL2), one DOSBox-X build, one day.

## Answer

### Ten repeats, one command, one state

- One command, `python3 runtime/iw-dos/driver/repeat.py --arm control --repeats 10`, exited 0 and wrote ten `completed` records, E006-r0001 to E006-r0010 (`measurements/command-output/20261005T132416Z-bb91e85d3230-control.out.txt`).
- In E006-r0001 to E006-r0010 the `before` screenshot has one raw-pixel sha256, `6d7d28500a9562d2...`, and one PNG file sha256, `ce3d9ebda664b064...`; the `after` screenshot (the Select level dialog) has one raw-pixel sha256, `c38316e1b2d6fcaf...`.
- These pixel hashes are those F005 reports for E003-r0001 to E003-r0003, from the spike's cycle at another commit.
- In E006-r0001 to E006-r0010 `start_state.sha256` is one value, `ea77bd8651b51f11...`: the listing of the run copy (size, sha256, modification time of each entry) that the command took as its baseline, which each repeat's seal required twice.
- In E006-r0001 to E006-r0010 every one of the 13 seal observations is `ok`: six checks at the start, the same six immediately before the launch, and the display held by the repeat's own Xvfb.
- In E006-r0001 to E006-r0010 DOSBox-X ended 0.05 s after the driver's SIGTERM with exit status 0, no process of the repeat was alive after terminate, the run copy had gained `ISLEWAR.SCR` (20 bytes, `1cc857c57bc83a00...`, the same in all ten), and "run copy after reset equals the baseline" is `yes`.

### What varies

- Across E006-r0001 to E006-r0010, 12 of the 39 observations take more than one value (`measurements/varies-E006-r0001-r0010-20261005T133026Z.md`).
- Of those 12 in E006-r0001 to E006-r0010, ten are times; the other two are the repeat's number and the configuration's sha256.
- The configuration differs between E006-r0001 and E006-r0002 only in its work directory (`/tmp/w1`, `/tmp/w2`): `dosbox.conf.txt`, `dosbox.log` and `run.log` of E006-r0001 to E006-r0010 are each one text once the work directory, the display number and the times are replaced by placeholders (same table).
- `before.png`, `after.png` and `changes.log` are one file each over E006-r0001 to E006-r0010 (same table).

### Time

- A repeat, from the first seal to the end of the reset, took a median of 18.475 s, range 18.38 to 18.64 s, over E006-r0001 to E006-r0010 (`measurements/tables/E006-r0001-r0016.md`).
- The option box was reached and stable at a median of 16.975 s after the launch (16.87 to 17.18) over E006-r0001 to E006-r0010; F005 had 16.92 to 17.07 s for E003-r0001 to E003-r0003.
- The Select level dialog was reached and stable at a median of 18.17 s after the launch (18.07 to 18.35) over E006-r0001 to E006-r0010.
- The wait for the option box is the largest stage in E006-r0001 to E006-r0010: Xvfb took 0.05 s, the 640x350 window came 1.63 to 1.70 s after the launch, the dialog about 1.2 s after the option box, and everything outside the launch-to-dialog span (the seals, Xvfb, terminate, the reset, the logs) about 0.3 s.

### Recovery

- E006-r0012 (SIGKILL of DOSBox-X after `before.png`, before the click, sent through the marker check) is `aborted: game-died: DOSBox-X was gone (exit status -9) before perform`.
- E006-r0015 (DOSBox-X's X client closed with `xdotool windowkill` after the click) is `aborted: game-died: DOSBox-X was gone (exit status 1) before wait_for_screen`.
- In E006-r0012 and E006-r0015 no process of the repeat was alive after terminate, and "run copy after reset equals the baseline" is `yes`; E006-r0012 has no click observation and no `after.png`, E006-r0015 no `after.png`.
- The next repeats, E006-r0013 and E006-r0016, completed with the control's `start_state.sha256` and `before` and `after` hashes, and each fault command exited 0 (`measurements/command-output/20261005T132738Z-f974f52207a0-sigkill-mid-cycle.out.txt`, `measurements/command-output/20261005T132833Z-f974f52207a0-close-mid-cycle.out.txt`).
- The first repeats of the fault commands, E006-r0011 and E006-r0014, completed like the control.
- The exit statuses in E006-r0012 (-9) and E006-r0015 (1) are those F005 reports for SIGKILL (E003-r0011) and a closed X client (E003-r0012).

## Method

The driver is `runtime/iw-dos/driver/`: `session.py` (one session, the API), `repeat.py` (E006's command), `procs.py` (the one command helper and the one signal sender), `errors.py` (the named failures). It reuses T11's spike (`runtime/iw-dos/spike/cycle.py`: the configuration, the snapshot, the reset, the screen predicates, the PNG writer) and T14's step language (`navsteps.py` and the spike's step verbs). Its guarantees, by construction:

- one guard (`_guarded`, applied to every method of `PUBLIC`, static:runtime/iw-dos/driver/session.py:67) checks DOSBox-X and the display before and after every public method; `perform()` checks them before and after every step, and every wait of a session checks them on each poll and has a bound (static:runtime/iw-dos/driver/session.py:200);
- every command goes through `procs.must`, which raises on a non-zero exit, a timeout or a failed start (static:runtime/iw-dos/driver/procs.py:41); the spike's step verbs and screen send their commands through `Cycle.sh`, which the session replaces with it;
- every signal goes through `procs.kill_marked`: a pidfd is opened, the markers (`IW_DOS_DRIVER_INVOCATION`, one token per command; `IW_DOS_DRIVER_RUN`, the run id; the side) are checked in the process's environment, and the signal is sent through the pidfd (static:runtime/iw-dos/driver/procs.py:64);
- the seal runs the six checks of `SEAL_CHECKS` at the start and again immediately before the launch, then requires the display held by the repeat's own Xvfb (static:runtime/iw-dos/driver/session.py:63, static:runtime/iw-dos/driver/session.py:302);
- `completed` needs the known before-state reached and shot before any input, an input whose command exited 0 (static:runtime/iw-dos/driver/session.py:380), `after.png` after the last input, DOSBox-X ended by the driver's SIGTERM with exit status 0 (static:runtime/iw-dos/driver/session.py:469), and the reset equal to the baseline (static:runtime/iw-dos/driver/session.py:507).

A repeat: the configuration, the seal, Xvfb on `:60+n` inside the command's network namespace, the snapshot, the seal again, DOSBox-X, its window, the option box by its pixels (120 s bound), `before.png`, the fault checkpoint `after-before`, the step `click 60 32`, the checkpoint `after-input`, the Select level dialog by its pixels (20 s bound), `after.png`, SIGTERM (15 s bound), Xvfb stopped, the snapshot, the reset (`rundir.sync`) and its comparison with the baseline. The fault arms inject SIGKILL through `kill_marked`, or `xdotool windowkill`, at the checkpoint, from the command, not from the session; the session sees the death through its guard.

The tests (`tests/test_iw_dos_driver.py`, a fake game over T11's synthetic world) and their mutants (`tests/mutants_iw_dos_driver.py`, 46 mutants, all killed) are listed in the PR.

## What this does not establish

- That the driver recovers from a fault at any other point than the two checkpoints tried (after `before.png`, after the click), or from a fault of Xvfb, of the reset or of the host; the fake-game tests visit more points, but they are not the original.
- The variance of the recovery: each fault arm is one fault (E006-r0012, E006-r0015).
- Why the option box takes about 17 s (F005's hypotheses stand), or whether a repeat could be shorter.
- That the game's state behind the `before` screen is the same in every repeat: the screen and the run copy are, nothing else was read (no savestate, no memory, I1).
- Anything about another machine, another DOSBox-X build or another cycles setting: one machine, `fixed 3000`, one day.
- The DOSBox-X version string: `dosbox-x -version` exits 1 on this build, so the driver's checked probe records it `unknown`; the package version (`2024.03.01+dfsg-1build2`) is recorded.
- Pro: E006 is DOS only (rule 19).

## Where the evidence is

- Records: `runs/E006/E006-r0001.json` to `runs/E006/E006-r0016.json`; manifests: `evidence/E006/`; bundles: release `E006` (screenshots, `changes.log`, `run.log`, `dosbox.log`, `dosbox.conf.txt`).
- Command outputs, tables and the table of what varies: [`experiments/E006-iw-dos-driver/measurements/`](../experiments/E006-iw-dos-driver/measurements/).

## Reproduction

With `IW_DOS_DIR`, `IW_DOS_RUN` and `E006_BUNDLES` set and `setup/iw-dos/iw-dos-runtime.sh` printing `ready`: `experiments/E006-iw-dos-driver/scripts/run-arm.sh control`, then `sigkill-mid-cycle` and `close-mid-cycle`; `scripts/tables.py FIRST LAST` and `scripts/varies.py FIRST LAST` on the new records.
