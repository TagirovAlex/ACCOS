from pydantic import BaseModel
from datetime import datetime
from typing import Any


class BaseResponse(BaseModel):
    success: bool = True
    error: str | None = None


class TokenStatsSchema(BaseModel):
    tokens_input: int = 0
    tokens_output: int = 0
    llm_cost: float = 0


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
    admin_role: str = "none"
    admin_group_id: str | None = None
    created_at: datetime
    avatar_path: str | None = None
    last_login: datetime | None = None
    token_stats: TokenStatsSchema | None = None


class AdminUserListResponse(BaseResponse):
    users: list[AdminUserResponse] = []


class AdminUserUpdate(BaseModel):
    balance: float | None = None
    permissions: str | None = None
    group_id: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    admin_role: str | None = None
    admin_group_id: str | None = None
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
    admin_role: str = "none"
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


class AdminGenerationSourceResponse(BaseModel):
    id: str
    workflow_type: str
    images: list[AdminGenerationAssetResponse] = []


class AdminGenerationResponse(BaseModel):
    id: str
    user_id: str
    username: str
    workflow_type: str
    prompt: str
    status: str
    cost: float
    width: int | None = None
    height: int | None = None
    seed: int | None = None
    thumbnail: str | None = None
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
    source_generation: AdminGenerationSourceResponse | None = None
    reference_images: list[str] = []


class AdminQueueItemResponse(BaseModel):
    id: str
    user_id: str
    username: str
    workflow_type: str
    prompt: str
    status: str
    created_at: datetime


class AdminGenerationQueueResponse(BaseResponse):
    items: list[AdminQueueItemResponse] = []
    processing_count: int = 0
    queued_count: int = 0


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
    deleted_at: datetime | None = None
    username: str | None = None


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


class LdapTestResponse(BaseResponse):
    message: str = ""


class AdminTokenStatsResponse(BaseResponse):
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost: float = 0
    session_count: int = 0


class FileEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int = 0
    modified: float = 0.0


class FileListResponse(BaseResponse):
    entries: list[FileEntry] = []
    current_path: str = ""


class LlmServerCreate(BaseModel):
    name: str
    base_url: str
    api_key: str = ""
    model_name: str = "default"
    system_prompt: str = ""
    weight: int = 1
    is_active: bool = True


class LlmServerUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    system_prompt: str | None = None
    weight: int | None = None
    is_active: bool | None = None


class LlmServerResponse(BaseModel):
    id: str
    name: str
    base_url: str
    api_key: str = ""
    model_name: str
    system_prompt: str = ""
    weight: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LlmServerListResponse(BaseResponse):
    servers: list[LlmServerResponse] = []


class WebFetchPermissionUpdate(BaseModel):
    enabled: bool | None = None
    requests_per_hour: int | None = None
    requests_per_day: int | None = None
    max_chars: int | None = None
    allowed_domains: str | None = None
    blocked_domains: str | None = None


class WebFetchPermissionResponse(BaseModel):
    id: str
    user_id: str
    username: str = ""
    enabled: bool
    requests_per_hour: int
    requests_per_day: int
    max_chars: int
    allowed_domains: str = ""
    blocked_domains: str = ""
    created_at: datetime
    updated_at: datetime


class WebFetchPermissionListResponse(BaseResponse):
    permissions: list[WebFetchPermissionResponse] = []
    users_without_perms: list[dict] = []
