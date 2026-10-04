# Exploration, round 1 (2026-10-04, before E003's first run)

T11's first round explored DOSBox-X by hand, with the probe scripts here, before any driver or run
record existed. These are its raw outputs, copied from the machine-local exploration folder on
2026-10-04 so that they are tracked (rule 20, L207). They are exploration, not run records: no
finding cites them as a measurement of the cycle. F005 cites them only where it says so.

What was copied, and what was not:
- Every log, table, configuration and probe script, with their names kept (`*.sh`, `*.log`,
  `*.txt`, `*.conf`, `userconf.list`), under the same relative paths.
- Screenshots and raw captures (`*.png`, `*.rgb`, `out/p3/cap/*.png`) are not committed: their
  size and sha256 are in `captures.sha256.tsv`. They stay on the user's machine.
- `game/`, the scratch copy of the original game the probes ran from, is not copied (rule 18). Its
  files are the set `iw-dos-3.1-30121376` plus what the game wrote (`ISLEWAR.SCR`, `ISLEWAR.DFT`).

Paths were replaced by placeholders, because a tracked file may not name a machine-local location
(T11 Done-when 6). Nothing else was changed:

| Placeholder | Stands for |
| --- | --- |
| `<EXPLORE>` | the machine-local exploration folder (outside every checkout) |
| `<SCRATCHPAD>` | the exploring session's scratchpad folder |
| `<OTHER-PROJECT>` | another project's working folder on the same machine (two DOSBox-X savestates of that project, found by `find /` in `out/p3/files2.txt`; not this project's) |
| `<TMPHOME>` | `/tmp/` followed by `home`: the private home folder on the probe's own tmpfs |

How the probes ran: `rp.sh TAG VAR=value ...` (or `probe1.sh` directly) inside
`unshare -rmpfn --mount-proc --kill-child`, a private Xvfb `:77` on a private `/tmp`, DOSBox-X
2024.03.01 mounting `<EXPLORE>/game` as `C:`. The tags: `p1`-`p4` (first launches, screenshots
every 2 s, `p3` DOSBox-X's own capture, `p4` a `config -wc` attempt), `q1` (640x350 screen,
hover and click), `m_never`/`m_always` (mouse emulation), `t1` (keys and SIGTERM to stop).
