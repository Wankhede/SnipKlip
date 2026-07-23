import { test, expect } from '@playwright/test';

const ROUTES = ['/', '/login', '/register', '/pricing', '/contact-us', '/about-us', '/forgot-password'];
const LOCALES = ['en', 'hi', 'te', 'ta', 'mr', 'xx-BAD', ''];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

test.describe('Monkey testing — UI chaos', () => {
  test('rapid navigation across public routes never whitescreens', async ({ page }) => {
    for (let i = 0; i < 12; i++) {
      const path = pick(ROUTES);
      const res = await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 45_000 });
      expect(res?.status() ?? 0).toBeLessThan(500);
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('locale thrashing mid-navigation does not crash', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    for (const code of LOCALES) {
      await page.evaluate((i18n) => {
        localStorage.setItem(
          'SnipKlip-react-next-ts-config',
          JSON.stringify({ i18n, mode: 'light' })
        );
      }, code);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await expect(page.locator('body')).toBeVisible();
      const html = (await page.content()).toLowerCase();
      expect(html).not.toContain('application error');
    }
  });

  test('monkey click spam on login controls stays stable', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    const submit = page.locator('button[type="submit"]').first();
    await expect(submit).toBeVisible({ timeout: 20_000 });
    for (let i = 0; i < 8; i++) {
      await submit.click({ force: true }).catch(() => undefined);
    }
    await expect(page.locator('body')).toBeVisible();
    expect(page.url().length).toBeGreaterThan(0);
  });
});
