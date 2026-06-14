import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import base64
from pathlib import Path

from app.db.models.chat import ChatMessage
from app.db.models.chat_queue import ChatQueue
from app.db.session import async_session_factory
from app.db.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.user_repository import UserRepository
from app.services.economy_service import EconomyService
from app.services.chat_worker import ensure_chat_worker
from app.services.settings_service import SettingsService
from app.services.file_parser_service import get_file_type, extract_text

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

    async def send_message(self, user_id: str, session_id: str, message: str, file: str | None = None) -> dict:
        uid = UUID(user_id)
        sid = UUID(session_id)

        chat_session = await self.chat_repo.get(sid)
        if not chat_session:
            return {"success": False, "error": "Chat session not found"}
        if str(chat_session.user_id) != user_id:
            return {"success": False, "error": "Access denied"}

        user_content: str | list[dict] = message
        file_injected = False

        if file:
            file_path = Path(file)
            if file_path.exists():
                file_type = get_file_type(file)
                if file_type == "image":
                    try:
                        from app.adapters.lmstudio_adapter import LMStudioAdapter
                        llm = LMStudioAdapter()
                        has_vision = await llm.check_vision_capability()
                    except Exception:
                        has_vision = False
                    if has_vision:
                        with open(file, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        ext = file_path.suffix.lstrip(".") or "png"
                        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/png")
                        user_content = [
                            {"type": "text", "text": message or "Опиши это изображение"},
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        ]
                        file_injected = True
                    else:
                        text = extract_text(file)
                        if text:
                            file_injected = True
                else:
                    text = extract_text(file)
                    if text:
                        file_injected = True
                if file_injected and isinstance(user_content, str) and user_content == message:
                    fname = file_path.name
                    user_content = f"[File: {fname}]\n{text}\n[/File]\n\n{message}"

        async with async_session_factory() as persist_session:
            content_str = json.dumps(user_content) if isinstance(user_content, list) else user_content
            persist_session.add(ChatMessage(session_id=sid, role="user", content=content_str))
            await persist_session.commit()

        history = await self.chat_repo.get_messages(sid)
        settings_svc = SettingsService(self.session)
        ctx_count = int(await settings_svc.get("chat_context_messages") or "50")

        system_content = chat_session.system_prompt or ""
        try:
            from app.services.knowledge_service import KnowledgeService
            user_obj = await self.user_repo.get(uid)
            ad_group_dns = getattr(user_obj, "ad_group_dns", None)
            kg = KnowledgeService(self.session)
            context = await kg.build_context(message, ad_group_dns)
            if context:
                rag_header = (
                    "\n\n=== Справочная информация из базы знаний ===\n"
                    "При использовании информации из документов копируй точный ID из квадратных скобок. Пример: если в контексте написано «[doc: abc-123] Название», используй «[doc: abc-123]». Не заменяй ID на название документа.\n\n"
                )
                system_content += rag_header + context
        except Exception as e:
            logger.warning(f"RAG context injection failed: {e}")

        try:
            from app.services.web_fetch_service import WebFetchService
            wf = WebFetchService(self.session)
            web_context = await wf.process_urls(user_id, message)
            if web_context:
                system_content += web_context
        except Exception as e:
            logger.warning(f"Web fetch injection failed: {e}")

        messages: list[dict] = []
        _wf_prompt = await settings_svc.get("web_fetch_prompt")
        if _wf_prompt:
            tool_instruction = _wf_prompt
        else:
            tool_instruction = "ВАЖНО: вы НЕ знаете содержимое сайтов. Для получения информации с любого URL ОБЯЗАТЕЛЬНО используйте fetch_web_page. НИКОГДА не выдумывайте содержимое страниц и не придумывайте URL."
        gen_instruction = (
            "\n\nВы можете генерировать документы. Для генерации верните JSON: "
            '{"_generate": {"template": "имя шаблона", "variables": {"ключ": "значение"}, "format": "pdf"}} '
            "Форматы: pdf, docx, xlsx, pptx. "
            "Также можете выполнять вычисления в блоке [COMPUTE]код[/COMPUTE] - код на Python с сохранением переменных между вызовами. "
            "Если используете информацию из интернета - указывайте источник в формате [source: url]."
        )
        tool_instruction += gen_instruction
        if system_content:
            system_content += "\n\n" + tool_instruction
            messages.append({"role": "system", "content": system_content})
        else:
            messages.append({"role": "system", "content": tool_instruction})
        for m in history[-ctx_count:]:
            try:
                mc = json.loads(m.content) if m.content.startswith("[") or m.content.startswith("{") else m.content
            except (json.JSONDecodeError, ValueError):
                mc = m.content
            messages.append({"role": m.role, "content": mc})
        messages.append({"role": "user", "content": user_content})

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
            .values(status="cancelling", updated_at=datetime.now(timezone.utc).replace(tzinfo=None))
        )
        if result.rowcount == 0:
            return {"success": False, "error": "No active generation to cancel"}

        return {"success": True}
