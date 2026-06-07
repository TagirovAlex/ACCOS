import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.ldap_adapter import LDAPAdapter, MockLDAPAdapter
from app.core.config import settings
from app.core.security import create_access_token
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        ldap_server = settings.ldap_server
        if "your-ldap" in ldap_server or "localhost" in ldap_server:
            self.ldap = MockLDAPAdapter()
            logger.warning("Using Mock LDAP adapter")
        else:
            self.ldap = LDAPAdapter()

    async def authenticate(self, username: str, password: str) -> dict:
        ldap_result = await self.ldap.execute(username=username, password=password)
        if not ldap_result.get("authenticated"):
            return {"success": False, "error": ldap_result.get("error", "Authentication failed")}
        user = await self.user_repo.get_by_username(username)
        if not user:
            user = await self.user_repo.create(
                username=username,
                email=ldap_result.get("email"),
                full_name=ldap_result.get("full_name"),
                balance=100.0,
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
                "is_admin": user.is_admin,
            },
        }

    async def get_user_info(self, user_id: str) -> dict:
        from uuid import UUID
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
            "is_admin": user.is_admin,
        }
