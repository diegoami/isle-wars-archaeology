"""Main-seeded #246 tests: post-PASS waits must not hide candidate changes."""
import json
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
        return now[0],ctx,p,perform,session

    def test_late_flash_in_both_regions_is_one_candidate_and_shot(self):
        elapsed,ctx,p,perform,session=self.drive(terminal=True)
        self.assertEqual(ctx.counts.get("flash candidates"),1)
        self.assertEqual(ctx.candidate_shots,1)
        self.assertEqual(p.call_count,1)
        self.assertGreaterEqual(elapsed,25)
        perform.assert_called_once()
        self.assertIn("shot flash-candidate-1",perform.call_args.args)
        self.assertEqual(ctx.counts.get("flash candidates"), 1)

    def test_terminal_frame_is_observed_before_safe_stop(self):
        _,ctx,_,perform,session=self.drive(terminal=True)
        self.assertTrue(any(call.args[2] == "event path stop" and "terminal eliminated" in call.args[3]
                            for call in session.observe.call_args_list))
        perform.assert_called_once()

    def test_unknown_post_pass_state_stops_without_a_second_placement(self):
        now=[0.0]
        session=mock.Mock()
        passed=[False]
        def phase():
            if not passed[0]:
                return "board-menu"
            return "board" if now[0] < 0.5 else "unknown"
        session.screen_name.side_effect=phase
        session.screen_attack_ready.return_value=True
        def pass_turn(*args):
            passed[0]=True
            return now[0]
        def sleep(t):
            now[0]+=t
        ctx=r.Ctx(dict(walks.WALKS["Q-UI-06"],qid="Q-UI-06"))
        with mock.patch.object(r,"CLOCK",lambda:now[0]),mock.patch.object(r,"SLEEP",sleep), \
                mock.patch.object(r,"read_region",lambda *args: b"\0"*300), \
                mock.patch.object(r,"place_and_attack",return_value=True) as place, \
                mock.patch.object(r,"leave_attack_and_pass",side_effect=pass_turn) as leave, \
                mock.patch.object(r,"perform"):
            r.composite_event_watch(session,ctx,turns=2,need=1)
        self.assertEqual((place.call_count, leave.call_count), (1,1))
        self.assertTrue(any(call.args[2] == "event path stop" and "unsupported" in call.args[3]
                            for call in session.observe.call_args_list))

    def test_target_stops_before_terminal_or_extra_input(self):
        elapsed,ctx,p,perform,_=self.drive(target=1)
        self.assertEqual(ctx.counts.get("flash candidates"),1)
        self.assertLess(elapsed,25)
        self.assertEqual(p.call_count,1)

    def test_no_change_is_bounded_without_next_placement(self):
        elapsed,ctx,p,perform,session=self.drive(change=False)
        self.assertLessEqual(elapsed,57.5) # protocol bound: 15 + 4 + (30 + 2 * 4)
        self.assertEqual(p.call_count,1)
        self.assertEqual(ctx.counts.get("flash candidates"),0)
        perform.assert_not_called()
        timed = [call.args[3] for call in session.observe.call_args_list
                 if call.args[2] == "read: timed-watch"]
        self.assertTrue(any('"seconds": 57' in value for value in timed))
        self.assertTrue(any(call.args[2] == "event path stop" and "no quiet-settle claim" in call.args[3]
                            for call in session.observe.call_args_list))

    def test_departure_precedes_human_ready_and_no_settle_or_extra_input_is_sent(self):
        now=[0.0]
        session=mock.Mock()
        passed=[False]
        def phase():
            if not passed[0]:
                return "board-menu"
            if now[0] < 16:
                return "board-menu"
            return "board-menu" if now[0] >= 17 else "board"
        session.screen_name.side_effect=phase
        session.screen_attack_ready.return_value=True
        def pass_turn(*args):
            passed[0]=True
            return now[0]
        def sleep(t):
            now[0]+=t
        ctx=r.Ctx(dict(walks.WALKS["Q-UI-06"],qid="Q-UI-06"))
        with mock.patch.object(r,"CLOCK",lambda:now[0]),mock.patch.object(r,"SLEEP",sleep), \
                mock.patch.object(r,"read_region",lambda *args: b"\0"*300), \
                mock.patch.object(r,"place_and_attack",return_value=True), \
                mock.patch.object(r,"leave_attack_and_pass",side_effect=pass_turn), \
                mock.patch.object(r,"perform") as perform:
            r.composite_event_watch(session,ctx,turns=2,need=1)
        # The first board-menu is stale; readiness is accepted only after the board departure.
        observed = session.observe.call_args_list
        self.assertTrue(any(call.args[2] == "event path departure" for call in observed))
        self.assertTrue(any(call.args[2] == "event path probe" and "human-ready board-menu" in call.args[3]
                            for call in observed))
        self.assertFalse(any(call.args and call.args[0].startswith("settle")
                             for call in perform.call_args_list))

    def test_candidate_shots_are_unique_across_turns_and_co_count_once_per_tick(self):
        now=[0.0]
        session=mock.Mock()
        starts=[]
        def phase():
            if not starts:
                return "board-menu"
            start=starts[-1]
            if now[0] < start + 21:
                return "board"
            return "board-menu"
        session.screen_name.side_effect=phase
        session.screen_attack_ready.return_value=True
        def pass_turn(*args):
            starts.append(now[0])
            return now[0]
        def sleep(t):
            now[0]+=t
        def pixels(*args):
            if not starts:
                return b"\0"*300
            return bytes([255 if now[0] >= starts[-1] + 20 else 0])*300
        ctx=r.Ctx(dict(walks.WALKS["Q-UI-06"],qid="Q-UI-06"))
        with mock.patch.object(r,"CLOCK",lambda:now[0]),mock.patch.object(r,"SLEEP",sleep), \
                mock.patch.object(r,"read_region",pixels),mock.patch.object(r,"place_and_attack",return_value=True), \
                mock.patch.object(r,"leave_attack_and_pass",side_effect=pass_turn),mock.patch.object(r,"perform") as perform:
            r.composite_event_watch(session,ctx,turns=2,need=2)
        self.assertEqual(ctx.counts.get("flash candidates"),2)
        self.assertEqual(ctx.candidate_shots,2)
        self.assertEqual([call.args[2] for call in perform.call_args_list],
                         ["shot flash-candidate-1", "shot flash-candidate-2"])
        timed = [call for call in session.observe.call_args_list if call.args[2] == "read: timed-watch"]
        self.assertEqual(len(timed),2)
        flash = [json.loads(call.args[3])["region"] for call in session.observe.call_args_list
                 if call.args[2] == "flash candidate"]
        self.assertEqual(flash.count("message-strip"), flash.count("board-area"))
