import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.comfyui_adapter import ComfyUIAdapter
from app.db.models.generation import GenerationRecord
from app.db.models.image_asset import ImageAsset
from app.db.session import async_session_factory
from app.repositories.generation_repository import GenerationRepository
from app.services.economy_service import EconomyService
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

GENERATED_DIR = Path(__file__).parent.parent.parent.parent / "static" / "generated"


async def _process_generation(session: AsyncSession, record: GenerationRecord) -> None:
    uid = record.user_id
    repo = GenerationRepository(session)
    economy = EconomyService(session)
    settings_svc = SettingsService(session)
    api_key = await settings_svc.get("comfyui_api_key")
    comfyui = ComfyUIAdapter(api_key=api_key)

    logger.info(f"Processing generation {record.id} ({record.workflow_type})")

    poll_timeout = await settings_svc.get_int("comfyui_poll_timeout_minutes", 30)
    poll_interval = await settings_svc.get_int("comfyui_poll_interval", 3)

    ref_images = []
    if record.result_path:
        try:
            ref_images = json.loads(record.result_path)
        except (json.JSONDecodeError, TypeError):
            pass

    try:
        result = await comfyui.execute(
            workflow_type=record.workflow_type,
            prompt=record.prompt,
            width=record.width or 1024,
            height=record.height or 1024,
            duration=record.duration or 5,
            images=ref_images,
            poll_timeout_minutes=poll_timeout,
            poll_interval=poll_interval,
        )

        if result["success"]:
            record.status = "completed"
            images = []
            gen_dir = GENERATED_DIR / str(record.id)
            for img in result.get("images", []):
                local_path = gen_dir / img["filename"]
                downloaded = await comfyui.download_image(
                    filename=img["filename"],
                    subfolder=img.get("subfolder", ""),
                    image_type=img.get("type", "output"),
                    save_path=str(local_path),
                )
                if downloaded:
                    asset = await repo.create_asset(
                        generation_id=record.id,
                        user_id=uid,
                        filename=img["filename"],
                        file_path=f"static/generated/{record.id}/{img['filename']}",
                    )
                    images.append({"id": str(asset.id), "filename": img["filename"]})
                else:
                    asset = await repo.create_asset(
                        generation_id=record.id,
                        user_id=uid,
                        filename=img["filename"],
                        file_path=f"{img.get('subfolder', '')}/{img['filename']}",
                    )
                    images.append({"id": str(asset.id), "filename": img["filename"]})
            await session.flush()
            logger.info(f"Generation {record.id} completed with {len(images)} images")
        else:
            record.status = "failed"
            record.error_message = result.get("error", "Generation failed")
            await economy.add_balance(str(uid), record.cost)
            await session.flush()
            logger.error(f"Generation {record.id} failed: {record.error_message}")

    except Exception as e:
        record.status = "failed"
        record.error_message = str(e)
        try:
            await economy.add_balance(str(uid), record.cost)
        except Exception as refund_err:
            logger.error(f"Failed to refund {record.cost} to user {uid}: {refund_err}")
        await session.flush()
        logger.error(f"Generation {record.id} crashed: {e}")


async def _claim_next_job(session: AsyncSession) -> GenerationRecord | None:
    result = await session.execute(
        select(GenerationRecord)
        .where(GenerationRecord.status == "queued")
        .order_by(GenerationRecord.created_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    record = result.scalar_one_or_none()
    if record:
        record.status = "processing"
        record.updated_at = datetime.now(timezone.utc)
        await session.flush()
    return record


async def queue_worker_loop() -> None:
    logger.info("Queue worker started")
    while True:
        record = None
        try:
            async with async_session_factory() as session:
                async with session.begin():
                    record = await _claim_next_job(session)
            if record:
                async with async_session_factory() as session:
                    async with session.begin():
                        await _process_generation(session, record)
        except Exception as e:
            logger.error(f"Queue worker error: {e}")
        await asyncio.sleep(2)
