"""Main-seeded #250: keep small changes visible without turning them into events."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_e019_ui_catalogue import FakeClock,FakeSession,fake_locs
import run_walk as r
import walks

class CalibrationTest(unittest.TestCase):
    def watch(self, share='tiny', both=False, enabled=True, countable=None, repeat=1, terminal=False):
        clock=FakeClock(); session=mock.Mock(); order=[]
        with mock.patch.object(r,'CLOCK',clock.clock),mock.patch.object(r,'SLEEP',clock.sleep):
            ctx=r.Ctx(dict(walks.WALKS['Q-UI-06'],qid='Q-UI-06',event_calibration=enabled))
            def pixels(session,rect):
                changed=share!='none' and clock.now>0
                if not both and rect==r.region_rect('message-strip'):changed=False
                if not changed:return bytes(300)
                return (b'\xff'*300) if share=='large' else b'\xff\x00\x00'+bytes(297)
            def capture(*args):order.append('capture');clock.now+=0.1
            def stop():order.append('stop');return 'terminal' if terminal else None
            with mock.patch.object(r,'read_region',side_effect=pixels),mock.patch.object(r,'perform',side_effect=capture) as shots:
                counts=[]
                for turn in range(1,repeat+1):
                    clock.now=0
                    counts.append(r.watch_regions(session,ctx,['message-strip','board-area'],.25,.25,
                        flashes=True,shoot=True,countable=countable,extra={'turn':turn},begun=0,
                        stop_when=stop,capture_changes=enabled))
        diagnostics=[json.loads(c.args[3]) for c in session.observe.call_args_list if c.args[2]=='read: event calibration frame']
        return counts,shots,diagnostics,order,ctx

    def test_tiny_changes_are_retained_but_not_candidates(self):
        counts,shots,frames,_,ctx=self.watch()
        self.assertEqual(counts,[0]);self.assertEqual(ctx.candidate_shots,0)
        shots.assert_called_once();self.assertEqual(len(frames),1)
        f=frames[0]
        self.assertTrue(f['frame'].endswith('.png'))
        self.assertEqual(f['turn'],1);self.assertEqual(f['tick'],1)
        self.assertLessEqual(f['observed_at_s'],f['capture_started_at_s'])
        self.assertLess(f['capture_started_at_s'],f['capture_finished_at_s'])
        self.assertIn('sequential',f['limitation'].lower())

    def test_both_regions_changed_one_calibration_frame(self):
        _,shots,frames,_,_=self.watch(both=True)
        shots.assert_called_once();self.assertEqual(len(frames),1)

    def test_noncountable_region_is_still_retained(self):
        counts,shots,frames,_,_=self.watch(countable=['message-strip'])
        self.assertEqual(counts,[0]);shots.assert_called_once();self.assertEqual(len(frames),1)

    def test_zero_change_and_default_create_no_calibration_frames(self):
        for opts in [{'share':'none'},{'enabled':False}]:
            with self.subTest(opts=opts):
                _,shots,frames,_,_=self.watch(**opts)
                shots.assert_not_called();self.assertEqual(frames,[])

    def test_candidate_count_and_shot_stay_separate(self):
        counts,shots,frames,_,ctx=self.watch(share='large',both=True)
        self.assertEqual(counts,[1]);self.assertEqual(ctx.candidate_shots,1)
        names=[c.args[2] for c in shots.call_args_list]
        self.assertIn('shot flash-candidate-1',names)
        self.assertEqual(len(names),2);self.assertEqual(len(frames),1)
        self.assertNotIn('flash-candidate',frames[0]['frame'])

    def test_names_unique_across_turns_and_capture_before_terminal_stop(self):
        _,shots,frames,order,_=self.watch(repeat=2,terminal=True)
        self.assertEqual(len(frames),2)
        self.assertEqual(len({f['frame'] for f in frames}),2)
        self.assertEqual(order,['capture','stop','capture','stop'])

    def test_cli_rejects_non_event_or_mixed_selection(self):
        for qids in [['Q-UI-08'],['Q-UI-06','Q-UI-08']]:
            args=r.parse_args([arg for q in qids for arg in ['--question',q]]+['--event-calibration'])
            with self.subTest(qids=qids),self.assertRaises(SystemExit):r.questions_of(args)
        args=r.parse_args(['--question','Q-UI-06','--question','Q-UI-07','--event-calibration'])
        self.assertEqual(r.questions_of(args),['Q-UI-06','Q-UI-07'])

    def test_inner_forwards_calibration_flag(self):
        args=r.parse_args(['--question','Q-UI-06','--event-calibration'])
        with mock.patch.object(r.spike,'confined_locations',return_value={'IWP_DIR':Path('/tmp/fake')}), \
                mock.patch.object(r.spike,'must'),mock.patch.object(r.spike,'versions',return_value={}), \
                mock.patch.object(r.sessionlib,'bind_install_readonly'), \
                mock.patch.object(r,'run_walk',return_value=('completed',True)) as run, \
                mock.patch.dict(r.os.environ,{'IWP_CYCLE_COMMIT':'123','IWP_CYCLE_DISPLAY':':99'}):
            self.assertEqual(r.inner(args,['--question','Q-UI-06','--event-calibration']),0)
        self.assertTrue(run.call_args.kwargs['event_calibration'])

    def test_opt_in_real_recorder_outputs_and_manifest(self):
        clock=FakeClock()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);locs=fake_locs(root)
            def factory(*args):return FakeSession(*args,clock=clock,workdir=root/'work')
            with mock.patch.object(r,'CLOCK',clock.clock),mock.patch.object(r,'SLEEP',clock.sleep),contextlib.redirect_stdout(io.StringIO()):
                status,recovered=r.run_walk('Q-UI-06',None,locs,':99','0123456789ab','local',['--event-calibration'],{'wine':'fake'},root=root,session_factory=factory,event_calibration=True)
            self.assertEqual((status,recovered),('completed',True))
            record=json.loads(next((root/'runs/E019/events-end').glob('*.json')).read_text())
            manifest=json.loads(next((root/'evidence/E019/events-end').glob('*.json')).read_text())
            observations=record['observations']
            frames=[json.loads(o['value']) for o in observations if o['field']=='read: event calibration frame']
            self.assertTrue(frames)
            outputs={o['name']:o['sha256'] for o in record['outputs']}
            entries={o['name']:o['sha256'] for o in manifest['files']}
            for f in frames:self.assertEqual(outputs[f['frame']],entries[f['frame']])
            self.assertTrue(any(o['field']=='event calibration policy' for o in observations))
