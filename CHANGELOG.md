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
