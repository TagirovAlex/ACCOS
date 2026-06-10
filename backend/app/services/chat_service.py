import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat import ChatMessage
from app.db.models.chat_queue import ChatQueue
from app.db.session import async_session_factory
from app.db.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.user_repository import UserRepository
from app.services.economy_service import EconomyService
from app.services.chat_worker import ensure_chat_worker
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chat_repo = ChatRepository(session)
        self.user_repo = UserRepository(session)
        self.economy = EconomyService(session)

    async def create_chat(self, user_id: str, title: str = "New Chat", system_prompt: str | None = None) -> dict:
        uid = UUID(user_id)
        chat = await self.chat_repo.create(
            user_id=uid,
            title=title,
            system_prompt=system_prompt,
        )
        return {
            "success": True,
            "chat": {
                "id": str(chat.id),
                "title": chat.title,
                "system_prompt": chat.system_prompt,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
            },
        }

    async def list_chats(self, user_id: str) -> dict:
        uid = UUID(user_id)
        chats = await self.chat_repo.get_user_chats(uid)
        return {
            "success": True,
            "chats": [
                {
                    "id": str(c.id),
                    "title": c.title,
                    "system_prompt": c.system_prompt,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at,
                }
                for c in chats
            ],
        }

    async def update_chat(self, user_id: str, session_id: str, title: str | None = None, system_prompt: str | None = None) -> dict:
        sid = UUID(session_id)
        session = await self.chat_repo.get(sid)
        if not session:
            return {"success": False, "error": "Chat session not found"}
        if str(session.user_id) != user_id:
            return {"success": False, "error": "Access denied"}
        if title is not None:
            session.title = title
        if system_prompt is not None:
            session.system_prompt = system_prompt
        await self.session.flush()
        return {
            "success": True,
            "chat": {
                "id": str(session.id),
                "title": session.title,
                "system_prompt": session.system_prompt,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
            },
        }

    async def get_history(self, session_id: str, user_id: str | None = None) -> dict:
        sid = UUID(session_id)
        session = await self.chat_repo.get(sid)
        if not session:
            return {"success": False, "error": "Chat session not found"}
        if user_id and str(session.user_id) != user_id:
            return {"success": False, "error": "Access denied"}
        messages = await self.chat_repo.get_messages(sid)
        has_pending = False
        if messages and messages[-1].role == "user":
            queue_count = await self.session.scalar(
                select(func.count(ChatQueue.id)).where(
                    ChatQueue.session_id == sid,
                    ChatQueue.status.in_(["queued", "processing"]),
                )
            )
            has_pending = (queue_count or 0) > 0
        return {
            "success": True,
            "has_pending": has_pending,
            "session": {
                "id": str(session.id),
                "title": session.title,
                "system_prompt": session.system_prompt,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
            },
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "tokens_input": m.tokens_input,
                    "tokens_output": m.tokens_output,
                    "cost": m.cost,
                    "created_at": m.created_at,
                }
                for m in messages
            ],
        }

    async def delete_chat(self, user_id: str, session_id: str) -> dict:
        sid = UUID(session_id)
        chat = await self.chat_repo.get(sid)
        if not chat:
            return {"success": False, "error": "Chat not found"}
        if str(chat.user_id) != user_id:
            return {"success": False, "error": "Access denied"}
        ok = await self.chat_repo.delete(sid)
        return {"success": ok, "error": None if ok else "Failed to delete chat"}

    async def send_message(self, user_id: str, session_id: str, message: str) -> dict:
        uid = UUID(user_id)
        sid = UUID(session_id)

        chat_session = await self.chat_repo.get(sid)
        if not chat_session:
            return {"success": False, "error": "Chat session not found"}
        if str(chat_session.user_id) != user_id:
            return {"success": False, "error": "Access denied"}

        async with async_session_factory() as persist_session:
            persist_session.add(ChatMessage(session_id=sid, role="user", content=message))
            await persist_session.commit()

        history = await self.chat_repo.get_messages(sid)
        settings_svc = SettingsService(self.session)
        ctx_count = int(await settings_svc.get("chat_context_messages") or "50")
        messages: list[dict] = []
        if chat_session.system_prompt:
            messages.append({"role": "system", "content": chat_session.system_prompt})
        for m in history[-ctx_count:]:
            messages.append({"role": m.role, "content": m.content})
        messages.append({"role": "user", "content": message})

        async with async_session_factory() as db:
            db.add(ChatQueue(
                session_id=sid,
                user_id=uid,
                prompt_messages=json.dumps(messages),
                status="queued",
            ))
            await db.commit()

        asyncio.create_task(ensure_chat_worker())

        return {"success": True, "message": "Queued"}

    async def cancel_generation(self, user_id: str, session_id: str) -> dict:
        sid = UUID(session_id)
        uid = UUID(user_id)

        chat_session = await self.chat_repo.get(sid)
        if not chat_session:
            return {"success": False, "error": "Chat session not found"}
        if str(chat_session.user_id) != user_id:
            return {"success": False, "error": "Access denied"}

        result = await self.session.execute(
            sa.update(ChatQueue)
            .where(
                ChatQueue.session_id == sid,
                ChatQueue.user_id == uid,
                ChatQueue.status.in_(["queued", "processing"]),
            )
            .values(status="cancelling", updated_at=datetime.now(timezone.utc))
        )
        if result.rowcount == 0:
            return {"success": False, "error": "No active generation to cancel"}

        return {"success": True}
