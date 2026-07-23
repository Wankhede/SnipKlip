#!/usr/bin/env node
/**
 * Full verification runner: architecture audit + Playwright suite + health summary.
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const reportsDir = path.join(ROOT, 'reports');
fs.mkdirSync(reportsDir, { recursive: true });

function run(cmd, args, opts = {}) {
  console.log(`\n>>> ${cmd} ${args.join(' ')}`);
  const result = spawnSync(cmd, args, {
    cwd: ROOT,
    stdio: 'inherit',
    env: process.env,
    shell: process.platform === 'win32',
    ...opts
  });
  return result.status ?? 1;
}

const summary = {
  generatedAt: new Date().toISOString(),
  auditExit: null,
  playwrightExit: null,
  playwright: null,
  health: 'UNKNOWN'
};

summary.auditExit = run(process.execPath, [path.join(ROOT, 'scripts/architecture-audit.js')]);
// Audit exit 1 means HIGH findings remain — still continue tests
summary.playwrightExit = run('npx', ['playwright', 'test']);

const resultsFile = path.join(reportsDir, 'results.json');
if (fs.existsSync(resultsFile)) {
  try {
    const results = JSON.parse(fs.readFileSync(resultsFile, 'utf8'));
    summary.playwright = {
      expected: results.stats?.expected,
      unexpected: results.stats?.unexpected,
      flaky: results.stats?.flaky,
      skipped: results.stats?.skipped,
      durationMs: results.stats?.duration
    };
  } catch {
    /* ignore */
  }
}

if (summary.playwrightExit === 0 && summary.auditExit === 0) {
  summary.health = 'HEALTHY';
} else if (summary.playwrightExit === 0) {
  summary.health = 'TESTS_PASS_WITH_AUDIT_WARNINGS';
} else {
  summary.health = 'UNHEALTHY';
}

fs.writeFileSync(path.join(reportsDir, 'health-summary.json'), JSON.stringify(summary, null, 2));
console.log('\n===== HEALTH SUMMARY =====');
console.log(JSON.stringify(summary, null, 2));
process.exit(summary.playwrightExit === 0 ? 0 : 1);
