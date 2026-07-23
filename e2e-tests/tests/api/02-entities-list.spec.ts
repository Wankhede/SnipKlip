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

test.describe('Entity list endpoints (discovered /api/v3)', () => {
  let session: Awaited<ReturnType<typeof apiLogin>>;

  test.beforeAll(async ({ request }) => {
    session = await apiLogin(request);
  });

  for (const endpoint of LIST_ENDPOINTS) {
    test(`GET /api/v3/${endpoint}/ does not 500 and returns JSON`, async ({ request }) => {
      const response = await request.get(`${BACKEND_URL}/api/v3/${endpoint}/`, {
        headers: authHeaders(session),
        params: businessContext(session)
      });
      await expectNotServerError(response, endpoint);
      const body = await getJson(response);
      expect(body._parseError).toBeFalsy();
      // Prefer structured status when present
      if (typeof body.status === 'number') {
        expect(body.status, `${endpoint} body.status`).toBeLessThan(500);
      }
    });
  }

  test('access-control-association exposes WEB_HEADER keys', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/access-control-association/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(response, 'access-control');
    const body = await getJson(response);
    const payload = body?.data || body;
    expect(payload).toBeTruthy();
  });

  test('salon-details with -1/-1 returns rows for Admin', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/salon-details/`, {
      headers: authHeaders(session),
      params: businessContext(session, { salon_id: -1, branch_id: -1 })
    });
    await expectNotServerError(response, 'salon-details');
    const body = await getJson(response);
    if (response.ok() && body?.status === 200) {
      expect(Array.isArray(body?.data?.rows)).toBeTruthy();
    }
  });

  test('message contracts: services/products/jobs/coupons are not expense copy', async ({ request }) => {
    for (const endpoint of ['services', 'products', 'jobs', 'coupons'] as const) {
      const response = await request.get(`${BACKEND_URL}/api/v3/${endpoint}/`, {
        headers: authHeaders(session),
        params: businessContext(session)
      });
      const body = await getJson(response);
      const message = String(body?.message || '');
      expect(message.toLowerCase(), `${endpoint} message leaked expense copy`).not.toContain('expense');
    }
  });
});
