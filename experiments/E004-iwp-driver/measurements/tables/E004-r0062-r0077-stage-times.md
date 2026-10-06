# E004 stage times, E004-r0062-r0077

Seconds, median (range, n) over the completed records of each arm of E004-r0062-r0077, read from their observations.

| stage | `control` | `kill-mid-cycle` | `sigkill-mid-cycle` |
| --- | --- | --- | --- |
| Xvfb ready | 0.05 (0.05 to 0.05, n=10) | 0.05 (0.05 to 0.05, n=2) | 0.05 (0.05 to 0.05, n=2) |
| xfwm4 registered | 0.12 (0.12 to 0.22, n=10) | 0.12 (0.12 to 0.12, n=2) | 0.12 (0.12 to 0.12, n=2) |
| snapshot of the prefix before the launch | 0.46 (0.45 to 2.84, n=10) | 0.50 (0.47 to 0.53, n=2) | 0.45 (0.45 to 0.45, n=2) |
| game window after launch | 0.53 (0.53 to 0.64, n=10) | 0.53 (0.53 to 0.53, n=2) | 0.53 (0.53 to 0.53, n=2) |
| title screen reached and stable, after launch | 6.51 (6.50 to 6.81, n=10) | 6.50 (6.49 to 6.50, n=2) | 6.51 (6.50 to 6.52, n=2) |
| terminate (`wineserver -k` and the bounded wait) | 0.50 (0.50 to 0.50, n=10) | 0.50 (0.50 to 0.50, n=2) | 0.50 (0.50 to 0.50, n=2) |
| game side gone after terminate | 0.00 (0.00 to 0.00, n=10) | 0.00 (0.00 to 0.00, n=2) | 0.00 (0.00 to 0.00, n=2) |
| display side gone after Xvfb and xfwm4 stopped | 0.00 (0.00 to 0.00, n=10) | 0.00 (0.00 to 0.00, n=2) | 0.00 (0.00 to 0.00, n=2) |
| stopping the display | 0.02 (0.02 to 0.04, n=10) | 0.02 (0.02 to 0.02, n=2) | 0.02 (0.02 to 0.02, n=2) |
| snapshot, diff and reset | 1.04 (1.00 to 1.17, n=10) | 0.99 (0.98 to 1.00, n=2) | 1.01 (1.01 to 1.01, n=2) |
| the whole session, first seal to end of reset | 9.88 (9.78 to 12.64, n=10) | 9.79 (9.74 to 9.85, n=2) | 9.82 (9.80 to 9.83, n=2) |

## Aborted repeats

- E004-r0073 (arm `kill-mid-cycle`): `aborted: game-died: the game process exited before the screenshot before.png (status 0)`; prefix after reset equals prefix before launch: yes; session 8.92 s
- E004-r0076 (arm `sigkill-mid-cycle`): `aborted: game-died: the game process exited before the options screen appeared (status -9)`; prefix after reset equals prefix before launch: yes; session 9.27 s
