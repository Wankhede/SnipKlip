#Requires -Version 5.1
<#
.SYNOPSIS
  Single-click SnipKlip launcher for Windows (VS Code / PowerShell).

.DESCRIPTION
  Fixes common Windows failures:
    - False "next/react not installed" (verifies via node require, not Unix bin bits)
    - TCP connection refused (waits for LISTEN, avoids stdout/stderr same-file redirect crash)
    - npm.cmd / PATH resolution
    - localhost-only browser URLs (not 127.0.0.1)

  Ports:
    Backend  → http://localhost:8082
    Frontend → http://localhost:8083
#>
[CmdletBinding()]
param(
  [Parameter(Position = 0)]
  [ValidateSet('start', 'stop', 'status', 'restart')]
  [string]$Command = 'start'
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

# Bypass corporate proxies for local health checks / NextAuth loopbacks
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
$env:no_proxy = $env:NO_PROXY
[System.Net.WebRequest]::DefaultWebProxy = $null

$BackendPort  = 8082
$FrontendPort = 8083
$PublicHost   = 'localhost'
$BindHost     = '0.0.0.0'

$ScriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$BackendDir = (Resolve-Path $ScriptRoot).Path
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

function Get-NpmCmd {
  $cmd = Get-Command 'npm.cmd' -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $cmd = Get-Command 'npm' -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

function Get-NodeCmd {
  $cmd = Get-Command 'node.exe' -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $cmd = Get-Command 'node' -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

function Resolve-PythonLauncher {
  if (Test-Cmd 'py') {
    try {
      $ver = & py -3 -c "import sys; print('%d.%d' % (sys.version_info.major, sys.version_info.minor))" 2>$null
      if ($ver) { return @{ Exe = 'py'; Args = @('-3') } }
    } catch { }
  }
  foreach ($name in @('python', 'python3')) {
    if (Test-Cmd $name) { return @{ Exe = $name; Args = @() } }
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
      $pkg = Join-Path $c 'package.json'
      if (Test-Path -LiteralPath $pkg) { return (Resolve-Path -LiteralPath $c).Path }
    } catch { }
  }
  return $null
}

function Get-PortOwnerPids([int]$Port) {
  $pids = New-Object System.Collections.Generic.List[int]
  try {
    foreach ($c in @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)) {
      if ($c.OwningProcess -and $c.OwningProcess -ne 0) { [void]$pids.Add([int]$c.OwningProcess) }
    }
  } catch { }
  if ($pids.Count -eq 0) {
    foreach ($line in @(& netstat -ano 2>$null | Select-String -Pattern ":$Port\s+.*LISTENING")) {
      if ($line.Line -match '\s+(\d+)\s*$') {
        $id = [int]$Matches[1]
        if ($id -ne 0) { [void]$pids.Add($id) }
      }
    }
  }
  return @($pids | Select-Object -Unique)
}

function Claim-Port {
  param([Parameter(Mandatory = $true)][int]$Port, [int]$Retries = 15)
  for ($i = 1; $i -le $Retries; $i++) {
    $owners = @(Get-PortOwnerPids $Port)
    if ($owners.Count -eq 0) {
      Write-Ok "Port $Port is free"
      return
    }
    foreach ($procId in $owners) {
      $name = ''
      try { $name = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName } catch { }
      Write-Warn "Port $Port occupied by pid $procId ($name) — reclaiming"
      & taskkill.exe /F /T /PID $procId 2>$null | Out-Null
      Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 800
  }
  $still = @(Get-PortOwnerPids $Port)
  if ($still.Count -gt 0) {
    Die "Could not free port $Port (pids: $($still -join ',')). Close that app, then retry."
  }
}

function Wait-PortListen([int]$Port, [int]$Attempts = 90) {
  for ($i = 1; $i -le $Attempts; $i++) {
    if (@(Get-PortOwnerPids $Port).Count -gt 0) {
      Write-Ok "TCP LISTEN on port $Port"
      return $true
    }
    Start-Sleep -Seconds 1
  }
  Write-Host "FAIL TCP LISTEN never appeared on port $Port" -ForegroundColor Red
  return $false
}

function Wait-Http([string]$Name, [string]$Url, [int]$Expected = 200, [int]$Attempts = 120) {
  for ($i = 1; $i -le $Attempts; $i++) {
    try {
      # Prefer curl.exe on Win10+ (more reliable than Invoke-WebRequest behind proxies)
      if (Test-Cmd 'curl.exe') {
        $code = & curl.exe -s -o NUL -w '%{http_code}' --max-time 4 $Url 2>$null
        if ($code -eq "$Expected") {
          Write-Ok "$Name ($Expected) $Url"
          return $true
        }
      } else {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4
        if ([int]$resp.StatusCode -eq $Expected) {
          Write-Ok "$Name ($Expected) $Url"
          return $true
        }
      }
    } catch { }
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
Enable "Add python.exe to PATH", then reopen VS Code / PowerShell.
"@
  }
  $nodePath = Get-NodeCmd
  $npmPath = Get-NpmCmd
  if (-not $nodePath -or -not $npmPath) {
    Die @"
Node.js / npm was not found on PATH.
Install Node.js 18 LTS from https://nodejs.org/en/download
Then reopen VS Code / PowerShell.
"@
  }

  $pyArgs = $py.Args + @('-c', 'import sys; print("%d.%d.%d" % sys.version_info[:3])')
  $pyVer = (& $py.Exe @pyArgs).Trim()
  $nodeVer = (& $nodePath -v).Trim()
  $npmVer = (& $npmPath -v).Trim()
  Write-Ok "Python $pyVer | Node $nodeVer ($nodePath) | npm $npmVer"

  $nodeMajor = [int]((& $nodePath -p "process.versions.node.split('.')[0]").Trim())
  if ($nodeMajor -ne 18) {
    Write-Warn "Host Node is $nodeVer — Next.js 12 prefers Node 18. Will prefer npx node@18 when launching."
  }
  return @{
    Py = $py
    Node = $nodePath
    Npm = $npmPath
    NodeMajor = $nodeMajor
  }
}

function Get-VenvPython {
  foreach ($c in @(
      (Join-Path $BackendDir '.venv\Scripts\python.exe'),
      (Join-Path (Split-Path $BackendDir -Parent) '.venv\Scripts\python.exe'),
      (Join-Path $BackendDir 'venv\Scripts\python.exe')
    )) {
    if (Test-Path -LiteralPath $c) { return (Resolve-Path -LiteralPath $c).Path }
  }
  return $null
}

function Ensure-VenvAndPackages([hashtable]$Tools) {
  Write-Step 'Ensuring Python virtualenv + installing requirements'
  $venvPy = Get-VenvPython
  if (-not $venvPy) {
    $venvPath = Join-Path $BackendDir '.venv'
    Write-Step "Creating $venvPath"
    $createArgs = $Tools.Py.Args + @('-m', 'venv', $venvPath)
    & $Tools.Py.Exe @createArgs
    $venvPy = Join-Path $venvPath 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $venvPy)) { Die "Failed to create venv at $venvPath" }
  }

  $venvScripts = Split-Path $venvPy -Parent
  $env:Path = "$venvScripts;$env:Path"

  & $venvPy -m pip install --upgrade "pip<25" "setuptools<70" wheel | Out-Host
  & $venvPy -m pip install --prefer-binary -r (Join-Path $BackendDir 'requirements.txt') | Out-Host
  if ($LASTEXITCODE -ne 0) {
    & $venvPy -c "import django" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
      Die 'pip install failed and Django is not importable. Prefer Python 3.10 or 3.11.'
    }
    Write-Warn 'pip reported errors, but Django imports — continuing'
  }
  Write-Ok "Python packages ready ($venvPy)"
  return $venvPy
}

function Test-FrontendModules([string]$FrontendDir, [string]$NodePath) {
  # Real Windows-safe check: can Node resolve next + react + react-dom?
  $probe = @'
const mods = ["next", "react", "react-dom"];
for (const m of mods) {
  try { require.resolve(m); }
  catch (e) { console.error("MISSING:" + m); process.exit(2); }
}
console.log("READY");
'@
  $probeFile = Join-Path $env:TEMP ("snipklip-probe-{0}.js" -f [guid]::NewGuid().ToString('N'))
  Set-Content -Path $probeFile -Value $probe -Encoding ASCII
  try {
    Push-Location $FrontendDir
    $out = & $NodePath $probeFile 2>&1 | Out-String
    Pop-Location
    if ($out -match 'READY') { return $true }
    Write-Warn ("Module probe failed: " + $out.Trim())
    return $false
  } catch {
    try { Pop-Location } catch { }
    Write-Warn $_.Exception.Message
    return $false
  } finally {
    Remove-Item $probeFile -Force -ErrorAction SilentlyContinue
  }
}

function Ensure-FrontendPackages([string]$FrontendDir, [hashtable]$Tools) {
  Write-Step 'Checking / installing frontend packages (next, react, …)'

  $alreadyOk = Test-FrontendModules $FrontendDir $Tools.Node
  if ($alreadyOk) {
    Write-Ok 'next / react / react-dom already resolve — refreshing with npm install anyway'
  } else {
    Write-Warn 'Frontend modules not resolvable yet — running npm install'
  }

  Push-Location $FrontendDir
  try {
    # Use cmd.exe so npm.cmd lifecycle scripts work reliably on Windows
    $npm = $Tools.Npm
    $args = @('install', '--legacy-peer-deps', '--no-fund', '--no-audit')
    Write-Host "Running: $npm $($args -join ' ')"
    $p = Start-Process -FilePath $npm -ArgumentList $args -WorkingDirectory $FrontendDir -Wait -PassThru -NoNewWindow
    if ($p.ExitCode -ne 0) {
      Die "npm install failed (exit $($p.ExitCode)). Delete node_modules and retry, or run: npm install --legacy-peer-deps"
    }
  } finally {
    Pop-Location
  }

  if (-not (Test-FrontendModules $FrontendDir $Tools.Node)) {
    Die @"
npm install finished but Node still cannot require('next') / require('react').
Frontend dir: $FrontendDir
Try manually:
  cd "$FrontendDir"
  rmdir /s /q node_modules
  npm install --legacy-peer-deps
"@
  }
  Write-Ok 'Frontend packages verified (next + react + react-dom)'
}

function Sync-BackendEnv {
  $envFile = Join-Path $BackendDir '.env'
  $example = Join-Path $BackendDir '.env.example'
  if (-not (Test-Path -LiteralPath $envFile)) {
    if (-not (Test-Path -LiteralPath $example)) { Die 'Missing .env.example' }
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
    'ALLOWED_HOSTS'          = 'localhost,127.0.0.1,0.0.0.0,testserver,[::1]'
    'BACKEND_PORT'           = "$BackendPort"
  }
  $lines = @(Get-Content -LiteralPath $envFile -ErrorAction SilentlyContinue)
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
  Set-Content -LiteralPath $envFile -Value $lines -Encoding UTF8
  Write-Ok "Backend env → FRONTEND_LINK=$frontendOrigin"
}

function Sync-FrontendEnv([string]$FrontendDir) {
  $envFile = Join-Path $FrontendDir '.env.local'
  $example = Join-Path $FrontendDir '.env.example'
  if (-not (Test-Path -LiteralPath $envFile)) {
    if (-not (Test-Path -LiteralPath $example)) { Die 'Missing frontend .env.example' }
    Copy-Item $example $envFile
    $secret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
    $jwt    = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
    $raw = Get-Content -LiteralPath $envFile -Raw
    $raw = $raw -replace 'NEXTAUTH_SECRET=.*', "NEXTAUTH_SECRET=$secret"
    $raw = $raw -replace 'JWT_SECRET=.*', "JWT_SECRET=$jwt"
    Set-Content -LiteralPath $envFile -Value $raw -Encoding UTF8 -NoNewline
    Write-Ok 'Created .env.local with local secrets'
  }

  $backendUrl  = "http://${PublicHost}:${BackendPort}/"
  $frontendUrl = "http://${PublicHost}:${FrontendPort}/"
  $map = [ordered]@{
    'NEXT_PUBLIC_BACKEND_URL'  = $backendUrl
    'NEXT_PUBLIC_FRONTEND_URL' = $frontendUrl
    'NEXTAUTH_URL'             = $frontendUrl
  }
  $lines = @(Get-Content -LiteralPath $envFile)
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
  Set-Content -LiteralPath $envFile -Value $lines -Encoding UTF8
  Write-Ok "Frontend env → backend $backendUrl | self $frontendUrl"
}

function Start-LoggedCmd {
  param(
    [Parameter(Mandatory = $true)][string]$FilePath,
    [Parameter(Mandatory = $true)][string[]]$ArgumentList,
    [Parameter(Mandatory = $true)][string]$WorkingDirectory,
    [Parameter(Mandatory = $true)][string]$LogPath
  )
  # CRITICAL on Windows: Start-Process cannot redirect stdout+stderr to the SAME file.
  # Use cmd.exe so both streams go to one log without that crash.
  if (Test-Path -LiteralPath $LogPath) { Remove-Item -LiteralPath $LogPath -Force -ErrorAction SilentlyContinue }

  $argString = ($ArgumentList | ForEach-Object {
      if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
    }) -join ' '

  $wrapper = "cd /d `"$WorkingDirectory`" && `"$FilePath`" $argString >> `"$LogPath`" 2>&1"
  $proc = Start-Process -FilePath 'cmd.exe' `
    -ArgumentList @('/d', '/c', $wrapper) `
    -WorkingDirectory $WorkingDirectory `
    -PassThru -WindowStyle Hidden
  return $proc
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

  Write-Step "Starting Django → http://${PublicHost}:${BackendPort}"
  $proc = Start-LoggedCmd -FilePath $VenvPython `
    -ArgumentList @('manage.py', 'runserver', "${BindHost}:${BackendPort}", '--noreload', '--settings=app.settings.local') `
    -WorkingDirectory $BackendDir `
    -LogPath $BackendLog

  Set-Content -LiteralPath (Join-Path $RunDir 'backend.pid') -Value $proc.Id
  Write-Ok "Backend pid $($proc.Id) → http://${PublicHost}:${BackendPort}"
}

function Start-FrontendProcess([string]$FrontendDir, [hashtable]$Tools) {
  Claim-Port -Port $FrontendPort
  Sync-FrontendEnv $FrontendDir

  Write-Step "Starting Next.js → http://${PublicHost}:${FrontendPort}"

  # Prefer npm run dev (uses package.json) — most reliable on Windows.
  # Force hostname localhost so NextAuth SSR fetch to localhost works.
  $npm = $Tools.Npm
  $node = $Tools.Node
  $nextCli = Join-Path $FrontendDir 'node_modules\next\dist\bin\next'

  if ($Tools.NodeMajor -eq 18 -and (Test-Path -LiteralPath $nextCli)) {
    $file = $node
    $args = @($nextCli, 'dev', '-p', "$FrontendPort", '-H', 'localhost')
  } elseif ($Tools.NodeMajor -eq 18) {
    # Fall back to npm script
    $file = $npm
    $args = @('run', 'dev', '--', '-H', 'localhost')
  } else {
    # Host Node is not 18 — run Next under portable Node 18
    $npx = (Get-Command 'npx.cmd' -ErrorAction SilentlyContinue)
    if (-not $npx) { Die 'npx.cmd not found (install Node 18 LTS).' }
    $file = $npx.Source
    $args = @('--yes', '--package=node@18.20.8', 'node', $nextCli, 'dev', '-p', "$FrontendPort", '-H', 'localhost')
  }

  $proc = Start-LoggedCmd -FilePath $file `
    -ArgumentList $args `
    -WorkingDirectory $FrontendDir `
    -LogPath $FrontendLog

  Set-Content -LiteralPath (Join-Path $RunDir 'frontend.pid') -Value $proc.Id
  Write-Ok "Frontend pid $($proc.Id) → http://${PublicHost}:${FrontendPort}"
}

function Stop-All {
  Write-Step 'Stopping SnipKlip + reclaiming reserved ports'
  foreach ($name in @('backend.pid', 'frontend.pid')) {
    $pidFile = Join-Path $RunDir $name
    if (Test-Path -LiteralPath $pidFile) {
      $procId = (Get-Content -LiteralPath $pidFile | Select-Object -First 1)
      if ($procId) {
        & taskkill.exe /F /T /PID $procId 2>$null | Out-Null
        Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
      }
      Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    }
  }
  Claim-Port -Port $BackendPort -Retries 8
  Claim-Port -Port $FrontendPort -Retries 8
}

function Show-Status {
  $b = @(Get-PortOwnerPids $BackendPort)
  $f = @(Get-PortOwnerPids $FrontendPort)
  if ($b.Count) { Write-Ok "backend:  LISTEN $BackendPort (pid $($b -join ',')) → http://${PublicHost}:${BackendPort}" }
  else { Write-Warn 'backend:  stopped' }
  if ($f.Count) { Write-Ok "frontend: LISTEN $FrontendPort (pid $($f -join ',')) → http://${PublicHost}:${FrontendPort}" }
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

$Tools = Assert-Prereqs
$venvPython = Ensure-VenvAndPackages $Tools
Ensure-FrontendPackages $FrontendDir $Tools

Stop-All
try {
  Start-BackendProcess $venvPython
  if (-not (Wait-PortListen $BackendPort 90)) {
    if (Test-Path -LiteralPath $BackendLog) { Get-Content -LiteralPath $BackendLog -Tail 60 }
    Die "Backend never opened TCP port $BackendPort"
  }
  if (-not (Wait-Http 'Django schema' "http://${PublicHost}:${BackendPort}/api/schema/" 200 120)) {
    if (Test-Path -LiteralPath $BackendLog) { Get-Content -LiteralPath $BackendLog -Tail 60 }
    Die "Backend HTTP health-check failed on http://${PublicHost}:${BackendPort}"
  }

  Start-FrontendProcess $FrontendDir $Tools
  if (-not (Wait-PortListen $FrontendPort 120)) {
    if (Test-Path -LiteralPath $FrontendLog) { Get-Content -LiteralPath $FrontendLog -Tail 80 }
    Die "Frontend never opened TCP port $FrontendPort (see .run\frontend.log)"
  }
  if (-not (Wait-Http 'Next.js login' "http://${PublicHost}:${FrontendPort}/login" 200 180)) {
    if (Test-Path -LiteralPath $FrontendLog) { Get-Content -LiteralPath $FrontendLog -Tail 80 }
    Die "Frontend HTTP health-check failed on http://${PublicHost}:${FrontendPort}"
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
Write-Host "  Logs:     $RunDir"
Write-Host ''
Write-Host 'Open http://localhost:8083 in your browser (not 127.0.0.1).' -ForegroundColor Cyan
Write-Host 'Stop with:  .\run-local.bat stop' -ForegroundColor Cyan
Show-Status
