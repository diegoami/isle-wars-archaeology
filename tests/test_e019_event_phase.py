"""Main-seeded #244 regressions: event watching cannot authorize unsafe inputs."""
import sys
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments/E019-pro-ui"))
import run_walk as r

class EventPhaseTest(unittest.TestCase):
    def drive(self, screen="board-menu", place=True, attack=True, passed=10.0, ready=False, candidates=1):
        session = mock.Mock()
        session.screen_name.return_value = screen
        session.screen_attack_ready.return_value = attack
        ctx = mock.Mock()
        with mock.patch.object(r, "place_and_attack", return_value=place) as p, mock.patch.object(r, "leave_attack_and_pass", return_value=passed) as q, mock.patch.object(r, "watch_regions", return_value=candidates) as w, mock.patch.object(r, "wait_human_ready_after_pass", return_value=ready) as h:
            r.composite_event_watch(session, ctx, turns=2, need=5)
        return p,q,w,h

    def test_unknown_initial_phase_has_no_placement(self):
        for screen in ["unknown", "eliminated", "game-over", "scoreboard"]:
            with self.subTest(screen=screen):
                p,q,w,h=self.drive(screen=screen)
                p.assert_not_called(); q.assert_not_called(); w.assert_not_called()

    def test_placement_refusal_has_no_pass(self):
        p,q,w,h=self.drive(place=False)
        q.assert_not_called(); w.assert_not_called()

    def test_zero_exchange_attack_phase_must_be_proved(self):
        p,q,w,h=self.drive(attack=False)
        q.assert_not_called(); w.assert_not_called()

    def test_pass_refusal_has_no_watch_or_next_placement(self):
        p,q,w,h=self.drive(passed=None)
        self.assertEqual(p.call_count,1); w.assert_not_called(); h.assert_not_called()

    def test_unfinished_computer_turn_uses_continuous_watch_without_settle_helper(self):
        p,q,w,h=self.drive(ready=False)
        self.assertEqual(p.call_count,1); w.assert_called_once(); h.assert_not_called()

    def test_target_reached_requires_no_further_input(self):
        p,q,w,h=self.drive(candidates=5)
        self.assertEqual(p.call_count,1); h.assert_not_called()
        self.assertEqual(w.call_args.kwargs.get("begun"),10.0)
