# Movement

Written by the main session at promotion, never by a research task. The summary describes only
`supported` and `corroborated` claims. Everything else stays in the table.

## Summary

*Isle Wars Pro*, unregistered, as read from its code: one move per turn, which ends the turn, between directly bordering countries, always leaving at least one army behind (C-MOV-01 to C-MOV-03).

## Claims

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-MOV-01 | A player makes at most one move per turn, and the move ends the turn; the computer moves once, at the end of its turn, by a hard-coded selection policy with random and army-count-based choices. | supported, narrowed: the human's turn-ending sequence depends on the undecoded score | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-MOV-01 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F011](../findings/F011-pro-combat-rules.md) |
| C-MOV-02 | At least one army stays in the source: all but one is the most that can move, and a 1-army country cannot be a source; the computer always moves all but one. | supported, narrowed: under the described controls; the button assignment is unverified | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-MOV-02 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F011](../findings/F011-pro-combat-rules.md) |
| C-MOV-03 | The destination must border the source directly; a just-captured country is not flagged, so it may attack on the same turn. | supported, narrowed: onward attacks depend on the score | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-MOV-03 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F011](../findings/F011-pro-combat-rules.md) |
