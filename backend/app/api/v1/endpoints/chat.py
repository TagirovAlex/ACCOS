from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.schemas.chat import (
    ChatCreateRequest,
    ChatSendRequest,
    ChatListResponse,
    ChatHistoryResponse,
    ChatSendResponse,
    ChatSessionResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/create", response_model=ChatSessionResponse)
async def create_chat(
    request: ChatCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.create_chat(user_id, request.title, request.system_prompt)
    return ChatSessionResponse(**result["chat"])


@router.get("/list", response_model=ChatListResponse)
async def list_chats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.list_chats(user_id)
    return ChatListResponse(**result)


@router.get("/{session_id}", response_model=ChatHistoryResponse)
async def get_chat(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.get_history(session_id)
    return ChatHistoryResponse(**result)


@router.post("/{session_id}/send", response_model=ChatSendResponse)
async def send_message(
    session_id: str,
    request: ChatSendRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.send_message(user_id, session_id, request.message)
    return ChatSendResponse(**result)
