#Requires -Version 5.1
<#
.SYNOPSIS
  Flawless single-click SnipKlip launcher for Windows (VS Code / PowerShell).

.DESCRIPTION
  On every start:
    1. Verifies Python + Node on PATH (clear download links if missing)
    2. Creates .venv if needed; always (re)installs Python + npm packages
    3. Writes .env / .env.local with localhost URLs
    4. Reclaims reserved ports 8082/8083 if another process holds them
    5. Starts Django + Next.js and health-checks via http://localhost:...

  Reserved ports (do not swap):
    Backend  (Django)  → http://localhost:8082
    Frontend (Next.js) → http://localhost:8083

.PARAMETER Command
  start | stop | status | restart

.EXAMPLE
  .\run-local.bat
  .\run-local.ps1 start
  .\run-local.ps1 stop
#>
[CmdletBinding()]
param(
  [Parameter(Position = 0)]
  [ValidateSet('start', 'stop', 'status', 'restart')]
  [string]$Command = 'start'
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ---- reserved ports ----
$BackendPort  = 8082
$FrontendPort = 8083
$PublicHost   = 'localhost'   # always advertise / call via localhost (not 127.0.0.1)
$BindHost     = '0.0.0.0'     # listen on all interfaces so localhost resolves cleanly

$ScriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$BackendDir = $ScriptRoot
if (-not (Test-Path (Join-Path $BackendDir 'manage.py'))) {
  Write-Host 'ERROR: Run from the SnipKlip backend repo root (manage.py missing).' -ForegroundColor Red
  exit 1
}

function Write-Step([string]$Msg) { Write-Host "==> $Msg" -ForegroundColor Cyan }
function Write-Ok([string]$Msg)   { Write-Host "OK  $Msg" -ForegroundColor Green }
function Write-Warn([string]$Msg) { Write-Host "WARN $Msg" -ForegroundColor Yellow }
function Die([string]$Msg) {
  Write-Host "ERROR: $Msg" -ForegroundColor Red
  exit 1
}

function Test-Cmd([string]$Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Resolve-PythonLauncher {
  # Prefer the Windows Python launcher, then python, then python3.
  if (Test-Cmd 'py') {
    try {
      $ver = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
      if ($ver) { return @{ Exe = 'py'; Args = @('-3') } }
    } catch { }
  }
  foreach ($name in @('python', 'python3')) {
    if (Test-Cmd $name) {
      return @{ Exe = $name; Args = @() }
    }
  }
  return $null
}

function Resolve-FrontendDir {
  $candidates = @(
    $env:FRONTEND_DIR,
    (Join-Path (Split-Path $BackendDir -Parent) 'snipklip-frontend'),
    (Join-Path $BackendDir 'snipklip-frontend'),
    (Join-Path (Split-Path $BackendDir -Parent) 'SnipKlip-frontend'),
    (Join-Path $env:USERPROFILE 'snipklip-frontend'),
    (Join-Path $env:USERPROFILE 'dev\snipklip-frontend')
  ) | Where-Object { $_ }
  foreach ($c in $candidates) {
    try {
      if (Test-Path (Join-Path $c 'package.json')) {
        return (Resolve-Path $c).Path
      }
    } catch { }
  }
  return $null
}

function Get-PortOwnerPids([int]$Port) {
  $pids = New-Object System.Collections.Generic.List[int]
  try {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in @($conns)) {
      if ($c.OwningProcess -and $c.OwningProcess -ne 0) { [void]$pids.Add([int]$c.OwningProcess) }
    }
  } catch { }

  if ($pids.Count -eq 0) {
    # netstat fallback (works without admin / NetTCP module)
    $lines = & netstat -ano 2>$null | Select-String -Pattern ":$Port\s+.*LISTENING"
    foreach ($line in $lines) {
      if ($line.Line -match '\s+(\d+)\s*$') {
        $id = [int]$Matches[1]
        if ($id -ne 0) { [void]$pids.Add($id) }
      }
    }
  }
  return @($pids | Select-Object -Unique)
}

function Claim-Port {
  param(
    [Parameter(Mandatory = $true)][int]$Port,
    [int]$Retries = 12
  )
  for ($i = 1; $i -le $Retries; $i++) {
    $owners = Get-PortOwnerPids $Port
    if (-not $owners -or $owners.Count -eq 0) {
      Write-Ok "Port $Port is free"
      return
    }
    foreach ($procId in $owners) {
      $name = ''
      try { $name = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName } catch { }
      Write-Warn "Port $Port occupied by pid $procId ($name) — reclaiming for SnipKlip"
      # taskkill /T kills the whole process tree (nested powershell → python/node)
      & taskkill.exe /F /T /PID $procId 2>$null | Out-Null
      Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 700
  }
  $still = Get-PortOwnerPids $Port
  if ($still -and $still.Count -gt 0) {
    Die "Could not free port $Port (still held by pid(s): $($still -join ',')). Close that app or reboot, then retry."
  }
}

function Wait-Http([string]$Name, [string]$Url, [int]$Expected = 200, [int]$Attempts = 120) {
  for ($i = 1; $i -le $Attempts; $i++) {
    try {
      # Force localhost DNS / avoid proxy surprises
      $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4 -MaximumRedirection 5
      if ([int]$resp.StatusCode -eq $Expected) {
        Write-Ok "$Name ($Expected) $Url"
        return $true
      }
    } catch {
      # keep polling
    }
    Start-Sleep -Seconds 1
  }
  Write-Host "FAIL $Name expected $Expected at $Url" -ForegroundColor Red
  return $false
}

function Assert-Prereqs {
  $py = Resolve-PythonLauncher
  if (-not $py) {
    Die @"
Python was not found on PATH.
Install Python 3.10 or 3.11 from https://www.python.org/downloads/
IMPORTANT: enable "Add python.exe to PATH", then close and reopen VS Code / PowerShell.
"@
  }
  if (-not (Test-Cmd 'node') -or -not (Test-Cmd 'npm')) {
    Die @"
Node.js / npm was not found on PATH.
Install Node.js 18 LTS from https://nodejs.org/en/download
Then close and reopen VS Code / PowerShell.
"@
  }

  $pyArgs = $py.Args + @('-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
  $pyVer = & $py.Exe @pyArgs
  $nodeVer = (& node -v).Trim()
  $npmVer = (& npm -v).Trim()
  Write-Ok "Python $pyVer | Node $nodeVer | npm $npmVer"

  $nodeMajor = [int]((& node -p "process.versions.node.split('.')[0]").Trim())
  if ($nodeMajor -ne 18) {
    Write-Warn "Host Node is $nodeVer — Next.js 12 prefers Node 18. Launcher will use npx node@18."
  }
  return $py
}

function Get-VenvPython {
  $candidates = @(
    (Join-Path $BackendDir '.venv\Scripts\python.exe'),
    (Join-Path (Split-Path $BackendDir -Parent) '.venv\Scripts\python.exe'),
    (Join-Path $BackendDir 'venv\Scripts\python.exe')
  )
  foreach ($c in $candidates) {
    if (Test-Path $c) { return $c }
  }
  return $null
}

function Ensure-VenvAndPackages([hashtable]$PyLauncher) {
  Write-Step 'Ensuring Python virtualenv + installing requirements'
  $venvPy = Get-VenvPython
  if (-not $venvPy) {
    $venvPath = Join-Path $BackendDir '.venv'
    Write-Step "Creating $venvPath"
    $createArgs = $PyLauncher.Args + @('-m', 'venv', $venvPath)
    & $PyLauncher.Exe @createArgs
    $venvPy = Join-Path $venvPath 'Scripts\python.exe'
    if (-not (Test-Path $venvPy)) { Die "Failed to create venv at $venvPath" }
  }

  # Prepend venv to PATH for this session (pip/scripts resolution)
  $venvScripts = Join-Path (Split-Path $venvPy -Parent) ''
  $env:Path = "$venvScripts;$env:Path"

  & $venvPy -m pip install --upgrade "pip<25" "setuptools<70" wheel
  & $venvPy -m pip install --prefer-binary -r (Join-Path $BackendDir 'requirements.txt')
  if ($LASTEXITCODE -ne 0) {
    & $venvPy -c "import django" 2>$null
    if ($LASTEXITCODE -ne 0) {
      Die 'pip install failed and Django is not importable. Prefer Python 3.10 or 3.11.'
    }
    Write-Warn 'pip install reported errors, but Django is importable — continuing'
  }
  Write-Ok "Python packages ready ($venvPy)"
  return $venvPy
}

function Ensure-FrontendPackages([string]$FrontendDir) {
  Write-Step 'Installing frontend packages (npm install --legacy-peer-deps)'
  Push-Location $FrontendDir
  try {
    # Clear broken installs if next binary is missing
    $nextBin = Join-Path $FrontendDir 'node_modules\next\dist\bin\next'
    if ((Test-Path (Join-Path $FrontendDir 'node_modules')) -and -not (Test-Path $nextBin)) {
      Write-Warn 'Broken node_modules detected — removing and reinstalling'
      Remove-Item -Recurse -Force (Join-Path $FrontendDir 'node_modules') -ErrorAction SilentlyContinue
    }
    & npm.cmd install --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) { Die "npm install failed (exit $LASTEXITCODE)" }
    if (-not (Test-Path $nextBin)) { Die 'Next.js binary missing after npm install' }
  } finally {
    Pop-Location
  }
  Write-Ok 'Frontend packages installed'
}

function Sync-BackendEnv {
  $envFile = Join-Path $BackendDir '.env'
  $example = Join-Path $BackendDir '.env.example'
  if (-not (Test-Path $envFile)) {
    if (-not (Test-Path $example)) { Die 'Missing .env.example' }
    Copy-Item $example $envFile
    Write-Ok 'Created .env from .env.example'
  }
  $frontendOrigin = "http://${PublicHost}:${FrontendPort}"
  $cors = "$frontendOrigin,http://127.0.0.1:${FrontendPort},http://localhost:3000,http://127.0.0.1:3000"
  $map = [ordered]@{
    'FRONTEND_LINK'          = $frontendOrigin
    'CORS_ALLOWED_ORIGINS'   = $cors
    'CORS_ALLOW_ALL_ORIGINS' = 'True'
    'DEBUG'                  = 'True'
    'ALLOWED_HOSTS'          = 'localhost,127.0.0.1,0.0.0.0,testserver'
    'BACKEND_PORT'           = "$BackendPort"
  }
  $lines = @(Get-Content $envFile -ErrorAction SilentlyContinue)
  foreach ($key in $map.Keys) {
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
      if ($lines[$i] -match "^$([regex]::Escape($key))=") {
        $lines[$i] = "$key=$($map[$key])"
        $found = $true
        break
      }
    }
    if (-not $found) { $lines += "$key=$($map[$key])" }
  }
  Set-Content -Path $envFile -Value $lines -Encoding UTF8
  Write-Ok "Backend env → FRONTEND_LINK=$frontendOrigin"
}

function Sync-FrontendEnv([string]$FrontendDir) {
  $envFile = Join-Path $FrontendDir '.env.local'
  $example = Join-Path $FrontendDir '.env.example'
  if (-not (Test-Path $envFile)) {
    if (-not (Test-Path $example)) { Die 'Missing frontend .env.example' }
    Copy-Item $example $envFile
    $secret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
    $jwt    = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
    $raw = Get-Content $envFile -Raw
    $raw = $raw -replace 'NEXTAUTH_SECRET=.*', "NEXTAUTH_SECRET=$secret"
    $raw = $raw -replace 'JWT_SECRET=.*', "JWT_SECRET=$jwt"
    Set-Content -Path $envFile -Value $raw -Encoding UTF8 -NoNewline
    Write-Ok 'Created .env.local with local secrets'
  }

  $backendUrl  = "http://${PublicHost}:${BackendPort}/"
  $frontendUrl = "http://${PublicHost}:${FrontendPort}/"
  $map = [ordered]@{
    'NEXT_PUBLIC_BACKEND_URL'  = $backendUrl
    'NEXT_PUBLIC_FRONTEND_URL' = $frontendUrl
    'NEXTAUTH_URL'             = $frontendUrl
  }
  $lines = @(Get-Content $envFile)
  foreach ($key in $map.Keys) {
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
      if ($lines[$i] -match "^$([regex]::Escape($key))=") {
        $lines[$i] = "$key=$($map[$key])"
        $found = $true
        break
      }
    }
    if (-not $found) { $lines += "$key=$($map[$key])" }
  }
  Set-Content -Path $envFile -Value $lines -Encoding UTF8
  Write-Ok "Frontend env → backend $backendUrl | self $frontendUrl"
}

function Start-BackendProcess([string]$VenvPython) {
  Claim-Port -Port $BackendPort
  Sync-BackendEnv

  $env:DJANGO_SETTINGS_MODULE = 'app.settings.local'
  $env:FRONTEND_LINK = "http://${PublicHost}:${FrontendPort}"
  $env:CORS_ALLOWED_ORIGINS = "http://${PublicHost}:${FrontendPort},http://127.0.0.1:${FrontendPort}"

  Write-Step 'Migrating database'
  Push-Location $BackendDir
  try {
    & $VenvPython scripts\init_db.py --settings=app.settings.local
    & $VenvPython manage.py migrate --noinput --settings=app.settings.local
    & $VenvPython manage.py check --settings=app.settings.local
  } finally {
    Pop-Location
  }

  Write-Step "Starting Django on ${BindHost}:${BackendPort} (URL http://${PublicHost}:${BackendPort})"
  if (Test-Path $BackendLog) { Remove-Item $BackendLog -Force -ErrorAction SilentlyContinue }

  # Start python directly (not nested powershell) so port reclaim can kill cleanly
  $argList = @(
    'manage.py', 'runserver', "${BindHost}:${BackendPort}",
    '--noreload', '--settings=app.settings.local'
  )
  $proc = Start-Process -FilePath $VenvPython `
    -ArgumentList $argList `
    -WorkingDirectory $BackendDir `
    -RedirectStandardOutput $BackendLog `
    -RedirectStandardError $BackendLog `
    -PassThru -WindowStyle Hidden

  Set-Content -Path (Join-Path $RunDir 'backend.pid') -Value $proc.Id
  Write-Ok "Backend pid $($proc.Id) → http://${PublicHost}:${BackendPort}"
}

function Start-FrontendProcess([string]$FrontendDir) {
  Claim-Port -Port $FrontendPort
  Sync-FrontendEnv $FrontendDir

  Write-Step "Starting Next.js on port $FrontendPort (URL http://${PublicHost}:${FrontendPort})"
  if (Test-Path $FrontendLog) { Remove-Item $FrontendLog -Force -ErrorAction SilentlyContinue }

  $nodeMajor = [int]((& node -p "process.versions.node.split('.')[0]").Trim())
  if ($nodeMajor -eq 18) {
    $filePath = (Get-Command node).Source
    $args = @('node_modules\next\dist\bin\next', 'dev', '-p', "$FrontendPort", '-H', 'localhost')
  } else {
    $filePath = (Get-Command npx.cmd).Source
    $args = @('--yes', '--package=node@18.20.8', 'node', 'node_modules\next\dist\bin\next', 'dev', '-p', "$FrontendPort", '-H', 'localhost')
  }

  $proc = Start-Process -FilePath $filePath `
    -ArgumentList $args `
    -WorkingDirectory $FrontendDir `
    -RedirectStandardOutput $FrontendLog `
    -RedirectStandardError $FrontendLog `
    -PassThru -WindowStyle Hidden

  Set-Content -Path (Join-Path $RunDir 'frontend.pid') -Value $proc.Id
  Write-Ok "Frontend pid $($proc.Id) → http://${PublicHost}:${FrontendPort}"
}

function Stop-All {
  Write-Step 'Stopping SnipKlip + reclaiming reserved ports'
  foreach ($name in @('backend.pid', 'frontend.pid')) {
    $pidFile = Join-Path $RunDir $name
    if (Test-Path $pidFile) {
      $procId = (Get-Content $pidFile | Select-Object -First 1)
      if ($procId) {
        & taskkill.exe /F /T /PID $procId 2>$null | Out-Null
        Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
      }
      Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
  }
  Claim-Port -Port $BackendPort -Retries 8
  Claim-Port -Port $FrontendPort -Retries 8
}

function Show-Status {
  $b = Get-PortOwnerPids $BackendPort
  $f = Get-PortOwnerPids $FrontendPort
  if ($b) { Write-Ok "backend:  listening on $BackendPort (pid $($b -join ',')) → http://${PublicHost}:${BackendPort}" }
  else { Write-Warn 'backend:  stopped' }
  if ($f) { Write-Ok "frontend: listening on $FrontendPort (pid $($f -join ',')) → http://${PublicHost}:${FrontendPort}" }
  else { Write-Warn 'frontend: stopped' }
}

# ---------- main ----------
$RunDir = Join-Path $BackendDir '.run'
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$BackendLog  = Join-Path $RunDir 'backend.log'
$FrontendLog = Join-Path $RunDir 'frontend.log'
$FrontendDir = Resolve-FrontendDir

switch ($Command) {
  'stop'   { Stop-All; Show-Status; exit 0 }
  'status' { Show-Status; exit 0 }
  'restart'{ Stop-All }
  'start'  { }
}

if (-not $FrontendDir) {
  Die @"
Frontend repo not found.
Clone as a sibling folder named snipklip-frontend:

  cd ..
  git clone https://github.com/Wankhede/SnipKlip-frontend.git snipklip-frontend
  cd SnipKlip
  .\run-local.bat

Or set:  `$env:FRONTEND_DIR = 'D:\path\to\snipklip-frontend'
"@
}

Write-Ok "Backend:  $BackendDir"
Write-Ok "Frontend: $FrontendDir"

$pyLauncher = Assert-Prereqs
$venvPython = Ensure-VenvAndPackages $pyLauncher
Ensure-FrontendPackages $FrontendDir

Stop-All
try {
  Start-BackendProcess $venvPython
  if (-not (Wait-Http 'Django schema' "http://${PublicHost}:${BackendPort}/api/schema/" 200 120)) {
    Write-Host '---- backend.log (tail) ----' -ForegroundColor Yellow
    if (Test-Path $BackendLog) { Get-Content $BackendLog -Tail 50 }
    Die "Backend failed health-check on http://${PublicHost}:${BackendPort}"
  }

  Start-FrontendProcess $FrontendDir
  if (-not (Wait-Http 'Next.js login' "http://${PublicHost}:${FrontendPort}/login" 200 180)) {
    Write-Host '---- frontend.log (tail) ----' -ForegroundColor Yellow
    if (Test-Path $FrontendLog) { Get-Content $FrontendLog -Tail 50 }
    Die "Frontend failed health-check on http://${PublicHost}:${FrontendPort}"
  }
} catch {
  Write-Host $_.Exception.Message -ForegroundColor Red
  Stop-All
  exit 1
}

Write-Host ''
Write-Host 'SnipKlip is running:' -ForegroundColor Green
Write-Host "  Backend:  http://${PublicHost}:${BackendPort}"
Write-Host "  Schema:   http://${PublicHost}:${BackendPort}/api/schema/"
Write-Host "  Frontend: http://${PublicHost}:${FrontendPort}"
Write-Host "  Login:    http://${PublicHost}:${FrontendPort}/login"
Write-Host "  Register: http://${PublicHost}:${FrontendPort}/register"
Write-Host "  Logs:     $RunDir"
Write-Host ''
Write-Host 'Open those localhost URLs in your browser (not 127.0.0.1).' -ForegroundColor Cyan
Write-Host 'Stop with:  .\run-local.bat stop' -ForegroundColor Cyan
Show-Status
