# Corrections to the round-0 analysis tables

The tables in this folder were built by round 0's `scripts/analyze.py` and `check-board-reader.py` and are kept as
they were (CLAUDE.md rule 20). The round-1 tables, built over r0001 to r0038 by the corrected scripts, are in
`../round1/analysis-20261005T113945Z/`; F007 cites those.

## 2026-10-05 (PR #58, review round 0)

- **`turn-diff.tsv`, lines 2, 7, 15 and 23 (R9).** Lines 2 and 15 say "armies placed = Blue countries // 3 (min 2) = 5
  (the game's own rule, ISLEWAR.DOC)", and lines 7 and 23 say "ALL moves all but one of the attacker's armies". Both are
  statements of a game rule, which T14 excludes, and neither was measured: the first is a formula applied by the
  analyzer, the second a generalisation of two observed move-ins. What the runs show is only this: the attack-result
  message read `5 AGAINST 0` (by eye) and the target's army line went from 1 to 4. The round-1 `turn-diff.tsv` marks
  the chosen countries and derives nothing from a rule.
- **`timings.tsv`, column `first_human_turn_s` (R11).** It is the duration of the `until` poll that saw the human-turn
  panel, which starts only after the start click's change and stability waits; it is not the time from the start click.
  The round-1 table has `human_turn_panel_poll_s` (the same values) and, from r0027, `start_click_to_human_turn_s`,
  timed from the first start click.
- **The window time (R11).** Round 0's F007 quoted "1.62 to 1.75 s after launch" from the records' field
  `DOSBox-X window at 640x350 after launch (s)`, which is a poll that starts after the isolation check
  (`runs/E005/CORRECTIONS.md`); no table here has it.
- **The scripts' "never overwrites" (R3).** Round 0's `analyze.py` and `check-board-reader.py` wrote `<name>.new` when a
  table existed, and wrote over that `.new` on the next run. No `.new` file is in this folder; whether an earlier
  version of a table here was written over cannot be told from what was kept. Since round 1 every batch is a new
  directory and every table is created exclusively.
