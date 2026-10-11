# Coordinates — the proven E002 tour set

The game's stage is **800×600**. Coordinates below are stage coordinates
(stage origin at the game window's top-left). To get desktop coordinates,
add the game window's top-left position (e.g. `(1920, 0)` for the second
monitor).

Source: `experiments/E002-iwp-state-inventory/scripts/tour.steps`.

## Bottom-bar buttons (always at the same y, ~525-585)

| Action | Stage x, y | Comment |
| --- | --- | --- |
| New Game (title screen) | 100, 585 | |
| Play Game (setup screen) | 565, 532 | |
| Options (title screen) | 320, 585 | |
| EASY level | 533, 311 | |
| Continue (after loss) | 400, 526 | the Scoreboard's button (T41); the loop clicks 401, 526 |
| Scores | 620, 585 | |
| Scores → Return | 388, 516 | |
| ALL (place all armies) | 307, 543 | |
| PLACE (commit placement) | 497, 543 | |
| PLUS (+ one army on the placement counter) | 373, 543 | fix #180: centre of the grey button, x 355-391, y 529-556. Source: frame `17-1791738450340.png` of sitting 20261011T170700Z (sha256 `9a3b479b44ead6647bdefe92ebdf163e9faa62b3132af5dbe3c30b9edf6a0af8`), the panel after ALL with 4 armies to place; read by pixel extent in place on the user's machine (rule 18, carve-out A). The game's own handler is `CastScript 85 plus2` (F013 Q-REI-03): adds one, capped at the pool |
| MINUS (- one army off the counter) | 422, 543 | same frame: grey button x 404-440, y 529-556. `CastScript 87 min2`, floored at 0. Not clicked by the loop (the counter is built up from zero) |
| ATTACK (start attack) | 337, 531 | |
| QUIT ATTACK / DONE | `click-until 0 192 64 16 600 456 531 495 540` | |
| PASS (end turn) | 417, 530 | |
| CONTINUE (after card awarded) | 402, 531 (`click-any?`) | |

## The elimination notice (T38 round 4)

Source: the frames of the model-driven sitting 20261008T184505Z (batch 1), measured by pixel colour:
frame `176-1791486093693.png` (sha256
`ad5970b63f864a7c7e2ef8a958c7e4619a587833dcdf763b68eaa44b1140adf0`) and the notice frames of steps
164 to 176. The frames stay on the user's machine (rule 18, constraint A).

| Action | Stage x, y | Box (x, y ranges) | Comment |
| --- | --- | --- | --- |
| KEEP PLAYING (red) | 665, 531 | x 572–759, y 512–550 | the computers play the game out (the owner's choice, block `eliminated-keep-playing`) |
| ACCEPT LOSS? (yellow-olive) | 130, 531 | x 37–224, y 513–550 | never clicked |

New Game (100, 585) is not on this screen: the menu row is hidden while the notice is up, and during
the computers' turns.

## Screen tests (pixel counts, never OCR)

`runtime/iwp/driver/screens.py` names the screen from one stage capture, by counting the pixels of
a colour in each region and comparing the count with a minimum. Measured over all 693 frames of the
same sitting; each minimum sits between the counts on the screen and the counts everywhere else.

| Test | Region x, y, w, h | Colour | Minimum | On the screen | Elsewhere |
| --- | --- | --- | --- | --- | --- |
| notice, right button | 572, 512, 188, 39 | red | 2900 | 3897 | at most 1878 |
| notice, left button | 37, 513, 188, 38 | yellow-olive | 2500 | 4036 | at most 966 |
| notice panel | 180, 165, 410, 220 | dark navy | 18000 | 26798 | at most 10204 |
| board (score panel) | 20, 20, 195, 85 | black | 6000 | at least 11545 | 0 (title, options) |
| menu row lit | 50, 576, 100, 20 | cyan label | 200 | 382 | 0 |
| title subtitle | 180, 335, 440, 25 | cyan | 1500 | 3220 | at most 413 (board) |

`eliminated` is the board with all three notice tests; `board-menu` the board with the menu row lit
(the human's turn: New Game is on the screen); `board` the board without it; `title` the subtitle and
the menu row without the board; anything else is `unknown` (the options screen). Round 6 added
`game-over`, below.

## The winner notice (T38 round 6)

Source: the frames of the model-driven sitting 20261008T195537Z (batch 2), measured by pixel colour:
frame `182-1791490010546.png` (sha256
`14ae2f71ee90f1578a5eeaeacef626cac3167bbeebe5fcfad27708db03994761`) and the 36 winner-notice frames
of steps 177 to 186 (the first `177-1791489984799.png`). The same dark panel as the elimination
notice, the winner's sentence in the winner's colour, and one grey button in the middle of the
bottom bar. The frames stay on the user's machine (rule 18, constraint A).

| Action | Stage x, y | Box (x, y ranges) | Comment |
| --- | --- | --- | --- |
| CONTINUE (blinks: light grey 181,189,181 and green, about 144,208,128) | 401, 534 | x 327–475, y 522–546 | clicked once after the game's end is logged (block `game-over-continue`); the blink is measured on sitting 20261009T160556Z (fix #141 round 2) |

The CONTINUE of a card award (402, 531 above) is a smaller grey button in the same place, shown
without the notice panel.

| Test | Region x, y, w, h | Colour | Minimum | On the screen | Elsewhere |
| --- | --- | --- | --- | --- | --- |
| winner notice, CONTINUE (grey phase) | 327, 522, 149, 25 | light grey | 2200 | 2958 | at most 1603 (a card award's CONTINUE) |
| winner notice, CONTINUE (green phase, `continue-green`) | 327, 522, 149, 25 | green (about 144,208,128; g − r > 24 and g − b > 24) | 1300 | about 1760 (census bins 1209 + 302 + 249, sitting 20261009T160556Z, fix #141 round 2) | 0 for the grey phase (its green spread is at most 15) |
| notice panel (as above) | 180, 165, 410, 220 | dark navy | 18000 | 27935 | at most 3901 where a card award's CONTINUE shows |

`game-over` is the board with the notice panel and CONTINUE, and neither the KEEP PLAYING nor the
ACCEPT LOSS? test. Over all 1179 frames of the two sittings (693 and 486), it matches the 36 winner
frames and nothing else, and every other frame keeps its round 4 name: sitting 20261008T184505Z
board 332, board-menu 201, eliminated 156, unknown 3, title 1; sitting 20261008T195537Z board 315,
board-menu 128, game-over 36, eliminated 3, unknown 3, title 1 (the 36 were read `board` before).

### The winner's seat (score panel, pixels, never OCR)

Each seat's number after its name, x 107–137, in the seat's own colour (as measured: blue
49,156,255, yellow 255,255,0, red 255,49,49, green 0,206,49).

| Seat | Region x, y, w, h | Winner frames |
| --- | --- | --- |
| blue | 107, 24, 31, 14 | 61 (its 0) |
| yellow | 107, 45, 31, 14 | 58 (its 0) |
| red | 107, 66, 31, 14 | 130 (its 46) |
| green | 107, 86, 31, 14 | 67 (its 0) |

The winner is the one seat at 100 pixels or more, read only on the winner notice (`winner_of`; None
when no seat or more than one reaches it). On all 36 winner frames it reads `red`, as the notice's
sentence and colour say; on every other frame it answers None.

## The Scoreboard (T41)

Source: the frames of the model-driven sitting 20261008T204817Z (batch 3), measured by pixel colour:
frame `368-1791494104472.png` (sha256 `f1b58aaf6dd827008cfa07513fa38bab8a7a1e0c3ab12d529a6b6695125df2c6`)
and the other 6 frames of steps 367 and 368 (`367-1791494095432.png`, sha256
`33e1dc20b35f6980ca6b137431d2aea3247ff30aebd436e4dbce7eb0c399875e`), 7 in all. The sitting sent New Game
from the board of a live game at its 30-turn cap, with the human holding fewer than 10 countries: the game
credited a loss, wrote its scoreboard file (F003) and showed this screen. A framed panel over the ocean
backdrop with a table of the three levels, a black box with the percentage at the end of each row, and one
grey CONTINUE button in the bottom bar; no board behind it. The frames stay on the user's machine
(rule 18, constraint A).

| Action | Stage x, y | Box (x, y ranges) | Comment |
| --- | --- | --- | --- |
| CONTINUE (light grey, 181,189,181) | 401, 526 | x 327-474, y 514-538 | clicked once, after the loop logs `loss-credited` (block `scoreboard-continue`); higher than the winner notice's (401, 534) |

E002's "Continue (after loss)" is 400, 526 (above), the same button. The title's Scores screen, which the loop
never opens, has a Return button near 388, 516 instead and was not measured.

| Test | Region x, y, w, h | Colour | Minimum | On the screen | Elsewhere |
| --- | --- | --- | --- | --- | --- |
| button, top rows | 327, 514, 149, 8 | light grey | 720 | 1079 | at most 368 |
| percentage box, Easy | 537, 230, 85, 28 | black | 1500 | 1969 | at most 1 |
| percentage box, Normal | 537, 302, 85, 28 | black | 1500 | 1969 | at most 130 |
| percentage box, Hard | 537, 376, 85, 28 | black | 1500 | 1969 | at most 59 |

`scoreboard` is the screen with all four tests and no board (no score panel), and is not the title; it is
named before the title (#141): over these frames no other reaches even half of any of the four minima, so a
frame that trips all four is the Scoreboard whatever the subtitle and menu rows show, and a real title,
which never trips them, keeps its name. (Before #141 it was tried after the title, and a frame with the four
signals and the title's subtitle and menu then read `title` — the name New Game is sent on.) The top rows of
the button (y 514-521) are what the
winner notice's button (y 522-546) never reaches. Over all 2267 frames of the three sittings (693, 486 and
1088), `experiments/E020-wine-first-run/check_screens.py` reads the 7 frames of steps 367 and 368 as
`scoreboard` and every other frame as before: sitting 20261008T184505Z board 332, board-menu 201,
eliminated 156, unknown 3, title 1; sitting 20261008T195537Z board 315, board-menu 128, game-over 36,
eliminated 3, unknown 3, title 1; sitting 20261008T204817Z board 685, board-menu 392, scoreboard 7,
unknown 3, title 1. (The 3 `unknown` frames of each sitting are the options screen of steps 5 to 9, unchanged.)

## The 46 country positions (for `attack-picked` and the placement `click-until`)

These are the center-of-country pixel coordinates, extracted from the E002
tour. The `attack-picked` step takes a list of (x, y) pairs and attacks the
first one the game accepts as a valid target from the currently-selected
source country.

```
55 193, 49 261, 42 330, 105 441, 142 385, 153 433, 188 399, 235 441, 239 282, 178 283, 132 238, 139 166, 277 177, 358 60, 344 110, 307 160, 390 163, 393 98, 473 139, 440 190, 509 223, 566 143, 525 89, 593 86, 682 99, 760 129, 685 153, 746 196, 668 211, 748 264, 655 282, 750 411, 698 436, 639 446, 515 404, 521 343, 454 363, 448 444, 372 453, 377 410, 308 425, 333 305, 412 294, 321 262
```

That's 46 pairs. The `attack-picked` step will try them in order and
pick the first one the game accepts.

## Stage sizes used

- Board area: `watch 0 0 800 495` (the top 495 pixels of the 800×600 stage).
- Turn menu / buttons: bottom 105 pixels of the stage.
- Placement frame: `watch 265 530 270 26` and `watch 262 502 276 70` (the "ALL" and "PLACE" button rows; the
  panel also holds the + and - buttons, the counter above them, and the pool's armies in the bottom bar).
- Battle result: `watch 545 502 250 70` (the ATTACK result row).

## Converting stage to desktop

If `set_window_pos` put the game window at desktop `(X, Y)`, then a stage
click at `(sx, sy)` is a desktop click at `(X + sx, Y + sy)`. The
`iwp_client.click(x, y)` takes desktop coordinates. The translation is the
main session's job (it knows the window position from the
`find_window` response).
