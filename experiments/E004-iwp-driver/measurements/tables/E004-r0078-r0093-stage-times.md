# E004 stage times, E004-r0078-r0093

Seconds, median (range, n) over the completed records of each arm of E004-r0078-r0093, read from their observations.

| stage | `control` | `kill-mid-cycle` | `sigkill-mid-cycle` |
| --- | --- | --- | --- |
| Xvfb ready | 0.05 (0.05 to 0.12, n=10) | 0.05 (0.05 to 0.05, n=2) | 0.05 (0.05 to 0.05, n=2) |
| xfwm4 registered | 0.12 (0.12 to 0.33, n=10) | 0.12 (0.12 to 0.12, n=2) | 0.12 (0.12 to 0.12, n=2) |
| snapshot of the prefix before the launch | 0.54 (0.47 to 0.65, n=10) | 0.47 (0.47 to 0.48, n=2) | 0.46 (0.46 to 0.47, n=2) |
| game window after launch | 0.64 (0.53 to 0.87, n=10) | 0.58 (0.53 to 0.64, n=2) | 0.58 (0.53 to 0.64, n=2) |
| title screen reached and stable, after launch | 6.78 (6.50 to 7.54, n=10) | 6.56 (6.50 to 6.62, n=2) | 6.55 (6.49 to 6.62, n=2) |
| terminate (`wineserver -k` and the bounded wait) | 0.50 (0.50 to 0.75, n=10) | 0.50 (0.50 to 0.50, n=2) | 0.50 (0.50 to 0.50, n=2) |
| game side gone after terminate | 0.00 (0.00 to 0.00, n=10) | 0.00 (0.00 to 0.00, n=2) | 0.00 (0.00 to 0.00, n=2) |
| display side gone after Xvfb and xfwm4 stopped | 0.00 (0.00 to 0.00, n=10) | 0.00 (0.00 to 0.00, n=2) | 0.00 (0.00 to 0.00, n=2) |
| stopping the display | 0.04 (0.02 to 0.23, n=10) | 0.02 (0.02 to 0.02, n=2) | 0.02 (0.02 to 0.02, n=2) |
| snapshot, diff and reset | 1.21 (1.06 to 3.26, n=10) | 1.04 (1.04 to 1.05, n=2) | 1.10 (1.07 to 1.13, n=2) |
| the whole session, first seal to end of reset | 10.67 (9.91 to 13.85, n=10) | 9.90 (9.79 to 10.02, n=2) | 10.00 (9.95 to 10.06, n=2) |

## Aborted repeats

- E004-r0089 (arm `kill-mid-cycle`): `aborted: game-died: the game process exited before the screenshot before.png (status 0)`; prefix after reset equals prefix before launch: yes; session 8.9 s
- E004-r0092 (arm `sigkill-mid-cycle`): `aborted: game-died: the game process exited before the options screen appeared (status -9)`; prefix after reset equals prefix before launch: yes; session 9.44 s
