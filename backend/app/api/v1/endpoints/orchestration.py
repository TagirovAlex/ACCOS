import asyncio
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.core.paths import UPLOADS_DIR
from app.schemas.generation import GenerateResponse
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/orchestrate", tags=["orchestration"])


@router.post("/image-to-edit/{generation_id}", response_model=GenerateResponse)
async def image_to_edit(
    generation_id: str,
    edit_workflow: str,
    prompt: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    files: list[UploadFile] | None = File(default=None),
):
    saved_paths: list[str] = []
    if files:
        for f in files:
            ext = os.path.splitext(f.filename or "image.png")[1] or ".png"
            file_id = str(uuid.uuid4())
            save_dir = UPLOADS_DIR / user_id
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / f"{file_id}{ext}"
            content = await f.read()
            await asyncio.to_thread(save_path.write_bytes, content)
            saved_paths.append(str(save_path))

    service = OrchestrationService(db)
    result = await service.enqueue_image_to_edit(
        user_id, generation_id, edit_workflow, prompt,
        reference_images=saved_paths if saved_paths else None,
    )

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
    result = await service.enqueue_image_to_video(user_id, generation_id, prompt, duration)
    return GenerateResponse(**result)
