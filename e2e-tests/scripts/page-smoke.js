/**
 * Visit every major authenticated frontend route and fail on pageerrors /
 * Application Error. Used by snipklip-verify-and-push before test:all.
 *
 * Usage: node scripts/page-smoke.js
 * Env: FRONTEND_URL (default http://127.0.0.1:8083), ADMIN_USER, ADMIN_PASS
 */
const { chromium } = require('@playwright/test');

const FRONTEND = process.env.FRONTEND_URL || 'http://127.0.0.1:8083';
const USER = process.env.ADMIN_USER || 'admin';
const PASS = process.env.ADMIN_PASS || 'Admin@123';

const ROUTES = [
  '/dashboard/default',
  '/dashboard/analytics',
  '/apps/calendar',
  '/apps/bookings/manage-bookings',
  '/apps/bookings/add-bookings',
  '/apps/customers/manage-customers',
  '/apps/customers/add-customer',
  '/apps/invoices/manage-invoices',
  '/apps/invoices/add-invoices',
  '/apps/employees/manage-employees',
  '/apps/employees/add-employees',
  '/apps/services/manage-service',
  '/apps/services/add-service',
  '/apps/salary/manage-salary',
  '/apps/salary/add-salary',
  '/apps/kanban/board',
  '/apps/reviews/manage-reviews',
  '/apps/reports/default',
  '/apps/e-commerce/product/manage-product',
  '/apps/expenses/manage-expenses',
  '/apps/membership/manage-membership',
  '/apps/coupon/manage-coupon',
  '/apps/subscription/account/subscriptions',
  '/apps/profiles/user/personal',
  '/apps/profiles/account/basic',
  '/contact-us'
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const pageErrors = [];
  const failures = [];

  page.on('pageerror', (e) => pageErrors.push({ msg: String(e).slice(0, 400), at: page.url() }));

  await page.goto(`${FRONTEND}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.locator('input[type="text"], input:not([type="hidden"]):not([type="password"])').first().fill(USER);
  await page.locator('input[type="password"]').fill(PASS);
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(4000);
  if (!page.url().includes('/dashboard') && !page.url().includes('/apps')) {
    console.error('LOGIN_FAILED', page.url());
    process.exit(1);
  }
  console.log('LOGIN_OK', page.url());

  for (const path of ROUTES) {
    const before = pageErrors.length;
    try {
      await page.goto(`${FRONTEND}${path}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForTimeout(2500);
    } catch (e) {
      failures.push({ path, reason: `goto: ${e.message}` });
      console.log('FAIL', path, 'goto', e.message);
      continue;
    }
    const body = (await page.locator('body').innerText().catch(() => '')).toLowerCase();
    const crashed =
      body.includes('application error') ||
      body.includes('unhandled runtime') ||
      body.includes('this page could not be found');
    const newErrs = pageErrors.slice(before);
    if (crashed || newErrs.length) {
      failures.push({
        path,
        reason: crashed ? 'render crash' : newErrs.map((e) => e.msg).join(' | ')
      });
      console.log('FAIL', path, crashed ? 'render crash' : newErrs.map((e) => e.msg).join(' | '));
    } else {
      console.log('OK', path);
    }
  }

  console.log('SUMMARY', JSON.stringify({ ok: ROUTES.length - failures.length, fail: failures.length, failures }, null, 2));
  await browser.close();
  process.exit(failures.length ? 1 : 0);
})().catch((e) => {
  console.error('FATAL', e);
  process.exit(1);
});
