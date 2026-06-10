import os, shutil
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user_id
from app.schemas.admin import (
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdate,
    AdminUserCreate,
    AdminGroupListResponse,
    AdminGroupResponse,
    AdminGroupCreate,
    AdminGroupUpdate,
    AdminSettingListResponse,
    AdminSettingUpdate,
    AdminSettingCreate,
    AdminBalanceAdjust,
    AdminChatListResponse,
    AdminChatDetailResponse,
    AdminGenerationListResponse,
    AdminGenerationDetailResponse,
    AdminGenerationQueueResponse,
    AdminAssetListResponse,
    AdminTokenStatsResponse,
    BackupListResponse,
    BackupCreateResponse,
    LdapGroupListResponse,
    LdapTestResponse,
    FileListResponse,
    BaseResponse,
)
from app.services.admin_service import AdminService
from app.services.backup_service import BackupService
from app.repositories.user_repository import UserRepository
from app.repositories.settings_repository import SettingsRepository
from app.adapters.ldap_adapter import LDAPAdapter, MockLDAPAdapter
from app.core.paths import STATIC_DIR

router = APIRouter(prefix="/admin", tags=["admin"])


async def _require_admin(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get(UUID(user_id))
    if not user or user.admin_role not in ("super_admin", "group_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user_id


async def _require_super_admin(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get(UUID(user_id))
    if not user or user.admin_role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")
    return user


async def _require_admin_or_documents(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await UserRepository(db).get(UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.admin_role in ("super_admin", "group_admin"):
        return user
    permissions = (user.permissions or "").split(",")
    if "documents_manage" in permissions:
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get("/dashboard")
async def get_dashboard_stats(
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.get_dashboard_stats()


@router.get("/dashboard/activity")
async def get_dashboard_activity(
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.get_dashboard_activity()


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminUserListResponse(**await service.list_users(skip=skip, limit=limit))


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


@router.post("/users", response_model=AdminUserResponse)
async def create_user(
    request: AdminUserCreate,
    user_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    result = await service.create_user(request.model_dump())
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Creation failed"))
    return result["user"]


@router.put("/users/{user_id}", response_model=BaseResponse)
async def update_user(
    user_id: str,
    request: AdminUserUpdate,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    result = await service.update_user(user_id, request.model_dump(exclude_none=True))
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Update failed"))
    return BaseResponse(**result)


@router.delete("/users/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: str,
    admin_id: str = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    result = await service.delete_user(user_id)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Delete failed"))
    return BaseResponse(**result)


@router.delete("/groups/{group_id}", response_model=BaseResponse)
async def delete_group(
    group_id: str,
    user_id: str = Depends(_require_super_admin),
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
    skip: int = 0,
    limit: int = 100,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminGroupListResponse(**await service.list_groups(skip=skip, limit=limit))


@router.get("/groups/{group_id}", response_model=AdminGroupResponse)
async def get_group(
    group_id: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    group = await service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


@router.post("/groups")
async def create_group(
    request: AdminGroupCreate,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    result = await service.create_group(
        name=request.name, ad_group_dn=request.ad_group_dn,
        permissions=request.permissions, start_balance=request.start_balance,
        description=request.description,
    )
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Creation failed"))
    return result


@router.put("/groups/{group_id}", response_model=BaseResponse)
async def update_group(
    group_id: str,
    request: AdminGroupUpdate,
    user_id: str = Depends(_require_super_admin),
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
    skip: int = 0,
    limit: int = 100,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminChatListResponse(**await service.list_all_chats(skip=skip, limit=limit))


@router.get("/chats/{chat_id}", response_model=AdminChatDetailResponse)
async def get_chat_detail(
    chat_id: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    chat = await service.get_chat_detail(chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


@router.delete("/chats/{chat_id}", response_model=BaseResponse)
async def delete_chat(
    chat_id: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    result = await service.force_delete_chat(chat_id)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Delete failed"))
    return BaseResponse(**result)


@router.get("/generations", response_model=AdminGenerationListResponse)
async def list_generations(
    skip: int = 0,
    limit: int = 100,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminGenerationListResponse(**await service.list_all_generations(skip=skip, limit=limit))


@router.get("/generations/{gen_id}", response_model=AdminGenerationDetailResponse)
async def get_generation_detail(
    gen_id: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    gen = await service.get_generation_detail(gen_id)
    if not gen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation not found")
    return gen


@router.delete("/generations/{gen_id}", response_model=BaseResponse)
async def delete_generation(
    gen_id: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    result = await service.force_delete_generation(gen_id)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Delete failed"))
    return BaseResponse(**result)


@router.get("/generation-queue", response_model=AdminGenerationQueueResponse)
async def list_generation_queue(
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminGenerationQueueResponse(**await service.list_generation_queue())


@router.delete("/generation-queue/{gen_id}", response_model=BaseResponse)
async def cancel_generation_from_queue(
    gen_id: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    result = await service.cancel_generation_queue(gen_id)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Cancel failed"))
    return BaseResponse(**result)


@router.get("/assets", response_model=AdminAssetListResponse)
async def list_assets(
    skip: int = 0,
    limit: int = 100,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminAssetListResponse(**await service.list_all_assets(skip=skip, limit=limit))


@router.get("/assets/{asset_id}")
async def get_asset_detail(
    asset_id: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    asset = await service.get_asset_detail(asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.delete("/assets/{asset_id}", response_model=BaseResponse)
async def delete_asset(
    asset_id: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    result = await service.force_delete_asset(asset_id)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Delete failed"))
    return BaseResponse(**result)


@router.get("/token-stats/{target_user_id}", response_model=AdminTokenStatsResponse)
async def get_user_token_stats(
    target_user_id: str,
    admin_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminTokenStatsResponse(**await service.get_token_stats(target_user_id))


@router.get("/settings", response_model=AdminSettingListResponse)
async def get_settings(
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return AdminSettingListResponse(**await service.get_settings())


@router.post("/settings", response_model=BaseResponse)
async def create_setting(
    request: AdminSettingCreate,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.create_setting(request.key, request.value, request.description))


@router.put("/settings/{key}", response_model=BaseResponse)
async def update_setting(
    key: str,
    request: AdminSettingUpdate,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.update_setting(key, request.value, request.description))


@router.delete("/settings/{key}", response_model=BaseResponse)
async def delete_setting(
    key: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return BaseResponse(**await service.delete_setting(key))


@router.get("/backups", response_model=BackupListResponse)
async def list_backups(
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = BackupService()
    backups = await service.list_backups()
    return BackupListResponse(success=True, backups=backups)


@router.post("/backups", response_model=BackupCreateResponse)
async def create_backup(
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = BackupService()
    result = await service.create_backup()
    return BackupCreateResponse(**result)


@router.delete("/backups/{filename}", response_model=BaseResponse)
async def delete_backup(
    filename: str,
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    service = BackupService()
    result = await service.delete_backup(filename)
    return BaseResponse(**result)


@router.get("/ldap-groups", response_model=LdapGroupListResponse)
async def list_ldap_groups(
    search: str = "",
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    sr = SettingsRepository(db)

    async def _val(key: str, default: str) -> str:
        s = await sr.get_by_key(key)
        return s.value if s else default

    server = await _val("ldap_server", settings.ldap_server)
    domain = await _val("ldap_domain", settings.ldap_domain)
    base_dn = await _val("ldap_base_dn", settings.ldap_base_dn)
    bind_dn = await _val("ldap_bind_dn", "")
    bind_username = await _val("ldap_bind_username", "")
    bind_password = await _val("ldap_bind_password", "")
    ldap_enabled = await _val("ldap_enabled", "true" if settings.ldap_enabled else "false")
    if not server or ldap_enabled != "true":
        adapter = MockLDAPAdapter()
    else:
        adapter = LDAPAdapter(server=server, domain=domain, base_dn=base_dn,
                              bind_dn=bind_dn or None, bind_username=bind_username or None,
                              bind_password=bind_password or None)
    groups = await adapter.list_groups(search)
    return LdapGroupListResponse(success=True, groups=groups)


@router.get("/ldap-test", response_model=LdapTestResponse)
async def test_ldap_connection(
    user_id: str = Depends(_require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    sr = SettingsRepository(db)

    async def _val(key: str, default: str) -> str:
        s = await sr.get_by_key(key)
        return s.value if s else default

    server = await _val("ldap_server", settings.ldap_server)
    domain = await _val("ldap_domain", settings.ldap_domain)
    base_dn = await _val("ldap_base_dn", settings.ldap_base_dn)
    bind_dn = await _val("ldap_bind_dn", "")
    bind_username = await _val("ldap_bind_username", "")
    bind_password = await _val("ldap_bind_password", "")
    ldap_enabled = await _val("ldap_enabled", "true" if settings.ldap_enabled else "false")
    if not server or ldap_enabled != "true":
        result = {"success": True, "message": "LDAP отключён в конфигурации"}
    else:
        adapter = LDAPAdapter(server=server, domain=domain, base_dn=base_dn,
                              bind_dn=bind_dn or None, bind_username=bind_username or None,
                              bind_password=bind_password or None)
        result = await adapter.test_connection()
    return LdapTestResponse(success=result.get("success", False), message=result.get("message", ""), error=result.get("error"))


@router.get("/files", response_model=FileListResponse)
async def list_files(
    path: str = Query(default="", description="Relative path under static/"),
    admin_id: str = Depends(_require_admin_or_documents),
):
    abs_dir = STATIC_DIR / path if path else STATIC_DIR
    if not abs_dir.exists() or not abs_dir.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")
    resolved = str(abs_dir.resolve())
    static_resolved = str(STATIC_DIR.resolve())
    unresolved = str(abs_dir)
    static_unresolved = str(STATIC_DIR)
    if not (resolved.startswith(static_resolved) or unresolved.startswith(static_unresolved)):
        raise HTTPException(status_code=403, detail="Access denied")

    entries = []
    for child in sorted(abs_dir.iterdir()):
        stat = child.stat()
        rel = (child.relative_to(STATIC_DIR).as_posix()) if child != STATIC_DIR else ""
        entries.append({
            "name": child.name,
            "path": rel,
            "is_dir": child.is_dir(),
            "size": stat.st_size if child.is_file() else 0,
            "modified": stat.st_mtime,
        })
    return {"success": True, "entries": entries, "current_path": path}


@router.get("/files/download")
async def download_file(
    path: str = Query(..., description="Relative path under static/"),
    admin_id: str = Depends(_require_admin_or_documents),
):
    abs_path = STATIC_DIR / path
    if not abs_path.exists() or not abs_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    resolved = str(abs_path.resolve())
    static_resolved = str(STATIC_DIR.resolve())
    unresolved = str(abs_path)
    static_unresolved = str(STATIC_DIR)
    if not (resolved.startswith(static_resolved) or unresolved.startswith(static_unresolved)):
        raise HTTPException(status_code=403, detail="Access denied")
    return FileResponse(str(abs_path))


@router.delete("/files")
async def delete_file(
    path: str = Query(..., description="Relative path under static/"),
    admin_id: str = Depends(_require_admin_or_documents),
):
    abs_path = STATIC_DIR / path
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    resolved = str(abs_path.resolve())
    static_resolved = str(STATIC_DIR.resolve())
    unresolved = str(abs_path)
    static_unresolved = str(STATIC_DIR)
    if not (resolved.startswith(static_resolved) or unresolved.startswith(static_unresolved)):
        raise HTTPException(status_code=403, detail="Access denied")
    if abs_path.samefile(STATIC_DIR):
        raise HTTPException(status_code=400, detail="Cannot delete root directory")

    try:
        if abs_path.is_dir():
            shutil.rmtree(str(abs_path))
        else:
            os.remove(str(abs_path))
        return JSONResponse({"success": True, "error": None})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str = Form(""),
    admin_id: str = Depends(_require_admin_or_documents),
):
    abs_dir = STATIC_DIR / path if path else STATIC_DIR
    if not abs_dir.exists():
        abs_dir.mkdir(parents=True, exist_ok=True)
    abs_path = abs_dir / file.filename
    content = await file.read()
    abs_path.write_bytes(content)
    return {"success": True, "filename": file.filename, "path": path}
