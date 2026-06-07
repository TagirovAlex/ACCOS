import logging

from ldap3 import Server, Connection, ALL, NTLM

from app.adapters.base import BaseAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class LDAPAdapter(BaseAdapter):
    def __init__(self):
        self.server = settings.ldap_server
        self.domain = settings.ldap_domain
        self.base_dn = settings.ldap_base_dn

    async def execute(self, **kwargs) -> dict:
        username = kwargs.get("username")
        password = kwargs.get("password")
        if not username or not password:
            return {"authenticated": False, "error": "Missing credentials"}
        return await self.authenticate(username, password)

    async def authenticate(self, username: str, password: str) -> dict:
        try:
            user_dn = f"{self.domain}\\{username}"
            server = Server(self.server, get_info=ALL)
            conn = Connection(server, user=user_dn, password=password, authentication=NTLM, auto_bind=True)
            conn.search(
                search_base=self.base_dn,
                search_filter=f"(sAMAccountName={username})",
                attributes=["mail", "displayName", "memberOf"],
            )
            user_info = {}
            if conn.entries:
                entry = conn.entries[0]
                user_info = {
                    "email": str(entry.mail.value) if hasattr(entry, "mail") and entry.mail.value else None,
                    "full_name": str(entry.displayName.value) if hasattr(entry, "displayName") and entry.displayName.value else None,
                    "groups": [str(g) for g in entry.memberOf.value] if hasattr(entry, "memberOf") and entry.memberOf.value else [],
                }
            conn.unbind()
            return {"authenticated": True, **user_info}
        except Exception as e:
            logger.error(f"LDAP auth failed for {username}: {e}")
            return {"authenticated": False, "error": str(e)}


class MockLDAPAdapter(BaseAdapter):
    async def execute(self, **kwargs) -> dict:
        username = kwargs.get("username", "")
        password = kwargs.get("password", "")
        if username == "admin" and password == settings.admin_password:
            return {
                "authenticated": True,
                "email": "admin@local",
                "full_name": "Admin User",
                "groups": [],
            }
        if username and password:
            return {
                "authenticated": True,
                "email": f"{username}@domain.local",
                "full_name": username.title(),
                "groups": [],
            }
        return {"authenticated": False, "error": "Invalid credentials"}
