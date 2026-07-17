"""
Shared helpers for loading encryption keys from environment configuration.
"""
from pathlib import Path

from django.conf import settings


def load_fernet_key() -> bytes:
    inline_key = getattr(settings, 'FERNET_KEY', '')
    if inline_key:
        return inline_key.encode('utf-8') if isinstance(inline_key, str) else inline_key

    key_path = Path(getattr(settings, 'FERNET_KEY_FILE', 'secret.key'))
    if not key_path.is_absolute():
        key_path = Path(settings.BASE_DIR) / key_path
    return key_path.read_bytes()
