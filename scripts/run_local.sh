#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-app.settings.local}"

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
elif [[ -f "../.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "../.venv/bin/activate"
elif [[ -f "env/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "env/bin/activate"
elif [[ -f "venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "venv/bin/activate"
fi

python scripts/init_db.py --settings="$DJANGO_SETTINGS_MODULE"
python manage.py migrate --noinput --settings="$DJANGO_SETTINGS_MODULE"
python manage.py check --settings="$DJANGO_SETTINGS_MODULE"
python manage.py runserver 127.0.0.1:8082 --settings="$DJANGO_SETTINGS_MODULE"
