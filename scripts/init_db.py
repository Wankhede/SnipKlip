#!/usr/bin/env python3
"""
Idempotent database initialization for SnipKlip.

- SQLite (local): ensures the database file path exists; never drops data.
- PostgreSQL: creates the database only when it does not already exist.

Usage:
    python scripts/init_db.py [--settings app.settings.local]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Initialize SnipKlip database if missing."
    )
    parser.add_argument(
        "--settings",
        default=os.getenv("DJANGO_SETTINGS_MODULE", "app.settings.local"),
        help="Django settings module (default: app.settings.local)",
    )
    return parser.parse_args()


def ensure_sqlite_database(db_path: Path) -> bool:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        print(f"already correct: SQLite database exists at {db_path}")
        return False
    db_path.touch()
    print(f"created: empty SQLite database at {db_path}")
    return True


def ensure_postgres_database(
    db_name: str, db_user: str, db_password: str, db_host: str, db_port: str
) -> bool:
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError as exc:
        raise SystemExit("psycopg2 is required for PostgreSQL initialization") from exc

    connect_kwargs = {"host": db_host, "port": db_port, "user": db_user}
    if db_password:
        connect_kwargs["password"] = db_password

    admin_conn = psycopg2.connect(dbname="postgres", **connect_kwargs)
    admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with admin_conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cursor.fetchone():
                print(f'already correct: PostgreSQL database "{db_name}" exists')
                return False
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f'created: PostgreSQL database "{db_name}"')
            return True
    finally:
        admin_conn.close()


def run_migrations(settings_module: str) -> None:
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = settings_module
    subprocess.run(
        [
            sys.executable,
            "manage.py",
            "migrate",
            "--noinput",
            f"--settings={settings_module}",
        ],
        cwd=PROJECT_ROOT,
        check=True,
        env=env,
    )


def main():
    args = parse_args()
    os.environ["DJANGO_SETTINGS_MODULE"] = args.settings

    import django

    django.setup()
    from django.conf import settings

    db = settings.DATABASES["default"]
    engine = db.get("ENGINE", "")
    created = False

    if "sqlite3" in engine:
        db_path = Path(db["NAME"])
        created = ensure_sqlite_database(db_path)
    elif "postgresql" in engine:
        created = ensure_postgres_database(
            db_name=db["NAME"],
            db_user=db.get("USER", ""),
            db_password=db.get("PASSWORD", ""),
            db_host=db.get("HOST", "127.0.0.1"),
            db_port=str(db.get("PORT", "5432")),
        )
    else:
        print(f"skip: unsupported database engine {engine}")
        return

    if created:
        print("running migrations...")
        run_migrations(args.settings)
    else:
        print(
            "no database creation needed; run manage.py migrate separately if schema is pending"
        )


if __name__ == "__main__":
    main()
