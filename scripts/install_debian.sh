#!/usr/bin/env bash
#
# Установка ACCOS на Debian 12+
# Запускать от root или через sudo.
#
# Usage:
#   sudo bash scripts/install_debian.sh

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${CYAN}[ACCOS]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; exit 1; }

if [[ $EUID -ne 0 ]]; then err "Запустите с sudo: sudo bash scripts/install_debian.sh"; fi

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
log "Корень проекта: $PROJECT_ROOT"

log "[1/9] Установка системных пакетов..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip python3-dev \
    postgresql postgresql-client nginx nodejs npm git curl openssl ca-certificates 2>&1 | tail -1
ok "Системные пакеты установлены"

log "[2/9] Создание пользователя accos..."
if ! id -u accos &>/dev/null; then useradd -m -s /bin/bash -d /opt/accos accos; ok "Пользователь accos создан"
else ok "Пользователь accos уже существует"; fi

log "[3/9] Настройка проекта..."
if [[ "$PROJECT_ROOT" != "/opt/accos" ]]; then
    warn "Проект в $PROJECT_ROOT, рекомендуется /opt/accos"
    echo -n "Создать симлинк /opt/accos -> $PROJECT_ROOT? [y/N]: "; read -r symlink_choice
    if [[ "$symlink_choice" =~ ^[yY] ]]; then
        ln -sfn "$PROJECT_ROOT" /opt/accos; PROJECT_ROOT="/opt/accos"; ok "Симлинк создан"
    fi
fi
chown -R accos:accos "$PROJECT_ROOT" 2>/dev/null || true

log "[4/9] Создание виртуального окружения..."
if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
    su - accos -c "cd '$PROJECT_ROOT' && python3 -m venv .venv"; ok ".venv создан"
else ok ".venv уже существует"; fi

log "[5/9] Установка Python зависимостей..."
su - accos -c "cd '$PROJECT_ROOT' && .venv/bin/pip install -q -r backend/requirements.txt"
ok "Python зависимости установлены"

log "[6/9] Сборка фронтендов..."
su - accos -c "cd '$PROJECT_ROOT/frontend' && npm install --silent && npm run build" 2>&1 | tail -1
ok "Frontend собран"
su - accos -c "cd '$PROJECT_ROOT/admin' && npm install --silent && npm run build" 2>&1 | tail -1
ok "Admin собран"

log "[7/9] Настройка PostgreSQL..."
DB_NAME="${DB_NAME:-accos}"; DB_USER="${DB_USER:-accos}"; DB_PASS="${DB_PASS:-}"
if [[ -z "$DB_PASS" ]]; then DB_PASS=$(openssl rand -base64 24); warn "Пароль БД: $DB_PASS (сохраните!)"; fi
systemctl start postgresql
su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'\" | grep -q 1 || psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\"" 2>&1
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='$DB_NAME'\" | grep -q 1 || createdb -O $DB_USER $DB_NAME" 2>&1
ok "PostgreSQL: БД $DB_NAME, пользователь $DB_USER"

log "[8/9] Настройка конфигурации..."
SERVER_IP=$(ip route get 1 | awk '{print $NF; exit}')
echo ""; warn "=== Настройка сети ==="
echo "Обнаружен IP сервера: $SERVER_IP"
echo -n "Введите IP для доступа (Enter для $SERVER_IP): "; read -r CUSTOM_IP; CUSTOM_IP="${CUSTOM_IP:-$SERVER_IP}"
echo -n "Введите порт ACCOS (Enter для 8000): "; read -r APP_PORT; APP_PORT="${APP_PORT:-8000}"
echo -n "Введите порт Nginx (Enter для 80): "; read -r NGINX_PORT; NGINX_PORT="${NGINX_PORT:-80}"
ENV_FILE="$PROJECT_ROOT/config/.env"; ENV_EXAMPLE="$PROJECT_ROOT/config/.env.example"
if [[ ! -f "$ENV_FILE" ]]; then cp "$ENV_EXAMPLE" "$ENV_FILE"; ok "Создан config/.env"; fi
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME|" "$ENV_FILE"
sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=[\"http://$CUSTOM_IP\",\"http://$CUSTOM_IP:$NGINX_PORT\"]|" "$ENV_FILE"
JWT_SECRET=$(openssl rand -base64 32)
sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" "$ENV_FILE"
ok "Конфигурация обновлена"

log "[9/9] Настройка Nginx..."
echo -n "Включить HTTPS? [y/N]: "; read -r USE_HTTPS; SSL_CONFIG=""
if [[ "$USE_HTTPS" =~ ^[yY] ]]; then
    mkdir -p /etc/nginx/ssl
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout /etc/nginx/ssl/accos.key -out /etc/nginx/ssl/accos.crt -subj "/C=RU/CN=$CUSTOM_IP" 2>&1
    SSL_CONFIG="listen $NGINX_PORT ssl;\n    ssl_certificate /etc/nginx/ssl/accos.crt;\n    ssl_certificate_key /etc/nginx/ssl/accos.key;"
    ok "Самоподписанный SSL создан"
else SSL_CONFIG="listen $NGINX_PORT;"; fi

cat > /etc/nginx/sites-available/accos.conf << NGINX_EOF
server {
    $SSL_CONFIG
    server_name $CUSTOM_IP;
    client_max_body_size 100M;

    location / {
        root $PROJECT_ROOT/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    location /admin/ {
        alias $PROJECT_ROOT/static/admin/;
        index index.html;
        try_files \$uri \$uri/ /admin/index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    location /static/ {
        alias $PROJECT_ROOT/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    location /docs {
        proxy_pass http://127.0.0.1:$APP_PORT/docs;
        proxy_set_header Host \$host;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/accos.conf /etc/nginx/sites-enabled/accos.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t 2>&1; systemctl restart nginx; ok "Nginx настроен"

log "[10] Создание systemd сервиса..."
cat > /etc/systemd/system/accos.service << SYSTEMD_EOF
[Unit]
Description=ACCOS Backend
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=accos
Group=accos
WorkingDirectory=$PROJECT_ROOT/backend
Environment=CONFIG_DIR=$PROJECT_ROOT/config
ExecStart=$PROJECT_ROOT/.venv/bin/uvicorn main:app --host 127.0.0.1 --port $APP_PORT --workers 4
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

systemctl daemon-reload; systemctl enable accos.service; ok "systemd сервис создан"

log "[11] Применение миграций БД..."
su - accos -c "cd '$PROJECT_ROOT/backend' && CONFIG_DIR='$PROJECT_ROOT/config' ../.venv/bin/alembic -c '$PROJECT_ROOT/config/alembic.ini' upgrade head" 2>&1
ok "Миграции применены"

log "[12] Создание директорий..."
mkdir -p "$PROJECT_ROOT/static/generated" "$PROJECT_ROOT/static/uploads" "$PROJECT_ROOT/static/avatars" \
    "$PROJECT_ROOT/static/knowledge" "$PROJECT_ROOT/static/edits" "$PROJECT_ROOT/static/videos" \
    "$PROJECT_ROOT/static/templates" "$PROJECT_ROOT/static/admin" \
    "$PROJECT_ROOT/backend/logs" "$PROJECT_ROOT/workflows"
cp -a "$PROJECT_ROOT/admin/dist/." "$PROJECT_ROOT/static/admin/" 2>/dev/null || true
chown -R accos:accos "$PROJECT_ROOT/static" "$PROJECT_ROOT/backend/logs"
ok "Директории созданы"

systemctl start accos.service; sleep 2
if systemctl is-active --quiet accos.service; then ok "ACCOS сервис запущен"
else warn "Сервис не запустился. Проверьте: journalctl -u accos.service"; fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Установка ACCOS завершена!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  Frontend:   ${CYAN}http://$CUSTOM_IP:$NGINX_PORT${NC}"
echo -e "  Admin:      ${CYAN}http://$CUSTOM_IP:$NGINX_PORT/admin${NC}"
echo -e "  API Docs:   ${CYAN}http://$CUSTOM_IP:$NGINX_PORT/docs${NC}"
echo ""
echo -e "  Admin login:  admin / admin123 (смените пароль!)"
echo ""
echo -e "  Управление:"
echo -e "    systemctl start|stop|restart|status accos.service"
echo -e "    journalctl -u accos.service -f"
echo ""
if [[ -z "${DB_PASS_SET+}" ]]; then echo -e "  Пароль БД: $DB_PASS"; fi
echo ""
