from pydantic import BaseModel
from datetime import datetime


class BaseResponse(BaseModel):
    success: bool = True
    error: str | None = None


class ChatCreateRequest(BaseModel):
    title: str = "New Chat"
    system_prompt: str | None = None


class ChatUpdateRequest(BaseModel):
    title: str | None = None
    system_prompt: str | None = None


class ChatSendRequest(BaseModel):
    message: str
    file: str | None = None


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    system_prompt: str | None = None
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tokens_input: int | None = None
    tokens_output: int | None = None
    cost: float | None = None
    created_at: datetime


class ChatListResponse(BaseResponse):
    chats: list[ChatSessionResponse]


class ChatHistoryResponse(BaseResponse):
    session: ChatSessionResponse
    messages: list[ChatMessageResponse]
    has_pending: bool = False


class ChatSendResponse(BaseResponse):
    message: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    cost: float = 0.0


class ChatUploadResponse(BaseResponse):
    file_path: str = ""


class ChatVisionResponse(BaseResponse):
    supports_vision: bool = False


class ChatCancelResponse(BaseResponse):
    pass
