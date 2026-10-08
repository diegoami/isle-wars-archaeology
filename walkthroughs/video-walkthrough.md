# Video-only walkthroughs — the owner just plays

The owner's decision (2026-10-07): for T28's C3 step the walkthroughs are **video-only and
user-driven** — no poller, no click-driver, no per-case discipline. The owner plays the game
naturally with **Bandicam (full version)** recording window video and system audio; the main
session turns the recording into the per-question records. The poller (`iwp-poller.ps1`) and
the click-driver (`run-batch.ps1`) stay in this directory as the fallback paths; they are not
part of a video-only session.

## Windows side (the owner)

### One-time setup

1. Video folder: `New-Item -ItemType Directory -Path C:\Temp\iwp-shots\video -Force`
   (the main session reads it from WSL as `/mnt/c/Temp/iwp-shots/video/`).
2. Bandicam (full version — no watermark, no time cap):
   - **Target**: the Isle Wars Pro window (game/window capture, or a rectangle drawn exactly
     around the 800×600 stage; no margin is needed without a watermark).
   - **FPS**: 30, fixed (not VFR).
   - **Audio**: on, recording system sounds ("Primary Sound Driver") — the game's sounds are
     half of what T24/T28 want from the video.
   - **Format**: MP4 (H.264 + AAC).
   - **Output folder**: `C:\Temp\iwp-shots\video`.
3. One continuous recording per session is fine (the full version has no 10-minute cap).
   Multiple files from several sittings are equally fine — files are processed by name order
   and content, never renamed.

### While playing

- Play at **normal speed** and **let animations finish** before the next click (attack dice,
  card award, colour-flip): army counters are read frame by frame, and a counter mid-animation
  is unreadable.
- No notes or announcements needed. A deliberate 2-second hover before a boundary-case attack
  makes that moment easy to find on the timeline, but is optional.
- A case that never comes up naturally is skipped; the main session marks it `narrowed`
  (rule 22, be practical) and it can be targeted later.

### What to play

**Session A — deliberate cases (~30–45 min, a few EASY games).** Skip anything that does not
come up; each row names the finding question it feeds (see `f011-questions.md`).

| Goal | What it looks like | Feeds |
| --- | --- | --- |
| Options screen, once | Visit it, let it sit ~10 s. | Q-SET-04 |
| Even attacks ×16 | Attack a neighbour at stack **2, 4, 8, 12** vs **N−1 / N / N+1 / N+2**. | Q-CMB-01 |
| Underdog attacks ×4 | Attack a **strictly stronger** defender from 4, 8, 12, 20. | Q-CMB-02 |
| Tiny attacks ×3 | Attack a 1-army country from 1, 2 and 3. | Q-CMB-03 |
| Small-stack moves | Stacks **2, 3, 5**: move **all / all-but-one / all-but-two**; can the counter reach 0? | Q-MOV-02 |
| Small-stack captures ×3 each | Take a country from stacks 2, 3, 5. | Q-OWN-01 |
| Move-then-more | ~10 turns with a move; some attack-first-then-move; after a move a second move or attack; capture then attack same turn. | Q-MOV-01, Q-MOV-03 |
| Quit an attack | The quit button mid-battle (×2 if convenient). | Q-CMB-08 |
| Lose some attacks | ~5 failed attacks; what happens to the turn. | Q-CMB-09 |
| Busy turns | ~10 turns with 3+ attacks; what ends each. | Q-CMB-10 |

**Session B — let the computers fight (any length; more is better).** Place armies (`ALL`),
`PASS`, repeat. Every computer-vs-computer attack is one exchange of data for Q-CMB-04/05/06/07
and Q-CMB-11, and it accumulates from *any* video, Session A included.

**Fixed for this batch (the owner, 2026-10-07):** all 16+4+3 human boundary cases; small stacks
2/3/5 only (10+ marked narrowed if unreached); **Q-CMB-12 dropped** (the "never attacks"
condition is rare — static-only or narrowed in the per-claim section).

## WSL side (the main session)

When the owner says a batch is done:

1. Pick the files up read-only from `/mnt/c/Temp/iwp-shots/video/`; `sha256sum` each. The video
   files never enter the repository or any release (rules 18/20) — only hashes and extracted
   frames, and the videos stay on the owner's machine.
2. Extract frames with ffmpeg (`/usr/bin/ffmpeg`, 6.1.1) at the timestamps each case needs;
   read army counters and screen state **by pixels only — no OCR pass** (T24's Done-when rule,
   carried over here). Audio events (sound onsets) are timed from the waveform, not by ear.
3. Write one record per question to `runs/E018/combat/<run-id>.json`, shaped like the playbook's
   record in `README.md`, with `video_sha256` and `video_offset` (mm:ss.ms) in place of
   `screenshot_path`/`screenshot_sha256`; frames land under `evidence/E018/combat/` by hash.
4. Commit and push after each batch (rule 20). Never overwrite a record: a re-read writes new
   files beside the old ones and says which it cites.
5. Post the batch's per-question outcomes on PR #102, then resume T28's implementer to fill
   F020's per-claim sections and re-run the Done-when checks.

Confirm to the owner that a video is fully processed (hashes and frames taken) before they
delete anything.

## Model plays under Wine (corroboration, not replacement)

The carve-out to rule 18 (CLAUDE.md, owner 2026-10-08) permits a model agent to run the
original Pro binary under Wine on the user's machine, for the purpose of run capture and
UI observation. This section is the playbook for that path. **It is not a replacement for
the owner-plays model above.** T28's owner-driven Bandicam captures are the play-length,
game-sense, and mistake-rich record. Model-driven runs are corroboration and per-action
timing.

### What the model-driven path produces

- **Per-frame screenshots** taken on a timer, keyed to the wine window. The watcher
  attaches to the wine process, takes a screenshot of the game window (not the desktop),
  names each by wall time, hashes it, and files it into a per-sitting index.
- **Per-action memory state** (optional, behind the static-first gate in constraint B of
  rule 18). A periodic memory dump of the wine process around specific frames, where the
  Lingo reading (F014 / F019) names the state that matters.
- **A click-driver** that issues `mouseDown` events at known coordinates, for the cases
  where the static reading names the input and the question is what the game does given
  the input.

### What the model-driven path does not do

- It does not play "naturally." The model is not a player; it is a script. The owner's
  recordings carry mistakes, hesitations, and tactics; the model-driven path carries
  neither. Where the question is "what does the computer do given that the human did X",
  the owner's recording is the only source.
- It does not move the binary. The install stays at
  `/mnt/c/Users/<owner>/Downloads/Isle-Wars-Pro_Win_EN_v20-Shareware/` (or wherever
  F019 pins it), the wine prefix is on the user's machine, and the run copy, savestates,
  screenshots, recordings, and dumps stay in the same place. None of this enters the
  repository, a release, an issue, or a cloud session.
- It does not paraphrase the original's text. Per constraint D of rule 18, the text of
  the original (event names, card names, screen labels, the title "Isle Wars Pro") is
  paraphrased or quoted only in the per-claim finding, not in run records' observations
  or in the watcher's log lines.

### Per-run tagging (constraint C of rule 18)

Every model-driven run record carries:

- `runtime.platform` set to `wine-on-user-machine` (or a more specific token the task
  file names, e.g. `wine-on-user-machine-iwp-2.0`).
- `start_state.sha256` set to the F019-known `Islepro.exe` hash for the set+variant
  named in the run record. The check in `tools/check_no_originals.py` (constraint F)
  refuses the run otherwise.
- Evidence bundles with class `recording` in the evidence manifest, not `screenshot`
  of a human session.

### Bookkeeping

- The watcher, the click-driver, and the wine prefix live in a per-sitting directory on
  the user's machine, named by wall time. The repo holds only the manifest and the run
  record, both with sha256 references into that directory.
- Run records cite the wine process's `start` and `end` wall times, not the watcher's.
  Re-reads of the same wine session write new records beside the old ones and the
  finding says which it cites (rule 20).
- The model-driven run does not, by itself, answer any question. The Lingo reading is
  read first (rule 24, static first), and the question the run answers is named in the
  task file's "Why a run is made" section.

### Where to start

This section is a placeholder. The watcher, the click-driver, the per-sitting directory
layout, and the integration with `check_no_originals.py` are follow-up work, in the
order named in the rule 18 commit message: F019 hash table first, then
`check_no_originals.py` constraint F, then this section gets the concrete paths, then
the new T-number's task file. Until those are in place, the carve-out is permitted but
not operational.
