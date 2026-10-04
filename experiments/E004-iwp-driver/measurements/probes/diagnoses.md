# Diagnoses made while the driver was built (2026-10-04)

Kept as they were made (rule 20). They are exploration, not run records: each used the spike
(`runtime/iwp/spike/cycle.py --explore`, no record) with a temporary print added to its terminate stage, which
was reverted and is not in the tree. Machine paths are left out.

## 1. What E002's 30 s wait after `wineserver -k` was waiting for

Command: the spike with `--experiment E002 --explore --script experiments/E002-iwp-state-inventory/scripts/opt-control.steps --terminate kill --may-write-saved-files`,
the shell's `DBUS_SESSION_BUS_ADDRESS` unset. The temporary print listed, three times at 2 s intervals right
after `wineserver -k` and the game's exit (status 0), every process of the run that the spike's
`wine_processes()` counted (it excluded only the comm names `Xvfb` and `xfwm4`):

```text
pid comm              cmdline start                                   state
25  dbus-launch       dbus-launch --autolaunch ... --binary-syntax    S
26  dbus-daemon       /usr/bin/dbus-daemon --syslog-only --fork ...   S
28  at-spi-bus-laun   /usr/libexec/at-spi-bus-launcher               S
34  dbus-daemon       /usr/bin/dbus-daemon --config-file=...at-spi2   S
37  at-spi2-registr   /usr/libexec/at-spi2-registryd                  S
46  xfconfd           .../xfce4/xfconf/xfconfd                        S
```

The same six, with the same pids, in all three listings; none is a Wine process. They carry the run's marker
because xfwm4, which has no session bus to reach, makes `dbus-launch --autolaunch` start them, and they
inherit xfwm4's environment. They end when the display does, which the spike's terminate stage reached only
after its 30 s poll had timed out. So the 30 s was the poll's timeout, not Wine: the game and every Wine
process were already gone.

## 2. The stale bus (E002 r0002 and r0003)

With the shell's `DBUS_SESSION_BUS_ADDRESS` set to a bus whose socket does not exist, the spike's xfwm4 did not
register as the window manager within its 20 s (`ABORT xfwm4 did not register`). With it unset, xfwm4
registered after 0.24 to 0.33 s.

## 3. A `TMPDIR` that Wine does not survive

The first attempts of this task ran with `TMPDIR` pointing at a short directory of the host's `/tmp`, which the
run's private `/tmp` does not contain: `wine.log` read `wine: unable to create wineserver tmpdir` and the
game never started. With `TMPDIR=/tmp` itself `wine.log` read `free(): invalid pointer` and the game process
ended with status -6. With `TMPDIR` unset the game started every time, in the spike (two runs) and in the
driver. This is observed, not explained. The driver passes no `TMPDIR` to the game, and the unit test
`EnvironmentTest` checks that.

## 4. A prefix off its baseline

Wine commands run by hand against the prefix, outside the cycle, re-created the `dosdevices/com*` links and
changed `system.reg` and `user.reg`. The next spike run then reset the prefix to its baseline, which was not
the state it had started from, and recorded `aborted: reset did not restore the prefix`
(`differing: system.reg, user.reg`). `setup/iwp/iwp-runtime.sh` removes the links but does not refresh an
existing baseline. The driver now compares the prefix's registry files with the baseline before anything
starts (`SealError`), so this is found at the start and not at the end of a repeat.
