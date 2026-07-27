#Requires -Version 5.1
<#
.SYNOPSIS
  Single-click SnipKlip local launcher for Windows.

.DESCRIPTION
  Bootstraps Python venv + npm deps, then starts:
    Backend  (Django)  http://127.0.0.1:8082
    Frontend (Next.js) http://localhost:8083

.NOTES
  Clone layout (siblings):
    parent\
      SnipKlip\              <- this repo (backend)
      snipklip-frontend\     <- frontend repo
#>
[CmdletBinding()]
param(
  [ValidateSet("start", "stop", "status", "restart")]
  [string]$Command = "start"
)

$ErrorActionPreference = "Stop"
$BackendPort = 8082
$FrontendPort = 8083
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = $ScriptRoot
if (-not (Test-Path (Join-Path $BackendDir "manage.py"))) {
  Write-Error "Run this script from the SnipKlip backend repo root (manage.py missing)."
}

function Resolve-FrontendDir {
  $candidates = @(
    $env:FRONTEND_DIR,
    (Join-Path (Split-Path $BackendDir -Parent) "snipklip-frontend"),
    (Join-Path $BackendDir "snipklip-frontend"),
    (Join-Path $env:USERPROFILE "snipklip-frontend")
  ) | Where-Object { $_ }
  foreach ($c in $candidates) {
    if (Test-Path (Join-Path $c "package.json")) { return (Resolve-Path $c).Path }
  }
  return $null
}

$FrontendDir = Resolve-FrontendDir
$RunDir = Join-Path $BackendDir ".run"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$BackendLog = Join-Path $RunDir "backend.log"
$FrontendLog = Join-Path $RunDir "frontend.log"

function Test-CommandExists([string]$Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-PortOwner([int]$Port) {
  try {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conns) { return @($conns | Select-Object -ExpandProperty OwningProcess -Unique) }
  } catch { }
  # Fallback for older Windows / missing NetTCP module
  $lines = netstat -ano | Select-String ":$Port\s+.*LISTENING"
  $pids = @()
  foreach ($line in $lines) {
    if ($line -match "\s+(\d+)\s*$") { $pids += [int]$Matches[1] }
  }
  return $pids | Select-Object -Unique
}

function Stop-Port([int]$Port) {
  $pids = Get-PortOwner $Port
  foreach ($procId in $pids) {
    if ($procId -and $procId -ne 0) {
      Write-Host "  freeing port $Port (pid $procId)"
      Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
  }
}

function Wait-Http([string]$Name, [string]$Url, [int]$Expected = 200, [int]$Attempts = 90) {
  for ($i = 1; $i -le $Attempts; $i++) {
    try {
      $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
      if ([int]$resp.StatusCode -eq $Expected) {
        Write-Host "PASS $Name ($Expected) $Url"
        return $true
      }
    } catch { }
    Start-Sleep -Seconds 1
  }
  Write-Host "FAIL $Name expected $Expected at $Url"
  return $false
}

function Assert-Prereqs {
  if (-not (Test-CommandExists "python")) {
    Write-Host @"
ERROR: Python not found on PATH.
Install Python 3.10 or 3.11 (recommended): https://www.python.org/downloads/
Tick "Add python.exe to PATH" during setup, then reopen this terminal.
"@
    exit 1
  }
  if (-not (Test-CommandExists "node") -or -not (Test-CommandExists "npm")) {
    Write-Host @"
ERROR: Node.js / npm not found on PATH.
Install Node.js 18 LTS: https://nodejs.org/en/download
Then reopen this terminal.
"@
    exit 1
  }
  $nodeMajor = [int]((node -p "process.versions.node.split('.')[0]").Trim())
  if ($nodeMajor -ne 18) {
    Write-Host "WARNING: Host Node is $(node -v). Next.js 12 works best on Node 18 LTS."
    Write-Host "         Install Node 18 from https://nodejs.org/ (or use nvm-windows)."
  }
}

function Invoke-Bootstrap {
  Assert-Prereqs
  if (-not $FrontendDir) {
    Write-Host @"
ERROR: Frontend repo not found.
Clone it as a sibling folder:
  git clone https://github.com/Wankhede/SnipKlip-frontend.git snipklip-frontend
Expected next to:
  $BackendDir
Or set FRONTEND_DIR to the absolute path.
"@
    exit 1
  }
  Write-Host "Bootstrapping environment..."
  Push-Location $BackendDir
  try {
    python scripts\bootstrap_env.py
  } finally {
    Pop-Location
  }
}

function Get-VenvPython {
  $candidates = @(
    (Join-Path $BackendDir ".venv\Scripts\python.exe"),
    (Join-Path (Split-Path $BackendDir -Parent) ".venv\Scripts\python.exe")
  )
  foreach ($c in $candidates) {
    if (Test-Path $c) { return $c }
  }
  Write-Error "Virtualenv python not found. Bootstrap failed."
}

function Start-Backend {
  $py = Get-VenvPython
  Stop-Port $BackendPort
  $cmd = @"
`$ErrorActionPreference='Continue'
Set-Location '$BackendDir'
`$env:DJANGO_SETTINGS_MODULE='app.settings.local'
`$env:FRONTEND_LINK='http://localhost:$FrontendPort'
`$env:CORS_ALLOWED_ORIGINS='http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort'
& '$py' scripts\init_db.py --settings=app.settings.local
& '$py' manage.py migrate --noinput --settings=app.settings.local
& '$py' manage.py runserver 0.0.0.0:$BackendPort --noreload --settings=app.settings.local *>> '$BackendLog'
"@
  $proc = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd) -WindowStyle Minimized -PassThru
  Set-Content -Path (Join-Path $RunDir "backend.pid") -Value $proc.Id
  Write-Host "Backend starting (pid $($proc.Id)) → http://127.0.0.1:$BackendPort"
}

function Start-Frontend {
  Stop-Port $FrontendPort
  $cmd = @"
`$ErrorActionPreference='Continue'
Set-Location '$FrontendDir'
npm run dev *>> '$FrontendLog'
"@
  # Prefer npx node@18 when host node is not 18
  $nodeMajor = [int]((node -p "process.versions.node.split('.')[0]").Trim())
  if ($nodeMajor -ne 18) {
    $cmd = @"
`$ErrorActionPreference='Continue'
Set-Location '$FrontendDir'
npx --yes node@18 node_modules/next/dist/bin/next dev -p $FrontendPort *>> '$FrontendLog'
"@
  }
  $proc = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd) -WindowStyle Minimized -PassThru
  Set-Content -Path (Join-Path $RunDir "frontend.pid") -Value $proc.Id
  Write-Host "Frontend starting (pid $($proc.Id)) → http://localhost:$FrontendPort"
}

function Stop-All {
  Write-Host "Stopping SnipKlip services..."
  Stop-Port $BackendPort
  Stop-Port $FrontendPort
  foreach ($name in @("backend.pid", "frontend.pid")) {
    $pidFile = Join-Path $RunDir $name
    if (Test-Path $pidFile) {
      $procId = Get-Content $pidFile | Select-Object -First 1
      if ($procId) { Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue }
      Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
  }
}

function Show-Status {
  $b = Get-PortOwner $BackendPort
  $f = Get-PortOwner $FrontendPort
  if ($b) { Write-Host "backend:  running (port $BackendPort, pid $($b -join ','))" } else { Write-Host "backend:  stopped" }
  if ($f) { Write-Host "frontend: running (port $FrontendPort, pid $($f -join ','))" } else { Write-Host "frontend: stopped" }
}

switch ($Command) {
  "stop" { Stop-All; Show-Status; exit 0 }
  "status" { Show-Status; exit 0 }
  "restart" { Stop-All }
  "start" { }
}

Invoke-Bootstrap
Stop-All
Start-Backend
if (-not (Wait-Http "Django schema" "http://127.0.0.1:$BackendPort/api/schema/" 200 90)) {
  Write-Host "Backend log tail:"
  if (Test-Path $BackendLog) { Get-Content $BackendLog -Tail 40 }
  exit 1
}
Start-Frontend
if (-not (Wait-Http "Next.js login" "http://127.0.0.1:$FrontendPort/login" 200 180)) {
  Write-Host "Frontend log tail:"
  if (Test-Path $FrontendLog) { Get-Content $FrontendLog -Tail 40 }
  exit 1
}

Write-Host ""
Write-Host "SnipKlip is running:"
Write-Host "  Backend:  http://127.0.0.1:$BackendPort"
Write-Host "  Schema:   http://127.0.0.1:$BackendPort/api/schema/"
Write-Host "  Frontend: http://localhost:$FrontendPort"
Write-Host "  Register: http://localhost:$FrontendPort/register"
Write-Host "  Logs:     $RunDir"
Write-Host ""
Write-Host "Stop with:  .\run-local.ps1 stop"
Show-Status
