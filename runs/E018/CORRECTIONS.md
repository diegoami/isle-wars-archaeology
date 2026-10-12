# E018 per-question outcomes

The run records in this folder are raw and immutable (CLAUDE.md rule 20). Where one is wrong,
the correction is written here and in the finding that cites it, and the record stays as it was
written. This file is the per-question outcome index for the `IP1 025.mp4` sitting
(2026-10-08, owner-driven Bandicam capture, 6:25, video sha256
`8f7e0655ee251660cdd99ed031454fefdd186f9e6be0374c9ca430d0e15d2e26`).

Per-question outcomes follow the `walkthroughs/f011-questions.md` convention
(`corroborated` / `narrowed` / `unestablished`).

## Q-BON-07 — trade-in only on a 3-of-a-kind match

- **Status:** narrowed
- **Static claim:** C-CRD-05 (spec/cards.md:18). A trade-in is at most one set per turn, a
  match is three cards of one tradeable kind (or 2 + wildcard up to 2 wildcards).
- **This run:** With 1 card in hand (video offsets 115.5s and 208.0s) and 2 cards in hand
  (offsets 299.5s and 328.5s), no trade-in screen was ever inserted between the action bar
  and the placement bar. The help-screen text at 239.0s reads "three cards" for the trade-in
  shape. The card screen at 115.5s shows a single +5 card and a CONTINUE button — a draw
  without a match, with no trade-in entry.
- **Cited by:** E018-r0001 (master), E018-r0002 (Q-BON-07-specific).
- **Why narrowed, not corroborated:** the 3-of-a-kind match path was not exercised at runtime
  in this 6:25 clip. The static reading and the help-text evidence are consistent, but the
  trade-in screen itself was not visited.

## Q-BON-05 — a card is given for a capturing turn

- **Status:** corroborated
- **Static claim:** C-CRD-03 (spec/cards.md:16). One draw per capturing turn for the human
  (on a card screen at end of turn) and the computer (after its move) alike.
- **This run:** Blue's `Cards: 0` at offset 9.5s and 29.5s. Blue's `Cards: 1` first appears
  at offset 115.5s on a `Blue's Cards` screen with a `5 ARMIES` badge — drawn after Blue
  captured (Blue went from 9 armies at 9.5s to 10 armies at 60s, with combat in between). One
  draw per capturing turn is consistent with what this clip shows.
- **Cited by:** E018-r0001.

## Q-BON-06 — hand limit and discard-on-draw

- **Status:** narrowed
- **Static claim:** C-CRD-04 (spec/cards.md:17). Hand limit 5; a draw into a full hand forces
  one discard first.
- **This run:** No hand ever reached 5 in this clip (the max was 3 across all seats). The
  full-hand discard notice was not exercised. The 5-card limit is textually confirmed by the
  help screen at 239.0s: "You can only hold 5 cards in your hand at once. If you have more
  then 5, the computer will ask which card you want to discard."
- **Cited by:** E018-r0001.

## Q-MOV-01 — moves per turn, what ends the turn

- **Status:** narrowed
- **Static claim:** C-MOV-01 (spec/movement.md). Human gets multiple moves per turn.
- **This run:** One explicit move action observed (`Moving from 41 to 43` at 328.5s). Far
  short of the 10-turn count target.
- **Cited by:** E018-r0001.

## Q-SET-04 — the options screen

- **Status:** unestablished
- **Static claim:** C-SET-01, C-SET-04 (spec/setup.md). Six controls on the options screen.
- **This run:** The owner did not visit the Options screen in this 6:25 recording.

## Q-CMB-01..11 — combat corroboration (whole family)

- **Status:** unestablished
- **Static claim:** C-CMB-01..11 (spec/combat.md). Per-arm count targets are 16 (human) +
  100+ (computer) for Q-CMB-01..03, 100-500 exchanges for Q-CMB-04..07, 10-30 for Q-CMB-08..10,
  500 for Q-CMB-11.
- **This run:** Two attack exchanges visible in this clip (Green's `Country 38 Attacks 33, 6
  Against 1` at ~90s; Blue's `Country 8 Attacks from 6, 3 Against 2` at ~150s) and one move
  action. No full attack resolution visible at readable density. Per-arm count targets are far
  out of reach for a 6:25 clip; this recording is too short for statistical corroboration of
  any C-CMB claim. The recording is not Session-B candidate material at this length — it is
  far under the natural-play accumulation threshold.

## Honest scope statement for this sitting

The owner's remark "gave up after two minutes" describes the owner's patience, not the
recording length. The recorder captured 6:25 of game time, including several turns of
computer-vs-computer play after Blue was defeated. Useful for the moment-of-truth UX
questions (card screen, help text, action bar) and for a couple of single-shot observations,
**not** for any of the count-based corroborations T28 needs. To answer the Q-CMB family and
the C-AI-09 quality claim, longer sittings are required — the playbook's Session B (let the
computers fight) and Session A (deliberate boundary cases) are the right path, not a longer
recording of the same game.

## Re-reads (rule 20)

A re-read of `IP1 025.mp4` writes a new record beside this one (e.g. `E018-r0010`) with its
own frame hashes, and the new record says which record it cross-references. The original
record is left unchanged.

---

# IP1 026 sitting

The second owner sitting (2026-10-10, owner-driven Bandicam capture, 17:20, video sha256
`0591d9595aac9603d66ed7c54c289005f22ec8d9ab4af631ab2a75e08f651c1a`, Bandicam 8.3.0.2533 per the file's
encoder tag; frame timestamps are irregular, 18456 frames in 1039.57 s, so offsets are container
timestamps, not frame numbers). One game from the options screen to the end screen: 55 player-turns
(13 human, 42 computer), 111 attacks (17 human, 94 computer), the human seat eliminated at 17:04.0 (by
attack 111) and the game over at 17:09.6, with the end dialog at 17:10.0.

Records, all immutable, `runtime.platform` `windows-native-bandicam`:

- `E018-r0003`: the 111 attacks (counter states, endings, capture splits and move-ins), nine frames.
- `E018-r0004`: the 55 turn starts (territory counts, cards, placement message), the trade-ins, the
  discards, the two event messages, seventeen frames.
- `E018-r0005`: the options screen, the opening deal, the human move-ins and move, the computer moves, the
  elimination prompt and the end, ten frames.

Frames are in the bundle store by hash, listed in `evidence/E018/E018-r0003..5.manifest.json`; the video and
the frames are never committed (rule 18). Everything was read by pixels (region comparison against the
counter panel, no OCR). Four checks backed the readings: every one of the 360 counter steps is a single
loss on one side (none was missed or double; three repeated, unchanged counter states in attacks 19, 58 and 83 are not exchanges); for all 82 captures the two country counters after the capture
add up to the attacker's armies at the capture; 72 states of 24 attacks were re-read by eye against the
readings and matched; and every attack's two countries are neighbours in the F017 border tables.

One correction to a record's label (rule 20: the record stays as written). `E018-r0005` step 55 names the
frame at 17:03.2 as the human seat eliminated; that frame shows the seat's last country, 0.8 s before attack
111 captured it. The elimination is at 17:04.0, the prompt at about 17:04.5.

Counts this sitting adds to the per-claim totals (constraint E): 442 exchanges (360 read from counter
steps, 82 capture exchanges inferred from the defender's last army), 111 attacks, 55 turn starts with income,
45 capturing turns with the card count before and after, 5 trade-ins, 8 moves.

Outcome words follow `walkthroughs/f011-questions.md`: `corroborated` when the count target is met and play
matches the static claim, `narrowed` when it matches in the part played, `unestablished` when nothing in the
video bears on it.

## The attacks: every one, before and after

`#` is the order in the video (`r0003`, step = `#`). `offset` is the first counter state. `seat` is the
attacking seat, `C` computer, `H` human. `before` is attacker/defender armies as the counter first shows
them (read from the country counters when the message strip had not yet appeared); `after` is the last
state, or, for a capture, the attacker's armies at the capture with the defender at 0, then the split
(computer: armies left in the attacker's country and armies placed in the captured country; human: the
move-in the owner chose and what the attacker keeps). A stop or quit leaves both countries with their owners.

| # | offset | seat | from>to | before | after | ending |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 00:30.167 | Yellow C | 4>5 | 7/3 | 4/0, then keeps 3 gets 1 | capture |
| 2 | 00:36.567 | Red C | 46>44 | 6/3 | 3/1 | stop |
| 3 | 00:42.200 | Green C | 25>26 | 7/1 | 3/1 | stop |
| 4 | 00:43.433 | Green C | 20>21 | 3/2 | 2/1 | stop |
| 5 | 01:01.833 | Blue H | 3>2 | 6/1 | 4/0, then in 1 keeps 3 | capture |
| 6 | 01:16.967 | Yellow C | 7>6 | 7/3 | 4/0, then keeps 3 gets 1 | capture |
| 7 | 01:25.033 | Red C | 22>20 | 3/2 | 3/1 | stop |
| 8 | 01:25.700 | Red C | 46>44 | 6/1 | 5/0, then keeps 3 gets 2 | capture |
| 9 | 01:31.833 | Green C | 25>26 | 7/1 | 7/0, then keeps 4 gets 3 | capture |
| 10 | 01:58.500 | Blue H | 42>41 | 7/1 | 5/0, then in 1 keeps 4 | capture |
| 11 | 02:16.633 | Blue H | 42>43 | 4/1 | 2/1 | quit |
| 12 | 02:29.467 | Yellow C | 32>31 | 11/3 | 2/1 | stop |
| 13 | 02:31.833 | Yellow C | 17>18 | 3/1 | 2/1 | stop |
| 14 | 02:36.933 | Red C | 14>15 | 5/2 | 4/0, then keeps 3 gets 1 | capture |
| 15 | 02:38.900 | Red C | 22>23 | 6/3 | 5/0, then keeps 1 gets 4 | capture |
| 16 | 02:46.333 | Green C | 27>28 | 4/1 | 4/0, then keeps 3 gets 1 | capture |
| 17 | 02:47.967 | Green C | 30>32 | 5/2 | 4/0, then keeps 1 gets 3 | capture |
| 18 | 02:49.900 | Green C | 24>23 | 7/4 | 6/0, then keeps 3 gets 3 | capture |
| 19 | 03:03.733 | Blue H | 39>37 | 6/1 | 2/0, then in 1 keeps 1 | capture |
| 20 | 03:35.467 | Yellow C | 12>11 | 10/2 | 6/0, then keeps 3 gets 3 | capture |
| 21 | 03:42.400 | Red C | 19>18 | 6/1 | 6/0, then keeps 2 gets 4 | capture |
| 22 | 03:43.967 | Red C | 18>17 | 4/2 | 4/0, then keeps 1 gets 3 | capture |
| 23 | 03:50.833 | Green C | 32>33 | 5/2 | 3/1 | stop |
| 24 | 03:51.867 | Green C | 31>33 | 4/1 | 2/1 | stop |
| 25 | 03:52.667 | Green C | 24>33 | 4/1 | 4/0, then keeps 3 gets 1 | capture |
| 26 | 04:05.033 | Blue H | 42>40 | 6/2 | 5/0, then in 1 keeps 4 | capture |
| 27 | 04:13.667 | Blue H | 42>43 | 4/1 | 3/1 | quit |
| 28 | 04:28.500 | Yellow C | 12>10 | 6/3 | 2/1 | stop |
| 29 | 04:30.000 | Yellow C | 11>10 | 5/1 | 5/0, then keeps 3 gets 2 | capture |
| 30 | 04:41.000 | Green C | 34>35 | 11/2 | 11/0, then keeps 3 gets 8 | capture |
| 31 | 04:42.867 | Green C | 35>36 | 8/2 | 6/0, then keeps 1 gets 5 | capture |
| 32 | 04:45.100 | Green C | 36>37 | 5/1 | 4/0, then keeps 3 gets 1 | capture |
| 33 | 05:02.867 | Blue H | 39>37 | 5/1 | 5/0, then in 4 keeps 1 | capture |
| 34 | 05:24.533 | Blue H | 42>43 | 3/1 | 2/1 | quit |
| 35 | 05:34.767 | Yellow C | 10>9 | 9/3 | 4/0, then keeps 1 gets 3 | capture |
| 36 | 05:43.267 | Red C | 15>16 | 7/1 | 6/0, then keeps 3 gets 3 | capture |
| 37 | 05:45.033 | Red C | 22>20 | 4/1 | 3/1 | stop |
| 38 | 05:45.633 | Red C | 17>20 | 7/1 | 6/0, then keeps 5 gets 1 | capture |
| 39 | 05:54.267 | Green C | 43>42 | 29/2 | 26/0, then keeps 3 gets 23 | capture |
| 40 | 05:56.567 | Green C | 42>39 | 23/1 | 20/0, then keeps 1 gets 19 | capture |
| 41 | 05:58.867 | Green C | 39>40 | 19/1 | 18/0, then keeps 4 gets 14 | capture |
| 42 | 06:00.667 | Green C | 39>38 | 4/1 | 4/0, then keeps 3 gets 1 | capture |
| 43 | 06:02.267 | Green C | 40>41 | 14/1 | 14/0, then keeps 4 gets 10 | capture |
| 44 | 08:32.567 | Blue H | 37>38 | 8/1 | 7/0, then in 1 keeps 6 | capture |
| 45 | 09:05.233 | Yellow C | 5>3 | 4/3 | 4/0, then keeps 3 gets 1 | capture |
| 46 | 09:07.267 | Yellow C | 9>14 | 18/3 | 16/0, then keeps 3 gets 13 | capture |
| 47 | 09:09.667 | Yellow C | 14>46 | 13/3 | 11/0, then keeps 3 gets 8 | capture |
| 48 | 09:11.967 | Yellow C | 46>45 | 8/4 | 4/0, then keeps 3 gets 1 | capture |
| 49 | 09:18.500 | Red C | 44>45 | 5/1 | 5/0, then keeps 4 gets 1 | capture |
| 50 | 09:24.667 | Green C | 43>8 | 12/5 | 11/0, then keeps 4 gets 7 | capture |
| 51 | 09:27.233 | Green C | 8>6 | 7/1 | 4/0, then keeps 3 gets 1 | capture |
| 52 | 09:29.367 | Green C | 40>37 | 16/6 | 10/0, then keeps 1 gets 9 | capture |
| 53 | 09:43.633 | Blue H | 2>3 | 3/1 | 3/0, then in 1 keeps 2 | capture |
| 54 | 10:20.200 | Yellow C | 4>6 | 7/1 | 6/0, then keeps 1 gets 5 | capture |
| 55 | 10:22.033 | Yellow C | 6>8 | 5/3 | 4/0, then keeps 1 gets 3 | capture |
| 56 | 10:35.067 | Red C | 44>46 | 7/3 | 7/0, then keeps 4 gets 3 | capture |
| 57 | 10:41.233 | Green C | 39>38 | 17/1 | 17/0, then keeps 14 gets 3 | capture |
| 58 | 10:56.633 | Blue H | 3>5 | 5/3 | 2/3 | quit |
| 59 | 11:14.233 | Yellow C | 14>18 | 11/1 | 8/0, then keeps 3 gets 5 | capture |
| 60 | 11:16.533 | Yellow C | 13>15 | 5/3 | 3/3 | stop |
| 61 | 11:21.900 | Red C | 15>14 | 6/3 | 2/3 | stop |
| 62 | 11:23.033 | Red C | 17>18 | 11/5 | 7/0, then keeps 3 gets 4 | capture |
| 63 | 11:26.100 | Red C | 18>14 | 4/3 | 3/1 | stop |
| 64 | 11:32.667 | Green C | 23>22 | 24/3 | 21/0, then keeps 3 gets 18 | capture |
| 65 | 11:35.233 | Green C | 22>19 | 18/2 | 10/0, then keeps 1 gets 9 | capture |
| 66 | 11:38.533 | Green C | 19>17 | 9/3 | 3/2 | stop |
| 67 | 11:51.400 | Blue H | 3>5 | 6/3 | 3/0, then in 1 keeps 2 | capture |
| 68 | 12:12.833 | Red C | 20>19 | 7/3 | 3/0, then keeps 1 gets 2 | capture |
| 69 | 12:20.267 | Green C | 22>21 | 17/1 | 17/0, then keeps 2 gets 15 | capture |
| 70 | 12:21.900 | Green C | 21>20 | 15/1 | 15/0, then keeps 1 gets 14 | capture |
| 71 | 12:23.633 | Green C | 43>8 | 7/5 | 5/0, then keeps 4 gets 1 | capture |
| 72 | 12:26.400 | Green C | 20>16 | 14/1 | 14/0, then keeps 2 gets 12 | capture |
| 73 | 12:39.167 | Blue H | 5>6 | 5/1 | 5/0, then in 1 keeps 4 | capture |
| 74 | 12:52.800 | Yellow C | 4>6 | 7/1 | 7/0, then keeps 4 gets 3 | capture |
| 75 | 12:54.400 | Yellow C | 7>5 | 9/4 | 7/0, then keeps 3 gets 4 | capture |
| 76 | 12:57.000 | Yellow C | 13>1 | 5/1 | 3/1 | stop |
| 77 | 13:02.767 | Red C | 18>14 | 8/1 | 4/0, then keeps 1 gets 3 | capture |
| 78 | 13:12.500 | Green C | 16>15 | 37/4 | 28/0, then keeps 2 gets 26 | capture |
| 79 | 13:16.333 | Green C | 15>14 | 26/3 | 22/0, then keeps 3 gets 19 | capture |
| 80 | 13:19.167 | Green C | 14>18 | 19/1 | 18/0, then keeps 3 gets 15 | capture |
| 81 | 13:21.000 | Green C | 18>17 | 15/2 | 14/0, then keeps 2 gets 12 | capture |
| 82 | 13:23.033 | Green C | 17>19 | 12/2 | 10/0, then keeps 9 gets 1 | capture |
| 83 | 13:25.133 | Green C | 43>44 | 6/4 | 3/2 | stop |
| 84 | 14:06.567 | Blue H | 1>13 | 9/3 | 7/0, then in 6 keeps 1 | capture |
| 85 | 14:22.633 | Yellow C | 6>8 | 3/1 | 3/0, then keeps 1 gets 2 | capture |
| 86 | 14:24.267 | Yellow C | 5>3 | 7/6 | 5/6 | stop |
| 87 | 14:28.533 | Red C | 45>23 | 6/3 | 3/1 | stop |
| 88 | 14:35.300 | Green C | 43>8 | 5/2 | 2/1 | stop |
| 89 | 14:36.467 | Green C | 14>9 | 29/3 | 18/0, then keeps 3 gets 15 | capture |
| 90 | 14:40.567 | Green C | 9>11 | 15/1 | 4/0, then keeps 3 gets 1 | capture |
| 91 | 14:59.367 | Blue H | 13>11 | 10/1 | 10/0, then in 9 keeps 1 | capture |
| 92 | 15:08.967 | Blue H | 11>9 | 9/3 | 9/0, then in 3 keeps 6 | capture |
| 93 | 15:40.967 | Yellow C | 10>11 | 3/1 | 3/0, then keeps 2 gets 1 | capture |
| 94 | 15:42.567 | Yellow C | 7>9 | 5/3 | 3/1 | stop |
| 95 | 15:47.367 | Red C | 44>43 | 4/2 | 3/1 | stop |
| 96 | 15:48.167 | Red C | 45>23 | 7/3 | 6/0, then keeps 3 gets 3 | capture |
| 97 | 15:55.600 | Green C | 22>23 | 19/3 | 18/0, then keeps 1 gets 17 | capture |
| 98 | 15:57.733 | Green C | 23>45 | 17/3 | 14/0, then keeps 3 gets 11 | capture |
| 99 | 16:00.300 | Green C | 45>46 | 11/4 | 4/0, then keeps 3 gets 1 | capture |
| 100 | 16:21.967 | Blue H | 13>11 | 10/1 | 2/1 | quit |
| 101 | 16:35.767 | Yellow C | 5>3 | 7/6 | 3/3 | stop |
| 102 | 16:37.567 | Yellow C | 7>9 | 7/1 | 5/0, then keeps 3 gets 2 | capture |
| 103 | 16:42.167 | Red C | 44>45 | 5/3 | 2/2 | stop |
| 104 | 16:48.600 | Green C | 14>9 | 4/2 | 2/2 | stop |
| 105 | 16:49.333 | Green C | 43>8 | 33/5 | 30/0, then keeps 3 gets 27 | capture |
| 106 | 16:52.433 | Green C | 8>6 | 27/1 | 27/0, then keeps 3 gets 24 | capture |
| 107 | 16:54.033 | Green C | 15>13 | 5/2 | 4/0, then keeps 3 gets 1 | capture |
| 108 | 16:56.000 | Green C | 6>5 | 24/3 | 18/0, then keeps 3 gets 15 | capture |
| 109 | 16:59.067 | Green C | 5>3 | 15/3 | 13/0, then keeps 3 gets 10 | capture |
| 110 | 17:01.367 | Green C | 3>2 | 10/2 | 7/0, then keeps 3 gets 4 | capture |
| 111 | 17:03.700 | Green C | 2>1 | 4/1 | 4/0, then keeps 1 gets 3 | capture (last country of the seat) |

## Combat

### Q-CMB-01 (C-CMB-01) — who may attack, human and computer

- **Status:** narrowed
- **Static claim:** a human needs at least 2 armies and at least as many as the target; the computer needs
  more than the target by a drawn margin of 0 or 1, so never at equal strength.
- **This sitting:** computer, 94 attack starts: 0 at equal or lower strength; the smallest margin seen is 1
  (six starts, with attackers of 3, 3, 4, 4, 7 and 7 armies; the table's `before` column has every start).
  Human, 17 starts: all had at least 2 armies and at least as many as the target; no equal-strength start
  and no refusal was shown, and the 16-case grid (N in 2, 4, 8, 12 against N-1 to N+2) was not played.
- **Why narrowed:** the computer half is not met on 94 starts (target 100+); the human boundary and the
  refusal are untested.
- **Cited by:** E018-r0003.

### Q-CMB-02 (C-CMB-02) — equality, not a ratio

- **Status:** narrowed
- **This sitting:** computer starts show margins from 1 to 33; the margin-1 starts all had attackers of 3 to
  7, and the starts with 10 or more attackers all had margins of at least 6. No start of a large attacker at
  margin 1 was seen, so "the gate does not scale" is not tested either way. The human boundary at N in 4, 8,
  12, 20 was not played.
- **Cited by:** E018-r0003.

### Q-CMB-03 (C-CMB-03) — minimum attacking stack

- **Status:** narrowed (the computer arm has 94 starts against a target of 100 or more, so it is narrowed too; the human arm is unestablished)
- **Static claim:** human minimum 2; computer minimum 3 or 4 before a capture this turn (4 or 5 for a country
  on the fixed 23-country list) and 4 after one (5 on the list).
- **This sitting:** the computer's smallest start by class, all four matching the low end of the claim:
  ordinary country before a capture 3 (23 starts), list country before a capture 4 (28), ordinary after a
  capture 4 (21), list country after a capture 5 (22); no start below its class minimum in 94. The human's
  smallest attack was 3 (attacks 34 and 53); no attempt with 1 or 2 armies, so the human minimum is not
  tested.
- **Cited by:** E018-r0003 (list membership from `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json`).

### Q-CMB-04 (C-CMB-04) — one die each, one army per exchange, five-at-once batching

- **Status:** narrowed
- **This sitting:** 442 exchanges; each changed exactly one counter by one (360 counter steps, none of
  (-1,-1) or larger). Exchanges against a one-army defender by attacker size: 2: 1, 3: 15, 4: 35, 5: 27,
  10: 9 (target 100+ each); 11 and over: 59. The five-exchange pass needs more than 40 against more than 15
  (computer) or more than 35 against more than 15 (human); the largest stack pairs seen were 37 v 4
  (computer) and 10 v 1 (human), so batching was not exercised.
- **Cited by:** E018-r0003.

### Q-CMB-05 (C-CMB-04, defender-size half) — defender size

- **Status:** narrowed
- **This sitting:** attacker-loss share by defender size: 1 army 128/210 (61.0%), 2 armies 61/116 (52.6%),
  3 armies 40/80 (50.0%), 4 armies 10/22, 5 or more 6/14. A chi-square test across the five groups gives
  p = 0.22, so no dependence on the defender's size is detected, but the trend (61.0% down to about 50%) is
  not excluded at this count. Defender size 10 was not seen (largest defender 6).
- **Cited by:** E018-r0003.

### Q-CMB-06 (C-CMB-05) — ties go to the defender

- **Status:** narrowed
- **Static claim:** ties go to the defender, so the attacker loses an exchange 21 times in 36 (7/12, 58.3%).
- **This sitting:** attacker lost 245 of 442 exchanges (55.4%; the defender lost 197), 95% interval 50.8% to 60.1%; 7/12
  is inside the interval (z = -1.24); an even 50% is not (z = +2.28, two-sided p about 0.02). Human 30 of 49
  (61.2%), computer 215 of 393 (54.7%); the two shares do not differ detectably (p = 0.39). Dice are not visible, so only the outcome share is tested.
- **Why narrowed:** 442 of the 500 target; the share is consistent with the claim, not a proof of it.
- **Cited by:** E018-r0003.

### Q-CMB-07 (C-CMB-06) — exactly one army lost per exchange

- **Status:** corroborated
- **This sitting:** 360 counter steps (target 200), every one a loss of one army on exactly one side; none
  lost two or lost one on each side; a 5-army run could not occur (see Q-CMB-04). 82 capture exchanges end
  with the defender's last army gone.
- **Cited by:** E018-r0003.

### Q-CMB-08 (C-CMB-08) — a battle's end, quit, automatic loop

- **Status:** narrowed
- **This sitting:** human, 17 attacks: 12 ended in a capture, 5 were quit by the owner with armies as they
  stood (attacks 11, 27, 34, 58, 100: ending at 2, 3, 2, 2 and 2 armies), ownership unchanged and no cost
  seen at the 5 offsets. Whether one click is one exchange is not established: clicks are not visible, and
  consecutive exchanges are 0.13 to 2.0 s apart (median 0.47 s over 37 intervals; the two repeated
  states, in attacks 19 and 58, are 11.4 s and 7.4 s apart and are pauses, not exchanges). Targets met on
  count (human 10 attacks, computer 30 battles). Computer, 94 battles: 70 captures, 24 stops without a
  capture; the attacker's armies at those
  stops were 2 (nine times), 3 (fourteen) and 5 (once), never below 2, as the static claim says. Computer
  exchange intervals 0.03 to 0.23 s, median 0.20 s over 254 (the repeated state in attack 83 is a 7.3 s
  pause, not an exchange).
- **Cited by:** E018-r0003.

### Q-CMB-09 (C-CMB-09) — a failed attack

- **Status:** narrowed (the computer arm met its count, 24 stops against 20; the human arm, 5 failed attacks wanted, saw none)
- **This sitting:** computer, 24 stops without a capture (target 20): the attacker's and defender's owners
  are unchanged in all 24 when read 1.2 s after the stop, and the attacker's country keeps at least 2.
  Human: no attack was lost down to 1 army (five quits at 2 or more), so the forfeit rule, the card
  cancellation and the turn change are not exercised.
- **Cited by:** E018-r0003.

### Q-CMB-10 (C-CMB-10) — attacks per turn

- **Status:** narrowed
- **This sitting:** computer attacks per turn over 42 turns: 0 in 2, 1 in 13, 2 in 12, 3 in 10, 4 in 2, 5, 6
  and 8 in one each; the green seat with 26 to 32 countries made 6, 3, 3 and 8 attacks (turns 43, 47, 51,
  55). Rounds are not visible, so the drawn rounds of 2 to 5 cannot be checked; none of the 42 turns had
  more than 8 attacks. Human: 13 turns, 1 attack in 9 and 2 in 4; nothing stopped the human from more
  (the owner chose), so "no limit" is untested.
- **Cited by:** E018-r0003 (turn assignment from the scoreboard marker in E018-r0004).

### Q-CMB-11 (C-CMB-07) — nothing but counts and dice enters an exchange

- **Status:** narrowed
- **This sitting:** attacker-loss share by whether the attacker's country is on the fixed 23-country list:
  list 146/259 (56.4%), not on the list 99/183 (54.1%), chi-square p = 0.64. By attacker size band: 1-3 14/27,
  4-6 90/165, 7-10 60/110, 11-20 43/81, 21+ 38/59, p = 0.68. A shift of about 4 points is not detectable
  with 442 exchanges; no gross effect appears.
- **Cited by:** E018-r0003.

## Capture, moves, ownership

### Q-OWN-01 (C-OWN-01) — armies moved in on a capture

- **Status:** narrowed
- **This sitting:** human, 12 captures (attacks 5, 10, 19, 26, 33, 44, 53, 67, 73, 84, 91, 92): the counter
  started at 1 each time; the owner moved in 1, 1, 1, 1, 4, 1, 1, 1, 1, 6, 9 and 3, never more than the
  attacker's armies minus 1 (at most all but one: 4 of 5, 6 of 7, 9 of 10); the attacker always kept at
  least 1; the captured country received exactly the number chosen. Whether 0 can be chosen is not shown.
  Captures from stacks of 2, 3, 5 and 10: 1, 2, 4 and 1 (target 3 each). Computer, 70 captures: the two
  counters add up to the attacker's armies in all 70, both at least 1; the attacker kept 1 in 16, 2 in 6,
  3 in 37, 4 in 8, 5, 9 and 14 in one each. The split is neither fixed nor "the dice"; keeping 3 is the
  commonest outcome (37 of 70), which fits C-AI-07's keep-3 branches, but the strongest-neighbour inputs
  were not read, so the rule itself is not tested.
- **Cited by:** E018-r0003, E018-r0005.

### Q-MOV-01 (C-MOV-01) — moves per turn

- **Status:** narrowed
- **This sitting:** human: one move in 13 turns (turn 48, 15:30.5 to 15:35.0), and the turn passed to the
  next seat 1.3 s after it, with no attack in between. Computer: 7 moves in 42 turns, never two in one turn,
  each in the closing seconds of that seat's turn (offsets 01:19.0, 01:33.0, 05:37.2, 06:03.4, 10:42.4,
  11:26.7, 12:57.4). The target (10 human turns with a move) is not met.
- **Cited by:** E018-r0005.

### Q-MOV-02 (C-MOV-02) — all but one

- **Status:** narrowed
- **This sitting:** human move from a stack of 6: 5 moved, 1 left. Computer: 7 of 7 moves left the source
  at exactly 1 (sources held 3, 4, 3, 10, 14, 3, 4). Stacks of 2, 3, 10 and the all-but-two refusal were not
  played by the human.
- **Cited by:** E018-r0005.

### Q-MOV-03 (C-MOV-03) — adjacency, move then attack

- **Status:** narrowed
- **This sitting:** all 8 moves were between neighbouring countries (human 11 to 13; computer 7). A country
  captured earlier in the same turn attacked in that turn 29 times (28 computer, 1 human: attack 92 from the
  country taken in attack 91), so a just-captured country is not blocked. A second move in a turn and a
  destination two borders away were not tried.
- **Cited by:** E018-r0003, E018-r0005.

## Cards and bonuses

### Q-BON-03 (C-CRD-01, C-CRD-02) — kinds seen

- **Status:** narrowed
- **This sitting:** seven of the eight kinds appeared on card screens or hands: +5, +8, the bomb-match card,
  the anti-bomb card, the doubling card, the wildcard and the empty-the-hand card (the last is the one that
  emptied hands at turns 42 and 44). Frames: a five-card hand at 09:50.2, the empty-the-hand card at 14:15.8,
  the wildcard in the hand at 12:47.0. The +15 card was not seen in 45 draws.
- **Cited by:** E018-r0004.

### Q-BON-05 (C-CRD-03) — a card per capturing turn

- **Status:** narrowed
- **Why narrowed:** F014's plan asks for at least 20 human turns and 20 computer turns split by captures, and a
  human turn ending in a forfeited attack after an earlier capture. This sitting has 13 human turns (with a
  following turn start: 2 with no capture, 10 with one, 1 with two or more) and 41 computer turns (7, 19 and
  15), and no forfeited human attack. The computer arm is met; the human arm and the forfeit case are not.
  The earlier sitting (IP1 025) is not counted here: its records do not give per-turn human counts.
  The IP1 025 section above marks Q-BON-05 `corroborated` on one capturing turn; that does not meet this
  target either, so read both sittings together as `narrowed`.
- **This sitting:** over the 54 turns with a following turn start: 45 capturing turns and 9 without a
  capture. In the 9 non-capturing turns the seat's card count did not change. In the 31 capturing turns
  with fewer than 5 cards and no trade-in the count rose by exactly 1, 11 of them turns with two or more
  captures (still +1). The other 14 capturing turns: 4 with a trade-in (3 cards out, 1 drawn: turns 23, 25,
  29, 43), 8 with 5 cards that stayed at 5 (Q-BON-06), and 2 where the empty-the-hand card was drawn (Red,
  turn 42; Blue, turn 44 after a trade-in). Human and computer seats alike. A failed human attack
  cancelling the draw is not tested. Every one of these observations agrees with the claim.
- **Cited by:** E018-r0004.

### Q-BON-06 (C-CRD-04) — five cards, discard on a full hand

- **Status:** narrowed
- **This sitting:** no seat ever showed more than 5 cards. Human: capturing with 5 cards (turns 24, 28,
  36, 40) left 5; at turns 24 and 28 the discard notice and the clicking away of one card were seen (08:46.5
  and 09:58.5; at turn 28 the anti-bomb card was clicked away and a +8 card took its place, 10:04.5). Computer:
  capturing with 5 cards left 5 in 4 cases (turns 34, 38, 39, 53); its discard priority is not visible.
  Drawing the empty-the-hand card emptied the hand with no discard first (Red, turn 42, at 5 cards; Blue,
  turn 44, at 2 cards).
- **Cited by:** E018-r0004.

### Q-BON-07 (C-CRD-05) — one set per turn, what is a set

- **Status:** narrowed
- **This sitting:** 5 trade-ins, at most one per seat-turn: computer doubling (turn 23), plus 5 (turns 25
  and 43), bomb match (turn 29); human plus-8 using two +8 cards and a wildcard (turn 44, the three selected
  cards were highlighted at 13:42.0). Each took 3 cards from the hand and the capture draw still followed.
  Several matches held at once and a second trade-in in a turn were not tried.
- **Cited by:** E018-r0004.

### Q-BON-08 (C-CRD-06) — the bomb card

- **Status:** unestablished
- **This sitting:** the computer's bomb-match trade (turn 29, 10:10.0) was cancelled by the victim's anti-bomb
  (see Q-BON-09), so the bomb's effect on a country was not seen; the human did not play a bomb.
- **Cited by:** E018-r0004.

### Q-BON-09 (C-CRD-07) — the anti-bomb card

- **Status:** narrowed
- **This sitting:** at the turn-29 bomb (10:17.5) a notice said the defending country had the protection;
  the red seat's hand went from 5 to 4 across the same turn change (the only hand besides the trading
  seat's to change) and the placement pool was unchanged (7). One case.
- **Cited by:** E018-r0004.

### Q-BON-10 / Q-BON-11 (C-CRD-05, C-REI-03) — trade-in effects on the pool

- **Status:** narrowed
- **This sitting:** plus 5 (yellow, turn 25): pool 11 became 16 (09:04.6 frame). Plus 8 (human, turn 44): pool
  4 became 12. Doubling (green, turn 23, three islands): pool 14 became 28, so the doubling takes in the
  bonus. Bomb match (turn 29): pool unchanged at 7. Plus 15 and the second plus 5 (turn 43, pool not shown
  for a computer) are not read.
- **Cited by:** E018-r0004.

## Income

### Q-REI-01 / Q-REI-02 (C-REI-01, C-REI-02) — income from the territory count, the floor of 2

- **Status:** narrowed
- **Why narrowed:** F013's plan asks for at least 2 turns at each of 1, 2, 3, 6, 9, 12 and 15 countries with no
  island held (and, for the floor, at 1, 2, 3, 5, 6 and 9, plus the floor-plus-bonus case of a whole small
  island and 2 outside countries). The turns with no island held are, by country count: 1 country, 1 turn;
  3, 1 turn; 9, 2 turns; and also 8 (1), 10 (3), 13 (4). There is none at 2, 6, 12, 15 or (for the second
  list) 5 with no island. The island identities were not read, so a bonus cannot be subtracted on an
  independent basis; the island turns agree with the static values but do not test them.
- **Static claim:** the country part is the count divided by 3, rounded down, raised to 2; the island bonus
  is added after; no first-turn exception.
- **This sitting:** all 55 turns agree with the claim (an independent check only for the 12 turns that
  show no island). The 12 turns with no island read exactly the country part: counts 13,
  10, 13, 9, 13, 10, 13, 9, 3, 10, 8 and 1 gave 4, 3, 4, 3, 4, 3, 4, 3, 2, 3, 2, 2 (counts of 1 and 3 get the
  floor; the first turn is not special). The remaining 43 turns read the country part plus an island
  amount that is a sum of the static bonus values: one island 2 (13 turns), 3 (9), 4 (9); two islands 7 (1)
  and 8 (2); three islands 9 (3); four islands 14 (4); five islands 22 (2). The blue seat with 3 countries
  read 2 with no island (turn 28) and 4 with one island (turns 32, 36, 44: country part 2 plus 2), as the
  static example of a 3-country 2-bonus island says.
- **Cited by:** E018-r0004.

### Q-REI-03 (C-REI-04) — placing the pool

- **Status:** narrowed
- **This sitting:** the human places through a counter that starts at 0 with an all button, plus and minus
  buttons and a place button, after clicking a country; the pool message counts down (09:35.4 to 09:38.5).
  Seen once; the over-pool and 999 cases are untested.
- **Cited by:** E018-r0005.

### Q-REI-05 — army growth over a game

- **Status:** unestablished
- **This sitting:** territory counts and card counts of all four seats at each of 55 turn starts are
  recorded (r0004); armies per seat and the largest stack are not shown on the panel, so growth is not
  read. One game.

### Q-BON-01 / Q-BON-02 (C-BON-01, C-BON-02) — island bonuses

- **Status:** narrowed
- **This sitting:** the single-island values read 2, 3 and 4 (never 5 or 8) and the sums for two to five
  islands are sums of the static values; which island was held is not read, so the nine values are not
  separated, and partial control was not isolated.
- **Cited by:** E018-r0004.

## Setup, turns, events, ending

### Q-SET-04 (C-SET-01) — the options screen

- **Status:** corroborated (one visit, as the target asks)
- **This sitting:** the options screen at 00:15.0 shows the groups the static claim lists: four seat toggles
  (one human, three computer), a five-entry starting-armies dial (3 highlighted), a three-entry strength dial,
  a four-entry event-frequency dial, a three-entry speed dial, and a sound icon, plus a save-as-default
  and a play button.
- **Cited by:** E018-r0005.

### Q-STA-01 / Q-STA-03 (C-STA-03, C-STA-05) — the deal

- **Status:** narrowed
- **This sitting:** one deal: counts blue 9, yellow 13, red 10, green 14 (sum 46), the human at 9 with the
  middle strength (level 2, claim: 9); every country showed 1 to 3 armies; the first seat to play was yellow.
  One deal, target 10.
- **Cited by:** E018-r0005.

### Q-TRN-02 (C-TRN-02) — seat order

- **Status:** narrowed
- **This sitting:** the playing seat followed yellow, red, green, blue without a break for all 55 turns
  (13 full rounds and 3 more); the skip of an eliminated seat was not seen (the human's elimination came at
  the end).
- **Cited by:** E018-r0004.

### Q-TRN-05 — game length

- **Status:** unestablished
- **This sitting:** one game: 55 player-turns, 17:04 of recording to the human's elimination and 17:10 to
  the end (the first turn starts at 00:25.5), at the owner's own pace. One game is not a distribution.
- **Cited by:** E018-r0004, E018-r0005.

### Q-HAZ-01 / Q-HAZ-02 / C-VIC-04 — event messages

- **Status:** narrowed
- **This sitting:** two event messages in 55 player-turns, both between turns and both of one kind (a
  production-centre increase): 10:25.0 to 10:31.0 (between turns 29 and 30) and 13:26.5 to 13:33.5 (between
  turns 43 and 44); none before turn 7; no seat held 39 or more countries before the end. 2 of the 49
  transitions from turn 6 on, so about 4 per cent (the claim's range is 1 in 8 to 1 in 21 by setting; the
  setting here was the middle one). The centre dialog area and the message strip were scanned for any other
  kind; none appeared.
- **Cited by:** E018-r0004.

### Q-VIC-01 / Q-SUR-05 (C-VIC-01, the elimination prompt) — the end

- **Status:** narrowed
- **This sitting:** the human seat was eliminated by a computer capture (attack 111, starting 17:03.7, the
  seat at 0 countries by 17:04.5); a prompt with an accept-the-loss button and a keep-playing button came at
  about 17:04.5; the owner's reply, read from the highlighted button at 17:07.4 and the stop-playing control
  that followed, was to keep playing; the remaining conquests (yellow 6, red 1) ran in under 0.5 s with no
  per-attack screen, and the game ended with the green seat holding 46 at 17:09.6 and an end dialog at 17:10.0. The attack-round bonus after the
  elimination (C-AI-03) cannot be read in a play-out that short.
- **Cited by:** E018-r0005.

## Computer opponent

### C-AI-03 / C-AI-04 (Q-AI-01, Q-AI-04) — attacks and turns with none

- **Status:** narrowed
- **This sitting:** 94 computer attacks in 42 computer turns recorded with counts before and after (table
  above); the gates of Q-CMB-01 and Q-CMB-03 hold in all 94. Two computer turns had no attack at all (turn
  18, red seat, 13 countries; turn 37, yellow seat, 10 countries), 2 of 42, about the 1 in 22 the static
  reading gives for a seat with 18 or fewer countries (expected 1.9); the cause (the skip draw or no
  qualifying pair) is not visible. The target is 20 games.
- **Cited by:** E018-r0003, E018-r0004.

### Q-AI-05 / Q-AI-02 / C-AI-06 — placement and cards

- **Status:** unestablished for placement (the computer places with no screen, so no placement is visible);
  the computer's trade-in priority is only partly visible (see Q-BON-07).

### Q-AI-07 — strength against scripted opponents

- **Status:** unestablished (one game with an unscripted human; a win rate needs many games).

### C-AI-05 (Q-AI-04's move half) — the computer's end-of-turn move

- **Status:** narrowed
- **This sitting:** 7 moves; every source was off the 23-country list (the claim excludes key sources),
  every destination was on it; each moved all but one army and the destination was a neighbour; source
  and destination counters are in r0005. Whether the source was the seat's largest eligible country was not
  checked.
- **Cited by:** E018-r0005.

## What only a human sitting shows (constraint E)

These rest on the owner's videos, and on this one for the sitting's own readings; none is a rule claim.

- The owner quit five battles at 2 or 3 armies (attacks 11, 27, 34, 58, 100); in attack 100 ten armies
  against one lost eight exchanges in a row (about a 1.3 per cent chance at 7/12 each) before the owner quit
  at 2 v 1 at about 16:28.
- At 8 of 12 captures the owner kept the move-in at 1 (the counter's start); three times took all but one
  (attacks 33, 84, 91); once 3 of 9 (attack 92).
- A click on the owner's own country as a target was refused at 05:22.4 and the attack began 2.1 s later.
- One human move in 13 turns (turn 48, at 15:30); one human trade-in in 13 turns (turn 44), a plus-8 set
  with a wildcard.
- The human seat shrank from 9 countries to 3 by turn 28 and held between 3 and 6 until its elimination at
  17:04.0; after the elimination the owner kept the game running (17:07.4).
- The computer's answer to the owner's play is not separable from its own policy here; the data above is
  the computer's play, with no model-driven sitting to compare.

## Re-reads (rule 20)

A re-read of `IP1 026.mp4` writes new files beside r0003..r0005 (the next free record numbers) with their
own frame hashes, and says which record it cross-references; these records stay as written.

---

# IP1 027 sitting

The third owner sitting (2026-10-11, owner-driven Bandicam capture, 11:02, video sha256
`aa8ed8c4f9b84d40ccc85c40b8198edb6e84062a89d57ee84b287f2c32f2e63d`, Bandicam 8.3.0.2533 per the file's encoder
tag; frame timestamps are irregular, 12978 frames in 662.50 s, so offsets are container timestamps, not frame
numbers). One game from the title screen to the title screen after the game: the options screen at 00:01, the
deal at 00:04, 46 player-turns before the human seat was out (12 human, 34 computer), 87 attacks (13 human, 74
computer), the human seat eliminated at 10:42.87 (by attack 86, the last human country), the owner choosing
to keep playing at 10:46.97, the yellow seat holding all 46 countries at 10:49.00, the winner dialog at 10:49.2,
the scoreboard screen at 10:56.2 and the title screen at 10:58.3. **The owner did not win**: the human seat was
eliminated and the computers played the game out.

Records, all immutable, `runtime.platform` `windows-native-bandicam`:

- `E018-r0006`: the 87 attacks (start counters, strip states, endings, capture splits and move-ins), ten frames.
- `E018-r0007`: the 46 turn starts (territory counts, army pools, cards), the card draws, the four computer
  trade-ins, the bomb match and its notice, four frames.
- `E018-r0008`: the options screen, the deal, the 12 human placements, the 7 computer moves, the elimination and
  the end, eight frames.
- `E018-r0009`: the three event messages and the scene changes at the end, one frame.

Frames are in the bundle store by hash, listed in `evidence/E018/E018-r0006..9.manifest.json`; the video and the
frames are never committed (rule 18). Everything was read by pixels (glyph-shape matching of the strip and the
map digits, colour regions; no OCR). Four checks backed the readings: every one of the 139 strip steps is a single
loss on one side (none was (1,1) or larger); for all 46 captures with both counters read (6 human, 40 computer)
the two country counters after the capture add up to the attacker's armies at the capture (the other 6 computer
captures had one counter hidden by the capture flash and take it from the total); the strip states of all 13
human attacks and 6 computer attacks (4, 11, 12, 32, 44, 45) were re-read by eye on crops of the frames and
matched; and every attack's two countries are neighbours in the F017 border tables (87 of 87).

**A correction to how attack starts are read** (it also bears on the IP1 026 section above, whose `before`
column already used the country counters). The strip of the counters appears after the computer's first
exchange: for 46 of the 73 resolved computer attacks of this sitting the country counters just before the strip
are one exchange ahead of its first state. Reading starts from the strip alone would have shown three
equal-strength starts (attacks 24, 44 and 74, at 3 against 3); the country counters show them at 4 against 3.
For the human the strip shows the counters before any exchange (13 of 13 agree with the country counters).

## What the owner meant to play, and what the video shows

The owner meant to build exact stacks (an even attacker of 4 against 6, 8 or 12 against N-1 to N+2, underdogs of
12 and 20; E021's open cells). **The video shows none of them.** The human held 9 countries at the deal and
income of 2 or 3 armies a turn; all 13 human attacks started from 3 to 6 armies against 1 or 2 (largest 6
against 2, attack 23, at 03:26.4); no human attacker was ever below the defender at the start. The 12
placements were of 2 or 3 armies each (r0008), so no stack could pass 6. So the sitting meets none of E021's open cells: even 4 against 6, 8
against 7, 9, 10, and 12 against 11, 12, 13, 14 (cells 8, 9, 11 to 16 of the even row), underdog 12 and 20
(cells 3 and 4). The E021 progress counter counts only E021 records and stays at 30 of 40.

Every human attack, with its start and what it fits (E021's cells, for the main session; nothing here is
counted in E021):

| # | offset | from>to | start | strip states | ending | Session A cell it fits |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 00:43.667 | 39>38 | 5 vs 2 | 5/2 4/2 3/2 | quit at 3/2 | quit cell |
| 2 | 00:50.667 | 42>41 | 4 vs 2 | 4/2 3/2 | quit at 3/2 | quit cell |
| 8 | 01:35.667 | 39>37 | 5 vs 2 | 5/2 4/2 3/2 | quit at 3/2 | quit cell |
| 15 | 02:13.300 | 39>37 | 5 vs 2 | 5/2 4/2 4/1 | capture at 4; moved in 2, kept 2 | none |
| 23 | 03:26.367 | 42>40 | 6 vs 2 | 6/2 5/2 5/1 4/1 | capture at 4; moved in 2, kept 2 | none |
| 27 | 04:19.433 | 42>41 | 5 vs 2 | 5/2 4/2 3/2 | quit at 3/2 | quit cell |
| 33 | 04:57.733 | 40>41 | 4 vs 2 | 4/2 3/2 | quit at 3/2 | quit cell |
| 39 | 05:37.733 | 44>46 | 5 vs 1 | 5/1 4/1 3/1 | capture at 3; moved in 1, kept 2 | none |
| 43 | 06:28.767 | 4>6 | 5 vs 2 | 5/2 4/2 4/1 3/1 2/1 | quit at 2/1 | quit cell |
| 51 | 07:21.133 | 4>6 | 4 vs 1 | 4/1 | capture at 4; moved in 1, kept 3 | none |
| 58 | 08:18.100 | 12>13 | 3 vs 1 | 3/1 | capture at 3; moved in 1, kept 2 | tiny, attacker 3 vs 1 (met earlier in E021) |
| 69 | 09:06.900 | 12>11 | 4 vs 2 | 4/2 3/2 2/2 | quit at 2/2 | quit cell |
| 81 | 10:23.133 | 12>11 | 4 vs 1 | 4/1 | capture at 4; moved in 1, kept 3 | none |

Reading the table: seven attacks ended by the owner (the quit button) with the attacker at 3 (five times), 2
against 1 (once) and 2 against 2 (once); six ended in a capture. No human attack started below 3 armies, none
at equal strength, none against a stronger defender; a human attacker was never reduced to 1 army. Cells fitted:
**tiny, attacker 3 against 1 (attack 58)**, one cell, which E021 had already met; **quit**, seven attacks (each
after at least one exchange the strip showed, the battle ending with owners and armies as they stood); no even
cell, no underdog cell, no lost cell (no failed attack: the human's lowest was 2), no busy cell (the most
attacks in one human turn was 2, turn 1; a busy cell needs 3 or more).

## The attacks: every one, before and after

`#` is the order in the video (`r0006`, step = `#`). `offset` is the first strip frame. `seat` is the attacking
seat, `C` computer, `H` human. `before` is attacker/defender armies as the country counters show them just
before the strip appeared (`(strip)` where those could not be read and the strip's first state is used);
`after` is the last state, or, for a capture, the attacker's armies at the capture with the defender at 0, then
the split (computer: armies kept in the attacker's country and armies placed in the captured country; human:
the move-in the owner chose and what the attacker keeps). A `*` marks a split number taken from the total because
the capture flash hid that counter. A stop or quit leaves both countries with their owners. Attack 87 is inside
the play-out and not resolved.

| # | offset | seat | from>to | before | after | ending |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 00:43.667 | Blue H | 39>38 | 5/2 | 3/2 | quit |
| 2 | 00:50.667 | Blue H | 42>41 | 4/2 | 3/2 | quit |
| 3 | 01:03.800 | Yellow C | 14>46 | 6/1 | 4/0, then keeps 3 gets 1 | capture |
| 4 | 01:09.700 | Red C | 30>31 | 5/2 | 3/2 | stop |
| 5 | 01:15.567 | Green C | 34>32 | 6/3 | 3/3 | stop |
| 6 | 01:16.600 | Green C | 19>22 | 3/1 | 3/0, then keeps 2 gets 1 | capture |
| 7 | 01:18.167 | Green C | 35>36 | 5/2 | 3/2 | stop |
| 8 | 01:35.667 | Blue H | 39>37 | 5/2 | 3/2 | quit |
| 9 | 01:46.533 | Yellow C | 18>19 | 5/2 | 4/0, then keeps 3 gets 1 | capture |
| 10 | 01:48.600 | Yellow C | 21>23 | 5/3 | 3/3 | stop |
| 11 | 01:53.200 | Red C | 30>31 | 3/2 | 3/1 | stop |
| 12 | 01:53.833 | Red C | 30>29 | 3/1 | 2/1 | stop |
| 13 | 01:54.500 | Red C | 33>38 | 4/2 | 3/2 | stop |
| 14 | 01:59.600 | Green C | 35>36 | 8/2 | 7/0, then keeps 4 gets 3 | capture |
| 15 | 02:13.300 | Blue H | 39>37 | 5/2 | 4/0, then in 2 keeps 2 | capture |
| 16 | 02:34.967 | Yellow C | 19>20 | 5/1 | 2/1 | stop |
| 17 | 02:35.933 | Yellow C | 17>20 | 3/1 | 2/1 | stop |
| 18 | 02:36.567 | Yellow C | 21>22 | 3/1 | 3/0, then keeps 2 gets 1 | capture |
| 19 | 02:41.933 | Red C | 30>32 | 5/3 | 3/2 | stop |
| 20 | 02:42.867 | Red C | 30>31 | 3/1 | 3/0, then keeps 2 gets 1 | capture |
| 21 | 02:48.767 | Green C | 26>24 | 7/2 | 5/0, then keeps 3 gets 2 | capture |
| 22 | 02:51.067 | Green C | 34>32 | 6/2 | 4/0, then keeps 3 gets 1 | capture |
| 23 | 03:26.367 | Blue H | 42>40 | 6/2 | 4/0, then in 2 keeps 2 | capture |
| 24 | 03:44.067 | Yellow C | 22>23 | 4/3 | 2/3 | stop |
| 25 | 03:48.667 | Red C | 30>29 | 5/1 | 3/0, then keeps 1 gets 2 | capture |
| 26 | 04:04.533 | Green C | 26>25 | 14/2 | 13/0, then keeps 12 gets 1 | capture |
| 27 | 04:19.433 | Blue H | 42>41 | 5/2 | 3/2 | quit |
| 28 | 04:28.333 | Yellow C | 21>20 | 4/1 | 3/0, then keeps 2 gets 1 | capture |
| 29 | 04:35.600 | Red C | 28>27 | 5/1 | 5/0, then keeps 1 gets 4 | capture |
| 30 | 04:42.167 | Green C | 43>42 | 8/3 (strip) | 7/0, then keeps 3 gets 4 | capture |
| 31 | 04:44.467 | Green C | 42>39 | 4/2 | 3/2 | stop |
| 32 | 04:45.100 | Green C | 26>27 | 12/4 | 7/0, then keeps 3 gets 4 | capture |
| 33 | 04:57.733 | Blue H | 40>41 | 4/2 | 3/2 | quit |
| 34 | 05:07.633 | Yellow C | 20>16 | 5/1 | 5/0, then keeps 1 gets 4 | capture |
| 35 | 05:09.300 | Yellow C | 22>23 | 6/3 | 3/2 | stop |
| 36 | 05:14.200 | Red C | 30>32 | 4/2 | 4/0, then keeps 1 gets 3 | capture |
| 37 | 05:21.100 | Green C | 42>39 | 8/2 | 6/0, then keeps 3 gets 3 | capture |
| 38 | 05:23.200 | Green C | 41>40 | 6/3 | 2/1 | stop |
| 39 | 05:37.733 | Blue H | 44>46 | 5/1 | 3/0, then in 1 keeps 2 | capture |
| 40 | 06:02.533 | Green C | 39>37 | 8/2 | 4/0, then keeps 2 gets 2 | capture |
| 41 | 06:05.100 | Green C | 24>33 | 5/3 | 4/0, then keeps 3 gets 1 | capture |
| 42 | 06:07.300 | Green C | 34>32 | 5/3 | 3/1 | stop |
| 43 | 06:28.767 | Blue H | 4>6 | 5/2 | 2/1 | quit |
| 44 | 06:37.600 | Yellow C | 16>15 | 4/3 | 2/3 | stop |
| 45 | 06:38.367 | Yellow C | 21>23 | 10/2 | 10/0, then keeps 3 gets 7 | capture |
| 46 | 06:40.233 | Yellow C | 23>45 | 7/3 | 5/0, then keeps 3 gets 2 | capture |
| 47 | 06:42.500 | Yellow C | 14>15 | 7/3 | 7/0, then keeps 3 gets 4* | capture |
| 48 | 06:49.967 | Red C | 28>27 | 7/4 | 2/1 | stop |
| 49 | 06:57.067 | Green C | 37>40 | 10/1 | 10/0, then keeps 9* gets 1 | capture |
| 50 | 06:58.700 | Green C | 37>38 | 8/2 (strip) | 7/0, then keeps 3 gets 4 | capture |
| 51 | 07:21.133 | Blue H | 4>6 | 4/1 | 4/0, then in 1 keeps 3 | capture |
| 52 | 07:38.033 | Yellow C | 5>4 | 13/3 | 7/0, then keeps 3 gets 4 | capture |
| 53 | 07:41.133 | Yellow C | 14>46 | 6/1 | 6/0, then keeps 3 gets 3 | capture |
| 54 | 07:53.467 | Green C | 10>9 | 3/2 | 3/1 | stop |
| 55 | 07:54.000 | Green C | 33>31 | 8/1 | 8/0, then keeps 3 gets 5 | capture |
| 56 | 07:55.733 | Green C | 31>30 | 5/1 | 4/0, then keeps 3 gets 1 | capture |
| 57 | 07:57.467 | Green C | 43>44 | 6/2 | 3/1 | stop |
| 58 | 08:18.100 | Blue H | 12>13 | 3/1 | 3/0, then in 1 keeps 2 | capture |
| 59 | 08:28.967 | Yellow C | 46>44 | 15/1 | 15/0, then keeps 3 gets 12 | capture |
| 60 | 08:30.600 | Yellow C | 4>6 | 4/1 | 4/0, then keeps 1 gets 3 | capture |
| 61 | 08:32.300 | Yellow C | 23>24 | 7/6 | 5/6 | stop |
| 62 | 08:33.067 | Yellow C | 44>43 | 12/3 | 11/0, then keeps 3 gets 8 | capture |
| 63 | 08:35.400 | Yellow C | 43>41 | 8/2 | 3/1 | stop |
| 64 | 08:41.767 | Red C | 32>30 | 5/1 | 3/0, then keeps 2 gets 1 | capture |
| 65 | 08:48.967 | Green C | 41>43 | 8/3 | 6/0, then keeps 1 gets 5 | capture |
| 66 | 08:51.233 | Green C | 43>8 | 5/1 | 4/0, then keeps 3 gets 1 | capture |
| 67 | 08:53.067 | Green C | 24>23 | 8/7 | 6/7 | stop |
| 68 | 08:53.867 | Green C | 34>32 | 5/2 | 5/0, then keeps 3 gets 2 | capture |
| 69 | 09:06.900 | Blue H | 12>11 | 4/2 | 2/2 | quit |
| 70 | 09:15.300 | Yellow C | 3>2 | 8/3 | 7/0, then keeps 3 gets 4 | capture |
| 71 | 09:17.433 | Yellow C | 6>8 | 9/1 (strip) | 9/0, then keeps 3 gets 6 | capture |
| 72 | 09:19.167 | Yellow C | 8>7 | 6/3 | 4/0, then keeps 1 gets 3 | capture |
| 73 | 09:21.467 | Yellow C | 23>38 | 7/6 | 5/6 | stop |
| 74 | 09:22.233 | Yellow C | 2>1 | 4/3 | 2/3 | stop |
| 75 | 09:37.333 | Red C | 29>27 | 12/1 | 12/0, then keeps 3 gets 9* | capture |
| 76 | 09:38.967 | Red C | 27>26 | 8/3 (strip) | 6/0, then keeps 3 gets 3 | capture |
| 77 | 09:57.533 | Green C | 31>30 | 3/1 | 2/1 | stop |
| 78 | 09:58.167 | Green C | 32>30 | 4/1 | 3/1 | stop |
| 79 | 09:58.833 | Green C | 10>11 | 3/2 | 2/1 | stop |
| 80 | 09:59.667 | Green C | 25>26 | 10/3 | 8/0, then keeps 1 gets 7 | capture |
| 81 | 10:23.133 | Blue H | 12>11 | 4/1 | 4/0, then in 1 keeps 3 | capture |
| 82 | 10:34.233 | Yellow C | 9>10 | 12/2 | 11/0, then keeps 3 gets 8 | capture |
| 83 | 10:36.267 | Yellow C | 10>11 | 8/1 | 8/0, then keeps 3 gets 5* | capture |
| 84 | 10:37.867 | Yellow C | 2>1 | 13/3 | 10/0, then keeps 1 gets 9* | capture |
| 85 | 10:40.400 | Yellow C | 11>12 | 5/3 | 3/0, then keeps 1 gets 2 | capture |
| 86 | 10:42.700 | Yellow C | 1>13 | 9/1 (strip) | 9/0, then keeps 6* gets 3 | capture |
| 87 | 10:47.867 | Green C | 43>44 | 6/4 (strip) | not resolved | play-out |
Counts this sitting adds to the per-claim totals (constraint E): 237 exchanges (139 strip steps, 52 capture
exchanges inferred from the defender's last army, 46 first exchanges read from the before-counters), 86 resolved
attacks (13 human, 73 computer) plus one unresolved, 46 turn starts with the army pool, 12 human placements, 6 human
move-ins, 4 computer trade-ins, 7 computer moves, 3 event messages, 6 human card draws.

Outcome words follow `walkthroughs/f011-questions.md`: `corroborated` when the count target is met and play
matches the static claim, `narrowed` when it matches in the part played, `unestablished` when nothing in the
video bears on it.

## Combat

### Q-CMB-01 (C-CMB-01) - who may attack, human and computer

- **Status:** narrowed
- **Static claim:** a human needs at least 2 armies and at least as many as the target; the computer needs more
  than the target by a drawn margin of 0 or 1, so never at equal strength.
- **This sitting:** computer, 73 resolved starts: none at equal or lower strength; margins 1 (9 starts: attacks 11,
  24, 44, 54, 61, 67, 73, 74, 79; attackers of 3, 4, 4, 3, 7, 8, 7, 4, 3), 2 (14), 3 (12), 4 (11) and up to 14.
  Together with IP1 026 (94 starts, none at equal strength) the computer arm stands at 167 starts against a target
  of 100 or more. Human, 13 starts: all had at least 3 armies and more than the target; no equal-strength start
  and no refused order was shown, and the 16-case grid (N in 2, 4, 8, 12 against N-1 to N+2) was not played (no
  cell reached, see above).
- **Why narrowed:** the human boundary and the refusal are untested.
- **Cited by:** E018-r0006.

### Q-CMB-02 (C-CMB-02) - equality, not a ratio

- **Status:** narrowed
- **This sitting:** the computer's margin-1 starts have attackers of 3 to 8 (the largest, 8 against 7, attack 67,
  is a larger stack at margin 1 than IP1 026 showed, 7 against 6); the starts with 10 or more attackers (11) all
  had margins of at least 7. A margin-1 start at 12 or more was not seen. The human boundary at N in 4, 8, 12, 20
  was not played.
- **Cited by:** E018-r0006.

### Q-CMB-03 (C-CMB-03) - minimum attacking stack

- **Status:** narrowed (computer arm met over the two sittings; the human arm is unestablished)
- **Static claim:** human minimum 2; computer minimum 3 or 4 before a capture this turn (4 or 5 for a country on
  the fixed 23-country list) and 4 after one (5 on the list).
- **This sitting:** the computer's smallest start by class, all four equal to the low end of the claim: ordinary
  country before a capture 3 (28 starts), list country before a capture 4 (14), ordinary after a capture 4 (12),
  list country after a capture 5 (19); no start below its class minimum in 73. The human's smallest start was 3
  (attack 58, 3 against 1, the tiny cell of 3 against 1); no attempt with 1 or 2 armies, so the human minimum 2 is
  not tested.
- **Cited by:** E018-r0006 (list membership from `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json`).

### Q-CMB-04 (C-CMB-04) - one die each, one army per exchange, five-at-once batching

- **Status:** narrowed
- **This sitting:** 237 exchanges; every strip step changed exactly one counter by one (139 steps, none of (-1,-1)
  or larger). Exchanges against a one-army defender by attacker size: 3: 17, 4: 27, 5: 20, 10: 4 (target 100 or more
  each; 110 in all against a defender of 1; size 2: none); 6 to 9: 32, 11 and over: 10. The five-exchange pass needs
  more than 40 against more than 15 (computer) or more than 35 against more than 15 (human); the largest pair seen
  was 15 against 1 (computer) and 6 against 2 (human), so batching was not exercised.
- **Cited by:** E018-r0006.

### Q-CMB-05 (C-CMB-04, defender-size half) - defender size

- **Status:** narrowed
- **This sitting:** attacker-loss share by defender size at the exchange: 1 army 58/110 (52.7%), 2 armies 39/76
  (51.3%), 3 armies 21/40 (52.5%), 4 or more 9/11; a chi-square test across the four groups gives p = 0.29, so no
  dependence on the defender's size is detected. Defender size 10 was not seen (largest 7).
- **Cited by:** E018-r0006.

### Q-CMB-06 (C-CMB-05) - ties go to the defender

- **Status:** narrowed
- **Static claim:** ties go to the defender, so the attacker loses an exchange 21 times in 36 (7/12, 58.3%).
- **This sitting:** attacker lost 127 of 237 exchanges (53.6%), 95% interval 47.2% to 59.9%; 7/12 is inside the interval
  (z = -1.48), and so is an even 50% (z = +1.10). With IP1 026 (245 of 442): 372 of 679 (54.8%), interval 51.0% to 58.5%;
  7/12 is inside (z = -1.88), an even 50% is not (z = +2.49). Human 18 of 27 (66.7%), computer 109 of 210 (51.9%); the two
  shares do not differ detectably (Fisher p = 0.16); at 7/12 a human share of 18 or more in 27 has probability 0.25.
  Dice are not visible, so only the outcome share is tested.
- **Why narrowed:** 679 of the 500 target over the two sittings, but the share is consistent with the claim, not a proof.
- **Cited by:** E018-r0006.

### Q-CMB-07 (C-CMB-06) - exactly one army lost per exchange

- **Status:** corroborated
- **This sitting:** 139 strip steps (and 46 steps from the before-counters), every one a loss of one army on exactly one side;
  none lost two or lost one on each side; a 5-army run could not occur (see Q-CMB-04). 52 capture exchanges end with the
  defender's last army gone. With IP1 026 (360 steps) the count is 499 against the target of 200.
- **Cited by:** E018-r0006.

### Q-CMB-08 (C-CMB-08) - a battle's end, quit, automatic loop

- **Status:** narrowed
- **This sitting:** human, 13 attacks: 6 ended in a capture, 7 were quit by the owner with armies as they stood (attacks 1, 2, 8,
  27, 33, 43, 69: ending at 3, 3, 3, 3, 3, 2 and 2 armies), ownership unchanged and no cost seen. Whether one click is one exchange
  is not established (clicks are not visible); consecutive human strip steps are 0.27 to 1.03 s apart (median 0.60 s over 21
  intervals), computer steps 0.03 to 0.70 s (median 0.17 s over 118). Targets met on count (human 10 attacks, computer 30
  battles). Computer, 73 battles: 46 captures, 27 stops without a capture; the attacker's armies at those stops were 2 (ten
  times), 3 (fourteen), 5 (twice) and 6 (once), never below 2, as the static claim says.
- **Cited by:** E018-r0006.

### Q-CMB-09 (C-CMB-09) - a failed attack

- **Status:** narrowed (the computer arm met its count, 27 stops against 20; the human arm, 5 failed attacks wanted, saw none)
- **This sitting:** computer, 27 stops without a capture: the defender's country keeps its owner and the counters equal the last strip state
  in 25 of 27 (attacks 11 and 19 are followed by the next attack within 0.4 s, so their stop state is the last strip state, 3/1 and 3/2,
  and the next attack's before-counters agree); the attacker's country keeps at least 2. Human: no attack was lost down to 1 army (seven
  quits at 2 or 3), so the forfeit rule, the card cancellation and the turn change are not exercised.
- **Cited by:** E018-r0006.

### Q-CMB-10 (C-CMB-10) - attacks per turn

- **Status:** narrowed
- **This sitting:** computer attacks per turn over 34 turns: 0 in 3 (turns 26, 27, 35), 1 in 11, 2 in 8, 3 in 5, 4 in 4, 5 in 3; none of
  the 34 turns had more than 5 attacks. Rounds are not visible, so the drawn rounds of 2 to 5 cannot be checked. Human: 12 turns, 1 attack
  in 11 and 2 in 1; nothing stopped the human from more (the owner chose), so "no limit" is untested.
- **Cited by:** E018-r0006, E018-r0007 (turn assignment from the scoreboard marker).

### Q-CMB-11 (C-CMB-07) - nothing but counts and dice enters an exchange

- **Status:** narrowed
- **This sitting:** computer attacker-loss share by whether the attacker's country is on the fixed 23-country list: list 54/109 (49.5%),
  not on the list 55/101 (54.5%), chi-square p = 0.48 (Pearson, no continuity correction, as in the IP1 026 section; 0.57, first written here, was the Yates-corrected value; Luna's review of PR #186, R2). A shift of about 5 points is not detectable at this count; no gross effect appears.
- **Cited by:** E018-r0006.

## Capture, moves, ownership

### Q-OWN-01 (C-OWN-01) - armies moved in on a capture

- **Status:** narrowed
- **This sitting:** human, 6 captures (attacks 15, 23, 39, 51, 58, 81): the move-in counter started at 1 each time; the owner moved in 2, 2, 1, 1,
  1 and 1 from attackers holding 4, 4, 3, 4, 3 and 4 at the capture; at attack 15 the counter went 1, 2, 3 (all but one) and back to 2 before done
  (02:19.4, 02:19.8, 02:21.5), at attack 23 it went 1, 2 (03:31.1); the attacker always kept at least 1 (2, 2, 2, 3, 2, 3) and the captured
  country received exactly the number chosen. Whether 0 can be chosen is not shown. Captures from stacks of 2, 3, 5 and 10: 0, 2, 0 and 0
  (target 3 each). Computer, 46 captures: the two counters add up to the attacker's armies in all 40 with both read, both at least 1; the attacker
  kept 1 in 10, 2 in 6, 3 in 26, 4, 6, 9 and 12 in one each. Keeping 3 is again the commonest outcome (26 of 46), which fits C-AI-07's keep-3
  branches, but the strongest-neighbour inputs were not read, so the rule itself is not tested.
- **Cited by:** E018-r0006.

### Q-MOV-01 (C-MOV-01) - moves per turn

- **Status:** narrowed
- **This sitting:** human: no move in 12 turns (the move button was never pressed). Computer: 7 moves in 34 turns, never two in one turn, each after
  the seat's last attack of the turn, six within 2 s of the turn's end and one 7 s before it (offsets 02:01.2, 04:29.7, 06:44.1, 07:00.5, 07:42.3, 08:36.5, 09:22.7 for the first strip frame). The target
  (10 human turns with a move) is not met.
- **Cited by:** E018-r0008.

### Q-MOV-02 (C-MOV-02) - all but one

- **Status:** narrowed
- **This sitting:** computer: 7 of 7 moves left the source at exactly 1 (sources held 4, 5, 3, 3, 3, 3, 3). No human move, so stacks of 2, 3, 10 and the
  all-but-two refusal were not played.
- **Cited by:** E018-r0008.

### Q-MOV-03 (C-MOV-03) - adjacency, move then attack

- **Status:** narrowed
- **This sitting:** all 7 moves were between neighbouring countries. A country captured earlier in the same turn attacked in that turn 12 times (all
  computer; the human never did), so a just-captured country is not blocked. A second move in a turn and a destination two borders away were not tried.
- **Cited by:** E018-r0006, E018-r0008.

## Cards and bonuses

### Q-BON-03 (C-CRD-01, C-CRD-02) - kinds seen

- **Status:** narrowed
- **This sitting:** seven of the eight kinds appeared: the doubling card (human hand, turns 9 and 13; a computer trade-in), the bomb card (human hand, turn 33;
  a computer bomb match), the +5 card (human hand, turn 37; a computer trade-in), the wildcard (human hand, turn 45), the empty-the-hand card (human draw,
  turn 25), the +8 trade-in message (a computer, turn 43) and the protection card (the yellow seat's hand, at the bomb notice). The +15 card was not seen
  in about 31 draws.
- **Cited by:** E018-r0007.

### Q-BON-05 (C-CRD-03) - a card per capturing turn

- **Status:** narrowed
- **Why narrowed:** F014's plan asks for at least 20 human turns and 20 computer turns split by captures, and a human turn ending in a forfeited attack
  after an earlier capture. This sitting has 12 human turns (6 with a capture, 6 without) and 34 computer turns, and no forfeited human attack; counted
  with IP1 026 (13 human turns) the human arm is 25 turns, but the forfeit case is still not seen.
- **This sitting:** over 45 of the 46 turns (all but turn 46, whose capture draw the elimination hides; the card counts of turns 43 to 45 are read from the card events, not from a next turn start): in the turns without a capture the seat's count did not change (6 human, 6 computer), apart from
  one computer trade-in at the start of a turn (yellow, turn 26, 5 to 2, three cards out, no draw). In capturing turns with fewer than 5 cards and no trade-in
  the count rose by exactly 1 (5 human, 21 computer). In the other capturing turns: three
  draws emptied the hand (green turn 24, human turn 25, green turn 44), three had a trade-in with a capture (green 16: three out, one drawn; red 43: three out, one drawn; green 44: the bomb trade-in, three out, then the empty hand), one had 5 cards and stayed at 5 (yellow, turn 42).
  Every one of these observations agrees with the claim. A failed human attack cancelling the draw is not tested.
- **Cited by:** E018-r0007.

### Q-BON-06 (C-CRD-04) - five cards, discard on a full hand

- **Status:** narrowed
- **This sitting:** no seat ever showed more than 5 cards. Yellow reached 5 at turn 22 and captured again with 5 at turn 42 (still 5, no sixth); the human never held
  more than 3. At the elimination of the human seat (10:42.90) the capturing yellow seat went from 4 to 5 while the eliminated hand of 3 went to 0: the hand
  limit held. The human discard prompt was not seen (never at 5).
- **Cited by:** E018-r0007.

### Q-BON-07 (C-CRD-05) - one set per turn, what is a set

- **Status:** narrowed
- **This sitting:** 4 trade-ins, all computer, at most one per seat-turn: plus 5 (green, turn 16), doubling (yellow, turn 26), plus 8 (red, turn 43), bomb match
  (green, turn 44); each took 3 cards from the hand and the capture draw still followed where there was a capture. The human never traded: its hand never held a set
  (two doubling cards at turn 13, then the empty hand; bomb, +5 and a wildcard at turn 45 is no set). The trade-in offer to the human was not seen.
- **Cited by:** E018-r0007.

### Q-BON-08 (C-CRD-06) - the bomb card

- **Status:** unestablished
- **This sitting:** the bomb match (green, turn 44) was cancelled by the protection card (see Q-BON-09), so the bomb's effect on a country was not seen; the human did
  not play a bomb (a bomb card was in its hand from turn 33).
- **Cited by:** E018-r0007.

### Q-BON-09 (C-CRD-07) - the anti-bomb card

- **Status:** narrowed
- **This sitting:** at the bomb match (09:46.0) a notice at 09:53.4 to 09:55.9 said the defending country had the protection; the yellow seat's hand went from 5 to 4
  at 09:55.97 (the only hand besides the trading seat's to change) and green's pool stayed 12. One case, the second after IP1 026's.
- **Cited by:** E018-r0007.

### Q-BON-10 / Q-BON-11 (C-CRD-05, C-REI-03) - trade-in effects on the pool

- **Status:** narrowed
- **This sitting:** plus 5 (green, turn 16): pool 6 became 11 (04:03.5). Doubling (yellow, turn 26, no island): pool 4 became 8 (05:52.1). Bomb match (green turn 44): pool
  unchanged at 12. Plus 8 (red, turn 43): the new pool was not read. The doubling of an amount with an island bonus is not separated (no island at turn 26).
- **Cited by:** E018-r0007.

## Income

### Q-REI-01 / Q-REI-02 (C-REI-01, C-REI-02) - income from the territory count, the floor of 2

- **Status:** narrowed
- **Static claim:** the country part is the count divided by 3, rounded down, raised to 2; the island bonus is added after; no first-turn exception.
- **This sitting:** the 12 human turns (no island named at turns 1, 37, 41 and 45 by eye, and the others agree with a pool of exactly the formula) read, by count: 9 gave 3,
  8 gave 2 (three turns), 9 gave 3, 10 gave 3, 7 gave 2 (two), 6 gave 2, 5 gave 2, 3 gave 2, 2 gave 2: the counts of 2, 3, 5, 6 and 7 get the floor of 2 and the first
  turn (count 9, pool 3) is not special. Counts of 1 and 12 and 15 were not reached; the island amount of the computer turns was not read, so those turns are not separated.
- **Cited by:** E018-r0007.

### Q-REI-03 (C-REI-04) - placing the pool

- **Status:** narrowed
- **This sitting:** the human places through a counter that starts at 0 with an all button, plus and minus buttons and a place button, after clicking a country; 12
  placements, the whole pool each time, in one go except turn 1 (2, then 1); the pool message counts down; the counter never exceeded the pool. The over-pool and 999
  cases are untested.
- **Cited by:** E018-r0008.

### Q-REI-05 - army growth over a game

- **Status:** unestablished
- **This sitting:** territory counts and card counts of all four seats at each of 46 turn starts are recorded (r0007); the map counters of the human seat's stacks are in r0006
  and r0008, but armies per seat are not shown on the panel, so growth is not read. One game.

## Setup, turns, events, ending

### Q-SET-04 (C-SET-01) - the options screen

- **Status:** corroborated (a second visit; the first target was one)
- **This sitting:** the options screen at 00:01.0 to 00:03.0 shows the same groups and defaults as IP1 026 (four seat toggles with one human and three computers, a
  five-entry starting-armies dial with the second entry highlighted, a three-entry strength dial, a four-entry event dial, a three-entry speed dial, a sound icon, a
  save-as-default and a play button).
- **Cited by:** E018-r0008.

### Q-STA-01 / Q-STA-03 (C-STA-03, C-STA-05) - the deal

- **Status:** narrowed
- **This sitting:** a second deal: counts blue 9, yellow 11, red 10, green 16 (sum 46), the human at 9 with the middle strength (level 2, claim: 9); the first seat to play was
  the human seat (IP1 026: yellow). Two deals of the target 10.
- **Cited by:** E018-r0008.

### Q-TRN-02 (C-TRN-02) - seat order

- **Status:** narrowed
- **This sitting:** the playing seat followed blue, yellow, red, green for all 46 turns before the human seat was out (11 full rounds and 2 more); after the elimination the
  marker skipped the human seat for every turn of the play-out, and after red reached 0 (10:48.4) it alternated yellow and green: the skip of an eliminated seat is seen
  twice. The play-out's turns are too fast (0.03 to 0.2 s) to count one by one.
- **Cited by:** E018-r0007.

### Q-TRN-05 - game length

- **Status:** unestablished
- **This sitting:** one game: 46 player-turns (12 human) to the human's elimination at 10:42.9 and 10:49.0 to the end, at the owner's own pace. Two games in two sittings
  (55 and 46 turns) are not a distribution.
- **Cited by:** E018-r0007, E018-r0008.

### Q-HAZ-01 / Q-HAZ-02 / C-VIC-04 - event messages

- **Status:** narrowed
- **This sitting:** three event messages in 46 turns, all between turns and all of one kind (a production-centre increase): 03:52.0 to 03:57.0 (between turns 15 and 16), 09:26.0
  to 09:31.0 (42 and 43) and 10:03.25 to 10:08.25 (44 and 45); none before turn 16; 3 of the 40 turn changes from turn 6 on, about 7.5 per cent (the claim's range is 1 in 8
  to 1 in 21 by setting; the setting was the middle one). With IP1 026 (2 of 49): 5 of 89. No seat held 39 or more countries before the play-out.
- **Cited by:** E018-r0009.

### Q-VIC-01 / Q-SUR-05 (C-VIC-01, the elimination prompt) - the end

- **Status:** narrowed
- **This sitting:** the human seat was eliminated by a computer capture (attack 86, strip from 10:42.70; the seat at 0 countries at 10:42.87, with its 3 cards moving to the capturer);
  the prompt with an accept-the-loss button and a keep-playing button came at 10:42.97; the owner's reply was to keep playing (the prompt closed at 10:46.97, the stop-playing
  control stayed on the bottom bar and was not pressed); the remaining conquests ran at 0.03 to 0.2 s per attack with no per-attack screen, the yellow seat held 46 at 10:49.00 and the winner
  dialog came at 10:49.2. The attack-round bonus after the elimination (C-AI-03) cannot be read in a play-out that short.
- **Cited by:** E018-r0008, E018-r0009.

## Computer opponent

### C-AI-03 / C-AI-04 (Q-AI-01, Q-AI-04) - attacks and turns with none

- **Status:** narrowed
- **This sitting:** 74 computer attacks in 34 computer turns recorded with counts before and after (table above); the gates of Q-CMB-01 and Q-CMB-03 hold in all 73 resolved. Three computer
  turns had no attack at all (turn 26, yellow seat, 12 countries; turn 27, red, 10; turn 35, red, 8), 3 of 34, about 9 per cent (the static reading gives about 1 in 22 for a seat
  with 18 or fewer countries, expected 1.5); the cause (the skip draw or no qualifying pair) is not visible. The target is 20 games.
- **Cited by:** E018-r0006, E018-r0007.

### Q-AI-05 / Q-AI-02 / C-AI-06 - placement and cards

- **Status:** unestablished for placement (the computer places with no screen); the computer's trade-in priority is only partly visible (see Q-BON-07).

### Q-AI-07 - strength against scripted opponents

- **Status:** unestablished (one game with an unscripted human; a win rate needs many games).

### C-AI-05 (Q-AI-04's move half) - the computer's end-of-turn move

- **Status:** narrowed
- **This sitting:** 7 moves; every source was off the 23-country list (the claim excludes key sources), six of the seven destinations were on it (the move 19 to 22 was not); each moved all
  but one army and the destination was a neighbour. Whether the source was the seat's largest eligible country was not checked.
- **Cited by:** E018-r0008.

## What only a human sitting shows (constraint E)

These rest on the owner's videos, and on this one for the sitting's own readings; none is a rule claim.

- The owner did not build the stacks the sitting was meant to test: the largest human stack was 6, and the owner quit seven of 13 battles at 3 or 2 armies (attacks 1, 2, 8, 27, 33, 43, 69),
  five of them from a 3 against 2 position after starting with 4 or 5.
- At the capture of attack 15 the owner moved the counter up to all but one (3 of 4) and then back to 2 before pressing done; at attack 23 it moved in 2 of 3 possible; in the other four captures it
  left the counter at 1.
- The human seat shrank from 9 countries to 3 by turn 41 and 2 by turn 43, and was eliminated at turn 46 by attack 86; the owner chose to keep playing at 10:46.97 and did not stop the play-out.
- The owner pressed the card button with an empty hand at 02:24.6 and the card screen showed five empty slots.
- The owner placed the whole pool every turn on one country (once split over two), and in all 12 turns the country it placed on (or, in turn 1, the two) was the attacker of that turn's attack or attacks (13 of 13 attacks).
- The computer's answer to the owner's play is not separable from its own policy here; the data above is the computer's play, with no model-driven sitting to compare.

## Re-reads (rule 20)

A re-read of `IP1 027.mp4` writes new files beside r0006..r0009 (the next free record numbers) with their own frame hashes, and says which record it cross-references; these records stay as written.

**Correction note (Luna's review of PR #186, R1):** E018-r0006 lists attack 87 twice: two identical `step: 87` observations, a copy made while writing. It is one attack (the unresolved play-out attack at 10:47.867), and every count above treats it as one: 87 attacks, 86 resolved plus one unresolved. The record stays as written. Anyone reading r0006 counts its step-87 observations once.

---

# IP1 028 sitting

The fourth owner sitting (2026-10-11, owner-driven Bandicam capture, 18:23, video sha256
`964272f436c11b76089c4fde0f37bec0342d73dbc3b7f085b137e9df6ee13723`, Bandicam 8.3.0.2533 per the file's encoder
tag; frame timestamps are irregular, 22095 frames in 1102.77 s, so offsets are container timestamps, not frame
numbers). One game from the title screen to the title screen after the game: the options screen at 00:03, the
deal at 00:12.8, 47 player-turns (13 human, 34 computer), 76 attacks (32 human, 44 computer), 6 human moves,
5 computer moves, 4 trade-ins (2 human, 2 computer) and 2 event messages. **The owner won**: the human seat held
33 countries from 17:52.07, the computers offered to concede at 18:10.75 (between turns, after the human turn that
took the 33rd country), the owner pressed the accept button at about 18:14.5, the winner dialog came at 18:15.27,
the scoreboard screen at 18:19.03 and the title screen at 18:21.03. The game was won by the computers'
concession at 33 of 46 countries, not by conquest (yellow 6 and green 7 countries were left).

Records, all immutable, `runtime.platform` `windows-native-bandicam` (built on PR #186's IP1 027 records, numbered
from E018-r0010):

- `E018-r0010`: the 76 attacks (start counters, strip states, endings, capture splits, the human move-in counters),
  nine frames.
- `E018-r0011`: the 47 turn starts (counts, pools, cards), the card draws, the two human trade-ins, the two computer
  trade-ins, both bombs, the elimination of the red seat; ten frames.
- `E018-r0012`: the options screen, the deal, the 13 human placements, the 6 human moves and the move controls;
  eleven frames.
- `E018-r0013`: the two event messages, army totals at 19 moments, the seat order, the concession offer, how the
  human won, the scoreboard and title screens; six frames.
- `E018-r0014`: the five computer moves and one computer stop at 8 against 9.

Frames are in the bundle store by hash (`IP1-028`), listed in `evidence/E018/E018-r0010..14.manifest.json`; the video and
the frames are never committed (rule 18). Everything was read by pixels (glyph-shape matching of the strip, the scoreboard
and the map digits, colour regions; no OCR); the readers are those of IP1 027, with their digit templates extended
(a first-pass template miss on larger stacks was found by listing every unclassified glyph, clustering the 389 map glyphs
and 4604 scoreboard glyphs that failed to match, and labelling each cluster by eye, before any reading was used).
Four checks backed the readings: every one of the 233 strip steps is a single loss on one side (none was (1,1) or larger);
for all 21 computer captures and 27 of the 28 human captures the two country counters after the capture add up to the
attacker's armies at the capture (attack 41 is the exception, below); the first and last strip states of eight human attacks (2, 38, 41, 53, 64, 71, 74, 76) were re-read by eye on crops of the frames and matched, and the splits of
attacks 10, 26 and 41 and the stop of attack 70 were re-read by eye on map crops; and every attack's two countries are
neighbours in the F017 border tables (76 of 76).

**One anomaly, not explained.** In attack 41 (human, country 31 against country 32, 07:00.4 to 07:12.6) the attacker held
3 armies at the capture (strip 3/2, 3/1; the map counter of country 31 read 3 before, during and after), the move-in counter
stayed at 1, the owner pressed the done button, and the two countries then read 3 and 1: four armies on the board where three
were at the capture. All other 27 human captures and all 21 computer captures conserve the total. Read twice on the map
(07:01.2 and 07:12.8) and once on the strip. It could be a read of 31 that is one low (the digit shape is clear), or a rule
that adds an army when the attacker would be left with 2; one case, so no rule is claimed.

## What the owner played, and what the video shows

The owner meant to play card trade-ins, moves and a full game that is won. All three are in the video. The owner also
built exact large stacks: the human's stacks after placement reached 16 (turn 27), 14, 25, 22, 33 (turn 41), 20 (turn 44) and
27 (turn 47), and 32 attacks started from 3 to 33 armies. **But every human defender held only 1 to 4 armies**, so none
of E021's open size cells is met: even 4 against 6, 8 against 7, 9, 10 (the human's 8-army attacks were 8 against 3 and 8 against 1), 12
against 11 to 14 (12 against 2); underdog 12 and 20 (the defender was never stronger). The E021 progress counter counts only E021
records and stays at 30 of 40.

Every human attack, with its start and the cell it fits (E021's cells, for the main session; nothing here is counted in E021):

| # | offset | from>to | start | strip states | ending | Session A cell it fits |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 00:48.133 | 37>38 | 6 v 1 | 6/1 5/1 | capture at 5; moved in 1, kept 4 | none |
| 3 | 00:54.333 | 37>40 | 4 v 1 | 4/1 | capture at 4; moved in 1, kept 3 | none |
| 7 | 01:51.233 | 40>41 | 6 v 2 | 6/2 5/2 4/2 4/1 3/1 2/1 | quit at 2/1 | quit cell |
| 13 | 02:32.533 | 40>41 | 5 v 1 | 5/1 4/1 3/1 2/1 | quit at 2/1 | quit cell |
| 20 | 03:18.700 | 40>41 | 5 v 1 | 5/1 | capture at 5; moved in 4, kept 1 | none |
| 21 | 03:26.667 | 41>43 | 4 v 2 | 4/2 3/2 | quit at 3/2 | quit cell |
| 25 | 04:14.200 | 41>43 | 6 v 2 | 6/2 5/2 5/1 4/1 3/1 2/1 | quit at 2/1 | quit cell |
| 32 | 04:54.567 | 41>43 | 5 v 1 | 5/1 4/1 | capture at 4; moved in 3, kept 1 | none |
| 38 | 06:29.333 | 37>36 | 16 v 3 | 16/3 16/2 15/2 15/1 | capture at 15; moved in 14, kept 1 | none |
| 39 | 06:36.733 | 36>35 | 14 v 1 | 14/1 13/1 12/1 11/1 10/1 9/1 8/1 | capture at 8; moved in 7, kept 1 | none |
| 40 | 06:44.833 | 35>34 | 7 v 3 | 7/3 7/2 7/1 | capture at 7; moved in 6, kept 1 | none |
| 41 | 07:00.367 | 31>32 | 3 v 2 | 3/2 3/1 | capture at 3; moved in 1, kept 3 (anomaly: 4 on the board) | none |
| 45 | 08:47.033 | 31>33 | 14 v 2 | 14/2 14/1 13/1 | capture at 13; moved in 1, kept 12 | none |
| 46 | 09:05.300 | 31>30 | 12 v 2 | 12/2 11/2 11/1 10/1 | capture at 10; moved in 1, kept 9 | none |
| 47 | 09:16.600 | 31>29 | 9 v 3 | 9/3 9/2 9/1 | capture at 9; moved in 1, kept 8 | none |
| 53 | 10:26.567 | 33>24 | 25 v 3 | 25/3 24/3 23/3 22/3 21/3 20/3 20/2 19/2 19/1 | capture at 19; moved in 18, kept 1 | none |
| 54 | 10:41.033 | 24>23 | 18 v 4 | 18/4 18/3 18/2 18/1 17/1 16/1 | capture at 16; moved in 2, kept 14 | none |
| 55 | 11:03.433 | 24>25 | 14 v 1 | 14/1 13/1 12/1 11/1 10/1 | capture at 10; moved in 1, kept 9 | none |
| 56 | 11:15.900 | 24>26 | 9 v 3 | 9/3 8/3 8/2 8/1 | capture at 8; moved in 1, kept 7 | none |
| 60 | 12:21.900 | 43>8 | 22 v 4 | 22/4 21/4 20/4 19/4 18/4 17/4 17/3 17/2 16/2 16/1 | capture at 16; moved in 1, kept 15 | none |
| 61 | 12:33.967 | 43>44 | 15 v 4 | 15/4 14/4 14/3 14/2 13/2 13/1 | capture at 13; moved in 1, kept 12 | none |
| 64 | 13:54.667 | 43>8 | 33 v 4 | 33/4 32/4 32/3 32/2 31/2 31/1 30/1 29/1 28/1 | capture at 28; moved in 27, kept 1 | none |
| 65 | 14:07.233 | 8>7 | 27 v 3 | 27/3 26/3 26/2 26/1 | capture at 26; moved in 25, kept 1 | none |
| 66 | 14:19.567 | 7>9 | 25 v 3 | 25/3 25/2 24/2 23/2 23/1 22/1 | capture at 22; moved in 10, kept 12 | none |
| 68 | 15:23.667 | 23>45 | 8 v 3 | 8/3 8/2 7/2 7/1 | capture at 7; moved in 1, kept 6 | none |
| 69 | 15:31.933 | 44>46 | 15 v 3 | 15/3 14/3 13/3 12/3 11/3 10/3 10/2 10/1 | capture at 10; moved in 4, kept 6 | none |
| 71 | 17:00.133 | 7>6 | 27 v 2 | 27/2 26/2 25/2 24/2 23/2 23/1 22/1 21/1 20/1 19/1 18/1 | capture at 18; moved in 1, kept 17 | none |
| 72 | 17:14.333 | 7>5 | 17 v 3 | 17/3 16/3 16/2 15/2 14/2 13/2 13/1 12/1 | capture at 12; moved in 11, kept 1 | none |
| 73 | 17:23.100 | 5>4 | 11 v 1 | 11/1 | capture at 11; moved in 1, kept 10 | none |
| 74 | 17:29.033 | 9>10 | 18 v 1 | 18/1 | capture at 18; moved in 8, kept 10 | none |
| 75 | 17:38.800 | 10>12 | 8 v 1 | 8/1 | capture at 8; moved in 7, kept 1 | none |
| 76 | 17:51.033 | 46>14 | 15 v 2 | 15/2 15/1 | capture at 15; moved in 14, kept 1 | none |

Reading the table: 28 captures and 4 quits (by the owner, at 2 against 1 three times, attacks 7, 13 and 25, and at 3 against 2 once, attack 21); no human attack started
below 3 armies, none at equal strength, none against a stronger defender; the human was never reduced to 1 army (the lowest end was 2).
Cells fitted: **quit**, four attacks (7, 13, 21, 25), each after at least two exchanges the strip showed. **Busy**: five human turns with 3 or
more fights, each fight a battle with an exchange the strip showed: turn 27 (4 fights: 38, 39, 40, 41; ended by a move), turn 31 (3: 45, 46, 47; ended by
a move), turn 35 (4: 53 to 56; ended by a move), turn 41 (3: 64, 65, 66; no move seen, the card screen followed) and turn 47 (6: 71 to
76; no move seen, the card screen followed); E021's busy row was already full (10 of 10). No tiny cell (3 against 1: no attack of 3 against
1; attack 41 was 3 against 2), no even cell, no underdog cell, no lost cell (no failed attack).

## The attacks: every one, before and after

`#` is the order in the video (`r0010`, step = `#`). `offset` is the first strip frame. `seat` is the attacking
seat, `C` computer, `H` human. `before` is attacker/defender armies as the country counters show them just
before the strip appeared (for the computer the strip starts one exchange in, so this differs from the strip's first state in 37 of 44 attacks; for the human they agree in 32 of 32);
`after` is the last state, or, for a capture, the attacker's armies at the capture with the defender at 0, then
the split (computer: armies kept in the attacker's country and armies placed in the captured country; human:
the move-in the owner chose and what the attacker keeps). A `*` marks a split number taken from the total because
the capture flash hid that counter. A stop or quit leaves both countries with their owners.

| # | offset | seat | from>to | before | after | ending |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 00:29.733 | Green C | 23>45 | 6/3 | 5/0, then keeps 3 gets 2 | capture |
| 2 | 00:48.133 | Blue H | 37>38 | 6/1 | 5/0, then in 1 keeps 4 | capture |
| 3 | 00:54.333 | Blue H | 37>40 | 4/1 | 4/0, then in 1 keeps 3 | capture |
| 4 | 01:17.267 | Yellow C | 46>44 | 7/5 | 3/0, then keeps 2 gets 1 | capture |
| 5 | 01:24.133 | Red C | 3>2 | 4/1 | 4/0, then keeps 3 gets 1 | capture |
| 6 | 01:30.000 | Green C | 18>15 | 6/2 | 6/0, then keeps 3 gets 3 | capture |
| 7 | 01:51.233 | Blue H | 40>41 | 6/2 | 2/1 | quit |
| 8 | 02:02.833 | Yellow C | 46>45 | 6/2 | 4/0, then keeps 1 gets 3 | capture |
| 9 | 02:08.867 | Red C | 22>21 | 3/1 | 2/1 | stop |
| 10 | 02:09.467 | Red C | 35>34 | 8/2 | 3/1 | stop |
| 11 | 02:10.967 | Red C | 30>28 | 3/1 | 2/1 | stop |
| 12 | 02:11.567 | Red C | 35>34 | 3/1 | 3/0, then keeps 1 gets 2 | capture |
| 13 | 02:32.533 | Blue H | 40>41 | 5/1 | 2/1 | quit |
| 14 | 02:48.367 | Yellow C | 8>7 | 6/2 | 2/2 | stop |
| 15 | 02:54.033 | Red C | 25>24 | 8/3 | 2/2 | stop |
| 16 | 02:55.767 | Red C | 34>32 | 4/3 | 3/2 | stop |
| 17 | 03:00.700 | Green C | 16>20 | 6/2 | 2/1 | stop |
| 18 | 03:02.000 | Green C | 21>22 | 4/2 | 3/2 | stop |
| 19 | 03:02.700 | Green C | 21>20 | 3/1 | 2/1 | stop |
| 20 | 03:18.700 | Blue H | 40>41 | 5/1 | 5/0, then in 4 keeps 1 | capture |
| 21 | 03:26.667 | Blue H | 41>43 | 4/2 | 3/2 | quit |
| 22 | 03:36.000 | Yellow C | 8>7 | 9/2 | 6/0, then keeps 3 gets 3 | capture |
| 23 | 03:42.433 | Red C | 25>26 | 9/3 | 5/0, then keeps 2 gets 3 | capture |
| 24 | 03:59.033 | Green C | 16>20 | 5/1 | 4/0, then keeps 1 gets 3 | capture |
| 25 | 04:14.200 | Blue H | 41>43 | 6/2 | 2/1 | quit |
| 26 | 04:25.900 | Yellow C | 4>5 | 10/3 | 9/0, then keeps 1 gets 8 | capture |
| 27 | 04:28.200 | Yellow C | 5>3 | 8/3 | 3/3 | stop |
| 28 | 04:34.600 | Red C | 26>24 | 5/2 | 3/1 | stop |
| 29 | 04:35.533 | Red C | 25>24 | 5/1 | 2/1 | stop |
| 30 | 04:36.533 | Red C | 9>7 | 5/3 | 3/3 | stop |
| 31 | 04:41.233 | Green C | 23>22 | 6/2 | 3/0, then keeps 2 gets 1 | capture |
| 32 | 04:54.567 | Blue H | 41>43 | 5/1 | 4/0, then in 3 keeps 1 | capture |
| 33 | 05:19.200 | Yellow C | 12>10 | 9/3 | 3/3 | stop |
| 34 | 05:20.733 | Yellow C | 11>9 | 7/3 | 5/0, then keeps 3 gets 2 | capture |
| 35 | 05:23.067 | Yellow C | 13>15 | 6/3 | 3/1 | stop |
| 36 | 05:28.867 | Red C | 30>29 | 6/2 | 6/0, then keeps 3 gets 3 | capture |
| 37 | 05:30.667 | Red C | 3>5 | 5/4 | 3/4 | stop |
| 38 | 06:29.333 | Blue H | 37>36 | 16/3 | 15/0, then in 14 keeps 1 | capture |
| 39 | 06:36.733 | Blue H | 36>35 | 14/1 | 8/0, then in 7 keeps 1 | capture |
| 40 | 06:44.833 | Blue H | 35>34 | 7/3 | 7/0, then in 6 keeps 1 | capture |
| 41 | 07:00.367 | Blue H | 31>32 | 3/2 | 3/0, then in 1 keeps 3 | capture |
| 42 | 07:55.100 | Yellow C | 11>10 | 6/3 | 5/0, then keeps 4 gets 1 | capture |
| 43 | 08:02.767 | Red C | 30>28 | 3/1 | 2/1 | stop |
| 44 | 08:07.367 | Green C | 15>14 | 9/3 | 5/0, then keeps 4 gets 1 | capture |
| 45 | 08:47.033 | Blue H | 31>33 | 14/2 | 13/0, then in 1 keeps 12 | capture |
| 46 | 09:05.300 | Blue H | 31>30 | 12/2 | 10/0, then in 1 keeps 9 | capture |
| 47 | 09:16.600 | Blue H | 31>29 | 9/3 | 9/0, then in 1 keeps 8 | capture |
| 48 | 09:53.833 | Yellow C | 13>1 | 9/6 | 6/0, then keeps 4 gets 2 | capture |
| 49 | 09:56.933 | Yellow C | 9>14 | 7/3 | 3/1 | stop |
| 50 | 09:58.467 | Yellow C | 5>3 | 15/5 | 9/0, then keeps 3 gets 6 | capture |
| 51 | 10:11.733 | Green C | 14>46 | 4/3 | 2/3 | stop |
| 52 | 10:12.567 | Green C | 24>25 | 4/2 | 4/0, then keeps 3 gets 1 | capture |
| 53 | 10:26.567 | Blue H | 33>24 | 25/3 | 19/0, then in 18 keeps 1 | capture |
| 54 | 10:41.033 | Blue H | 24>23 | 18/4 | 16/0, then in 2 keeps 14 | capture |
| 55 | 11:03.433 | Blue H | 24>25 | 14/1 | 10/0, then in 1 keeps 9 | capture |
| 56 | 11:15.900 | Blue H | 24>26 | 9/3 | 8/0, then in 1 keeps 7 | capture |
| 57 | 11:52.367 | Yellow C | 3>2 | 20/3 | 14/0, then keeps 13 gets 1 | capture |
| 58 | 11:55.600 | Yellow C | 13>15 | 8/6 | 6/0, then keeps 3 gets 3 | capture |
| 59 | 12:02.100 | Green C | 21>23 | 4/1 | 2/1 | stop |
| 60 | 12:21.900 | Blue H | 43>8 | 22/4 | 16/0, then in 1 keeps 15 | capture |
| 61 | 12:33.967 | Blue H | 43>44 | 15/4 | 13/0, then in 1 keeps 12 | capture |
| 62 | 12:59.700 | Yellow C | 7>8 | 14/1 | 12/0, then keeps 3 gets 9 | capture |
| 63 | 13:01.733 | Yellow C | 9>14 | 5/2 | 3/2 | stop |
| 64 | 13:54.667 | Blue H | 43>8 | 33/4 | 28/0, then in 27 keeps 1 | capture |
| 65 | 14:07.233 | Blue H | 8>7 | 27/3 | 26/0, then in 25 keeps 1 | capture |
| 66 | 14:19.567 | Blue H | 7>9 | 25/3 | 22/0, then in 10 keeps 12 | capture |
| 67 | 14:51.067 | Green C | 17>15 | 5/3 | 3/3 | stop |
| 68 | 15:23.667 | Blue H | 23>45 | 8/3 | 7/0, then in 1 keeps 6 | capture |
| 69 | 15:31.933 | Blue H | 44>46 | 15/3 | 10/0, then in 4 keeps 6 | capture |
| 70 | 16:09.633 | Yellow C | 11>9 | 12/10 | 8/9 | stop |
| 71 | 17:00.133 | Blue H | 7>6 | 27/2 | 18/0, then in 1 keeps 17 | capture |
| 72 | 17:14.333 | Blue H | 7>5 | 17/3 | 12/0, then in 11 keeps 1 | capture |
| 73 | 17:23.100 | Blue H | 5>4 | 11/1 | 11/0, then in 1 keeps 10 | capture |
| 74 | 17:29.033 | Blue H | 9>10 | 18/1 | 18/0, then in 8 keeps 10 | capture |
| 75 | 17:38.800 | Blue H | 10>12 | 8/1 | 8/0, then in 7 keeps 1 | capture |
| 76 | 17:51.033 | Blue H | 46>14 | 15/2 | 15/0, then in 14 keeps 1 | capture |

Counts this sitting adds to the per-claim totals (constraint E): 319 exchanges (233 strip steps, 49 capture exchanges inferred from
the defender's last army, 37 first exchanges of computer attacks read from the before-counters), 76 attacks (32 human, 44 computer), 47 turn
starts with the army pool, 13 human placements, 6 human moves and 5 computer moves, 28 human move-ins, 4 trade-ins, 2 bombs, 2 event messages, 1
concession.

Outcome words follow `walkthroughs/f011-questions.md`: `corroborated` when the count target is met and play
matches the static claim, `narrowed` when it matches in the part played, `unestablished` when nothing in the
video bears on it.

## Combat

### Q-CMB-01 (C-CMB-01) - who may attack, human and computer

- **Status:** narrowed
- **Static claim:** a human needs at least 2 armies and at least as many as the target; the computer needs more than the target by a drawn margin of 0 or 1,
  so never at equal strength.
- **This sitting:** computer, 44 starts: none at equal or lower strength; margin 1 in 3 (attacks 16, 37 and 51, with attackers of 4, 5 and 4), 2 in 12, 3 in 8, 4 in 10 and up to 17.
  With IP1 026 (94 starts) and IP1 027 (73): 211 computer starts, none at equal strength, against a target of 100 or more (the computer arm is met).
  Human, 32 starts: all had at least 3 armies and more than the target (margin 1 once: attack 41, 3 against 2); no equal-strength start and no refused order
  was shown, and the 16-case grid was not played (no cell reached, see above).
- **Why narrowed:** the human boundary and the refusal are untested.
- **Cited by:** E018-r0010.

### Q-CMB-02 (C-CMB-02) - equality, not a ratio

- **Status:** narrowed
- **This sitting:** the computer's margin-1 starts have attackers of 4 to 5 (with IP1 027's, attackers of 3 to 8); the 5 computer starts with 10 or more armies were 10 against 3 (attack 26), 12 against 10 (attack 70, margin 2),
  14 against 1 (62), 15 against 5 (50) and 20 against 3 (57): a 12-army attacker started at a margin of only 2, so the gate does not need a margin that grows with the stack. A margin-1 start at 12 or more was not seen; the human boundary (N in 4, 8, 12, 20) was not played, though the human attacked from
  stacks of 8, 12 and 20 or more against defenders of 1 to 4 and none was refused.
- **Cited by:** E018-r0010.

### Q-CMB-03 (C-CMB-03) - minimum attacking stack

- **Status:** narrowed (computer arm met over the sittings; the human arm unestablished)
- **Static claim:** human minimum 2; computer minimum 3 or 4 before a capture this turn (4 or 5 for a country on the fixed 23-country list) and 4 after one (5 on the list).
- **This sitting:** the computer's smallest start by class: ordinary country before a capture 3 (21 starts), list country before a capture 4 (16), list country after a
  capture 5 (7); no ordinary-country start after a capture (that class is empty here); no start below its class minimum in 44. The human's smallest start was 3 (attack 41, 3 against 2); no attempt with 1 or 2 armies.
- **Cited by:** E018-r0010 (list membership from `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json`).

### Q-CMB-04 (C-CMB-04) - one die each, one army per exchange, five-at-once batching

- **Status:** narrowed
- **This sitting:** 319 exchanges; every strip step changed exactly one counter by one (233 steps, none of (-1,-1) or larger). Exchanges against a one-army defender by attacker
  size: 3: 14, 4: 17, 5: 17, 10: 5 (size 2: none); 6 to 9: 21, 11 and over: 43 (to 31). Over the three sittings the sizes 2, 3, 4, 5, 10 stand at 1, 46, 79, 64, 18 (target 100 or more each). The five-exchange
  pass needs more than 40 against more than 15 (computer) or more than 35 against more than 15 (human): the largest pairs were 33 against 4 (human) and 20 against 3 (computer), the defenders far below 15, so batching was not exercised.
- **Cited by:** E018-r0010.

### Q-CMB-05 (C-CMB-04, defender-size half) - defender size

- **Status:** narrowed
- **This sitting:** attacker-loss share by defender size at the exchange: 1 army 68/117 (58.1%), 2 armies 50/93 (53.8%), 3 armies 45/74 (60.8%), 4 or more 20/35 (57.1%); a chi-square test across the four groups
  gives p = 0.83, so no dependence on the defender's size is detected. Defender size 9 was seen (4 exchanges, the attacker lost all 4, attack 70) and 10 once.
- **Cited by:** E018-r0010.

### Q-CMB-06 (C-CMB-05) - ties go to the defender

- **Status:** narrowed
- **Static claim:** ties go to the defender, so the attacker loses an exchange 21 times in 36 (7/12, 58.3%).
- **This sitting:** attacker lost 183 of 319 exchanges (57.4%), 95% interval 51.9% to 62.8%; 7/12 is inside the interval (z = -0.35); an even 50% is not (z = +2.63).
  Over the three sittings (245 of 442, 127 of 237, 183 of 319): 555 of 998 (55.6%), interval 52.5% to 58.7%; 7/12 is inside (z = -1.74), an even 50% is not (z = +3.55).
  Human 74 of 141 (52.5%), computer 109 of 178 (61.2%); the two shares do not differ detectably (Fisher p = 0.14). Dice are not visible, so only the outcome share is tested.
- **Why narrowed:** 998 of the 500 target over the three sittings, but the share is consistent with the claim, not a proof.
- **Other explanations of the 57.4% (Luna's review of PR #187, R4):**
  - *Missed exchanges.* Frames could miss strip steps unevenly between wins and losses. This is mostly excluded: all 233 strip steps are single losses, and the strips reconcile with the before and after counters, so a missed step would show as a two-army jump, and none does. The 49 capture exchanges and the first exchanges are inferred by rule rather than seen. Capture exchanges are always attacker wins, so if anything they pull the loss share down, not up.
  - *Selection of attacks.* Which stacks fight is chosen: the computer attacks only at a margin, and the owner chose the targets. That could shift the share only if an exchange depended on the stack sizes, which is what Q-CMB-05 and Q-CMB-11 test. No dependence on the defender's size is detected (p = 0.83), but it is not excluded at this count.
  - *Five-at-once batching.* Not reached: no stack crossed the thresholds (see Q-CMB-04), so batching cannot have changed what was counted.
  - *Dice that are not uniform.* Not excluded: the dice are never shown, and only the outcome share is tested. 7/12 is the uniform-dice value. A share inside its interval is consistent with uniform dice, but does not prove them.
- **Cited by:** E018-r0010.

### Q-CMB-07 (C-CMB-06) - exactly one army lost per exchange

- **Status:** corroborated
- **This sitting:** 233 strip steps, every one a loss of one army on exactly one side; none lost two or lost one on each side; a 5-army run could not occur (see Q-CMB-04). 49 capture exchanges end with the
  defender's last army gone. With IP1 026 and IP1 027 the strip steps stand at 360, 139 and 233 against the target of 200.
- **Cited by:** E018-r0010.

### Q-CMB-08 (C-CMB-08) - a battle's end, quit, automatic loop

- **Status:** narrowed
- **This sitting:** human, 32 attacks: 28 ended in a capture, 4 were quit by the owner with armies as they stood (attacks 7, 13, 21, 25: ending at 2, 2, 3 and 2 armies), ownership unchanged and no cost seen.
  Whether one click is one exchange is not established (clicks are not visible); consecutive human strip steps are 0.20 to 1.67 s apart (median 0.37 s over 113 intervals), computer steps 0.03 to 0.67 s
  (median 0.17 s over 120). Targets met on count (human 10 attacks, computer 30 battles). Computer, 44 battles: 21 captures, 23 stops without a capture; the attacker's armies at those stops were 2 (ten times),
  3 (twelve) and 8 (once: attack 70, stopped at 8 against 9), never below 2, as the static claim says.
- **Cited by:** E018-r0010, E018-r0014.

### Q-CMB-09 (C-CMB-09) - a failed attack

- **Status:** narrowed (the computer arm met its count, 23 stops against 20; the human arm, 5 failed attacks wanted, saw none)
- **This sitting:** computer, 23 stops without a capture: the defender's country keeps its owner and the counters equal the last strip state in 22 of 23 (attack 18's attacker reads 2 on the map 0.7 s later, one exchange
  more than the strip, with the next attack following at once); the attacker's country keeps at least 2. Human: no attack was lost down to 1 army (four quits at 2 or 3), so the forfeit rule, the card cancellation and the
  turn change are not exercised.
- **Cited by:** E018-r0010.

### Q-CMB-10 (C-CMB-10) - attacks per turn

- **Status:** narrowed
- **This sitting:** computer attacks per turn over 34 turns: 0 in 7 (turns 1, 10, 26, 33, 40, 42, 46; the green seat twice with 5 cards in hand, turns 40 and 46), 1 in 16, 2 in 6, 3 in 4, 4 in 1; none of the 34 turns had more than 4
  attacks. Rounds are not visible, so the drawn rounds of 2 to 5 cannot be checked. Human, 13 turns: 1 attack in 4, 2 in 4, 3 in 2, 4 in 2 and 6 in 1 (turn 47, which ran to the end of the game): the human
  attacked 6 times in one turn with nothing stopping it, so "no limit" is shown to 6; the turns with 3 or more attacks were 5 (turns 27, 31, 35, 41, 47), of a target of 10; three of them ended in a move, two with no move seen (the card screen followed, the owner having
  pressed pass or the equivalent; the button press is not visible).
- **Cited by:** E018-r0010, E018-r0011 (turn assignment from the scoreboard marker), E018-r0012.

### Q-CMB-11 (C-CMB-07) - nothing but counts and dice enters an exchange

- **Status:** narrowed
- **This sitting:** computer attacker-loss share by whether the attacker's country is on the fixed 23-country list: list 63/110 (57.3%), not on the list 46/68 (67.6%), chi-square p = 0.17 (Pearson, no continuity correction, as in the IP1 026 and 027 sections; 0.22, first written here, was the Yates-corrected value; Luna's review of PR #187, R2) (the difference seen is 10 points
  against a 50 to 60 per cent baseline, not significant at this count); no gross effect appears.
- **Cited by:** E018-r0010.

## Capture, moves, ownership

### Q-OWN-01 (C-OWN-01) - armies moved in on a capture

- **Status:** narrowed
- **This sitting:** human, 28 captures: the move-in counter started at 1 each time; the owner moved in all but one 11 times (attacks 20, 32, 38, 39, 40, 53, 64, 65, 72, 75, 76: the counter jumps from 1 to
  attacker armies minus 1 within one frame, the all button; in attack 75 after two plus steps), left it at 1 in 13 (attacks 2, 3, 41, 45, 46, 47, 55, 56, 60, 61, 68, 71, 73), and set other values with the plus and minus buttons in 4 (attack 54: 2 of 16, via 3 and back; 66: 10 of 22;
  69: 4 of 10; 74: 8 of 18); never more than the attacker's armies minus 1; the attacker always kept at least 1; the captured country received exactly the number chosen; the total was conserved in 27 of 28 (attack 41: see the anomaly above). Whether 0
  can be chosen is not shown. Captures from stacks of 2, 3, 5 and 10 (the attacker's armies at the capture): 0, 1, 2 and 3 here (target 3 each; the earlier sittings' counts are in their own sections). Computer, 21 captures: the two counters add up to the
  attacker's armies in all 21, both at least 1; the attacker kept 1 in 4, 2 in 3, 3 in 10, 4 in 3 and 13 in one; keeping 3 is again the commonest (10 of 21), fitting C-AI-07's keep-3 branches; the strongest-neighbour inputs were not read.
- **Cited by:** E018-r0010.

### Q-MOV-01 (C-MOV-01) - moves per turn

- **Status:** narrowed
- **This sitting:** human: 6 moves in 13 turns (turns 3, 27, 31, 35, 38, 44), at most one per turn and each after the turn's last attack with no attack and no second move after it: after the done button the card screen of the turn came within 2 s and the
  turn passed (6 of 6, offsets in E018-r0012). All six followed at least one capture of the same turn, so the attack-first case is 6 (target 5); the case of a move with no attack first was not seen. Computer: 5 moves in 34 turns, never two in one turn, each after the seat's last attack of the turn
  (E018-r0014). The target (10 human turns with a move) is 6 here, 7 with IP1 026, not met.
- **Cited by:** E018-r0012, E018-r0014.

### Q-MOV-02 (C-MOV-02) - all but one

- **Status:** narrowed
- **This sitting:** human, 6 of 6 moves left exactly 1 in the source: from stacks of 3, 2, 8, 2, 8 and 6, moving 2, 1, 7, 1, 7 and 5; all but one is reached with the all button (3 times), with the plus button (once), or by leaving the counter at 1 on a stack of 2
  (twice). Stacks of 2 (twice) and 3 (once) are covered, 5 and 10 not; all-but-two and a counter of 0 were not tried. Computer: 5 of 5 moves left 1 (sources held 3, 3, 6, 3 and 4).
- **Cited by:** E018-r0012, E018-r0014.

### Q-MOV-03 (C-MOV-03) - adjacency, move then attack

- **Status:** narrowed
- **This sitting:** all 11 moves were between neighbouring countries (human 6, computer 5). A country captured earlier in the same turn attacked in that turn 11 times (10 human, 1 computer), so a just-captured country is not blocked. A second move in a turn was not offered (the turn ended
  after the move) and a destination two borders away was not tried (the destination was always picked by clicking, and the six picks were all neighbours); an attack after a move was not possible (the turn ended).
- **Cited by:** E018-r0010, E018-r0012, E018-r0014.

### Move controls seen (the human move, for walkthroughs/coordinates.md)

Source: E018-r0012, steps 0 to 6 of the moves (frame references in its outputs). Mapping from the video to the 800x600 stage: the picture is not black from x 125 to 1859 and y 85 to 1003 of the 1920x1080 frame (a 1735 by 919 area), so
`stage x = (frame x - 125) / 2.169` and `stage y = (frame y - 85) / 1.532` (the stage is stretched, not letter-boxed). Checks: the attack button of the battle panel reads (337, 531) and the pass button (419, 530), the numbers `walkthroughs/coordinates.md`
already has, and the numeral centres of 44 countries land within 5 stage pixels of E021's click points (`experiments/E021-pro-session-a/points.py`). Proposed rows (stage coordinates of the button's centre, all read from the frames named; the buttons are wide, a click anywhere inside works, as the existing table's own coordinates are not centres):

| Action | Stage x, y | Frame offset | Comment |
| --- | --- | --- | --- |
| MOVE (action bar) | 369, 530 | 00:59.0 | the cyan button of the turn menu, between ATTACK (305, 530) and PASS (419, 530); the others are CARD (469, 531) and CANCEL (514, 528) |
| Source prompt: CANCEL | 514, 528 | 01:04.5 | the only button on the source prompt (the left panel asks for the country to move from, with an arrow marker); the country is chosen by clicking it on the map, then the right panel reads "move from country N" (01:05.2) |
| Destination prompt: CANCEL | 514, 528 | 01:05.5 | the only button on the destination prompt; clicking a bordering country opens the counter panel (01:06.4) |
| Move counter: ALL | 309, 539 | 01:06.5 | all but one (counter jumps to source armies minus 1: 1 to 7 at 09:45.1, 1 to 5 at 15:54.1); highlighted gold when the pointer is over it |
| Move counter: PLUS | 373, 539 | 01:06.5 | one more army; counter 1 to 2 at 01:09.5 (move 1) |
| Move counter: MINUS | 420, 539 | 01:06.5 | one fewer army (highlighted at 07:36.0 and 12:49.5 without a change in the counter) |
| Move counter: DONE | 495, 539 | 01:06.5 | confirms; green when the pointer is over it (01:10.5); no further question; the move ends the turn (card screen at 01:11.5) |
| Move counter digit | 496, 514 | 01:06.5 | where the counter is read (starts at 1) |
| Placement counter | same panel | 00:43.0 | ALL (309, 539), PLUS, MINUS and PLACE (495, 539, in the place of DONE) |

The move counter is the same panel as the move-in counter after a capture (done at the same position) and as the placement counter. The countries to click for a move were: source 37 (numeral at stage 516, 404), destination 40 (451, 443) in move 1; 34 (749, 416) and 32 (741, 271) in move 2; 31 (681, 217) and 33 (665, 291) in move 3; 23 (504, 226) and 24 (563, 142) in move 4 and its reverse in move 5; 44 (338, 307) and 46 (350, 252) in move 6.

## Cards and bonuses

### Q-BON-03 (C-CRD-01, C-CRD-02) - kinds seen

- **Status:** narrowed
- **This sitting:** five of the eight kinds appeared in the human's hand: the +8 card (turns 3 and 15), the +5 card (turn 44), the doubling card (turn 31), the bomb card (turns 27 and 47) and the wildcard (turns 23, 35, 38, 41); a computer trade-in announced +8 and another a bomb match. The +15 card, the protection card
  and the empty-the-hand card were not seen in this game (no draw emptied a hand; the red seat's four cards vanished at its elimination, see Q-SUR). The +15 card has not been seen in any of the three sittings; the other kinds have each appeared in at least one.
- **Cited by:** E018-r0011.

### Q-BON-05 (C-CRD-03) - a card per capturing turn

- **Status:** narrowed
- **Why narrowed:** the forfeit case (a failed human attack after an earlier capture) is not seen in any of the three sittings; the human arm is met on count over the sittings (13 human turns here, 13 in IP1 026 and 12 in IP1 027: 38 against the 20 wanted).
- **This sitting:** over the 43 turns with a next turn start of the same seat (all but turns 33, 45, 46 and 47): in the turns without a capture the seat's count did not change (3 human: turns 7, 11, 19; 12 computer). In capturing turns with fewer than 5 cards and no trade-in the count rose by exactly 1 (7 human, 16 computer). Capturing turns with a
  trade-in: the count fell by 2 (3 out, 1 drawn; 2 human, turns 27 and 41; 2 computer, yellow turns 24 and 36). A capturing computer turn with 5 cards (green, turn 34) stayed at 5. Human turn 47's draw (3 to 4) is on the card screen at 18:09. Every observation agrees with the claim.
- **Cited by:** E018-r0011.

### Q-BON-06 (C-CRD-04) - five cards, discard on a full hand

- **Status:** narrowed
- **This sitting:** no seat ever showed more than 5 cards. The green seat held 5 from 08:13.0 to the end and captured once with 5 (turn 34), still 5 at its next start; the human never held more than 4 (turn 38's hand). The human discard prompt was not seen. No hand emptied by a draw in this game.
- **Cited by:** E018-r0011.

### Q-BON-07 (C-CRD-05) - one set per turn, what is a set

- **Status:** narrowed
- **This sitting:** 4 trade-ins, at most one per seat-turn: computer +8 (yellow, turn 24) and bomb match (yellow, turn 36); human +8 from two +8 cards and a wildcard (turn 27) and a bomb from the bomb card and two wildcards (turn 41), each taking 3 cards from the hand; the capture draw still followed. The
  trade-in offer to the human appeared in exactly two turns (27 and 41), both accepted, none declined; at turn 41 the hand held a fourth card (doubling), which the owner left out of the set. The set with one wildcard and one with two wildcards are both shown; three of a kind with no wildcard and a second trade-in in one turn were not tried.
- **Cited by:** E018-r0011.

### Q-BON-08 (C-CRD-06) - the bomb card

- **Status:** narrowed
- **This sitting:** the human bombed country 8 (yellow, 9 armies; clicked on the map; own countries not tried): 9 became 4, within the claim's 1 to half of 9 (4), ownership unchanged, the placement pool unchanged at 21. The computer's bomb match (yellow turn 36) hit country 43 (blue, 3 armies): it read 1, within 1 to half of 3
  (floored at 1), the pool unchanged. Two cases, both inside the range; the draw's uniformity is not testable.
- **Cited by:** E018-r0011, E018-r0012.

### Q-BON-09 (C-CRD-07) - the anti-bomb card

- **Status:** unestablished
- **This sitting:** no protection card was held by a bombed seat (neither bomb met a protection notice).
- **Cited by:** E018-r0011.

### Q-BON-10 / Q-BON-11 (C-CRD-05, C-REI-03) - trade-in effects on the pool

- **Status:** narrowed
- **This sitting:** plus 8 (human, turn 27): pool 8 became 16 (read 8 at 05:39.2 and 16 at 05:51.0, with one island in the message); plus 8 (yellow, turn 24): the pool message after the trade read 19 for two islands, 8 above the pre-trade base of 11; bomb (human, turn 41): pool unchanged at 21 (13:09 and
  13:44); bomb (yellow, turn 36): pool message 16 unchanged. The doubling of a pool and plus 5 and plus 15 were not played in this game.
- **Cited by:** E018-r0011.

## Income

### Q-REI-01 / Q-REI-02 (C-REI-01, C-REI-02) - income from the territory count, the floor of 2

- **Status:** narrowed
- **Static claim:** the country part is the count divided by 3, rounded down, raised to 2; the island bonus is added after; no first-turn exception.
- **This sitting:** the 6 human turns with no island named read exactly the country part: counts 9, 10, 10, 10, 10 and 10 gave 3 each (the first turn is not special); turns with islands: 11 countries gave 8 (3 plus 5), 14 gave 11 (4 plus 7), 17 gave 17 (5 plus 12), 21 gave 21 (7 plus 14), 22 gave 21 (7 plus 14), 25 gave 22 (8 plus 14), 27 gave 26 (9 plus 17), the island amounts
  being sums of the static bonus values (not separated here). The floor of 2 was seen for the computer: red with 3 countries (turn 33) and green with 8 (turns 37, 40, 43, 46) gave 2, and the red seat with 7 countries gave 4 (country part 2 plus an island amount of 2). Counts of 1, 2, 12 and 15 with no island were not reached.
- **Cited by:** E018-r0011.

### Q-REI-03 (C-REI-04) - placing the pool

- **Status:** narrowed
- **This sitting:** the human places through a counter that starts at 0 with an all button, plus and minus buttons and a place button, after clicking a country; 13 placements, the whole pool each time (3 times split over two to four countries: 15 and 1, 14 and 8, 7, 9, 4 and 6); the panel counter counts down after the place button at about 0.17 s per army; the counter never exceeded the pool.
  The over-pool and 999 cases are untested.
- **Cited by:** E018-r0012.

### Q-REI-05 - army growth over a game

- **Status:** narrowed (one game's curve, no distribution)
- **This sitting:** armies by colour (blue, the human, / yellow / red / green) from the map counters at 19 moments (E018-r0013): 19/27/32/26 at 00:30, 19/37/28/19 at 05:30, 41/42/6/24 at 10:30, 47/46/0/12 at 12:30, 80/37/0/14 at 15:30 and 83/30/0/14 at 18:10;
  the human's country count over the same moments was 9, 11, 17, 22, 27 and 33; the largest stack reached 33 (human, 13:54) and the computers' largest was 20. The human's total rose by its pool each turn minus its losses (the pool was 16 to 26 from turn 27), and the
  computers' totals fell as their territory fell. One game; a total is a lower bound by one country whose colour could not be read in some frames.
- **Cited by:** E018-r0013.

### Q-BON-01 / Q-BON-02 (C-BON-01, C-BON-02) - island bonuses

- **Status:** narrowed
- **This sitting:** with the pool messages "N islands, place M armies" the human's island amounts (the pool minus the country part) were 5 (1 island named, turn 27), 7, 12, 14 (4 islands named at turn 41), 14, 14 and 17 (turn 47); partial control was not isolated and the nine single-island values are not separated here.
- **Cited by:** E018-r0011.

## Setup, turns, events, ending

### Q-SET-04 (C-SET-01) - the options screen

- **Status:** corroborated (a third visit; the first target was one)
- **This sitting:** the options screen at 00:03.0 to 00:09.5 shows the same groups and defaults as IP1 026 and IP1 027.
- **Cited by:** E018-r0012.

### Q-STA-01 / Q-STA-03 (C-STA-03, C-STA-05) - the deal

- **Status:** narrowed
- **This sitting:** a third deal: counts blue 9, yellow 14, red 11, green 12 (sum 46), the human at 9 with the middle strength (level 2, claim: 9); the first seat to play was red, after a draw animation of 14 marker moves in 1.5 s. Three deals of the target 10 (first seats yellow, blue, red).
- **Cited by:** E018-r0011, E018-r0012.

### Q-TRN-02 (C-TRN-02) - seat order

- **Status:** narrowed
- **This sitting:** the playing seat followed red, green, blue, yellow without a break for 36 turns, then (red eliminated at 11:55) green, blue, yellow without the red seat for 11 turns: the skip of an eliminated seat is seen at 4 changes (yellow to green).
- **Cited by:** E018-r0011, E018-r0013.

### Q-TRN-05 - game length

- **Status:** narrowed
- **This sitting:** 47 player-turns to the offer at 18:10.75 (18:15 to the winner dialog), at the owner's own pace: three games in three sittings (55, 46 and 47 turns; 17:10, 10:49 and 18:15 of recording to the end); three games are not a distribution.
- **Cited by:** E018-r0011, E018-r0013.

### Q-HAZ-01 / Q-HAZ-02 / C-VIC-04 - event messages

- **Status:** narrowed
- **This sitting:** two event messages in 47 turns, both between turns and both of one kind (production centres moved to new locations, a kind not seen in the earlier two sittings): 03:46.75 to 03:54.50 (turns 17 and 18) and 07:41.25 to 07:49.00 (turns 27 and 28); none before turn 17; 2 of the 42 turn changes from turn 5 on, about 5 per cent
  (the setting was the middle one). Across the three sittings 7 of 131 turn changes (about 5 per cent; the claim's range is 1 in 8 to 1 in 21 by setting). No seat held 39 or more countries before the end.
- **Cited by:** E018-r0013.

### Q-VIC-01 / Q-SUR-05 (C-VIC-01, the elimination prompt) - the end

- **Status:** unestablished (the human was not eliminated; no conquest of 46)
- **This sitting:** the game ended by the concession, see C-SUR-01; no elimination prompt for the human.

### Q-SUR-01 / Q-SUR-04 (C-SUR-01, C-SUR-02) - the concession offer

- **Status:** narrowed
- **Static claim:** the computers concede collectively to the only human seat when it holds 33 or more of 46 countries, checked once per turn transition by country count; accepting ends the game at once as a scored win.
- **This sitting:** the human seat held 33 countries from 17:52.07; the owner finished that turn (action bar at 18:07.0, the capture card screen at 18:08.5 to 18:10.0); at 18:10.75 the offer came, two buttons (accept the win, keep playing) and a dialog saying the other forces concede to the blue army; the owner pressed accept (18:14.5) and the game ended at once with a winner dialog (18:15.27), a scoreboard
  screen (18:19.03) and the title screen (18:21.03). The offer came at the turn transition, not at the 33rd capture, and with the human holding 33 (the previous transitions had it at 27 or fewer: no test of the boundary 32 against 33); the refuse path was not taken. **One observation that the claim does not explain:** the scoreboard screen read normal 0 won, 3 lost, 0 per cent after the win was accepted (the three losses fit the owner's three earlier lost games, IP1 025 to 027), so no win was shown on the screen
  for a win the game had just called a win, while the claim says a result is written when the counters sum to 50 or fewer (they sum to 3); the screen may be drawn before the write. One case.
- **Cited by:** E018-r0013.

### Q-SUR-03 (C-SUR-03) - what an eliminated seat's cards do

- **Status:** narrowed
- **This sitting:** the red seat was eliminated by attack 57 (yellow); at 11:55.1 red's cards went from 4 to 0 and yellow's stayed 1 (yellow then drew one capture card, 1 to 2 at 11:58.0): an eliminated seat's cards vanish and are not inherited, consistent with F012. (Elimination of the human seat was seen in IP1 026 and IP1 027, where the capturer's hand did not grow either.)
- **Cited by:** E018-r0011.

## Computer opponent

### C-AI-03 / C-AI-04 (Q-AI-01, Q-AI-04) - attacks and turns with none

- **Status:** narrowed
- **This sitting:** 44 computer attacks in 34 computer turns recorded with counts before and after (table above); the gates of Q-CMB-01 and Q-CMB-03 hold in all 44. Seven computer turns had no attack at all (turns 1, 10, 26, 33, 40, 42, 46: red 11 countries, green 11, green 11, red 3, green 8, yellow 13, green 8), 7 of 34 (21 per cent); the static reading gives about 1 in 22 for a seat with 18 or fewer countries; the green seat's empty turns 40 and 46 came with 5 cards in hand. The cause (the skip draw or no qualifying pair) is not visible. Under the 1-in-22 skip alone 7 or more in 34 turns has a probability of about 0.0007 (12 or more in the three sittings' 110 turns, about 0.004), so the skip draw does not explain them all; the other route in the claim, no pair that qualifies, is plausible for the 8-country green seat, whose stacks were small. The target is 20 games.
- **Cited by:** E018-r0010, E018-r0011.

### Q-AI-05 / Q-AI-02 / C-AI-06 - placement and cards

- **Status:** unestablished for placement (the computer places with no screen); the computer's trade-in priority is only partly visible (two trade-ins: +8 and bomb match).

### Q-AI-07 - strength against scripted opponents

- **Status:** narrowed (one game that the human won, by stacking on single countries and taking neighbours one at a time; a win rate needs many games and a scripted opponent)

### C-AI-05 (Q-AI-04's move half) - the computer's end-of-turn move

- **Status:** narrowed
- **This sitting:** 5 moves; every source off the 23-country list (the claim excludes key sources), four of five destinations on it (the first, country 17, is not); each moved all but one army and the destination was a neighbour. Whether the source was the seat's largest eligible country was not checked.
- **Cited by:** E018-r0014.

## What only a human sitting shows (constraint E)

These rest on the owner's videos, and on this one for the sitting's own readings; none is a rule claim.

- The owner won by taking 33 countries and accepting the concession, not by finishing the conquest; the owner kept attacking after reaching 33 (the last turn had 6 attacks) until the end of that turn.
- Stacking: from turn 27 on the owner placed the whole pool on one or two countries and attacked from them (stacks of 14, 16, 22, 25, 33), each time against a defender of 1 to 4, with all-but-one moved in about as often as 1 (11 against 13 of 28).
- The owner quit four battles at 2 or 3 armies against 1 or 2 (attacks 7, 13, 21, 25), all in the first 4:20 of the game; none after.
- The owner waited 22 s with the trade-in offer open at turn 41 before choosing the bomb and two wildcards, leaving the doubling card out; the owner bombed a stack of 9, the largest yellow country in reach.
- The owner moved at the end of 6 of 13 turns, always all but one except twice from stacks of 2, and never moved a stack of 5 or 10.
- The computer's answer to the owner's play is not separable from its own policy here; the data above is the computer's play, with no model-driven sitting to compare.

## Re-reads (rule 20)

A re-read of `IP1 028.mp4` writes new files beside r0010..r0014 (the next free record numbers) with their own frame hashes, and says which record it cross-references; these records stay as written.

**Correction notes (Luna's review of PR #187; the records stay as written):**
- **R1, readings inside observations** (round 1 of Luna's review; completed after its re-review, from a full read of every observation value in r0010–r0014). Read the clauses below as interpretation, not observation. The per-question entries above are where they are weighed.
  - *Finding, question or static-list references* (a lookup, not something the screen showed):
    - r0011 obs[86]: "not inherited (F012, Q-SUR-03)";
    - r0013 obs[24]: "as F012 reads (Q-SUR-01…)";
    - r0013 obs[25]: the F012 clause and the reading of "0 won" (IP1 029's note shows the result is added about 2.2 to 2.4 s after the screen appears);
    - r0012 obs[18]–[23] and r0014 obs[1]–[5]: "neighbours (F017 border tables)";
    - r0014 obs[1]–[6]: on or off "the fixed 23-country list".
  - *Formulas and rule readings fitted to the counts:*
    - r0011 obs[88]: the pool as the count divided by 3, rounded down, raised to 2, and the island amounts as sums of the static bonus values;
    - r0011 obs[83] and obs[85]: the bombed country's new count read as "within 1 to half", "a replacement by a draw, not a fixed loss", "floored at 1";
    - r0011 obs[82]: the pool of 16 read as 8 plus 8 extra armies;
    - r0014 obs[7]: "above the usual minimum".
  - *Comparisons with other sittings or other sources:*
    - r0011 obs[1]: the order "continues cyclically" from the earlier sittings, and the first seats across three games;
    - r0012 obs[0]: same screen and defaults as IP1 026 and 027;
    - r0012 obs[2]: the deals across the sittings;
    - r0012 obs[17]: the stacks set against E021's defender sizes;
    - r0012 obs[26]: the mapping said to reproduce coordinates.md's attack (337, 531) and pass rows and E021's click points (attack's centre is 305, per Luna's review of this PR);
    - r0013 obs[0]: the event rate set against the middle setting and the earlier sittings.
  - *Derivations and method notes:*
    - r0010 obs[1]: the last exchange of a capture is inferred;
    - r0010 obs[2]: the computer's start is taken from the counters;
    - r0012 obs[23]: the destination is read from the total;
    - r0013 obs[21]: totals are lower bounds;
    - r0013 obs[22]: the seat order is inferred from the turn sequence.
- **R3, a count corrected before review.** Commit 3cbbaa0, labelled a wording fix, also changed r0012's placement count from "one country in 9 turns, two or more in 4" to "10 and 3". The new numbers are the consistent ones: the value lists exactly three turns with two or more countries (27, 44 and 47), and 10 + 3 = 13 placements. The change was a correction of the first write, made before any review, and is recorded here because its commit message did not say so.

---

# IP1 029 sitting

The fifth owner sitting (2026-10-11, owner-driven Bandicam capture, 15:10, video sha256
`d19ad65dc161a1d3c4138fec478fd6e660300c05227979ec4e91a26feeea1d95`, Bandicam 8.3.0.2533 per the file's encoder
tag; frame timestamps are irregular, 17099 frames in 910.37 s, so offsets are container timestamps, not frame
numbers). One game from the title screen to the title screen after the game: the options screen at 00:03, the deal
at 00:36 to 00:47, the first seat (the human) drawn at 00:48.2, 29 player-turns (8 human, 21 computer), 54 attacks
(31 human, 23 computer), 4 human moves (and 2 cancelled), 2 human trade-in offers (one declined, one accepted) and 1 event
message. **The owner won**, on the **easy level at slow speed** (the first sitting off the middle level): the human seat took
the red seat's last country at 13:50.07 and the yellow seat's at 14:48.8, held 41 of 46 countries, and at the
turn transition (about 14:55.0) the computers' concession offer came; the owner pressed accept at about 15:01.2, the winner dialog
came at 15:01.47, the scoreboard screen at 15:03.77 and the title screen at 15:06.13. As in IP1 028 the game ended by the concession,
this time with 41 countries held (green kept 5).

Records, all immutable, `runtime.platform` `windows-native-bandicam` (built on PR #187's records, numbered from E018-r0015):

- `E018-r0015`: the 54 attacks (start counters, strip states, endings, capture splits, the human move-in counters), five frames.
- `E018-r0016`: the 29 turn starts (counts, pools, cards), the card draws, the two human trade-in offers, the elimination of the red
  seat; six frames.
- `E018-r0017`: the options screen with the easy level, the deal, the 8 human placements, the 4 human moves and 2 cancelled ones, the move
  controls checked against IP1 028; eleven frames.
- `E018-r0018`: the event message, army totals at 14 moments, the seat eliminations, the concession offer, the scoreboard before and after
  its update; seven frames.

Frames are in the bundle store by hash (`IP1-029`), listed in `evidence/E018/E018-r0015..18.manifest.json`; the video and the frames are never
committed (rule 18). Everything was read by pixels (glyph-shape matching of the strip, the scoreboard and the map digits, colour regions;
no OCR); the readers are those of IP1 027 and IP1 028 with a few digit templates added after listing every unmatched glyph. Four checks backed
the readings: every one of the 151 strip steps is a single loss on one side (none was (1,1) or larger); for all 39 captures (29 human, 10 computer)
the two country counters after the capture add up to the attacker's armies at the capture, **so the extra army seen once in IP1 028 (attack 41)
does not recur**, including in five captures made from exactly 3 armies; the first and last strip states of six human attacks (1, 9, 40, 42, 53, 54)
were re-read by eye on crops of the frames and matched; and every attack's two countries are neighbours in the F017 border tables (54 of 54).

**Notes that correct earlier readings, written here and not in the records (rule 20).**

- E018-r0013 (IP1 028), the scoreboard: it records that no win was shown at the end of IP1 028. Here the scoreboard screen first shows the counts from before the
  game and, about 2.2 to 2.4 s after it appears, adds the result (screen at 15:03.77; easy 0/0 became 1/0 at the scene change of 15:06.13, first seen in the frame at 15:06.0, E018-r0018; "about 1.7 s" and "15:05.2 to 15:05.6", first written here, do not follow from the record: Luna's review of PR #188, R4); the normal row at the start of this video already reads 1 won 3 lost,
  so IP1 028's win was recorded. IP1 028's screen was up for 2.0 s without an update in its last frame, so the win was recorded but not yet shown. The concession win counts
  on the scoreboard (C-SUR-02's "scored win"); E018-r0013's wording stands as written and this note is the correction.
- E018-r0018 (this sitting), the last observation's turn durations are wrong: human turns lasted 34 s to 198 s (median 68 s; turn 21, with a trade-in offer open for about 90 s and a
  cancelled move, is the longest) and computer turns 4.9 s to 18.2 s (median 7.6 s), not 33 to 110 s and 3 to 10 s as the record says. The same record's "easy level at slow speed" and the rest stand.

## What the owner played, and what the video shows

The owner meant to play moves and trade-ins and to win a full game. All three are in the video. **Moves:** 4 completed (turns 5, 13, 21, 25) and 2 started and cancelled; every move leaves exactly 1 in the source, and
the largest, from a stack of 26, moved 25. **Trade-ins:** two offers to the human, one declined (turn 17, hand +5, wildcard, bomb, bomb) and one accepted (turn 21, +5 from two +5 cards and a wildcard, pool 18 to 23); no computer
traded and no bomb was played. **The win:** by concession at 41 countries. The owner built exact stacks: 8 (turn 5, country 42), 12 (turn 9, country 43), 13, 17, 27 and 41, and attacked from 8, 12 and more, **but every human
defender held only 1 to 4 armies**, so none of E021's open size cells is met (even 4 against 6, 8 against 7, 9, 10, 12 against 11 to 14; underdog 12 and 20). E021's progress counter counts only E021 records and stays at 30 of 40.

Every human attack, with its start and the cell it fits (E021's cells, for the main session; nothing here is counted in E021):

| # | offset | from>to | start | strip states | ending | Session A cell it fits |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 01:11.700 | 39>40 | 7 v 1 | 7/1 6/1 5/1 4/1 3/1 | capture at 3; moved in 2, kept 1 | none |
| 4 | 02:01.933 | 42>41 | 8 v 1 | 8/1 | capture at 8; moved in 1, kept 7 | none |
| 7 | 02:59.700 | 43>8 | 12 v 2 | 12/2 12/1 11/1 | capture at 11; moved in 7, kept 4 | none |
| 8 | 03:11.133 | 8>6 | 7 v 1 | 7/1 6/1 | capture at 6; moved in 1, kept 5 | none |
| 9 | 03:22.967 | 5>7 | 3 v 2 | 3/2 3/1 2/1 | quit at 2/1 | quit cell |
| 10 | 03:32.433 | 8>7 | 5 v 1 | 5/1 4/1 | capture at 4; moved in 3, kept 1 | none |
| 15 | 04:39.367 | 7>9 | 13 v 1 | 13/1 12/1 11/1 10/1 9/1 | capture at 9; moved in 8, kept 1 | none |
| 16 | 04:49.933 | 9>14 | 8 v 2 | 8/2 7/2 7/1 | capture at 7; moved in 1, kept 6 | none |
| 23 | 06:08.700 | 11>13 | 17 v 2 | 17/2 17/1 | capture at 17; moved in 16, kept 1 | none |
| 24 | 06:23.300 | 13>12 | 16 v 2 | 16/2 15/2 15/1 14/1 13/1 | capture at 13; moved in 1, kept 12 | none |
| 25 | 06:33.467 | 13>1 | 12 v 3 | 12/3 11/3 11/2 11/1 | capture at 11; moved in 7, kept 4 | none |
| 26 | 06:47.533 | 1>2 | 7 v 2 | 7/2 6/2 5/2 4/2 3/2 3/1 | capture at 3; moved in 1, kept 2 | none |
| 32 | 09:40.600 | 13>15 | 27 v 2 | 27/2 27/1 | capture at 27; moved in 26, kept 1 | none |
| 33 | 09:50.667 | 15>16 | 26 v 2 | 26/2 25/2 24/2 23/2 23/1 22/1 | capture at 22; moved in 21, kept 1 | none |
| 34 | 10:10.633 | 16>17 | 21 v 2 | 21/2 21/1 | capture at 21; moved in 20, kept 1 | none |
| 35 | 10:21.467 | 17>19 | 20 v 2 | 20/2 19/2 18/2 18/1 17/1 16/1 | capture at 16; moved in 15, kept 1 | none |
| 36 | 10:31.567 | 19>22 | 15 v 2 | 15/2 14/2 13/2 13/1 | capture at 13; moved in 12, kept 1 | none |
| 40 | 11:51.100 | 23>38 | 41 v 2 | 41/2 41/1 40/1 | capture at 40; moved in 39, kept 1 | none |
| 41 | 12:06.700 | 38>37 | 39 v 3 | 39/3 39/2 38/2 37/2 36/2 35/2 35/1 | capture at 35; moved in 34, kept 1 | none |
| 42 | 12:17.067 | 37>36 | 34 v 4 | 34/4 34/3 33/3 32/3 31/3 30/3 29/3 29/2 29/1 28/1 27/1 | capture at 27; moved in 26, kept 1 | none |
| 44 | 13:21.233 | 38>23 | 26 v 4 | 26/4 26/3 25/3 25/2 24/2 24/1 23/1 22/1 | capture at 22; moved in 21, kept 1 | none |
| 45 | 13:32.333 | 23>45 | 21 v 3 | 21/3 21/2 20/2 19/2 19/1 | capture at 19; moved in 18, kept 1 | none |
| 46 | 13:39.567 | 45>46 | 18 v 2 | 18/2 17/2 16/2 15/2 15/1 14/1 | capture at 14; moved in 13, kept 1 | none |
| 47 | 13:48.267 | 46>44 | 13 v 3 | 13/3 13/2 12/2 11/2 10/2 10/1 9/1 | capture at 9; moved in 8, kept 1 | none |
| 48 | 13:55.500 | 35>34 | 28 v 3 | 28/3 28/2 28/1 27/1 26/1 25/1 | capture at 25; moved in 24, kept 1 | none |
| 49 | 14:02.600 | 34>32 | 24 v 3 | 24/3 24/2 24/1 23/1 | capture at 23; moved in 22, kept 1 | none |
| 50 | 14:12.100 | 32>31 | 22 v 1 | 22/1 21/1 | capture at 21; moved in 20, kept 1 | none |
| 51 | 14:20.367 | 31>29 | 20 v 2 | 20/2 20/1 | capture at 20; moved in 19, kept 1 | none |
| 52 | 14:26.933 | 29>30 | 19 v 1 | 19/1 18/1 17/1 | capture at 17; moved in 8, kept 9 | none |
| 53 | 14:38.033 | 29>27 | 9 v 2 | 9/2 8/2 7/2 6/2 5/2 4/2 3/2 3/1 2/1 | quit at 2/1 | quit cell |
| 54 | 14:46.733 | 30>28 | 8 v 2 | 8/2 7/2 6/2 6/1 5/1 4/1 | capture at 4; moved in 3, kept 1 | none |

Reading the table: 29 captures and 2 stops by the owner (attacks 9 and 53, both at 2 against 1, the quit button), no failed attack: **the human was never reduced to 1 army**, so the forfeit case of Q-BON-05 and Q-CMB-09 is not seen
in this sitting either. No human attack started below 3 armies, none at equal strength, none against a stronger defender. Cells fitted: **quit**, two attacks (9, 53), each after two exchanges the strip showed; **busy**, five human turns with 3 or more
fights (turn 9: 4 fights, ended by the card screen with no move; turn 17: 4, no move; turn 21: 5, ended by a move; turn 25: 3, ended by a move; turn 29: 11, ended by the concession offer); E021's busy row was already full. No tiny cell (no 3 against 1), no even or underdog cell, no lost cell.

## The attacks: every one, before and after

`#` is the order in the video (`r0015`, step = `#`). `offset` is the first strip frame. `seat` is the attacking seat, `C` computer, `H` human. `before` is attacker/defender armies as the country counters show them just before the strip
appeared (for the computer the strip starts one exchange in, so this differs from the strip's first state in 20 of 23 attacks; for the human they agree in 31 of 31); `after` is the last state, or, for a capture, the attacker's armies at the capture with the
defender at 0, then the split (computer: armies kept in the attacker's country and armies placed in the captured country; human: the move-in the owner chose and what the attacker keeps). A stop or quit leaves both countries with their owners.

| # | offset | seat | from>to | before | after | ending |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 01:11.700 | Blue H | 39>40 | 7/1 | 3/0, then in 2 keeps 1 | capture |
| 2 | 01:33.633 | Red C | 46>45 | 6/1 | 3/0, then keeps 1 gets 2 | capture |
| 3 | 01:42.500 | Green C | 2>3 | 6/2 | 2/1 | stop |
| 4 | 02:01.933 | Blue H | 42>41 | 8/1 | 8/0, then in 1 keeps 7 | capture |
| 5 | 02:28.633 | Yellow C | 31>30 | 4/2 | 4/0, then keeps 1 gets 3 | capture |
| 6 | 02:38.400 | Red C | 8>6 | 5/2 | 3/0, then keeps 2 gets 1 | capture |
| 7 | 02:59.700 | Blue H | 43>8 | 12/2 | 11/0, then in 7 keeps 4 | capture |
| 8 | 03:11.133 | Blue H | 8>6 | 7/1 | 6/0, then in 1 keeps 5 | capture |
| 9 | 03:22.967 | Blue H | 5>7 | 3/2 | 2/1 | quit |
| 10 | 03:32.433 | Blue H | 8>7 | 5/1 | 4/0, then in 3 keeps 1 | capture |
| 11 | 03:51.900 | Yellow C | 19>22 | 3/1 | 3/0, then keeps 2 gets 1 | capture |
| 12 | 03:54.267 | Yellow C | 30>29 | 5/1 | 4/0, then keeps 2 gets 2 | capture |
| 13 | 04:03.667 | Red C | 14>9 | 5/3 | 2/1 | stop |
| 14 | 04:11.133 | Green C | 26>25 | 5/3 | 4/0, then keeps 3 gets 1 | capture |
| 15 | 04:39.367 | Blue H | 7>9 | 13/1 | 9/0, then in 8 keeps 1 | capture |
| 16 | 04:49.933 | Blue H | 9>14 | 8/2 | 7/0, then in 1 keeps 6 | capture |
| 17 | 05:21.367 | Yellow C | 29>28 | 5/2 | 3/2 | stop |
| 18 | 05:22.500 | Yellow C | 30>28 | 4/2 | 3/2 | stop |
| 19 | 05:28.200 | Red C | 15>13 | 8/3 | 5/0, then keeps 3 gets 2 | capture |
| 20 | 05:38.433 | Green C | 24>23 | 5/3 | 2/3 | stop |
| 21 | 05:39.900 | Green C | 2>3 | 4/1 | 2/1 | stop |
| 22 | 05:40.933 | Green C | 12>13 | 3/2 | 2/2 | stop |
| 23 | 06:08.700 | Blue H | 11>13 | 17/2 | 17/0, then in 16 keeps 1 | capture |
| 24 | 06:23.300 | Blue H | 13>12 | 16/2 | 13/0, then in 1 keeps 12 | capture |
| 25 | 06:33.467 | Blue H | 13>1 | 12/3 | 11/0, then in 7 keeps 4 | capture |
| 26 | 06:47.533 | Blue H | 1>2 | 7/2 | 3/0, then in 1 keeps 2 | capture |
| 27 | 07:32.033 | Yellow C | 29>28 | 6/2 | 2/1 | stop |
| 28 | 07:33.967 | Yellow C | 30>28 | 3/1 | 3/0, then keeps 1 gets 2 | capture |
| 29 | 07:41.700 | Red C | 15>16 | 6/2 | 2/2 | stop |
| 30 | 07:49.067 | Green C | 36>35 | 5/3 | 2/3 | stop |
| 31 | 07:50.467 | Green C | 24>33 | 4/2 | 2/2 | stop |
| 32 | 09:40.600 | Blue H | 13>15 | 27/2 | 27/0, then in 26 keeps 1 | capture |
| 33 | 09:50.667 | Blue H | 15>16 | 26/2 | 22/0, then in 21 keeps 1 | capture |
| 34 | 10:10.633 | Blue H | 16>17 | 21/2 | 21/0, then in 20 keeps 1 | capture |
| 35 | 10:21.467 | Blue H | 17>19 | 20/2 | 16/0, then in 15 keeps 1 | capture |
| 36 | 10:31.567 | Blue H | 19>22 | 15/2 | 13/0, then in 12 keeps 1 | capture |
| 37 | 11:15.300 | Yellow C | 29>27 | 4/2 | 2/2 | stop |
| 38 | 11:21.433 | Red C | 44>43 | 8/4 | 3/3 | stop |
| 39 | 11:29.133 | Green C | 24>33 | 4/2 | 4/0, then keeps 3 gets 1 | capture |
| 40 | 11:51.100 | Blue H | 23>38 | 41/2 | 40/0, then in 39 keeps 1 | capture |
| 41 | 12:06.700 | Blue H | 38>37 | 39/3 | 35/0, then in 34 keeps 1 | capture |
| 42 | 12:17.067 | Blue H | 37>36 | 34/4 | 27/0, then in 26 keeps 1 | capture |
| 43 | 12:48.600 | Red C | 45>23 | 11/1 | 7/0, then keeps 3 gets 4 | capture |
| 44 | 13:21.233 | Blue H | 38>23 | 26/4 | 22/0, then in 21 keeps 1 | capture |
| 45 | 13:32.333 | Blue H | 23>45 | 21/3 | 19/0, then in 18 keeps 1 | capture |
| 46 | 13:39.567 | Blue H | 45>46 | 18/2 | 14/0, then in 13 keeps 1 | capture |
| 47 | 13:48.267 | Blue H | 46>44 | 13/3 | 9/0, then in 8 keeps 1 | capture |
| 48 | 13:55.500 | Blue H | 35>34 | 28/3 | 25/0, then in 24 keeps 1 | capture |
| 49 | 14:02.600 | Blue H | 34>32 | 24/3 | 23/0, then in 22 keeps 1 | capture |
| 50 | 14:12.100 | Blue H | 32>31 | 22/1 | 21/0, then in 20 keeps 1 | capture |
| 51 | 14:20.367 | Blue H | 31>29 | 20/2 | 20/0, then in 19 keeps 1 | capture |
| 52 | 14:26.933 | Blue H | 29>30 | 19/1 | 17/0, then in 8 keeps 9 | capture |
| 53 | 14:38.033 | Blue H | 29>27 | 9/2 | 2/1 | quit |
| 54 | 14:46.733 | Blue H | 30>28 | 8/2 | 4/0, then in 3 keeps 1 | capture |

Counts this sitting adds to the per-claim totals (constraint E): 210 exchanges (151 strip steps, 39 capture exchanges inferred from the defender's last army, 20 first exchanges of computer attacks read from the before-counters), 54 attacks (31 human,
23 computer), 29 turn starts with the army pool, 8 human placements, 4 human moves (2 more cancelled), 29 human move-ins, 1 accepted trade-in and 1 declined offer, 1 event message, 1 concession.

Outcome words follow `walkthroughs/f011-questions.md`: `corroborated` when the count target is met and play matches the static claim, `narrowed` when it matches in the part played, `unestablished` when nothing in the video bears on it.

## Combat

### Q-CMB-01 (C-CMB-01) - who may attack, human and computer

- **Status:** narrowed
- **Static claim:** a human needs at least 2 armies and at least as many as the target; the computer needs more than the target by a drawn margin of 0 or 1, so never at equal strength.
- **This sitting:** computer, 23 starts: none at equal or lower strength; margin 1 once (attack 22, 3 against 2), 2 in 11, 3 in 3, 4 in 5, 5 in 2 and one of 10 (attack 43, 11 against 1). Over the four sittings (94, 73, 44 and 23 starts): 234 computer starts, none at equal strength
  (the computer arm is met against a target of 100 or more). Human, 31 starts: all had at least 3 armies and more than the target; no equal-strength start and no refused order was shown; the 16-case grid was not played (no cell reached, see above).
- **Why narrowed:** the human boundary and the refusal are untested.
- **Cited by:** E018-r0015.

### Q-CMB-02 (C-CMB-02) - equality, not a ratio

- **Status:** narrowed
- **This sitting:** the one computer start with 10 or more armies was 11 against 1 (margin 10). The human attacked from 12 (12 against 2, attack 7; 12 against 3, attack 25), 13, 17 and up to 41 armies, against defenders of 1 to 4, and none was refused; the human boundary at N in 4, 8, 12, 20 was not
  played with a defender near N.
- **Cited by:** E018-r0015.

### Q-CMB-03 (C-CMB-03) - minimum attacking stack

- **Status:** narrowed (computer arm met over the sittings; the human arm unestablished)
- **Static claim:** human minimum 2; computer minimum 3 or 4 before a capture this turn (4 or 5 for a country on the fixed 23-country list) and 4 after one (5 on the list).
- **This sitting:** the computer's smallest start by class: ordinary country before a capture 3 (10 starts), list country before a capture 4 (12), ordinary country after a capture 5 (1; attack 12); no list-country start after a capture; no start below its class minimum in 23. The human's smallest start was 3 (attack 9, 3 against 2).
- **Cited by:** E018-r0015 (list membership from `experiments/E015-pro-board-reading/measurements/board-tabulation-r1e.json`).

### Q-CMB-04 (C-CMB-04) - one die each, one army per exchange, five-at-once batching

- **Status:** narrowed
- **This sitting:** 210 exchanges; every strip step changed exactly one counter by one (151 steps, none of (-1,-1) or larger). Exchanges against a one-army defender by attacker size: 3: 12, 4: 12, 5: 7, 10: 3 (size 2: none); 6 to 9: 15, 11 and over: 43 (up to 41). Over the four sittings
  the sizes 2, 3, 4, 5, 10 stand at 1, 58, 91, 71, 21 (target 100 or more each). The five-exchange pass needs more than 40 against more than 15 (computer) or more than 35 against more than 15 (human): the largest pair was 41 against 2 (human), the defenders far below 15, so batching was not exercised.
- **Cited by:** E018-r0015.

### Q-CMB-05 (C-CMB-04, defender-size half) - defender size

- **Status:** narrowed
- **This sitting:** attacker-loss share by defender size at the exchange: 1 army 53/92 (57.6%), 2 armies 53/85 (62.4%), 3 armies 17/28 (60.7%), 4 armies 2/5; a chi-square test across the four groups gives p = 0.75, so no dependence on the defender's size is detected. Defender sizes above 4 were not seen.
- **Cited by:** E018-r0015.

### Q-CMB-06 (C-CMB-05) - ties go to the defender

- **Status:** narrowed
- **Static claim:** ties go to the defender, so the attacker loses an exchange 21 times in 36 (7/12, 58.3%).
- **This sitting:** attacker lost 125 of 210 exchanges (59.5%), 95% interval 52.9% to 66.2%; 7/12 is inside the interval (z = +0.35); an even 50% is not (z = +2.76). Over the four sittings: 680 of 1208 (56.3%), interval 53.5% to 59.1%; 7/12 is inside (z = -1.44), an even 50% is not (z = +4.37).
  Human 75 of 138 (54.3%), computer 50 of 72 (69.4%); in this sitting the two shares differ (Pearson chi-square p = 0.034, no continuity correction, the convention of these sections; Fisher's exact p = 0.04 agrees; Luna's review of PR #188, R3), the first time in the four sittings (earlier p: 0.39, 0.16, 0.14), with four comparisons made and no correction; the computer's loss share of 69% over 72 exchanges is above 7/12 (z = +1.9) and
  the sitting is one game, so this is a thing to watch, not a claim. Dice are not visible, so only the outcome share is tested.
- **Why narrowed:** 1208 of the 500 target over the four sittings, but the share is consistent with the claim, not a proof.
- **Other explanations (Luna's review of PR #188, R5):**
  - *The 59.5%, and the computer's 69.4%: missed exchanges.* Mostly excluded. The 151 strip steps are all single losses and reconcile with the counters, so a missed step would show as a two-army jump. The inferred capture exchanges are attacker wins, so they pull the loss share down.
  - *Selection.* At the easy level the computer attacks with its own gates and stops (C-CMB-01, C-CMB-08). A per-exchange share can move only if exchanges depended on stack sizes, and no defender-size effect is detected (p = 0.75). The human/computer gap could still come from which stacks each side chose: not excluded.
  - *Chance across several comparisons.* Four sittings, four comparisons, no correction. A Bonferroni threshold of 0.0125 is not met by p = 0.034, so chance is not excluded.
  - *Dice that depend on the level or the seat.* Not excluded: the dice are never shown, and C-CMB-07 reads only the counts and dice into an exchange. This one game at the easy level is the only sitting where the shares differ.
- **Cited by:** E018-r0015.

### Q-CMB-07 (C-CMB-06) - exactly one army lost per exchange

- **Status:** corroborated
- **This sitting:** 151 strip steps, every one a loss of one army on exactly one side; none lost two or lost one on each side; a 5-army run could not occur (see Q-CMB-04). 39 capture exchanges end with the defender's last army gone. Over the four sittings the strip steps stand at 360, 139, 233 and 151 against the target of 200.
- **Cited by:** E018-r0015.

### Q-CMB-08 (C-CMB-08) - a battle's end, quit, automatic loop

- **Status:** narrowed
- **This sitting:** human, 31 attacks: 29 ended in a capture, 2 were quit by the owner with armies as they stood (attacks 9 and 53, both at 2 against 1), ownership unchanged and no cost seen. Whether one click is one exchange is not established (clicks are not visible); consecutive human strip steps are 0.10 to 1.37 s apart (median 0.23 s over 109 intervals), computer steps 0.03 to 0.30 s
  (median 0.27 s over 42). Targets met on count (human 10 attacks, computer 30 battles over the sittings). Computer, 23 battles: 10 captures, 13 stops without a capture; the attacker's armies at those stops were 2 (ten times) and 3 (three), never below 2, as the static claim says.
- **Cited by:** E018-r0015.

### Q-CMB-09 (C-CMB-09) - a failed attack

- **Status:** narrowed (the computer arm met its count over the sittings; the human arm, 5 failed attacks wanted, saw none in four sittings)
- **This sitting:** computer, 13 stops without a capture: both countries keep their owners and the counters equal the last strip state in 13 of 13 (attack 27 is followed within 0.4 s by the next attack, which took the same country; its stop state is the last strip state); the attacker's country keeps at least 2.
  Human: no attack was lost down to 1 army (two quits at 2 against 1), so the forfeit rule, the card cancellation and the turn change are not exercised, again.
- **Cited by:** E018-r0015.

### Q-CMB-10 (C-CMB-10) - attacks per turn

- **Status:** narrowed
- **This sitting:** computer attacks per turn over 21 turns: 0 in 4 (turns 2, 8, 26, 28: yellow 7 countries, green 10, yellow 6, green 5), 1 in 12, 2 in 4, 3 in 1; none of the 21 turns had more than 3 attacks. Over the four sittings 16 of 131 computer turns made no attack (12%; under the static 1 in 22 skip alone that many has a probability of about 0.001, so the skip draw does not explain them all). Rounds are not visible. Human, 8 turns: 1 attack in 2, 2 in 1, 3 in 1, 4 in 2, 5 in 1 and 11 in 1 (turn 29, 12:56.7 to 14:48.8, with 10 captures):
  eleven attacks in one turn with nothing stopping them, so "no limit" is shown to 11. The turns with 3 or more fights were 5 (turns 9, 17, 21, 25, 29); with IP1 028's 5 that is 10 turns with 3 or more fights in the two sittings.
- **Cited by:** E018-r0015, E018-r0016 (turn assignment from the scoreboard marker).

### Q-CMB-11 (C-CMB-07) - nothing but counts and dice enters an exchange

- **Status:** narrowed
- **This sitting:** computer attacker-loss share by whether the attacker's country is on the fixed 23-country list: list 33/48 (68.8%), not on the list 17/24 (70.8%), p = 1.0; no gross effect appears.
- **Cited by:** E018-r0015.

## Capture, moves, ownership

### Q-OWN-01 (C-OWN-01) - armies moved in on a capture

- **Status:** narrowed
- **This sitting:** human, 29 captures: the move-in counter started at 1 each time; it was taken to the attacker's armies minus 1 in one jump 21 times (attacks 1, 10, 15, 23, 32 to 36, 40 to 42, 44 to 51 and 54; the button is not visible), left at 1 in 5 (attacks 4, 8, 16, 24, 26), and set to other values in 3 (attack 7: 11 at the capture, jumped to 10 and
  reduced to 7; attack 25: 11 at the capture, raised to 7 one step at a time; attack 52: 17 at the capture, raised to 8 one step at a time); never more than the attacker's armies minus 1; the attacker always kept at least 1; the captured country received exactly the number chosen; the total was conserved in 29 of 29. Whether 0 can be chosen is not shown.
  Captures from stacks of 2, 3, 5 and 10 (the attacker's armies at the capture): 0, 2, 0, 0 here (target 3 each). Computer, 10 captures: the two counters add up to the attacker's armies in all 10, both at least 1; the attacker kept 1 in 3, 2 in 3, 3 in 4 (keeping 3: 4 of 10).
- **Cited by:** E018-r0015.

### Q-MOV-01 (C-MOV-01) - moves per turn

- **Status:** narrowed
- **This sitting:** human: 4 completed moves in 8 turns (5, 13, 21, 25), at most one per turn, each after the turn's last attack with no attack and no second move after it: the card screen of the turn came within 2 s and the turn passed (4 of 4, offsets in E018-r0017). Two moves were started and cancelled
  (turns 13 and 21), each by the cancel button of the destination prompt, and started again after (turn 13) or after a cancelled attack order (turn 21): a cancelled move does not use up the move. Computer: no move detected in 21 turns by the template that found 5 in IP1 028 (not checked by eye turn by turn).
  The target (10 human turns with a move) is 4 here and 11 over the owner's four sittings (1, 0, 6 and 4), not met per sitting.
- **Cited by:** E018-r0017.

### Q-MOV-02 (C-MOV-02) - all but one

- **Status:** narrowed
- **This sitting:** human, 4 of 4 moves left exactly 1 in the source: from stacks of 7, 6, 12 and 26, moving 6, 5, 11 and 25 (the all button was shown highlighted for moves 3 and 4, the plus button for move 2; move 1's button not isolated). Over the sittings, sources of 2, 3, 6, 7, 8, 12 and 26 armies are covered; 5 and 10 not; all-but-two and a counter of 0 were not tried.
- **Cited by:** E018-r0017.

### Q-MOV-03 (C-MOV-03) - adjacency, move then attack

- **Status:** narrowed
- **This sitting:** all 4 moves were between neighbouring countries. A country captured earlier in the same turn attacked in that turn 21 times (all human; no computer), so a just-captured country is not blocked. A second move in a turn was not offered (the turn ended after the move) and a destination two borders away was not tried (the destination was picked by clicking
  and was always a neighbour); an attack after a move was not possible (the turn ended).
- **Cited by:** E018-r0015, E018-r0017.

### Move controls seen, checked against IP1 028

Source: E018-r0017 (frames in its outputs). Same mapping as in the IP1 028 section: the picture is not black from x 125 to 1859 and y 85 to 1003 of the 1920x1080 frame in this video too, so `stage x = (frame x - 125) / 2.169` and `stage y = (frame y - 85) / 1.532`. **Every proposed row of the IP1 028 section is confirmed**
(frame centres within 2 pixels, stage centres within 1):

| Action | Stage x, y here | Frame offset here | Same as IP1 028? |
| --- | --- | --- | --- |
| ATTACK (action bar) | 305, 530 | 04:56.0 | yes |
| MOVE (action bar) | 369, 530 | 04:56.0 | yes |
| PASS (action bar) | 419, 530 | 04:56.0 | yes |
| CARD (action bar) | 468, 531 | 04:56.0 | yes (469, 531) |
| CANCEL (action bar and both move prompts) | 514, 528 | 04:56.0, 04:58.0, 05:00.0 | yes |
| Move counter: ALL | 309, 539 | 05:06.0 | yes |
| Move counter: PLUS | 373, 539 | 05:06.0 | yes |
| Move counter: MINUS | 420, 539 | 05:06.0 | yes |
| Move counter: DONE | 495, 539 | 05:06.0 | yes |

One addition: the CANCEL of the destination prompt, pressed after choosing a source, returns to the action bar with no counter panel (05:02.4, 10:52.4); the move can be started again at once. The source prompt's marker in the left panel alternates between a yellow arrow and a red bar every 1 to 2 s (05:04.0 against 05:06.0): it is a blinking marker, not a state.

## Cards and bonuses

### Q-BON-03 (C-CRD-01, C-CRD-02) - kinds seen

- **Status:** narrowed
- **This sitting:** five of the eight kinds in the human's hand: the +5 card (turns 1, 17, 25), the wildcard (turn 5), the bomb card (turns 9 and 13), the +15 card (turn 21) and the protection card (turn 29). Not seen here: +8, doubling, the empty-the-hand card. The +15 card is seen for the first time in the four sittings (not in 45 draws in IP1 026), so all eight kinds have now appeared across the four sittings.
- **Cited by:** E018-r0016.

### Q-BON-05 (C-CRD-03) - a card per capturing turn

- **Status:** narrowed
- **Why narrowed:** the forfeit case (a failed human attack after an earlier capture) is not seen in any of the four sittings (the human never lost an attack down to 1 army); the human arm is met on count (8 human turns here; 46 over the four sittings against the 20 wanted).
- **This sitting:** over the turns with a next turn start of the same seat: in the turns without a capture the seat's count did not change (10 computer turns: 2, 4, 8, 11, 14, 16, 19, 20, 22, 23; no human turn without a capture); in capturing turns with fewer than 5 cards and no trade-in the count rose by exactly 1 (6 human: turns 1, 5, 9, 13, 25 and 17 (4 to 5);
  8 computer: 3, 6, 7, 10, 12, 15, 18, 24); the one capturing turn with a trade-in (human turn 21) fell by 2 (3 out, 1 drawn). Human turn 29's draw (the protection card, 4 to 5) is on the card screen at 14:54.5 and not yet on the scoreboard. Every observation agrees with the claim.
- **Cited by:** E018-r0016.

### Q-BON-06 (C-CRD-04) - five cards, discard on a full hand

- **Status:** narrowed
- **This sitting:** no seat ever showed more than 5 cards. The human reached 5 at the end of turn 17 (4 to 5) and again at the end of turn 29; at turn 21 the hand of 5 was reduced by the trade-in before the draw; a draw into a full hand was therefore not made (no discard prompt). The computers' hands stayed at 4 or fewer.
- **Cited by:** E018-r0016.

### Q-BON-07 (C-CRD-05) - one set per turn, what is a set

- **Status:** narrowed
- **This sitting:** two offers to the human (turns 17 and 21), after income and before placement. **Declined (turn 17):** hand +5, wildcard, bomb, bomb, where bomb, bomb and the wildcard would have been a set; the owner clicked no card and pressed the do-not-trade button; the turn went on with the pool unchanged at 10 and no loss of cards. **Accepted (turn 21):** hand +5, wildcard, bomb, bomb, +5; the owner picked the two +5 cards and the wildcard, left the two bombs, and the pool went 18 to 23. Cards 5 to 2.
  The offer's two buttons and the pick of three are as in IP1 028. No computer trade-in; a second trade-in in a turn and three of a kind with no wildcard were not tried. Across IP1 028 and IP1 029: 4 offers, 3 accepted, 1 declined.
- **Cited by:** E018-r0016.

### Q-BON-08 (C-CRD-06) - the bomb card

- **Status:** narrowed (as IP1 028's two cases; none new)
- **This sitting:** no bomb was played: the human held two bomb cards from turn 13 to the end, and the owner declined the one set that would have used them. Nothing new on the bomb's effect.

### Q-BON-09 (C-CRD-07) - the anti-bomb card

- **Status:** unestablished
- **This sitting:** the protection card was drawn by the human (turn 29) and held to the end of the game; no bomb was played against it, so its effect was not seen.
- **Cited by:** E018-r0016.

### Q-BON-10 / Q-BON-11 (C-CRD-05, C-REI-03) - trade-in effects on the pool

- **Status:** narrowed
- **This sitting:** plus 5 from two +5 cards and a wildcard (human, turn 21): pool 18 became 23 (read 18 at 07:54.1 and 07:55.5, 23 at 09:32.6, 09:36.0 and 09:37.0). A declined offer leaves the pool as it was (10, turn 17). Doubling, plus 8 and plus 15 trades were not played in this game.
- **Cited by:** E018-r0016.

## Income

### Q-REI-01 / Q-REI-02 (C-REI-01, C-REI-02) - income from the territory count, the floor of 2

- **Status:** narrowed
- **Static claim:** the country part is the count divided by 3, rounded down, raised to 2; the island bonus is added after; no first-turn exception.
- **This sitting:** the first three human turns (counts 14, 15, 15) gave 4, 5, 5 exactly, the first turn not special; the later ones: 18 gave 10 (6 plus 4, one island named), 20 gave 10 (6 plus 4), 24 gave 18 (8 plus 10), 29 gave 27 (9 plus 18), 31 gave 25 (10 plus 15), the island amounts being sums of the static bonus values (not separated here). The floor of 2 was seen for the computer: yellow with 7 countries (turns 2 and 6) and 6 (turn 26) gave 2; red with 3 countries gave 5 (2 plus 3), green with 5 gave 4 (2 plus 2).
- **Cited by:** E018-r0016.

### Q-REI-03 (C-REI-04) - placing the pool

- **Status:** narrowed
- **This sitting:** the human places through a counter that starts at 0 (all, plus, minus and place buttons) after clicking a country; 8 placements, the whole pool each time on one country; the counter never exceeded the pool. The over-pool and 999 cases are untested.
- **Cited by:** E018-r0017.

### Q-REI-05 - army growth over a game

- **Status:** narrowed (one game's curve, no distribution)
- **This sitting:** armies by colour (blue, the human, / yellow / red / green) from the map counters at 14 moments (E018-r0018): 33/15/21/24 at 00:50, 36/16/21/25 at 03:50, 43/17/16/17 at 06:50, 66/19/13/13 at 09:50, 82/13/11/17 at 11:50, 80/12/0/15 at 13:50 and 67/2/0/14 at 14:40 (blue's countries 14, 18, 24, 25, 29, 34, 40); the largest stack reached 41 (human, 11:50) and the
  computers' largest was 11. The human's total rose from its pool each turn (4 to 27) and fell with its losses; the computers' totals fell with their territory, and the easy level's starting 14 countries (against 9) gave the human a lead from the start (33 armies against 15 to 24 at 00:50). One game; a lower bound by one country whose colour could not be read.
- **Cited by:** E018-r0018.

### Q-BON-01 / Q-BON-02 (C-BON-01, C-BON-02) - island bonuses

- **Status:** narrowed
- **This sitting:** island amounts (the pool minus the country part): the human 4 (one island named, turns 13 and 17), 10, 18, 15; computers 0 to 3 (for example red with 12 countries, pool 7 = 4 plus 3, and with 8 countries, pool 5 = 2 plus 3); partial control not isolated; the nine single-island values not separated here.
- **Cited by:** E018-r0016.

## Setup, turns, events, ending

### Q-SET-04 (C-SET-01) - the options screen

- **Status:** corroborated (a fourth visit; the first target was one)
- **This sitting:** the options screen at 00:03.0 to 00:35 shows the same groups; the starting-level group was changed from the middle entry to the easy entry (between 00:20.5 and 00:24.5) and the speed group from the middle to the slow entry (between 00:24.5 and 00:28.5) before the play button. The controls are exercised: the level and speed groups change on a click.
- **Cited by:** E018-r0017.

### Q-STA-01 / Q-STA-03 (C-STA-03, C-STA-05) - the deal

- **Status:** narrowed
- **Static claim (F018):** the human seat holds exactly 5, 9 or 14 countries at the hard, normal and easy entries, never one more, the computers sharing the rest (none above 15 in the usual case).
- **This sitting:** a fourth deal, at the easy entry: counts blue 14, yellow 7, red 12, green 13 (sum 46): the human at exactly 14, as F018 predicts for the easy level, the first deal not at the middle level; the computers' 7, 12 and 13 are all at most 15. The first seat to play was the human seat, drawn by a 1.7 s flicker of the marker over the seats. Four deals of the target 10 (first seats yellow, human, red, human); the 14 of F018's third level is now seen once and the 5 of its first level not at all.
- **Cited by:** E018-r0016, E018-r0017.

### Q-TRN-02 (C-TRN-02) - seat order

- **Status:** narrowed
- **This sitting:** the playing seat followed blue, yellow, red, green without a break for all 29 turns (7 full rounds and the human's turn 29); the red seat was eliminated during the last turn, so no skip of an eliminated seat was seen here.
- **Cited by:** E018-r0016.

### Q-TRN-05 - game length

- **Status:** narrowed
- **This sitting:** 29 player-turns to the offer at about 14:55 (15:01 to the winner dialog), on the easy level at the owner's own pace: four games in four sittings (55, 46, 47 and 29 turns); four games are not a distribution, and a short game on the easy level says nothing about the middle level.
- **Cited by:** E018-r0016, E018-r0018.

### Q-HAZ-01 / Q-HAZ-02 / C-VIC-04 - event messages

- **Status:** narrowed
- **This sitting:** one event message in 29 turns, between turns 12 and 13, of the production-centre increase kind (04:16.50 to 04:23.00); none before turn 12; 1 of the 26 turn changes from turn 4 on, about 4 per cent (the setting was the middle one, the event group having been left at the middle entry). Across the four sittings 8 of 157 turn changes (about 5 per cent; the claim's range is 1 in 8 to 1 in 21 by setting). No seat held 39 or more countries before the offer (the human held 41 at its end).
- **Cited by:** E018-r0018.

### Q-SUR-01 / Q-SUR-04 (C-SUR-01, C-SUR-02) - the concession offer

- **Status:** narrowed
- **Static claim:** the computers concede collectively to the only human seat when it holds 33 or more of 46 countries, checked once per turn transition by country count; accepting ends the game at once as a scored win.
- **This sitting:** the human seat held 33 countries from 13:34.03 and attacked on for 75 s and 8 more countries (to 41, 14:48.8) in the same turn; the offer came at the turn transition (about 14:55.0), not at the 33rd capture, as in IP1 028 (there 33 was reached and the offer came at the end of the same turn); two cases now, both with the offer at the end of the turn that reached 33. The offer was two buttons (accept the win, keep playing) and a dialog; the owner pressed accept (15:01.0 to 15:01.2) and the game ended at once with a winner dialog (15:01.47), the scoreboard (15:03.77, updated at 15:06.13) and the title screen (about 15:08.0). The previous transitions had the human at 31 or fewer (13:23 to 13:34: 32, 33 during the turn): the boundary 32 against 33 at a transition is not isolated. The refuse path was not taken.
  **The win is on the scoreboard**: after the screen's update (about 2.2 to 2.4 s after it appears, at 15:06.13) the easy row reads 1 won 0 lost and the normal row, which held IP1 028's win, reads 1 won 3 lost; this answers IP1 028's open observation (see the note at the top of this section).
  **Other explanations of the delayed update (Luna's review of PR #188, R5):**
  - *A redraw or animation, not a late write.* The screen may draw the new counts as an animation after showing the stored ones. The record shows one change at 15:06.13 and nothing about how it is drawn, so this is not excluded; either way the result is counted.
  - *A frame-timing artefact.* The video's frame timestamps are irregular. Still, the change is seen in consecutive frames (15:06.0 to 15:06.2), and 2.2 to 2.4 s is far beyond a frame interval, so this is excluded.
  - *A count from somewhere else, such as a second game.* Excluded for this sitting: the easy row went from 0/0 to 1/0, and this was the only easy game.
- **Cited by:** E018-r0018.

### Q-SUR-03 (C-SUR-03) - what an eliminated seat's cards do

- **Status:** narrowed
- **This sitting:** the red seat was eliminated by the human's attack 48 (0 countries at 13:50.07); its cards went from 4 to 0 at 13:57.13, seven seconds later in the same turn, and the human's count stayed 4 (no inheritance by a human capturer, as for a computer in IP1 028). The yellow seat, eliminated at 14:48.8 by the last attack of the turn, still showed 3 cards at 14:58.5 (the offer's screen): the cards are wiped some time after the seat reaches 0, which agrees with F012's reading that they are cleared at a later rebuild of the seat lists, not at the capture.
- **Cited by:** E018-r0016, E018-r0018.

### Q-VIC-01 (C-VIC-01) - the end by conquest

- **Status:** unestablished (the game ended by the concession; no conquest of 46)
- **This sitting:** nothing new: 41 of 46 held at the end.

## Computer opponent

### C-AI-03 / C-AI-04 (Q-AI-01, Q-AI-04) - attacks and turns with none

- **Status:** narrowed
- **This sitting:** 23 computer attacks in 21 computer turns recorded with counts before and after (table above); the gates of Q-CMB-01 and Q-CMB-03 hold in all 23. Four computer turns had no attack at all (turns 2, 8, 26, 28: yellow 7 countries, green 10, yellow 6, green 5), 4 of 21 (19 per cent); over the four sittings 16 of 131; see Q-CMB-10. The cause (the skip draw or no qualifying pair) is not visible. The target is 20 games.
- **Cited by:** E018-r0015, E018-r0016.

### Q-AI-05 / Q-AI-02 / C-AI-06 - placement and cards

- **Status:** unestablished for placement (the computer places with no screen); no computer trade-in in this game.

### Q-AI-07 - strength against scripted opponents

- **Status:** narrowed (one more game that the human won, on the easy level, by stacking on one country per turn and taking neighbours one at a time; a win rate needs many games and a scripted opponent)

### C-AI-05 (Q-AI-04's move half) - the computer's end-of-turn move

- **Status:** unestablished here (no computer move detected in 21 turns; see Q-MOV-01).

## What only a human sitting shows (constraint E)

These rest on the owner's videos, and on this one for the sitting's own readings; none is a rule claim.

- The owner won on the easy level at slow speed, taking 41 countries (the concession was accepted with 5 countries left to green) and attacking on for 75 s after reaching 33.
- Stacking: the owner placed the whole pool on one country every turn (8 of 8) and attacked from it, with stacks of 8, 12, 13, 17, 27 and 41 against defenders of 1 to 4; turn 29 took 10 countries in one turn (11 attacks), mostly moving all but one in after each capture.
- The owner declined a trade-in offer that was a set (two bombs and a wildcard) and accepted the next one (two +5 cards and a wildcard); the offer of turn 21 stayed open for about 90 s while the owner chose, and the owner kept two bombs for the rest of the game without playing them.
- The owner started a move and cancelled it twice (turns 13 and 21), the second time followed by an attack order that was also cancelled, then moved; four moves were all but one.
- The owner quit two battles (attacks 9 and 53) at 2 against 1, both from stacks that had fallen from 3 and 9 armies.
- The computer's answer to the owner's play is not separable from its own policy here; the data above is the computer's play, with no model-driven sitting to compare.

## Re-reads (rule 20)

A re-read of `IP1 029.mp4` writes new files beside r0015..r0018 (the next free record numbers) with their own frame hashes, and says which record it cross-references; these records stay as written.

**Correction notes (Luna's review of PR #188):**
- **R1, rule 18 D: the records were reworded before merge** (the owner's decision, 2026-10-12, as with 8274ccd for IP1 027). r0016–r0018 named the original's cards, buttons and dialogs in its own words. Those were replaced with our own role words, and no count, offset or value changed: a script compared the digits of every changed field. The role words are: the five-army and fifteen-army cards, the joker, the strike card, the shield card; the draw screen and the tally screen; the accept and decline buttons of the trade-in offer; the all-but-one, up, down and confirm buttons of the counter; the accept and play-on buttons of the concession; a dialog announcing the concession, and a dialog naming the winner. Evidence file names in the manifests are unchanged.
- **R2, readings inside observations.** Read these clauses as interpretation, not observation. They come from a full read of every non-routine observation in r0015–r0018:
  - *finding, question or E021 references:* r0017 obs[12] ("no even or underdog cell of E021"); r0016 obs[53] ("not inherited");
  - *formulas and rule readings:* r0016 obs[54] (the pool formula and the island amounts); r0016 obs[51] (the pool rise read as +5 armies);
  - *comparisons with other sittings or sources:* r0016 obs[1] (the deal against the earlier sittings, the first seats so far); r0016 obs[49] (the fifteen-army card first seen in four sittings); r0016 obs[50] (the first declined offer); r0016 obs[53] ("for a human capturer", against IP1 028); r0017 obs[0] ("as in the three earlier sittings"); r0017 obs[17] ("the largest so far", the template that found moves in 027 and 028); r0017 obs[18] (the rows confirmed against IP1 028); r0018 obs[0] (the event rate against the setting and the four sittings); r0018 obs[19] ("as in IP1 028"); r0018 obs[20] (which games the normal row "fits", and "so the win of a concession is recorded"); r0018 obs[21] (IP1 028's note "explained by the timing");
  - *derivations and method notes:* r0015 obs[1] (the last exchange of a capture inferred); r0015 obs[2] (the computer's start taken from the counters); r0018 obs[17] (totals as lower bounds); r0018 obs[18] (the scoreboard "not yet clearing" yellow's cards); r0016 obs[0] (the card count lagging the draw screen).
