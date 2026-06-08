import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import async_session_factory
from app.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)


async def run_auto_accrual() -> int:
    try:
        async with async_session_factory() as session:
            settings_repo = SettingsRepository(session)
            interval_setting = await settings_repo.get_by_key("auto_accrual_interval_minutes")
            amount = await settings_repo.get_by_key("auto_accrual_amount")
            if not amount:
                return 3600
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
            if interval_setting:
                return int(interval_setting.value) * 60
            return 3600
    except Exception as e:
        logger.error(f"Auto-accrual failed: {e}")
        return 3600
