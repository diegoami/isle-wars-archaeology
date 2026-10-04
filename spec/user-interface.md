# User interface

Written by the main session at promotion, never by a research task. The summary describes only
`supported` and `corroborated` claims. Everything else stays in the table.

## Summary

*Isle Wars Pro*, unregistered 2.0 under Wine: the game state of a turn (owners, army counts, whose
turn and phase, cards, an attack's result) is shown on the screen, and every screen of F003's
inventory but the end of a game was reached (C-UI-01). Timing and rendering need V3 (U8) and are not
claimed.

## Claims

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-UI-01 | The screens show the territory owners, the army counts, whose turn it is, the phase, the cards and the result of an attack. Reached: Title, Options (with its locked-control message), New Game setup, the board at the start of a game, a human turn's placing and attack, the turn menu (Attack, MOVE, PASS, CARD, Cancel), a computer turn passing, Help (12 pages), Scores (with a Reset Scores button), the loss notice, and the unregistered notice on quitting. An attack shows the army counts before and after, not the dice. Not reached: the end of a game and the registered-only screens. That the screen is the only place the game holds the position is not shown. | supported | Pro, set `iwp-2.0-de5a82a2`, unregistered; Wine 9.0, headless (V2); E002's screens | observed | [F003](../findings/F003-iwp-observable-state-inventory.md) |
