import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.ldap_adapter import LDAPAdapter, MockLDAPAdapter
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.repositories.user_repository import UserRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.settings_repo = SettingsRepository(session)
        self.settings_svc = SettingsService(session)
        self.ldap = None

    async def _init_ldap(self):
        if self.ldap is not None:
            return
        if not settings.ldap_enabled:
            self.ldap = None
            return
        server = await self.settings_svc.get("ldap_server", settings.ldap_server)
        domain = await self.settings_svc.get("ldap_domain", settings.ldap_domain)
        base_dn = await self.settings_svc.get("ldap_base_dn", settings.ldap_base_dn)
        self.ldap = LDAPAdapter(server=server, domain=domain, base_dn=base_dn)

    async def _authenticate_ldap(self, username: str, password: str) -> dict:
        await self._init_ldap()
        if not self.ldap:
            logger.info("LDAP disabled, using local authentication fallback")
            mock = MockLDAPAdapter()
            return await mock.execute(username=username, password=password)
        result = await self.ldap.execute(username=username, password=password)
        if not result.get("authenticated"):
            logger.warning(f"LDAP failed ({result.get('error')}), trying local admin fallback")
            mock = MockLDAPAdapter()
            mock_result = await mock.execute(username=username, password=password)
            if mock_result.get("authenticated"):
                return mock_result
        return result

    async def _resolve_group_and_permissions(self, ldap_result: dict) -> tuple[str | None, str, float]:
        permissions = "chat"
        start_balance = 100.0
        group_id = None
        ad_groups = ldap_result.get("groups", [])
        if not ad_groups:
            settings_val = await self.settings_repo.get_by_key("default_permissions")
            if settings_val:
                permissions = settings_val.value
            balance_val = await self.settings_repo.get_by_key("default_start_balance")
            if balance_val:
                start_balance = float(balance_val.value)
            return group_id, permissions, start_balance
        from app.db.models.user_group import UserGroup
        from sqlalchemy import select
        result = await self.session.execute(
            select(UserGroup).where(UserGroup.ad_group_dn.in_(ad_groups), UserGroup.is_active == True)
        )
        matched_group = result.scalar_one_or_none()
        if matched_group:
            group_id = str(matched_group.id)
            permissions = matched_group.permissions
            start_balance = matched_group.start_balance
        return group_id, permissions, start_balance

    async def _require_ad_group(self, username: str, ldap_result: dict) -> bool:
        if username == settings.admin_username:
            return True
        require = await self.settings_svc.get_bool("require_ad_group_for_login", False)
        if not require:
            return True
        ad_groups = ldap_result.get("groups", [])
        if not ad_groups:
            return False
        from app.db.models.user_group import UserGroup
        from sqlalchemy import select
        result = await self.session.execute(
            select(UserGroup).where(UserGroup.ad_group_dn.in_(ad_groups), UserGroup.is_active == True)
        )
        return result.scalar_one_or_none() is not None

    async def authenticate(self, username: str, password: str) -> dict:
        ldap_result = await self._authenticate_ldap(username, password)
        if not ldap_result.get("authenticated"):
            return {"success": False, "error": ldap_result.get("error", "Authentication failed")}
        if not await self._require_ad_group(username, ldap_result):
            return {"success": False, "error": "Доступ запрещён: пользователь не состоит ни в одной разрешённой доменной группе"}
        user = await self.user_repo.get_by_username(username)
        avatar_path = await self._save_ad_avatar(str(user.id) if user else username, ldap_result.get("avatar_base64"))
        if not user:
            group_id, permissions, start_balance = await self._resolve_group_and_permissions(ldap_result)
            is_admin = (username == settings.admin_username)
            user = await self.user_repo.create(
                username=username,
                email=ldap_result.get("email"),
                full_name=ldap_result.get("full_name"),
                balance=start_balance,
                permissions=permissions,
                is_admin=is_admin,
                auth_source="ldap",
                avatar_path=avatar_path,
                group_id=UUID(group_id) if group_id else None,
            )
        else:
            if user.auth_source != "ldap":
                await self.user_repo.update(user.id, auth_source="ldap")
                user.auth_source = "ldap"
            if username == settings.admin_username and not user.is_admin:
                await self.user_repo.update(user.id, is_admin=True)
                user.is_admin = True
        access = create_access_token(subject=str(user.id))
        refresh = create_refresh_token(subject=str(user.id))
        return {
            "success": True,
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "balance": user.balance,
                "permissions": user.permissions,
                "is_admin": user.is_admin,
                "auth_source": "ldap",
            },
        }

    async def _save_ad_avatar(self, user_id: str, avatar_base64: str | None) -> str | None:
        if not avatar_base64:
            return None
        try:
            import base64, io
            from PIL import Image
            from pathlib import Path
            image_data = base64.b64decode(avatar_base64)
            avatar_dir = Path(__file__).parent.parent.parent.parent / "static" / "avatars"
            avatar_dir.mkdir(parents=True, exist_ok=True)
            filepath = avatar_dir / f"{user_id}.jpg"
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((256, 256), Image.LANCZOS)
            canvas = Image.new("RGB", (256, 256), (255, 255, 255))
            x = (256 - img.width) // 2
            y = (256 - img.height) // 2
            canvas.paste(img, (x, y))
            canvas.save(filepath, "JPEG", quality=85)
            return f"static/avatars/{user_id}.jpg"
        except Exception as e:
            logger.warning(f"Failed to save AD avatar for {user_id}: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return {"success": False, "error": "Invalid or expired refresh token"}
        user = await self.user_repo.get(UUID(payload["sub"]))
        if not user:
            return {"success": False, "error": "User not found"}
        access = create_access_token(subject=str(user.id))
        refresh = create_refresh_token(subject=str(user.id))
        return {
            "success": True,
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }

    async def get_user_info(self, user_id: str) -> dict:
        user = await self.user_repo.get(UUID(user_id))
        if not user:
            return {"success": False, "error": "User not found"}
        return {
            "success": True,
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "balance": user.balance,
            "permissions": user.permissions,
            "is_admin": user.is_admin,
            "auth_source": user.auth_source,
            "avatar_path": user.avatar_path,
        }
