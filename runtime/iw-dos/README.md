# runtime/iw-dos/

The DOS *Isle Wars* runtime under DOSBox-X: launch, input, observation, savestates, memory reads. Code only. The game and its DOSBox mount stay on the user's machine and are never committed (CLAUDE.md rule 18).

- `spike/cycle.py`: E003's cycle (W3b spike, F005), not yet the reusable driver (W5b). `--experiment E005 --steps <script>` runs E005's arms (T14, F007) inside the same seal.
- `spike/dosconf.py`: the DOSBox-X configuration each run generates, and the check that refuses any other mount.
- `spike/navsteps.py`: the step scripts of the E005 inventory runs (T14): what a run may do after the known screen, parsed and refused before anything is launched (`cycle.py --steps`).
- `spike/board.py`: reading the board from a screenshot (owner of each country, which countries touch), for `choose-attack`.
- `save/savefmt.py`: the layout of `ISLEWAR.SAV` (T16, F009): `decode` the bytes the game wrote into a position, `encode` a position back into the same bytes (it refuses a position it cannot carry, and checks that its bytes decode to that position), `roundtrip`. Pure functions.
- `save/writer.py`: the crafted-save writer (an I3 intervention): `place` writes `ISLEWAR.SAV`, and only that name, into a run copy and nowhere else (never `IW_DOS_DIR`), from a position `savefmt` accepts. Command line: `decode`, `roundtrip`, `craft`, `write`. The cycle's `put-save` step and `--crafted` position use it (`spike/cycle.py`, `spike/navsteps.py`).
