T24 research review (sol)
You review PR #105 at 591992ab9a9947dd41c62c507e4cf2dd69d5635c: a research finding (F020, structure only; the [C3] walks are T39's, #117). You did not write it, and your job is to try to falsify it. The task file follows. Work through the gates, in order:
This is round 3, granted by the owner after escalation. Opus took over and pushed 591992ab9a9947dd41c62c507e4cf2dd69d5635c. Round 2 (your review): https://github.com/diegoami/isle-wars-archaeology/pull/105 , the last review comment before this one, with R1–R7. Round 1 (Luna): https://github.com/diegoami/isle-wars-archaeology/pull/105#issuecomment-6064808755 . The Done-when was amended on main (f1ddad6) by the owner's decision: this PR merges as the recorder and F020's structure, so your round-2 R1 (DW3 needs the walks) is resolved by contract. Check that every finding of both rounds is fixed as a class, and that each fix's test fails without it; then review the whole PR.
G0 Tree and records: the tree proof your agent file asks for; every run record validates against
   run/1; for at least one evidence file, download it from release E<nnn> and check its sha256
   against the manifest.
G0a Static first (U32): the question was attacked statically (unpacked, decompiled) before any
   runs, or the finding's Method shows why static analysis could not answer it. Runs made because a
   tool was not installed are a contract defect (C): rework. Toy research is exempt (§6).
G1 Artifact identity: every run's artifact set and variant match artifacts/known.json and the
   task's Artifact line; a patched variant is named as such.
G2 Environment identity: the runtime fingerprint is recorded; state how your environment differs.
G3 Reproduction: YOU choose at least one control and one treatment run (not the ones the finding
   highlights) and rerun them from the recorded start state and seed; compare raw observations
   field by field. A claim about a rate or a distribution needs its statistic rerun, not one sample.
   If your machine cannot run the artifact, say so: that is a tier you did not reach, not a pass.
G4 Raw vs interpretation: every sentence in Answer and Inferences cites run ids that exist;
   observations carry no interpretation; every decoded value cites an R-claim.
G5 Alternatives: write at least two other explanations of the observations yourself, and say for
   each whether the design excludes it. Check that the arms differ ONLY in the treatment: start-state
   path, how the state was restored, seed control, settings, driver path.
G6 Intervention: the finding's "Max intervention" equals the highest level in its runs, and each
   I2/I3 use is declared and justified in the finding; an I2/I3 result is not stated as
   untouched-original behaviour without a neutrality argument.
G7 Scope: the claim is no wider than the artifact versions, settings and states actually run.
Every finding names a file from the diff, and is proven (run it, quote the record) or labelled
unverified. Classify each: implementation defect | contract defect (C) | architectural uncertainty |
research uncertainty.
Post one PR comment:
  line 1: the header above
  line 2: the record verdict, one of: approve | approve after named fixes | rework | user decision
          (is the record sound?)
  line 3: "Claim outcome: " and one of: supported | supported, narrowed: <narrowing> | inconclusive |
          refuted   (what does the sound record establish?)
  then, if the finding proposes other claims (a representation claim R<nnn> included), one line
          each: "Claim outcome <id>: " and one of the same four
  then one line per Done-when line: "DW<k>: ran <command> → <result>" or "DW<k>: not run — <reason>"
  then one line per gate: "G<k>: <what you did> → <result>"
  then "Tier reached: V<k>" (the highest verification tier your review reached, and why not higher)
  then the findings R1..Rn (file:line, blocking or not, class)
  last line: the record verdict again, exactly as on line 2.
A refuted or inconclusive claim with a sound record is approved: a negative result is a result.
Apply status:approved or status:rework to issue #72.

F020 holds no observations yet: line 3 is 'Claim outcome: inconclusive' with that reason, and the record verdict judges the recorder, the checker, the tests and the Done-when.

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

## The task file (docs/tasks/T24.md on main, in full)

# T24 UI observations for malpaco: Isle Wars Pro

- **Kind**: research (a Pro screen-walk that catalogues the UI for malpaco — what the player
  sees, hears and clicks; **no rule claims**, the catalogue is an observation, not a finding)
- **Issue**: #72 · **Branch**: `task/T24-pro-ui-walk` · **Merge after**: T17 (merged)
- **Implementer**: opencode `zai-glm-5.3-flash` (GLM-5.3 Flash, Z.AI Coding Plan, effort
  `high`), rule 6's easy pair, after the quota check. L26 names Sonnet for research and the
  install, but Claude is out until ~2026-10-08, so the implementer is the next model in the
  chain whose provider has quota (the harness default). T13's round 5 and T28 take the same
  step. Substitutes: GLM-5.3 (`zai-glm-5.3`), then DeepSeek V4.1 Flash (`deepseek-flash`); a
  Claude fallback would escalate to the owner. The implementer writes the recorder in a
  worktree; the [C3] lines (the screen walks) are the main session's, and their output is
  posted on the PR.
  **Round 2 (L38):** DeepSeek V4.1 Flash (`deepseek-flash`, effort `high`), one step up: Luna's
  round-1 review asked for rework with four blocking findings (R1–R4, PR #105).
  **Round 3 (the owner, 2026-10-08, after escalation):** Opus (`task-agent-heavy`, effort
  `medium`), the top of the ladder: Sol's round-2 review raised seven blocking findings, R3 of
  round 1's R4 class (Q-UI-06 counting unidentified flashes as events). Sol reviews.
- **Reviewer**: opencode `luna` (GPT-5.6 Luna, the easy reviewer, effort `high`), another
  family, after the quota check (rule 6). Luna fits: the catalogue is small observations
  against a fixed list of questions, the volume is the data, not the reading. Substitutes:
  GPT-6.1 Sol (if a screen walk needs a careful re-look), then DeepSeek V4 Pro
  (`deepseek-pro`); a Claude reviewer is never allowed. The review re-runs the catalogue's
  per-question check from the recorded files; it does not re-run the game.
- **Easy** (rule 6): research, not a guard or gate, no new mechanism — a recorder on top of
  T13's driver, plus a per-question observation. A wrong observation is a finding, not a
  bypass of a protected rule (rule 18's source-statement rule, rule 19's Pro-only scope, rule
  20's measurement-immutability). The volume (22 Q-UI rows + the Q-PLY-04 colour row) is
  large but each row is small.
- **Why**: malpaco's UI bar needs a record of what Pro shows, sounds, and accepts — the
  static readings (F011–F016, F018, F019) cover the rules, and T28 corroborates them; the
  visible half is not in any finding. The 62 `mouseDown` and 39 `mouseUp` handlers give the
  input behaviour, but layout, timing and the look are in the score (`VWSC`) and the cast
  members, which ProjectorRays does not decode. The only way to that half is observed screens
  (T13's Pro driver). T24 catalogues the screens, the sounds, the hit areas and the timings
  for malpaco to read; it does not write rules into `spec/`.
- **Evidence**:
  - `questions/pro-static.md`: 22 `Q-UI-*` rows, almost all `screen:` corroboration, and
    `Q-PLY-04` (count the colours on the board and the options screen, T24's screen half).
    Two are `none found`: Q-UI-14 (no event log) and Q-UI-21 (board look is bitmaps in the
    cast, handlers only swap them) — both T24 records by walking the game and looking.
  - F002 (T08): the title recognised by pixels 6.6–6.7 s after launch, the seal, the cycle
    times.
  - F003 (T09): the screens and how they are reached (`experiments/E002-iwp-state-inventory/scripts/*.steps`),
    the regions and the gotchas (the board start is random; `settle` hangs while an arrow
    blinks).
  - F006 (T13): the cycle, the seal, the recovery, the time per cycle. T24 builds on T13's
    driver API.
  - F011–F016, F018, F019: each finding's **T24** cross-reference (e.g. F011 Q-UI-12 "the
    status texts and the button frames"). T24 carries those forward as the catalogue's
    anchors.
  - T29 + T31: the implementer reads the static folder through T31's grant (a comparison
    sometimes needs the handler text — e.g. Q-UI-13's "the computer's status texts, flashes
    and busy-wait pauses" is the catalogue, the handler is the cited source); the reviewer
    reads the same scripts through T29's grant.
- **Owns**: `findings/F020-pro-ui-observations.md` (new — the catalogue, status `proposed`,
  no rule claims, the observation per question is the body), `experiments/E019-pro-ui/**`
  (new: a README, a per-question runner, a per-screen walk script, the recorded files and
  their sha256, the screenshots by hash, and `check_ui_catalogue.py` that maps a recorded
  file to its question id and asserts every `Q-UI-*` row has at least one record), `runs/E019/**`
  and `evidence/E019/**` (under tracked paths, with originals out and only hashes recorded
  — rule 20). T24 does **not** own any `spec/` page; the catalogue is descriptive.
- **Scope**:
  - **Protects:** rule 18 (no decompiled line in the repository, the PR, the screenshots'
    OCR layer, or a comment; the catalogue describes screens in our own words and cites the
    finding's claim id and the script kind/number/handler); rule 19 (Pro only, set
    `iwp-2.0-996e86c5`, unregistered; a screen that needs the registered build is `static-only`
    here); rule 20 (every screenshot committed as taken, never deleted or overwritten,
    originals out and only hashes recorded).
  - **F020** (proposed), template headings as F011–F016's, for each of the 22 `Q-UI-*` rows
    plus Q-PLY-04: the observation per question (`observed` with the screen region and
    description; `narrowed` if the look depends on a cast member; `static-only` for
    Q-UI-14 and Q-UI-21 with what the walk looked for and did not find; `unestablished` if
    the walk could not visit), the cited scripts, the recorded files (path and sha256), the
    recorded timings where the question is about timing, and what would change it. No
    summary of "rule claims" — F020 is a catalogue, not a finding. A `## Observations`
    table by screen (title, options, board, placement, attack, end, scores) names what the
    catalogue shows at a glance.
  - **The recorder** (a small script in `experiments/E019-pro-ui/`): a per-question runner
    that takes a question id, the screen region (or the menu path), the count target (e.g.
    "at least 5 events" for Q-UI-06), the timing target ("frame-timed" for Q-UI-06, Q-UI-13,
    Q-UI-16), and the hit-area target ("measured" for Q-UI-18), and produces a JSON record
    per question. Each record carries the run id, the screenshot path and sha256, the
    pixels-read result, the cycle's before/after, the seal status, and the observation.
    The recorder's [C3] entries are run by the main session on the install (L26); the
    implementer writes the recorder, the main session runs the walks, the implementer
    turns the records into the catalogue.
  - **Per-screen batches (L58):** the catalogue is one finding, but the implementer pushes
    one screen-walk per commit, in this order: title and options (Q-UI-04, Q-UI-10,
    Q-UI-19, Q-UI-22), board and pieces (Q-UI-01, Q-UI-02, Q-UI-03, Q-UI-05, Q-UI-20,
    Q-PLY-04), play (Q-UI-08, Q-UI-12, Q-UI-13, Q-UI-15, Q-UI-16), events and end
    (Q-UI-06, Q-UI-07, Q-UI-11, Q-UI-14, Q-UI-21), inputs and sounds (Q-UI-09, Q-UI-17,
    Q-UI-18). Each batch merges on its own with a Done-when that names the per-question
    observation. The boundary sits at a screen, not at an arbitrary half of the catalogue.
  - **What this does not establish:** the registered build (rule 19); the score and cast
    members' decoded bytes (ProjectorRays does not decode them — the catalogue describes
    them in our words, never quotes bytes); the *content* of rules (T20–T23, T27, T28's
    surface, not T24's); the quality of play; the *playback* of a position (no save in this
    build); the projector-level windowing (Q-UI-19's window and scaling settings belong to
    the projector, not the Lingo — the catalogue notes this and stops).
  - **Not in scope:** any rule claim; a `spec/` page; rewriting T13's driver; Wine / Xvfb
    setup; DOS Isle Wars; the cast-member images or the score's frame order (these stay
    undecoded — T24 records what the player sees, not what the cast or score holds).
- **Done when** (amended 2026-10-08 by the owner's decision on the round-2 escalation: this PR
  merges as the recorder and F020's structure; the walks, their records and the full catalogue
  check move to T39, #117):
  1. F020 exists with its structure, status `proposed`, verification tier `V0`, and every
     `Q-UI-*` entry and `Q-PLY-04` marked pending; no observation is stated as made.
  2. `python3 -m unittest tests.test_e019_ui_catalogue` passes, and it includes an end-to-end
     test: every walk in `walks.py` is driven through `run_walk.py` with a fake session (no
     game, no display), and the records the recorder itself writes, with nothing added by
     hand, are fed to `check_ui_catalogue.py`'s checks, which return no error. Removing any
     field the recorder writes and the checker requires makes that test fail.
  3. Each round-2 finding has a regression test that fails when its fix is removed (R2 the
     observation field, R3 Q-UI-06's unidentified candidates never counted as events, R4 the
     regions polled together in one timed loop, R5 distinct display sizes recorded and
     required, R6 citations checked on every record including aborted ones, R7 no absence
     statement written by the recorder). The PR body names each test and the mutation that
     makes it fail.
  4. No line of decompiled Lingo appears in the repository or the PR: in bash,
     `git grep -n -i -E '/home/|/mnt/|\.local/share' -- findings experiments/E019-pro-ui runs/E019 evidence/E019`
     prints nothing. The OCR layer of screenshots is forbidden: the implementer reads the
     screen region by pixels, not by an OCR pass.
  5. `python3 tools/check_no_originals.py` and `python3 tools/check_links.py` exit 0; CI is
     green.
- **Hazards**:
  - **The look is in the cast, not the Lingo** (every row's `medium` or `low` confidence
    says so). The catalogue describes what the player sees, never quotes a cast member or
    a score byte. "The colour-keyed text members" is the cited source; the actual colour
    is the recorded observation.
  - **The frame order is in the score** (Q-UI-04, Q-UI-10, Q-UI-12, Q-UI-19). The
    catalogue names the screens the walk visits and the order the walk took; the score's
    order is not decoded and stays undecoded.
  - **The speed setting** (Q-UI-06, Q-UI-13, Q-UI-16): pause lengths depend on speed. The
    recorder normalises its timings to "speed = normal" (the unlocked default) and says so
    in the record; a future task can re-time at "fast" or "slow" if a screen question
    needs it.
  - **A misread screen** (T13's pixels-by-region path; a region outside the seal's
    viewport loses its reference). Stay inside the regions E004's manifest defines.
  - **The deal is random** (F018; Q-UI-01's "screenshots of the board at the one player
    count the build allows"): the recorder takes the screenshot after the deal, never
    before; the same deal across two records differs by definition, and the catalogue says
    so.
  - **The event frequency** is locked to normal in the unregistered build (F019's
    registration gates; Q-UI-22 "screenshots with the option on and off" is reachable only
    at the file-write path, not at the click — the recorder notes the locked state).
  - **The "no event log" claim** (Q-UI-14, `none found`): the catalogue walks the game
    for at least one long session and notes the absence; "absence confirmed" is the
    observation, not "an absence claim is supported".
  - **The board look** (Q-UI-21, `none found`): the catalogue's observation is the
    reference screenshots themselves — "the look is in the bitmaps, the handlers only swap
    them" — and a future task can adopt a score decoder if one becomes available.
  - **The C3 lines are not the implementer's**: the main session runs them, posts the
    records on the PR, and the implementer turns the records into the catalogue (L26).
- **Runs on**: `artifact:iwp-2.0-996e86c5` (the unregistered build; through T13's driver) ·
  cloud: C3 only (the install is on the user's machine) · network: N1 for push · GitHub:
  `gh:push gh:pr`

Finding: findings/F020-pro-ui-observations.md
