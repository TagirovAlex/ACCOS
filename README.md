# ACCOS — AI Content & Chat Orchestrator Service

**Цель:** Предоставить сотрудникам локальной сети унифицированный, экономически управляемый интерфейс для работы с LLM (чат-ассистент через LMStudio) и ComfyUI (генерация/редактирование изображений и видео) по предопределённым workflow.

**Стек:** Python 3.11 / FastAPI (async) + PostgreSQL 17 + SQLAlchemy 2.0 (async) / asyncpg + Alembic + React 19 / MUI 7 / Vite  
**Интеграции:** LMStudio API, ComfyUI API, LDAP/AD  
**Аутентификация:** JWT (HS256) access 60 min + refresh 7 days

---

## Статус проекта

| Область | Статус |
|---------|--------|
| Бэкенд (FastAPI) | ✅ Завершён (Phases 0–4) |
| Admin API | ✅ Завершён (Phase 5) |
| Admin Panel (React) | ✅ Завершён (Phase 5) |
| User Frontend (React) | ✅ Завершён (Phase 6) |
| Тесты бэкенда (26/26) | ✅ Все проходят |
| Тесты фронтенда (16/16) | ✅ Все проходят |
| Rate limiting | ✅ slowapi (login 5/min, gen 10/min, chat 30/min) |
| Коммитов | 7 |
| Ветка | `master` |

---

## Структура проекта

```
C:\Github\ACCOS\
│
├── backend/                        # FastAPI сервер
│   ├── app/
│   │   ├── __init__.py
│   │   │
│   │   ├── api/v1/endpoints/       # Роуты (контроллеры FastAPI)
│   │   │   ├── auth.py             # POST /login, GET /me
│   │   │   ├── user.py             # GET /balance
│   │   │   ├── chat.py             # CRUD чатов + отправка сообщений
│   │   │   ├── generation.py       # Запуск генерации + история
│   │   │   ├── orchestration.py    # Image→Edit, Image→Video
│   │   │   └── admin.py            # 16 админских эндпоинтов
│   │   │
│   │   ├── core/                   # Ядро приложения
│   │   │   ├── config.py           # Pydantic Settings (читает config/.env)
│   │   │   ├── security.py         # JWT create/verify + bcrypt
│   │   │   ├── dependencies.py     # get_db, get_current_user_id
│   │   │   └── exceptions.py       # Кастомные исключения
│   │   │
│   │   ├── db/                     # База данных
│   │   │   ├── base.py             # DeclarativeBase
│   │   │   ├── session.py          # engine + async_session_factory
│   │   │   └── models/
│   │   │       ├── user.py         # User (users)
│   │   │       ├── user_group.py   # UserGroup (user_groups)
│   │   │       ├── chat.py         # ChatSession + ChatMessage
│   │   │       ├── generation.py   # GenerationRecord (generation_records)
│   │   │       ├── image_asset.py  # ImageAsset (image_assets)
│   │   │       └── admin_settings.py  # AdminSettings (admin_settings)
│   │   │
│   │   ├── repositories/           # Паттерн Repository
│   │   │   ├── base.py             # Generic BaseRepository<T>
│   │   │   ├── user_repository.py
│   │   │   ├── chat_repository.py
│   │   │   ├── generation_repository.py
│   │   │   ├── group_repository.py
│   │   │   └── settings_repository.py
│   │   │
│   │   ├── services/               # Бизнес-логика
│   │   │   ├── auth_service.py     # LDAP → JWT, auto-create user
│   │   │   ├── economy_service.py  # Strategy Pattern: LLM/Image/Video Cost
│   │   │   ├── chat_service.py     # Чат: история, LLM вызов, списание
│   │   │   ├── comfyui_service.py  # ComfyUI: генерация, история
│   │   │   ├── orchestration_service.py  # Image→Edit, Image→Video
│   │   │   ├── admin_service.py    # Все админские CRUD
│   │   │   └── accrual_service.py  # Автоначисление баланса каждые 3600с
│   │   │
│   │   ├── adapters/               # Внешние интеграции
│   │   │   ├── base.py             # BaseAdapter (ABC)
│   │   │   ├── ldap_adapter.py     # LDAPAdapter + MockLDAPAdapter
│   │   │   ├── lmstudio_adapter.py # LMStudio chat/completions
│   │   │   └── comfyui_adapter.py  # ComfyUI upload/run/poll
│   │   │
│   │   ├── schemas/                # Pydantic схемы
│   │   │   ├── auth.py             # LoginRequest, TokenResponse, UserInfoResponse
│   │   │   ├── chat.py             # ChatCreateRequest, ChatSendRequest, ...
│   │   │   ├── generation.py       # GenerateRequest, GenerateResponse, ...
│   │   │   └── admin.py            # 20+ Admin схем
│   │   │
│   │   └── modules/                # Подключаемые модули (BaseModule)
│   │       ├── base.py             # BaseModule (ABC)
│   │       ├── chat_module.py      # ChatModule
│   │       └── comfyui_module.py   # ComfyUIModule
│   │
│   ├── alembic/                    # Миграции
│   │   ├── env.py, script.py.mako
│   │   └── versions/
│   │       ├── 5419b7ff722a_initial_migration.py
│   │       └── 032cd001e02b_add_usergroup_model_and_user_permissions.py
│   │
│   ├── tests/                      # pytest (26 тестов)
│   │   ├── conftest.py             # Фикстуры: БД, клиент, токены
│   │   ├── test_health.py          # 1 тест
│   │   ├── test_auth.py            # 6 тестов
│   │   ├── test_chat.py            # 4 теста
│   │   ├── test_economy.py         # 5 тестов
│   │   ├── test_generation.py      # 2 теста
│   │   └── test_admin.py           # 8 тестов
│   │
│   ├── requirements.txt            # Python зависимости
│   └── main.py                     # Точка входа FastAPI
│
├── admin/                          # React Admin Panel
│   ├── src/
│   │   ├── App.tsx                 # react-admin + theme toggle
│   │   ├── services/
│   │   │   ├── api.ts              # HTTP helper (Bearer token)
│   │   │   ├── authProvider.ts     # react-admin AuthProvider
│   │   │   └── dataProvider.ts     # react-admin DataProvider
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx       # Статистика (количество)
│   │   │   ├── Users.tsx           # CRUD пользователей
│   │   │   ├── Groups.tsx          # CRUD групп
│   │   │   ├── Chats.tsx           # Просмотр чатов (read-only)
│   │   │   ├── Generations.tsx     # Просмотр генераций (read-only)
│   │   │   ├── Assets.tsx          # Просмотр ресурсов (read-only)
│   │   │   └── Settings.tsx        # Редактирование настроек
│   │   └── assets/themes/
│   │       ├── light.ts            # Светлая тема MUI
│   │       └── dark.ts             # Тёмная тема MUI
│   └── package.json
│
├── frontend/                       # React User Frontend
│   ├── src/
│   │   ├── App.tsx                 # BrowserRouter, MUI theme, Layout, Auth guard
│   │   ├── services/
│   │   │   ├── api.ts              # HTTP helper + uploadFile
│   │   │   └── auth.ts             # login(), getMe(), logout()
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx       # Форма входа
│   │   │   ├── DashboardPage.tsx   # Баланс, права, информация
│   │   │   ├── ChatPage.tsx        # Чат-интерфейс
│   │   │   └── GenerationPage.tsx  # Генерация (выбор workflow + промпт)
│   │   └── assets/themes/
│   │       ├── light.ts
│   │       └── dark.ts
│   └── package.json
│
├── config/                         # Конфигурация (единая папка)
│   ├── .env                        # Фактические секреты (gitignored)
│   ├── .env.example                # Шаблон с дефолтами
│   └── alembic.ini                 # Alembic (script_location → backend/alembic)
│
├── static/                         # Статические файлы
│   ├── css/global.css              # CSS-переменные (светлая/тёмная тема)
│   ├── js/                         # (пусто)
│   ├── images/                     # (пусто)
│   └── templates/
│       └── admin_preview.html      # HTML-превью админки (демо)
│
├── workflows/                      # ComfyUI шаблоны
│   ├── ZIT.json                    # Text-to-Image (Z-Image)
│   ├── QWEN edit 1 pic.json        # Редактирование 1 референс
│   ├── QWEN edit 2 pic.json        # Редактирование 2 референса
│   ├── QWEN edit 3 pic.json        # Редактирование 3 референса
│   ├── text_to_video.json          # ⏳ зарезервировано
│   └── image_to_video.json         # ⏳ зарезервировано
│
├── .gitignore
├── AGENTS.md                       # Инструкции для AI-агента
├── CHANGELOG.md                    # Лог всех изменений
└── README.md                       # Этот файл
```

---

## База данных

### Схема

```
┌─────────────────────┐       ┌──────────────────┐
│       users         │       │   user_groups    │
├─────────────────────┤       ├──────────────────┤
│ id (PK)             │────┐  │ id (PK)          │
│ username (UQ, IX)   │    └──│ group_id (FK)    │
│ email               │       │ name (UQ)        │
│ full_name           │       │ ad_group_dn (UQ) │
│ balance             │       │ permissions      │
│ permissions         │       │ start_balance    │
│ group_id (FK)       │       │ description      │
│ is_active           │       │ is_active        │
│ is_admin            │       │ created_at       │
│ created_at          │       │ updated_at       │
│ updated_at          │       └──────────────────┘
└───────┬─────────────┘
        │
        │ 1:N
        │
┌───────┴──────────────────┐    ┌───────────────────────┐
│   chat_sessions          │    │   chat_messages       │
├──────────────────────────┤    ├───────────────────────┤
│ id (PK)                  │ 1:N│ id (PK)               │
│ user_id (FK)             │────│ session_id (FK)       │
│ title                    │    │ role (user/assistant)  │
│ system_prompt            │    │ content               │
│ is_active                │    │ tokens_input          │
│ created_at               │    │ tokens_output         │
│ updated_at               │    │ cost                  │
└──────────────────────────┘    │ created_at            │
                                └───────────────────────┘

┌──────────────────────────┐    ┌───────────────────────┐
│   generation_records     │    │   image_assets        │
├──────────────────────────┤    ├───────────────────────┤
│ id (PK)                  │ 1:N│ id (PK)               │
│ user_id (FK)             │────│ generation_id (FK)    │
│ workflow_type            │    │ user_id (FK)          │
│ prompt                   │    │ filename              │
│ width, height, duration  │    │ file_path             │
│ cost                     │    │ file_size, width,     │
│ status                   │    │   height              │
│ result_path              │    │ is_reference          │
│ error_message            │    │ created_at            │
│ created_at / updated_at  │    │ deleted_at            │
└──────────────────────────┘    └───────────────────────┘

┌───────────────────────┐
│   admin_settings      │
├───────────────────────┤
│ id (PK)               │
│ key (UQ, IX)          │
│ value                 │
│ description           │
└───────────────────────┘
```

### Модели

| Файл | Класс | Таблица | Описание |
|------|-------|---------|----------|
| `db/models/user.py` | `User` | `users` | Пользователи системы, баланс, права |
| `db/models/user_group.py` | `UserGroup` | `user_groups` | Группы AD → права + стартовый баланс |
| `db/models/chat.py` | `ChatSession` | `chat_sessions` | Сессии чатов |
| `db/models/chat.py` | `ChatMessage` | `chat_messages` | Сообщения чатов (user/assistant) |
| `db/models/generation.py` | `GenerationRecord` | `generation_records` | Записи генераций |
| `db/models/image_asset.py` | `ImageAsset` | `image_assets` | Сгенерированные/загруженные изображения |
| `db/models/admin_settings.py` | `AdminSettings` | `admin_settings` | Ключ-значение настроек системы |

---

## API Endpoints

### Публичные (JWT не требуется)

| Метод | Path | Описание | Request | Response |
|-------|------|----------|---------|----------|
| GET | `/api/v1/health` | Проверка сервера | — | `{"status":"ok","version":"1.0.0"}` |

### Auth

| Метод | Path | Auth | Описание |
|-------|------|------|----------|
| POST | `/api/v1/auth/login` | — | Аутентификация (LDAP) → JWT access + refresh |
| POST | `/api/v1/auth/refresh` | — | Обновить access token по refresh token |
| GET | `/api/v1/auth/me` | Bearer | Профиль + баланс + права |

### User

| Метод | Path | Описание | Request | Response |
|-------|------|----------|---------|----------|
| GET | `/api/v1/user/balance` | Текущий баланс | JWT Bearer | `BalanceResponse` |

### Chat

| Метод | Path | Описание | Request | Response |
|-------|------|----------|---------|----------|
| POST | `/api/v1/chat/create` | Создать чат-сессию | Bearer | `ChatCreateRequest` → `ChatSessionResponse` |
| GET | `/api/v1/chat/list` | Список чатов пользователя | Bearer | `ChatListResponse` |
| GET | `/api/v1/chat/{session_id}` | История сообщений | Bearer | `ChatHistoryResponse` |
| POST | `/api/v1/chat/{session_id}/send` | Отправить сообщение (LLM) | Bearer | `ChatSendRequest` → `ChatSendResponse` |
| DELETE | `/api/v1/chat/{session_id}` | Удалить чат (soft) | Bearer | `{"success": true}` |

### Generation

| Метод | Path | Описание | Request | Response |
|-------|------|----------|---------|----------|
| POST | `/api/v1/generate/upload` | Загрузить reference-изображение (resize 2048px) | Bearer | multipart → `UploadResponse` |
| POST | `/api/v1/generate/` | Запустить workflow (ставит в очередь) | Bearer | `GenerateRequest` → `GenerateResponse` |
| GET | `/api/v1/generate/history` | История генераций | Bearer | `HistoryResponse` |
| GET | `/api/v1/generate/{generation_id}/status` | Статус генерации + изображения | Bearer | `GenerationStatusResponse` |

### Orchestration

| Метод | Path | Описание | Request | Response |
|-------|------|----------|---------|----------|
| POST | `/api/v1/orchestrate/image-to-edit/{generation_id}` | Редактировать изображение | multipart (files + params) | `GenerateResponse` |
| POST | `/api/v1/orchestrate/image-to-video/{generation_id}` | Создать видео из изображения | query params | `GenerateResponse` |

### Admin (все требуют JWT + is_admin=True)

| Метод | Path | Описание |
|-------|------|----------|
| GET | `/api/v1/admin/users` | Список пользователей |
| GET | `/api/v1/admin/users/{user_id}` | Пользователь по ID |
| PUT | `/api/v1/admin/users/{user_id}` | Обновить пользователя |
| DELETE | `/api/v1/admin/users/{user_id}` | Удалить пользователя |
| POST | `/api/v1/admin/balance/adjust` | Коррекция баланса |
| GET | `/api/v1/admin/groups` | Список групп |
| POST | `/api/v1/admin/groups` | Создать группу |
| PUT | `/api/v1/admin/groups/{group_id}` | Обновить группу |
| DELETE | `/api/v1/admin/groups/{group_id}` | Удалить группу |
| GET | `/api/v1/admin/chats` | Все чаты |
| DELETE | `/api/v1/admin/chats/{chat_id}` | Удалить чат |
| GET | `/api/v1/admin/generations` | Все генерации |
| DELETE | `/api/v1/admin/generations/{gen_id}` | Удалить генерацию |
| GET | `/api/v1/admin/assets` | Все assets |
| GET | `/api/v1/admin/settings` | Все настройки |
| PUT | `/api/v1/admin/settings/{key}` | Обновить настройку |

---

## Сервисы — полное описание

### `auth_service.py`
```python
class AuthService:
    __init__(self, session: AsyncSession)
    _authenticate_ldap(username, password) -> dict       # LDAP + Mock fallback
    _resolve_group_and_permissions(ldap_result) -> tuple  # UserGroup из AD групп
    authenticate(username, password) -> dict              # LDAP → create user → JWT
    get_user_info(user_id) -> dict                        # Профиль из БД
```

### `economy_service.py`
```python
class PricingStrategy(ABC):                # abstract calculate_cost(**kwargs)
class LLMCostStrategy(PricingStrategy):    # cost = input*0.001 + output*0.002
class ImageGenCostStrategy(PricingStrategy): # cost = 1.0 + (w*h)*0.0001
class ImageEditCostStrategy(PricingStrategy): # cost = 0.5 + (ref*h)*0.00005
class VideoGenCostStrategy(PricingStrategy):  # cost = 5.0 + (res*dur)*0.5

class EconomyService:
    strategies = {"llm": LLMCostStrategy, ...}
    @classmethod calculate_cost(operation_type, **params) -> float
    async get_balance(user_id) -> dict
    async deduct_balance(user_id, amount) -> dict
    async add_balance(user_id, amount) -> dict
```

### `chat_service.py`
```python
class ChatService:
    __init__(self, session)                     # chat_repo, user_repo, economy, llm adapter
    async create_chat(user_id, title, system_prompt) -> dict
    async list_chats(user_id) -> dict
    async get_history(session_id) -> dict
    async send_message(user_id, session_id, message) -> dict  # LLM → deduct → save
```

### `comfyui_service.py`
```python
class ComfyUIService:
    __init__(self, session)                     # generation_repo, economy, comfyui adapter
    async generate(user_id, workflow_type, prompt, width, height, duration) -> dict
    async get_history(user_id) -> dict
```

### `orchestration_service.py`
```python
class OrchestrationService:
    __init__(self, session)
    async image_to_edit(user_id, generation_id, edit_workflow, prompt, reference_images) -> dict
    async image_to_video(user_id, generation_id, prompt, duration) -> dict
```

### `admin_service.py`
```python
class AdminService:
    __init__(self, session)                     # user_repo, group_repo, settings_repo
    async get_user(user_id) -> dict
    async update_user(user_id, data) -> dict
    async delete_user(user_id) -> dict
    async delete_group(group_id) -> dict
    async list_users() -> dict
    async adjust_balance(admin_id, target_user_id, amount) -> dict
    async list_groups() -> dict
    async create_group(name, ad_group_dn, options...) -> dict
    async update_group(group_id, **kwargs) -> dict
    async list_all_chats() -> dict
    async force_delete_chat(chat_id) -> dict
    async list_all_generations() -> dict
    async force_delete_generation(gen_id) -> dict
    async list_all_assets() -> dict
    async get_settings() -> dict
    async update_setting(key, value, description) -> dict
```

### `accrual_service.py`
```python
async run_auto_accrual()  # Добавляет auto_accrual_amount каждому активному пользователю
```

### `main.py` — lifespan
```python
lifespan(app):  # Запускает accrual_loop (asyncio task, каждые 3600с)
```

---

## Адаптеры (внешние интеграции)

### `base.py`
```python
class BaseAdapter(ABC):
    async def execute(self, **kwargs) -> Any: ...
```

### `ldap_adapter.py`
```python
class LDAPAdapter(BaseAdapter):       # Реальный LDAP через ldap3
    execute(username, password) → dict с {authenticated, email, full_name, groups}
class MockLDAPAdapter(BaseAdapter):   # Заглушка для разработки
    execute(username, password) → admin/admin123 = успех, иначе = провал
```

### `lmstudio_adapter.py`
```python
class LMStudioAdapter(BaseAdapter):
    execute(messages) → chat_completion(messages)
    chat_completion(messages) → POST /v1/chat/completions → {success, content, tokens}
```

### `comfyui_adapter.py`
```python
class ComfyUIAdapter(BaseAdapter):
    execute(workflow_type, prompt, images, width, height, duration) → run_workflow(...)
    _load_workflow(workflow_type) → dict|None      # JSON из workflows/
    _apply_prompt(workflow, prompt, images) → dict  # Inject prompt + placeholders
    upload_image(file_path) → str|None               # POST /upload/image
    run_workflow(workflow_type, prompt, images, ...) → dict
    _poll_result(client, prompt_id, max_attempts) → dict  # Каждые 2с до 60 попыток
```

---

## Repository Layer

### `base.py` — Generic
```python
class BaseRepository[ModelType]:
    async get(id: UUID) -> ModelType | None
    async list(skip=0, limit=100) -> list[ModelType]
    async create(**kwargs) -> ModelType
    async update(id: UUID, **kwargs) -> ModelType | None
    async delete(id: UUID, hard=False) -> bool
    async count() -> int
```

### Конкретные репозитории

| Репозиторий | Модель | Доп. методы |
|-------------|--------|-------------|
| `UserRepository` | `User` | `get_by_username`, `get_by_email`, `update_balance`, `get_balance` |
| `ChatRepository` | `ChatSession` | `get_user_chats`, `get_messages`, `add_message` |
| `GenerationRepository` | `GenerationRecord` | `get_user_generations`, `create_asset` |
| `GroupRepository` | `UserGroup` | `get_by_name`, `get_by_ad_group_dn` |
| `SettingsRepository` | `AdminSettings` | `get_by_key`, `set_value`, `get_all_as_dict` |

---

## Pydantic Schemas

| Файл | Схемы |
|------|-------|
| `schemas/auth.py` | `BaseResponse`, `LoginRequest`, `TokenResponse`, `UserInfoResponse`, `BalanceResponse` |
| `schemas/chat.py` | `ChatCreateRequest`, `ChatSendRequest`, `ChatSessionResponse`, `ChatMessageResponse`, `ChatListResponse`, `ChatHistoryResponse`, `ChatSendResponse` |
| `schemas/generation.py` | `GenerateRequest`, `GenerateResponse`, `GenerationRecordResponse`, `HistoryResponse`, `AdminGroupResponse`, `AdminGroupListResponse` |
| `schemas/admin.py` | 20 схем: `AdminUserResponse`, `AdminGroupCreate/Update`, `AdminSettingUpdate`, `AdminChatResponse`, `AdminGenerationResponse`, `AdminAssetResponse`, `AdminBalanceAdjust`, etc. |

---

## Конфигурация

### `config/.env`

| Параметр | Тип | Дефолт | Описание |
|----------|-----|--------|----------|
| `DATABASE_URL` | str | `postgresql+asyncpg://postgres:postgres@localhost:5432/accos` | Подключение к БД |
| `JWT_SECRET_KEY` | str | `super-secret-key` | Секрет для JWT |
| `JWT_ALGORITHM` | str | `HS256` | Алгоритм JWT |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | int | `60` | Время жизни токена |
| `LDAP_SERVER` | str | `ldap://localhost:389` | LDAP сервер |
| `LDAP_DOMAIN` | str | `DOMAIN` | Домен AD |
| `LDAP_BASE_DN` | str | `DC=domain,DC=local` | Base DN |
| `LMSTUDIO_BASE_URL` | str | `http://localhost:1234/v1` | LMStudio endpoint |
| `LMSTUDIO_MODEL` | str | `default` | Модель LLM |
| `COMFYUI_BASE_URL` | str | `http://localhost:8188` | ComfyUI endpoint |
| `ADMIN_USERNAME` | str | `admin` | Локальный админ (fallback) |
| `ADMIN_PASSWORD` | str | `admin123` | Пароль локального админа |
| `CORS_ORIGINS` | str (JSON) | `["http://localhost:3000","http://localhost:5173"]` | Разрешённые origin'ы |
| `LOG_LEVEL` | str | `DEBUG` | Уровень логирования |

### Настройки в БД (AdminSettings)

Эти настройки можно менять через Admin API / Admin Panel, они имеют приоритет над `.env`:

| Ключ | Тип | Описание |
|------|-----|----------|
| `default_permissions` | str | Права по умолчанию (`chat`, `full_access`, ...) |
| `default_start_balance` | float | Стартовый баланс новых пользователей |
| `auto_accrual_interval_minutes` | int | Интервал автоначисления (не используется — заменён на asyncio task с 3600с) |
| `auto_accrual_amount` | float | Сумма автоначисления |

---

## Тестирование

```bash
# Бэкенд (26 тестов)
cd backend
.venv\Scripts\python -m pytest tests/ -v

# Фронтенд (16 тестов)
cd frontend
npx vitest run

# Всё сразу
npm test   # из корня проекта
```

### Фикстуры (conftest.py)

| Фикстура | Scope | Описание |
|----------|-------|----------|
| `event_loop` | session | Event loop для asyncio |
| `test_engine` | session | Движок БД (NullPool) + create/drop tables |
| `session` | function | Сессия SQLAlchemy на один тест |
| `client` | function | httpx AsyncClient с FastAPI + override get_db |
| `admin_token` | function | JWT токен админа (LDAP замокан) |
| `user_token` | function | JWT токен обычного пользователя (LDAP замокан) |

### Покрытие тестов

| Файл | Тесты | Что тестирует |
|------|-------|---------------|
| `test_auth.py` | 6 | Логин (успех/ошибка/новый пользователь), /me, /health |
| `test_chat.py` | 4 | Создание, список, отправка, история |
| `test_economy.py` | 5 | LLM/Image/Edit/Video cost + unknown strategy |
| `test_generation.py` | 2 | Запуск workflow, история |
| `test_admin.py` | 8 | Все админские CRUD + проверка прав |
| `test_health.py` | 1 | Health check |

### Frontend тесты (Vitest + Testing Library)

| Файл | Тесты | Что тестирует |
|------|-------|---------------|
| `ErrorPage.test.tsx` | 5 | Рендер статуса, error_id, чипсов, кнопок, вызов onRetry |
| `SimpleMarkdown.test.tsx` | 6 | Bold, italic, inline code, code block, HTML escape, plain text |
| `api.test.ts` | 5 | GET запрос, Authorization header, ApiError, 401 auto-refresh |

---

## Быстрый старт

```powershell
# 1. Виртуальное окружение
cd C:\Github\ACCOS\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. База данных
# Убедитесь что PostgreSQL 17 запущен на localhost:5432
# База accos должна существовать
alembic -c ../config/alembic.ini upgrade head

# 3. Настройки
# Скопируйте config/.env.example в config/.env и отредактируйте

# 4. Запуск бэкенда
uvicorn main:app --reload --port 8000

# 5. (отдельный терминал) Admin Panel
cd C:\Github\ACCOS\admin
npm run dev                      # → http://localhost:5173

# 6. (отдельный терминал) User Frontend
cd C:\Github\ACCOS\frontend
npm run dev                      # → http://localhost:3000

# → Документация API: http://localhost:8000/docs
```

---

## Roadmap

| Фаза | Описание | Статус |
|------|----------|--------|
| Phase 0 | Scaffold, модели, Alembic, config, базовый CRUD | ✅ |
| Phase 1 | Auth (LDAP + JWT), Economy (Strategy), AdminSettings | ✅ |
| Phase 2 | Chat (LMStudio, системный промпт, история, списание) | ✅ |
| Phase 3 | ComfyUI (6 workflow, Image/Video gen, расчёт стоимости) | ✅ |
| Phase 4 | Оркестрация (Image→Edit, Image→Video) | ✅ |
| Phase 5 | Admin API + React Admin Panel | ✅ |
| Phase 6 | User Frontend (React) | ✅ |
| **Будущее** | **Что можно сделать дальше** | |
| — | Видео-генерация (text_to_video.json, image_to_video.json) | ⏳ |
| — | E2E тесты (Playwright) | 📝 |
| — | CI/CD (GitHub Actions) | 📝 |
| — | Мониторинг и алертинг | 📝 |
| — | Frontend тесты (Vitest) | ✅ |
| — | Rate limiting (slowapi) | ✅ |

---

## Ключевые архитектурные решения

1. **Только async/await** — все эндпоинты и сервисы асинхронные
2. **Repository Pattern** — доступ к БД только через репозитории
3. **Strategy Pattern** — расчёт стоимости через стратегии (легко добавить новые типы)
4. **Adapter Pattern** — внешние интеграции через BaseAdapter (легко мокать, легко заменять)
5. **Module Pattern** — подключаемые модули (BaseModule), хотя сейчас все роуты зарегистрированы в main.py напрямую
6. **JWT с refresh** — access token живёт 60 минут, refresh token 7 дней, 401 → автоматическое обновление
7. **LDAP fallback** — при недоступности реального LDAP работает MockLDAPAdapter (локальный admin)
8. **NullPool в тестах** — изолированные соединения для избежания блокировок asyncpg
9. **Автоаккреал** — asyncio background task (не APScheduler) каждые 3600с

---

*Подробнее: `CHANGELOG.md` (лог изменений), `AGENTS.md` (правила для AI-агента)*
