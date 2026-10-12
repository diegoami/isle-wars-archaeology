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
