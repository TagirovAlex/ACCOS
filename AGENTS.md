# Правила для AI-агента разработки ACCOS

## 1. Общие правила

- **Не выходить за пределы папки проекта** `C:\Github\ACCOS\`. Все генерируемые файлы, скрипты, конфиги — только внутри проекта.
- **Не устанавливать глобальные пакеты.** Всё через виртуальное окружение (`.venv` внутри проекта) и `requirements.txt`.
- **Не создавать файлы вне проекта.** Для временных файлов использовать `C:\Github\ACCOS\tmp\`.
- **Не запрашивать у пользователя разрешение на каждое действие.** Работать максимально автономно. Если нужно уточнение — задать один вопрос с вариантами.
- **Сообщать пользователю только о критических проблемах** или когда требуется принятие решения.
- **Перед началом любой фазы — прочитать текущее состояние проекта** (структуру, существующие файлы).

## 2. Структура проекта — строгое соблюдение

```
C:\Github\ACCOS\
├── backend/                    # FastAPI сервер
│   ├── app/
│   │   ├── api/v1/endpoints/   # Роуты FastAPI
│   │   ├── core/               # Конфигурация, безопасность
│   │   ├── db/                 # База данных
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models/
│   │   ├── repositories/       # Паттерн Repository
│   │   ├── services/           # Бизнес-логика
│   │   ├── adapters/           # Внешние интеграции
│   │   ├── schemas/            # Pydantic схемы
│   │   └── modules/            # Подключаемые модули
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── main.py
├── frontend/                   # React (пользователь)
├── admin/                      # React Admin Panel
│   ├── src/
│   │   ├── assets/             # Статика (темы, стили, скрипты)
│   │   │   ├── themes/         # Темы (light/dark)
│   │   │   └── styles/         # CSS/Style файлы
│   │   ├── components/         # UI компоненты
│   │   ├── pages/              # Страницы
│   │   ├── services/           # API клиенты
│   │   └── App.tsx
│   └── package.json
├── config/                     # Все конфиги проекта
│   ├── .env
│   ├── .env.example
│   └── alembic.ini
├── static/                     # Статические файлы (шаблоны, css, js, images)
│   ├── css/
│   ├── js/
│   ├── images/
│   └── templates/
├── workflows/                  # ComfyUI JSON шаблоны
│   ├── ZIT.json
│   ├── QWEN edit 1 pic.json
│   ├── QWEN edit 2 pic.json
│   ├── QWEN edit 3 pic.json
│   ├── text_to_video.json      # резерв
│   └── image_to_video.json     # резерв
├── .gitignore
├── AGENTS.md
├── CHANGELOG.md
└── README.md
```

- При создании новых файлов строго придерживаться этой структуры.
- Новая бизнес-логика → новый файл в соответствующей папке.
- `__init__.py` должен быть в каждой папке с Python-модулями.

## 3. Технические требования к коду

### 3.1. FastAPI

- **Только async/await.** Никаких `def` для эндпоинтов — только `async def`.
- Все эндпоинты версионированы: `/api/v1/...`.
- Использовать `APIRouter` для каждого модуля.
- Dependencies через `Depends()`.

### 3.2. База данных

- **SQLAlchemy 2.0+** (async) + `asyncpg`.
- **Alembic** для миграций. Каждое изменение модели = новая миграция.
- Модели наследуют `DeclarativeBase`.
- Все запросы к БД — строго через **Repository** слой. Запрещено писать SQLAlchemy запросы напрямую из сервисов или эндпоинтов.
- Repository принимает `AsyncSession` через конструктор.
- Транзакции: `async with session.begin():`.

### 3.3. Паттерны

- **Repository Pattern** — для доступа к данным.
- **Strategy Pattern** — для расчёта стоимости (LLM Cost, Image Cost, Video Cost).
- **Adapter Pattern** — для внешних интеграций (LMStudio, ComfyUI, LDAP).
- **Module Pattern** — для подключаемых модулей (BaseModule).
- Все абстракции — через `ABC` и `abstractmethod`.

### 3.4. Адаптеры (внешние интеграции)

```python
class BaseAdapter(ABC):
    @abstractmethod
    async def execute(self, **kwargs) -> Any: ...
```

- Каждый адаптер в отдельном файле.
- Адаптеры не имеют прямой зависимости от FastAPI.
- Настройки адаптера (endpoint, ключи) берутся из `core/config.py`, который читает из БД (admin_settings) с fallback на `.env`.

### 3.5. Pydantic схемы

- Отдельный файл для каждой группы схем (auth, chat, generation, admin).
- Request/Response схемы разделены (например, `ChatRequest`, `ChatResponse`).
- Наследование: `BaseResponse` с полями `success: bool`, `error: str | None`.

### 3.6. Обработка ошибок

- Кастомные исключения в `app/core/exceptions.py`.
- Exception handlers в FastAPI.
- Все ошибки логируются.
- Пользователю возвращается понятное сообщение, технические детали — в лог.

### 3.7. Логирование

- `import logging` — стандартный логгер Python.
- Уровни: DEBUG для разработки, INFO для продa.
- Логи пишутся в `logs/` (папка создаётся автоматически).
- Формат: `[YYYY-MM-DD HH:MM:SS] LEVEL module: message`.

## 4. Процесс разработки

### 4.1. Последовательность фаз

Фазы выполняются строго по порядку. Каждая фаза начинается только после завершения предыдущей.

| Фаза | Описание |
|------|----------|
| Phase 0 | Scaffold FastAPI, модели БД, Alembic, config, базовый CRUD |
| Phase 1 | Auth (LDAP + JWT), Economy (баланс, автоначисление), Admin settings model |
| Phase 2 | Chat Module (LMStudio adapter, системный промпт, история) |
| Phase 3 | ComfyUI Module (6 workflow, Image/Video gen, расчёт стоимости) |
| Phase 4 | Оркестрация (Image→Edit, Image→Video) |
| Phase 5 | Admin API + Admin Panel (React) — управление БД, архивами, настройками |
| Phase 6 | User Frontend (React) |

### 4.2. Внутри фазы

1. Прочитать README.md и AGENTS.md для понимания контекста.
2. Изучить существующие файлы в проекте.
3. Написать код.
4. Установить зависимости (`pip install`), если добавили новые.
5. Проверить что код запускается (`uvicorn main:app`).
6. Обновить CHANGELOG.md — добавить запись о завершённой фазе.
7. Написать тесты на новую функциональность.
8. Запустить тесты (`pytest`).
9. Сообщить о завершении фазы списком созданных файлов.

### 4.3. Зависимости

- При добавлении новой зависимости — сразу добавить в `requirements.txt`.
- Предпочитать популярные, поддерживаемые библиотеки.
- Минимизировать количество зависимостей.
- Фиксировать версии (`package==1.2.3`).
- **Запрещено** устанавливать глобальные пакеты через `pip install --global`.

### 4.4. Тестирование

- pytest + pytest-asyncio.
- `@pytest.mark.asyncio` для async тестов.
- Mock для внешних сервисов (LMStudio, ComfyUI, LDAP).
- Тесты в `backend/tests/`.
- Минимальное покрытие новой логики — 70%.

## 5. Стиль кода

- **Никаких комментариев в коде.** Код должен быть самодокументируемым.
- Имена: `snake_case` для переменных/функций, `PascalCase` для классов, `SCREAMING_SNAKE_CASE` для констант.
- Аннотации типов обязательны для всех функций и методов.
- Длина строки — до 100 символов.
- Импорты: стандартная библиотека → сторонние → внутренние (разделённые пустой строкой).
- Никаких `print()` в коде — только `logger`.

## 6. Безопасность

- Пароли, секреты, endpoint'ы — только в `.env`. `.env` в `.gitignore`.
- Валидация всех входных данных через Pydantic.
- Проверка прав доступа на каждый эндпоинт (admin, user).
- SQL injection защита через SQLAlchemy (RAW SQL запрещён).
- CORS настройки — только разрешённые origin'ы (из конфига).

## 7. Работа с AI Agent (самореференция)

- **Агент не ждёт команд на каждое действие.** Он читает README, AGENTS.md, и выполняет следующую фазу.
- Если фаза завершена — агент пишет сообщение: `**Фаза X завершена.** Созданы файлы: ...` и переходит к следующей.
- Если возникла ошибка — агент пишет: `**Ошибка в фазе X:** описание` и предлагает 2-3 варианта решения.
- Агент не спрашивает "можно начать фазу X?" — он начинает, если все условия выполнены.
- Перед началом проекта агент проверяет: есть ли `.venv`, установлены ли зависимости, запускается ли сервер.
- Агент ведёт todo-list через `todowrite` и обновляет статусы.
- Агент НЕ изменяет AGENTS.md и README.md без явного указания пользователя.

## 8. Git

- **Автоматический commit после каждой завершённой фазы** с сообщением `[Phase N] Краткое описание`.
- Перед началом проекта — инициализировать git-репозиторий в корне `C:\Github\ACCOS\`.
- Не коммитить: `.env`, `__pycache__/`, `.venv/`, `*.pyc`, `node_modules/`.
- Ветки не создавать — вся работа в `main/master`.
- Если commit упал (ошибка hooks, pre-commit и т.д.) — исправить проблему и сделать новый commit, не amend.

## 9. План следующих блоков

### Block 0: Module System Core
Реализация полноценной модульной инфраструктуры. Все последующие блоки разрабатываются как модули.

**ModuleRegistry:**
- Центральный реестр модулей (Singleton)
- Автообнаружение: `discover_modules()` сканирует `modules/`, загружает все наследники `BaseModule`
- Порядок загрузки по `depends_on` (топологическая сортировка)
- `register_all(app)` — итерация по модулям, вызов `module.register_routes(app)`
- Lifecycle: `on_startup()`, `on_shutdown()` (вызов в lifespan)
- `get_module(name)` — получение модуля по имени

**BaseModule (расширенный) — единая структура модуля:**
```python
class BaseModule(ABC):
    name: str
    depends_on: list[str]
    
    @abstractmethod
    def register_routes(self, app: FastAPI) -> None: ...
    
    def get_name(self) -> str: ...
    def on_startup(self) -> None: ...
    def on_shutdown(self) -> None: ...
    
    def get_settings_schema(self) -> list[ModuleSettingDef]: ...
    def get_admin_menu(self) -> list[MenuItemDef]: ...
    def get_user_menu(self) -> list[MenuItemDef]: ...
```

**ModuleSettingDef — стандартное описание настройки модуля:**
- `key: str` — уникальный ключ (например `telegram_bot_chat_id`)
- `label: str` — отображаемое имя (например "Telegram ID")
- `type: str` — `"string"`, `"boolean"`, `"number"`, `"select"`, `"password"`
- `category: str` — категория для группировки в UI
- `default: Any` — значение по умолчанию
- `is_user_setting: bool` — True = видно в ЛК пользователя, False = только админ
- `is_admin_setting: bool` — True = видно в админке
- `validation: dict | None` — опциональные правила валидации (regex, min, max, options)
- `description: str` — подсказка

**MenuItemDef — стандартное описание пункта меню:**
- `label: str` — текст пункта
- `path: str` — URL (например `/telegram`)
- `icon: str` — имя MUI-иконки
- `permission: str | None` — требуемое право (None = всем)
- `order: int` — порядок сортировки

**Модель module_settings (таблица БД):**
- `id` (PK), `user_id` (FK → users, nullable = глобальная), `module_name` (str), `key` (str), `value` (text), `created_at`, `updated_at`
- Unique: `(user_id, module_name, key)` — user_id NULL = глобальное значение модуля

**Модель module_menu_items (опционально):**
- Для статического определения пунктов меню модулями

**Сбор настроек:**
- Admin API: `GET /admin/modules/{name}/settings` — глобальные настройки модуля
- Admin API: `GET /admin/users/{id}/module-settings` — настройки модуля для конкретного пользователя
- User API: `GET /user/module-settings` — свои настройки модулей
- Admin Panel: динамическая секция "Настройки модулей" в Settings + вкладка "Модули" в профиле пользователя
- User Frontend: динамическая секция в ProfilePage

**Безопасность:**
- Валидация всех значений настроек через `ModuleSettingDef.validation`
- Проверка прав доступа к пунктам меню
- Изоляция модулей друг от друга

**Рефакторинг существующих модулей:**
- ChatModule, ComfyUIModule, RAGModule — привести к единому BaseModule
- RAGModule — исправить (добавить register_routes, get_name)
- main.py — перевести на модульную загрузку (`registry.register_all(app)`)
- Все текущие роуты (`auth`, `user`, `chat`, `generation`, `orchestration`, `admin`, `knowledge`, `help`) должны регистрироваться через модули

### Block 5: LLM Server Management
Управление несколькими LLM-серверами для распределения нагрузки и тестирования моделей.

**Модель `llm_servers`:**
- `id`, `name`, `base_url`, `api_key` (encrypted), `model_name`, `system_prompt`, `weight` (для балансировки), `is_active`, `created_at`, `updated_at`

**Backend:**
- `POST /admin/llm-servers` — создать сервер
- `GET /admin/llm-servers` — список серверов
- `PUT /admin/llm-servers/{id}` — обновить
- `DELETE /admin/llm-servers/{id}` — удалить
- `POST /admin/llm-servers/{id}/test` — тест соединения

**ChatWorker:**
- При отправке сообщения выбирать сервер из активных (round-robin / random по weight)
- Fallback при ошибке: переключиться на следующий доступный
- System prompt: если задан в чате — используется он, иначе — system_prompt сервера, иначе — пусто

**Admin UI:**
- Новая страница "LLM-серверы" в админке
- CRUD: имя, URL, API-ключ, модель, system prompt (textarea), weight (число)
- Кнопка "Тест" — отправляет test prompt, показывает ответ/ошибку

### Block 6: Images in chat
- ChatSendRequest schema (image field)
- Vision-формат сообщений (multipart content с type:text + type:image_url)
- Frontend attachment UI (drag-n-drop, загрузка, превью)
- **Проверка vision-способностей модели**: перед включением отправки картинок проверить модель LM Studio через `/v1/models` — смотреть `supports_vision` или наличие vision-ключевых слов в имени (llava, qwen-vl, vision, llama3.2-vision)
- Если модель не поддерживает vision — не показывать кнопку прикрепления изображения и блокировать image field в запросе

### Block 7: LLM Document Recognition
- `rag_llm_ocr` setting
- Отправка изображения документа в LM Studio vision для извлечения текста (вместо Tesseract)

### RAG-2: Scraping (отложено)
- Сбор веб-страниц по URL
- Автоматическое добавление в базу знаний

### Видео-генерация (отложено)
- text_to_video.json, image_to_video.json — workflow зарезервированы
- Запуск через ComfyUI как отдельный workflow_type
- Расчёт стоимости через VideoGenCostStrategy

### Admin Page Guidelines

#### Shared Components (`admin/src/components/`)
- **`CardGrid`** — CSS Grid `auto-fill, minmax(240px, 1fr)`. Использовать вместо `MuiGrid container` для карточных тайлов. Children — `Box` (аналог `MuiGrid item`).
- **`ViewToggle`** — `ToggleButtonGroup` (ViewListIcon / GridViewIcon) с сохранением в localStorage. Использовать композицию: `<ViewToggle storageKey="section_view" />`. Либо хук `useView(storageKey)` возвращает `{ view, ViewToggleEl, setView }`.
- **`StatusChip`** — маппинг статусов: completed/ready/active → green, failed/error → red, processing/indexing → blue, queued → default, pending → orange.

#### Правила для страниц admin
- **Карточные тайлы:** `CardGrid` вместо `MuiGrid container spacing={2}`, `Box` вместо `MuiGrid size={{...}}`.
- **Тоггл вида:** `ViewToggle` или `useView` вместо дублирования `ToggleButtonGroup` + `localStorage`.
- **Статусы:** `StatusChip` вместо ручного `Chip` с цветами.
- **Тема:** не задавать ручные цвета — только MUI `color` prop или `sx` с theme ссылками. Light/dark автоматически.
- **localStorage ключи:** `<section>_view` (generations_view, assets_view, groups_view, docs_view, docs_root_view, backups_view, files_view, llm_servers_view, doc_scraper_view).
- **ViewToggle внутри TopToolbar:** использовать `<ViewToggle storageKey="..." />` вместо inline-кнопок.

#### Страницы без тайлов (не трогать)
- Users, GenerationQueue, Settings, ModuleSettings, Templates, WebFetchAccess

### Деплой — чеклист

#### Полный деплой (deploy.py)
- `cd scripts && python deploy.py` — собирает tar.gz, загружает, запускает deploy.sh на сервере
- deploy.sh: останавливает сервис → распаковывает → сохраняет .venv/.env/logs → собирает admin/frontend → миграции → запуск
- **Внимание:** tar.gz не сохраняет симлинки. После деплоя проверить:
  - `ls -la /opt/accos/static/generations` → symlink to `/mnt/storage/generations`
  - `ls -la /opt/accos/static/documents` → symlink to `/mnt/storage/documents`
  - `ls -la /opt/accos/static/knowledge` → symlink to `/mnt/storage/knowledge`
  - `ls -la /opt/accos/static/knowledge_preview` → symlink to `/mnt/storage/knowledge_preview`
- deploy.py таймаут 600s — если npm install на сервере долгий, скрипт падает. После таймаута: `systemctl start accos` вручную

#### Быстрый деплой (только admin)
- `npm run build` в `admin/`
- `scp -i ~/.ssh/accos_deploy -r dist/* root@10.0.68.43:/opt/accos/static/admin/`
- **Важно:** копировать содержимое `assets/*`, а не саму папку `assets` — иначе получится `assets/assets/`

#### Проверка после деплоя
- `systemctl status accos` — active (running)
- `curl localhost/admin/` — 200
- `curl localhost/` — 200
- `curl localhost/static/generations/...` — 200 (проверить существующий файл)
- `nginx -t && nginx -s reload` — если менялась конфигурация

### Полезное
1. **Audit log** — логирование всех действий пользователей и админов
2. **PDF preview caching** — lazy render-to-images при первом открытии, сохранение в `static/knowledge_preview/{doc_id}/`, отдача готовых картинок при повторных просмотрах (реализовано)
3. **Rate limit UI** — отображение и настройка лимитов через админку
4. **Password change** — смена пароля для локальных пользователей (не LDAP)
5. **Notifications** — система уведомлений (завершение генерации, ошибки, новый пользователь)
6. **Document versioning** — версионирование документов в базе знаний
