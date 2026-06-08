import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.generation_repository import GenerationRepository
from app.services.economy_service import EconomyService

logger = logging.getLogger(__name__)


class OrchestrationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.generation_repo = GenerationRepository(session)
        self.economy = EconomyService(session)

    async def enqueue_image_to_edit(self, user_id: str, generation_id: str, edit_workflow: str, prompt: str, reference_images: list[str]) -> dict:
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
            status="queued",
        )

        await self.session.flush()

        return {"success": True, "generation_id": str(record.id), "cost": cost, "status": "queued"}

    async def enqueue_image_to_video(self, user_id: str, generation_id: str, prompt: str, duration: int = 5) -> dict:
        uid = UUID(user_id)
        gen = await self.generation_repo.get(UUID(generation_id))
        if not gen:
            return {"success": False, "error": "Source generation not found"}
        if str(gen.user_id) != user_id:
            return {"success": False, "error": "Access denied"}

        assets = gen.assets
        if not assets:
            return {"success": False, "error": "No source images found"}

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
            status="queued",
        )

        await self.session.flush()

        return {"success": True, "generation_id": str(record.id), "cost": cost, "status": "queued"}
