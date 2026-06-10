import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.services.settings_service import SettingsService
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _reindex_all_job():
    logger.info("Scheduled reindex: starting reindex of all documents")
    try:
        async with async_session_factory() as session:
            svc = KnowledgeService(session)
            result = await svc.reindex_all()
            logger.info(f"Scheduled reindex completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled reindex failed: {e}")


async def _reindex_new_job():
    logger.info("Scheduled reindex: starting reindex of new/failed documents")
    try:
        async with async_session_factory() as session:
            svc = KnowledgeService(session)
            result = await svc.reindex_new()
            logger.info(f"Scheduled reindex new completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled reindex new failed: {e}")


async def update_schedule():
    async with async_session_factory() as session:
        ss = SettingsService(session)
        enabled = await ss.get_bool("reindex_schedule_enabled", False)
        cron = await ss.get("reindex_cron", "0 3 * * *")
        mode = await ss.get("reindex_mode", "all")

    job_id = "reindex_scheduled"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if not enabled:
        logger.info("Scheduled reindex is disabled")
        return

    job_fn = _reindex_all_job if mode == "all" else _reindex_new_job
    scheduler.add_job(job_fn, "cron", id=job_id, replace_existing=True, cron=cron)
    logger.info(f"Scheduled reindex enabled: cron={cron}, mode={mode}")


async def start_scheduler():
    scheduler.start()
    logger.info("Reindex scheduler started")
    await update_schedule()


async def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Reindex scheduler stopped")


async def run_reindex_all():
    await _reindex_all_job()


async def run_reindex_new():
    await _reindex_new_job()


async def run_reindex_failed():
    logger.info("Manual reindex: starting reindex of failed documents")
    try:
        async with async_session_factory() as session:
            svc = KnowledgeService(session)
            result = await svc.reindex_failed()
            logger.info(f"Manual reindex failed completed: {result}")
    except Exception as e:
        logger.error(f"Manual reindex failed: {e}")
