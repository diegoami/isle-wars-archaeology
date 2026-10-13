"""Build the synthetic E022 single-exchange record (T44 Done-when 2 support).

It runs the T44 mechanism (`single_exchange.single_exchange`) on one synthetic board pair, writes
the two synthetic frames it cites, and writes `runs/E022/synthetic/E022-r0001.json` — a valid run/1
record whose one observation is a single exchange (`event:seq`, `single:rank`). The offline test
(`tools/tests/test_e022_single_exchange.py`) re-derives the observation from these same boards and
fails if it differs; nothing here reads the game, the install or the network.

`python3 experiments/E022-pro-fast-capture/build_record.py` (re)writes the record and its frames.
"""
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import single_exchange  # noqa: E402

SITTING_EPOCH = 1791460800
GAME = 1
SEQ = 1
CODE_COMMIT = "0000000"

# The synthetic pair: country 1 (red, the seat in turn) attacks country 2 (blue) and wins one die —
# country 2's counter drops from 4 to 3, country 1 is unchanged. Country 1 borders only country 2,
# so the defender is unambiguous and the pair is (1, 2).
BEFORE = {1: {"army": 9, "owner": "red"}, 2: {"army": 4, "owner": "blue"}}
AFTER = {1: {"army": 9, "owner": "red"}, 2: {"army": 3, "owner": "blue"}}
SEAT = "red"
ADJACENCY = {1: {2}, 2: {1}}
FRAMES = (b"E022 synthetic frame before", b"E022 synthetic frame after")


def _png(width, height, rgb):
    """A minimal valid RGB PNG of one colour, so a cited frame is a real file, not only a hash."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def build(root=ROOT):
    """Write the frames and the record under `root`; return (record path, values)."""
    values, reason = single_exchange.single_exchange(BEFORE, AFTER, SEAT, ADJACENCY)
    if reason != "single":
        raise SystemExit(f"the fixture is not a single exchange: {reason}")
    folder = Path(root) / "runs" / "E022" / "synthetic"
    frames = folder / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    pngs = {"frame-before.png": _png(1, 1, (255, 0, 0)), "frame-after.png": _png(1, 1, (0, 0, 255))}
    refs = []
    for name, data in pngs.items():
        (frames / name).write_bytes(data)
        refs.append("sha256:" + hashlib.sha256(data).hexdigest())
    observations = [{"step": 0, "source": "process", "field": "sitting:epoch", "value": str(SITTING_EPOCH)}]
    observations += single_exchange.observation(values, GAME, SEQ, refs)
    record = {
        "schema": "run/1",
        "run_id": "E022-r0001",
        "experiment": "E022",
        "arm": "synthetic",
        "rep": 1,
        "code_commit": CODE_COMMIT,
        "machine": "local",
        "artifact": {"set": "iwp-2.0-996e86c5", "variant": "unregistered"},
        "runtime": {"driver": "experiments/E022-pro-fast-capture/single_exchange.py@" + CODE_COMMIT,
                    "platform": "synthetic", "fingerprint": {"python": "%d" % sys.version_info.major}},
        "interventions": [{"level": "I0", "what": "none"}],
        "start_state": {"id": "synthetic-board-after-one-die",
                        "sha256": hashlib.sha256(repr(sorted(AFTER.items())).encode()).hexdigest(),
                        "restore": "none (synthetic frames; no game was run)"},
        "seed": None,
        "actions": {"script": "experiments/E022-pro-fast-capture/build_record.py",
                    "sha256": hashlib.sha256(BUILD_BYTES()).hexdigest(), "args": []},
        "observations": observations,
        "outputs": [{"name": name, "sha256": ref[7:], "store": "release:E022"}
                    for name, ref in zip(pngs, refs)],
        "started": "2026-10-13T00:00:00Z",
        "ended": "2026-10-13T00:00:00Z",
        "status": "completed",
    }
    path = folder / "E022-r0001.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, values


def BUILD_BYTES():
    return Path(__file__).read_bytes()


if __name__ == "__main__":
    path, _ = build()
    print(f"wrote {path.relative_to(ROOT)}")
