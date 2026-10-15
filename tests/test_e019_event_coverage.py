"""Main-seeded #246 tests: post-PASS waits must not hide candidate changes."""
import sys
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"experiments/E019-pro-ui"))
import run_walk as r
import walks

class EventCoverageTest(unittest.TestCase):
    def drive(self, target=5, terminal=False, change=True):
        now=[0.0]
        session=mock.Mock()
        passed=[False]
        def phase():
            if not passed[0]: return "board-menu"
            if terminal and now[0]>=25: return "eliminated"
            return "board"
        session.screen_name.side_effect=phase
        session.screen_attack_ready.return_value=True
        def pass_turn(*args): passed[0]=True; return now[0]
        def sleep(t): now[0]+=t
        def pixels(*args):
            return bytes([255 if change and now[0]>=20 else 0])*300
        ctx=r.Ctx(dict(walks.WALKS["Q-UI-06"],qid="Q-UI-06"))
        with mock.patch.object(r,"CLOCK",lambda:now[0]),mock.patch.object(r,"SLEEP",sleep),mock.patch.object(r,"read_region",pixels),mock.patch.object(r,"place_and_attack",return_value=True) as p,mock.patch.object(r,"leave_attack_and_pass",side_effect=pass_turn),mock.patch.object(r,"perform") as perform,mock.patch.object(r,"wait_human_ready_after_pass",side_effect=AssertionError("blind wait forbidden")):
            r.composite_event_watch(session,ctx,turns=2,need=target)
        return now[0],ctx,p,perform

    def test_late_flash_in_both_regions_is_one_candidate_and_shot(self):
        elapsed,ctx,p,perform=self.drive(terminal=True)
        self.assertEqual(ctx.counts.get("flash candidates"),1)
        self.assertEqual(ctx.candidate_shots,1)
        self.assertEqual(p.call_count,1)
        self.assertGreaterEqual(elapsed,25)
        perform.assert_called_once()
        self.assertIn("shot flash-candidate-1",perform.call_args.args)

    def test_target_stops_before_terminal_or_extra_input(self):
        elapsed,ctx,p,perform=self.drive(target=1)
        self.assertEqual(ctx.counts.get("flash candidates"),1)
        self.assertLess(elapsed,25)
        self.assertEqual(p.call_count,1)

    def test_no_change_is_bounded_without_next_placement(self):
        elapsed,ctx,p,perform=self.drive(change=False)
        self.assertLessEqual(elapsed,57.5) # prior watch15 + departure4 + settle(30+2*4)
        self.assertEqual(p.call_count,1)
        self.assertEqual(ctx.counts.get("flash candidates"),0)
        perform.assert_not_called()
