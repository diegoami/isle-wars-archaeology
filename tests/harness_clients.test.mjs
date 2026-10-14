import test from 'node:test';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { sessionFamily } from '../tools/harness/lib/common.mjs';
import { selectOpenCode } from '../tools/harness/lib/opencode.mjs';

test('Codex markers and explicit client preserve Claude endpoint routing', () => {
  assert.equal(sessionFamily({ CODEX_THREAD_ID: 'thread' }), 'openai');
  assert.equal(sessionFamily({ CODEX_SESSION_ID: 'session', ANTHROPIC_BASE_URL: 'https://api.z.ai' }), 'openai');
  assert.equal(sessionFamily({ HARNESS_CLIENT: 'codex' }), 'openai');
  assert.equal(sessionFamily({ HARNESS_CLIENT: 'claude', CODEX_THREAD_ID: 'thread', ANTHROPIC_BASE_URL: 'https://api.z.ai' }), 'glm');
  assert.equal(sessionFamily({ CODEX_HOME: '/config' }), 'claude');
  assert.equal(sessionFamily({}), 'claude');
  assert.equal(sessionFamily({ ANTHROPIC_BASE_URL: 'https://api.minimax.io' }), 'minimax');
  assert.equal(sessionFamily({ ANTHROPIC_BASE_URL: 'https://api.z.ai.evil.example' }), null);
  assert.equal(sessionFamily({ HARNESS_CLIENT: 'unknown' }), null);
  assert.equal(sessionFamily({ HARNESS_CLIENT: 'codex', HARNESS_SESSION_FAMILY: 'Claude' }), 'claude');
});

test('broken, missing, unsupported and hanging primary use supported backup; healthy primary stays', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'iwa-cli-test-'));
  try {
    const primary = path.join(dir, 'primary.mjs');
    const backup = path.join(dir, 'backup.mjs');
    fs.writeFileSync(backup, "console.log('1.18.32');");
    const env = { ...process.env, HOME: dir, PATH: '', HARNESS_OPENCODE_EXE: primary, HARNESS_OPENCODE_BAK: backup };
    const select = () => selectOpenCode(env, { timeoutMs: 300 });
    assert.deepEqual((await select()).prefix, [backup]);
    for (const script of ["process.exit(1)", "console.log('2.0.0')", 'setInterval(() => {}, 1000)']) {
      fs.writeFileSync(primary, script);
      assert.deepEqual((await select()).prefix, [backup]);
    }
    fs.writeFileSync(primary, "console.log('1.18.34')");
    assert.deepEqual((await select()).prefix, [primary]);
    fs.writeFileSync(primary, 'process.exit(1)');
    fs.writeFileSync(backup, "console.log('2.0.0')");
    await assert.rejects(select(), /not supported/);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('plain and versioned sibling backups are discovered', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'iwa-backup-test-'));
  try {
    const primary = path.join(dir, 'opencode');
    const backup = path.join(dir, 'opencode.bak');
    fs.writeFileSync(primary, '#!/bin/sh\nexit 1\n', { mode: 0o755 });
    fs.writeFileSync(backup, '#!/bin/sh\necho 1.18.32\n', { mode: 0o755 });
    const env = { HOME: dir, PATH: dir };
    assert.equal((await selectOpenCode(env)).exe, backup);
    const versioned = path.join(dir, 'opencode.1.18.32.bak');
    fs.renameSync(backup, versioned);
    assert.equal((await selectOpenCode(env)).exe, versioned);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('direct read failure retries without corrupt output; model run never replays', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'iwa-wrapper-test-'));
  try {
    const primary = path.join(dir, 'primary.mjs');
    const backup = path.join(dir, 'backup.mjs');
    const marker = path.join(dir, 'backup-called');
    fs.writeFileSync(primary, "if(process.argv[2]==='--version') console.log('1.18.34'); else { console.log('partial JSON'); process.exit(1); }");
    fs.writeFileSync(backup, `import fs from 'node:fs'; if(process.argv[2]==='--version') console.log('1.18.32'); else { fs.writeFileSync(${JSON.stringify(marker)}, 'yes'); console.log('{"info":{"id":"ses_test"}}'); }`);
    const env = { ...process.env, OPENCODE_BIN: '', HARNESS_OPENCODE_EXE: primary, HARNESS_OPENCODE_BAK: backup };
    const wrapper = fileURLToPath(new URL('../tools/harness/opencode.mjs', import.meta.url));
    const read = spawnSync(process.execPath, [wrapper, 'export', 'ses_test'], { env, encoding: 'utf8', timeout: 10000 });
    assert.equal(read.status, 0, read.stderr);
    assert.equal(JSON.parse(read.stdout).info.id, 'ses_test');
    fs.unlinkSync(marker);
    const run = spawnSync(process.execPath, [wrapper, 'run'], { env, encoding: 'utf8', timeout: 10000 });
    assert.equal(run.status, 1);
    assert.equal(fs.existsSync(marker), false);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});
