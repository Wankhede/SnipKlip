import { test, expect } from '@playwright/test';
import { apiLogin, authHeaders, businessContext, expectNotServerError, getJson } from '../../helpers/api';
import { BACKEND_URL } from '../../helpers/env';

/**
 * CRUD smoke for primary business entities.
 * Creates are best-effort: when validation fails we assert no 500;
 * when create succeeds we attempt list/read and cleanup where delete exists.
 */
test.describe('CRUD smoke — business entities', () => {
  let session: Awaited<ReturnType<typeof apiLogin>>;

  test.beforeAll(async ({ request }) => {
    session = await apiLogin(request);
  });

  test('customers: list shape has count/rows', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/customers/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(response, 'customers list');
    const body = await getJson(response);
    expect(body?.data).toHaveProperty('rows');
    expect(body?.data).toHaveProperty('count');
  });

  test('employees: list shape has count/rows', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/employees/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(response, 'employees list');
    const body = await getJson(response);
    expect(body?.data).toHaveProperty('rows');
  });

  test('services: create minimal then list', async ({ request }) => {
    const create = await request.post(`${BACKEND_URL}/api/v3/services/`, {
      headers: authHeaders(session),
      data: {
        ...businessContext(session),
        name: `E2E Service ${Date.now()}`,
        price: 100,
        time_for_each_service: 30,
        category: 'General',
        status: 'Active'
      }
    });
    await expectNotServerError(create, 'service create');

    const list = await request.get(`${BACKEND_URL}/api/v3/services/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(list, 'service list');
    const body = await getJson(list);
    expect(Array.isArray(body?.data?.rows)).toBeTruthy();
  });

  test('products: create minimal then list', async ({ request }) => {
    const create = await request.post(`${BACKEND_URL}/api/v3/products/`, {
      headers: authHeaders(session),
      data: {
        ...businessContext(session),
        name: `E2E Product ${Date.now()}`,
        category: 'Retail',
        description: 'e2e',
        price: 50,
        availablity: true,
        quantity: 1,
        sku: `E2E-${Date.now()}`
      }
    });
    await expectNotServerError(create, 'product create');

    const list = await request.get(`${BACKEND_URL}/api/v3/products/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(list, 'product list');
  });

  test('expenses: create minimal then list', async ({ request }) => {
    const create = await request.post(`${BACKEND_URL}/api/v3/expenses/`, {
      headers: authHeaders(session),
      data: {
        ...businessContext(session),
        name: `E2E Expense ${Date.now()}`,
        amount: 25,
        category: 'Ops',
        description: 'e2e'
      }
    });
    await expectNotServerError(create, 'expense create');
  });

  test('memberships & coupons list', async ({ request }) => {
    for (const endpoint of ['memberships', 'coupons'] as const) {
      const response = await request.get(`${BACKEND_URL}/api/v3/${endpoint}/`, {
        headers: authHeaders(session),
        params: businessContext(session)
      });
      await expectNotServerError(response, endpoint);
      const body = await getJson(response);
      expect(body?.data).toHaveProperty('rows');
    }
  });

  test('jobs list and invalid delete-job id does not 500', async ({ request }) => {
    const list = await request.get(`${BACKEND_URL}/api/v3/jobs/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(list, 'jobs');

    const del = await request.post(`${BACKEND_URL}/api/v3/delete-job/999999/`, {
      headers: authHeaders(session),
      data: businessContext(session)
    });
    await expectNotServerError(del, 'delete-job missing');
  });

  test('salary GET by branch', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/salary/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(response, 'salary');
    // 429 (throttle) or JSON status payloads are both acceptable for smoke health
    expect(response.status()).toBeLessThan(500);
  });

  test('kanban columns/items do not 500', async ({ request }) => {
    for (const endpoint of ['kanban/columns', 'kanban/items', 'kanban/profiles'] as const) {
      const response = await request.get(`${BACKEND_URL}/api/v3/${endpoint}/`, {
        headers: authHeaders(session),
        params: businessContext(session)
      });
      await expectNotServerError(response, endpoint);
    }
  });

  test('calendar events do not 500', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/calendar/events/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(response, 'calendar events');
  });

  test('reports endpoints do not 500', async ({ request }) => {
    for (const endpoint of [
      'reports',
      'employee-reports',
      'performance-reports',
      'revenue-reports',
      'payment-reports'
    ] as const) {
      const response = await request.get(`${BACKEND_URL}/api/v3/${endpoint}/`, {
        headers: authHeaders(session),
        params: businessContext(session)
      });
      await expectNotServerError(response, endpoint);
    }
  });
});
