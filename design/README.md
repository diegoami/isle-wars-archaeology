# design/

malpaco's rules, derived from this repository's reviewed specification (`spec/`) and from the
owner's direction that malpaco be fun, roughly balanced and varied, not a copy (CLAUDE.md, "The
goal is a fun game, not a copy", 2026-10-11).

- **What it is.** Rules a TypeScript implementer can build without reading `spec/`. Each file says,
  claim by claim, whether malpaco keeps, changes, replaces or drops the predecessor's rule, or leaves
  it to the owner (`open`), and why.
- **What it is not.** Evidence. Nothing here is a finding or a measurement: the evidence stays in
  `spec/`, `findings/` and `runs/`, and it never passes to malpaco. Numbers in these files are either
  malpaco's own constants or models (stated as models); none is a measurement of the predecessor.
- **Rule 18.** Only behaviour and design pass to malpaco. No code, asset, text, label, screen text,
  name or title of the original game appears here, and no quote from the findings. malpaco uses its
  own names, or none.
- **Who decides.** Every `open` row, and every change that alters the feel of play, is listed in its
  file's `## Choices for the owner` with options and a recommendation. The owner decides; the section
  then becomes `## The owner's decisions (<date>)`, keeping the options and reasons and adding each
  decision. `core-rules.md`'s choices were all decided on 2026-10-12. An implementer builds each
  decided value behind a named constant.

## Files

| File | What | Task |
| --- | --- | --- |
| [core-rules.md](core-rules.md) | setup, seats, the board generator and island bonuses, the deal, the turn, reinforcement, movement, combat, ownership, victory and leaving a game | T50 (#192) |
| `extras.md` (planned) | cards (and tuning the island bonus constants), production centres, hazards, the computer opponent | T51 (#193) |
| `ui.md` (planned) | the UI, against the predecessor's and malpaco's recorded weaknesses | T52 (#194) |

`python3 tools/check_design.py` checks that `core-rules.md`'s decision table has exactly one row per
in-scope spec claim, with a valid decision and a reason, and that every `open` row is in the owner's
list.
