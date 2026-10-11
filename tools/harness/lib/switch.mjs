// Switching the default reviewer in harness.json (reviewer.default), kept free of OpenCode and git
// so it can be tested directly. switch-model.mjs runs the checks that need OpenCode. The implementer
// is the main session or a Claude agent (CLAUDE.md rule 6, 2026-10-11), so the one role here is the
// reviewer, and a model of the Claude family is refused: it would be the implementer's family.

export const ROLES = ['reviewer'];

// A model's family, from its id: the family rule (L3) compares these. "opencode-go/gpt-6-luna" and
// "openai/gpt-6-luna" are both openai: the vendor, not the route.
const FAMILIES = [
  [/^deepseek/, 'deepseek'], [/^glm/, 'glm'], [/^(gpt|o\d|codex|chatgpt)/, 'openai'],
  [/^claude/, 'anthropic'], [/^kimi/, 'kimi'], [/^qwen/, 'qwen'], [/^minimax/, 'minimax'],
  [/^mimo/, 'mimo'], [/^grok/, 'xai'], [/^gemini/, 'google'], [/^longcat/, 'longcat'],
  [/^hy\d/, 'hunyuan'], [/^(llama|muse)/, 'meta'], [/^mistral|^devstral|^codestral/, 'mistral'],
];
const modelPart = (id) => String(id).split('/').slice(1).join('/').toLowerCase();
// The vendor's family when the id names a known vendor, else null: only then may --family name it.
// The model's own name decides, also behind a vendor segment that is not a family name
// (openrouter/xiaomi/mimo-v2.6-pro is mimo, Luna's R1 on PR 150).
export function knownFamilyOf(id) {
  const part = modelPart(id);
  const own = part.split('/').at(-1);
  return FAMILIES.find(([re]) => re.test(part) || re.test(own))?.[1] ?? null;
}
export function familyOf(id) {
  const model = modelPart(id);
  return knownFamilyOf(id) ?? (model.match(/^[a-z]+/)?.[0] ?? model);
}

// Heavy models run at `low`, or `medium` at most; light ones at `high` (L54, #83). Heavy: Sol, GLM-5.3
// (not Flash), DeepSeek V4 Pro, MiMo V2.6 Pro, Opus, wherever they are served from (DeepSeek is
// blacklisted since 2026-10-09, but still recognised).
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
 * Claude-family model is refused: the implementer is Claude, and the reviewer is never the
 * implementer's family. A `family` that contradicts a known vendor in the id is refused too, so
 * --family can never carry a model past the family rule (Luna's R1 on PR 17).
 * Returns { config, name, entry, before, after } or throws with the reason.
 */
export function planSwitch(config, { role = 'reviewer', id, variant, name, family, force = false }) {
  // `variant` has no default: a model that offers no variants (MiniMax-M2.7) must switch without
  // one, not inherit 'high' (Luna's round-2 R1, PR 115). Callers pass defaultVariant's answer.
  if (!ROLES.includes(role)) throw new Error(`--role must be ${ROLES.join(', ')}; got ${role}`);
  if (!/^[\w.-]+\/[\w./-]+$/.test(String(id ?? ''))) throw new Error(`--model must be a provider/model id, e.g. openai/gpt-5.6-luna; got ${id}`);
  if (variant === 'max') throw new Error('Effort max is never used: it was slower with no gain (L27). Use high.');
  if (/deepseek/i.test(id)) throw new Error('Refused: DeepSeek is never used, on any route (CLAUDE.md rule 6).');
  const n = name ?? nameOf(config, id);
  const existing = config.models?.[n];
  if (existing && existing.id !== id) throw new Error(`The name ${n} already holds ${existing.id}; pass --name for ${id}.`);
  const known = knownFamilyOf(id);
  if (family && known && family !== known && !force) {
    throw new Error(`Refused: --family ${family} contradicts ${id}, whose vendor is ${known}; the family rule compares vendors. Drop --family, or pass --force.`);
  }
  const entry = { id, ...(variant !== undefined && variant !== null ? { variant } : {}), family: family ?? existing?.family ?? familyOf(id), ...(existing?.note ? { note: existing.note } : {}) };
  if ([entry.family, known].some((f) => f === 'anthropic' || f === 'claude')) {
    throw new Error('Refused: a Claude model cannot be the default reviewer: Claude implements, and the reviewer is never the implementer\'s family (CLAUDE.md rule 6).');
  }
  const describe = (c) => {
    const d = c.reviewer?.default;
    const e = c.models?.[d];
    return d ? `${d} (${e?.id ?? '?'}, ${e?.variant ?? 'no variant'})` : '(none)';
  };
  const next = structuredClone(config);
  next.models = { ...next.models, [n]: entry };
  next.reviewer = { ...next.reviewer, default: n };
  return { config: next, name: n, entry, before: describe(config), after: describe(next) };
}

// What runs now: the default reviewer, then the models on watch (L35), if any.
export function showRoles(config) {
  const d = config.reviewer?.default;
  const e = config.models?.[d] ?? {};
  const line = d ? `reviewer: ${d} = ${e.id ?? '?'} (${e.variant ?? 'no variant'}, family ${e.family ?? '?'})` : 'reviewer: (none)';
  const others = Object.entries(config.models ?? {}).filter(([m]) => m !== d).map(([m, x]) => `${m} = ${x.id}`);
  return [line, 'implementer: the main session, or a Claude agent (CLAUDE.md rule 6)', ...(others.length ? [`also registered, for --reviewer: ${others.join(', ')}`] : [])].join('\n');
}
