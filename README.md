# 🤖 ACCOS — AI Content & Chat Orchestrator Service

**Название Проекта:** AI Content & Chat Orchestrator Service (ACCOS)
**Версия ТЗ:** 1.2 (Реализованная)
**Цель проекта:** Предоставить сотрудникам локальной сети унифицированный, экономически управляемый интерфейс для взаимодействия с LLM (чат-ассистент) и ComfyUI (генерация изображений/видео), используя предопределенные рабочие процессы.

---

## 📋 1. Общие Положения

### 1.1. Назначение Системы
ACCOS — это бэкенд-сервис, который выступает в роли оркестратора между пользователем (через фронтенд), LLM (интеграция с LMStudio) и ComfyUI. Он управляет контекстом чатов, выполняет вызовы генерации по заданным шаблонам и строго контролирует расход внутренней валюты пользователя.

### 1.2. Архитектурный Стек
*   **Бэкенд:** Python 3.11 / FastAPI (async/await) — строго асинхронные эндпоинты
*   **База Данных:** PostgreSQL 17 / SQLAlchemy 2.0 (async) + asyncpg
*   **Миграции:** Alembic (async)
*   **Фронтент (Admin):** React 19 + react-admin 5 + MUI 7 + Vite
*   **Фронтент (User):** React — Phase 6
*   **AI Интеграция:** LMStudio API (HTTP) + ComfyUI API (HTTP + WebSocket poll)
*   **Авторизация:** LDAP/AD через python-ldap (реальный + Mock для разработки)
*   **Аутентификация:** JWT (HS256)

### 1.3. Требования к Доступу и Безопасности
1.  **Аутентификация:** Все запросы проходят проверку JWT токена.
2.  **Авторизация Групп:** Система проверяет принадлежность пользователя к группам AD. Права и тариф задаются через модель `UserGroup` (AD группа → permissions + start_balance).
3.  **Начальный Баланс:** При первом логине баланс устанавливается согласно `UserGroup` для его AD группы, либо из `default_start_balance` глобальных настроек.

---

## ⚙️ 2. Функциональные Требования (Реализовано)

### 2.1. Модуль Чат-Ассистента (LMStudio)
*   ✅ **FR-CHAT-001:** Создание и продолжение чат-сессий.
*   ✅ **FR-CHAT-002:** Системный промпт для каждого чата (переопределяемый).
*   ✅ **FR-CHAT-003:** История диалога (сообщения хранятся в `ChatMessage`, передаются как context).
*   ✅ **FR-CHAT-004:** Атомарное списание токенов + вызов LMStudio API + возврат ответа.

### 2.2. Модуль Генерации Изображений (ComfyUI)
*   ✅ **FR-IMG-001:** Выбор предустановленного Workflow из 6 доступных JSON-шаблонов.
*   ✅ **FR-IMG-002:** Передача текстового промпта и генерация по Workflow.
*   ✅ **FR-IMG-003 (Z-Image):** Генерация изображения по промпту (`ZIT.json`).
*   ✅ **FR-IMG-004 (Qwen Image Edit):** Редактирование по 1, 2 или 3 референсам (соответствующие QWEN edit 1/2/3 pic.json).
*   ✅ Загрузка референсных изображений через `UploadFile`, сохранение в папку пользователя.
*   ✅ Расчёт стоимости генерации перед запуском, атомарное списание с баланса.

### 2.3. Модуль Генерации Видео (ComfyUI)
*   ⏳ **FR-VID-001:** Workflow зарезервированы — `text_to_video.json` и `image_to_video.json`.
*   ⏳ **FR-VID-002:** Будет реализовано после подключения видеомодели на ComfyUI.

### 2.4. Модуль Оркестрации (Workflow Chaining)
*   ✅ **FR-ORCH-001:** Изображение → Редактирование (Qwen Image Edit). Принимает asset_id + промпт + опционально новые референсы.
*   ✅ **FR-ORCH-002:** Изображение → Видео (Image-to-Video). Принимает asset_id как первый кадр.
*   🔧 Оркестратор проверяет тип asset (image/generated), списывает стоимость за оба этапа суммарно.

---

## 💰 3. Экономический Модуль

### 3.1. Валюта
*   **Единица:** Внутренняя валюта ("Кредиты").
*   **Хранение:** Поле `balance` в таблице `users`.
*   **Автоначисление:** Планируется в Phase 5 (Admin Panel → cron).

### 3.2. Расчет Стоимости LLM (Чат)
```python
Cost_LLM = (InputTokens × Rate_In) + (OutputTokens × Rate_Out)
```

### 3.3. Расчет Стоимости Генерации Изображений (ComfyUI)
*   **Z-Image (Генерация):** `Cost = BaseCost + (Width × Height) × Rate_Pixel`
*   **Qwen Image Edit:** `Cost = BaseCost_Edit + (Avg_Ref_Size × Height) × Rate_Pixel`

### 3.4. Расчет Стоимости Генерации Видео (ComfyUI)
```python
Cost_Video = BaseCost_Vid + (Resolution × Duration) × Rate_Sec
```

### 3.5. Транзакционный Процесс
1.  **Транзакция:** Все операции атомарны в PostgreSQL (`async with session.begin()`).
2.  **Проверка/Списание:** Перед вызовом API проверяется баланс и списывается стоимость.
3.  **Выполнение:** Вызов LMStudio / ComfyUI.
4.  **Фиксация:** COMMIT при успехе, ROLLBACK при ошибке.

---

## 🛠️ 4. Административные Функции (Phase 5 — в работе)

### 4.1. Управление Пользователями и Материалами
*   ✅ Просмотр списка пользователей, чатов, генераций, asset'ов.
*   ✅ Корректировка баланса пользователя администратором.
*   ✅ Принудительное удаление чатов и генераций.
*   🚧 Управление архивами (бэкапы, логи, файлы генераций).

### 4.2. Управление Группами Доступа (UserGroup)
*   ✅ Создание/редактирование групп AD.
*   ✅ Настройка прав для каждой группы: `chat_only`, `chat_generation`, `images_only`, `edit_only`, `full_access`.
*   ✅ Стартовый баланс для участников группы.
*   ✅ Автоматическое применение прав и баланса при первом входе пользователя.

### 4.3. Настройка Системы (AdminSettings)
*   ✅ Хранение конфигурации LMStudio (endpoint, model, api_key) — в БД с fallback на `.env`.
*   ✅ Хранение конфигурации ComfyUI (endpoint, api_key).
*   ✅ Глобальные коэффициенты стоимости (BaseCost, Rate_Pixel, Rate_Sec и т.д.).
*   ✅ Настройка CORS origins.
*   ✅ Изменение через Admin API + React Admin Panel.

### 4.4. Темы оформления
*   ✅ Светлая и тёмная тема в Admin Panel.
*   ✅ Переключение через Switch в шапке.
*   ✅ Сохранение выбора в localStorage.
*   ✅ CSS-переменные для кастомных стилей.

---

## 🗺️ 5. Карта Проекта (Roadmap)

| Этап | Название Этапа | Статус |
| :--- | :--- | :--- |
| **Phase 0** | **Setup & Core DB** | ✅ Завершена |
| **Phase 1** | **Auth & Economy Core** | ✅ Завершена |
| **Phase 2** | **LLM Chat Module** | ✅ Завершена |
| **Phase 3** | **ComfyUI Integration (Image)** | ✅ Завершена |
| **Phase 4** | **Advanced Features & Orchestration** | ✅ Завершена |
| **Phase 5** | **Admin Panel (API + React)** | 🚧 В работе |
| **Phase 6** | **User Frontend** | ⏳ Ожидает |

---

## 📁 Структура проекта

```
C:\Github\ACCOS\
├── backend/                    # FastAPI сервер
│   ├── app/
│   │   ├── api/v1/endpoints/   # 12 роутов (auth, user, chat, generation, orchestration, admin)
│   │   ├── core/               # config, security, dependencies, exceptions
│   │   ├── db/models/          # User, ChatSession, ChatMessage, GenerationRecord, ImageAsset, AdminSettings, UserGroup
│   │   ├── repositories/       # Repository Pattern (base, user, chat, generation, settings)
│   │   ├── services/           # auth, economy, chat, comfyui, admin, orchestration
│   │   ├── adapters/           # LMStudio, ComfyUI, LDAP (real + Mock)
│   │   ├── schemas/            # auth, chat, generation, admin
│   │   └── modules/            # BaseModule, ChatModule, ComfyUIModule
│   ├── alembic/                # Миграции (4 версии)
│   ├── tests/                  # pytest тесты
│   ├── requirements.txt
│   └── main.py
├── frontend/                   # React (пользователь) — Phase 6 ⏳
├── admin/                      # React Admin Panel — Phase 5 🚧
│   ├── src/
│   │   ├── assets/themes/      # light.ts, dark.ts
│   │   ├── assets/styles/      # CSS/MUI overrides
│   │   ├── pages/              # Dashboard, Users, Groups, Chats, Generations, Assets, Settings
│   │   ├── services/           # api, authProvider, dataProvider
│   │   └── App.tsx             # react-admin + theme toggle
│   └── package.json
├── config/                     # Единое место для конфигов
│   ├── .env                    # Секреты (в .gitignore)
│   ├── .env.example            # Шаблон
│   └── alembic.ini
├── static/                     # Статические файлы
│   ├── css/global.css          # CSS-переменные для тем
│   ├── js/                     # Общие скрипты
│   ├── images/                 # Изображения
│   └── templates/              # HTML-шаблоны (admin_preview.html)
├── workflows/                  # ComfyUI JSON шаблоны
│   ├── ZIT.json                # Text-to-Image (Z-Image)
│   ├── QWEN edit 1 pic.json    # Редактирование по 1 референсу
│   ├── QWEN edit 2 pic.json    # Редактирование по 2 референсам
│   ├── QWEN edit 3 pic.json    # Редактирование по 3 референсам
│   ├── text_to_video.json      # Зарезервировано
│   └── image_to_video.json     # Зарезервировано
├── .gitignore
├── AGENTS.md                   # Правила для AI-агента
├── CHANGELOG.md                # Лог изменений
└── README.md                   # Этот файл
```

---

## 🔌 API Эндпоинты

### Публичные (Phase 0-4)

| Path | Метод | Описание |
|------|-------|----------|
| `/api/v1/health` | GET | Проверка сервера |
| `/api/v1/auth/login` | POST | Вход (LDAP) → JWT |
| `/api/v1/auth/me` | GET | Профиль + баланс + права |
| `/api/v1/user/balance` | GET | Текущий баланс |
| `/api/v1/chat/create` | POST | Создать чат |
| `/api/v1/chat/list` | GET | Список чатов |
| `/api/v1/chat/{id}` | GET | История чата |
| `/api/v1/chat/{id}/send` | POST | Отправить сообщение |
| `/api/v1/generate/` | POST | Запустить генерацию |
| `/api/v1/generate/history` | GET | История генераций |
| `/api/v1/orchestrate/image-to-edit/{id}` | POST | Референс → редактирование |
| `/api/v1/orchestrate/image-to-video/{id}` | POST | Референс → видео |

### Admin API (Phase 5)

| Path | Метод | Описание |
|------|-------|----------|
| `/api/v1/admin/users` | GET | Список пользователей |
| `/api/v1/admin/balance/adjust` | POST | Коррекция баланса |
| `/api/v1/admin/groups` | GET | Список групп AD |
| `/api/v1/admin/groups` | POST | Создать группу |
| `/api/v1/admin/groups/{id}` | PUT | Обновить группу |
| `/api/v1/admin/chats` | GET | Список всех чатов |
| `/api/v1/admin/chats/{id}` | DELETE | Удалить чат |
| `/api/v1/admin/generations` | GET | Список генераций |
| `/api/v1/admin/generations/{id}` | DELETE | Удалить генерацию |
| `/api/v1/admin/assets` | GET | Список ресурсов |
| `/api/v1/admin/settings` | GET | Настройки системы |
| `/api/v1/admin/settings/{key}` | PUT | Изменить настройку |

---

## 🚀 Быстрый старт

```bash
# 1. Клонировать и войти
cd C:\Github\ACCOS

# 2. Настроить окружение
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Настроить config/.env (скопировать из .env.example)
# 4. Применить миграции БД
alembic -c ../config/alembic.ini upgrade head

# 5. Запустить backend
uvicorn main:app --reload

# 6. (отдельный терминал) Запустить Admin Panel
cd admin
npm run dev

# → Backend: http://127.0.0.1:8000
# → Admin:  http://127.0.0.1:5173
# → Документация API: http://127.0.0.1:8000/docs
```

---

## 🧠 Правила разработки (для AI-агента)

1.  **Транзакционная Целостность:** Все операции с балансом — атомарны в PostgreSQL.
2.  **Изоляция Процессов:** Логика разделена на сервисы/классы. FastAPI — Controller.
3.  **Паттерны:** Repository (БД) + Strategy (расчёт стоимости) + Adapter (внешние интеграции).
4.  **Модульность:** Все интеграции через абстрактные классы (BaseAdapter, BaseModule).
5.  **Генерация:**
    *   **ZIT.json (Generator):** Prompt → изображение.
    *   **QWEN edit N pic.json (Editor):** Prompt + N референсов → отредактированное изображение.
6.  **Только async/await:** Никаких синхронных `def` для эндпоинтов.
7.  **Без комментариев:** Код самодокументируемый.
8.  **Автокоммит:** После каждой завершённой фазы.

---

*Подробнее о ходе разработки — в `CHANGELOG.md` и `AGENTS.md`.*
