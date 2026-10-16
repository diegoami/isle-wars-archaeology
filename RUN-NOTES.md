# RUN-NOTES — #248

## Plan

- Implement only the cooperative Q-UI-06/Q-UI-07 event budget and selected-walk outer watchdog.
- Extend focused tests for setup recheck, lifecycle cleanup failure, below-target rejection, and
  actual outer delegation.
- Run the focused suite, the E019 catalogue/phase/coverage tests, safety/link/diff checks, and
  independent mutation checks. Preserve raw measurements and restore mutation files byte-for-byte.

## Progress

- Read `CLAUDE.md`, `docs/process.md`, the complete #248 brief, the seeded tests, recorder, driver
  lifecycle, catalogue checker, and E019 README.
- Seeded baseline: `tests.test_e019_event_budget` had 6 failures and 1 error on commit `a39ece8`;
  the target-priority test passed.
- Added context-start event accounting, cooperative turn/setup/watch gates, configured outer-bound
  calculation, and the append-only README explanation. Tests and validation remain in progress.
- Commit `064b52f` was pushed to `origin/fix/248-event-budget`; PR #249 was opened with `Closes #248`
  and `Refs #117`.
- Focused E019 validation passed: 135 tests. Both independent mutations were killed and restored
  byte-for-byte. No-originals, link/JSON, diff, and scoped path checks passed.
- Full unittest discovery ran 1040 tests with 383 skipped and one machine-local E020 reset failure:
  `IWP_PREFIX` was inside this checkout/worktree. No original game or install was accessed.

## END

- Final implementation commit: `064b52f` (pushed).
- PR: https://github.com/diegoami/isle-wars-archaeology/pull/249
- No game run, install, prefix, bundle, capture, review, subagent, merge, or worktree removal was
  performed. Raw measurements were not changed.

# RUN-NOTES — #250

## Plan

- Implement only opt-in Q-UI-06/Q-UI-07 event calibration in the E019 recorder, with CLI gating,
  provenance, diagnostic brackets, and unchanged candidate/count/lifecycle semantics.
- Add focused regression coverage for small/non-countable changes, per-tick retention, CLI and inner
  forwarding, capture failure recovery, defaults, and no-input behavior.
- Prove the added tests fail against the saved pre-fix recorder, run the focused E019 suite and safety
  checks under the 6G/no-swap cap, and restore every mutation byte-for-byte.

## Progress

- Read the repository `CLAUDE.md`, `docs/process.md`, existing #248 recorder/tests, and the complete
  #250 brief. No original install, prefix, bundle, game, or capture was accessed.
- The seeded pre-fix calibration suite failed with 9 tests and 10 errors on the baseline recorder:
  missing `capture_changes`, CLI flag, and `run_walk` forwarding contract.
- Added synchronous full-stage calibration retention for any changed shared event-watch tick,
  separate calibration names/counters, turn/tick and accepted-PASS capture brackets, explicit
  sequential-read limitation, opt-in policy observation, and CLI rejection before launch.
- Added tests for defaults without the keyword, mixed event batches, event-helper forwarding,
  capture-failure lifecycle, and no-input behavior. The expanded pre-fix suite failed as expected
  (12 tests, 12 errors/failures); the exact saved recorder bytes were restored in `finally`.
- Focused E019 validation passed: 147 tests. Independent capture-retention and CLI-forwarding
  mutations both failed their seeded tests and the exact saved bytes were restored.
- `check_no_originals.py`, `check_links.py`, `git diff --check`, and the forbidden machine-path grep
  passed. No raw measurements or evidence records were changed.

## END

- Implementation is ready for the final non-`[skip ci]` commit and PR. No game run, install, prefix,
  bundle, capture, review, subagent, merge, or worktree removal was performed.
