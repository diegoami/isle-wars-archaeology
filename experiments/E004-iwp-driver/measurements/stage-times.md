# E004 stage times

Seconds, median (range, n) over the completed records of each arm group; read from the observations of `runs/E004/*.json`. The `control` arm is the 10-repeat command; `fault arms` are the completed repeats of `kill-mid-cycle` and `sigkill-mid-cycle`.

| stage | control | fault arms (completed repeats) |
| --- | --- | --- |
| Xvfb ready | 0.11 (0.10 to 0.11, n=10) | 0.11 (0.11 to 0.11, n=4) |
| xfwm4 registered | 0.23 (0.22 to 0.24, n=10) | 0.23 (0.23 to 0.23, n=4) |
| snapshot of the prefix before the launch | 0.67 (0.55 to 0.89, n=10) | 0.74 (0.67 to 0.79, n=4) |
| game window after launch | 1.00 (0.76 to 1.23, n=10) | 1.06 (0.65 to 1.23, n=4) |
| title screen reached and stable, after launch | 7.62 (7.17 to 8.10, n=10) | 7.72 (6.99 to 7.79, n=4) |
| terminate (`wineserver -k` and the bounded wait) | 0.50 (0.50 to 0.51, n=10) | 0.50 (0.50 to 0.50, n=4) |
| game side gone after terminate | 0.00 (0.00 to 0.00, n=10) | 0.00 (0.00 to 0.00, n=4) |
| display side gone after Xvfb and xfwm4 stopped | 3.02 (3.00 to 3.04, n=10) | 3.00 (3.00 to 3.02, n=4) |
| stopping the display | 3.03 (3.02 to 3.05, n=10) | 3.01 (3.01 to 3.04, n=4) |
| snapshot, diff and reset | 1.52 (1.20 to 1.80, n=10) | 1.67 (1.44 to 1.91, n=4) |
| the whole session, first seal to end of reset | 15.06 (14.25 to 16.24, n=10) | 15.43 (15.03 to 15.54, n=4) |

## Aborted repeats

- E004-r0012 (arm `kill-mid-cycle`): `aborted: game-died: the game process exited before the screenshot before.png (status 0)`; prefix after reset equals prefix before launch: yes; session 13.95 s
- E004-r0015 (arm `sigkill-mid-cycle`): `aborted: game-died: the game process exited before the options screen appeared (status -9)`; prefix after reset equals prefix before launch: yes; session 15.23 s

