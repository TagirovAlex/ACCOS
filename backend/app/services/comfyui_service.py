import json
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.comfyui_adapter import ComfyUIAdapter
from app.repositories.generation_repository import GenerationRepository
from app.services.economy_service import EconomyService

logger = logging.getLogger(__name__)


class ComfyUIService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.generation_repo = GenerationRepository(session)
        self.economy = EconomyService(session)

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

        assets = []
        for a in record.assets or []:
            assets.append({
                "id": str(a.id),
                "filename": a.filename,
                "file_path": a.file_path,
            })

        return {
            "success": True,
            "generation_id": str(record.id),
            "workflow_type": record.workflow_type,
            "prompt": record.prompt,
            "status": record.status,
            "cost": record.cost,
            "error_message": record.error_message,
            "images": assets,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    async def get_history(self, user_id: str) -> dict:
        uid = UUID(user_id)
        records = await self.generation_repo.get_user_generations(uid)
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
                    "images": [
                        {"id": str(a.id), "filename": a.filename, "file_path": a.file_path}
                        for a in (r.assets or [])
                    ],
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
        await self.generation_repo.delete(gen_id, hard=False)
        return {"success": True}
