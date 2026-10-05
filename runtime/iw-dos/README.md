# runtime/iw-dos/

The DOS *Isle Wars* runtime under DOSBox-X: launch, input, observation, savestates, memory reads. Code only. The game and its DOSBox mount stay on the user's machine and are never committed (CLAUDE.md rule 18).

- `spike/cycle.py`: E003's cycle (W3b spike, F005), not yet the reusable driver (W5b). `--experiment E005 --steps <script>` runs E005's arms (T14, F007) inside the same seal.
- `spike/dosconf.py`: the DOSBox-X configuration each run generates, and the check that refuses any other mount.
- `spike/navsteps.py`: the step scripts of the E005 inventory runs (T14): what a run may do after the known screen, parsed and refused before anything is launched (`cycle.py --steps`).
- `spike/board.py`: reading the board from a screenshot (owner of each country, which countries touch), for `choose-attack`.
