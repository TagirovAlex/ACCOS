import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


_index_tasks: set[asyncio.Task] = set()
_index_semaphore = asyncio.Semaphore(3)


async def _enqueue_and_track(document_id: uuid.UUID) -> None:
    from app.services.queue_worker import enqueue_knowledge_index
    async with _index_semaphore:
        await enqueue_knowledge_index(document_id)


class KnowledgeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KnowledgeRepository(session)
        self.rag = RAGService(session)

    async def create_document(
        self,
        title: str,
        filename: str,
        content_type: str,
        file_path: str,
        folder: str = "",
        file_hash: str | None = None,
        ad_group_dn: str | None = None,
        doc_number: str | None = None,
        doc_date: datetime | None = None,
        supersedes_doc_id: str | None = None,
        created_by: uuid.UUID | None = None,
    ) -> dict:
        doc = await self.repo.create_document(
            title=title,
            filename=filename,
            content_type=content_type,
            file_path=file_path,
            file_hash=file_hash,
            folder=folder,
            ad_group_dn=ad_group_dn,
            doc_number=doc_number,
            doc_date=doc_date,
            created_by=created_by or uuid.UUID(int=0),
        )

        if supersedes_doc_id:
            try:
                old_id = uuid.UUID(supersedes_doc_id)
                await self.repo.replace_document(old_id, doc.id)
            except (ValueError, Exception) as e:
                logger.warning(f"Failed to link supersession: {e}")

        await self.session.flush()
        pending = self.session.info.setdefault("pending_index", [])
        pending.append(str(doc.id))

        return {"document_id": str(doc.id)}

    async def list_documents(
        self,
        folder: str | None = None,
        ad_group_dns: list[str] | None = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict]:
        docs = await self.repo.list_documents(
            folder=folder,
            ad_group_dns=ad_group_dns,
            include_inactive=include_inactive,
            skip=skip,
            limit=limit,
        )
        return [self._doc_to_dict(d) for d in docs]

    async def get_document(self, doc_id: uuid.UUID) -> dict | None:
        doc = await self.repo.get_document(doc_id)
        if not doc:
            return None
        return self._doc_to_dict(doc)

    async def delete_document(self, doc_id: uuid.UUID) -> bool:
        return await self.repo.soft_delete_document(doc_id)

    async def get_document_chunks(self, doc_id: uuid.UUID) -> list[dict]:
        return await self.repo.get_chunks_by_document(doc_id)

    async def reindex_document(self, doc_id: uuid.UUID) -> dict:
        return await self.rag.index_document(doc_id)

    async def reindex_all(self) -> dict:
        docs = await self.repo.list_documents(include_inactive=False)
        total = len(docs)
        for doc in docs:
            self._fire_index(doc.id)
        return {"success": True, "total": total, "message": "Reindex started in background"}

    async def reindex_new(self) -> dict:
        docs = await self.repo.list_documents(include_inactive=False, limit=9999)
        total = 0
        for doc in docs:
            if doc.status == "pending":
                total += 1
                self._fire_index(doc.id)
        return {"success": True, "total": total, "message": "Indexing started in background"}

    async def reindex_failed(self) -> dict:
        docs = await self.repo.list_documents(include_inactive=False, limit=9999)
        total = 0
        for doc in docs:
            if doc.status == "failed":
                total += 1
                self._fire_index(doc.id)
        return {"success": True, "total": total, "message": "Reindex started in background"}

    def _fire_index(self, doc_id: uuid.UUID) -> None:
        logger.info(f"Firing index task for {doc_id}")
        task = asyncio.create_task(_enqueue_and_track(doc_id))
        _index_tasks.add(task)
        task.add_done_callback(lambda t: (_index_tasks.discard(t), logger.info(f"Index task done for {doc_id}")))

    async def replace_document(
        self,
        old_id: uuid.UUID,
        title: str,
        filename: str,
        content_type: str,
        file_path: str,
        created_by: uuid.UUID,
        file_hash: str | None = None,
    ) -> dict:
        old_doc = await self.repo.get_document(old_id)
        if not old_doc:
            return {"success": False, "error": "Original document not found"}

        doc = await self.repo.create_document(
            title=title,
            filename=filename,
            content_type=content_type,
            file_path=file_path,
            file_hash=file_hash,
            folder=old_doc.folder,
            ad_group_dn=old_doc.ad_group_dn,
            doc_number=old_doc.doc_number,
            doc_date=old_doc.doc_date,
            created_by=created_by,
        )
        await self.repo.replace_document(old_id, doc.id)
        await self.session.flush()
        pending = self.session.info.setdefault("pending_index", [])
        pending.append(str(doc.id))

        return {"success": True, "document_id": str(doc.id)}

    async def search(self, query: str, ad_group_dns: list[str] | None = None) -> dict:
        return await self.rag.search(query, ad_group_dns)

    async def search_documents(self, q: str, limit: int = 10) -> list[dict]:
        docs = await self.repo.search_documents(q, limit)
        return [self._doc_to_dict(d) for d in docs]

    async def get_folders(self) -> list[str]:
        return await self.repo.list_folders()

    async def get_stats(self) -> dict:
        from sqlalchemy import func as sa_func
        from app.db.models.knowledge import KnowledgeDocument
        base = select(sa_func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.deleted_at.is_(None))
        total = (await self.session.execute(base)).scalar() or 0
        pending = (await self.session.execute(base.where(KnowledgeDocument.status == "pending"))).scalar() or 0
        indexing = (await self.session.execute(base.where(KnowledgeDocument.status == "indexing"))).scalar() or 0
        ready = (await self.session.execute(base.where(KnowledgeDocument.status == "ready"))).scalar() or 0
        failed = (await self.session.execute(base.where(KnowledgeDocument.status == "failed"))).scalar() or 0
        return {"total": total, "pending": pending, "indexing": indexing, "ready": ready, "failed": failed}

    async def build_context(self, query: str, ad_group_dns: list[str] | None = None) -> str:
        return await self.rag.build_context(query, ad_group_dns)

    def _doc_to_dict(self, doc) -> dict:
        return {
            "id": str(doc.id),
            "title": doc.title,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "status": doc.status,
            "ad_group_dn": doc.ad_group_dn,
            "file_path": doc.file_path,
            "file_hash": doc.file_hash,
            "folder": doc.folder or "",
            "doc_number": doc.doc_number,
            "doc_date": doc.doc_date.isoformat() if doc.doc_date else None,
            "is_active": doc.is_active,
            "supersedes_doc_id": str(doc.supersedes_doc_id) if doc.supersedes_doc_id else None,
            "superseded_by_doc_id": str(doc.superseded_by_doc_id) if doc.superseded_by_doc_id else None,
            "created_by": str(doc.created_by),
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        }
