$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "uvicorn trader_app.api:app --host 127.0.0.1 --port 8000"
npm --prefix dashboard run dev
