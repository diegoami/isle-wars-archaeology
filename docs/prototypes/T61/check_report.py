#!/usr/bin/env python3
"""Check artifact accounting and table consistency; prose truth still needs human review."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GUIDE = ROOT.parents[1] / 'client-compatibility.md'
REQUIRED = {'instructions', 'skills', 'agent-tools', 'worktrees', 'permissions-hooks',
            'client-provider', 'headless-supervision', 'monitoring', 'discovery-auth',
            'implementation', 'review', 'publication-ci', 'local-research', 'cloud',
            'model-choice-policy'}
COLUMNS = ['area', 'disposition', 'claude', 'codex', 'operator_action', 'alternative_or_limit', 'follow_up']
# These are outcome-bearing artifacts, not prompts or schemas offered as proof of execution.
EVIDENCE = {area: {'preflight-r2.json'} for area in REQUIRED}
for area in ['instructions', 'worktrees', 'headless-supervision', 'discovery-auth', 'permissions-hooks']:
    EVIDENCE[area].add('codex-smoke-r1.json')
EVIDENCE['monitoring'].add('export-diagnostic-r1.json')

class ReportError(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise ReportError(message)

def table_row(row):
    values = [row.get(key) or '—' for key in COLUMNS]
    if row.get('follow_up'):
        values[-1] = '[' + row['follow_up'] + '](https://github.com/diegoami/isle-wars-archaeology/issues/' + row['follow_up'][1:] + ')'
    return '| ' + ' | '.join(values) + ' |'

def validate(data, guide_text=None):
    require(data.get('schema') == 2, 'expected matrix schema 2')
    require(bool(re.fullmatch(r'[0-9a-f]{40}', data.get('baseline', ''))), 'missing baseline')
    rows = data.get('areas', [])
    require(len(rows) == len(REQUIRED) and {r.get('area') for r in rows} == REQUIRED, 'missing or duplicate area')
    require(bool(data.get('official_sources')), 'missing official sources')
    for name, digest in data.get('artifacts', {}).items():
        require(Path(name).name == name, 'artifact must be a local filename')
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, 'artifact digest differs: ' + name)
    for row in rows:
        area = row['area']
        require(row.get('disposition') in {'works', 'explicit-equivalent', 'broken', 'untested'}, 'invalid disposition')
        for key in ['claude', 'codex', 'operator_action']:
            text = row.get(key)
            # Designed placeholder floor, not a semantic proof: a reviewer still assesses meaning.
            require(isinstance(text, str) and len(text.split()) >= 8, area + ': inadequate ' + key)
        refs = set(row.get('evidence', []))
        require(EVIDENCE[area] <= refs <= set(data['artifacts']), area + ': wrong or missing outcome evidence')
        follow = row.get('follow_up')
        if follow is not None:
            require(isinstance(follow, str) and bool(re.fullmatch(r'#[1-9][0-9]*', follow)), area + ': invalid issue reference')
        if row['disposition'] != 'works':
            text = row.get('alternative_or_limit')
            require(isinstance(text, str) and len(text.split()) >= 8, area + ': missing explicit alternative or limitation')
        if row['disposition'] in {'broken', 'untested'}:
            require(follow is not None, area + ': missing follow-up')
    pre = json.loads((ROOT / 'preflight-r2.json').read_text())
    require(pre['completed'] and pre['tracked_and_untracked_status_unchanged'] and pre['instruction_pointer'], 'preflight did not complete read-only')
    require(pre['baseline'] == data['baseline'] and pre['runtime_files_unchanged_from_baseline'], 'runtime baseline mismatch')
    require(pre['preflight_sha256'] == hashlib.sha256((ROOT / 'preflight.py').read_bytes()).hexdigest(), 'preflight source changed after evidence run')
    require(all(t['exit'] == 0 for t in pre['tests']), 'preflight regression failed')
    detection = pre['detection']
    require(detection['codexCanSelectClaude'], 'documented local route unavailable')
    require(detection['sameFamilyRejected'] and detection['sameFamilyRejectedOpenAI'] and detection['blockedRejected'], 'recorded policy probes no longer reproduce; audit needs new evidence')
    by_area = {r['area']: r for r in rows}
    require(by_area['model-choice-policy']['disposition'] == 'broken' and by_area['model-choice-policy']['follow_up'] == '#270', 'policy disposition contradicts probes')
    require(by_area['monitoring']['disposition'] == 'broken' and by_area['monitoring']['follow_up'] == '#261', 'monitoring disposition contradicts diagnostic')
    require(by_area['cloud']['disposition'] == 'untested' and by_area['cloud']['follow_up'] == '#271', 'no live cloud evidence exists')
    smoke = json.loads((ROOT / 'codex-smoke-r1.json').read_text())
    require(any(e['type'] == 'turn.completed' for e in smoke['events']), 'smoke turn incomplete')
    final = smoke['final']
    require(set(final['files_read']) == {'AGENTS.md', 'CLAUDE.md'} and final['instruction_file'] == 'CLAUDE.md', 'smoke did not read instruction pointer')
    require(final['claude_hooks_in_codex'] is False and final['originals_in_git'] is False, 'smoke boundaries incorrect')
    commands = [e for e in smoke['events'] if e.get('item_type') == 'command_execution']
    require(len(commands) == 2 and all(e['exit_code'] == 0 for e in commands), 'smoke commands did not complete')
    diagnostic = json.loads((ROOT / 'export-diagnostic-r1.json').read_text())
    require(diagnostic['exit'] == 0 and diagnostic['json_error'] and diagnostic['follow_up'] == '#261', 'export diagnostic missing')
    text = GUIDE.read_text() if guide_text is None else guide_text
    actual = [line for line in text.splitlines() if line.startswith('| ') and line.split('|')[1].strip() in REQUIRED]
    require(actual == [table_row(row) for row in rows], 'guide table differs from matrix (area, disposition, prose, limitation or follow-up)')

def self_test(data):
    """Reproduce R1-R3 and the original four accounting controls, without source mutations."""
    validate(data)
    results = []
    cases = ['missing-area', 'missing-evidence', 'tampered-digest', 'untriaged-broken-route',
             'invalid-issue-reference', 'missing-alternative', 'placeholder-action', 'contradictory-disposition',
             'prompt-only-evidence', 'placeholder-claude-text', 'missing-guide-area',
             'wrong-guide-disposition', 'missing-guide-issue']
    for name in cases:
        changed = copy.deepcopy(data)
        guide = GUIDE.read_text()
        policy = next(r for r in changed['areas'] if r['area'] == 'model-choice-policy')
        if name == 'missing-area': changed['areas'].pop()
        elif name == 'missing-evidence': changed['areas'][0]['evidence'] = []
        elif name == 'tampered-digest': changed['artifacts']['preflight-r2.json'] = '0' * 64
        elif name == 'untriaged-broken-route': policy['follow_up'] = None
        elif name == 'invalid-issue-reference': policy['follow_up'] = '#'
        elif name == 'missing-alternative': policy['alternative_or_limit'] = 'x'
        elif name == 'placeholder-action': policy['operator_action'] = 'x'
        elif name == 'contradictory-disposition': policy['disposition'] = 'works'
        elif name == 'prompt-only-evidence': changed['areas'][0]['evidence'] = ['codex-smoke-prompt.txt']
        elif name == 'placeholder-claude-text': changed['areas'][0]['claude'] = 'x'
        elif name == 'missing-guide-area': guide = guide.replace(table_row(data['areas'][0]) + '\n', '')
        elif name == 'wrong-guide-disposition': guide = guide.replace('| model-choice-policy | broken |', '| model-choice-policy | works |')
        elif name == 'missing-guide-issue': guide = guide.replace(table_row(policy), table_row(policy).replace('#270', '#'))
        try:
            validate(changed, guide)
        except ReportError:
            results.append({'control': name, 'caught': True})
        else:
            raise ReportError('surviving control: ' + name)
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    try:
        matrix = json.loads((ROOT / 'matrix-r2.json').read_text())
        validate(matrix)
        if args.self_test:
            print(json.dumps({'scope': 'reproducible structural controls, not universal runtime proof', 'controls': self_test(matrix)}, indent=2))
        else:
            print('15 audit areas accounted for; guide table, evidence roles, hashes and bounded outcomes verified')
    except (ReportError, KeyError, ValueError, OSError) as error:
        print('audit accounting failed:', error)
        raise SystemExit(1)
