"""Step scripts for the E002 cycle (W4a): a short list of inputs and observations the driver runs
between the known screen and the end of a run.

A script is a text file, one step per line; blank lines and `#` comments are ignored. This module only
parses and checks; `cycle.py` runs the steps. Nothing here touches the game.

    settle [SECONDS]        wait until the watched area is unchanged between two captures, or, with SECONDS,
                            has stayed unchanged for that long (a poll on the screen, never a fixed time)
    watch X Y W H           from now on `settle` and the change check of `click` look at this rectangle only
                            (a blinking arrow on the board keeps the full screen changing); `watch all` undoes it
    move X Y                put the pointer there
    click X Y               move there, wait for the label under the pointer to react, click; the
                            observation says whether the screen changed
    click! X Y              the same, and the run aborts when the screen did not change
    attack-picked X Y [X Y ...]
                            from the point that the last click-any/click-until picked, attack the first of
                            these countries that the game accepts as a target and accepts that point as the
                            attacker of (the ATTACK / QUIT ATTACK panel is up); the run aborts when none is.
                            Starts from the turn menu and leaves the panel up
    clicks N X Y            move there, wait for the label to react, then click N times, 80 ms apart (N from 2 to 60;
                            one line of text scrolls per click on a scrollbar arrow)
    click-any X Y [X Y ...]     click the points in order and stop at the first after which the watched area
                            changed; the run aborts when none did (a click the game ignores changes nothing).
                            `click-any?` is the same, and a failure is only noted
    click-until R G B TOL N X Y [X Y ...]
                            click the points in order and stop at the first after which at least N pixels of
                            the watched area are within TOL (per channel) of the colour R G B; the run aborts
                            when none is. `click-until?` is the same, and a failure is only noted
    key NAME                press one key (a short allow-list: Return, Escape, space, Tab, arrows, F1 to
                            F12, one letter or digit); never `$`, which opens the registration screen
    shot NAME               one screenshot, kept as NAME.png in the run's bundle
    title                   the game window's title, read from the window manager
    proc                    the game process's thread count and resident memory, read from /proc
    file PATH               one file of the game copy: size, sha256, and whether it equals the install's file.
                            When the game changed it: the changed byte offsets (old and new value) and, if it
                            has at most 64 bytes, its bytes in hex. A file the game did not change is never
                            dumped. PATH is relative to the game copy.
    changes                 which files of the game copy and the prefix differ now from the start of the run

Coordinates are the 800x600 stage's. Clicks inside a forbidden rectangle are refused when the script
is parsed and again when the click is sent.
"""
import re
from collections import namedtuple

STAGE = (800, 600)
Step = namedtuple("Step", "op args line")

# Rectangles x, y, w, h that no click may touch, whatever screen is showing. Each is a control that
# opens the publisher's site or an order page (T09 hazards). The title screen's bottom bar holds the
# "Soleau Games" label; more are added as screens are seen.
FORBIDDEN = {
    "Soleau Games label on the title screen": (405, 568, 135, 32),
}

KEYS = {"Return", "Escape", "space", "Tab", "Up", "Down", "Left", "Right", "BackSpace", "Delete",
        "Home", "End", "Prior", "Next"} | {f"F{n}" for n in range(1, 13)} | set("abcdefghijklmnopqrstuvwxyz0123456789")
NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,40}")
FILE_PART = re.compile(r"[A-Za-z0-9._-]{1,100}")


class StepError(ValueError):
    """A step that is not allowed or not understood."""


def forbidden(x, y):
    """The name of the forbidden rectangle containing the point, or None."""
    for name, (rx, ry, rw, rh) in FORBIDDEN.items():
        if rx <= x < rx + rw and ry <= y < ry + rh:
            return name
    return None


def _point(args, op):
    if len(args) != 2 or not all(a.lstrip("-").isdigit() for a in args):
        raise StepError(f"{op} takes X Y")
    x, y = int(args[0]), int(args[1])
    if not (0 <= x < STAGE[0] and 0 <= y < STAGE[1]):
        raise StepError(f"{op} {x} {y} is outside the {STAGE[0]}x{STAGE[1]} stage")
    hit = forbidden(x, y)
    if hit:
        raise StepError(f"{op} {x} {y} is inside a forbidden area: {hit}")
    return (x, y)


def parse_line(text, number=0):
    """One Step from one line, or StepError. Returns None for a blank line or a comment."""
    text = text.split("#", 1)[0].strip()
    if not text:
        return None
    words = text.split()
    op, args = words[0], words[1:]
    if op in ("title", "proc", "changes"):
        if args:
            raise StepError(f"{op} takes no argument")
        return Step(op, (), number)
    if op == "settle":
        if len(args) > 1 or (args and not args[0].isdigit()) or (args and not 1 <= int(args[0]) <= 60):
            raise StepError("settle takes no argument, or a number of seconds from 1 to 60")
        return Step(op, tuple(int(a) for a in args), number)
    if op == "attack-picked":
        if not args or len(args) % 2:
            raise StepError("attack-picked takes pairs X Y")
        return Step(op, tuple(v for i in range(0, len(args), 2) for v in _point(args[i:i + 2], op)), number)
    if op == "clicks":
        if len(args) != 3 or not args[0].isdigit() or not 2 <= int(args[0]) <= 60:
            raise StepError("clicks takes N X Y, with N from 2 to 60")
        return Step(op, (int(args[0]),) + _point(args[1:], op), number)
    if op in ("click-any", "click-any?"):
        if not args or len(args) % 2:
            raise StepError(f"{op} takes pairs X Y")
        return Step(op, tuple(v for i in range(0, len(args), 2) for v in _point(args[i:i + 2], op)), number)
    if op in ("click-until", "click-until?"):
        if len(args) < 7 or (len(args) - 5) % 2 or not all(a.isdigit() for a in args[:5]):
            raise StepError("click-until takes R G B TOL N, then pairs X Y")
        r, g, b, tol, n = (int(a) for a in args[:5])
        if max(r, g, b) > 255 or tol > 255 or n < 1:
            raise StepError("click-until: colour channels 0-255, TOL 0-255, N at least 1")
        points = tuple(v for i in range(5, len(args), 2) for v in _point(args[i:i + 2], op))
        return Step(op, (r, g, b, tol, n) + points, number)
    if op == "watch":
        if args == ["all"]:
            return Step(op, (), number)
        if len(args) != 4 or not all(a.isdigit() for a in args):
            raise StepError("watch takes X Y W H, or `all`")
        x, y, w, h = (int(a) for a in args)
        if w < 1 or h < 1 or x + w > STAGE[0] or y + h > STAGE[1]:
            raise StepError("watch rectangle is outside the stage")
        return Step(op, (x, y, w, h), number)
    if op in ("move", "click", "click!"):
        return Step(op, _point(args, op), number)
    if op == "key":
        if len(args) != 1 or args[0] not in KEYS:
            raise StepError("key takes one name from the allow-list (Return, Escape, space, Tab, arrows, F1-F12, a letter or digit)")
        return Step(op, (args[0],), number)
    if op == "shot":
        if len(args) != 1 or not NAME.fullmatch(args[0]):
            raise StepError("shot takes one name: lowercase letters, digits and dashes")
        return Step(op, (args[0],), number)
    if op == "file":
        if len(args) != 1:
            raise StepError("file takes one path")
        parts = args[0].split("/")
        if args[0].startswith("/") or any(p in ("", ".", "..") or not FILE_PART.fullmatch(p) for p in parts):
            raise StepError("file takes a plain relative path inside the game copy")
        return Step(op, (args[0],), number)
    raise StepError(f"unknown step {op!r}")


def parse(text):
    """The list of Steps in a script; StepError names the first bad line."""
    steps = []
    for number, line in enumerate(text.splitlines(), start=1):
        try:
            step = parse_line(line, number)
        except StepError as exc:
            raise StepError(f"line {number}: {exc}") from None
        if step:
            steps.append(step)
    return steps
