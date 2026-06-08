import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.lmstudio_adapter import LMStudioAdapter
from app.repositories.chat_repository import ChatRepository
from app.repositories.user_repository import UserRepository
from app.services.economy_service import EconomyService
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
        return {
            "success": True,
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

        session = await self.chat_repo.get(sid)
        if not session:
            return {"success": False, "error": "Chat session not found"}
        if str(session.user_id) != user_id:
            return {"success": False, "error": "Access denied"}

        history = await self.chat_repo.get_messages(sid)
        messages = []
        if session.system_prompt:
            messages.append({"role": "system", "content": session.system_prompt})
        for m in history:
            messages.append({"role": m.role, "content": m.content})
        messages.append({"role": "user", "content": message})

        settings_svc = SettingsService(self.session)
        api_key = await settings_svc.get("lmstudio_api_key")
        model = await settings_svc.get("lmstudio_model")
        base_url = await settings_svc.get("lmstudio_base_url")
        llm = LMStudioAdapter(api_key=api_key, model=model, base_url=base_url)

        llm_result = await llm.chat_completion(messages)
        if not llm_result["success"]:
            return {"success": False, "error": llm_result.get("error", "LLM call failed")}

        tokens_input = llm_result.get("tokens_input", 0)
        tokens_output = llm_result.get("tokens_output", 0)
        cost = await self.economy.calculate_cost("llm", tokens_input=tokens_input, tokens_output=tokens_output)

        deduct = await self.economy.deduct_balance(user_id, cost)
        if not deduct["success"]:
            return {"success": False, "error": deduct.get("error", "Insufficient balance")}

        content = llm_result["content"]
        await self.chat_repo.add_message(sid, "user", message, tokens_input=tokens_input)
        await self.chat_repo.add_message(sid, "assistant", content, tokens_input=tokens_input, tokens_output=tokens_output, cost=cost)

        return {
            "success": True,
            "message": content,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "cost": cost,
        }
