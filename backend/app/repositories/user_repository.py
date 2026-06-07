from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def update_balance(self, user_id: UUID, amount: float) -> User | None:
        user = await self.get(user_id)
        if user:
            user.balance += amount
            await self.session.flush()
        return user

    async def get_balance(self, user_id: UUID) -> float | None:
        user = await self.get(user_id)
        return user.balance if user else None
