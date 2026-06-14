from fastapi import FastAPI

from app.api.v1.endpoints import web_fetch_admin
from app.modules.base import BaseModule, ModuleSettingDef


class WebFetchModule(BaseModule):
    name = "web_fetch"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        app.include_router(web_fetch_admin.router, prefix="/api/v1")

    def get_settings_schema(self) -> list[ModuleSettingDef]:
        return [
            ModuleSettingDef(key="web_fetch_enabled", label="Enabled", type="boolean", category="general", default=True, is_admin_setting=True),
            ModuleSettingDef(key="web_fetch_timeout", label="Timeout (s)", type="number", category="general", default=15, is_admin_setting=True),
            ModuleSettingDef(key="web_fetch_max_size", label="Max size (chars)", type="number", category="general", default=10000, is_admin_setting=True),
            ModuleSettingDef(key="web_fetch_blocked_domains", label="Blocked domains", type="string", category="restrictions", default="", is_admin_setting=True),
            ModuleSettingDef(key="web_fetch_blocked_extensions", label="Blocked extensions", type="string", category="restrictions", default=".pdf,.doc,.docx,.zip,.exe", is_admin_setting=True),
        ]
