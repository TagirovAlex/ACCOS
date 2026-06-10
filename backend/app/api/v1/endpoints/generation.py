import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.core.paths import UPLOADS_DIR
from app.core.rate_limit import rate_limit
from app.schemas.generation import (
    GenerateRequest, GenerateResponse, HistoryResponse,
    GenerationStatusResponse, QueueResponse, UploadResponse, BaseResponse,
)
from app.services.comfyui_service import ComfyUIService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/generate", tags=["generation"])

WORKFLOW_PERMISSION = {
    "z_image": "generate",
    "qwen_edit_1": "edit",
    "qwen_edit_2": "edit",
    "qwen_edit_3": "edit",
    "text_to_video": "video",
    "image_to_video": "video",
}

MAX_IMAGE_DIM = 2048


logger = logging.getLogger(__name__)


def _resize_if_needed(file_path: Path) -> Path:
    try:
        img = Image.open(file_path)
        w, h = img.size
        if w > MAX_IMAGE_DIM or h > MAX_IMAGE_DIM:
            ratio = MAX_IMAGE_DIM / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            rgb = img.convert("RGB") if img.mode in ("RGBA", "P") else img
            rgb.save(file_path, quality=95)
        return file_path
    except Exception as e:
        logger.error(f"Image resize failed: {e}")
        return file_path


@router.post("/upload", response_model=UploadResponse)
@rate_limit("10/minute")
async def upload_reference(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    ext = Path(file.filename or "image.png").suffix or ".png"
    unique_name = f"{uuid4().hex}{ext}"
    abs_save_dir = UPLOADS_DIR / user_id
    abs_save_dir.mkdir(parents=True, exist_ok=True)
    abs_path = abs_save_dir / unique_name
    content = await file.read()
    abs_path.write_bytes(content)
    _resize_if_needed(abs_path)
    return UploadResponse(success=True, file_path=str(abs_path), session_id="")


@router.post("/", response_model=GenerateResponse)
@rate_limit("10/minute")
async def generate(
    request: Request,
    body: GenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    required = WORKFLOW_PERMISSION.get(body.workflow_type, "generate")
    user = await UserRepository(db).get(UUID(user_id))
    if user and required not in user.permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Требуется право '{required}' для этого типа генерации")
    service = ComfyUIService(db)
    result = await service.enqueue_generation(
        user_id,
        body.workflow_type,
        body.prompt,
        body.width,
        body.height,
        body.duration,
        body.seed,
        body.reference_images,
    )
    return GenerateResponse(**result)


@router.get("/{generation_id}/status", response_model=GenerationStatusResponse)
@rate_limit("60/minute")
async def get_generation_status(
    request: Request,
    generation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ComfyUIService(db)
    result = await service.get_generation_status(generation_id, user_id)
    return GenerationStatusResponse(**result)


@router.get("/history", response_model=HistoryResponse)
@rate_limit("30/minute")
async def get_history(
    request: Request,
    workflow_type: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ComfyUIService(db)
    result = await service.get_history(user_id, workflow_type)
    return HistoryResponse(**result)


@router.get("/queue", response_model=QueueResponse)
@rate_limit("30/minute")
async def get_queue(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ComfyUIService(db)
    result = await service.get_queue(user_id)
    return QueueResponse(**result)


@router.delete("/queue/{generation_id}", response_model=BaseResponse)
async def cancel_queue_item(
    generation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ComfyUIService(db)
    result = await service.cancel_queue_item(generation_id, user_id)
    return BaseResponse(**result)


@router.delete("/{generation_id}", response_model=BaseResponse)
async def delete_generation(
    generation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ComfyUIService(db)
    result = await service.delete_generation(generation_id, user_id)
    return BaseResponse(**result)
