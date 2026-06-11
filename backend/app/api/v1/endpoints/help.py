from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/v1", tags=["help"])


@router.get("/help")
async def get_help_content(db: AsyncSession = Depends(get_db)):
    ss = SettingsService(db)
    content = await ss.get("help_content", "")
    return {"content": content}
