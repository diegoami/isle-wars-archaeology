# Surrender

Written by the main session at promotion, never by a research task. The summary describes only
`supported` and `corroborated` claims. Everything else stays in the table.

## Summary

*Isle Wars Pro*, unregistered, as read from its code: the computers concede together to a single human seat holding 33 or more countries, once per game (C-SUR-01, C-SUR-02); a human leaves through the new-game button, which records a loss at 1 to 9 countries for three of the four colours (C-SUR-03).

## Claims

| ID | Claim | Status | Scope | Basis | Findings |
| --- | --- | --- | --- | --- | --- |
| C-SUR-01 | The computers concede collectively to the only human seat when it holds 33 or more of 46 countries, checked once per turn transition, by country count alone (no army or income share). | supported | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-SUR-01, Q-SUR-03 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F012](../findings/F012-pro-turn-victory-rules.md) |
| C-SUR-02 | Accepting ends the game at once as a scored win; refusing returns to play and bans the offer for the rest of the game, with no other cost. | supported | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-SUR-04 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F012](../findings/F012-pro-turn-victory-rules.md) |
| C-SUR-03 | There is no resign control; leaving through the new-game button records a loss at 1 to 9 countries for the blue, yellow and red seats and nothing at 10 or more or at 0, unless the quit-early flag is already set (after the elimination prompt). The green seat's branch stores into a local instead of that flag, so a green human leaving with 1 to 9 countries is not charged a loss (read as a slip in the original's code, about 80%). | supported, narrowed: the green-seat exception | Pro, set `iwp-2.0-996e86c5`, unregistered; a static reading of ProjectorRays 0.2.0 output (V0), not yet corroborated by play (T28); Q-SUR-05; narrowed in review rounds 1 and 2 | static:decompile (`Islepro.exe` sha256 `c4d7a248…`) | [F012](../findings/F012-pro-turn-victory-rules.md) |
