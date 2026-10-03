# runtime/iwp/

The *Isle Wars Pro* (Windows) runtime driver: launch, input, observation, termination, reset, and state restore, on whatever path W3a shows works (native Windows, or Wine + Xvfb). Code only. The game, its install and any Wine prefix stay on the user's machine and are never committed (CLAUDE.md rule 18).

- `spike/cycle.py`: the W3a spike (E001, [F002](../../findings/F002-iwp-runtime-wine-xvfb.md)): one launch, known screen, input, observation, termination and reset on the Wine + Xvfb + xfwm4 path, with one `run/1` record per run. Each run binds the install read-only in its own namespace, checks the prefix before anything starts and again immediately before the launch, records `completed` only for a full cycle, and writes through `setup/iwp/safeio.py`. It is a spike, not the driver (W5a).
