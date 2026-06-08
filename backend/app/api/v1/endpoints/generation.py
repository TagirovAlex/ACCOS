import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.core.rate_limit import rate_limit
from app.schemas.generation import GenerateRequest, GenerateResponse, HistoryResponse, GenerationStatusResponse, UploadResponse
from app.services.comfyui_service import ComfyUIService

router = APIRouter(prefix="/generate", tags=["generation"])

UPLOAD_DIR = Path(__file__).parent.parent.parent.parent.parent / "static" / "uploads"


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
    _user_id: str = Depends(get_current_user_id),
):
    session_id = str(uuid.uuid4())
    abs_save_dir = UPLOAD_DIR / session_id
    abs_save_dir.mkdir(parents=True, exist_ok=True)
    abs_path = abs_save_dir / file.filename
    content = await file.read()
    abs_path.write_bytes(content)
    _resize_if_needed(abs_path)
    return UploadResponse(success=True, file_path=str(abs_path), session_id=session_id)


@router.post("/", response_model=GenerateResponse)
@rate_limit("10/minute")
async def generate(
    request: Request,
    body: GenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ComfyUIService(db)
    result = await service.enqueue_generation(
        user_id,
        body.workflow_type,
        body.prompt,
        body.width,
        body.height,
        body.duration,
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
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = ComfyUIService(db)
    result = await service.get_history(user_id)
    return HistoryResponse(**result)
