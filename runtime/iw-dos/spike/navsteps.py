"""The step scripts of the E005 inventory runs: what a run does after the known screen.

A script is a text file, one step per line, `#` starts a comment. It is parsed here and nowhere else,
and a line that is not exactly one of the verbs below is refused before anything is launched, so a
script can say only what a player could do with the mouse (and the few keys listed in KEYS).
Coordinates are inside the game's 640x350 window.

    click X Y            move the pointer onto X,Y, wait until the game has drawn its pointer, click
                         the left button
    rclick X Y           the same with the right button (the game uses it to confirm a choice)
    click-change X Y [S] click as `click`, and when the screen has not changed within S seconds (default 6)
                         click again, up to 3 clicks in all; the run aborts if it never changes. For a
                         click that must change the screen (a dialog, "click to continue"): the game
                         sometimes ignores a click made while it is drawing
    rclick-change X Y [S]  the same with the right button
    wait-stable          poll until two captures 0.4 s apart are equal (30 s)
    wait-change [S]      poll until the screen differs from the last wait or shot (default 20 s)
    until X Y W H R G B MIN [S]
                         poll until more than MIN pixels of the rectangle are exactly (R,G,B)
                         (default 20 s); the run aborts at the timeout, so a script never goes on
                         clicking from a screen it did not expect
    choose-attack        read the board (board.py) and remember two countries: `mine`, a Blue country
                         with an enemy neighbour, and `target`, the nearest such neighbour. The board is
                         random in every run, so a script cannot name a country; the run aborts when
                         Blue has none. The choice is recorded.
    click-mine, rclick-mine, click-target, rclick-target
                         click the number box of the remembered country (left or right button)
    shot NAME            capture the game window to NAME.png (PNG, deterministic bytes)
    files                record the run copy's added, removed and changed files since the launch
    key NAME             press and release one key of KEYS (the game is mouse-driven; this is for
                         screens that say "press any key", `c` and `e` for the shareware notices' <C>ontinue and <E>xit To Dos; never `u` (Upgrade) or `r` (Registration))
    wait-exit [S]        poll until DOSBox-X has ended by itself (the game's own way out: its last
                         screen, then the autoexec's `exit`); default 90 s. Not fatal: the run records
                         whether it ended, and the cycle stops it afterwards anyway
    savestate            DOSBox-X's own F12+S, then the savestate's members and memory are classified (I2)

The game's own screens, never this module, decide what is safe to click: a script that would reach
an order, registration or network screen must not be written (T14 Scope).
"""
import re

GAME_SIZE = (640, 350)
KEYS = ("Return", "space", "Escape", "c", "e")
NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,40}")


class Refused(ValueError):
    """A line of a script that the grammar does not allow."""


def _ints(words, count, line, lowest=0):
    try:
        values = [int(w) for w in words]
    except ValueError:
        raise Refused(f"not whole numbers: {line!r}") from None
    if len(values) != count or min(values) < lowest:
        raise Refused(f"wrong number of values: {line!r}")
    return values


def _point(x, y, line):
    if not (0 <= x < GAME_SIZE[0] and 0 <= y < GAME_SIZE[1]):
        raise Refused(f"outside the {GAME_SIZE[0]}x{GAME_SIZE[1]} window: {line!r}")


def parse(text):
    """[(verb, args)] of a script; Refused, naming the line, when any line is not allowed."""
    steps = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        verb, *words = line.split()
        if verb in ("click", "rclick"):
            x, y = _ints(words, 2, line)
            _point(x, y, line)
            steps.append((verb, (x, y)))
        elif verb in ("click-change", "rclick-change"):
            x, y, seconds = _ints(words + ([] if len(words) == 3 else ["6"]), 3, line, lowest=0)
            _point(x, y, line)
            if len(words) not in (2, 3) or seconds < 1:
                raise Refused(f"{verb} takes X Y [S]: {line!r}")
            steps.append((verb, (x, y, seconds)))
        elif verb in ("wait-stable", "files", "savestate", "choose-attack", "click-mine", "rclick-mine",
                      "click-target", "rclick-target"):
            if words:
                raise Refused(f"{verb} takes no argument: {line!r}")
            steps.append((verb, ()))
        elif verb in ("wait-change", "wait-exit"):
            (seconds,) = _ints(words or ["20" if verb == "wait-change" else "90"], 1, line, lowest=1)
            steps.append((verb, (seconds,)))
        elif verb == "until":
            if len(words) not in (8, 9):
                raise Refused(f"until takes X Y W H R G B MIN [S]: {line!r}")
            x, y, w, h, r, g, b, count, *rest = _ints(words + ([] if len(words) == 9 else ["20"]), 9, line)
            _point(x, y, line)
            _point(x + w - 1, y + h - 1, line)
            if min(w, h) < 1 or max(r, g, b) > 255 or rest[0] < 1:
                raise Refused(f"until has a bad rectangle, colour or time: {line!r}")
            steps.append((verb, ((x, y, w, h), (r, g, b), count, rest[0])))
        elif verb == "shot":
            if len(words) != 1 or not NAME.fullmatch(words[0]) or words[0] in ("before", "after"):
                raise Refused(f"shot takes one new lowercase name (a-z, 0-9, dashes): {line!r}")
            steps.append((verb, (words[0] + ".png",)))
        elif verb == "key":
            if len(words) != 1 or words[0] not in KEYS:
                raise Refused(f"key takes one of {', '.join(KEYS)}: {line!r}")
            steps.append((verb, (words[0],)))
        else:
            raise Refused(f"unknown step: {line!r}")
    chosen = False
    for verb, _ in steps:
        if verb == "choose-attack":
            chosen = True
        elif verb.endswith(("-mine", "-target")) and not chosen:
            raise Refused(f"{verb} comes before choose-attack")
    names = [args[0] for verb, args in steps if verb == "shot"]
    if len(names) != len(set(names)):
        raise Refused("two shots have the same name")
    return steps


def shot_names(steps):
    return [args[0] for verb, args in steps if verb == "shot"]
