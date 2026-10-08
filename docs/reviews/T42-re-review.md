T42 review (sol)
You review PR #129 at 513a71e575e24b7ddfdb4b85cbf251d7b46f3da0. You did not write it. The task file follows.
This is round 2, the last before escalation. Your round-1 review (R1–R3 blocking) is on PR #129. Opus took over (L38): the rate now counts every capture over max(deadline, end of the last capture) and is compared unrounded; an adversarial test drives a display answered by another process's socket. The PR body lists a sweep of every watcher guard and 17 mutations. Check each round-1 finding is fixed as a class, with a test that fails without it, and review the whole PR.
0. Prove the tree: HEAD is 513a71e575e24b7ddfdb4b85cbf251d7b46f3da0 and the diff against origin/main is the PR's; findings name its files.
1. Re-run every Done-when line yourself, and account for each (L32). The PR's evidence is no proof.
2. [evidence-driven] Every constant traces to a fixture, report or investigation; a [designed] one says what was searched.
3. [seeded] No wall clock, unseeded random or order-dependent iteration in rule code.
4. Every changed file and behaviour is one the task asks for (L44); docs it makes wrong are updated.
5. Sweep the diff: tests that pass with the behaviour deleted (mutate, rebuild clean, re-take any
   negative result), branches no input reaches, edge comments without a test, any path by which a capture reaches the caller's DISPLAY, display :0 or the root window; a frame index line naming a file whose sha256 differs.
Prove each finding (run it, or delete the behaviour and name the test that fails) or label it
unverified. Your final message is the review: the header; the verdict (approve | approve after
named fixes | rework | user decision); per Done-when line `DW<k>: ran <command> → <result>` or
`DW<k>: not run — <reason>`; the findings R1..Rn (file:line, blocking or not); the verdict again
last. Never post it: the script posts it and applies the label.

Done-when 2 is machine-local: the main session ran it at this head and posted the output on the PR (8.000 fps, exit 0, at the new head). Account for it as 'not run — machine-local; main session's output on the PR'. Display isolation is this task's guard: try hard to break it.

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

## The task file (docs/tasks/T42.md, in full)

# T42 E020 watcher: capture fast enough to see single exchanges

- **Kind**: infrastructure (a driver change; its first sitting is a measurement)
- **Issue**: #128 · **Branch**: `task/T42-fast-capture` · **Merge after**: T41 (merged)
- **Implementer**: claude `task-agent` (Sonnet, effort `high`), with the tripwire paragraph of
  `docs/models.md`. Measuring a capture rate needs the driver's display tools on the user's machine,
  which OpenCode cannot reach (L26). Fallback: Opus (`task-agent-heavy`).
- **Reviewer**: opencode `gpt-6.1-sol` (GPT-6.1 Sol, effort `low`), another family.
- **Hard** (rule 6): the watcher is on the display-isolation path (T38 R1): a capture that falls back
  to the caller's display, or to the root window, would capture the owner's desktop.
- **Why**: T40's reader is accurate (100% on its validation sample), but the watcher grabs one frame
  about every 1.4 s (ImageMagick `import`, `runtime/iwp/driver/watcher.py`), and the computer plays
  several exchanges in that time. All 55 events read from the three sittings are nets of two or
  more exchanges, so no per-exchange claim of F011 can be corroborated. The owner decided on
  2026-10-09: **faster capture first**, with no change to the game; if exchanges still blur, the
  game's SLOW speed is the fallback (a separate decision).
- **Evidence**: `runtime/iwp/driver/watcher.py` (T38: one frame per interval, `import -window
  <id>`, never the root window, the session's own environment); T40's PR #126 (the net-event
  finding and the reader); `ffmpeg` and `xwd` are installed on the user's machine.
- **Owns**: `runtime/iwp/driver/watcher.py`, the watcher's tests, `experiments/E020-wine-first-run/
  README.md` (the capture section), `experiments/E020-wine-first-run/measurements/capture/**`
  (new: the rate measurements).
- **Scope**:
  - A capture path that sustains at least 5 frames per second of the game window, measured, on the
    session's own display only. The method is the implementer's choice (for example `ffmpeg
    x11grab` limited to the game window's geometry on the session display, or `xwd` of the window
    id). Frames keep T38's contract: each hashed into `frames-index.jsonl`, structural logs only,
    the window and never the root window, the session's environment passed to every command.
  - Identical consecutive frames are stored once (by hash), so a fast capture does not multiply
    disk use on a still screen.
  - Measure the sustained rate on an empty Xvfb display of the driver's own (never the owner's
    `:0`), with no game: the measurement is committed under `measurements/capture/`.
  - **Out of scope:** any game run (the main session runs the next sitting after the merge, then
    T40's reader reports whether single exchanges separate); the reader; the game's speed.
- **Done when**:
  1. `python3 -m unittest discover -s tests` passes, including tests that fail with the change
     removed: the capture command always targets the session's display and the game window's id
     or geometry, never the root window, and never inherits the caller's `DISPLAY`; duplicate
     frames are stored once.
  2. `python3 runtime/iwp/driver/watcher.py --measure-rate --seconds 20` (new) starts its own Xvfb
     display, captures a test window on it for 20 s, prints the sustained frames per second, and
     exits 0 only when the rate is at least 5. Runs on the user's machine; the main session posts
     its output on the PR, and the measurement file is committed.
  3. `python3 tools/check_no_originals.py` and `python3 tools/check_links.py` exit 0; CI is green.
- **Hazards**:
  - **Capturing the owner's desktop.** `x11grab` without an explicit display and geometry grabs
    `:0`. Pass the session display and the window geometry explicitly, and test that.
  - **Disk.** A 90-minute sitting at 5 fps is 27,000 frames: deduplicate still frames, and bound
    the frame count per sitting.
- **Runs on**: the user's machine (Xvfb, no game). No original file is touched.
