#!/usr/bin/env python3
"""pred.py menu|dialog: read an 800x600 RGB8 root capture on stdin (the 640x350 window at 80,100)
and exit 0 when the screen shows the option box (menu) or the Select level dialog (dialog)."""
import sys

W, OX, OY = 800, 80, 100
data = sys.stdin.buffer.read()


def count(x, y, w, h, colour):
    n = 0
    for j in range(y, y + h):
        for i in range(x, x + w):
            k = ((j + OY) * W + i + OX) * 3
            n += tuple(data[k:k + 3]) == colour
    return n


if len(data) != W * 600 * 3:
    sys.exit(2)
if sys.argv[1] == "menu":
    ok = count(28, 22, 66, 18, (170, 0, 0)) > 150 and count(108, 46, 52, 22, (85, 255, 255)) > 250
else:
    ok = count(272, 138, 80, 18, (170, 85, 0)) > 800
sys.exit(0 if ok else 1)
