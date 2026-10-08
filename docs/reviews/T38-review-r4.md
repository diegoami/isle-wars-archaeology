T38 review (sol)
You review PR #118 at d2e8009d5196617e7f9c2657396c2239920d5724. You did not write it. This is a narrow re-review of round 4, granted by the owner after the first sitting.
0. Prove the tree: HEAD is d2e8009d5196617e7f9c2657396c2239920d5724. Round 4 is `git diff f19dab6c72d4aa15f546425e6a903453bcb1586c 68d0ea4f7de69b5d4fad3e0e73d1b82c40a94b8f`; d2e8009 then merges origin/main and keeps main's tests/test_runs.py (T24 already allows batch folders). Findings name files in that diff.
1. Scope: round 4's four items only (the contract is below), plus anything round 4 broke. Your round-3 findings stay closed. Raise no other finding unless it is blocking.
2. The first sitting's frames are on this machine under /mnt/c/Temp/iwp-shots/wine/20261008T184505Z/frames/. Rule 18 now lets you read them (CLAUDE.md, constraint A, 2026-10-08); never copy one. Check the screen tests against real frames: `eliminated` on 166-* and 176-1791486093693.png; not `eliminated` on 158-* and on the first frames of 164-*.
3. For each item, remove the change (in place, then restore) and name the test that fails.
4. Display isolation must still hold: the new screen reads go through Session.
5. Re-run `python3 -m unittest discover -s tests` and every Done-when line that can run, including DW3 with the exported record runs/E020/cmb-accumulation/E020-r0001.json. Account for DW1–DW8 (DW8's counts wait for T40).
Prove each finding (run it, or delete the behaviour and name the test that fails) or label it unverified. Your final message is the review: the header; the verdict (approve | approve after named fixes | rework | user decision); the DW lines; the findings R1..Rn (file:line, blocking or not); the verdict again last. Never post it.

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

## Round 4's contract (the brief Opus worked from), in full

# T38 round 4 (narrow), Opus: the elimination notice

The owner granted a narrow round 4 after the first sitting. Branch `task/T38-wine-first-run`,
head f19dab6 (your round 3). Fetch it, check it out in your worktree, commit on it and push to it
(no force-push). Keep PR #118 a draft and add a "Round 4" section to its body. **Never launch
wine, Islepro.exe or the install, even to test: fakes only.** The main session runs the next
sitting itself.

Rule 18 changed today (CLAUDE.md, constraint A): a model-driven sitting's screenshots and frames
may now be read by model APIs, to inspect a sitting. They are still never committed, uploaded or
posted. You may view the frames named below with the Read tool, to measure from them.

## What happened in the first sitting (batch 1, sitting 20261008T184505Z)
The sitting directory, on this machine, is `/mnt/c/Temp/iwp-shots/wine/20261008T184505Z/`.
- Game 1 played 15 turns cleanly. The loop's placement stacks every army on the first country
  that accepts it, so by turn 15 the human seat (Blue) held one country (frame `164-*.png`).
- On turn 16 the game showed a modal notice over the board: "You've been eliminated from the
  game. Do you want the other armies to play it out?", with two buttons in the bottom bar. Frames
  `166-*.png` (the first turn-16 placement attempt) and `176-1791486093693.png` (sha256
  ad5970b63f864a7c7e2ef8a958c7e4619a587833dcdf763b68eaa44b1140adf0) both show it.
- The loop tried all 44 placement points (none worked), found nothing to dismiss, treated it as a
  game end and clicked New Game at 100,585, which is not on this screen. `click!` saw no change,
  and the driver aborted with `aborted: step-failed`. It recovered cleanly (prefix reset,
  0 processes left).

Measured by the main session from frame 176, by pixel colour (record these in
`walkthroughs/coordinates.md` with that source):
- KEEP PLAYING (red): box x 572–759, y 512–550, centre 665,531.
- ACCEPT LOSS? (yellow-olive): box x 37–224, y 513–550, centre 130,531.

## The owner's decision: KEEP PLAYING
1. **Recognise the elimination notice at the start of every human turn, before placement**, by a
   pixel test on its measured regions (both buttons' colour boxes, plus the dark modal panel over
   the board). Never by OCR. Derive the test from frames 166 and 176, and check it is false on
   normal-turn frames (for example 158 and 164) and on the setup and title frames of the same
   sitting.
2. On the notice, `click!` KEEP PLAYING (665,531) once, log it as its own block
   (`eliminated-keep-playing`), and from then on send **no** input except what a recorded source
   proves is needed. Watch and capture frames while the computers play the game out, bounded by
   the batch's `sitting_seconds`, and record the game's end.
3. **Any other screen the loop does not recognise** (including the unmeasured game-over screen
   after a computer wins) ends the sitting cleanly: take a final frame, log
   `ended: unknown-screen` with the frame's sha256, and stop through Session without clicking.
   Never click New Game on a screen not proven to be the title or the board. A later round
   measures the game-over screen from this sitting's frames.
4. **Export without readings.** `--records` must turn a sitting that has no `readings.jsonl`
   (T40 builds the reader), or that aborted, into a raw run/1 record and evidence manifest that
   keep the real status, the provenance and the frames by hash, with no events. This is T38's
   first record (DW1 and DW3). Export sitting 20261008T184505Z itself with it, and commit the
   record and manifest under `runs/E020/` and `evidence/E020/` (rule 20: measured outputs are
   committed as made). The frames themselves stay on the machine.

Each change has a test that fails with it removed (check that). Run `python3 -m unittest
discover -s tests`, `git diff --check origin/main...HEAD`, DW2, DW3 (now with the exported
record: `validate_records`, the platform-token test, `check_no_originals.py`,
`validate_wine_manifests.py`), DW4, DW6 and DW7. Hand back: the change and test per item, the
exported record's path and status, each command with its output tail, the pushed head SHA, and
anything you could not do.
