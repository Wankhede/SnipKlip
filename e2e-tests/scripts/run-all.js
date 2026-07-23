#!/usr/bin/env node
/**
 * Full verification runner:
 *  1) architecture audit
 *  2) Playwright in phases (core API → monkey/BVA → UI) with backend health checks
 *  3) health summary
 *  4) ALWAYS wipe all DB application data (preserve log files) + reseed bootstrap
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const http = require('http');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const WORKSPACE = path.resolve(ROOT, '..');
const BACKEND = path.resolve(WORKSPACE, 'SnipKlip');
const BACKEND_URL = process.env.SNIPKLIP_BACKEND_URL || 'http://127.0.0.1:8082';
const FRONTEND_URL = process.env.SNIPKLIP_FRONTEND_URL || 'http://127.0.0.1:8083';
const reportsDir = path.join(ROOT, 'reports');
fs.mkdirSync(reportsDir, { recursive: true });

function run(cmd, args, opts = {}) {
  console.log(`\n>>> ${cmd} ${args.join(' ')}`);
  const result = spawnSync(cmd, args, {
    cwd: opts.cwd || ROOT,
    stdio: 'inherit',
    env: { ...process.env, ...(opts.env || {}) },
    shell: process.platform === 'win32'
  });
  return result.status ?? 1;
}

function findPython() {
  const candidates = [
    path.join(WORKSPACE, '.venv', 'bin', 'python'),
    path.join(BACKEND, '..', '.venv', 'bin', 'python'),
    'python3',
    'python'
  ];
  for (const c of candidates) {
    if (c === 'python3' || c === 'python') return c;
    if (fs.existsSync(c)) return c;
  }
  return 'python3';
}

function httpOk(url, timeoutMs = 4000) {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: timeoutMs }, (res) => {
      res.resume();
      resolve(res.statusCode > 0 && res.statusCode < 500);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function waitHealthy(label, url, attempts = 30, delayMs = 1000) {
  for (let i = 1; i <= attempts; i++) {
    // eslint-disable-next-line no-await-in-loop
    const ok = await httpOk(url);
    if (ok) {
      console.log(`[health] ${label} OK (${url})`);
      return true;
    }
    console.log(`[health] waiting for ${label}… ${i}/${attempts}`);
    // eslint-disable-next-line no-await-in-loop
    await new Promise((r) => setTimeout(r, delayMs));
  }
  console.warn(`[health] ${label} still down after ${attempts}s`);
  return false;
}

function restartBackend() {
  const startAll = path.join(WORKSPACE, 'start_all.sh');
  const manage = path.join(BACKEND, 'manage.py');
  const py = findPython();
  const logDir = path.join(WORKSPACE, '.run');
  fs.mkdirSync(logDir, { recursive: true });

  if (fs.existsSync(startAll)) {
    console.log('[health] invoking start_all.sh to bring services up');
    return run('bash', [startAll], { cwd: WORKSPACE });
  }

  if (!fs.existsSync(manage)) {
    console.warn('[health] cannot restart backend — manage.py missing');
    return 1;
  }

  console.log('[health] starting Django with nohup');
  return run(
    'bash',
    [
      '-lc',
      `cd "${BACKEND}" && export DJANGO_SETTINGS_MODULE=app.settings.local && ` +
        `nohup "${py}" manage.py runserver 0.0.0.0:8082 --noreload --settings=app.settings.local ` +
        `>> "${logDir}/backend.log" 2>&1 & echo $! > "${logDir}/backend.pid"`
    ],
    { cwd: BACKEND }
  );
}

async function ensureBackend() {
  const schemaUrl = `${BACKEND_URL.replace(/\/$/, '')}/api/schema/`;
  if (await waitHealthy('backend', schemaUrl, 5, 500)) return true;
  restartBackend();
  return waitHealthy('backend', schemaUrl, 40, 1000);
}

async function main() {
  const summary = {
    generatedAt: new Date().toISOString(),
    auditExit: null,
    phases: {},
    playwrightExit: null,
    wipeExit: null,
    playwright: null,
    health: 'UNKNOWN'
  };

  summary.auditExit = run(process.execPath, [path.join(ROOT, 'scripts/architecture-audit.js')]);

  const backendUp = await ensureBackend();
  if (!backendUp) {
    console.error('Backend not reachable — aborting Playwright (will still wipe if possible)');
    summary.playwrightExit = 1;
  } else {
    // Phase A: core API (exclude monkey/BVA so a chaos flake does not obscure contracts)
    summary.phases.coreApi = run('npx', [
      'playwright',
      'test',
      'tests/api',
      '--project=api',
      '--grep-invert',
      'Monkey|BVA'
    ]);

    // Re-check after core; restart if process died
    await ensureBackend();

    // Phase B: monkey + BVA
    summary.phases.chaos = run('npx', [
      'playwright',
      'test',
      'tests/api/05-monkey.spec.ts',
      'tests/api/06-bva.spec.ts',
      '--project=api'
    ]);

    await ensureBackend();
    await waitHealthy('frontend', FRONTEND_URL, 10, 1000);

    // Phase C: UI
    summary.phases.ui = run('npx', ['playwright', 'test', 'tests/ui', '--project=chromium']);

    summary.playwrightExit = [summary.phases.coreApi, summary.phases.chaos, summary.phases.ui].every(
      (c) => c === 0
    )
      ? 0
      : 1;
  }

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

  // Always wipe DB after the suite — keep log files, reseed admin bootstrap
  const py = findPython();
  const wipeScript = path.join(BACKEND, 'scripts', 'wipe_test_data.py');
  if (fs.existsSync(wipeScript)) {
    summary.wipeExit = run(py, [wipeScript, '--settings=app.settings.local'], { cwd: BACKEND });
  } else {
    console.warn(`wipe script missing at ${wipeScript}`);
    summary.wipeExit = 1;
  }

  if (summary.playwrightExit === 0 && summary.auditExit === 0 && summary.wipeExit === 0) {
    summary.health = 'HEALTHY';
  } else if (summary.playwrightExit === 0 && summary.wipeExit === 0) {
    summary.health = 'TESTS_PASS_WITH_AUDIT_WARNINGS';
  } else if (summary.playwrightExit === 0) {
    summary.health = 'TESTS_PASS_WIPE_FAILED';
  } else {
    summary.health = 'UNHEALTHY';
  }

  fs.writeFileSync(path.join(reportsDir, 'health-summary.json'), JSON.stringify(summary, null, 2));
  console.log('\n===== HEALTH SUMMARY =====');
  console.log(JSON.stringify(summary, null, 2));
  process.exit(summary.playwrightExit === 0 ? 0 : 1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
