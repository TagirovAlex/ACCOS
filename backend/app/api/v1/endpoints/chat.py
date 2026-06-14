from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.core.paths import UPLOADS_DIR
from app.core.rate_limit import rate_limit
from app.schemas.chat import (
    ChatCreateRequest,
    ChatUpdateRequest,
    ChatSendRequest,
    ChatListResponse,
    ChatHistoryResponse,
    ChatSendResponse,
    ChatSessionResponse,
    ChatUploadResponse,
    ChatVisionResponse,
    ChatCancelResponse,
)
from app.services.chat_service import ChatService
from app.services.file_parser_service import get_file_type, get_file_size_limit

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
    result = await service.get_history(session_id, user_id=user_id)
    return ChatHistoryResponse(**result)


@router.patch("/{session_id}", response_model=ChatSessionResponse)
@rate_limit("30/minute")
async def update_chat(
    request: Request,
    session_id: str,
    body: ChatUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.update_chat(user_id, session_id, body.title, body.system_prompt)
    return ChatSessionResponse(**result["chat"])


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
    result = await service.send_message(user_id, session_id, body.message, file=body.file)
    return ChatSendResponse(**result)


@router.post("/{session_id}/upload", response_model=ChatUploadResponse)
@rate_limit("10/minute")
async def chat_upload(
    request: Request,
    session_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from app.services.settings_service import SettingsService
    ext = Path(file.filename or "file.bin").suffix or ".bin"
    file_type = get_file_type(file.filename or "")
    settings_svc = SettingsService(db)
    size_key = f"chat_file_max_size_{file_type}"
    max_size = await settings_svc.get_int(size_key, get_file_size_limit(file_type))
    content = await file.read()
    if len(content) > max_size:
        return ChatUploadResponse(success=False, error=f"File too big: max {max_size // 1024 // 1024}MB for {file_type}")
    unique_name = f"{uuid4().hex}{ext}"
    save_dir = UPLOADS_DIR / user_id / "chat"
    save_dir.mkdir(parents=True, exist_ok=True)
    abs_path = save_dir / unique_name
    abs_path.write_bytes(content)
    return ChatUploadResponse(success=True, file_path=str(abs_path))


@router.get("/vision", response_model=ChatVisionResponse)
@rate_limit("10/minute")
async def check_vision(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    from app.adapters.lmstudio_adapter import LMStudioAdapter
    from app.services.settings_service import SettingsService
    settings_svc = SettingsService(db)
    api_key = await settings_svc.get("lmstudio_api_key")
    model = await settings_svc.get("lmstudio_model")
    base_url = await settings_svc.get("lmstudio_base_url")
    llm = LMStudioAdapter(api_key=api_key, model=model, base_url=base_url)
    supports_vision = await llm.check_vision_capability()
    return ChatVisionResponse(supports_vision=supports_vision)


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


@router.post("/{session_id}/cancel", response_model=ChatCancelResponse)
@rate_limit("30/minute")
async def cancel_generation(
    request: Request,
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    result = await service.cancel_generation(user_id, session_id)
    return ChatCancelResponse(**result)
