#!/usr/bin/env node
/**
 * Static architecture / contract audit for SnipKlip.
 * Scans backend urls + frontend services and reports mismatches.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '../..');
const BACKEND = path.join(ROOT, 'SnipKlip');
const FRONTEND_CANDIDATES = [
  path.join(ROOT, 'snipklip-frontend'),
  path.join(require('os').homedir(), 'snipklip-frontend'),
  '/Users/k_wankhede/snipklip-frontend'
];
const FRONTEND = FRONTEND_CANDIDATES.find((p) => fs.existsSync(path.join(p, 'src/services'))) || FRONTEND_CANDIDATES[0];

const findings = [];
const systemMap = {
  backendUrlFile: path.join(BACKEND, 'api/urls.py'),
  endpoints: [],
  frontendServices: [],
  models: [],
  contractIssues: [],
  antiPatterns: []
};

function read(file) {
  try {
    return fs.readFileSync(file, 'utf8');
  } catch {
    return '';
  }
}

function walk(dir, filter, acc = []) {
  if (!fs.existsSync(dir)) return acc;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (['node_modules', '.git', '.next', '__pycache__', '.venv'].includes(entry.name)) continue;
      walk(full, filter, acc);
    } else if (filter(entry.name, full)) {
      acc.push(full);
    }
  }
  return acc;
}

// --- Endpoints from urls.py ---
const urlsSrc = read(systemMap.backendUrlFile);
const pathRe = /path\(\s*'([^']+)'/g;
let m;
while ((m = pathRe.exec(urlsSrc))) {
  systemMap.endpoints.push(`/api/v3/${m[1]}`);
}

// --- Models ---
const modelsFile = path.join(BACKEND, 'backend/models.py');
const modelsSrc = read(modelsFile);
const modelRe = /^class\s+(\w+)\(.*Model/gm;
while ((m = modelRe.exec(modelsSrc))) {
  systemMap.models.push(m[1]);
}

// --- Frontend services ---
const serviceFiles = walk(path.join(FRONTEND, 'src/services'), (n) => n.endsWith('.ts'));
for (const file of serviceFiles) {
  const src = read(file);
  const calls = [...src.matchAll(/url:\s*[`'"]([^`'"]+)[`'"]/g)].map((x) => x[1]);
  systemMap.frontendServices.push({
    file: path.relative(FRONTEND, file),
    urls: [...new Set(calls)]
  });
}

// --- Contract / anti-pattern checks ---
const constants = read(path.join(BACKEND, 'api/constants.py'));
if (constants.includes('ALL_SERVICE_RETRIEVED = "Successfully retrieved all expense')) {
  findings.push({ severity: 'HIGH', issue: 'SERVICE messages still aliased to expense copy in constants.py' });
}
if (!constants.includes('ALL_PRODUCT_RETRIEVED')) {
  findings.push({ severity: 'MED', issue: 'Missing ALL_PRODUCT_RETRIEVED constant' });
}

const inventory = read(path.join(BACKEND, 'api/views/inventory.py'));
if (inventory.includes('ALL_EXPENSE_RETRIEVED') && inventory.includes('getAllProducts')) {
  findings.push({ severity: 'HIGH', issue: 'inventory.getAllProducts still returns expense message' });
}
if (inventory.includes('Expense._meta.get_fields()')) {
  findings.push({ severity: 'HIGH', issue: 'Product detail lookup validates against Expense fields' });
}

const job = read(path.join(BACKEND, 'api/views/job.py'));
if (job.includes('ALL_EXPENSE_RETRIEVED')) {
  findings.push({ severity: 'HIGH', issue: 'job list still uses ALL_EXPENSE_RETRIEVED' });
}

const voucher = read(path.join(BACKEND, 'api/views/voucher.py'));
if (voucher.includes('ALL_EXPENSE_RETRIEVED')) {
  findings.push({ severity: 'HIGH', issue: 'coupon list still uses ALL_EXPENSE_RETRIEVED' });
}

const todos = read(path.join(BACKEND, 'api/views/todos.py'));
if (todos.includes('ALL_TODO_RETRIEVED.values')) {
  findings.push({ severity: 'HIGH', issue: 'todos uses Enum.values instead of .value (runtime 500)' });
}

const review = read(path.join(BACKEND, 'api/views/review.py'));
if (review.includes("data['salon_id']") && review.includes('request.method == "GET"')) {
  findings.push({ severity: 'HIGH', issue: 'reviews GET still uses required KeyError-prone data[salon_id]' });
}
if (review.includes("data['invoice_id']")) {
  findings.push({ severity: 'HIGH', issue: 'reviews POST still KeyError on invoice_id' });
}

const salary = read(path.join(BACKEND, 'api/views/salary.py'));
if (!salary.includes('import datetime') && salary.includes('datetime.datetime')) {
  findings.push({ severity: 'HIGH', issue: 'salary.py uses datetime without import' });
}

const feJob = read(path.join(FRONTEND, 'src/services/job.ts'));
if (feJob.includes('delete-product')) {
  findings.push({ severity: 'HIGH', issue: 'frontend deleteJob still points at delete-product' });
}

// Frontend rows[0] assumptions
const feSrcFiles = walk(path.join(FRONTEND, 'src'), (n) => n.endsWith('.ts') || n.endsWith('.tsx'));
let rows0 = 0;
for (const f of feSrcFiles) {
  const s = read(f);
  const c = (s.match(/\.rows\[0\]/g) || []).length;
  rows0 += c;
}
if (rows0 > 0) {
  findings.push({
    severity: 'MED',
    issue: `Frontend uses response.data.data.rows[0] (or similar) in ~${rows0} places without empty guards`
  });
}

systemMap.contractIssues = findings;
systemMap.antiPatterns = [
  'AccessControlMiddleware trusts client-supplied user_id/group/subscription_name when JWT decorator absent',
  'CORS_ALLOW_ALL_ORIGINS often True in local settings',
  'Many list endpoints lack @jwt_authentication_required',
  'Duplicate business rows + Model.objects.get() can 500 (MultipleObjectsReturned)'
];

const outDir = path.join(ROOT, 'e2e-tests', 'reports');
fs.mkdirSync(outDir, { recursive: true });
const reportPath = path.join(outDir, 'architecture-audit.json');
fs.writeFileSync(reportPath, JSON.stringify({ generatedAt: new Date().toISOString(), systemMap, findings }, null, 2));

const openHigh = findings.filter((f) => f.severity === 'HIGH');
console.log('SnipKlip architecture audit');
console.log(`  endpoints: ${systemMap.endpoints.length}`);
console.log(`  models: ${systemMap.models.length}`);
console.log(`  frontend services: ${systemMap.frontendServices.length}`);
console.log(`  findings: ${findings.length} (${openHigh.length} HIGH)`);
for (const f of findings) {
  console.log(`  [${f.severity}] ${f.issue}`);
}
console.log(`  wrote ${reportPath}`);

process.exit(openHigh.length ? 1 : 0);
