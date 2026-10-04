# E004 cycle table, E004-r0062-r0077

Made by `make_tables.py 62 77` from `runs/E004/`. One row per record.

| run | arm | rep | status | session s | before pixels sha256 (first 16) | before.png file sha256 (first 16) | start_state sha256 (first 16) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E004-r0062 | control | 41 | completed | 12.64 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0063 | control | 42 | completed | 9.88 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0064 | control | 43 | completed | 9.84 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0065 | control | 44 | completed | 10.03 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0066 | control | 45 | completed | 9.88 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0067 | control | 46 | completed | 10.01 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0068 | control | 47 | completed | 10.2 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0069 | control | 48 | completed | 9.84 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0070 | control | 49 | completed | 9.78 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0071 | control | 50 | completed | 9.84 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0072 | kill-mid-cycle | 10 | completed | 9.85 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0073 | kill-mid-cycle | 11 | aborted: game-died: the game process exited before the screenshot befo | 8.92 | none | none | b1df17775116d148 |
| E004-r0074 | kill-mid-cycle | 12 | completed | 9.74 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0075 | sigkill-mid-cycle | 13 | completed | 9.83 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0076 | sigkill-mid-cycle | 14 | aborted: game-died: the game process exited before the options screen  | 9.27 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0077 | sigkill-mid-cycle | 15 | completed | 9.8 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |

## What is identical

- before pixels sha256, arm `control`: 10 completed record(s), 1 distinct value(s)
- before pixels sha256, arm `kill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- before pixels sha256, arm `sigkill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- before pixels sha256, all completed records: 14 records, 1 distinct value(s): `fecd0a984e0d2f36d0c91f1ab2504a335bfdd059907a2622ba2d40804c983753`
- before.png file sha256, arm `control`: 10 completed record(s), 1 distinct value(s)
- before.png file sha256, arm `kill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- before.png file sha256, arm `sigkill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- before.png file sha256, all completed records: 14 records, 1 distinct value(s): `ae6e98d28d379bb4d2a9c4793ce5aac51222be771f1c666d8a614c26758bab83`
- after.png file sha256, arm `control`: 10 completed record(s), 1 distinct value(s)
- after.png file sha256, arm `kill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- after.png file sha256, arm `sigkill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- after.png file sha256, all completed records: 14 records, 1 distinct value(s): `426d77e724d793ddbe78a94bd79c173145b7be35d56b9a0ae211f0e74f81b693`
- start_state sha256, arm `control`: 10 completed record(s), 1 distinct value(s)
- start_state sha256, arm `kill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- start_state sha256, arm `sigkill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- start_state sha256, all completed records: 14 records, 1 distinct value(s): `b1df17775116d1482d9fb8efdd62780ab8bd47af510e00e1a2eade9c5c320695`

## The seal and the clean-up, in every record that reached them

| observation | value wanted | records with it | records |
| --- | --- | --- | --- |
| install read-only inside the run | yes | 0 | 0 of 16 |
| install read-only inside the run (before anything starts) | yes | 16 | 16 of 16 |
| prefix seal before anything starts: problems found | 0 | 16 | 16 of 16 |
| registry files equal their baseline before the launch | yes | 0 | 0 of 16 |
| registry files equal their baseline (before anything starts) | yes | 16 | 16 of 16 |
| install read-only inside the run (immediately before launch) | yes | 16 | 16 of 16 |
| prefix seal immediately before launch: problems found | 0 | 16 | 16 of 16 |
| registry files equal their baseline (immediately before launch) | yes | 16 | 16 of 16 |
| game and display alive just before terminate | yes | 14 | 16 of 16 |
| X display held by this run's Xvfb (attempt) | 1 | 16 | 16 of 16 |
| game in its own network namespace | yes | 16 | 16 of 16 |
| network interfaces the game sees | lo | 16 | 16 of 16 |
| processes of this run still alive after terminate | 0 | 16 | 16 of 16 |
| prefix after reset equals prefix before launch | yes | 16 | 16 of 16 |

| observation | values seen | records |
| --- | --- | --- |
| input steps that succeeded so far | 1 | 15 of 16 |
| clean-up: every stage succeeded and the prefix was reset (the next session may start) | yes | 16 of 16 |
