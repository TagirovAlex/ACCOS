import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.models.doc_template import DocTemplate


class DocTemplateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, file_path: str, description: str | None = None,
                     variables: str | None = None, category: str | None = None) -> DocTemplate:
        tpl = DocTemplate(
            name=name, file_path=file_path, description=description,
            variables=variables, category=category,
        )
        self.session.add(tpl)
        await self.session.flush()
        return tpl

    async def get(self, template_id: uuid.UUID) -> DocTemplate | None:
        return await self.session.get(DocTemplate, template_id)

    async def list_all(self) -> list[DocTemplate]:
        result = await self.session.execute(select(DocTemplate).order_by(DocTemplate.created_at.desc()))
        return list(result.scalars().all())

    async def update(self, template_id: uuid.UUID, **kwargs) -> DocTemplate | None:
        tpl = await self.get(template_id)
        if not tpl:
            return None
        for key, val in kwargs.items():
            if val is not None and hasattr(tpl, key):
                setattr(tpl, key, val)
        tpl.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return tpl

    async def delete(self, template_id: uuid.UUID) -> bool:
        result = await self.session.execute(delete(DocTemplate).where(DocTemplate.id == template_id))
        return result.rowcount > 0
