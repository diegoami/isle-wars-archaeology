#!/usr/bin/env python3
"""Verify this audit's evidence accounting, not universal runtime compatibility."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REQUIRED={'instructions','skills','agent-tools','worktrees','permissions-hooks','client-provider','headless-supervision','monitoring','discovery-auth','implementation','review','publication-ci','local-research','cloud','model-choice-policy'}
def check(data):
    assert data['schema']==1 and len(data['baseline'])==40
    rows=data['areas'];assert len(rows)==len(REQUIRED) and {r['area'] for r in rows}==REQUIRED
    assert data['official_sources']
    for name,digest in data['artifacts'].items():
        assert Path(name).name==name and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    for r in rows:
        assert r['disposition'] in {'works','explicit-equivalent','broken','untested'}
        assert all(isinstance(r[k],str) and r[k].strip() for k in ['claude','codex','operator_action'])
        assert r['evidence'] and all(e in data['artifacts'] for e in r['evidence'])
        if r['disposition'] in {'broken','untested'}:assert r['follow_up'] and r['follow_up'].startswith('#')
    pre=json.loads((ROOT/'preflight-r1.json').read_text());assert pre['completed'] and pre['tracked_and_untracked_status_unchanged'] and pre['instruction_pointer']
    assert all(t['exit']==0 for t in pre['tests'])
    assert pre['detection']['codexCanSelectClaude']
    assert pre['detection']['sameFamilyRejected'] and pre['detection']['blockedRejected']
    smoke=json.loads((ROOT/'codex-smoke-r1.json').read_text())
    assert any(e['type']=='turn.completed' for e in smoke['events'])
    assert set(smoke['final']['files_read'])=={'AGENTS.md','CLAUDE.md'}
    assert smoke['final']['instruction_file']=='CLAUDE.md'
    assert smoke['final']['claude_hooks_in_codex'] is False and smoke['final']['originals_in_git'] is False
    commands=[e for e in smoke['events'] if e.get('item_type')=='command_execution']
    assert len(commands)==2 and all(e['exit_code']==0 for e in commands)
    diagnostic=json.loads((ROOT/'export-diagnostic-r1.json').read_text());assert diagnostic['exit']==0 and diagnostic['json_error'] and diagnostic['follow_up']=='#261'
if __name__=='__main__':
    try:check(json.loads((ROOT/'matrix-r1.json').read_text()))
    except (AssertionError,KeyError,ValueError,OSError) as e:print('audit accounting failed:',e,file=sys.stderr);raise SystemExit(1)
    print('15 audit areas accounted for; retained evidence hashes and bounded probe outcomes verified')
