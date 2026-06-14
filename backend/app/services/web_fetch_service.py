import logging
import re
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.web_fetch_adapter import WebFetchAdapter
from app.repositories.user_repository import UserRepository
from app.repositories.web_fetch_repository import WebFetchRepository
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+(?:\.[^\s<>\"']+)+", re.IGNORECASE)


class WebFetchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.web_repo = WebFetchRepository(session)
        self.settings = SettingsService(session)

    def extract_urls(self, text: str) -> list[str]:
        return URL_PATTERN.findall(text)

    async def check_user_permission(self, user_id: str) -> bool:
        user = await self.user_repo.get(UUID(user_id))
        if not user:
            return False
        permissions = user.permissions or []
        return "web" in permissions

    async def process_urls(self, user_id: str, message: str) -> str | None:
        urls = self.extract_urls(message)
        if not urls:
            return None

        if not await self.settings.get_bool("web_fetch_enabled", False):
            logger.debug("Web fetch globally disabled")
            return None

        if not await self.check_user_permission(user_id):
            logger.debug("User %s does not have web permission", user_id)
            return None

        perms = await self.web_repo.get_by_user_id(user_id)
        if not perms or not perms.enabled:
            logger.debug("Web fetch disabled for user %s", user_id)
            return None

        blocked_domains_raw = await self.settings.get("web_fetch_blocked_domains", "")
        blocked_global = [d.strip().lower() for d in blocked_domains_raw.split(",") if d.strip()]

        max_chars = perms.max_chars
        global_max = await self.settings.get_int("web_fetch_max_size", 10000)
        if global_max > 0:
            max_chars = min(max_chars, global_max)

        timeout = await self.settings.get_int("web_fetch_timeout", 15)

        adapter = WebFetchAdapter(timeout=timeout, max_chars=max_chars)

        results = []
        for url in urls:
            domain = urlparse(url).hostname or ""
            if domain in blocked_global:
                results.append(f"[URL blocked by global policy: {domain}]")
                continue
            if not self.web_repo.is_domain_allowed(domain, perms):
                results.append(f"[URL blocked by user policy: {domain}]")
                continue
            result = await adapter.fetch(url, max_chars=max_chars, timeout=timeout)
            if result["success"]:
                results.append(f"=== Content from: {url} ===\n{result['content']}")
            else:
                logger.warning("Failed to fetch %s: %s", url, result.get("error"))
                results.append(f"[Failed to fetch: {url} — {result.get('error')}]")

        if not results:
            return None

        context = "\n\n".join(results)
        header = (
            "\n\n=== WEB FETCH: Содержимое веб-страниц ===\n"
            "Пользователь отправил URL(ы). Ниже приведено содержимое этих страниц. "
            "Используй этот контент для ответа пользователю, если это уместно.\n\n"
        )
        return header + context
