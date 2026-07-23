import { APIRequestContext, expect } from '@playwright/test';
import {
  ADMIN_PASSWORD,
  ADMIN_USER,
  BACKEND_URL,
  DEFAULT_BRANCH_ID,
  DEFAULT_SALON_ID
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

export async function apiLogin(request: APIRequestContext): Promise<LoginSession> {
  const response = await request.post(`${BACKEND_URL}/api/v3/login/`, {
    data: { username: ADMIN_USER, password: ADMIN_PASSWORD }
  });
  const body = await response.json().catch(() => ({}));
  expect(response.ok(), `login failed: ${response.status()} ${JSON.stringify(body)}`).toBeTruthy();

  const data = body?.data || body;
  const accessToken = data?.access_token || body?.access_token;
  expect(accessToken, 'access_token missing from login response').toBeTruthy();

  let salonId = data?.salon_id ?? DEFAULT_SALON_ID;
  let branchId = data?.branch_id ?? DEFAULT_BRANCH_ID;
  let group = data?.group || 'Admin';
  let subscriptionName = data?.subscription_name || 'Premium';
  let userId = data?.user_id || data?.id || body?.id;

  // Admin accounts often return -1 for salon/branch — resolve to a real tenant for CRUD lists
  if (Number(salonId) < 0) salonId = DEFAULT_SALON_ID;
  if (Number(branchId) < 0) branchId = DEFAULT_BRANCH_ID;

  return {
    accessToken,
    userId,
    salonId,
    branchId,
    group,
    subscriptionName: subscriptionName == null ? 'Premium' : String(subscriptionName),
    raw: body
  };
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
