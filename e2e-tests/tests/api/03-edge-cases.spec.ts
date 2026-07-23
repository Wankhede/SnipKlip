import { test, expect } from '@playwright/test';
import { apiLogin, authHeaders, businessContext, expectNotServerError, getJson } from '../../helpers/api';
import { BACKEND_URL } from '../../helpers/env';

test.describe('Edge cases & boundary conditions', () => {
  let session: Awaited<ReturnType<typeof apiLogin>>;

  test.beforeAll(async ({ request }) => {
    session = await apiLogin(request);
  });

  test('missing required salon/branch for reviews returns 4xx body, not HTML 500', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/reviews/`, {
      headers: authHeaders(session),
      params: { user_id: session.userId, group: 'Admin', subscription_name: 'Premium' }
    });
    await expectNotServerError(response, 'reviews missing params');
    const text = await response.text();
    expect(text.toLowerCase()).not.toContain('multivaluedictkeyerror');
    expect(text.toLowerCase()).not.toContain('<!doctype html>');
  });

  test('reviews POST without invoice_id does not 500', async ({ request }) => {
    const response = await request.post(`${BACKEND_URL}/api/v3/reviews/`, {
      headers: authHeaders(session),
      data: businessContext(session)
    });
    await expectNotServerError(response, 'reviews post missing invoice');
    const body = await getJson(response);
    expect(body?.status === 500).toBeFalsy();
  });

  test('salary without branch_id returns validation, not 500', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/salary/`, {
      headers: authHeaders(session),
      params: businessContext(session, { branch_id: undefined as unknown as number })
    });
    // Playwright omits undefined params — call explicitly empty
    const response2 = await request.get(`${BACKEND_URL}/api/v3/salary/`, {
      headers: authHeaders(session),
      params: {
        salon_id: session.salonId,
        user_id: session.userId,
        group: 'Admin',
        subscription_name: 'Premium'
      }
    });
    await expectNotServerError(response2, 'salary missing branch');
    const body = await getJson(response2);
    expect([400, 200].includes(body?.status) || body?.message).toBeTruthy();
  });

  test('nonexistent foreign keys do not crash bookings', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/bookings/`, {
      headers: authHeaders(session),
      params: businessContext(session, { salon_id: 999999, branch_id: 999999 })
    });
    await expectNotServerError(response, 'bookings bad fk');
  });

  test('check-availability rejects incomplete payload without 500', async ({ request }) => {
    const response = await request.post(`${BACKEND_URL}/api/v3/check-availability/`, {
      headers: authHeaders(session),
      data: businessContext(session)
    });
    await expectNotServerError(response, 'check-availability incomplete');
  });

  test('todos list succeeds after .value fix', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/todos/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(response, 'todos');
    const body = await getJson(response);
    expect(body?.status).toBe(200);
    expect(Array.isArray(body?.data?.rows)).toBeTruthy();
  });

  test('contact-us GET does not 500', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/contact-us/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(response, 'contact-us');
  });

  test('get-a-invoice without id does not 500', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v3/get-a-invoice/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(response, 'get-a-invoice');
  });

  test('duplicate/null unique-ish customer create is handled', async ({ request }) => {
    const payload = {
      ...businessContext(session),
      first_name: 'E2E',
      last_name: 'Dup',
      email: 'jondoe@gmail.com',
      mobile: '9999999999',
      gender: 'Male',
      status: 'Active'
    };
    const response = await request.post(`${BACKEND_URL}/api/v3/customers/`, {
      headers: authHeaders(session),
      data: payload
    });
    await expectNotServerError(response, 'duplicate customer');
  });
});
