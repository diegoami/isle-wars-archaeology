# Turn sequence

Written by the main session at promotion, never by a research task. The summary describes only
`supported` and `corroborated` claims. Everything else stays in the table.

## Summary

*Isle Wars Pro*, unregistered, as read from its code: seats play in a fixed colour order, the first seat drawn at random, eliminated seats skipped (C-TRN-02); a turn is income, placement, attacks and one move (C-TRN-01); a player-turn counter gates events but is not shown (C-TRN-03).

## Claims

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-TRN-01 | A turn is: income computed, placement, then attacks and at most one move, ended by Pass, a move or a failed attack (human); the computer runs the same order in one handler chain. | supported | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-TRN-01 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F012](../findings/F012-pro-turn-victory-rules.md) |
| C-TRN-02 | Seats are numbered 1 to 4 by colour (blue, yellow, red, green), advance by one each turn with wrap, and seats with no countries are skipped; the first seat is drawn at random and shown by an animated marker. | supported | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-TRN-02 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F012](../findings/F012-pro-turn-victory-rules.md) |
| C-TRN-03 | A count of player-turns since the deal exists, used only to gate events (none in the first six player-turns); it is not shown, and there is no round counter. | supported | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-TRN-04 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F012](../findings/F012-pro-turn-victory-rules.md) |
