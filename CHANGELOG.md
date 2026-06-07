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

## Запланировано в админ-панели (Phase 5)
- Управление БД (просмотр/удаление чатов, генераций, референсов)
- Управление архивами (бэкапы, логи, файлы генераций)

## Workflow (Phase 3)
- 4 из 6 workflow готовы: ZIT.json, QWEN edit 1/2/3 pic.json
- text_to_video.json, image_to_video.json — зарезервированы (будут позже)
