from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        pass
