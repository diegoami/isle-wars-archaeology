T53 review (Sol)

You review PR #200 at daf8c5769475622fcd650fa579ad4ee5e81f9e8a. You did not write it; a Claude (Opus) subagent did, and the main session
merged main into it (one conflict in core-rules.md's Options table, resolved by keeping both sides). It is
a design task: malpaco's computer opponent, a decision for each of the 9 spec claims (C-AI-01 to 09),
12 choices for the owner (A1–A12), T53's section appended to design/variants.md, and check_design.py
extended to a third file. The task file follows in full. T50 (core-rules.md) and T51 (variety.md,
whose card, centre and event rules are deliberately swingy by the owner's choice) are the rules it
plays by. Your working directory is the review worktree: run commands there with no `workdir`
argument, and use relative paths.

0. Prove the tree: HEAD is daf8c57…, and the diff against origin/main is the PR's.
1. Re-run every Done-when line yourself, and account for each (L32). DW4 is a reading line: write
   `DW4: ran a read of the choices and variants sections → <result>`.
2. Every changed file is one the task owns (L44). In core-rules.md, only the references naming T51 for
   the computer's strength or policy changed: list any other change.
3. The extended check_design.py: mutation-prove each check for the third file, restoring by writing back
   the saved contents in a `finally`. Also try to hide a computer-file row: the fence, comment and raw
   HTML bans apply.
4. Design quality, the task's purpose:
   - fairness and honesty hold as stated: the same rules and action interface as a human, only
     human-visible information, its own random stream per seat, and replay that stays exact;
   - each of Pro's computer-only behaviours is dropped or replaced with its row;
   - the difficulty levels change only how it decides, never its rules or information, and a player
     can feel the difference;
   - the model numbers are right: re-run the pasted model and check the stall thresholds, the Squall
     risk, the Shield chance and the sample sizes;
   - the strength targets and their sample sizes can be measured;
   - no feel-changing call is settled without being in Choices for the owner;
   - every proposed core-rules amendment is a choice;
   - it states properties, not algorithms with promised bounds;
   - no status line appears (rule 3);
   - the rules are complete enough to build: name any gap or constructed counterexample, such as the
     leader check against a human, a computer stalling against the round limit, a Raid set with no legal
     target, the Squall in a computer hand, or two computer seats appearing to cooperate.
5. Rule 18: no original names or text; Pro's computer cited by counts only.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: a spec claim with no row, or a wrong decision word, that
   check_design.py accepts for the third file; a computer that cheats (extra information, rules only it
   follows, or randomness that alters the shared dice); a feel-changing decision made without being
   listed for the owner; original game text (rule 18). A bypass you proved is blocking, even when it
   looks like an edge case. (L47)
3. Behaviour nobody asked for inside a file the task owns, or an edit outside Owns. (L44)
4. A test that passes with its check deleted; a wrong number that an argument rests on; a status written
   into a document.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the task protects; otherwise it is a follow-up. (L53)

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking
finding: finish reading the whole diff and the PR body, check every Done-when line and
every item under "Blocking means", and report all blocking findings together.

- Before you write the verdict, make one last pass over the full diff for anything you have
  not yet rated, and say "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an
  earlier one was already blocking is a review defect: if two problems share a cause, list
  both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review
  checks those fixes and new code only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or
  sections you did not cover. Do not approve in that case.

Your final message is the review: the header; the verdict (approve | approve after named fixes |
rework | user decision); per Done-when line `DW<k>: ran <command> → <result>` or
`DW<k>: not run — <reason>`; the findings R1..Rn (file:line, blocking or not); the verdict again
last. Never post it: the script posts it.

---
The task file, in full:

# T53 malpaco's design, the computer opponent: how it plays, and its difficulty levels

- **Kind**: feature (design; no code in malpaco, no research run)
- **Issue**: #196 · **Branch**: `task/T53-design-computer` · **Merge after**: T51 (the canonical
  card, centre and event rules the computer plays by, and check_design.py's fail-closed form)
- **Implementer**: the user's choice, asked before the run (CLAUDE.md rule 6), recorded here and on
  the issue.
- **Reviewer**: the user's choice at review: an external model, never the implementer's family.
- **Evidence**: the promoted spec only, at the commit the branch starts from: `spec/computer-opponent.md`
  (9 claims, C-AI-01 to 09). Also these:
  - malpaco's rules in `design/core-rules.md` (T50) and `design/variety.md` (T51), with the owner's
    decisions, and `design/variants.md`;
  - `runs/coverage.md` for what play has shown of the computer: Q-AI-01 to 07. Per-sitting counts of
    the computer's attacks, stops, moves and trade-ins are in `runs/E018/CORRECTIONS.md` and the E021
    records; use them as counts only, never quoted;
  - the direction in CLAUDE.md, "The goal is a fun game, not a copy".
- **Owns**:
  - `design/computer.md`;
  - a section for T53's choices appended to `design/variants.md`;
  - a line for the new file in `design/README.md`;
  - `tools/check_design.py` and `tools/tests/test_check_design.py`, extended to a third design file;
  - in `design/core-rules.md`, only the references that name T51 for the computer's strength or policy,
    which now point to T53 (a mechanical fix, rule 12). Every other change to core-rules.md or
    variety.md is a proposed amendment, listed as a choice.

  Not `spec/**`, `findings/**`, `runs/**` or `questions/**`.
- **Why**: in the standard game, three of the four seats are the computer, so its play is most of what a
  player meets. Pro's computer is shaped by its own rules:
  - it attacks in drawn rounds, from gates the human doesn't have;
  - it moves from a hard-coded 23-country table;
  - it trades cards by a fixed priority;
  - its difficulty level changes nothing in its play, only the human's starting share (C-AI-08);
  - how well it plays is unestablished (C-AI-09).

  T50 gave every seat one rule set, and T51 decided the cards and events. malpaco needs a computer that
  plays by those same rules, is fun to play against, and gets harder in ways a player can feel.
- **Scope**:
  - **`design/computer.md`**: what the computer does on its turn, in T50's turn order (cards,
    placement, attacks, the move) and under T51's canonical cards and events. It is written so a
    TypeScript implementer can build it without reading the spec, in our own words (rule 18). This is
    design: state the computer's goals, the information it may use, its decision rules or their
    required properties, and its difficulty levels. No search algorithm with a promised bound (T50's
    review lesson).
  - **The decision table**: one row per in-scope claim (C-AI-01 to 09), in T50's form, with exactly
    one of `keep`, `change`, `replace`, `drop` or `open`, under the same rules as T50 and T51.
  - **Fairness and honesty, as requirements**:
    - the computer plays by exactly the rules a human plays by (T50's one attack rule, T51's cards and
      events);
    - it uses only what a human seat could see: no peeking at hands, the deck order or the seed's next
      draws;
    - its own random choices come from a separate seeded stream, so a game replays exactly (T50's saved
      game), and an AI change never alters the dice;
    - each of Pro's computer-only behaviours is listed with its row, as dropped or replaced: drawn attack
      rounds, the gate floors, the fixed move table, the fixed trade priority, the extra rounds after the
      human is out, and the capture split.
  - **Difficulty levels**: what changes between levels, and how a player feels it:
    - levels may vary the computer's foresight, aggression, card timing, mistakes on purpose, or
      cooperation against a leader, but never its rules or its information;
    - T50's options table names a computer-strength setting: give its levels and default;
    - T50 decision 6's human share setting stays separate from strength.
  - **Making it fun**: argue, with numbers where possible (a number from a model says so):
    - the computer doesn't stall: no endless turtling that runs into the round limit;
    - it doesn't gang up on the human unfairly, but does check a runaway leader of any seat;
    - it uses T51's swingy cards (doubling, the raid, the self-punishing card) in ways a player can
      read;
    - its turns are quick to watch (a bound on actions per turn, stated as a requirement for T52's
      presentation).
  - **Measuring strength**: C-AI-09 says Pro's quality is unknown. State how malpaco will measure its
    own computer in malpaco's tests, as requirements for the implementation, not results:
    - win rates of each level against a simple scripted baseline and against each other, over many
      seeds;
    - the target each level should hit;
    - game length.
  - **The owner's choices**: `## Choices for the owner`, with every `open` row and every feel-changing
    call, each with 2–3 options, a recommendation and its reason.
  - **Variants**: append T53's choices to `design/variants.md` in its existing form: the canonical
    option, the named alternatives, and their interactions. The canonical options are filled in once the
    owner decides.
  - **check_design.py** checks `design/computer.md` against `spec/computer-opponent.md`, the same way
    as the other two files, with the fail-closed ban on fences and comments. The tests visit the third
    file, and every check is mutation-proven (rule 9).
  - Out of scope: the computer's turn presentation and its speed settings (T52); edits to the malpaco
    repository; new runs or recordings.
- **Done when**:
  1. `python3 tools/check_design.py` prints one ok line for each of `design/core-rules.md` (59),
     `design/variety.md` (23) and `design/computer.md` (`9 claims, 9 rows`), and exits 0. It exits 1 on
     `main` today, because there is no computer design.
  2. `python3 -m unittest tools.tests.test_check_design` passes, with tests that visit the third file
     for each failure, each with a fixture that trips that failure alone.
  3. `grep -c '^| C-AI-' design/computer.md` prints 9.
  4. `## Choices for the owner` exists in `design/computer.md`, and every entry has options, a
     recommendation and a reason. `design/variants.md` has a section for T53's choices. The reviewer
     reads both.
  5. `python3 tools/check_links.py` and `python3 tools/check_no_originals.py` pass, and the full test
     suite is green.
- **Hazards**:
  - **Copying Pro's computer.** Its tables, its 23-country list and its drawn rounds are evidence of
    what one computer did, not a target. Design from what makes it a good opponent under malpaco's
    rules.
  - **A cheating computer.** Hidden bonuses, extra information, or rules only it follows make a level
    "harder" in a way players resent. The requirements forbid them; levels change only how it decides.
  - **Algorithms with promises.** State the properties a level must have and how malpaco's tests
    measure them, not a search method with a bound.
  - **Deciding for the owner.** Every feel-changing call is listed as a choice with a recommendation.
