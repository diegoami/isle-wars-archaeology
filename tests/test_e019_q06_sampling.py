"""Main-seeded boundary tests for the owner-approved Q06 bounded unknown result."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from tests.test_e019_ui_catalogue import (
    drive_one, records_of, rewrite, check_ui_catalogue, walks, QUESTIONS, INVENTORY,
)

FAILURE = 'experiments/E019-pro-ui/measurements/q06-outer-timeout-20261015.json'


class Q06BoundedContractTest(unittest.TestCase):
    def make(self, root, count=3, qid='Q-UI-06', candidate_count=1):
        for _ in range(count):
            self.assertEqual(drive_one(root, qid, None), ('completed', True))
        for path, _ in records_of(root, qid):
            def below(record):
                for obs in record['observations']:
                    if obs['field'] == 'count: flash candidates':
                        obs['value'] = str(candidate_count)
                    elif obs['field'] == 'count: centre-flash candidates':
                        obs['value'] = str(candidate_count)
                    elif obs['field'] == 'observation':
                        summary = json.loads(obs['value'])
                        summary['counts'] = {k: candidate_count for k in summary['counts']}
                        obs['value'] = json.dumps(summary)
            rewrite(path, below)
        path = Path(root) / FAILURE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(question='Q-UI-06', kind='capture-attempt-failure',
            formal_run_record_written=False, reason='Synthetic interrupted capture',
            limitations=['No formal record; no absence conclusion.'])))
        self.cite(root, qid=qid)

    def cite(self, root, status='unestablished', qid='Q-UI-06', omit=None):
        lines = [f'#### {qid} bounded observation', f'- **Observation**: {status}: random-event timing remains unmeasured.']
        for index, (path, record) in enumerate(records_of(root, qid)):
            if omit == ('run', index):
                continue
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f'- Run: `{path.relative_to(root).as_posix()}` (sha256 `{sha}`)')
            if omit != ('output', index):
                lines.append(f"- Screenshot: sha256 `{record['outputs'][0]['sha256']}`")
        failure = Path(root) / FAILURE
        if failure.is_file() and omit != 'failure':
            lines.append(f'- Interrupted attempt: `{FAILURE}` (sha256 `{hashlib.sha256(failure.read_bytes()).hexdigest()}`)')
        path = Path(root) / 'findings/F020-pro-ui-observations.md'
        path.parent.mkdir(exist_ok=True)
        path.write_text('\n'.join(lines))
        return path

    def errors(self, root, qid='Q-UI-06', f020=True):
        with mock.patch.object(walks, 'BATCHES', dict(walks.BATCHES, **{'events-end': [qid]})):
            return check_ui_catalogue.run_checks(Path(root), questions_path=QUESTIONS,
                inventory_path=INVENTORY, batch='events-end', f020=f020)

    def test_three_traceable_completed_runs_allow_unestablished_only(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root)
            self.assertEqual(self.errors(root), [])

    def test_fewer_than_three_runs_cannot_pass(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, 2)
            self.assertTrue(self.errors(root))

    def test_zero_candidate_runs_are_valid_raw_contributors(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, candidate_count=0)
            self.assertEqual(self.errors(root), [])

    def test_positive_pending_and_static_statuses_retain_target(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root)
            for status in ('observed', 'narrowed', 'pending', 'static-only'):
                with self.subTest(status=status):
                    self.cite(root, status=status)
                    self.assertTrue(self.errors(root))

    def test_conflicting_duplicate_sections_cannot_bypass_positive_target(self):
        import re
        for first in ('unestablished', 'narrowed'):
            with self.subTest(first=first), tempfile.TemporaryDirectory() as root:
                self.make(root)
                f020 = self.cite(root)
                bounded = re.sub(r'`([0-9a-f]{64})`',
                                 lambda m: '`' + m[1][:16] + '…`', f020.read_text())
                positive = '\n'.join(line for line in bounded.replace(
                    '**Observation**: unestablished', '**Observation**: narrowed').splitlines()
                    if 'Interrupted attempt' not in line)
                sections = (bounded, positive) if first == 'unestablished' else (positive, bounded)
                f020.write_text('\n'.join(sections))
                self.assertTrue(self.errors(root), 'conflicting Q06 sections must fail closed')

    def test_records_only_retains_target(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root)
            self.assertTrue(self.errors(root, f020=False))

    def test_q07_unestablished_retains_target(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root, qid='Q-UI-07')
            self.assertTrue(self.errors(root, qid='Q-UI-07'))

    def test_invalid_run_cannot_contribute_even_with_updated_citation(self):
        mutations = {
            'aborted': lambda r: r.update(status='aborted: synthetic'),
            'binary': lambda r: r['start_state'].update(sha256='f' * 64),
            'seal': lambda r: r['start_state'].update(restore='no seal'),
            'platform': lambda r: r['runtime'].update(platform='other-platform'),
            'artifact': lambda r: r['artifact'].update(set='other-artifact'),
            'speed': lambda r: next(o for o in r['observations'] if o['field']=='speed setting').update(value='fast'),
            'size': lambda r: next(o for o in r['observations'] if o['field']=='display size').update(value=json.dumps({'requested':'1024x768x24','display pixels':[1024,768]})),
        }
        for name, change in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as root:
                self.make(root)
                rewrite(records_of(root, 'Q-UI-06')[-1][0], change)
                self.cite(root)
                self.assertTrue(self.errors(root))

    def test_missing_manifest_cannot_contribute(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root)
            manifest = next((Path(root)/'evidence/E019/events-end').glob('*.manifest.json'))
            manifest.write_text(json.dumps({'artifact':{}, 'files':[]}))
            self.assertTrue(self.errors(root))

    def test_every_run_and_output_and_failure_need_citations(self):
        for omit in (('run', 2), ('output', 2), 'failure'):
            with self.subTest(omit=omit), tempfile.TemporaryDirectory() as root:
                self.make(root)
                self.cite(root, omit=omit)
                self.assertTrue(self.errors(root))

    def test_duplicate_run_citations_do_not_count_as_distinct_runs(self):
        with tempfile.TemporaryDirectory() as root:
            self.make(root)
            f020 = self.cite(root, omit=('run', 1))
            path, record = records_of(root, 'Q-UI-06')[0]
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            f020.write_text(f020.read_text() +
                            f'\n- Duplicate run: `{path.relative_to(root).as_posix()}` '
                            f'(sha256 `{sha}`)\n'
                            f"- Duplicate screenshot: `{record['outputs'][0]['sha256']}`\n")
            self.assertTrue(self.errors(root))

    def test_wrong_record_output_and_failure_hash_rejected(self):
        for kind in ('record', 'output', 'failure'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as root:
                self.make(root)
                path, record = records_of(root, 'Q-UI-06')[-1]
                digest = {'record':hashlib.sha256(path.read_bytes()).hexdigest(),
                          'output':record['outputs'][0]['sha256'],
                          'failure':hashlib.sha256((Path(root)/FAILURE).read_bytes()).hexdigest()}[kind]
                f020 = self.cite(root)
                f020.write_text(f020.read_text().replace(digest, 'e' * 64))
                self.assertTrue(self.errors(root))

    def test_false_failure_provenance_rejected_even_with_matching_hash(self):
        for key, value in (('question','Q-UI-07'), ('kind','completed'),
                           ('formal_run_record_written',True), ('reason',''), ('limitations',[])):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as root:
                self.make(root)
                failure = Path(root)/FAILURE
                doc = json.loads(failure.read_text()); doc[key] = value
                failure.write_text(json.dumps(doc)); self.cite(root)
                self.assertTrue(self.errors(root))


if __name__ == '__main__':
    unittest.main()
