@echo off
setlocal EnableExtensions
REM SnipKlip Windows launcher — delegates to PowerShell for robust path/venv handling.
cd /d "%~dp0"
where powershell >nul 2>&1
if errorlevel 1 (
  echo ERROR: PowerShell is required. Install Windows PowerShell 5.1+ or PowerShell 7+.
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-local.ps1" %*
exit /b %ERRORLEVEL%
