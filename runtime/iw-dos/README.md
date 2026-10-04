# runtime/iw-dos/

The DOS *Isle Wars* runtime under DOSBox-X: launch, input, observation, savestates, memory reads. Code only. The game and its DOSBox mount stay on the user's machine and are never committed (CLAUDE.md rule 18).

- `spike/cycle.py`: E003's cycle (W3b spike, F005), not yet the reusable driver (W5b).
- `spike/dosconf.py`: the DOSBox-X configuration each run generates, and the check that refuses any other mount.
