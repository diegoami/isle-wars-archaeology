"""Main-seeded #248: stop at event boundaries and preserve evidence through normal lifecycle."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_e019_ui_catalogue import FakeClock, FakeSession, fake_locs
import run_walk as r
import walks

class EventBudgetTest(unittest.TestCase):
    def drive(self, elapsed=0, setup_seconds=0, per_turn=0, need=5):
        now = [0.0]
        session = mock.Mock()
        session.screen_name.return_value = 'board-menu'
        session.screen_attack_ready.return_value = True
        with mock.patch.object(r, 'CLOCK', lambda: now[0]):
            ctx = r.Ctx(dict(walks.WALKS['Q-UI-06'], qid='Q-UI-06'))
            now[0] = elapsed
            def setup(*args, **kwargs):
                now[0] += setup_seconds
                return True
            def watch(*args, **kwargs):
                now[0] += per_turn
                ctx.candidate_shots += 1
                return 1, 'human-ready'
            with mock.patch.object(r, 'place_and_attack', side_effect=setup) as place, \
                    mock.patch.object(r, 'leave_attack_and_pass', side_effect=lambda *a: now[0]) as passed, \
                    mock.patch.object(r, 'watch_event_turn_after_pass', side_effect=watch) as watched:
                r.composite_event_watch(session, ctx, turns=30, need=need)
        return ctx, session, place, passed, watched

    def test_expired_budget_has_no_placement_or_pass(self):
        for elapsed in (r.WALK_BOUND, r.WALK_BOUND + 1):
            with self.subTest(elapsed=elapsed):
                ctx, s, p, q, w = self.drive(elapsed=elapsed)
                p.assert_not_called(); q.assert_not_called(); w.assert_not_called()
                self.assertEqual(ctx.counts['flash candidates'], 0)
                self.assertTrue(any(c.args[2] == 'event path stop' and 'budget' in c.args[3].lower()
                                    for c in s.observe.call_args_list))

    def test_less_than_full_watch_remaining_has_no_placement(self):
        _, _, p, q, w = self.drive(elapsed=r.WALK_BOUND-r.EVENT_WATCH_SECONDS+0.01)
        p.assert_not_called(); q.assert_not_called(); w.assert_not_called()

    def test_setup_consumes_allowance_so_no_pass(self):
        _, _, p, q, w = self.drive(elapsed=r.WALK_BOUND-r.EVENT_WATCH_SECONDS-1, setup_seconds=2)
        p.assert_called_once(); q.assert_not_called(); w.assert_not_called()

    def test_last_complete_watch_candidate_survives_boundary_stop(self):
        ctx, s, p, q, w = self.drive(per_turn=r.WALK_BOUND-1)
        self.assertEqual((p.call_count, q.call_count, w.call_count), (1,1,1))
        self.assertEqual(ctx.counts['flash candidates'], 1)
        self.assertEqual(ctx.candidate_shots, 1)
        self.assertTrue(any(c.args[2] == 'event path stop' and 'budget' in c.args[3].lower()
                            for c in s.observe.call_args_list))

    def test_target_still_finishes_without_extra_turn(self):
        ctx, s, p, q, w = self.drive(per_turn=r.WALK_BOUND-1, need=1)
        self.assertEqual((p.call_count, q.call_count, w.call_count), (1,1,1))
        self.assertEqual(ctx.counts['flash candidates'], 1)
        self.assertFalse(any(c.args[2] == 'event path stop' for c in s.observe.call_args_list))

    def test_watchdog_accounts_for_selected_event_turns(self):
        # Planned public helper: the outer command must call this same calculator.
        self.assertEqual(r.outer_bound(['Q-UI-06']), 1200+30*57)
        self.assertEqual(r.outer_bound(['Q-UI-07']), 1200+30*57)
        self.assertEqual(r.outer_bound(['Q-UI-08']), 1200)
        self.assertEqual(r.outer_bound(['Q-UI-06', 'Q-UI-08', 'Q-UI-06']), 2*(1200+30*57)+1200)
        self.assertEqual(r.outer_bound(['Q-UI-19']), len(walks.WALKS['Q-UI-19']['sizes'])*1200)

    def test_bounded_stop_writes_real_record_and_outputs(self):
        clock = FakeClock()
        class ExpiredSession(FakeSession):
            def known_screen(self):
                super().known_screen()
                clock.now = r.WALK_BOUND+1
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); locs=fake_locs(root)
            def factory(*args):
                return ExpiredSession(*args, clock=clock, workdir=root/'work')
            with mock.patch.object(r, 'CLOCK', clock.clock), mock.patch.object(r, 'SLEEP', clock.sleep), \
                    mock.patch.object(r, 'place_and_attack', side_effect=AssertionError('expired walk sends no input')), \
                    contextlib.redirect_stdout(io.StringIO()):
                status, recovered=r.run_walk('Q-UI-06',None,locs,':99','0123456789ab','local',[],{'wine':'fake'},root=root,session_factory=factory)
            self.assertEqual((status,recovered),('completed',True))
            paths=list((root/'runs/E019/events-end').glob('*.json'))
            self.assertEqual(len(paths),1)
            record=json.loads(paths[0].read_text())
            self.assertTrue(any(o['field']=='count: flash candidates' and o['value']=='0' for o in record['observations']))
            self.assertTrue(any(o['field']=='event path stop' and 'budget' in o['value'].lower() for o in record['observations']))
            self.assertTrue(any(o['name']=='after.png' for o in record['outputs']))
            self.assertEqual(len(list((root/'evidence/E019/events-end').glob('*.json'))),1)
