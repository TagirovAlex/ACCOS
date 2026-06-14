import json
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.web_fetch_permissions import WebFetchPermissions


class WebFetchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: str) -> WebFetchPermissions | None:
        result = await self.session.execute(
            select(WebFetchPermissions).where(WebFetchPermissions.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[WebFetchPermissions]:
        result = await self.session.execute(
            select(WebFetchPermissions).order_by(WebFetchPermissions.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, user_id: str, **kwargs) -> WebFetchPermissions:
        instance = WebFetchPermissions(user_id=user_id, **kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, user_id: str, **kwargs) -> WebFetchPermissions | None:
        instance = await self.get_by_user_id(user_id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.flush()
        return instance

    async def upsert(self, user_id: str, **kwargs) -> WebFetchPermissions:
        existing = await self.get_by_user_id(user_id)
        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self.session.flush()
            return existing
        return await self.create(user_id, **kwargs)

    def parse_domains(self, raw: str | None) -> list[str]:
        if not raw:
            return []
        return [d.strip().lower() for d in raw.split(",") if d.strip()]

    def is_domain_allowed(self, domain: str, permissions: WebFetchPermissions) -> bool:
        domain = domain.lower()
        allowed = self.parse_domains(permissions.allowed_domains)
        blocked = self.parse_domains(permissions.blocked_domains)
        if blocked and any(domain == d or domain.endswith("." + d) for d in blocked):
            return False
        if allowed:
            return any(domain == d or domain.endswith("." + d) for d in allowed)
        return True

    async def increment_usage(self, user_id: str, count: int = 1) -> None:
        from datetime import datetime, timezone
        perms = await self.get_by_user_id(user_id)
        if perms:
            perms.usage_count = (perms.usage_count or 0) + count
            perms.last_usage_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.session.flush()
