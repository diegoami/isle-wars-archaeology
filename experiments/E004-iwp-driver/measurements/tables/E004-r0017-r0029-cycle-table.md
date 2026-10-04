# E004 cycle table, E004-r0017-r0029

Made by `make_tables.py 17 29` from `runs/E004/`. One row per record.

| run | arm | rep | status | session s | before pixels sha256 (first 16) | before.png file sha256 (first 16) | start_state sha256 (first 16) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E004-r0017 | control | 11 | completed | 14.99 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0018 | control | 12 | completed | 14.92 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0019 | control | 13 | completed | 14.84 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0020 | control | 14 | completed | 15.21 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0021 | control | 15 | completed | 15.21 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0022 | control | 16 | completed | 15.52 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0023 | control | 17 | completed | 14.68 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0024 | control | 18 | completed | 14.91 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0025 | control | 19 | completed | 15.22 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0026 | control | 20 | completed | 15.53 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0027 | sigkill-mid-cycle | 4 | completed | 15.2 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0028 | sigkill-mid-cycle | 5 | aborted: game-died: the game process exited before the options screen  | 14.59 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0029 | sigkill-mid-cycle | 6 | completed | 14.49 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |

## What is identical

- before pixels sha256, arm `control`: 10 completed record(s), 1 distinct value(s)
- before pixels sha256, arm `sigkill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- before pixels sha256, all completed records: 12 records, 1 distinct value(s): `fecd0a984e0d2f36d0c91f1ab2504a335bfdd059907a2622ba2d40804c983753`
- before.png file sha256, arm `control`: 10 completed record(s), 1 distinct value(s)
- before.png file sha256, arm `sigkill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- before.png file sha256, all completed records: 12 records, 1 distinct value(s): `ae6e98d28d379bb4d2a9c4793ce5aac51222be771f1c666d8a614c26758bab83`
- after.png file sha256, arm `control`: 10 completed record(s), 1 distinct value(s)
- after.png file sha256, arm `sigkill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- after.png file sha256, all completed records: 12 records, 1 distinct value(s): `426d77e724d793ddbe78a94bd79c173145b7be35d56b9a0ae211f0e74f81b693`
- start_state sha256, arm `control`: 10 completed record(s), 1 distinct value(s)
- start_state sha256, arm `sigkill-mid-cycle`: 2 completed record(s), 1 distinct value(s)
- start_state sha256, all completed records: 12 records, 1 distinct value(s): `b1df17775116d1482d9fb8efdd62780ab8bd47af510e00e1a2eade9c5c320695`

## The seal and the clean-up, in every record that reached them

| observation | value wanted | records with it | records |
| --- | --- | --- | --- |
| install read-only inside the run | yes | 13 | 13 of 13 |
| prefix seal before anything starts: problems found | 0 | 13 | 13 of 13 |
| registry files equal their baseline before the launch | yes | 13 | 13 of 13 |
| prefix seal immediately before launch: problems found | 0 | 13 | 13 of 13 |
| game in its own network namespace | yes | 13 | 13 of 13 |
| network interfaces the game sees | lo | 13 | 13 of 13 |
| processes of this run still alive after terminate | 0 | 13 | 13 of 13 |
| prefix after reset equals prefix before launch | yes | 13 | 13 of 13 |

| observation | values seen | records |
| --- | --- | --- |
| input steps that succeeded so far | n/a | 0 of 13 |
| clean-up: every stage succeeded and the prefix was reset (the next session may start) | n/a | 0 of 13 |
