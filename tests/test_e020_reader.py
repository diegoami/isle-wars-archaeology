"""T40: the E020 board reader on synthetic frames. No wine, no sitting, no original pixel: the font
is made up (seeded random bitmaps with a frame, so that each is one blob of 18 x 12), the land is
four flat colours, the frames are painted here.

What each test pins, and what would make it fail (rule 9, rule 10):
- png: a decoder that skips or botches any of the five PNG filters returns other pixels;
- glyphs: a one-pixel variant still matches, a different digit, a clipped glyph, an ambiguous
  blob and a blob of another size do not;
- board: all 46 countries read back exactly from a painted frame, 1 to 3 digits, white and cyan;
  with the matching removed nothing is read (the mock below), so the first test fails; a covered,
  half-covered or text-covered numeral is unread, never a wrong number; a ring cut by the window
  does not spoil a country; an owner is read only when one colour holds 70% of the land;
- seat: the boxed row of the score panel;
- events: a pair is an exchange only when exactly two adjacent countries changed and the rest holds
  (a pair where three changed, a capture, a placement, an unread country, the human's seat, two
  countries of one owner, two countries that do not border each other: none is an event);
- pass: windows of computer turns from the click-driver's log, events written in the form
  e020_export.py reads, and a frame pair of three changes writes none;
- score: exit 0 only when the sample is big enough, accurate enough, mostly read and every hidden
  numeral unread.
"""
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / "experiments" / "E020-wine-first-run" / "reader"
for _path in (READER, ROOT / "tools", ROOT / "experiments" / "E020-wine-first-run"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
import boardreader  # noqa: E402
import check_counts  # noqa: E402
import exchange_events  # noqa: E402
import glyphs  # noqa: E402
import measure  # noqa: E402
import pngdecode  # noqa: E402
import readpass  # noqa: E402
import score  # noqa: E402

SEA = (0x31, 0x6B, 0xDE)
LAND = {"blue": (0x33, 0x33, 0x99), "green": (0x33, 0x99, 0x66), "red": (0xCC, 0x33, 0x33), "yellow": (0x99, 0x99, 0x33)}
SHADES = {"blue": [(0x66, 0x66, 0xCC), (0x00, 0x33, 0x66)], "green": [(0x66, 0xCC, 0x99), (0x00, 0x66, 0x33)],
          "red": [(0x99, 0x33, 0x00), (0xCC, 0x66, 0x66)], "yellow": [(0xCC, 0xCC, 0x66), (0x66, 0x66, 0x00)]}
WHITE, CYAN, BLACK = (0xFF, 0xFB, 0xF0), (0x33, 0xFF, 0xFF), (0, 0, 0)
BOX = (0x66, 0x99, 0xFF)
NAVY = (0x00, 0x10, 0x60)


def make_font(seed=7):
    """{digit: 18x12 bitmap}: a frame (outline) and seeded random interior pixels, drawn again
    until the glyph is one blob and at least 20 pixels from every earlier digit."""
    rng = np.random.RandomState(seed)
    font = {}
    for d in "0123456789":
        while True:
            bitmap = (rng.rand(18, 12) < 0.4).astype(np.uint8)
            bitmap[0, :] = bitmap[-1, :] = bitmap[:, 0] = bitmap[:, -1] = 1
            if len(glyphs.blobs(bitmap.astype(bool))) == 1 and all(int((bitmap != other).sum()) >= 20 for other in font.values()):
                font[d] = bitmap
                break
    return font


FONT = make_font()


def number_width(text):
    return 15 * len(text) - 3


def paint_number(rgb, cx, cy, text, colour=WHITE, clip=None):
    """Paint `text` centred on (cx, cy) with a black shadow; the glyph rows are cy-9 to cy+8."""
    x = int(round(cx - number_width(text) / 2.0))
    y = int(round(cy)) - 9
    for ch in text:
        bitmap = FONT[ch]
        for dy in range(18):
            for dx in range(12):
                if bitmap[dy, dx]:
                    rgb[y + dy + 2, x + dx + 2] = BLACK
        for dy in range(18):
            for dx in range(12):
                if bitmap[dy, dx]:
                    rgb[y + dy, x + dx] = colour
        x += 15


def paint_frame(armies, owners, marks=None, seat=None, anchors=None, texture_seed=3):
    """An 800x600 frame: sea, a land patch per country in its owner's colours (flat with a few
    shaded pixels), the numeral, and the score panel's box on `seat`'s row."""
    anchors = anchors or boardreader.load_anchors()
    marks = marks or {}
    rgb = np.zeros((600, 800, 3), dtype=np.uint8)
    rgb[:, :] = SEA
    rgb[19:105, 19:216] = BLACK                                  # the score panel's ground
    rng = np.random.RandomState(texture_seed)
    for c, (cx, cy) in anchors.items():
        text = str(armies[c])
        half = number_width(text) // 2 + 9
        x0, x1, y0, y1 = int(cx) - half, int(cx) + half, int(cy) - 14, int(cy) + 14
        patch = np.zeros((y1 - y0, x1 - x0, 3), dtype=np.uint8)
        patch[:, :] = LAND[owners[c]]
        shaded = rng.rand(y1 - y0, x1 - x0) < 0.25
        patch[shaded] = SHADES[owners[c]][0]
        rgb[y0:y1, x0:x1] = patch
    for c, (cx, cy) in anchors.items():
        paint_number(rgb, cx, cy, str(armies[c]), CYAN if marks.get(c) == "cyan" else WHITE)
    if seat:
        top, bottom = boardreader.SEAT_BANDS[seat]
        rgb[top:bottom, 18:21] = BOX
    return rgb


def templates():
    return glyphs.Templates({d: [b] for d, b in FONT.items()})


def default_board(armies=None, owners=None):
    armies = armies or {c: 1 + (c * 7) % 29 for c in range(1, 47)}
    colours = ["blue", "green", "red", "yellow"]
    owners = owners or {c: colours[(c * 5 + c // 3) % 4] for c in range(1, 47)}
    return armies, owners


class PngTest(unittest.TestCase):
    def test_every_filter_round_trips(self):
        rng = np.random.RandomState(1)
        rgb = rng.randint(0, 256, size=(15, 9, 3)).astype(np.uint8)
        for filters in ([0], [1], [2], [3], [4], [0, 1, 2, 3, 4], [4, 3, 2, 1, 0]):
            data = pngdecode.encode(rgb, filters)
            self.assertTrue((pngdecode.decode(data) == rgb).all(), filters)

    def test_a_decoder_that_botches_paeth_or_average_is_caught(self):
        rng = np.random.RandomState(2)
        rgb = rng.randint(0, 256, size=(6, 8, 3)).astype(np.uint8)
        for name, filters in (("_paeth_row", [4]), ("_average_row", [3])):
            data = pngdecode.encode(rgb, filters)
            with mock.patch.object(pngdecode, name, lambda line, up, bpp: list(line)):
                self.assertFalse((pngdecode.decode(data) == rgb).all(), name)

    def test_refuses_what_it_does_not_understand(self):
        data = pngdecode.encode(np.zeros((2, 2, 3), dtype=np.uint8))
        with self.assertRaises(pngdecode.PngError):
            pngdecode.decode(b"nope" + data)
        with self.assertRaises(pngdecode.PngError):
            pngdecode.decode(data[:-20] + b"\0" * 20)       # a bad CRC or a cut chunk
        palette = bytearray(data)
        palette[25] = 3                                     # colour type 3 (palette)
        with self.assertRaises(pngdecode.PngError):
            pngdecode.decode(bytes(palette))


class GlyphTest(unittest.TestCase):
    def test_the_font_is_ten_far_apart_blobs(self):
        digits = sorted(FONT)
        for d in digits:
            blobs = glyphs.blobs(FONT[d].astype(bool))
            self.assertEqual(len(blobs), 1, d)
        for i, a in enumerate(digits):
            for b in digits[i + 1:]:
                self.assertGreaterEqual(int((FONT[a] != FONT[b]).sum()), 20, (a, b))

    def test_exact_variant_other_digit_and_wrong_size(self):
        t = templates()
        for d, bitmap in FONT.items():
            self.assertEqual(t.match(bitmap), d)
        variant = FONT["4"].copy()
        variant[9, 5] ^= 1
        variant[10, 6] ^= 1
        self.assertEqual(t.match(variant), "4")               # two pixels off: still its digit
        damaged = FONT["4"].copy()
        damaged[3:7, 3:9] ^= 1
        self.assertIsNone(t.match(damaged))                   # too far from every template
        self.assertIsNone(t.match(FONT["4"][:, :11]))         # clipped on the right: another size
        self.assertIsNone(t.match(FONT["4"][:16]))

    def test_an_ambiguous_blob_is_not_matched(self):
        a = FONT["1"].copy()
        b = a.copy()
        b[8, 4:7] ^= 1                                        # a template of another digit 3 pixels away
        t = glyphs.Templates({"1": [a], "2": [b]})
        self.assertIsNone(t.match(a))                         # nearest by 0, but the next is within the margin
        far = FONT["5"]
        self.assertEqual(glyphs.Templates({"1": [a], "5": [far]}).match(a), "1")

    def test_template_file_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "templates.json"
            glyphs.Templates.dump([(d, b) for d, b in FONT.items()], path)
            loaded = glyphs.Templates.load(path)
            for d, bitmap in FONT.items():
                self.assertEqual(loaded.match(bitmap), d)


class BoardTest(unittest.TestCase):
    def read(self, rgb):
        return boardreader.read_board(rgb, templates())

    def test_all_46_countries_read_back_exactly(self):
        armies, owners = default_board()
        armies[2], armies[13], armies[30] = 24, 100, 999        # two and three digits
        rgb = paint_frame(armies, owners, marks={5: "cyan", 6: "cyan"})
        board = self.read(rgb)
        for c in range(1, 47):
            self.assertEqual((board[c]["army"], board[c]["owner"]), (armies[c], owners[c]), c)
            self.assertIsNone(board[c]["why"])
        self.assertEqual({board[c]["mark"] for c in range(1, 47)}, {"white", "cyan"})
        self.assertEqual(board[5]["mark"], "cyan")

    def test_with_the_matching_removed_nothing_is_read(self):
        armies, owners = default_board()
        rgb = paint_frame(armies, owners)
        with mock.patch.object(glyphs.Templates, "match", return_value=None):
            board = self.read(rgb)
        self.assertTrue(all(r["army"] is None and r["why"] == "unmatched-glyph" for r in board.values()))

    def test_a_wrong_template_is_read_as_the_digit_it_is_not(self):
        # the reader is only as good as its templates: swap two digits in the template set and the
        # same frame reads other numbers, which is why the labelled sample scores the real set.
        armies, owners = default_board({c: 12 for c in range(1, 47)})
        rgb = paint_frame(armies, owners)
        swapped = glyphs.Templates({"2": [FONT["1"]], "1": [FONT["2"]], **{d: [FONT[d]] for d in "03456789"}})
        board = boardreader.read_board(rgb, swapped)
        self.assertEqual({r["army"] for r in board.values()}, {21})

    def test_a_country_without_a_numeral_is_unread(self):
        armies, owners = default_board()
        rgb = paint_frame(armies, owners)
        cx, cy = boardreader.load_anchors()[17]
        rgb[int(cy) - 14:int(cy) + 14, int(cx) - 30:int(cx) + 30] = NAVY          # a notice covers it
        board = self.read(rgb)
        self.assertEqual((board[17]["army"], board[17]["owner"], board[17]["why"]), (None, None, "no-glyph"))
        self.assertEqual(board[16]["army"], armies[16])

    def test_a_half_covered_numeral_is_unread_not_misread(self):
        armies, owners = default_board({c: 5 for c in range(1, 47)})
        rgb = paint_frame(armies, owners)
        cx, cy = boardreader.load_anchors()[9]
        rgb[int(cy) + 1:int(cy) + 14, int(cx) - 20:int(cx) + 20] = NAVY            # the lower half
        board = self.read(rgb)
        self.assertIsNone(board[9]["army"])
        self.assertEqual(board[9]["why"], "stray-blob")

    def test_a_number_of_two_colours_is_unread(self):
        armies, owners = default_board({c: 12 for c in range(1, 47)})
        rgb = paint_frame(armies, owners)
        cx, cy = boardreader.load_anchors()[13]
        x = int(round(cx - number_width("12") / 2.0)) + 15           # the second glyph's columns
        box = rgb[int(cy) - 9:int(cy) + 9, x:x + 12]
        box[(box == WHITE).all(axis=2)] = CYAN
        board = self.read(rgb)
        self.assertEqual((board[13]["army"], board[13]["why"]), (None, "mixed-glyph-colours"))
        self.assertEqual(board[14]["army"], 12)

    def test_text_over_a_numeral_is_unread(self):
        armies, owners = default_board({c: 3 for c in range(1, 47)})
        rgb = paint_frame(armies, owners)
        cx, cy = boardreader.load_anchors()[20]
        rgb[int(cy) - 5:int(cy) + 6, int(cx) - 12:int(cx) + 12] = WHITE            # a band of white text
        self.assertIsNone(self.read(rgb)[20]["army"])

    def test_a_label_ring_cut_by_the_window_does_not_spoil_the_country(self):
        armies, owners = default_board()
        rgb = paint_frame(armies, owners)
        cx, cy = boardreader.load_anchors()[30]
        left, top = int(cx) - boardreader.HALF_WIDTH - 8, int(cy) - boardreader.HALF_HEIGHT - 8
        ring = np.zeros((17, 16), dtype=bool)
        ring[0, 5:11] = ring[-1, 5:11] = ring[:, 0] = ring[:, -1] = True
        for dy in range(17):
            for dx in range(16):
                if ring[dy, dx]:
                    rgb[top + dy, left + dx] = WHITE                                 # straddles the window's corner
        board = self.read(rgb)
        self.assertEqual(board[30]["army"], armies[30])

    def test_an_owner_needs_one_colour_holding_most_of_the_land(self):
        armies, owners = default_board()
        rgb = paint_frame(armies, owners)
        cx, cy = boardreader.load_anchors()[11]
        half = number_width(str(armies[11])) // 2 + 9
        left = rgb[int(cy) - 14:int(cy) + 14, int(cx) - half:int(cx)]
        left[:, :] = LAND["yellow" if owners[11] != "yellow" else "red"]           # half of it another colour
        paint_number(rgb, cx, cy, str(armies[11]))
        board = self.read(rgb)
        self.assertEqual(board[11]["army"], armies[11])
        self.assertIsNone(board[11]["owner"])
        self.assertEqual(board[11]["why"], "owner-mixed")
        sea = paint_frame(armies, owners)
        sea[int(cy) - 14:int(cy) + 14, int(cx) - half:int(cx) + half] = SEA
        paint_number(sea, cx, cy, str(armies[11]))
        self.assertEqual(self.read(sea)[11]["why"], "owner-no-land")

    def test_every_owner_colour_and_shade_is_named(self):
        for colour, shades in SHADES.items():
            for shade in [LAND[colour]] + shades:
                patch = np.zeros((20, 20, 3), dtype=np.uint8)
                patch[:, :] = shade
                family = boardreader.land_family(patch)
                self.assertTrue((family == boardreader.COLOURS.index(colour) + 1).all(), (colour, shade))
        sea = np.zeros((4, 4, 3), dtype=np.uint8)
        sea[:, :] = SEA
        self.assertTrue((boardreader.land_family(sea) == 0).all())

    def test_the_seat_in_turn_is_the_boxed_row(self):
        armies, owners = default_board()
        for seat in ("blue", "yellow", "red", "green"):
            self.assertEqual(boardreader.current_seat(paint_frame(armies, owners, seat=seat)), seat)
        self.assertIsNone(boardreader.current_seat(paint_frame(armies, owners)))
        two = paint_frame(armies, owners, seat="red")
        two[boardreader.SEAT_BANDS["green"][0]:boardreader.SEAT_BANDS["green"][1], 18:21] = BOX
        self.assertIsNone(boardreader.current_seat(two))

    def test_the_anchors_are_46_distinct_countries_with_room_for_their_numbers(self):
        anchors = boardreader.load_anchors()
        self.assertEqual(sorted(anchors), list(range(1, 47)))
        for a, (ax, ay) in anchors.items():
            for b, (bx, by) in anchors.items():
                if a < b:
                    # no other numeral (up to 28 pixels wide) can fall inside a window
                    self.assertTrue(abs(ax - bx) > 40 or abs(ay - by) > 20, (a, b))


def board_of(armies, owners):
    return {c: {"army": armies[c], "owner": owners[c], "mark": "white", "why": None} for c in range(1, 47)}


class EventTest(unittest.TestCase):
    adjacency = exchange_events.load_adjacency()

    def setUp(self):
        self.armies = {c: 5 for c in range(1, 47)}
        self.owners = {c: "green" for c in range(1, 47)}
        self.owners[8], self.owners[43] = "red", "yellow"       # 8 and 43 border each other (E015's table)
        self.before = board_of(self.armies, self.owners)

    def after(self, **changes):
        armies, owners = dict(self.armies), dict(self.owners)
        for key, value in changes.items():
            kind, country = key.split("_")
            (armies if kind == "a" else owners)[int(country)] = value
        return board_of(armies, owners)

    def classify(self, after, before=None, seat_before="yellow", seat_after="yellow"):
        return exchange_events.classify(before or self.before, after, seat_before, seat_after, self.adjacency)

    def test_two_adjacent_countries_lowering_is_an_exchange(self):
        reason, values = self.classify(self.after(a_8=3, a_43=4))
        self.assertEqual(reason, "exchange")
        self.assertEqual(values, {
            "counter:attacker-before": "5", "counter:attacker-after": "4", "counter:defender-before": "5",
            "counter:defender-after": "3", "country:attacker": "43", "country:defender": "8",
            "owner:attacker": "yellow", "owner:defender": "red"})
        self.assertEqual(sorted(values), sorted(check_counts.event_fields(
            check_counts.load_batches(ROOT / "experiments" / "E020-wine-first-run" / "scenarios.txt")["cmb-accumulation"])))
        for field, value in values.items():
            self.assertEqual(check_counts.value_problem(field, value), "", field)

    def test_the_attacker_is_the_seat_in_turn(self):
        reason, values = self.classify(self.after(a_8=3, a_43=4), seat_before="red", seat_after="red")
        self.assertEqual((reason, values["country:attacker"]), ("exchange", "8"))

    def test_a_pair_where_more_than_two_countries_changed_is_not_an_event(self):
        reason, values = self.classify(self.after(a_8=3, a_43=4, a_9=4))
        self.assertEqual((reason, values), ("many-changes", None))

    def test_one_change_no_change_and_not_adjacent(self):
        self.assertEqual(self.classify(self.after(a_8=4))[0], "one-change")
        self.assertEqual(self.classify(self.after())[0], "no-change")
        self.owners[20] = "red"
        before = board_of(self.armies, self.owners)
        armies = dict(self.armies)
        armies[8], armies[20] = 3, 4
        far = board_of(armies, self.owners)
        self.assertEqual(self.classify(far, before)[0], "not-adjacent")

    def test_a_capture_a_placement_and_a_move_are_not_exchanges(self):
        self.assertEqual(self.classify(self.after(a_8=1, a_43=2, o_8="yellow"))[0], "ownership-change")
        self.assertEqual(self.classify(self.after(a_8=6, a_43=4))[0], "counter-rise")
        self.assertEqual(self.classify(self.after(a_8=4, a_43=7))[0], "counter-rise")

    def test_owners_and_seat_must_make_one_attacker(self):
        same = board_of(self.armies, {**self.owners, 8: "yellow"})
        self.assertEqual(self.classify(self.after(a_8=3, a_43=4), same)[0], "same-owner")
        self.assertEqual(self.classify(self.after(a_8=3, a_43=4), seat_before="green", seat_after="green")[0], "no-attacker")
        self.assertEqual(self.classify(self.after(a_8=3, a_43=4), seat_before=None, seat_after=None)[0], "seat-unknown")
        self.assertEqual(self.classify(self.after(a_8=3, a_43=4), seat_before="yellow", seat_after="red")[0], "seat-unknown")
        self.assertEqual(self.classify(self.after(a_8=3, a_43=4), seat_before="blue", seat_after="blue")[0], "human-seat")

    def test_an_unread_country_could_hide_a_change(self):
        broken = self.after(a_8=3, a_43=4)
        broken[30] = {"army": None, "owner": None, "mark": None, "why": "no-glyph"}
        self.assertEqual(self.classify(broken)[0], "unread")
        self.assertEqual(self.classify(self.after(a_8=3, a_43=4), broken)[0], "unread")

    def test_the_adjacency_table_is_symmetric_and_has_46_countries(self):
        self.assertEqual(sorted(self.adjacency), list(range(1, 47)))
        for a, bs in self.adjacency.items():
            for b in bs:
                self.assertIn(a, self.adjacency[b])
        self.assertIn(43, self.adjacency[8])


def action_rows():
    """The click-driver's log of one game: game start, a placement, PASS (step 5), and the next
    turn's placement (step 9)."""
    pass_click = {"block": "commit", "op": "click!", "args": [417, 530], "status": "ok", "game": 1}
    return [{"event": "game-start", "game": 1, "seq": 1},
            {"block": "place", "op": "watch", "game": 1, "seq": 2, "status": "ok"},
            {"block": "commit", "op": "click!", "args": [307, 543], "game": 1, "seq": 3, "status": "ok"},
            {"block": "commit", "op": "click!", "args": [497, 543], "game": 1, "seq": 4, "status": "ok"},
            {**pass_click, "seq": 5},
            {"block": "quiet", "op": "settle", "game": 1, "seq": 6, "status": "ok"},
            {"block": "quiet", "op": "settle", "game": 1, "seq": 7, "status": "ok"},
            {"event": "screen", "game": 1, "seq": 8, "screen": "board-menu"},
            {"block": "place", "op": "watch", "game": 1, "seq": 9, "status": "ok"}]


def make_sitting(root, sid, frames, rows=None):
    """A sitting directory: frames (list of (step, rgb)), frames-index.jsonl, actions.jsonl."""
    sitting = Path(root) / sid
    (sitting / "frames").mkdir(parents=True)
    index, shas = [], []
    for n, (step, rgb) in enumerate(frames):
        data = pngdecode.encode(rgb)
        name = f"{step}-{1000 + n}.png"
        (sitting / "frames" / name).write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        shas.append(digest)
        index.append({"name": name, "sha256": digest, "wall_time": "2026-10-08T20:00:00Z"})
    (sitting / "frames-index.jsonl").write_text("".join(json.dumps(r) + "\n" for r in index), encoding="utf-8")
    (sitting / "actions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in (rows or action_rows())), encoding="utf-8")
    return sitting, shas


class PassTest(unittest.TestCase):
    def test_computer_windows_run_from_pass_to_the_next_placement(self):
        self.assertEqual(readpass.computer_windows(action_rows()), [(5, 8)])
        keep = action_rows()[:5] + [{"block": "eliminated-keep-playing", "op": "click!", "status": "ok", "game": 1, "seq": 20}]
        self.assertEqual(readpass.computer_windows(keep), [(5, 10 ** 9)])
        self.assertEqual(readpass.computer_windows(action_rows()[:3]), [])
        failed = [dict(r, status="failed") if r.get("args") == [417, 530] else r for r in action_rows()]
        self.assertEqual(readpass.computer_windows(failed), [])

    def test_events_are_written_in_the_form_the_export_reads(self):
        armies, owners = default_board({c: 5 for c in range(1, 47)}, {c: "green" for c in range(1, 47)})
        owners[8], owners[43] = "red", "yellow"
        a0 = paint_frame(armies, owners, seat="yellow")
        two = {**armies, 8: 3, 43: 4}
        a1 = paint_frame(two, owners, seat="yellow")
        three = {**two, 9: 4, 10: 4, 11: 4}
        a2 = paint_frame(three, owners, seat="yellow")
        frames = [(4, a0), (5, a0), (6, a1), (7, a2), (8, a2)]   # a0 -> a1: two change; a1 -> a2: three change
        with tempfile.TemporaryDirectory() as tmp:
            sitting, shas = make_sitting(tmp, "20261008T000000Z", frames)
            template_path = Path(tmp) / "templates.json"
            glyphs.Templates.dump([(d, b) for d, b in FONT.items()], template_path)
            measurements = Path(tmp) / "m"
            summary = readpass.run(sitting, measurements, template_path, True, 2)
            events = [json.loads(line) for line in (sitting / "readings.jsonl").read_text().splitlines()]
            self.assertEqual(len(events), 1)                       # the three-change pair is not an event
            self.assertEqual(events[0]["game"], 1)
            self.assertEqual(events[0]["seq"], 1)
            self.assertEqual(events[0]["frames"], [shas[1], shas[2]])
            self.assertEqual(events[0]["values"]["counter:defender-after"], "3")
            self.assertEqual(summary["pairs"], {"exchange": 1, "many-changes": 1, "no-change": 1, "outside-a-computer-turn": 1})
            self.assertEqual(summary["frames"], 5)
            lines = [json.loads(line) for line in (measurements / "frame-readings-20261008T000000Z.jsonl").read_text().splitlines()]
            self.assertEqual([line["computer_turn"] for line in lines], [False, True, True, True, True])
            self.assertEqual(lines[1]["armies"][7], 5)             # country 8
            self.assertEqual(lines[2]["armies"][7], 3)
            self.assertEqual(lines[1]["owners"][42], "yellow")
            self.assertEqual(lines[1]["seat"], "yellow")
            for line in lines:                                     # constraint D: numbers and colour words only
                for value in line["armies"]:
                    self.assertTrue(value is None or isinstance(value, int))
                for value in line["owners"]:
                    self.assertIn(value, boardreader.COLOURS)
            # the export contract (e020_export.events), with the frames and games it checks
            import e020_export
            batch = check_counts.load_batches(ROOT / "experiments" / "E020-wine-first-run" / "scenarios.txt")["cmb-accumulation"]
            paths = {"readings": sitting / "readings.jsonl"}
            observations = e020_export.events(paths, batch, {s: Path(tmp) / s for s in shas}, {1})
            self.assertEqual(len([o for o in observations if "field" in o]), 2 + 8)
            self.assertEqual([o["ref"] for o in observations if "ref" in o], [f"sha256:{shas[1]}", f"sha256:{shas[2]}"])
            with self.assertRaises(SystemExit):                    # a measured output is never overwritten
                readpass.run(sitting, measurements, template_path, True, 2)


class ScoreTest(unittest.TestCase):
    def sample(self, tmp, frames_per_sitting=2, wrong=0, wrong_owner=0):
        """(labels, root): three sittings, `frames_per_sitting` painted frames each, every country
        labelled; `wrong` labels are off by one; a hidden numeral is a covered country."""
        root = Path(tmp) / "root"
        root.mkdir()
        readings = []
        for s in range(3):
            frames, labelled = [], []
            for f in range(frames_per_sitting):
                armies, owners = default_board({c: 1 + (c + f + s) % 40 for c in range(1, 47)})
                rgb = paint_frame(armies, owners)
                cx, cy = boardreader.load_anchors()[1]
                rgb[int(cy) - 14:int(cy) + 14, int(cx) - 30:int(cx) + 30] = NAVY
                frames.append((10 + f, rgb))
                labelled.append((armies, owners))
            sitting, shas = make_sitting(root, f"2026100800000{s}Z", frames)
            for sha, (armies, owners) in zip(shas, labelled):
                for c in range(1, 47):
                    hidden = c == 1
                    readings.append({"sitting": sitting.name, "frame": sha, "country": c,
                                     "army": None if hidden else armies[c], "owner": None if hidden else owners[c],
                                     "visible": not hidden})
        visible = [r for r in readings if r["visible"]]
        for r in visible[:wrong]:
            r["army"] += 1
        for r in visible[:wrong_owner]:
            r["owner"] = "blue" if r["owner"] != "blue" else "red"
        return {"readings": readings}, root

    def run_score(self, labels, root):
        return score.score(labels, root, templates())

    def test_a_good_sample_scores_ok_when_big_enough(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels, root = self.sample(tmp)
            with mock.patch.object(score, "MIN_READINGS", 200), mock.patch.object(score, "MIN_FRAMES", 6):
                code, lines = self.run_score(labels, root)
            self.assertEqual(code, 0, lines)
            self.assertIn("sample: 270 visible readings from 6 frames of 3 sittings", lines[0])
            self.assertIn("hidden numerals read as numbers: 0 of 6", "\n".join(lines))

    def test_the_real_floors_refuse_a_small_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels, root = self.sample(tmp)
            code, lines = self.run_score(labels, root)
            self.assertEqual(code, 1)
            self.assertIn("fewer than 30 frames", lines[-1])

    def test_accuracy_below_98_percent_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels, root = self.sample(tmp, wrong=6)          # 6 of 270 labels off: 97.8%
            with mock.patch.object(score, "MIN_FRAMES", 6):
                code, lines = self.run_score(labels, root)
            self.assertEqual(code, 1)
            self.assertIn("army accuracy below 98%", lines[-1])
            self.assertIn("army count right: 264 of 270 read = 97.8%", "\n".join(lines))

    def test_an_owner_colour_below_98_percent_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels, root = self.sample(tmp, wrong_owner=6)
            with mock.patch.object(score, "MIN_FRAMES", 6):
                code, lines = self.run_score(labels, root)
            self.assertEqual(code, 1)
            self.assertIn("owner accuracy below 98%", lines[-1])
            self.assertNotIn("army accuracy", lines[-1])

    def test_a_read_hidden_numeral_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels, root = self.sample(tmp)
            seen = next(r for r in labels["readings"] if r["visible"])    # a numeral the frame shows ...
            seen["visible"], seen["army"], seen["owner"] = False, None, None   # ... labelled as not on the screen
            with mock.patch.object(score, "MIN_FRAMES", 6):
                code, lines = self.run_score(labels, root)
            self.assertEqual(code, 1)
            self.assertIn("a numeral that is not on the screen was read", lines[-1])

    def test_too_many_unread_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels, root = self.sample(tmp)
            with mock.patch.object(score, "MIN_FRAMES", 6), mock.patch.object(glyphs.Templates, "match", return_value=None):
                code, lines = self.run_score(labels, root)
            self.assertEqual(code, 1)
            self.assertIn("more than 10% unread", lines[-1])


class MeasureTest(unittest.TestCase):
    def test_templates_are_built_from_labelled_bitmaps_and_missing_ones_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            hashes = {d: glyphs.bitmap_sha256(b) for d, b in FONT.items()}
            labels = tmp / "labels.json"
            labels.write_text(json.dumps({"labels": {h: d for d, h in hashes.items()}}), encoding="utf-8")
            local = tmp / "bitmaps.json"
            local.write_text(json.dumps({h: ["".join("#" if v else "." for v in row) for row in FONT[d]]
                                         for d, h in hashes.items()}), encoding="utf-8")
            out = tmp / "templates.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(measure.main(["templates", "--labels", str(labels), "--bitmaps", str(local), "--out", str(out)]), 0)
            loaded = glyphs.Templates.load(out)
            for d, bitmap in FONT.items():
                self.assertEqual(loaded.match(bitmap), d)
            local.write_text("{}", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(measure.main(["templates", "--labels", str(labels), "--bitmaps", str(local), "--out", str(tmp / "x.json")]), 1)

    def test_the_committed_digit_labels_name_ten_digits_by_hash_only(self):
        doc = json.loads((ROOT / "experiments" / "E020-wine-first-run" / "measurements" / "digit-labels.json").read_text())
        self.assertEqual(sorted(doc["labels"].values()), list("0123456789"))
        for h in doc["labels"]:
            self.assertRegex(h, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
