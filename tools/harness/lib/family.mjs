// One name per model family, wherever the name comes from (Sol's R2 on PR 189): Claude models are
// `claude`, also when a harness.json entry or a declaration says `anthropic`. review.mjs
// (lib/common.mjs) and switch-model.mjs (lib/switch.mjs) compare families only through this, so the
// two can never disagree on a name. Free of OpenCode and git, like lib/switch.mjs.
export function canonicalFamily(f) {
  if (f === null || f === undefined) return null;
  const s = String(f).trim().toLowerCase();
  if (!s) return null;
  return s === 'anthropic' ? 'claude' : s;
}
