import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update

from app.db.models.doc_scrape_job import DocScrapeJob


class DocScraperRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> DocScrapeJob:
        if "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.now(timezone.utc)
        if "updated_at" not in kwargs:
            kwargs["updated_at"] = datetime.now(timezone.utc)
        job = DocScrapeJob(**kwargs)
        self.session.add(job)
        await self.session.flush()
        return job

    async def get(self, job_id: str) -> DocScrapeJob | None:
        stmt = select(DocScrapeJob).where(DocScrapeJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, limit: int = 50) -> list[DocScrapeJob]:
        stmt = select(DocScrapeJob).order_by(desc(DocScrapeJob.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, job_id: str, **kwargs) -> DocScrapeJob | None:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        stmt = update(DocScrapeJob).where(DocScrapeJob.id == job_id).values(**kwargs)
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get(job_id)
