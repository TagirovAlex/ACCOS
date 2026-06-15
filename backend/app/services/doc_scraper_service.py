import json
import logging
import uuid
import re
import os
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

BATCH_SIZE = 5


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


def page_to_dict(p: ScrapedPage) -> dict:
    return {"url": p.url, "title": p.title, "content": p.content, "word_count": p.word_count, "fetched_at": p.fetched_at}


def dict_to_page(d: dict) -> ScrapedPage:
    return ScrapedPage(url=d["url"], title=d["title"], content=d["content"], word_count=d["word_count"], fetched_at=d["fetched_at"])


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
        return {"success": True, "job_id": job_id, "site_url": site_url, "site_name": site_name, "status": "queued"}

    async def execute_job(self, job_id: str) -> dict:
        job = await self.repo.get(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}
        if job.status in ("crawling", "processing", "ingesting"):
            return {"success": False, "error": f"Job is already {job.status}"}
        if job.status == "paused":
            state = job.state or {}
        else:
            state = {}
            await self.repo.update(job_id, status="crawling", pages_found=0, pages_scraped=0)
        await self.session.commit()

        is_spa = "#!" in job.site_url
        if is_spa:
            adapter = SpaCrawlerAdapter(max_pages=job.max_pages, max_depth=job.max_depth)
        else:
            adapter = DocScraperAdapter(max_pages=job.max_pages, max_depth=job.max_depth)

        # Phase 1: Discover
        all_slugs = state.get("all_slugs")
        pages_serialized = state.get("pages", [])
        completed_slugs = set(state.get("completed_slugs", []))
        error_list = state.get("errors", [])

        if not all_slugs:
            logger.info(f"{job_id}: starting discovery")
            await self.repo.update(job_id, status="crawling")
            await self.session.commit()

            if is_spa:
                project, base_domain, slugs = await adapter.discover(job.site_url)
                all_slugs = slugs
            else:
                urls = await adapter.discover(job.site_url)
                all_slugs = urls

            state = {
                "all_slugs": all_slugs,
                "completed_slugs": [],
                "pages": [],
                "errors": [],
            }
            if is_spa:
                state["project"] = project
                state["base_domain"] = base_domain
            await self.repo.update(job_id, pages_found=len(all_slugs), state=state)
            await self.session.commit()
            logger.info(f"{job_id}: discovered {len(all_slugs)} pages")

        remaining = [s for s in all_slugs if s not in completed_slugs]
        if not remaining:
            logger.info(f"{job_id}: all pages already fetched, processing...")
            pages = [dict_to_page(d) for d in pages_serialized]
        else:
            pages = [dict_to_page(d) for d in pages_serialized]

        # Phase 2: Fetch in batches
        while remaining:
            fresh = await self.repo.get(job_id)
            if fresh.status == "paused":
                logger.info(f"{job_id}: paused, saving state")
                state["completed_slugs"] = list(completed_slugs)
                state["pages"] = pages_serialized
                state["errors"] = error_list
                await self.repo.update(job_id, status="paused", pages_scraped=len(completed_slugs), state=state)
                await self.session.commit()
                return {"success": True, "job_id": job_id, "status": "paused", "pages_found": len(all_slugs), "pages_scraped": len(completed_slugs)}
            if fresh.status not in ("crawling", "paused"):
                # cancelled or failed — stop
                logger.info(f"{job_id}: status changed to {fresh.status}, stopping")
                return {"success": True, "job_id": job_id, "status": fresh.status}

            batch = remaining[:BATCH_SIZE]
            logger.info(f"{job_id}: fetching batch of {len(batch)} ({len(completed_slugs)}/{len(all_slugs)} done)")

            if is_spa:
                result = await adapter._crawl_batch(state["project"], state["base_domain"], batch, max_pages=job.max_pages)
            else:
                result = await self._crawl_urls_batch(adapter, batch)

            pages.extend(result.pages)
            for e in result.errors:
                error_list.append(e)

            for s in batch:
                completed_slugs.add(s)
            remaining = [s for s in all_slugs if s not in completed_slugs]

            pages_serialized = [page_to_dict(p) for p in pages]
            state["completed_slugs"] = list(completed_slugs)
            state["pages"] = pages_serialized
            state["errors"] = error_list
            await self.repo.update(job_id, pages_scraped=len(completed_slugs), state=state)
            await self.session.commit()

        # Phase 3: Ingest
        await self._ingest(job_id, job, pages, error_list)

    async def _crawl_urls_batch(self, adapter: DocScraperAdapter, urls: list[str]) -> "CrawlResult":
        from app.adapters.doc_scraper_adapter import CrawlResult, ScrapedPage
        import httpx
        from trafilatura import extract
        from app.adapters.doc_scraper_adapter import traf_config

        pages = []
        errors = []
        headers = {"User-Agent": adapter.user_agent}

        async with httpx.AsyncClient(headers=headers, timeout=adapter.timeout) as client:
            for url in urls:
                try:
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code != 200:
                        errors.append(f"{url}: HTTP {resp.status_code}")
                        continue
                    if "text/html" not in resp.headers.get("content-type", ""):
                        continue
                    text_content = extract(resp.text, include_comments=False, include_tables=True, include_links=False, include_formatting=True, favor_recall=True, config=traf_config)
                    if text_content and len(text_content.strip()) >= 50:
                        title = adapter._extract_title(resp.text) if hasattr(adapter, "_extract_title") else ""
                        pages.append(ScrapedPage(url=url, title=title, content=text_content, word_count=len(text_content.split()), fetched_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
                    else:
                        errors.append(f"{url}: empty content")
                except Exception as e:
                    errors.append(f"{url}: {e}")

        return CrawlResult(pages=pages, pages_found=len(urls), errors=errors)

    async def _ingest(self, job_id: str, job: DocScrapeJob, pages: list[ScrapedPage], error_list: list[str]) -> dict:
        if not pages:
            await self.repo.update(job_id, status="failed", pages_found=0, errors=error_list[:100])
            await self.session.commit()
            return {"success": False, "error": "No pages scraped"}

        await self.repo.update(job_id, status="processing", pages_found=len(pages), pages_scraped=len(pages))
        await self.session.commit()

        chunk_size = await self.settings_svc.get_int("rag_chunk_size", 500)
        chunk_overlap = await self.settings_svc.get_int("rag_chunk_overlap", 50)
        min_chunk = 100

        page_chunks = []
        for page in pages:
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

        await self.repo.update(job_id, status="ingesting", chunks_created=len(page_chunks))
        await self.session.commit()

        try:
            from app.adapters.rag_adapter import RAGAdapter
            from app.core.paths import STATIC_DIR

            model = await self.settings_svc.get("rag_embedding_model", "intfloat/multilingual-e5-small")
            if model.startswith("local/"):
                api_key = ""
                base_url = "local"
                model = model.replace("local/", "", 1)
            else:
                base_url = await self.settings_svc.get("lmstudio_base_url", "")
                api_key = await self.settings_svc.get("lmstudio_api_key", "")
            adapter = RAGAdapter(base_url=base_url, model=model, api_key=api_key)

            texts = [pc["text"] for pc in page_chunks]
            embeddings = await adapter.embed(texts)

            scraped_dir = STATIC_DIR / "knowledge" / "scraped" / job.site_name
            os.makedirs(str(scraped_dir), exist_ok=True)
            file_name = f"{uuid.uuid4()}.txt"
            file_path_rel = f"knowledge/scraped/{job.site_name}/{file_name}"
            file_path_abs = str(STATIC_DIR / file_path_rel)
            with open(file_path_abs, "w", encoding="utf-8") as _f:
                _f.write("\n\n---PAGE BREAK---\n\n".join(pc["text"] for pc in page_chunks))

            all_none = all(e is None for e in embeddings) if embeddings else True

            doc_id = uuid.uuid4()
            from app.db.models.knowledge import KnowledgeDocument
            doc = KnowledgeDocument(
                id=doc_id,
                title=f"[Scraped] {job.site_name}",
                filename=f"scrape_{job.site_name}.txt",
                content_type="doc_scrape",
                status="failed" if all_none else "ready",
                error_message="Embedding failed - all chunks have NULL embeddings" if all_none else None,
                file_path=file_path_rel,
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
                status="completed" if not all_none else "failed",
                chunks_ingested=len(page_chunks) if not all_none else 0,
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None) if not all_none else None,
                state=None,
            )
            await self.session.commit()

            return {"success": not all_none, "job_id": job_id, "status": "completed" if not all_none else "failed",
                    "pages_found": len(pages), "pages_scraped": len(pages), "chunks_ingested": len(page_chunks) if not all_none else 0,
                    "document_id": str(doc_id), "error": "Embedding failed" if all_none else None}

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

    async def pause_job(self, job_id: str) -> dict:
        job = await self.repo.get(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}
        if job.status != "crawling":
            return {"success": False, "error": f"Only crawling jobs can be paused (current: {job.status})"}
        await self.repo.update(job_id, status="paused")
        await self.session.commit()
        return {"success": True, "job_id": job_id, "status": "paused"}

    async def resume_job(self, job_id: str) -> dict:
        job = await self.repo.get(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}
        if job.status != "paused":
            return {"success": False, "error": f"Only paused jobs can be resumed (current: {job.status})"}
        await self.repo.update(job_id, status="crawling")
        await self.session.commit()
        return {"success": True, "job_id": job_id, "status": "crawling"}

    async def cancel_job(self, job_id: str) -> dict:
        job = await self.repo.get(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}
        if job.status in ("completed", "failed", "cancelled"):
            return {"success": False, "error": f"Job already {job.status}"}
        await self.repo.update(job_id, status="cancelled")
        return {"success": True, "job_id": job_id, "status": "cancelled"}

    async def delete_job(self, job_id: str) -> dict:
        job = await self.repo.get(job_id)
        if not job:
            return {"success": False, "error": "Job not found"}
        site_name = job.site_name
        await self.delete_site(site_name)
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
