import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
from app.db.models.admin_settings import AdminSettings
from app.modules import ModuleRegistry, ModuleSettingDef

logger = logging.getLogger(__name__)

_registry = ModuleRegistry()
router = APIRouter(prefix="/admin", tags=["admin-modules"])


async def _require_admin(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get(UUID(user_id))
    if not user or user.admin_role not in ("super_admin", "group_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user_id


@router.get("/modules", response_model=dict)
async def list_modules():
    modules = []
    for m in _registry.get_all_modules():
        modules.append({"name": m.name, "depends_on": m.depends_on})
    return {"success": True, "modules": modules}


@router.get("/modules/{module_name}/settings", response_model=ModuleSettingsResponse)
async def get_module_settings(
    module_name: str,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    mod = _registry.get_module(module_name)
    schema = mod.get_settings_schema() if mod else []
    schema_by_key = {s.key: s for s in schema}
    schema_keys = set(schema_by_key.keys())

    result = await db.execute(select(AdminSettings).where(AdminSettings.key.in_(schema_keys)))
    admin_rows = {r.key: r.value for r in result.scalars().all()}

    repo = ModuleSettingsRepository(db)
    module_rows = await repo.list_global(module_name)
    overrides = {r.key: r.value for r in module_rows}

    settings = []
    for s_def in schema:
        value = overrides.get(s_def.key, admin_rows.get(s_def.key, s_def.default))
        settings.append(ModuleSettingResponse(
            module_name=module_name,
            key=s_def.key,
            label=s_def.label,
            type=s_def.type,
            category=s_def.category,
            default=s_def.default,
            description=s_def.description,
            is_admin_setting=s_def.is_admin_setting,
            is_user_setting=s_def.is_user_setting,
            validation=s_def.validation,
            value=str(value) if value is not None else None,
        ))
    return ModuleSettingsResponse(success=True, settings=settings)


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
    result = await db.execute(select(AdminSettings).where(AdminSettings.key == key))
    admin_row = result.scalar_one_or_none()
    if admin_row:
        admin_row.value = request.value
    else:
        db.add(AdminSettings(key=key, value=request.value))
    await db.commit()
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
