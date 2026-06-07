from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.dependencies import get_db, get_current_user_id
from app.schemas.admin import (
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdate,
    AdminGroupListResponse,
    AdminGroupCreate,
    AdminGroupUpdate,
    AdminSettingListResponse,
    AdminSettingUpdate,
    AdminBalanceAdjust,
    AdminChatListResponse,
    AdminGenerationListResponse,
    AdminAssetListResponse,
    BaseResponse,
)
from app.services.admin_service import AdminService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/admin", tags=["admin"])


async def _require_admin(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get(UUID(user_id))
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user_id


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminUserListResponse(**await service.list_users())


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: str,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=BaseResponse)
async def update_user(
    user_id: str,
    request: AdminUserUpdate,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.update_user(user_id, request.model_dump(exclude_none=True)))


@router.delete("/users/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: str,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.delete_user(user_id))


@router.delete("/groups/{group_id}", response_model=BaseResponse)
async def delete_group(
    group_id: str,
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.delete_group(group_id))


@router.post("/balance/adjust", response_model=BaseResponse)
async def adjust_balance(
    request: AdminBalanceAdjust,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.adjust_balance(admin_id, request.user_id, request.amount))


@router.get("/groups", response_model=AdminGroupListResponse)
async def list_groups(
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminGroupListResponse(**await service.list_groups())


@router.post("/groups", response_model=BaseResponse)
async def create_group(
    request: AdminGroupCreate,
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.create_group(
        name=request.name, ad_group_dn=request.ad_group_dn,
        permissions=request.permissions, start_balance=request.start_balance,
        description=request.description,
    ))


@router.put("/groups/{group_id}", response_model=BaseResponse)
async def update_group(
    group_id: str,
    request: AdminGroupUpdate,
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.update_group(
        group_id, name=request.name, ad_group_dn=request.ad_group_dn,
        permissions=request.permissions, start_balance=request.start_balance,
        description=request.description, is_active=request.is_active,
    ))


@router.get("/chats", response_model=AdminChatListResponse)
async def list_chats(
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminChatListResponse(**await service.list_all_chats())


@router.delete("/chats/{chat_id}", response_model=BaseResponse)
async def delete_chat(
    chat_id: str,
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.force_delete_chat(chat_id))


@router.get("/generations", response_model=AdminGenerationListResponse)
async def list_generations(
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminGenerationListResponse(**await service.list_all_generations())


@router.delete("/generations/{gen_id}", response_model=BaseResponse)
async def delete_generation(
    gen_id: str,
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.force_delete_generation(gen_id))


@router.get("/assets", response_model=AdminAssetListResponse)
async def list_assets(
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminAssetListResponse(**await service.list_all_assets())


@router.get("/settings", response_model=AdminSettingListResponse)
async def get_settings(
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminSettingListResponse(**await service.get_settings())


@router.put("/settings/{key}", response_model=BaseResponse)
async def update_setting(
    key: str,
    request: AdminSettingUpdate,
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.update_setting(key, request.value, request.description))
