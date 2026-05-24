$ErrorActionPreference = "Stop"

$backendDir = Split-Path -Parent $PSScriptRoot
$python = Join-Path $backendDir "venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    $python = Join-Path $backendDir ".venv\Scripts\python.exe"
}

if (-not (Test-Path $python)) {
    Write-Error "No backend virtual environment found. Create one with: python -m venv venv"
}

$port = if ($env:BACKEND_PORT) { [int]$env:BACKEND_PORT } else { 8000 }
while (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
    Write-Host "Port $port is already in use; trying $($port + 1)."
    $port += 1
}

Write-Host "Starting MedGuard backend on http://127.0.0.1:$port"
Set-Location $backendDir
& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $port
