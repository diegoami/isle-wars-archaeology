"""Step scripts for the E002 cycle (W4a): a short list of inputs and observations the driver runs
between the known screen and the end of a run.

A script is a text file, one step per line; blank lines and `#` comments are ignored. This module only
parses and checks; `cycle.py` runs the steps. Nothing here touches the game.

    settle                  wait until the watched area is unchanged between two captures (a poll, never a time)
    watch X Y W H           from now on `settle` and the change check of `click` look at this rectangle only
                            (a blinking arrow on the board keeps the full screen changing); `watch all` undoes it
    move X Y                put the pointer there
    click X Y               move there, wait for the label under the pointer to react, click; the
                            observation says whether the screen changed
    click! X Y              the same, and the run aborts when the screen did not change
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
    if op in ("settle", "title", "proc", "changes"):
        if args:
            raise StepError(f"{op} takes no argument")
        return Step(op, (), number)
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
