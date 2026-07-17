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

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-8081}"

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

wait_for_http() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local attempts="${4:-60}"
  local status=""

  for ((i = 1; i <= attempts; i++)); do
    status="$(curl --silent --output /dev/null --write-out '%{http_code}' "$url" 2>/dev/null || true)"
    if [[ "$status" == "$expected" ]]; then
      echo "PASS $name ($status) $url"
      return 0
    fi
    sleep 1
  done

  echo "FAIL $name: expected $expected, got ${status:-none} ($url)" >&2
  return 1
}

ensure_frontend_env() {
  local env_file="$FRONTEND_DIR/.env.local"
  if [[ -f "$env_file" ]]; then
    return 0
  fi

  [[ -f "$FRONTEND_DIR/.env.example" ]] || die "Missing frontend .env.example"

  local nextauth_secret jwt_secret
  nextauth_secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  jwt_secret="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

  sed \
    -e "s|^NEXT_PUBLIC_BACKEND_URL=.*|NEXT_PUBLIC_BACKEND_URL=http://${BACKEND_HOST}:${BACKEND_PORT}/|" \
    -e "s|^NEXT_PUBLIC_FRONTEND_URL=.*|NEXT_PUBLIC_FRONTEND_URL=http://localhost:${FRONTEND_PORT}/|" \
    -e "s|^NEXTAUTH_URL=.*|NEXTAUTH_URL=http://localhost:${FRONTEND_PORT}/|" \
    -e "s|^NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=${nextauth_secret}|" \
    -e "s|^JWT_SECRET=.*|JWT_SECRET=${jwt_secret}|" \
    "$FRONTEND_DIR/.env.example" > "$env_file"

  echo "Created $env_file with local secrets."
}

stop_services() {
  local backend_pid="" frontend_pid=""
  [[ -f "$PID_DIR/backend.pid" ]] && backend_pid="$(cat "$PID_DIR/backend.pid" 2>/dev/null || true)"
  [[ -f "$PID_DIR/frontend.pid" ]] && frontend_pid="$(cat "$PID_DIR/frontend.pid" 2>/dev/null || true)"

  if [[ -n "${frontend_pid:-}" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    kill "$frontend_pid" 2>/dev/null || true
    pkill -P "$frontend_pid" 2>/dev/null || true
    wait "$frontend_pid" 2>/dev/null || true
  fi
  if [[ -n "${backend_pid:-}" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid" 2>/dev/null || true
    pkill -P "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
  fi

  # Free ports if a stale listener remains.
  for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
    local pids
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
    fi
  done

  rm -f "$PID_DIR/backend.pid" "$PID_DIR/frontend.pid"
}

start_backend() {
  require_dir "Backend" "$BACKEND_DIR"
  [[ -f "$BACKEND_DIR/manage.py" ]] || die "manage.py missing in $BACKEND_DIR"
  [[ -n "${VENV_ACTIVATE:-}" && -f "$VENV_ACTIVATE" ]] || die "Python venv missing"

  (
    cd "$BACKEND_DIR"
    # shellcheck disable=SC1091
    source "$VENV_ACTIVATE"
    export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-app.settings.local}"
    python scripts/init_db.py --settings="$DJANGO_SETTINGS_MODULE"
    python manage.py migrate --noinput --settings="$DJANGO_SETTINGS_MODULE"
    python manage.py check --settings="$DJANGO_SETTINGS_MODULE"
    exec python manage.py runserver "${BACKEND_HOST}:${BACKEND_PORT}" --settings="$DJANGO_SETTINGS_MODULE"
  ) >"$LOG_DIR/backend.log" 2>&1 &
  echo $! >"$PID_DIR/backend.pid"
  echo "Backend starting (pid $(cat "$PID_DIR/backend.pid")) → http://${BACKEND_HOST}:${BACKEND_PORT}"
}

ensure_frontend_deps() {
  if [[ ! -x "$FRONTEND_DIR/node_modules/next/dist/bin/next" ]]; then
    echo "Installing frontend dependencies..."
    (cd "$FRONTEND_DIR" && npm install --legacy-peer-deps)
  fi
  [[ -x "$FRONTEND_DIR/node_modules/next/dist/bin/next" ]] || die "Next.js binary missing after npm install"
}

start_frontend() {
  require_dir "Frontend" "$FRONTEND_DIR"
  ensure_frontend_env
  ensure_frontend_deps

  (
    cd "$FRONTEND_DIR"
    NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0)"
    if [[ "$NODE_MAJOR" == "18" ]]; then
      exec npm run dev -- -p "$FRONTEND_PORT"
    else
      echo "Host Node is $(node -v); using portable Node 18 for Next.js 12." >&2
      exec npm exec --yes --package=node@18 -- node node_modules/next/dist/bin/next dev -p "$FRONTEND_PORT"
    fi
  ) >"$LOG_DIR/frontend.log" 2>&1 &
  echo $! >"$PID_DIR/frontend.pid"
  echo "Frontend starting (pid $(cat "$PID_DIR/frontend.pid")) → http://localhost:${FRONTEND_PORT}"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [start|stop|status|restart]

Starts SnipKlip Django (:${BACKEND_PORT}) and Next.js (:${FRONTEND_PORT}) together.

Paths:
  backend:  $BACKEND_DIR
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
    for name in backend frontend; do
      if [[ -f "$PID_DIR/${name}.pid" ]] && kill -0 "$(cat "$PID_DIR/${name}.pid")" 2>/dev/null; then
        echo "$name: running (pid $(cat "$PID_DIR/${name}.pid"))"
      else
        echo "$name: stopped"
      fi
    done
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

stop_services

on_error() {
  local code=$?
  echo "Startup failed. Stopping services..." >&2
  stop_services
  exit "$code"
}
trap on_error EXIT
trap 'echo; echo "Stopping..."; stop_services; exit 0' INT TERM

start_backend
wait_for_http "Django schema" "http://${BACKEND_HOST}:${BACKEND_PORT}/api/schema/" "200" 90

start_frontend
wait_for_http "Next.js login" "http://${FRONTEND_HOST}:${FRONTEND_PORT}/login" "200" 180

# Keep services up after successful boot; only stop on Ctrl+C / kill.
trap - EXIT
trap 'echo; echo "Stopping..."; stop_services; exit 0' INT TERM

cat <<EOF

SnipKlip is running:
  Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}
  Frontend: http://localhost:${FRONTEND_PORT}
  Register: http://localhost:${FRONTEND_PORT}/register
  Logs:     $LOG_DIR/backend.log
            $LOG_DIR/frontend.log

Press Ctrl+C to stop both services.
EOF

wait
