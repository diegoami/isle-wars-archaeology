# E004 stage times, E004-r0030-r0045

Seconds, median (range, n) over the completed records of each arm of E004-r0030-r0045, read from their observations.

| stage | `control` | `kill-mid-cycle` | `sigkill-mid-cycle` |
| --- | --- | --- | --- |
| Xvfb ready | 0.11 (0.06 to 0.11, n=10) | 0.11 (0.11 to 0.11, n=2) | 0.11 (0.11 to 0.12, n=2) |
| xfwm4 registered | 0.23 (0.23 to 0.35, n=10) | 0.36 (0.24 to 0.49, n=2) | 0.29 (0.23 to 0.36, n=2) |
| snapshot of the prefix before the launch | 0.82 (0.66 to 4.38, n=10) | 1.00 (0.79 to 1.22, n=2) | 1.02 (0.68 to 1.35, n=2) |
| game window after launch | 1.12 (0.88 to 1.37, n=10) | 1.31 (1.11 to 1.50, n=2) | 1.36 (1.00 to 1.73, n=2) |
| title screen reached and stable, after launch | 7.88 (7.41 to 8.38, n=10) | 8.52 (7.85 to 9.19, n=2) | 8.71 (7.80 to 9.62, n=2) |
| terminate (`wineserver -k` and the bounded wait) | 0.76 (0.50 to 0.76, n=10) | 0.76 (0.75 to 0.76, n=2) | 0.76 (0.76 to 0.76, n=2) |
| game side gone after terminate | 0.00 (0.00 to 0.01, n=10) | 0.00 (0.00 to 0.00, n=2) | 0.00 (0.00 to 0.00, n=2) |
| display side gone after Xvfb and xfwm4 stopped | 3.02 (3.00 to 3.03, n=10) | 3.01 (3.00 to 3.02, n=2) | 3.01 (3.00 to 3.03, n=2) |
| stopping the display | 3.04 (3.01 to 3.05, n=10) | 3.03 (3.03 to 3.03, n=2) | 3.04 (3.03 to 3.05, n=2) |
| snapshot, diff and reset | 1.84 (1.58 to 2.66, n=10) | 2.44 (1.89 to 2.98, n=2) | 1.86 (1.85 to 1.88, n=2) |
| the whole session, first seal to end of reset | 16.15 (15.16 to 21.34, n=10) | 17.89 (16.21 to 19.58, n=2) | 17.59 (16.01 to 19.17, n=2) |

## Aborted repeats

- E004-r0041 (arm `kill-mid-cycle`): `aborted: game-died: the game process exited before the screenshot before.png (status 0)`; prefix after reset equals prefix before launch: yes; session 17.58 s
- E004-r0044 (arm `sigkill-mid-cycle`): `aborted: game-died: the game process exited before the options screen appeared (status -9)`; prefix after reset equals prefix before launch: yes; session 15.67 s
