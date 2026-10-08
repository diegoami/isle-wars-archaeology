T38 review (sol)
You review PR #118 at 0b82d82db005e131a0cc407249bd4a2207db6627. You did not write it. This is a narrow re-review of rounds 5 and 6 (granted by the main session under rule 7's exception and the owner's KEEP PLAYING decision).
0. Prove the tree: HEAD is 0b82d82db005e131a0cc407249bd4a2207db6627. Round 5 is 2983ee1 (your round-4 R1: classify the screen between quiet blocks). 45ac6fc merges origin/main. Round 6 is `git diff 45ac6fc2f3eed4df8e6e816eb83e3caad34cccb6 0b82d82db005e131a0cc407249bd4a2207db6627` (the winner notice, `game-over`, CONTINUE at 401,534, and the second sitting's record E020-r0002). Findings name files in that diff.
1. Scope: your round-4 R1, and round 6's changes, plus anything they broke. Raise no other finding unless it is blocking.
2. Your sandbox cannot read the sittings' frames yet (#122). The main session ran the classifier over both sittings' real frames locally and reports: frame 182-1791490010546.png (sha256 14ae2f71…) reads `game-over` with winner red; frame 176-1791486093693.png reads `eliminated`; frame 158-1791485847675.png reads `board-menu`. Opus reports per-name counts over all 1179 frames in walkthroughs/coordinates.md. Treat those numbers as the main session's and the implementer's measurements, unverified by you; check the code and tests against them.
3. For each change, remove it (in place, then restore) and name the test that fails.
4. Display isolation must still hold: the new reads go through Session and send no input.
5. Re-run `python3 -m unittest discover -s tests` and DW2–DW8 as far as they run, with both records. Account for DW1–DW8 (DW1's find is machine-local; DW8's counts wait for T40).
Prove each finding or label it unverified. Your final message is the review: the header; the verdict (approve | approve after named fixes | rework | user decision); the DW lines; the findings R1..Rn (file:line, blocking or not); the verdict again last. Never post it.

The owner already decided: the count floors are T40's (#119); headless sittings run without asking; KEEP PLAYING on the elimination notice. Do not return "user decision" for those.

# The review brief's own sections

Every review brief carries these two sections, in full, after the numbered block of
`process.md` §5 (or, in the review profile, after the brief's numbered lines). The reviewer reads
the brief in another file, so paste them; never point to this one. Write "Blocking means" for the
task; paste the second section as it is. (L47, L49)

```text
## Blocking means

Any one is enough; a blocking finding means rework, never approve.
1. A Done-when line fails, or cannot be run as written.
2. What this task protects can be got past: <name it: the guard, check, permission, invariant,
   rule value or file this task exists to protect>. A bypass you proved is blocking, even when it
   looks like an edge case. Never "follow-up hardening" or "outside the threat model" unless the
   task says so; if it does, quote the line. (L47)
3. Behaviour the task forbids, or behaviour nobody asked for, inside a file the task requires. (L44)
4. <project-specific items: a constant with no evidence, a test that passes with the behaviour
   deleted, a status written into a document>
Not blocking: wording, style, and defects in code the PR did not change: file those as follow-ups.
When unsure, say how likely the problem is. Rate it blocking only if it is likely and would get
past what the task protects; otherwise it is a follow-up. (L53)

## Report every blocking finding in this one review

This review is your only pass before the author fixes. Do not stop at the first blocking
finding: finish reading the whole diff and the task file, check every Done-when line and
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
```

## Round 6's contract, in full

# T38 round 6 (narrow), Opus: the winner screen

Same decision as round 4 (the owner chose KEEP PLAYING, "watch until the game ends and record the
game's end"). Branch `task/T38-wine-first-run`, head 45ac6fc (your round 5 plus merges of main).
Fetch, check it out in your worktree, commit on it, push (no force-push). Keep PR #118 a draft;
add a "Round 6" section. **Never launch wine, Islepro.exe or the install. Fakes only.** No sitting
is running now.

## What the second sitting showed (sitting 20261008T195537Z, driver 45ac6fc's parent d2e8009)
Frames: `/mnt/c/Temp/iwp-shots/wine/20261008T195537Z/frames/` (you may read them; never copy one).
- Game 1, 14 turns, then the elimination notice; the loop clicked KEEP PLAYING (665,531), the
  screen changed, and the loop polled the screen. Correct.
- About 10 s later the game showed the **winner screen**: the dark notice panel over the board,
  text "The Red Army is the winner of this Game!" (in the winner's colour), and a single grey
  **CONTINUE** button in the bottom centre panel. Red held all 46 countries (score panel). Frame
  `182-1791490010546.png`, sha256 14ae2f71ee90f1578a5eeaeacef626cac3167bbeebe5fcfad27708db03994761.
- `screens.name_of` read it as `board` (the score panel is up, and `eliminated` needs both
  buttons), so the play-out would have polled until `sitting_seconds`. The main session
  interrupted it (status `aborted: driver-bug: KeyboardInterrupt`, clean recovery).
- Measured by the main session, by pixel colour on frame 182: CONTINUE grey box x 327–475,
  y 522–546, centre 401,534.

## The change
1. `screens.name_of` gains `game-over`: the notice panel plus the CONTINUE box, with neither the
   KEEP PLAYING nor the ACCEPT LOSS box. Derive thresholds from the real frames of both sittings,
   and check over every frame of both that `game-over` matches only the winner frames, and that
   no earlier name changes (eliminated, board, board-menu, title, unknown). Record the measures
   in `walkthroughs/coordinates.md` with their sources, as in round 4.
2. During the play-out, and at any turn's start, `game-over` ends the game: log
   `game-end` with `ended: game-over` and the winner's colour if the score panel shows it by pixels
   (the seat with 46; colour words only, never OCR), click CONTINUE once (its own block,
   `game-over-continue`), then read the screen. Start the next game only on `title` or
   `board-menu` (proven New Game screens). On anything else, end the sitting cleanly through the
   existing unknown-screen path. Do not guess what follows CONTINUE.
3. Export the second sitting as a raw record (`--records --sitting
   /mnt/c/Temp/iwp-shots/wine/20261008T195537Z --batch cmb-accumulation`) and commit it beside
   E020-r0001 (rule 20).

Each change gets a test that fails with it removed (check). Run `python3 -m unittest discover -s
tests`, `git diff --check origin/main...HEAD`, and DW3 over both records. Hand back: the changes,
tests, mutation results, the classifier's counts over both sittings' frames, the new record's
path and status, the command tails, and the pushed head SHA.

## Round 5's contract, in full

# T38 round 5 (narrow, one finding), Opus

The main session grants a narrow round under rule 7's exception: the remaining finding changes
no result, because both paths send no input. Branch `task/T38-wine-first-run`, head d2e8009 (your
round 4 plus a merge of origin/main). Fetch it, check it out in your worktree, commit on it and
push (no force-push). Keep PR #118 a draft; add a "Round 5" line to its body. **Never launch
wine, Islepro.exe or the install, even to test. Fakes only.** A real sitting is running on this
machine right now from another worktree: do not touch `/mnt/c/Temp/iwp-shots/` or any wine
process.

Fix only Sol's round-4 R1 (the review follows): classify the screen before entering or retrying
a readiness wait, so an unknown screen that never settles ends the sitting as `unknown-screen`,
with its final frame and no click. Keep the existing no-input guard: a known board that never
settles still aborts as `not-ready`. Add the regression test Sol describes (screens `["title",
"unknown"]`, noisy waits): it must fail with the fix removed (check that). Run `python3 -m
unittest discover -s tests` and `git diff --check origin/main...HEAD`. Hand back: the change, the
test, the mutation result, the command tails and the pushed head SHA.

## Sol's round-4 review, in full

T38 review (gpt-6.1-sol)
rework

HEAD verified: d2e8009d5196617e7f9c2657396c2239920d5724; worktree identity matches the brief; origin/main diff is nonempty. Reviewed the complete narrow round-4 diff, including all 444 record/manifest entries. No game launched.

Verification: `python3 -m unittest discover -s tests` passed twice, including after restoring mutations: 801 tests. `git diff --check origin/main...HEAD` passed. Screen reads use guarded `Session.screen_name` and the session engine’s own capture.

DW1: not run — the machine-local existence command accesses a path forbidden by the brief’s overriding output rules. User-path grep passed. Clean status contains only the supplied untracked harness brief; no review mutations remain.
DW2: ran both named batch `--help` commands and `--batch unknown-x --help` → known batches print the required targets; unknown batch is refused by name, exit 2.
DW3: ran `python3 tools/validate_records.py runs/E020/cmb-accumulation/E020-r0001.json`, the prescribed platform-token assertion, `python3 tools/check_no_originals.py`, and `python3 tools/validate_wine_manifests.py evidence/E020/E020-r0001.manifest.json` → all passed.
DW4: ran record schema validation and the prescribed structural-field assertion → passed; the exported record has only `sitting:epoch`, with no events.
DW5: ran the prescribed diff assertion over owner-play records and finding → passed; both batch help notes identify owner-play evidence as primary.
DW6: ran `python3 tools/check_no_originals.py` and the five-case gate assertions → F019 row passes; all four mutations are refused.
DW7: ran the prescribed `spec/` diff assertion → passed.
DW8: ran `python3 tools/check_counts.py experiments/E020-wine-first-run/scenarios.txt` → exit 1 with zero observed events and explicit shortfalls, as permitted pending T40. `check_links.py`, `check_no_originals.py`, and `check_pro_question_map.py` passed. Remote CI was not checked.

Mutation checks, all restored with `git checkout -- <file>`:
- Item 1: removing the `eliminated` classification fails `ScreenNameTest.test_each_synthetic_screen_is_named` and `test_the_notice_wins_over_the_board_and_its_menu`.
- Item 2: removing the KEEP PLAYING block call fails `ScreenLoopTest.test_the_first_sittings_turn_16_is_answered_with_keep_playing`.
- Item 3: removing final-frame capture fails `ScreenLoopTest.test_an_unknown_screen_at_a_turns_start_ends_the_sitting_unclicked`.
- Item 4: removing indexed frames from export fails `ExportTest.test_a_sitting_without_readings_is_exported_raw_with_its_frames_and_no_events`. This export capability predates round 4; round 4 adds its regression test and actual record.

Real-frame verification was not performed: the overriding output rules forbid every external read except the static folder, whereas the requested sitting frames are outside it. Consequently, measured thresholds remain independently unverified against frames 166, 176, 158, and 164.

R1 — **blocking**, `experiments/E020-wine-first-run/e020_loop.py:97–109`: Unknown-screen handling is gated behind the readiness wait. `play_game()` calls `wait_quiet()` before its first screen classification, and repeats that ordering after committed turns. An unrecognised screen that does not settle therefore exhausts the quiet attempts and aborts as `not-ready`, rather than taking a final frame and ending cleanly as `unknown-screen`, as round-4 item 3 requires. Reproduced with the existing fake driver using screens `["title", "unknown"]`, `noisy=99`, and `raises=True`: the trail contains the title read, New Game, and six quiet blocks; no unknown-screen read or final frame occurs, and the summary is `aborted: not-ready`. Classify before entering or retrying readiness waits, routing unknown screens to the final-frame stop without weakening the existing no-input readiness guard. Add a regression test for this non-settling unknown-screen case.

Final pass done

rework

— gpt-6.1-sol, via tools/harness/review.mjs (openai/gpt-6.1-sol)
