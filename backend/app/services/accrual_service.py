import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import async_session_factory
from app.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)


async def run_auto_accrual():
    try:
        async with async_session_factory() as session:
            settings_repo = SettingsRepository(session)
            interval = await settings_repo.get_by_key("auto_accrual_interval_minutes")
            if not interval:
                return
            amount = await settings_repo.get_by_key("auto_accrual_amount")
            if not amount:
                return
            amount_val = float(amount.value)
            result = await session.execute(
                select(User).where(User.is_active == True)
            )
            users = result.scalars().all()
            count = 0
            for user in users:
                user.balance += amount_val
                count += 1
            await session.flush()
            logger.info(f"Auto-accrual: added {amount_val} to {count} active users")
    except Exception as e:
        logger.error(f"Auto-accrual failed: {e}")


async def start_accrual_scheduler():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from app.core.config import settings as app_settings

    scheduler = AsyncIOScheduler()
    interval_minutes = 60

    async def accrual_job():
        async with async_session_factory() as session:
            settings_repo = SettingsRepository(session)
            interval_setting = await settings_repo.get_by_key("auto_accrual_interval_minutes")
            amount_setting = await settings_repo.get_by_key("auto_accrual_amount")
            if interval_setting:
                nonlocal interval_minutes
                interval_minutes = int(interval_setting.value)
            if amount_setting:
                await run_auto_accrual()

    scheduler.add_job(
        accrual_job,
        "interval",
        minutes=interval_minutes,
        id="auto_accrual",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Auto-accrual scheduler started (interval={interval_minutes}min)")
    return scheduler
