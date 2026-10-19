// Main-seeded T62 regressions. All model IDs come from the repository roster;
// no provider, credentials, network or paid CLI is used by this file.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { namedModel, reviewRefusal, implementerFamilies, sessionFamily } from '../lib/common.mjs';
import { planSwitch, planBlock } from '../lib/switch.mjs';
import { validateClaudeEnvironment, readClaudeEvents, scopeProblems } from '../lib/claude.mjs';
import { readReview } from '../lib/chain.mjs';
import { planPost } from '../lib/post.mjs';

const roster = JSON.parse(fs.readFileSync(new URL('../../../harness.json', import.meta.url), 'utf8'));
const native = roster.models['claude-sonnet'];
const openai = roster.models.luna;
const fixture = (blocked = []) => ({
  models: { native: structuredClone(native), luna: structuredClone(openai) },
  reviewer: { default: 'luna' }, implementer: { default: 'sonnet' }, blocked: [...blocked],
});
const die = (code, message) => { throw Object.assign(new Error(message), { code }); };
const clients = [
  ['Claude', { HARNESS_CLIENT: 'claude' }, 'claude', 'native', native],
  ['Codex', { CODEX_THREAD_ID: 'synthetic-thread' }, 'openai', 'luna', openai],
];

test('selection: same-family registration and review preserve both real client identities', () => {
  for (const [name, env, family, key, model] of clients) {
    const config = fixture(); const before = structuredClone(env);
    assert.equal(sessionFamily(env), family, name);
    assert.equal(reviewRefusal(config.models, key, ['native', 'luna'], env), null, name);
    assert.deepEqual(implementerFamilies(config.models, ['native', 'luna'], env).families,
      family === 'claude' ? ['claude', 'openai'] : ['openai', 'claude']);
    assert.equal(planSwitch(config, { id: model.id, name: key, family, sessionFamily: family,
      ...(model.backend ? { backend: model.backend } : {}) }).entry.family, family);
    assert.deepEqual(env, before, name);
  }
});

test('selection: legacy blocked families and ID fragments do not reject an explicit choice', () => {
  for (const blocked of [['claude'], ['openai'], ['sonnet'], [openai.id.split('/').at(-1)]]) {
    for (const key of ['native', 'luna']) {
      const config = fixture(blocked);
      assert.equal(namedModel(config, key, {}, die), key);
      assert.equal(namedModel(config, config.models[key].id, {}, die), key);
      assert.doesNotThrow(() => planSwitch(config, { id: config.models[key].id, name: key,
        sessionFamily: config.models[key].family,
        ...(config.models[key].backend ? { backend: config.models[key].backend } : {}) }));
    }
  }
});

test('selection: implementer aliases and legacy default listing remain selectable', () => {
  const config = fixture(['claude', 'sonnet']);
  assert.equal(planSwitch(config, { role: 'implementer', id: 'sonnet', sessionFamily: 'claude' }).config.implementer.default, 'sonnet');
  assert.equal(planSwitch(config, { role: 'implementer', id: 'session', sessionFamily: 'claude' }).config.implementer.default, 'session');
  const next = planBlock(fixture(), { block: openai.family }).config;
  assert.equal(next.reviewer.default, 'luna');
  assert.ok(next.blocked.includes(openai.family));
  assert.equal(namedModel(next, 'luna', {}, die), 'luna');
});

test('identity: explicit contradictory and unknown raw identities remain rejected', () => {
  const config = fixture();
  assert.throws(() => namedModel(config, 'native', { family: 'qwen' }, die));
  assert.throws(() => namedModel(config, 'acme/zeta-1', { family: 'claude' }, die));
  assert.throws(() => planSwitch(config, { id: native.id, family: 'qwen', force: true, sessionFamily: 'openai' }));
  assert.throws(() => planSwitch(config, { id: openai.id, backend: 'claude', sessionFamily: 'claude' }));
  assert.ok(reviewRefusal(config.models, 'native', ['unknown-implementer'], { HARNESS_CLIENT: 'claude' }));
  assert.ok(reviewRefusal(config.models, 'native', [], { ANTHROPIC_BASE_URL: 'https://unknown.example/v1' }));
});

test('identity: actual clients and endpoint detection cannot be silently spoofed', () => {
  assert.equal(sessionFamily({ CODEX_THREAD_ID: 'fixture', ANTHROPIC_BASE_URL: 'https://api.minimax.io' }), 'openai');
  assert.equal(sessionFamily({ HARNESS_CLIENT: 'claude', CODEX_THREAD_ID: 'fixture', ANTHROPIC_BASE_URL: 'https://api.minimax.io' }), 'minimax');
  assert.equal(sessionFamily({ CODEX_HOME: '/synthetic-config' }), 'claude');
  assert.equal(sessionFamily({ ANTHROPIC_BASE_URL: 'https://api.anthropic.com.evil.example' }), null);
  assert.equal(sessionFamily({ HARNESS_CLIENT: 'invalid' }), null);
});

const model = native.id.slice('anthropic/'.length);
const header = 'T62 review (synthetic)';
const review = [header, 'approve', 'DW1: ran synthetic check → passed', 'FILE: fixture.txt',
  'SCOPE: complete', 'Final pass done', 'approve'].join('\n');
const init = { type: 'system', subtype: 'init', session_id: 'fixture', model };
const result = { type: 'result', subtype: 'success', is_error: false, session_id: 'fixture',
  permission_denials: [], result: review };
const encode = (events) => events.map((event) => JSON.stringify(event)).join('\n') + '\n';

test('transport: native direct-provider and remapping safeguards still reject unsafe routes', () => {
  assert.doesNotThrow(() => validateClaudeEnvironment({}, model));
  for (const env of [{ ANTHROPIC_BASE_URL: 'https://api.z.ai/api/anthropic' },
    { ANTHROPIC_BASE_URL: 'http://api.anthropic.com' }, { ANTHROPIC_MODEL: 'glm-5.3' },
    { CLAUDE_CODE_USE_VERTEX: '1' }]) assert.throws(() => validateClaudeEnvironment(env, model));
});

test('transport: exact model/session, clean final and permission outcomes remain mandatory', () => {
  assert.equal(readClaudeEvents(encode([init, result]), model, 'fixture').review, review);
  for (const events of [[init], [result], [{ ...init, model: 'wrong-model' }, result],
    [{ ...init, session_id: 'other' }, result], [init, { ...result, session_id: 'other' }],
    [init, { ...result, is_error: true }], [init, { ...result, permission_denials: [{ tool_name: 'Bash' }] }]]) {
    assert.throws(() => readClaudeEvents(encode(events), model, 'fixture'));
  }
});

test('transport: coverage and missing Done-when never become automatic approval', () => {
  assert.deepEqual(scopeProblems(review, ['fixture.txt']), []);
  assert.ok(scopeProblems(review.replace('FILE: fixture.txt', ''), ['fixture.txt']).length);
  const incomplete = review.replace('DW1: ran synthetic check → passed\n', '');
  const plan = planPost({ read: readReview(incomplete, header), header, doneWhen: 1, source: 'synthetic', signature: 'synthetic' });
  assert.equal(plan.code, 4); assert.equal(plan.label, null);
});

test('defaults: planned changes preserve inputs, roster defaults and variant metadata', () => {
  const config = fixture(); const before = structuredClone(config);
  const plan = planSwitch(config, { id: native.id, name: 'native', sessionFamily: 'openai', backend: 'claude', variant: 'medium' });
  assert.deepEqual(config, before);
  assert.equal(plan.config.reviewer.default, 'native');
  assert.equal(plan.config.models.native.variant, 'medium');
  assert.equal(plan.config.implementer.default, before.implementer.default);
  const variantConfig = fixture(); const defaults = structuredClone([variantConfig.reviewer, variantConfig.implementer]);
  const key = namedModel(variantConfig, 'native', { variant: 'medium' }, die);
  assert.equal(variantConfig.models[key].variant, 'medium');
  assert.deepEqual([variantConfig.reviewer, variantConfig.implementer], defaults);
  assert.equal(JSON.parse(fs.readFileSync(new URL('../../../harness.json', import.meta.url), 'utf8')).reviewer.default, roster.reviewer.default);
});
