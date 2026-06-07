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
        self.comfyui = ComfyUIAdapter()

    async def generate(self, user_id: str, workflow_type: str, prompt: str, width: int = 1024, height: int = 1024, duration: int = 5) -> dict:
        uid = UUID(user_id)

        cost = self.economy.calculate_cost("image_gen", width=width, height=height)
        if workflow_type.startswith("qwen"):
            cost = self.economy.calculate_cost("image_edit", width=width, height=height, avg_ref_size=width)
        if workflow_type in ("text_to_video", "image_to_video"):
            cost = self.economy.calculate_cost("video_gen", resolution=width * height, duration=duration)

        deduct = await self.economy.deduct_balance(user_id, cost)
        if not deduct["success"]:
            return {"success": False, "error": deduct.get("error", "Insufficient balance")}

        record = await self.generation_repo.create(
            user_id=uid,
            workflow_type=workflow_type,
            prompt=prompt,
            width=width,
            height=height,
            duration=duration,
            cost=cost,
            status="processing",
        )

        result = await self.comfyui.execute(
            workflow_type=workflow_type,
            prompt=prompt,
            width=width,
            height=height,
            duration=duration,
        )

        if result["success"]:
            record.status = "completed"
            images = []
            for img in result.get("images", []):
                asset = await self.generation_repo.create_asset(
                    generation_id=record.id,
                    user_id=uid,
                    filename=img["filename"],
                    file_path=f"{img.get('subfolder', '')}/{img['filename']}",
                )
                images.append({"id": str(asset.id), "filename": img["filename"]})
            await self.session.flush()
            return {"success": True, "generation_id": str(record.id), "images": images, "cost": cost}
        else:
            record.status = "failed"
            record.error_message = result.get("error")
            await self.session.flush()
            await self.economy.add_balance(user_id, cost)
            return {"success": False, "error": result.get("error", "Generation failed")}

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
                }
                for r in records
            ],
        }
