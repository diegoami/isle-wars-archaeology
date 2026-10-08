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
  local, C0 (the install never leaves the user's machine, constraint A). A sitting runs as the
  E004 command does: private user, mount and PID namespaces, a private /tmp, the install bound
  read-only, and one `Session` (`runtime/iwp/driver/session.py`: the seal, its own Xvfb, the game in
  its own network namespace, every wait bounded). The watcher and the click-driver are T38's.
- **Design**:
  - `scenarios.txt` is the batch list: one block per batch, with its questions, its event and the
    fields an event carries, its floors, its loop bounds and its claims. The dispatcher
    (`tools/wine-driver.sh`) and `tools/check_counts.py` both read it.
  - `launcher.py` resolves a batch and prints its targets (`--help`, never starts wine), runs a
    sitting, or exports one (`--records`); a batch outside the list is refused by name before wine
    starts (constraint B). It has no option that moves the sitting directory.
  - `e020_sitting.py`: the one sitting root `/mnt/c/Temp/iwp-shots/wine/` (refused when it is a
    link, inside a checkout or this repository, or overlaps the install, the prefix or the
    bundles), the sitting directory created new, and the binary's identity measured before the
    launch (the install's and the run copy's `Islepro.exe` equal the F019 row).
  - `play.steps` holds the step blocks (E002 step language): `new-game` (E002 `loss-easy.steps`'
    order: New Game, EASY, Play Game; mid-game at EASY New Game goes straight to the setup screen,
    E002-r0018), `quiet` (the board unchanged for 4 s, bounded), `place` (E002's `click-until` over
    the proven country points: the placement row lights only for a country the human owns),
    `commit` (ALL, PLACE, PASS, CONTINUE), `dismiss`, `eliminated-keep-playing` (one click on
    the elimination notice's KEEP PLAYING, 665,531; round 4) and `game-over-continue` (one click on
    the winner notice's CONTINUE, 401,534; round 6). No block attacks.
  - `e020_loop.py` plays games of place-all and pass from those blocks until the human cannot
    place, `turns_max`, `games_max` or `sitting_seconds`, and logs each game's start and end.
    A wait is never ignored: a `settle` that does not settle stops its block (`not-ready`), and
    when six `quiet` blocks pass without a quiet board the loop sends nothing more and the sitting
    ends `aborted: not-ready: <reason>` (round 3, R1).
    The screen is read by pixels before each placement attempt, before New Game and during a
    play-out (`runtime/iwp/driver/screens.py`, measured from sitting 20261008T184505Z; round 4).
    On the elimination notice the loop clicks KEEP PLAYING once (the owner's decision), then sends
    nothing and reads the screen while the computers play, within `sitting_seconds`. The winner
    notice (`game-over`, measured from sitting 20261008T195537Z; round 6), in the play-out or at a
    turn's start, ends the game: the `game-end` line says `ended: game-over` and the winner's colour
    word when the score panel shows it by pixels; then CONTINUE once, and the screen is read again.
    New Game is sent only on the title or on the board with its menu row lit. Any other screen where
    the loop would act ends the sitting cleanly: a last screenshot (`session/unknown-screen.png`), an
    `ended: unknown-screen` line with its sha256 in `actions.jsonl`, and no click.
    Sitting 20261008T184505Z (round 3's driver) met the notice at turn 16, tried the placement
    points, clicked New Game where it is not, and ended `aborted: step-failed`; it is exported as
    `E020-r0001`, with no events (no reading pass yet). Sitting 20261008T195537Z (round 5's driver,
    d2e8009) played game 1 for 14 turns, answered the elimination notice with KEEP PLAYING, and
    polled the play-out; about 10 s later the winner notice (red, all 46 countries) came up and was
    read as the board, so the main session interrupted the sitting (`aborted: driver-bug:
    KeyboardInterrupt`, clean recovery). It is exported as `E020-r0002`, with no events.
    The click-driver (`runtime/iwp/driver/clicks.py`) sends every step through `Session.perform`
    and logs every attempted step, failed ones included, to `actions.jsonl`; the watcher
    (`runtime/iwp/driver/watcher.py`) captures the game window on the session's display.
  - The sitting directory is `/mnt/c/Temp/iwp-shots/wine/<YYYYMMDDTHHMMSSZ>/` on the user's machine
    (constraint A): `sitting.json` (the session's status, times, versions, commit, the block
    file's sha256 and the measured binary), `frames/`, `frames-index.jsonl`, `actions.jsonl`,
    `dumps/`, `session/` (the session's before and after screenshots and logs), `watcher.log`, and
    `readings.jsonl`, which the reading pass writes after the sitting: one event per line (game,
    seq, the frames it was read from, and the batch's event fields by pixels, no OCR).
  - `e020_export.py` (`--records --sitting DIR --batch NAME`) turns one sitting directory into
    `runs/E020/<batch>/<run-id>.json` and `evidence/E020/<run-id>.manifest.json`, or writes
    nothing: it requires `sitting.json` as the proof of the sitting and keeps its status and
    provenance, checks every frame against its index, refuses an event that is not complete, not
    of a game the click-driver started, not unique, or whose values are not integers and colour
    words, and takes run ids experiment-wide, never writing over a file.
  - `check_records.py` is the batch checker of Done-when 3, 4 and 6; `tools/check_counts.py` is
    Done-when 8's: complete events by (sitting, game, seq), real games, and per-arm targets per
    claim before `outcomes.json` may declare a claim `corroborated`.
- **Outputs**: run records at `runs/E020/<batch>/<run-id>.json`; evidence manifests at
  `evidence/E020/<run-id>.manifest.json`; per-claim outcomes, when declared, at
  `experiments/E020-wine-first-run/outcomes.json`. The sitting directory is never committed.
- **Walkthroughs**: `walkthroughs/video-walkthrough.md` "Model plays under Wine" is the playbook.
- **Not yet built**: the reading pass (army counters, owners and countries from the frames, by
  pixels). It needs the counters' glyphs, which only a sitting's frames show; until it exists a
  sitting exports with no event, and Done-when 8's floors stay unmet.

## Constraint map

| Constraint | Where it holds |
| --- | --- |
| A locality | the sitting directory under `/mnt/c/Temp/iwp-shots/wine/`; records reference by hash only |
| B static-first | `scenarios.txt` is exactly "Why a run is made"; an unknown batch is refused by name |
| C per-run tagging | `runtime.platform = wine-on-user-machine-iwp-2.0`, `artifact.set/variant`, and `start_state.sha256` = the binary measured before the launch, checked against F019; `files[].class = recording`, and only `evidence-manifest/1` documents pass as manifests |
| D text handling | records carry `kind:role` fields whose values are integers or colour words only; the watcher and click-driver log structural values only |
| E corroboration | the task is not T28 and touches none of its records; the sitting corroborates |
| F tool check | `tools/check_no_originals.py` re-runs the F019 gate over every committed record |
| G per-claim wording | no `spec/` file is touched; amendments go through the per-claim finding |

## Scripts

- `bash tools/wine-driver.sh --batch <name> [--help]` — the dispatcher.
- `bash tools/wine-driver.sh --records --sitting <dir> --batch <name>` — the export.
- `python3 tools/check_counts.py experiments/E020-wine-first-run/scenarios.txt` — the count checker.
- `python3 experiments/E020-wine-first-run/check_records.py` — the batch record/manifest checker.

After the first run this file is append-only. A changed design is a new experiment, or `v2/`.
