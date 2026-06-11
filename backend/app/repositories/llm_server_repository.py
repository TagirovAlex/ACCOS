from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.llm_server import LlmServer
from typing import List


class LlmServerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, server_id: str) -> LlmServer | None:
        result = await self.session.execute(
            select(LlmServer).where(LlmServer.id == server_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[LlmServer]:
        result = await self.session.execute(
            select(LlmServer).order_by(LlmServer.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_active(self) -> List[LlmServer]:
        result = await self.session.execute(
            select(LlmServer).where(LlmServer.is_active == True).order_by(LlmServer.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> LlmServer:
        instance = LlmServer(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, server_id: str, **kwargs) -> LlmServer | None:
        instance = await self.get(server_id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.flush()
        return instance

    async def delete(self, server_id: str) -> bool:
        instance = await self.get(server_id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False
