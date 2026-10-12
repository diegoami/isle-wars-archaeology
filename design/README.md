# design/

malpaco's rules, derived from this repository's reviewed specification (`spec/`) and from the
owner's direction that malpaco be fun, roughly balanced and varied, not a copy (CLAUDE.md, "The
goal is a fun game, not a copy", 2026-10-11).

- **What it is.** Rules a TypeScript implementer can build without reading `spec/`. Each file says,
  claim by claim, whether malpaco keeps, changes, replaces or drops the predecessor's rule, or leaves
  it to the owner (`open`), and why.
- **What it is not.** Evidence. Nothing here is a finding or a measurement: the evidence stays in
  `spec/`, `findings/` and `runs/`, and it never passes to malpaco. Numbers in these files are either
  malpaco's own constants or models (stated as models); none is a measurement of the predecessor,
  except a count from the owner's recorded play cited as context, with its source.
- **Rule 18.** Only behaviour and design pass to malpaco. No code, asset, text, label, screen text,
  name or title of the original game appears here, and no quote from the findings. malpaco uses its
  own names, or none.
- **Who decides.** Every `open` row, and every change that alters the feel of play, is listed in its
  file's `## Choices for the owner` with options and a recommendation. The owner decides; the section
  then becomes `## The owner's decisions (<date>)`, keeping the options and reasons and adding each
  decision. The choices of `core-rules.md` and `variety.md` were all decided on 2026-10-12. The decided
  options are the **canonical** variant; the other options are kept as named variants in
  `variants.md`. An implementer builds each decided value behind a named constant.

## Files

| File | What | Task |
| --- | --- | --- |
| [core-rules.md](core-rules.md) | setup, seats, the board generator and island bonuses, the deal, the turn, reinforcement, movement, combat, ownership, victory and leaving a game | T50 (#192) |
| [variety.md](variety.md) | cards, island bonuses on a generated board, production centres and events | T51 (#193) |
| [variants.md](variants.md) | every T50, T51, T53 and T52 choice: the canonical option and each alternative as a named variant, with its interactions; no spec rows | T51 (#193), T53 (#196), T52 (#194) |
| [computer.md](computer.md) | the computer opponent: what it may know, how it plays each phase of the turn under the T50 and T51 rules, its difficulty levels, and how malpaco measures its strength | T53 (#196) |
| [ui.md](ui.md) | the UI: screens and flow, the board, the turn, combat, cards, events, computer turns, standings and log, sound, input, no trace of switched-off features, and what tests can check; argued against the predecessor's UI and the 19 weaknesses malpaco's proof of concept recorded | T52 (#194) |

`python3 tools/check_design.py` checks that each design file's decision table has exactly one row per
claim of its own in-scope spec files, with a valid decision and a reason, and that every `open` row is
in the owner's list; it prints one line per design file. `ui.md` also has one row per UI question of
`questions/malpaco.md` (`Q-UI-01` to `Q-UI-22`), checked the same way. A row may be indented up to
three spaces, as Markdown allows; a line whose first cell looks like an id but is not a well-formed row
(indented deeper, without a leading pipe, or with a malformed id) fails the check. Every design file, `variants.md` included,
fails the check if it holds a code fence or an HTML comment, so nothing in it can be hidden from a
reader; code goes in indented blocks.
