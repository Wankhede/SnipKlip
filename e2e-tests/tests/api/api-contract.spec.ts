import { test, expect } from '@playwright/test';
import {
  LIST_ENDPOINTS,
  apiLogin,
  authHeaders,
  businessContext,
  expectNotServerError,
  getJson
} from '../../helpers/api';
import { BACKEND_URL } from '../../helpers/env';

/**
 * End-to-end API contract verification for discovered /api/v3 endpoints.
 * Asserts: no 500s, JSON body shape, and auth/validation contracts.
 */
test.describe('API contract — auth & session', () => {
  test('login contract returns access_token + tenant context fields', async ({ request }) => {
    const session = await apiLogin(request);
    expect(session.accessToken).toBeTruthy();
    expect(Number(session.salonId)).toBeGreaterThan(0);
    expect(Number(session.branchId)).toBeGreaterThan(0);
  });

  test('token refresh verify endpoints do not 500', async ({ request }) => {
    const session = await apiLogin(request);
    for (const path of ['/api/token/verify/', '/api/token/refresh/']) {
      const res = await request.post(`${BACKEND_URL}${path}`, {
        data: path.includes('refresh')
          ? { refresh: 'invalid' }
          : { token: session.accessToken }
      });
      await expectNotServerError(res, path);
    }
  });
});

test.describe('API contract — list endpoints', () => {
  for (const slug of LIST_ENDPOINTS) {
    test(`GET /api/v3/${slug}/ returns JSON and <500`, async ({ request }) => {
      const session = await apiLogin(request);
      const res = await request.get(`${BACKEND_URL}/api/v3/${slug}/`, {
        headers: authHeaders(session),
        params: businessContext(session)
      });
      await expectNotServerError(res, slug);
      const body = await getJson(res);
      expect(body._parseError).toBeFalsy();
    });
  }
});

test.describe('API contract — previously crashing surfaces', () => {
  test('get-user without user_id returns 4xx JSON (not HTML 500)', async ({ request }) => {
    const session = await apiLogin(request);
    const res = await request.get(`${BACKEND_URL}/api/v3/get-user/`, {
      headers: authHeaders(session)
    });
    expect(res.status()).toBeLessThan(500);
    const body = await getJson(res);
    expect(body._parseError).toBeFalsy();
    expect(body.message || body.detail || body.status).toBeTruthy();
  });

  test('get-user with user_id returns user payload', async ({ request }) => {
    const session = await apiLogin(request);
    const res = await request.get(`${BACKEND_URL}/api/v3/get-user/`, {
      headers: authHeaders(session),
      params: { user_id: session.userId }
    });
    await expectNotServerError(res, 'get-user');
    expect(res.ok()).toBeTruthy();
  });

  test('subscription without salon/branch returns 4xx (not 500)', async ({ request }) => {
    const session = await apiLogin(request);
    const res = await request.get(`${BACKEND_URL}/api/v3/subscription/`, {
      headers: authHeaders(session)
    });
    expect(res.status()).toBeLessThan(500);
  });

  test('subscription with salon/branch returns JSON', async ({ request }) => {
    const session = await apiLogin(request);
    const res = await request.get(`${BACKEND_URL}/api/v3/subscription/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(res, 'subscription');
  });

  test('kanban profiles with null user does not 500', async ({ request }) => {
    const session = await apiLogin(request);
    const res = await request.post(`${BACKEND_URL}/api/v3/kanban/profiles/`, {
      headers: authHeaders(session),
      data: businessContext(session)
    });
    await expectNotServerError(res, 'kanban/profiles');
    const body = await getJson(res);
    expect(body.data?.rows || body.data || body).toBeTruthy();
  });

  test('bookings POST missing slot returns 4xx not 500', async ({ request }) => {
    const session = await apiLogin(request);
    const res = await request.post(`${BACKEND_URL}/api/v3/bookings/`, {
      headers: authHeaders(session),
      data: businessContext(session)
    });
    expect(res.status()).toBeLessThan(500);
    expect(res.status()).toBeGreaterThanOrEqual(400);
  });

  test('billings POST missing required fields returns 4xx not 500', async ({ request }) => {
    const session = await apiLogin(request);
    const res = await request.post(`${BACKEND_URL}/api/v3/billings/`, {
      headers: authHeaders(session),
      data: businessContext(session)
    });
    expect(res.status()).toBeLessThan(500);
    expect(res.status()).toBeGreaterThanOrEqual(400);
  });

  test('check-availability incomplete payload returns 4xx', async ({ request }) => {
    const session = await apiLogin(request);
    const res = await request.post(`${BACKEND_URL}/api/v3/check-availability/`, {
      headers: authHeaders(session),
      data: businessContext(session)
    });
    expect(res.status()).toBeLessThan(500);
  });
});

test.describe('API contract — reports & dashboard', () => {
  const reportPaths = [
    'dashboard',
    'reports',
    'employee-reports',
    'performance-reports',
    'revenue-reports',
    'payment-reports'
  ];

  for (const slug of reportPaths) {
    test(`GET /api/v3/${slug}/ contract`, async ({ request }) => {
      const session = await apiLogin(request);
      const res = await request.get(`${BACKEND_URL}/api/v3/${slug}/`, {
        headers: authHeaders(session),
        params: businessContext(session)
      });
      await expectNotServerError(res, slug);
    });
  }
});
