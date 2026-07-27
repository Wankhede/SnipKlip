# SnipKlip — Local Setup Guide (Windows / macOS / Linux)

Single-click local development for the **two-repo** SnipKlip stack.

| Service | Stack | Reserved port | URL |
|---------|--------|---------------|-----|
| **Backend** | Django 3.2 + DRF + SQLite | **8082** | http://localhost:8082 |
| **Frontend** | Next.js 12 + NextAuth | **8083** | http://localhost:8083 |

> Always open **`http://localhost:...`** in the browser (not `127.0.0.1`). The launcher binds `0.0.0.0` and reclaims ports 8082/8083 if another process is holding them.

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
- Prefer **Node 18 LTS**. If you only have Node 20+, the launcher falls back to `npx node@18` automatically.

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

## 3. Single-click start

### Windows

Double-click **`run-local.bat`**, or in PowerShell / VS Code terminal:

```powershell
.\run-local.bat
# or
powershell -ExecutionPolicy Bypass -File .\run-local.ps1
```

Other commands:

```powershell
.\run-local.bat stop
.\run-local.bat status
.\run-local.bat restart
```

### macOS / Linux

```bash
chmod +x ./run-local.sh
./run-local.sh
```

```bash
./run-local.sh stop
./run-local.sh status
./run-local.sh restart
```

### What the launcher does

1. Checks Python + Node/npm on `PATH` (prints download links if missing).
2. Creates `.venv` if missing and **always installs** `requirements.txt`.
3. Creates `.env` / `.env.local` from examples when missing (localhost URLs).
4. **Reclaims ports 8082/8083** if another process is using them (kills the occupant tree, retries until free).
5. Runs migrations / DB init.
6. **Always runs** `npm install --legacy-peer-deps` for the frontend.
7. Starts Django on **8082** (`0.0.0.0` bind) and Next.js on **8083** (`localhost` bind — required for NextAuth).
8. Waits until `/api/schema/` and `/login` return HTTP 200 on **http://localhost:...**.
9. On Unix, supervises both processes until you press **Ctrl+C**. On Windows, leave the workers running and use `.\run-local.bat stop` to shut down.

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

Default seeded admin after e2e wipe / local seed (when used): `admin` / `Admin@123`.

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
NEXT_PUBLIC_BACKEND_URL=http://localhost:8082/
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
| Port already in use | `.\run-local.bat stop` then start again |
| `ExecutionPolicy` blocked | `powershell -ExecutionPolicy Bypass -File .\run-local.ps1` |
| `backports.zoneinfo` build error | Use Python 3.9+ (marker skips that package) |
| Next.js odd crashes on Node 20+ | Install Node 18, or let the launcher use `npx node@18` |
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
