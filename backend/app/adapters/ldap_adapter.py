import asyncio
import logging

from ldap3 import Server, Connection, ALL, NTLM
from ldap3.utils.conv import escape_filter_chars

from app.adapters.base import BaseAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class LDAPAdapter(BaseAdapter):
    def __init__(self, server: str | None = None, domain: str | None = None, base_dn: str | None = None,
                 bind_dn: str | None = None, bind_password: str | None = None,
                 bind_username: str | None = None):
        self.server = server or settings.ldap_server
        self.domain = domain or settings.ldap_domain
        self.base_dn = base_dn or settings.ldap_base_dn
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        self.bind_username = bind_username

    async def execute(self, **kwargs) -> dict:
        username = kwargs.get("username")
        password = kwargs.get("password")
        if not username or not password:
            return {"authenticated": False, "error": "Missing credentials"}
        return await self.authenticate(username, password)

    def _sync_authenticate(self, username: str, password: str) -> dict:
        try:
            safe_username = escape_filter_chars(username)
            user_dn = f"{self.domain}\\{username}"
            server = Server(self.server, get_info=ALL)
            conn = Connection(server, user=user_dn, password=password, authentication=NTLM, auto_bind=True)
            conn.search(
                search_base=self.base_dn,
                search_filter=f"(sAMAccountName={safe_username})",
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

    async def authenticate(self, username: str, password: str) -> dict:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_authenticate, username, password),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            logger.error(f"LDAP auth timed out for {username}")
            return {"authenticated": False, "error": "LDAP connection timed out"}

    def _bind_connection(self) -> Connection:
        """Create an LDAP connection using available bind credentials.
        Tries: 1) NTLM with bind_username, 2) bind_dn as-is, 3) anonymous."""
        server = Server(self.server, get_info=ALL)
        if self.bind_username:
            user = f"{self.domain}\\{self.bind_username}"
            return Connection(server, user=user, password=self.bind_password, authentication=NTLM, auto_bind=True)
        if self.bind_dn and self.bind_password:
            return Connection(server, user=self.bind_dn, password=self.bind_password, authentication=NTLM, auto_bind=True)
        return Connection(server, auto_bind=True)

    def _sync_list_groups(self, search: str = "") -> list[dict]:
        conn = self._bind_connection()
        search_filter = "(&(objectClass=group)(cn=*))"
        if search:
            safe = escape_filter_chars(search)
            search_filter = f"(&(objectClass=group)(cn=*{safe}*))"
        conn.search(
            search_base=self.base_dn,
            search_filter=search_filter,
            attributes=["cn", "distinguishedName", "description"],
            size_limit=200,
        )
        groups = []
        for entry in conn.entries:
            dn = str(entry.distinguishedName.value) if hasattr(entry, "distinguishedName") and entry.distinguishedName.value else ""
            cn = str(entry.cn.value) if hasattr(entry, "cn") and entry.cn.value else ""
            desc = str(entry.description.value) if hasattr(entry, "description") and entry.description.value else ""
            groups.append({"dn": dn, "cn": cn, "description": desc})
        conn.unbind()
        logger.info(f"LDAP list_groups found {len(groups)} groups")
        return groups

    async def list_groups(self, search: str = "") -> list[dict]:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_list_groups, search),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            logger.error("LDAP list_groups timed out")
            return []
        except Exception as e:
            logger.error(f"LDAP list_groups failed: {e}")
            return []

    async def test_connection(self) -> dict:
        """Проверка подключения к LDAP. Возвращает success и детали ошибки."""
        try:
            conn = await asyncio.wait_for(
                asyncio.to_thread(self._bind_connection),
                timeout=10.0,
            )
            conn.unbind()
            return {"success": True, "message": "Подключение успешно"}
        except Exception as e:
            logger.error(f"LDAP test_connection failed: {e}")
            return {"success": False, "error": str(e)}


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

    async def list_groups(self, search: str = "") -> list[dict]:
        mock = [
            {"dn": "CN=Domain Admins,CN=Users,DC=fidelio,DC=local", "cn": "Domain Admins", "description": "Domain administrators"},
            {"dn": "CN=Domain Users,CN=Users,DC=fidelio,DC=local", "cn": "Domain Users", "description": "All domain users"},
            {"dn": "CN=Domain Guests,CN=Users,DC=fidelio,DC=local", "cn": "Domain Guests", "description": "Domain guests"},
            {"dn": "CN=Enterprise Admins,CN=Users,DC=fidelio,DC=local", "cn": "Enterprise Admins", "description": "Enterprise administrators"},
            {"dn": "CN=Schema Admins,CN=Users,DC=fidelio,DC=local", "cn": "Schema Admins", "description": "Schema administrators"},
            {"dn": "CN=ACCOS Users,OU=ACCOS,DC=fidelio,DC=local", "cn": "ACCOS Users", "description": "ACCOS application users"},
            {"dn": "CN=ACCOS Admins,OU=ACCOS,DC=fidelio,DC=local", "cn": "ACCOS Admins", "description": "ACCOS administrators"},
        ]
        if search:
            s = search.lower()
            mock = [g for g in mock if s in g["cn"].lower() or s in g["dn"].lower()]
        return mock
