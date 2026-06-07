from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.admin_settings import AdminSettings
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[AdminSettings]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AdminSettings)

    async def get_by_key(self, key: str) -> AdminSettings | None:
        result = await self.session.execute(
            select(AdminSettings).where(AdminSettings.key == key)
        )
        return result.scalar_one_or_none()

    async def set_value(self, key: str, value: str, description: str | None = None) -> AdminSettings:
        existing = await self.get_by_key(key)
        if existing:
            existing.value = value
            if description:
                existing.description = description
            await self.session.flush()
            return existing
        setting = AdminSettings(key=key, value=value, description=description)
        self.session.add(setting)
        await self.session.flush()
        return setting

    async def get_all_as_dict(self) -> dict[str, str]:
        result = await self.session.execute(select(AdminSettings))
        settings = result.scalars().all()
        return {s.key: s.value for s in settings}
