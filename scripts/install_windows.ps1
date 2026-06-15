<#
.SYNOPSIS
    Установка ACCOS на Windows (Python 3.11+, Node.js 18+, PostgreSQL).
#>

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $PROJECT_ROOT

Write-Host "=== Установка ACCOS ===" -ForegroundColor Cyan

# --- 1. Проверка предварительных требований ---
Write-Host "[1/8] Проверка зависимостей..." -ForegroundColor Yellow

$python = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python не найден. Установите Python 3.11+ и добавьте в PATH."
}
$pyver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pyver -lt [version]"3.11") {
    throw "Требуется Python 3.11+, найдена версия $pyver"
}
Write-Host "  Python $pyver OK"

$node = Get-Command "node" -ErrorAction SilentlyContinue
if (-not $node) {
    throw "Node.js не найден. Установите Node.js 18+."
}
$nodever = & node --version
Write-Host "  Node.js $nodever OK"

$npm = Get-Command "npm" -ErrorAction SilentlyContinue
if (-not $npm) {
    throw "npm не найден."
}

$psql = Get-Command "psql" -ErrorAction SilentlyContinue
if (-not $psql) {
    Write-Host "  [WARN] psql не найден. Убедитесь что PostgreSQL установлен и добавлен в PATH." -ForegroundColor Yellow
} else {
    Write-Host "  PostgreSQL OK"
}

# --- 2. Создание .venv ---
Write-Host "[2/8] Создание виртуального окружения..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    & python -m venv .venv
    Write-Host "  .venv создан"
} else {
    Write-Host "  .venv уже существует"
}

$pip = "$PROJECT_ROOT\.venv\Scripts\pip.exe"
$python_venv = "$PROJECT_ROOT\.venv\Scripts\python.exe"

# --- 3. Установка Python зависимостей ---
Write-Host "[3/8] Установка Python зависимостей..." -ForegroundColor Yellow
& $pip install -r "$PROJECT_ROOT\backend\requirements.txt" 2>&1 | Out-Null
Write-Host "  Зависимости установлены"

# --- 4. Установка Node.js зависимостей ---
Write-Host "[4/8] Установка Node.js зависимостей (frontend)..." -ForegroundColor Yellow
Set-Location -LiteralPath "$PROJECT_ROOT\frontend"
& npm install 2>&1 | Out-Null
Write-Host "  Frontend зависимости установлены"

Write-Host "[4/8] Установка Node.js зависимостей (admin)..." -ForegroundColor Yellow
Set-Location -LiteralPath "$PROJECT_ROOT\admin"
& npm install 2>&1 | Out-Null
Write-Host "  Admin зависимости установлены"

Set-Location -LiteralPath $PROJECT_ROOT

# --- 5. Создание .env ---
Write-Host "[5/8] Настройка конфигурации..." -ForegroundColor Yellow
$envPath = "$PROJECT_ROOT\config\.env"
$envExample = "$PROJECT_ROOT\config\.env.example"
if (-not (Test-Path $envPath)) {
    Copy-Item $envExample $envPath
    Write-Host "  Создан config\.env из .env.example"
    Write-Host "  !!! Отредактируйте config\.env перед запуском: настройте БД, LDAP, ComfyUI, LMStudio !!!" -ForegroundColor Red
} else {
    Write-Host "  config\.env уже существует"
}

# --- 6. Создание директорий ---
Write-Host "[6/8] Создание директорий..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$PROJECT_ROOT\static\generated" -Force | Out-Null
New-Item -ItemType Directory -Path "$PROJECT_ROOT\static\uploads" -Force | Out-Null
New-Item -ItemType Directory -Path "$PROJECT_ROOT\static\avatars" -Force | Out-Null
New-Item -ItemType Directory -Path "$PROJECT_ROOT\static\knowledge" -Force | Out-Null
New-Item -ItemType Directory -Path "$PROJECT_ROOT\static\edits" -Force | Out-Null
New-Item -ItemType Directory -Path "$PROJECT_ROOT\static\videos" -Force | Out-Null
New-Item -ItemType Directory -Path "$PROJECT_ROOT\static\templates" -Force | Out-Null
New-Item -ItemType Directory -Path "$PROJECT_ROOT\workflows" -Force | Out-Null
New-Item -ItemType Directory -Path "$PROJECT_ROOT\backend\logs" -Force | Out-Null
Write-Host "  Директории созданы"

# --- 7. Миграции БД ---
Write-Host "[7/8] Применение миграций БД..." -ForegroundColor Yellow
try {
    $env:CONFIG_DIR = "$PROJECT_ROOT\config"
    & $python_venv -m alembic -c "$PROJECT_ROOT\config\alembic.ini" upgrade head 2>&1
    Write-Host "  Миграции применены"
} catch {
    Write-Host "  [WARN] Не удалось применить миграции. Проверьте PostgreSQL и config\.env" -ForegroundColor Yellow
}

# --- 8. Сборка фронтендов ---
Write-Host "[8/8] Сборка фронтендов..." -ForegroundColor Yellow
Set-Location -LiteralPath "$PROJECT_ROOT\frontend"
& npm run build 2>&1 | Out-Null
Write-Host "  Frontend собран"

Set-Location -LiteralPath "$PROJECT_ROOT\admin"
& npm run build 2>&1 | Out-Null
Write-Host "  Admin собран"

Set-Location -LiteralPath $PROJECT_ROOT

Write-Host "=== Установка завершена ===" -ForegroundColor Green
Write-Host ""
Write-Host "Для запуска сервера выполните:" -ForegroundColor Cyan
Write-Host "  .venv\Scripts\uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "Или используйте start_server.ps1:" -ForegroundColor Cyan
Write-Host "  .\scripts\start_server.ps1" -ForegroundColor White
