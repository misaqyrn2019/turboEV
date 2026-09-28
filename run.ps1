$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonLocal = Join-Path $projectRoot '.venv/Scripts/python.exe'
$pythonParent = Join-Path (Split-Path $projectRoot -Parent) '.venv/Scripts/python.exe'
if (Test-Path -LiteralPath $pythonLocal) {
    $fleetPython = $pythonLocal
} elseif (Test-Path -LiteralPath $pythonParent) {
    $fleetPython = $pythonParent
} else {
    python -m venv (Join-Path $projectRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 or newer, then run this file again.' }
    $fleetPython = $pythonLocal
}
& $fleetPython -c "import importlib.util, sys; sys.exit(0 if all(importlib.util.find_spec(m) for m in ['fastapi', 'uvicorn', 'argon2']) else 1)"
if ($LASTEXITCODE -ne 0) {
    & $fleetPython -m pip install -r (Join-Path $projectRoot 'backend/requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Could not install Python dependencies.' }
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'dist/index.html'))) {
    npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Could not install frontend dependencies.' }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
}
& $fleetPython -c 'from backend.app import initialize; initialize()'
if ($LASTEXITCODE -ne 0) { throw 'Database initialization failed.' }
Write-Host 'Fleet is ready. Open http://127.0.0.1:8000 in your browser.' -ForegroundColor Green
Write-Host 'Initial admin credentials: fleet_web/data/initial-credentials.txt'
Write-Host 'Keep this window open. Press Ctrl+C to stop the local service.'
& $fleetPython -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
if ($LASTEXITCODE -ne 0) { throw 'Server stopped. Check whether port 8000 is already in use.' }
