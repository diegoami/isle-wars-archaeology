T52 re-review (Sol)

You re-check PR #201 at 382c5a735202e9ee3d01253a60d03876617ef91a, narrowly. Your review at 31a5910 asked for rework on R1–R3. The
Opus implementer fixed them in cda6f09 (R1), 075cb0e (R2) and 382c5a7 (R3). Check
`git diff 31a5910..382c5a7`. Your working directory is the review worktree: run commands there with no
`workdir` argument, and use relative paths.

0. Prove the tree: HEAD is 382c5a7….
1. For each of R1–R3, repeat your reproduction against the new code and text, and say fixed, not fixed,
   or partly:
   - R1: your three lines (` | Q-UI-99 | nope | text | |`, an indented duplicate of Q-UI-22, an
     unindented `Q-UI-23a` row), plus an indented question row in another design file; then try further
     ways to get a rendered table row past the check (a tab, 4 spaces, no leading pipe, a lower-case id,
     a row inside a list or blockquote, a fullwidth or other look-alike pipe or hyphen). Mutation-prove
     the new checks, restoring by writing back the saved contents in a `finally`. The other three files'
     ok lines must not change.
   - R2: your 1000-against-100, N=1 case: a stop is offered after every exchange, including the 13th;
     the pause at the end of the watch budget; and that only an option the player picks (finish now,
     Instant in settings) resolves exchanges unseen. Check UI5, UI6, UW-13, Q-UI-16 and variants agree.
   - R3: repeated autosaves and manual saves of the same game charge nothing; a different game over an
     unfinished one charges exactly one loss per human seat with no result; a resigned seat is never
     counted twice; game identity is fixed at start and kept in the save; play again and replay-the-seed
     get new identities. Check the UI14 amendment text, options (b) and (c), and the UI14 variants agree.
2. Look for any contradiction or new gap the fixes opened, such as the pause interacting with hot-seat
   hand-over or a computer turn, identity and a loaded save of a finished game, or the check rejecting a
   legitimate row in an existing design file.
3. Re-run Done-when 1–3 and 5, and read the choices section, the UW argument and the variants section
   for Done-when 4.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: a spec claim or UI question with no row, an unknown id, or
   a wrong decision word, that check_design.py accepts; a rule or look-and-feel decision made without
   being listed for the owner; a UI that reveals what a seat may not see; original game text or layout
   (rule 18). A bypass you proved is blocking, even when it looks like an edge case. (L47)
3. Behaviour nobody asked for inside a file the task owns, or an edit outside Owns. (L44)
4. A test that passes with its check deleted; a wrong number that an argument rests on; a status written
   into a document.
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the task protects; otherwise it is a follow-up. (L53)

## Report every blocking finding in this one review

This is round 2 of 2: a remaining blocking finding escalates to the owner. Finish the whole re-check
and report every blocking finding together, numbered R1, R2, … (new numbers after your earlier R3: use
R4 onwards for new findings). Say "Final pass done" as the last line before the verdict. If you ran out
of time or context, say what you did not cover, and do not approve.

Your final message is the review: the header; the verdict (approve | approve after named fixes |
rework | user decision); per Done-when line `DW<k>: ran <command> → <result>`; R1–R3 fixed or not, and
any new findings (file:line, blocking or not); the verdict again last. Never post it: the script posts
it.

---
The task file, in full:

# T52 malpaco's design, the UI: screens, the board, feedback and sound, at least as good as Pro's

- **Kind**: feature (design; no code in malpaco, no research run)
- **Issue**: #194 · **Branch**: `task/T52-design-ui` · **Merge after**: T53 (what the UI presents:
  T50's rules, T51's cards and events, and T53's computer turns and their presentation budget)
- **Implementer**: the user's choice: the implementer subagent on Opus (the owner, 2026-10-12).
- **Reviewer**: the user's choice at review: an external model, never the implementer's family.
- **Evidence**:
  - `spec/user-interface.md` (2 claims, C-UI-01 and C-UI-02).
  - What Pro shows: the UI catalogue `findings/F020-pro-ui-observations.md` (proposed, observations
    only; it is read here because the spec holds only two UI claims), `walkthroughs/coordinates.md`
    (the layout of Pro's controls), and the UI observations in `runs/E018/CORRECTIONS.md`. Use all of
    them in our own words only: no screen text, label, image, layout copied or quoted (rule 18).
  - malpaco's 22 UI questions and 19 recorded weaknesses, `Q-UI-01` to `22` and `UW-1` to `19`, in
    `questions/malpaco.md`, under "User interface". They come from malpaco's Godot proof of concept and
    are the bar this design must clear.
  - malpaco's rules in `design/core-rules.md`, `design/variety.md` and `design/computer.md`, with the
    owner's decisions, and `design/variants.md`.
  - The owner's aim (CLAUDE.md and the owner's decision of 2026-10-02): malpaco has a UI at least as
    good as Pro's, and the game is fun, not a copy.
- **Owns**: `design/ui.md`; a section for T52's choices appended to `design/variants.md`; a line in
  `design/README.md`; `tools/check_design.py` and `tools/tests/test_check_design.py`, extended to the
  new file. Not `design/core-rules.md`, `variety.md` or `computer.md`: a change they need is a proposed
  amendment, listed as a choice. Not `spec/**`, `findings/**`, `runs/**` or `questions/**`.
- **Why**: everything a player knows about a game reaches them through the screen, the input and the
  sound. Pro's UI shows the state of a turn on its screens (C-UI-01), but malpaco's own proof of concept
  recorded 19 weaknesses: ownership readable by colour only, the start screen, illegal actions, computer
  turns never presented, no hand UI, no juice, no audio, and more. malpaco's rules also add what Pro
  never had to show: a generated board, hot-seat play, a visible seed and round counter, domination at
  three quarters, decks and sets, events, and three computer levels.
- **Scope**:
  - **`design/ui.md`**: the UI malpaco builds first (the canonical variant), written so a TypeScript
    implementer can build it without the evidence. Give requirements and properties; do not give
    pixel-exact layouts copied from Pro.
    - **Screens and flow**: from launch to the first move, setup and options (every option T50, T51 and
      T53 define), the board, the end and result screen, saving and loading, with the number of steps to
      a first game (UW-7).
    - **The board** on a generated map: how ownership shows (colour plus a non-colour cue, a
      colour-blind-safe palette), army counts, islands and their bonuses, centres, legibility at the
      smallest supported size, and resolution independence (UW-1, UW-3, UW-16, UW-17, UW-18).
    - **The turn**: a phase bar for income, cards, placement, attacks, the move and the end; what is
      legal is offered and what is illegal is explained (UW-6, UW-9); hot-seat hand-over that hides
      hands.
    - **Combat feedback**: dice, the exchange, the capture, the move-in counter, quitting a battle, and
      T50's re-rolled ties made visible (UW-13).
    - **Cards**: the hand, sets, the trade-in, the raid and the shield, the self-emptying card, and the
      discard before a draw into a full hand, all readable at a glance (UW-12). T51's swings must be
      visible as they happen.
    - **Events and centres**: each event shown on the countries it hits, centre moves, the harvest
      (UW-4).
    - **Computer turns**: shown within T53's presentation budget, followable, with a fast-forward; the
      computer's level shown per seat (UW-10).
    - **Information**: standings and who leads, so domination and the leader check are readable; the
      round counter and limit; an event log (UW-5, UW-11).
    - **Sound**: what events and actions sound like, music, and the volume and mute controls, as
      requirements (UW-14).
    - **Input**: generous hit targets, nothing that depends on hover, keyboard shortcuts, touch where
      possible (UW-15).
    - **Disabled features leave no trace**: switched-off events, centres or the round limit show nothing
      (UW-19).
    - **Testability**: what an automated check can verify about each screen, so the gates can tell a
      blank screen from a working one (UW-2).
  - **The decision table**: one row per spec claim (C-UI-01, C-UI-02) in T50's form, and **one row
    per UI question**: `| Q-UI-<nn> | decision | malpaco's design (§ link) | what Pro does, in our words,
    and the weakness addressed |`. The decision is one of `keep`, `change`, `replace`, `drop` or `open`.
    `keep` means malpaco does as Pro does, and says why that works.
  - **At least as good as Pro's, argued**: for each of UW-1 to 19, say how the design meets or beats both
    Pro and the proof of concept. Name anything that falls short, as a choice.
  - **The owner's choices**: `## Choices for the owner`, with every `open` row and every call that
    changes the look or feel, such as the art direction, the palette, the board style, the pacing of
    computer turns or the sound. Each has 2–3 options, a recommendation and a reason.
  - **Variants**: append T52's choices to `design/variants.md` in its existing form. UI settings (speed,
    animations, colour-blind palette, sound) are named variants of the canonical UI.
  - **check_design.py** checks `design/ui.md` against `spec/user-interface.md` (2 claims) and against
    the `Q-UI-*` ids of `questions/malpaco.md` (22 questions). Every id has exactly one row and no row
    names an unknown id, with the same decision words, why-checks and fail-closed bans as the other
    design files. The tests visit the new file, and every check is mutation-proven (rule 9).
  - Out of scope: art assets, mockups as images, and code; any edit in the malpaco repository; new runs
    or recordings.
- **Done when**:
  1. `python3 tools/check_design.py` prints an ok line for each of the four design files, including
     `design/ui.md ok: 24 claims, 24 rows` (2 spec claims and 22 UI questions), and exits 0. It exits 1
     on `main` today, because there is no UI design.
  2. `python3 -m unittest tools.tests.test_check_design` passes, with tests that visit the new file for
     each failure, including a missing `Q-UI-*` row and an unknown `Q-UI-*` id, each with a fixture
     that trips that failure alone.
  3. `grep -cE '^\| (C-UI|Q-UI)-' design/ui.md` prints 24.
  4. `## Choices for the owner` exists in `design/ui.md`, or, once the owner has decided,
     `## The owner's decisions (<date>)`. Every entry has options, a recommendation and a reason, and,
     when decided, the decision. Each of UW-1 to UW-19 is addressed by name in the file. `design/variants.md` has a
     section for T52's choices. The reviewer reads all three.
  5. `python3 tools/check_links.py` and `python3 tools/check_no_originals.py` pass, and the full test
     suite is green.
- **Hazards**:
  - **Copying Pro's look.** Its screens, labels, images and layout stay out (rule 18). F020 tells you
    what Pro shows and how well, not what malpaco looks like.
  - **Designing the rules again.** The UI presents T50, T51 and T53 as decided. If presenting a rule
    well needs a rule change, propose it as a choice.
  - **Mockups instead of requirements.** State what each screen must show and allow, and how a test can
    check it. Leave pixels to malpaco's implementer and art direction to the owner's choices.
  - **Deciding for the owner.** Every look-and-feel call is listed as a choice with a recommendation.
