T40 research review (sol)
You review PR #126 at 6afb0c22cdd1cdd3beebe5fa58a3017589baea23: a research reading pass (the E020 frame reader, its validation, and per-claim outcomes for F011 and F014). You did not write it, and your job is to try to falsify it. The task file follows. Work through the gates, in order:
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
Apply status:approved or status:rework to issue #119.

Notes from the main session:
- The sitting frames are on the user's machine under /mnt/c/Temp/iwp-shots/wine/; your sandbox cannot read them yet (#122). Done-when 2 (score.py over the labelled sample) reads them: account for it as `not run — machine-local`; the main session re-runs it and posts its output on the PR. You can still check score.py's logic, the labels' form, and the reader's tests.
- Done-when 5 was amended on main today (f-string: check_quotes.py dropped, it cannot run bare); the task file below is the amended one.
- The implementer reports that every event is the net of two or more exchanges (frames about 1.4 s apart), and declares every claim `unestablished`. Check that outcome, and that check_counts.py and outcomes.json cannot promote a net event to a single-exchange claim. The owner decides separately how to get single exchanges.
- G3 (reproduction) is not reachable without the frames; say so.

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

## The task file (docs/tasks/T40.md on main, in full)

# T40 E020 reader and counts: read the sittings' frames by pixels

- **Kind**: research (a reading pass over model-driven sittings; corroboration of F011 and F014)
- **Issue**: #119 · **Branch**: `task/T40-e020-reader` · **Merge after**: T38 (merged)
- **Implementer**: claude `task-agent` (Sonnet, effort `high`), with the tripwire paragraph of
  `docs/models.md`. It must read the sitting frames on the user's machine, which OpenCode cannot
  reach (L26; rule 6's research/install line). Fallback: Opus (`task-agent-heavy`).
- **Reviewer**: opencode `gpt-6.1-sol` (GPT-6.1 Sol, effort `low`), another family, after the
  quota check (`/recommend`). Substitute: Opus would be the implementer's family, so escalate.
- **Hard** (rule 6): a new mechanism (a pixel reader of the board's army numbers and owners) whose
  errors would let `check_counts.py` (T38's corroboration guard) accept counts the game never
  showed.
- **Why**: T38 built the driver and split the counting off (the owner, 2026-10-08): events can only
  be read from a sitting's frames, and the reader can only be built against real frames. Three
  sittings exist (records `E020-r0001` and `E020-r0002`; the third, `20261008T204817Z`, is
  exported by T41). They hold about 2,300 frames of computer-vs-computer play, including one
  30-turn game.
- **Evidence**:
  - The sitting directories on the user's machine, under `/mnt/c/Temp/iwp-shots/wine/`
    (`20261008T184505Z`, `20261008T195537Z`, `20261008T204817Z`): `frames/`, `frames-index.jsonl`
    (each frame's step, time and sha256), `actions.jsonl` (the loop's blocks, games and turns).
    Rule 18's constraint A, as amended on 2026-10-08, lets model APIs read them. Never copy a frame
    into the repository.
  - `tools/check_counts.py`, `experiments/E020-wine-first-run/scenarios.txt`, `e020_export.py` and
    `outcomes.json` (T38): the event contract the readings must satisfy. An event is one step with
    `game:ordinal`, `event:seq`, every event field once, valid values, and two distinct frames held
    in the record's outputs.
  - `walkthroughs/coordinates.md`: the 44 measured country points (#120: 2 of 46 are missing) and
    the screen regions. `findings/F011-pro-combat-rules.md` (the exchange as read from the Lingo),
    `walkthroughs/f011-questions.md` (the per-arm targets), and F014 (`C-CRD-06`, the bomb).
  - The static reading comes first (rule 24): F011 names what one exchange changes on the board
    (the attacker's and defender's counters). This task reads those changes from frames because
    the counts are distributions that only play can give.
- **Owns**: `experiments/E020-wine-first-run/reader/**` (new), `experiments/E020-wine-first-run/
  measurements/**` (new: the labelled validation sample and the per-sitting reading summaries),
  `experiments/E020-wine-first-run/outcomes.json`, `runs/E020/**`, `evidence/E020/**`, the
  per-claim sections of F011 and F014 that cite E020 (constraint G: per claim, never in bulk), and
  tests for the reader.
- **Scope**:
  - **The reader** turns a sitting's frames into `readings.jsonl`: per frame, the army number and
    the owner's colour word of each country it can read, by pixels only. Digit glyphs are matched
    against templates measured from the frames; there is no OCR engine and no OCR pass. A country
    the reader cannot read with confidence is recorded as unread, never guessed.
  - **Events**: an exchange is a pair of frames, during a computer's turn, in which exactly two
    adjacent countries change. From it, record the attacker's and defender's counters before and
    after, and the owners. Anything ambiguous (more than two countries change, a placement, a
    redraw) is not an event. Each event cites its two frames by sha256.
  - **Validation**: before any count is believed, a labelled sample. At least 200 country readings,
    from at least 30 frames across all three sittings, labelled by looking at the frames, are
    committed as numbers and colour words only (frame sha256, country number, army count, owner).
    The reader is scored against it.
  - **Counts and outcomes**: export each sitting's record with its readings. Run
    `check_counts.py`. Declare each claim's outcome in `outcomes.json` honestly: `corroborated`
    only where its arm rule holds; otherwise `narrowed` or `unestablished`, with the shortfall. The
    targets are not expected to be met by three sittings; more sittings follow (T41).
  - **Out of scope**: the driver (T41); any `spec/` change (only the main session promotes);
    reading text of any kind.
- **Done when**:
  1. `python3 -m unittest discover -s tests` passes. It includes reader tests on synthetic frames
     that fail with the matching removed, and event tests that refuse a frame pair where more than
     two countries changed.
  2. `python3 experiments/E020-wine-first-run/reader/score.py experiments/E020-wine-first-run/measurements/labels.json`
     (new) prints the sample size and the reader's accuracy, and exits 0 only when the sample has
     at least 200 readings from at least 30 frames of all three sittings, and the reader's army
     count is right on at least 98% of the readings it does not mark unread, with at most 10%
     marked unread. Runs on the user's machine; the main session posts its output on the PR.
  3. For each sitting, `python3 tools/validate_records.py runs/E020/cmb-accumulation/<record>.json`
     exits 0, and `python3 experiments/E020-wine-first-run/check_records.py` reports every record
     and manifest ok.
  4. `python3 tools/check_counts.py experiments/E020-wine-first-run/scenarios.txt` runs and prints,
     per claim, the observed counts and any shortfall. Every outcome in `outcomes.json` that says
     `corroborated` passes its arm rule (the checker refuses otherwise). It need not exit 0 while
     floors are unmet.
  5. `python3 tools/check_no_originals.py` and `python3 tools/check_links.py` exit 0; CI is green.
     (Amended 2026-10-09: `check_quotes.py` needs an original and a sources file, so it cannot run
     bare; this task quotes nothing of the original, and constraint D is checked by DW3's records
     carrying numbers and colour words only.)
- **Hazards**:
  - **A misread digit becomes a fake exchange.** Count only what the validation sample supports;
    unread is better than guessed.
  - **A redraw or a placement looks like an exchange.** Use `actions.jsonl` to place each frame in
    the computers' turns, and accept only two-country changes between adjacent countries.
  - **The two missing country points** (#120): countries the reader has no point for stay unread,
    not interpolated.
  - **Quoting** (constraint D): readings and records carry numbers and colour words only.
- **Runs on**: the frames already on the user's machine; no new sitting is run in this task.
