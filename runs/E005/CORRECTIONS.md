# Corrections to the E005 run records

The records in this folder are raw and immutable (CLAUDE.md rule 20). Where one is wrong, the correction is written here
and in the finding that cites it, and the record stays as it was written.

## 2026-10-05: interventions of r0001 to r0026 (PR #58, review round 0, R8)

- **What the records say.** r0001 to r0021 and r0023 to r0026 declare `"interventions": [{"level": "I0", "what": "none"}]`.
  r0022 declares one entry, I2 (the savestate).
- **What is true.** Every one of these runs took screenshots of the game window (their `outputs` name `.png` files, at
  least `before.png`). A screenshot is passive instrumentation, I1 (`vocabulary/interventions.md` at the pin). So each
  of them is I1, and r0022 is I1 and I2. The files the game wrote were read after it wrote them, which is I0.
- **Why.** The cycle's `interventions()` returned I0 unless a probe or a savestate step was used.
- **Since.** From r0027 the cycle lists every intervention, the screenshots as I1 first (`runtime/iw-dos/spike/cycle.py`,
  `interventions`; test `SavestateStepTest`, mutant "R8: screenshots are not declared"). F007 states the correction.

## 2026-10-05: two observation fields of r0001 to r0026 (PR #58, R11 and R7)

- `DOSBox-X window at 640x350 after launch (s)` is the duration of the poll for the window, which starts after the
  isolation check, not the time since the launch. From r0027 the records carry
  `DOSBox-X window at 640x350: poll seconds after the isolation check` and
  `DOSBox-X window at 640x350, seconds after launch`.
- These records were made with waits whose time-out did not abort the run (`wait-stable`, `wait-change`, `wait-exit`,
  and the settling after a click). None of the completed ones holds a timed-out required wait:
  `experiments/E005-iw-dos-state-inventory/measurements/round1/analysis-20261005T113945Z/waits.tsv`. The stillness
  before a click was not recorded before r0027.
