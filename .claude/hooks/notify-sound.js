#!/usr/bin/env node
/*
 * Stop / SubagentStop / Notification hook — a short sound, so you can look away while Claude works.
 *   done      → Claude finished its reply          (Glass)
 *   subagent  → a helper agent finished            (Hero)
 *   needs-you → Claude is waiting on you to answer (Pop)
 *
 * Pause switch, one per computer: the file ~/.claude/sounds-paused.
 *   pause:  touch ~/.claude/sounds-paused
 *   resume: rm ~/.claude/sounds-paused
 * It is checked before every sound, so switching needs no restart.
 *
 * macOS only for now (the built-in `afplay` and system sounds). Anywhere else it stays silent.
 * The player is started detached, so the hook returns at once and never holds up Claude.
 *
 * FAIL-OPEN: an unknown event / no player / any error → no sound, exit 0. Never blocks a session.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const SOUNDS = { done: 'Glass', subagent: 'Hero', 'needs-you': 'Pop' };

function pauseFile(home) {
  return path.join(home, '.claude', 'sounds-paused');
}

// (event, platform, home) → the player to run, or null for silence.
function plan(event, platform, home) {
  if (!Object.prototype.hasOwnProperty.call(SOUNDS, event)) return null;
  if (platform !== 'darwin') return null;
  if (fs.existsSync(pauseFile(home))) return null;
  return { cmd: 'afplay', args: [`/System/Library/Sounds/${SOUNDS[event]}.aiff`] };
}

module.exports = { plan, pauseFile, SOUNDS };

if (require.main === module) {
  try {
    const p = plan(process.argv[2], process.platform, os.homedir());
    if (p) {
      const child = spawn(p.cmd, p.args, { detached: true, stdio: 'ignore' });
      child.on('error', () => {});
      child.unref();
    }
  } catch (_) { /* fail-open */ }
  process.exit(0);
}
