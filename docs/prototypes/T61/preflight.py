#!/usr/bin/env python3
"""Read-only client probes. Exit zero means probes completed, not universal compatibility."""
import argparse, hashlib, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
BASELINE = 'cdde67142ffc15d7af7432f89b24aabcd16b9b70'

def command(argv):
    try:
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=45)
        return {"argv": argv, "exit": r.returncode, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"argv": argv, "exit": None, "error": type(e).__name__}

def main():
    a = argparse.ArgumentParser(); a.add_argument('--output', type=Path, required=True); args = a.parse_args()
    before = command(['git', 'status', '--porcelain'])['stdout']
    probes = {}
    for name, argv in [('node', ['node', '--version']), ('python', ['python3', '--version']),
                       ('git', ['git', '--version']), ('gh', ['gh', '--version']),
                       ('codex', ['codex', '--version']), ('claude', ['claude', '--version'])]:
        r = command(argv)
        probes[name] = {k:v for k,v in r.items() if k not in ['stdout','stderr']}
        probes[name]['version'] = r.get('stdout', '').splitlines()[:1]
        # Never persist inherited config diagnostics or credentials.
        probes[name]['diagnostic_present'] = bool(r.get('stderr'))
    for client, argv, flags in [('codex', ['codex', 'exec', '--help'], ['--sandbox','--json','--ephemeral','--output-schema']),
                                ('claude', ['claude', '--help'], ['--effort','--setting-sources','--permission-mode','--output-format'])]:
        r = command(argv); probes[client]['help_exit'] = r['exit']
        probes[client]['flags'] = {f:f in r.get('stdout','') for f in flags}
    js = """import {sessionFamily,sessionClient,reviewRefusal,namedModel} from './tools/harness/lib/common.mjs';
const envs=[{}, {CODEX_THREAD_ID:'fixture'}, {HARNESS_CLIENT:'codex'},
 {HARNESS_CLIENT:'claude',CODEX_THREAD_ID:'fixture',ANTHROPIC_BASE_URL:'https://api.z.ai'},
 {CODEX_HOME:'/fixture'}, {HARNESS_CLIENT:'codex',HARNESS_SESSION_FAMILY:'claude'}];
const samples=envs.map(env=>({env,client:sessionClient(env),family:sessionFamily(env)}));
const models={sonnet:{id:'anthropic/claude-sonnet-5-5',family:'claude',backend:'claude'},luna:{id:'openai/gpt-5.6-luna',family:'openai'}};
let blockedRejected=false;try{namedModel({models,blocked:['claude']},'sonnet',{},(code,msg)=>{throw Error(msg)})}catch{blockedRejected=true}
console.log(JSON.stringify({samples,sameFamilyRejected:!!reviewRefusal(models,'sonnet',[],{HARNESS_CLIENT:'claude'}),
 sameFamilyRejectedOpenAI:!!reviewRefusal(models,'luna',[],{HARNESS_CLIENT:'codex'}),
 codexCanSelectClaude:reviewRefusal(models,'sonnet',[],{HARNESS_CLIENT:'codex'})===null,blockedRejected}));"""
    r = command(['node','--input-type=module','-e',js])
    detection = json.loads(r['stdout']) if r['exit']==0 else {'error':'client probe failed'}
    tests=[]
    for argv in [['node','--test','tests/harness_clients.test.mjs','tools/harness/test/claude.test.mjs'],
                 ['node','tools/harness/review.mjs','--self-test']]:
        t=command(argv);tests.append({'argv':argv,'exit':t['exit'],'summary':t.get('stdout','').splitlines()[-8:]})
    manager=command(['systemctl','--user','is-system-running'])
    paths={name:(Path.home()/'.local/share/isle-wars-archaeology'/name).is_dir()
           for name in ['static','E019-bundles']}
    after=command(['git','status','--porcelain'])['stdout']
    ok=(all(p['exit']==0 and p.get('help_exit',0)==0 and all(p.get('flags',{}).values()) for p in probes.values())
        and r['exit']==0 and all(t['exit']==0 for t in tests) and before==after)
    data={'schema':1,'scope':'read-only offline client preflight; no model request or universal compatibility claim',
          'host_scope':'local owner host over SSH; not cloud',
          'baseline':BASELINE,'source_head':command(['git','rev-parse','HEAD'])['stdout'],
          'preflight_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'runtime_files_unchanged_from_baseline':command(['git','diff','--quiet',BASELINE,'--','tools/harness','tests/harness_clients.test.mjs','.claude/skills'])['exit']==0,
          'repo_layout':{'claude_skills':(ROOT/'.claude/skills').is_dir(),'codex_repo_skills':(ROOT/'.agents/skills').is_dir()},
          'instruction_pointer': 'CLAUDE.md' in (ROOT/'AGENTS.md').read_text(),
          'probes':probes,'detection':detection,'tests':tests,
          'user_service_manager':{'exit':manager['exit'],'state':manager.get('stdout','')},
          'local_research_directories':paths,'tracked_and_untracked_status_unchanged':before==after,'completed':ok}
    args.output.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'completed':ok,'report':str(args.output),'known_policy_filters':{k:detection.get(k) for k in ['sameFamilyRejected','blockedRejected']}}))
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
