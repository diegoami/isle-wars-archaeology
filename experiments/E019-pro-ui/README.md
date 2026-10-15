# E019 pro-ui

Copied from the research task's contract when the experiment was created. After the first run this
file is append-only. A changed design is a new experiment, or `v2/`.

- **Task**: T24 (#72) — the UI observations for malpaco: a screen-walk that catalogues what the
  unregistered *Isle Wars Pro* shows, sounds and accepts. **No rule claims**: the catalogue
  (findings/F020-pro-ui-observations.md) is an observation, not a finding about how the game
  decides anything.
- **Question**: What does one screen walk of Pro show for each of the 22 `Q-UI-*` rows of
  `questions/pro-static.md` and for Q-PLY-04 — the screens, the sounds' switch, the hit areas and
  the timings? Two rows are `none found` in the static map (Q-UI-14, no event log; Q-UI-21, the
  board look) and are recorded here by walking the game and looking.
- **Artifact**: set `iwp-2.0-996e86c5`, variant none, for every walk that cannot write a file of
  the set; set `iwp-2.0-de5a82a2` (the same files with both saved-files declared runtime writes,
  as in E002) for the walks that pass through the mid-game loss, which credits a loss and writes
  `xtras/Islepro.skr` (F003): Q-UI-04, Q-UI-11, Q-UI-21. Rule 19: Pro only; nothing here is
  claimed for DOS Isle Wars.
- **Runtime**: `experiments/E019-pro-ui/run_walk.py@<commit in each record>`, on Linux (WSL2) with
  Wine 9.0 (win32 prefix), Xvfb 800x600x24 (Q-UI-19 at the sizes its walk names), xfwm4, xdotool
  and ImageMagick, the game in a network namespace of its own, through T13's driver
  (`runtime/iwp/driver/session.py`), as in E004 ([F006](../../findings/F006-iwp-driver-cycle.md)).
  Maximum intervention level I1: screenshots of the display and read-only reads of `/proc` and of
  the game copy; the recorder's own screen reads are pixels-read only (censuses, text rows, hover
  maps, timed watches) — **no OCR pass anywhere**.
- **Design**:
  - one walk per question: one launch of the game, one `run/1` record per launch under
    `runs/E019/<batch>/`, its evidence manifest under `evidence/E019/<batch>/`. The screenshots
    are release assets of release `E019`, named `<sha256[:16]>-<name>`; **no PNG is committed**
    (tools/check_no_originals.py refuses them; rule 20: originals and media stay out, hashes are
    recorded).
  - batches, in the task's order, one commit each: `title-options` (Q-UI-04, Q-UI-10, Q-UI-19,
    Q-UI-22), `board-pieces` (Q-UI-01, Q-UI-02, Q-UI-03, Q-UI-05, Q-UI-20, Q-PLY-04), `play`
    (Q-UI-08, Q-UI-12, Q-UI-13, Q-UI-15, Q-UI-16), `events-end` (Q-UI-06, Q-UI-07, Q-UI-11,
    Q-UI-14, Q-UI-21), `inputs-sounds` (Q-UI-09, Q-UI-17, Q-UI-18).
  - every click point and rectangle of the walk table (`walks.py`) is measured, with its source
    named: E002's recorded step scripts (F003's runs), the spike's constants (F002's exploration),
    or E002's committed exploration commands; a point the repository does not have (the turn
    menu's CARD and MOVE buttons, the placement plus/minus) stays unmeasured and the walk records
    the gap instead of guessing (CLAUDE.md rule 17).
  - timings are wall-clock readings at **speed = normal**, the unlocked default; each timing
    record observes that the options file equals the shipped one, which is that default (F003's
    P2/P4). A future task can re-time at FAST or SLOW.
  - every board read happens **after the deal** (the deal is random, F018): the walks reach the
    board through the setup screen's Play Game and wait for the computer players' opening turns
    to go quiet, as E002's tour did.
  - the count targets are the rows' own where a row names one ("at least 5 events", "at least
    20 computer turns", "at least 20 attacks", "at least 5 centre moves"), else the walk table's,
    each declared in `walks.py` with the counter that measures it (`shots`, `distinct shots` — the
    distinct raw-pixel hashes among the walk's own screenshots —, `attempts`, `labels`, or a
    composite's counter), and the recorder emits a `count:` observation for every one of them — a
    target the recorder cannot produce is a defect, not a walk.
  - **the recorder writes measurements, never identifications.** Three rows' words need an
    identification the pixels cannot make, and their targets are proxies: Q-UI-06's events and
    Q-UI-07's centre moves are counted as `flash candidates` / `centre-flash candidates` (poll ticks
    in which a watched region changed over a large share of its pixels, each one shot; a redraw or
    either transition of a flash makes one), and Q-UI-13's computer turns as `computer turns
    derived from passes` (the walk's own PASS clicks the game took, times the three default
    computer seats, F003). Each carries a `count note` naming the substitution, and their F020
    entries can only be `narrowed`. The absence tour (Q-UI-14) records the screenshots it took and
    nothing more; whether any shows an event log is the catalogue's reading of them. Each record's
    `observation` is the recorder's summary of what it measured (the screenshots, counts, reads
    and timing observations), with the reading left to F020.
  - a target is met by one completed record: counts are never added across records, so a repeat
    is not a second instance. A walk that sees fewer records fewer and is re-run — a re-run writes
    new records beside the old ones and says which it cites; nothing is padded.
  - every walk measures the display it ran on (the pixel count of one capture of the whole
    display, beside the size it asked for); Q-UI-19 is covered only by a completed record at each
    of its four sizes whose measured pixel count equals the size asked for.
  - every timed watch polls all its regions together in one loop (a shared budget spent by
    sequential per-region loops starved every region but the first: round 2's R4).
  - the Quit path stops at the unregistered notice: T13's driver terminates by kill, so Exit Game
    is never clicked inside a recorded walk. The Soleau Games label is a refused rectangle
    (`runtime/iwp/spike/steps.py`); its screens are never walked.
  - Q-UI-17's sound half: the driver runs with audio off (no sound device in its display
    namespace), so the record carries the sound switch's reaction on the screen and the note that
    sound capture needs a driver change.
- **Measurements**: screenshots (the driver's captures, by hash), the recorder's pixel reads
  (quantised colour censuses, greyscale/luminance censuses, text-row heights, hover maps, timed
  watches with change timestamps), the session's own stage timings and seal observations — all as
  `run/1` observations, raw only.
- **Outputs**:
  - run records: `runs/E019/<batch>/`;
  - evidence manifests: `evidence/E019/<batch>/`, bundles in release `E019`;
  - the catalogue: `findings/F020-pro-ui-observations.md`, status `proposed`, no rule claims;
  - the check: `python3 experiments/E019-pro-ui/check_ui_catalogue.py`. It fails until the walks
    have run and F020 is turned from their records (T39, #117); T24's Done-when runs its checks on
    the recorder's own output, end to end with a fake session (`tests/test_e019_ui_catalogue.py`).

## Scripts

- `walks.py`: the per-question walk table (batches, targets, measured points and regions, notes)
  and the parser of the questions map's rows.
- `pixels.py`: the pixels-read helpers (census, greyscale census, text rows, hover grids, change
  shares). Pure functions over raw RGB bytes.
- `records.py`: the record and manifest shapes, the batch paths, the arm/question mapping.
- `run_walk.py`: the command. `--question Q-UI-06` (repeatable) or `--batch events-end`. Needs
  `IWP_PREFIX`, `IWP_DIR` and `E019_BUNDLES`, as E004 does; refuses to start when runtime, setup,
  tools, formats or this folder have uncommitted changes. Its timed loops run on its own `CLOCK`
  and `SLEEP`, and `run_walk()` takes the session factory and the records' root, so the tests drive
  every walk with a fake session.
- `check_ui_catalogue.py`: maps every recorded file to its question id and checks every record
  (any status: identity, place, manifest, citations) and every completed one (the seal, the
  fields of `required_fields()`, the outputs of `required_outputs()`, the observation summary,
  the measured display size, one count per record), then the coverage, the targets and F020.

## #239 — bounded Q-UI-16 attack phase

The Q-UI-16 walk keeps its unchanged target of 20 attacks and its existing eight-turn / three-
exchange bounds. Its strict path is separate from the other composites: it accepts an attack only
after the measured human attack-ready probe (the existing human board-menu and score signals plus
the bounded red population in the existing phase panel), after a successful input, and after the
watched attack-panel rectangle changed. A generic screen change elsewhere is not enough.

Placement refusal, capture or move-in, early combat end, terminal screens, and unsupported states
stop the walk before another attack or PASS. If a later attack input is refused or its watched panel
does not change, earlier valid attacks remain counted but the strict helper returns failure, so the
composite stops before QUIT ATTACK, PASS, or another placement. After an accepted PASS, the walk
requires an observed departure, the existing quiet settle, and a fresh human board-menu reading
before another placement.
The probe is a bounded measured population, not a universal phase classifier; no Q-UI-16 run record
or F020 observation is fabricated by this repair.

## Division of work (the task file's)

The implementer writes the recorder, the walk table and the check (T24); the main session runs
the walks on the install ([C3]) and the records are turned into the catalogue in T39 (#117), by
the owner's decision of 2026-10-08 that split T24. No record is ever fabricated: until a walk has run, its question has
no record, and the check fails naming it.
