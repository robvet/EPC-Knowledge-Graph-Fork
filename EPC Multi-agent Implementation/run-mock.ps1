Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $workspaceRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found at '$pythonExe'. Create the workspace .venv first."
}

Push-Location $scriptDir
try {
    & $pythonExe -m uvicorn frontend.server:app --host 127.0.0.1 --port 8000 --reload
}
finally {
    Pop-Location
}