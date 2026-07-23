import { test, expect } from '@playwright/test';
import {
  apiLogin,
  authHeaders,
  businessContext,
  expectNotServerError,
  getJson
} from '../../helpers/api';
import { BACKEND_URL } from '../../helpers/env';

/**
 * Boundary Value Analysis (BVA) for critical SnipKlip API inputs.
 * Covers min / just-below / just-above / max / empty / null / type-mismatch.
 */

test.describe('BVA — auth boundaries', () => {
  test('login username/password edge lengths', async ({ request }) => {
    const cases = [
      { username: '', password: '' },
      { username: 'a', password: 'b' },
      { username: 'admin', password: '' },
      { username: '', password: 'Admin@123' },
      { username: 'a'.repeat(255), password: 'x'.repeat(255) },
      { username: 'a'.repeat(256), password: 'x'.repeat(256) },
      { username: 'admin', password: 'wrong' },
      { username: 'ADMIN', password: 'Admin@123' },
      { username: ' admin ', password: ' Admin@123 ' },
      { username: 'admin\x00', password: 'Admin@123' }
    ];
    for (const data of cases) {
      const res = await request.post(`${BACKEND_URL}/api/v3/login/`, { data });
      await expectNotServerError(res, `login BVA ${JSON.stringify(data).slice(0, 80)}`);
      expect(res.status()).toBeLessThan(500);
    }
  });
});

test.describe('BVA — tenant context ids', () => {
  const idEdges = [-1, 0, 1, 2, 999999, 'abc', ''];

  for (const salon_id of idEdges) {
    test(`dashboard salon=${salon_id} with valid/invalid branch edges`, async ({ request }) => {
      const session = await apiLogin(request);
      for (const branch_id of [-1, 0, 1, 999999]) {
        const res = await request.get(`${BACKEND_URL}/api/v3/dashboard/`, {
          headers: authHeaders(session),
          params: {
            ...businessContext(session),
            salon_id: salon_id as any,
            branch_id: branch_id as any,
            user_id: session.userId
          }
        });
        await expectNotServerError(res, `dashboard salon=${salon_id} branch=${branch_id}`);
        expect(res.status()).toBeLessThan(500);
      }
    });
  }
});

test.describe('BVA — numeric money / rating fields', () => {
  test('expense amount boundaries', async ({ request }) => {
    const session = await apiLogin(request);
    const amounts = [-0.01, -1, 0, 0.01, 1, 99999999.99, '', 'NaN', 'abc'];
    for (const amount of amounts) {
      const res = await request.post(`${BACKEND_URL}/api/v3/expenses/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          amount,
          description: 'BVA expense',
          category: 'Misc',
          date: '2026-07-23'
        }
      });
      await expectNotServerError(res, `expense amount=${amount}`);
    }
  });

  test('product price / stock boundaries', async ({ request }) => {
    const session = await apiLogin(request);
    const prices = [-1, 0, 0.01, 1, 999999.99, 1000000, '', 'free'];
    for (const price of prices) {
      const res = await request.post(`${BACKEND_URL}/api/v3/products/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          name: `BVA Product ${String(price).slice(0, 20)}`,
          price,
          quantity: price === 0 ? 0 : 1,
          status: 'Active'
        }
      });
      await expectNotServerError(res, `product price=${price}`);
    }
  });

  test('review rating boundaries', async ({ request }) => {
    const session = await apiLogin(request);
    for (const rating of [-1, 0, 1, 4, 5, 6, 100, 'good', '']) {
      const res = await request.post(`${BACKEND_URL}/api/v3/reviews/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          rating,
          invoice_id: 1,
          comment: 'BVA'
        }
      });
      await expectNotServerError(res, `rating=${rating}`);
    }
  });

  test('coupon discount percentage edges', async ({ request }) => {
    const session = await apiLogin(request);
    for (const discount of [-1, 0, 1, 50, 99, 100, 101, 1000, '']) {
      const res = await request.post(`${BACKEND_URL}/api/v3/coupons/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          code: `BVA${Date.now()}${discount}`,
          discount,
          discount_type: 'PERCENT'
        }
      });
      await expectNotServerError(res, `coupon discount=${discount}`);
    }
  });
});

test.describe('BVA — string length & format', () => {
  test('customer name/email/mobile edges', async ({ request }) => {
    const session = await apiLogin(request);
    const stamp = Date.now();
    const cases = [
      { name: '', email: `a${stamp}@t.com`, mobile: '9000000001' },
      { name: 'A', email: `b${stamp}@t.com`, mobile: '9000000002' },
      { name: 'x'.repeat(255), email: `c${stamp}@t.com`, mobile: '9000000003' },
      { name: 'x'.repeat(1000), email: `d${stamp}@t.com`, mobile: '9000000004' },
      { name: 'OK', email: 'not-an-email', mobile: '9000000005' },
      { name: 'OK', email: `e${stamp}@t.com`, mobile: '' },
      { name: 'OK', email: `f${stamp}@t.com`, mobile: '1' },
      { name: 'OK', email: `g${stamp}@t.com`, mobile: '9'.repeat(15) },
      { name: 'OK', email: `h${stamp}@t.com`, mobile: '9'.repeat(20) },
      { name: '  spaced  ', email: ` i${stamp}@t.com `, mobile: ' 9000000006 ' }
    ];
    for (const data of cases) {
      const res = await request.post(`${BACKEND_URL}/api/v3/customers/`, {
        headers: authHeaders(session),
        data: { ...businessContext(session), ...data }
      });
      await expectNotServerError(res, `customer BVA ${JSON.stringify(data).slice(0, 60)}`);
    }
  });

  test('service name length boundaries', async ({ request }) => {
    const session = await apiLogin(request);
    for (const name of ['', 'A', 'x'.repeat(255), 'x'.repeat(512)]) {
      const res = await request.post(`${BACKEND_URL}/api/v3/services/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          name,
          price: 100,
          duration: 30,
          status: 'Active'
        }
      });
      await expectNotServerError(res, `service name len=${String(name).length}`);
    }
  });
});

test.describe('BVA — date / time windows', () => {
  test('check-availability date edges', async ({ request }) => {
    const session = await apiLogin(request);
    const dates = [
      '1970-01-01',
      '2020-01-01',
      '2026-07-23',
      '2099-12-31',
      'not-a-date',
      '',
      '2026-13-40',
      '2026-02-30'
    ];
    for (const booking_date of dates) {
      const res = await request.post(`${BACKEND_URL}/api/v3/check-availability/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          booking_platform: 'ONLINE',
          booking_date,
          start_time: '10:00',
          service: []
        }
      });
      await expectNotServerError(res, `avail date=${booking_date}`);
    }
  });

  test('check-availability time edges', async ({ request }) => {
    const session = await apiLogin(request);
    for (const start_time of ['00:00', '09:59', '10:00', '23:59', '24:00', '99:99', '', 'noon']) {
      const res = await request.post(`${BACKEND_URL}/api/v3/check-availability/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          booking_platform: 'ONLINE',
          booking_date: '2026-07-23',
          start_time,
          service: []
        }
      });
      await expectNotServerError(res, `avail time=${start_time}`);
    }
  });

  test('bookings POST with empty vs nested slot objects', async ({ request }) => {
    const session = await apiLogin(request);
    const slots = [{}, { Haircut: {} }, { Haircut: { '1': [] } }, []];
    for (const slot of slots) {
      const res = await request.post(`${BACKEND_URL}/api/v3/bookings/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          slot,
          booking_date: '2099-01-01T10:00:00',
          customer_id: 1,
          booking_platform: 'ONLINE'
        }
      });
      await expectNotServerError(res, 'booking slot BVA');
      // Controlled outcome: either validation 4xx or an accepted/handled 2xx — never 5xx.
      expect(res.status()).toBeLessThan(500);
    }
  });
});

test.describe('BVA — pagination / filter params', () => {
  test('list endpoints with page/size extremes', async ({ request }) => {
    const session = await apiLogin(request);
    const edges = [
      { page: -1, page_size: 10 },
      { page: 0, page_size: 0 },
      { page: 1, page_size: 1 },
      { page: 1, page_size: 100 },
      { page: 1, page_size: 1000 },
      { page: 999999, page_size: 50 },
      { offset: -1, limit: -1 },
      { search: 'x'.repeat(500) },
      { search: '' }
    ];
    for (const extra of edges) {
      const res = await request.get(`${BACKEND_URL}/api/v3/customers/`, {
        headers: authHeaders(session),
        params: { ...businessContext(session), ...extra }
      });
      await expectNotServerError(res, `customers page BVA ${JSON.stringify(extra)}`);
      const body = await getJson(res);
      expect(body._parseError).toBeFalsy();
    }
  });
});
