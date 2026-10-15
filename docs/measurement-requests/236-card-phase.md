# Measurement request: Q-UI-15 card phase

This request is repository-only. No original assets or machine-local frames belong in the
repository, issue, or PR. The requested frames remain on the main session's machine and are
reported by hash and provenance.

## Supplied evidence and bounded result

The main session supplied an immutable census at
`experiments/E019-pro-ui/measurements/236-card-phase-census.json`, with its path-independent
reproduction script beside it. It contains 136 frames from the preserved E002/E019 local bundles,
counted with the existing measured screen predicates at 800x600x24. The positive visual reading is
the settled-before-CONTINUE frame from `E019-r0030` and its identical after frame: two files, one
unique positive raw RGB8 frame, SHA-256
`16a84dc21a66a6cbb12f52302133bd3963bf5819b66d9b0c5903b55432ee6776`. The positive population has
1878 green CONTINUE pixels, 386 grey CONTINUE pixels, 4034 notice-panel pixels, 12021 score-panel
pixels, and no menu pixels. The other 134 frames have at most 37 green CONTINUE pixels and are the
bounded negative population; this is not a universal claim about every possible game frame.

The evidence supports only a conservative green-prompt probe that reuses the existing
`continue-green` minimum of 1300 and the existing score-panel, notice-button, and menu predicates.
The grey award phase has not been measured and remains unsupported. Candidate screenshots therefore
remain unidentified evidence for the catalogue; no semantic award claim is made by the recorder.

## Why the original evidence was insufficient

`runtime/iwp/driver/screens.py` measures `board-menu` (the menu row is lit) and `board` (the
menu row is not lit). It also measures the winner notice's CONTINUE phases. It does **not** identify
the smaller card-award CONTINUE, and `settle 4` only establishes that the watched pixels stayed
unchanged. Therefore neither mechanism can safely distinguish a card award from a quiet computer
phase, and a centre-strip change cannot identify either phase.

## Required follow-up measurement, if broader coverage is needed

If a universal grey/green card-phase detector or broader claim is needed, capture an additional
Q-UI-15 card-path probe on the supported 800x600x24 unregistered build, preserving the original
capture bundle locally. The probe must include, in order, and with no CONTINUE click before the
required frames:

1. a completed human placement/attack/pass that enters the computer phase;
2. at least one frame while the computer phase is active and one frame after it becomes human-ready;
3. a capture-turn path that reaches the card-award prompt, with several consecutive frames before
   CONTINUE; and
4. a no-award pass path, with several consecutive frames before any next-turn input.

For every frame, record the raw-pixel SHA-256, run id, step/action, display size, and the exact
local source/provenance. Supply measured positive and negative populations for any proposed
detector region or threshold: card-award frames, human-ready `board-menu` frames, computer-phase
`board` frames, and other nearby board states. The requested detector must have no overlap in
those populations, or the repair must remain conservative and stop/report an unsupported state.

Do not use OCR, guessed coordinates, arbitrary sleeps, generic pixel changes, or a semantic label
such as “award” derived only from stability. No implementation should be added until these local
measurements establish the gate.
