from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.generation import GenerationRecord
from app.db.models.image_asset import ImageAsset
from app.repositories.base import BaseRepository


class GenerationRepository(BaseRepository[GenerationRecord]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, GenerationRecord)

    async def get_user_generations(self, user_id: UUID, skip: int = 0, limit: int = 50) -> list[GenerationRecord]:
        result = await self.session.execute(
            select(GenerationRecord)
            .where(GenerationRecord.user_id == user_id, GenerationRecord.deleted_at.is_(None))
            .options(selectinload(GenerationRecord.assets))
            .order_by(desc(GenerationRecord.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_asset(self, generation_id: UUID | None, user_id: UUID, filename: str, file_path: str, **kwargs) -> ImageAsset:
        asset = ImageAsset(
            generation_id=generation_id,
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            **kwargs
        )
        self.session.add(asset)
        await self.session.flush()
        return asset
