#!/usr/bin/env node
/** Thin wrapper so npm run db:wipe works from e2e-tests/ */
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKSPACE = path.resolve(__dirname, '../..');
const BACKEND = path.join(WORKSPACE, 'SnipKlip');
const wipeScript = path.join(BACKEND, 'scripts', 'wipe_test_data.py');
const pyCandidates = [
  path.join(WORKSPACE, '.venv', 'bin', 'python'),
  'python3',
  'python'
];
const py = pyCandidates.find((c) => c === 'python3' || c === 'python' || fs.existsSync(c));

if (!fs.existsSync(wipeScript)) {
  console.error('Missing wipe script:', wipeScript);
  process.exit(1);
}

const result = spawnSync(py, [wipeScript, '--settings=app.settings.local', ...process.argv.slice(2)], {
  cwd: BACKEND,
  stdio: 'inherit',
  env: process.env
});
process.exit(result.status ?? 1);
