from pydantic import BaseModel
from datetime import datetime


class BaseResponse(BaseModel):
    success: bool = True
    error: str | None = None


class GenerateRequest(BaseModel):
    workflow_type: str
    prompt: str
    width: int = 1024
    height: int = 1024
    duration: int = 5
    reference_images: list[str] = []


class GenerateResponse(BaseResponse):
    generation_id: str = ""
    images: list[dict] = []
    cost: float = 0.0
    status: str = ""


class ImageAssetResponse(BaseModel):
    id: str
    filename: str
    file_path: str


class GenerationRecordResponse(BaseModel):
    id: str
    workflow_type: str
    prompt: str
    status: str
    cost: float
    created_at: datetime
    images: list[ImageAssetResponse] = []


class HistoryResponse(BaseResponse):
    generations: list[GenerationRecordResponse] = []


class GenerationStatusResponse(BaseResponse):
    generation_id: str = ""
    workflow_type: str = ""
    prompt: str = ""
    status: str = ""
    cost: float = 0.0
    error_message: str | None = None
    images: list[ImageAssetResponse] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AdminGroupResponse(BaseModel):
    id: str
    name: str
    ad_group_dn: str
    permissions: str
    start_balance: float
    is_active: bool


class AdminGroupListResponse(BaseResponse):
    groups: list[AdminGroupResponse] = []


class UploadResponse(BaseResponse):
    file_path: str = ""
    session_id: str = ""
