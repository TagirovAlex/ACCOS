# RAG — База знаний для ACCOS
## Проектная документация

### Права доступа (Permissions)

Новые permission'ы для пользователей:

| Permission | Кому | Что даёт |
|---|---|---|
| `documents` | Все пользователи департаментов | Доступ к БЗ — поиск, чтение, просмотр документов |
| `documents_manage` | Специальная группа (HR, секретариат) | Загрузка документов в любой департамент + общие |

### Структура AD (источник департаментов)

```
DC=fidelio,DC=local
 └── OU=Clients              ← корень департаментов (настройка ad_clients_ou)
      ├── OU=Бухгалтерия
      ├── OU=IT-отдел
      └── ...
```

- Департаменты = OUs внутри `OU=Clients`
- Поиск AD-групп для назначения прав — тоже только внутри `OU=Clients`
- Настройка: `ad_clients_ou` (SettingsService)

### Поддерживаемые форматы файлов

| Формат | MIME type | Обработка |
|---|---|---|
| PDF | `application/pdf` | Извлечение текста (pdfplumber) → чанки. Оригинал сохраняется для показа. |
| DOCX | `application/vnd.openxmlformats...` | Извлечение текста (python-docx) → чанки. Оригинал сохраняется. |
| TXT | `text/plain` | Текст → чанки. Оригинал сохраняется. |
| MD | `text/markdown` | Текст → чанки. Оригинал сохраняется. |
| PNG | `image/png` | **OCR** (Tesseract) → извлечённый текст → чанки. Оригинал сохраняется для показа. |
| JPG/JPEG | `image/jpeg` | **OCR** (Tesseract) → извлечённый текст → чанки. Оригинал сохраняется для показа. |

### OCR для изображений

- Изображения (PNG, JPG) не имеют встроенного текста — для индексации нужен OCR
- Используется **Tesseract** (`pytesseract`) — локально, бесплатно, без очередей
- LM Studio vision-модели не подходят для OCR: медленно, дорого (токены), нет batch-режима
- Если Tesseract не установлен на сервере — изображения загружаются, но статус `failed` с ошибкой "OCR not available"
- Docker-образ с Tesseract: `tesseractshadow/tesseract4re`

**TODO при реализации:** обновить `scripts/install_debian.sh` — добавить `tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng` в apt-пакеты

### Судьба оригиналов

**Все оригиналы сохраняются.** Ни один файл не удаляется после индексации.

| Шаг | PDF | DOCX | TXT/MD | PNG/JPG |
|---|---|---|---|---|
| После загрузки | Файл на диске | Файл на диске | Файл на диске | Файл на диске |
| Извлечение | pdfplumber → text | python-docx → text | читаем как есть | Tesseract → text |
| Чанкинг | text → chunks | text → chunks | text → chunks | extracted_text → chunks |
| Эмбеддинг | chunks → vectors | chunks → vectors | chunks → vectors | chunks → vectors |
| Показ | PDF.js (оригинал) | PDF.js (конверт. в PDF) | PDF.js (конверт. в PDF) | PDF.js (конверт. в PDF) |
| Re-index | повторное извлечение | повторное извлечение | повторное извлечение | повторный OCR |

Оригиналы хранятся в `static/knowledge/{document_id}/{filename}`.

**На сервере:** `/dev/sdb` (100G ext4) примонтирован в `/mnt/storage`, симлинк `/opt/accos/static/knowledge → /mnt/storage/knowledge`.
В fstab по UUID: `UUID=76d6d90f-0277-429c-9839-756e6faf7f7a /mnt/storage ext4 defaults 0 2`.

### Модели БД

```
User.ad_group_dns: list[str]   # JSONB — все memberOf пользователя из AD (обновляется при логине)

KnowledgeDocument
  id UUID PK
  title: str
  filename: str
  content_type: str           # pdf / docx / txt / md / png / jpeg
  status: str                 # pending → indexing → ready / failed
  ad_group_dn: str | None     # NULL = общий документ, иначе AD DN департамента
  file_path: str
  folder: str                 # путь в файловом менеджере, e.g. "Приказы", "Положения/Кадровые"
  doc_number: str | None      # номер документа (приказ №888)
  doc_date: date | None       # дата подписания/утверждения
  supersedes_doc_id: UUID | None  # FK → knowledge_documents (какой отменяет)
  superseded_by_doc_id: UUID | None # FK → knowledge_documents (чем отменён)
  is_active: bool = true
  created_by: FK → users
  created_at, updated_at, deleted_at

KnowledgeChunk
  id UUID PK
  document_id: FK → knowledge_documents CASCADE
  content: str
  embedding: vector(1536)     # pgvector
  chunk_index: int
  metadata: dict              # {page, section, doc_number, doc_date}
```

### Интерфейс: Файловый менеджер документов

Вместо формы загрузки с полями и autocomplete — **проводник** (как в админке FileManager).

**Структура:**
```
📁 Документы
 ├── 📁 Приказы
 │   ├── 📄 Приказ №222 от 10.03.2022
 │   ├── 📄 Приказ №888 от 15.01.2024  (заменяет №222)
 │   └── ...
 ├── 📁 Положения
 │   ├── 📁 Кадровые
 │   └── 📁 Финансы
 └── 📁 Стандарты
```

**Возможности:**
- Создание папок (просто `folder` — строка пути)
- Drag & drop в папку
- Клик по папке → содержимое (список/плитка)
- Поиск/фильтр по папкам

**Загрузка:**
1. Перешёл в папку «Приказы»
2. Кнопка «Загрузить» → выбор файла → файл в папке
3. `folder` = путь выбранной папки

**Замена документа:**
1. Нашёл «Приказ №222» в папке «Приказы»
2. Выделил / кликнул → кнопка «Загрузить замену»
3. Выбрал файл «Приказ №888.pdf»
4. Система: новый документ в той же папке, `supersedes_doc_id = 222.id`, старый → `is_active=false`, superseded_by_doc_id
5. В проводнике оба видны, но №222 помечен серым/перечёркнутым

### Отношения между документами (supersession)

**Проблема:** приказ №888 отменяет приказ №222. В поиске оба — LLM может опираться на устаревший.

**Решение — 2 уровня:**

**Уровень 1. Автоматика (при индексации):**
- RAGService анализирует извлечённый текст: ищет паттерны `(отменить|отменяется|признать утратившим силу|отменяет|взамен|вместо)`, рядом — номер документа (цифры, возможно с №/N/No)
- Если нашёл: `supersedes_doc_number` → ищем документ по `doc_number` в БД → ставим `supersedes_doc_id`, `superseded_by_doc_id`, `is_active=false` на старом
- Если документ найден, но ещё не загружен — загрузится позже, при его индексации свяжем

**Уровень 2. Без автоматики (не нашлось явной отмены в тексте):**
- Оба документа `is_active=true` — оба участвуют в поиске
- В метаданных чанков: номер и дата документа
- LLM получает чанки от обоих и сама разрешает коллизию (более новый документ имеет приоритет)
- Администратор может вручную связать документы через Admin Panel

### Логика показа документов

```sql
WHERE is_active = true
  AND (ad_group_dn IS NULL OR ad_group_dn = ANY(:user_ad_group_dns))
```

- `is_active = true` — отсекает документы, которые явно отменены (supersession найден)
- Если supersession не найден — `is_active = true` по умолчанию, документ участвует в поиске
- Общие документы видят все с правом `documents`
- Документы департамента — только сотрудники этого департамента (по AD-группам)

### Доступ пользователя к документам

- **Обычный пользователь** (`documents`) — НЕТ пункта меню «Документы». Доступ только через чат:
  1. При каждом запросе backend ищет релевантные чанки в pgvector
  2. Найденные чанки подмешиваются в системный промпт как контекст
  3. LLM отвечает с учётом контекста, цитируя источники
  4. Под ответом — блок «Источники» с кликабельными ссылками 📄
  5. Клик на ссылку документа → модальное окно с просмотрщиком:
     - PDF → PDF.js (без кнопки скачивания/печати)
     - DOCX/TXT/MD/PNG/JPG → конвертация в PDF на сервере, затем показ через PDF.js
     - Защита (слабая, но должна быть):
       - `contextmenu` disabled (правый клик)
       - CSS `user-select: none`, `-webkit-user-select: none`
       - `sandbox` iframe без `allow-downloads`
       - PDF.js с отключёнными кнопками download/print
       - **Важно:** защита не предотвращает скриншоты/DevTools — это осознанное допущение
- **Архитектурно заложено:** в будущем можно добавить пункт меню и отдельную страницу документов
- **Uploader** (`documents_manage`) — форма загрузки доступна в пользовательском интерфейсе (отдельная страница или модалка)

### Процесс загрузки документа

1. Uploader (право `documents_manage`) открывает файловый менеджер
2. Переходит в нужную папку (или создаёт новую)
3. Кнопка «Загрузить»:
   - Выбирает файл
   - Выбирает департамент (AD-группа) или «Общие документы»
   - `folder` = путь текущей папки
4. Кнопка «Загрузить замену» (на выделенном документе):
   - Выбирает файл
   - `folder` = папка заменяемого документа
   - `supersedes_doc_id = старый.id`
   - Старый → `is_active=false`, `superseded_by_doc_id = новый.id`
5. Документ сохраняется → задача в queue_worker → chunking → embedding → pgvector

### Интеграция с чатом (подмешивание контекста)

**Принцип: поиск выполняется всегда, LLM не принимает решение.**

Перед отправкой каждого запроса в LLM chat_worker:

1. Берёт последнее сообщение пользователя
2. Делает эмбеддинг запроса
3. Ищет топ-K чанков в pgvector (`<=>` cosine similarity)
4. Фильтрует по `ad_group_dn IN user.ad_group_dns` + порог `rag_min_score`
5. Если есть релевантные результаты — вставляет блок в system prompt:

```
[Контекст из базы знаний]:
[Регламент отчетности.pdf (раздел 2.1)]:
Отчет по продукту составляется ежеквартально до 5 числа...

[Инструкция.pdf (раздел 4)]:
...
```

6. Отправляет LLM (system prompt + контекст + история + вопрос)
7. LLM отвечает, используя контекст

**Если релевантных чанков нет** — контекст пустой, LLM отвечает как обычно.

**Преимущества перед Function Calling:**
- Поиск выполняется всегда — не пропустим нужный документ
- Работает с любой LLM (не требуется поддержка function calling)
- Пользователь не замечает «лишнего шага»
- Ответ всегда обогащён контекстом, если он есть

### Вызов эмбеддингов

`RAGAdapter` вызывает LM Studio через `POST /v1/embeddings`:

```json
{
  "model": "<rag_embedding_model>",
  "input": "текст чанка или поисковый запрос"
}
```

Ответ:
```json
{
  "data": [{"embedding": [0.001, -0.02, ...], "index": 0}],
  "model": "<rag_embedding_model>",
  "usage": {"total_tokens": 42}
}
```

- Для чанков: отправляется батч текстов одним запросом (LM Studio поддерживает `input: [str, str, ...]`)
- Для поискового запроса: один текст

### Векторное хранилище

PostgreSQL + pgvector. Расширение ставится на сервере БД:
```sql
CREATE EXTENSION vector;
```
Зависимость: `pgvector` (клиент для SQLAlchemy).

pgvector выбран вместо специализированных векторных БД (Qdrant, Weaviate, Milvus), так как:
- Масштаб: сотни документов, десятки тысяч чанков — pgvector справляется < 50ms
- Не нужен отдельный сервис (деплой, бэкап, мониторинг)
- ACID-транзакции с метаданными документов
- Бэкап = pg_dump одной БД

### Внешние сайты и Wiki (Scraping)

**Возможно, но вынесено в отдельный функционал.**

**Принцип:**
- Добавляется модель `KnowledgeSource` — источник (URL/sitemap, название, периодичность синхронизации)
- Каждая страница источника → `KnowledgeDocument` (с `source_id` FK)
- Scraper (`httpx + trafilatura/BeautifulSoup`) → чистый текст → чанки → эмбеддинги
- При повторной синхронизации: проверка ETag/Last-Modified → только изменившиеся страницы
- Расписание: фоновый таск (аналог auto_accrual), проверяет `next_sync_at`

**Нюансы:**
- Требуется авторизация? (внутренние wiki, Confluence)
- Разная структура сайтов → для каждого может понадобиться свой парсер
- robots.txt, rate limiting

**TODO при реализации основного RAG:** спроектировать и добавить как Phase RAG-2 после стабильного релиза file-based RAG.

### Файловая структура (новые файлы)

```
backend/app/
├── adapters/rag_adapter.py
├── api/v1/endpoints/knowledge.py
├── db/models/knowledge.py
├── repositories/knowledge_repository.py
├── services/rag_service.py
├── schemas/knowledge.py
└── modules/rag_module.py

admin/src/pages/
├── KnowledgeManager.tsx     # файловый менеджер (проводник + загрузка)
├── KnowledgeShow.tsx        # просмотр документа
└── components/
    └── KnowledgeViewer.tsx  # PDF.js модалка
```

### Настройки (SettingsService)

| Ключ | Default | Описание |
|---|---|---|
| `ad_clients_ou` | `OU=Clients,DC=...` | Корень департаментов в AD |
| `rag_enabled` | `false` | Вкл/выкл RAG |
| `rag_embedding_model` | `default` | Модель эмбеддингов (из LM Studio). Передаётся как `model` в `POST /v1/embeddings` |
| `rag_chunk_size` | `500` | Токенов на чанк |
| `rag_chunk_overlap` | `50` | Перекрытие чанков |
| `rag_top_k` | `5` | Количество результатов поиска |
| `rag_min_score` | `0.5` | Минимальный порог схожести |

### План реализации (порядок шагов)

1. **pgvector на сервере БД** — `CREATE EXTENSION vector;`
2. **alembic миграция #1** — `ad_group_dns JSONB` на User
3. **alembic миграция #2** — таблицы `knowledge_documents` + `knowledge_chunks` (с `Vector(1536)`)
4. **config.py** — 3 новых поля: `ad_clients_ou`, `rag_embedding_model`, `rag_enabled`
5. **SettingsService** — 7 новых ключей в `seed_defaults` (все из раздела «Настройки»)
6. **LDAPAdapter.list_groups** — параметр `search_base` для поиска внутри OU=Clients
7. **AuthService** — при логине сохранять `user.ad_group_dns = ldap_result.get("groups", [])`
8. **Модели SQLAlchemy** — `KnowledgeDocument`, `KnowledgeChunk` + `User.ad_group_dns`
9. **KnowledgeRepository** — CRUD для документов + векторный поиск через `<=>`
10. **RAGAdapter** — вызов `POST /v1/embeddings` с `model = rag_embedding_model`, batch для чанков
11. **RAGService** — chunking (`tiktoken` + recursive split), embedding, index, search
12. **Queue worker** — новый тип задачи `knowledge_index: pending → indexing → ready`
13. **API endpoints** — `POST /upload`, `GET /documents`, `DELETE /{id}`, `POST /{id}/reindex`, `GET /folders` (список папок), `GET /documents?folder=...` (по папке), `POST /{id}/replace` (загрузить замену)
14. **Chat worker** — подмешивание контекста RAG в system prompt перед отправкой в LLM
15. **Admin panel** — `KnowledgeList`, `KnowledgeShow` (список + просмотр)
16. **User frontend** — файловый менеджер для uploader'ов (создание папок, загрузка, замена), просмотрщик для всех
17. **Тесты** — pytest на новые модули

### Зависимости (requirements.txt)

- `pgvector` — клиент pgvector для SQLAlchemy
- `pdfplumber` — чтение PDF
- `python-docx` — чтение DOCX
- `tiktoken` — подсчёт токенов для чанков
- `weasyprint` или `pdfkit` — конвертация DOCX/TXT/MD/PNG/JPG → PDF для показа в модалке
- `pytesseract` — OCR для изображений (PNG, JPG)
- `Pillow` — уже есть (для resize/image upload)
