# Правила для AI-агента разработки ACCOS

## 1. Общие правила

- **Не выходить за пределы папки проекта** `C:\Github\ACCOS\`. Все генерируемые файлы, скрипты, конфиги — только внутри проекта.
- **Не устанавливать глобальные пакеты.** Всё через виртуальное окружение (`.venv` внутри проекта) и `requirements.txt`.
- **Не создавать файлы вне проекта.** Для временных файлов использовать `C:\Users\TAGIRO~1\AppData\Local\Temp\opencode\`.
- **Не запрашивать у пользователя разрешение на каждое действие.** Работать максимально автономно. Если нужно уточнение — задать один вопрос с вариантами.
- **Сообщать пользователю только о критических проблемах** или когда требуется принятие решения.
- **Перед началом любой фазы — прочитать текущее состояние проекта** (структуру, существующие файлы).

## 2. Структура проекта — строгое соблюдение

```
C:\Github\ACCOS\
├── backend/                    # FastAPI сервер
│   ├── app/
│   │   ├── api/v1/endpoints/   # Роуты FastAPI
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── generation.py
│   │   │   ├── admin.py
│   │   │   └── user.py
│   │   ├── core/               # Конфигурация, безопасность
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── dependencies.py
│   │   ├── db/                 # База данных
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models/
│   │   │       ├── user.py
│   │   │       ├── chat.py
│   │   │       ├── generation.py
│   │   │       ├── image_asset.py
│   │   │       ├── admin_settings.py
│   │   │       └── __init__.py
│   │   ├── repositories/       # Паттерн Repository
│   │   │   ├── base.py
│   │   │   ├── user_repository.py
│   │   │   ├── chat_repository.py
│   │   │   ├── generation_repository.py
│   │   │   └── settings_repository.py
│   │   ├── services/           # Бизнес-логика
│   │   │   ├── auth_service.py
│   │   │   ├── economy_service.py
│   │   │   ├── chat_service.py
│   │   │   ├── comfyui_service.py
│   │   │   └── admin_service.py
│   │   ├── adapters/           # Внешние интеграции
│   │   │   ├── base.py         # AbstractAdapter
│   │   │   ├── lmstudio_adapter.py
│   │   │   ├── comfyui_adapter.py
│   │   │   └── ldap_adapter.py
│   │   ├── schemas/            # Pydantic схемы
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── generation.py
│   │   │   └── admin.py
│   │   └── modules/            # Подключаемые модули
│   │       ├── base.py         # BaseModule
│   │       ├── chat_module.py
│   │       ├── comfyui_module.py
│   │       └── __init__.py
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_economy.py
│   │   ├── test_chat.py
│   │   └── test_comfyui.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── main.py
├── frontend/                   # React (пользователь)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── App.tsx
│   └── package.json
├── admin/                      # React Admin Panel
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   └── package.json
├── workflows/                  # ComfyUI JSON шаблоны
│   ├── text_to_image.json
│   ├── image_edit_1.json
│   ├── image_edit_2.json
│   ├── image_edit_3.json
│   ├── text_to_video.json
│   └── image_to_video.json
├── .env.example
├── AGENTS.md                   # Этот файл
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
