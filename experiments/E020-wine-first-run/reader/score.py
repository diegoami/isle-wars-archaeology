#!/usr/bin/env python3
"""Score the reader against the labelled validation sample (T40, Done-when 2).

    python3 experiments/E020-wine-first-run/reader/score.py experiments/E020-wine-first-run/measurements/labels.json

The labels are numbers and colour words only: for each reading, the sitting, the frame's sha256,
the country number, the army count and the owner's colour word as seen by looking at the frame, or
`visible: false` when the numeral is not on the screen (a notice covers it). The frames are read in
place under the sitting root, on the user's machine; they are never copied.

Prints the sample size and the reader's accuracy. Exits 0 only when:
  * the sample holds at least 200 visible readings from at least 30 frames, of all three sittings;
  * the army count is right on at least 98% of the visible readings the reader does not mark unread,
    and the owner's colour on at least 98% of those it does not mark unread;
  * at most 10% of the visible readings are marked unread (an army or an owner not read);
  * every reading whose numeral is not visible is marked unread (the reader never reads what is not
    there);
  * no (sitting, frame, country) is labelled twice (R2: a repeat is refused before scoring);
  * each country whose anchor was measured from the frames alone (no click point in
    walkthroughs/coordinates.md, #120: 11 and 15; `measured_only` in anchors.json) has at least 5
    visible labelled readings from at least 3 frames (the task's R3 amendment), scored like the rest.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boardreader  # noqa: E402
import glyphs  # noqa: E402
import pngdecode  # noqa: E402

SITTING_ROOT = Path("/mnt/c/Temp/iwp-shots/wine")
TEMPLATES = SITTING_ROOT / "reader-templates.json"
MIN_READINGS, MIN_FRAMES, MIN_SITTINGS = 200, 30, 3
MIN_ACCURACY, MAX_UNREAD = 0.98, 0.10
MIN_ANCHOR_READINGS, MIN_ANCHOR_FRAMES = 5, 3     # per measured-only anchor (the task's R3 amendment, 2026-10-09)


def frame_path(root, sitting, sha):
    index = Path(root) / sitting / "frames-index.jsonl"
    for line in index.read_text(encoding="utf-8").splitlines():
        row = json.loads(line) if line.strip() else None
        if row and row["sha256"] == sha:
            return Path(root) / sitting / "frames" / row["name"]
    raise SystemExit(f"frame {sha} is not in the index of sitting {sitting}")


def duplicates(entries):
    """The (sitting, frame, country) keys labelled more than once (R2): one reading is one country
    of one frame, so a repeat would count one validated reading several times."""
    counts = Counter((e["sitting"], e["frame"], e["country"]) for e in entries)
    return sorted(k for k, n in counts.items() if n > 1)


def score(labels, root=SITTING_ROOT, templates=None, out=print, measured_only=None):
    """(exit code, report lines) for a labels document. `measured_only` is the countries whose
    anchor was measured from the frames with no click point to check it against (anchors.json;
    by default boardreader.measured_only_anchors())."""
    entries = labels["readings"]
    repeated = duplicates(entries)
    if repeated:
        shown = ", ".join(f"{s} {f[:12]} country {c}" for s, f, c in repeated[:5])
        return 1, [f"score FAILED: {len(repeated)} (sitting, frame, country) label(s) appear more than once "
                   f"({shown}{', ...' if len(repeated) > 5 else ''}); a repeated label is one reading, "
                   "never several, and the sample is not scored"]
    measured_only = boardreader.measured_only_anchors() if measured_only is None else measured_only
    templates = templates or glyphs.Templates.load(TEMPLATES)
    by_frame = defaultdict(list)
    for entry in entries:
        by_frame[(entry["sitting"], entry["frame"])].append(entry)
    boards = {}
    for (sitting, sha) in by_frame:
        boards[(sitting, sha)] = boardreader.read_board(pngdecode.decode_file(frame_path(root, sitting, sha)), templates)
    visible = [e for e in entries if e["visible"]]
    hidden = [e for e in entries if not e["visible"]]
    army_wrong, owner_wrong, unread, armies_read, owners_read, reasons = [], [], 0, 0, 0, Counter()
    for e in visible:
        r = boards[(e["sitting"], e["frame"])][e["country"]]
        if r["army"] is None or r["owner"] is None:
            unread += 1
            reasons[r["why"]] += 1
        if r["army"] is not None:
            armies_read += 1
            if r["army"] != e["army"]:
                army_wrong.append((e, r))
        if r["owner"] is not None:
            owners_read += 1
            if r["owner"] != e["owner"]:
                owner_wrong.append((e, r))
    hidden_read = [e for e in hidden if boards[(e["sitting"], e["frame"])][e["country"]]["army"] is not None
                   or boards[(e["sitting"], e["frame"])][e["country"]]["owner"] is not None]
    sittings = sorted({e["sitting"] for e in visible})
    frames = {(e["sitting"], e["frame"]) for e in visible}
    n = len(visible)
    army_acc = (armies_read - len(army_wrong)) / armies_read if armies_read else 0.0
    owner_acc = (owners_read - len(owner_wrong)) / owners_read if owners_read else 0.0
    unread_rate = unread / n if n else 1.0
    lines = [
        f"sample: {n} visible readings from {len(frames)} frames of {len(sittings)} sittings "
        f"({', '.join(f'{s}: {sum(1 for e in visible if e['sitting'] == s)}' for s in sittings)}); "
        f"{len(hidden)} readings of numerals not on the screen",
        f"unread (army or owner): {unread} of {n} = {unread_rate:.1%}"
        + (f" ({', '.join(f'{k} {v}' for k, v in sorted(reasons.items()))})" if reasons else ""),
        f"army count right: {armies_read - len(army_wrong)} of {armies_read} read = {army_acc:.1%}",
        f"owner colour right: {owners_read - len(owner_wrong)} of {owners_read} read = {owner_acc:.1%}",
        f"hidden numerals read as numbers: {len(hidden_read)} of {len(hidden)}",
    ]
    anchor_problems = []
    for c in sorted(measured_only):
        own = [e for e in visible if e["country"] == c]
        own_frames = {(e["sitting"], e["frame"]) for e in own}
        right = sum(1 for e in own if boards[(e["sitting"], e["frame"])][c]["army"] == e["army"])
        lines.append(f"measured-only anchor, country {c}: {len(own)} visible readings from {len(own_frames)} frames, "
                     f"army right on {right}")
        if len(own) < MIN_ANCHOR_READINGS or len(own_frames) < MIN_ANCHOR_FRAMES:
            anchor_problems.append(f"country {c}'s measured anchor has fewer than {MIN_ANCHOR_READINGS} visible "
                                   f"readings from {MIN_ANCHOR_FRAMES} frames")
    for e, r in army_wrong:
        lines.append(f"  army wrong: sitting {e['sitting']} frame {e['frame'][:12]} country {e['country']}: "
                     f"labelled {e['army']}, read {r['army']}")
    for e, r in owner_wrong:
        lines.append(f"  owner wrong: sitting {e['sitting']} frame {e['frame'][:12]} country {e['country']}: "
                     f"labelled {e['owner']}, read {r['owner']}")
    problems = list(anchor_problems)
    if n < MIN_READINGS:
        problems.append(f"fewer than {MIN_READINGS} visible readings")
    if len(frames) < MIN_FRAMES:
        problems.append(f"fewer than {MIN_FRAMES} frames")
    if len(sittings) < MIN_SITTINGS:
        problems.append(f"readings from fewer than {MIN_SITTINGS} sittings")
    if army_acc < MIN_ACCURACY:
        problems.append(f"army accuracy below {MIN_ACCURACY:.0%}")
    if owner_acc < MIN_ACCURACY:
        problems.append(f"owner accuracy below {MIN_ACCURACY:.0%}")
    if unread_rate > MAX_UNREAD:
        problems.append(f"more than {MAX_UNREAD:.0%} unread")
    if hidden_read:
        problems.append("a numeral that is not on the screen was read")
    lines.append("score ok" if not problems else "score FAILED: " + "; ".join(problems))
    return (0 if not problems else 1), lines


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if len(argv) != 1:
        print("usage: score.py <labels.json>")
        return 2
    labels = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    code, lines = score(labels)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
