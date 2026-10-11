"""T45: the 44 proven country click points (experiments/E021-pro-session-a/points.py).

They are the E002 tour's list, which walkthroughs/coordinates.md carries and E020's `place` block
sends. These tests pin the copy the player clicks against both committed sources, so a change on
either side is a failing test rather than a silent drift, and against the step language's own
rules (inside the stage, outside every forbidden rectangle).
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "tests"))
import e021_fixtures as fx  # noqa: E402  (puts experiments/E021-pro-session-a on sys.path)
import points as points_module  # noqa: E402
import steps as stepslib  # noqa: E402

E020_STEPS = ROOT / "experiments" / "E020-wine-first-run" / "play.steps"
COORDINATES = ROOT / "walkthroughs" / "coordinates.md"


def e020_place_points():
    """The `click-until` candidates of E020's `place` block: [(x, y), ...]."""
    text = E020_STEPS.read_text(encoding="utf-8")
    block = text.split("# --- block place", 1)[1].split("# --- block", 1)[0]
    numbers = [int(n) for n in re.findall(r"click-until\?((?:\s+\d+)+)", block)[0].split()]
    # Five watch parameters precede the candidate x/y pairs in click-until?.
    candidates = numbers[5:]
    return list(zip(candidates[::2], candidates[1::2]))


def coordinates_points():
    """The fenced list of walkthroughs/coordinates.md's country positions: [(x, y), ...]."""
    text = COORDINATES.read_text(encoding="utf-8")
    body = re.search(r"```\n((?:\d+ \d+(?:, )?\n?)+)```", text).group(1)
    numbers = [int(n) for n in re.findall(r"\d+", body)]
    return list(zip(numbers[::2], numbers[1::2]))


class PointsTest(unittest.TestCase):
    def test_the_list_is_the_44_countries_that_have_a_proven_point(self):
        self.assertEqual(len(points_module.LIST), 44)
        self.assertEqual(len(points_module.COUNTRY_ORDER), 44)
        self.assertEqual(points_module.NO_POINT, (11, 15))
        self.assertEqual(sorted(points_module.POINTS),
                         sorted(c for c in range(1, 47) if c not in (11, 15)))
        self.assertEqual(sorted(points_module.POINTS), sorted(points_module.COUNTRY_ORDER))

    def test_the_list_matches_the_tours_committed_list(self):
        self.assertEqual(points_module.LIST, tuple(coordinates_points()))
        self.assertEqual(points_module.LIST, tuple(e020_place_points()))
        self.assertEqual(points_module.as_steps_list(),
                         " ".join(f"{x} {y}" for x, y in e020_place_points()))

    def test_every_point_is_a_click_the_step_language_allows(self):
        for country, (x, y) in points_module.POINTS.items():
            step = stepslib.parse_line(f"click {x} {y}")
            self.assertEqual(step.op, "click", country)
            self.assertIsNone(stepslib.forbidden(x, y), country)

    def test_the_list_position_maps_to_the_country_in_board_order(self):
        # #120: the list skips 11 and 15, so position 11 is country 12 and position 14 is country 16
        self.assertEqual(points_module.COUNTRY_ORDER[10], 12)
        self.assertEqual(points_module.COUNTRY_ORDER[13], 16)
        self.assertEqual(points_module.POINTS[1], (55, 193))
        self.assertEqual(points_module.POINTS[46], (321, 262))

    def test_every_block_the_loop_sends_is_in_the_step_file(self):
        from driver.clicks import parse_blocks
        source = (ROOT / "experiments" / "E021-pro-session-a" / "e021_loop.py").read_text()
        sent = set(re.findall(r'self\.send\("([a-z-]+)"\)', source))
        blocks = parse_blocks((ROOT / "experiments" / "E021-pro-session-a" / "session-a.steps").read_text())
        self.assertTrue({"quit-attack", "move-in-done", "exchange", "attack-open"} <= sent)
        self.assertEqual(sent - set(blocks), set())

    def test_the_battle_presses_are_single_clicks_with_no_candidate_fallback(self):
        # round 2, point 1: a second candidate hid that the first had worked (sitting
        # 20261011T070437Z); each press is one plain click, and the loop reads the board after it
        from driver.clicks import parse_blocks
        blocks = parse_blocks((ROOT / "experiments" / "E021-pro-session-a" / "session-a.steps").read_text())
        for name, point in (("quit-attack", (456, 531)), ("move-in-done", (495, 540)), ("exchange", (337, 531)),
                            ("attack-open", (303, 530)), ("attack-cancel", (405, 530))):
            inputs = [s for s in blocks[name] if s.op != "watch"]
            self.assertEqual([(s.op, tuple(s.args)) for s in inputs], [("click", point)], name)

    def test_each_point_is_nearest_to_the_readers_anchor_of_its_own_country(self):
        # the reader (E020's anchors.json) and the clicks must name the same country by the same
        # number: a list position mapped to the wrong country would attack the wrong one
        import boardreader
        anchors = boardreader.load_anchors()
        for country, (x, y) in points_module.POINTS.items():
            nearest = min(anchors, key=lambda c: (anchors[c][0] - x) ** 2 + (anchors[c][1] - y) ** 2)
            self.assertEqual(nearest, country, (country, (x, y)))


if __name__ == "__main__":
    unittest.main()
