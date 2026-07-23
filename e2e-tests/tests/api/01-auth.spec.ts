import { test, expect } from '@playwright/test';
import { apiLogin, authHeaders, businessContext, expectNotServerError, getJson } from '../../helpers/api';
import { BACKEND_URL } from '../../helpers/env';

test.describe('Auth & Authorization', () => {
  test('login returns access_token and session context', async ({ request }) => {
    const session = await apiLogin(request);
    expect(session.accessToken.split('.').length).toBe(3);
    expect(Number(session.userId)).toBeGreaterThan(0);
    expect(session.group).toBeTruthy();
  });

  test('login rejects invalid credentials without 500', async ({ request }) => {
    const response = await request.post(`${BACKEND_URL}/api/v3/login/`, {
      data: { username: 'admin', password: 'definitely-wrong-password' }
    });
    await expectNotServerError(response, 'invalid login');
    expect(response.status()).toBeLessThan(500);
    expect([400, 401, 403, 404].includes(response.status()) || !(await response.json()).data?.access_token).toBeTruthy();
  });

  test('login rejects empty payload without 500', async ({ request }) => {
    const response = await request.post(`${BACKEND_URL}/api/v3/login/`, { data: {} });
    await expectNotServerError(response, 'empty login');
  });

  test('protected list without token does not 500', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/customers/`, {
      params: { salon_id: 3, branch_id: 1, user_id: 1, group: 'Admin', subscription_name: 'Premium' }
    });
    // Some endpoints are JWT-gated; others rely on middleware only — never 500
    await expectNotServerError(response, 'customers unauthenticated');
  });

  test('expired/garbage bearer token does not 500 on JWT endpoints', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/services/`, {
      headers: { Authorization: 'Bearer not.a.real.jwt' },
      params: { salon_id: 3, branch_id: 1, user_id: 1, group: 'Admin', subscription_name: 'Premium' }
    });
    await expectNotServerError(response, 'services garbage token');
  });

  test('user-details returns contract fields after login', async ({ request }) => {
    const session = await apiLogin(request);
    const response = await request.get(`${BACKEND_URL}/api/v3/user-details/`, {
      headers: authHeaders(session),
      params: { email: 'admin@snipklip.in', user_id: String(session.userId) }
    });
    await expectNotServerError(response, 'user-details');
    const body = await getJson(response);
    expect(body?.data?.user_id || body?.data?.group).toBeTruthy();
  });

  test('non-admin without subscription gets controlled denial (not 500)', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/customers/`, {
      params: {
        salon_id: 3,
        branch_id: 1,
        user_id: 999999,
        group: 'Manager',
        subscription_name: '',
        current_page: 'WEB_HEADER_CUSTOMER'
      }
    });
    await expectNotServerError(response, 'missing subscription');
    // Middleware returns plain-text 400 DO-NOT-HAVE-SUBSCRIPTION
    if (response.status() === 400) {
      const text = await response.text();
      expect(text).toContain('DO-NOT-HAVE-SUBSCRIPTION');
    }
  });
});
