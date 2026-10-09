# Tasks

One file per task, `T<nn>.md`, from [`TEMPLATE.md`](TEMPLATE.md). This index lists the task files that
exist, each with its issue. The plan, including tasks not yet written, is the set of task issues
(CLAUDE.md rule 23): `gh issue list --label task --state all`. The issue's `status:*` label is the
status; this index carries none.

| Task | Title | Issue | Merge after |
| --- | --- | --- | --- |
| T01 | The research repository: layout, knowledge map, guards (W0) | #1 | — |
| T02 | Registration tools and the guards that use them (W1a prerequisite; folds #3) | #4 | T01 |
| T03 | Artifact identity: Isle Wars Pro (W1a) | #5 | T02 |
| T04 | Documentation map, part 1: Isle Wars Pro's own documents and the user's report (W2a) | #6 | T03, T06 |
| T05 | Documentation map, part 2: public sources for both games (W2b) | #7 | T04 |
| T06 | The quote checker (W2a prerequisite) | #8 | T02 |
| T07 | malpaco's rules as research questions | #16 | — |
| T08 | Runtime feasibility: Isle Wars Pro under Wine and Xvfb (W3a) | #24 | T03 |
| T09 | Observable-state inventory: Isle Wars Pro (W4a; folds #27) | #29 | T08 |
| T10 | Artifact identity: DOS Isle Wars (W1b) | #30 | T03 |
| T11 | Runtime feasibility: DOS Isle Wars under DOSBox-X (W3b) | #34 | T10 |
| T12 | Use game-archaeologist's pinned validator and register_artifact.py (folds #42, #48) | #49 | — |
| T13 | Minimal driver: Isle Wars Pro (W5a; folds #40's cycle-time items) | #51 | T09 |
| T14 | Observable-state inventory: DOS Isle Wars (W4b) | #52 | T11 |
| T15 | Minimal driver: DOS Isle Wars (W5b) | #63 | T14 |
| T16 | Save format: DOS `ISLEWAR.SAV` decoded, and a crafted-save setup (W4b follow-on) | #64 | T14 |
| T26 | Static triage: unpack, identify and load both executables (U32, static first) | #76 | — |
| T29 | Reviewer read access to the machine-local static folder | #81 | — |
| T17 | Research-question backlog v2: Pro, static first | #65 | T26 |
| T20 | Combat rules: Pro Lingo reading | #68 | T17, T29 |
| T31 | Implementer read access to the machine-local static folder | #89 | T29 |
| T30 | Turn order, victory and concession: Pro Lingo reading | #85 | T17, T31 |
| T21 | Reinforcement and island bonuses: Pro Lingo reading | #69 | T17, T31 |
| T22 | Cards and trade-ins: Pro Lingo reading | #70 | T17, T29 |
| T23 | Production centres and hazards: Pro Lingo reading | #71 | T17, T29 |
| T27 | Computer opponent: Pro Lingo reading | #79 | T17, T29 |
| T32 | Board and adjacency: Pro Lingo reading (T18 part 1) | #96 | T17, T31 |
| T33 | The deal and starting state: Pro Lingo reading (T18 part 2) | #97 | T17, T31, T27 |
| T34 | Setup, seats, files and randomness: Pro Lingo reading (T18 part 3) | #98 | T17, T31 |
| T28 | Pro corroboration of the Lingo rule readings, from recorded play | #80 | T13, T20, T21, T22, T23, T27, T30 |
| T25 | Bring the findings into game-archaeologist's `check_citations.py` form | #57 | — |
| T24 | UI observations for malpaco: Isle Wars Pro | #72 | T17 |
| T35 | F019 known-good Islepro.exe sha256 table for the rule 18 carve-out | #107 | T36, T37 |
| T36 | `check_no_originals.py` constraint F: gate wine-on-user-machine runs on F019 hash | #108 | T35, T37 |
| T37 | Wine driver: model-driven run capture under rule 18 carve-out | #109 | T35, T36 |
| T38 | First model-driven run under Wine: the watcher, the click-driver and the E020 sitting | #114 | T20, T21, T22, T23, T27, T30, T37 |
| T40 | E020 reader and counts: read the sittings' frames by pixels | #119 | T38 |
| T41 | E020 driver: play each game to its end, and the Scoreboard | #123 | T38 |
| T42 | E020 watcher: capture fast enough to see single exchanges | #128 | T41 |
| T45 | Model-played Session A, attacks: the human boundary cases | #143 | #141, the harness bump |
