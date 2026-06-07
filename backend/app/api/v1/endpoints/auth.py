from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.schemas.auth import LoginRequest, TokenResponse, UserInfoResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.authenticate(request.username, request.password)
    if not result["success"]:
        return TokenResponse(success=False, error=result.get("error"), access_token="")
    return TokenResponse(
        success=True,
        access_token=result["access_token"],
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
