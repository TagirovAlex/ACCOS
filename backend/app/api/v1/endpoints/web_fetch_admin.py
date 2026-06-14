import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.dependencies import get_db, get_current_user_id
from app.repositories.web_fetch_repository import WebFetchRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import WebFetchPermissionResponse, WebFetchPermissionUpdate, BaseResponse
from app.api.v1.endpoints.admin import _require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/web-fetch", tags=["admin-web-fetch"])


async def _serialize_perms(perms, db=None) -> dict:
    username = str(perms.user_id)
    if db:
        ur = UserRepository(db)
        u = await ur.get(perms.user_id)
        if u:
            username = u.username
    return {
        "id": str(perms.id),
        "user_id": str(perms.user_id),
        "username": username,
        "enabled": perms.enabled,
        "requests_per_hour": perms.requests_per_hour,
        "requests_per_day": perms.requests_per_day,
        "max_chars": perms.max_chars,
        "usage_count": perms.usage_count,
        "last_usage_at": str(perms.last_usage_at) if perms.last_usage_at else None,
        "allowed_domains": perms.allowed_domains or "",
        "blocked_domains": perms.blocked_domains or "",
        "created_at": perms.created_at,
        "updated_at": perms.updated_at,
    }


@router.get("/permissions")
async def list_web_fetch_permissions(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    repo = WebFetchRepository(db)
    perms_list = await repo.list_all()
    result = []
    for p in perms_list:
        result.append(await _serialize_perms(p, db))
    user_repo = UserRepository(db)
    users = await user_repo.list(limit=1000)
    users_without_perms = []
    for u in users:
        found = any(p.user_id == str(u.id) for p in perms_list)
        if not found:
            users_without_perms.append({
                "user_id": str(u.id),
                "username": u.username,
                "enabled": False,
                "requests_per_hour": 10,
                "requests_per_day": 50,
                "max_chars": 10000,
                "allowed_domains": "",
                "blocked_domains": "",
            })
    return {"success": True, "permissions": result, "users_without_perms": users_without_perms}


@router.get("/permissions/{user_id}")
async def get_web_fetch_permission(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    repo = WebFetchRepository(db)
    perms = await repo.get_by_user_id(user_id)
    if not perms:
        return {"success": True, "permission": None}
    return {"success": True, "permission": await _serialize_perms(perms, db)}


@router.put("/permissions/{user_id}")
async def update_web_fetch_permission(
    user_id: str,
    body: WebFetchPermissionUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    repo = WebFetchRepository(db)
    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    perms = await repo.upsert(user_id, **kwargs)
    return {"success": True, "permission": await _serialize_perms(perms, db)}
