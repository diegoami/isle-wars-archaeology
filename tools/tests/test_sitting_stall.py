"""tools/harness/sitting_stall.py: a stuck sitting is named, a moving one is not."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "harness"))
import sitting_stall  # noqa: E402

MIN = 60000


class Sitting:
    """A sitting folder written line by line, as the driver and the watcher do."""

    def __init__(self, root):
        self.root = pathlib.Path(root)

    def frame(self, t, sha, n=[0]):
        n[0] += 1
        with open(self.root / "frames-index.jsonl", "a") as f:
            f.write(json.dumps({"name": f"{n[0]}-{t}.png", "sha256": sha * 64, "epoch_ms": t}) + "\n")

    def act(self, t, **row):
        with open(self.root / "actions.jsonl", "a") as f:
            f.write(json.dumps(dict(row, t_ms=t, game=1, turn=1)) + "\n")


class StallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = Sitting(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def check(self, now):
        return sitting_stall.check(self.s.root, now)

    def test_a_moving_sitting_is_not_stuck(self):
        for i in range(12):
            self.s.frame(i * MIN, "ab"[i % 2])
            self.s.act(i * MIN, event="attack-attempt", fought=True)
        self.assertEqual(self.check(11 * MIN + 1000), [])

    def test_the_same_screen_for_five_minutes_is_named_with_its_frame(self):
        self.s.frame(0, "a")
        for i in range(1, 7):
            self.s.frame(i * MIN, "b")
            self.s.act(i * MIN, event="case-met")
        found = self.check(6 * MIN + 1000)
        self.assertEqual(len(found), 1)
        self.assertIn("screen still for 5.0 min", found[0])
        self.assertIn("-360000.png", found[0])

    def test_four_minutes_of_the_same_screen_is_not_yet_stuck(self):
        self.s.frame(0, "a")
        for i in range(1, 5):
            self.s.frame(i * MIN, "b")
        self.assertEqual(self.check(5 * MIN), [])

    def test_no_new_capture_for_five_minutes_is_named(self):
        self.s.frame(0, "a")
        found = self.check(5 * MIN)
        self.assertEqual(len(found), 1)
        self.assertIn("no captures for 5.0 min", found[0])

    def test_clicks_without_play_for_five_minutes_are_named(self):
        self.s.act(0, event="attack-attempt", fought=True)
        for i in range(1, 7):
            self.s.frame(i * MIN, "ab"[i % 2])
            self.s.act(i * MIN, event="turn-end", fights=0)   # the driver passes, nothing fights
        found = self.check(6 * MIN + 1000)
        self.assertEqual(len(found), 1)
        self.assertIn("no play for 6.0 min", found[0])

    def test_an_attack_that_did_not_fight_is_not_play(self):
        self.s.act(0, event="game-start")
        for i in range(1, 7):
            self.s.frame(i * MIN, "ab"[i % 2])
            self.s.act(i * MIN, event="attack-attempt", fought=False)
        self.assertTrue(any("no play" in line for line in self.check(6 * MIN + 1000)))

    def test_a_replay_sees_only_what_was_logged_by_then(self):
        self.s.act(0, event="game-start")
        for i in range(1, 7):
            self.s.frame(i * MIN, "ab"[i % 2])
            self.s.act(i * MIN, event="turn-end", fights=0)
        self.s.act(20 * MIN, event="case-met")                # logged later than the replay moment
        self.assertTrue(any("no play" in line for line in self.check(6 * MIN + 1000)))

    def test_a_half_written_last_line_is_skipped(self):
        self.s.frame(0, "a")
        with open(self.s.root / "frames-index.jsonl", "a") as f:
            f.write('{"name": "2-6')
        self.assertEqual(len(self.check(MIN)), 0)

    def test_the_command_exits_1_when_stuck_and_0_when_not(self):
        self.s.frame(0, "a")
        self.assertEqual(sitting_stall.main([str(self.s.root), "--now-ms", str(MIN)]), 0)
        self.assertEqual(sitting_stall.main([str(self.s.root), "--now-ms", str(6 * MIN)]), 1)


if __name__ == "__main__":
    unittest.main()
