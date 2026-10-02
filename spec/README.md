# Specification

The current best statement of how *Isle Wars* (DOS) and *Isle Wars Pro* behave. **Only the main
session writes here**, when it promotes a reviewed finding (game-archaeologist ADR-008). A research
task proposes, and never edits this directory.

- One file per knowledge-map area (`setup.md`, `combat.md`, …), created at its first promotion from
  game-archaeologist `formats/templates/spec-area.md`. It holds a short summary of `supported` and
  `corroborated` claims, then the claim table `ID | Claim | Status | Scope | Basis | Findings`.
- [representation.md](representation.md): what raw values mean (file layouts, memory, screen
  elements), as `R<nnn>` claims that decoded values cite.
- Claim ids are `C-<AREA>-<nn>` (e.g. `C-SET-01`). Statuses, basis and scope follow
  game-archaeologist `vocabulary/` at the commit [archaeology.json](../archaeology.json) pins.
- Every claim is scoped to an artifact set, DOS or Pro, and to the unregistered releases unless shown
  otherwise.
