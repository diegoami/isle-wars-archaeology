# Seats and players

Written by the main session at promotion, never by a research task. The summary describes only
`supported` and `corroborated` claims. Everything else stays in the table.

## Summary

*Isle Wars Pro*, unregistered, as read from its code: the table is four seats; the board is fixed and does not change the player count (C-PLY-01, C-PLY-03). In the unregistered build, the seat toggles are locked to a single human seat (seat 1) and three computer seats (seats 2–4): no several-human hot-seat play, no all-computer; the gate sits in the option handlers and exits before any seat-changing logic, and the registered build's hot-seat construction is `unknown` (C-PLY-02). The default seat configuration of a new game is exactly this: one human seat and three computer seats, with the deal's seat-fill algorithm run against the registered list (C-PLY-03).

## Claims

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-PLY-01 | The table has four seats. The board is fixed (46 countries, 9 islands) and does not change the player count. | supported, narrowed: registered-build changes (e.g. fewer seats via registration) are explicitly unknown | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-PLY-01 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F019](../findings/F019-pro-setup-rules.md) |
| C-PLY-02 | In the unregistered build, the seat toggles are locked to a single human seat and three computer seats — no several-human play, no all-computer play. The gate sits in the seat option handler and exits before any seat-changing logic. Registered-build hot-seat construction is `unknown`. | supported, narrowed: registered hot-seat behaviour is explicitly unknown; the rest of the registration check is read in full in C-SET-02 | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-PLY-02 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F019](../findings/F019-pro-setup-rules.md) |
| C-PLY-03 | The default seat configuration of a new game is one human seat and three computer seats, set by the unregistered forcing and confirmed by the startup options handler. The deal's seat-fill algorithm then runs against the registered list. | supported, narrowed: loading does not preclude a foreign seat layout on disk; the loaded in-memory seats are forced unregistered. | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-PLY-03 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F019](../findings/F019-pro-setup-rules.md) |
