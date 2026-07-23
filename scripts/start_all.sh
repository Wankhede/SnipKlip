#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

resolve_backend() {
  local candidate
  for candidate in \
    "${BACKEND_DIR:-}" \
    "$SCRIPT_DIR/SnipKlip" \
    "$SCRIPT_DIR/../SnipKlip" \
    "$SCRIPT_DIR" \
    "$HOME/SnipKlip/SnipKlip"
  do
    [[ -n "$candidate" ]] || continue
    if [[ -f "$candidate/manage.py" ]]; then
      cd "$candidate" && pwd
      return 0
    fi
  done
  return 1
}

resolve_frontend() {
  local candidate
  for candidate in \
    "${FRONTEND_DIR:-}" \
    "$SCRIPT_DIR/../snipklip-frontend" \
    "$SCRIPT_DIR/../../snipklip-frontend" \
    "$SCRIPT_DIR" \
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

resolve_venv() {
  local candidate
  for candidate in \
    "$BACKEND_DIR/../.venv/bin/activate" \
    "$BACKEND_DIR/../../.venv/bin/activate" \
    "$HOME/SnipKlip/.venv/bin/activate"
  do
    if [[ -f "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

BACKEND_DIR="$(resolve_backend || true)"
FRONTEND_DIR="$(resolve_frontend || true)"
VENV_ACTIVATE="$(resolve_venv || true)"
WORKSPACE_DIR="$(cd "$(dirname "$BACKEND_DIR")" && pwd)"
LOG_DIR="${LOG_DIR:-$WORKSPACE_DIR/.run}"
PID_DIR="$LOG_DIR"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8082}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-8083}"
# Client-facing backend URL (0.0.0.0 is not a valid browser host).
BACKEND_URL_HOST="${BACKEND_URL_HOST:-127.0.0.1}"

mkdir -p "$LOG_DIR"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

require_dir() {
  local label="$1"
  local path="$2"
  [[ -d "$path" ]] || die "$label not found at $path"
}

http_code() {
  curl --silent --output /dev/null --write-out '%{http_code}' --max-time 3 "$1" 2>/dev/null || echo "000"
}

wait_for_http() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local attempts="${4:-60}"
  local status=""

  for ((i = 1; i <= attempts; i++)); do
    status="$(http_code "$url")"
    if [[ "$status" == "$expected" ]]; then
      echo "PASS $name ($status) $url"
      return 0
    fi
    sleep 1
  done

  echo "FAIL $name: expected $expected, got ${status:-none} ($url)" >&2
  return 1
}

port_pids() {
  lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null || true
}

write_listener_pid() {
  local name="$1"
  local port="$2"
  local pids
  pids="$(port_pids "$port" | tr '\n' ' ' | awk '{print $1}')"
  if [[ -n "$pids" ]]; then
    echo "$pids" >"$PID_DIR/${name}.pid"
  fi
}

service_running() {
  local port="$1"
  local pids
  pids="$(port_pids "$port")"
  [[ -n "$pids" ]]
}

sync_frontend_env_ports() {
  local env_file="$1"
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
}

ensure_frontend_env() {
  local env_file="$FRONTEND_DIR/.env.local"
  if [[ ! -f "$env_file" ]]; then
    [[ -f "$FRONTEND_DIR/.env.example" ]] || die "Missing frontend .env.example"

    local nextauth_secret jwt_secret
    nextauth_secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
    jwt_secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

    sed \
      -e "s|^NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=${nextauth_secret}|" \
      -e "s|^JWT_SECRET=.*|JWT_SECRET=${jwt_secret}|" \
      "$FRONTEND_DIR/.env.example" > "$env_file"
    echo "Created $env_file with local secrets."
  fi

  sync_frontend_env_ports "$env_file"
  echo "Frontend env ports → backend ${BACKEND_URL_HOST}:${BACKEND_PORT}, frontend localhost:${FRONTEND_PORT}"
}

sync_backend_env_ports() {
  local env_file="$BACKEND_DIR/.env"
  [[ -f "$env_file" ]] || return 0

  local frontend_origin="http://localhost:${FRONTEND_PORT}"
  local frontend_origin_ip="http://127.0.0.1:${FRONTEND_PORT}"
  local cors_value="${frontend_origin},${frontend_origin_ip},http://localhost:3000,http://127.0.0.1:3000"
  local tmp
  tmp="$(mktemp)"

  if grep -q '^FRONTEND_LINK=' "$env_file"; then
    sed -e "s|^FRONTEND_LINK=.*|FRONTEND_LINK=${frontend_origin}|" "$env_file" > "$tmp"
  else
    printf '\nFRONTEND_LINK=%s\n' "$frontend_origin" >> "$env_file"
    cp "$env_file" "$tmp"
  fi

  if grep -q '^CORS_ALLOWED_ORIGINS=' "$tmp"; then
    sed -e "s|^CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=${cors_value}|" "$tmp" > "${tmp}.2"
    mv "${tmp}.2" "$tmp"
  else
    printf '\nCORS_ALLOWED_ORIGINS=%s\n' "$cors_value" >> "$tmp"
  fi

  mv "$tmp" "$env_file"
  echo "Backend env ports → FRONTEND_LINK=${frontend_origin}"
}

# Kill whatever is listening on a TCP port: TERM first, then KILL.
kill_port() {
  local port="$1"
  local pids
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

# Kill a tracked pid (and its children) recorded in a pid file.
kill_pidfile() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 0
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    pkill -P "$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$pid_file"
}

# Terminate any prior SnipKlip processes, whether tracked or stray.
stop_services() {
  kill_pidfile "$PID_DIR/frontend.pid"
  kill_pidfile "$PID_DIR/backend.pid"

  # Stray servers for the configured ports only (avoid killing unrelated apps).
  pkill -f "manage.py runserver ${BACKEND_HOST}:${BACKEND_PORT}" 2>/dev/null || true
  pkill -f "manage.py runserver 127.0.0.1:${BACKEND_PORT}" 2>/dev/null || true
  pkill -f "manage.py runserver 0.0.0.0:${BACKEND_PORT}" 2>/dev/null || true
  pkill -f "next dev -p ${FRONTEND_PORT}" 2>/dev/null || true
  pkill -f "node_modules/next/dist/bin/next dev -p ${FRONTEND_PORT}" 2>/dev/null || true

  kill_port "$BACKEND_PORT"
  kill_port "$FRONTEND_PORT"
  # Legacy ports from older scripts.
  kill_port 8000
  kill_port 8081
}

prepare_backend() {
  require_dir "Backend" "$BACKEND_DIR"
  [[ -f "$BACKEND_DIR/manage.py" ]] || die "manage.py missing in $BACKEND_DIR"
  [[ -n "${VENV_ACTIVATE:-}" && -f "$VENV_ACTIVATE" ]] || die "Python venv missing"
  sync_backend_env_ports

  (
    cd "$BACKEND_DIR"
    # shellcheck disable=SC1091
    source "$VENV_ACTIVATE"
    export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-app.settings.local}"
    export FRONTEND_LINK="${FRONTEND_LINK:-http://localhost:${FRONTEND_PORT}}"
    export CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}}"
    python scripts/init_db.py --settings="$DJANGO_SETTINGS_MODULE"
    python manage.py migrate --noinput --settings="$DJANGO_SETTINGS_MODULE"
    python manage.py check --settings="$DJANGO_SETTINGS_MODULE"
  )
}

start_backend() {
  prepare_backend

  (
    cd "$BACKEND_DIR"
    # shellcheck disable=SC1091
    source "$VENV_ACTIVATE"
    export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-app.settings.local}"
    export FRONTEND_LINK="${FRONTEND_LINK:-http://localhost:${FRONTEND_PORT}}"
    export CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}}"
    # Disable autoreloader so the tracked PID is the process that owns the port.
    exec python manage.py runserver "${BACKEND_HOST}:${BACKEND_PORT}" --noreload --settings="$DJANGO_SETTINGS_MODULE"
  ) >"$LOG_DIR/backend.log" 2>&1 &
  echo $! >"$PID_DIR/backend.pid"
  echo "Backend starting (pid $(cat "$PID_DIR/backend.pid")) → http://${BACKEND_URL_HOST}:${BACKEND_PORT}"
}

ensure_frontend_deps() {
  if [[ ! -x "$FRONTEND_DIR/node_modules/next/dist/bin/next" ]]; then
    echo "Installing frontend dependencies..."
    (cd "$FRONTEND_DIR" && npm install --legacy-peer-deps)
  fi
  [[ -x "$FRONTEND_DIR/node_modules/next/dist/bin/next" ]] || die "Next.js binary missing after npm install"
}

# Resolve a Node 18 binary Next.js 12 can run under (host may be Node 20+/26).
# Echoes the path on success; returns 1 on failure (never call die from here —
# this function is used inside command substitution).
resolve_node18() {
  local major
  major="$(node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0)"
  if [[ "$major" == "18" ]]; then
    command -v node
    return 0
  fi

  local arch node_arch node_ver prefix bin tarball url
  arch="$(uname -m)"
  if [[ "$arch" == "arm64" ]]; then
    node_arch="arm64"
  else
    node_arch="x64"
  fi
  node_ver="v18.20.8"
  prefix="$LOG_DIR/node18/node-${node_ver}-darwin-${node_arch}"
  bin="$prefix/bin/node"

  if [[ -x "$bin" ]]; then
    echo "$bin"
    return 0
  fi

  echo "Host Node is $(node -v); downloading portable Node ${node_ver} for Next.js 12..." >&2
  mkdir -p "$LOG_DIR/node18"
  tarball="$LOG_DIR/node18/node-${node_ver}-darwin-${node_arch}.tar.gz"
  url="https://nodejs.org/dist/${node_ver}/node-${node_ver}-darwin-${node_arch}.tar.gz"
  if ! curl -fsSL "$url" -o "$tarball"; then
    echo "Failed to download $url" >&2
    return 1
  fi
  if ! tar -xzf "$tarball" -C "$LOG_DIR/node18"; then
    echo "Failed to extract $tarball" >&2
    return 1
  fi
  [[ -x "$bin" ]] || return 1
  echo "$bin"
}

start_frontend() {
  require_dir "Frontend" "$FRONTEND_DIR"
  ensure_frontend_env
  ensure_frontend_deps

  local node_bin
  if ! node_bin="$(resolve_node18)"; then
    die "Could not resolve a Node 18 binary for Next.js"
  fi

  (
    cd "$FRONTEND_DIR"
    echo "Using Node $($node_bin -v) for Next.js." >&2
    exec "$node_bin" node_modules/next/dist/bin/next dev -p "$FRONTEND_PORT"
  ) >"$LOG_DIR/frontend.log" 2>&1 &
  echo $! >"$PID_DIR/frontend.pid"
  echo "Frontend starting (pid $(cat "$PID_DIR/frontend.pid")) → http://localhost:${FRONTEND_PORT}"
}

# Start backend, verify, and self-heal common failures across attempts.
start_backend_resilient() {
  local attempts="${MAX_ATTEMPTS:-3}"
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    echo "Backend start attempt ${attempt}/${attempts}..."
    kill_pidfile "$PID_DIR/backend.pid"
    kill_port "$BACKEND_PORT"

    if ! start_backend; then
      echo "Backend prepare/start failed. Recent log:" >&2
      tail -n 20 "$LOG_DIR/backend.log" >&2 || true
      continue
    fi

    if wait_for_http "Django schema" "http://${BACKEND_URL_HOST}:${BACKEND_PORT}/api/schema/" "200" 90; then
      write_listener_pid backend "$BACKEND_PORT"
      return 0
    fi

    echo "Backend did not become healthy. Recent log:" >&2
    tail -n 20 "$LOG_DIR/backend.log" >&2 || true
    kill_pidfile "$PID_DIR/backend.pid"
    kill_port "$BACKEND_PORT"

    if grep -qiE "no module named|importerror" "$LOG_DIR/backend.log" 2>/dev/null; then
      echo "Detected missing Python dependency; reinstalling requirements..." >&2
      (
        cd "$BACKEND_DIR"
        # shellcheck disable=SC1091
        source "$VENV_ACTIVATE"
        [[ -f requirements.txt ]] && pip install -r requirements.txt >/dev/null 2>&1 || true
      ) || true
    fi
    sleep 2
  done
  return 1
}

# Start frontend, verify, and self-heal common failures across attempts.
start_frontend_resilient() {
  local attempts="${MAX_ATTEMPTS:-3}"
  for ((attempt = 1; attempt <= attempts; attempt++)); do
    echo "Frontend start attempt ${attempt}/${attempts}..."
    kill_pidfile "$PID_DIR/frontend.pid"
    kill_port "$FRONTEND_PORT"

    start_frontend
    if wait_for_http "Next.js login" "http://${FRONTEND_HOST}:${FRONTEND_PORT}/login" "200" 180; then
      write_listener_pid frontend "$FRONTEND_PORT"
      return 0
    fi

    echo "Frontend did not become healthy. Recent log:" >&2
    tail -n 20 "$LOG_DIR/frontend.log" >&2 || true
    kill_pidfile "$PID_DIR/frontend.pid"
    kill_port "$FRONTEND_PORT"

    if grep -qiE "cannot find module|module_not_found|next: not found" "$LOG_DIR/frontend.log" 2>/dev/null \
       || [[ ! -x "$FRONTEND_DIR/node_modules/next/dist/bin/next" ]]; then
      echo "Detected missing frontend dependency; reinstalling node_modules..." >&2
      (cd "$FRONTEND_DIR" && npm install --legacy-peer-deps) || true
    fi
    sleep 2
  done
  return 1
}

print_status() {
  local backend_pids frontend_pids
  backend_pids="$(port_pids "$BACKEND_PORT" | tr '\n' ' ')"
  frontend_pids="$(port_pids "$FRONTEND_PORT" | tr '\n' ' ')"

  if [[ -n "${backend_pids// }" ]]; then
    echo "backend: running (port ${BACKEND_PORT}, pid ${backend_pids})"
  else
    echo "backend: stopped"
  fi

  if [[ -n "${frontend_pids// }" ]]; then
    echo "frontend: running (port ${FRONTEND_PORT}, pid ${frontend_pids})"
  else
    echo "frontend: stopped"
  fi
}

# Keep the launcher alive while both service ports stay listening.
# Transient HTTP 000 during Next.js recompiles must not kill the stack.
supervise_services() {
  while true; do
    if ! service_running "$BACKEND_PORT"; then
      echo "Backend listener on :${BACKEND_PORT} is gone." >&2
      tail -n 20 "$LOG_DIR/backend.log" >&2 || true
      return 1
    fi
    if ! service_running "$FRONTEND_PORT"; then
      echo "Frontend listener on :${FRONTEND_PORT} is gone." >&2
      tail -n 20 "$LOG_DIR/frontend.log" >&2 || true
      return 1
    fi
    write_listener_pid backend "$BACKEND_PORT"
    write_listener_pid frontend "$FRONTEND_PORT"
    sleep 5
  done
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [start|stop|status|restart]

Starts SnipKlip Django (:${BACKEND_PORT}) and Next.js (:${FRONTEND_PORT}) together.

Paths:
  backend:  ${BACKEND_DIR:-<not found>}
  frontend: ${FRONTEND_DIR:-<not found>}
  logs:     $LOG_DIR
EOF
}

cmd="${1:-start}"

case "$cmd" in
  -h|--help|help)
    usage
    exit 0
    ;;
  stop)
    stop_services
    echo "Stopped SnipKlip services."
    exit 0
    ;;
  status)
    print_status
    exit 0
    ;;
  restart)
    stop_services
    ;;
  start)
    ;;
  *)
    usage
    exit 1
    ;;
esac

require_dir "Backend" "$BACKEND_DIR"
[[ -n "${FRONTEND_DIR:-}" ]] || die "Frontend not found. Set FRONTEND_DIR=/path/to/snipklip-frontend"
require_dir "Frontend" "$FRONTEND_DIR"

echo "Cleaning up any existing SnipKlip processes..."
stop_services

on_error() {
  local code=$?
  echo "Startup failed. Stopping services..." >&2
  stop_services
  exit "$code"
}
trap on_error EXIT
trap 'echo; echo "Stopping..."; stop_services; exit 0' INT TERM

start_backend_resilient || die "Backend failed to start after ${MAX_ATTEMPTS:-3} attempts. See $LOG_DIR/backend.log"
start_frontend_resilient || die "Frontend failed to start after ${MAX_ATTEMPTS:-3} attempts. See $LOG_DIR/frontend.log"

# Keep services up after successful boot; only stop on Ctrl+C / kill.
trap - EXIT
trap 'echo; echo "Stopping..."; stop_services; exit 0' INT TERM

cat <<EOF

SnipKlip is running:
  Backend:  http://${BACKEND_URL_HOST}:${BACKEND_PORT}
  Schema:   http://${BACKEND_URL_HOST}:${BACKEND_PORT}/api/schema/
  Frontend: http://localhost:${FRONTEND_PORT}
  Register: http://localhost:${FRONTEND_PORT}/register
  Logs:     $LOG_DIR/backend.log
            $LOG_DIR/frontend.log

Press Ctrl+C to stop both services.
EOF

supervise_services
echo "A service exited. Stopping remaining processes..." >&2
stop_services
exit 1
