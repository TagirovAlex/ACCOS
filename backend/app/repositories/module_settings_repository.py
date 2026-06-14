from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.module_setting import ModuleSetting


class ModuleSettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_global(self, module_name: str, key: str) -> str | None:
        result = await self.session.execute(
            select(ModuleSetting).where(
                ModuleSetting.module_name == module_name,
                ModuleSetting.key == key,
                ModuleSetting.user_id.is_(None),
            )
        )
        s = result.scalar_one_or_none()
        return s.value if s else None

    async def get_user_setting(self, user_id: str, module_name: str, key: str) -> str | None:
        result = await self.session.execute(
            select(ModuleSetting).where(
                ModuleSetting.user_id == user_id,
                ModuleSetting.module_name == module_name,
                ModuleSetting.key == key,
            )
        )
        s = result.scalar_one_or_none()
        return s.value if s else None

    async def set_global(self, module_name: str, key: str, value: str) -> ModuleSetting:
        result = await self.session.execute(
            select(ModuleSetting).where(
                ModuleSetting.module_name == module_name,
                ModuleSetting.key == key,
                ModuleSetting.user_id.is_(None),
            )
        )
        s = result.scalar_one_or_none()
        if s:
            s.value = value
            await self.session.flush()
            return s
        setting = ModuleSetting(module_name=module_name, key=key, value=value, user_id=None)
        self.session.add(setting)
        await self.session.flush()
        return setting

    async def list_global(self, module_name: str) -> list[ModuleSetting]:
        result = await self.session.execute(
            select(ModuleSetting).where(
                ModuleSetting.module_name == module_name,
                ModuleSetting.user_id.is_(None),
            )
        )
        return list(result.scalars().all())

    async def list_user_settings(self, user_id: str) -> list[ModuleSetting]:
        result = await self.session.execute(
            select(ModuleSetting).where(ModuleSetting.user_id == user_id)
        )
        return list(result.scalars().all())

    async def delete_global(self, module_name: str, key: str) -> bool:
        result = await self.session.execute(
            select(ModuleSetting).where(
                ModuleSetting.module_name == module_name,
                ModuleSetting.key == key,
                ModuleSetting.user_id.is_(None),
            )
        )
        s = result.scalar_one_or_none()
        if s:
            await self.session.delete(s)
            await self.session.flush()
            return True
        return False
