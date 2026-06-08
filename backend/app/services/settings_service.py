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
            # ── LDAP / Домен ──
            ("ldap_server", settings.ldap_server,
             "[Домен] Адрес LDAP-сервера для авторизации пользователей (например ldap://10.0.68.8:389)"),
            ("ldap_domain", settings.ldap_domain,
             "[Домен] NetBIOS-имя домена (например FIDELIO)"),
            ("ldap_base_dn", settings.ldap_base_dn,
              "[Домен] Базовый DN для поиска в LDAP (например DC=FIDELIO,DC=LOCAL)"),
            ("ldap_bind_dn", "",
              "[Домен] DN учётной записи для поиска в LDAP (например CN=svc-accos,CN=Users,DC=fidelio,DC=local). Оставьте пустым для анонимного поиска"),
            ("ldap_bind_password", "",
              "[Домен] Пароль учётной записи для поиска в LDAP"),

            # ── LLM / Чат ──
            ("lmstudio_base_url", settings.lmstudio_base_url,
             "[LLM] Адрес сервера LMStudio (совместимого с OpenAI API форматом) для чат-запросов"),
            ("lmstudio_model", settings.lmstudio_model,
             "[LLM] Название модели по умолчанию (например default, llama, qwen и т.д.)"),
            ("lmstudio_api_key", settings.lmstudio_api_key,
             "[LLM] API-ключ для доступа к LMStudio (Bearer token). Оставьте пустым, если аутентификация не требуется"),

            # ── Генерация изображений / ComfyUI ──
            ("comfyui_base_url", settings.comfyui_base_url,
             "[Генерация] Адрес сервера ComfyUI для генерации и редактирования изображений"),
            ("comfyui_api_key", settings.comfyui_api_key,
              "[Генерация] API-ключ для доступа к ComfyUI (заголовок x-api-key). Оставьте пустым, если аутентификация не требуется"),
            ("comfyui_poll_timeout_minutes", "30",
              "[Генерация] Максимальное время ожидания генерации (в минутах). Если генерация длится дольше — задача отметится как неудачная"),
            ("comfyui_poll_interval", "3",
              "[Генерация] Интервал опроса ComfyUI (в секундах). Чем меньше — тем быстрее отклик, но выше нагрузка на сервер"),

            # ── Стоимость: LLM ──
            ("llm_rate_input", "1",
             "[Цены: LLM] Стоимость (MS) за 1 единицу расчёта. Итог: ceil(max(tokens) / tokens_per_unit) × rate"),
            ("llm_tokens_per_unit", "1000",
             "[Цены: LLM] Количество токенов на 1 единицу стоимости. Итог: ceil(max(tokens) / N) × rate"),
            ("llm_rate_output", "0",
             "[Цены: LLM] Не используется (зарезервировано)"),

            # ── Стоимость: Генерация изображений ──
            ("image_gen_base_cost", "0",
             "[Цены: Генерация] Не используется (зарезервировано)"),
            ("image_gen_rate_pixel", "10",
             "[Цены: Генерация] Стоимость (MS) за 1 единицу расчёта. Итог: ceil((W×H) / pixels_per_unit) × rate"),
            ("image_pixels_per_unit", "1000000",
             "[Цены: Генерация] Количество пикселей на 1 единицу стоимости. Итог: ceil((W×H) / N) × rate"),

            # ── Стоимость: Редактирование ──
            ("image_edit_base_cost", "0",
             "[Цены: Редактирование] Не используется (зарезервировано)"),
            ("image_edit_rate_pixel", "10",
             "[Цены: Редактирование] Стоимость (MS) за 1 единицу расчёта. Итог: ceil((W×H) / pixels_per_unit) × rate"),

            # ── Стоимость: Видео ──
            ("video_gen_base_cost", "10",
             "[Цены: Видео] Базовая стоимость генерации видео (в MS)"),
            ("video_gen_rate_sec", "2",
             "[Цены: Видео] Стоимость (MS) за секунду видео"),

            # ── Пользователи ──
            ("default_permissions", '["chat","generate"]',
             "[Пользователи] Права по умолчанию для новых пользователей (JSON-массив)"),
            ("default_start_balance", "100",
             "[Пользователи] Стартовый баланс для новых пользователей (в MS)"),

            # ── Экономика ──
            ("auto_accrual_amount", "10",
             "[Экономика] Сумма автоматического начисления баланса активным пользователям (в MS)"),
            ("auto_accrual_interval_minutes", "60",
              "[Экономика] Интервал автоматического начисления баланса (в минутах)"),

            # ── Доступ ──
            ("require_ad_group_for_login", "false",
              "[Доступ] Требовать членство в доменной группе для входа. Если включено — логин разрешён только пользователям из настроенных AD групп"),
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
