import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import PROJECT_ROOT
from app.core.dependencies import get_db, get_current_user_id
from app.repositories.user_repository import UserRepository
from app.schemas.auth import BalanceResponse
from app.schemas.user import ProfileUpdateRequest, ProfileResponse, AvatarResponse
from app.services.economy_service import EconomyService

router = APIRouter(prefix="/user", tags=["user"])

AVATAR_DIR = PROJECT_ROOT / "static" / "avatars"
AVATAR_MAX_SIZE = 256


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = EconomyService(db)
    result = await service.get_balance(user_id)
    return BalanceResponse(**result)


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return ProfileResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        default_system_prompt=user.default_system_prompt,
        avatar_path=user.avatar_path,
        balance=user.balance,
        permissions=user.permissions,
        is_admin=user.is_admin,
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updates = {}
    if body.default_system_prompt is not None:
        updates["default_system_prompt"] = body.default_system_prompt
    if user.auth_source == "ldap":
        if body.full_name is not None or body.email is not None:
            pass
    else:
        if body.full_name is not None:
            updates["full_name"] = body.full_name
        if body.email is not None:
            updates["email"] = body.email
    user = await repo.update(uuid.UUID(user_id), **updates)
    return ProfileResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        default_system_prompt=user.default_system_prompt,
        avatar_path=user.avatar_path,
        balance=user.balance,
        permissions=user.permissions,
        is_admin=user.is_admin,
    )


@router.post("/avatar", response_model=AvatarResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    ext = "jpg"
    filename = f"{user_id}.{ext}"
    filepath = AVATAR_DIR / filename
    image_data = await file.read()
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_data))
        size = min(img.width, img.height)
        left = (img.width - size) // 2
        top = (img.height - size) // 2
        img = img.crop((left, top, left + size, top + size))
        img = img.resize((AVATAR_MAX_SIZE, AVATAR_MAX_SIZE), Image.LANCZOS)
        img.save(filepath, "JPEG", quality=85)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image processing failed: {e}",
        )
    repo = UserRepository(db)
    avatar_path = f"static/avatars/{filename}"
    await repo.update(uuid.UUID(user_id), avatar_path=avatar_path)
    return AvatarResponse(avatar_url=f"/{avatar_path}")
