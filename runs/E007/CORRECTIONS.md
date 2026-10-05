# Corrections to the E007 run records

Run records are raw and are not changed. The one change made here is recorded so that nobody has to trust it.

**E007-r0001 to E007-r0005 (2026-10-05).** The first batch was started by a runner that gave the cycle the
step script by an absolute path of the machine it ran on, and the cycle records its arguments
(`actions.args`). The value of `--steps` in each of the five records was therefore
`<absolute path of the worktree>/experiments/E007-iw-dos-save-format/scripts/../steps/<arm>.steps`, a
machine-local path that no record may hold (T16 Done-when 6). Before any record was committed, that one string in
each of the five files was replaced by `experiments/E007-iw-dos-save-format/steps/<arm>.steps`, the path the cycle
receives from `scripts/run-arms.sh` since (relative to the repository root). Nothing else in a record, a manifest
or a bundle differs from what the cycle wrote: the steps script's own sha256 is in the record's observations and
is unchanged by the path. The five runs are `sv-easy-1`, `sv-normal-1`, `sv-hard-1`, `sv-hardest-1` and
`sv-easy-3`; every later run was made with the relative path.

**What this means for the five records (review R1, round 1; the owner's decision of 2026-10-05).** E007-r0001 to
E007-r0005 are **cleaned copies, not raw records**: their `actions.args` is not what the cycle wrote. The owner
decided to declare this and not to re-run them; they are kept as they are and are not rewritten or deleted. F009
marks them "(cleaned)" wherever it cites them, and rests no claim on them alone: every field they show is also shown
by a pair of raw records (F009, Method, "The five cleaned records"). The originals' one changed string held a
machine-local path, so it is not kept anywhere in the repository.
