# SnipKlip Migration Status

> Hexamart → SnipKlip migration tracker. Updated after each batch.

## Phase Overview

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Setup for Token Efficiency (.cursorignore, this file) | [Complete] |
| 1 | Local Environment & Database | [Complete] |
| 2 | Branding & Domain Isolation | [Complete] |
| 3 | Secrets & Environment | [Complete — **ROTATE THESE pending your ack**] |
| 4 | Package/Module Renaming | [Complete — already `app`; no Hexamart package found] |
| 5 | UI/UX Polish | [Complete — API backend; formatted touched modules] |
| 6 | Git Branching Strategy | [Complete — branches created locally, not pushed] |
| 7 | Final Report | [Complete] |

## Checkpoints

| Tag | Created | Notes |
|-----|---------|-------|
| checkpoint/phase-0-start | 2026-07-17 | Initial migration tracker |
| checkpoint/phase-1-start | 2026-07-17 | Before local env changes |
| checkpoint/phase-1 | 2026-07-17 | Local env verified |
| checkpoint/phase-2-start | 2026-07-17 | Before branding batch |
| checkpoint/phase-2 | 2026-07-17 | Central branding config |
| checkpoint/phase-3-start | 2026-07-17 | Before secrets batch |
| checkpoint/phase-3 | 2026-07-17 | django-environ + secret externalization |
| checkpoint/phase-4-start | 2026-07-17 | Package rename audit |
| checkpoint/phase-4 | 2026-07-17 | No rename required (`app` package) |

## ROTATE THESE

> Real credentials previously hardcoded or committed. **Acknowledge before considering Phase 3 fully closed.**

| Secret | Location | Action Required |
|--------|----------|-----------------|
| Fernet encryption key (`secret.key`) | Was tracked in git (`secret.key`); now gitignored | Generate new Fernet key, set `FERNET_KEY` in `.env`, re-encrypt any data if needed |
| Hardcoded Fernet key | `backend/views/common/qr.py` (removed) | Same as above — treat as compromised |
| Cron job token `dx6QJHqEDSGfG7XqKHdp` | `backend/cron.py` (removed) | Set new `CRON_JOB_TOKEN` in `.env`; update cron/wget jobs on servers |
| WhatsApp Phone Number ID `100715709627999` | `api/views/whatsapp.py` (removed) | Confirm Meta app ownership; set `WHATSAPP_PHONE_NUMBER_ID` in `.env` |
| SendGrid API key | Previously misused via `EMAIL_HOST_PASSWORD` | Ensure `SENDGRID_API_KEY` is set; rotate if ever committed |
| `.env` production values | Local `.env` (gitignored) | Review git history (`9442b8b` cleaned secrets); rotate any that ever appeared in commits |

## Remaining #TODO (Manual)

| Item | Phase | Notes |
|------|-------|-------|
| SnipKlip logo (`logo.png`) | 2 | Place at `static/branding/logo.png`; set `LOGO` if path differs |
| SnipKlip brochure PDF | 2 | Place at `static/branding/SnipKlip-Brochure.pdf` or set `BROCHURE_LINK` |
| Google OAuth client | 3 | Create SnipKlip OAuth app; set `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY/SECRET` |
| Razorpay keys | 3 | Set `RAZORPAY_KEY_ID/SECRET` for payments |
| HubSpot API key | 3 | Set `HUBSPOT_KEY` |
| VAPID / Web Push keys | 3 | Set `VAPID_*`, `PRIVATE_KEY_WEB_PUSH`, `API_KEY_WEB_PUSH` |
| Facebook/WhatsApp tokens | 3 | Set `FACEBOOK_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` |
| Fast2SMS API key | 3 | Set `FAST2SMS_API_KEY` |
| reCAPTCHA keys | 3 | Set `GOOGLE_CAPTCHA_KEY/SECRET` |
| `backend/migrations/` gitignored | 1 | Run `makemigrations backend` on each fresh clone until migrations are tracked |
| drf-spectacular `/api/schema/` 500 | 1 | AssertionError on schema generation — investigate serializer annotations |
| PostgreSQL local DB (optional) | 1 | Use `scripts/init_db.py` with `DB_ENGINE=postgresql` in `.env` |

## Verification Log

| Phase | Command / Test | Result | Timestamp |
|-------|----------------|--------|-----------|
| 1 | `python manage.py check --settings=app.settings.local` | PASS | 2026-07-17 |
| 1 | `python manage.py migrate --plan --settings=app.settings.local` | PASS | 2026-07-17 |
| 1 | `python manage.py migrate --settings=app.settings.local` | PASS | 2026-07-17 |
| 1 | `runserver` on 127.0.0.1:8000 | PASS | 2026-07-17 |
| 1 | GET `/account-management/` → 302 | PASS | 2026-07-17 |
| 1 | GET `/api/v3/login/` → 405 (POST required) | PASS | 2026-07-17 |
| 1 | GET `/api/schema/` → 500 | WARN | 2026-07-17 |
| 2 | `grep -ri hexamart` (excl. this doc) | 0 hits | 2026-07-17 |
| 3 | `.gitignore` blocks `.env`, `secret.key`, certs | PASS | 2026-07-17 |
| 4 | `python manage.py check` post package audit | PASS | 2026-07-17 |

## Errors Log

| Phase | Batch | Error | Fix Attempted | Result |
|-------|-------|-------|---------------|--------|
| 1 | deps | Django not in venv | Installed core requirements | Fixed |
| 1 | deps | django-allauth middleware mismatch | Pinned allauth==0.52.0 | Fixed |
| 1 | deps | debug_toolbar missing | pip install | Fixed |
| 1 | migrate | `.env` unreadable in sandbox | Ran with full permissions | Fixed |
| Integration | backend tests | Legacy tests import swapped `auth.User` and call removed `assertEquals` | One verification run; no unrelated test rewrite | Pre-existing, logged |
| Integration | signup API | Access-control middleware rejected public signup before reaching the view | Added signup/login/send-email to explicit public API paths | Fixed |
| Frontend auth | salon registration | Middleware blocked `/api/v3/add-salon/`; login assumed every salon already had a branch | Made registration public and branch lookup nullable during onboarding | Fixed |
| Frontend auth | user details | `/api/v3/user-details/` also dereferenced a missing first branch | Made pre-onboarding branch ID nullable | Fixed |

## Files Modified / Added / Removed

### New
- `.cursorignore`
- `migration_status.md`
- `scripts/init_db.py`, `scripts/run_local.sh`
- `app/snipklip_config.py`
- `backend/crypto_utils.py`
- `static/branding/README.md`

### Modified
- `app/settings/base.py`, `app/settings/env.py`
- `backend/apps.py`, `backend/custom.py`, `backend/cron.py`
- `backend/views/common/qr.py`, `backend/views/vendor/vendor.py`
- `api/views/contact_us.py`, `api/views/mail.py`, `api/views/whatsapp.py`, `api/views/sms.py`, `api/views/billing.py`
- `app/urls.py`, `app/middlewares.py` (public signup and API paths)
- `api/common.py`, `api/urls.py`, `api/views/signup_page.py` (signup API/page)
- `.env.example`, `.gitignore`, `requirements.txt`

### Removed from git tracking
- `secret.key` (file remains locally if present; now gitignored)

### Uncommitted / gitignored (local only)
- `app/settings/local.py` (localhost CORS/ALLOWED_HOSTS overrides)
- `backend/migrations/` (generated locally)
- `db.sqlite3`, `.env`

## Functionality at Risk & Verification

| Area | Risk | Status |
|------|------|--------|
| Auth / JWT / OAuth | Google OAuth keys empty locally | Routes load; OAuth login needs keys |
| Bookings / REST API | Migrations generated fresh | `/api/v3/login/` responds |
| Payments (Razorpay) | Keys empty | Code reads env; untested without keys |
| Email (SendGrid / Gmail OAuth) | Needs `SENDGRID_API_KEY` or Gmail OAuth token | contact_us wired to settings |
| Celery/cron | Cron token moved to env | Update server cron URLs |
| Admin portal | Boots | `/account-management/` → 302 |
| Vendor/customer portals | Frontend at `FRONTEND_LINK` | Backend API verified booting |
| WhatsApp notifications | Needs Meta tokens | Externalized to env |
| Fernet encryption (billing/QR) | **Key rotation required** | Uses `backend/crypto_utils.py` |

## Git Branching (Phase 6 — not pushed)

| Branch | Purpose | Tip commit | Would push to |
|--------|---------|------------|---------------|
| `main` | Production-ready verified work | `ae5e868` (+ pending phase 5/7 commit) | `origin/main` |
| `stag` | Pre-production mirror | same as main at branch creation | `origin/stag` (create remote) |
| `dev` | Active sandbox / trial work | same as main at branch creation | `origin/dev` (create remote) |

**Awaiting your explicit "push" before any remote push.**

## Local Run Quickstart

```bash
source ../.venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in secrets
python scripts/init_db.py --settings=app.settings.local
python manage.py migrate --settings=app.settings.local
python manage.py runserver 127.0.0.1:8000 --settings=app.settings.local
```

Or: `./scripts/run_local.sh`

## AI Help Assistant

- [Complete] Authenticated endpoint: `POST /api/v3/assistant/ask/`.
- [Complete] OpenAI-compatible provider configuration with local retrieval fallback.
- The corpus contains curated product guidance only and imports no customer, salon, staff, billing, or admin models.
- Questions are checked for sensitive-data extraction, prompt injection, credentials, and PII before any optional LLM call.
- No prompts, responses, or conversations are persisted.
- Verification: 6 focused tests pass, covering JWT enforcement, retrieval, refusal, redaction, and outbound LLM payload isolation.
- Security note: replace the weak local Django signing key before any shared deployment; tests correctly emit a short-key warning.
