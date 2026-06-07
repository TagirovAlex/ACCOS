from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.schemas.auth import BalanceResponse
from app.services.economy_service import EconomyService

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = EconomyService(db)
    result = await service.get_balance(user_id)
    return BalanceResponse(**result)
