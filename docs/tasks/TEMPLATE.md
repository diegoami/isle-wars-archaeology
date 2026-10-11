# T<nn> <Title>

- **Kind**: feature | correction (of T<nn>, bug #<n>) | slice | infrastructure | model-driven
  (runs the original under a gated carve-out, process.md §10; its lettered preconditions are
  Done-when lines, its table and gate named in Scope; here CLAUDE.md rule 18's carve-out:
  T35, T36, T37 merged, per-claim wording per constraint G)
- **Issue**: #<n> · **Branch**: `task/T<nn>-<slug>` · **Merge after**: T<nn>, …
- **Implementer**: the user's choice, asked before the run (CLAUDE.md rule 6, 2026-10-11): who (the main session, a Claude agent, OpenCode) and which model, with `/recommend`'s suggestion and its reasons. Recorded here and on the issue. *Superseded: the default chain, choose.mjs and the Claude fallback.*
- **Reviewer**: the user's choice at each review: an external model, never the implementer's family (CLAUDE.md rule 6). *Superseded: Luna, then Opus.*
- **Evidence**: the reports, fixtures or investigations this task rests on, with links.
- **Owns**: directories or files, e.g. `src/Calendar/**`, `tests/Calendar/**`. A task that measures
  owns a tracked path for its outputs, e.g. `runs/E<nnn>/**` or `spike/measurements/**`: they are
  pushed after each batch and every 30 minutes, never deleted or overwritten; originals stay out,
  their hashes recorded (L40).
- **Scope**: what to build, in a few sentences. What is out of scope, if it is easy to confuse. A task
  likely to outlast one implementer run (about an hour), or whose Done-when is all or nothing (an exact
  match, a whole model), is split into milestone tasks first, each merging on its own with a Done-when
  that measures a number (L58).
- **Done when**:
  1. One check a command can run, with the expected result. Before dispatch, each line fails on
     `main` and passes on a mock fix (L45).
  2. …
  3. The build and the test suite are green.
- **Hazards**: the mistake an implementer is most likely to make here, and how to avoid it.
