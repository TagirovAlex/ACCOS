from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository


class PricingStrategy(ABC):
    @abstractmethod
    def calculate_cost(self, **kwargs) -> float:
        pass


class LLMCostStrategy(PricingStrategy):
    rate_input: float = 0.001
    rate_output: float = 0.002

    def calculate_cost(self, **kwargs) -> float:
        tokens_input = kwargs.get("tokens_input", 0)
        tokens_output = kwargs.get("tokens_output", 0)
        return (tokens_input * self.rate_input) + (tokens_output * self.rate_output)


class ImageGenCostStrategy(PricingStrategy):
    base_cost: float = 1.0
    rate_pixel: float = 0.0001

    def calculate_cost(self, **kwargs) -> float:
        width = kwargs.get("width", 512)
        height = kwargs.get("height", 512)
        return self.base_cost + (width * height) * self.rate_pixel


class ImageEditCostStrategy(PricingStrategy):
    base_cost: float = 0.5
    rate_pixel: float = 0.00005

    def calculate_cost(self, **kwargs) -> float:
        width = kwargs.get("width", 512)
        height = kwargs.get("height", 512)
        avg_ref_size = kwargs.get("avg_ref_size", width)
        return self.base_cost + (avg_ref_size * height) * self.rate_pixel


class VideoGenCostStrategy(PricingStrategy):
    base_cost: float = 5.0
    rate_sec: float = 0.5

    def calculate_cost(self, **kwargs) -> float:
        resolution = kwargs.get("resolution", 1024)
        duration = kwargs.get("duration", 5)
        return self.base_cost + (resolution * duration) * self.rate_sec


class EconomyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.strategies = {
            "llm_chat": LLMCostStrategy(),
            "image_gen": ImageGenCostStrategy(),
            "image_edit": ImageEditCostStrategy(),
            "video_gen": VideoGenCostStrategy(),
        }

    async def get_balance(self, user_id: str) -> dict:
        from uuid import UUID
        balance = await self.user_repo.get_balance(UUID(user_id))
        if balance is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "balance": balance}

    def calculate_cost(self, operation_type: str, **params) -> float:
        strategy = self.strategies.get(operation_type)
        if not strategy:
            raise ValueError(f"Unknown operation type: {operation_type}")
        return strategy.calculate_cost(**params)

    async def deduct_balance(self, user_id: str, amount: float) -> dict:
        from uuid import UUID
        uid = UUID(user_id)
        balance = await self.user_repo.get_balance(uid)
        if balance is None:
            return {"success": False, "error": "User not found"}
        if balance < amount:
            return {"success": False, "error": f"Insufficient balance: {balance} < {amount}"}
        await self.user_repo.update_balance(uid, -amount)
        return {"success": True, "new_balance": balance - amount}

    async def add_balance(self, user_id: str, amount: float) -> dict:
        from uuid import UUID
        uid = UUID(user_id)
        user = await self.user_repo.update_balance(uid, amount)
        if not user:
            return {"success": False, "error": "User not found"}
        return {"success": True, "new_balance": user.balance}
