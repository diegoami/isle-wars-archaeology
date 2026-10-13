T52 review (Sol)

You review PR #201 at 31a59102b8b18eafa2492ec1694df68fd3a2c31d. You did not write it; a Claude (Opus) subagent did. It is
a design task: malpaco's user interface, `design/ui.md`, with one decision row for each of the 2 spec
claims (C-UI-01, C-UI-02) and each of the 22 UI questions (Q-UI-01 to 22), an argument for each of the
19 recorded weaknesses (UW-1 to 19), 18 choices for the owner (UI1–UI18), T52's section appended to
design/variants.md, and check_design.py extended to a fourth file whose ids come from two sources (the
spec and `questions/malpaco.md`). The task file follows in full. The rules the UI presents are T50
(core-rules.md), T51 (variety.md) and T53 (computer.md), as decided by the owner. Your working
directory is the review worktree: run commands there with no `workdir` argument, and use relative paths.

0. Prove the tree: HEAD is 31a5910…, and the diff against origin/main is the PR's.
1. Re-run every Done-when line yourself, and account for each (L32). DW4 is a reading line: write
   `DW4: ran a read of the choices, the UW argument and the variants section → <result>`.
2. Every changed file is one the task owns (L44). The ci.yml change is declared under Scope in the PR
   body as a comment-only fix: confirm it changes no behaviour. core-rules.md, variety.md and
   computer.md must be unchanged.
3. The extended check_design.py: mutation-prove each check for the fourth file, restoring by writing
   back the saved contents in a `finally`. Check the two-source id set: a missing Q-UI row, an unknown
   Q-UI id, a duplicate, a Q-UI row in another design file, a missing questions file, and an id named
   only in the weakness table, not in the decision table. Try to hide a row: the fence, comment and raw
   HTML bans apply. Confirm the earlier three files still check as before.
4. Design quality, the task's purpose:
   - it states requirements and testable properties, not mockups or pixel layouts copied from Pro;
   - every one of UW-1 to 19 is met or beaten, with any shortfall named as a choice (the PR names one
     for UW-10);
   - it presents T50, T51 and T53 as decided, and every rule change it needs is a proposed amendment
     listed as a choice (UI14, UI15, UI17), not applied;
   - every look-and-feel call is in Choices for the owner, with options, a recommendation and a reason;
   - the numbers hold: re-run the pasted palette model (colour distance under three colour-blind
     simulations), and check the hit-area arithmetic at the smallest window, the pacing against T53's
     36-step and watch budget (A17), and any other number an argument rests on; a tuning constant that
     is not evidence must say so;
   - the testability section lets a gate tell a blank screen from a working one;
   - the no-trace table covers every switched-off feature T50, T51 and T53 define;
   - hidden information stays hidden: hot-seat hands, the discard memory levels of A12, and anything a
     human seat could not see;
   - no status line appears (rule 3);
   - the design is complete enough to build: name any gap or constructed counterexample, such as a
     4-seat hot-seat game, a 1000-against-100 battle, an event on 3 countries after a computer turn, the
     smallest window with 46 countries, or a draw into a full hand during a computer turn.
5. Rule 18: no screen text, label, image or layout of Pro copied or quoted; Pro described in our own
   words only.

## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: a spec claim or UI question with no row, an unknown id, or
   a wrong decision word, that check_design.py accepts for the fourth file; a look-and-feel or rule
   decision made without being listed for the owner; a UI that reveals what a seat may not see;
   original game text or layout (rule 18). A bypass you proved is blocking, even when it looks like an
   edge case. (L47)
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
