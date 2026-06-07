from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.schemas.generation import GenerateRequest, GenerateResponse, HistoryResponse
from app.services.comfyui_service import ComfyUIService

router = APIRouter(prefix="/generate", tags=["generation"])


@router.post("/", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ComfyUIService(db)
    result = await service.generate(
        user_id,
        request.workflow_type,
        request.prompt,
        request.width,
        request.height,
        request.duration,
    )
    return GenerateResponse(**result)


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ComfyUIService(db)
    result = await service.get_history(user_id)
    return HistoryResponse(**result)
