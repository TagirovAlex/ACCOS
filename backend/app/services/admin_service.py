import logging
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.models.user import User
from app.db.models.user_group import UserGroup
from app.db.models.chat import ChatSession, ChatMessage
from app.db.models.generation import GenerationRecord
from app.db.models.image_asset import ImageAsset
from app.db.models.admin_settings import AdminSettings
from app.repositories.user_repository import UserRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.settings_repository import SettingsRepository
from app.core.security import get_password_hash as hash_password

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
            allowed = {"balance", "permissions", "is_active", "is_admin", "full_name"}
            update_data = {k: v for k, v in data.items() if k in allowed and v is not None}
            if "password" in data and data["password"]:
                update_data["hashed_password"] = hash_password(data["password"])
            if update_data:
                await self.user_repo.update(UUID(user_id), **update_data)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_user(self, data: dict) -> dict:
        try:
            existing = await self.user_repo.get_by_username(data.get("username", ""))
            if existing:
                return {"success": False, "error": "Username already exists"}
            hashed_pw = hash_password(data.get("password", "changeme")) if data.get("password") else None
            user = await self.user_repo.create(
                username=data.get("username", ""),
                email=data.get("email", ""),
                hashed_password=hashed_pw,
                balance=data.get("balance", 100.0),
                permissions=data.get("permissions", "chat"),
                is_admin=data.get("is_admin", False),
                is_active=data.get("is_active", True),
            )
            return {"success": True, "user": {"id": str(user.id), "username": user.username}}
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

    async def list_users(self, skip: int = 0, limit: int = 100) -> dict:
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        )
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

    async def list_groups(self, skip: int = 0, limit: int = 100) -> dict:
        result = await self.session.execute(
            select(UserGroup).order_by(UserGroup.name).offset(skip).limit(limit)
        )
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

    async def get_chat_detail(self, chat_id: str) -> dict | None:
        try:
            result = await self.session.execute(
                select(ChatSession)
                .options(joinedload(ChatSession.user), selectinload(ChatSession.messages))
                .where(ChatSession.id == UUID(chat_id))
            )
            chat = result.unique().scalar_one_or_none()
            if not chat:
                return None
            return {
                "success": True,
                "id": str(chat.id), "user_id": str(chat.user_id),
                "username": chat.user.username if chat.user else "unknown",
                "title": chat.title, "system_prompt": chat.system_prompt,
                "is_active": chat.is_active,
                "created_at": chat.created_at, "updated_at": chat.updated_at,
                "messages": [
                    {
                        "id": str(m.id), "role": m.role, "content": m.content,
                        "tokens_input": m.tokens_input, "tokens_output": m.tokens_output,
                        "cost": m.cost, "created_at": m.created_at,
                    }
                    for m in chat.messages
                ],
            }
        except Exception:
            return None

    async def list_all_chats(self, skip: int = 0, limit: int = 100) -> dict:
        result = await self.session.execute(
            select(ChatSession)
            .options(joinedload(ChatSession.user))
            .order_by(ChatSession.updated_at.desc())
            .offset(skip).limit(limit)
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

    async def get_generation_detail(self, gen_id: str) -> dict | None:
        try:
            result = await self.session.execute(
                select(GenerationRecord)
                .options(joinedload(GenerationRecord.user), selectinload(GenerationRecord.assets))
                .where(GenerationRecord.id == UUID(gen_id))
            )
            record = result.unique().scalar_one_or_none()
            if not record:
                return None
            return {
                "success": True,
                "id": str(record.id), "user_id": str(record.user_id),
                "username": record.user.username if record.user else "unknown",
                "workflow_type": record.workflow_type, "prompt": record.prompt,
                "width": record.width, "height": record.height,
                "duration": record.duration,
                "status": record.status, "cost": record.cost,
                "error_message": record.error_message,
                "created_at": record.created_at, "updated_at": record.updated_at,
                "images": [
                    {
                        "id": str(a.id), "filename": a.filename,
                        "file_path": a.file_path, "file_size": a.file_size,
                    }
                    for a in (record.assets or [])
                ],
            }
        except Exception:
            return None

    async def list_all_generations(self, skip: int = 0, limit: int = 100) -> dict:
        result = await self.session.execute(
            select(GenerationRecord)
            .options(joinedload(GenerationRecord.user))
            .order_by(GenerationRecord.created_at.desc())
            .offset(skip).limit(limit)
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

    async def get_asset_detail(self, asset_id: str) -> dict | None:
        try:
            result = await self.session.execute(
                select(ImageAsset).where(ImageAsset.id == UUID(asset_id))
            )
            asset = result.scalar_one_or_none()
            if not asset:
                return None
            return {
                "success": True,
                "id": str(asset.id), "user_id": str(asset.user_id),
                "generation_id": str(asset.generation_id) if asset.generation_id else None,
                "filename": asset.filename, "file_path": asset.file_path,
                "file_size": asset.file_size, "width": asset.width, "height": asset.height,
                "created_at": asset.created_at,
            }
        except Exception:
            return None

    async def list_all_assets(self, skip: int = 0, limit: int = 100) -> dict:
        result = await self.session.execute(
            select(ImageAsset)
            .order_by(ImageAsset.created_at.desc())
            .offset(skip).limit(limit)
        )
        assets = result.scalars().all()
        return {
            "success": True,
            "assets": [
                {
                    "id": str(a.id), "user_id": str(a.user_id),
                    "generation_id": str(a.generation_id) if a.generation_id else None,
                    "filename": a.filename, "file_path": a.file_path,
                    "file_size": a.file_size, "width": a.width, "height": a.height,
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

    async def create_setting(self, key: str, value: str, description: str | None = None) -> dict:
        try:
            existing = await self.settings_repo.get_by_key(key)
            if existing:
                return {"success": False, "error": "Setting already exists"}
            await self.settings_repo.set_value(key, value, description)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def update_setting(self, key: str, value: str, description: str | None = None) -> dict:
        await self.settings_repo.set_value(key, value, description)
        return {"success": True}

    async def delete_setting(self, key: str) -> dict:
        try:
            await self.session.execute(
                delete(AdminSettings).where(AdminSettings.key == key)
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_dashboard_stats(self) -> dict:
        from sqlalchemy import func
        users_count = (await self.session.execute(select(func.count()).select_from(User))).scalar()
        groups_count = (await self.session.execute(select(func.count()).select_from(UserGroup))).scalar()
        chats_count = (await self.session.execute(select(func.count()).select_from(ChatSession))).scalar()
        gens_count = (await self.session.execute(select(func.count()).select_from(GenerationRecord))).scalar()
        assets_count = (await self.session.execute(select(func.count()).select_from(ImageAsset))).scalar()
        return {
            "success": True,
            "users": users_count or 0,
            "groups": groups_count or 0,
            "chats": chats_count or 0,
            "generations": gens_count or 0,
            "assets": assets_count or 0,
        }

    async def _force_delete(self, model_class, record_id: str) -> dict:
        try:
            await self.session.execute(
                delete(model_class).where(model_class.id == UUID(record_id))
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
