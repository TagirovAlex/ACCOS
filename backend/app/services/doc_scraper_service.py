import logging
import uuid
import re
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.doc_scrape_job import DocScrapeJob
from app.adapters.doc_scraper_adapter import DocScraperAdapter, ScrapedPage
from app.adapters.spa_crawler_adapter import SpaCrawlerAdapter
from app.services.rag_service import RAGService
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.doc_scraper_repository import DocScraperRepository
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150, min_size: int = 100) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) > chunk_size:
            if current and len(current) >= min_size:
                chunks.append(current)
            current = para
            while len(current) > chunk_size:
                chunks.append(current[:chunk_size])
                current = current[chunk_size - overlap:]
        elif len(current) + len(para) + 2 <= chunk_size:
            current = current + "\n\n" + para if current else para
        else:
            if current and len(current) >= min_size:
                chunks.append(current)
            current = para

    if current and len(current) >= min_size:
        chunks.append(current)

    return chunks


class DocScraperService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DocScraperRepository(session)
        self.rag = RAGService(session)
        self.knowledge_repo = KnowledgeRepository(session)
        self.settings_svc = SettingsService(session)

    async def start_job(self, site_url: str, site_name: str, max_pages: int = 500, max_depth: int = 10, created_by: str | None = None) -> dict:
        job_id = str(uuid.uuid4())
        job = await self.repo.create(
            id=job_id,
            site_url=site_url,
            site_name=site_name,
            status="queued",
            max_pages=max_pages,
            max_depth=max_depth,
            created_by=created_by,
        )
        return {
            "success": True,
            "job_id": job_id,
            "site_url": site_url,
            "site_name": site_name,
            "status": "queued",
        }

    async def execute_job(self, job_id: str) -> dict:
        job = await self.repo.get(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}

        if job.status in ("crawling", "processing", "ingesting"):
            return {"success": False, "error": f"Job is already {job.status}"}

        await self.repo.update(job_id, status="crawling")
        await self.session.commit()

        if "#!" in job.site_url:
            logger.info(f"{job_id}: detected SPA site, using Playwright crawler")
            adapter = SpaCrawlerAdapter(max_pages=job.max_pages, max_depth=job.max_depth)
        else:
            adapter = DocScraperAdapter(max_pages=job.max_pages, max_depth=job.max_depth)
        result = await adapter.crawl(job.site_url, max_pages=job.max_pages, max_depth=job.max_depth)

        if not result.pages:
            await self.repo.update(
                job_id,
                status="failed",
                pages_found=result.pages_found,
                errors=result.errors[:100],
            )
            await self.session.commit()
            return {"success": False, "error": "No pages scraped", "errors": result.errors}

        await self.repo.update(
            job_id,
            status="processing",
            pages_found=result.pages_found,
            pages_scraped=len(result.pages),
        )
        await self.session.commit()

        chunk_size = await self.settings_svc.get_int("rag_chunk_size", 500)
        chunk_overlap = await self.settings_svc.get_int("rag_chunk_overlap", 50)
        min_chunk = 100

        page_chunks = []
        for page in result.pages:
            chunks = chunk_text(page.content, chunk_size, chunk_overlap, min_chunk)
            for idx, chunk_content in enumerate(chunks):
                page_chunks.append({
                    "text": chunk_content,
                    "metadata": {
                        "source_url": page.url,
                        "page_title": page.title,
                        "site_name": job.site_name,
                        "doc_type": "external_documentation",
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "word_count": len(chunk_content.split()),
                        "fetched_at": page.fetched_at,
                        "display_title": f"{job.site_name} — {page.title}" if page.title else job.site_name,
                    },
                })

        await self.repo.update(
            job_id,
            status="ingesting",
            chunks_created=len(page_chunks),
        )
        await self.session.commit()

        try:
            from app.adapters.rag_adapter import RAGAdapter
            model = await self.settings_svc.get("rag_embedding_model", "intfloat/multilingual-e5-small")
            base_url = await self.settings_svc.get("lmstudio_base_url", "")
            api_key = await self.settings_svc.get("lmstudio_api_key", "")
            adapter = RAGAdapter(base_url=base_url, model=model, api_key=api_key)

            texts = [pc["text"] for pc in page_chunks]
            embeddings = await adapter.embed(texts)

            doc_id = uuid.uuid4()
            from app.db.models.knowledge import KnowledgeDocument
            doc = KnowledgeDocument(
                id=doc_id,
                title=f"[Scraped] {job.site_name}",
                filename=f"scrape_{job.site_name}.txt",
                content_type="doc_scrape",
                status="ready",
                file_path="",
                folder=f"_scraped/{job.site_name}",
                created_by=uuid.UUID(job.created_by) if job.created_by else uuid.uuid4(),
            )
            self.session.add(doc)

            for idx, pc in enumerate(page_chunks):
                embedding = embeddings[idx] if embeddings and idx < len(embeddings) else None
                await self.knowledge_repo.create_chunk(
                    document_id=doc_id,
                    content=pc["text"],
                    chunk_index=idx,
                    embedding=embedding,
                    meta=pc["metadata"],
                )

            await self.repo.update(
                job_id,
                status="completed",
                chunks_ingested=len(page_chunks),
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            await self.session.commit()

            return {
                "success": True,
                "job_id": job_id,
                "status": "completed",
                "pages_found": result.pages_found,
                "pages_scraped": len(result.pages),
                "chunks_ingested": len(page_chunks),
                "document_id": str(doc_id),
            }

        except Exception as e:
            logger.error(f"Ingestion failed for job {job_id}: {e}")
            await self.repo.update(job_id, status="failed", errors=[str(e)])
            await self.session.commit()
            return {"success": False, "error": str(e)}

    async def get_job(self, job_id: str) -> dict | None:
        return await self._serialize(await self.repo.get(job_id))

    async def list_jobs(self, limit: int = 50) -> list[dict]:
        jobs = await self.repo.list(limit=limit)
        return [await self._serialize(j) for j in jobs]

    async def cancel_job(self, job_id: str) -> dict:
        job = await self.repo.get(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}
        if job.status in ("completed", "failed", "cancelled"):
            return {"success": False, "error": f"Job already {job.status}"}
        await self.repo.update(job_id, status="cancelled")
        return {"success": True, "job_id": job_id, "status": "cancelled"}

    async def delete_job(self, job_id: str) -> dict:
        ok = await self.repo.delete(job_id)
        return {"success": ok, "error": None if ok else "Job not found"}

    async def delete_site(self, site_name: str) -> dict:
        folder = f"_scraped/{site_name}"
        docs = await self.knowledge_repo.list_documents(folder=folder)
        count = 0
        for doc in docs:
            await self.knowledge_repo.soft_delete_document(doc.id)
            count += 1
        return {"success": True, "deleted_documents": count}

    async def _serialize(self, job: DocScrapeJob | None) -> dict | None:
        if not job:
            return None
        return {
            "id": job.id,
            "site_url": job.site_url,
            "site_name": job.site_name,
            "status": job.status,
            "pages_found": job.pages_found,
            "pages_scraped": job.pages_scraped,
            "chunks_created": job.chunks_created,
            "chunks_ingested": job.chunks_ingested,
            "errors": job.errors or [],
            "max_pages": job.max_pages,
            "max_depth": job.max_depth,
            "is_active": job.is_active,
            "created_by": job.created_by,
            "created_at": str(job.created_at),
            "updated_at": str(job.updated_at),
            "completed_at": str(job.completed_at) if job.completed_at else None,
        }
