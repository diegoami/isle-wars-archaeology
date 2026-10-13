# E022 — a single computer-vs-computer exchange (T44)

Single computer-vs-computer exchanges for T28's counts. The E020 sittings gave none: at the E020
capture rate the computers resolve several dice between two frames, so the reader could only call a
pair a `net` (`experiments/E020-wine-first-run/outcomes.json`; 0 exchanges, 55 nets). This
experiment holds the **offline** half — the static-first reading and the reader/checker that turn one
die into a counted exchange. The live sitting is T55 (#222).

## The static-first reading (rule 24, carve-out B)

The artifact this reading pins (F019): set `iwp-2.0-996e86c5`, variant `unregistered`, file
`Islepro.exe`, **sha256 `c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e`**. The
sitting (T55) names that hash in its record's `start_state.sha256` (constraint F); it is the
executable's identity, distinct from the set id above it.

Read from the decompiled Pro Lingo (machine-local, read-only):

- The game's **speed** is a user option, not a patch: `BehaviorScript 500 - SPEEDbehavior` sets a
  global from a click on one of three labelled buttons (fast / normal / slow), `MovieScript 458 -
  getdefaults` defaults it to normal, and it is persisted with the settings.
- **SPD** is a separate flag the movie sets to 0 (`MovieScript 1 - Startmovie`, `BehaviorScript
  463`/`474`); no handler in the extracted casts sets it to 1, so it stays 0.
- `MovieScript 1 - Startmovie` defines the wait handlers `count1/count2/count3/count5/count10/count15/count30/count60`,
  each a busy loop until the Director tick timer passes a *fixed multiple of the speed setting* for
  the speed-sensitive ones (`count10` = 5×speed ticks, `count60` = 30×speed ticks, …; the Director
  tick is 1/60 s). Each returns at once when SPD=1; `count1`, `count2` and `count3` are fixed.
- The computer's per-die path is `MovieScript 337 - computerrolldice`. Its outer loop rolls **R
  dice** (R=1; R=5 when the attacker has more than 40 armies and the defender more than 15), and each
  die writes both counters and calls `updateStage()`. Between outer iterations it calls `count10()`
  **only when SPD=0 and the attacker's remaining count is below 51**; it calls `count1()` when SPD=1.
  Within an R=5 iteration the five dice are separated by a fixed `count1()`.

**Candidate 1 (the slow speed setting) is dropped, and candidate 2's guarantee is bounded (not
"every die is a frame").** The inter-iteration wait is `count10()` = 5×speed ticks **only under
SPD=0 and an attacker below 51 armies**: ~83 ms at fast, 166 ms at normal, 250 ms at slow. At
normal or slow speed with the attacker below 51, that wait exceeds the fast watcher's ~125 ms
(`runtime/iwp/driver/watcher.py`, T42: up to 8 fps), so each die is a frame. But at fast speed
(83 ms), when the attacker reaches 51 armies (no wait at all), or in the R=5 branch (~17 ms per
die), the dice can outrun the watcher and one frame can hold several — so a frame is *not* known to
be a single exchange there.

So the reading's conclusion is a **conditioned** one: a sitting must run at normal or slow speed and
keep the attacking countries below 51 armies for the capture to be known single, and an exchange on
a larger stack may still be missed. The remaining gap the mechanism fills is the reader, not the
capture. T55 runs the sitting under these conditions. Candidate 3 (reading the army counts from
process memory, rule 18 B) is not needed and is left unbuilt.

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
