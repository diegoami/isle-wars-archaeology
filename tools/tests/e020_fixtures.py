"""Synthetic E020 sittings and records for T38's tests: no wine, no display, no original bytes.

`make_sitting(root, sid, ...)` writes a sitting directory as the launcher would leave it: two
synthetic frames indexed by sha256, the click-driver's game-start lines, sitting.json with a
measured binary equal to the F019 row's hash, and the readings given."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _sub in ("tools", "runtime/iwp", "setup/iwp", "experiments/E020-wine-first-run"):
    if str(ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(ROOT / _sub))

F019_SHA = "c4d7a248646454adeb48232e3ac7b3d2c0f08b290051a79d6fe6e47bb76b594e"
TABLE = [{"set": "iwp-2.0-996e86c5", "variant": "unregistered", "file": "Islepro.exe", "sha256": F019_SHA}]
SID = "20261008T120000Z"
EXCHANGE = {"counter:attacker-before": "5", "counter:attacker-after": "4", "counter:defender-before": "1",
            "counter:defender-after": "1", "country:attacker": "12", "country:defender": "13",
            "owner:attacker": "red", "owner:defender": "green"}
BOMB = {"owner:bomber": "red", "owner:victim": "blue", "country:victim": "7", "counter:victim-before": "6",
        "counter:victim-after": "3", "hand:bomber": "4"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def make_sitting(root, sid=SID, batch="cmb-accumulation", status="completed", games=(1,), readings=(),
                 frames=(b"synthetic frame one", b"synthetic frame two"), doc_changes=None):
    sitting = Path(root) / sid
    (sitting / "frames").mkdir(parents=True)
    (sitting / "session").mkdir()
    index, digests = [], []
    for i, data in enumerate(frames, start=1):
        name = f"{i}-{1700000000000 + i}.png"
        (sitting / "frames" / name).write_bytes(data)
        index.append({"name": name, "sha256": sha(data), "wall_time": "2026-10-08T12:00:0%dZ" % i,
                      "window": "0x2a", "geometry": {}})
        digests.append(sha(data))
    (sitting / "frames-index.jsonl").write_text("".join(json.dumps(l) + "\n" for l in index))
    (sitting / "actions.jsonl").write_text("".join(json.dumps({"seq": g, "game": g, "turn": 0, "event": "game-start"}) + "\n"
                                                   for g in games))
    lines = []
    for r in readings:
        r = dict(r)
        r.setdefault("frames", digests[:2])
        lines.append(json.dumps(r) + "\n")
    if lines:
        (sitting / "readings.jsonl").write_text("".join(lines))
    doc = {"schema": "e020-sitting/1", "sitting_id": sid, "batch": batch, "argv": ["--batch", batch],
           "platform": "wine-on-user-machine-iwp-2.0", "set": "iwp-2.0-996e86c5", "variant": "unregistered",
           "binary": {"file": "Islepro.exe", "sha256": F019_SHA, "measured": ["install", "run copy"]},
           "driver_commit": "abcdef123456", "blocks_sha256": "b" * 64, "machine": "local",
           "versions": {"wine": "wine-9.0", "xvfb": "2:21.1", "xfwm4": "4.18.0"},
           "session_run_id": f"E020-sitting-{sid}", "status": status, "recovered": True,
           "started": "2026-10-08T12:00:00Z", "ended": "2026-10-08T13:00:00Z", "loop": {}}
    doc.update(doc_changes or {})
    (sitting / "sitting.json").write_text(json.dumps(doc))
    return sitting, digests


def exchange_reading(game, seq, **values):
    return {"game": game, "seq": seq, "values": dict(EXCHANGE, **values)}


def bomb_reading(game, seq, **values):
    return {"game": game, "seq": seq, "values": dict(BOMB, **values)}


def record(batch, run_id, sitting_epoch, events, fields_of, frames=("a" * 64, "b" * 64)):
    """A run/1-shaped record of E020 with the events given ([(game, seq, values)])."""
    obs = [{"step": 0, "source": "process", "field": "sitting:epoch", "value": str(sitting_epoch)}]
    for step, (game, seq, values) in enumerate(events, start=1):
        obs += [{"step": step, "source": "screen", "field": "game:ordinal", "value": str(game)},
                {"step": step, "source": "screen", "field": "event:seq", "value": str(seq)}]
        obs += [{"step": step, "source": "screen", "field": f, "value": values[f]} for f in fields_of]
        obs += [{"step": step, "source": "screen", "ref": f"sha256:{d}"} for d in frames]
    return {"schema": "run/1", "run_id": run_id, "experiment": "E020", "arm": batch, "observations": obs,
            "outputs": [{"name": f"{i}.png", "sha256": d, "store": "release:E020"} for i, d in enumerate(frames)]}


# --- synthetic stage captures for runtime/iwp/driver/screens.py (T38 round 4) -------------------
# Plain colours painted on the measured regions, on a neutral grey ground that no test's colour matches.
GROUND = (128, 128, 128)
PAINT = {"score-panel": (0, 0, 0), "menu": (140, 239, 247), "subtitle": (0, 200, 255),
         "keep-playing": (189, 8, 66), "accept-loss": (180, 170, 30), "notice-panel": (0, 0, 100),
         "continue": (181, 189, 181)}
SCREEN_PARTS = {"unknown": (), "board": ("score-panel",), "board-menu": ("score-panel", "menu"),
                "title": ("subtitle", "menu"),
                "eliminated": ("score-panel", "keep-playing", "accept-loss", "notice-panel"),
                "game-over": ("score-panel", "notice-panel", "continue")}
# The score panel's seat numbers (round 6), in the colours measured on the frames.
SEAT_PAINT = {"blue": (49, 156, 255), "yellow": (255, 255, 0), "red": (255, 49, 49), "green": (0, 206, 49)}
ZERO = 60       # the pixels a seat's 0 fills (58 to 67 measured on the winner notice)


def stage_frame(*parts, pixels=None, seats=None):
    """An 800x600 RGB capture with the named regions of screens.TESTS painted in their colour.
    `pixels` limits a part to its first N pixels (row by row), to sit just below or at a minimum.
    `seats` ({seat: N}) paints the first N pixels of each seat's number box in the seat's colour,
    after the parts (so over the score panel's black)."""
    from driver import screens
    frame = bytearray(bytes(GROUND) * (800 * 600))
    regions = [(screens.TESTS[part].rect, PAINT[part], (pixels or {}).get(part)) for part in parts]
    regions += [(screens.SEAT_NUMBERS[seat][0], SEAT_PAINT[seat], n) for seat, n in (seats or {}).items()]
    for (x, y, w, h), paint, limit in regions:
        left = w * h if limit is None else limit
        for row in range(y, y + h):
            n = min(w, left)
            if n <= 0:
                break
            start = (row * 800 + x) * 3
            frame[start:start + n * 3] = bytes(paint) * n
            left -= n
    return bytes(frame)


def screen_frame(name, winner=None):
    """A synthetic capture of one named screen (screens.NAMES); with `winner`, the score panel shows
    that seat's number filled (as a two-digit number does) and every other seat's 0 (round 6)."""
    seats = None if winner is None else {seat: (31 * 14 if seat == winner else ZERO) for seat in SEAT_PAINT}
    return stage_frame(*SCREEN_PARTS[name], seats=seats)
