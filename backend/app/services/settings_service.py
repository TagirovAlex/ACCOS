import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.settings_repository import SettingsRepository
from app.core.config import settings

logger = logging.getLogger(__name__)


class SettingsService:
    def __init__(self, session: AsyncSession):
        self.repo = SettingsRepository(session)
        self._cache: dict[str, str] | None = None

    async def _load(self):
        if self._cache is None:
            self._cache = await self.repo.get_all_as_dict()

    async def get(self, key: str, default: str = "") -> str:
        await self._load()
        if key in self._cache:
            return self._cache[key]
        return getattr(settings, key, default)

    async def get_int(self, key: str, default: int = 0) -> int:
        val = await self.get(key, str(default))
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default

    async def get_float(self, key: str, default: float = 0.0) -> float:
        val = await self.get(key, str(default))
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    async def get_bool(self, key: str, default: bool = False) -> bool:
        val = await self.get(key, str(default))
        return val.lower() in ("true", "1", "yes")

    async def set(self, key: str, value: str, description: str | None = None) -> dict:
        await self.repo.set_value(key, value, description)
        if self._cache is not None:
            self._cache[key] = value
        return {"success": True}

    async def get_all(self) -> dict[str, str]:
        await self._load()
        return dict(self._cache or {})

    async def seed_defaults(self):
        defaults: list[tuple[str, str, str]] = [
            # -- LDAP / Domain --
            ("ldap_server", settings.ldap_server,
             "[Домен] Адрес LDAP-сервера (например ldap://10.0.68.8:389)"),
            ("ldap_domain", settings.ldap_domain,
             "[Домен] NetBIOS-имя домена (например FIDELIO)"),
            ("ldap_base_dn", settings.ldap_base_dn,
             "[Домен] Базовый DN для поиска (например DC=FIDELIO,DC=LOCAL)"),
            ("ldap_bind_dn", "",
             "[Домен] DN учётной записи для поиска (CN=...). Оставьте пустым если используется ldap_bind_username"),
            ("ldap_bind_username", "",
             "[Домен] Имя учётной записи для поиска в AD (без домена). Используется как DOMAIN\\username"),
            ("ldap_bind_password", "",
             "[Домен] Пароль учётной записи для поиска"),
            ("ldap_enabled", "false",
             "[Домен] Включить LDAP-аутентификацию (true/false)"),

            # -- LLM / Chat --
            ("lmstudio_base_url", settings.lmstudio_base_url,
             "[LLM] Адрес LMStudio-сервера (OpenAI API формат) для чата"),
            ("lmstudio_model", settings.lmstudio_model,
             "[LLM] Название модели по умолчанию (например llama, qwen)"),
            ("lmstudio_api_key", settings.lmstudio_api_key,
             "[LLM] API-ключ LMStudio (Bearer token). Оставьте пустым если аутентификация не требуется"),
            ("chat_context_messages", "50",
             "[LLM] Количество последних сообщений в контексте LLM. Более старые сообщения обрезаются"),

            # -- ComfyUI / Generation --
            ("comfyui_base_url", settings.comfyui_base_url,
             "[Генерация] Адрес ComfyUI-сервера для генерации и редактирования изображений"),
            ("comfyui_generate_base_url", settings.comfyui_generate_base_url,
             "[Генерация] URL для базовой генерации (z_image). Если пусто - используется comfyui_base_url"),
            ("comfyui_edit_base_url", settings.comfyui_edit_base_url,
             "[Генерация] URL для редактирования (Qwen edit 1/2/3). Если пусто - используется comfyui_base_url"),
            ("comfyui_video_base_url", settings.comfyui_video_base_url,
             "[Генерация] URL для видео (text_to_video, image_to_video). Если пусто - используется comfyui_base_url"),
            ("comfyui_api_key", settings.comfyui_api_key,
             "[Генерация] API-ключ ComfyUI (x-api-key header). Оставьте пустым если аутентификация не требуется"),
            ("comfyui_poll_timeout_minutes", "30",
             "[Генерация] Максимальное время ожидания генерации в минутах"),
            ("comfyui_poll_interval", "3",
             "[Генерация] Интервал опроса ComfyUI в секундах"),

            # -- Pricing: LLM --
            ("llm_rate_input", "1",
             "[Цены: LLM] Стоимость за единицу расчёта. Результат: ceil(max(tokens) / tokens_per_unit) x rate"),
            ("llm_tokens_per_unit", "1000",
             "[Цены: LLM] Токенов на 1 единицу стоимости"),
            ("llm_rate_output", "0",
             "[Цены: LLM] Не используется (резерв)"),

            # -- Pricing: Image Generation --
            ("image_gen_base_cost", "0",
             "[Цены: Генерация] Не используется (резерв)"),
            ("image_gen_rate_pixel", "10",
             "[Цены: Генерация] Стоимость за единицу расчёта. Результат: ceil((WxH) / pixels_per_unit) x rate"),
            ("image_pixels_per_unit", "1000000",
             "[Цены: Генерация] Пикселей на 1 единицу стоимости"),

            # -- Pricing: Editing --
            ("image_edit_base_cost", "0",
             "[Цены: Редактирование] Не используется (резерв)"),
            ("image_edit_rate_pixel", "10",
             "[Цены: Редактирование] Стоимость за единицу расчёта. Результат: ceil((WxH) / pixels_per_unit) x rate"),

            # -- Pricing: Video --
            ("video_gen_base_cost", "10",
             "[Цены: Видео] Базовая стоимость генерации видео в MS"),
            ("video_gen_rate_sec", "2",
             "[Цены: Видео] Стоимость за секунду видео"),

            # -- Users --
            ("default_permissions", '["chat","generate","edit","video","documents_manage","web"]',
             "[Пользователи] Права доступа по умолчанию для новых пользователей (JSON-массив)"),
            ("default_start_balance", "100",
             "[Пользователи] Стартовый баланс для новых пользователей в MS"),

            # -- Economy --
            ("auto_accrual_amount", "10",
             "[Экономика] Сумма автоначисления для активных пользователей (MS)"),
            ("auto_accrual_interval_minutes", "60",
             "[Экономика] Интервал автоначисления в минутах"),
            ("auto_accrual_time", "",
             "[Экономика] Время начисления (HH:MM по серверу). Если пусто - используется интервал"),

            # -- Access --
            ("require_ad_group_for_login", "false",
             "[Домен] Требовать группу AD для входа. Если включено - только пользователи из настроенных групп AD могут входить"),

            # -- Help / Spravka --
            ("help_content", "",
             "[Пользователи] Текст страницы справки для пользователя (HTML/Markdown)"),
            ("hidden_doc_folders", "",
             "[База знаний] Список скрытых папок с документами (через запятую)"),

            # -- RAG / Knowledge Base --
            ("ad_clients_ou", settings.ad_clients_ou,
             "[База знаний] Корневая OU для отделов в AD (например OU=Clients,DC=fidelio,DC=local)"),
            ("rag_enabled", str(settings.rag_enabled).lower(),
             "[База знаний] Включить базу знаний (true/false). При включении контекст документов добавляется в каждый запрос LLM"),
            ("rag_embedding_model", settings.rag_embedding_model,
             "[База знаний] Название модели эмбеддинга из LM Studio. Передаётся как 'model' в POST /v1/embeddings"),
            ("rag_chunk_size", "500",
             "[База знаний] Размер чанка в токенах. Текст документа разбивается на фрагменты этого размера"),
            ("rag_chunk_overlap", "50",
             "[База знаний] Перекрытие между соседними чанками в токенах"),
            ("rag_top_k", "5",
             "[База знаний] Количество наиболее релевантных чанков в результатах поиска"),
            ("rag_min_score", "0.5",
             "[База знаний] Минимальный порог косинусного сходства. Чанки ниже порога не возвращаются"),
            ("reindex_schedule_enabled", "false",
             "[База знаний] Включить автоматическое переиндексирование по расписанию"),
            ("reindex_cron", "0 3 * * *",
             "[База знаний] CRON-выражение для расписания (по умолчанию ежедневно в 3:00)"),
            ("reindex_mode", "all",
             "[База знаний] Режим переиндексации: all — все документы, new — только новые/упавшие"),

            # -- Web Fetch --
            ("web_fetch_enabled", "false",
             "[Веб-парсер] Включить авто-детект URL в чате"),
            ("web_fetch_max_size", "10000",
             "[Веб-парсер] Максимум символов на один запрос"),
            ("web_fetch_timeout", "15",
             "[Веб-парсер] Таймаут HTTP-запроса в секундах"),
            ("web_fetch_blocked_extensions",
             ".pdf,.doc,.docx,.xls,.xlsx,.zip,.rar,.tar,.gz,.exe,.dmg,.iso,.bin,.mp3,.mp4,.avi,.mov,.png,.jpg,.jpeg,.gif,.svg,.webp",
             "[Веб-парсер] Заблокированные расширения файлов (через запятую)"),
            ("web_fetch_blocked_domains", "",
             "[Веб-парсер] Глобальный чёрный список доменов (через запятую)"),

            # -- Chat file uploads --
            ("chat_file_max_size_image", "10485760",
             "[Чат] Максимальный размер изображения в байтах (10MB)"),
            ("chat_file_max_size_pdf", "52428800",
             "[Чат] Максимальный размер PDF в байтах (50MB)"),
            ("chat_file_max_size_docx", "10485760",
             "[Чат] Максимальный размер Word в байтах (10MB)"),
            ("chat_file_max_size_xlsx", "10485760",
             "[Чат] Максимальный размер Excel в байтах (10MB)"),
            ("chat_file_max_size_pptx", "31457280",
             "[Чат] Максимальный размер PowerPoint в байтах (30MB)"),
        ]
        for key, value, description in defaults:
            existing = await self.repo.get_by_key(key)
            if existing:
                existing.description = description
            else:
                await self.repo.set_value(key, value, description)
        await self.repo.session.flush()
        self._cache = None
        logger.info("Default settings seeded")
