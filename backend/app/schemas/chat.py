from pydantic import BaseModel
from datetime import datetime


class BaseResponse(BaseModel):
    success: bool = True
    error: str | None = None


class ChatCreateRequest(BaseModel):
    title: str = "New Chat"
    system_prompt: str | None = None


class ChatSendRequest(BaseModel):
    message: str


class ChatSessionResponse(BaseModel):
    id: str
    title: str
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


class ChatSendResponse(BaseResponse):
    message: str
    tokens_input: int
    tokens_output: int
    cost: float
