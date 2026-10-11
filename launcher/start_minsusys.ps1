$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "未找到项目 Python 环境：$pythonExe"
}

$listener = Get-NetTCPConnection -LocalAddress "127.0.0.1" -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $listener) {
    Start-Process -WindowStyle Hidden -FilePath $pythonExe -ArgumentList "manage.py", "runserver", "127.0.0.1:8000", "--noreload" -WorkingDirectory $projectRoot
    Start-Sleep -Seconds 3
}

Start-Process "http://127.0.0.1:8000/"
Start-Process "http://127.0.0.1:8000/admin/"
