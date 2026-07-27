# SnipKlip — Local Setup Guide (Windows / macOS / Linux)

Single entry local development for the **two-repo** SnipKlip stack.

| Service | Stack | Reserved port | URL |
|---------|--------|---------------|-----|
| **Backend** | Django 3.2 + DRF + SQLite | **8082** | http://localhost:8082 |
| **Frontend** | Next.js 12 + NextAuth | **8083** | http://localhost:8083 |

## The one thing to run

```bash
node run-local.js
```

Same command on **Windows, macOS, and Linux** — in Cursor, VS Code, PowerShell, cmd, or Terminal.

| Where | Action |
|-------|--------|
| **Cursor / VS Code** | `Terminal` → `Run Task…` → **SnipKlip: Start** · or **Cmd/Ctrl+Shift+B** (default build task) |
| **Terminal** | `node run-local.js` |
| Stop | `node run-local.js stop` |
| Status | `node run-local.js status` |
| Restart | `node run-local.js restart` |

`run-local.js` picks the OS launcher for you (`run-local.bat` / `run-local.ps1` on Windows, `run-local.sh` on macOS/Linux). You do not need to remember which script matches your OS.

> Always open **`http://localhost:...`** in the browser (not `127.0.0.1`). The launcher reclaims ports 8082/8083 if another process is holding them.

---

## 1. Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Git | any recent | https://git-scm.com/downloads |
| Python | **3.10–3.12** (3.9+ minimum) | https://www.python.org/downloads/ |
| Node.js | **18.x LTS** (required by Next.js 12) | https://nodejs.org/en/download |

**Windows tips**
- During Python install, enable **Add python.exe to PATH**.
- Install Git for Windows so `git` works in PowerShell / VS Code.
- Prefer **Node 18 LTS**. If you only have Node 20+/26, the launcher downloads a portable Node 18 under `.run/node18/` (no `npx` / global npm cache needed).

---

## 2. Clone both repositories (sibling layout)

```text
parent/
  SnipKlip/              ← backend  (this repo)
  snipklip-frontend/     ← frontend
```

### Windows (PowerShell)

```powershell
cd $HOME\dev   # or any folder you prefer
git clone https://github.com/Wankhede/SnipKlip.git
git clone https://github.com/Wankhede/SnipKlip-frontend.git snipklip-frontend
cd SnipKlip
git checkout dev
cd ..\snipklip-frontend
git checkout dev
cd ..\SnipKlip
```

### macOS / Linux

```bash
mkdir -p ~/dev && cd ~/dev
git clone https://github.com/Wankhede/SnipKlip.git
git clone https://github.com/Wankhede/SnipKlip-frontend.git snipklip-frontend
cd SnipKlip && git checkout dev
cd ../snipklip-frontend && git checkout dev
cd ../SnipKlip
```

If the frontend lives elsewhere, set:

```powershell
$env:FRONTEND_DIR = "D:\path\to\snipklip-frontend"
```

```bash
export FRONTEND_DIR=/path/to/snipklip-frontend
```

---

## 3. Start (one command)

From the **backend repo** root (`SnipKlip/`):

```bash
node run-local.js
```

**Cursor / VS Code:** open this repo (or the parent folder that contains `run-local.js`), then **Run Task → SnipKlip: Start**.

Optional OS-native shortcuts (same behavior):

```powershell
# Windows only
.\run-local.bat
```

```bash
# macOS / Linux only
./run-local.sh
```

### What the launcher does

1. Checks Python + Node/npm on `PATH` (prints download links if missing).
2. Creates `.venv` if missing. **Installs** `requirements.txt` only when packages are missing/broken (or `FORCE_INSTALL=1`).
3. Creates `.env` / `.env.local` from examples when missing (localhost URLs).
4. **Reclaims ports 8082/8083** if another process is using them (kills the occupant tree, retries until free).
5. Runs migrations / DB init.
6. **Installs** frontend packages (`npm install --legacy-peer-deps`) only when `next` / `react` are missing — otherwise skips straight to start.
7. Starts Django on **8082** (`0.0.0.0` bind) and Next.js on **8083** (`localhost` bind — required for NextAuth).
8. Waits until `/api/schema/` and `/login` return HTTP 200 on **http://localhost:...**.
9. On Unix, supervises both processes until you press **Ctrl+C**. On Windows, leave the workers running and use `.\run-local.bat stop` to shut down.

**Everyday use:** once deps are installed, `node run-local.js` just starts backend + frontend. To force reinstall: `FORCE_INSTALL=1 node run-local.js`.

Logs:

- Backend: `.run/backend.log`
- Frontend: `.run/frontend.log`

---

## 4. Verify

With the launcher running:

| Check | Expected |
|-------|----------|
| http://localhost:8082/api/schema/ | 200 |
| http://localhost:8083/login | 200 |
| http://localhost:8083/register | page loads |

Default seeded accounts after e2e wipe / local seed:

| Role | Login (email or username) | Password |
|------|---------------------------|----------|
| **Admin** | `admin` or `admin@snipklip.local` | `Admin@123` |
| **Employee (Staff)** | `employee@snipklip.local` | `Employee@123` |
| **Customer** | `customer@snipklip.local` | `Customer@123` |

Salon id **3**, branch id **1**, Premium subscription.

---

## 5. Environment defaults (auto-written)

### Backend `.env` (from `.env.example`)

```dotenv
DEBUG=True
FRONTEND_LINK=http://localhost:8083
CORS_ALLOWED_ORIGINS=http://localhost:8083,http://127.0.0.1:8083,http://localhost:3000,http://127.0.0.1:3000
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

### Frontend `.env.local` (from `.env.example`)

```dotenv
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8082/
NEXT_PUBLIC_FRONTEND_URL=http://localhost:8083/
NEXTAUTH_URL=http://localhost:8083/
```

Secrets (`NEXTAUTH_SECRET`, `JWT_SECRET`) are generated on first create.

---

## 6. Common Windows failures

| Symptom | Fix |
|---------|-----|
| `Python was not found` | Reinstall Python with PATH enabled; reopen terminal |
| `Node.js / npm was not found` | Install Node 18 LTS; reopen terminal |
| `Frontend repo not found` | Clone sibling `snipklip-frontend` or set `FRONTEND_DIR` |
| Port already in use | Launcher reclaim should free it; or `.\run-local.bat stop` |
| `ExecutionPolicy` blocked | `powershell -ExecutionPolicy Bypass -File .\run-local.ps1` |
| `TCP connection failed` / login 500 | Use **http://localhost:8083** (not 127.0.0.1) in the browser. Pull latest launcher — it sets `NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8082/` so NextAuth does not hit IPv6 `::1` while Django is IPv4-only. |
| Says next/react not installed but `node_modules` exists | Pull latest launcher — it verifies with `require('next')` instead of Unix bin checks. Then `cd ..\snipklip-frontend && npm install --legacy-peer-deps`. |
| `backports.zoneinfo` build error | Use Python 3.9+ (marker skips that package) |
| Next.js odd crashes / `npx` EACCES on Node 20+ | Install Node 18 LTS, or let the launcher use portable `.run/node18`. If you see `Your cache folder contains root-owned files`, run: `sudo chown -R $(whoami) ~/.npm` |
| `numpy` / pip build fails on Python 3.12 | Prefer Python **3.10 or 3.11**. Launcher continues if Django is already importable. |
| CORS / auth loop | Confirm frontend is on **8083** and backend env `FRONTEND_LINK` matches |

---

## 7. Manual (advanced) start

Backend:

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py --settings=app.settings.local
python manage.py migrate --settings=app.settings.local
python manage.py runserver 127.0.0.1:8082 --settings=app.settings.local
```

Frontend:

```bash
cp .env.example .env.local   # set secrets + ports
npm install --legacy-peer-deps
npx --yes --package=node@18.20.8 node node_modules/next/dist/bin/next dev -p 8083
```

---

## 8. Repo map

| Repo | URL |
|------|-----|
| Backend | https://github.com/Wankhede/SnipKlip.git |
| Frontend | https://github.com/Wankhede/SnipKlip-frontend.git |

Branch for local work: **`dev`**.
