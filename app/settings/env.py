import os
from pathlib import Path


def load_env_file(env_file=None):
    env_path = Path(env_file) if env_file else Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return False

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return True


def get_env(name, default=None, cast=None):
    value = os.getenv(name, default)
    if value is None:
        return None
    if cast is None:
        return value
    if cast is bool:
        if isinstance(value, bool):
            return value
        if str(value).strip().lower() in {"1", "true", "yes", "on"}:
            return True
        if str(value).strip().lower() in {"0", "false", "no", "off", ""}:
            return False
        return bool(value)
    if cast is int:
        return int(value)
    if cast is float:
        return float(value)
    return cast(value)


load_env_file()
