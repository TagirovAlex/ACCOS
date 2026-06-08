<#
.SYNOPSIS
    Запуск ACCOS сервера в production режиме (без --reload).
    Для разработки используйте --reload флаг.
.PARAMETER Dev
    Запуск с hot-reload для разработки.
.PARAMETER Port
    Порт сервера (по умолчанию 8000).
.PARAMETER Host
    Хост (по умолчанию 0.0.0.0).
.PARAMETER Workers
    Количество воркеров (по умолчанию 4, только без --dev).
#>

param(
    [switch]$Dev,
    [int]$Port = 8000,
    [string]$Host = "0.0.0.0",
    [int]$Workers = 4
)

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath "$PROJECT_ROOT\backend"
$Uvicorn = "$PROJECT_ROOT\.venv\Scripts\uvicorn.exe"

if (-not (Test-Path $Uvicorn)) {
    Write-Error "uvicorn не найден. Запустите install_windows.ps1 сначала."
    exit 1
}

if ($Dev) {
    Write-Host "Запуск в режиме разработки (reload)..." -ForegroundColor Yellow
    & $Uvicorn main:app --reload --host $Host --port $Port
} else {
    Write-Host "Запуск production: $Host`:$Port, workers=$Workers" -ForegroundColor Green
    & $Uvicorn main:app --host $Host --port $Port --workers $Workers
}
