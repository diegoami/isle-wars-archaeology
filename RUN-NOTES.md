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

## Progress

- Final implementation commit `799a6b2` was pushed without `[skip ci]`.
- Code-only PR #251 was opened with `Closes #250` and `Refs #117` (the parent remains non-closing),
  attributed to OpenCode Luna 5.6 high; no review or subagent was run.
- Exact-head CI passed: checks and GitGuardian Security Checks both passed.

## END

- PR: https://github.com/diegoami/isle-wars-archaeology/pull/251
- Working tree remains clean. No game run, install, prefix, bundle, capture, review, subagent, merge,
  or worktree removal was performed; raw measurements remain unchanged.

# RUN-NOTES — #252

## Plan

- Implement only the owner-approved Q-UI-06 bounded `unestablished` checker exception.
- Require three distinct valid completed runs with shared artifact/configuration identity, exact
  record and manifest-backed PNG citations, and validated interrupted-attempt provenance.
- Preserve the positive count gate, records-only gate, Q-UI-07/Q16 policies, global integrity checks,
  raw measurements and existing metadata; add focused zero-count and duplicate-citation coverage.
- Run focused E019 tests, mutation verification, safety/link/diff checks, and record all results here.

## Progress

- Read `CLAUDE.md`, `docs/process.md`, the complete #252 brief, the seeded Q06 tests, checker,
  recorder helpers, README and existing RUN-NOTES. No original install, prefix, bundle, screenshot,
  game run or machine-local capture was accessed.
- Seeded baseline on `5b33b09`: the ten seeded Q06 tests had exactly one failure, the positive
  bounded-result case; all rejection cases passed.
- Added the Q06-only bounded configuration/sample and provenance gates, append-only README policy,
  and focused zero-candidate/duplicate-citation tests. Raw records and measured metadata were not
  changed.

## Progress

- Checkpoint commit `f3c5745` was pushed to `origin/fix/q06-bounded-result`.
- Focused Q06 tests passed: 12 tests. The focused E019 checker/recorder suite passed: 159 tests.
- Independently mutated the bounded exception away; the positive bounded test failed with the
  unchanged five-candidate diagnostic. The exact checker bytes were restored and matched the
  checkpoint byte-for-byte.
- `tools/check_no_originals.py`, `tools/check_links.py`, `git diff --check`, and the forbidden
  machine-path grep passed. No raw measurements, run records, manifests or failure metadata were
  changed.

## END

- Implementation is ready for the required final CI-triggering head commit and code-only PR.
- No game run, install, prefix, bundle, screenshot capture, review, subagent, merge or worktree
  removal was performed. Main alone performed the repository checks; unreviewed tests used the
  6G/no-swap memory cap.

# RUN-NOTES — #252 rework

## Plan

- Fix only the reproduced duplicate-Q06-section status/parser mismatch in PR253.
- Explicitly reject duplicate Q-UI-06 F020 sections, preserving the existing parser and all
  positive-status, no-F020, Q-UI-07, Q-UI-16, integrity and target gates.
- Run both seeded duplicate-section orderings before and after the fix, the 13-test Q06 suite, the
  160-test focused E019 suite, safety/link/diff checks, and an independent reverse mutation with
  exact byte restoration.
- Append progress and END notes, push checkpoint and final commits, and update PR253 only.

## Progress

- Read the complete rework brief, the independent M3 review, the main reproduction, current
  checker/tests/RUN-NOTES, and the new seeded regression commit `5b01257`. No original install,
  prefix, bundle, screenshot or game evidence was accessed.
- Before the fix, the seeded duplicate-section test failed for the first=`unestablished`,
  last=`narrowed` ordering because the checker returned `[]`; the opposite ordering was also
  covered by the seed and remains part of the rework verification.

## Progress

- Added the narrow fail-closed duplicate-Q06-section guard; no parser-wide rewrite or policy,
  runtime, raw-data, catalogue, target, task or CI change was made.
- After the fix, both seeded duplicate-section orderings pass, the Q06 suite passes 13 tests, and
  the focused E019 suite passes 160 tests.
- Independently reversed the duplicate-section guard; the seeded duplicate regression failed with
  the reproduced empty-error result. The exact saved checker bytes were restored in `finally`.

## END

- Checkpoint `32d21e6` was pushed to `origin/fix/q06-bounded-result`.
- Final post-check verification passed: Q06 focused tests 13, focused E019 tests 160, no-originals,
  links/JSON, diff-check and forbidden machine-path grep. The final commit below is the sole
  rework commit without `[skip ci]` and will trigger CI once.
- No original install, prefix, bundle, screenshot, game run, capture, review, subagent, merge or
  worktree removal was performed. Raw measurements, records, manifests and failure metadata remain
  unchanged. Unreviewed tests used the 6G/no-swap memory cap.
