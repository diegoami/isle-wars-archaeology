# E004 stage times, E004-r0017-r0029

Seconds, median (range, n) over the completed records of each arm of E004-r0017-r0029, read from their observations.

| stage | `control` | `sigkill-mid-cycle` |
| --- | --- | --- |
| Xvfb ready | 0.11 (0.11 to 0.11, n=10) | 0.11 (0.10 to 0.12, n=2) |
| xfwm4 registered | 0.23 (0.23 to 0.24, n=10) | 0.23 (0.22 to 0.23, n=2) |
| snapshot of the prefix before the launch | 0.64 (0.58 to 0.84, n=10) | 0.66 (0.60 to 0.72, n=2) |
| game window after launch | 0.99 (0.77 to 1.23, n=10) | 0.88 (0.88 to 0.88, n=2) |
| title screen reached and stable, after launch | 7.42 (7.16 to 7.83, n=10) | 7.37 (7.11 to 7.62, n=2) |
| terminate (`wineserver -k` and the bounded wait) | 0.63 (0.50 to 0.76, n=10) | 0.50 (0.50 to 0.50, n=2) |
| game side gone after terminate | 0.00 (0.00 to 0.00, n=10) | 0.00 (0.00 to 0.00, n=2) |
| display side gone after Xvfb and xfwm4 stopped | 3.02 (3.00 to 3.05, n=10) | 3.01 (3.00 to 3.02, n=2) |
| stopping the display | 3.04 (3.01 to 3.06, n=10) | 3.02 (3.01 to 3.03, n=2) |
| snapshot, diff and reset | 1.52 (1.42 to 1.70, n=10) | 1.50 (1.50 to 1.51, n=2) |
| the whole session, first seal to end of reset | 15.10 (14.68 to 15.53, n=10) | 14.84 (14.49 to 15.20, n=2) |

## Aborted repeats

- E004-r0028 (arm `sigkill-mid-cycle`): `aborted: game-died: the game process exited before the options screen appeared (status -9)`; prefix after reset equals prefix before launch: yes; session 14.59 s
