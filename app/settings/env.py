import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]
env = environ.Env(
    DEBUG=(bool, False),
    CORS_ALLOW_ALL_ORIGINS=(bool, True),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_USE_OAUTH2=(bool, True),
    SECURE_SSL_REDIRECT=(bool, False),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    SECURE_HSTS_SECONDS=(int, 0),
    SERVER=(int, 0),
    FTP=(bool, False),
    EMAIL_PORT=(int, 587),
)

env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)


def get_env(name, default=None, cast=None):
    """Backward-compatible env accessor used across settings and config modules."""
    if cast is None:
        return env(name, default=default)
    if cast is bool:
        return env.bool(name, default=default if default is not None else False)
    if cast is int:
        return env.int(name, default=default if default is not None else 0)
    if cast is float:
        return env.float(name, default=default if default is not None else 0.0)
    return cast(env(name, default=default))


def load_env_file(env_file_path=None):
    path = Path(env_file_path) if env_file_path else BASE_DIR / '.env'
    if path.exists():
        environ.Env.read_env(path)
        return True
    return False
