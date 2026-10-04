# E004 stage times, E004-r0046-r0061

Seconds, median (range, n) over the completed records of each arm of E004-r0046-r0061, read from their observations.

| stage | `control` | `kill-mid-cycle` | `sigkill-mid-cycle` |
| --- | --- | --- | --- |
| Xvfb ready | 0.11 (0.10 to 0.11, n=10) | 0.11 (0.10 to 0.11, n=2) | 0.11 (0.11 to 0.11, n=2) |
| xfwm4 registered | 0.12 (0.12 to 0.24, n=10) | 0.23 (0.22 to 0.23, n=2) | 0.23 (0.22 to 0.23, n=2) |
| snapshot of the prefix before the launch | 0.56 (0.54 to 3.50, n=10) | 0.63 (0.61 to 0.65, n=2) | 0.60 (0.56 to 0.65, n=2) |
| game window after launch | 0.76 (0.64 to 1.71, n=10) | 0.99 (0.77 to 1.22, n=2) | 0.93 (0.87 to 0.99, n=2) |
| title screen reached and stable, after launch | 7.02 (6.66 to 8.01, n=10) | 7.37 (7.11 to 7.63, n=2) | 7.22 (7.03 to 7.41, n=2) |
| terminate (`wineserver -k` and the bounded wait) | 0.75 (0.50 to 0.75, n=10) | 0.75 (0.75 to 0.75, n=2) | 0.75 (0.75 to 0.75, n=2) |
| game side gone after terminate | 0.00 (0.00 to 0.00, n=10) | 0.00 (0.00 to 0.00, n=2) | 0.00 (0.00 to 0.00, n=2) |
| display side gone after Xvfb and xfwm4 stopped | 0.00 (0.00 to 0.00, n=10) | 0.00 (0.00 to 0.00, n=2) | 0.00 (0.00 to 0.00, n=2) |
| stopping the display | 0.01 (0.01 to 0.04, n=10) | 0.01 (0.01 to 0.01, n=2) | 0.03 (0.01 to 0.04, n=2) |
| snapshot, diff and reset | 1.29 (1.19 to 2.01, n=10) | 1.46 (1.40 to 1.53, n=2) | 1.46 (1.34 to 1.57, n=2) |
| the whole session, first seal to end of reset | 11.12 (10.47 to 15.18, n=10) | 11.96 (11.65 to 12.26, n=2) | 11.71 (11.32 to 12.11, n=2) |

## Aborted repeats

- E004-r0057 (arm `kill-mid-cycle`): `aborted: game-died: the game process exited before the screenshot before.png (status 0)`; prefix after reset equals prefix before launch: yes; session 11.31 s
- E004-r0060 (arm `sigkill-mid-cycle`): `aborted: game-died: the game process exited before the options screen appeared (status -9)`; prefix after reset equals prefix before launch: yes; session 11.12 s
