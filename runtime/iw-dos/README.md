# runtime/iw-dos/

The DOS *Isle Wars* runtime under DOSBox-X: launch, input, observation, savestates, memory reads. Code only. The game and its DOSBox mount stay on the user's machine and are never committed (CLAUDE.md rule 18).

- `driver/` (T15, W5b, E006): the reusable driver a later experiment imports (`from driver import session`, with `runtime/iw-dos` on `sys.path`). `session.py` is one session: the seal, this run's own Xvfb, DOSBox-X, named screens by pixels, steps in T14's step language, observations, terminate and reset, every failure a named error (`errors.py`); one guard checks DOSBox-X and the display before and after every public method and step, every command goes through `procs.must` (non-zero exit raises), every signal through `procs.kill_marked` (markers re-checked through a pidfd). `repeat.py` is E006's repeated cycle, one record per repeat, with `--fault` for the recovery arms.
- `spike/cycle.py`: E003's cycle (W3b spike, F005). The driver reuses its stages and step verbs; those verbs send their commands through `Cycle.sh` and wait through `Cycle.wait_until`, which the driver replaces with its checked versions (the spike's own are its unchecked `run` and `poll`, as before). `--experiment E005 --steps <script>` runs E005's arms (T14, F007) inside the same seal.
- `spike/dosconf.py`: the DOSBox-X configuration each run generates, and the check that refuses any other mount.
- `spike/navsteps.py`: the step scripts of the E005 inventory runs (T14): what a run may do after the known screen, parsed and refused before anything is launched (`cycle.py --steps`).
- `spike/board.py`: reading the board from a screenshot (owner of each country, which countries touch), for `choose-attack`.
