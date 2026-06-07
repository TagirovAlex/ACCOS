# ACCOS — AI Content & Chat Orchestrator Service

Бэкенд-оркестратор для LLM (LMStudio) и ComfyUI с экономическим модулем.

## Текущий статус

| Фаза | Статус |
|------|--------|
| Phase 0: Setup & Core DB | ✅ Завершена |
| Phase 1: Auth & Economy | ✅ Завершена |
| Phase 2: Chat Module | ⏳ Ожидает |
| Phase 3: ComfyUI Integration | ⏳ Ожидает |
| Phase 4: Orchestration | ⏳ Ожидает |
| Phase 5: Admin Panel | ⏳ Ожидает |
| Phase 6: User Frontend | ⏳ Ожидает |

## Стек

- Backend: Python 3.11 / FastAPI (async)
- Database: PostgreSQL 17 / SQLAlchemy 2.0 / Alembic
- Auth: LDAP/AD + JWT
- AI: LMStudio API + ComfyUI API
- Frontend: React (отдельно для пользователя и админа)

## Быстрый старт

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

## Эндпоинты

| Path | Описание |
|------|----------|
| `GET /api/v1/health` | Health check |
| `POST /api/v1/auth/login` | Вход по LDAP |
| `GET /api/v1/auth/me` | Информация о пользователе |
| `GET /api/v1/user/balance` | Баланс пользователя |

## Структура

```
backend/     # FastAPI сервер
frontend/    # React (пользователь)
admin/       # React Admin Panel
workflows/   # ComfyUI JSON шаблоны
```

Подробнее — в `AGENTS.md` и `CHANGELOG.md`.
