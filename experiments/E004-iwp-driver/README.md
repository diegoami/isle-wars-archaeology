# E004 iwp-driver

Copied from the research task's contract when the experiment was created. After the first run this
file is append-only. A changed design is a new experiment, or `v2/`.

- **Task**: T13 (#51), which folds #40's first two items
- **Question**: Does the minimal driver (`runtime/iwp/driver/`, W5a) take *Isle Wars Pro* from a known
  state to a known screen, give one input, observe before and after, terminate and reset, ten times in one
  command, with the same `before` screenshot every time? Does a game killed in the middle of a cycle make
  that repeat `aborted`, leave the prefix at its baseline and let the next repeat complete? How long does a
  kill-terminated repeat take, against E002's 40 to 46 s?
- **Hypotheses**:
  - H0: the driver cannot repeat the cycle: some repeat aborts, or two `before` screenshots differ, or a
    repeat starts from a prefix that the one before did not reset. Distinguished by any control repeat
    that is not `completed`, or `before` hashes that are not all equal.
  - H1: it can. Distinguished by ten `completed` control repeats with one `before` pixel hash and one
    `start_state.sha256`.
  - Side questions: what the time of a repeat is spent on; whether the 30 s that E002 waited after
    `wineserver -k` was the Wine processes or something else.
- **Artifact**: set `iwp-2.0-996e86c5`, variant none. No arm clicks Save as default or plays a game, so
  no run writes a file of the set.
- **Runtime**: `runtime/iwp/driver/run_cycle.py@<commit in each record>`, on Linux (WSL2) with Wine 9.0
  (win32 prefix), Xvfb 800x600x24, xfwm4, xdotool and ImageMagick, the game in a network namespace of
  its own, as in E001 and E002 ([F002](../../findings/F002-iwp-runtime-wine-xvfb.md)). Maximum intervention
  level I1: screenshots of the display and read-only reads of `/proc` and of the game copy.
- **Design**:
  - start state: `S-cold-prefix-title`, the prefix as `setup/iwp/iwp-runtime.sh` leaves it and as each
    repeat's reset leaves it; each record carries the sha256 of the listing of every entry of the prefix.
  - arms (arguments in each record's `actions.args`):
    - `control`: `--repeats 10`. Launch, the title screen by its pixels, `before.png`, the pointer onto
      Options and a click, the Options screen by its pixels, `after.png`, `wineserver -k`, reset.
    - `kill-mid-cycle`: `--repeats 3 --fault kill-game --fault-at after-title --fault-repeat 2`: in repeat 2
      an outside `wineserver -k` kills the game after the title screen.
    - `sigkill-mid-cycle`: `--repeats 3 --fault sigkill-game --fault-at after-input --fault-repeat 2`:
      in repeat 2 the game process is sent SIGKILL after the Options click.
  - n per arm: 10 repeats for `control` in one command; 3 repeats for each fault arm (the second repeat
    is the fault, the third shows the recovery). Stopping rule: none, the list is fixed. A repeat that does not
    end as expected stops the command; it stays in `runs/E004/`.
- **Measurements**: screenshots (screen: ImageMagick `import`, PNG encoded by the driver), the time of each
  stage of a repeat (process: monotonic clock, as observations), the processes of the run on the game side
  and on the display side (process: `/proc`), the prefix before the launch and after the reset (file: size and
  sha256 of every entry, the registry files included).
- **Outputs**:
  - run records: `runs/E004/`;
  - evidence manifests: `evidence/E004/`, bundles in release `E004` (screenshots, `changes.log`, `run.log`,
    `wine.log`);
  - the tables of the records' timings: `measurements/` (rule 20), made by `measurements/make_tables.py`;
  - `findings/F006-iwp-driver-cycle.md`, status `proposed`.

## Scripts

- `runtime/iwp/driver/run_cycle.py [--arm NAME] [--repeats N] [--fault kill-game|sigkill-game] [--fault-at after-title|after-input] [--fault-repeat N]`.
  Needs `IWP_PREFIX`, `IWP_DIR` and `E004_BUNDLES`. It writes the next `runs/E004/E004-r<nnnn>.json` and
  `evidence/E004/E004-r<nnnn>.manifest.json` for each repeat, and refuses to start when runtime, setup,
  tools or formats have uncommitted changes.
- `runtime/iwp/driver/session.py`: the API a later experiment imports.

## Rework round 1 (PR #54)

Appended after round 0's review. The design above is unchanged. The driver changed (a token per command for
the clean-up, a recovery gate, bounds on every wait and helper, an input required between the two
screenshots), and its arms were run again as a new batch, E004-r0030 to r0045 at `a464f266d8ae`, beside the
earlier ones (r0001 to r0016, r0017 to r0029), which stay. Each batch's tables are made once, by
`measurements/make_tables.py FIRST LAST`.

## Rework round 2 (PR #54)

Appended after round 1's review. The design above is unchanged. The driver changed again (every signal
through a marker re-check, every relied-on helper's exit status checked, both sides alive at every stage
boundary, the full seal repeated before launch, the display proven to be this run's own Xvfb's), and its arms
were run again as batch E004-r0062 to r0077 at `74bfcb5`, beside the earlier ones (r0001 to r0061), which stay.
