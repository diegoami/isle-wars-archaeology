# Exploration, round 2 (2026-10-04, before E003's first run)

Hand-run probes that settled the open questions of round 1 before `cycle.py` was written. They are
exploration, not run records. F005 cites them only where it says so; its claims rest on the
records in `runs/E003/`.

How they ran: `batch1.sh` and `batch2.sh` (and `probe.sh` by hand for `a1`, `dbg-text`,
`dbg-text2`) call `probe.sh TAG VAR=value ...`. Each probe runs in private user, mount, PID and
network namespaces (`unshare -rmpfn`), binds `IW_DOS_DIR` read-only, mounts a tmpfs on `/tmp`,
copies the game onto it (`/tmp/w/game`, gone when the probe ends), starts Xvfb `:61` 800x600x24
and DOSBox-X 2024.03.01 with the configuration in each `out/<tag>/dosbox.conf`, then sources a
steps script (`s_full.sh`, `s_det.sh`, `s_text.sh`). `pred.py` is the pixel test for the option
box and the Select level dialog. `savestate_members.py` produced `savestate-members.txt`.

What is here, and what is not:
- `out/<tag>/`: `shots.txt` (each capture's sha256 prefix and its seconds since launch, and how
  DOSBox-X ended), `dosbox.log`, `dosbox.conf`, `files.txt`, `wid.txt`, `save.txt`, and
  `game.sha256` (the hashes of the game copy's files when the probe ended).
- Not committed: the captures (`*.rgb`, `*.png`, DOSBox-X's `cap/*.png`) and the savestates
  (`save/state.sav`, which hold the game's memory). Their sizes and sha256 are in
  `out/captures.sha256.tsv`. They stay machine-local.
- After the batches ran, the private home folder in `probe.sh` was renamed from `/tmp/w/` plus
  `home` to `/tmp/w/h`, because a tracked file may not contain that path fragment (T11 Done-when 6).
  Nothing else in the scripts changed. The `files.txt` listings show the old name.

What the probes showed (raw values in `out/<tag>/shots.txt`):

| Tags | Question | Result |
| --- | --- | --- |
| `det-host-1..3`, `det-fixed-1..3` | Is the option box the same in three starts, with the host's clock and with DATE/TIME fixed in [autoexec]? | Yes in all six: capture prefix `39959f3fa0bb5e0f` |
| `speed-fixed-10000`, `speed-fixed-30000`, `speed-max` | Do more cycles shorten the wait? | The box at 13.0, 12.1 and 12.4 s, against about 15.5 s at fixed 3000; the same screen |
| `a1` | Does a savestate restore the screen? | F12+S at the box, a click to the dialog, F12+L: the restored capture equals the box's |
| `det-*`, `a1` | Is the savestate's memory the same across identical starts? | No: 2312 to 3106 bytes of 17055864 differ (`savestate-members.txt`) |
| `dbg-breakstart`, `dbg-debugbox`, `dbg-text2` | Is there a debugger? | No: `-break-start` changed nothing; the shell answers `Bad command or filename - "DEBUGBOX"` |
| `secure`, `dbg-text` | Does `config -securemode` in [autoexec] work here? | DOSBox-X never showed its window, and the game never started; not pursued |
| `term-sigterm`, `term-sigkill`, `a1`, `cap-*` | How does DOSBox-X stop? | SIGTERM: exits in 0.10 s, status 0 (with `quit warning=false`); SIGKILL: 0.10 s, status 137; closing the X client (`xdotool windowkill`): 0.11 s, status 1 |
| `cap-1`, `cap-2` | Are DOSBox-X's own screenshots stable bytes? | Yes at the dialog: the same file (`f41537a79e5b3807`) and the same pixels in both |
