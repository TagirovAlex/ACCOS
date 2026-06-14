import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.dependencies import get_db, get_current_user_id
from app.repositories.module_settings_repository import ModuleSettingsRepository
from app.repositories.user_repository import UserRepository
from app.schemas.module_admin import (
    ModuleSettingsResponse,
    ModuleSettingResponse,
    ModuleSettingUpdate,
    BaseResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-modules"])


async def _require_admin(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get(UUID(user_id))
    if not user or user.admin_role not in ("super_admin", "group_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user_id


@router.get("/modules/{module_name}/settings", response_model=ModuleSettingsResponse)
async def get_module_settings(
    module_name: str,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ModuleSettingsRepository(db)
    settings = await repo.list_global(module_name)
    return ModuleSettingsResponse(
        success=True,
        settings=[
            ModuleSettingResponse(module_name=s.module_name, key=s.key, value=s.value)
            for s in settings
        ],
    )


@router.put("/modules/{module_name}/settings/{key}", response_model=BaseResponse)
async def update_module_setting(
    module_name: str,
    key: str,
    request: ModuleSettingUpdate,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ModuleSettingsRepository(db)
    await repo.set_global(module_name, key, request.value)
    return BaseResponse(success=True)


@router.delete("/modules/{module_name}/settings/{key}", response_model=BaseResponse)
async def delete_module_setting(
    module_name: str,
    key: str,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    repo = ModuleSettingsRepository(db)
    ok = await repo.delete_global(module_name, key)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return BaseResponse(success=True)
