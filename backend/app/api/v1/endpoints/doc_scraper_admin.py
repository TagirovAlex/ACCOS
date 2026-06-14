import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.api.v1.endpoints.admin import _require_admin
from app.repositories.doc_scraper_repository import DocScraperRepository
from app.services.doc_scraper_service import DocScraperService
from app.schemas.doc_scraper import StartScrapeRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/doc-scraper", tags=["admin-doc-scraper"])


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

    asyncio.create_task(svc.execute_job(result["job_id"]))
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
    return result


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    result = await svc.execute_job(job_id)
    return result


@router.delete("/sites/{site_name}")
async def delete_site(
    site_name: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(_require_admin),
):
    svc = DocScraperService(db)
    result = await svc.delete_site(site_name)
    return result
