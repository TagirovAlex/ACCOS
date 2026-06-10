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
             "Domain LDAP server address for user authentication (e.g. ldap://10.0.68.8:389)"),
            ("ldap_domain", settings.ldap_domain,
             "NetBIOS domain name (e.g. FIDELIO)"),
            ("ldap_base_dn", settings.ldap_base_dn,
             "Base DN for LDAP search (e.g. DC=FIDELIO,DC=LOCAL)"),
            ("ldap_bind_dn", "",
             "DN of the account for LDAP search (CN=...). Leave empty if ldap_bind_username is used"),
            ("ldap_bind_username", "",
             "Username for LDAP search (without domain). Used as DOMAIN\\username"),
            ("ldap_bind_password", "",
              "Password for LDAP search account"),
            ("ldap_enabled", "false",
             "Enable LDAP authentication (true/false)"),

            # -- LLM / Chat --
            ("lmstudio_base_url", settings.lmstudio_base_url,
             "LMStudio server address (OpenAI API compatible format) for chat requests"),
            ("lmstudio_model", settings.lmstudio_model,
             "Default model name (e.g. default, llama, qwen etc.)"),
            ("lmstudio_api_key", settings.lmstudio_api_key,
             "API key for LMStudio (Bearer token). Leave empty if auth not required"),
            ("chat_context_messages", "50",
             "Number of recent messages sent as LLM context. Old messages are trimmed to fit context window"),

            # -- ComfyUI / Generation --
            ("comfyui_base_url", settings.comfyui_base_url,
             "ComfyUI server address for image generation and editing"),
            ("comfyui_generate_base_url", settings.comfyui_generate_base_url,
             "URL for base generation (z_image). If empty - uses comfyui_base_url"),
            ("comfyui_edit_base_url", settings.comfyui_edit_base_url,
             "URL for editing (Qwen edit 1/2/3). If empty - uses comfyui_base_url"),
            ("comfyui_video_base_url", settings.comfyui_video_base_url,
             "URL for video (text_to_video, image_to_video). If empty - uses comfyui_base_url"),
            ("comfyui_api_key", settings.comfyui_api_key,
              "API key for ComfyUI (x-api-key header). Leave empty if auth not required"),
            ("comfyui_poll_timeout_minutes", "30",
              "Maximum generation wait time in minutes. If generation takes longer - task is marked as failed"),
            ("comfyui_poll_interval", "3",
              "ComfyUI poll interval in seconds. Lower = faster response but higher server load"),

            # -- Pricing: LLM --
            ("llm_rate_input", "1",
             "Cost (MS) per calculation unit. Result: ceil(max(tokens) / tokens_per_unit) x rate"),
            ("llm_tokens_per_unit", "1000",
             "Tokens per 1 cost unit. Result: ceil(max(tokens) / N) x rate"),
            ("llm_rate_output", "0",
             "Not used (reserved)"),

            # -- Pricing: Image Generation --
            ("image_gen_base_cost", "0",
             "Not used (reserved)"),
            ("image_gen_rate_pixel", "10",
             "Cost (MS) per calculation unit. Result: ceil((WxH) / pixels_per_unit) x rate"),
            ("image_pixels_per_unit", "1000000",
             "Pixels per 1 cost unit. Result: ceil((WxH) / N) x rate"),

            # -- Pricing: Editing --
            ("image_edit_base_cost", "0",
             "Not used (reserved)"),
            ("image_edit_rate_pixel", "10",
             "Cost (MS) per calculation unit. Result: ceil((WxH) / pixels_per_unit) x rate"),

            # -- Pricing: Video --
            ("video_gen_base_cost", "10",
             "Base video generation cost in MS"),
            ("video_gen_rate_sec", "2",
             "Cost (MS) per video second"),

            # -- Users --
            ("default_permissions", '["chat","generate"]',
             "Default permissions for new users (JSON array)"),
            ("default_start_balance", "100",
             "Starting balance for new users in MS"),

            # -- Economy --
            ("auto_accrual_amount", "10",
             "Auto balance accrual amount for active users (in MS)"),
            ("auto_accrual_interval_minutes", "60",
              "Auto balance accrual interval in minutes"),
            ("auto_accrual_time", "",
              "Accrual time (HH:MM server time). If empty - uses interval"),

            # -- Access --
            ("require_ad_group_for_login", "false",
              "Require AD group membership for login. If enabled - only users from configured AD groups can log in"),

            # -- RAG / Knowledge Base --
            ("ad_clients_ou", settings.ad_clients_ou,
             "Root OU for departments in AD (e.g. OU=Clients,DC=fidelio,DC=local). Used for AD group search when uploading documents"),
            ("rag_enabled", str(settings.rag_enabled).lower(),
             "Enable knowledge base (true/false). When enabled, document context is injected into every LLM request"),
            ("rag_embedding_model", settings.rag_embedding_model,
             "Embedding model name (from LM Studio). Passed as 'model' field in POST /v1/embeddings"),
            ("rag_chunk_size", "500",
             "Chunk size in tokens. Document text is split into fragments of this size for embedding"),
            ("rag_chunk_overlap", "50",
             "Overlap between adjacent chunks in tokens. Needed to preserve context at boundaries"),
            ("rag_top_k", "5",
             "Number of most relevant chunks returned by search"),
            ("rag_min_score", "0.5",
             "Minimum cosine similarity threshold. Chunks below threshold are not returned"),
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
