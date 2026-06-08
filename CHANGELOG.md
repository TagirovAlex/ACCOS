# Changelog ACCOS

## Phase 0 — Setup & Core DB
- Инициализирован FastAPI проект
- Созданы SQLAlchemy модели: User, ChatSession, ChatMessage, GenerationRecord, ImageAsset, AdminSettings
- Настроен Alembic (async), создана и применена initial migration
- Реализован базовый CRUD через Repository Pattern
- Созданы: BaseModule, BaseAdapter (абстракции)
- Созданы: config, security (JWT + bcrypt), dependencies, exceptions
- Создана структура для тестов

## Phase 1 — Auth & Economy Core
- Реализован адаптер LDAP (реальный + Mock для разработки)
- Реализован AuthService (login через LDAP, создание пользователя, JWT)
- Реализован EconomyService (Strategy Pattern: LLM, Image Gen, Image Edit, Video Gen)
- Созданы эндпоинты:
  - `POST /api/v1/auth/login` — аутентификация
  - `GET /api/v1/auth/me` — информация о пользователе
  - `GET /api/v1/user/balance` — баланс пользователя
- Новые пользователи получают стартовый баланс 100 кредитов
- Фикс: транзакции БД теперь корректно коммитятся через `async with session.begin()`

## Phase 5 — Admin API + Admin Panel (React)
- Созданы Admin API эндпоинты: /admin/users, /admin/groups, /admin/chats, /admin/generations, /admin/assets, /admin/settings
- Реализован AdminService (list, create, update, delete для всех ресурсов)
- Добавлены недостающие эндпоинты: GET/PUT/DELETE /admin/users/{id}, DELETE /admin/groups/{id}
- Настроена React Admin Panel (Vite + react-admin + MUI)
- Реализована поддержка тёмной/светлой темы (MUI ThemeProvider + localStorage)
- Создана структура admin/src/assets/themes/ (light.ts, dark.ts)
- Настроен Vite proxy на backend (port 8000)
- Настроен CORS для admin dev server (port 5173)
- Интерфейс админ-панели полностью на русском языке

## Phase 6 — User Frontend (React)
- Создана структура frontend/ (Vite + React + TypeScript + MUI)
- Реализована страница логина (с интеграцией /auth/login)
- Реализован дашборд с отображением баланса и прав
- Реализован интерфейс чата (список сессий, отправка/получение сообщений)
- Реализована страница генерации (выбор workflow, промпт, результат)
- Настроена маршрутизация (react-router-dom)
- Переключатель тёмной/светлой темы
- Настроен Vite proxy на backend (port 8000)

## Workflow (Phase 3)
- 4 из 6 workflow готовы: ZIT.json, QWEN edit 1/2/3 pic.json
- text_to_video.json, image_to_video.json — зарезервированы (будут позже)

## Rate limiting + Frontend tests + Preview + Polish
- **Структурированные ошибки на бэкенде:** `error_id`, `status_code`, `request` (method, path, query), `traceback` (в DEBUG), отдельный обработчик для `HTTPException`
- **ErrorPage.tsx** — отдельная страница ошибки с HTTP статусом, сообщением, error_id, чипсами метода/пути, стектрейсом в DEV, кнопками "Назад" / "Повторить" / "Обновить"
- **ErrorBoundary** (оба фронтенда) — показывает ErrorPage при React-сбое с componentStack
- **ApiError класс** — все HTTP ошибки кидают `ApiError` со статусом, error_id и деталями из бэкенда
- **JWT Refresh Token:** `POST /auth/refresh` (refresh token живёт 7 дней). При логине возвращается `refresh_token`. 401 → `tryRefresh()` → повтор запроса
- **Удаление чатов:** `DELETE /chat/{session_id}` + кнопка с корзиной + Dialog подтверждения
- **Loading skeletons:** в GenerationPage при загрузке истории

## Deployment scripts + Security doc
- **Скрипты установки:** `scripts/install_windows.ps1` (Windows) и `scripts/install_debian.sh` (Debian 12+)
  - Windows: проверка Python/Node.js, .venv, pip/npm install, сборка фронтендов, миграции БД
  - Debian: + установка system пакетов (nginx, postgresql, nodejs), создание пользователя, настройка PostgreSQL, nginx reverse-proxy (опрос IP/порта/HTTPS), systemd сервис
- **Production веб-сервер:** uvicorn (workers=4) → nginx reverse-proxy (Debian) или прямой uvicorn (Windows)
  - Nginx отдаёт статику (frontend, admin, /static/) напрямую, проксирует /api/ на uvicorn
  - systemd для авто-восстановления (Debian)
  - Скрипт `scripts/start_server.ps1` для Windows (dev/prod режимы)
- **JWT в локальной сети:** без HTTPS токены в открытом виде — документировано в .env.example
  - Рекомендации: короткое время жизни токена (15-30 мин), самоподписанный HTTPS (опция в install_debian.sh)
  - CORS_ORIGINS теперь указывается IP сервера, а не localhost
- Обновлён `config/.env.example` с комментариями по локальному развёртыванию

## ComfyUI workflow fix + Image resize + Tech Debt
- **ComfyUI `_apply_prompt` исправлен:** заменял `__image_N__` (не существовали) → теперь находит `LoadImage` nodes и устанавливает `inputs.image` из списка загруженных файлов по порядку; устанавливает `inputs.text`/`inputs.prompt` только если поле пустое
- **`upload_image()` исправлен:** возвращает `name` из ответа ComfyUI (а не `os.path.basename`)
- **Image resize:** в `POST /generate/upload` добавлено пропорциональное сжатие до 2048px по длинной стороне (Pillow), PNG с прозрачностью → RGB
- **Qwen Edit workflow:** добавлен `POST /generate/upload`, `reference_images` в `GenerateRequest`, передача через `result_path` (JSON). Frontend: загружает файлы → `/generate/` с `reference_images`
- **ChatPage markdown:** добавлен `SimpleMarkdown` (код блоки, жирный/курсив, моноширинный) для ассистента
- **Dead code:** удалён `start_accrual_scheduler()` (APScheduler) из `requirements.txt`, `run_auto_accrual()` возвращает интервал из БД
- **Error Boundaries:** добавлены в оба фронтенда
- Добавлен Pillow в зависимости

## Admin Panel — полная реализация (Phase 5)
- **Бэкенд: новые endpoints:**
  - `POST /admin/users` — создание пользователя с паролем, is_admin, is_active, permissions
  - `PUT /admin/users/{id}` — добавлена возможность менять is_admin, пароль
  - `GET /admin/chats/{id}` — детальный просмотр чата с сообщениями (роль, контент, стоимость)
  - `GET /admin/generations/{id}` — детальный просмотр генерации с изображениями
  - `GET /admin/assets/{id}` — детальный просмотр ресурса с превью
  - `GET /admin/dashboard` — статистика (users, groups, chats, generations, assets)
  - `POST /admin/settings` — создание новой настройки
  - `DELETE /admin/settings/{key}` — удаление настройки
- **Admin Service:** добавлены `create_user`, `get_chat_detail`, `get_generation_detail`, `get_asset_detail`, `create_setting`, `delete_setting`, `get_dashboard_stats`
- **Admin Panel (React):**
  - **Users:** форма создания — пароль, is_admin, is_active, permissions; форма редактирования — смена пароля, is_admin, is_active
  - **Chats:** детальный просмотр с лентой сообщений (user/assistant баблы, стоимость)
  - **Generations:** детальный просмотр с превью изображений, метаданными (width, height, error)
  - **Assets:** детальный просмотр с превью, информацией о файле, ссылками на пользователя/генерацию
  - **Settings:** полноценный CRUD — список, создание, редактирование, удаление
  - **Dashboard:** 5 карточек статистики с иконками, быстрые действия (+ пользователь, + группа, + настройка)
  - DataProvider: полная поддержка create/delete для settings, extractId для всех ресурсов

## Async ComfyUI Queue + Frontend Fixes
- Добавлен **ComfyUI Queue Worker** (`backend/app/services/queue_worker.py`):
  - Фоновый asyncio-воркер, каждые 2с проверяет `generation_records` со статусом `queued`
  - Запускает генерацию через ComfyUI, скачивает изображения в `static/generated/`
  - Обновляет статус: `queued → processing → completed/failed`
  - При ошибке автоматически возвращает средства на баланс
- **Generation endpoint** переделан: `POST /generate/` создаёт запись со статусом `queued` и возвращает `generation_id` сразу (не блокирует HTTP-запрос)
- Добавлен **Status endpoint**: `GET /generate/{id}/status` — проверка статуса генерации + список изображений
- Добавлен **`download_image`** в ComfyUIAdapter — скачивание готовых изображений с ComfyUI-сервера
- Добавлена **пагинация** во все admin list-эндпоинты (skip/limit)
- **Frontend GenerationPage** — полностью переработана:
  - Отображение сгенерированных изображений (через `/static/generated/...`)
  - Поля для загрузки референс-изображений (для Qwen Edit workflow)
  - Polling статуса генерации (каждые 2с до завершения)
  - Боковая панель истории генераций
  - Workflow типы приведены к единому формату: `z_image`, `qwen_edit_1/2/3`
- **Frontend ChatPage** — улучшена обработка ошибок:
  - При ошибке отправки сообщение пользователя сохраняется с пометкой об ошибке (вместо удаления)
  - Snackbar-уведомления об ошибках
  - Индикатор "ассистент печатает..."
  - Empty state для списка чатов и сообщений
- **Frontend App.tsx** — исправлен двойной вызов `getMe()` при логине
- **Admin dataProvider** — исправлена передача параметров пагинации, сортировки и фильтрации
- **main.py** — Queue Worker запускается в lifespan вместе с accrual scheduler

## Fixes & Enhancements
- Исправлены тесты: 26/26 проходят (было 9 pass, 2 fail, 16 error)
  - EconomyService.calculate_cost сделан classmethod
  - Исправлены имена параметров в тестах (input_tokens→tokens_input, ref_size→avg_ref_size)
  - Исправлен конфиг тестовой БД: NullPool для избежания блокировок asyncpg
  - Исправлены пути моков в тестах (прямое мокирование адаптеров вместо сервисов)
  - Исправлены форматы возвращаемых значений моков
- Добавлен автоаккреал баланса (asyncio background task, каждые 3600с)
  - Настройки: auto_accrual_interval_minutes, auto_accrual_amount (AdminSettings)
- Добавлена опция pool_pre_ping в engine для продакшена
