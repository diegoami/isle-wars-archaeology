#!/usr/bin/env node
// Hands one PR to the selected OpenCode or Claude CLI backend and posts one review comment.
//
//   node tools/harness/review.mjs --pr 42 --brief brief.md [--reviewer NAME [--family F] [--variant V]]
//     [--exclude NAME,...] [--issue 12 --apply-label] [--done-when K] [--dry-run] [--env KEY=VALUE]...
//   node tools/harness/review.mjs --self-test   (the reader's samples and the family checks; no model is called)
//
// One reviewer, one run (the owner, 2026-10-11: no chains, no second opinion, no quota check).
// --reviewer is a harness.json key or an OpenCode id provider/model; without it, harness.json's
// reviewer.default runs. The reviewer is never the implementer's model family: --exclude names the
// implementer (a harness.json key, an id or a family), else a model:<name> label on the PR or
// --issue, else the session's own family: the main session or an agent it spawned implements by
// default, and lib/common.mjs sessionFamily reads that family from ANTHROPIC_BASE_URL (or
// HARNESS_SESSION_FAMILY). Runs use the scripts' own OpenCode data directory. harness.json's
// blocked list is refused (switch-model.mjs --block/--unblock).
//
// The brief's first line is the review header the model prints, e.g. "T07 review (Luna)". The
// model never writes to GitHub (the agent file denies it); this script is the only writer.
//
// A review is never thrown away (lib/chain.mjs readReview). A readable review is posted normalised
// and acted on. One that may be cut off, has no readable verdict, opens and closes with different
// verdicts, or has a finding after its closing verdict is posted whole, exactly as it arrived, under
// a note, with no label: OpenCode's models do not always follow the brief, and the main session
// reads such a review instead of paying for another. Closing keywords lose their '#'.
//
// The review accounts for each Done-when line of the task file pasted in the brief (or --done-when
// K): one "DW<k>:" line each, after the verdict (L32). An approve with a line missing, or one not
// run, is posted under a note and not labelled approved (exit 4).
//
// A brief naming a commit other than the PR's head as the one to review is refused, exit 2, before
// anything runs (#23). Only the lines before the pasted task file's title (`# T<nn>`) are read (#32).
//
// Exit 0: posted, and labelled with --apply-label. Exit 1: refused or a defect. Exit 2: usage.
// Exit 3: OpenCode unavailable, its model not listed, or no review came back; nothing posted. Read
// the run's final message (CLAUDE.md rule 25), fix the cause, and run again; whether another model
// reviews instead is the user's call. Exit 4: posted under a note, no label; the main session reads
// it on the PR and decides, and never pays for a second review because of it. --dry-run prints
// what would be posted and the exit code it would use, and exits 0; it still runs, and bills, the
// model.

import fs from 'node:fs';
import path from 'node:path';
import { randomBytes, randomUUID } from 'node:crypto';
import { runOpenCodeWatched, selectOpenCode, OpenCodeInfraError, keyProblem } from './lib/opencode.mjs';
import { resolveClaude, validateClaudeEnvironment, claudeSettings, runClaudeWatched, ClaudeInfraError, scopeProblems, hash } from './lib/claude.mjs';
import { materializeReviewDependencies } from './lib/review-dependencies.mjs';
import { credentialJail, OFF_WARNING } from './lib/jail.mjs';
import { readReview, doneWhenCount, briefTargets } from './lib/chain.mjs';
import { planPost, publish } from './lib/post.mjs';
import { selfTest, SAMPLES } from './lib/review-selftest.mjs';
import { choiceSelfTest } from './lib/choice-selftest.mjs';
import {
  sh, requireTools, repoPaths, loadConfig, parseArgs, envWith, ocArgs, prepareOpenCode, watchLine, namedModel, implementerFamilies, reviewRefusal,
} from './lib/common.mjs';

const say = (s) => console.log(s);
const die = (code, s) => { console.error(s); process.exit(code); };

const a = parseArgs(process.argv.slice(2), { flags: ['apply-label', 'dry-run', 'self-test'], repeatable: ['env'] });
if (a['self-test']) {
  const failures = selfTest();
  for (const f of failures) console.error(`FAIL ${f}`);
  say(`self-test: ${SAMPLES.length - failures.length} of ${SAMPLES.length} samples read as expected`);
  const choice = choiceSelfTest();
  for (const f of choice.failures) console.error(`FAIL ${f}`);
  say(`self-test: model families, ${choice.failures.length ? `${choice.failures.length} failed` : `all ${choice.count} checks passed`}`);
  process.exit(failures.length || choice.failures.length ? 1 : 0);
}
if (!a.pr || !a.brief) die(2, '--pr and --brief are required.');
if (a['apply-label'] && !a.issue) die(2, '--apply-label needs --issue.');
const brief = fs.readFileSync(a.brief, 'utf8').split(/\r?\n/);
const briefHeader = brief[0].trim();
const doneWhen = a['done-when'] !== undefined ? Number(a['done-when']) : doneWhenCount(brief.join('\n'));
if (!Number.isInteger(doneWhen) || doneWhen < 0) die(2, `--done-when takes a count; got ${a['done-when']}`);
if (!/review \(/.test(briefHeader)) die(2, `The brief's first line must be the review header, e.g. "T07 review (Luna)"; got: ${briefHeader}`);

requireTools('git', 'gh');

const top0 = sh('git', ['rev-parse', '--show-toplevel']);
const config = loadConfig(top0);
const { top, workRoot } = repoPaths(config);
const rev = config.reviewer;

// The implementer's family never reviews.
const labelsOf = (kind, n) => sh('gh', [kind, 'view', String(n), '--json', 'labels', '--jq', '.labels[].name'], { cwd: top, allowFail: true }).split('\n');
const implementedBy = a.exclude ? a.exclude.split(',').map((s) => s.trim()).filter(Boolean)
  : [...labelsOf('pr', a.pr), ...(a.issue ? labelsOf('issue', a.issue) : [])]
    .filter((l) => l.startsWith('model:')).map((l) => l.slice(6));
// The reviewer: the one named, else harness.json's reviewer.default (CLAUDE.md rule 6).
if (!a.reviewer && !rev.default) die(2, 'No reviewer: pass --reviewer, or set reviewer.default in harness.json.');
const reviewer = namedModel(config, a.reviewer ?? rev.default, { family: a.family, variant: a.variant }, die);
// Every implementer name resolves to a family, or the review is refused (Sol's R2 on PR 164); none
// named means the session's family implemented (lib/common.mjs implementerFamilies).
// The session's family is always excluded too (Sol's R1 on PR 189).
const refusal = reviewRefusal(config.models, reviewer, implementedBy);
if (refusal) die(1, `Refused: ${refusal}. Nothing posted.`);
const fams = implementerFamilies(config.models, implementedBy);
say(`implemented by: ${fams.families.join(', ')} (the detected session's family${implementedBy.length ? `, plus ${implementedBy.join(', ')}` : ''})`);
const fallback = 'Nothing posted. Read the run\'s final message (CLAUDE.md rule 25) and fix the cause; another reviewer is the user\'s call.';
// OpenCode is looked for only now, so that its absence is reported with the same fallback (Sol's R1 on PR 41).
const backend = config.models[reviewer].backend ?? 'opencode';
if (!['opencode', 'claude'].includes(backend)) die(2, `Unknown reviewer backend ${backend}`);
let opencode, claude, pre;
if (backend === 'claude') {
  try {
    if (config.jail?.enabled === true) throw new ClaudeInfraError('Claude backend does not support the optional credential jail yet; no run started.');
    const modelId = config.models[reviewer].id;
    if (!modelId.startsWith('anthropic/')) throw new ClaudeInfraError('Claude backend requires an anthropic/claude-* model ID.');
    validateClaudeEnvironment(envWith(a.env), modelId.slice('anthropic/'.length));
    claude = resolveClaude(envWith(a.env));
    pre = { env: envWith(a.env) };
    say(`claude: ${claude.version}`);
  } catch (e) { if (e instanceof ClaudeInfraError) die(3, `${e.message} ${fallback}`); throw e; }
} else {
  try { opencode = await selectOpenCode(process.env, { cwd: top, log: say }); } catch (e) {
    if (e instanceof OpenCodeInfraError) die(3, `OpenCode unavailable: ${e.message} ${fallback}`);
    throw e;
  }
  const jail = config.jail?.enabled === true ? credentialJail() : { off: 'harness.json does not enable it', quiet: true };
  if (jail.off && !jail.quiet) say(OFF_WARNING(jail.off));
  else if (!jail.off) opencode = { exe: jail.exe, prefix: [...jail.args, '--', opencode.exe, ...opencode.prefix] };
  pre = await prepareOpenCode({ opencode, chain: [reviewer], models: config.models, env: envWith(a.env), cwd: top, log: say });
  for (const p of pre.problems) say(p);
  if (!pre.usable.length) die(3, `OpenCode unavailable: ${pre.problems.join('; ')}. ${fallback}`);
}

// The reviewer's agent and OpenCode config come from this checkout, the main session's, never from
// the PR under review: OpenCode reads a project's .opencode/ by default, so a PR's own reviewer.md
// (or anything else it puts there) would decide what its reviewer may do. Checked on OpenCode
// 1.18.34: without these two variables a PR's reviewer.md with `git push *: allow` was the one
// loaded (#10, L34; ic2-conquest's reviewer does the same).
const agentFile = path.join(top, '.opencode', 'agents', `${rev.agent}.md`);
if (backend === 'opencode' && !fs.existsSync(agentFile)) die(2, `The reviewer agent is missing from this checkout: ${agentFile}. Nothing run.`);
const reviewEnv = { ...pre.env, OPENCODE_CONFIG_DIR: path.join(top, '.opencode'), OPENCODE_DISABLE_PROJECT_CONFIG: '1' };
const prMeta = JSON.parse(sh('gh', ['pr', 'view', String(a.pr), '--json', 'headRefOid,baseRefOid'], { cwd: top }));
const headSha = prMeta.headRefOid;
const baseSha = prMeta.baseRefOid;
if (![headSha, baseSha].every((s) => /^[0-9a-f]{40}$/.test(s))) die(2, 'PR head/base identity missing or invalid.');
// A brief that names another commit as the one to review would make the reviewer's tree proof stop
// it after a billed run (#23): refuse it before any worktree or model run.
const stale = [...new Set(briefTargets(brief.join('\n')))].filter((c) => c !== headSha.toLowerCase());
if (stale.length) {
  die(2, `The brief names ${stale.join(', ')} as the commit to review, but PR ${a.pr}'s head is ${headSha}. `
    + 'Nothing was run or posted. The brief was written before the latest push, or the head was read before '
    + 'GitHub updated: take it from the local branch (git rev-parse <branch>), or rerun once GitHub shows it.');
}
sh('git', ['-C', top, 'fetch', '-q', 'origin', `pull/${a.pr}/head`]);
// A path of this invocation's own; only this tree is ever removed.
const worktree = path.join(process.env.HARNESS_REVIEW_WORKTREE_ROOT ? path.resolve(process.env.HARNESS_REVIEW_WORKTREE_ROOT) : workRoot, `${a.pr}-review-${randomBytes(4).toString('hex')}`);
let created = false;
const removeTree = () => {
  if (!created) return;
  if (backend === 'claude') { say(`retained worktree: ${worktree}`); created = false; return; }
  sh('git', ['-C', top, 'worktree', 'remove', '--force', worktree], { allowFail: true });
  fs.rmSync(worktree, { recursive: true, force: true });
  // Never prune inherited worktree registrations.
  created = false;
};
const newTree = () => {
  removeTree();
  fs.mkdirSync(workRoot, { recursive: true });
  sh('git', ['-C', top, 'worktree', 'add', '--detach', worktree, headSha]);
  created = true;
  say(`worktree: ${worktree} at ${headSha}`);
};

// The review, in a fresh worktree at the PR's head. Resolves { ok: true, value } or
// { ok: false, reason, detail }. The header names the default reviewer when none was given.
const attempt = async (m) => {
      const model = config.models[m];
      const header = a.reviewer ? briefHeader : briefHeader.replace(/\([^()]*\)\s*$/, `(${m})`);
      let prompt = `${header}\n${brief.slice(1).join('\n')}

---
OUTPUT RULES (from tools/harness/review.mjs; they override anything above that conflicts):
- Do not post to GitHub, commit, push, label or merge anything. The script posts your review.
  Edit nothing, but for a mutation made in place in your worktree and never committed.
  Undo a mutation or scratch edit by writing back the file's saved contents (read it first,
  restore it in a \`finally\`), or commit first; never \`git checkout\`, \`git restore\` or \`git reset\`
  a file with uncommitted work: they return the last commit and destroy the rest. Keep the saved
  copy inside your worktree (\`<file>.saved\`, deleted afterwards) or in your \`mktemp -d\` folder, or
  anywhere under \`/tmp\` (open to the reviewer since 2026-10-11). Outside your worktree, only read the static
  folder ~/.local/share/isle-wars-archaeology/static/ (never write there, and never paste its
  contents into the review), and write only under \`/tmp\` (a \`mktemp -d /tmp/iwa-review-XXXXXX\` folder is
  the tidiest, removed afterwards). Every other path outside your worktree is forbidden (T29).
- Your final message is the review and nothing else. Line 1 is exactly: ${header}
  Line 2 is the verdict, alone on its line: approve, approve after named fixes, rework, or user
  decision. Then any where-I-worked lines (worktree, HEAD, diff, the commands you ran), then the
  findings (R1, R2, ... with file and line, blocking or not), then the verdict again as the very
  last line. Nothing comes after it.
- A finding you proved that lets a forbidden action or a wrong result past what the task protects
  is blocking, and blocks an approve: never "follow-up hardening" or "outside the threat model"
  unless the task's text says so (L47).
- Report every blocking finding in this one review, not one per round: read the whole diff, then
  make a final pass and write "Final pass done" as the line before the closing verdict. Name any
  part you did not cover, and do not approve then (L49).${doneWhen ? `
- The task has ${doneWhen} Done-when line${doneWhen > 1 ? 's' : ''}. Right after the verdict line, account for each, one
  line per Done-when line, DW1 to DW${doneWhen}: "DW<k>: ran <command> → <result>", or
  "DW<k>: not run — <reason>". An approve with one missing, or one not run, is not applied.` : ''} A review that does not end with its verdict, or that has a
  finding after it, is posted flagged and acted on by no one until the main session reads it.
- Your worktree is ${worktree} at ${headSha}, and it is already your working directory. Run git
  there without -C, and never type that path: a mistyped path ends the run. This rule is about
  your own worktree only (L61): a Done-when line may send git at a pinned repository outside it
  (git -C <path> show <pin>:<file>); run that exactly as written — OpenCode does not path-check
  git -C — and read a granted outside path only with the L59 recipe.
`;
      newTree();
      let reviewDependencies = null;
      if (backend === 'claude') {
        reviewDependencies = materializeReviewDependencies({
          source: path.join(top, 'node_modules'),
          destination: path.join(worktree, 'node_modules'),
          ownedRoot: worktree,
        });
        say(reviewDependencies
          ? `claude: private dependencies copied into retained worktree (${reviewDependencies.destination})`
          : 'claude: launcher has no node_modules directory; continuing with the existing dependency setup');
      }
      const watch = watchLine(m, model);
      if (watch) say(watch);
      let run;
      let scopeFiles = [];
      if (backend === 'claude') {
        const evidence = path.resolve(top, '.cache', 'review-evidence', `pr${a.pr}-${randomBytes(6).toString('hex')}`);
        fs.mkdirSync(evidence, { recursive: true });
        const local = (args) => sh('git', args, { cwd: worktree });
        const mergeBaseSha = local(['merge-base', baseSha, headSha]);
        // Large diffs use a file descriptor, never spawnSync's bounded stdout buffer.
        const { spawnSync } = await import('node:child_process');
        const diffPath = path.join(evidence, 'full.diff');
        const diffFd = fs.openSync(diffPath, 'w');
        let diffRun;
        try { diffRun = spawnSync('git', ['diff', '--no-ext-diff', '--no-textconv', mergeBaseSha, headSha], { cwd: worktree, stdio: ['ignore', diffFd, 'pipe'] }); }
        finally { fs.closeSync(diffFd); }
        if (diffRun.status !== 0) throw new Error('Cannot construct exact local PR diff.');
        scopeFiles = local(['diff', '--name-only', mergeBaseSha, headSha]).split('\n').filter(Boolean);
        const diff = fs.readFileSync(diffPath, 'utf8');
        const lines = diff.split('\n');
        const parts = path.join(evidence, 'diff-parts'); fs.mkdirSync(parts);
        for (let i = 0; i < lines.length; i += 240) fs.writeFileSync(path.join(parts, `${String(i / 240).padStart(5, '0')}.diff`), lines.slice(i, i+240).join('\n')+'\n');
        fs.writeFileSync(path.join(evidence, 'inventory.json'), JSON.stringify({ baseSha, mergeBaseSha, headSha, diffSha256: hash(diff), files: scopeFiles }, null, 2)+'\n');
        const sessionId = randomUUID();
        if (reviewDependencies) prompt += '\nThe launcher dependency tree was copied into a private node_modules directory in this retained review worktree.\n';
        else prompt += '\nThe launcher has no node_modules directory; no dependency copy was made.\n';
        prompt += `\nCLAUDE BACKEND CONTRACT: The exact PR base is ${baseSha}, merge-base ${mergeBaseSha}, head ${headSha}. The diff uses merge-base to head, matching GitHub PR changes. Do not use origin/main for a merged PR. Complete local diff: ${diffPath}; bounded parts: ${parts}; full changed-file inventory: ${evidence}/inventory.json. Read all executable changes. For generated evidence you may audit a group explicitly. Never claim a file you did not inspect. Before Final pass done, emit SCOPE: complete only if you covered all changes; otherwise SCOPE: incomplete plus UNCOVERED: paths/reasons. Emit FILE: <exact path> for each changed file inspected; EVIDENCE: <docs/prototypes/.../ prefix> may account for generated evidence only, never executable scripts. These are coverage claims, not independent proof. Every Done-when must be run; include exact DW lines. A missing scope acknowledgment prevents approval. No subagents or GitHub writes. Native Claude permission denials mirror OpenCode publishing restrictions; the trusted hook protects credential paths for Read/Grep/Glob. Bash is granted for tests and in-tree mutations. These are mistake safeguards, not an OS sandbox. Preserve scratch/evidence; do not clean up. Your scratch is your retained worktree or /tmp; the static folder remains read-only under the project rules above. Original captures and derived source are never pasted into the final review. No blanket permission bypass.\n`;
        if (/sonnet/i.test(model.id)) {
          const modelsDoc = fs.readFileSync(path.join(top, 'docs/models.md'), 'utf8');
          const tripwire = modelsDoc.match(/```text\n(Out of your depth:[\s\S]*?)\n```/);
          if (!tripwire) throw new Error('Missing Sonnet tripwire in trusted docs/models.md.');
          prompt += '\nThe read-only contract overrides the tripwire instruction to push: never push.\n'+tripwire[1]+'\n';
        }
        fs.writeFileSync(path.join(evidence, 'prompt.md'), prompt);
        const settingsPath = path.join(evidence, 'settings.json');
        fs.writeFileSync(settingsPath, JSON.stringify(claudeSettings(path.join(top, 'tools/harness/guard.mjs')), null, 2)+'\n');
        const args = ['-p', `Read the full review brief at ${evidence}/prompt.md before any other action.`, '--model', model.id.slice('anthropic/'.length),
          '--effort', model.variant ?? 'medium', '--setting-sources', '', '--settings', settingsPath,
          '--permission-mode', 'dontAsk', '--permission-prompts', 'none', '--tools', 'Bash,Read,Grep,Glob',
          '--strict-mcp-config', '--disable-slash-commands', '--no-chrome', '--verbose', '--output-format', 'stream-json', '--session-id', sessionId, '--add-dir', evidence];
        say(`claude: evidence ${evidence}; worktree retained after completion`);
        try {
          run = await runClaudeWatched({ command: claude, args, workDir: worktree, evidenceDir: evidence,
            model: model.id.slice('anthropic/'.length), sessionId, env: { ...pre.env, CLAUDE_PROJECT_DIR: top },
            startupTimeoutMs: rev.startupTimeoutSec * 1000, idleTimeoutMs: rev.idleTimeoutSec * 1000, totalTimeoutMs: rev.totalTimeoutSec * 1000, log: say });
        } catch (e) { if (e instanceof ClaudeInfraError) return { ok: false, reason: e.message }; throw e; }
      } else try {
        run = await runOpenCodeWatched({
          args: ocArgs(worktree, rev.agent, model), prompt, workDir: worktree, title: `pr${a.pr}-${m}`,
          startupTimeoutMs: rev.startupTimeoutSec * 1000, idleTimeoutMs: rev.idleTimeoutSec * 1000,
          totalTimeoutMs: rev.totalTimeoutSec * 1000, opencode, env: reviewEnv, log: say,
        });
      } catch (e) {
        if (!(e instanceof OpenCodeInfraError)) throw e;
        return { ok: false, reason: e.reason, detail: e.message };
      }
      // OpenCode's own error stream on a failed run, never the model's output (Luna's R1, round 2).
      if (run.exitCode !== 0) return { ok: false, reason: keyProblem(run.stderr, model.id, reviewEnv.XDG_DATA_HOME) ?? `exit ${run.exitCode}`, detail: run.output };
      if (run.agentFallback) return { ok: false, reason: 'fell back to the default agent', detail: run.output };
      if (run.permissionRejected) {
        return { ok: false, reason: `permission rejected: ${run.permissionRejected}${run.permissionHint ? `; ${run.permissionHint}` : ''}`, detail: run.output };
      }
      let read = readReview(run.stdout, header);
      if (backend === 'claude' && read.kind === 'ok') {
        const problems = scopeProblems(read.review, scopeFiles);
        if (problems.length) read = { kind: 'flagged', review: run.stdout, note: problems.join('; ') };
      }
      if (read.kind === 'none') return { ok: false, reason: read.reason, detail: run.output };
      return { ok: true, value: { ...read, header, model } };
};

say(`attempt: ${reviewer}`);
let result;
try { result = await attempt(reviewer); } finally { removeTree(); }
if (!result.ok) {
  if (result.detail) say(result.detail.split(/\r?\n/).slice(-20).join('\n'));
  die(3, `No review from ${reviewer}: ${result.reason}. ${fallback}`);
}
const plan = planPost({
  read: result.value, header: result.value.header, doneWhen, source: 'tools/harness/review.mjs',
  signature: `${reviewer}, via tools/harness/review.mjs (${result.value.model.id})`,
});
publish({ plan, pr: a.pr, issue: a.issue, applyLabel: a['apply-label'], dryRun: a['dry-run'], top, say, die });
