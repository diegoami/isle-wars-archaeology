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
