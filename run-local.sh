#!/usr/bin/env bash
# SnipKlip cross-platform local launcher (macOS / Linux / Git Bash on Windows)
# Backend  → http://localhost:8082
# Frontend → http://localhost:8083
#
# On every start: install pkgs, reclaim reserved ports, bind 0.0.0.0, advertise localhost.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
BACKEND_PORT="${BACKEND_PORT:-8082}"
FRONTEND_PORT="${FRONTEND_PORT:-8083}"
PUBLIC_HOST="${PUBLIC_HOST:-localhost}"
BIND_HOST="${BIND_HOST:-0.0.0.0}"
LOG_DIR="${LOG_DIR:-$BACKEND_DIR/.run}"
PID_DIR="$LOG_DIR"
CMD="${1:-start}"

die() { echo "ERROR: $*" >&2; exit 1; }
ok() { echo "OK  $*" >&2; }
step() { echo "==> $*" >&2; }
warn() { echo "WARN $*" >&2; }

mkdir -p "$LOG_DIR"
[[ -f "$BACKEND_DIR/manage.py" ]] || die "Run from the SnipKlip backend repo root (manage.py missing)."

resolve_frontend() {
  local candidate
  for candidate in \
    "${FRONTEND_DIR:-}" \
    "$SCRIPT_DIR/../snipklip-frontend" \
    "$SCRIPT_DIR/snipklip-frontend" \
    "$SCRIPT_DIR/../SnipKlip-frontend" \
    "$HOME/snipklip-frontend" \
    "$HOME/dev/snipklip-frontend"
  do
    [[ -n "$candidate" ]] || continue
    if [[ -f "$candidate/package.json" ]]; then
      (cd "$candidate" && pwd)
      return 0
    fi
  done
  return 1
}

resolve_venv_python() {
  local candidate
  for candidate in \
    "$BACKEND_DIR/.venv/bin/python" \
    "$BACKEND_DIR/../.venv/bin/python" \
    "$BACKEND_DIR/venv/bin/python" \
    "$BACKEND_DIR/.venv/Scripts/python.exe" \
    "$BACKEND_DIR/../.venv/Scripts/python.exe"
  do
    if [[ -x "$candidate" ]] || [[ -f "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

port_pids() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
  elif command -v ss >/dev/null 2>&1; then
    ss -lptn "sport = :$port" 2>/dev/null | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | sort -u || true
  else
    true
  fi
}

claim_port() {
  local port="$1" retries="${2:-12}" i pids
  for ((i = 1; i <= retries; i++)); do
    pids="$(port_pids "$port")"
    if [[ -z "${pids// }" ]]; then
      ok "Port $port is free"
      return 0
    fi
    warn "Port $port occupied (pids: $(echo "$pids" | tr '\n' ' ')) — reclaiming for SnipKlip"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 0.5
    pids="$(port_pids "$port")"
    if [[ -n "${pids// }" ]]; then
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
    fi
    sleep 0.5
  done
  pids="$(port_pids "$port")"
  [[ -z "${pids// }" ]] || die "Could not free port $port (still held by: $(echo "$pids" | tr '\n' ' '))"
  ok "Port $port is free"
}

kill_pidfile() {
  local f="$1" pid
  [[ -f "$f" ]] || return 0
  pid="$(cat "$f" 2>/dev/null || true)"
  if [[ -n "${pid:-}" ]]; then
    kill "$pid" 2>/dev/null || true
    sleep 0.3
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$f"
}

stop_services() {
  step "Stopping SnipKlip + reclaiming reserved ports"
  kill_pidfile "$PID_DIR/backend.pid"
  kill_pidfile "$PID_DIR/frontend.pid"
  claim_port "$BACKEND_PORT" 8
  claim_port "$FRONTEND_PORT" 8
}

http_code() {
  curl --silent --output /dev/null --write-out '%{http_code}' --max-time 3 "$1" 2>/dev/null || echo "000"
}

wait_for_http() {
  local name="$1" url="$2" expected="$3" attempts="${4:-120}" status="" i
  for ((i = 1; i <= attempts; i++)); do
    status="$(http_code "$url")"
    if [[ "$status" == "$expected" ]]; then
      ok "$name ($status) $url"
      return 0
    fi
    sleep 1
  done
  echo "FAIL $name: expected $expected, got ${status:-none} ($url)" >&2
  return 1
}

assert_prereqs() {
  local pybin
  pybin="$(command -v python3 || command -v python || true)"
  [[ -n "$pybin" ]] || die "Python not found. Install 3.10–3.12 from https://www.python.org/downloads/"
  command -v node >/dev/null 2>&1 || die "Node.js not found. Install Node 18 LTS from https://nodejs.org/"
  command -v npm >/dev/null 2>&1 || die "npm not found (install Node 18 LTS)."
  ok "Python $($pybin --version 2>&1) | Node $(node -v) | npm $(npm -v)"
}

ensure_venv_and_packages() {
  local py pybin
  if py="$(resolve_venv_python)"; then
    ok "Using venv: $py"
  else
    step "Creating Python virtualenv at .venv"
    pybin="$(command -v python3 || command -v python)"
    "$pybin" -m venv "$BACKEND_DIR/.venv"
    if [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
      py="$BACKEND_DIR/.venv/bin/python"
    elif [[ -f "$BACKEND_DIR/.venv/Scripts/python.exe" ]]; then
      py="$BACKEND_DIR/.venv/Scripts/python.exe"
    else
      die "Failed to create .venv"
    fi
  fi
  step "Installing Python packages"
  # All chatter must go to stderr — stdout is captured as the python path.
  if ! "$py" -m pip install --upgrade "pip<25" "setuptools<70" wheel >&2; then
    warn "pip/setuptools upgrade had issues — continuing"
  fi
  if ! "$py" -m pip install --prefer-binary -r "$BACKEND_DIR/requirements.txt" >&2; then
    if "$py" -c "import django" >/dev/null 2>&1; then
      warn "pip install reported errors, but Django is already importable — continuing"
    else
      die "pip install failed and Django is not importable. Prefer Python 3.10 or 3.11."
    fi
  fi
  ok "Python packages ready"
  printf '%s\n' "$py"
}

ensure_frontend_packages() {
  local frontend_dir="$1"
  step "Installing frontend packages (npm install --legacy-peer-deps)"
  if [[ -d "$frontend_dir/node_modules" && ! -e "$frontend_dir/node_modules/next/dist/bin/next" ]]; then
    warn "Broken node_modules — removing"
    rm -rf "$frontend_dir/node_modules"
  fi
  (cd "$frontend_dir" && npm install --legacy-peer-deps)
  [[ -e "$frontend_dir/node_modules/next/dist/bin/next" ]] || die "Next.js binary missing after npm install"
  ok "Frontend packages installed"
}

sync_backend_env() {
  local env_file="$BACKEND_DIR/.env" example="$BACKEND_DIR/.env.example" tmp
  if [[ ! -f "$env_file" ]]; then
    [[ -f "$example" ]] || die "Missing .env.example"
    cp "$example" "$env_file"
    ok "Created .env from .env.example"
  fi
  local frontend_origin="http://${PUBLIC_HOST}:${FRONTEND_PORT}"
  local cors="${frontend_origin},http://127.0.0.1:${FRONTEND_PORT},http://localhost:3000,http://127.0.0.1:3000"
  tmp="$(mktemp)"
  sed \
    -e "s|^FRONTEND_LINK=.*|FRONTEND_LINK=${frontend_origin}|" \
    -e "s|^CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=${cors}|" \
    -e "s|^DEBUG=.*|DEBUG=True|" \
    -e "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,testserver|" \
    "$env_file" > "$tmp"
  grep -q '^FRONTEND_LINK=' "$tmp" || printf '\nFRONTEND_LINK=%s\n' "$frontend_origin" >> "$tmp"
  grep -q '^CORS_ALLOWED_ORIGINS=' "$tmp" || printf '\nCORS_ALLOWED_ORIGINS=%s\n' "$cors" >> "$tmp"
  mv "$tmp" "$env_file"
  ok "Backend env → FRONTEND_LINK=${frontend_origin}"
}

sync_frontend_env() {
  local frontend_dir="$1" env_file="$1/.env.local" example="$1/.env.example" tmp
  if [[ ! -f "$env_file" ]]; then
    [[ -f "$example" ]] || die "Missing frontend .env.example"
    local nextauth_secret jwt_secret
    nextauth_secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))' 2>/dev/null \
      || python -c 'import secrets; print(secrets.token_urlsafe(32))')"
    jwt_secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))' 2>/dev/null \
      || python -c 'import secrets; print(secrets.token_urlsafe(32))')"
    sed \
      -e "s|^NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=${nextauth_secret}|" \
      -e "s|^JWT_SECRET=.*|JWT_SECRET=${jwt_secret}|" \
      "$example" > "$env_file"
    ok "Created frontend .env.local with local secrets"
  fi
  local backend_url="http://${PUBLIC_HOST}:${BACKEND_PORT}/"
  local frontend_url="http://${PUBLIC_HOST}:${FRONTEND_PORT}/"
  tmp="$(mktemp)"
  sed \
    -e "s|^NEXT_PUBLIC_BACKEND_URL=.*|NEXT_PUBLIC_BACKEND_URL=${backend_url}|" \
    -e "s|^NEXT_PUBLIC_FRONTEND_URL=.*|NEXT_PUBLIC_FRONTEND_URL=${frontend_url}|" \
    -e "s|^NEXTAUTH_URL=.*|NEXTAUTH_URL=${frontend_url}|" \
    "$env_file" > "$tmp"
  mv "$tmp" "$env_file"
  ok "Frontend env → backend ${backend_url} | self ${frontend_url}"
}

start_backend() {
  local py="$1"
  claim_port "$BACKEND_PORT"
  sync_backend_env
  export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-app.settings.local}"
  export FRONTEND_LINK="http://${PUBLIC_HOST}:${FRONTEND_PORT}"
  export CORS_ALLOWED_ORIGINS="http://${PUBLIC_HOST}:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}"
  (
    cd "$BACKEND_DIR"
    "$py" scripts/init_db.py --settings="$DJANGO_SETTINGS_MODULE"
    "$py" manage.py migrate --noinput --settings="$DJANGO_SETTINGS_MODULE"
    "$py" manage.py check --settings="$DJANGO_SETTINGS_MODULE"
  )
  : >"$LOG_DIR/backend.log"
  (
    cd "$BACKEND_DIR"
    export DJANGO_SETTINGS_MODULE FRONTEND_LINK CORS_ALLOWED_ORIGINS
    exec "$py" manage.py runserver "${BIND_HOST}:${BACKEND_PORT}" --noreload --settings="$DJANGO_SETTINGS_MODULE"
  ) >>"$LOG_DIR/backend.log" 2>&1 &
  echo $! >"$PID_DIR/backend.pid"
  ok "Backend pid $(cat "$PID_DIR/backend.pid") → http://${PUBLIC_HOST}:${BACKEND_PORT}"
}

start_frontend() {
  local frontend_dir="$1" node_major
  claim_port "$FRONTEND_PORT"
  sync_frontend_env "$frontend_dir"
  : >"$LOG_DIR/frontend.log"
  node_major="$(node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0)"
  (
    cd "$frontend_dir"
    if [[ "$node_major" == "18" ]]; then
      exec node node_modules/next/dist/bin/next dev -p "$FRONTEND_PORT" -H localhost
    else
      warn "Host Node is $(node -v); launching Next with portable Node 18 via npx."
      exec npx --yes --package=node@18.20.8 node node_modules/next/dist/bin/next dev -p "$FRONTEND_PORT" -H localhost
    fi
  ) >>"$LOG_DIR/frontend.log" 2>&1 &
  echo $! >"$PID_DIR/frontend.pid"
  ok "Frontend pid $(cat "$PID_DIR/frontend.pid") → http://${PUBLIC_HOST}:${FRONTEND_PORT}"
}

print_status() {
  if [[ -n "$(port_pids "$BACKEND_PORT")" ]]; then ok "backend: listening on $BACKEND_PORT → http://${PUBLIC_HOST}:${BACKEND_PORT}"; else warn "backend: stopped"; fi
  if [[ -n "$(port_pids "$FRONTEND_PORT")" ]]; then ok "frontend: listening on $FRONTEND_PORT → http://${PUBLIC_HOST}:${FRONTEND_PORT}"; else warn "frontend: stopped"; fi
}

case "$CMD" in
  -h|--help|help)
    cat <<EOF
Usage: $(basename "$0") [start|stop|status|restart]

Ports (localhost):
  Backend  http://${PUBLIC_HOST}:${BACKEND_PORT}
  Frontend http://${PUBLIC_HOST}:${FRONTEND_PORT}
EOF
    exit 0
    ;;
  stop) stop_services; print_status; exit 0 ;;
  status) print_status; exit 0 ;;
  restart) stop_services ;;
  start) ;;
  *) die "Unknown command: $CMD" ;;
esac

assert_prereqs
FRONTEND_DIR="$(resolve_frontend)" || die \
  "Frontend not found. Clone sibling snipklip-frontend or set FRONTEND_DIR."
ok "Backend:  $BACKEND_DIR"
ok "Frontend: $FRONTEND_DIR"

VENV_PYTHON="$(ensure_venv_and_packages)"
ensure_frontend_packages "$FRONTEND_DIR"

stop_services
trap 'echo; echo "Stopping..."; stop_services; exit 0' INT TERM

start_backend "$VENV_PYTHON"
wait_for_http "Django schema" "http://${PUBLIC_HOST}:${BACKEND_PORT}/api/schema/" "200" 120 \
  || { tail -n 50 "$LOG_DIR/backend.log" >&2 || true; die "Backend unhealthy"; }

start_frontend "$FRONTEND_DIR"
wait_for_http "Next.js login" "http://${PUBLIC_HOST}:${FRONTEND_PORT}/login" "200" 180 \
  || { tail -n 50 "$LOG_DIR/frontend.log" >&2 || true; die "Frontend unhealthy"; }

cat <<EOF

SnipKlip is running:
  Backend:  http://${PUBLIC_HOST}:${BACKEND_PORT}
  Schema:   http://${PUBLIC_HOST}:${BACKEND_PORT}/api/schema/
  Frontend: http://${PUBLIC_HOST}:${FRONTEND_PORT}
  Login:    http://${PUBLIC_HOST}:${FRONTEND_PORT}/login
  Register: http://${PUBLIC_HOST}:${FRONTEND_PORT}/register
  Logs:     $LOG_DIR/backend.log
            $LOG_DIR/frontend.log

Open those localhost URLs in your browser (not 127.0.0.1).
Press Ctrl+C to stop both services.
EOF

while true; do
  [[ -n "$(port_pids "$BACKEND_PORT")" ]] || die "Backend listener on :${BACKEND_PORT} is gone."
  [[ -n "$(port_pids "$FRONTEND_PORT")" ]] || die "Frontend listener on :${FRONTEND_PORT} is gone."
  sleep 5
done
