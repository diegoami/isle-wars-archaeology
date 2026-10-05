# Ownership change

Written by the main session at promotion, never by a research task. The summary describes only
`supported` and `corroborated` claims. Everything else stays in the table.

## Summary

*Isle Wars Pro*, unregistered, as read from its code: a captured country changes hands at once; the human moves armies in, and the computer splits them automatically (C-OWN-01).

## Claims

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-OWN-01 | On a human capture the country changes hands at once and the human moves in 1 up to the attacker's armies minus 1 (whether 0 can be chosen is open); on a computer capture the split is automatic, at least 1 in each country, and conserves the total before each stack is clipped to 999 (armies are lost only when a stack would exceed 999). | supported, narrowed: computer conservation before per-stack clipping; the human zero-placement question depends on the score | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-OWN-01 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F011](../findings/F011-pro-combat-rules.md) |
