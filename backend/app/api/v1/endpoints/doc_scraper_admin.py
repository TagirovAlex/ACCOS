import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.api.v1.endpoints.admin import _require_admin
from app.db.session import async_session_factory
from app.services.doc_scraper_service import DocScraperService
from app.schemas.doc_scraper import StartScrapeRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/doc-scraper", tags=["admin-doc-scraper"])

_background_tasks: set[asyncio.Task] = set()


async def _run_job(job_id: str) -> None:
    current = asyncio.current_task()
    try:
        async with async_session_factory() as session:
            svc = DocScraperService(session)
            await svc.execute_job(job_id)
    except Exception:
        logger.exception(f"_run_job failed for {job_id}")
    finally:
        _background_tasks.discard(current)


@router.post("/scrape")
async def start_scrape(
    body: StartScrapeRequest,
    db: AsyncSession = Depends(get_db),
    admin_id: str = Depends(_require_admin),
):
    svc = DocScraperService(db)
    result = await svc.start_job(
        site_url=body.site_url,
        site_name=body.site_name,
        max_pages=body.max_pages,
        max_depth=body.max_depth,
        created_by=admin_id,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to start job"))

    await db.commit()
    task = asyncio.create_task(_run_job(result["job_id"]))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return result


@router.get("/jobs")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    jobs = await svc.list_jobs()
    return {"success": True, "jobs": jobs}


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    job = await svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "job": job}


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    result = await svc.cancel_job(job_id)
    await db.commit()
    return result


@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    result = await svc.pause_job(job_id)
    await db.commit()
    return result


@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    result = await svc.resume_job(job_id)
    await db.commit()
    if result.get("success"):
        task = asyncio.create_task(_run_job(job_id))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
    return result


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    job = await svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] in ("crawling", "processing", "ingesting", "paused"):
        raise HTTPException(status_code=400, detail=f"Job is already {job['status']}")

    result = await svc.start_job(
        site_url=job["site_url"],
        site_name=job["site_name"],
        max_pages=job["max_pages"],
        max_depth=job["max_depth"],
        created_by=job["created_by"],
    )
    await db.commit()
    task = asyncio.create_task(_run_job(result["job_id"]))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return result


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    result = await svc.delete_job(job_id)
    await db.commit()
    return result


@router.post("/jobs/{job_id}/reindex")
async def reindex_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    job = await svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from app.services.rag_service import RAGService
    from app.repositories.knowledge_repository import KnowledgeRepository
    from app.db.models.knowledge import KnowledgeDocument
    from sqlalchemy import select

    folder = f"_scraped/{job['site_name']}"
    repo = KnowledgeRepository(db)
    rag = RAGService(db)

    query = select(KnowledgeDocument).where(
        KnowledgeDocument.folder == folder,
        KnowledgeDocument.is_active == True,
    )
    result = await db.execute(query)
    docs = list(result.scalars().all())

    if not docs:
        return {"success": False, "error": f"No documents found in folder {folder}"}

    from datetime import datetime, timezone
    results = []
    for doc in docs:
        doc.deleted_at = None
        db.add(doc)
        result = await rag.index_document(doc.id)
        results.append({"document_id": str(doc.id), "success": result.get("success"), "error": result.get("error")})

    await db.commit()
    return {"success": True, "job_id": job_id, "results": results}


@router.delete("/sites/{site_name}")
async def delete_site(
    site_name: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    result = await svc.delete_site(site_name)
    await db.commit()
    return result
