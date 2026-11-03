#!/usr/bin/env node
// Codex decision adapter. The existing Claude module owns the command rules.
function deny(reason) {
  return { hookSpecificOutput: {
    hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: reason,
  } };
}

function decision(event) {
  if (event && typeof event === 'object' && !Array.isArray(event)) {
    if (typeof event.hook_event_name === 'string' && event.hook_event_name && event.hook_event_name !== 'PreToolUse') return null;
    if (typeof event.tool_name === 'string' && event.tool_name && event.tool_name !== 'Bash') return null;
    if (event.hook_event_name === 'PreToolUse' && event.tool_name === 'Bash' &&
        event.tool_input && typeof event.tool_input === 'object' && !Array.isArray(event.tool_input) &&
        typeof event.tool_input.command === 'string') {
      const { analyze } = require('../../.claude/hooks/guard-dangerous-git.js');
      const reason = analyze(event.tool_input.command);
      return reason ? deny(`SAFETY CHECK: ${reason}. Codex refused this command. ` +
        'Preserve the work and use the authorized review route before attempting it again.') : null;
    }
  }
  return deny('Codex command safety input is malformed; no command was authorized.');
}

module.exports = { decision };
if (require.main === module) {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { input += chunk; });
  process.stdin.on('end', () => {
    let result;
    try { result = decision(JSON.parse(input)); }
    catch (_) { result = deny('Codex command safety check is unavailable or input is invalid; no command was authorized.'); }
    if (result) process.stdout.write(JSON.stringify(result));
  });
}
