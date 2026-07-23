import { test, expect } from '@playwright/test';
import { FRONTEND_URL } from '../../helpers/env';

const APP_PATHS = [
  '/dashboard/default',
  '/apps/customers/manage-customers',
  '/apps/employees/manage-employees',
  '/apps/services/manage-service',
  '/apps/e-commerce/product/manage-product',
  '/apps/bookings/manage-bookings',
  '/apps/invoices/manage-invoices',
  '/apps/expenses/manage-expenses',
  '/apps/coupon/manage-coupon',
  '/apps/membership/manage-membership',
  '/apps/salary/manage-salary',
  '/apps/reviews/manage-reviews',
  '/apps/kanban/board'
];

test.describe('UI route discovery smoke', () => {
  for (const path of APP_PATHS) {
    test(`GET ${path} does not return server error page`, async ({ page }) => {
      const response = await page.goto(`${FRONTEND_URL}${path}`, {
        waitUntil: 'domcontentloaded',
        timeout: 45_000
      });
      const status = response?.status() ?? 0;
      expect(status, `${path} HTTP ${status}`).toBeLessThan(500);
      const body = await page.locator('body').innerText().catch(() => '');
      expect(body.toLowerCase()).not.toContain('application error');
    });
  }
});
