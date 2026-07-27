@echo off
setlocal EnableExtensions
REM ============================================================================
REM  SnipKlip Windows single-click launcher
REM  Backend  http://localhost:8082
REM  Frontend http://localhost:8083
REM  Usage: run-local.bat [start|stop|status|restart]
REM ============================================================================
cd /d "%~dp0"

where powershell >nul 2>&1
if errorlevel 1 (
  echo ERROR: PowerShell was not found on PATH.
  echo Install Windows PowerShell 5.1+ or PowerShell 7: https://aka.ms/powershell
  exit /b 1
)

REM Ensure common tool paths are visible even if the user opened a stale terminal
set "PATH=%LocalAppData%\Programs\Python\Python311;%LocalAppData%\Programs\Python\Python311\Scripts;%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%ProgramFiles%\nodejs;%PATH%"

set "CMD=%~1"
if "%CMD%"=="" set "CMD=start"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-local.ps1" -Command %CMD%
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" (
  echo.
  echo Launcher exited with code %EC%. See .run\backend.log and .run\frontend.log
)
exit /b %EC%
