#!/usr/bin/env python3
"""
Cross-platform local bootstrap for SnipKlip.

Creates/updates .venv, installs requirements, ensures .env files exist,
and prints resolved paths/ports. Safe to re-run.
"""
from __future__ import annotations

import argparse
import os
import platform
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND_PORT = "8082"
FRONTEND_PORT = "8083"


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None, env=env)


def find_backend(start: Path) -> Path:
    candidates = [
        start,
        start / "SnipKlip",
        start.parent / "SnipKlip",
        start.parent.parent / "SnipKlip",
    ]
    for c in candidates:
        if (c / "manage.py").is_file():
            return c.resolve()
    die("Backend not found (manage.py). Clone Wankhede/SnipKlip and re-run.")


def find_frontend(start: Path, backend: Path) -> Path | None:
    candidates = [
        Path(os.environ["FRONTEND_DIR"]) if os.environ.get("FRONTEND_DIR") else None,
        start / "snipklip-frontend",
        start.parent / "snipklip-frontend",
        backend.parent / "snipklip-frontend",
        backend.parent.parent / "snipklip-frontend",
        Path.home() / "snipklip-frontend",
    ]
    for c in candidates:
        if c and (c / "package.json").is_file():
            return c.resolve()
    return None


def venv_python(venv: Path) -> Path:
    if platform.system() == "Windows":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def ensure_venv(backend: Path, venv: Path) -> Path:
    py = venv_python(venv)
    if not py.is_file():
        print(f"Creating virtualenv at {venv}")
        # Prefer the interpreter running this script
        run([sys.executable, "-m", "venv", str(venv)])
        py = venv_python(venv)
    if not py.is_file():
        die(f"Failed to create venv python at {py}")
    return py


def ensure_backend_env(backend: Path) -> None:
    example = backend / ".env.example"
    env_file = backend / ".env"
    if not example.is_file():
        die(f"Missing {example}")
    if not env_file.is_file():
        shutil.copyfile(example, env_file)
        print(f"Created {env_file} from .env.example")
    # Keep reserved ports wired
    text = env_file.read_text(encoding="utf-8")
    replacements = {
        "FRONTEND_LINK=": f"FRONTEND_LINK=http://localhost:{FRONTEND_PORT}",
        "CORS_ALLOWED_ORIGINS=": (
            f"CORS_ALLOWED_ORIGINS=http://localhost:{FRONTEND_PORT},"
            f"http://127.0.0.1:{FRONTEND_PORT},http://localhost:3000,http://127.0.0.1:3000"
        ),
        "BACKEND_PORT=": f"BACKEND_PORT={BACKEND_PORT}",
    }
    lines = []
    seen = set()
    for line in text.splitlines():
        key = line.split("=", 1)[0] + "=" if "=" in line and not line.strip().startswith("#") else None
        if key and key in replacements:
            lines.append(replacements[key])
            seen.add(key)
        else:
            lines.append(line)
    for key, value in replacements.items():
        if key not in seen:
            lines.append(value)
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_frontend_env(frontend: Path) -> None:
    example = frontend / ".env.example"
    env_file = frontend / ".env.local"
    if not example.is_file():
        die(f"Missing {example}")
    if not env_file.is_file():
        content = example.read_text(encoding="utf-8")
        content = content.replace(
            "NEXTAUTH_SECRET=replace-with-a-new-random-secret",
            f"NEXTAUTH_SECRET={secrets.token_urlsafe(32)}",
        )
        content = content.replace(
            "JWT_SECRET=replace-with-a-new-random-secret",
            f"JWT_SECRET={secrets.token_urlsafe(32)}",
        )
        env_file.write_text(content, encoding="utf-8")
        print(f"Created {env_file} with generated secrets")

    text = env_file.read_text(encoding="utf-8")
    replacements = {
        "NEXT_PUBLIC_BACKEND_URL=": f"NEXT_PUBLIC_BACKEND_URL=http://localhost:{BACKEND_PORT}/",
        "NEXT_PUBLIC_FRONTEND_URL=": f"NEXT_PUBLIC_FRONTEND_URL=http://localhost:{FRONTEND_PORT}/",
        "NEXTAUTH_URL=": f"NEXTAUTH_URL=http://localhost:{FRONTEND_PORT}/",
        "PORT=": f"PORT={FRONTEND_PORT}",
    }
    lines = []
    seen = set()
    for line in text.splitlines():
        key = line.split("=", 1)[0] + "=" if "=" in line and not line.strip().startswith("#") else None
        if key and key in replacements:
            lines.append(replacements[key])
            seen.add(key)
        else:
            lines.append(line)
    for key, value in replacements.items():
        if key not in seen:
            lines.append(value)
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap SnipKlip local environment")
    parser.add_argument("--skip-pip", action="store_true")
    parser.add_argument("--skip-npm", action="store_true")
    args = parser.parse_args()

    start = Path.cwd()
    backend = find_backend(start)
    frontend = find_frontend(start, backend)

    # Prefer workspace-level .venv next to backend parent (SnipKlip/.venv), else backend/.venv
    parent_venv = backend.parent / ".venv"
    local_venv = backend / ".venv"
    venv = parent_venv if parent_venv.exists() or not local_venv.exists() else local_venv
    if not parent_venv.exists() and not local_venv.exists():
        venv = parent_venv if (backend.parent / "snipklip-frontend").exists() or (backend.parent.name.lower() != "snipklip") else local_venv
        # Default: create beside backend for portable Windows clones
        venv = local_venv

    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 9):
        die(f"Python {major}.{minor} is too old. Install Python 3.10 or 3.11.")
    if (major, minor) >= (3, 12):
        print(
            f"WARNING: Python {major}.{minor} is newer than Django 3.2 officially supports. "
            "Prefer Python 3.10 or 3.11 for fewest surprises."
        )

    py = ensure_venv(backend, venv)
    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    if not args.skip_pip:
        req = backend / "requirements.txt"
        if not req.is_file():
            die(f"Missing {req}")
        run([str(py), "-m", "pip", "install", "-r", str(req)])

    ensure_backend_env(backend)

    if frontend:
        ensure_frontend_env(frontend)
        if not args.skip_npm:
            npm = shutil.which("npm")
            if not npm:
                die("npm not found. Install Node.js 18 LTS from https://nodejs.org/")
            node_modules = frontend / "node_modules" / "next"
            if not node_modules.exists():
                print("Installing frontend dependencies (npm install --legacy-peer-deps)...")
                run([npm, "install", "--legacy-peer-deps"], cwd=frontend)
            else:
                print("Frontend node_modules present — skipping npm install.")
    else:
        print(
            "WARNING: Frontend repo not found. Clone "
            "https://github.com/Wankhede/SnipKlip-frontend.git as a sibling "
            "folder named snipklip-frontend (or set FRONTEND_DIR)."
        )

    print()
    print("Bootstrap complete.")
    print(f"  Backend:  {backend}")
    print(f"  Frontend: {frontend or '<missing>'}")
    print(f"  Venv:     {venv}")
    print(f"  Python:   {py}")
    print(f"  Ports:    backend={BACKEND_PORT}  frontend={FRONTEND_PORT}")


if __name__ == "__main__":
    main()
