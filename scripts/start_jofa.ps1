# JOFA — one-click local startup (Windows / PowerShell)
# Prerequisites: XAMPP MySQL started, Python venv at .\.venv
#
# Usage:
#   .\scripts\start_jofa.ps1
#   .\scripts\start_jofa.ps1 -ForceSeed
#   .\scripts\start_jofa.ps1 -Port 8000

param(
    [int]$Port = 8000,
    [switch]$ForceSeed
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

$python = Join-Path $PWD '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Host 'Virtualenv not found. Creating .venv ...' -ForegroundColor Yellow
    py -3 -m venv .venv
    $python = Join-Path $PWD '.venv\Scripts\python.exe'
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
}

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Created .env from .env.example — edit MySQL password if needed.' -ForegroundColor Yellow
}

$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

Write-Host '=== JOFA bootstrap ===' -ForegroundColor Cyan
Write-Host 'Make sure XAMPP MySQL is running before continuing.'

$seedArgs = @('manage.py', 'ensure_ready')
if ($ForceSeed) { $seedArgs += '--force-seed' }

& $python @seedArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Bootstrap failed. Start MySQL in XAMPP, then re-run this script.' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Starting server at http://127.0.0.1:$Port/" -ForegroundColor Green
Write-Host "AI Consult:  http://127.0.0.1:$Port/consult/"
Write-Host "Admin:       http://127.0.0.1:$Port/admin/"
& $python manage.py runserver "127.0.0.1:$Port"
