import { APIRequestContext, expect } from '@playwright/test';
import {
  ADMIN_PASSWORD,
  ADMIN_USER,
  BACKEND_URL,
  CUSTOMER_PASSWORD,
  CUSTOMER_USER,
  DEFAULT_BRANCH_ID,
  DEFAULT_SALON_ID,
  EMPLOYEE_PASSWORD,
  EMPLOYEE_USER
} from './env';

export type LoginSession = {
  accessToken: string;
  userId: number | string;
  salonId: number | string;
  branchId: number | string;
  group: string;
  subscriptionName: string;
  raw: any;
};

export type RoleName = 'admin' | 'employee' | 'customer';

const ROLE_CREDS: Record<RoleName, { username: string; password: string }> = {
  admin: { username: ADMIN_USER, password: ADMIN_PASSWORD },
  employee: { username: EMPLOYEE_USER, password: EMPLOYEE_PASSWORD },
  customer: { username: CUSTOMER_USER, password: CUSTOMER_PASSWORD }
};

/** Reuse sessions across tests to avoid BurstRateThrottle 429s on /login/. */
const cachedSessions: Partial<Record<RoleName, { session: LoginSession; at: number }>> = {};
const CACHE_MS = 10 * 60 * 1000;

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function apiLoginAs(
  request: APIRequestContext,
  role: RoleName = 'admin'
): Promise<LoginSession> {
  const cached = cachedSessions[role];
  if (cached && Date.now() - cached.at < CACHE_MS) {
    return cached.session;
  }

  const creds = ROLE_CREDS[role];
  let lastBody: any = {};
  let response: Awaited<ReturnType<APIRequestContext['post']>> | null = null;

  for (let attempt = 0; attempt < 5; attempt++) {
    response = await request.post(`${BACKEND_URL}/api/v3/login/`, {
      data: { username: creds.username, password: creds.password }
    });
    lastBody = await response.json().catch(() => ({}));
    if (response.status() === 429) {
      const waitSec = Number(String(lastBody?.detail || '').match(/(\d+)/)?.[1] || 5);
      await sleep((waitSec + 1) * 1000);
      continue;
    }
    break;
  }

  expect(
    response!.ok(),
    `${role} login failed: ${response!.status()} ${JSON.stringify(lastBody)}`
  ).toBeTruthy();

  const data = lastBody?.data || lastBody;
  const accessToken = data?.access_token || lastBody?.access_token;
  expect(accessToken, `${role} access_token missing from login response`).toBeTruthy();

  let salonId = data?.salon_id ?? DEFAULT_SALON_ID;
  let branchId = data?.branch_id ?? DEFAULT_BRANCH_ID;
  let group = data?.group || role;
  let subscriptionName = data?.subscription_name || 'Premium';
  let userId = data?.user_id || data?.id || lastBody?.id;

  // Admin accounts often return -1 for salon/branch — resolve to a real tenant for CRUD lists
  if (Number(salonId) < 0) salonId = DEFAULT_SALON_ID;
  if (Number(branchId) < 0) branchId = DEFAULT_BRANCH_ID;

  const session: LoginSession = {
    accessToken,
    userId,
    salonId,
    branchId,
    group,
    subscriptionName: subscriptionName == null ? 'Premium' : String(subscriptionName),
    raw: lastBody
  };
  cachedSessions[role] = { session, at: Date.now() };
  return session;
}

/** Default admin login (back-compat with existing specs). */
export async function apiLogin(request: APIRequestContext): Promise<LoginSession> {
  return apiLoginAs(request, 'admin');
}

/** Force a fresh login (e.g. after DB wipe mid-suite). */
export function clearLoginCache() {
  for (const key of Object.keys(cachedSessions) as RoleName[]) {
    delete cachedSessions[key];
  }
}

export function authHeaders(session: LoginSession) {
  return {
    Authorization: `Bearer ${session.accessToken}`,
    'Content-Type': 'application/json'
  };
}

export function businessContext(session: LoginSession, extra: Record<string, unknown> = {}) {
  return {
    salon_id: Number(session.salonId),
    user_id: Number(session.userId),
    branch_id: Number(session.branchId),
    group: session.group || 'Admin',
    subscription_name: session.subscriptionName || 'Premium',
    ...extra
  };
}

export async function expectNotServerError(
  response: { status: () => number; text: () => Promise<string> },
  label: string
) {
  const status = response.status();
  if (status >= 500) {
    const body = await response.text();
    expect(status, `${label} returned ${status}: ${body.slice(0, 500)}`).toBeLessThan(500);
  }
}

export async function getJson(response: { json: () => Promise<any>; status: () => number }) {
  try {
    return await response.json();
  } catch {
    return { _parseError: true, status: response.status() };
  }
}

/** Core GET list endpoints discovered from api/urls.py */
export const LIST_ENDPOINTS = [
  'customers',
  'employees',
  'services',
  'products',
  'bookings',
  'billings',
  'expenses',
  'reviews',
  'memberships',
  'coupons',
  'jobs',
  'salary',
  'dashboard',
  'todos',
  'get-invoice',
  'reports',
  'access-control-association'
] as const;
