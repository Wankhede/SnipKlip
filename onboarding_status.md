# SnipKlip Onboarding Repair Status

Updated: 2026-07-19

## Verification policy

- Add or identify a failing regression test before changing workflow behavior.
- After each module: run focused tests, type-check/build, restart locally, and verify HTTP behavior.
- If a change fails, restore that file to its pre-change contents, record the exception below, and retry once with a smaller implementation.
- Do not mark work verified without passing automated checks and local request-count validation.

## Phase 1 — Bottleneck remediation and anti-loop fixes

- [Fixed/Verified] Trace the Shop Owner post-login request and redirect sequence.
- [Fixed/Verified] Add regression coverage for duplicate profile/branch requests and redirect loops.
- [Fixed/Verified] Remove duplicate branch/profile queries and unstable React effect dependencies.
- [Fixed/Verified] Add an authenticated “Booking Next” shortcut to the booking workflow.
- [Fixed/Verified] Verify no recursive redirects, duplicate writes, or repeated branch requests.

### Findings

1. Backend `/api/v3/user-details/` called `get_user_details()` twice and then re-queried salon/branch/subscription again (17 SQL statements for one owner context response).
2. Frontend `AccessControlProvider` depended on the whole `userData` object and called `router.push('/apps/salon-onboarding')` even when already on that route.
3. Frontend `UserProvider` re-fetched `/api/v3/user-details/` whenever the NextAuth session object identity changed.
4. `AuthGuard` issued an extra `/api/auth/protected` fetch on every session change.

### Fixes

- Backend: single-pass owner/manager/staff/salon context resolution with `select_related` / `values_list`.
- Backend: login no longer crashes on multiple active subscriptions.
- Backend: adding a second branch no longer creates another paid trial.
- Backend: branch serializer safely returns null manager names.
- Frontend: stable access-context key, one-shot onboarding redirect, session-key guarded user fetch, session-status AuthGuard.
- Dashboard: primary “Booking Next” CTA → `/apps/bookings/add-bookings`.

### Verification

- `python manage.py test api.test_user_details_performance api.test_post_login_stability` → PASS
- `node scripts/test_phase1.js` → PASS
- Live:
  - `http://127.0.0.1:8082/api/schema/` → 200
  - `http://localhost:8083/login` → 200
  - `http://localhost:8083/dashboard/default` → 200
  - `http://localhost:8083/apps/bookings/add-bookings` → 200
  - `http://127.0.0.1:8082/account-management/login/` → 200

### Follow-up from audits

- [Trace backend branch queries](371ad649-20c5-43fc-813f-0bd606ba66a1) and [Trace frontend login loop](44977218-e218-4317-bdd0-37c27e19e671) confirmed the same bootstrap bottlenecks and added residual risks around duplicate trials and null managers; those residual risks are now covered by `api.test_post_login_stability`.

## Phase 2 — Stepped Shop Owner onboarding

- [Pending] First-login state and enforced step sequence.
- [Pending] Owner/Manager registry.
- [Pending] Staff profile setup.
- [Pending] Validated service-template parser and UI.
- [Pending] Operating hours, breaks, and holidays.

## Phase 3 — Membership and pricing gate

- [Pending] Active subscription check after profile completion.
- [Pending] Premium pricing redirect when no plan is active.
- [Pending] Environment-backed mock payment and success callback.

## Phase 4 — Guest and customer conversion

- [Pending] Customer schema and registration audit.
- [Pending] Require only name and phone number.
- [Pending] Make all other customer fields optional in model, API, and UI.

## Baseline

- Backend branch: `dev`
- Frontend branch: `dev`
- Local backend: `http://127.0.0.1:8082`
- Local frontend: `http://localhost:8083`

## Error log

- None for the accepted Phase 1 implementation.
- Initial regression intentionally failed at 17 queries before the backend rewrite.
