# E004 cycle table, E004-r0078-r0093

Made by `make_tables.py 78 93` from `runs/E004/`. One row per record.

| run | arm | rep | status | session s | before pixels sha256 (first 16) | before.png file sha256 (first 16) | start_state sha256 (first 16) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E004-r0078 | control | 51 | completed | 10.72 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0079 | control | 52 | completed | 10.62 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0080 | control | 53 | completed | 13.85 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0081 | control | 54 | completed | 12.03 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0082 | control | 55 | completed | 10.82 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0083 | control | 56 | completed | 11.2 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0084 | control | 57 | completed | 10.43 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0085 | control | 58 | completed | 10.07 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0086 | control | 59 | completed | 9.92 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0087 | control | 60 | completed | 9.91 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0088 | kill-mid-cycle | 13 | completed | 9.79 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0089 | kill-mid-cycle | 14 | aborted: game-died: the game process exited before the screenshot befo | 8.9 | none | none | b1df17775116d148 |
| E004-r0090 | kill-mid-cycle | 15 | completed | 10.02 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0091 | sigkill-mid-cycle | 16 | completed | 9.95 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0092 | sigkill-mid-cycle | 17 | aborted: game-died: the game process exited before the options screen  | 9.44 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0093 | sigkill-mid-cycle | 18 | completed | 10.06 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |

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
