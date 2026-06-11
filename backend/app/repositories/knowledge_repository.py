import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_, or_, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.knowledge import KnowledgeDocument, KnowledgeChunk


class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(
        self,
        title: str,
        filename: str,
        content_type: str,
        file_path: str,
        created_by: uuid.UUID,
        file_hash: str | None = None,
        ad_group_dn: str | None = None,
        folder: str = "",
        doc_number: str | None = None,
        doc_date: datetime | None = None,
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            id=uuid.uuid4(),
            title=title,
            filename=filename,
            content_type=content_type,
            file_path=file_path,
            file_hash=file_hash,
            ad_group_dn=ad_group_dn,
            folder=folder,
            doc_number=doc_number,
            doc_date=doc_date,
            created_by=created_by,
        )
        self.session.add(doc)
        return doc

    async def find_by_hash(self, file_hash: str) -> KnowledgeDocument | None:
        result = await self.session.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.file_hash == file_hash,
                KnowledgeDocument.deleted_at.is_(None),
                KnowledgeDocument.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_document(self, doc_id: uuid.UUID) -> KnowledgeDocument | None:
        result = await self.session.execute(
            select(KnowledgeDocument)
            .options(joinedload(KnowledgeDocument.chunks))
            .where(KnowledgeDocument.id == doc_id, KnowledgeDocument.deleted_at.is_(None))
        )
        return result.unique().scalar_one_or_none()

    async def list_documents(
        self,
        folder: str | None = None,
        ad_group_dns: list[str] | None = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[KnowledgeDocument]:
        query = select(KnowledgeDocument).where(KnowledgeDocument.deleted_at.is_(None))
        if not include_inactive:
            query = query.where(KnowledgeDocument.is_active == True)
        if folder is not None:
            query = query.where(KnowledgeDocument.folder == folder)
        if ad_group_dns:
            query = query.where(
                or_(
                    KnowledgeDocument.ad_group_dn.is_(None),
                    KnowledgeDocument.ad_group_dn.in_(ad_group_dns),
                )
            )
        query = query.order_by(KnowledgeDocument.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_folders(self) -> list[str]:
        result = await self.session.execute(
            text("SELECT DISTINCT folder FROM knowledge_documents WHERE deleted_at IS NULL ORDER BY folder")
        )
        return [row[0] for row in result.fetchall() if row[0]]

    async def search_documents(self, query_str: str, limit: int = 10) -> list[KnowledgeDocument]:
        query = (
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.deleted_at.is_(None),
                KnowledgeDocument.is_active == True,
                or_(
                    KnowledgeDocument.title.ilike(f"%{query_str}%"),
                    KnowledgeDocument.doc_number.ilike(f"%{query_str}%"),
                    KnowledgeDocument.filename.ilike(f"%{query_str}%"),
                ),
            )
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_document(self, doc_id: uuid.UUID, **kwargs) -> KnowledgeDocument | None:
        doc = await self.get_document(doc_id)
        if not doc:
            return None
        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        doc.updated_at = datetime.now(timezone.utc)
        return doc

    async def soft_delete_document(self, doc_id: uuid.UUID) -> bool:
        doc = await self.get_document(doc_id)
        if not doc:
            return False
        doc.deleted_at = datetime.now(timezone.utc)
        await self.delete_chunks_by_document(doc_id)
        return True

    async def replace_document(
        self, old_id: uuid.UUID, new_doc_id: uuid.UUID
    ) -> tuple[KnowledgeDocument | None, KnowledgeDocument | None]:
        old = await self.get_document(old_id)
        new_doc = await self.get_document(new_doc_id)
        if not old or not new_doc:
            return None, None
        old.is_active = False
        old.superseded_by_doc_id = new_doc_id
        new_doc.supersedes_doc_id = old_id
        return old, new_doc

    async def get_document_by_doc_number(self, doc_number: str) -> KnowledgeDocument | None:
        result = await self.session.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.doc_number == doc_number,
                KnowledgeDocument.deleted_at.is_(None),
                KnowledgeDocument.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_chunks_by_document(self, document_id: uuid.UUID) -> list[dict]:
        result = await self.session.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
        chunks = result.scalars().all()
        return [
            {
                "id": str(c.id),
                "content": c.content,
                "chunk_index": c.chunk_index,
                "meta": c.meta,
            }
            for c in chunks
        ]

    async def count_documents(self) -> int:
        result = await self.session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.deleted_at.is_(None))
        )
        return len(result.scalars().all())

    async def create_chunk(
        self,
        document_id: uuid.UUID,
        content: str,
        chunk_index: int,
        embedding: list[float] | None = None,
        meta: dict | None = None,
    ) -> KnowledgeChunk:
        chunk = KnowledgeChunk(
            id=uuid.uuid4(),
            document_id=document_id,
            content=content,
            embedding=embedding,
            chunk_index=chunk_index,
            meta=meta,
        )
        self.session.add(chunk)
        return chunk

    async def delete_chunks_by_document(self, document_id: uuid.UUID) -> None:
        await self.session.execute(
            text("DELETE FROM knowledge_chunks WHERE document_id = :doc_id"),
            {"doc_id": document_id},
        )

    async def vector_search(
        self,
        embedding: list[float],
        ad_group_dns: list[str] | None = None,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> list[dict[str, Any]]:
        embedding_sql = str(embedding)
        ad_filter = ""
        if ad_group_dns:
            escaped = [f"'{g}'" for g in ad_group_dns]
            ad_filter = f"AND (d.ad_group_dn IS NULL OR d.ad_group_dn IN ({','.join(escaped)}))"
        query = text(f"""
            SELECT
                c.id,
                c.content,
                c.chunk_index,
                c.meta,
                d.id as document_id,
                d.title,
                d.filename,
                d.doc_number,
                d.folder,
                1 - (c.embedding <=> '{embedding_sql}'::vector) AS similarity
            FROM knowledge_chunks c
            JOIN knowledge_documents d ON d.id = c.document_id
            WHERE d.deleted_at IS NULL
              AND d.is_active = TRUE
              {ad_filter}
              AND 1 - (c.embedding <=> '{embedding_sql}'::vector) >= :min_score
            ORDER BY similarity DESC
            LIMIT :top_k
        """)
        result = await self.session.execute(query, {"top_k": top_k, "min_score": min_score})
        rows = []
        for row in result.fetchall():
            rows.append({
                "chunk_id": str(row[0]),
                "content": row[1],
                "chunk_index": row[2],
                "meta": row[3],
                "document_id": str(row[4]),
                "title": row[5],
                "filename": row[6],
                "doc_number": row[7],
                "folder": row[8],
                "similarity": float(row[9]),
            })
        return rows
