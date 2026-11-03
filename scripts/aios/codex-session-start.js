#!/usr/bin/env node
// Local status guidance only. No fetch, release query, identity API or permission decision.
const fs = require('fs');
const path = require('path');

function decision(event, options = {}) {
  if (event && typeof event.hook_event_name === 'string' && event.hook_event_name && event.hook_event_name !== 'SessionStart') return null;
  try {
    if (!event || event.hook_event_name !== 'SessionStart' || typeof event.cwd !== 'string' ||
        !path.isAbsolute(event.cwd)) throw new Error('invalid event');
    const root = fs.realpathSync(options.root || path.resolve(__dirname, '../..'));
    const cwd = fs.realpathSync(event.cwd);
    if (!fs.statSync(cwd).isDirectory()) throw new Error('invalid directory');
    const relative = path.relative(root, cwd);
    if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
      throw new Error('outside workspace');
    }
    const { collectStatus, formatStatus } = require('../../.claude/hooks/git-staleness-check.js');
    const state = collectStatus(root, { ...options, refresh: false, releaseNotice: false });
    const context = formatStatus(state, { localOnly: true, startMyDay: '$start-my-day', wrapUp: '$wrap-up' });
    if (!context) throw new Error('status unavailable');
    return { hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: context.slice(0, 6000) } };
  } catch (_) {
    return { systemMessage: 'Local startup status is unavailable. No remote freshness or role authorization was established.' };
  }
}

module.exports = { decision };
if (require.main === module) {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { input += chunk; });
  process.stdin.on('end', () => {
    let event;
    try { event = JSON.parse(input); } catch (_) { event = null; }
    const result = decision(event);
    if (result) process.stdout.write(JSON.stringify(result));
  });
}
