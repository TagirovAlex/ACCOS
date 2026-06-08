from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.core.rate_limit import rate_limit
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
@rate_limit("30/minute")
async def create_chat(
    request: Request,
    body: ChatCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.create_chat(user_id, body.title, body.system_prompt)
    return ChatSessionResponse(**result["chat"])


@router.get("/list", response_model=ChatListResponse)
@rate_limit("60/minute")
async def list_chats(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.list_chats(user_id)
    return ChatListResponse(**result)


@router.get("/{session_id}", response_model=ChatHistoryResponse)
@rate_limit("60/minute")
async def get_chat(
    request: Request,
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.get_history(session_id)
    return ChatHistoryResponse(**result)


@router.post("/{session_id}/send", response_model=ChatSendResponse)
@rate_limit("30/minute")
async def send_message(
    request: Request,
    session_id: str,
    body: ChatSendRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.send_message(user_id, session_id, body.message)
    return ChatSendResponse(**result)


@router.delete("/{session_id}")
@rate_limit("30/minute")
async def delete_chat(
    request: Request,
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.delete_chat(user_id, session_id)
    if not result["success"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result.get("error", "Chat not found"))
    return {"success": True}
