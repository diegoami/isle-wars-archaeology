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
| Continue (after loss) | 400, 526 | |
| Scores | 620, 585 | |
| Scores → Return | 388, 516 | |
| ALL (place all armies) | 307, 543 | |
| PLACE (commit placement) | 497, 543 | |
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
the menu row without the board; anything else is `unknown` (the options screen, and the game-over
screen, not measured yet).

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
- Placement frame: `watch 265 530 270 26` and `watch 262 502 276 70` (the "ALL" and "PLACE" button rows).
- Battle result: `watch 545 502 250 70` (the ATTACK result row).

## Converting stage to desktop

If `set_window_pos` put the game window at desktop `(X, Y)`, then a stage
click at `(sx, sy)` is a desktop click at `(X + sx, Y + sy)`. The
`iwp_client.click(x, y)` takes desktop coordinates. The translation is the
main session's job (it knows the window position from the
`find_window` response).
