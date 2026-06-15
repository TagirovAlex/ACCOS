#!/usr/bin/env bash
#
# Полное удаление ACCOS с Debian 12+
# Запускать от root или через sudo.
#
# Usage:
#   sudo bash scripts/uninstall_debian.sh

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log() { echo -e "${CYAN}[ACCOS]${NC} $1"; }
ok()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERR]${NC} $1"; exit 1; }

if [[ $EUID -ne 0 ]]; then err "Запустите с sudo: sudo bash scripts/uninstall_debian.sh"; fi

echo -e "${RED}========================================${NC}"
echo -e "${RED}  Полное удаление ACCOS с сервера${NC}"
echo -e "${RED}========================================${NC}"
echo ""
echo "Будут удалены:"
echo "  - systemd сервис accos.service"
echo "  - Nginx конфигурация /etc/nginx/sites-available/accos.conf"
echo "  - SSL сертификаты /etc/nginx/ssl/accos.*"
echo "  - База данных PostgreSQL accos и пользователь accos"
echo "  - Директория проекта /opt/accos (или текущая)"
echo "  - Пользователь accos"
echo "  - Python виртуальное окружение .venv"
echo ""
echo -n "ПРОДОЛЖИТЬ? (введите YES): "; read -r confirm
if [[ "$confirm" != "YES" ]]; then err "Отменено"; fi

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
log "Корень проекта: $PROJECT_ROOT"

log "[1/5] Остановка и удаление systemd сервиса..."
systemctl stop accos.service 2>/dev/null || true
systemctl disable accos.service 2>/dev/null || true
rm -f /etc/systemd/system/accos.service
systemctl daemon-reload
ok "systemd сервис удалён"

log "[2/5] Удаление Nginx конфигурации..."
rm -f /etc/nginx/sites-enabled/accos.conf
rm -f /etc/nginx/sites-available/accos.conf
rm -f /etc/nginx/ssl/accos.crt /etc/nginx/ssl/accos.key
rmdir /etc/nginx/ssl 2>/dev/null || true
systemctl reload nginx 2>/dev/null || true
ok "Nginx конфигурация удалена"

log "[3/5] Удаление базы данных PostgreSQL..."
DB_NAME="${DB_NAME:-accos}"; DB_USER="${DB_USER:-accos}"
su - postgres -c "psql -c \"DROP DATABASE IF EXISTS $DB_NAME;\"" 2>/dev/null || warn "Не удалось удалить БД $DB_NAME"
su - postgres -c "psql -c \"DROP ROLE IF EXISTS $DB_USER;\"" 2>/dev/null || warn "Не удалось удалить пользователя $DB_USER"
ok "База данных удалена"

log "[4/5] Удаление файлов проекта..."
rm -rf "$PROJECT_ROOT/.venv" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/static" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/backend/logs" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/frontend/dist" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/frontend/node_modules" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/admin/dist" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/admin/node_modules" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/node_modules" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/tmp" 2>/dev/null || true
# Удаляем сам проект если он в /opt/accos — только после подтверждения
if [[ "$PROJECT_ROOT" == "/opt/accos" ]]; then
    echo -n "Удалить директорию /opt/accos полностью? [y/N]: "; read -r rm_root
    if [[ "$rm_root" =~ ^[yY] ]]; then
        rm -rf /opt/accos; ok "Проект удалён"
    else ok "Файлы проекта оставлены"; fi
fi
ok "Файлы проекта удалены"

log "[5/5] Удаление пользователя accos..."
if id -u accos &>/dev/null; then
    pkill -u accos 2>/dev/null || true
    userdel -r accos 2>/dev/null || warn "Пользователь accos не удалён (возможно, есть активные процессы)"
    ok "Пользователь accos удалён"
else ok "Пользователь accos не существует"; fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ACCOS полностью удалён${NC}"
echo -e "${GREEN}========================================${NC}"
