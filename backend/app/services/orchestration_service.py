import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.comfyui_adapter import ComfyUIAdapter
from app.repositories.generation_repository import GenerationRepository
from app.services.economy_service import EconomyService

logger = logging.getLogger(__name__)


class OrchestrationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.generation_repo = GenerationRepository(session)
        self.economy = EconomyService(session)
        self.comfyui = ComfyUIAdapter()

    async def image_to_edit(self, user_id: str, generation_id: str, edit_workflow: str, prompt: str, reference_images: list[str]) -> dict:
        uid = UUID(user_id)
        gen = await self.generation_repo.get(UUID(generation_id))
        if not gen:
            return {"success": False, "error": "Source generation not found"}
        if str(gen.user_id) != user_id:
            return {"success": False, "error": "Access denied"}

        cost = self.economy.calculate_cost("image_edit", width=gen.width or 1024, height=gen.height or 1024)
        deduct = await self.economy.deduct_balance(user_id, cost)
        if not deduct["success"]:
            return {"success": False, "error": deduct.get("error", "Insufficient balance")}

        record = await self.generation_repo.create(
            user_id=uid,
            workflow_type=edit_workflow,
            prompt=prompt,
            width=gen.width,
            height=gen.height,
            cost=cost,
            status="processing",
        )

        result = await self.comfyui.execute(
            workflow_type=edit_workflow,
            prompt=prompt,
            images=reference_images,
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
            return {"success": False, "error": result.get("error", "Edit failed")}

    async def image_to_video(self, user_id: str, generation_id: str, prompt: str, duration: int = 5) -> dict:
        uid = UUID(user_id)
        gen = await self.generation_repo.get(UUID(generation_id))
        if not gen:
            return {"success": False, "error": "Source generation not found"}
        if str(gen.user_id) != user_id:
            return {"success": False, "error": "Access denied"}

        assets = gen.assets
        if not assets:
            return {"success": False, "error": "No source images found"}
        reference_path = assets[0].file_path

        cost = self.economy.calculate_cost("video_gen", resolution=(gen.width or 1024) * (gen.height or 1024), duration=duration)
        deduct = await self.economy.deduct_balance(user_id, cost)
        if not deduct["success"]:
            return {"success": False, "error": deduct.get("error", "Insufficient balance")}

        record = await self.generation_repo.create(
            user_id=uid,
            workflow_type="image_to_video",
            prompt=prompt,
            width=gen.width,
            height=gen.height,
            duration=duration,
            cost=cost,
            status="processing",
        )

        result = await self.comfyui.execute(
            workflow_type="image_to_video",
            prompt=prompt,
            images=[reference_path],
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
            return {"success": False, "error": result.get("error", "Video generation failed")}
