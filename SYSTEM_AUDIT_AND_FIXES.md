# SnipKlip System Audit & Fixes Report

**Date:** 2026-07-23  
**Branch:** `dev`  
**Scope:** Backend (`SnipKlip/`), Frontend (`snipklip-frontend`), E2E (`e2e-tests/`)

---

## Verdict

Language-switching blank screens and several `/api/v3` HTML 500s were fixed. Playwright coverage expanded (`i18n`, `api-contract`, `user-journeys`). Frontend production build succeeds on Node 18. API suite: **80/80**. UI i18n + user-journeys: **42/42**.

---

## Phase 1 — Root causes (i18n / language switching)

| Root cause | Impact | Fix |
|------------|--------|-----|
| Locale JSON catalogs incomplete vs `en.json` (up to 109 missing keys) | Missing nav/labels; fragile `FormattedMessage` usage | Filled missing keys from English for `hi/mr/te/ta/fr/ro/zh` |
| `Locales.tsx` rendered nothing until async load; no English merge | White-screen flash / empty tree on locale swap | Seed with `en`, merge overlays, `onError` no-op, never unmount children |
| Invalid/corrupt `localStorage` config crashed boot (`JSON.parse`) | Full app crash on reload | Safe parse in `useLocalStorage` + typed setter |
| Unsupported `i18n` codes persisted without sanitization | Bad dynamic import / unstable locale | `sanitizeConfig` + whitelist in `ConfigContext` |
| Localization menu items missing React `key` | Console warnings / unstable list | Added `key={language.code}` |

**Note:** Locale remains frontend-only (react-intl). APIs do not receive `Accept-Language`; Django `User.language` is unused by REST.

---

## Phase 2 — Runtime / API fixes

| Endpoint / area | Failure | Fix |
|-----------------|---------|-----|
| `GET /api/v3/kanban/profiles/` | `AttributeError` on `obj.user.name` when `user` is null | Null-safe serializer `get_name` |
| `GET /api/v3/get-user/` | `MultiValueDictKeyError: user_id` | `.get()` + HTTP 400 when missing |
| `GET /api/v3/subscription/` | `MultiValueDictKeyError: salon_id` | Query/body `.get()` + 400 |
| `POST /api/v3/bookings/` | `KeyError: slot` on incomplete body | Required-field validation → 400 |
| `POST /api/v3/billings/` | `KeyError: discount` etc. | Required-field validation + guarded parse → 400 |
| `GET /api/v3/dashboard/` | `MultiValueDictKeyError` without branch/user | Guard params → 400; stop raising `Response` |
| Prior (already in working tree) | Middleware null `subscription_name`, salary URL clash, todos `.value`, reviews/booking/inventory/kanban hardenings | Retained and verified |

Also corrected: frontend `deleteJob` → `/api/v3/delete-job/` (was `delete-product`).

---

## Phase 3 — Test suite (`/e2e-tests`)

### New / updated specs
- `tests/ui/i18n.spec.ts` — locale persistence, corrupt storage, mid-session swaps, Hindi route smoke
- `tests/api/api-contract.spec.ts` — auth, all list endpoints, previously crashing surfaces, reports
- `tests/ui/user-journeys.spec.ts` — auth + discovered module routes + mid-flow edges
- `tests/ui/02-app-routes.spec.ts` — corrected paths to real Next.js routes (`manage-customers`, etc.)

### npm scripts
**Workspace** (`SnipKlip/package.json`):
- `npm run test:all`
- `npm run test:i18n`
- `npm run test:e2e` / `test:ui` / `test:audit`
- `npm run build` (frontend via Node path)

**e2e-tests**:
- `test:i18n`, `test:journeys`, `test:contract`, `test:api`, `test:browser`, `test:all`

---

## Phase 4 — Verification

| Check | Result |
|-------|--------|
| `npx playwright test tests/api --project=api` | **80 passed** |
| `npx playwright test tests/ui/i18n.spec.ts tests/ui/user-journeys.spec.ts` | **42 passed** |
| Frontend `npm run build` (Node 18) | **Success** (Next.js 12; Node 26 incompatible — use Node 18) |
| Architecture audit | Exit 0 (no HIGH) |

---

## Files touched (summary)

### Backend (`SnipKlip/`)
`api/serializers.py`, `api/views/user_profile.py`, `api/views/subscription.py`, `api/views/booking.py`, `api/views/billing.py`, `api/views/dashboard.py`, plus prior heal diffs: `app/middlewares.py`, `api/urls.py`, `api/constants.py`, `api/views/{inventory,job,kanban,review,salary,salon,todos,voucher}.py`

### Frontend (`snipklip-frontend/`)
`src/components/Locales.tsx`, `src/contexts/ConfigContext.tsx`, `src/hooks/useLocalStorage.ts`, `src/layout/.../Localization.tsx`, `src/utils/locales/*.json`, `src/services/job.ts`

### E2E (`e2e-tests/`)
New/updated specs + `package.json` scripts; workspace `package.json`

---

## Ops notes

- Backend is started with `--noreload`; code changes require a process restart.
- Prefer `./start_all.sh` for a supervised stack; killing only the Django PID will make the supervisor shut everything down.
- Run frontend build/dev under **Node 18** (see `.run/node18`).
