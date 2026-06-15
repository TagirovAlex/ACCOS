import json
import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paths import STATIC_DIR
from app.repositories.generation_repository import GenerationRepository
from app.services.economy_service import EconomyService
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


def _abs_path_to_url(abs_path: str) -> str:
    if not abs_path:
        return ""
    try:
        p = Path(abs_path)
        rel = p.relative_to(STATIC_DIR)
        return f"/static/{rel.as_posix()}"
    except (ValueError, TypeError):
        pass
    norm = abs_path.replace("\\", "/")
    for marker in ("/static/", "static/"):
        idx = norm.find(marker)
        if idx != -1:
            result = norm[idx:]
            if not result.startswith("/"):
                result = "/" + result
            return result
    return abs_path


def _parse_reference_images(result_path: str | None) -> list[str]:
    if not result_path:
        return []
    try:
        paths = json.loads(result_path)
        if not isinstance(paths, list):
            return []
        return [_abs_path_to_url(p) for p in paths if isinstance(p, str)]
    except (json.JSONDecodeError, TypeError):
        return []


class ComfyUIService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.generation_repo = GenerationRepository(session)
        self.economy = EconomyService(session)

    async def get_queue(self, user_id: str) -> dict:
        uid = UUID(user_id)
        items = await self.generation_repo.get_user_queue(uid)
        processing_count = await self.generation_repo.count_processing()
        avg_minutes = await SettingsService(self.session).get_int("comfyui_poll_timeout_minutes", 30)

        async def _position(item) -> int:
            ahead = processing_count - 1  # processing counts as position 0
            if item.status == "queued":
                ahead = await self.generation_repo.count_ahead_in_queue(item.created_at)
            return ahead + 1

        queue_items = []
        total_ahead = 0
        for item in items:
            pos = await _position(item)
            if item.status == "queued" and pos > total_ahead:
                total_ahead = pos
            queue_items.append({
                "id": str(item.id),
                "workflow_type": item.workflow_type,
                "prompt": item.prompt,
                "status": item.status,
                "position": pos,
                "estimated_seconds": (pos - 1) * avg_minutes * 60 if item.status == "queued" else 0,
                "created_at": item.created_at.isoformat(),
            })

        return {
            "success": True,
            "items": queue_items,
            "total_ahead": total_ahead,
            "estimated_wait_seconds": total_ahead * avg_minutes * 60,
        }

    async def cancel_queue_item(self, generation_id: str, user_id: str) -> dict:
        gen_id = UUID(generation_id)
        uid = UUID(user_id)
        record = await self.generation_repo.cancel_queued(gen_id, uid)
        if not record:
            return {"success": False, "error": "Не удалось отменить. Задание уже выполняется или не найдено."}
        await self.economy.add_balance(user_id, record.cost)
        return {"success": True, "message": "Задание отменено, кредиты возвращены"}

    async def enqueue_generation(self, user_id: str, workflow_type: str, prompt: str, width: int = 1024, height: int = 1024, duration: int = 5, seed: int = -1, reference_images: list[str] | None = None) -> dict:
        uid = UUID(user_id)

        cost = await self.economy.calculate_cost("image_gen", width=width, height=height)
        if workflow_type.startswith("qwen"):
            cost = await self.economy.calculate_cost("image_edit", width=width, height=height, avg_ref_size=width)
        if workflow_type in ("text_to_video", "image_to_video"):
            cost = await self.economy.calculate_cost("video_gen", resolution=width * height, duration=duration)

        deduct = await self.economy.deduct_balance(user_id, cost)
        if not deduct["success"]:
            return {"success": False, "error": deduct.get("error", "Insufficient balance")}

        ref_json = json.dumps(reference_images or [])

        record = await self.generation_repo.create(
            user_id=uid,
            workflow_type=workflow_type,
            prompt=prompt,
            width=width,
            height=height,
            duration=duration,
            seed=seed,
            cost=cost,
            status="queued",
            result_path=ref_json,
        )

        await self.session.flush()

        return {
            "success": True,
            "generation_id": str(record.id),
            "cost": cost,
            "status": "queued",
        }

    async def get_generation_status(self, generation_id: str, user_id: str) -> dict:
        uid = UUID(user_id)
        gen_id = UUID(generation_id)
        record = await self.generation_repo.get(gen_id)
        if not record:
            return {"success": False, "error": "Generation not found"}
        if str(record.user_id) != user_id:
            return {"success": False, "error": "Access denied"}

        def _asset_json(a):
            return {"id": str(a.id), "filename": a.filename, "file_path": a.file_path}

        assets = [_asset_json(a) for a in record.assets or []]

        source_data = None
        if record.source_generation_id and record.source_gen:
            source_data = {
                "id": str(record.source_gen.id),
                "workflow_type": record.source_gen.workflow_type,
                "images": [_asset_json(a) for a in record.source_gen.assets or []],
            }

        return {
            "success": True,
            "generation_id": str(record.id),
            "workflow_type": record.workflow_type,
            "prompt": record.prompt,
            "status": record.status,
            "cost": record.cost,
            "error_message": record.error_message,
            "images": assets,
            "source_generation": source_data,
            "reference_images": _parse_reference_images(record.result_path),
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    async def get_history(self, user_id: str, workflow_type: str | None = None) -> dict:
        uid = UUID(user_id)
        records = await self.generation_repo.get_user_generations(uid, workflow_type=workflow_type)

        def _asset_json(a):
            return {"id": str(a.id), "filename": a.filename, "file_path": a.file_path}

        return {
            "success": True,
            "generations": [
                {
                    "id": str(r.id),
                    "workflow_type": r.workflow_type,
                    "prompt": r.prompt,
                    "status": r.status,
                    "cost": r.cost,
                    "created_at": r.created_at,
                    "images": [_asset_json(a) for a in (r.assets or [])],
                    "source_generation": {
                        "id": str(r.source_gen.id),
                        "workflow_type": r.source_gen.workflow_type,
                        "images": [_asset_json(a) for a in r.source_gen.assets or []],
                    } if r.source_generation_id and r.source_gen else None,
                    "reference_images": _parse_reference_images(r.result_path),
                }
                for r in records
            ],
        }

    async def delete_generation(self, generation_id: str, user_id: str) -> dict:
        gen_id = UUID(generation_id)
        record = await self.generation_repo.get(gen_id)
        if not record:
            return {"success": False, "error": "Generation not found"}
        if str(record.user_id) != user_id:
            return {"success": False, "error": "Access denied"}
        from datetime import datetime, timezone
        from app.db.models.image_asset import ImageAsset
        now = datetime.now(timezone.utc)
        if record.assets:
            for asset in record.assets:
                asset.deleted_at = now
        await self.generation_repo.delete(gen_id, hard=False)
        return {"success": True}
