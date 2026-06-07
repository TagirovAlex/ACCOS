import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.ldap_adapter import LDAPAdapter, MockLDAPAdapter
from app.core.config import settings
from app.core.security import create_access_token
from app.repositories.user_repository import UserRepository
from app.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.settings_repo = SettingsRepository(session)
        ldap_server = settings.ldap_server
        if "your-ldap" in ldap_server or "localhost" in ldap_server:
            self.ldap = MockLDAPAdapter()
            logger.warning("Using Mock LDAP adapter")
        else:
            self.ldap = LDAPAdapter()

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

    async def authenticate(self, username: str, password: str) -> dict:
        ldap_result = await self.ldap.execute(username=username, password=password)
        if not ldap_result.get("authenticated"):
            return {"success": False, "error": ldap_result.get("error", "Authentication failed")}
        user = await self.user_repo.get_by_username(username)
        if not user:
            group_id, permissions, start_balance = await self._resolve_group_and_permissions(ldap_result)
            user = await self.user_repo.create(
                username=username,
                email=ldap_result.get("email"),
                full_name=ldap_result.get("full_name"),
                balance=start_balance,
                permissions=permissions,
                group_id=UUID(group_id) if group_id else None,
            )
        token = create_access_token(subject=str(user.id))
        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "balance": user.balance,
                "permissions": user.permissions,
                "is_admin": user.is_admin,
            },
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
        }
