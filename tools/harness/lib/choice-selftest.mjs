// The model-choice self-test (CLAUDE.md rule 6, the owner, 2026-10-11): run by
// `node tools/harness/review.mjs --self-test`, so CI runs it. No model is called; OpenCode is a fake
// shell script. It pins Sol's findings on PR 164: a model's family is never taken from a declaration
// (R1 of both rounds), an implementer name always resolves to a family (R2), a foreign session is
// refused before anything is sent (R3), and a resumed session is watched by its id (re-review R2).

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { namedModel, familyOf } from './common.mjs';
import { runOpenCodeWatched } from './opencode.mjs';

const MODELS = () => ({
  'gpt-6.1-sol': { id: 'openai/gpt-6.1-sol', family: 'openai' },
  luna: { id: 'openai/gpt-5.6-luna', family: 'openai' },
  'mm-m3': { id: 'minimax/MiniMax-M3', family: 'minimax' },
  'ali-glm': { id: 'alibaba-token-plan/glm-5.3', family: 'glm' },
});

// [label, name, options, expected family or 'refused']
const NAMED = [
  ['registered key', 'gpt-6.1-sol', {}, 'openai'],
  ['registered id, false family', 'openai/gpt-6.1-sol', { family: 'qwen' }, 'refused'],
  ['registered id, no family', 'openai/gpt-6.1-sol', {}, 'openai'],
  ['single-family provider, unrecognised name, false family', 'openai/chatgpt-4o-latest', { family: 'qwen' }, 'refused'],
  ['single-family provider, unrecognised name', 'openai/chatgpt-4o-latest', {}, 'openai'],
  ['single-family provider, contradicting name', 'openai/glm-9', {}, 'refused'],
  ['multi-family route, recognised name', 'openrouter/xiaomi/mimo-v2.6-pro', {}, 'mimo'],
  ['multi-family route, unrecognised name, declared family', 'openrouter/acme/zeta-1', { family: 'zeta' }, 'refused'],
  ['unknown provider, unrecognised name', 'acme/zeta-1', {}, 'refused'],
  ['DeepSeek on any route', 'openrouter/deepseek/deepseek-v4-pro', {}, 'refused'],
  ['Alibaba without --alibaba', 'ali-glm', {}, 'refused'],
  ['Alibaba with --alibaba', 'ali-glm', { alibaba: true }, 'glm'],
  ['not a key, not an id', 'nonsense', {}, 'refused'],
];

// [implementer name, expected family or null]
const IMPLEMENTERS = [
  ['gpt-6.1-sol', 'openai'], ['openai/gpt-6.1-sol', 'openai'], ['openai/chatgpt-4o-latest', 'openai'],
  ['claude', 'claude'], ['openrouter/acme/zeta-1', null], ['nonsense', null],
];

function checkNamed(failures) {
  for (const [label, name, opts, want] of NAMED) {
    const config = { models: MODELS() };
    let got;
    try {
      const key = namedModel(config, name, opts, (code, msg) => { throw Object.assign(new Error(msg), { refused: code }); });
      got = config.models[key].family;
    } catch (e) {
      if (e.refused === undefined) throw e;
      got = 'refused';
    }
    if (got !== want) failures.push(`namedModel: ${label} (${name}): ${got}, expected ${want}`);
  }
  for (const [name, want] of IMPLEMENTERS) {
    const got = familyOf(MODELS(), name);
    if (got !== want) failures.push(`familyOf(${name}): ${got}, expected ${want}`);
  }
}

// A fake `opencode`: `session list` prints one session, updated now, in `dir`; `run` writes a
// marker file, then lives for `runMs` and exits 0.
function fakeOpenCode(root, { sessionDir, runMs }) {
  const exe = path.join(root, 'opencode');
  fs.writeFileSync(exe, `#!/bin/sh
if [ "$1" = session ]; then
  now=$(( $(date +%s) * 1000 ))   # whole seconds: not every date(1) supports %3N
  echo '[{"id":"ses_own","title":"first-title","directory":"${sessionDir}","created":1,"updated":'$now'}]'
  exit 0
fi
echo dispatched > "${root}/dispatched"
sleep ${runMs / 1000}
exit 0
`, { mode: 0o755 });
  return { exe, prefix: [] };
}

async function checkResume(failures) {
  const root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'harness-choice-')));
  try {
    fs.mkdirSync(path.join(root, 'wd'));
    const wd = fs.realpathSync(path.join(root, 'wd'));
    const other = path.join(root, 'other');
    fs.mkdirSync(other);
    const base = { args: ['run', '--dir', wd], prompt: 'continue', workDir: wd, title: 'resume-test', resumeSessionId: 'ses_own', logDir: root };

    // R3: a session made in another directory is refused before `run` is spawned.
    let refused = false;
    try {
      await runOpenCodeWatched({ ...base, opencode: fakeOpenCode(root, { sessionDir: other, runMs: 100 }) });
    } catch { refused = true; }
    if (!refused) failures.push('resume: a foreign session was not refused');
    if (fs.existsSync(path.join(root, 'dispatched'))) failures.push('resume: a foreign session was dispatched before the check');

    // Re-review R2: our own session, active for 3 s with a 1.5 s idle limit, runs to its exit.
    fs.rmSync(path.join(root, 'dispatched'), { force: true });
    try {
      const run = await runOpenCodeWatched({
        ...base, opencode: fakeOpenCode(root, { sessionDir: wd, runMs: 3000 }),
        idleTimeoutMs: 1500, pollMs: 200, startupTimeoutMs: 5000, totalTimeoutMs: 20_000,
      });
      if (run.exitCode !== 0) failures.push(`resume: an active resumed session exited ${run.exitCode}`);
    } catch (e) {
      failures.push(`resume: an active resumed session was killed: ${e.message}`);
    }
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
}

export async function choiceSelfTest() {
  const failures = [];
  checkNamed(failures);
  await checkResume(failures);
  return { failures, count: NAMED.length + IMPLEMENTERS.length + 3 };
}
