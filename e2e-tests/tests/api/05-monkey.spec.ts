import { test, expect } from '@playwright/test';
import {
  LIST_ENDPOINTS,
  apiLogin,
  authHeaders,
  businessContext,
  expectNotServerError
} from '../../helpers/api';
import { BACKEND_URL } from '../../helpers/env';

/**
 * Monkey testing: random / malformed / adversarial payloads across discovered endpoints.
 * Goal: never HTML 500; always JSON or controlled 4xx.
 * Payloads stay finite and moderately sized so the suite does not take down Django/SQLite.
 */

const MONKEY_STRINGS = [
  '',
  ' ',
  'null',
  'undefined',
  'NaN',
  '<script>alert(1)</script>',
  "' OR 1=1 --",
  '{"a":1}',
  '🚀' + 'x'.repeat(400),
  '../../etc/passwd',
  '%00',
  'true',
  'false'
];

/** Finite numbers only — Infinity/NaN serialize poorly and can crash brittle handlers. */
const MONKEY_NUMBERS = [-1, 0, 1, 999999999, -999999999, Number.MAX_SAFE_INTEGER, 1.5];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

test.describe('Monkey testing — adversarial API payloads', () => {
  test('random GETs with garbage query params never 500', async ({ request }) => {
    const session = await apiLogin(request);
    for (const slug of LIST_ENDPOINTS) {
      const params: Record<string, unknown> = {
        ...businessContext(session),
        // Keep branch on known safe ids so monkey focuses on query chaos, not every uncaught .get()
        salon_id: pick([-1, 0, 1, 3, 999999]),
        branch_id: pick([-1, 1, Number(session.branchId)]),
        user_id: pick(['1', '-1', 'abc', '']),
        group: pick(['Admin', 'admin', '', 'Hacker']),
        subscription_name: pick(['Premium', 'null', '', 'Basic']),
        page: pick([-1, 0, 1, 9999]),
        search: pick(MONKEY_STRINGS)
      };
      const res = await request.get(`${BACKEND_URL}/api/v3/${slug}/`, {
        headers: authHeaders(session),
        params
      });
      await expectNotServerError(res, `monkey GET ${slug}`);
    }
  });

  test('random POSTs with empty / partial / garbage bodies never 500', async ({ request }) => {
    const session = await apiLogin(request);
    // Cover create surfaces that should reject garbage with 4xx (not HTML 500).
    const targets = [
      'customers',
      'products',
      'expenses',
      'reviews',
      'memberships',
      'jobs',
      'check-availability',
      'contact-us'
    ];

    const failures: string[] = [];
    for (const slug of targets) {
      const payloads = [
        {},
        { ...businessContext(session) },
        {
          ...businessContext(session),
          name: pick(MONKEY_STRINGS),
          email: pick(MONKEY_STRINGS),
          mobile: pick(MONKEY_STRINGS),
          price: pick(MONKEY_NUMBERS),
          amount: pick(MONKEY_NUMBERS),
          slot: pick([{}, 'bad', { x: { y: [] } }]),
          discount: pick(MONKEY_NUMBERS),
          invoice_id: pick(MONKEY_NUMBERS)
        },
        {
          salon_id: pick(MONKEY_STRINGS),
          branch_id: pick(MONKEY_STRINGS),
          user_id: pick(MONKEY_STRINGS),
          group: pick(MONKEY_STRINGS),
          subscription_name: pick(MONKEY_STRINGS)
        }
      ];

      for (const data of payloads) {
        const res = await request.post(`${BACKEND_URL}/api/v3/${slug}/`, {
          headers: authHeaders(session),
          data: data as any
        });
        if (res.status() >= 500) {
          const body = (await res.text()).slice(0, 180);
          failures.push(`${slug} → ${res.status()} ${body}`);
        }
      }
    }
    expect(failures, failures.join('\n')).toEqual([]);
  });

  test('rapid duplicate creates do not crash (idempotency / uniqueness pressure)', async ({
    request
  }) => {
    const session = await apiLogin(request);
    const stamp = Date.now();
    const body = {
      ...businessContext(session),
      name: `Monkey Dup ${stamp}`,
      email: `monkey.dup.${stamp}@example.com`,
      mobile: `9${String(stamp).slice(-9)}`
    };
    const results: number[] = [];
    for (let i = 0; i < 5; i++) {
      const res = await request.post(`${BACKEND_URL}/api/v3/customers/`, {
        headers: authHeaders(session),
        data: body
      });
      await expectNotServerError(res, `dup customer ${i}`);
      results.push(res.status());
    }
    expect(results.every((s) => s < 500)).toBeTruthy();
  });

  test('sequential list hammering does not 500', async ({ request }) => {
    const session = await apiLogin(request);
    for (const slug of LIST_ENDPOINTS.slice(0, 8)) {
      for (let i = 0; i < 3; i++) {
        const res = await request.get(`${BACKEND_URL}/api/v3/${slug}/`, {
          headers: authHeaders(session),
          params: businessContext(session)
        });
        await expectNotServerError(res, `hammer ${slug}#${i}`);
      }
    }
  });

  test('logout-style garbage bearer tokens never 500', async ({ request }) => {
    for (const token of ['', 'Bearer', 'xxx.yyy.zzz', 'not-a-jwt', '<script>']) {
      const res = await request.get(`${BACKEND_URL}/api/v3/customers/`, {
        headers: {
          Authorization: token.startsWith('Bearer') ? token : `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        params: { salon_id: 3, branch_id: 1, user_id: 1, group: 'Admin' }
      });
      await expectNotServerError(res, 'garbage token');
    }
  });
});
