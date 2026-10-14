#!/usr/bin/env node
// Shared entry point for direct calls; run failures require diagnosis, never automatic replay.
import { spawn } from 'node:child_process';
import { selectOpenCode, backupOpenCodes } from './lib/opencode.mjs';
const args = process.argv.slice(2);
const env = { ...process.env, ...(process.env.OPENCODE_BIN ? { HARNESS_OPENCODE_EXE: process.env.OPENCODE_BIN } : {}) };
try {
  const selected = await selectOpenCode(env, { cwd: process.cwd(), log: s => console.error(s) });
  const readOnly = ['models', 'export', '--version'].includes(args[0]);
  const invoke = cmd => new Promise(resolve => {
    const output = [];
    const child = spawn(cmd.exe, [...cmd.prefix, ...args], { env, stdio: ['ignore', readOnly ? 'pipe' : 'inherit', 'inherit'] });
    child.stdout?.on('data', chunk => output.push(chunk));
    child.on('error', () => resolve(1));
    child.on('close', code => {
      if (code === 0 && readOnly) process.stdout.write(Buffer.concat(output));
      resolve(code ?? 1);
    });
  });
  let code = await invoke(selected);
  // These commands only read; a CLI failure can safely be retried against a backup.
  if (code && readOnly) {
    for (const backup of backupOpenCodes(env, selected)) {
      if (JSON.stringify(backup) === JSON.stringify(selected)) continue;
      try {
        const cmd = await selectOpenCode({ ...env, HARNESS_OPENCODE_EXE: backup.prefix[0] || backup.exe,
          HARNESS_OPENCODE_BAK: backup.prefix[0] || backup.exe }, { log: s => console.error(s) });
        console.error('opencode: retrying read-only command with backup');
        code = await invoke(cmd);
        if (!code) break;
      } catch { /* next supported backup */ }
    }
  }
  process.exitCode = code;
} catch (e) { console.error(e.message); process.exitCode = 3; }
