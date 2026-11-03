#!/usr/bin/env node
/* Shared read-only status collection. The Claude command entry retains its bounded fetch and
 * release notice; the Codex adapter explicitly disables both. This is a nudge, never a gate. */
const { execFileSync } = require('child_process');

function run(program, args, ms) {
  try {
    return execFileSync(program, args, {
      encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: ms || 4000,
    }).trim();
  } catch (_) { return null; }
}

function collectStatus(root, options = {}) {
  const execute = options.run || run;
  const git = (args, ms) => execute('git', ['-C', root, ...args], ms);
  if (git(['rev-parse', '--is-inside-work-tree'], 3000) !== 'true') return { isRepo: false };
  const branch = git(['rev-parse', '--abbrev-ref', 'HEAD'], 3000);
  if (options.refresh !== false) git(['fetch', '--quiet', 'origin', 'main'], 8000);
  const behindText = git(['rev-list', '--count', 'HEAD..origin/main'], 3000);
  const behind = typeof behindText === 'string' && /^\d+$/.test(behindText) ? Number(behindText) : null;
  const dirtyText = git(['status', '--porcelain'], 3000);
  const dirty = dirtyText === null ? null : dirtyText.split('\n').filter(Boolean).length;
  let who = '';
  try {
    const readOperator = options.readOperator || (() => {
      const fs = require('fs');
      const p = require('path').join(root, '.aios/local-operator.json');
      return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : {};
    });
    const operator = readOperator();
    who = operator.display_name || operator.operator || '';
  } catch (_) { /* optional greeting */ }
  const newer = options.releaseNotice === false ? '' : execute('python3', [
    require('path').join(root, 'scripts/aios/aios.py'), 'release', 'notice', '--target', root,
  ], 15000);
  return { isRepo: true, branch, behind, dirty, who, newer };
}

function formatStatus(state, options = {}) {
  if (!state.isRepo) return '';
  const start = options.startMyDay || '/start-my-day';
  const wrap = options.wrapUp || '/wrap-up';
  const hi = state.who ? `${state.who} — ` : '';
  const lines = [];
  if (state.branch === 'main') {
    lines.push(`⚠️  ${hi}you're on **main** (the official timeline). Don't work here — run \`${start}\` to start safely on your own branch.`);
  } else if (state.behind > 0) {
    lines.push(`👋 ${hi}branch \`${state.branch}\` is **${state.behind} commit${state.behind === 1 ? '' : 's'} behind main**. Run \`${start}\` to sync before you work.`);
  }
  if (state.dirty > 0 && state.branch !== 'main') {
    lines.push(`   You have ${state.dirty} uncommitted change${state.dirty === 1 ? '' : 's'} — \`${wrap}\` will commit + push them cleanly so they're not stranded.`);
  }
  if (state.newer) lines.push(`📦 ${state.newer}`);
  if (options.localOnly) {
    lines.push(state.behind === null ? 'Remote comparison unavailable; remote freshness was not checked.' :
      'Uses locally cached origin/main; remote freshness was not checked.');
    if (state.branch === null) lines.push('Current branch is unavailable.');
    if (state.dirty === null) lines.push('Working-tree status is unavailable.');
  }
  return lines.length ? `[git status check]\n${lines.join('\n')}\n` : '';
}

module.exports = { collectStatus, formatStatus };
if (require.main === module) {
  try {
    const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    process.stdout.write(formatStatus(collectStatus(root)));
  } catch (_) { /* Claude startup remains nonblocking. */ }
}
