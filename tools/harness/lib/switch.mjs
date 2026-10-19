// Switching the defaults in harness.json, kept free of OpenCode and git so it can be tested directly;
// switch-model.mjs runs the checks that need OpenCode. The roster is the owner's to change (the
// owner, 2026-10-11), through this script and the /switch-model skill:
// - implementer.default: a Claude Code model alias (sonnet, opus, haiku, fable) or any model id the
//   session's provider serves, on which the `implementer` subagent is spawned (Opus spawns Sonnet;
//   under Z.AI `sonnet` is GLM-5.3 Flash); or `session`, the main session implementing directly
//   where the provider cannot spawn one. Either runs through the session's Anthropic environment,
//   so its family is the session's (lib/common.mjs sessionFamily).
// - reviewer.default: a harness.json key, the OpenCode model that reviews unless the user names
//   another; same-family choices are permitted.
// - blocked: legacy metadata, editable with --block / --unblock; it does not restrict choices.

import { canonicalFamily } from './family.mjs';

export const ROLES = ['implementer', 'reviewer'];
export const IMPLEMENTER_ALIASES = ['sonnet', 'opus', 'haiku', 'fable'];
export const IMPLEMENTER_CHOICES = ['session', ...IMPLEMENTER_ALIASES];

// A model's family, from its id: identity metadata uses these. "opencode-go/gpt-6-luna" and
// "openai/gpt-6-luna" are both openai: the vendor, not the route. Claude models are `claude`, the
// name sessionFamily and review.mjs use (lib/family.mjs, Sol's R2 on PR 189).
const FAMILIES = [
  [/^deepseek/, 'deepseek'], [/^glm/, 'glm'], [/^(gpt|o\d|codex|chatgpt)/, 'openai'],
  [/^claude/, 'claude'], [/^kimi/, 'kimi'], [/^qwen/, 'qwen'], [/^minimax/, 'minimax'],
  [/^mimo/, 'mimo'], [/^grok/, 'xai'], [/^gemini/, 'google'], [/^longcat/, 'longcat'],
  [/^hy\d/, 'hunyuan'], [/^(llama|muse)/, 'meta'], [/^mistral|^devstral|^codestral/, 'mistral'],
];
const modelPart = (id) => String(id).split('/').slice(1).join('/').toLowerCase();
// The vendor's family when the id names a known vendor, else null: only then may --family name it.
// The model's own name decides, also behind a vendor segment that is not a family name
// (openrouter/xiaomi/mimo-v2.6-pro is mimo, Luna's R1 on PR 150).
export function knownFamilyOf(id) {
  const part = String(id).includes('/') ? modelPart(id) : String(id).toLowerCase();
  const own = part.split('/').at(-1);
  return FAMILIES.find(([re]) => re.test(part) || re.test(own))?.[1] ?? null;
}
export function familyOf(id) {
  const model = modelPart(id);
  return knownFamilyOf(id) ?? (model.match(/^[a-z]+/)?.[0] ?? model);
}

// Heavy models run at `low`, or `medium` at most; light ones at `high` (L54, #83). Heavy: Sol, GLM-5.3
// (not Flash), DeepSeek V4 Pro, MiMo V2.6 Pro, Opus, wherever they are served from (DeepSeek is
// historically blocked, now selectable under rule 6.3).
// Exactly the models the rule names (Sol's R2 on PR 94): another GLM or DeepSeek release is not heavy.
// A dated suffix is the same model, not a release: deepseek-v4-pro-0813 (the only Alibaba id with
// the night discount) is the named DeepSeek V4 Pro.
// Qwen 3.8 Max is the heavy model of Alibaba's Token Plan (the owner, 2026-10-05).
// MiniMax-M3 is the heavy model of the MiniMax Token Plan (the owner, 2026-10-06); its ladder
// is none/thinking, not the effort ladder, so its entry pins `thinking` itself.
const HEAVY = [/(^|\/)gpt-[\d.]+-sol(-fast)?$/, /(^|\/)glm-5\.3$/, /(^|\/)deepseek-v4-pro(-\d+)?$/, /(^|\/)mimo-v2\.6-pro$/, /(^|\/)qwen3\.8-max$/, /(^|\/)minimax-m3$/, /(^|\/)claude-opus/, /(^|\/)opus$/];
export const isHeavy = (id) => HEAVY.some((re) => re.test(modelPart(id)));
const EFFORTS = ['none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max'];

// The effort a switch writes when --variant is not given, from the efforts OpenCode offers for the
// model (`offered`, from `opencode models --verbose`; null when unknown): a light model `high`; a
// heavy one `low`, else `medium`, else its lowest effort (DeepSeek V4 Pro offers only high and max).
// A model whose variants are not the effort ladder keeps its own (MiniMax-M3 offers none/thinking,
// so it gets `thinking`); one that offers none at all (MiniMax-M2.7) gets no variant. A light model
// that offers no plain `high` gets the nearest below it (Qwen 3.8 Flash: `medium`).
export function defaultVariant(id, offered) {
  if (!offered) return isHeavy(id) ? 'low' : 'high';
  // Ranked, not in the order OpenCode lists them (Sol's R1 on PR 94).
  const usable = EFFORTS.filter((v) => offered.includes(v) && v !== 'none' && v !== 'max');
  if (!usable.length) {
    const own = offered.filter((v) => v !== 'none');
    return own.length ? own[0] : undefined;
  }
  if (isHeavy(id)) return ['low', 'medium'].find((v) => usable.includes(v)) ?? usable[0];
  const belowHigh = usable.filter((v) => EFFORTS.indexOf(v) < EFFORTS.indexOf('high'));
  return usable.includes('high') ? 'high' : belowHigh.at(-1) ?? usable.at(-1);
}

// The harness.json name for an id: the existing entry's, else the id's model part.
export function nameOf(config, id) {
  const found = Object.entries(config.models ?? {}).find(([, m]) => m.id === id);
  return found ? found[0] : String(id).split('/').slice(1).join('/').toLowerCase().replace(/[^a-z0-9.-]+/g, '-');
}

/**
 * The new harness.json for making `id` the default reviewer: the entry is added or updated,
 * reviewer.default becomes its name, and every other model stays for an explicit --reviewer. A
 * same-family or legacy-blocked model is selectable under rule 6.3. A `family` that contradicts
 * a known vendor in the id is still refused: model selection never changes identity.
 * Returns { config, name, entry, before, after } or throws with the reason.
 */
export function planSwitch(config, { role = 'reviewer', id, variant, name, family, force = false, sessionFamily = 'claude', backend }) {
  if (!ROLES.includes(role)) throw new Error(`--role must be one of ${ROLES.join(', ')}; got ${role}`);
  if (role === 'implementer') return planImplementer(config, id, sessionFamily);
  // `variant` has no default: a model that offers no variants (MiniMax-M2.7) must switch without
  // one, not inherit 'high' (Luna's round-2 R1, PR 115). Callers pass defaultVariant's answer.
  if (!/^[\w.-]+\/[\w./-]+$/.test(String(id ?? ''))) throw new Error(`--model must be a provider/model id, e.g. openai/gpt-5.6-luna; got ${id}`);
  if (variant === 'max') throw new Error('Effort max is never used: it was slower with no gain (L27). Use high.');
  const n = name ?? nameOf(config, id);
  const existing = config.models?.[n];
  if (existing && existing.id !== id) throw new Error(`The name ${n} already holds ${existing.id}; pass --name for ${id}.`);
  // The family established from the id decides, whatever --family says: a contradicting declaration
  // is refused, also with --force, so no entry is ever saved with a family its id contradicts (Sol's
  // R3 and re-review R1/R2 on PR 189). --force no longer overrides this; review.mjs also re-derives
  // the family from the id (lib/common.mjs entryFamily) for entries saved before.
  const known = knownFamilyOf(id);
  if (family && known && canonicalFamily(family) !== known) {
    throw new Error(`Refused: --family ${family} contradicts ${id}, whose vendor is ${known}; identity must match the id${force ? ', and --force does not override it' : ''}. Drop --family.`);
  }
  backend ??= existing?.backend ?? 'opencode';
  if (!['opencode', 'claude'].includes(backend)) throw new Error('Unknown review backend.');
  if (backend === 'claude' && !/^anthropic\/claude-/.test(id)) throw new Error('Claude backend requires anthropic/claude-* identity.');
  const entry = { id, ...(backend === 'claude' ? { backend } : {}), ...(variant !== undefined && variant !== null ? { variant } : {}), family: known ?? canonicalFamily(family ?? existing?.family ?? familyOf(id)), ...(existing?.note ? { note: existing.note } : {}) };
  const next = structuredClone(config);
  next.models = { ...next.models, [n]: entry };
  next.reviewer = { ...next.reviewer, default: n };
  return { config: next, name: n, entry, before: describeReviewer(config), after: describeReviewer(next) };
}

// The implementer's default: the implementer subagent on a Claude Code alias or a model id the
// session's provider serves, or `session` (the main session implements directly). A model id is
// taken as given: the next run shows whether the provider honours it. Legacy blocked metadata
// does not restrict the implementer's alias, id or session selection (rule 6.3).
function planImplementer(config, choice, sessionFamily = null) {
  const c = String(choice ?? '').trim();
  const lower = c.toLowerCase();
  if (!IMPLEMENTER_CHOICES.includes(lower) && !/^[\w.:-]+$/.test(c)) {
    throw new Error(`--model for the implementer is session, one of ${IMPLEMENTER_ALIASES.join(', ')}, or a model id the session's provider serves; got ${choice}`);
  }
  const value = IMPLEMENTER_CHOICES.includes(lower) ? lower : c;
  const next = structuredClone(config);
  next.implementer = { ...next.implementer, default: value };
  return { config: next, name: value, entry: { id: value }, before: describeImplementer(config), after: describeImplementer(next) };
}

// --block / --unblock edit legacy metadata, including entries naming the current default.
export function planBlock(config, { block, unblock }) {
  const list = [...(config.blocked ?? [])];
  const has = (x) => list.some((b) => b.toLowerCase() === x.toLowerCase());
  if (block) {
    if (has(block)) throw new Error(`${block} is already blocked.`);
    list.push(block);
  }
  if (unblock) {
    if (!has(unblock)) throw new Error(`${unblock} is not blocked (blocked: ${list.join(', ') || 'nothing'}).`);
    list.splice(list.findIndex((b) => b.toLowerCase() === unblock.toLowerCase()), 1);
  }
  const next = { ...structuredClone(config), blocked: list };
  return { config: next, before: `legacy blocked metadata (no selection restriction): ${(config.blocked ?? []).join(', ') || 'nothing'}`, after: `legacy blocked metadata (no selection restriction): ${list.join(', ') || 'nothing'}` };
}

const describeReviewer = (c) => {
  const d = c.reviewer?.default;
  const e = c.models?.[d];
  return d ? `reviewer: ${d} (${e?.id ?? '?'}, ${e?.variant ?? 'no variant'}, family ${e?.family ?? '?'})` : 'reviewer: (none)';
};
const describeImplementer = (c) => {
  const d = c.implementer?.default ?? 'session';
  return `implementer: ${d === 'session' ? 'the main session, directly' : `the implementer subagent on ${d}`} (the session's family, through its endpoint)`;
};

// What runs now: the session's family, both defaults, the blocked list, then the other models
// registered for an explicit --reviewer.
export function showRoles(config, { sessionFamily = null } = {}) {
  const d = config.reviewer?.default;
  const others = Object.entries(config.models ?? {}).filter(([m]) => m !== d).map(([m, x]) => `${m} = ${x.id}`);
  return [
    `session: family ${sessionFamily ?? 'unknown (set HARNESS_SESSION_FAMILY)'}, from the detected client and provider environment`,
    describeImplementer(config), describeReviewer(config),
    `legacy blocked metadata (no selection restriction): ${(config.blocked ?? []).join(', ') || 'nothing'}`,
    ...(others.length ? [`also registered, for --reviewer: ${others.join(', ')}`] : []),
  ].join('\n');
}
