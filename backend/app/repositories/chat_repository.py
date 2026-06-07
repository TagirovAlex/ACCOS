from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat import ChatSession, ChatMessage
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ChatSession)

    async def get_user_chats(self, user_id: UUID, skip: int = 0, limit: int = 50) -> list[ChatSession]:
        result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.is_active == True)
            .order_by(desc(ChatSession.updated_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_messages(self, session_id: UUID) -> list[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())

    async def add_message(self, session_id: UUID, role: str, content: str, tokens_input: int | None = None, tokens_output: int | None = None, cost: float | None = None) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost=cost,
        )
        self.session.add(message)
        await self.session.flush()
        return message
