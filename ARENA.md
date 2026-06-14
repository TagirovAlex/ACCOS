# Техническое задание: MCP-серверы для LM Studio
Дата: 2025-06-20
Статус: Готово к разработке
1. Контекст и окружение
Текущая инфраструктура

    LM Studio — сервер с LLM-моделью (рекомендуется Qwen 2.5 14B+ для tool calling)
    Самописный веб-интерфейс — многопользовательский чат с LLM в локальной сети
    RAG-база — уже существует, содержит документы компании
    Всё работает в локальной сети организации

Целевая архитектура

text

Пользователи ──→ Чат-интерфейс ──→ LM Studio ←──→ MCP-серверы
                      │                                │
                      │          Admin API              │
                      └──────────────────────→──────────┘

2. Компонент A: MCP Web Scraper (доступ к веб-страницам из чата)
Назначение

Пользователи чата могут запрашивать данные с конкретных URL.
Например: "Покажи последние новости с https://example.com/news"
Функциональные требования
MCP-сервер (порт 8100)
Tool	Описание
fetch_web_page(url, user_id, max_chars)	Загрузка одной страницы, извлечение текста
fetch_multiple_pages(urls, user_id)	Загрузка нескольких страниц за один запрос
search_in_page(url, query, user_id)	Загрузка страницы + поиск релевантных абзацев по запросу
Admin API (порт 8101)

REST API для управления из основного чат-сервера.

Аутентификация: заголовок X-Admin-Secret
Метод	Endpoint	Описание
GET	/api/users	Список всех пользователей с их статистикой
GET	/api/users/{user_id}	Настройки конкретного пользователя
PUT	/api/users/{user_id}	Создать/обновить пользователя
POST	/api/users/{user_id}/enable	Быстро включить доступ
POST	/api/users/{user_id}/disable	Быстро отключить доступ
DELETE	/api/users/{user_id}	Удалить пользователя
POST	/api/users/bulk	Массовое включение/отключение
GET	/api/logs	Логи запросов (опционально фильтр по user_id)
GET	/api/stats/{user_id}	Статистика + оставшиеся лимиты
GET	/api/cache/stats	Статистика кэша
POST	/api/cache/clear	Очистка кэша
GET	/api/health	Проверка работоспособности
Система лимитов и безопасности
Настройки на уровне пользователя (хранятся в SQLite)
Параметр	По умолчанию	Описание
enabled	false	Функция выключена по умолчанию
requests_per_hour	20	Лимит запросов в час
requests_per_day	100	Лимит запросов в сутки
max_chars	10000	Максимум символов на страницу
max_pages	3	Максимум страниц за один запрос
allowed_domains	[]	Белый список доменов (пусто = все)
blocked_domains	[]	Чёрный список доменов
Глобальные настройки безопасности (config.yaml)

    Чёрный список доменов: localhost, 127.0.0.1, внутренние сети
    Блокировка расширений: .exe, .zip, .rar, .pdf, .doc
    Глобальный белый список доменов (опционально)

Логика проверки при каждом запросе

    Пользователь существует? → если нет: ⛔ "Не зарегистрирован"
    enabled = true? → если нет: ⛔ "Функция отключена"
    Домен разрешён? → проверка глобальных + пользовательских списков
    Расширение файла? → блокировка скачивания бинарных файлов
    Rate limit не превышен? → проверка за час и за сутки
    ✅ Запрос выполняется, логируется

Кэширование

    In-memory LRU кэш
    TTL: 300 секунд (настраивается)
    Максимум записей: 500
    Ключ: SHA256 от URL

Стек технологий
Компонент	Технология
MCP протокол	mcp[cli] (Python SDK), транспорт SSE
Извлечение контента	trafilatura
Admin API	FastAPI + uvicorn
База данных	SQLite (WAL mode)
HTTP клиент	httpx
Конфигурация	YAML
Схема базы данных

SQL

-- Пользователи и их настройки
CREATE TABLE users (
    user_id           TEXT PRIMARY KEY,
    enabled           INTEGER DEFAULT 0,
    requests_per_hour INTEGER DEFAULT 20,
    requests_per_day  INTEGER DEFAULT 100,
    max_chars         INTEGER DEFAULT 10000,
    max_pages         INTEGER DEFAULT 3,
    allowed_domains   TEXT DEFAULT '[]',    -- JSON array
    blocked_domains   TEXT DEFAULT '[]',    -- JSON array
    notes             TEXT DEFAULT '',
    created_at        TEXT DEFAULT (datetime('now')),
    updated_at        TEXT DEFAULT (datetime('now'))
);

-- Лог всех запросов
CREATE TABLE request_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    url            TEXT NOT NULL,
    status         TEXT NOT NULL,  -- ok | denied | rate_limited | blocked | error
    chars_returned INTEGER DEFAULT 0,
    error          TEXT DEFAULT '',
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_log_user_time ON request_log(user_id, created_at);

Файлы реализации
Файл	Назначение
server.py	MCP-сервер + запуск Admin API в отдельном потоке
admin_api.py	FastAPI приложение с REST endpoints
config.py	Загрузка config.yaml в dataclass-ы
database.py	CRUD операции, логирование, подсчёт запросов
limiter.py	Проверка доступа, лимитов, доменов
cache.py	In-memory LRU кэш с TTL
config.yaml	Все настройки
Исходный код Компонента A
config.yaml

YAML

server:
  host: "0.0.0.0"
  mcp_port: 8100
  admin_port: 8101
  admin_secret: "change-me-to-random-string-32chars"

database:
  path: "./scraper_data.db"

defaults:
  requests_per_hour: 20
  requests_per_day: 100
  max_chars_per_page: 10000
  max_pages_per_request: 3
  enabled: false

cache:
  enabled: true
  ttl_seconds: 300
  max_entries: 500

security:
  allowed_domains: []
  blocked_domains:
    - "localhost"
    - "127.0.0.1"
    - "10.0.0.0/8"
    - "192.168.0.0/16"
  block_extensions:
    - ".exe"
    - ".zip"
    - ".rar"
    - ".pdf"
    - ".doc"

config.py

Python

import yaml
from pathlib import Path
from dataclasses import dataclass, field

CONFIG_PATH = Path(__file__).parent / "config.yaml"


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    mcp_port: int = 8100
    admin_port: int = 8101
    admin_secret: str = "change-me"


@dataclass
class DefaultLimits:
    requests_per_hour: int = 20
    requests_per_day: int = 100
    max_chars_per_page: int = 10000
    max_pages_per_request: int = 3
    enabled: bool = False


@dataclass
class CacheConfig:
    enabled: bool = True
    ttl_seconds: int = 300
    max_entries: int = 500


@dataclass
class SecurityConfig:
    allowed_domains: list[str] = field(default_factory=list)
    blocked_domains: list[str] = field(default_factory=list)
    block_extensions: list[str] = field(default_factory=list)


@dataclass
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    defaults: DefaultLimits = field(default_factory=DefaultLimits)
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)


def load_config() -> AppConfig:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            raw = yaml.safe_load(f) or {}
    else:
        raw = {}

    config = AppConfig()

    if "server" in raw:
        config.server = ServerConfig(**raw["server"])
    if "defaults" in raw:
        config.defaults = DefaultLimits(**raw["defaults"])
    if "cache" in raw:
        config.cache = CacheConfig(**raw["cache"])
    if "security" in raw:
        config.security = SecurityConfig(**raw["security"])

    return config


CONFIG = load_config()

database.py

Python

import sqlite3
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from config import CONFIG

DB_PATH = CONFIG.server.__dict__.get("db_path", None) or "./scraper_data.db"

_local = threading.local()


def get_db() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id          TEXT PRIMARY KEY,
            enabled          INTEGER DEFAULT 0,
            requests_per_hour INTEGER DEFAULT 20,
            requests_per_day  INTEGER DEFAULT 100,
            max_chars        INTEGER DEFAULT 10000,
            max_pages        INTEGER DEFAULT 3,
            allowed_domains  TEXT DEFAULT '[]',
            blocked_domains  TEXT DEFAULT '[]',
            notes            TEXT DEFAULT '',
            created_at       TEXT DEFAULT (datetime('now')),
            updated_at       TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS request_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            url         TEXT NOT NULL,
            status      TEXT NOT NULL,
            chars_returned INTEGER DEFAULT 0,
            error       TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_log_user_time
            ON request_log(user_id, created_at);

        CREATE TABLE IF NOT EXISTS global_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    db.commit()
    db.close()


def get_user(user_id: str) -> dict | None:
    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row:
        d = dict(row)
        d["allowed_domains"] = json.loads(d["allowed_domains"])
        d["blocked_domains"] = json.loads(d["blocked_domains"])
        return d
    return None


def upsert_user(user_id: str, **kwargs) -> dict:
    db = get_db()
    existing = get_user(user_id)

    if existing is None:
        data = {
            "user_id": user_id,
            "enabled": int(CONFIG.defaults.enabled),
            "requests_per_hour": CONFIG.defaults.requests_per_hour,
            "requests_per_day": CONFIG.defaults.requests_per_day,
            "max_chars": CONFIG.defaults.max_chars_per_page,
            "max_pages": CONFIG.defaults.max_pages_per_request,
            "allowed_domains": "[]",
            "blocked_domains": "[]",
            "notes": "",
        }
    else:
        data = {
            "user_id": user_id,
            "enabled": existing["enabled"],
            "requests_per_hour": existing["requests_per_hour"],
            "requests_per_day": existing["requests_per_day"],
            "max_chars": existing["max_chars"],
            "max_pages": existing["max_pages"],
            "allowed_domains": json.dumps(existing["allowed_domains"]),
            "blocked_domains": json.dumps(existing["blocked_domains"]),
            "notes": existing.get("notes", ""),
        }

    for k, v in kwargs.items():
        if k in ("allowed_domains", "blocked_domains") and isinstance(v, list):
            data[k] = json.dumps(v)
        elif k == "enabled" and isinstance(v, bool):
            data[k] = int(v)
        elif k in data:
            data[k] = v

    db.execute("""
        INSERT INTO users (user_id, enabled, requests_per_hour, requests_per_day,
                          max_chars, max_pages, allowed_domains, blocked_domains, notes,
                          updated_at)
        VALUES (:user_id, :enabled, :requests_per_hour, :requests_per_day,
                :max_chars, :max_pages, :allowed_domains, :blocked_domains, :notes,
                datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET
            enabled = :enabled,
            requests_per_hour = :requests_per_hour,
            requests_per_day = :requests_per_day,
            max_chars = :max_chars,
            max_pages = :max_pages,
            allowed_domains = :allowed_domains,
            blocked_domains = :blocked_domains,
            notes = :notes,
            updated_at = datetime('now')
    """, data)
    db.commit()
    return get_user(user_id)


def list_users() -> list[dict]:
    db = get_db()
    rows = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["allowed_domains"] = json.loads(d["allowed_domains"])
        d["blocked_domains"] = json.loads(d["blocked_domains"])
        result.append(d)
    return result


def delete_user(user_id: str) -> bool:
    db = get_db()
    cur = db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    db.commit()
    return cur.rowcount > 0


def log_request(user_id: str, url: str, status: str,
                chars_returned: int = 0, error: str = ""):
    db = get_db()
    db.execute("""
        INSERT INTO request_log (user_id, url, status, chars_returned, error)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, url, status, chars_returned, error))
    db.commit()


def count_requests(user_id: str, hours: int) -> int:
    db = get_db()
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    row = db.execute("""
        SELECT COUNT(*) as cnt FROM request_log
        WHERE user_id = ? AND created_at >= ? AND status = 'ok'
    """, (user_id, since)).fetchone()
    return row["cnt"] if row else 0


def get_user_stats(user_id: str) -> dict:
    return {
        "requests_last_hour": count_requests(user_id, 1),
        "requests_last_24h": count_requests(user_id, 24),
        "requests_last_7d": count_requests(user_id, 168),
    }


def get_recent_logs(user_id: str = None, limit: int = 50) -> list[dict]:
    db = get_db()
    if user_id:
        rows = db.execute("""
            SELECT * FROM request_log WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
    else:
        rows = db.execute("""
            SELECT * FROM request_log
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]

limiter.py

Python

from urllib.parse import urlparse
from database import get_user, count_requests, log_request
from config import CONFIG


class AccessDenied(Exception):
    pass


class RateLimitExceeded(Exception):
    pass


class DomainBlocked(Exception):
    pass


def check_access(user_id: str, url: str) -> dict:
    user = get_user(user_id)

    if user is None:
        raise AccessDenied(
            f"Пользователь '{user_id}' не зарегистрирован для веб-доступа. "
            "Обратитесь к администратору."
        )

    if not user["enabled"]:
        raise AccessDenied(
            "Функция веб-доступа отключена для вашего аккаунта. "
            "Обратитесь к администратору."
        )

    parsed = urlparse(url)
    domain = parsed.hostname or ""

    _check_domain(domain, user)

    path_lower = parsed.path.lower()
    for ext in CONFIG.security.block_extensions:
        if path_lower.endswith(ext):
            raise DomainBlocked(f"Загрузка файлов {ext} запрещена")

    hour_count = count_requests(user_id, 1)
    if hour_count >= user["requests_per_hour"]:
        raise RateLimitExceeded(
            f"Превышен лимит запросов: {hour_count}/{user['requests_per_hour']} в час. "
            "Попробуйте позже."
        )

    day_count = count_requests(user_id, 24)
    if day_count >= user["requests_per_day"]:
        raise RateLimitExceeded(
            f"Превышен дневной лимит: {day_count}/{user['requests_per_day']}. "
            "Попробуйте завтра."
        )

    return user


def _check_domain(domain: str, user: dict):
    if not domain:
        raise DomainBlocked("Некорректный URL")

    for blocked in CONFIG.security.blocked_domains:
        if _domain_matches(domain, blocked):
            raise DomainBlocked(f"Домен {domain} заблокирован")

    for blocked in user.get("blocked_domains", []):
        if _domain_matches(domain, blocked):
            raise DomainBlocked(f"Домен {domain} заблокирован для вашего аккаунта")

    if CONFIG.security.allowed_domains:
        if not any(_domain_matches(domain, a) for a in CONFIG.security.allowed_domains):
            raise DomainBlocked(f"Домен {domain} не в списке разрешённых")

    if user.get("allowed_domains"):
        if not any(_domain_matches(domain, a) for a in user["allowed_domains"]):
            raise DomainBlocked(f"Домен {domain} не в вашем списке разрешённых")


def _domain_matches(domain: str, pattern: str) -> bool:
    if "/" in pattern:
        return domain.startswith(pattern.split("/")[0].rstrip(".0"))
    return domain == pattern or domain.endswith("." + pattern)

cache.py

Python

import time
import hashlib
import threading
from collections import OrderedDict
from config import CONFIG


class PageCache:
    def __init__(self):
        self._cache: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._lock = threading.Lock()
        self.ttl = CONFIG.cache.ttl_seconds
        self.max_entries = CONFIG.cache.max_entries
        self.enabled = CONFIG.cache.enabled

    def _key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    def get(self, url: str) -> str | None:
        if not self.enabled:
            return None
        key = self._key(url)
        with self._lock:
            if key in self._cache:
                ts, content = self._cache[key]
                if time.time() - ts < self.ttl:
                    self._cache.move_to_end(key)
                    return content
                else:
                    del self._cache[key]
        return None

    def set(self, url: str, content: str):
        if not self.enabled:
            return
        key = self._key(url)
        with self._lock:
            self._cache[key] = (time.time(), content)
            self._cache.move_to_end(key)
            while len(self._cache) > self.max_entries:
                self._cache.popitem(last=False)

    def clear(self):
        with self._lock:
            self._cache.clear()

    def stats(self) -> dict:
        with self._lock:
            return {
                "entries": len(self._cache),
                "max_entries": self.max_entries,
                "ttl_seconds": self.ttl,
                "enabled": self.enabled,
            }


page_cache = PageCache()

server.py

Python

import json
import threading
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP
from trafilatura import fetch_url, extract
from trafilatura.settings import use_config

from config import CONFIG
from database import init_db, log_request, get_user
from limiter import check_access, AccessDenied, RateLimitExceeded, DomainBlocked
from cache import page_cache

init_db()

traf_config = use_config()
traf_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")

mcp = FastMCP(
    "WebScraper",
    host=CONFIG.server.host,
    port=CONFIG.server.mcp_port,
)


def _normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _do_fetch(url: str, max_chars: int) -> str:
    cached = page_cache.get(url)
    if cached:
        text = cached
    else:
        downloaded = fetch_url(url)
        if not downloaded:
            raise Exception(f"Не удалось загрузить страницу")

        text = extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_links=True,
            include_formatting=True,
            favor_recall=True,
            config=traf_config,
        )

        if not text:
            raise Exception("Страница загружена, но контент не извлечён")

        page_cache.set(url, text)

    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n... [контент обрезан]"

    return text


@mcp.tool()
def fetch_web_page(url: str, user_id: str = "anonymous",
                   max_chars: int = 0) -> str:
    """
    Загружает веб-страницу и возвращает текстовый контент.
    Используй когда пользователь просит получить информацию
    с конкретного URL или веб-сайта.

    ВАЖНО: всегда передавай user_id текущего пользователя из контекста чата.

    Args:
        url: URL страницы для загрузки
        user_id: ID пользователя (передаётся автоматически)
        max_chars: Максимум символов (0 = лимит пользователя)
    """
    url = _normalize_url(url)

    try:
        user_settings = check_access(user_id, url)

        if max_chars <= 0:
            max_chars = user_settings["max_chars"]
        else:
            max_chars = min(max_chars, user_settings["max_chars"])

        content = _do_fetch(url, max_chars)
        log_request(user_id, url, "ok", len(content))
        return f"[Источник: {url}]\n\n{content}"

    except AccessDenied as e:
        log_request(user_id, url, "denied", error=str(e))
        return f"⛔ Доступ запрещён: {e}"

    except RateLimitExceeded as e:
        log_request(user_id, url, "rate_limited", error=str(e))
        return f"⏱️ {e}"

    except DomainBlocked as e:
        log_request(user_id, url, "blocked", error=str(e))
        return f"🚫 {e}"

    except Exception as e:
        log_request(user_id, url, "error", error=str(e))
        return f"❌ Ошибка: {e}"


@mcp.tool()
def fetch_multiple_pages(urls: list[str], user_id: str = "anonymous") -> str:
    """
    Загружает несколько веб-страниц за один запрос.

    Args:
        urls: Список URL-адресов (максимум определяется лимитами)
        user_id: ID пользователя
    """
    try:
        user_settings = check_access(user_id, urls[0] if urls else "http://check")
    except (AccessDenied, RateLimitExceeded, DomainBlocked) as e:
        return f"⛔ {e}"

    max_pages = user_settings["max_pages"]
    if len(urls) > max_pages:
        return f"⛔ Максимум {max_pages} страниц за запрос. Вы запросили {len(urls)}."

    chars_per_page = user_settings["max_chars"] // len(urls)
    results = []

    for url in urls:
        result = fetch_web_page(url, user_id, chars_per_page)
        results.append(result)

    return "\n\n" + ("═" * 60) + "\n\n".join(results)


if __name__ == "__main__":
    from admin_api import start_admin_api

    admin_thread = threading.Thread(target=start_admin_api, daemon=True)
    admin_thread.start()

    mcp.run(transport="sse")

admin_api.py

Python

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import uvicorn

from config import CONFIG
from database import (
    get_user, upsert_user, delete_user, list_users,
    get_user_stats, get_recent_logs, init_db
)
from cache import page_cache

app = FastAPI(title="Web Scraper Admin API", docs_url="/docs")


async def verify_admin(x_admin_secret: str = Header(...)):
    if x_admin_secret != CONFIG.server.admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    return True


class UserUpdate(BaseModel):
    enabled: bool | None = None
    requests_per_hour: int | None = None
    requests_per_day: int | None = None
    max_chars: int | None = None
    max_pages: int | None = None
    allowed_domains: list[str] | None = None
    blocked_domains: list[str] | None = None
    notes: str | None = None


class BulkEnableRequest(BaseModel):
    user_ids: list[str]
    enabled: bool


@app.get("/api/users")
async def api_list_users(auth=Depends(verify_admin)):
    users = list_users()
    for u in users:
        u["stats"] = get_user_stats(u["user_id"])
    return {"users": users}


@app.get("/api/users/{user_id}")
async def api_get_user(user_id: str, auth=Depends(verify_admin)):
    user = get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    user["stats"] = get_user_stats(user_id)
    return user


@app.put("/api/users/{user_id}")
async def api_update_user(user_id: str, data: UserUpdate,
                          auth=Depends(verify_admin)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    user = upsert_user(user_id, **update_data)
    return {"status": "ok", "user": user}


@app.post("/api/users/{user_id}/enable")
async def api_enable_user(user_id: str, auth=Depends(verify_admin)):
    user = upsert_user(user_id, enabled=True)
    return {"status": "ok", "user": user}


@app.post("/api/users/{user_id}/disable")
async def api_disable_user(user_id: str, auth=Depends(verify_admin)):
    user = upsert_user(user_id, enabled=False)
    return {"status": "ok", "user": user}


@app.delete("/api/users/{user_id}")
async def api_delete_user(user_id: str, auth=Depends(verify_admin)):
    if delete_user(user_id):
        return {"status": "ok"}
    raise HTTPException(404, "User not found")


@app.post("/api/users/bulk")
async def api_bulk_enable(data: BulkEnableRequest,
                          auth=Depends(verify_admin)):
    results = []
    for uid in data.user_ids:
        user = upsert_user(uid, enabled=data.enabled)
        results.append(user)
    return {"status": "ok", "updated": len(results)}


@app.get("/api/logs")
async def api_logs(user_id: str = None, limit: int = 50,
                   auth=Depends(verify_admin)):
    logs = get_recent_logs(user_id, limit)
    return {"logs": logs}


@app.get("/api/stats/{user_id}")
async def api_user_stats(user_id: str, auth=Depends(verify_admin)):
    user = get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    stats = get_user_stats(user_id)
    return {
        "user_id": user_id,
        "limits": {
            "per_hour": user["requests_per_hour"],
            "per_day": user["requests_per_day"],
        },
        "usage": stats,
        "remaining": {
            "this_hour": max(0, user["requests_per_hour"] - stats["requests_last_hour"]),
            "today": max(0, user["requests_per_day"] - stats["requests_last_24h"]),
        }
    }


@app.get("/api/cache/stats")
async def api_cache_stats(auth=Depends(verify_admin)):
    return page_cache.stats()


@app.post("/api/cache/clear")
async def api_cache_clear(auth=Depends(verify_admin)):
    page_cache.clear()
    return {"status": "ok", "message": "Cache cleared"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "mcp-web-scraper"}


def start_admin_api():
    print(f"🔧 Admin API запущен на порту {CONFIG.server.admin_port}")
    uvicorn.run(
        app,
        host=CONFIG.server.host,
        port=CONFIG.server.admin_port,
        log_level="warning",
    )

3. Компонент B: MCP Documentation Scraper (полный скрапинг сайта в RAG)
Назначение

Скрапинг целых документационных сайтов для загрузки в единую RAG-базу
(рядом с документами компании). Управляется из основного сервера через Admin API.
Функциональные требования
MCP-сервер (порт 8200)
Tool	Описание
scrape_documentation_site(site_url, site_name, max_pages, collection)	Запуск полного обхода сайта (асинхронно)
check_scrape_status(job_id)	Проверка статуса задачи
list_scrape_jobs()	Список всех задач
cancel_scrape_job(job_id)	Отмена задачи
remove_site_from_rag(site_name, collection)	Удаление данных сайта из RAG
Admin API (порт 8201)
Метод	Endpoint	Описание
POST	/api/scrape	Запуск скрапинга
GET	/api/jobs	Список всех задач
GET	/api/jobs/{job_id}	Детали задачи
POST	/api/jobs/{job_id}/cancel	Отмена задачи
DELETE	/api/sites/{site_name}	Удаление данных сайта из RAG
GET	/api/health	Health check
Пайплайн обработки

text

[queued] → [crawling] → [processing] → [ingesting] → [completed]
                                                       или
                                                      [failed]

Этап 1: Crawling (обход сайта)

    BFS (breadth-first search) обход по ссылкам
    Начинается с корневого URL
    Ограничение: только тот же домен + базовый путь
    Параллельные запросы (настраивается, по умолчанию 3)
    Задержка между запросами (0.5 сек)
    Фильтрация ссылок:
        Исключаются: изображения, CSS, JS, PDF, архивы, /api/, /search, /login
        Только text/html контент
        Удаление якорей (#fragment)
    Извлечение контента через trafilatura
    Извлечение метаданных: заголовок (h1 > title), хлебные крошки
    Пропуск страниц с контентом < 50 символов

Настройки краулера
Параметр	По умолчанию	Описание
max_pages	500	Максимум страниц на сайт
max_depth	10	Глубина обхода
delay_between_requests	0.5 сек	Пауза между запросами
timeout	30 сек	Таймаут на страницу
concurrent_requests	3	Параллельные запросы
Этап 2: Chunking (разбивка на куски)

    Метод: семантический (по заголовкам → по абзацам → по размеру)
    Алгоритм:
        Разбить по markdown-заголовкам
        Если секция > chunk_size → разбить по двойным переносам строк
        Если всё ещё большие → разбить по размеру с перекрытием
        Склеить мелкие абзацы
        Отбросить чанки < min_chunk_size

Параметр	По умолчанию
chunk_size	1000 символов
chunk_overlap	150 символов
min_chunk_size	100 символов
Этап 3: Ingestion (загрузка в RAG)

Каждый чанк содержит метаданные:

JSON

{
    "text": "Содержимое чанка...",
    "metadata": {
        "source_url": "https://docs.example.com/guide/quickstart",
        "page_title": "Quick Start Guide",
        "site_name": "Example Docs",
        "doc_type": "external_documentation",
        "breadcrumbs": "Home > Guide > Quick Start",
        "chunk_index": 2,
        "total_chunks": 5,
        "word_count": 187,
        "fetched_at": "2025-06-20T12:00:00Z",
        "display_title": "Example Docs — Quick Start Guide"
    }
}

Поле doc_type: "external_documentation" отличает скрапированные документы
от внутренних (doc_type: "internal").
Поддержка RAG-бэкендов (адаптеры)
Бэкенд	Класс	Описание
HTTP API	HTTPRAGClient	Отправка через REST API основного сервера
ChromaDB	ChromaRAGClient	Прямая запись в ChromaDB
Qdrant	QdrantRAGClient	Прямая запись в Qdrant

Логика ingestion:

    Удалить старые данные этого site_name из коллекции
    Отправить новые чанки батчами по 50-100
    Использовать upsert с ID = hash от site_name + url + chunk_index

Исходный код Компонента B
config.yaml

YAML

server:
  host: "0.0.0.0"
  mcp_port: 8200
  admin_port: 8201
  admin_secret: "your-secret-key-here"

crawler:
  max_pages: 500
  max_depth: 10
  delay_between_requests: 0.5
  timeout: 30
  concurrent_requests: 3
  respect_robots_txt: true
  user_agent: "DocsBot/1.0 (internal documentation indexer)"

chunking:
  method: "semantic"
  chunk_size: 1000
  chunk_overlap: 150
  min_chunk_size: 100

rag:
  endpoint: "http://your-main-server:8000/api/rag/ingest"
  api_key: "your-rag-api-key"

models.py

Python

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    CRAWLING = "crawling"
    PROCESSING = "processing"
    INGESTING = "ingesting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScrapedPage:
    url: str
    title: str
    content: str
    markdown: str
    breadcrumbs: list[str]
    depth: int
    parent_url: str | None = None
    word_count: int = 0
    fetched_at: str = ""


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class CrawlJob:
    job_id: str
    site_url: str
    site_name: str
    status: JobStatus = JobStatus.QUEUED
    pages_found: int = 0
    pages_scraped: int = 0
    chunks_created: int = 0
    chunks_ingested: int = 0
    errors: list[str] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""
    config_overrides: dict = field(default_factory=dict)

crawler.py

Python

import asyncio
import re
import time
from urllib.parse import urlparse, urljoin, urldefrag
from dataclasses import dataclass

import httpx
from trafilatura import extract
from trafilatura.settings import use_config
from bs4 import BeautifulSoup

from models import ScrapedPage

traf_config = use_config()
traf_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")


@dataclass
class CrawlConfig:
    max_pages: int = 500
    max_depth: int = 10
    delay: float = 0.5
    timeout: int = 30
    concurrent: int = 3
    user_agent: str = "DocsBot/1.0"
    include_patterns: list[str] = None
    exclude_patterns: list[str] = None

    def __post_init__(self):
        self.include_patterns = self.include_patterns or []
        self.exclude_patterns = self.exclude_patterns or [
            r"/api/",
            r"\.(png|jpg|gif|svg|css|js|woff|ico|pdf|zip)$",
            r"/search",
            r"/login",
            r"/signup",
            r"#",
            r"\?.*page=",
        ]


class SiteCrawler:
    def __init__(self, base_url: str, config: CrawlConfig = None,
                 progress_callback=None):
        self.base_url = base_url.rstrip("/")
        self.config = config or CrawlConfig()
        self.progress_callback = progress_callback

        parsed = urlparse(self.base_url)
        self.base_domain = parsed.netloc
        self.base_path = parsed.path or "/"

        self.visited: set[str] = set()
        self.pages: list[ScrapedPage] = []
        self.errors: list[str] = []
        self._semaphore = asyncio.Semaphore(self.config.concurrent)
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _normalize_url(self, url: str) -> str | None:
        url, _ = urldefrag(url)
        url = url.rstrip("/")
        parsed = urlparse(url)

        if parsed.netloc and parsed.netloc != self.base_domain:
            return None

        if not parsed.path.startswith(self.base_path):
            return None

        for pattern in self.config.exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return None

        if self.config.include_patterns:
            if not any(re.search(p, url) for p in self.config.include_patterns):
                return None

        return url

    def _extract_links(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute = urljoin(page_url, href)
            normalized = self._normalize_url(absolute)
            if normalized and normalized not in self.visited:
                links.append(normalized)
        return list(set(links))

    def _extract_breadcrumbs(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        for selector in [
            "nav[aria-label*='breadcrumb']",
            ".breadcrumb", ".breadcrumbs",
            "[class*='breadcrumb']",
            "ol.breadcrumb",
        ]:
            bc = soup.select_one(selector)
            if bc:
                items = bc.find_all("li") or bc.find_all("a")
                return [item.get_text(strip=True) for item in items
                        if item.get_text(strip=True)]
        return []

    def _extract_title(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title = soup.find("title")
        if title:
            return title.get_text(strip=True)
        return ""

    async def _fetch_page(self, client: httpx.AsyncClient,
                          url: str, depth: int,
                          parent_url: str = None) -> list[str]:
        if self._cancelled:
            return []
        if url in self.visited:
            return []
        if len(self.visited) >= self.config.max_pages:
            return []
        if depth > self.config.max_depth:
            return []

        self.visited.add(url)

        async with self._semaphore:
            try:
                await asyncio.sleep(self.config.delay)

                resp = await client.get(
                    url, follow_redirects=True,
                    timeout=self.config.timeout
                )

                if resp.status_code != 200:
                    self.errors.append(f"{url}: HTTP {resp.status_code}")
                    return []

                content_type = resp.headers.get("content-type", "")
                if "text/html" not in content_type:
                    return []

                html = resp.text

                text_content = extract(
                    html,
                    include_comments=False,
                    include_tables=True,
                    include_links=False,
                    include_formatting=True,
                    favor_recall=True,
                    config=traf_config,
                )

                markdown_content = extract(
                    html,
                    include_comments=False,
                    include_tables=True,
                    include_links=True,
                    include_formatting=True,
                    favor_recall=True,
                    output_format="txt",
                    config=traf_config,
                )

                if not text_content or len(text_content.strip()) < 50:
                    links = self._extract_links(html, url)
                    return links

                title = self._extract_title(html)
                breadcrumbs = self._extract_breadcrumbs(html)

                page = ScrapedPage(
                    url=url,
                    title=title,
                    content=text_content,
                    markdown=markdown_content or text_content,
                    breadcrumbs=breadcrumbs,
                    depth=depth,
                    parent_url=parent_url,
                    word_count=len(text_content.split()),
                    fetched_at=time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                    ),
                )
                self.pages.append(page)

                if self.progress_callback:
                    self.progress_callback(
                        pages_scraped=len(self.pages),
                        current_url=url
                    )

                links = self._extract_links(html, url)
                return links

            except Exception as e:
                self.errors.append(f"{url}: {str(e)}")
                return []

    async def crawl(self) -> list[ScrapedPage]:
        headers = {"User-Agent": self.config.user_agent}

        async with httpx.AsyncClient(headers=headers) as client:
            queue: list[tuple[str, int, str | None]] = [
                (self.base_url, 0, None)
            ]

            while queue and not self._cancelled:
                batch = []
                while queue and len(batch) < self.config.concurrent:
                    item = queue.pop(0)
                    if item[0] not in self.visited:
                        batch.append(item)

                if not batch:
                    break

                tasks = [
                    self._fetch_page(client, url, depth, parent)
                    for url, depth, parent in batch
                ]
                results = await asyncio.gather(*tasks)

                for (url, depth, _), new_links in zip(batch, results):
                    for link in new_links:
                        if link not in self.visited:
                            queue.append((link, depth + 1, url))

                if len(self.visited) >= self.config.max_pages:
                    break

        return self.pages

chunker.py

Python

import re
from models import Chunk, ScrapedPage


class DocumentChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 150,
                 min_size: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_size = min_size

    def chunk_page(self, page: ScrapedPage, site_name: str) -> list[Chunk]:
        text = page.content

        if not text or len(text.strip()) < self.min_size:
            return []

        sections = self._split_by_headers(text)

        chunks = []
        for section in sections:
            if len(section) <= self.chunk_size:
                if len(section.strip()) >= self.min_size:
                    chunks.append(section)
            else:
                sub_chunks = self._split_by_size(section)
                chunks.extend(sub_chunks)

        result = []
        for i, chunk_text in enumerate(chunks):
            chunk = Chunk(
                text=chunk_text.strip(),
                metadata={
                    "source_url": page.url,
                    "page_title": page.title,
                    "site_name": site_name,
                    "doc_type": "external_documentation",
                    "breadcrumbs": " > ".join(page.breadcrumbs)
                                  if page.breadcrumbs else "",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "word_count": len(chunk_text.split()),
                    "fetched_at": page.fetched_at,
                    "display_title": f"{site_name} — {page.title}"
                                     if page.title else site_name,
                },
            )
            result.append(chunk)

        return result

    def _split_by_headers(self, text: str) -> list[str]:
        pattern = (
            r'\n(?=#{1,4}\s)'
            r'|(?:\n\n(?=[A-ZА-ЯЁ][^\n]{5,}\n[-=]{3,}))'
        )
        parts = re.split(pattern, text)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) <= 1:
            parts = text.split("\n\n")
            parts = [p.strip() for p in parts if p.strip()]

            merged = []
            current = ""
            for part in parts:
                if len(current) + len(part) + 2 <= self.chunk_size:
                    current = current + "\n\n" + part if current else part
                else:
                    if current:
                        merged.append(current)
                    current = part
            if current:
                merged.append(current)
            return merged

        return parts

    def _split_by_size(self, text: str) -> list[str]:
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current) + len(para) + 2 <= self.chunk_size:
                current = current + "\n\n" + para if current else para
            else:
                if current and len(current) >= self.min_size:
                    chunks.append(current)

                if self.overlap > 0 and current:
                    overlap_text = current[-self.overlap:]
                    dot_pos = overlap_text.find(". ")
                    if dot_pos > 0:
                        overlap_text = overlap_text[dot_pos + 2:]
                    current = overlap_text + "\n\n" + para
                else:
                    current = para

        if current and len(current) >= self.min_size:
            chunks.append(current)

        return chunks

    def chunk_all_pages(self, pages: list[ScrapedPage],
                        site_name: str) -> list[Chunk]:
        all_chunks = []
        for page in pages:
            page_chunks = self.chunk_page(page, site_name)
            all_chunks.extend(page_chunks)
        return all_chunks

rag_client.py

Python

import httpx
import json
import hashlib
from abc import ABC, abstractmethod
from models import Chunk


class RAGClient(ABC):
    @abstractmethod
    async def ingest_chunks(self, chunks: list[Chunk],
                            collection: str) -> dict:
        pass

    @abstractmethod
    async def delete_by_source(self, site_name: str,
                               collection: str) -> dict:
        pass


class HTTPRAGClient(RAGClient):
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key

    async def ingest_chunks(self, chunks: list[Chunk],
                            collection: str = "default") -> dict:
        async with httpx.AsyncClient(timeout=120) as client:
            total_sent = 0
            batch_size = 50

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                payload = {
                    "collection": collection,
                    "documents": [
                        {
                            "text": chunk.text,
                            "metadata": chunk.metadata,
                        }
                        for chunk in batch
                    ]
                }

                resp = await client.post(
                    f"{self.endpoint}/ingest",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    }
                )
                resp.raise_for_status()
                total_sent += len(batch)

            return {"ingested": total_sent}

    async def delete_by_source(self, site_name: str,
                               collection: str = "default") -> dict:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.endpoint}/delete",
                json={
                    "collection": collection,
                    "filter": {"site_name": site_name}
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            resp.raise_for_status()
            return resp.json()


class ChromaRAGClient(RAGClient):
    def __init__(self, host: str = "localhost", port: int = 8000):
        import chromadb
        self.client = chromadb.HttpClient(host=host, port=port)

    async def ingest_chunks(self, chunks: list[Chunk],
                            collection: str = "company_docs") -> dict:
        col = self.client.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"}
        )

        batch_size = 100
        total = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            ids = [
                hashlib.sha256(
                    f"{c.metadata['site_name']}_{c.metadata['source_url']}"
                    f"_{c.metadata['chunk_index']}".encode()
                ).hexdigest()[:16]
                for c in batch
            ]

            col.upsert(
                ids=ids,
                documents=[c.text for c in batch],
                metadatas=[c.metadata for c in batch],
            )
            total += len(batch)

        return {"ingested": total}

    async def delete_by_source(self, site_name: str,
                               collection: str = "company_docs") -> dict:
        col = self.client.get_collection(collection)
        col.delete(where={"site_name": site_name})
        return {"deleted": True}


import yaml

def create_rag_client() -> RAGClient:
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)

    rag_cfg = cfg.get("rag", {})
    rag_type = rag_cfg.get("type", "http")

    if rag_type == "chromadb":
        return ChromaRAGClient(
            host=rag_cfg.get("chromadb_host", "localhost"),
            port=rag_cfg.get("chromadb_port", 8000),
        )
    else:
        return HTTPRAGClient(
            endpoint=rag_cfg.get("endpoint", "http://localhost:8000/api/rag"),
            api_key=rag_cfg.get("api_key", ""),
        )

server.py

Python

import asyncio
import threading
import uuid
import time
import yaml
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from crawler import SiteCrawler, CrawlConfig
from chunker import DocumentChunker
from rag_client import create_rag_client
from models import CrawlJob, JobStatus

with open("config.yaml") as f:
    CFG = yaml.safe_load(f)

mcp = FastMCP(
    "DocsScraper",
    host=CFG["server"]["host"],
    port=CFG["server"]["mcp_port"],
)

jobs: dict[str, CrawlJob] = {}
active_crawlers: dict[str, SiteCrawler] = {}
rag_client = create_rag_client()


@mcp.tool()
def scrape_documentation_site(
    site_url: str,
    site_name: str,
    max_pages: int = 200,
    collection: str = "company_docs"
) -> str:
    """
    Полностью скрапит документационный сайт и загружает
    в RAG-базу знаний. Процесс асинхронный.

    Args:
        site_url: Корневой URL документации
        site_name: Понятное название
        max_pages: Максимум страниц для загрузки
        collection: Название коллекции в RAG-базе
    """
    job_id = str(uuid.uuid4())[:8]

    job = CrawlJob(
        job_id=job_id,
        site_url=site_url,
        site_name=site_name,
        status=JobStatus.QUEUED,
        created_at=datetime.utcnow().isoformat(),
        config_overrides={
            "max_pages": max_pages,
            "collection": collection
        },
    )
    jobs[job_id] = job

    thread = threading.Thread(
        target=_run_job_sync,
        args=(job_id,),
        daemon=True
    )
    thread.start()

    return (
        f"✅ Задача создана: {job_id}\n"
        f"Сайт: {site_url}\n"
        f"Название: {site_name}\n"
        f"Лимит страниц: {max_pages}\n\n"
        f"Используйте check_scrape_status(job_id='{job_id}') "
        f"для проверки статуса."
    )


@mcp.tool()
def check_scrape_status(job_id: str) -> str:
    """Проверяет статус задачи скрапинга."""
    job = jobs.get(job_id)
    if not job:
        return f"❌ Задача {job_id} не найдена"

    status_icons = {
        JobStatus.QUEUED: "⏳",
        JobStatus.CRAWLING: "🔄",
        JobStatus.PROCESSING: "⚙️",
        JobStatus.INGESTING: "📥",
        JobStatus.COMPLETED: "✅",
        JobStatus.FAILED: "❌",
        JobStatus.CANCELLED: "🚫",
    }

    icon = status_icons.get(job.status, "❓")
    lines = [
        f"{icon} Задача: {job.job_id}",
        f"Статус: {job.status.value}",
        f"Сайт: {job.site_url}",
        f"Страниц найдено: {job.pages_found}",
        f"Страниц обработано: {job.pages_scraped}",
        f"Чанков создано: {job.chunks_created}",
        f"Чанков загружено в RAG: {job.chunks_ingested}",
    ]

    if job.errors:
        lines.append(f"Ошибки ({len(job.errors)}):")
        for err in job.errors[:5]:
            lines.append(f"  • {err}")
        if len(job.errors) > 5:
            lines.append(f"  ... и ещё {len(job.errors) - 5}")

    if job.completed_at:
        lines.append(f"Завершено: {job.completed_at}")

    return "\n".join(lines)


@mcp.tool()
def list_scrape_jobs() -> str:
    """Показывает все задачи скрапинга"""
    if not jobs:
        return "Нет задач"

    lines = ["Задачи скрапинга:", ""]
    for job in jobs.values():
        lines.append(
            f"  [{job.status.value:>12}] {job.job_id} — "
            f"{job.site_name} ({job.pages_scraped} стр.)"
        )

    return "\n".join(lines)


@mcp.tool()
def cancel_scrape_job(job_id: str) -> str:
    """Отменяет задачу скрапинга"""
    job = jobs.get(job_id)
    if not job:
        return f"Задача {job_id} не найдена"

    if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
        return f"Задача уже завершена со статусом {job.status.value}"

    job.status = JobStatus.CANCELLED
    crawler = active_crawlers.get(job_id)
    if crawler:
        crawler.cancel()

    return f"Задача {job_id} отменена"


@mcp.tool()
def remove_site_from_rag(
    site_name: str,
    collection: str = "company_docs"
) -> str:
    """Удаляет все документы конкретного сайта из RAG-базы."""
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            rag_client.delete_by_source(site_name, collection)
        )
        loop.close()
        return (
            f"✅ Документы '{site_name}' удалены "
            f"из коллекции '{collection}'"
        )
    except Exception as e:
        return f"❌ Ошибка удаления: {e}"


def _run_job_sync(job_id: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_job(job_id))
    finally:
        loop.close()


async def _run_job(job_id: str):
    job = jobs[job_id]

    try:
        # Этап 1: Crawling
        job.status = JobStatus.CRAWLING

        crawler_cfg = CrawlConfig(
            max_pages=job.config_overrides.get(
                "max_pages", CFG["crawler"]["max_pages"]
            ),
            max_depth=CFG["crawler"]["max_depth"],
            delay=CFG["crawler"]["delay_between_requests"],
            timeout=CFG["crawler"]["timeout"],
            concurrent=CFG["crawler"]["concurrent_requests"],
        )

        def on_progress(pages_scraped, current_url):
            job.pages_scraped = pages_scraped

        crawler = SiteCrawler(
            job.site_url, crawler_cfg,
            progress_callback=on_progress
        )
        active_crawlers[job_id] = crawler

        pages = await crawler.crawl()
        job.pages_found = len(crawler.visited)
        job.pages_scraped = len(pages)
        job.errors = crawler.errors[:50]

        del active_crawlers[job_id]

        if job.status == JobStatus.CANCELLED:
            return

        if not pages:
            job.status = JobStatus.FAILED
            job.errors.append("Не удалось извлечь ни одной страницы")
            return

        # Этап 2: Chunking
        job.status = JobStatus.PROCESSING

        chunker = DocumentChunker(
            chunk_size=CFG["chunking"]["chunk_size"],
            overlap=CFG["chunking"]["chunk_overlap"],
            min_size=CFG["chunking"]["min_chunk_size"],
        )

        chunks = chunker.chunk_all_pages(pages, job.site_name)
        job.chunks_created = len(chunks)

        if not chunks:
            job.status = JobStatus.FAILED
            job.errors.append("Не удалось создать чанки")
            return

        # Этап 3: Ingestion
        job.status = JobStatus.INGESTING

        collection = job.config_overrides.get(
            "collection", "company_docs"
        )

        try:
            await rag_client.delete_by_source(
                job.site_name, collection
            )
        except Exception:
            pass

        result = await rag_client.ingest_chunks(chunks, collection)
        job.chunks_ingested = result.get("ingested", len(chunks))

        # Готово
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow().isoformat()

    except Exception as e:
        job.status = JobStatus.FAILED
        job.errors.append(f"Fatal: {str(e)}")
        job.completed_at = datetime.utcnow().isoformat()


if __name__ == "__main__":
    from admin_api import start_admin_api

    admin_thread = threading.Thread(
        target=start_admin_api, daemon=True
    )
    admin_thread.start()

    print(f"🕷️ Docs Scraper MCP на порту {CFG['server']['mcp_port']}")
    mcp.run(transport="sse")

admin_api.py

Python

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import uvicorn
import yaml

with open("config.yaml") as f:
    CFG = yaml.safe_load(f)

app = FastAPI(title="Docs Scraper Admin", docs_url="/docs")


async def verify_admin(x_admin_secret: str = Header(...)):
    if x_admin_secret != CFG["server"]["admin_secret"]:
        raise HTTPException(403, "Invalid secret")
    return True


class ScrapeRequest(BaseModel):
    site_url: str
    site_name: str
    max_pages: int = 200
    collection: str = "company_docs"
    include_patterns: list[str] = []
    exclude_patterns: list[str] = []


def _get_jobs():
    from server import jobs
    return jobs


@app.post("/api/scrape")
async def api_start_scrape(req: ScrapeRequest,
                           auth=Depends(verify_admin)):
    from server import scrape_documentation_site
    result = scrape_documentation_site(
        req.site_url, req.site_name,
        req.max_pages, req.collection
    )
    job_id = result.split("Задача создана: ")[1].split("\n")[0]
    return {"status": "ok", "job_id": job_id, "message": result}


@app.get("/api/jobs")
async def api_list_jobs(auth=Depends(verify_admin)):
    jobs = _get_jobs()
    return {
        "jobs": [
            {
                "job_id": j.job_id,
                "site_url": j.site_url,
                "site_name": j.site_name,
                "status": j.status.value,
                "pages_scraped": j.pages_scraped,
                "chunks_created": j.chunks_created,
                "chunks_ingested": j.chunks_ingested,
                "errors_count": len(j.errors),
                "created_at": j.created_at,
                "completed_at": j.completed_at,
            }
            for j in jobs.values()
        ]
    }


@app.get("/api/jobs/{job_id}")
async def api_job_detail(job_id: str,
                         auth=Depends(verify_admin)):
    jobs = _get_jobs()
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "job_id": job.job_id,
        "site_url": job.site_url,
        "site_name": job.site_name,
        "status": job.status.value,
        "pages_found": job.pages_found,
        "pages_scraped": job.pages_scraped,
        "chunks_created": job.chunks_created,
        "chunks_ingested": job.chunks_ingested,
        "errors": job.errors,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }


@app.post("/api/jobs/{job_id}/cancel")
async def api_cancel_job(job_id: str,
                         auth=Depends(verify_admin)):
    from server import cancel_scrape_job
    result = cancel_scrape_job(job_id)
    return {"status": "ok", "message": result}


@app.delete("/api/sites/{site_name}")
async def api_remove_site(site_name: str,
                          collection: str = "company_docs",
                          auth=Depends(verify_admin)):
    from server import remove_site_from_rag
    result = remove_site_from_rag(site_name, collection)
    return {"status": "ok", "message": result}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


def start_admin_api():
    print(
        f"🔧 Admin API: "
        f"http://0.0.0.0:{CFG['server']['admin_port']}/docs"
    )
    uvicorn.run(
        app, host="0.0.0.0",
        port=CFG["server"]["admin_port"],
        log_level="warning"
    )

Результат в RAG-базе

text

┌───────────────────────────────────────────────────────────┐
│              Единая коллекция: company_docs                │
│                                                           │
│  📄 Приказ_директора.pdf       [doc_type: internal]       │
│  📄 Регламент_ИТ.docx         [doc_type: internal]       │
│                                                           │
│  🌐 FastAPI Docs — Quickstart  [doc_type: external_docs]  │
│  🌐 FastAPI Docs — Middleware  [doc_type: external_docs]  │
│  🌐 Python Docs — asyncio     [doc_type: external_docs]  │
│  ...                                                      │
└───────────────────────────────────────────────────────────┘

4. Подключение к LM Studio

JSON

{
    "mcpServers": {
        "web-scraper": {
            "url": "http://localhost:8100/sse"
        },
        "docs-scraper": {
            "url": "http://localhost:8200/sse"
        }
    }
}

5. Интеграция с чат-сервером
System prompt (шаблон)

text

Ты полезный ассистент. Текущий пользователь: {user_id}

Когда пользователь просит получить информацию с веб-сайта или указывает URL:
1. Используй инструмент fetch_web_page
2. ОБЯЗАТЕЛЬНО передай user_id="{user_id}"
3. После получения контента — обработай и структурируй ответ
4. Новости оформляй нумерованным списком с заголовками

Примеры вызовов Admin API из основного сервера

Python

# Включить пользователю веб-доступ
PUT /api/users/vasya
{"enabled": true, "requests_per_hour": 10}

# Ограничить домены
PUT /api/users/vasya
{"allowed_domains": ["ria.ru", "tass.ru"]}

# Запустить скрапинг документации
POST /api/scrape
{
    "site_url": "https://docs.example.com",
    "site_name": "Example",
    "max_pages": 200
}

# Проверить статус
GET /api/jobs/abc123

# Удалить устаревшую документацию
DELETE /api/sites/Example

6. Общий стек технологий
Компонент	Технология	Версия
MCP SDK	mcp[cli]	>= 1.0.0
Извлечение контента	trafilatura	>= 1.12.0
Парсинг HTML	beautifulsoup4	>= 4.12.0
REST API	fastapi	>= 0.115.0
ASGI сервер	uvicorn	>= 0.34.0
HTTP клиент	httpx	>= 0.27.0
Конфигурация	pyyaml	>= 6.0
БД	SQLite (встроенная)	—
LLM модель	Qwen 2.5 14B+	рекомендация
7. Порты и сервисы (сводка)
Порт	Сервис	Назначение
1234	LM Studio	API модели
8100	Web Scraper MCP	SSE для LM Studio
8101	Web Scraper Admin	REST API управления
8200	Docs Scraper MCP	SSE для LM Studio
8201	Docs Scraper Admin	REST API управления
8. Порядок развёртывания

    Установить зависимости: pip install -r requirements.txt
    Настроить config.yaml (секреты, адреса, лимиты)
    Запустить Web Scraper: python mcp-web-scraper/server.py
    Запустить Docs Scraper: python mcp-docs-scraper/server.py
    Подключить оба MCP-сервера в LM Studio
    Интегрировать Admin API в основной чат-сервер
    Добавить system prompt с user_id
    Зарегистрировать пользователей через Admin API