import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from PIL import Image
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.comfyui_adapter import ComfyUIAdapter
from app.core.paths import GENERATIONS_DIR
from app.db.models.generation import GenerationRecord
from app.db.models.image_asset import ImageAsset
from app.db.session import async_session_factory
from app.repositories.generation_repository import GenerationRepository
from app.services.economy_service import EconomyService
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


async def _set_indexing_status(document_id: UUID) -> bool:
    from app.db.session import async_session_factory
    from app.db.models.knowledge import KnowledgeDocument as DocumentModel
    try:
        async with async_session_factory() as session:
            async with session.begin():
                doc = await session.get(DocumentModel, document_id)
                if not doc or doc.status not in ("pending", "ready"):
                    return False
                doc.status = "indexing"
                return True
    except Exception as e:
        logger.error(f"Failed to set indexing status for {document_id}: {e}")
        return False


async def enqueue_knowledge_index(document_id: UUID) -> None:
    ok = await _set_indexing_status(document_id)
    if not ok:
        return
    from app.db.session import async_session_factory
    try:
        async with async_session_factory() as session:
            async with session.begin():
                from app.services.rag_service import RAGService
                svc = RAGService(session)
                result = await svc.index_document(document_id)
                if result["success"]:
                    logger.info(f"Knowledge index completed for {document_id}: {result['chunks']} chunks")
                else:
                    logger.error(f"Knowledge index failed for {document_id}: {result.get('error')}")
    except Exception as e:
        logger.error(f"Knowledge index crashed for {document_id}: {e}")


async def _process_generation(session: AsyncSession, record: GenerationRecord) -> None:
    record = await session.merge(record)
    uid = record.user_id
    repo = GenerationRepository(session)
    economy = EconomyService(session)
    settings_svc = SettingsService(session)
    api_key = await settings_svc.get("comfyui_api_key")
    base_url = await settings_svc.get("comfyui_base_url", "")
    if record.workflow_type == "z_image":
        node_url = await settings_svc.get("comfyui_generate_base_url", "")
    elif record.workflow_type.startswith("qwen"):
        node_url = await settings_svc.get("comfyui_edit_base_url", "")
    elif record.workflow_type in ("text_to_video", "image_to_video"):
        node_url = await settings_svc.get("comfyui_video_base_url", "")
    else:
        node_url = ""
    if not node_url:
        node_url = base_url
    comfyui = ComfyUIAdapter(base_url=node_url, api_key=api_key)

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
            seed=record.seed,
            images=ref_images,
            poll_timeout_minutes=poll_timeout,
            poll_interval=poll_interval,
        )

        if result["success"]:
            record.status = "completed"
            images = []
            gen_dir = GENERATIONS_DIR / str(uid) / str(record.id)
            gen_dir.mkdir(parents=True, exist_ok=True)
            for img in result.get("images", []):
                ext = Path(img["filename"]).suffix or ".png"
                unique_name = f"{uuid4().hex}{ext}"
                local_path = gen_dir / unique_name
                downloaded = await comfyui.download_image(
                    filename=img["filename"],
                    subfolder=img.get("subfolder", ""),
                    image_type=img.get("type", "output"),
                    save_path=str(local_path),
                )
                img_width = None
                img_height = None
                img_size = None
                if downloaded:
                    try:
                        with Image.open(local_path) as pil_img:
                            img_width, img_height = pil_img.size
                        img_size = os.path.getsize(local_path)
                    except Exception:
                        pass
                    asset = await repo.create_asset(
                        generation_id=record.id,
                        user_id=uid,
                        filename=unique_name,
                        file_path=f"static/generations/{uid}/{record.id}/{unique_name}",
                        width=img_width,
                        height=img_height,
                        file_size=img_size,
                    )
                    images.append({"id": str(asset.id), "filename": unique_name})
                else:
                    asset = await repo.create_asset(
                        generation_id=record.id,
                        user_id=uid,
                        filename=unique_name,
                        file_path=f"static/generations/{uid}/{record.id}/{unique_name}",
                    )
                    images.append({"id": str(asset.id), "filename": unique_name})
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
        text("""
            UPDATE generation_records
            SET status = 'processing', updated_at = NOW()
            WHERE id = (
                SELECT id FROM generation_records
                WHERE status = 'queued'
                ORDER BY created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id
        """)
    )
    row = result.fetchone()
    if row:
        record = await session.get(GenerationRecord, row[0])
        return record
    return None


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
