# F011 questions — the per-arm count targets

Source: `findings/F011-pro-combat-rules.md`, each question's **T28** paragraph.

The main session runs the walkthroughs and writes a record per question to
`runs/E018/combat/<run-id>.json`. The per-arm count target is the
minimum number of recorded plays (or exchanges) the plan asks for; the
outcome is `corroborated` if the count is met and the static claim
matches what play shows, `narrowed` if it matches partially, `unestablished`
if it doesn't match at all.

| Q-id | C-id | Count target | What to record |
| --- | --- | --- | --- |
| Q-MOV-01 | C-MOV-01 | 10 + 5 + 30 | Human: 10 turns with a move; 5 with attack first. Computer: 30 turns, moves per turn. |
| Q-MOV-02 | C-MOV-02 | 2 + 2 + 2 | Stacks 2, 3, 10: all / all-but-one / all-but-two. Counter to 0? Static-only for 999 clip. |
| Q-MOV-03 | C-MOV-03 | 10 + 3 + 5 | After move: second move + attack. Destination 2 borders away. Capture then attack same turn. |
| Q-CMB-01 | C-CMB-01 | 16 + 100 | Human: 16 cases (N in {2,4,8,12} × target in {N-1,N,N+1,N+2}). Computer: 100+ attack starts. |
| Q-CMB-02 | C-CMB-02 | 4 + 100 | Human: N in {4,8,12,20}, once each. Computer: 100+ starts, lowest diff. |
| Q-CMB-03 | C-CMB-03 | 3 + 100 | Human: 3 cases (attacker 1, 2, 3 vs defender 1). Computer: 100+ starts, smallest stack. |
| Q-CMB-04 | C-CMB-04 | 500 | 100+ exchanges per attacker size in {2,3,4,5,10} vs defender 1. One army lost per exchange. |
| Q-CMB-05 | C-CMB-05 | 500 | 100+ exchanges per defender size in {1,2,3,4,10} vs attacker fixed. |
| Q-CMB-06 | C-CMB-06 | 500 | Total exchanges, attacker-loss share (expect ~58%, 7/12). |
| Q-CMB-07 | C-CMB-07 | 200 | Each exchange is (attacker -1, defender 0) or (0, defender -1) and no other. |
| Q-CMB-08 | C-CMB-08 | 10 + 30 | Human: 10 attacks, single vs multiple exchanges, quit button. Computer: 30 battles, stop reason and armies. |
| Q-CMB-09 | C-CMB-09 | 5 + 20 | Human: 5 failed attacks, owner/armies/card/next turn. Computer: 20 no-capture battles, no country change. |
| Q-CMB-10 | C-CMB-10 | 10 + 30 | Human: 10 turns with 3+ attacks, what ended each. Computer: attacks per turn vs owned-country count. |
| Q-CMB-11 | C-CMB-11 | 500 | 500 exchanges split by VIPC-list country membership. |
| Q-CMB-12 | C-CMB-12 | 100 + 20 | **Dropped this batch** — "never attacks" is rare. |
| Q-OWN-01 | C-OWN-01 | 3 + 3 + 3 + 3 | Captures from stacks {2, 3, 5, 10}, 3 each. Counter to 0? Try small stacks only (2, 3, 5). |
| Q-SET-04 | C-SET-04 | 1 | List controls on the options screen (one visit). |

## What "out of the way" means here

For Q-CMB-01 through Q-CMB-03, the per-arm count is a small number of
targeted plays (16, 4, 3). The main session reads the plan and decides which
games reach the right positions. A natural game has ~46 countries, and the
human (Blue) starts with some; the main session looks for a country where
the human has N armies and a neighbour has the target count.

For Q-CMB-04/05/06/07/11, the data comes from computer play. The main
session plays the human's turn with `ALL` on a country and then `PASS`,
and lets the computer attack. Each computer attack gives one exchange. 500
exchanges need many games.

For Q-MOV-01/02/03 and Q-OWN-01, the main session plays the human's
turn (move, capture) and records the outcome.

For Q-SET-04, one visit to the options screen and a screenshot of the
control list suffices.
