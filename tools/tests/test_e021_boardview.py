"""T45: the player's live view (experiments/E021-pro-session-a/boardview.py), on synthetic captures
only (arrays the test paints, never a frame of the game, rule 18)."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "tests"))
import e021_fixtures as fx  # noqa: E402,F401  (sys.path)
import boardview  # noqa: E402
import glyphs  # noqa: E402

TEMPLATES = glyphs.Templates({"1": [np.ones((9, 3), dtype=np.uint8)]})


def blank():
    return np.zeros((600, 800, 3), dtype=np.uint8)


def with_quit_button(pixels=boardview.QUIT_ATTACK_MINIMUM):
    rgb = blank()
    x, y, w, _h = boardview.CENTRE_PANEL
    flat = rgb[y:y + 10, x:x + w].reshape(-1, 3)
    flat[:pixels] = boardview.QUIT_ATTACK_COLOUR
    rgb[y:y + 10, x:x + w] = flat.reshape(10, w, 3)
    return rgb


class BattleProbeTest(unittest.TestCase):
    def test_the_quit_attack_gold_is_the_battle_and_its_minimum_is_the_spikes(self):
        self.assertTrue(boardview.battle_ready(with_quit_button()))
        self.assertFalse(boardview.battle_ready(with_quit_button(boardview.QUIT_ATTACK_MINIMUM - 1)))
        self.assertFalse(boardview.battle_ready(blank()))


class ReaderTest(unittest.TestCase):
    def test_a_capture_the_reader_cannot_read_is_unread_never_guessed(self):
        reader = boardview.FrameReader(lambda: (blank(), "a" * 64), TEMPLATES)
        reading = reader.read()
        self.assertEqual(reading.unread, 46)
        self.assertTrue(all(row == {"army": None, "owner": None} for row in reading.board.values()))
        self.assertEqual(reading.sha256, "a" * 64)
        self.assertFalse(reading.battle)

    def scripted(self, boards):
        """A FrameReader whose reads return `boards` in turn (the last repeats)."""
        reader = boardview.FrameReader(lambda: (blank(), "s" * 64), TEMPLATES, sleep=lambda s: None,
                                       clock=iter(range(0, 1000)).__next__)
        queue = list(boards)

        def read():
            board = queue.pop(0) if len(queue) > 1 else queue[0]
            return boardview.Reading(board, "s" * 64, "blue", True, 0)
        reader.read = read
        return reader

    def test_wait_settled_returns_once_the_counts_changed_and_held(self):
        before = fx.board({3: (fx.BLUE, 5), 4: (fx.RED, 3)})
        moving = fx.board({3: (fx.BLUE, 4), 4: (fx.RED, 3)})
        settled = fx.board({3: (fx.BLUE, 4), 4: (fx.RED, 2)})
        reader = self.scripted([before, moving, settled, settled, fx.board({3: (fx.BLUE, 1)})])
        seen = reader.wait_settled(before, (3, 4), seconds=100)
        self.assertEqual(seen[-1].board, settled)
        self.assertEqual(len(seen), 4)

    def test_wait_settled_gives_up_at_its_bound_with_every_capture(self):
        before = fx.board({3: (fx.BLUE, 5), 4: (fx.RED, 3)})
        reader = self.scripted([before])
        seen = reader.wait_settled(before, (3, 4), seconds=3)
        self.assertEqual(seen[-1].board, before)
        self.assertGreaterEqual(len(seen), 3)


if __name__ == "__main__":
    unittest.main()
