#!/usr/bin/env node
// Runs one task's (or one fix's) implementer on OpenCode, in a worktree this script creates.
//
//   node tools/harness/implement.mjs --task T07 --slug calendar --issue 12 --brief brief.md [--model NAME]
//   node tools/harness/implement.mjs --fix 34 --slug save-path --brief brief.md
//     [--copy local.ini]...  untracked files copied from the main checkout into the worktree
//     [--env KEY=VALUE]...   environment for the run
//   node tools/harness/implement.mjs --self-test   (the reset's save, on a throwaway repository)
//
// The main session fills the brief (the task file pasted in full, plus review URLs on a rework
// round). This script creates or resumes the branch and worktree, runs OpenCode watched, and checks
// the handover: a PR exists, the worktree is clean, pushed and detached.
//
// The model is harness.json's implementer.chain (one model, by the user's decision of 2026-10-02:
// DeepSeek V4.1 Flash, then Claude Sonnet); --model runs another alone. Runs use the scripts' own
// OpenCode data directory, and a model OpenCode does not list there exits 3 before anything is
// billed. With a longer chain, the next model runs
// only on an infrastructure failure, and only when the failed run left nothing behind (no new
// commit locally or on origin, no new PR), judged against the state before the first attempt, so a
// resumed rework branch can still fall back. An implementer that stops and reports has NOT failed:
// its run exits 0 and is never retried; this script then exits 1 at "no open PR".
//
// Exit 0: PR open. Exit 1: the main session decides (read the log). Exit 3: OpenCode unavailable;
// fall back to a Claude implementer.
//
// When an attempt fails and left nothing behind, the reset between attempts first saves the
// worktree's uncommitted changes (staged, unstaged and untracked) to
// <workRoot>/<name>.<model key>.<UTC time>.unsaved.patch, a file created exclusively (#87): an
// implementer that edited files without committing before a rejected tool call ended its run keeps
// that work. The exit 1 and exit 3 messages name every patch the run saved.

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { runOpenCodeWatched, resolveOpenCode, OpenCodeInfraError } from './lib/opencode.mjs';
import { runChain } from './lib/chain.mjs';
import {
  sh, requireTools, repoPaths, loadConfig, parseArgs, envWith, ensureAgent, ocArgs, prepareOpenCode, watchLine,
} from './lib/common.mjs';

const say = (s) => console.log(s);
const die = (code, s) => { console.error(s); process.exit(code); };

// The reset's save (#87): on T13 round 3 an implementer edited five files without committing, a
// rejected tool call ended its run, and the reset discarded all of it. Before the reset destroys
// the worktree's state, what the attempt left uncommitted is written to one binary patch.

/**
 * Saves the worktree's uncommitted changes (staged, unstaged and untracked) against the run's
 * start commit, to <workRoot>/<name>.<model key>.<UTC time>.unsaved.patch — a file created
 * exclusively ('.1', '.2', … if the same millisecond ever collides), never an overwrite — and
 * logs its path. Returns the patch's path, or null when the worktree is clean: nothing changed,
 * no file. `stamp` exists for tests.
 */
export function saveUnsavedWork({ worktree, startSha, workRoot, name, model, log = () => {}, stamp = new Date() }) {
  if (!sh('git', ['-C', worktree, 'status', '--porcelain'])) return null;
  sh('git', ['-C', worktree, 'add', '-A']);
  // sh() trims stdout, which would corrupt a patch's last line; the diff goes through its own
  // spawn, raw and binary-safe.
  const d = spawnSync('git', ['-C', worktree, 'diff', '--cached', '--binary', startSha], { encoding: 'buffer' });
  if (d.error) throw new Error(`git diff could not run: ${d.error.message}`);
  if (d.status !== 0) throw new Error(`git diff --cached --binary ${startSha} failed (${d.status}):\n${d.stderr}`);
  const diff = d.stdout;
  const stampText = stamp.toISOString().replaceAll(':', '-');
  let file = null;
  for (let i = 0; !file; i++) {
    const p = path.join(workRoot, `${name}.${model}.${stampText}${i ? `.${i}` : ''}.unsaved.patch`);
    try {
      const fd = fs.openSync(p, 'wx');
      try { fs.writeFileSync(fd, diff); } finally { fs.closeSync(fd); }
      file = p;
    } catch (e) {
      if (e.code !== 'EEXIST' || i >= 100) throw e;
    }
  }
  log(`unsaved work saved to: ${file}`);
  return file;
}

/**
 * The reset between chain attempts: first save what the failed attempt left uncommitted (above),
 * then hard-reset to the start commit and drop untracked files, as before. Returns the patch's
 * path from saveUnsavedWork, or null when there was nothing to save.
 */
export function resetWorktree({ worktree, startSha, workRoot, name, model, log, stamp }) {
  const patch = saveUnsavedWork({ worktree, startSha, workRoot, name, model, log, stamp });
  sh('git', ['-C', worktree, 'reset', '-q', '--hard', startSha]);
  sh('git', ['-C', worktree, 'clean', '-q', '-fd']);
  return patch;
}

// --self-test: the reset's save, on a throwaway repository, with no OpenCode, gh or network. A
// tracked change and an untracked file must survive resetWorktree in one patch that applies
// cleanly to the start commit and restores both; a clean worktree must write no file; and a save
// must never overwrite an earlier one. Fails when the save is removed.
export function selfTest() {
  const failures = [];
  const ok = (what, cond) => { if (!cond) failures.push(what); };
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'implement-selftest-'));
  const saves = path.join(dir, 'saves'); // outside the repo, as workRoot always is
  const repo = path.join(dir, 'repo');
  try {
    fs.mkdirSync(repo);
    const git = (...args) => sh('git', ['-C', repo, ...args]);
    git('init', '-q');
    git('config', 'user.email', 'selftest@invalid');
    git('config', 'user.name', 'selftest');
    git('config', 'commit.gpgsign', 'false');
    fs.writeFileSync(path.join(repo, 'tracked.txt'), 'one\n');
    git('add', '-A');
    git('commit', '-q', '-m', 'start');
    const startSha = git('rev-parse', 'HEAD');
    fs.mkdirSync(saves);
    const reset = (o) => resetWorktree({ worktree: repo, startSha, workRoot: saves, name: 'selftest', model: 'test-model', log: () => {}, ...o });
    const stamp = new Date('2026-10-05T12:00:00Z');

    fs.writeFileSync(path.join(repo, 'tracked.txt'), 'one\ntwo\n');
    fs.writeFileSync(path.join(repo, 'untracked.txt'), 'fresh\n');
    const patch = reset({ stamp });
    const want = path.join(saves, 'selftest.test-model.2026-10-05T12-00-00.000Z.unsaved.patch');
    ok(`the patch is written where the naming says (${patch} vs ${want})`, patch === want && fs.existsSync(want));
    if (patch !== want || !fs.existsSync(want)) return failures; // no patch: the rest cannot run
    ok('the worktree is clean after the reset', git('status', '--porcelain') === '');
    try { git('apply', '--check', want); } catch (e) { failures.push(`the patch does not apply cleanly: ${e.message}`); }
    git('apply', want);
    ok('the tracked change is restored', fs.readFileSync(path.join(repo, 'tracked.txt'), 'utf8') === 'one\ntwo\n');
    ok('the untracked file is restored', fs.readFileSync(path.join(repo, 'untracked.txt'), 'utf8') === 'fresh\n');

    // The worktree is dirty again (the patch was applied): a reset saves it under the new stamp.
    reset({ stamp: new Date('2026-10-05T12:00:01Z') });
    // Nothing changed now: no file, even though the first stamp's name is already taken.
    ok('a clean worktree writes no file', reset({ stamp }) === null && fs.readdirSync(saves).length === 2);
    // The first stamp again: another name ('.1'), never an overwrite of the first patch.
    fs.writeFileSync(path.join(repo, 'tracked.txt'), 'one\ntwo\nthree\n');
    const second = reset({ stamp });
    ok(`a second save takes another name, not an overwrite (${second})`,
      second === path.join(saves, 'selftest.test-model.2026-10-05T12-00-00.000Z.1.unsaved.patch'));
    ok('the second patch holds the second change', second !== null && fs.readFileSync(second, 'utf8').includes('three'));
    ok('the first patch is intact', fs.readFileSync(want, 'utf8').includes('two') && !fs.readFileSync(want, 'utf8').includes('three'));
    ok('exactly the three expected patches exist', fs.readdirSync(saves).length === 3);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
  return failures;
}

const a = parseArgs(process.argv.slice(2), { flags: ['self-test'], repeatable: ['copy', 'env'] });
if (a['self-test']) {
  const failures = selfTest();
  for (const f of failures) console.error(`FAIL ${f}`);
  say(`self-test: ${failures.length ? `${failures.length} checks failed` : 'all checks passed'}`);
  process.exit(failures.length ? 1 : 0);
}
if (!a.task === !a.fix) die(2, 'Give exactly one of --task T<nn> or --fix <issue>.');
if (a.task && !/^T\d{2,3}$/.test(a.task)) die(2, `--task must look like T07; got ${a.task}`);
if (!a.slug || !a.brief) die(2, '--slug and --brief are required.');
if (!fs.existsSync(a.brief)) die(2, `Brief not found: ${a.brief}`);

let opencode;
try { opencode = resolveOpenCode(); } catch (e) {
  if (e instanceof OpenCodeInfraError) die(3, `OpenCode unavailable: ${e.message} Fall back to a Claude implementer (see harness.json).`);
  throw e;
}
requireTools('git', 'gh');

const top0 = sh('git', ['rev-parse', '--show-toplevel']);
const config = loadConfig(top0);
const { top, commonDir, mainRoot, workRoot } = repoPaths(config);
const impl = config.implementer;
const chain = a.model ? [a.model] : impl.chain;
for (const m of chain) if (!config.models[m]) die(2, `Unknown model ${m}; harness.json lists ${Object.keys(config.models).join(', ')}.`);
const fallback = `Fall back to a Claude implementer (${impl.claudeFallback ?? 'sonnet'}).`;
const pre = await prepareOpenCode({ opencode, chain, models: config.models, env: envWith(a.env), cwd: top, log: say });
for (const p of pre.problems) say(p);
if (!pre.usable.length) die(3, `OpenCode unavailable: ${pre.problems.join('; ')}. ${fallback}`);

const name = a.task ?? `fix-${a.fix}`;
const branch = a.task ? `task/${a.task}-${a.slug}` : `fix/${a.fix}-${a.slug}`;
const issue = a.issue ?? a.fix;
const worktree = path.join(workRoot, name);
const logFile = path.join(workRoot, `${name}.implementer.log`);
fs.mkdirSync(workRoot, { recursive: true });

// 1. The worktree and branch: resume a pushed branch, otherwise start from origin/main and push.
sh('git', ['-C', top, 'fetch', '-q', 'origin']);
const remoteHas = sh('git', ['-C', top, 'ls-remote', '--heads', 'origin', branch]);
if (fs.existsSync(worktree)) {
  if (sh('git', ['-C', worktree, 'rev-parse', '--abbrev-ref', 'HEAD']) !== branch) sh('git', ['-C', worktree, 'checkout', '-q', branch]);
} else if (remoteHas) {
  sh('git', ['-C', top, 'worktree', 'add', worktree, branch]);
} else {
  sh('git', ['-C', top, 'worktree', 'add', '-b', branch, worktree, 'origin/main']);
  sh('git', ['-C', worktree, 'push', '-q', '-u', 'origin', branch]);
}
if (remoteHas) sh('git', ['-C', worktree, 'merge', '-q', '--ff-only', `origin/${branch}`]);
for (const f of a.copy) fs.copyFileSync(path.join(mainRoot, f), path.join(worktree, f));
ensureAgent({ top, commonDir, worktree, agent: impl.agent });
say(`worktree: ${worktree} on ${branch}`);

// 2. The run.
const prompt = `${fs.readFileSync(a.brief, 'utf8')}

---
RUN RULES (from tools/harness/implement.mjs; they override the brief where they conflict):
- Your worktree is ${worktree} on branch ${branch}, already created and pushed. Never run
  git worktree. Pass git -C "${worktree}" explicitly.
- Everything else in the brief is binding: Owns, Done when, the PR body, the detach, the report.
- The PR body's "Closes #${issue}" is the only place a closing keyword may precede #<n>.
`;
const openPr = () => sh('gh', ['pr', 'list', '--head', branch, '--state', 'open', '--json', 'number', '--jq', '.[0].number'], { cwd: top, allowFail: true });
const originSha = () => sh('git', ['-C', top, 'rev-parse', `origin/${branch}`], { allowFail: true });
const startSha = sh('git', ['-C', worktree, 'rev-parse', 'HEAD']);
const startRemote = originSha();
const startPr = openPr();
const patches = []; // the unsaved-work patches this run's resets wrote, in save order
let attemptModel = null; // the chain key of the attempt whose uncommitted work reset saves
fs.writeFileSync(logFile, '');

// The implementer runs on the agent copied into its worktree, so it must not inherit the reviewer's
// settings (review.mjs, L34) from a session that ran a review: OPENCODE_DISABLE_PROJECT_CONFIG would
// hide that agent, and OPENCODE_CONFIG_DIR would put another in its place.
const { OPENCODE_CONFIG_DIR: _dir, OPENCODE_DISABLE_PROJECT_CONFIG: _off, ...implementEnv } = pre.env;

const result = await runChain({
  chain: pre.usable,
  log: say,
  attempt: async (m) => {
    attemptModel = m;
    const model = config.models[m];
    const watch = watchLine(m, model);
    if (watch) say(watch);
    let reason = null;
    let output;
    try {
      const run = await runOpenCodeWatched({
        args: ocArgs(worktree, impl.agent, model), prompt, workDir: worktree, title: `${name}-${m}`,
        startupTimeoutMs: impl.startupTimeoutSec * 1000, idleTimeoutMs: impl.idleTimeoutSec * 1000,
        totalTimeoutMs: impl.totalTimeoutSec * 1000, opencode, env: implementEnv, log: say,
      });
      output = run.output;
      if (run.exitCode !== 0) reason = `exit ${run.exitCode}`;
      else if (run.agentFallback) reason = 'fell back to the default agent';
      else if (run.permissionRejected) reason = `permission rejected: ${run.permissionRejected}${run.permissionHint ? `; ${run.permissionHint}` : ''}`;
    } catch (e) {
      if (!(e instanceof OpenCodeInfraError)) throw e;
      reason = e.reason;
      output = e.message;
    }
    fs.appendFileSync(logFile, `=== ${m} (${model.id}): ${reason ? `failed: ${reason}` : 'ran'} ===\n${watch ? `${watch}\n` : ''}${output}\n`);
    return reason ? { ok: false, reason } : { ok: true, value: output };
  },
  leftWork: async () => {
    sh('git', ['-C', top, 'fetch', '-q', 'origin']);
    const pr = openPr();
    return sh('git', ['-C', worktree, 'rev-parse', 'HEAD']) !== startSha
      || originSha() !== startRemote || (pr && pr !== startPr);
  },
  reset: async () => {
    // Before the hard reset destroys it: the failed attempt's uncommitted work goes to a patch
    // (saveUnsavedWork, above), so a run a rejected tool call ended is not lost twice (#87).
    const patch = resetWorktree({ worktree, startSha, workRoot, name, model: attemptModel, log: say });
    if (patch) patches.push(patch);
  },
});

say(`run log: ${logFile}`);
const reasons = result.failures.map((f) => `${f.name}: ${f.reason}`).join('; ');
const savedNote = patches.length ? ` Unsaved work was saved before the reset: ${patches.join(', ')}.` : '';
if (!result.ok) {
  if (result.leftWork) die(1, `The run failed (${reasons}) after committing, pushing or opening a PR on ${branch}; not retrying. The main session decides.${savedNote}`);
  die(3, `OpenCode unavailable: ${result.sameCause ? `same failure twice: ${result.sameCause} (${reasons})` : reasons}. ${fallback}${savedNote}`);
}
if (reasons) say(`fell back: ${reasons}`);
// The reviewer must not be this model's family: pass it to review.mjs as --exclude.
say(`implemented by: ${result.name} (${config.models[result.name].id})`);

// 3. The handover: a PR, and a clean, pushed, detached worktree.
sh('git', ['-C', top, 'fetch', '-q', 'origin']);
const pr = sh('gh', ['pr', 'list', '--head', branch, '--state', 'open', '--json', 'number,url', '--jq', '.[0].url'], { cwd: top, allowFail: true });
if (sh('git', ['-C', worktree, 'status', '--porcelain'])) console.warn(`warning: uncommitted changes remain in ${worktree}`);
if (sh('git', ['-C', worktree, 'rev-parse', 'HEAD']) !== originSha()) console.warn(`warning: ${worktree}'s HEAD is not pushed to origin/${branch}`);
sh('git', ['-C', worktree, 'checkout', '-q', '--detach']);
say('--- tail of the run ---');
say(result.value.split(/\r?\n/).slice(-40).join('\n'));
if (!pr) die(1, `No open PR for ${branch}. Read ${logFile}: an implementer that stopped and reported is not a failure.`);
say(`PR: ${pr}`);
