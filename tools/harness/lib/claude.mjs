// Claude CLI backend. It shares the review parser/poster; it never posts or changes defaults.
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

export class ClaudeInfraError extends Error {}
const fail = (message) => { throw new ClaudeInfraError(message); };
export const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
export function validateClaudeEnvironment(env, model) {
  if (!/^claude-(?:sonnet|opus|haiku|fable)-[a-z0-9.-]+$/.test(model)) fail('Select an exact Claude model ID discovered from the live CLI, not an alias.');
  if (env.ANTHROPIC_BASE_URL) {
    let url;
    try { url = new URL(env.ANTHROPIC_BASE_URL); } catch { fail('Invalid ANTHROPIC_BASE_URL (value withheld).'); }
    if (url.origin !== 'https://api.anthropic.com' || url.username || url.password || url.search || url.hash || !['', '/', '/v1', '/v1/'].includes(url.pathname)) fail('Claude requires the direct Anthropic endpoint; provider override refused (value withheld).');
  }
  for (const [key, value] of Object.entries(env)) {
    if (/^CLAUDE_CODE_USE_(?:BEDROCK|VERTEX|FOUNDRY)$/.test(key) && value && value !== '0') fail(`Claude provider override ${key} refused.`);
    if (/^ANTHROPIC_(?:MODEL|DEFAULT_.*_MODEL)$/.test(key) && value && value !== model) fail(`Model remapping ${key} refused; use an environment without provider/model overrides.`);
  }
}
export function claudeSettings(guard) {
  // No user/project/local settings loaded. Only this trusted launcher's hook is installed.
  const quote = (s) => `'${s.replaceAll("'", "'\\''")}'`;
  const publishing = ['git push *', 'git -C * push *', 'git commit *', 'git -C * commit *',
    'git push', 'git commit', 'git * push*', 'git * commit*',
    ...['merge', 'comment', 'review', 'edit', 'create', 'close', 'reopen'].map((v) => `gh pr ${v} *`),
    ...['edit', 'comment', 'create', 'close', 'reopen', 'delete', 'transfer'].map((v) => `gh issue ${v} *`),
    'gh run rerun *', 'gh run cancel *', 'gh workflow run *',
    ...['POST', 'PATCH', 'PUT', 'DELETE'].flatMap((v) => [`gh api *-X ${v}*`, `gh api *-X${v}*`, `gh api *--method ${v}*`, `gh api *--method=${v}*`]),
    'gh api *-f*', 'gh api *-F*', 'gh api *--input*'];
  // Preserve this research project's read-only static-folder mistake safeguards.
  const staticWrites = ['rm', 'rmdir', 'unlink', 'mv', 'cp', 'touch', 'mkdir', 'chmod', 'chown', 'truncate', 'tee']
    .flatMap((cmd) => [`${cmd} *isle-wars-archaeology/static*`, `${cmd} *IWA_STATIC*`]);
  staticWrites.push('sed -i*isle-wars-archaeology/static*', 'sed -i*IWA_STATIC*', '*>*isle-wars-archaeology/static*', '*>*IWA_STATIC*');
  return { permissions: { allow: ['Bash', 'Read', 'Grep', 'Glob'], deny: ['Agent', 'Edit', 'Write', ...[...publishing, ...staticWrites].map((p) => `Bash(${p})`)] },
    hooks: { PreToolUse: [{ matcher: 'Read|Grep|Glob', hooks: [{ type: 'command', command: `CLAUDE_PROJECT_DIR=${quote(path.resolve(path.dirname(guard), '../..'))} ${quote(process.execPath)} ${quote(guard)} reviewer` }] }] } };
}
export function readClaudeEvents(text, model, sessionId) {
  let events;
  try { events = text.split(/\r?\n/).filter((s) => s.trim()).map((s) => JSON.parse(s)); } catch { fail('Malformed or truncated Claude event stream.'); }
  const init = events.filter((e) => e.type === 'system' && e.subtype === 'init');
  const results = events.filter((e) => e.type === 'result');
  if (init.length !== 1 || results.length !== 1) fail('Claude must emit exactly one init and one final result.');
  if (init[0].model !== model || init[0].session_id !== sessionId || results[0].session_id !== sessionId) fail('Claude actual model or session differs from the selection.');
  const assistantModels = [...new Set(events.filter((e) => e.type === 'assistant' && e.message?.model).map((e) => e.message.model))];
  if (assistantModels.some((actual) => actual !== model)) fail('Claude response model differs from the selected model.');
  const result = results[0];
  if (result.is_error !== false || result.subtype !== 'success' || typeof result.result !== 'string' || !result.result.trim()) fail('Claude did not return a successful final review.');
  if (!Array.isArray(result.permission_denials) || result.permission_denials.length) fail('Claude permission denial; widen the trusted grant before another run.');
  for (const e of events) {
    if (e.type !== 'user' || !Array.isArray(e.message?.content)) continue;
    for (const part of e.message.content) {
      if (part.type === 'tool_result' && part.is_error && /PreToolUse[\s\S]*hook[\s\S]*(?:blocked|error)|blocked by[\s\S]*hook|Permission to use[\s\S]*denied/i.test(String(part.content))) fail('Claude tool hook rejected a call.');
    }
  }
  return { review: result.result, actualModel: init[0].model, sessionId, permissionDenials: result.permission_denials, assistantModels };
}
// Only known generated data can be grouped; unknown/executable suffixes require FILE lines.
const groupedEvidence = (f) => f.startsWith('docs/prototypes/') && /\.(?:jsonl?|txt|log|md|png|jpe?g|gif|webp|gz|zip|pdf)$/i.test(f);
export function scopeProblems(review, files) {
  const lines = review.split(/\r?\n/);
  const scope = lines.filter((l) => /^SCOPE:/i.test(l));
  const problems = scope.length === 1 && /^SCOPE: complete\s*$/i.test(scope[0]) ? [] : ['Scope is not explicitly complete.'];
  const acknowledged = new Set(lines.filter((l) => l.startsWith('FILE: ')).map((l) => l.slice(6).trim()));
  const groups = lines.filter((l) => l.startsWith('EVIDENCE: ')).map((l) => l.slice(10).trim()).filter((p) => p.startsWith('docs/prototypes/') && p.endsWith('/') && !p.includes('..'));
  const missing = files.filter((f) => !acknowledged.has(f) && !(groupedEvidence(f) && groups.some((g) => f.startsWith(g))));
  if (missing.length) problems.push(`Scope not accounted for: ${missing.join(', ')}`);
  if (lines.some((l) => /^UNCOVERED:/i.test(l))) problems.push('Reviewer declares uncovered scope.');
  return problems;
}
export function resolveClaude(env = process.env) {
  const exe = env.HARNESS_CLAUDE_EXE || 'claude';
  const command = /\.m?js$/.test(exe) ? { exe: process.execPath, prefix: [exe] } : { exe, prefix: [] };
  const v = spawnSync(command.exe, [...command.prefix, '--version'], { env, encoding: 'utf8', timeout: 30000 });
  if (v.status !== 0 || !/Claude Code/.test(v.stdout ?? '')) fail('Claude CLI unavailable or unrecognized; install/authenticate Claude CLI. No fallback.');
  return { ...command, version: v.stdout.trim() };
}
export function runClaudeWatched({ command, args, workDir, evidenceDir, model, sessionId, env = process.env,
  startupTimeoutMs = 180000, idleTimeoutMs = 600000, totalTimeoutMs = 3600000, log = console.log }) {
  fs.mkdirSync(evidenceDir, { recursive: true });
  const temporaryDir = path.join(evidenceDir, 'tmp');
  fs.mkdirSync(temporaryDir, { recursive: true });
  const childEnv = { ...env, TMPDIR: temporaryDir, ...(process.platform === 'win32' ? { TEMP: temporaryDir, TMP: temporaryDir } : {}) };
  const stdoutFile = path.join(evidenceDir, 'stdout.jsonl'), stderrFile = path.join(evidenceDir, 'stderr.txt');
  const outFd = fs.openSync(stdoutFile, 'w'), errFd = fs.openSync(stderrFile, 'w');
  const started = Date.now();
  return new Promise((resolve, reject) => {
    let child, timer, exitCode = null, failure = null, lastActivity = started, pending = '', initSeen = false, observedModel = null, observedSessionId = null;
    const stop = (reason) => {
      failure ??= reason;
      if (child?.pid) {
        try {
          if (process.platform === 'win32') spawnSync('taskkill', ['/T', '/F', '/PID', String(child.pid)], { stdio: 'ignore' });
          else process.kill(-child.pid, 'SIGKILL');
        } catch { /* own group already exited */ }
      }
    };
    const onSignal = () => stop('Claude run cancelled.');
    const finish = () => {
      clearInterval(timer); process.removeListener('SIGTERM', onSignal); process.removeListener('SIGINT', onSignal);
      fs.closeSync(outFd); fs.closeSync(errFd);
      const stdout = fs.readFileSync(stdoutFile, 'utf8');
      let parsed = null;
      // Preserve any real final even when another event/exit invalidates the run.
      let rawFinal = '';
      for (const line of stdout.split(/\r?\n/)) { try { const e = JSON.parse(line); if (e.type === 'result' && typeof e.result === 'string') rawFinal = e.result; } catch { /* retained verbatim */ } }
      fs.writeFileSync(path.join(evidenceDir, 'final.md'), rawFinal);
      try { parsed = readClaudeEvents(stdout, model, sessionId); } catch (e) { failure ??= e.message; }
      if (exitCode !== 0) failure ??= `Claude CLI exit ${exitCode}.`;
      const receipt = { expectedModel: model, actualModel: observedModel, observedSessionId, assistantModels: parsed?.assistantModels ?? [], sessionId, pid: child?.pid ?? null, exitCode,
        seconds: (Date.now() - started) / 1000, failure, temporaryDir, cliVersion: command.version ?? null, command: [command.exe, ...command.prefix, ...args],
        sha256: Object.fromEntries(['stdout.jsonl', 'stderr.txt', 'final.md', 'prompt.md', 'settings.json', 'inventory.json', 'full.diff'].filter((n) => fs.existsSync(path.join(evidenceDir, n))).map((n) => [n, hash(fs.readFileSync(path.join(evidenceDir, n)))])) };
      fs.writeFileSync(path.join(evidenceDir, 'receipt.json'), JSON.stringify(receipt, null, 2)+'\n');
      if (failure) reject(new ClaudeInfraError(`${failure} Evidence retained: ${evidenceDir}`));
      else resolve({ stdout: parsed.review, stderr: fs.readFileSync(stderrFile, 'utf8'), exitCode, seconds: receipt.seconds, sessionId, actualModel: parsed.actualModel });
    };
    try { child = spawn(command.exe, [...command.prefix, ...args], { cwd: workDir, env: childEnv, detached: process.platform !== 'win32', stdio: ['ignore', 'pipe', 'pipe'] }); }
    catch (e) { failure = e.message; finish(); return; }
    child.stdout.on('data', (d) => {
      fs.writeSync(outFd, d); lastActivity = Date.now(); pending += d.toString('utf8');
      let end;
      while ((end = pending.indexOf('\n')) >= 0) {
        const line = pending.slice(0, end); pending = pending.slice(end+1);
        try {
          const event = JSON.parse(line);
          if (event.type === 'system' && event.subtype === 'init') {
            initSeen = true; observedModel = event.model; observedSessionId = event.session_id;
            if (event.model !== model || event.session_id !== sessionId) stop('Claude actual model/session mismatch.');
            else log(`claude: session ${sessionId} started (${event.model}); events ${stdoutFile}`);
          }
        } catch { /* final strict parser rejects malformed lines */ }
      }
    });
    child.stderr.on('data', (d) => { fs.writeSync(errFd, d); lastActivity = Date.now(); });
    child.once('error', (e) => { failure = `Claude spawn failed: ${e.message}`; });
    child.once('close', (code) => { exitCode = code; finish(); });
    process.once('SIGTERM', onSignal); process.once('SIGINT', onSignal);
    timer = setInterval(() => {
      const now = Date.now();
      if (now-started >= totalTimeoutMs) stop('Claude total timeout.');
      else if (!initSeen && now-started >= startupTimeoutMs) stop('Claude startup timeout.');
      else if (initSeen && now-lastActivity >= idleTimeoutMs) stop('Claude idle timeout.');
    }, Math.min(100, startupTimeoutMs, idleTimeoutMs, totalTimeoutMs));
  });
}
