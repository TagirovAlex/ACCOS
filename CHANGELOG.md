# Changelog ACCOS

## Phase 2 — Documentation Scraper (Jun 14)
- **Model**: `doc_scrape_jobs` — хранение задач скрапинга (статус, прогресс, ошибки)
- **Migration**: `5c2755f18c3d` — add_doc_scrape_jobs_table
- **DocScraperAdapter**: BFS-краулер на httpx + trafilatura + BeautifulSoup, 6 фильтров исключения, задержка 0.5с
- **DocScraperService**: оркестрация crawl → chunk → embed → ingest в RAG через KnowledgeChunks
- **Admin API**: `POST /admin/doc-scraper/scrape`, `GET /admin/doc-scraper/jobs`, `POST cancel/retry`, `DELETE /sites/{name}`
- **Admin UI**: MUI страница "📚 Doc Scraper" в админке, диалог запуска, статусы, cancel/retry/delete
- **Chunking**: семантическая разбивка по абзацам, chunk_size/overlap из настроек RAG
- **Bugfix**: миграция `e5f4d3c2b1a0` — FK user_id исправлен с String(36) на Uuid для совместимости с users.id

## Phase 1C — Web Fetch Module: MCP Server for LM Studio (Jun 14)
- **MCP WebFetch сервер**: порт 8100, SSE transport, два инструмента — `fetch_web_page` и `search_in_page`
- **Server**: запускается в lifespan main.py как фоновый uvicorn, использует `WebFetchAdapter` для загрузки
- **LM Studio конфиг**: `config/lmstudio_mcp_servers.json` — SSE endpoint для подключения
- **Dependency**: `mcp>=1.27.0` (MCP Python SDK + sse-starlette)
- **FastAPI upgrade**: 0.115.0 → 0.136.3 (совместимость со starlette 1.x от MCP SDK)

## Phase 1B — Web Fetch Module: Backend + Admin UI (Jun 14)
- **WebFetchRepository**: CRUD + upsert + domain validation per user
- **WebFetchService**: URL auto-detection (regex), permission chain (global → user permission → per-user enabled → domains), trafilatura extraction
- **ChatService.send_message**: автоматический детект URL в сообщении → fetch → инжект в system prompt (вслед за RAG)
- **Admin API**: `GET /admin/web-fetch/permissions`, `GET/PUT /admin/web-fetch/permissions/{user_id}`
- **Admin UI**: новая страница «Web Fetch» — таблица пользователей с toggles, лимитами, доменами, inline-редактирование через диалог
- **Право `web`**: добавлено в default_permissions, проверяется в WebFetchService.check_user_permission
- **Pydantic схемы**: `WebFetchPermissionUpdate`, `WebFetchPermissionResponse`, `WebFetchPermissionListResponse`

## Phase 1A — Web Fetch Module: Database + Adapter (Jun 14)
- **Model `web_fetch_permissions`**: новая таблица с per-user настройками (enabled, лимиты, домены)
- **Migration**: `e5f4d3c2b1a0_add_web_fetch_permissions_table`
- **WebFetchAdapter**: `httpx` + `trafilatura` → извлекает контент URL в markdown, блокирует бинарные типы/расширения
- **Admin settings**: 5 новых ключей — `web_fetch_enabled/max_size/timeout/blocked_extensions/blocked_domains`
- **Dependencies**: `trafilatura==2.0.0`, `beautifulsoup4==4.12.3`

## Block 5 — LLM Server Management + UI Fixes (Jun 11)
- **Model `llm_servers`**: новая таблица + миграция `a1b2c3d4e5f6`
- **CRUD API `/admin/llm-servers`**: создание, список, редактирование, удаление, тест соединения
- **Batch document upload**: новый эндпоинт `POST /api/v1/knowledge/upload-batch` + multi-file выбор в админке и пользовательском интерфейсе
- **Admin UI «LLM-серверы»**: страница с list/tiles toggle, добавление/редактирование серверов, кнопка «Тест»
- **Dashboard**: редизайн карточек (StatCard вместо InfoBox), компактнее, чище
- **Backups**: добавлен tile/row toggle
- **Groups**: карточки книжная ориентация (описание, чипы прав, стартовый баланс)
- **Chats**: карточки книжная ориентация (статус, кол-во сообщений)
- **Documents**: root view папок отделов — добавлен list/tiles toggle

## Block 3 — RAG Tuning UI (Jun 10)
- **Reindex-all/new/failed**: Массовая переиндексация всех/новых/упавших документов
- **KnowledgeActions**: Кнопки "Переиндексировать всё", "Новые", "Упавшие" на страницах Settings + Documents
- **Настройки расписания**: `reindex_schedule_enabled`, `reindex_cron`, `reindex_mode`

## Block 4 — Reindex Scheduler (Jun 10)
- **apscheduler**: Фоновый cron-планировщик для автоиндексации
- **scheduler_service.py**: Запуск/остановка планировщика при старте/остановке приложения
- **Автообновление расписания**: При изменении настроек планировщика через Admin API

## Phase 3 — RAG Knowledge Base (Jun 10)
- **KnowledgeDocument/KnowledgeChunk**: Модели БД для базы знаний (chunk + embedding Vector(1536))
- **KnowledgeRepository**: CRUD, поиск, векторный поиск (cosine similarity через pgvector)
- **RAGAdapter**: Адаптер для `/v1/embeddings` (LM Studio OpenAI-compatible API)
- **RAGService**: Извлечение текста (PDF/docx/image OCR), чанкинг (tiktoken), индексация, поиск
- **KnowledgeService**: Фасад над RAGService + KnowledgeRepository для endpoints
- **Knowledge endpoints**: upload, list, get, delete, replace, reindex, search, folders
- **Chat RAG injection**: В `send_message` — поиск релевантных чанков по user.ad_group_dns, инжект в system prompt
- **Queue worker**: `enqueue_knowledge_index(doc_id)` — асинхронная индексация после загрузки
- **Settings**: 7 новых ключей — `ad_clients_ou`, `rag_enabled`, `rag_embedding_model`, `rag_chunk_size/overlap`, `rag_top_k`, `rag_min_score`
- **Model fix**: KnowledgeDocument.error_message (Text, nullable)

## Multi-Node ComfyUI (Jun 10)
- **ComfyUIAdapter**: `base_url` теперь параметр конструктора, не читается из `settings`
- **Config**: Добавлены `comfyui_generate_base_url`, `comfyui_edit_base_url`, `comfyui_video_base_url` (опционально)
- **Settings**: 3 новых ключа в админке — URL для генерации, редактирования и видео отдельно
- **Queue worker**: Выбор ноды ComfyUI по `workflow_type` (z_image → generate, qwen → edit, video → video)
- **Admin panel**: Поля в форме настроек с русскими названиями
- **comfyui_service.py**: Убран неиспользуемый импорт ComfyUIAdapter
- **Backwards compatible**: Если новые поля пусты — всё идёт на `comfyui_base_url` как раньше

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

## SettingsService + LDAP/Economy в админке + Chat fix
- **SettingsService** (`backend/app/services/settings_service.py`) — читает настройки из DB (`admin_settings`) с fallback на `.env`
- **Seed на старте**: 18 настроек автоматически заполняются при первом запуске (LDAP, LMStudio, ComfyUI, цены, экономика)
- **Настройки LDAP** (`ldap_server`, `ldap_domain`, `ldap_base_dn`) — теперь в админ-панели, редактируются через Settings
- **Настройки экономики** (цены LLM, Image Gen, Image Edit, Video Gen, автоаккреал) — читаются из DB, редактируются через Settings
## API Token Auth — LMStudio + ComfyUI
- **LMStudioAdapter**: добавлен параметр `api_key` — передаётся в HTTP-заголовок `Authorization: Bearer <token>`, fallback на `settings.lmstudio_api_key`
- **ComfyUIAdapter**: добавлен параметр `api_key` — передаётся в HTTP-заголовок `x-api-key`, fallback на `settings.comfyui_api_key`
- **ChatService**: при отправке сообщения читает `lmstudio_api_key` из БД (SettingsService) и передаёт в LMStudioAdapter
- **QueueWorker**: при обработке генерации читает `comfyui_api_key` из БД и передаёт в ComfyUIAdapter
- **Seed defaults**: добавлены `lmstudio_api_key` и `comfyui_api_key` (пустые строки по умолчанию, заполняются через админку)
- Настройки `LMSTUDIO_API_KEY` и `COMFYUI_API_KEY` уже присутствуют в `config.py` и `.env.example`

## UI/UX — Design Pass & User Management Fixes
- **LDAPAdapter**: принимает параметры `server/domain/base_dn` (опционально, fallback на `.env`)
- **AuthService**: LDAP настройки читаются из DB через `SettingsService` каждый раз при логине
- **Chat validation error**: `ChatSendResponse.message/tokens_input/tokens_output/cost` — теперь опциональны с дефолтами
- **Все `calculate_cost()` вызовы**: исправлены на `await` (метод стал instance async)
- Тесты: 26/26 проходят
- Nginx: `/admin` → `/admin/` (trailing slash) + `alias` с trailing slash для корректной SPA маршрутизации
- Nginx: добавлен `location /openapi.json` (обратно-прокси на бэкенд), ранее уходил во frontend SPA
- Admin Vite config: добавлен `base: '/admin/'`, пересобраны assets с путями `/admin/assets/...`
- Frontend: удалены Google Fonts (`fonts.googleapis.com`) — все шрифты только системные (`Arial, Helvetica, sans-serif`)
- Admin/Frontend themes: добавлен `typography.fontFamily: 'Arial, Helvetica, sans-serif'`
- Fix: `backend/requirements.txt` — добавлены `passlib[bcrypt]==1.7.4` и `bcrypt==4.0.1` (отсутствовали)
- `scripts/install_debian.sh`: обновлён шаблон nginx (trailing slash + /openapi.json)

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

## UI/UX — Design Pass & User Management Fixes
### Backend
- **User schema**: `AdminUserCreate`, `AdminUserUpdate`, `AdminUserResponse` — добавлено поле `group_id: str | None`
- **AdminService**: `create_user`, `update_user`, `get_user`, `list_users` — теперь работают с `group_id`
- **Group endpoint**: добавлен `GET /admin/groups/{group_id}` (требовался react-admin ReferenceInput)
- **AdminGroupResponse** импортирован в admin endpoint

### Admin Frontend (React-admin)
- **Users.tsx**: добавлен `ReferenceInput source="group_id"` — выпадающий список групп AD для создания/редактирования пользователя
- **Users.tsx/Groups.tsx**: улучшены helperText для поля `permissions` — "chat — чат, generate — генерация, chat,generate — оба"
- **Users.tsx**: добавлено поле `full_name`

### User Frontend (React MUI)
- **SimpleMarkdown.tsx**: исправлен crash при `text === null/undefined` — добавлено `|| ""`
- **ChatPage.tsx**: `reply.content` — fallback на `""` при null
- **Themes (light/dark)**: добавлены `shape.borderRadius: 10`, компонент-оверрайды (`MuiCard` с тенью/hover, `MuiButton` скруглённый, `MuiPaper backgroundImage: none`)
- **LoginPage**: новый дизайн — градиентный фон, крупный Avatar/иконка ACCOS, улучшенные отступы
- **App.tsx**: улучшен AppBar — иконка ACCOS, баланс в Chip с иконкой кошелька, Avatar с инициалом пользователя, имя пользователя
- **DashboardPage**: карточки с цветными Avatar-иконками (баланс/пользователь/права/чат), компактная история со статусными лейблами
- **ChatPage**: аватары для user (зелёный) и assistant (синий), скруглённые "пузырьки", таймштампы, раздельный дизайн сообщений
- **GenerationPage**: улучшенный layout — иконки в заголовках, статусные Chip'ы, sticky история с кнопкой обновления, улучшенная карточка референс-изображений

## Session — Fixes & Domain Group Login Restriction
- **Admin panel**: Theme toggle moved inside UserMenu dropdown — no more overlap with logout button
- **Admin panel**: `TokenResponse` now includes `is_admin` field — login check for admin status works correctly
- **Admin panel**: Chat messages cost label changed from "кр." to "MS"
- **Admin panel**: Dark theme chat viewer — fixed white text on light background (grey.100→grey.800 in dark mode)
- **Admin panel**: Added backup management page (list, create, delete backups via pg_dump)
- **Auth**: New setting `require_ad_group_for_login` (default: false) — when enabled, only users belonging to a configured AD group can log in
- **Auth**: Admin user always bypasses the AD group check
- **User model**: Added `default_system_prompt` and `avatar_path` fields
- **User API**: New endpoints `GET/PUT /api/v1/user/profile`, `POST /api/v1/user/avatar` with 256×256 auto-crop
- **User frontend**: New ProfilePage (avatar upload, default system prompt, name/email editing)
- **Admin groups**: Interactive AD group selector (AutocompleteInput) — выбирает DN из LDAP, не нужно вводить вручную
- **LDAP**: Добавлены настройки `ldap_bind_dn`, `ldap_bind_password` для чтения групп из AD
- **LDAP**: Добавлен метод `list_groups(search)` в LDAPAdapter (фильтр по cn)
- **Admin API**: Новый эндпоинт `GET /api/v1/admin/ldap-groups?search=...`

## Fixes (Jun 08)
- **LDAP adapter**: Добавлена поддержка `bind_username` для NTLM-биндинга (DOMAIN\\username) при поиске групп — больше не требуется полный DN
- **LDAP adapter**: Добавлен метод `_bind_connection()` с приоритетом: bind_username → bind_dn → anonymous
- **Settings**: Добавлена настройка `ldap_bind_username` (имя учётной записи без домена)
- **Admin UI (LDAP)**: Поле "Учётная запись для поиска" изменено с DN на имя пользователя + хелптекст
- **ComfyUI adapter**: Фильтр `_poll_result` теперь собирает только `type=="output"` изображения, исключая temp/preview (исправляет дублирование изображений)
- **Frontend (App.tsx)**: `overflow-y: auto` добавлен в main-контейнер — исправлен скроллинг страницы
- **Frontend (GenerationPage)**: Добавлены `maxHeight: 600` + `overflowY: auto` в контейнер результатов — изображения не выходят за границу
- **SettingsService**: Исправлен синтаксис в seed_defaults (отсутствовала закрывающая скобка)

## Features (Jun 08)
- **Генерация**: Добавлен выбор разрешения через пресеты (8 предустановок: квадрат/портрет/ландшафт) + ручной ввод ширины/высоты
- **Генерация**: Предпросмотр загруженных референс-изображений (полная ширина карточки, соотношение сторон оригинала, checkerboard фон для прозрачности)
- **Генерация**: История теперь кликабельна — открывается диалог управления генерацией (скачать, удалить, отправить в редактирование Qwen, создать видео)
- **Генерация**: Подтверждение действий — диалог для редактирования (выбор workflow + промпт) и создания видео (промпт + длительность)
- **API**: `DELETE /api/v1/generate/{generation_id}` — пользователь может удалить свою генерацию (soft-delete)
- **Model**: GenerationRecord добавлено поле `deleted_at` (soft delete), миграция `fd9f90364766`
- **API**: `GET /api/v1/admin/ldap-test` — эндпоинт для проверки LDAP-подключения с детальным ответом об ошибке
- **LDAP adapter**: Метод `test_connection()` для проверки bind-а, `_sync_list_groups` теперь пробрасывает исключения наверх для правильной обработки ошибок
- **Seed**: Добавлено поле `seed` в форму генерации (пусто = -1 = случайный). Хранится в БД (generation_records.seed), миграция `943ce26f1ef3`. Передаётся в ComfyUI workflow (перезаписывает seed в KSampler)
- **Админка**: Ресурсы и Генерации — переключение список/плитка с превью, кнопка "Назад" в Show (Assets, Generations, Users), масштаб/размер изображений в ресурсах

## Admin Roles + Permission Split + Settings Fix (Jun 08)
- **DB**: Добавлены `admin_role` (VARCHAR 20) и `admin_group_id` (UUID FK → user_groups) в таблицу `users`, миграция `2f821ab49813`
- **Model**: User.group relationship — явно указан `foreign_keys=[group_id]` (фикс AmbiguousForeignKeyError от двух FK на user_groups)
- **Schemas**: `AdminUserResponse`, `UserInfoResponse`, `TokenResponse` — добавлено поле `admin_role`
- **Backend auth**: `_require_super_admin()` для dashboard/groups/chats/generations/assets/settings/backups/ldap; `_require_admin()` для users CRUD + balance
- **Admin panel**: `<Admin>{(permissions) => ...}</Admin>` — `group_admin` видит только users, `super_admin` — все 7 ресурсов
- **Permission split**: `WORKFLOW_PERMISSION` в `generation.py` — `generate` (z_image), `edit` (qwen_edit_1/2/3), `video` (text_to_video, image_to_video)
- **Frontend routes**: `/generate` → `mode="generate"`, `/edit` → `mode="edit"`, `/video` → `mode="video"`, `/history` → `mode="all"`
- **Dashboard**: 3 отдельных `HistorySection` (generate/edit/video) с per-section viewMode localStorage
- **Settings**: `isBoolean()` теперь key-whitelist, `isNumeric()` для числовых полей, `auto_accrual_time` (HH:MM серверное время)
- **Frontend sidebar**: Динамические navItems по `canGenerate/canEdit/canVideo/canChat`

## Bugfix batch (Jun 09)
- **Group create**: Исправлен ответ API — теперь возвращается полный объект группы с `id` на корневом уровне (react-admin dataProvider)
- **Asset delete**: Добавлена кнопка DeleteButton в AssetShow, uniform размер тайлов (aspectRatio 4/3), username в ответе API
- **Chats admin**: Добавлен переключатель список/плитка с localStorage
- **Token stats**: `token_stats` добавлены в AdminUserResponse, dashboard (total_tokens_input/output/llm_cost), list_users (агрегация через JOIN) и get_user
- **User frontend**: Клик по изображению результата открывает модальное окно с полноразмерным превью; улучшена обработка ошибок при загрузке истории
- **Asset schema**: `AdminAssetResponse` — добавлено поле `username`
- **Backend**: `list_all_assets` — eager load пользователя через `joinedload`, group create — расширенный возврат
- **ComfyUI resolution**: Добавлен `_apply_resolution` — при генерации ширина/высота теперь передаются в ноды `*LatentImage` воркфлоу (например, `EmptySD3LatentImage`), ранее размер игнорировался
- **File manager fix**: `FileEntry.modified` schema изменён с `str` на `float` (была Pydantic validation error, entries не отображались). Download теперь использует fetch с auth header вместо `<a href>`
- **Admin generation show**: Добавлены кнопки "Скачать" для всех изображений (результат, source, reference_images)
- **User frontend reference images**: Добавлен показ `reference_images` в диалоге истории и в начальном результате генерации
- **FileManager — плитки, превью, фильтрация**: Добавлен режим плиток (list/tiles), клик по картинке открывает полноразмерный превью-диалог, скрыты системные папки (`css`, `js`, `templates`, `images`, `generated` — старый путь), оставлены только рабочие директории

## Chat Queue Worker (Jun 09)
- **Model**: `ChatQueue` — новая таблица `chat_queue` с полями `id, session_id, user_id, prompt_messages, status, error_message, tokens_input, tokens_output, cost, created_at, updated_at`
- **Migration**: `87042875ea58_add_chat_queue_table` — создана и применена на сервере
- **Chat worker**: `chat_worker.py` — отдельный фоновый воркер с циклом claim → process → update; не блокирует HTTP request
- **send_message**: Теперь не вызывает LLM синхронно, а создаёт запись в `chat_queue` и возвращает `{success: true}` немедленно
- **get_history**: `has_pending` проверяет наличие `queued/processing` записей в `chat_queue` (вместо проверки последнего сообщения)
- **main.py**: Запуск `chat_worker_loop` в lifespan наравне с `queue_worker_loop`
- **Frontend**: `sendMessage` больше не добавляет оптимистичный assistant-ответ, полагается на polling из `loadMessages`; при успешной отправке вызывает `loadMessages(activeChat)` для старта polling
- **Tests**: Адаптирован `test_send_message` (проверка очереди вместо ответа LLM), добавлен `test_send_message_queue_processed` (проверка полного цикла: enqueue → worker → assistant message)
