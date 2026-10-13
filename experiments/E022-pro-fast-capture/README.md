# E022 — a single computer-vs-computer exchange (T44)

Single computer-vs-computer exchanges for T28's counts. The E020 sittings gave none: at the E020
capture rate the computers resolve several dice between two frames, so the reader could only call a
pair a `net` (`experiments/E020-wine-first-run/outcomes.json`; 0 exchanges, 55 nets). This
experiment holds the **offline** half — the static-first reading and the reader/checker that turn one
die into a counted exchange. The live sitting is T55 (#222).

## The static-first reading (rule 24, carve-out B)

Read from the decompiled Pro Lingo (machine-local, read-only; `iwp-2.0-996e86c5`, the unregistered
set). The handlers, by name, and what they do:

- The game's **speed** is a user option, not a patch: `BehaviorScript 500 - SPEEDbehavior` sets a
  global from a click on one of three labelled buttons (fast / normal / slow), `MovieScript 458 -
  getdefaults` defaults it to normal, and it is persisted with the settings. `MovieScript 1 -
  Startmovie` defines the six wait handlers `count1/count2/count3/count5/count10/count15/count30/count60`,
  each a busy loop until the Director tick timer passes a *fixed multiple of the speed setting* for
  the speed-sensitive ones (`count10` = 5×speed ticks, `count60` = 30×speed ticks, …; the Director
  tick is 1/60 s). `count1`, `count2` and `count3` are fixed.
- The computer's per-die path is `MovieScript 337 - computerrolldice`: the outer loop rolls **one
  die** per iteration, writes both countries' counters each die, calls `updateStage()` and then
  `count10()` between iterations. Its only five-dice branch (a large attacker against a large
  defender) rolls five dice separated by a fixed `count1()`.

**Candidate 1 (the slow speed setting) is dropped.** The per-die wait is `count10()` = 5×speed ticks:
250 ms at slow, 166 ms at normal — the slow setting buys only 1.5×, and the five-dice branch's fixed
`count1()` (~17 ms) is speed-independent. Slow speed alone cannot separate the dice from a ~1.4 s
capture.

**Candidate 2 (a faster capture) is picked.** `count10()` is below the interval a fast watcher can
reach: `runtime/iwp/driver/watcher.py` (T42) captures at up to 8 fps (125 ms), so each `updateStage()`
— each die — is a frame. The remaining gap is the reader, not the capture.

Candidate 3 (reading the army counts from process memory, rule 18 B) is not needed once candidate 2
lands and is left unbuilt.

## The mechanism

`single_exchange.py` reads two board readings (`{country: {"army", "owner"}}`) and the seat in turn:
exactly one country's counter is one lower, its owner is unchanged, and the other country of the pair
is the *unique* neighbour of the right side (another seat, if the changed country is the seat's). It
returns the exchange's fields plus a `single:rank` marker, exported as `event:seq` (never `net:seq`).
When more than one neighbour fits, the pair is ambiguous and no exchange is claimed.

## The checker

`tools/check_counts.py --accept-single` accepts the `single:rank` kind and counts the observation as
an exchange; without the flag the kind is unknown and the observation is refused, so it is never
counted. `--experiment`/`--records-root` point the checker at E022 (`experiments/E022-pro-fast-capture/scenarios.txt`,
`runs/E022/`).

## Files

- `scenarios.txt` — the one `[batch synthetic]` block.
- `single_exchange.py` — the mechanism (pure).
- `build_record.py` — writes `runs/E022/synthetic/E022-r0001.json` and its two synthetic frames.
- `tools/tests/test_e022_single_exchange.py` — the offline test (fails on `main`, passes here).
