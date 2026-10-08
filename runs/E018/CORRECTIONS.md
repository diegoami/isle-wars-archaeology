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
