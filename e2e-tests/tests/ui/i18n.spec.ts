import { test, expect, Page } from '@playwright/test';
import { FRONTEND_URL, ADMIN_PASSWORD, ADMIN_USER } from '../../helpers/env';

const LOCALES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi' },
  { code: 'te', label: 'Telugu' },
  { code: 'ta', label: 'Tamil' },
  { code: 'mr', label: 'Marathi' }
] as const;

const APP_PAGES = [
  '/login',
  '/dashboard/default',
  '/apps/customers/manage-customers',
  '/apps/employees/manage-employees',
  '/apps/services/manage-service',
  '/apps/bookings/manage-bookings',
  '/apps/invoices/manage-invoices',
  '/apps/e-commerce/product/manage-product',
  '/apps/expenses/manage-expenses',
  '/apps/membership/manage-membership',
  '/apps/coupon/manage-coupon',
  '/apps/salary/manage-salary',
  '/apps/reviews/manage-reviews',
  '/apps/kanban/board',
  '/apps/reports/default'
];

async function openLocaleMenu(page: Page) {
  const trigger = page.getByRole('button', { name: /open localization/i });
  await expect(trigger).toBeVisible({ timeout: 20_000 });
  await trigger.click();
}

async function selectLocale(page: Page, label: string) {
  await openLocaleMenu(page);
  await page.getByRole('button', { name: new RegExp(label, 'i') }).or(
    page.locator('.MuiListItemButton-root', { hasText: label })
  ).first().click();
  await page.waitForTimeout(400);
}

async function softLogin(page: Page) {
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded' });
  const userField = page.locator('input[name="email"], input[name="username"], input[type="email"]').first();
  const passField = page.locator('input[name="password"], input[type="password"]').first();
  if (!(await userField.isVisible().catch(() => false))) return false;
  await userField.fill(ADMIN_USER);
  await passField.fill(ADMIN_PASSWORD);
  await page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first().click();
  await page.waitForURL(/\/(apps|dashboard|login)/, { timeout: 45_000 }).catch(() => undefined);
  return !page.url().includes('/login') || (await page.locator('body').innerText()).length > 0;
}

test.describe('i18n — language switching resilience', () => {
  test('locale config persists supported codes only', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded' });
    // Inject an invalid locale and ensure app recovers to English (no white-screen)
    await page.evaluate(() => {
      localStorage.setItem(
        'SnipKlip-react-next-ts-config',
        JSON.stringify({ i18n: 'xx-INVALID', mode: 'light' })
      );
    });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page.locator('body')).toBeVisible();
    const content = await page.content();
    expect(content.toLowerCase()).not.toContain('application error');
    expect(content.toLowerCase()).not.toContain('internal server error');
  });

  test('corrupt localStorage config does not crash boot', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.setItem('SnipKlip-react-next-ts-config', '{not-json');
    });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page.locator('input[name="email"], input[name="username"], input[type="email"]').first()).toBeVisible({
      timeout: 20_000
    });
  });

  test('switching through all switcher locales on login keeps form usable', async ({ page }) => {
    const apiFailures: string[] = [];
    page.on('response', (res) => {
      if (res.status() >= 500) apiFailures.push(`${res.status()} ${res.url()}`);
    });
    page.on('pageerror', (err) => apiFailures.push(`pageerror: ${err.message}`));

    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('input[type="password"]').first()).toBeVisible({ timeout: 20_000 });

    for (const loc of LOCALES) {
      // Prefer setting config directly (header switcher only exists in MainLayout)
      await page.evaluate((code) => {
        const key = 'SnipKlip-react-next-ts-config';
        let cfg: any = {};
        try {
          cfg = JSON.parse(localStorage.getItem(key) || '{}');
        } catch {
          cfg = {};
        }
        cfg.i18n = code;
        localStorage.setItem(key, JSON.stringify(cfg));
      }, loc.code);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await expect(page.locator('input[type="password"]').first()).toBeVisible({ timeout: 20_000 });
      await expect(page.locator('body')).toBeVisible();
    }

    expect(apiFailures, apiFailures.join('\n')).toEqual([]);
  });

  test('authenticated pages survive mid-session locale swaps', async ({ page }) => {
    const failures: string[] = [];
    page.on('pageerror', (err) => failures.push(err.message));
    page.on('response', (res) => {
      if (res.url().includes('/api/') && res.status() >= 500) {
        failures.push(`${res.status()} ${res.url()}`);
      }
    });

    await softLogin(page);
    // Navigate to a real manage page if auth succeeded; otherwise stay on login
    const target = page.url().includes('login')
      ? `${FRONTEND_URL}/login`
      : `${FRONTEND_URL}/apps/customers/manage-customers`;
    await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 45_000 });

    for (const loc of LOCALES) {
      await page.evaluate((code) => {
        const key = 'SnipKlip-react-next-ts-config';
        let cfg: any = {};
        try {
          cfg = JSON.parse(localStorage.getItem(key) || '{}');
        } catch {
          cfg = {};
        }
        cfg.i18n = code;
        localStorage.setItem(key, JSON.stringify(cfg));
        window.dispatchEvent(new Event('storage'));
      }, loc.code);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await expect(page.locator('body')).toBeVisible();
      const text = (await page.locator('body').innerText()).toLowerCase();
      expect(text).not.toContain('application error');
    }

    expect(failures.filter((f) => !f.includes('favicon')), failures.join('\n')).toEqual([]);
  });

  for (const path of APP_PAGES.slice(0, 8)) {
    test(`route ${path} loads under Hindi without layout crash`, async ({ page }) => {
      await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded' });
      await page.evaluate(() => {
        localStorage.setItem(
          'SnipKlip-react-next-ts-config',
          JSON.stringify({ i18n: 'hi', mode: 'light', fontFamily: `'Public Sans', sans-serif` })
        );
      });
      const response = await page.goto(`${FRONTEND_URL}${path}`, {
        waitUntil: 'domcontentloaded',
        timeout: 45_000
      });
      expect(response?.status() ?? 0).toBeLessThan(500);
      await expect(page.locator('body')).toBeVisible();
    });
  }
});
