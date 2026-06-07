from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user_group import UserGroup
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository[UserGroup]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserGroup)

    async def get_by_name(self, name: str) -> UserGroup | None:
        from sqlalchemy import select
        result = await self.session.execute(
            select(UserGroup).where(UserGroup.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_ad_group_dn(self, ad_group_dn: str) -> UserGroup | None:
        from sqlalchemy import select
        result = await self.session.execute(
            select(UserGroup).where(UserGroup.ad_group_dn == ad_group_dn)
        )
        return result.scalar_one_or_none()
