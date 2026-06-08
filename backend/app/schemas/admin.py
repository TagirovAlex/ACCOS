from pydantic import BaseModel
from datetime import datetime
from typing import Any


class BaseResponse(BaseModel):
    success: bool = True
    error: str | None = None


class AdminUserResponse(BaseModel):
    id: str
    username: str
    email: str | None = None
    full_name: str | None = None
    balance: float
    permissions: str
    group_id: str | None = None
    auth_source: str = "local"
    is_active: bool
    is_admin: bool
    created_at: datetime


class AdminUserListResponse(BaseResponse):
    users: list[AdminUserResponse] = []


class AdminUserUpdate(BaseModel):
    balance: float | None = None
    permissions: str | None = None
    group_id: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    full_name: str | None = None
    password: str | None = None


class AdminUserCreate(BaseModel):
    username: str
    email: str = ""
    password: str = ""
    balance: float = 100.0
    permissions: str = "chat"
    group_id: str | None = None
    is_admin: bool = False
    is_active: bool = True


class AdminGroupCreate(BaseModel):
    name: str
    ad_group_dn: str
    permissions: str = "chat"
    start_balance: float = 100.0
    description: str | None = None


class AdminGroupUpdate(BaseModel):
    name: str | None = None
    ad_group_dn: str | None = None
    permissions: str | None = None
    start_balance: float | None = None
    description: str | None = None
    is_active: bool | None = None


class AdminGroupResponse(BaseModel):
    id: str
    name: str
    ad_group_dn: str
    permissions: str
    start_balance: float
    description: str | None = None
    is_active: bool
    created_at: datetime


class AdminGroupListResponse(BaseResponse):
    groups: list[AdminGroupResponse] = []


class AdminSettingResponse(BaseModel):
    key: str
    value: str
    description: str | None = None


class AdminSettingListResponse(BaseResponse):
    settings: list[AdminSettingResponse] = []


class AdminSettingUpdate(BaseModel):
    value: str
    description: str | None = None


class AdminSettingCreate(BaseModel):
    key: str
    value: str
    description: str | None = None


class AdminBalanceAdjust(BaseModel):
    user_id: str
    amount: float
    reason: str | None = None


class AdminChatResponse(BaseModel):
    id: str
    user_id: str
    username: str
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminChatListResponse(BaseResponse):
    chats: list[AdminChatResponse] = []


class AdminMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tokens_input: int | None = None
    tokens_output: int | None = None
    cost: float | None = None
    created_at: datetime


class AdminChatDetailResponse(BaseResponse):
    id: str
    user_id: str
    username: str
    title: str
    system_prompt: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: list[AdminMessageResponse] = []


class AdminGenerationAssetResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    file_size: int | None = None


class AdminGenerationResponse(BaseModel):
    id: str
    user_id: str
    username: str
    workflow_type: str
    prompt: str
    status: str
    cost: float
    created_at: datetime


class AdminGenerationListResponse(BaseResponse):
    generations: list[AdminGenerationResponse] = []


class AdminGenerationDetailResponse(BaseResponse):
    id: str
    user_id: str
    username: str
    workflow_type: str
    prompt: str
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    status: str
    cost: float
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    images: list[AdminGenerationAssetResponse] = []


class AdminAssetResponse(BaseModel):
    id: str
    user_id: str
    generation_id: str | None = None
    filename: str
    file_path: str
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    created_at: datetime


class AdminAssetListResponse(BaseResponse):
    assets: list[AdminAssetResponse] = []


class BackupItem(BaseModel):
    filename: str
    size_bytes: int
    created_at: str


class BackupListResponse(BaseResponse):
    backups: list[BackupItem] = []


class BackupCreateResponse(BaseResponse):
    filename: str = ""
    size_bytes: int = 0
    created_at: str = ""


class LdapGroupItem(BaseModel):
    dn: str
    cn: str
    description: str = ""


class LdapGroupListResponse(BaseResponse):
    groups: list[LdapGroupItem] = []
