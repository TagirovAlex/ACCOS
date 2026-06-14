from pydantic import BaseModel

from app.schemas.admin import BaseResponse


class ModuleSettingResponse(BaseModel):
    module_name: str
    key: str
    value: str


class ModuleSettingsResponse(BaseResponse):
    settings: list[ModuleSettingResponse] = []


class ModuleSettingUpdate(BaseModel):
    value: str
