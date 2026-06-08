from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.core.rate_limit import rate_limit
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, UserInfoResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@rate_limit("5/minute")
async def login(request: Request, login_req: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.authenticate(login_req.username, login_req.password)
    if not result["success"]:
        return TokenResponse(success=False, error=result.get("error"), access_token="")
    return TokenResponse(
        success=True,
        access_token=result["access_token"],
        refresh_token=result.get("refresh_token", ""),
        token_type=result["token_type"],
        is_admin=result.get("user", {}).get("is_admin", False),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.refresh_token(request.refresh_token)
    if not result["success"]:
        return TokenResponse(success=False, error=result.get("error"), access_token="")
    return TokenResponse(
        success=True,
        access_token=result["access_token"],
        refresh_token=result.get("refresh_token", ""),
        token_type=result["token_type"],
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    result = await service.get_user_info(user_id)
    return UserInfoResponse(**result)
