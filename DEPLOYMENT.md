# Развёртывание ACCOS

## Содержание

1. [Требования](#1-требования)
2. [Быстрый старт (Windows)](#2-быстрый-старт-windows)
3. [Быстрый старт (Debian 12+)](#3-быстрый-старт-debian-12)
4. [Production-развёртывание](#4-production-развёртывание)
   - [Windows (production)](#41-windows-production)
   - [Debian (nginx + systemd)](#42-debian-nginx--systemd)
5. [Настройка после установки](#5-настройка-после-установки)
6. [Обслуживание](#6-обслуживание)
7. [Устранение неполадок](#7-устранение-неполадок)

---

## 1. Требования

### Аппаратные

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| CPU | 2 ядра | 4+ ядра |
| RAM | 4 ГБ | 8+ ГБ |
| Диск | 10 ГБ | 50+ ГБ (для изображений) |

### Программные

| Компонент | Windows | Debian 12+ |
|-----------|---------|------------|
| Python | 3.11+ | 3.11+ |
| PostgreSQL | 17 | 17 |
| Node.js | 18+ | 18+ |
| npm | 9+ | 9+ |
| Nginx | — | optional |
| Git | optional | optional |

### Внешние сервисы

| Сервис | Назначение | Порт |
|--------|------------|------|
| **LMStudio** | LLM для чата | 1234 |
| **ComfyUI** | Генерация/редактирование изображений | 8188 |
| **LDAP/AD** | Аутентификация пользователей | 389 |

---

## 2. Быстрый старт (Windows)

### Автоматическая установка

```powershell
# Из корня проекта:
.\scripts\install_windows.ps1
```

Скрипт выполнит:
1. Проверку Python, Node.js, npm, PostgreSQL
2. Создание `.venv` и установку Python-зависимостей
3. Установку Node-зависимостей (frontend + admin)
4. Копирование `config/.env.example` → `config/.env`
5. Создание директорий `static/generated/`, `static/uploads/`, `backend/logs/`
6. Применение миграций БД (alembic upgrade head)
7. Сборку frontend и admin

### Ручная установка

```powershell
# 1. Виртуальное окружение
cd backend
python -m venv ..\.venv
..\.venv\Scripts\pip install -r requirements.txt

# 2. База данных
# Создайте БД accos в PostgreSQL 17
..\.venv\Scripts\alembic -c ..\config\alembic.ini upgrade head

# 3. Конфигурация
# Скопируйте и отредактируйте:
copy ..\config\.env.example ..\config\.env
# notepad ..\config\.env

# 4. Фронтенды
cd ..\frontend
npm install && npm run build

cd ..\admin
npm install && npm run build

# 5. Директории
mkdir ..\static\generated, ..\static\uploads, backend\logs -Force

# 6. Запуск (development)
cd ..\backend
..\.venv\Scripts\uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Запуск (dev-режим)

```powershell
# Терминал 1 — бэкенд
.\scripts\start_server.ps1 -Dev

# Терминал 2 — frontend
cd frontend
npm run dev          # → http://localhost:3000

# Терминал 3 — admin
cd admin
npm run dev          # → http://localhost:5173
```

---

## 3. Быстрый старт (Debian 12+)

### Автоматическая установка

```bash
# Из корня проекта (от root или через sudo):
sudo bash scripts/install_debian.sh
```

Скрипт выполнит:
1. Установку системных пакетов (python3, postgresql, nginx, nodejs, openssl)
2. Создание пользователя `accos`
3. Настройку проекта (опционально — симлинк в `/opt/accos`)
4. Создание `.venv` и установку Python-зависимостей
5. Сборку frontend и admin
6. Настройку PostgreSQL (создание БД `accos` и пользователя)
7. Генерацию `config/.env` с:
   - Паролем БД (авто)
   - CORS_ORIGINS (опрос IP)
   - JWT_SECRET_KEY (авто, openssl)
8. Настройку Nginx (опрос порта/HTTPS)
9. Создание systemd-сервиса `accos.service`
10. Применение миграций БД
11. Запуск сервиса

### Ручная установка

```bash
# 1. Системные зависимости
sudo apt update && sudo apt install -y \
    python3 python3-venv python3-pip \
    postgresql postgresql-client \
    nginx nodejs npm openssl

# 2. Виртуальное окружение
cd /opt/accos   # или ваш путь
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

# 3. База данных
sudo -u postgres psql -c "CREATE USER accos WITH PASSWORD 'strong-password';"
sudo -u postgres psql -c "CREATE DATABASE accos OWNER accos;"

# 4. Конфигурация
cp config/.env.example config/.env
# Отредактируйте config/.env:
#   DATABASE_URL=postgresql+asyncpg://accos:strong-password@localhost:5432/accos
#   CORS_ORIGINS=["http://10.0.0.100:80", "http://localhost:3000"]
#   JWT_SECRET_KEY=<openssl rand -base64 32>

# 5. Миграции
.venv/bin/alembic -c config/alembic.ini upgrade head

# 6. Сборка фронтендов
cd frontend && npm install && npm run build
cd ../admin && npm install && npm run build
cd ..

# 7. Директории
mkdir -p static/generated static/uploads backend/logs
chown -R accos:accos static backend/logs

# 8. Запуск (development)
cd backend
../.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 4. Production-развёртывание

### 4.1 Windows (production)

```powershell
# Запуск сервера с 4 воркерами (без --reload)
.\scripts\start_server.ps1 -Port 8000 -Workers 4
```

**Рекомендации для Windows production:**

- Используйте **NSSM** (Non-Sucking Service Manager) для запуска uvicorn как службы Windows:

```powershell
# Установка NSSM
choco install nssm  # или скачайте с https://nssm.cc

# Создание службы
nssm install ACCOS "C:\Github\ACCOS\.venv\Scripts\uvicorn.exe"
nssm set ACCOS AppParameters "main:app --host 127.0.0.1 --port 8000 --workers 4"
nssm set ACCOS AppDirectory "C:\Github\ACCOS\backend"
nssm set ACCOS AppEnvironmentExtra "CONFIG_DIR=C:\Github\ACCOS\config"
nssm set ACCOS Start SERVICE_AUTO_START
nssm start ACCOS
```

- Настройте **файрвол**: откройте порт 8000
- Включите `RATE_LIMITS_ENABLED=true` в `config/.env`
- Смените `JWT_SECRET_KEY` на сгенерированный
- Установите `LOG_LEVEL=INFO` (убирает traceback из ответов API)
- Для HTTPS используйте Nginx на Windows или reverse-proxy на отдельном сервере

### 4.2 Debian (nginx + systemd)

#### Структура после установки

```
/etc/nginx/sites-available/accos.conf  # конфигурация Nginx
/etc/systemd/system/accos.service       # systemd-сервис
/etc/nginx/ssl/accos.crt                # SSL-сертификат (если включён)
/etc/nginx/ssl/accos.key                # SSL-ключ (если включён)
```

#### Проверка статуса

```bash
# Статус сервиса
systemctl status accos.service

# Логи
journalctl -u accos.service -f

# Статус Nginx
systemctl status nginx

# Перезапуск
sudo systemctl restart accos.service
sudo systemctl reload nginx
```

#### Обновление после изменений

```bash
# После изменения кода:
cd /opt/accos
git pull                           # если используется git

# Бэкенд
sudo -u accos .venv/bin/pip install -q -r backend/requirements.txt
sudo -u accos .venv/bin/alembic -c config/alembic.ini upgrade head

# Фронтенды
cd frontend && sudo -u accos npm install && sudo -u accos npm run build
cd ../admin && sudo -u accos npm install && sudo -u accos npm run build
cd ..

# Перезапуск
sudo systemctl restart accos.service

# Если менялась конфигурация Nginx:
sudo nginx -t && sudo systemctl reload nginx
```

#### Настройка HTTPS (вручную)

Если при установке HTTPS не был включён, можно добавить позже:

```bash
# 1. Получите Let's Encrypt сертификат (если есть домен)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 2. Или создайте самоподписанный
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/accos.key \
    -out /etc/nginx/ssl/accos.crt \
    -subj "/C=RU/CN=10.0.0.100"   # замените на ваш IP

# 3. Раскомментируйте listen 443 ssl в /etc/nginx/sites-available/accos.conf
sudo nginx -t && sudo systemctl reload nginx
```

---

## 5. Настройка после установки

### 5.1 config/.env

Минимальные обязательные параметры:

| Параметр | Обязательный | Как получить |
|----------|-------------|--------------|
| `DATABASE_URL` | да | Данные вашего PostgreSQL |
| `JWT_SECRET_KEY` | да | `openssl rand -base64 32` |
| `CORS_ORIGINS` | да | IP сервера (пример: `["http://10.0.0.100:80"]`) |
| `LMSTUDIO_BASE_URL` | да | URL вашего LMStudio |
| `COMFYUI_BASE_URL` | да | URL вашего ComfyUI |

### 5.2 Администратор

После первого запуска войдите как `admin / admin123`. **Смените пароль** через Admin Panel:

```
Admin Panel → Пользователи → admin → Редактировать
```

Или через API:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token' > /tmp/token

curl -X PUT http://localhost:8000/api/v1/admin/users/<user_id> \
  -H "Authorization: Bearer $(cat /tmp/token)" \
  -H "Content-Type: application/json" \
  -d '{"password":"new-secure-password"}'
```

### 5.3 Rate limiting

По умолчанию включён (`RATE_LIMITS_ENABLED=true`). Лимиты:

| Эндпоинт | Лимит | Защита от |
|----------|-------|-----------|
| `POST /auth/login` | 5/min | Брутфорс паролей |
| `POST /generate/` | 10/min | Злоупотребление генерацией |
| `POST /chat/*/send` | 30/min | Спам в чат |
| GET-запросы | 30–60/min | Чтение |

Для отладки: `RATE_LIMITS_ENABLED=false` (не отключайте на production).

### 5.4 Безопасность в локальной сети

При развёртывании в локальной сети без домена:

1. **JWT передаётся без HTTPS** — в доверенной сети приемлемо, но:
   - Установите короткое время жизни токена: `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15`
   - Включите самоподписанный HTTPS (см. выше)
2. **CORS_ORIGINS** — укажите IP сервера, а не `localhost`
3. **Смените ADMIN_PASSWORD** в `.env` (используется только как fallback при недоступности LDAP)
4. **LOG_LEVEL=INFO** на production (скрывает traceback из ответов API)

---

## 6. Обслуживание

### 6.1 Тестирование

```bash
# Полный прогон тестов (из корня проекта):
npm test

# Или по отдельности:
cd backend && .venv/bin/python -m pytest tests -v
cd frontend && npx vitest run
```

### 6.2 Резервное копирование

```bash
# База данных
pg_dump -U accos accos > /backup/accos_$(date +%Y%m%d).sql

# Изображения
tar -czf /backup/accos_static_$(date +%Y%m%d).tar.gz \
  -C /opt/accos static/generated static/uploads
```

### 6.3 Миграции БД

При изменении моделей (`backend/app/db/models/`):

```bash
# Создать новую миграцию
.venv/bin/alembic -c config/alembic.ini revision --autogenerate -m "description"

# Применить
.venv/bin/alembic -c config/alembic.ini upgrade head
```

### 6.4 Логи

```
backend/logs/accos.log        # Основной лог
journalctl -u accos.service   # systemd (Debian)
```

Ротация логов настраивается через `logging.handlers.RotatingFileHandler` в `main.py`.

---

## 7. Устранение неполадок

### Сервер не запускается

```bash
# Проверка синтаксиса Python
cd backend
python -c "from main import app; print('OK')"

# Проверка подключения к БД
python -c "from app.db.session import engine; import asyncio; asyncio.run(engine.connect())"

# Проверка конфигурации
python -c "from app.core.config import settings; print(settings.database_url)"
```

### Ошибка 502 Bad Gateway (Debian)

```bash
# Nginx не видит uvicorn
sudo systemctl status accos.service
sudo journalctl -u accos.service -n 50

# Возможные причины:
# — uvicorn не запущен → sudo systemctl restart accos.service
# — Порт не совпадает → проверьте PORT в /etc/systemd/system/accos.service и nginx
# — Файрвол → sudo ufw allow 8000
```

### ComfyUI не отвечает

```bash
# Проверьте в config/.env:
#   COMFYUI_BASE_URL=http://<ip>:8188
# Убедитесь, что ComfyUI запущен:
curl http://<ip>:8188/
```

### LDAP не работает

- По умолчанию включён `MockLDAPAdapter` — работает всегда (admin/admin123)
- Для реального LDAP настройте: `LDAP_SERVER`, `LDAP_DOMAIN`, `LDAP_BASE_DN`
- Если LDAP недоступен, `AuthService` падает на Mock-адаптер автоматически

### Чат не отвечает (LMStudio)

```bash
# Проверьте:
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hello"}]}'

# LMStudio должен быть запущен с флагом --cors
```
