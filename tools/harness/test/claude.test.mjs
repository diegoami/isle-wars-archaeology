import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { validateClaudeEnvironment, readClaudeEvents, scopeProblems, runClaudeWatched, claudeSettings } from '../lib/claude.mjs';
import { readReview } from '../lib/chain.mjs';
import { planPost } from '../lib/post.mjs';
import { planSwitch } from '../lib/switch.mjs';
import { materializeReviewDependencies } from '../lib/review-dependencies.mjs';
import { reviewRefusal, namedModel } from '../lib/common.mjs';
const id = 'claude-sonnet-5-5';
const init = { type: 'system', subtype: 'init', model: id, session_id: 'ours' };
const final = { type: 'result', subtype: 'success', is_error: false, session_id: 'ours', result: 'T69 review (Claude)\napprove\nDW1: ran check → passed\nFILE: src/a.ts\nSCOPE: complete\nFinal pass done\napprove', permission_denials: [] };
const encode = (events) => events.map((e) => JSON.stringify(e)).join('\n')+'\n';
test('identity: actual selected model and real final required, not exit0 or quoted content', () => {
 assert.equal(readClaudeEvents(encode([init,final]), id, 'ours').review,final.result);
 for (const events of [[final],[init],[init,init,final],[init,final,final],[{...init,model:'glm-5.3'},final],[init,{type:'assistant',message:{model:'glm-5.3',content:[]}},final],[{...init,model:'claude-opus-5-5'},final],[{...init,session_id:'other'},final],[init,{...final,session_id:'other'}],[init,{...final,is_error:true}],[init,{...final,subtype:'error_max_turns'}],[init,{...final,permission_denials:[{tool_name:'Bash'}]}]]) assert.throws(()=>readClaudeEvents(encode(events),id,'ours'));
 assert.throws(()=>readClaudeEvents(encode([init,final])+'{',id,'ours'));
 assert.throws(()=>readClaudeEvents(encode([init,{type:'user',message:{content:[{type:'tool_result',content:'PreToolUse hook blocked this tool call',is_error:true}]}},final]),id,'ours'));
 assert.doesNotThrow(()=>readClaudeEvents(encode([init,{type:'assistant',message:{content:[{type:'text',text:'Permission to use Bash has been denied (quoted fixture)'}]}},final]),id,'ours'));
});
test('provider/remapped model cannot reach Claude billing; credentials not in errors',()=>{
 assert.doesNotThrow(()=>validateClaudeEnvironment({},id));
 assert.doesNotThrow(()=>validateClaudeEnvironment({ANTHROPIC_BASE_URL:'https://api.anthropic.com'},id));
 for(const env of [{ANTHROPIC_BASE_URL:'https://api.z.ai/api/anthropic?secret=REDACT'},{ANTHROPIC_BASE_URL:'https://api.anthropic.com.evil.test'},{ANTHROPIC_BASE_URL:'http://api.anthropic.com'},{ANTHROPIC_MODEL:'glm-5.3'},{ANTHROPIC_DEFAULT_SONNET_MODEL:'glm-5.3'},{CLAUDE_CODE_USE_BEDROCK:'1'},{CLAUDE_CODE_USE_VERTEX:'1'},{ANTHROPIC_AUTH_TOKEN:'REDACT',ANTHROPIC_BASE_URL:'invalid'}]) {
  assert.throws(()=>validateClaudeEnvironment(env,id),e=>!e.message.includes('REDACT'));
 }
 assert.throws(()=>validateClaudeEnvironment({},'sonnet'));
 const settings=claudeSettings('/trusted/guard.mjs');assert.ok(settings.hooks.PreToolUse.length);assert.deepEqual(settings.permissions.allow,['Bash','Read','Grep','Glob']);
});
test('coverage is explicit per changed file; generated evidence grouping cannot hide code',()=>{
 const files=['src/a.ts','docs/prototypes/T/report.json','docs/prototypes/T/check.py'];
 assert.equal(scopeProblems(final.result,files).length>0,true);
 for(const script of ['check.py','check.js','check.ts','check.sh','page.html','component.jsx','extensionless']) assert.ok(scopeProblems(final.result+'\nEVIDENCE: docs/prototypes/T/', ['src/a.ts','docs/prototypes/T/'+script]).length,script);
 const complete=final.result+'\nFILE: docs/prototypes/T/check.py\nEVIDENCE: docs/prototypes/T/';assert.deepEqual(scopeProblems(complete,files),[]);
 assert.ok(scopeProblems(complete.replace('SCOPE: complete','SCOPE: incomplete'),files).length);
 const config={models:{claude:{id:'anthropic/'+id,family:'claude',backend:'claude'}},blocked:[]};
 assert.equal(namedModel(config,'claude',{},()=>assert.fail()),'claude');
 assert.equal(reviewRefusal(config.models,'claude',[],{HARNESS_CLIENT:'claude'}),null);
 assert.equal(reviewRefusal(config.models,'claude',[],{HARNESS_SESSION_FAMILY:'openai'}),null);
 const switched=planSwitch(config,{id:'anthropic/'+id,backend:'claude',name:'claude',sessionFamily:'openai',variant:'high'});assert.equal(switched.entry.backend,'claude');assert.equal(planSwitch(switched.config,{id:'anthropic/'+id,sessionFamily:'openai'}).entry.backend,'claude');assert.throws(()=>planSwitch(config,{id:'openai/gpt-x',backend:'claude',sessionFamily:'minimax'}));
 config.blocked=['claude'];assert.equal(namedModel(config,'claude',{},()=>assert.fail()),'claude');
 const plan=planPost({read:readReview(final.result,'T69 review (Claude)'),header:'T69 review (Claude)',doneWhen:2,source:'test',signature:'test'});assert.equal(plan.code,4);assert.equal(plan.label,null);
});
test('watched subprocess retains success, failure and timeout evidence, kills its own group',async()=>{
 const parentTmp=process.env.TMPDIR;
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'claude-harness-'));
 const fake=path.join(root,'fake.mjs');
 fs.writeFileSync(fake,`import fs from 'node:fs'; const mode=process.env.FAKE_MODE; if(process.env.TMPDIR!==process.env.EXPECTED_TMPDIR || !fs.existsSync(process.env.TMPDIR)) throw Error('child temp directory not isolated'); if(['hang','startup','idle'].includes(mode)){if(mode==='idle')console.log(JSON.stringify(${JSON.stringify(init)}));setInterval(()=>{},1000);}else{console.log(JSON.stringify(${JSON.stringify(init)})); console.log(JSON.stringify(${JSON.stringify(final)}));process.exitCode=mode==='fail'?7:0;}`);
 for(const mode of ['ok','fail','hang','startup','idle']){
  const evidenceDir=path.join(root,mode);const options={command:{exe:process.execPath,prefix:[fake]},args:[],workDir:root,evidenceDir,model:id,sessionId:'ours',env:{...process.env,FAKE_MODE:mode,EXPECTED_TMPDIR:path.join(evidenceDir,'tmp')},startupTimeoutMs:mode==='startup'?150:1000,idleTimeoutMs:mode==='idle'?150:1000,totalTimeoutMs:mode==='hang'?150:3000,log:()=>{}};
  if(mode==='ok')assert.equal((await runClaudeWatched(options)).stdout,final.result);
  else await assert.rejects(runClaudeWatched(options));
  assert.equal(process.env.TMPDIR,parentTmp);
  for(const name of ['stdout.jsonl','stderr.txt','receipt.json','final.md']) assert.ok(fs.existsSync(path.join(evidenceDir,name)),name);
  const receipt=JSON.parse(fs.readFileSync(path.join(evidenceDir,'receipt.json')));assert.equal(receipt.expectedModel,id);assert.ok(receipt.sha256['stdout.jsonl']);
  if(['hang','startup','idle'].includes(mode)){assert.throws(()=>process.kill(receipt.pid,0));assert.match(receipt.failure,new RegExp(mode==='hang'?'total timeout':mode+' timeout'));}
 }
});

test('real review entry selects Claude without OpenCode, publishes once, refuses failed gates', async()=>{
 const { spawnSync } = await import('node:child_process');
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'claude-entry-')), repo=path.join(root,'repo');fs.mkdirSync(repo);
 const git=(...args)=>{const r=spawnSync('git',args,{cwd:repo,encoding:'utf8'});assert.equal(r.status,0,r.stderr);return r.stdout.trim();};
 git('init','-q');git('config','user.email','test@example.invalid');git('config','user.name','fixture');
 fs.writeFileSync(path.join(repo,'a.txt'),'base\n');git('add','.');git('commit','-qm','base');let base=git('rev-parse','HEAD');
 fs.writeFileSync(path.join(repo,'a.txt'),'head\n');git('add','.');git('commit','-qm','head');const head=git('rev-parse','HEAD');
 git('checkout','-qb','base-only',base);fs.writeFileSync(path.join(repo,'base-only.txt'),'not a PR change');git('add','.');git('commit','-qm','base advanced independently');base=git('rev-parse','HEAD');git('checkout','--detach',head);
 git('update-ref','refs/pull/1/head',head);git('remote','add','origin',repo);
 fs.cpSync(new URL('../',import.meta.url),path.join(repo,'tools/harness'),{recursive:true});fs.mkdirSync(path.join(repo,'docs'));fs.copyFileSync(path.resolve('docs/models.md'),path.join(repo,'docs/models.md'));
 fs.mkdirSync(path.join(repo,'node_modules','fake-dependency'),{recursive:true});fs.writeFileSync(path.join(repo,'node_modules','fake-dependency','index.js'),'launcher dependency\n');fs.writeFileSync(path.join(repo,'node_modules','fake-dependency','cli.mjs'),'export {};\n');fs.mkdirSync(path.join(repo,'node_modules','.bin'));fs.symlinkSync('../fake-dependency/cli.mjs',path.join(repo,'node_modules','.bin','fake-dependency'));
 fs.writeFileSync(path.join(repo,'harness.json'),JSON.stringify({worktreeRoot:'work',models:{claude:{id:'anthropic/'+id,family:'claude',backend:'claude',variant:'medium'}},blocked:[],reviewer:{default:'claude',startupTimeoutSec:2,idleTimeoutSec:2,totalTimeoutSec:5}}));
 const brief=path.join(root,'brief.md');fs.writeFileSync(brief,`T69 review (Claude)\nYou review PR #1 at ${head}.\n# T69 fixture\n- **Done when**:\n  1. git diff --check BASE HEAD passes.\n- **Hazards**: none.\n`);
 const gh=path.join(root,'gh.mjs'),cli=path.join(root,'claude.mjs'),trace=path.join(root,'gh-trace');
 fs.writeFileSync(gh,`import fs from 'node:fs'; const a=process.argv.slice(2);if(a.includes('--version')){console.log('gh fake');}else if(a[0]==='pr'&&a[1]==='view'){console.log(a.includes('headRefOid,baseRefOid')?JSON.stringify({headRefOid:process.env.HEAD_SHA,baseRefOid:process.env.BASE_SHA}):'');}else{fs.appendFileSync(process.env.TRACE,JSON.stringify(a)+'\\n');if(a.includes('--body-file'))fs.writeFileSync(process.env.TRACE+'.body',fs.readFileSync(a[a.indexOf('--body-file')+1]));}`);
 fs.writeFileSync(cli,`import fs from 'node:fs';import path from 'node:path';const a=process.argv.slice(2);if(a.includes('--version')){console.log('2.1.292 (Claude Code)');process.exit(0);}const copied=path.join(process.cwd(),'node_modules','fake-dependency','index.js');if(process.env.CASE!=='absent'){if(!fs.existsSync(copied))throw Error('private dependencies not prepared before Claude launch');const bin=path.join(process.cwd(),'node_modules','.bin','fake-dependency');if(fs.readlinkSync(bin)!=='../fake-dependency/cli.mjs'||!fs.realpathSync(bin).startsWith(path.join(process.cwd(),'node_modules')+path.sep))throw Error('relative .bin link not preserved');fs.writeFileSync(copied,'review-owned mutation');}else if(fs.existsSync(copied))throw Error('absent install was fabricated');const v=k=>a[a.indexOf(k)+1];if(v('--setting-sources')!=='')throw Error('settings not isolated');const dir=path.dirname(v('--settings'));const s=JSON.parse(fs.readFileSync(v('--settings')));if(!s.hooks.PreToolUse.length)throw Error('no guard');const inv=JSON.parse(fs.readFileSync(path.join(dir,'inventory.json')));if(JSON.stringify(inv.files)!==JSON.stringify(['a.txt']))throw Error('diff included unrelated base branch changes');if(!fs.readFileSync(path.join(dir,'full.diff'),'utf8').includes('+head'))throw Error('no local diff');const mode=process.env.CASE;console.log(JSON.stringify({type:'system',subtype:'init',session_id:v('--session-id'),model:mode==='wrong'?'glm-5.3':v('--model')}));if(mode==='missing')process.exit(0);const r=['T69 review (Claude)','approve',mode==='dw'?'DW1: not run — fixture':'DW1: ran git diff --check → passed',...(mode==='scope'?[]:inv.files.map(f=>'FILE: '+f)),'SCOPE: complete','R1: test full findings survive flags','Final pass done','approve'].join('\\n');console.log(JSON.stringify({type:'result',subtype:'success',is_error:false,session_id:v('--session-id'),permission_denials:mode==='denied'?[{tool_name:'Bash'}]:[],result:r}));if(mode==='exit')process.exitCode=7;`);
 const seenEvidence=new Set();
 for(const mode of ['ok','same-claude','absent','scope','dw','wrong','missing','denied','exit','jail']){
  fs.writeFileSync(trace,'');
  if(mode==='absent')fs.renameSync(path.join(repo,'node_modules'),path.join(repo,'saved-node_modules'));
  else if(fs.existsSync(path.join(repo,'saved-node_modules')))fs.renameSync(path.join(repo,'saved-node_modules'),path.join(repo,'node_modules'));
  const cfgPath=path.join(repo,'harness.json');const cfg=JSON.parse(fs.readFileSync(cfgPath));cfg.jail={enabled:mode==='jail'};fs.writeFileSync(cfgPath,JSON.stringify(cfg));
  const env={...process.env,HARNESS_GH_EXE:gh,HARNESS_CLAUDE_EXE:cli,HARNESS_OPENCODE_EXE:'/does/not/exist',HARNESS_CLIENT:mode==='same-claude'?'claude':'codex',HEAD_SHA:head,BASE_SHA:base,TRACE:trace,CASE:mode};
  delete env.HARNESS_SESSION_FAMILY;
  for(const k of Object.keys(env))if(k.startsWith('ANTHROPIC_')||k.startsWith('CLAUDE_CODE_USE_'))delete env[k];
  const r=spawnSync(process.execPath,[path.resolve('tools/harness/review.mjs'),'--pr','1','--brief',brief,'--issue','2','--apply-label'],{cwd:repo,env,encoding:'utf8',timeout:15000});
  assert.equal(r.status,['ok','same-claude','absent'].includes(mode)?0:['scope','dw'].includes(mode)?4:3,mode+'\n'+r.stdout+'\n'+r.stderr);
  if(mode==='jail'){assert.match(r.stderr,/does not support the optional credential jail/);assert.ok(fs.readFileSync(trace,'utf8').split('\n').filter(Boolean).map(JSON.parse).every(a=>a[1]==='view'));continue;}
  const evidenceRoot=path.join(repo,'.cache/review-evidence');const fresh=fs.readdirSync(evidenceRoot).find(n=>!seenEvidence.has(n));assert.ok(fresh);seenEvidence.add(fresh);const receipt=JSON.parse(fs.readFileSync(path.join(evidenceRoot,fresh,'receipt.json')));assert.equal(receipt.actualModel,mode==='wrong'?'glm-5.3':id);
  const writes=fs.readFileSync(trace,'utf8').split('\n').filter(Boolean).map(JSON.parse);
  assert.equal(writes.filter(a=>a[0]==='pr'&&a[1]==='comment').length,['ok','same-claude','absent','scope','dw'].includes(mode)?1:0,mode);
  assert.equal(writes.some(a=>a.includes('--add-label')),['ok','same-claude','absent'].includes(mode),mode);
  if(['scope','dw'].includes(mode))assert.match(fs.readFileSync(trace+'.body','utf8'),/R1: test full findings survive flags/);
 }
 const registrationCfg=JSON.parse(fs.readFileSync(path.join(repo,'harness.json')));registrationCfg.reviewer.default='luna';registrationCfg.models.luna={id:'openai/gpt-5.6-luna',family:'openai',variant:'high'};fs.writeFileSync(path.join(repo,'harness.json'),JSON.stringify(registrationCfg));
 const switchEnv={...process.env,HARNESS_CLAUDE_EXE:cli,HARNESS_OPENCODE_EXE:'/does/not/exist',HARNESS_SESSION_FAMILY:'openai'};
 for(const k of Object.keys(switchEnv))if(k.startsWith('ANTHROPIC_')||k.startsWith('CLAUDE_CODE_USE_'))delete switchEnv[k];
 const switchArgs=[path.resolve('tools/harness/switch-model.mjs'),'--role','reviewer','--model','anthropic/'+id,'--backend','claude','--name','claude','--register-only'];
 for(const dry of [true,false]){const before=fs.readFileSync(path.join(repo,'harness.json'),'utf8');const r=spawnSync(process.execPath,[...switchArgs,...(dry?['--dry-run']:[])],{cwd:repo,env:switchEnv,encoding:'utf8',timeout:10000});assert.equal(r.status,0,r.stderr);const after=fs.readFileSync(path.join(repo,'harness.json'),'utf8');if(dry)assert.equal(after,before);assert.equal(JSON.parse(after).reviewer.default,'luna');assert.equal(JSON.parse(after).models.claude.backend,'claude');}
 assert.equal(fs.readFileSync(path.join(repo,'node_modules','fake-dependency','index.js'),'utf8'),'launcher dependency\n');
 assert.equal(git('rev-parse','HEAD'),head);assert.equal(JSON.parse(fs.readFileSync(path.join(repo,'harness.json'))).reviewer.default,'luna');
});

test('Claude dependency materialization makes an independent real copy and preserves relative .bin links', (t) => {
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'review-dependencies-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
 const source=path.join(root,'launcher','node_modules'),worktree=path.join(root,'review-worktree');
 fs.mkdirSync(path.join(source,'sample-package'),{recursive:true});fs.mkdirSync(path.join(source,'.bin'));
 fs.writeFileSync(path.join(source,'sample-package','cli.mjs'),'export const value = 1;\n');
 fs.writeFileSync(path.join(source,'sample-package','data.txt'),'unchanged source bytes\n');
 fs.symlinkSync('../sample-package/cli.mjs',path.join(source,'.bin','sample'));
 fs.mkdirSync(worktree);
 const prepared=materializeReviewDependencies({source,destination:path.join(worktree,'node_modules'),ownedRoot:worktree});
 const copied=path.join(worktree,'node_modules');
 assert.equal(prepared.source,fs.realpathSync(source));assert.equal(prepared.destination,copied);
 assert.ok(fs.statSync(copied).isDirectory());
 assert.equal(fs.readlinkSync(path.join(copied,'.bin','sample')),'../sample-package/cli.mjs');
 assert.equal(fs.readFileSync(path.join(copied,'.bin','sample'),'utf8'),'export const value = 1;\n');
 fs.writeFileSync(path.join(copied,'sample-package','data.txt'),'review-owned mutation\n');
 assert.equal(fs.readFileSync(path.join(source,'sample-package','data.txt'),'utf8'),'unchanged source bytes\n');
});

test('Claude dependency materialization skips absent installs and refuses outside, overlapping, or existing destinations', (t) => {
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'review-dependency-boundaries-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
 const source=path.join(root,'launcher','node_modules'),worktree=path.join(root,'review-worktree');
 fs.mkdirSync(source,{recursive:true});fs.writeFileSync(path.join(source,'dep.txt'),'source');fs.mkdirSync(worktree);
 fs.mkdirSync(path.join(root,'outside'));
 assert.equal(materializeReviewDependencies({source:path.join(root,'missing'),destination:path.join(worktree,'node_modules'),ownedRoot:worktree}),null);
 const danglingSource=path.join(root,'broken-node-modules');fs.symlinkSync(path.join(root,'missing-target'),danglingSource);
 assert.throws(()=>materializeReviewDependencies({source:danglingSource,destination:path.join(worktree,'node_modules'),ownedRoot:worktree}),/does not resolve to a directory/);
 assert.equal(fs.readlinkSync(danglingSource),path.join(root,'missing-target'));
 const escaped=path.join(root,'outside','target');fs.writeFileSync(escaped,'outside');fs.symlinkSync(path.relative(source,escaped),path.join(source,'escaping-link'));
 assert.throws(()=>materializeReviewDependencies({source,destination:path.join(worktree,'node_modules'),ownedRoot:worktree}),/escapes its source tree/);
 assert.equal(fs.existsSync(path.join(worktree,'node_modules')),false);fs.unlinkSync(path.join(source,'escaping-link'));
 assert.throws(()=>materializeReviewDependencies({source,destination:path.join(root,'outside','node_modules'),ownedRoot:worktree}),/outside the owned review root/);
 assert.throws(()=>materializeReviewDependencies({source,destination:path.join(source,'copy'),ownedRoot:root}),/overlap/);
 const existing=path.join(worktree,'node_modules');fs.mkdirSync(existing);fs.writeFileSync(path.join(existing,'sentinel'),'keep');
 assert.throws(()=>materializeReviewDependencies({source,destination:existing,ownedRoot:worktree}),/already exists/);
 assert.equal(fs.readFileSync(path.join(existing,'sentinel'),'utf8'),'keep');fs.rmSync(existing,{recursive:true});
 const dangling=path.join(worktree,'node_modules');fs.symlinkSync(path.join(root,'absent-target'),dangling);
 assert.throws(()=>materializeReviewDependencies({source,destination:dangling,ownedRoot:worktree}),/already exists/);
 assert.equal(fs.readlinkSync(dangling),path.join(root,'absent-target'));
});

test('native Claude command denials cover OpenCode publishing policy without a second Bash parser',()=>{
 const settings=claudeSettings('/trusted/tools/harness/guard.mjs');
 const agent=fs.readFileSync('.opencode/agents/reviewer.md','utf8');
 for(const m of agent.split('  bash:')[1].split('---')[0].matchAll(/^    "([^"]+)": deny$/gm))assert.ok(settings.permissions.deny.includes('Bash('+m[1]+')'),m[1]);
 assert.ok(settings.permissions.deny.includes('Bash(gh api *-X POST*)'));
 assert.equal(settings.hooks.PreToolUse.some(h=>h.matcher.split('|').includes('Bash')),false);
 assert.equal(settings.hooks.PreToolUse.some(h=>h.matcher.split('|').includes('Read')),true);
});
