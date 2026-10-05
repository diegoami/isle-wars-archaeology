"""The step scripts of the E005 inventory runs: what a run does after the known screen.

A script is a text file, one step per line, `#` starts a comment. It is parsed here and nowhere else,
and a line that is not exactly one of the verbs below is refused before anything is launched, so a
script can say only what a player could do with the mouse (and the few keys listed in KEYS).
Coordinates are inside the game's 640x350 window.

    click X Y            move the pointer onto X,Y, wait until the screen is still, click the left button
    rclick X Y           the same with the right button (the game uses it to confirm a choice)
    click-change X Y [S] click as `click`, and when the screen has not changed within S seconds (default 6)
                         click again, up to 3 clicks in all; the run aborts if it never changes, or if it
                         is not still within 30 s after the change. For a click that must change the
                         screen (a dialog, "click to continue"): in some runs a first click was not
                         followed by a change and a second one was (r0033's Save; why is not known)
    rclick-change X Y [S]  the same with the right button
    click-until X Y RX RY RW RH R G B MIN [N]
                         click X,Y, wait up to 3 s for more than MIN pixels of (R,G,B) in the
                         rectangle RX,RY,RW,RH, and click again if they are not there; at most N clicks
                         (default 12), then the run aborts. For a button that may need more than one
                         click before the expected panel shows (ATTACK needed two in r0011 and r0012;
                         what one click does in the game is not established here)
    wait-stable          poll until two captures 0.4 s apart are equal; the run aborts after 30 s
    wait-change [S]      poll until the screen differs from the last wait or shot; the run aborts after
                         S seconds (default 20)
    until X Y W H R G B MIN [S]
                         poll until more than MIN pixels of the rectangle are exactly (R,G,B)
                         (default 20 s); the run aborts at the timeout, so a script never goes on
                         clicking from a screen it did not expect
    choose-attack        read the board (board.py) and remember two countries: `mine`, a Blue country
                         with an enemy neighbour, and `target`, the nearest such neighbour. The board
                         differs between runs, so a script cannot name a country; the run aborts when
                         Blue has none. The choice is recorded.
    click-mine, rclick-mine, click-target, rclick-target
                         click the number box of the remembered country (left or right button), as click-change does
    shot NAME            capture the game window to NAME.png (PNG, deterministic bytes)
    files                record the run copy's added, removed and changed files since the launch
    key NAME             press and release one key of KEYS (the game is mouse-driven; this is for
                         screens that say "press any key", `c` and `e` for the shareware notices' <C>ontinue and <E>xit To Dos; never `u` (Upgrade) or `r` (Registration))
    wait-exit [S]        poll until DOSBox-X has ended by itself (the game's own way out: its last
                         screen, then the autoexec's `exit`); the run aborts after S seconds (default 90)
    savestate            DOSBox-X's own F12+S, then the savestate's members and memory are classified (I2)
    put-save             write the crafted save (the cycle's --crafted position, encoded by runtime/iw-dos/save/) into
                         the run copy as ISLEWAR.SAV, while the game waits at its option box; the file is a new file of
                         the run copy and the reset removes it. An I3 intervention (a crafted save), declared in the
                         record. Allowed once, and only when the run has --crafted (the cycle checks both)

Every wait is required: a wait that times out aborts the run, so it is never completed past a screen
it did not see (PR #58 R7). The one poll that does not abort is the "pointer drawn" observation inside
a click: the pointer may already be where it is moved to, and the click that follows is checked by its
own verb (click-change, click-until) or by the next wait.

Forbidden controls (T14 Scope: never a click that would order, register or reach a network). The game's
shareware notices, shown when a game ends and Another game is answered No, draw two buttons in the same
place on both notices: <C>ontinue and <U>pgrade on the first, <R>egistration and <E>xit To Dos on the
second (E005-r0021 `shareware-notice.png` and `registration-notice.png`, file sha256 06d117310d84e114...
and ceedcdec94c8beb7..., and every other capture of the notices: `measurements/round1/constants-20261005T112209Z/notice-scan.tsv`).
Their outer frames, colour (255, 85, 85), span x 287..416 and 439..568, y 291..315 on both. FORBIDDEN is
that band, the gap between the buttons included, widened by 4 pixels on every side: the margin is a
design choice, not a measurement of the game's own hit area (not looked for: no code is read, T14 Scope);
the nearest point any E005 script clicks on another screen is y 323, 8 pixels below the frame. A click
verb (CLICK_VERBS) whose point is in it is refused here, before anything is launched; the cycle refuses it
again at the click itself (it is where every click verb, and click-mine and its kind, end), and refuses
any click and any key but `c` and `e` while the notices are on the screen (cycle.py, NOTICE_FRAME).
"""
import re

GAME_SIZE = (640, 350)
KEYS = ("Return", "space", "Escape", "c", "e")
NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,40}")
FORBIDDEN = ((283, 287, 290, 33),)    # x, y, w, h: both notice buttons and the gap, widened by 4 (see above)
CLICK_VERBS = ("click", "rclick", "click-change", "rclick-change", "click-until")   # verbs whose first two values are a click point


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


def forbidden(x, y):
    """True when the point x, y of the game window is on a forbidden control (FORBIDDEN)."""
    return any(rx <= x < rx + rw and ry <= y < ry + rh for rx, ry, rw, rh in FORBIDDEN)


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
        elif verb == "click-until":
            if len(words) not in (10, 11):
                raise Refused(f"click-until takes X Y RX RY RW RH R G B MIN [N]: {line!r}")
            x, y, rx, ry, rw, rh, r, g, b, count, tries = _ints(words + ([] if len(words) == 11 else ["12"]), 11, line)
            _point(x, y, line)
            _point(rx, ry, line)
            _point(rx + rw - 1, ry + rh - 1, line)
            if min(rw, rh) < 1 or max(r, g, b) > 255 or tries < 1:
                raise Refused(f"click-until has a bad rectangle, colour or count: {line!r}")
            steps.append((verb, (x, y, (rx, ry, rw, rh), (r, g, b), count, tries)))
        elif verb in ("click-change", "rclick-change"):
            x, y, seconds = _ints(words + ([] if len(words) == 3 else ["6"]), 3, line, lowest=0)
            _point(x, y, line)
            if len(words) not in (2, 3) or seconds < 1:
                raise Refused(f"{verb} takes X Y [S]: {line!r}")
            steps.append((verb, (x, y, seconds)))
        elif verb in ("wait-stable", "files", "savestate", "put-save", "choose-attack", "click-mine", "rclick-mine",
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
    for verb, args in steps:
        if verb in CLICK_VERBS and forbidden(args[0], args[1]):
            raise Refused(f"{verb} at {args[0]},{args[1]} is on the shareware notices' buttons (Upgrade, Registration): "
                          "never clicked")
    chosen = False
    for verb, _ in steps:
        if verb == "choose-attack":
            chosen = True
        elif verb.endswith(("-mine", "-target")) and not chosen:
            raise Refused(f"{verb} comes before choose-attack")
    if sum(1 for verb, _ in steps if verb == "put-save") > 1:
        raise Refused("put-save is allowed once in a script")
    names = [args[0] for verb, args in steps if verb == "shot"]
    if len(names) != len(set(names)):
        raise Refused("two shots have the same name")
    return steps


def shot_names(steps):
    return [args[0] for verb, args in steps if verb == "shot"]
