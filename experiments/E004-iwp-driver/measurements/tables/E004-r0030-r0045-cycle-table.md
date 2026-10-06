# E004 cycle table, E004-r0030-r0045

Made by `make_tables.py 30 45` from `runs/E004/`. One row per record.

| run | arm | rep | status | session s | before pixels sha256 (first 16) | before.png file sha256 (first 16) | start_state sha256 (first 16) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E004-r0030 | control | 21 | completed | 21.34 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0031 | control | 22 | completed | 17.2 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0032 | control | 23 | completed | 16.33 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0033 | control | 24 | completed | 16.26 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0034 | control | 25 | completed | 16.04 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0035 | control | 26 | completed | 16.04 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0036 | control | 27 | completed | 16.03 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0037 | control | 28 | completed | 15.88 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0038 | control | 29 | completed | 15.16 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0039 | control | 30 | completed | 16.45 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0040 | kill-mid-cycle | 4 | completed | 16.21 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0041 | kill-mid-cycle | 5 | aborted: game-died: the game process exited before the screenshot befo | 17.58 | none | none | b1df17775116d148 |
| E004-r0042 | kill-mid-cycle | 6 | completed | 19.58 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0043 | sigkill-mid-cycle | 7 | completed | 19.17 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0044 | sigkill-mid-cycle | 8 | aborted: game-died: the game process exited before the options screen  | 15.67 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0045 | sigkill-mid-cycle | 9 | completed | 16.01 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |

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
| install read-only inside the run | yes | 16 | 16 of 16 |
| prefix seal before anything starts: problems found | 0 | 16 | 16 of 16 |
| registry files equal their baseline before the launch | yes | 16 | 16 of 16 |
| prefix seal immediately before launch: problems found | 0 | 16 | 16 of 16 |
| game in its own network namespace | yes | 16 | 16 of 16 |
| network interfaces the game sees | lo | 16 | 16 of 16 |
| processes of this run still alive after terminate | 0 | 16 | 16 of 16 |
| prefix after reset equals prefix before launch | yes | 16 | 16 of 16 |

| observation | values seen | records |
| --- | --- | --- |
| input steps that succeeded so far | 1 | 15 of 16 |
| clean-up: every stage succeeded and the prefix was reset (the next session may start) | yes | 16 of 16 |
