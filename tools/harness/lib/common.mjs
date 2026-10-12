// git, gh, the config and argument parsing, for review.mjs, post-review.mjs and switch-model.mjs.

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { openCodeHome, listedModels, loginHint, openCodeVersion, versionProblem } from './opencode.mjs';
import { canonicalFamily } from './family.mjs';
import { knownFamilyOf } from './switch.mjs';
export { canonicalFamily };

// The command that runs a tool. HARNESS_GH_EXE names the gh to run (the tests' fake, #2); a .mjs or
// .js one runs through Node, since Windows cannot execute a script.
export function toolCommand(cmd, env = process.env) {
  const over = cmd === 'gh' ? env.HARNESS_GH_EXE : null;
  if (!over) return [cmd, []];
  return /\.m?js$/.test(over) ? [process.execPath, [over]] : [over, []];
}

export function sh(cmd, args, { cwd, allowFail = false, env } = {}) {
  const [exe, pre] = toolCommand(cmd, env ?? process.env);
  const r = spawnSync(exe, [...pre, ...args], { cwd, env, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  if (r.error) throw new Error(`${cmd} could not run: ${r.error.message}`);
  if (r.status !== 0 && !allowFail) throw new Error(`${cmd} ${args.join(' ')} failed (${r.status}):\n${r.stderr}`);
  return r.status === 0 ? r.stdout.trim() : '';
}

export function requireTools(...tools) {
  for (const t of tools) {
    const [exe, pre] = toolCommand(t);
    const r = spawnSync(exe, [...pre, '--version'], { stdio: 'ignore' });
    if (r.error) throw new Error(`${t} is not on PATH.`);
  }
}

// The main checkout, even when run from a worktree, and the directory agents' worktrees live in.
export function repoPaths(config) {
  const top = sh('git', ['rev-parse', '--show-toplevel']);
  const commonDir = sh('git', ['-C', top, 'rev-parse', '--path-format=absolute', '--git-common-dir']);
  const mainRoot = path.dirname(commonDir);
  const rel = (config.worktreeRoot ?? '../{repo}-work').replaceAll('{repo}', path.basename(mainRoot));
  return { top, commonDir, mainRoot, workRoot: path.resolve(mainRoot, rel) };
}

export function loadConfig(top) {
  const file = path.join(top, 'harness.json');
  if (!fs.existsSync(file)) throw new Error(`harness.json not found at ${file}`);
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

// A model's note in harness.json (what to look for, its login, its effort), printed when it runs.
export function watchLine(name, model) {
  const note = model.note ?? model.watch;
  return note ? `note: ${name} (${model.id}): ${note}` : null;
}

// --name value, --flag, and repeatable --env KEY=VALUE / --copy path.
export function parseArgs(argv, { flags = [], repeatable = [] } = {}) {
  const out = {};
  for (const r of repeatable) out[r] = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) throw new Error(`Unexpected argument: ${a}`);
    const key = a.slice(2);
    if (flags.includes(key)) { out[key] = true; continue; }
    const val = argv[++i];
    if (val === undefined) throw new Error(`${a} needs a value`);
    if (repeatable.includes(key)) out[key].push(val); else out[key] = val;
  }
  return out;
}

export function envWith(pairs) {
  const env = { ...process.env };
  for (const p of pairs) {
    const i = p.indexOf('=');
    if (i < 1) throw new Error(`--env takes KEY=VALUE; got ${p}`);
    env[p.slice(0, i)] = p.slice(i + 1);
  }
  return env;
}

// OpenCode silently falls back to its default, full-permission agent when --agent names one it
// cannot find, and a branch cut before the agent file existed does not carry it (IC2 #480). Copy
// the agent into the worktree, and keep the copy out of git so the model cannot commit it.
export function ensureAgent({ top, commonDir, worktree, agent }) {
  const rel = `.opencode/agents/${agent}.md`;
  const src = path.join(top, rel);
  if (!fs.existsSync(src)) throw new Error(`Agent file not found: ${src}`);
  if (sh('git', ['-C', worktree, 'ls-files', '--', rel], { allowFail: true })) return;
  fs.mkdirSync(path.join(worktree, '.opencode', 'agents'), { recursive: true });
  fs.copyFileSync(src, path.join(worktree, rel));
  const exclude = path.join(commonDir, 'info', 'exclude');
  const text = fs.existsSync(exclude) ? fs.readFileSync(exclude, 'utf8') : '';
  if (!text.split(/\r?\n/).includes(rel)) {
    fs.mkdirSync(path.dirname(exclude), { recursive: true });
    fs.appendFileSync(exclude, `${text && !text.endsWith('\n') ? '\n' : ''}${rel}\n`);
  }
}

// Before anything is billed: the scripts' own data directory, the OpenCode version (any major but
// the supported one is refused, #26), and which models of `chain` OpenCode lists there. A model it
// does not list (an unknown id, or a provider not logged in in that directory) is dropped, with the
// command that fixes it. Quota is not checked (the owner, 2026-10-11: the model named runs).
// Returns { env, usable, problems }.
export async function prepareOpenCode({ opencode, chain, models, env, cwd, log }) {
  const oc = openCodeHome(env, { log });
  const version = await openCodeVersion(opencode, { env: oc.env, cwd });
  log(`opencode: ${version ?? 'unknown version'} (${opencode.exe})`);
  const bad = versionProblem(version, opencode.exe);
  if (bad) return { env: oc.env, usable: [], problems: [bad], version };
  const { listed, errors } = await listedModels(opencode, chain.map((m) => models[m].id.split('/')[0]), { env: oc.env, cwd });
  const problems = [];
  const usable = chain.filter((m) => {
    if (listed.has(models[m].id)) return true;
    problems.push(`${m}: ${loginHint(models[m].id, listed, oc.dataHome, errors)}`);
    return false;
  });
  return { env: oc.env, usable, problems, version };
}

// The family of the main session, and so of every Claude Code agent it spawns (an agent runs through
// the same endpoint). The session is set only by the Anthropic environment variables: with
// ANTHROPIC_BASE_URL unset or at anthropic.com it is Claude; when Claude's tokens are out the owner
// points it at another provider that speaks the same API: Z.AI's GLM, MiniMax, or Moonshot's Kimi
// (the owner, 2026-10-12), and the family rule must then keep that family out of the reviewer's
// seat. The names match the families the reviewer models get (glm, minimax, kimi). HARNESS_SESSION_FAMILY
// overrides the guess; an endpoint this list does not know returns null, and the caller refuses
// to review until it is set.
// Matched on the parsed URL's hostname only, never on its path or query string (Sol's R5 on PR 189),
// and only as an exact domain or a bounded suffix of one (host === d or host ends with '.' + d; Sol's
// re-review R3): api.z.ai is glm, notz.ai and api.z.ai.evil.example are unknown. anthropic.com and
// its subdomains are Claude; an unparseable URL or an unknown host is null.
const ENDPOINT_FAMILIES = [['anthropic.com', 'claude'], ['z.ai', 'glm'], ['bigmodel.cn', 'glm'],
  ['minimax.io', 'minimax'], ['minimaxi.com', 'minimax'], ['minimax.chat', 'minimax'],
  ['moonshot.ai', 'kimi'], ['moonshot.cn', 'kimi'], ['kimi.com', 'kimi'], ['deepseek.com', 'deepseek'],
  ['aliyuncs.com', 'qwen'], ['aliyun.com', 'qwen'], ['xiaomimimo.com', 'mimo'], ['xiaomi.com', 'mimo']];
export function sessionFamily(env = process.env) {
  if (env.HARNESS_SESSION_FAMILY) return canonicalFamily(env.HARNESS_SESSION_FAMILY);
  const url = String(env.ANTHROPIC_BASE_URL || '').trim();
  if (!url) return 'claude';
  let host;
  try { host = new URL(url).hostname.toLowerCase(); } catch { return null; }
  return ENDPOINT_FAMILIES.find(([d]) => host === d || host.endsWith(`.${d}`))?.[1] ?? null;
}

// harness.json's `blocked` list, changed with switch-model.mjs --block/--unblock: a family name
// ("deepseek") or a piece of a model id ("deepseek-v4"), case-insensitive. The reason a model may
// not run, or null. The family the id names is checked too, whatever family was declared or saved
// (Sol's re-review R2 on PR 189).
export function blockedReason(config, { id, family }) {
  const fams = [family, id ? knownFamilyOf(id) : null].map(canonicalFamily).filter(Boolean);
  for (const b of config.blocked ?? []) {
    const needle = String(b).toLowerCase();
    if (fams.includes(canonicalFamily(needle))) return `${family} is blocked in harness.json (switch-model.mjs --unblock ${b} lifts it)`;
    if (id && id.toLowerCase().includes(needle)) return `${id} matches "${b}", blocked in harness.json (switch-model.mjs --unblock ${b} lifts it)`;
  }
  return null;
}

export const ocArgs = (worktree, agent, model) =>
  ['run', '--dir', worktree, '--agent', agent, '--model', model.id, ...(model.variant ? ['--variant', model.variant] : [])];

// The model named for a run (CLAUDE.md rule 6): a harness.json key, or any OpenCode id
// `provider/model`. Its family decides the reviewer-family rule, so it is never taken on trust (Sol's
// R1 and re-review R1 on PR 164): a registered id keeps its registered family; a new id's family
// comes from a single-family provider or an unambiguous model name, else the id is refused; a
// declared --family is only a cross-check. harness.json's blocked list is refused.
export const FAMILIES = ['claude', 'openai', 'glm', 'mimo', 'minimax', 'kimi', 'qwen', 'deepseek'];
// Providers that serve one family only: their prefix alone fixes the family. Every other route
// (openrouter, opencode-go, alibaba-token-plan, …) serves several, so the model name must say it.
const PROVIDER_FAMILY = { openai: 'openai', anthropic: 'claude', minimax: 'minimax', moonshot: 'kimi', 'zai-coding-plan': 'glm', zai: 'glm' };
const NAME_FAMILY = [[/deepseek/, 'deepseek'], [/claude|opus|sonnet|haiku|fable/, 'claude'], [/gpt|^o\d|codex/, 'openai'],
  [/glm/, 'glm'], [/mimo/, 'mimo'], [/minimax/, 'minimax'], [/kimi/, 'kimi'], [/qwen/, 'qwen']];
// The family an OpenCode id belongs to, established from the id alone, never from a declaration
// (Sol's re-review R1 on PR 164); null when it cannot be established.
export function familyFromId(id) {
  const parts = String(id).toLowerCase().split('/');
  const byName = NAME_FAMILY.filter(([re]) => re.test(parts[parts.length - 1])).map(([, f]) => f);
  const byProvider = PROVIDER_FAMILY[parts[0]];
  if (byProvider) return byName.every((f) => f === byProvider) ? byProvider : null;   // e.g. openai/glm-x: contradictory
  return new Set(byName).size === 1 ? byName[0] : null;
}
// A registered entry's family: the family its id names wherever that is known (knownFamilyOf), and
// the saved family only where the id says nothing, so a declared or force-saved family never
// carries a model past the family rule or the blocked list (Sol's re-review R1/R2 on PR 189).
export const entryFamily = (entry) => (entry ? knownFamilyOf(entry.id) ?? canonicalFamily(entry.family) : null);
// The family a name stands for: a harness.json key, a registered id, a provider/model id, or a
// family name. Null when it cannot be established (Sol's R2 on PR 164).
export function familyOf(models, name) {
  if (!name) return null;
  if (models[name]) return entryFamily(models[name]);
  const reg = Object.values(models).find((m) => m.id === name);
  if (reg) return entryFamily(reg);
  if (name.includes('/')) return familyFromId(name);
  const fam = canonicalFamily(name);
  return FAMILIES.includes(fam) || Object.values(models).some((m) => canonicalFamily(m.family) === fam) ? fam : null;
}
export function namedModel(config, name, { family, variant } = {}, die) {
  if (!name) die(2, 'Name the model: pass --reviewer with a harness.json key or an OpenCode id provider/model (CLAUDE.md rule 6).');
  const entry = config.models[name] ?? Object.values(config.models).find((m) => m.id === name);
  if (!entry && !name.includes('/')) die(2, `Unknown model ${name}: not a harness.json key, and not an OpenCode id provider/model.`);
  const id = entry ? entry.id : name;
  const known = entry ? entryFamily(entry) : familyFromId(id);
  const blocked = blockedReason(config, { id, family: known });
  if (blocked) die(2, `${name}: ${blocked} (CLAUDE.md rule 6).`);
  // The family is never taken from --family alone: an unknown one is refused (re-review R1 on PR 164).
  if (!known) die(2, `${name}: its family cannot be established from its provider or its name. Register it in harness.json with its family (via /switch-model), then name it.`);
  if (family && canonicalFamily(family) !== known) die(2, `${name} is of the ${known} family; --family ${family} disagrees.`);
  const fam = known;
  if (entry) {
    const key = config.models[name] ? name : Object.keys(config.models).find((k) => config.models[k] === entry);
    // --variant on a registered model runs it at that effort (the user's choice, e.g. Sol at medium);
    // a copy keeps harness.json's entry as it is.
    if (!variant || variant === entry.variant) return key;
    const vkey = `${key}@${variant}`;
    config.models[vkey] = { ...entry, variant };
    return vkey;
  }
  config.models[name] = { id, family: fam, ...(variant ? { variant } : {}) };
  return name;
}

// The implementer's families, for the reviewer-family rule: every name must resolve to a family.
// The session's own family (sessionFamily) is ALWAYS among them, whatever --exclude or a `model:`
// label adds: the main session or an agent it spawned implements, since 2026-10-11 (Sol's R1 on PR
// 189; round-3 R1 on PR 164). An endpoint whose family cannot be told is refused, also when names
// are given, until HARNESS_SESSION_FAMILY is set. Returns { families } or { refuse }.
export function implementerFamilies(models, names, env = process.env) {
  const own = sessionFamily(env);
  if (!own) return { refuse: `the session's family cannot be told from ANTHROPIC_BASE_URL=${env.ANTHROPIC_BASE_URL}; set HARNESS_SESSION_FAMILY` };
  const given = names.map((n) => String(n).trim()).filter(Boolean);
  const unknown = given.filter((n) => !familyOf(models, n));
  if (unknown.length) return { refuse: `the implementer's family cannot be established for ${unknown.join(', ')}; pass --exclude <family>` };
  return { families: [...new Set([own, ...given.map((n) => familyOf(models, n))])] };
}

// review.mjs's decision (CLAUDE.md rule 6): the reason the named reviewer may not review work by
// `names` (and always by the session's family), or null. Kept here so that the self-test runs the
// very decision review.mjs enforces. `reviewer` is a harness.json key (namedModel's answer).
export function reviewRefusal(models, reviewer, names, env = process.env) {
  const fams = implementerFamilies(models, names, env);
  if (fams.refuse) return fams.refuse;
  const fam = familyOf(models, reviewer);
  if (!fam) return `${reviewer}: its family cannot be established`;
  if (fams.families.includes(fam)) return `${reviewer} is the implementer's model family (${fams.families.join(', ')})`;
  return null;
}
