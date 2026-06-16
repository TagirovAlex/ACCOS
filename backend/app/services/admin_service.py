import json
import logging
from pathlib import Path
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, desc, delete, text
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

STATIC_DIR = Path(__file__).parent.parent.parent.parent / "static"


def _abs_path_to_url(abs_path: str) -> str:
    if not abs_path:
        return ""
    try:
        p = Path(abs_path)
        rel = p.relative_to(STATIC_DIR)
        return f"/static/{rel.as_posix()}"
    except (ValueError, TypeError):
        pass
    norm = abs_path.replace("\\", "/")
    for marker in ("/static/", "static/"):
        idx = norm.find(marker)
        if idx != -1:
            result = norm[idx:]
            if not result.startswith("/"):
                result = "/" + result
            return result
    return abs_path


def _parse_reference_images(result_path: str | None) -> list[str]:
    if not result_path:
        return []
    try:
        paths = json.loads(result_path)
        if not isinstance(paths, list):
            return []
        return [_abs_path_to_url(p) for p in paths if isinstance(p, str)]
    except (json.JSONDecodeError, TypeError):
        return []


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
            token_stats = await self.get_token_stats(user_id)
            return {
                "id": str(user.id), "username": user.username, "email": user.email,
                "full_name": user.full_name, "balance": user.balance,
                "permissions": user.permissions,
                "group_id": str(user.group_id) if user.group_id else None,
                "auth_source": user.auth_source,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "admin_role": user.admin_role,
                "admin_group_id": str(user.admin_group_id) if user.admin_group_id else None,
                "created_at": user.created_at,
                "avatar_path": user.avatar_path, "last_login": user.last_login,
                "token_stats": token_stats,
            }
        except Exception:
            return None

    async def update_user(self, user_id: str, data: dict) -> dict:
        try:
            user = await self.user_repo.get(UUID(user_id))
            if not user:
                return {"success": False, "error": "User not found"}
            if user.auth_source == "ldap" and "password" in data and data["password"]:
                return {"success": False, "error": "Нельзя сменить пароль доменного пользователя"}
            allowed = {"balance", "permissions", "is_active", "is_admin", "admin_role", "admin_group_id", "full_name", "group_id"}
            update_data = {}
            for k, v in data.items():
                if k in allowed and v is not None:
                    if k in ("group_id", "admin_group_id"):
                        update_data[k] = UUID(v) if v else None
                    else:
                        update_data[k] = v
            if "is_admin" in update_data:
                if update_data["is_admin"] and ("admin_role" not in update_data or update_data.get("admin_role") in (None, "none")):
                    update_data["admin_role"] = "admin"
                elif not update_data["is_admin"]:
                    update_data["admin_role"] = "none"
            if "password" in data and data["password"] and user.auth_source != "ldap":
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
                auth_source="local",
                group_id=UUID(data["group_id"]) if data.get("group_id") else None,
                is_admin=data.get("is_admin", False),
                admin_role=data.get("admin_role", "admin") if data.get("is_admin") and data.get("admin_role", "none") == "none" else data.get("admin_role", "none"),
                is_active=data.get("is_active", True),
            )
            return {
                "success": True,
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email or "",
                    "full_name": user.full_name,
                    "balance": float(user.balance),
                    "permissions": user.permissions,
                    "group_id": str(user.group_id) if user.group_id else None,
                    "auth_source": user.auth_source or "local",
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "admin_role": user.admin_role,
                    "created_at": user.created_at,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_user(self, user_id: str) -> dict:
        try:
            user = await self.user_repo.get(UUID(user_id))
            if not user:
                return {"success": False, "error": "User not found"}
            if user.auth_source == "ldap":
                return {"success": False, "error": "Нельзя удалить доменного пользователя. Если нужно заблокировать — установите is_active = False"}
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
        from sqlalchemy import func as sa_func
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        )
        users = result.scalars().all()

        user_ids = [u.id for u in users]
        token_rows = {}
        if user_ids:
            token_result = await self.session.execute(
                select(
                    ChatSession.user_id,
                    sa_func.coalesce(sa_func.sum(ChatMessage.tokens_input), 0),
                    sa_func.coalesce(sa_func.sum(ChatMessage.tokens_output), 0),
                    sa_func.coalesce(sa_func.sum(ChatMessage.cost), 0),
                )
                .select_from(ChatSession)
                .join(ChatMessage, ChatMessage.session_id == ChatSession.id)
                .where(ChatSession.user_id.in_(user_ids))
                .group_by(ChatSession.user_id)
            )
            for uid, tin, tout, cost in token_result:
                token_rows[str(uid)] = {
                    "tokens_input": int(tin),
                    "tokens_output": int(tout),
                    "llm_cost": float(cost),
                }

        return {
            "success": True,
            "users": [
                {
                    "id": str(u.id), "username": u.username, "email": u.email,
                    "full_name": u.full_name, "balance": u.balance,
                    "permissions": u.permissions,
                    "group_id": str(u.group_id) if u.group_id else None,
                    "auth_source": u.auth_source,
                    "is_active": u.is_active,
                    "is_admin": u.is_admin,
                    "admin_role": u.admin_role,
                    "admin_group_id": str(u.admin_group_id) if u.admin_group_id else None,
                    "created_at": u.created_at,
                    "avatar_path": u.avatar_path, "last_login": u.last_login,
                    "token_stats": token_rows.get(str(u.id), {"tokens_input": 0, "tokens_output": 0, "llm_cost": 0}),
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
        return {
            "success": True,
            "id": str(group.id), "name": group.name,
            "ad_group_dn": group.ad_group_dn, "permissions": group.permissions,
            "start_balance": group.start_balance, "description": group.description,
            "is_active": group.is_active, "created_at": group.created_at,
        }

    async def update_group(self, group_id: str, **kwargs) -> dict:
        group = await self.group_repo.get(UUID(group_id))
        if not group:
            return {"success": False, "error": "Group not found"}
        clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if clean_kwargs:
            await self.group_repo.update(UUID(group_id), **clean_kwargs)
        return {"success": True}

    async def get_group(self, group_id: str) -> dict | None:
        try:
            group = await self.group_repo.get(UUID(group_id))
            if not group:
                return None
            return {
                "id": str(group.id), "name": group.name,
                "ad_group_dn": group.ad_group_dn,
                "permissions": group.permissions,
                "start_balance": group.start_balance,
                "description": group.description,
                "is_active": group.is_active,
                "created_at": group.created_at,
            }
        except Exception:
            return None

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
                .options(
                    joinedload(GenerationRecord.user),
                    selectinload(GenerationRecord.assets),
                    selectinload(GenerationRecord.source_gen).selectinload(GenerationRecord.assets),
                )
                .where(GenerationRecord.id == UUID(gen_id))
            )
            record = result.unique().scalar_one_or_none()
            if not record:
                return None

            def _asset_json(a):
                return {
                    "id": str(a.id), "filename": a.filename,
                    "file_path": a.file_path, "file_size": a.file_size,
                    "width": a.width, "height": a.height,
                }

            source_data = None
            if record.source_generation_id and record.source_gen:
                source_data = {
                    "id": str(record.source_gen.id),
                    "workflow_type": record.source_gen.workflow_type,
                    "images": [_asset_json(a) for a in (record.source_gen.assets or [])],
                }

            return {
                "success": True,
                "id": str(record.id), "user_id": str(record.user_id),
                "username": record.user.username if record.user else "unknown",
                "workflow_type": record.workflow_type, "prompt": record.prompt,
                "width": record.width, "height": record.height,
                "duration": record.duration, "seed": record.seed,
                "status": record.status, "cost": record.cost,
                "error_message": record.error_message,
                "created_at": record.created_at, "updated_at": record.updated_at,
                "images": [_asset_json(a) for a in (record.assets or [])],
                "source_generation": source_data,
                "reference_images": _parse_reference_images(record.result_path),
            }
        except Exception as e:
            logger.exception("get_generation_detail failed")
            return None

    async def list_all_generations(self, skip: int = 0, limit: int = 100) -> dict:
        result = await self.session.execute(
            select(GenerationRecord)
            .options(joinedload(GenerationRecord.user))
            .where(GenerationRecord.deleted_at.is_(None))
            .order_by(GenerationRecord.created_at.desc())
            .offset(skip).limit(limit)
        )
        records = result.unique().scalars().all()

        gen_ids = [r.id for r in records]
        thumb_map: dict[str, str | None] = {}
        if gen_ids:
            thumb_result = await self.session.execute(
                select(ImageAsset.generation_id, ImageAsset.file_path)
                .where(ImageAsset.generation_id.in_(gen_ids))
                .distinct(ImageAsset.generation_id)
                .order_by(ImageAsset.generation_id, ImageAsset.created_at)
            )
            for row in thumb_result:
                thumb_map[str(row.generation_id)] = row.file_path

        return {
            "success": True,
            "generations": [
                {
                    "id": str(r.id), "user_id": str(r.user_id),
                    "username": r.user.username if r.user else "unknown",
                    "workflow_type": r.workflow_type, "prompt": r.prompt,
                    "status": r.status, "cost": r.cost, "created_at": r.created_at,
                    "width": r.width, "height": r.height,
                    "seed": r.seed,
                    "thumbnail": thumb_map.get(str(r.id)),
                }
                for r in records
            ],
        }

    async def force_delete_generation(self, gen_id: str) -> dict:
        try:
            obj = await self.session.get(GenerationRecord, UUID(gen_id))
            if obj is None:
                return {"success": False, "error": "Generation not found"}
            if obj.assets:
                for asset in obj.assets:
                    if asset.file_path:
                        try:
                            p = resolve_path(asset.file_path)
                            if p.exists():
                                p.unlink()
                        except Exception as e:
                            logger.warning(f"Could not delete file {asset.file_path}: {e}")
            await self.session.delete(obj)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

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
                "deleted_at": asset.deleted_at,
            }
        except Exception:
            return None

    async def list_all_assets(self, skip: int = 0, limit: int = 100) -> dict:
        result = await self.session.execute(
            select(ImageAsset)
            .options(joinedload(ImageAsset.user))
            .order_by(ImageAsset.created_at.desc())
            .offset(skip).limit(limit)
        )
        assets = result.unique().scalars().all()
        return {
            "success": True,
            "assets": [
                {
                    "id": str(a.id), "user_id": str(a.user_id),
                    "generation_id": str(a.generation_id) if a.generation_id else None,
                    "filename": a.filename, "file_path": a.file_path,
                    "file_size": a.file_size, "width": a.width, "height": a.height,
                    "created_at": a.created_at,
                    "deleted_at": a.deleted_at,
                    "username": a.user.username if a.user else None,
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
        from sqlalchemy import func as sa_func
        from app.db.models.knowledge import KnowledgeDocument
        users_count = (await self.session.execute(select(sa_func.count()).select_from(User))).scalar()
        groups_count = (await self.session.execute(select(sa_func.count()).select_from(UserGroup))).scalar()
        chats_count = (await self.session.execute(select(sa_func.count()).select_from(ChatSession))).scalar()
        gens_count = (await self.session.execute(
            select(sa_func.count()).select_from(GenerationRecord)
            .where(GenerationRecord.deleted_at.is_(None))
        )).scalar()
        assets_count = (await self.session.execute(
            select(sa_func.count()).select_from(ImageAsset)
            .where(ImageAsset.deleted_at.is_(None))
        )).scalar()
        docs_count = (await self.session.execute(
            select(sa_func.count()).select_from(KnowledgeDocument)
            .where(KnowledgeDocument.deleted_at.is_(None))
        )).scalar()
        indexed_count = (await self.session.execute(
            select(sa_func.count()).select_from(KnowledgeDocument)
            .where(KnowledgeDocument.deleted_at.is_(None))
            .where(KnowledgeDocument.status == "ready")
        )).scalar()
        pending_count = (await self.session.execute(
            select(sa_func.count()).select_from(KnowledgeDocument)
            .where(KnowledgeDocument.deleted_at.is_(None))
            .where(KnowledgeDocument.status == "pending")
        )).scalar()

        token_row = (await self.session.execute(
            select(
                sa_func.coalesce(sa_func.sum(ChatMessage.tokens_input), 0),
                sa_func.coalesce(sa_func.sum(ChatMessage.tokens_output), 0),
                sa_func.coalesce(sa_func.sum(ChatMessage.cost), 0),
            )
        )).one()
        total_tokens_input = int(token_row[0])
        total_tokens_output = int(token_row[1])
        total_llm_cost = float(token_row[2])

        recent_users = (await self.session.execute(
            select(User).order_by(User.created_at.desc()).limit(5)
        )).scalars().all()
        recent_chats = (await self.session.execute(
            select(ChatSession).order_by(ChatSession.created_at.desc()).limit(5)
        )).scalars().all()
        recent_gens = (await self.session.execute(
            select(GenerationRecord).order_by(GenerationRecord.created_at.desc()).limit(5)
        )).scalars().all()

        gens_today = (await self.session.execute(
            select(sa_func.count()).select_from(GenerationRecord)
            .where(
                GenerationRecord.created_at >= sa_func.now() - text("INTERVAL '24 hours'"),
                GenerationRecord.deleted_at.is_(None),
            )
        )).scalar() or 0

        return {
            "success": True,
            "users": users_count or 0,
            "groups": groups_count or 0,
            "chats": chats_count or 0,
            "generations": gens_count or 0,
            "assets": assets_count or 0,
            "generations_today": gens_today,
            "documents": docs_count or 0,
            "documents_indexed": indexed_count or 0,
            "documents_pending": pending_count or 0,
            "total_tokens_input": total_tokens_input,
            "total_tokens_output": total_tokens_output,
            "total_llm_cost": total_llm_cost,
            "recent_users": [
                {"id": str(u.id), "username": u.username, "full_name": u.full_name, "avatar_path": u.avatar_path, "created_at": u.created_at}
                for u in recent_users
            ],
            "recent_chats": [
                {"id": str(c.id), "title": c.title, "user_id": str(c.user_id), "created_at": c.created_at}
                for c in recent_chats
            ],
            "recent_generations": [
                {
                    "id": str(g.id), "user_id": str(g.user_id),
                    "workflow_type": g.workflow_type, "status": g.status,
                    "created_at": g.created_at,
                }
                for g in recent_gens
            ],
        }

    async def get_dashboard_activity(self) -> dict:
        from sqlalchemy import func
        rows = (await self.session.execute(
            text("""
                SELECT
                    date_trunc('day', created_at)::date AS day,
                    COUNT(*) AS cnt
                FROM generation_records
                WHERE created_at >= CURRENT_DATE - INTERVAL '14 days'
                GROUP BY day
                ORDER BY day
            """)
        )).fetchall()
        return {
            "success": True,
            "activity": [
                {"date": str(r[0]), "count": r[1]} for r in rows
            ],
        }

    async def force_delete_asset(self, asset_id: str) -> dict:
        try:
            obj = await self.session.get(ImageAsset, UUID(asset_id))
            if obj is None:
                return {"success": False, "error": "Asset not found"}
            if obj.file_path:
                try:
                    p = resolve_path(obj.file_path)
                    if p.exists():
                        p.unlink()
                        parent = p.parent
                        if parent.exists() and not any(parent.iterdir()):
                            parent.rmdir()
                except Exception as e:
                    logger.warning(f"Could not delete file {obj.file_path}: {e}")
            await self.session.delete(obj)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_token_stats(self, user_id: str) -> dict:
        try:
            from sqlalchemy import func as sa_func
            from app.db.models.chat import ChatMessage, ChatSession
            result = await self.session.execute(
                select(
                    sa_func.coalesce(sa_func.sum(ChatMessage.tokens_input), 0),
                    sa_func.coalesce(sa_func.sum(ChatMessage.tokens_output), 0),
                    sa_func.coalesce(sa_func.sum(ChatMessage.cost), 0),
                    sa_func.count(ChatSession.id.distinct()),
                )
                .select_from(ChatSession)
                .join(ChatMessage, ChatMessage.session_id == ChatSession.id)
                .where(ChatSession.user_id == UUID(user_id))
            )
            row = result.one()
            return {
                "success": True,
                "total_tokens_input": int(row[0]),
                "total_tokens_output": int(row[1]),
                "total_cost": float(row[2]),
                "session_count": int(row[3]),
            }
        except Exception as e:
            return {"success": True, "total_tokens_input": 0, "total_tokens_output": 0, "total_cost": 0, "session_count": 0}

    async def list_generation_queue(self) -> dict:
        try:
            result = await self.session.execute(
                select(GenerationRecord)
                .options(joinedload(GenerationRecord.user))
                .where(GenerationRecord.status.in_(["queued", "processing"]))
                .order_by(GenerationRecord.created_at)
            )
            records = result.unique().scalars().all()
            queued_count = sum(1 for r in records if r.status == "queued")
            processing_count = sum(1 for r in records if r.status == "processing")
            return {
                "success": True,
                "items": [
                    {
                        "id": str(r.id), "user_id": str(r.user_id),
                        "username": r.user.username if r.user else "unknown",
                        "workflow_type": r.workflow_type, "prompt": r.prompt,
                        "status": r.status, "created_at": r.created_at,
                    }
                    for r in records
                ],
                "queued_count": queued_count,
                "processing_count": processing_count,
            }
        except Exception as e:
            logger.exception("list_generation_queue failed")
            return {"success": False, "error": str(e)}

    async def cancel_generation_queue(self, gen_id: str) -> dict:
        try:
            record = await self.session.get(GenerationRecord, UUID(gen_id))
            if not record:
                return {"success": False, "error": "Generation not found"}
            if record.status not in ("queued", "processing"):
                return {"success": False, "error": "Можно отменить только задания в очереди или обработке"}
            record.status = "cancelled"
            from app.services.economy_service import EconomyService
            await EconomyService(self.session).add_balance(str(record.user_id), record.cost)
            await self.session.flush()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _force_delete(self, model_class, record_id: str) -> dict:
        try:
            obj = await self.session.get(model_class, UUID(record_id))
            if obj is None:
                return {"success": False, "error": "Record not found"}
            await self.session.delete(obj)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
