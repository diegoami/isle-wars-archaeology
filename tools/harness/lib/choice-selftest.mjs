// The model-choice self-test (CLAUDE.md rule 6): run by `node tools/harness/review.mjs --self-test`,
// so CI runs it. No model is called. It pins Sol's findings on PR 164: a model's family is never
// taken from a declaration (R1 of both rounds) and an implementer name always resolves to a family
// (R2); and the 2026-10-11 default: no implementer named means Claude implemented.

import { namedModel, familyOf, implementerFamilies } from './common.mjs';

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
  ['DeepSeek on any route', 'openrouter/deepseek/deepseek-v4-pro', {}, 'refused'],
  ['Alibaba without --alibaba', 'ali-glm', {}, 'refused'],
  ['Alibaba with --alibaba', 'ali-glm', { alibaba: true }, 'glm'],
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
  ['no model: label: Claude implemented', [], 'claude'],
  ['--exclude ","', ','.split(',').map((x) => x.trim()).filter(Boolean), 'claude'],
  ['blank names', ['', ' '], 'claude'],
  ['an unknown name', ['nonsense'], 'refused'],
  ['a registered id', ['openai/gpt-6.1-sol'], 'openai'],
  ['two names, one family', ['luna', 'openai'], 'openai'],
];

function checkVariants(failures) {
  for (const [label, name, variant, want] of VARIANTS) {
    const config = { models: MODELS() };
    const key = namedModel(config, name, { variant }, (c, m) => { throw new Error(m); });
    const got = config.models[key].variant;
    if (got !== want) failures.push(`variant: ${label}: ${got}, expected ${want}`);
    if (config.models['gpt-6.1-sol'].variant !== 'low') failures.push(`variant: ${label}: harness.json's entry was changed`);
    if (config.models[key].family !== 'openai') failures.push(`variant: ${label}: family lost`);
  }
}

function checkNamed(failures) {
  checkVariants(failures);
  for (const [label, names, want] of GUARD) {
    const r = implementerFamilies(MODELS(), names);
    const got = r.refuse ? 'refused' : r.families.join(',');
    if (got !== want) failures.push(`implementerFamilies: ${label}: ${got}, expected ${want}`);
  }
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

export function choiceSelfTest() {
  const failures = [];
  checkNamed(failures);
  return { failures, count: GUARD.length + NAMED.length + VARIANTS.length + IMPLEMENTERS.length };
}
