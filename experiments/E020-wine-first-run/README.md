# E020 — first model-driven sitting under Wine

Contract: `docs/tasks/T38.md` (issue #114). This experiment is the first dispatch of the rule 18
carve-out (CLAUDE.md, 2026-10-08): a model agent drives the unregistered *Isle Wars Pro* build
under Wine on the owner's machine and captures per-frame evidence, for run capture and UI
observation. It is **corroboration, not replacement** of the owner's Bandicam captures (constraint
E): the sitting adds per-action timing; the owner's recordings stay the play-length, game-sense and
mistake-rich record.

- **Question**: can the dispatcher, watcher and click-driver take the F019 unregistered build
  through the two batches "Why a run is made" names, emit the per-sitting directory on the user's
  machine, and produce run records and evidence manifests whose frames are `recording` (constraint
  C) and which pass the constraint-F gate? Batches:
  - `cmb-accumulation` — Q-CMB-04/05/06/07/11 (F011): at least 100 computer-vs-computer exchanges
    with before/after counters for both sides in the first sitting; the
    `walkthroughs/f011-questions.md` counts accumulate across sittings.
  - `bomb-sampling` — `C-CRD-06` / Q-BON-08: at least 9 computer bomb plays across at least 3 games.
- **Artifact**: set `iwp-2.0-996e86c5`, variant `unregistered`, `Islepro.exe` sha256
  `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e` (F019's one known-good row,
  T35). No registered build is ever run (rule 19).
- **Runtime**: `wine-on-user-machine-iwp-2.0` (the only recognised platform token, constraint C),
  local, C0 (the install never leaves the user's machine, constraint A). The E004 machinery
  (`runtime/iwp/driver/session.py`) launches the session; the watcher and click-driver are T38's.
- **Design**:
  - `scenarios.txt` is the batch list: one block per batch, with its questions, its step file, its
    count floor and its structural vocabulary. It is the single source the dispatcher
    (`tools/wine-driver.sh`) and `tools/check_counts.py` read.
  - `launcher.py` resolves a batch and either prints its targets (`--help`, never starts wine) or
    runs it; a batch outside the list is refused by name before wine starts (constraint B).
  - The sitting directory is `/mnt/c/Temp/iwp-shots/wine/<YYYYMMDDTHHMMSSZ>/` on the user's machine
    (constraint A): `sitting.json`, `frames/`, `frames-index.jsonl`, `actions.jsonl`, `dumps/`,
    `watcher.log`, and the optional `readings.jsonl` the reading pass writes.
  - `--records --sitting DIR --batch NAME` turns a sitting's frames and readings into
    `runs/E020/<batch>/<run-id>.json` and `evidence/E020/<run-id>.manifest.json`, refusing a
    reading field outside the batch's vocabulary and never overwriting an existing record.
  - `check_records.py` is the batch checker of Done-when 3, 4 and 6.
- **Outputs**: run records at `runs/E020/<batch>/<run-id>.json`; evidence manifests at
  `evidence/E020/<run-id>.manifest.json`; bundles are release `E020` assets, never committed. The
  sitting directory is never committed.
- **Walkthroughs**: `walkthroughs/video-walkthrough.md` "Model plays under Wine" is the playbook.

## Constraint map

| Constraint | Where it holds |
| --- | --- |
| A locality | the sitting directory under `/mnt/c/Temp/iwp-shots/wine/`; records reference by hash only |
| B static-first | `scenarios.txt` is exactly "Why a run is made"; an unknown batch is refused by name |
| C per-run tagging | `runtime.platform = wine-on-user-machine-iwp-2.0`, `artifact.set/variant` and `start_state.sha256` against F019; `files[].class = recording` |
| D text handling | records carry `kind:role` fields and raw counters; the watcher and click-driver log structural names only |
| E corroboration | the task is not T28 and touches none of its records; the sitting corroborates |
| F tool check | `tools/check_no_originals.py` re-runs the F019 gate over every committed record |
| G per-claim wording | no `spec/` file is touched; amendments go through the per-claim finding |

## Scripts

- `bash tools/wine-driver.sh --batch <name> [--help]` — the dispatcher.
- `python3 tools/check_counts.py experiments/E020-wine-first-run/scenarios.txt` — the count checker.
- `python3 experiments/E020-wine-first-run/check_records.py` — the batch record/manifest checker.

After the first run this file is append-only. A changed design is a new experiment, or `v2/`.
