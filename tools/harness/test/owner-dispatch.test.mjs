// Offline entry-point checks: every CLI call uses these local fake executables.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
const roster = JSON.parse(fs.readFileSync(new URL('../../../harness.json', import.meta.url)));
test('same-family choices complete fake OpenCode dispatch from both actual clients with labels and exclude', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'iwa-owner-dispatch-'));
  const repo = path.join(root, 'repo'); fs.mkdirSync(repo);
  const git = (...args) => { const r = spawnSync('git', args, { cwd: repo, encoding: 'utf8' }); assert.equal(r.status, 0, r.stderr); };
  git('init', '-q'); git('config', 'user.name', 'fixture'); git('config', 'user.email', 'fixture@example.invalid');
  fs.writeFileSync(path.join(repo, 'fixture.txt'), 'base'); git('add', 'fixture.txt'); git('commit', '-qm', 'fixture');
  const head = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: repo, encoding: 'utf8' }).stdout.trim();
  git('update-ref', 'refs/pull/1/head', head); git('remote', 'add', 'origin', repo);
  fs.mkdirSync(path.join(repo, '.opencode', 'agents'), { recursive: true });
  fs.writeFileSync(path.join(repo, '.opencode', 'agents', 'reviewer.md'), 'synthetic reviewer');
  const gh = path.join(root, 'gh.mjs'), cli = path.join(root, 'opencode.mjs'), trace = path.join(root, 'trace');
  const ghTrace = path.join(root, 'gh-trace');
  fs.writeFileSync(gh, `import fs from 'node:fs';const a=process.argv.slice(2);if(a.includes('--version'))console.log('fake gh');else if(a[0]==='pr'&&a[1]==='view')console.log(a.includes('headRefOid,baseRefOid')?JSON.stringify({headRefOid:process.env.HEAD_SHA,baseRefOid:process.env.HEAD_SHA}):'model:'+process.env.FIXTURE_KEY);else fs.appendFileSync(process.env.GH_TRACE,JSON.stringify(a)+'\\n');`);
  fs.writeFileSync(cli, `import fs from 'node:fs';const a=process.argv.slice(2);fs.appendFileSync(process.env.TRACE,JSON.stringify(a)+'\\n');if(a.includes('--version'))console.log('1.18.34');else if(a[0]==='models')console.log(process.env.FIXTURE_MODEL);else if(a[0]==='run'){const val=k=>a[a.indexOf(k)+1];if(val('--model')!==process.env.FIXTURE_MODEL)throw Error('model changed');fs.writeFileSync(process.env.SESSION_FILE,JSON.stringify({id:'ses_fixture',title:val('--title'),directory:process.cwd(),created:Date.now(),updated:Date.now()}));console.log(['T62 review (offline)','approve','Final pass done','approve'].join('\\n'));}else if(a[0]==='session')console.log('['+fs.readFileSync(process.env.SESSION_FILE,'utf8')+']');else if(a[0]==='export')console.log(JSON.stringify({info:{agent:'reviewer'},messages:[]}));else throw Error('unexpected CLI operation');`);
  const brief = path.join(root, 'brief.md'); fs.writeFileSync(brief, 'T62 review (offline)\n');
  const script = new URL('../review.mjs', import.meta.url).pathname;
  for (const [client, key, family] of [['claude', 'claude-sonnet', 'claude'], ['codex', 'luna', 'openai']]) {
    const entry = { ...roster.models[key] }; delete entry.backend;
    fs.writeFileSync(path.join(repo, 'harness.json'), JSON.stringify({ models: { [key]: entry }, reviewer: { default: key, agent: 'reviewer', startupTimeoutSec: 2, idleTimeoutSec: 2, totalTimeoutSec: 5 }, blocked: [family, entry.id.split('/').at(-1)] }));
    for (const exclude of [false, true]) {
      fs.writeFileSync(trace, ''); fs.writeFileSync(ghTrace, '');
      const env = { ...process.env, HARNESS_CLIENT: client, HARNESS_GH_EXE: gh, HARNESS_OPENCODE_EXE: cli, HARNESS_OPENCODE_HOME: path.join(root, 'oc-home'), HARNESS_OPENCODE_AUTH_SOURCE: path.join(root, 'absent-auth.json'), TRACE: trace, FIXTURE_KEY: key, FIXTURE_MODEL: entry.id, HEAD_SHA: head, GH_TRACE: ghTrace, SESSION_FILE: path.join(root, 'session.json') };
      delete env.HARNESS_SESSION_FAMILY; delete env.ANTHROPIC_BASE_URL;
      const r = spawnSync(process.execPath, [script, '--pr', '1', '--brief', brief, '--reviewer', key, ...(exclude ? ['--exclude', key] : [])], { cwd: repo, env, encoding: 'utf8', timeout: 10000 });
      assert.equal(r.status, 0, r.stdout+'\n'+r.stderr);
      assert.match(r.stdout, new RegExp('implemented by: '+family));
      assert.equal(fs.readFileSync(ghTrace, 'utf8').split('\n').filter(Boolean).map(JSON.parse).filter(args => args[0] === 'pr' && args[1] === 'comment').length, 1);
      assert.ok(fs.readFileSync(trace, 'utf8').split('\n').filter(Boolean).map(JSON.parse).some(args => args[0] === 'run' && args[args.indexOf('--model')+1] === entry.id), client);
    }
  }
  // Retain scratch under /tmp, matching repository worktree/evidence retention rules.
});
