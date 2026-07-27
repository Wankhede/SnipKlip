#!/usr/bin/env bash
# SnipKlip cross-platform local launcher (macOS / Linux)
# Backend  → http://127.0.0.1:8082
# Frontend → http://localhost:8083
#
# Expected sibling layout:
#   parent/
#     SnipKlip/            ← this repo
#     snipklip-frontend/   ← frontend repo
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
BACKEND_PORT="${BACKEND_PORT:-8082}"
FRONTEND_PORT="${FRONTEND_PORT:-8083}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_URL_HOST="${BACKEND_URL_HOST:-127.0.0.1}"
LOG_DIR="${LOG_DIR:-$BACKEND_DIR/.run}"
PID_DIR="$LOG_DIR"
CMD="${1:-start}"

die() { echo "ERROR: $*" >&2; exit 1; }
ok() { echo "OK  $*" >&2; }
step() { echo "==> $*" >&2; }

mkdir -p "$LOG_DIR"

resolve_frontend() {
  local candidate
  for candidate in \
    "${FRONTEND_DIR:-}" \
    "$SCRIPT_DIR/../snipklip-frontend" \
    "$SCRIPT_DIR/snipklip-frontend" \
    "$SCRIPT_DIR/../SnipKlip-frontend" \
    "$HOME/snipklip-frontend"
  do
    [[ -n "$candidate" ]] || continue
    if [[ -f "$candidate/package.json" ]]; then
      cd "$candidate" && pwd
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
    "$BACKEND_DIR/env/bin/python"
  do
    if [[ -x "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

port_pids() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null || true
  elif command -v ss >/dev/null 2>&1; then
    ss -lptn "sport = :$1" 2>/dev/null | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | sort -u || true
  else
    true
  fi
}

kill_port() {
  local port="$1" pids
  pids="$(port_pids "$port")"
  if [[ -n "$pids" ]]; then
    echo "  freeing port $port (pids: $(echo "$pids" | tr '\n' ' '))"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1
    pids="$(port_pids "$port")"
    if [[ -n "$pids" ]]; then
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

kill_pidfile() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  local pid
  pid="$(cat "$f" 2>/dev/null || true)"
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    sleep 0.5
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$f"
}

stop_services() {
  step "Stopping SnipKlip services"
  kill_pidfile "$PID_DIR/backend.pid"
  kill_pidfile "$PID_DIR/frontend.pid"
  kill_port "$BACKEND_PORT"
  kill_port "$FRONTEND_PORT"
}

http_code() {
  curl --silent --output /dev/null --write-out '%{http_code}' --max-time 3 "$1" 2>/dev/null || echo "000"
}

wait_for_http() {
  local name="$1" url="$2" expected="$3" attempts="${4:-90}" status=""
  local i
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
  command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || die \
    "Python not found. Install 3.10–3.12 from https://www.python.org/downloads/"
  command -v node >/dev/null 2>&1 || die \
    "Node.js not found. Install Node 18 LTS from https://nodejs.org/"
  command -v npm >/dev/null 2>&1 || die "npm not found (install Node 18 LTS)."
  ok "Python $($(command -v python3 || command -v python) --version 2>&1) | Node $(node -v) | npm $(npm -v)"
}

ensure_venv() {
  local py
  if py="$(resolve_venv_python)"; then
    ok "Using venv: $py"
    echo "$py"
    return 0
  fi
  step "Creating Python virtualenv at .venv"
  local pybin
  pybin="$(command -v python3 || command -v python)"
  "$pybin" -m venv "$BACKEND_DIR/.venv"
  py="$BACKEND_DIR/.venv/bin/python"
  [[ -x "$py" ]] || die "Failed to create .venv"
  "$py" -m pip install --upgrade pip
  "$py" -m pip install -r "$BACKEND_DIR/requirements.txt"
  ok "Virtualenv ready"
  echo "$py"
}

sync_backend_env() {
  local env_file="$BACKEND_DIR/.env"
  local example="$BACKEND_DIR/.env.example"
  if [[ ! -f "$env_file" ]]; then
    [[ -f "$example" ]] || die "Missing .env.example"
    cp "$example" "$env_file"
    ok "Created .env from .env.example"
  fi
  local frontend_origin="http://localhost:${FRONTEND_PORT}"
  local cors="${frontend_origin},http://127.0.0.1:${FRONTEND_PORT},http://localhost:3000,http://127.0.0.1:3000"
  local tmp
  tmp="$(mktemp)"
  # shellcheck disable=SC2002
  cat "$env_file" \
    | sed -e "s|^FRONTEND_LINK=.*|FRONTEND_LINK=${frontend_origin}|" \
          -e "s|^CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=${cors}|" \
          -e "s|^DEBUG=.*|DEBUG=True|" \
    > "$tmp"
  grep -q '^FRONTEND_LINK=' "$tmp" || printf '\nFRONTEND_LINK=%s\n' "$frontend_origin" >> "$tmp"
  grep -q '^CORS_ALLOWED_ORIGINS=' "$tmp" || printf '\nCORS_ALLOWED_ORIGINS=%s\n' "$cors" >> "$tmp"
  mv "$tmp" "$env_file"
  ok "Backend env ports → FRONTEND_LINK=${frontend_origin}"
}

sync_frontend_env() {
  local frontend_dir="$1"
  local env_file="$frontend_dir/.env.local"
  local example="$frontend_dir/.env.example"
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
  local backend_url="http://${BACKEND_URL_HOST}:${BACKEND_PORT}/"
  local frontend_url="http://localhost:${FRONTEND_PORT}/"
  local tmp
  tmp="$(mktemp)"
  sed \
    -e "s|^NEXT_PUBLIC_BACKEND_URL=.*|NEXT_PUBLIC_BACKEND_URL=${backend_url}|" \
    -e "s|^NEXT_PUBLIC_FRONTEND_URL=.*|NEXT_PUBLIC_FRONTEND_URL=${frontend_url}|" \
    -e "s|^NEXTAUTH_URL=.*|NEXTAUTH_URL=${frontend_url}|" \
    "$env_file" > "$tmp"
  mv "$tmp" "$env_file"
  ok "Frontend env → backend ${backend_url} | self ${frontend_url}"
}

ensure_frontend_deps() {
  local frontend_dir="$1"
  if [[ ! -x "$frontend_dir/node_modules/next/dist/bin/next" ]]; then
    step "Installing frontend dependencies"
    (cd "$frontend_dir" && npm install --legacy-peer-deps)
  fi
  [[ -x "$frontend_dir/node_modules/next/dist/bin/next" ]] || die "Next.js binary missing after npm install"
}

resolve_node_for_next() {
  local major
  major="$(node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0)"
  if [[ "$major" == "18" ]]; then
    command -v node
    return 0
  fi
  # Use npm's package runner to execute Next under Node 18 without global downgrade.
  echo "npx-node18"
}

start_backend() {
  local py="$1"
  sync_backend_env
  export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-app.settings.local}"
  export FRONTEND_LINK="${FRONTEND_LINK:-http://localhost:${FRONTEND_PORT}}"
  export CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}}"
  (
    cd "$BACKEND_DIR"
    "$py" scripts/init_db.py --settings="$DJANGO_SETTINGS_MODULE"
    "$py" manage.py migrate --noinput --settings="$DJANGO_SETTINGS_MODULE"
    "$py" manage.py check --settings="$DJANGO_SETTINGS_MODULE"
  )
  (
    cd "$BACKEND_DIR"
    export DJANGO_SETTINGS_MODULE FRONTEND_LINK CORS_ALLOWED_ORIGINS
    exec "$py" manage.py runserver "${BACKEND_HOST}:${BACKEND_PORT}" --noreload --settings="$DJANGO_SETTINGS_MODULE"
  ) >"$LOG_DIR/backend.log" 2>&1 &
  echo $! >"$PID_DIR/backend.pid"
  ok "Backend pid $(cat "$PID_DIR/backend.pid") → http://${BACKEND_URL_HOST}:${BACKEND_PORT}"
}

start_frontend() {
  local frontend_dir="$1"
  sync_frontend_env "$frontend_dir"
  ensure_frontend_deps "$frontend_dir"
  local node_bin
  node_bin="$(resolve_node_for_next)"
  (
    cd "$frontend_dir"
    if [[ "$node_bin" == "npx-node18" ]]; then
      echo "Host Node is $(node -v); launching Next with portable Node 18 via npx." >&2
      exec npx --yes --package=node@18.20.8 node node_modules/next/dist/bin/next dev -p "$FRONTEND_PORT"
    else
      echo "Using Node $($node_bin -v) for Next.js." >&2
      exec "$node_bin" node_modules/next/dist/bin/next dev -p "$FRONTEND_PORT"
    fi
  ) >"$LOG_DIR/frontend.log" 2>&1 &
  echo $! >"$PID_DIR/frontend.pid"
  ok "Frontend pid $(cat "$PID_DIR/frontend.pid") → http://localhost:${FRONTEND_PORT}"
}

print_status() {
  if [[ -n "$(port_pids "$BACKEND_PORT")" ]]; then ok "backend: listening on $BACKEND_PORT"; else echo "backend: stopped"; fi
  if [[ -n "$(port_pids "$FRONTEND_PORT")" ]]; then ok "frontend: listening on $FRONTEND_PORT"; else echo "frontend: stopped"; fi
}

[[ -f "$BACKEND_DIR/manage.py" ]] || die "Run from the SnipKlip backend repo root (manage.py missing)."

case "$CMD" in
  -h|--help|help)
    cat <<EOF
Usage: $(basename "$0") [start|stop|status|restart]

Ports:
  Backend  http://${BACKEND_URL_HOST}:${BACKEND_PORT}
  Frontend http://localhost:${FRONTEND_PORT}
EOF
    exit 0
    ;;
  stop)
    stop_services
    ok "Stopped SnipKlip services."
    exit 0
    ;;
  status)
    print_status
    exit 0
    ;;
  restart)
    stop_services
    ;;
  start) ;;
  *)
    die "Unknown command: $CMD"
    ;;
esac

assert_prereqs
FRONTEND_DIR="$(resolve_frontend)" || die \
  "Frontend not found. Clone sibling snipklip-frontend or set FRONTEND_DIR."
ok "Backend:  $BACKEND_DIR"
ok "Frontend: $FRONTEND_DIR"

stop_services
trap 'echo; echo "Stopping..."; stop_services; exit 0' INT TERM

VENV_PYTHON="$(ensure_venv)"
start_backend "$VENV_PYTHON"
wait_for_http "Django schema" "http://${BACKEND_URL_HOST}:${BACKEND_PORT}/api/schema/" "200" 90 \
  || { tail -n 40 "$LOG_DIR/backend.log" >&2 || true; die "Backend unhealthy. See $LOG_DIR/backend.log"; }

start_frontend "$FRONTEND_DIR"
wait_for_http "Next.js login" "http://127.0.0.1:${FRONTEND_PORT}/login" "200" 180 \
  || { tail -n 40 "$LOG_DIR/frontend.log" >&2 || true; die "Frontend unhealthy. See $LOG_DIR/frontend.log"; }

cat <<EOF

SnipKlip is running:
  Backend:  http://${BACKEND_URL_HOST}:${BACKEND_PORT}
  Schema:   http://${BACKEND_URL_HOST}:${BACKEND_PORT}/api/schema/
  Frontend: http://localhost:${FRONTEND_PORT}
  Login:    http://localhost:${FRONTEND_PORT}/login
  Logs:     $LOG_DIR/backend.log
            $LOG_DIR/frontend.log

Press Ctrl+C to stop both services.
EOF

while true; do
  [[ -n "$(port_pids "$BACKEND_PORT")" ]] || die "Backend listener on :${BACKEND_PORT} is gone."
  [[ -n "$(port_pids "$FRONTEND_PORT")" ]] || die "Frontend listener on :${FRONTEND_PORT} is gone."
  sleep 5
done
