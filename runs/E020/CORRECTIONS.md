# Corrections to the E020 run records

The records in this folder are raw and immutable (CLAUDE.md rule 20). Where one is wrong, the correction is written here
and in the finding that cites it, and the record stays as it was written.

## 2026-10-09: interventions of E020-r0001 to E020-r0003 (T40, PR #126, review round 1, R4)

- **What the records say.** `cmb-accumulation/E020-r0001.json` to `E020-r0003.json` declare
  `"interventions": [{"level": "I0", "what": "none"}]`.
- **What is true.** Each is the export of a model-driven sitting whose evidence is the watcher's frames, screenshots of
  the display (their `outputs` name the `.png` frames). A screenshot is passive instrumentation, I1
  (`vocabulary/interventions.md`). So each of them is I1. No memory was read and no file of the game was modified.
- **Why.** `experiments/E020-wine-first-run/e020_export.py` wrote I0 for every record.
- **Since.** From E020-r0004 the export declares the screenshots as I1 (`e020_export.INTERVENTIONS`; test
  `test_every_record_declares_its_screenshots_as_i1` in `tools/tests/test_wine_tools.py`). F011 and F014 state the
  maximum intervention of their E020 notes as I1.
