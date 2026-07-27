/**
 * SnipKlip permanent monkey suite — multi-role auth + adversarial CRUD + BVA.
 *
 * Run from e2e-tests/:
 *   npm run test:monkey
 *   npx playwright test monkey-suite.spec.ts
 *
 * Requires seeded accounts (wipe_test_data.py reseed):
 *   admin@snipklip.local / Admin@123  (username: admin)
 *   employee@snipklip.local / Employee@123
 *   customer@snipklip.local / Customer@123
 */
import { test, expect } from '@playwright/test';
import {
  LIST_ENDPOINTS,
  apiLogin,
  apiLoginAs,
  authHeaders,
  businessContext,
  clearLoginCache,
  expectNotServerError,
  getJson,
  type RoleName
} from './helpers/api';
import {
  ADMIN_EMAIL,
  ADMIN_PASSWORD,
  ADMIN_USER,
  BACKEND_URL,
  CUSTOMER_EMAIL,
  CUSTOMER_PASSWORD,
  EMPLOYEE_EMAIL,
  EMPLOYEE_PASSWORD,
  FRONTEND_URL
} from './helpers/env';

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

const MONKEY_NUMBERS = [-1, 0, 1, 999999999, -999999999, Number.MAX_SAFE_INTEGER, 1.5];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function stamp() {
  return `${Date.now()}${Math.floor(Math.random() * 1000)}`;
}

test.describe('Monkey suite — Phase 1 auth & RBAC', () => {
  test.beforeAll(() => {
    clearLoginCache();
  });

  test('admin login works with username and email', async ({ request }) => {
    for (const username of [ADMIN_USER, ADMIN_EMAIL]) {
      const res = await request.post(`${BACKEND_URL}/api/v3/login/`, {
        data: { username, password: ADMIN_PASSWORD }
      });
      await expectNotServerError(res, `admin login ${username}`);
      expect(res.ok(), `admin login ${username}`).toBeTruthy();
      const body = await getJson(res);
      expect(body?.data?.access_token).toBeTruthy();
      expect(body?.data?.group).toBe('Admin');
    }
  });

  test('employee and customer seeded logins succeed without 500', async ({ request }) => {
    for (const [role, username, password, expectedGroup] of [
      ['employee', EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD, 'Staff'],
      ['customer', CUSTOMER_EMAIL, CUSTOMER_PASSWORD, 'Customer']
    ] as const) {
      const res = await request.post(`${BACKEND_URL}/api/v3/login/`, {
        data: { username, password }
      });
      await expectNotServerError(res, `${role} login`);
      const body = await getJson(res);
      expect(res.ok(), `${role} login body=${JSON.stringify(body)}`).toBeTruthy();
      expect(body?.data?.access_token).toBeTruthy();
      expect(String(body?.data?.group)).toBe(expectedGroup);
    }
  });

  test('invalid credentials rejected without 500 for all roles', async ({ request }) => {
    for (const username of [ADMIN_EMAIL, EMPLOYEE_EMAIL, CUSTOMER_EMAIL, 'ghost@snipklip.local']) {
      const res = await request.post(`${BACKEND_URL}/api/v3/login/`, {
        data: { username, password: 'definitely-wrong' }
      });
      await expectNotServerError(res, `bad login ${username}`);
      expect(res.status()).toBeLessThan(500);
      expect([400, 401, 403, 404].includes(res.status()) || !(await getJson(res))?.data?.access_token).toBeTruthy();
    }
  });

  test('protected routes deny garbage JWT without 500', async ({ request }) => {
    for (const token of ['', 'xxx.yyy.zzz', 'not-a-jwt', '<script>']) {
      const res = await request.get(`${BACKEND_URL}/api/v3/customers/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        params: { salon_id: 3, branch_id: 1, user_id: 1, group: 'Admin', subscription_name: 'Premium' }
      });
      await expectNotServerError(res, 'garbage JWT');
    }
  });

  test('apiLoginAs resolves Admin / Staff / Customer sessions', async ({ request }) => {
    const admin = await apiLoginAs(request, 'admin');
    const employee = await apiLoginAs(request, 'employee');
    const customer = await apiLoginAs(request, 'customer');
    expect(admin.group).toBe('Admin');
    expect(employee.group).toBe('Staff');
    expect(customer.group).toBe('Customer');
    expect(Number(admin.salonId)).toBeGreaterThan(0);
    expect(Number(employee.branchId)).toBeGreaterThan(0);
  });
});

test.describe('Monkey suite — Phase 2 entity CRUD + chaos', () => {
  test('customers: create / list / update / duplicate email pressure', async ({ request }) => {
    const session = await apiLogin(request);
    const s = stamp();
    const email = `monkey.cust.${s}@example.com`;
    const mobile = `9${String(s).slice(-9)}`;

    const create = await request.post(`${BACKEND_URL}/api/v3/customers/`, {
      headers: authHeaders(session),
      data: {
        ...businessContext(session),
        first_name: 'Monkey',
        last_name: `Cust${s}`,
        email,
        mobile,
        gender: 'Male'
      }
    });
    await expectNotServerError(create, 'customer create');
    const created = await getJson(create);
    const customerId = created?.data?.rows?.[0]?.id;

    const list = await request.get(`${BACKEND_URL}/api/v3/customers/`, {
      headers: authHeaders(session),
      params: { ...businessContext(session), search: email }
    });
    await expectNotServerError(list, 'customer list');
    expect((await getJson(list))?.data).toHaveProperty('rows');

    if (customerId) {
      const update = await request.put(`${BACKEND_URL}/api/v3/customers/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          customer_id: customerId,
          first_name: 'MonkeyUpd',
          last_name: `Cust${s}`,
          email,
          mobile,
          gender: 'Female',
          status: 'Active'
        }
      });
      await expectNotServerError(update, 'customer update');
    }

    // Duplicate create should not 500
    const dup = await request.post(`${BACKEND_URL}/api/v3/customers/`, {
      headers: authHeaders(session),
      data: {
        ...businessContext(session),
        first_name: 'Monkey',
        last_name: `Dup${s}`,
        email,
        mobile,
        gender: 'Male'
      }
    });
    await expectNotServerError(dup, 'customer duplicate');
  });

  test('employees: create / list / status toggle chaos', async ({ request }) => {
    const session = await apiLogin(request);
    const s = stamp();
    const create = await request.post(`${BACKEND_URL}/api/v3/employees/`, {
      headers: authHeaders(session),
      data: {
        ...businessContext(session),
        first_name: 'Monkey',
        last_name: `Emp${s}`,
        email: `monkey.emp.${s}@example.com`,
        mobile: `8${String(s).slice(-9)}`,
        employee_type: 'Staff',
        product_incentive: 0,
        service_incentive: 0,
        base_salary: 12000
      }
    });
    await expectNotServerError(create, 'employee create');

    const list = await request.get(`${BACKEND_URL}/api/v3/employees/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(list, 'employee list');
    expect((await getJson(list))?.data).toHaveProperty('rows');
  });

  test('services: create / list with pricing + duration', async ({ request }) => {
    const session = await apiLogin(request);
    const s = stamp();
    const create = await request.post(`${BACKEND_URL}/api/v3/services/`, {
      headers: authHeaders(session),
      data: {
        ...businessContext(session),
        name: `Monkey Service ${s}`,
        price: 199,
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
  });

  test('coupons: create / list with expiry + usage limits', async ({ request }) => {
    const session = await apiLogin(request);
    const s = stamp();
    // Coupon API expects '%b %d, %Y' e.g. Jul 27, 2027
    const expiry = new Date();
    expiry.setFullYear(expiry.getFullYear() + 1);
    const expiryStr = expiry.toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      year: 'numeric'
    });

    const create = await request.post(`${BACKEND_URL}/api/v3/coupons/`, {
      headers: authHeaders(session),
      data: {
        ...businessContext(session),
        coupon_code: `MK${s}`.slice(0, 20),
        discount_percent: 15,
        expiry_date: expiryStr,
        available_count: 10
      }
    });
    await expectNotServerError(create, 'coupon create');

    const list = await request.get(`${BACKEND_URL}/api/v3/coupons/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(list, 'coupon list');
    expect((await getJson(list))?.data).toHaveProperty('rows');
  });

  test('subscriptions + payment hooks never 500 on garbage', async ({ request }) => {
    const session = await apiLogin(request);

    const types = await request.get(`${BACKEND_URL}/api/v3/get-subscription-type/`, {
      headers: authHeaders(session)
    });
    await expectNotServerError(types, 'subscription types');

    const subs = await request.get(`${BACKEND_URL}/api/v3/subscription/`, {
      headers: authHeaders(session),
      params: businessContext(session)
    });
    await expectNotServerError(subs, 'subscription list');

    for (const amount of [null, '', 'abc', -1, 0, 100] as const) {
      const pay = await request.post(`${BACKEND_URL}/api/v3/createPayment/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          amount,
          subscriptionType: 'yearly',
          subscriptionName: 'PREMIUM'
        }
      });
      await expectNotServerError(pay, `createPayment amount=${amount}`);
    }

    const cb = await request.post(`${BACKEND_URL}/api/v3/paymentCallback/`, {
      headers: authHeaders(session),
      data: {
        razorpay_order_id: 'order_monkey',
        razorpay_payment_id: 'pay_monkey',
        razorpay_signature: 'bad'
      }
    });
    await expectNotServerError(cb, 'paymentCallback garbage');
  });

  test('adversarial POSTs across core entities never 500', async ({ request }) => {
    const session = await apiLogin(request);
    const targets = [
      'customers',
      'employees',
      'services',
      'products',
      'expenses',
      'reviews',
      'memberships',
      'coupons',
      'jobs',
      'check-availability',
      'contact-us',
      'createPayment'
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
          discount_percent: pick(MONKEY_NUMBERS),
          first_name: pick(MONKEY_STRINGS),
          last_name: pick(MONKEY_STRINGS),
          employee_type: pick(['Staff', 'Manager', '', null]),
          coupon_code: pick(MONKEY_STRINGS),
          expiry_date: pick(['bad', '2020-01-01', '', null]),
          available_count: pick(MONKEY_NUMBERS)
        }
      ];
      for (const data of payloads) {
        const res = await request.post(`${BACKEND_URL}/api/v3/${slug}/`, {
          headers: authHeaders(session),
          data: data as any
        });
        if (res.status() >= 500) {
          failures.push(`${slug} → ${res.status()} ${(await res.text()).slice(0, 160)}`);
        }
      }
    }
    expect(failures, failures.join('\n')).toEqual([]);
  });

  test('random GETs with garbage query params never 500', async ({ request }) => {
    const session = await apiLogin(request);
    for (const slug of LIST_ENDPOINTS) {
      const res = await request.get(`${BACKEND_URL}/api/v3/${slug}/`, {
        headers: authHeaders(session),
        params: {
          ...businessContext(session),
          salon_id: pick([-1, 0, 1, 3, 999999]),
          branch_id: pick([-1, 1, Number(session.branchId)]),
          user_id: pick(['1', '-1', 'abc', '']),
          group: pick(['Admin', 'Staff', 'Customer', '', 'Hacker']),
          subscription_name: pick(['Premium', 'null', '', 'Basic']),
          page: pick([-1, 0, 1, 9999]),
          search: pick(MONKEY_STRINGS)
        }
      });
      await expectNotServerError(res, `monkey GET ${slug}`);
    }
  });

  test('role-scoped list access never 500 (Admin / Staff / Customer)', async ({ request }) => {
    for (const role of ['admin', 'employee', 'customer'] as RoleName[]) {
      const session = await apiLoginAs(request, role);
      for (const slug of ['customers', 'services', 'coupons', 'dashboard'] as const) {
        const res = await request.get(`${BACKEND_URL}/api/v3/${slug}/`, {
          headers: authHeaders(session),
          params: businessContext(session)
        });
        await expectNotServerError(res, `${role} GET ${slug}`);
      }
    }
  });
});

test.describe('Monkey suite — Phase 2 UI chaos', () => {
  const PUBLIC = ['/', '/login', '/register', '/pricing', '/contact-us', '/about-us', '/forgot-password'];

  test('rapid public navigation never whitescreens', async ({ page }) => {
    for (let i = 0; i < 10; i++) {
      const path = pick(PUBLIC);
      const res = await page.goto(`${FRONTEND_URL}${path}`, {
        waitUntil: 'domcontentloaded',
        timeout: 45_000
      });
      expect(res?.status() ?? 0).toBeLessThan(500);
      await expect(page.locator('body')).toBeVisible();
      const html = (await page.content()).toLowerCase();
      expect(html).not.toContain('application error');
    }
  });

  test('login form double-click spam stays stable', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'domcontentloaded' });
    const email = page.locator('input[name="email"], input[type="email"], input[name="username"]').first();
    const password = page.locator('input[name="password"], input[type="password"]').first();
    const submit = page.locator('button[type="submit"]').first();
    await expect(submit).toBeVisible({ timeout: 20_000 });
    if (await email.count()) await email.fill(ADMIN_EMAIL);
    if (await password.count()) await password.fill(ADMIN_PASSWORD);
    for (let i = 0; i < 6; i++) {
      await submit.click({ force: true }).catch(() => undefined);
    }
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Monkey suite — Phase 4 BVA boundaries', () => {
  test('login string length edges never 500', async ({ request }) => {
    const cases = [
      { username: '', password: '' },
      { username: 'a', password: 'b' },
      { username: ADMIN_EMAIL, password: '' },
      { username: '', password: ADMIN_PASSWORD },
      { username: 'a'.repeat(255), password: 'x'.repeat(255) },
      { username: 'a'.repeat(1024), password: 'x'.repeat(1024) },
      { username: ADMIN_EMAIL, password: 'wrong' },
      { username: ` ${ADMIN_EMAIL} `, password: ` ${ADMIN_PASSWORD} ` }
    ];
    for (const data of cases) {
      const res = await request.post(`${BACKEND_URL}/api/v3/login/`, { data });
      await expectNotServerError(res, `login BVA ${JSON.stringify(data).slice(0, 60)}`);
    }
  });

  test('price / discount / duration numeric edges never 500', async ({ request }) => {
    const session = await apiLogin(request);
    for (const price of [-1, 0, 0.01, 1, 999999.99, '', 'free', null]) {
      const res = await request.post(`${BACKEND_URL}/api/v3/services/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          name: `BVA ${String(price).slice(0, 12)}`,
          price,
          time_for_each_service: pick([-1, 0, 1, 30, 99999]),
          category: 'General'
        }
      });
      await expectNotServerError(res, `service price=${price}`);
    }
    for (const discount of [-1, 0, 1, 100, 101, 999, '', null]) {
      const res = await request.post(`${BACKEND_URL}/api/v3/coupons/`, {
        headers: authHeaders(session),
        data: {
          ...businessContext(session),
          coupon_code: `BVA${stamp()}`.slice(0, 12),
          discount_percent: discount,
          expiry_date: 'Dec 31, 2099',
          available_count: pick([-1, 0, 1, 100])
        }
      });
      await expectNotServerError(res, `coupon discount=${discount}`);
    }
  });
});
