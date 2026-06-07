from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import os
import uuid
from pathlib import Path

from app.core.dependencies import get_db, get_current_user_id
from app.schemas.generation import GenerateResponse
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/orchestrate", tags=["orchestration"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/image-to-edit/{generation_id}", response_model=GenerateResponse)
async def image_to_edit(
    generation_id: str,
    edit_workflow: str,
    prompt: str,
    files: list[UploadFile] = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    saved_paths = []
    for f in files:
        ext = os.path.splitext(f.filename or "image.png")[1] or ".png"
        file_id = str(uuid.uuid4())
        save_path = UPLOAD_DIR / f"{file_id}{ext}"
        async with aiofiles.open(save_path, "wb") as buffer:
            content = await f.read()
            await buffer.write(content)
        saved_paths.append(str(save_path))

    service = OrchestrationService(db)
    result = await service.image_to_edit(user_id, generation_id, edit_workflow, prompt, saved_paths)

    for p in saved_paths:
        try:
            os.remove(p)
        except OSError:
            pass

    return GenerateResponse(**result)


@router.post("/image-to-video/{generation_id}", response_model=GenerateResponse)
async def image_to_video(
    generation_id: str,
    prompt: str,
    duration: int = 5,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = OrchestrationService(db)
    result = await service.image_to_video(user_id, generation_id, prompt, duration)
    return GenerateResponse(**result)
