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
