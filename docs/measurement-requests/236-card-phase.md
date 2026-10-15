# Measurement request: Q-UI-15 card phase

This request is repository-only. No original assets or machine-local frames belong in the
repository, issue, or PR. The requested frames remain on the main session's machine and are
reported by hash and provenance.

## Why the current evidence is insufficient

`runtime/iwp/driver/screens.py` measures `board-menu` (the menu row is lit) and `board` (the
menu row is not lit). It also measures the winner notice's CONTINUE phases. It does **not** identify
the smaller card-award CONTINUE, and `settle 4` only establishes that the watched pixels stayed
unchanged. Therefore neither mechanism can safely distinguish a card award from a quiet computer
phase, and a centre-strip change cannot identify either phase.

## Required local measurement

Capture a new Q-UI-15 card-path probe on the supported 800x600x24 unregistered build, preserving
the original capture bundle locally. The probe must include, in order, and with no CONTINUE click
before the required frames:

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
