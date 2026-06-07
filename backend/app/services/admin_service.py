import logging
from uuid import UUID
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.user import User
from app.db.models.user_group import UserGroup
from app.db.models.chat import ChatSession, ChatMessage
from app.db.models.generation import GenerationRecord
from app.db.models.image_asset import ImageAsset
from app.db.models.admin_settings import AdminSettings
from app.repositories.user_repository import UserRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.group_repo = GroupRepository(session)
        self.settings_repo = SettingsRepository(session)

    async def get_user(self, user_id: str) -> dict | None:
        try:
            user = await self.user_repo.get(UUID(user_id))
            if not user:
                return None
            return {
                "id": str(user.id), "username": user.username, "email": user.email,
                "full_name": user.full_name, "balance": user.balance,
                "permissions": user.permissions, "is_active": user.is_active,
                "is_admin": user.is_admin, "created_at": user.created_at,
            }
        except Exception:
            return None

    async def update_user(self, user_id: str, data: dict) -> dict:
        try:
            user = await self.user_repo.get(UUID(user_id))
            if not user:
                return {"success": False, "error": "User not found"}
            allowed = {"balance", "permissions", "is_active", "full_name"}
            update_data = {k: v for k, v in data.items() if k in allowed and v is not None}
            if update_data:
                await self.user_repo.update(UUID(user_id), **update_data)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_user(self, user_id: str) -> dict:
        try:
            await self.user_repo.delete(UUID(user_id), hard=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_group(self, group_id: str) -> dict:
        try:
            await self.group_repo.delete(UUID(group_id), hard=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_users(self) -> dict:
        result = await self.session.execute(select(User).order_by(User.created_at.desc()))
        users = result.scalars().all()
        return {
            "success": True,
            "users": [
                {
                    "id": str(u.id), "username": u.username, "email": u.email,
                    "full_name": u.full_name, "balance": u.balance,
                    "permissions": u.permissions, "is_active": u.is_active,
                    "is_admin": u.is_admin, "created_at": u.created_at,
                }
                for u in users
            ],
        }

    async def adjust_balance(self, admin_id: str, target_user_id: str, amount: float) -> dict:
        try:
            user = await self.user_repo.get(UUID(target_user_id))
            if not user:
                return {"success": False, "error": "User not found"}
            await self.user_repo.update_balance(UUID(target_user_id), amount)
            logger.info(f"Admin {admin_id} adjusted balance of {target_user_id} by {amount}")
            return {"success": True, "new_balance": user.balance + amount}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_groups(self) -> dict:
        result = await self.session.execute(select(UserGroup).order_by(UserGroup.name))
        groups = result.scalars().all()
        return {
            "success": True,
            "groups": [
                {
                    "id": str(g.id), "name": g.name, "ad_group_dn": g.ad_group_dn,
                    "permissions": g.permissions, "start_balance": g.start_balance,
                    "description": g.description, "is_active": g.is_active,
                    "created_at": g.created_at,
                }
                for g in groups
            ],
        }

    async def create_group(self, name: str, ad_group_dn: str, permissions: str = "chat", start_balance: float = 100.0, description: str | None = None) -> dict:
        existing = await self.group_repo.get_by_name(name)
        if existing:
            return {"success": False, "error": "Group already exists"}
        group = await self.group_repo.create(
            name=name, ad_group_dn=ad_group_dn,
            permissions=permissions, start_balance=start_balance,
            description=description,
        )
        return {"success": True, "group": {"id": str(group.id), "name": group.name}}

    async def update_group(self, group_id: str, **kwargs) -> dict:
        group = await self.group_repo.get(UUID(group_id))
        if not group:
            return {"success": False, "error": "Group not found"}
        clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if clean_kwargs:
            await self.group_repo.update(UUID(group_id), **clean_kwargs)
        return {"success": True}

    async def list_all_chats(self) -> dict:
        result = await self.session.execute(
            select(ChatSession)
            .options(joinedload(ChatSession.user))
            .order_by(ChatSession.updated_at.desc())
        )
        chats = result.unique().scalars().all()
        return {
            "success": True,
            "chats": [
                {
                    "id": str(c.id), "user_id": str(c.user_id),
                    "username": c.user.username if c.user else "unknown",
                    "title": c.title, "is_active": c.is_active,
                    "created_at": c.created_at, "updated_at": c.updated_at,
                }
                for c in chats
            ],
        }

    async def force_delete_chat(self, chat_id: str) -> dict:
        return await self._force_delete(ChatSession, chat_id)

    async def list_all_generations(self) -> dict:
        result = await self.session.execute(
            select(GenerationRecord)
            .options(joinedload(GenerationRecord.user))
            .order_by(GenerationRecord.created_at.desc())
        )
        records = result.unique().scalars().all()
        return {
            "success": True,
            "generations": [
                {
                    "id": str(r.id), "user_id": str(r.user_id),
                    "username": r.user.username if r.user else "unknown",
                    "workflow_type": r.workflow_type, "prompt": r.prompt,
                    "status": r.status, "cost": r.cost, "created_at": r.created_at,
                }
                for r in records
            ],
        }

    async def force_delete_generation(self, gen_id: str) -> dict:
        return await self._force_delete(GenerationRecord, gen_id)

    async def list_all_assets(self) -> dict:
        result = await self.session.execute(
            select(ImageAsset)
            .order_by(ImageAsset.created_at.desc())
        )
        assets = result.scalars().all()
        return {
            "success": True,
            "assets": [
                {
                    "id": str(a.id), "user_id": str(a.user_id),
                    "generation_id": str(a.generation_id) if a.generation_id else None,
                    "filename": a.filename, "file_size": a.file_size,
                    "created_at": a.created_at,
                }
                for a in assets
            ],
        }

    async def get_settings(self) -> dict:
        result = await self.session.execute(select(AdminSettings))
        settings = result.scalars().all()
        return {
            "success": True,
            "settings": [
                {"key": s.key, "value": s.value, "description": s.description}
                for s in settings
            ],
        }

    async def update_setting(self, key: str, value: str, description: str | None = None) -> dict:
        await self.settings_repo.set_value(key, value, description)
        return {"success": True}

    async def _force_delete(self, model_class, record_id: str) -> dict:
        from sqlalchemy import delete
        try:
            await self.session.execute(
                delete(model_class).where(model_class.id == UUID(record_id))
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
