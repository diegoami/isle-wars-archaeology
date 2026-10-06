# E004 cycle table

Made by `make_tables.py` from `runs/E004/*.json`. One row per record.

| run | arm | rep | status | session s | before pixels sha256 (first 16) | before.png file sha256 (first 16) | start_state sha256 (first 16) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E004-r0001 | control | 1 | completed | 14.26 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0002 | control | 2 | completed | 14.25 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0003 | control | 3 | completed | 15.08 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0004 | control | 4 | completed | 14.91 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0005 | control | 5 | completed | 15.04 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0006 | control | 6 | completed | 14.94 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0007 | control | 7 | completed | 15.45 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0008 | control | 8 | completed | 15.25 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0009 | control | 9 | completed | 16.24 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0010 | control | 10 | completed | 15.71 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0011 | kill-mid-cycle | 1 | completed | 15.47 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0012 | kill-mid-cycle | 2 | aborted: game-died: the game process exited before the screenshot befo | 13.95 | none | none | b1df17775116d148 |
| E004-r0013 | kill-mid-cycle | 3 | completed | 15.54 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0014 | sigkill-mid-cycle | 1 | completed | 15.03 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0015 | sigkill-mid-cycle | 2 | aborted: game-died: the game process exited before the options screen  | 15.23 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0016 | sigkill-mid-cycle | 3 | completed | 15.39 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |

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

## The seal, in every record that reached it

| observation | value | records with it | records |
| --- | --- | --- | --- |
| install read-only inside the run | yes | 16 | 16 of 16 |
| prefix seal before anything starts: problems found | 0 | 16 | 16 of 16 |
| registry files equal their baseline before the launch | yes | 16 | 16 of 16 |
| prefix seal immediately before launch: problems found | 0 | 16 | 16 of 16 |
| game in its own network namespace | yes | 16 | 16 of 16 |
| network interfaces the game sees | lo | 16 | 16 of 16 |
| processes of this run still alive after terminate | 0 | 16 | 16 of 16 |
| prefix after reset equals prefix before launch | yes | 16 | 16 of 16 |

