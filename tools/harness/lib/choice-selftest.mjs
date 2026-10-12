// The model-choice self-test (CLAUDE.md rule 6): run by `node tools/harness/review.mjs --self-test`,
// so CI runs it. No model is called. It pins Sol's findings on PR 164: a model's family is never
// taken from a declaration (R1 of both rounds) and an implementer name always resolves to a family
// (R2); the 2026-10-11 default: no implementer named means the session's family implemented, read
// from the Anthropic environment; and harness.json's blocked list. Sol's review of PR 189 added the
// decisions themselves, each case failing when its decision is deleted (rule 9): review.mjs's
// refusal (reviewRefusal, with the session's family always excluded, R1), planSwitch's same-family
// and blocked refusals (one family name for Claude, R2; the id's family over --family/--force, R3),
// planImplementer's blocked refusal (R4), and the session's family from the URL's host only (R5).

import { namedModel, familyOf, implementerFamilies, sessionFamily, reviewRefusal } from './common.mjs';
import { planSwitch } from './switch.mjs';

const BLOCKED = ['deepseek', 'gpt-5.6'];
const MODELS = () => ({
  'gpt-6.1-sol': { id: 'openai/gpt-6.1-sol', family: 'openai', variant: 'low' },
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
  ['a blocked family on any route', 'openrouter/deepseek/deepseek-v4-pro', {}, 'refused'],
  ['a blocked id fragment', 'openai/gpt-5.6-luna', {}, 'refused'],
  ['Alibaba, no flag needed', 'ali-glm', {}, 'glm'],
  ['not a key, not an id', 'nonsense', {}, 'refused'],
];

// [label, name, variant, expected variant] (the user's effort choice is honoured, PR 166's review)
const VARIANTS = [
  ['registered key, no variant', 'gpt-6.1-sol', undefined, 'low'],
  ['registered key, medium', 'gpt-6.1-sol', 'medium', 'medium'],
  ['registered id, medium', 'openai/gpt-6.1-sol', 'medium', 'medium'],
  ['same as registered', 'gpt-6.1-sol', 'low', 'low'],
];

// [implementer name, expected family or null]
const IMPLEMENTERS = [
  ['gpt-6.1-sol', 'openai'], ['openai/gpt-6.1-sol', 'openai'], ['openai/chatgpt-4o-latest', 'openai'],
  ['claude', 'claude'], ['openrouter/acme/zeta-1', null], ['nonsense', null],
];

// [label, names as review.mjs reads them, expected families or 'refused'] (round-3 R1 on PR 164)
const GUARD = [
  ['no model: label: the session implemented (Claude)', [], 'claude'],
  ['--exclude ","', ','.split(',').map((x) => x.trim()).filter(Boolean), 'claude'],
  ['blank names', ['', ' '], 'claude'],
  ['an unknown name', ['nonsense'], 'refused'],
  ['a registered id', ['openai/gpt-6.1-sol'], 'claude,openai'],
  ['two names, one family', ['luna', 'openai'], 'claude,openai'],
];

const ZAI = { ANTHROPIC_BASE_URL: 'https://api.z.ai/api/anthropic' };
const UNKNOWN = { ANTHROPIC_BASE_URL: 'https://proxy.example/v1' };
// review.mjs's decision: [label, reviewer key, --exclude names, env, 'refused' or 'allowed']
const REVIEW = [
  ['GLM session, --exclude claude, GLM reviewer (R1)', 'zai-glm', ['claude'], ZAI, 'refused'],
  ['GLM session, nothing named, GLM reviewer', 'zai-glm', [], ZAI, 'refused'],
  ['GLM session, --exclude claude, OpenAI reviewer', 'luna', ['claude'], ZAI, 'allowed'],
  ['unknown endpoint, --exclude claude (R1)', 'luna', ['claude'], UNKNOWN, 'refused'],
  ['unknown endpoint, override glm', 'luna', ['claude'], { ...UNKNOWN, HARNESS_SESSION_FAMILY: 'glm' }, 'allowed'],
  ['Claude session, an entry that says anthropic (R2)', 'old-claude', [], {}, 'refused'],
  ['Claude session, --exclude openai, OpenAI reviewer', 'luna', ['openai'], {}, 'refused'],
  ['Claude session, OpenAI reviewer', 'luna', [], {}, 'allowed'],
];
// planSwitch: [label, config's blocked list, options, 'refused' or the written family]
const SWITCH = [
  ['GLM session, GLM reviewer', [], { id: 'zai-coding-plan/glm-5.3', variant: 'low', sessionFamily: 'glm' }, 'refused'],
  ['Claude session, a Claude reviewer', [], { id: 'anthropic/claude-sonnet-4-5', variant: 'high', sessionFamily: 'claude' }, 'refused'],
  ['GLM session, a Claude reviewer is written as claude (R2)', [], { id: 'anthropic/claude-sonnet-4-5', variant: 'high', sessionFamily: 'glm' }, 'claude'],
  ['Claude session, OpenAI reviewer', ['deepseek'], { id: 'openai/gpt-6.1-sol', variant: 'low', sessionFamily: 'claude' }, 'openai'],
  ['a blocked reviewer on any route', ['deepseek'], { id: 'openrouter/deepseek/deepseek-v4-pro', variant: 'low', sessionFamily: 'claude' }, 'refused'],
  ['a blocked family behind --family --force (R3)', ['openai'], { id: 'opencode-go/gpt-6-luna', variant: 'high', family: 'qwen', force: true, sessionFamily: 'claude' }, 'refused'],
  ['the session family behind --family --force (R3)', [], { id: 'zai-coding-plan/glm-5.3', variant: 'low', family: 'qwen', force: true, sessionFamily: 'glm' }, 'refused'],
];
// planImplementer: [label, blocked list, choice, session family, 'refused' or 'allowed'] (R4)
const IMPLEMENTER_CHOICE = [
  ['a blocked model id', ['deepseek'], 'deepseek-v4-pro', 'claude', 'refused'],
  ['a blocked family by its id', ['qwen'], 'qwen3.8-max', 'claude', 'refused'],
  ['an alias through a blocked session family', ['deepseek'], 'sonnet', 'deepseek', 'refused'],
  ['an alias', ['deepseek'], 'sonnet', 'claude', 'allowed'],
  ['a model id', ['deepseek'], 'glm-5.3-flash', 'glm', 'allowed'],
];

function checkDecisions(failures) {
  const models = () => ({ ...MODELS(), 'zai-glm': { id: 'zai-coding-plan/glm-5.3', family: 'glm' },
    'old-claude': { id: 'anthropic/claude-opus-4', family: 'anthropic' } });
  for (const [label, reviewer, names, env, want] of REVIEW) {
    const got = reviewRefusal(models(), reviewer, names, env) ? 'refused' : 'allowed';
    if (got !== want) failures.push(`reviewRefusal: ${label}: ${got}, expected ${want}`);
  }
  for (const [label, blocked, opts, want] of SWITCH) {
    let got;
    try { got = planSwitch({ models: MODELS(), blocked, reviewer: { default: 'luna' } }, opts).entry.family; } catch (e) {
      if (!/^Refused/.test(e.message)) throw e;
      got = 'refused';
    }
    if (got !== want) failures.push(`planSwitch: ${label}: ${got}, expected ${want}`);
  }
  // R2's path end to end: a Claude reviewer switched in from a GLM session, then reviewing from a
  // Claude session, is refused by review.mjs's decision.
  const plan = planSwitch({ models: MODELS(), blocked: [], reviewer: { default: 'luna' } }, { id: 'anthropic/claude-sonnet-4-5', variant: 'high', sessionFamily: 'glm' });
  if (!reviewRefusal(plan.config.models, plan.name, [], {})) failures.push('switch then review: a switched-in Claude reviewer reviews Claude work');
  if (!reviewRefusal(plan.config.models, plan.name, [], { HARNESS_SESSION_FAMILY: 'anthropic' })) failures.push('switch then review: HARNESS_SESSION_FAMILY=anthropic is not claude');
  for (const [label, blocked, choice, own, want] of IMPLEMENTER_CHOICE) {
    let got = 'allowed';
    try { planSwitch({ models: MODELS(), blocked, implementer: { default: 'sonnet' } }, { role: 'implementer', id: choice, sessionFamily: own }); } catch (e) {
      if (!/^Refused/.test(e.message)) throw e;
      got = 'refused';
    }
    if (got !== want) failures.push(`planImplementer: ${label} (${choice}): ${got}, expected ${want}`);
  }
}

function checkVariants(failures) {
  for (const [label, name, variant, want] of VARIANTS) {
    const config = { models: MODELS(), blocked: BLOCKED };
    const key = namedModel(config, name, { variant }, (c, m) => { throw new Error(m); });
    const got = config.models[key].variant;
    if (got !== want) failures.push(`variant: ${label}: ${got}, expected ${want}`);
    if (config.models['gpt-6.1-sol'].variant !== 'low') failures.push(`variant: ${label}: harness.json's entry was changed`);
    if (config.models[key].family !== 'openai') failures.push(`variant: ${label}: family lost`);
  }
}

function checkNamed(failures) {
  checkVariants(failures);
  // The session's family, from the Anthropic environment (the owner, 2026-10-11).
  const SESSION = [['no base URL', {}, 'claude'], ['anthropic.com', { ANTHROPIC_BASE_URL: 'https://api.anthropic.com' }, 'claude'],
    ['Z.AI', { ANTHROPIC_BASE_URL: 'https://api.z.ai/api/anthropic' }, 'glm'], ['MiniMax', { ANTHROPIC_BASE_URL: 'https://api.minimax.io/anthropic' }, 'minimax'],
    ['Moonshot', { ANTHROPIC_BASE_URL: 'https://api.moonshot.ai/anthropic' }, 'kimi'], ['override', { ANTHROPIC_BASE_URL: 'https://api.z.ai/api/anthropic', HARNESS_SESSION_FAMILY: 'Claude' }, 'claude'],
    ['unknown endpoint', { ANTHROPIC_BASE_URL: 'https://proxy.example/v1' }, null],
    // On the host only (R5): a path or a query string naming anthropic.com changes nothing.
    ['Z.AI, anthropic.com in the query', { ANTHROPIC_BASE_URL: 'https://api.z.ai/api/anthropic?target=anthropic.com' }, 'glm'],
    ['unknown host, anthropic.com in the path', { ANTHROPIC_BASE_URL: 'https://proxy.example/anthropic.com/v1' }, null],
    ['a host that only starts with anthropic.com', { ANTHROPIC_BASE_URL: 'https://anthropic.com.proxy.example/v1' }, null],
    ['an anthropic.com subdomain', { ANTHROPIC_BASE_URL: 'https://gateway.anthropic.com/v1' }, 'claude'],
    ['not a URL', { ANTHROPIC_BASE_URL: 'anthropic.com' }, null]];
  for (const [label, env, want] of SESSION) {
    const got = sessionFamily(env);
    if (got !== want) failures.push(`sessionFamily: ${label}: ${got}, expected ${want}`);
  }
  const glm = implementerFamilies(MODELS(), [], { ANTHROPIC_BASE_URL: 'https://api.z.ai/api/anthropic' });
  if (glm.families?.[0] !== 'glm') failures.push('implementerFamilies: a GLM-backed session excludes glm');
  const unknown = implementerFamilies(MODELS(), [], { ANTHROPIC_BASE_URL: 'https://proxy.example/v1' });
  if (!unknown.refuse) failures.push('implementerFamilies: an unknown endpoint is refused');
  for (const [label, names, want] of GUARD) {
    const r = implementerFamilies(MODELS(), names, {});
    const got = r.refuse ? 'refused' : r.families.join(',');
    if (got !== want) failures.push(`implementerFamilies: ${label}: ${got}, expected ${want}`);
  }
  for (const [label, name, opts, want] of NAMED) {
    const config = { models: MODELS(), blocked: BLOCKED };
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

export function choiceSelfTest() {
  const failures = [];
  checkNamed(failures);
  checkDecisions(failures);
  return { failures, count: GUARD.length + NAMED.length + VARIANTS.length + IMPLEMENTERS.length + 14
    + REVIEW.length + SWITCH.length + 2 + IMPLEMENTER_CHOICE.length };
}
