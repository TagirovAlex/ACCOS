from typing import Any

from pydantic import BaseModel

from app.schemas.admin import BaseResponse


class ModuleSettingResponse(BaseModel):
    module_name: str
    key: str
    label: str | None = None
    type: str | None = None
    category: str | None = None
    default: Any = None
    description: str | None = None
    is_admin_setting: bool = True
    is_user_setting: bool = False
    validation: dict | None = None
    value: str | None = None


class ModuleSettingsResponse(BaseResponse):
    settings: list[ModuleSettingResponse] = []


class ModuleSettingUpdate(BaseModel):
    value: str
