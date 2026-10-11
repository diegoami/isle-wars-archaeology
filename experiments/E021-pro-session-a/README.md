# E021 — Session A by a scripted human seat (T45)

The original *Isle Wars Pro* binary under Wine on the user's machine (rule 18's carve-out), with
the human seat played by a script that attacks on purpose: the playbook's Session A
(`walkthroughs/video-walkthrough.md`, "What to play") for F011's human combat claims Q-CMB-01,
02, 03, 08, 09 and 10. Static first (rule 24): F011's reading of the Lingo names the gate, the
exchange, the battle's exits and the forfeit. A sitting records what the running game shows.

## The cases

| Case | Attack | Cells | Claim | Met by |
| --- | --- | --- | --- | --- |
| even | attacker N in {2, 4, 8, 12} vs N−1, N, N+1, N+2 | 16 | Q-CMB-01 | the game's answer to the order: a battle, or a refusal (the attacker's click changed the bottom bar and no battle came up); an order with neither is `unresolved` and meets nothing |
| underdog | attacker 4, 8, 12, 20 vs a strictly stronger defender | 4 | Q-CMB-02 | the same |
| tiny | attacker 1, 2, 3 vs a defender of 1 | 3 | Q-CMB-03 | the same (an attacker of 1 refused is the observation) |
| quit | the quit-attack button mid-battle | 2 | Q-CMB-08 | a quit-attack press after an exchange the board showed, confirmed by a reading (battle panel gone, counts unchanged) |
| lost | attacks that fail; what happens to the turn | 5 | Q-CMB-09 | the attacking country changing hands, with the seat after |
| busy | turns with 3 or more attacks; what ends each | 10 | Q-CMB-10 | a turn with 3 or more fights (battles with an exchange the board showed), with what ended it |

Each event meets at most one cell of a row. A case whose own action fails five times in a row is
dropped for the sitting (`case-dropped`). After three turns in a row of one game with no needed
cell on the board and no attack opened, the game is abandoned (`game-abandoned`, then New Game
from the board; the loss it credits is handled as E020 handles a credited loss), and a new game
starts. With 10 or more human countries the Scoreboard does not show (F003): sitting 20261011T142906Z's
second abandon went straight to the Game Options screen. The loop recognises that screen by pixels
(`boardview.options_up`), ends the game as `abandoned-no-scoreboard` with no loss credited, restores the
shipped scoreboard file, and starts the next game with block `options-play` (the clicks of `new-game` after
its first, which the abandon already sent); any other screen after the abandon still ends the sitting.
A turn that grew a stack towards a needed attacker size (its `gap` smaller than that country's smallest
earlier one in the game; `growing` on the `turn-end` line) does not count as a no-fit turn, so a game is
not abandoned while a stack is on its way; a stack that stops growing counts again.
When no needed cell is reachable on the board, the placement still names a target (fix #178; sitting
20261011T163105Z, 26 of 40 met, where the open even and underdog rows needed stacks of 8, 12 or 20 and every
`place-target` read no case and gap 0, so games 2 to 6 were abandoned at turn 3 with no fights): the strongest
country with an adjacent enemy is grown towards the smallest attacker size an unmet even or underdog cell
still asks for above its armies (`place-target` then carries `case`, `cell` and the `gap`). The gap is kept per
country and target size, so a stack that passes 8 and heads for 12 is still growing; a stack that stops growing,
or one with no open size above it, is abandoned after three turns as before. Busy's drop count is per game: at each
game start busy's failures are cleared and busy is aimed at again (the same sitting dropped it at game 1 turn 6
for the rest of the sitting); the other cases keep the sitting-wide count.
A turn can start with the card trade-in offer instead of the placement row (fix #175; sitting 20261011T154319Z,
game 1 turn 10): the game shows two buttons in the middle panel when the hand holds a valid match, after income and
before placement. F014 (Q-BON-07, C-CRD-05) reads it as the human's choice, with a second button that skips it, and
finds no forced trade (the only forced card step is a full hand's discard, C-CRD-04). Every reading carries
`offer` (`boardview.offer_up`, a pixel check of the two buttons, traced to frames by name and sha256); at a turn's
start, and once more after a placement that picked nothing, the loop sends block `card-decline` (one plain click on
the red decline button), waits for the offer to go, logs `card-offer` (`declined` 1) and places as usual. An offer
still up after the wait is treated as forced: `card-offer` with `forced` 1 and the sitting ends cleanly as
`card-trade-forced`, with no further click. The loop never trades; a trade path (picking three matching cards) is a
follow-up. The card count is not read (no reader for it), so the line has none.
Exact stack sizes (fix #180; the owner, 2026-10-11, "Plan A"): ALL puts the whole pool on one country, so a stack
jumped past 8 and 12 (sitting 20261011T170700Z grew one to 27, which no open cell fits). The placement panel also holds
a + and a - button (F013 Q-REI-03: `plus2` adds one to the counter, capped at the pool; `min2` takes one off; `Pall2`
sets it to the whole pool; `place2` moves it into the selected country), so when the placement has a target with a
`gap` above 0 and a named size case, the loop selects the country, sends block `place-plus` once per army (+ at
373,543, `walkthroughs/coordinates.md`), then block `place-only` (PLACE). If the turn menu shows, the pool is spent;
if the placement row is still up, the rest goes with `place-commit` (ALL, PLACE) on a second country, chosen by
`cases.rest_choices`: never the stack just sized, never a needed attacker showing its size, an interior country first,
then a frontier country (the phase ends only at pool zero, so the rest must go somewhere). The list is asked before the
exact path is taken: with no safe second country the turn keeps ALL and PLACE on the target (`place-exact` with `exact` 0
and `reason` `no-safe-rest`). If the exact path was taken and no candidate can be selected, or the row is still up after
the rest, the sitting ends cleanly as `placement-stuck` with no further click (E020's `place-any` is not used for the rest:
it could pick the target). Lines: `place-exact` (`exact`, `country`, `gap`, `plus`, `rest_to`) and, from the first reading after the
placement, `place-landed` (`landed` 1 when the stack holds its armies before plus min(gap, pool), the pool being what
the human's countries gained in all; 0 otherwise). `landed` never credits a cell: attacks are picked from the board
alone. With no gap or no named case the placement is today's ALL and PLACE. Fix #178's bounds are unchanged.
`measurements/CORRECTIONS.md` says why progress-r01's
busy 10/10 is not met, and what the count requires since. The deal is random (F018): a cell no board offers
stays unmet, and `measurements/progress-r<nn>.json` lists it under `unmet`; it is never forced.

## Files

- `cases.py`: the table and the pure picker (which pair, which country to grow).
- `points.py`: the 44 proven click points (countries 11 and 15 have none, #120, and are never clicked).
- `boardview.py`: the live reader, one capture through the session, read by E020's reader.
- `e021_loop.py`: E020's loop with the human's turn replaced (placement, attacks, PASS).
- `session-a.steps`: the step blocks; the country clicks between them are made by the loop.
- `e021_export.py`: one sitting directory to `runs/E021/session-a/E021-rNNNN.json` and
  `evidence/E021/E021-rNNNN.manifest.json`.
- `e021_progress.py`: the progress number over every E021 record (a new `r<nn>` each time).
- `launcher.py`, `scenarios.txt`: the sitting and its one batch, `session-a`.

E020 (`experiments/E020-wine-first-run/`) is imported, never edited.

## A sitting (the main session's `[C3]` lines, on the user's machine)

```bash
source /tmp/iwp-env.sh            # IWP_DIR, IWP_PREFIX, IWP_MACHINE
export E021_BUNDLES=...           # the session's bundle folder for E021 (machine-local)
export E021_TEMPLATES=/mnt/c/Temp/iwp-shots/wine/reader-templates.json   # the default
python3 experiments/E021-pro-session-a/launcher.py --batch session-a --help
python3 experiments/E021-pro-session-a/launcher.py --batch session-a
python3 experiments/E021-pro-session-a/launcher.py --records --sitting /mnt/c/Temp/iwp-shots/wine/<sid> --batch session-a
python3 experiments/E021-pro-session-a/e021_progress.py
python3 tools/check_no_originals.py
```

Commit the record, the manifest and the new progress file together, then push. The sitting
refuses to start (nothing is launched) when the digit templates cannot be loaded or the driver's
code has uncommitted changes.

## What to read from a first sitting (DW3)

`sitting.json`'s `loop` and the record's step-0 counters: `exchange-clicks`, `clicks-one-army`
(the two countries lost one army together), `clicks-several-armies`, `clicks-no-change`,
`clicks-unread` and `clicks-unisolated` (the reading after the click boxed another seat, so the
count is unknown: mostly the click that lost a country, after which the turn passes by itself). Each `exchange-click` group holds both countries before and after one click and
`counter:lost`, the armies the two lost together: their total is conserved across a capture's
move-in (Q-OWN-01) and a failure's hand-over (Q-CMB-09), so it counts exchanges at one army each
(Q-CMB-07). F011 expects five exchanges per click only when the attacker holds more than 35 and the
defender more than 15. Any other click with more than one army lost means one click is not one
exchange: the task file's hazard, for the main session and the owner to decide.

## Not yet measured (offline-only assumptions, for the first sitting to check)

- The + button at 373,543 registers one army per click at the loop's pace (a plain `click` each, no extra delay),
  and the counter starts at zero after a country is selected (F013's reading; the frame cited in `coordinates.md`
  shows the counter after ALL). `place-landed` reads 0 if either fails, and the next sitting says which.
- The turn menu's attack button at 303,530 and the battle's at 337,531 (the spike's and the tour's
  points), the cancel button at 405,530, and the target panel changing when a target is taken.
- A refusal of the attacker leaves no prompt that `attack-cancel` does not clear, and its message
  changes the bottom bar (`watch 0 495 800 105`). If the message shows on the board instead, every
  refusal is recorded `unresolved` and no size cell is met by one: widen the watch then.
- The score panel boxes the next seat only once its turn has begun, so a reading that still boxes
  blue holds the human's battle alone.
- The session's screenshots decode with E020's PNG reader and hold the stage at the origin the
  session recorded.
- `boardview.UNREAD_LIMIT` (6) is a guess: a turn's reading with more unread countries ends the
  sitting cleanly.
