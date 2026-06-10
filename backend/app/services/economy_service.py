import math
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository


class PricingStrategy(ABC):
    @abstractmethod
    def calculate_cost(self, **kwargs) -> float:
        pass


class LLMCostStrategy(PricingStrategy):
    def __init__(self, cost_per_1000: int = 1, token_divisor: int = 1000):
        self.cost_per_1000 = cost_per_1000
        self.token_divisor = token_divisor

    def calculate_cost(self, **kwargs) -> float:
        tokens_input = kwargs.get("tokens_input", 0)
        tokens_output = kwargs.get("tokens_output", 0)
        total = max(tokens_input, tokens_output) / self.token_divisor * self.cost_per_1000
        return max(total, self.cost_per_1000 / self.token_divisor)


class ImageGenCostStrategy(PricingStrategy):
    def __init__(self, cost_per_mp: int = 10, pixel_divisor: int = 1_000_000):
        self.cost_per_mp = cost_per_mp
        self.pixel_divisor = pixel_divisor

    def calculate_cost(self, **kwargs) -> float:
        width = kwargs.get("width", 512)
        height = kwargs.get("height", 512)
        mp = (width * height) / self.pixel_divisor
        return max(math.ceil(mp), 1) * self.cost_per_mp


class ImageEditCostStrategy(PricingStrategy):
    def __init__(self, cost_per_mp: int = 10, pixel_divisor: int = 1_000_000):
        self.cost_per_mp = cost_per_mp
        self.pixel_divisor = pixel_divisor

    def calculate_cost(self, **kwargs) -> float:
        width = kwargs.get("width", 512)
        height = kwargs.get("height", 512)
        mp = (width * height) / self.pixel_divisor
        return max(math.ceil(mp), 1) * self.cost_per_mp


class VideoGenCostStrategy(PricingStrategy):
    def __init__(self, base_cost: int = 10, cost_per_sec: int = 2):
        self.base_cost = base_cost
        self.cost_per_sec = cost_per_sec

    def calculate_cost(self, **kwargs) -> float:
        duration = kwargs.get("duration", 5)
        return self.base_cost + math.ceil(duration) * self.cost_per_sec


class EconomyService:
    CURRENCY = "MS"
    CURRENCY_FULL = "Marins"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self._strategies: dict[str, PricingStrategy] = {}

    async def _load_strategies(self):
        from app.services.settings_service import SettingsService
        ss = SettingsService(self.session)
        self._strategies = {
            "llm": LLMCostStrategy(
                cost_per_1000=max(1, await ss.get_int("llm_rate_input", 1)),
                token_divisor=max(1, await ss.get_int("llm_tokens_per_unit", 1000)),
            ),
            "image_gen": ImageGenCostStrategy(
                cost_per_mp=max(1, await ss.get_int("image_gen_rate_pixel", 10)),
                pixel_divisor=max(1, await ss.get_int("image_pixels_per_unit", 1_000_000)),
            ),
            "image_edit": ImageEditCostStrategy(
                cost_per_mp=max(1, await ss.get_int("image_edit_rate_pixel", 10)),
                pixel_divisor=max(1, await ss.get_int("image_pixels_per_unit", 1_000_000)),
            ),
            "video_gen": VideoGenCostStrategy(
                base_cost=max(0, await ss.get_int("video_gen_base_cost", 10)),
                cost_per_sec=max(1, await ss.get_int("video_gen_rate_sec", 2)),
            ),
        }

    async def calculate_cost(self, operation_type: str, **params) -> float:
        if not self._strategies:
            await self._load_strategies()
        strategy = self._strategies.get(operation_type)
        if not strategy:
            raise ValueError(f"Unknown operation type: {operation_type}")
        return strategy.calculate_cost(**params)

    async def get_balance(self, user_id: str) -> dict:
        from uuid import UUID
        balance = await self.user_repo.get_balance(UUID(user_id))
        if balance is None:
            return {"success": False, "error": "User not found"}
        return {"success": True, "balance": balance}

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
