# Tasks

One file per task, `T<nn>.md`, from [`TEMPLATE.md`](TEMPLATE.md). This index is the plan: every task
written or planned, in order (CLAUDE.md rule 23). A planned task has an issue labelled
`status:planned`, and its task file is written when it is next. The index carries no status: the
issue's `status:*` label is the status (`gh issue list --label task --state all`).

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
| T17 | Research-question backlog v1, DOS first (W6) | #65 | T14 |
| T18 | Setup determinism: DOS Isle Wars (W7b) | #66 | T15, T17 |
| T19 | Research review with reruns of T18 (W8b) | #67 | T18 |
| T20 | Combat rules: DOS Isle Wars | #68 | T16, T18 |
| T21 | Reinforcement and island bonuses: DOS Isle Wars | #69 | T16, T18 |
| T22 | Cards and trade-ins: DOS Isle Wars | #70 | T16, T18 |
| T23 | Production centres and hazards: DOS Isle Wars | #71 | T16, T18 |
| T24 | UI observations for malpaco: Isle Wars Pro | #72 | T09 |

The plan after T14 is the owner's of 2026-10-05: the research concentrates on DOS *Isle Wars*. Pro
stays for malpaco's UI (T24), and T13, the Pro driver, is parked. T20 to T23 are refined by T17's
backlog.
