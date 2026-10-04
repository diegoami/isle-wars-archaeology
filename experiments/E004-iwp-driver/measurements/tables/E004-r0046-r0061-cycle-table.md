# E004 cycle table, E004-r0046-r0061

Made by `make_tables.py 46 61` from `runs/E004/`. One row per record.

| run | arm | rep | status | session s | before pixels sha256 (first 16) | before.png file sha256 (first 16) | start_state sha256 (first 16) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E004-r0046 | control | 31 | completed | 15.18 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0047 | control | 32 | completed | 11.18 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0048 | control | 33 | completed | 11.42 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0049 | control | 34 | completed | 11.07 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0050 | control | 35 | completed | 10.83 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0051 | control | 36 | completed | 12.05 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0052 | control | 37 | completed | 10.65 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0053 | control | 38 | completed | 10.47 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0054 | control | 39 | completed | 11.03 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0055 | control | 40 | completed | 12.29 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0056 | kill-mid-cycle | 7 | completed | 12.26 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0057 | kill-mid-cycle | 8 | aborted: game-died: the game process exited before the screenshot befo | 11.31 | none | none | b1df17775116d148 |
| E004-r0058 | kill-mid-cycle | 9 | completed | 11.65 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0059 | sigkill-mid-cycle | 10 | completed | 12.11 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0060 | sigkill-mid-cycle | 11 | aborted: game-died: the game process exited before the options screen  | 11.12 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |
| E004-r0061 | sigkill-mid-cycle | 12 | completed | 11.32 | fecd0a984e0d2f36 | ae6e98d28d379bb4 | b1df17775116d148 |

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
