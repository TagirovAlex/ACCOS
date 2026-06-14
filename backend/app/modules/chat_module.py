from fastapi import FastAPI

from app.api.v1.endpoints import chat
from app.modules.base import BaseModule, ModuleSettingDef


class ChatModule(BaseModule):
    name = "chat"
    depends_on = ["core"]

    def register_routes(self, app: FastAPI) -> None:
        app.include_router(chat.router, prefix="/api/v1")

    def get_settings_schema(self) -> list[ModuleSettingDef]:
        return [
            ModuleSettingDef(key="chat_context_messages", label="Context messages", type="number", category="general", default=35, is_admin_setting=True, description="Messages kept in chat context"),
            ModuleSettingDef(key="lmstudio_base_url", label="LM Studio URL", type="string", category="llm", default="http://localhost:1234/v1", is_admin_setting=True, description="LLM API endpoint"),
            ModuleSettingDef(key="lmstudio_model", label="Model", type="string", category="llm", default="", is_admin_setting=True, description="Model name"),
            ModuleSettingDef(key="lmstudio_api_key", label="API key", type="password", category="llm", default="", is_admin_setting=True, description="LLM API key"),
            ModuleSettingDef(key="llm_rate_input", label="Input rate (MS per unit)", type="number", category="pricing", default=1, is_admin_setting=True, description="Cost per 1000 input tokens"),
            ModuleSettingDef(key="llm_rate_output", label="Output rate (MS per unit)", type="number", category="pricing", default=1, is_admin_setting=True, description="Cost per 1000 output tokens"),
            ModuleSettingDef(key="llm_tokens_per_unit", label="Tokens per unit", type="number", category="pricing", default=1000, is_admin_setting=True, description="Token count per pricing unit"),
        ]
