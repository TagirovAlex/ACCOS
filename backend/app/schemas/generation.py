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


class GenerateResponse(BaseResponse):
    generation_id: str = ""
    images: list[dict] = []
    cost: float = 0.0


class GenerationRecordResponse(BaseModel):
    id: str
    workflow_type: str
    prompt: str
    status: str
    cost: float
    created_at: datetime


class HistoryResponse(BaseResponse):
    generations: list[GenerationRecordResponse] = []


class AdminGroupResponse(BaseModel):
    id: str
    name: str
    ad_group_dn: str
    permissions: str
    start_balance: float
    is_active: bool


class AdminGroupListResponse(BaseResponse):
    groups: list[AdminGroupResponse] = []
