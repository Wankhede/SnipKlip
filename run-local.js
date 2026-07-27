#!/usr/bin/env node
/**
 * SnipKlip — single local launcher for Windows, macOS, and Linux.
 *
 * Cursor / VS Code / any terminal:
 *   node run-local.js
 *   node run-local.js stop|status|restart
 *
 * Dispatches to run-local.bat (Windows) or run-local.sh (macOS/Linux).
 */
'use strict';

const { spawnSync } = require('child_process');
const path = require('path');

const root = __dirname;
const args = process.argv.slice(2);
const isWin = process.platform === 'win32';

let result;
if (isWin) {
  result = spawnSync(
    process.env.ComSpec || 'cmd.exe',
    ['/d', '/s', '/c', path.join(root, 'run-local.bat'), ...args],
    { cwd: root, stdio: 'inherit', windowsHide: false }
  );
} else {
  result = spawnSync('bash', [path.join(root, 'run-local.sh'), ...args], {
    cwd: root,
    stdio: 'inherit',
  });
}

if (result.error) {
  console.error('ERROR: failed to start launcher:', result.error.message);
  process.exit(1);
}
process.exit(result.status == null ? 1 : result.status);
