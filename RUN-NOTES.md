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

## END

Pending implementation and validation.
